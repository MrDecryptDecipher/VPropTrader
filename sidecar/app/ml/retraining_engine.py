"""Model Retraining Engine with Drift Detection"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger
import numpy as np
from scipy.stats import ks_2samp

from app.ml.trainer import ModelTrainer
from app.ml.drift_detector import DriftDetector
from app.ml.model_manager import model_manager
from app.memory.long_term_memory import long_term_memory
from app.core.config import settings


class RetrainingEngine:
    """
    Handles nightly model retraining and drift-triggered retraining
    """
    
    def __init__(self):
        self.trainer = ModelTrainer()
        self.drift_detector = DriftDetector()
        self.last_retrain_time: Optional[datetime] = None
        self.retrain_history: list = []
        self.is_retraining = False
        
        # Retraining parameters
        self.min_samples = 1000  # Minimum samples needed for retraining
        self.target_samples = 5000  # Target number of samples
        self.drift_check_interval = 3600  # Check drift every hour
        self.last_drift_check: Optional[datetime] = None
    
    async def nightly_retrain(self) -> Dict:
        """
        Perform nightly model retraining
        
        Returns:
            Dict with retraining results and metrics
        """
        if self.is_retraining:
            logger.warning("Retraining already in progress, skipping")
            return {'status': 'skipped', 'reason': 'already_retraining'}
        
        try:
            self.is_retraining = True
            logger.info("Starting nightly model retraining")
            
            # Get training data from long-term memory
            X, y = await long_term_memory.get_training_data(
                limit=self.target_samples
            )
            
            if len(X) < self.min_samples:
                logger.warning(
                    f"Insufficient training data: {len(X)} < {self.min_samples}"
                )
                return {
                    'status': 'skipped',
                    'reason': 'insufficient_data',
                    'samples': len(X)
                }
            
            logger.info(f"Training with {len(X)} samples")
            
            # Train Random Forest
            logger.info("Training Random Forest model...")
            rf_metrics = await self.trainer.train_random_forest(X, y)
            
            # Train LSTM
            logger.info("Training LSTM model...")
            lstm_metrics = await self.trainer.train_lstm(X, y)
            
            # Check if we should train GBT (weekly)
            gbt_metrics = None
            if self._should_train_gbt():
                logger.info("Training Gradient Boosted Tree meta-learner...")
                gbt_metrics = await self.trainer.train_gbt(X, y)
            
            # Export models to ONNX
            logger.info("Exporting models to ONNX...")
            export_success = await self.trainer.export_all_models()
            
            if not export_success:
                logger.error("Failed to export models to ONNX")
                return {
                    'status': 'failed',
                    'reason': 'export_failed'
                }
            
            # Validate inference speed
            logger.info("Validating inference speed...")
            inference_valid = await self._validate_inference_speed()
            
            if not inference_valid:
                logger.error("Inference speed validation failed")
                return {
                    'status': 'failed',
                    'reason': 'inference_too_slow'
                }
            
            # Atomic model swap
            logger.info("Performing atomic model swap...")
            swap_success = await model_manager.reload_models()
            
            if not swap_success:
                logger.error("Model swap failed")
                return {
                    'status': 'failed',
                    'reason': 'swap_failed'
                }
            
            # Update retraining history
            self.last_retrain_time = datetime.utcnow()
            
            result = {
                'status': 'success',
                'timestamp': self.last_retrain_time.isoformat(),
                'samples': len(X),
                'rf_metrics': rf_metrics,
                'lstm_metrics': lstm_metrics,
                'gbt_metrics': gbt_metrics,
                'inference_validated': True,
            }
            
            self.retrain_history.append(result)
            
            # Keep only last 30 retraining records
            if len(self.retrain_history) > 30:
                self.retrain_history = self.retrain_history[-30:]
            
            logger.info(f"Nightly retraining completed successfully")
            logger.info(f"RF Accuracy: {rf_metrics.get('accuracy', 0):.3f}")
            logger.info(f"LSTM Val Loss: {lstm_metrics.get('val_loss', 0):.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during nightly retraining: {e}", exc_info=True)
            return {
                'status': 'failed',
                'reason': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        finally:
            self.is_retraining = False
    
    async def check_and_retrain_on_drift(self) -> Optional[Dict]:
        """
        Check for distribution drift and trigger retraining if needed
        
        Returns:
            Retraining results if triggered, None otherwise
        """
        try:
            # Rate limit drift checks
            if self.last_drift_check:
                elapsed = (datetime.utcnow() - self.last_drift_check).total_seconds()
                if elapsed < self.drift_check_interval:
                    return None
            
            self.last_drift_check = datetime.utcnow()
            
            logger.info("Checking for distribution drift...")
            
            # Get recent and historical data
            recent_cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
            historical_cutoff = (datetime.utcnow() - timedelta(days=60)).isoformat()
            
            X_recent, _ = await long_term_memory.get_training_data(
                limit=500,
                min_date=recent_cutoff
            )
            
            X_historical, _ = await long_term_memory.get_training_data(
                limit=2000,
                min_date=historical_cutoff
            )
            
            if len(X_recent) < 100 or len(X_historical) < 500:
                logger.debug("Insufficient data for drift detection")
                return None
            
            # Perform KS test on each feature
            drift_detected = False
            drift_features = []
            
            for i in range(X_recent.shape[1]):
                ks_stat, p_value = ks_2samp(X_recent[:, i], X_historical[:, i])
                
                if p_value < 0.01:  # Significant drift
                    drift_detected = True
                    drift_features.append({
                        'feature_idx': i,
                        'ks_stat': float(ks_stat),
                        'p_value': float(p_value)
                    })
            
            # Check autoencoder reconstruction error
            ae_drift = await self.drift_detector.detect_drift(X_recent)
            
            if ae_drift['drift_detected']:
                drift_detected = True
                logger.warning(
                    f"Autoencoder drift detected: "
                    f"error={ae_drift['reconstruction_error']:.4f}, "
                    f"threshold={ae_drift['threshold']:.4f}"
                )
            
            if drift_detected:
                logger.warning(
                    f"Distribution drift detected! "
                    f"Features with drift: {len(drift_features)}"
                )
                
                # Trigger emergency retraining
                logger.info("Triggering drift-based retraining...")
                result = await self.nightly_retrain()
                
                result['trigger'] = 'drift'
                result['drift_features'] = drift_features
                result['ae_drift'] = ae_drift
                
                return result
            
            else:
                logger.info("No significant drift detected")
                return None
            
        except Exception as e:
            logger.error(f"Error checking drift: {e}", exc_info=True)
            return None
    
    def _should_train_gbt(self) -> bool:
        """Check if GBT should be trained (weekly)"""
        if not self.last_retrain_time:
            return True
        
        # Train GBT once per week
        days_since_retrain = (datetime.utcnow() - self.last_retrain_time).days
        return days_since_retrain >= 7
    
    async def _validate_inference_speed(self) -> bool:
        """Validate that inference speed is < 1ms"""
        try:
            # Create dummy input
            dummy_features = np.random.randn(1, 50).astype(np.float32)
            
            # Time RF inference
            import time
            start = time.perf_counter()
            for _ in range(100):
                _ = model_manager.rf_model.predict(dummy_features)
            rf_time = (time.perf_counter() - start) / 100 * 1000  # ms
            
            # Time LSTM inference
            dummy_sequence = np.random.randn(1, 20, 50).astype(np.float32)
            start = time.perf_counter()
            for _ in range(100):
                _ = model_manager.lstm_model.predict(dummy_sequence)
            lstm_time = (time.perf_counter() - start) / 100 * 1000  # ms
            
            logger.info(f"Inference times - RF: {rf_time:.2f}ms, LSTM: {lstm_time:.2f}ms")
            
            # Both should be < 1ms
            return rf_time < 1.0 and lstm_time < 1.0
            
        except Exception as e:
            logger.error(f"Error validating inference speed: {e}")
            return False
    
    def get_retrain_history(self, limit: int = 10) -> list:
        """Get recent retraining history"""
        return self.retrain_history[-limit:]
    
    def get_last_retrain_info(self) -> Optional[Dict]:
        """Get info about last retraining"""
        if not self.retrain_history:
            return None
        return self.retrain_history[-1]


# Global retraining engine instance
retraining_engine = RetrainingEngine()


async def schedule_nightly_retrain():
    """
    Background task to run nightly retraining
    Should be called at startup to schedule retraining
    """
    while True:
        try:
            # Calculate time until next 2 AM UTC
            now = datetime.utcnow()
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            
            if next_run <= now:
                next_run += timedelta(days=1)
            
            wait_seconds = (next_run - now).total_seconds()
            
            logger.info(f"Next retraining scheduled for {next_run} UTC")
            logger.info(f"Waiting {wait_seconds/3600:.1f} hours...")
            
            await asyncio.sleep(wait_seconds)
            
            # Run retraining
            result = await retraining_engine.nightly_retrain()
            logger.info(f"Nightly retraining result: {result['status']}")
            
        except Exception as e:
            logger.error(f"Error in retraining scheduler: {e}", exc_info=True)
            # Wait 1 hour before retrying
            await asyncio.sleep(3600)


async def schedule_drift_checks():
    """
    Background task to periodically check for drift
    """
    while True:
        try:
            # Check every hour
            await asyncio.sleep(3600)
            
            result = await retraining_engine.check_and_retrain_on_drift()
            
            if result:
                logger.info(f"Drift-triggered retraining: {result['status']}")
            
        except Exception as e:
            logger.error(f"Error in drift check scheduler: {e}", exc_info=True)
            await asyncio.sleep(3600)
