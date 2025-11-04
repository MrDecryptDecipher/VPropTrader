"""Gradient Boosted Tree Meta-Learner for Probability Refinement"""

import numpy as np
import lightgbm as lgb
from pathlib import Path
from typing import Dict, Optional, Tuple
from loguru import logger
from app.core import settings


class GBTMetaLearner:
    """
    Gradient Boosted Tree meta-learner that refines predictions
    from Random Forest and LSTM models
    """
    
    def __init__(self):
        self.model = None
        self.model_path = Path(settings.model_path) / "gbt_meta_learner.txt"
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.feature_names = [
            'rf_pwin',
            'lstm_vol',
            'lstm_dir',
            'regime_trend',
            'regime_revert',
            'regime_choppy',
            'q_star',
            'confidence',
            'expected_rr',
        ]
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        val_split: float = 0.2
    ) -> Dict[str, float]:
        """
        Train GBT meta-learner
        
        Args:
            X: Feature matrix with RF, LSTM, and other predictions
            y: True labels (1 = TP, 0 = SL)
            val_split: Validation split ratio
        
        Returns:
            Dict with training metrics
        """
        try:
            logger.info(f"Training GBT meta-learner on {len(X)} samples...")
            
            # Split data
            n_val = int(len(X) * val_split)
            n_train = len(X) - n_val
            
            X_train, y_train = X[:n_train], y[:n_train]
            X_val, y_val = X[n_train:], y[n_train:]
            
            # Create LightGBM datasets
            train_data = lgb.Dataset(
                X_train,
                label=y_train,
                feature_name=self.feature_names
            )
            val_data = lgb.Dataset(
                X_val,
                label=y_val,
                feature_name=self.feature_names,
                reference=train_data
            )
            
            # Parameters
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': -1,
            }
            
            # Train
            self.model = lgb.train(
                params,
                train_data,
                num_boost_round=100,
                valid_sets=[train_data, val_data],
                valid_names=['train', 'val'],
                callbacks=[
                    lgb.early_stopping(stopping_rounds=10),
                    lgb.log_evaluation(period=10)
                ]
            )
            
            # Evaluate
            train_pred = self.model.predict(X_train)
            val_pred = self.model.predict(X_val)
            
            train_acc = np.mean((train_pred > 0.5) == y_train)
            val_acc = np.mean((val_pred > 0.5) == y_val)
            
            # Calculate log loss
            train_loss = -np.mean(
                y_train * np.log(train_pred + 1e-10) +
                (1 - y_train) * np.log(1 - train_pred + 1e-10)
            )
            val_loss = -np.mean(
                y_val * np.log(val_pred + 1e-10) +
                (1 - y_val) * np.log(1 - val_pred + 1e-10)
            )
            
            metrics = {
                'train_accuracy': float(train_acc),
                'val_accuracy': float(val_acc),
                'train_loss': float(train_loss),
                'val_loss': float(val_loss),
                'train_samples': n_train,
                'val_samples': n_val,
                'n_features': X.shape[1],
            }
            
            logger.info(
                f"✓ GBT meta-learner trained - "
                f"Train Acc: {train_acc:.4f}, Val Acc: {val_acc:.4f}, "
                f"Val Loss: {val_loss:.4f}"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training GBT meta-learner: {e}", exc_info=True)
            return {}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict refined probabilities
        
        Args:
            X: Feature matrix with RF, LSTM predictions
        
        Returns:
            Refined probabilities
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        return self.model.predict(X)
    
    def refine_prediction(
        self,
        rf_pwin: float,
        lstm_vol: float,
        lstm_dir: float,
        regime: str,
        q_star: float,
        confidence: float,
        expected_rr: float
    ) -> float:
        """
        Refine a single prediction
        
        Args:
            rf_pwin: Random Forest P(win)
            lstm_vol: LSTM volatility forecast
            lstm_dir: LSTM direction forecast
            regime: Market regime
            q_star: Q* confidence score
            confidence: Alpha confidence
            expected_rr: Expected risk-reward
        
        Returns:
            Refined probability
        """
        if self.model is None:
            # Fallback to RF prediction if model not loaded
            return rf_pwin
        
        try:
            # Encode regime
            regime_trend = 1.0 if regime == 'trend_up' else 0.0
            regime_revert = 1.0 if regime == 'revert' else 0.0
            regime_choppy = 1.0 if regime == 'choppy' else 0.0
            
            # Create feature vector
            features = np.array([[
                rf_pwin,
                lstm_vol,
                lstm_dir,
                regime_trend,
                regime_revert,
                regime_choppy,
                q_star,
                confidence,
                expected_rr,
            ]])
            
            refined_prob = self.predict(features)[0]
            
            logger.debug(
                f"GBT refinement: RF={rf_pwin:.4f} → Refined={refined_prob:.4f}"
            )
            
            return float(refined_prob)
            
        except Exception as e:
            logger.error(f"Error refining prediction: {e}")
            return rf_pwin
    
    def save(self) -> bool:
        """Save model to disk"""
        if self.model is None:
            logger.warning("No model to save")
            return False
        
        try:
            self.model.save_model(str(self.model_path))
            logger.info(f"✓ GBT meta-learner saved to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving GBT meta-learner: {e}")
            return False
    
    def load(self) -> bool:
        """Load model from disk"""
        if not self.model_path.exists():
            logger.warning(f"Model file not found: {self.model_path}")
            return False
        
        try:
            self.model = lgb.Booster(model_file=str(self.model_path))
            logger.info(f"✓ GBT meta-learner loaded from {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading GBT meta-learner: {e}")
            return False
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if self.model is None:
            return {}
        
        importance = self.model.feature_importance(importance_type='gain')
        
        return {
            name: float(imp)
            for name, imp in zip(self.feature_names, importance)
        }


# Global GBT meta-learner instance
gbt_meta_learner = GBTMetaLearner()
