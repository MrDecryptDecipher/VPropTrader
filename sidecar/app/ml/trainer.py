"""ML Model Training Orchestrator"""

import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

from app.ml.random_forest import random_forest
from app.ml.lstm_model import lstm_model
from app.ml.model_manager import model_manager
from app.data.database import db


class ModelTrainer:
    """Orchestrates training of all ML models"""
    
    def __init__(self):
        self.min_samples = 100  # Minimum samples needed for training
        self.sequence_length = 20  # For LSTM
    
    async def prepare_training_data(self, limit: int = 5000) -> Optional[Dict]:
        """
        Prepare training data from database
        
        Args:
            limit: Maximum number of samples to fetch
        
        Returns:
            Dict with features, labels, sequences
        """
        try:
            logger.info(f"Preparing training data (limit: {limit})...")
            
            # Fetch closed trades from database
            query = """
                SELECT 
                    features_json,
                    exit_reason,
                    pnl,
                    timestamp
                FROM trades
                WHERE status = 'closed'
                AND features_json IS NOT NULL
                AND exit_reason IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT ?
            """
            
            rows = await db.fetch_all(query, (limit,))
            
            if not rows or len(rows) < self.min_samples:
                logger.warning(f"Insufficient training data: {len(rows) if rows else 0} samples")
                return None
            
            logger.info(f"Fetched {len(rows)} trades for training")
            
            # Parse features and labels
            import json
            
            features_list = []
            labels_list = []
            volatility_list = []
            direction_list = []
            
            for row in rows:
                try:
                    features = json.loads(row['features_json'])
                    
                    # Convert features dict to array (must match feature order)
                    feature_vector = self._dict_to_vector(features)
                    features_list.append(feature_vector)
                    
                    # Label: 1 if TP, 0 if SL
                    exit_reason = row['exit_reason']
                    label = 1 if exit_reason in ['TP1', 'TP2'] else 0
                    labels_list.append(label)
                    
                    # For LSTM: calculate realized volatility and direction
                    pnl = row['pnl'] or 0
                    # Simplified - in production, calculate from actual price movement
                    volatility = abs(pnl) / 100  # Normalize
                    direction = 1.0 if pnl > 0 else -1.0
                    
                    volatility_list.append(volatility)
                    direction_list.append(direction)
                    
                except Exception as e:
                    logger.debug(f"Error parsing trade data: {e}")
                    continue
            
            if len(features_list) < self.min_samples:
                logger.warning(f"Insufficient valid samples: {len(features_list)}")
                return None
            
            # Convert to numpy arrays
            X = np.array(features_list)
            y = np.array(labels_list)
            
            # Create sequences for LSTM
            sequences, seq_targets = self._create_sequences(
                X, 
                np.column_stack([volatility_list, direction_list])
            )
            
            data = {
                'X': X,
                'y': y,
                'sequences': sequences,
                'seq_targets': seq_targets,
                'n_samples': len(X),
            }
            
            logger.info(f"✓ Training data prepared: {len(X)} samples, {len(sequences)} sequences")
            
            return data
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}", exc_info=True)
            return None
    
    def _dict_to_vector(self, features: Dict) -> np.ndarray:
        """Convert features dict to ordered vector"""
        # Must match feature order from features.py
        feature_names = [
            'z_close', 'z_high', 'z_low', 'ema_slope', 'roc_5', 'roc_10',
            'rsi', 'price_position', 'm5_trend', 'm15_trend',
            'rvol', 'cvd', 'vwap_distance', 'volume_trend', 'vpin',
            'atr_z', 'bb_width', 'bb_position', 'realized_vol', 'vol_ratio',
            'dxy_z', 'vix_z', 'ust10y_z', 'ust2y_z', 'yield_curve',
            'sentiment',
            'corr_nas100', 'corr_xauusd', 'corr_eurusd',
            'regime_trend', 'regime_revert', 'regime_choppy',
        ]
        
        vector = np.array([features.get(name, 0.0) for name in feature_names])
        
        # Pad to 50 dimensions
        if len(vector) < 50:
            vector = np.pad(vector, (0, 50 - len(vector)), constant_values=0.0)
        
        return vector[:50]
    
    def _create_sequences(
        self, 
        features: np.ndarray, 
        targets: np.ndarray
    ) -> tuple:
        """Create sequences for LSTM training"""
        sequences = []
        seq_targets = []
        
        for i in range(len(features) - self.sequence_length):
            seq = features[i:i + self.sequence_length]
            target = targets[i + self.sequence_length]
            
            sequences.append(seq)
            seq_targets.append(target)
        
        return np.array(sequences), np.array(seq_targets)
    
    async def train_all_models(self, use_atomic_swap: bool = True) -> Dict[str, Dict]:
        """
        Train all ML models with optional atomic swap
        
        Args:
            use_atomic_swap: If True, use model manager for atomic swap
        
        Returns:
            Dict with metrics for each model
        """
        results = {}
        
        try:
            # Prepare data
            data = await self.prepare_training_data(limit=5000)
            
            if data is None:
                logger.warning("Cannot train models - insufficient data")
                return results
            
            if use_atomic_swap:
                # Use model manager for complete workflow with atomic swap
                training_data = {
                    'rf_X': data['X'],
                    'rf_y': data['y'],
                    'lstm_sequences': data['sequences'],
                    'lstm_targets': data['seq_targets'],
                    'n_features': 50,
                    'sequence_length': self.sequence_length,
                }
                
                success = model_manager.retrain_and_swap(training_data)
                
                if success:
                    results['status'] = 'success'
                    results['version'] = model_manager.current_version
                    logger.info(f"✓ Models retrained and swapped to v{model_manager.current_version}")
                else:
                    results['status'] = 'failed'
                    logger.error("Model retraining and swap failed")
                
            else:
                # Traditional training without atomic swap
                # Train Random Forest
                logger.info("Training Random Forest...")
                rf_metrics = random_forest.train(data['X'], data['y'])
                if rf_metrics:
                    random_forest.save()
                    results['random_forest'] = rf_metrics
                
                # Train LSTM
                logger.info("Training LSTM...")
                lstm_metrics = lstm_model.train(
                    data['sequences'],
                    data['seq_targets'],
                    epochs=50,
                    batch_size=32
                )
                if lstm_metrics:
                    lstm_model.save()
                    results['lstm'] = lstm_metrics
                
                logger.info("✓ All models trained successfully")
            
            # Log to database
            await self._log_retraining(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error training models: {e}", exc_info=True)
            return results
    
    async def _log_retraining(self, results: Dict):
        """Log retraining event to database"""
        try:
            import json
            
            for model_name, metrics in results.items():
                query = """
                    INSERT INTO model_retraining (
                        model_name,
                        trigger_reason,
                        samples_count,
                        train_accuracy,
                        val_accuracy,
                        train_loss,
                        val_loss
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                await db.execute(query, (
                    model_name,
                    'scheduled',
                    metrics.get('train_samples', 0) + metrics.get('val_samples', 0),
                    metrics.get('train_accuracy'),
                    metrics.get('val_accuracy'),
                    metrics.get('train_loss'),
                    metrics.get('val_loss'),
                ))
            
            logger.debug("Retraining logged to database")
            
        except Exception as e:
            logger.error(f"Error logging retraining: {e}")


# Global trainer instance
model_trainer = ModelTrainer()
