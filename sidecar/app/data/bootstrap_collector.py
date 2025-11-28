"""Bootstrap data collector"""

from loguru import logger


class BootstrapCollector:
    """Collects bootstrap data for ML training"""
    
    def __init__(self):
        logger.info("BootstrapCollector initialized")
    
    async def run_bootstrap(self) -> bool:
        """Run bootstrap data collection"""
        logger.info("Bootstrap collection skipped (stub implementation)")
        return True
    
    async def get_data_quality_metrics(self) -> dict:
        """Get data quality metrics"""
        return {
            "total_bars": 0,
            "real_bars": 0,
            "synthetic_bars": 0,
            "synthetic_percentage": 0.0
        }


# Global instance
bootstrap_collector = BootstrapCollector()
