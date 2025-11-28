"""MetaTrader 5 client for data collection"""

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

from loguru import logger
from app.core import settings


class MT5Client:
    """MT5 client for market data"""
    
    def __init__(self):
        self.connected = False
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 module not installed. Running without MT5 data.")
        logger.info("MT5Client initialized")
    
    def connect(self):
        """Connect to MT5"""
        if not MT5_AVAILABLE:
            logger.warning("MT5 not available. Running without MT5 data.")
            return False
        
        try:
            if not mt5.initialize():
                logger.warning("MT5 not available. Running without MT5 data.")
                return False
            
            self.connected = True
            logger.info("MT5 connected")
            return True
        except Exception as e:
            logger.warning(f"MT5 connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected and MT5_AVAILABLE:
            mt5.shutdown()
            self.connected = False
            logger.info("MT5 disconnected")


# Global instance
mt5_client = MT5Client()
