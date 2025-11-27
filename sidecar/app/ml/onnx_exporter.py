import numpy as np
import joblib
import json
import pickle
import time
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any
from loguru import logger
from app.core import settings

try:
    import onnxruntime as ort
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType
    ONNX_AVAILABLE = True
except ImportError:
    logger.warning("ONNX/ONNXRuntime not available. ML inference will run in fallback mode.")
    ONNX_AVAILABLE = False
    ort = None

class ONNXExporter:
    """
    Handles exporting trained models to ONNX format for high-performance inference.
    """
    def __init__(self):
        self.onnx_dir = Path(settings.models_dir) / "onnx"
        self.onnx_dir.mkdir(parents=True, exist_ok=True)
        
        self.rf_onnx_path = self.onnx_dir / "random_forest.onnx"
        self.lstm_onnx_path = self.onnx_dir / "lstm_transformer.onnx"
        
        self.rf_session = None
        self.lstm_session = None
        
        self.metadata = {}
        
        # Try to load existing sessions
        if ONNX_AVAILABLE:
            self.load_sessions()
    
    def export_random_forest(self, model_path: Path = None, n_features: int = 50) -> bool:
        """
        Convert scikit-learn Random Forest to ONNX
        """
        if not ONNX_AVAILABLE:
            logger.warning("Cannot export RF: ONNX not available")
            return False

        try:
            if model_path is None:
                model_path = Path(settings.models_dir) / "random_forest.joblib"
            
            if not model_path.exists():
                logger.warning(f"RF model not found at {model_path}")
                return False
            
            # Load sklearn model
            rf_model = joblib.load(model_path)
            
            # Define input type
            initial_type = [('float_input', FloatTensorType([None, n_features]))]
            
            # Convert
            onnx_model = convert_sklearn(rf_model, initial_types=initial_type)
            
            # Save
            with open(self.rf_onnx_path, "wb") as f:
                f.write(onnx_model.SerializeToString())
            
            logger.info(f"✓ Random Forest exported to {self.rf_onnx_path}")
            
            # Update metadata
            self.metadata['random_forest'] = {
                'exported_at': time.time(),
                'n_features': n_features,
                'path': str(self.rf_onnx_path)
            }
            
            # Reload session
            self.load_sessions()
            return True
            
        except Exception as e:
            logger.error(f"Error exporting RF to ONNX: {e}", exc_info=True)
            return False

    def export_lstm(self, model_wrapper=None, sequence_length: int = 20, n_features: int = 50) -> bool:
        """
        Export PyTorch LSTM/Transformer to ONNX
        """
        if not ONNX_AVAILABLE:
            logger.warning("Cannot export LSTM: ONNX not available")
            return False

        try:
            import torch
            
            if model_wrapper is None:
                # Need the actual model instance to export
                logger.warning("Model wrapper instance required for LSTM export")
                return False
            
            model = model_wrapper.model
            if model is None:
                return False
            
            model.eval()
            
            # Create dummy input
            dummy_input = torch.randn(1, sequence_length, n_features)
            
            # Export
            torch.onnx.export(
                model,
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
            
            logger.info(f"✓ LSTM/Transformer exported to {self.lstm_onnx_path}")
            
            # Update metadata
            self.metadata['lstm'] = {
                'exported_at': time.time(),
                'sequence_length': sequence_length,
                'n_features': n_features,
                'path': str(self.lstm_onnx_path)
            }
            
            # Reload session
            self.load_sessions()
            return True
            
        except Exception as e:
            logger.error(f"Error exporting LSTM to ONNX: {e}", exc_info=True)
            return False
    
    def load_sessions(self) -> bool:
        """Load ONNX inference sessions"""
        if not ONNX_AVAILABLE:
            return False

        try:
            success = True
            
            if self.rf_onnx_path.exists():
                self.rf_session = ort.InferenceSession(
                    str(self.rf_onnx_path),
                    providers=['CPUExecutionProvider']
                )
                logger.info(f"✓ RF ONNX session loaded")
            else:
                logger.warning(f"RF ONNX not found: {self.rf_onnx_path}")
                success = False
            
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
        """
        if not ONNX_AVAILABLE or self.rf_session is None:
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
        """
        if not ONNX_AVAILABLE or self.lstm_session is None:
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
        """
        if not ONNX_AVAILABLE:
            return {}

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
        """
        if not ONNX_AVAILABLE:
            logger.warning("Cannot export models: ONNX not available")
            return False

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
