"""ONNX Model Export and Validation"""

import numpy as np
import onnx
import onnxruntime as ort
from pathlib import Path
from typing import Dict, Optional, Tuple
from loguru import logger
import time
import pickle

# For sklearn to ONNX
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

# For PyTorch to ONNX
import torch

from app.core import settings
from app.ml.random_forest import random_forest
from app.ml.lstm_model import lstm_model


class ONNXExporter:
    """Handles ONNX export and validation for all models"""
    
    def __init__(self):
        self.onnx_dir = Path(settings.model_path) / "onnx"
        self.onnx_dir.mkdir(parents=True, exist_ok=True)
        
        self.rf_onnx_path = self.onnx_dir / "random_forest_v4.onnx"
        self.lstm_onnx_path = self.onnx_dir / "lstm_2head.onnx"
        
        # ONNX Runtime sessions
        self.rf_session = None
        self.lstm_session = None
        
        # Model metadata
        self.metadata = {}
    
    def export_random_forest(self, n_features: int = 50) -> bool:
        """
        Export Random Forest to ONNX format
        
        Args:
            n_features: Number of input features
        
        Returns:
            True if export successful
        """
        try:
            if random_forest.model is None:
                logger.error("Random Forest model not trained or loaded")
                return False
            
            logger.info("Exporting Random Forest to ONNX...")
            
            # Define input type
            initial_type = [('float_input', FloatTensorType([None, n_features]))]
            
            # Convert to ONNX
            onnx_model = convert_sklearn(
                random_forest.model,
                initial_types=initial_type,
                target_opset=12,
                options={
                    'zipmap': False,  # Don't use ZipMap for probabilities
                }
            )
            
            # Save ONNX model
            onnx.save_model(onnx_model, str(self.rf_onnx_path))
            
            # Validate
            if not self._validate_onnx_model(self.rf_onnx_path):
                logger.error("Random Forest ONNX validation failed")
                return False
            
            # Store metadata
            self.metadata['random_forest'] = {
                'n_features': n_features,
                'n_estimators': random_forest.model.n_estimators,
                'max_depth': random_forest.model.max_depth,
                'export_time': time.time(),
            }
            
            logger.info(f"✓ Random Forest exported to {self.rf_onnx_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting Random Forest to ONNX: {e}", exc_info=True)
            return False
    
    def export_lstm(self, sequence_length: int = 20, n_features: int = 50) -> bool:
        """
        Export LSTM to ONNX format
        
        Args:
            sequence_length: Length of input sequences
            n_features: Number of features per timestep
        
        Returns:
            True if export successful
        """
        try:
            if lstm_model.model is None:
                logger.error("LSTM model not trained or loaded")
                return False
            
            logger.info("Exporting LSTM to ONNX...")
            
            # Set model to eval mode
            lstm_model.model.eval()
            
            # Create dummy input
            dummy_input = torch.randn(1, sequence_length, n_features).to(lstm_model.device)
            
            # Export to ONNX
            torch.onnx.export(
                lstm_model.model,
                dummy_input,
                str(self.lstm_onnx_path),
                export_params=True,
                opset_version=12,
                do_constant_folding=True,
                input_names=['input'],
                output_names=['volatility', 'direction'],
                dynamic_axes={
                    'input': {0: 'batch_size'},
                    'volatility': {0: 'batch_size'},
                    'direction': {0: 'batch_size'}
                }
            )
            
            # Validate
            if not self._validate_onnx_model(self.lstm_onnx_path):
                logger.error("LSTM ONNX validation failed")
                return False
            
            # Store metadata
            self.metadata['lstm'] = {
                'sequence_length': sequence_length,
                'n_features': n_features,
                'hidden_size': lstm_model.model.lstm.hidden_size,
                'num_layers': lstm_model.model.lstm.num_layers,
                'export_time': time.time(),
            }
            
            logger.info(f"✓ LSTM exported to {self.lstm_onnx_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting LSTM to ONNX: {e}", exc_info=True)
            return False
    
    def _validate_onnx_model(self, model_path: Path) -> bool:
        """Validate ONNX model structure"""
        try:
            onnx_model = onnx.load(str(model_path))
            onnx.checker.check_model(onnx_model)
            logger.debug(f"✓ ONNX model validation passed: {model_path.name}")
            return True
        except Exception as e:
            logger.error(f"ONNX validation error: {e}")
            return False
    
    def load_onnx_models(self) -> bool:
        """Load ONNX models into ONNX Runtime sessions"""
        try:
            success = True
            
            # Load Random Forest
            if self.rf_onnx_path.exists():
                self.rf_session = ort.InferenceSession(
                    str(self.rf_onnx_path),
                    providers=['CPUExecutionProvider']
                )
                logger.info(f"✓ Random Forest ONNX session loaded")
            else:
                logger.warning(f"Random Forest ONNX not found: {self.rf_onnx_path}")
                success = False
            
            # Load LSTM
            if self.lstm_onnx_path.exists():
                self.lstm_session = ort.InferenceSession(
                    str(self.lstm_onnx_path),
                    providers=['CPUExecutionProvider']
                )
                logger.info(f"✓ LSTM ONNX session loaded")
            else:
                logger.warning(f"LSTM ONNX not found: {self.lstm_onnx_path}")
                success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error loading ONNX models: {e}", exc_info=True)
            return False
    
    def predict_rf_onnx(self, X: np.ndarray) -> np.ndarray:
        """
        Run Random Forest inference using ONNX
        
        Args:
            X: Feature matrix (n_samples, n_features)
        
        Returns:
            Probability of TP (P_win) for each sample
        """
        if self.rf_session is None:
            raise ValueError("Random Forest ONNX session not loaded")
        
        try:
            # Ensure correct dtype and shape
            X = X.astype(np.float32)
            if len(X.shape) == 1:
                X = X.reshape(1, -1)
            
            # Get input name
            input_name = self.rf_session.get_inputs()[0].name
            
            # Run inference
            outputs = self.rf_session.run(None, {input_name: X})
            
            # outputs[0] is labels, outputs[1] is probabilities
            # Return probability of class 1 (TP)
            probabilities = outputs[1]
            
            # Extract P(class=1)
            if len(probabilities.shape) == 2:
                p_win = probabilities[:, 1]
            else:
                p_win = probabilities
            
            return p_win
            
        except Exception as e:
            logger.error(f"Error in RF ONNX inference: {e}", exc_info=True)
            raise
    
    def predict_lstm_onnx(self, sequence: np.ndarray) -> Tuple[float, float]:
        """
        Run LSTM inference using ONNX
        
        Args:
            sequence: Input sequence (sequence_length, n_features) or (1, sequence_length, n_features)
        
        Returns:
            (volatility_forecast, direction_forecast)
        """
        if self.lstm_session is None:
            raise ValueError("LSTM ONNX session not loaded")
        
        try:
            # Ensure correct dtype and shape
            sequence = sequence.astype(np.float32)
            if len(sequence.shape) == 2:
                sequence = sequence.reshape(1, sequence.shape[0], sequence.shape[1])
            
            # Get input name
            input_name = self.lstm_session.get_inputs()[0].name
            
            # Run inference
            outputs = self.lstm_session.run(None, {input_name: sequence})
            
            # outputs[0] is volatility, outputs[1] is direction
            volatility = float(outputs[0][0][0])
            direction = float(outputs[1][0][0])
            
            return volatility, direction
            
        except Exception as e:
            logger.error(f"Error in LSTM ONNX inference: {e}", exc_info=True)
            raise
    
    def benchmark_inference_speed(self, n_iterations: int = 1000) -> Dict[str, float]:
        """
        Benchmark ONNX inference speed
        
        Args:
            n_iterations: Number of inference iterations
        
        Returns:
            Dict with timing statistics
        """
        results = {}
        
        # Benchmark Random Forest
        if self.rf_session is not None:
            try:
                n_features = self.metadata.get('random_forest', {}).get('n_features', 50)
                X_dummy = np.random.randn(1, n_features).astype(np.float32)
                
                # Warmup
                for _ in range(10):
                    self.predict_rf_onnx(X_dummy)
                
                # Benchmark
                start_time = time.perf_counter()
                for _ in range(n_iterations):
                    self.predict_rf_onnx(X_dummy)
                elapsed = time.perf_counter() - start_time
                
                avg_time_ms = (elapsed / n_iterations) * 1000
                results['rf_avg_ms'] = avg_time_ms
                results['rf_throughput'] = n_iterations / elapsed
                
                logger.info(f"Random Forest ONNX: {avg_time_ms:.4f} ms/inference")
                
            except Exception as e:
                logger.error(f"Error benchmarking RF: {e}")
        
        # Benchmark LSTM
        if self.lstm_session is not None:
            try:
                seq_len = self.metadata.get('lstm', {}).get('sequence_length', 20)
                n_features = self.metadata.get('lstm', {}).get('n_features', 50)
                seq_dummy = np.random.randn(1, seq_len, n_features).astype(np.float32)
                
                # Warmup
                for _ in range(10):
                    self.predict_lstm_onnx(seq_dummy)
                
                # Benchmark
                start_time = time.perf_counter()
                for _ in range(n_iterations):
                    self.predict_lstm_onnx(seq_dummy)
                elapsed = time.perf_counter() - start_time
                
                avg_time_ms = (elapsed / n_iterations) * 1000
                results['lstm_avg_ms'] = avg_time_ms
                results['lstm_throughput'] = n_iterations / elapsed
                
                logger.info(f"LSTM ONNX: {avg_time_ms:.4f} ms/inference")
                
            except Exception as e:
                logger.error(f"Error benchmarking LSTM: {e}")
        
        # Total inference time
        if 'rf_avg_ms' in results and 'lstm_avg_ms' in results:
            results['total_avg_ms'] = results['rf_avg_ms'] + results['lstm_avg_ms']
            
            if results['total_avg_ms'] < 1.0:
                logger.info(f"✓ Total inference time: {results['total_avg_ms']:.4f} ms (< 1ms target)")
            else:
                logger.warning(f"⚠ Total inference time: {results['total_avg_ms']:.4f} ms (> 1ms target)")
        
        return results
    
    def save_metadata(self) -> bool:
        """Save model metadata"""
        try:
            metadata_path = self.onnx_dir / "metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.info(f"✓ Metadata saved to {metadata_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            return False
    
    def load_metadata(self) -> bool:
        """Load model metadata"""
        try:
            metadata_path = self.onnx_dir / "metadata.pkl"
            if not metadata_path.exists():
                logger.warning("Metadata file not found")
                return False
            
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            logger.info(f"✓ Metadata loaded from {metadata_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return False
    
    def export_all_models(self, n_features: int = 50, sequence_length: int = 20) -> bool:
        """
        Export all models to ONNX
        
        Args:
            n_features: Number of input features
            sequence_length: LSTM sequence length
        
        Returns:
            True if all exports successful
        """
        logger.info("=== Exporting all models to ONNX ===")
        
        rf_success = self.export_random_forest(n_features=n_features)
        lstm_success = self.export_lstm(sequence_length=sequence_length, n_features=n_features)
        
        if rf_success and lstm_success:
            self.save_metadata()
            logger.info("✓ All models exported to ONNX successfully")
            return True
        else:
            logger.error("⚠ Some models failed to export")
            return False


# Global ONNX exporter instance
onnx_exporter = ONNXExporter()
