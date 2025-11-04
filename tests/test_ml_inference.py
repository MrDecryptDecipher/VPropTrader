"""Unit tests for ML model inference speed and accuracy"""

import pytest
import numpy as np
import time
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sidecar"))

from app.ml.model_manager import model_manager
from app.ml.inference import InferenceEngine


class TestMLInference:
    """Test ML model inference performance"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment"""
        # Load models
        await model_manager.load_models()
        self.inference_engine = InferenceEngine()
        yield
    
    def test_rf_inference_speed(self):
        """Test Random Forest inference speed < 1ms"""
        # Create dummy features
        features = np.random.randn(1, 50).astype(np.float32)
        
        # Warm up
        for _ in range(10):
            model_manager.rf_model.predict(features)
        
        # Time 100 inferences
        start = time.perf_counter()
        for _ in range(100):
            prediction = model_manager.rf_model.predict(features)
        elapsed = (time.perf_counter() - start) / 100 * 1000  # ms
        
        print(f"RF inference time: {elapsed:.3f}ms")
        assert elapsed < 1.0, f"RF inference too slow: {elapsed:.3f}ms"
        assert prediction is not None
    
    def test_lstm_inference_speed(self):
        """Test LSTM inference speed < 1ms"""
        # Create dummy sequence
        sequence = np.random.randn(1, 20, 50).astype(np.float32)
        
        # Warm up
        for _ in range(10):
            model_manager.lstm_model.predict(sequence)
        
        # Time 100 inferences
        start = time.perf_counter()
        for _ in range(100):
            prediction = model_manager.lstm_model.predict(sequence)
        elapsed = (time.perf_counter() - start) / 100 * 1000  # ms
        
        print(f"LSTM inference time: {elapsed:.3f}ms")
        assert elapsed < 1.0, f"LSTM inference too slow: {elapsed:.3f}ms"
        assert prediction is not None
    
    def test_gbt_inference_speed(self):
        """Test GBT inference speed < 1ms"""
        # Create dummy features
        features = np.random.randn(1, 10).astype(np.float32)
        
        # Warm up
        for _ in range(10):
            model_manager.gbt_model.predict(features)
        
        # Time 100 inferences
        start = time.perf_counter()
        for _ in range(100):
            prediction = model_manager.gbt_model.predict(features)
        elapsed = (time.perf_counter() - start) / 100 * 1000  # ms
        
        print(f"GBT inference time: {elapsed:.3f}ms")
        assert elapsed < 1.0, f"GBT inference too slow: {elapsed:.3f}ms"
        assert prediction is not None
    
    def test_full_inference_pipeline(self):
        """Test complete inference pipeline"""
        # Create dummy features
        features = {
            'z_close': 0.5,
            'z_high': 0.6,
            'z_low': 0.4,
            'ema_slope': 0.02,
            'rsi': 55.0,
            'rvol': 1.2,
            'atr_z': 0.3,
            'dxy_z': -0.1,
            'vix_z': 0.2,
            'sentiment': 0.3,
        }
        
        # Time full pipeline
        start = time.perf_counter()
        result = self.inference_engine.predict(features)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        
        print(f"Full pipeline time: {elapsed:.3f}ms")
        assert elapsed < 5.0, f"Pipeline too slow: {elapsed:.3f}ms"
        assert 'rf_pwin' in result
        assert 'lstm_sigma' in result
        assert 'lstm_direction' in result
        assert 0 <= result['rf_pwin'] <= 1
    
    def test_batch_inference(self):
        """Test batch inference performance"""
        # Create batch of features
        batch_size = 10
        features = np.random.randn(batch_size, 50).astype(np.float32)
        
        # Time batch inference
        start = time.perf_counter()
        predictions = model_manager.rf_model.predict(features)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        
        per_sample = elapsed / batch_size
        print(f"Batch inference: {elapsed:.3f}ms total, {per_sample:.3f}ms per sample")
        assert per_sample < 1.0, f"Batch inference too slow: {per_sample:.3f}ms per sample"
        assert len(predictions) == batch_size


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
