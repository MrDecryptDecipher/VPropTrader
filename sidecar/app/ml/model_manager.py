"""ML model manager"""

from loguru import logger


class ModelManager:
    """Manages ML model loading and inference"""
    
    def __init__(self):
        self.models = {}
        logger.info("ModelManager initialized")
    
    async def load_models(self) -> bool:
        """Load ML models"""
        logger.info("ML models loading skipped (stub implementation)")
        return True


# Global instance
model_manager = ModelManager()
