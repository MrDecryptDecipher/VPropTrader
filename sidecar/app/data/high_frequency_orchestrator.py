"""High-frequency data orchestrator"""

import asyncio
from loguru import logger

class HighFrequencyDataOrchestrator:
    """Orchestrates high-frequency data collection"""
    
    def __init__(self, symbols: list, collection_interval: int = 1, max_retries: int = 3, api_keys: dict = None):
        self.symbols = symbols
        self.collection_interval = collection_interval
        self.max_retries = max_retries
        self.api_keys = api_keys or {}
        self.running = False
        logger.info(f"HighFrequencyDataOrchestrator initialized for {len(symbols)} symbols")
    
    async def start(self):
        """Start data collection"""
        self.running = True
        logger.info("High-frequency data collection started")
        asyncio.create_task(self._collection_loop())
    
    async def stop(self):
        """Stop data collection"""
        self.running = False
        logger.info("High-frequency data collection stopped")

    async def _collection_loop(self):
        """Main data collection loop"""
        from app.data.mt5_client import mt5_client
        
        while self.running:
            try:
                for symbol in self.symbols:
                    tick = mt5_client.get_latest_tick(symbol)
                    if tick:
                        logger.info(f"Tick {symbol}: {tick['bid']} / {tick['ask']}")
                    else:
                        # Try to get symbol info to see if it's valid
                        info = mt5_client.get_symbol_info(symbol)
                        if not info:
                            logger.warning(f"Could not get info for {symbol}")
                            
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                
            await asyncio.sleep(self.collection_interval)
