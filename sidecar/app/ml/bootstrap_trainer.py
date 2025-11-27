"""Bootstrap ML model trainer"""

from loguru import logger


class BootstrapTrainer:
    """Trains ML models from bootstrap data"""
    
    def __init__(self):
        logger.info("BootstrapTrainer initialized")
    
    async def train_if_needed(self) -> bool:
        """Train models if needed"""
        logger.info("ML training skipped (stub implementation)")
        return True
    
    def get_training_status(self) -> dict:
        """Get training status"""
        return {
            "rf_onnx_exists": False,
            "lstm_onnx_exists": False,
            "rf_native_exists": False,
            "lstm_native_exists": False
        }


# Global instance
bootstrap_trainer = BootstrapTrainer()
