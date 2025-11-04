"""Random Forest V4 - TP/SL Classification Model"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
from pathlib import Path
from typing import Tuple, Optional, Dict
from loguru import logger
from app.core import settings


class RandomForestModel:
    """Random Forest classifier for TP vs SL prediction"""
    
    def __init__(self):
        self.model = None
        self.feature_importance = None
        self.model_path = Path(settings.model_path) / "random_forest_v4.pkl"
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, float]:
        """
        Train Random Forest model
        
        Args:
            X: Feature matrix (n_samples, 50)
            y: Labels (1 = TP, 0 = SL)
            test_size: Validation split ratio
            random_state: Random seed
        
        Returns:
            Dict with training metrics
        """
        try:
            logger.info(f"Training Random Forest on {len(X)} samples...")
            
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
            
            # Create model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=random_state,
                n_jobs=-1,
                verbose=0
            )
            
            # Train
            self.model.fit(X_train, y_train)
            
            # Evaluate
            train_pred = self.model.predict(X_train)
            val_pred = self.model.predict(X_val)
            
            train_acc = accuracy_score(y_train, train_pred)
            val_acc = accuracy_score(y_val, val_pred)
            
            # Feature importance
            self.feature_importance = self.model.feature_importances_
            
            # Get probability predictions
            train_proba = self.model.predict_proba(X_train)[:, 1]
            val_proba = self.model.predict_proba(X_val)[:, 1]
            
            metrics = {
                "train_accuracy": float(train_acc),
                "val_accuracy": float(val_acc),
                "train_samples": len(X_train),
                "val_samples": len(X_val),
                "n_features": X.shape[1],
            }
            
            logger.info(f"✓ Random Forest trained - Train Acc: {train_acc:.4f}, Val Acc: {val_acc:.4f}")
            
            # Print classification report
            logger.debug("\nValidation Classification Report:")
            logger.debug(classification_report(y_val, val_pred, target_names=['SL', 'TP']))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training Random Forest: {e}", exc_info=True)
            return {}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels
        
        Args:
            X: Feature matrix
        
        Returns:
            Predicted labels (1 = TP, 0 = SL)
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities
        
        Args:
            X: Feature matrix
        
        Returns:
            Probability of TP (P_win)
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Return probability of class 1 (TP)
        return self.model.predict_proba(X)[:, 1]
    
    def save(self) -> bool:
        """Save model to disk"""
        if self.model is None:
            logger.warning("No model to save")
            return False
        
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'feature_importance': self.feature_importance
                }, f)
            
            logger.info(f"✓ Random Forest saved to {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Random Forest: {e}")
            return False
    
    def load(self) -> bool:
        """Load model from disk"""
        if not self.model_path.exists():
            logger.warning(f"Model file not found: {self.model_path}")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
            
            self.model = data['model']
            self.feature_importance = data.get('feature_importance')
            
            logger.info(f"✓ Random Forest loaded from {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading Random Forest: {e}")
            return False
    
    def get_feature_importance(self, top_n: int = 10) -> Dict[int, float]:
        """Get top N most important features"""
        if self.feature_importance is None:
            return {}
        
        # Get indices of top features
        indices = np.argsort(self.feature_importance)[::-1][:top_n]
        
        return {
            int(idx): float(self.feature_importance[idx])
            for idx in indices
        }


# Global Random Forest instance
random_forest = RandomForestModel()
