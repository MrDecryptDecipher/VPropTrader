"""Bootstrap Model Trainer - Trains ML models automatically on startup"""

import numpy as np
import json
from pathlib import Path
from typing import Dict, Optional
from loguru import logger

from app.ml.random_forest import random_forest
from app.ml.lstm_model import lstm_model
from app.ml.onnx_exporter import onnx_exporter
from app.ml.trainer import model_trainer
from app.core import settings


class BootstrapTrainer:
    """
    Trains ML models automatically if not already trained
    
    Purpose: Enable immediate signal generation from day one
    """
    
    def __init__(self):
        self.model_path = Path(settings.model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.min_samples = 100
        self.sequence_length = 20
    
    async def train_if_needed(self) -> bool:
        """
        Check if models exist and train if not
        
        Returns:
            True if models are ready (existed or trained successfully)
        """
        try:
            logger.info("Checking if ML models need training...")
            
            # Check if ONNX models exist
            rf_onnx_path = self.model_path / "random_forest.onnx"
            lstm_onnx_path = self.model_path / "lstm_model.onnx"
            
            if rf_onnx_path.exists() and lstm_onnx_path.exists():
                logger.info("✓ ML models already exist, skipping training")
                return True
            
            logger.info("ML models not found, initiating training...")
            
            # Prepare training data
            training_data = await model_trainer.prepare_training_data(limit=5000)
            
            if not training_data:
                logger.error("Failed to prepare training data")
                return False
            
            logger.info(f"Training data prepared: {training_data['n_samples']} samples")
            
            # Train Random Forest
            logger.info("Training Random Forest model...")
            rf_metrics = await self.train_random_forest(
                training_data['X'],
                training_data['y']
            )
            
            if not rf_metrics:
                logger.error("Random Forest training failed")
                return False
            
            logger.info(f"✓ Random Forest trained: {rf_metrics['val_accuracy']:.1%} val accuracy")
            
            # Train LSTM
            logger.info("Training LSTM model...")
            lstm_metrics = await self.train_lstm(
                training_data['sequences'],
                training_data['seq_targets']
            )
            
            if not lstm_metrics:
                logger.error("LSTM training failed")
                return False
            
            logger.info(f"✓ LSTM trained: {lstm_metrics['val_loss']:.4f} val loss")
            
            # Export to ONNX
            logger.info("Exporting models to ONNX...")
            export_success = await self.export_to_onnx()
            
            if not export_success:
                logger.warning("⚠ ONNX export failed, will use native models")
            else:
                logger.info("✓ Models exported to ONNX")
            
            # Validate inference speed
            logger.info("Validating inference speed...")
            speed_ok = await self.validate_inference_speed()
            
            if not speed_ok:
                logger.warning("⚠ Inference speed validation failed")
            else:
                logger.info("✓ Inference speed validated (<1ms)")
            
            logger.info("✓ ML model training complete")
            return True
            
        except Exception as e:
            logger.error(f"Bootstrap training failed: {e}", exc_info=True)
            return False
    
    async def train_random_forest(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Optional[Dict]:
        """
        Train Random Forest classifier
        
        Args:
            X: Feature matrix (n_samples, 50)
            y: Labels (n_samples,) - 1 for TP, 0 for SL
        
        Returns:
            Dict with training metrics
        """
        try:
            # Train using existing random_forest module
            metrics = random_forest.train(X, y)
            
            if not metrics:
                return None
            
            # Save model
            random_forest.save()
            
            # Validate
            if metrics.get('val_accuracy', 0) < 0.50:
                logger.warning(f"Low validation accuracy: {metrics['val_accuracy']:.1%}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Random Forest training error: {e}", exc_info=True)
            return None
    
    async def train_lstm(
        self,
        sequences: np.ndarray,
        targets: np.ndarray
    ) -> Optional[Dict]:
        """
        Train LSTM model for volatility and direction forecasting
        
        Args:
            sequences: Sequence data (n_samples, sequence_length, 50)
            targets: Target values (n_samples, 2) - [volatility, direction]
        
        Returns:
            Dict with training metrics
        """
        try:
            # Train using existing lstm_model module
            metrics = lstm_model.train(
                sequences,
                targets,
                epochs=50,
                batch_size=32
            )
            
            if not metrics:
                return None
            
            # Save model
            lstm_model.save()
            
            # Validate
            if metrics.get('val_loss', 999) > 0.5:
                logger.warning(f"High validation loss: {metrics['val_loss']:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"LSTM training error: {e}", exc_info=True)
            return None
    
    async def export_to_onnx(self) -> bool:
        """
        Export trained models to ONNX format
        
        Returns:
            True if successful
        """
        try:
            # Export Random Forest
            rf_success = onnx_exporter.export_random_forest(random_forest.model)
            if not rf_success:
                logger.error("Random Forest ONNX export failed")
                return False
            
            # Export LSTM
            lstm_success = onnx_exporter.export_lstm(lstm_model.model)
            if not lstm_success:
                logger.error("LSTM ONNX export failed")
                return False
            
            # Save metadata
            onnx_exporter.save_metadata({
                'rf_features': 50,
                'lstm_sequence_length': self.sequence_length,
                'lstm_features': 50,
                'export_timestamp': str(np.datetime64('now')),
            })
            
            return True
            
        except Exception as e:
            logger.error(f"ONNX export error: {e}", exc_info=True)
            return False
    
    async def validate_inference_speed(self) -> bool:
        """
        Validate that inference speed is < 1ms
        
        Returns:
            True if inference is fast enough
        """
        try:
            # Load ONNX models
            onnx_loaded = onnx_exporter.load_onnx_models()
            if not onnx_loaded:
                logger.warning("ONNX models not loaded, skipping speed validation")
                return False
            
            # Benchmark
            benchmark = onnx_exporter.benchmark_inference_speed(n_iterations=100)
            
            total_time = benchmark.get('total_avg_ms', 999)
            
            if total_time < 1.0:
                logger.info(f"✓ Inference speed: {total_time:.4f}ms (target: <1ms)")
                return True
            else:
                logger.warning(f"⚠ Inference speed: {total_time:.4f}ms (target: <1ms)")
                return False
            
        except Exception as e:
            logger.error(f"Speed validation error: {e}")
            return False
    
    def get_training_status(self) -> Dict:
        """
        Get current training status
        
        Returns:
            Dict with status information
        """
        rf_onnx_path = self.model_path / "random_forest.onnx"
        lstm_onnx_path = self.model_path / "lstm_model.onnx"
        rf_pkl_path = self.model_path / "random_forest.pkl"
        lstm_pt_path = self.model_path / "lstm_model.pt"
        
        return {
            'models_path': str(self.model_path),
            'rf_onnx_exists': rf_onnx_path.exists(),
            'lstm_onnx_exists': lstm_onnx_path.exists(),
            'rf_native_exists': rf_pkl_path.exists(),
            'lstm_native_exists': lstm_pt_path.exists(),
            'ready_for_inference': (
                (rf_onnx_path.exists() or rf_pkl_path.exists()) and
                (lstm_onnx_path.exists() or lstm_pt_path.exists())
            )
        }


# Global bootstrap trainer instance
bootstrap_trainer = BootstrapTrainer()
