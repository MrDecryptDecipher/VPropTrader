"""
MT5 Client Module
Handles connection and data retrieval from MetaTrader 5.
"""

import os
from loguru import logger
from app.core.config import settings

# Try to import MetaTrader5, handle failure for non-Windows environments
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 module not found. Install with 'pip install MetaTrader5'")

class MT5Client:
    """
    Wrapper for MetaTrader 5 API.
    """
    
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
            # logger.info("MT5 connected") # Reduce log spam
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

    def get_symbol_info(self, symbol: str):
        """Get symbol information"""
        if not self.connect():
            return None
        
        info = mt5.symbol_info(symbol)
        if info is None:
            logger.warning(f"Symbol {symbol} not found")
            return None
            
        if not info.visible:
            if not mt5.symbol_select(symbol, True):
                logger.warning(f"Symbol {symbol} not visible and cannot be selected")
                return None
                
        return info

    def get_latest_tick(self, symbol: str):
        """Get latest tick data"""
        if not self.connect():
            return None
            
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.warning(f"Tick data not available for {symbol}")
            return None
            
        return {
            'time': tick.time,
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'volume': tick.volume
        }

    def get_rates(self, symbol: str, timeframe, count: int = 100):
        """Get historical rates"""
        if not self.connect():
            return None
            
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            logger.warning(f"Rates not available for {symbol}")
            return None
            
        return rates

    def place_trade(self, symbol: str, action: str, volume: float, sl: float = 0.0, tp: float = 0.0, comment: str = ""):
        """Place a trade"""
        if not self.connect():
            return None
            
        order_type = mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).ask if action == 'BUY' else mt5.symbol_info_tick(symbol).bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.comment}")
            return None
            
        logger.info(f"Trade placed: {result.order}")
        return result._asdict()
    
    def timeframe_to_mt5(self, tf_str: str):
        """Convert string timeframe to MT5 constant"""
        if not MT5_AVAILABLE:
            return 15 # Default
            
        mapping = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        return mapping.get(tf_str, mt5.TIMEFRAME_M15)


# Global instance
mt5_client = MT5Client()
