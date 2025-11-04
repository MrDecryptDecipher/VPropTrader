#!/usr/bin/env python3
"""
Bootstrap Data Collection Script
Collects historical market data using configured API keys
"""

import asyncio
import sys
from loguru import logger
from app.data.multi_source_provider import multi_source_provider
from app.data.database import db
from app.data.redis_client import redis_client
from app.core import settings

async def collect_data_for_symbol(symbol: str, bars_needed: int = 5000):
    """Collect historical data for a symbol"""
    logger.info(f"Collecting {bars_needed} bars for {symbol}...")
    
    try:
        # Try to get data from multiple sources
        df, source = await multi_source_provider.fetch_best_available_data(
            symbol=symbol,
            timeframe='1h',
            target_bars=bars_needed
        )
        
        if df is not None and len(df) > 0:
            logger.success(f"✓ Collected {len(df)} bars for {symbol} from {source}")
            
            # Store in database
            for _, row in df.iterrows():
                await db.store_bar(
                    symbol=symbol,
                    timeframe='H1',
                    timestamp=row['time'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row.get('volume', 0)
                )
            
            logger.success(f"✓ Stored {len(df)} bars in database for {symbol} (source: {source})")
            return True
        else:
            logger.warning(f"✗ No data collected for {symbol} (source: {source})")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error collecting data for {symbol}: {e}")
        return False

async def main():
    """Main bootstrap collection"""
    logger.info("=" * 60)
    logger.info("BOOTSTRAP DATA COLLECTION")
    logger.info("=" * 60)
    
    # Check API keys
    logger.info("\nChecking API configuration...")
    logger.info(f"  FRED API: {'✓ Configured' if settings.fred_api_key else '✗ Missing'}")
    logger.info(f"  Twelve Data: {'✓ Configured' if hasattr(settings, 'twelve_data_key') and settings.twelve_data_key else '✗ Missing'}")
    logger.info(f"  Alpha Vantage: {'✓ Configured' if hasattr(settings, 'alpha_vantage_key') and settings.alpha_vantage_key else '✗ Missing'}")
    logger.info(f"  Polygon: {'✓ Configured' if hasattr(settings, 'polygon_key') and settings.polygon_key else '✗ Missing'}")
    
    # Initialize connections
    logger.info("\nInitializing connections...")
    try:
        await db.connect()
        logger.success("✓ Database connected")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return
    
    try:
        await redis_client.connect()
        logger.success("✓ Redis connected")
    except Exception as e:
        logger.warning(f"⚠ Redis connection failed: {e}")
    
    # Collect data for each symbol
    logger.info(f"\nCollecting data for {len(settings.symbols_list)} symbols...")
    logger.info(f"Symbols: {', '.join(settings.symbols_list)}")
    
    results = {}
    for symbol in settings.symbols_list:
        success = await collect_data_for_symbol(symbol, bars_needed=5000)
        results[symbol] = success
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("COLLECTION SUMMARY")
    logger.info("=" * 60)
    
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    
    logger.info(f"Total symbols: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    
    if successful > 0:
        logger.success("\n✓ Bootstrap data collection completed!")
        logger.info("You can now restart the sidecar to start generating signals.")
    else:
        logger.error("\n✗ No data was collected. Please check your API keys and network connection.")
    
    # Cleanup
    await db.disconnect()
    if redis_client.connected:
        await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
