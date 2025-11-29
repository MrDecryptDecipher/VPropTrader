import asyncio
from loguru import logger
from app.core.config import settings

class HighFrequencyDataOrchestrator:
    """
    Orchestrates data collection from MT5.
    """
    
    def __init__(self, symbols: list[str], collection_interval: float = 1.0):
        self.symbols = symbols
        self.collection_interval = collection_interval
        self.running = False
        self.task = None
        logger.info(f"Data Orchestrator initialized for {len(symbols)} symbols")

    async def start(self):
        """Start data collection"""
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._collection_loop())
        logger.info("High-frequency data collection started")

    async def stop(self):
        """Stop data collection"""
        self.running = False
        logger.info("High-frequency data collection stopped")

    async def _collection_loop(self):
        """Main data collection loop"""
        from app.data.mt5_client import mt5_client
        from app.agents.vision_agent import VisionAgent
        
        vision_agent = VisionAgent()
        last_scan = {} # Track last scan time per symbol
        scan_interval = 900 # 15 minutes
        
        while self.running:
            try:
                current_time = asyncio.get_event_loop().time()
                
                for symbol in self.symbols:
                    # 1. High Frequency Tick Data
                    tick = mt5_client.get_latest_tick(symbol)
                    if tick:
                        # logger.info(f"Tick {symbol}: {tick['bid']} / {tick['ask']}") # Reduce spam
                        pass
                    
                    # 2. Low Frequency Vision Scan
                    last_time = last_scan.get(symbol, 0)
                    if current_time - last_time > scan_interval:
                        logger.info(f"👁️ Scanning {symbol} with Vision Agent...")
                        # Run in thread pool to avoid blocking the loop
                        result = await asyncio.to_thread(vision_agent.analyze, symbol)
                        if "error" not in result:
                            logger.info(f"✅ Analysis for {symbol}: {result}")
                            # TODO: Send to Reasoning Agent
                        else:
                            logger.warning(f"❌ Vision failed for {symbol}: {result['error']}")
                        
                        last_scan[symbol] = current_time
                            
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                
            await asyncio.sleep(self.collection_interval)
