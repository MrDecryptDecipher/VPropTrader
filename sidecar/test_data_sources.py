"""Test script to verify all data sources are working"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.data.multi_source_provider import multi_source_provider
from app.core import settings
from loguru import logger


async def test_all_sources():
    """Test all configured data sources"""
    
    logger.info("=" * 60)
    logger.info("Testing All Data Sources")
    logger.info("=" * 60)
    
    results = {
        'yahoo_finance': False,
        'twelve_data': False,
        'alpha_vantage': False,
        'polygon': False,
        'coingecko': False,
        'macro_data': False
    }
    
    # Test 1: Yahoo Finance (no API key needed)
    logger.info("\n1. Testing Yahoo Finance...")
    try:
        df = await multi_source_provider.fetch_yahoo_finance("^NDX", period="5d", interval="1d")
        if df is not None and len(df) > 0:
            results['yahoo_finance'] = True
            logger.info(f"✓ Yahoo Finance: {len(df)} bars retrieved")
        else:
            logger.warning("✗ Yahoo Finance: No data")
    except Exception as e:
        logger.error(f"✗ Yahoo Finance error: {e}")
    
    # Test 2: Twelve Data
    logger.info("\n2. Testing Twelve Data...")
    if settings.twelve_data_key:
        try:
            df = await multi_source_provider.fetch_twelve_data_timeseries("NDX", interval="1day", outputsize=10)
            if df is not None and len(df) > 0:
                results['twelve_data'] = True
                logger.info(f"✓ Twelve Data: {len(df)} bars retrieved")
            else:
                logger.warning("✗ Twelve Data: No data")
        except Exception as e:
            logger.error(f"✗ Twelve Data error: {e}")
    else:
        logger.warning("⚠ Twelve Data: API key not configured")
    
    # Test 3: Alpha Vantage
    logger.info("\n3. Testing Alpha Vantage...")
    if settings.alpha_vantage_key:
        try:
            df = await multi_source_provider.fetch_alpha_vantage_intraday("NDX", interval="60min", outputsize="compact")
            if df is not None and len(df) > 0:
                results['alpha_vantage'] = True
                logger.info(f"✓ Alpha Vantage: {len(df)} bars retrieved")
            else:
                logger.warning("✗ Alpha Vantage: No data")
        except Exception as e:
            logger.error(f"✗ Alpha Vantage error: {e}")
    else:
        logger.warning("⚠ Alpha Vantage: API key not configured")
    
    # Test 4: Polygon.io
    logger.info("\n4. Testing Polygon.io...")
    if settings.polygon_key:
        try:
            from datetime import datetime, timedelta
            to_date = datetime.now().strftime("%Y-%m-%d")
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            df = await multi_source_provider.fetch_polygon_aggregates("AAPL", multiplier=1, timespan="day", from_date=from_date, to_date=to_date)
            if df is not None and len(df) > 0:
                results['polygon'] = True
                logger.info(f"✓ Polygon.io: {len(df)} bars retrieved")
            else:
                logger.warning("✗ Polygon.io: No data")
        except Exception as e:
            logger.error(f"✗ Polygon.io error: {e}")
    else:
        logger.warning("⚠ Polygon.io: API key not configured")
    
    # Test 5: CoinGecko
    logger.info("\n5. Testing CoinGecko...")
    try:
        df = await multi_source_provider.fetch_coingecko_ohlc("bitcoin", vs_currency="usd", days=7)
        if df is not None and len(df) > 0:
            results['coingecko'] = True
            logger.info(f"✓ CoinGecko: {len(df)} bars retrieved")
        else:
            logger.warning("✗ CoinGecko: No data")
    except Exception as e:
        logger.error(f"✗ CoinGecko error: {e}")
    
    # Test 6: Macro Data (Multi-source)
    logger.info("\n6. Testing Macro Data Sources...")
    try:
        macro_data = await multi_source_provider.fetch_macro_data_multi_source()
        if macro_data and len(macro_data) > 0:
            results['macro_data'] = True
            logger.info(f"✓ Macro Data: {len(macro_data)} indicators retrieved")
            for key, value in macro_data.items():
                logger.info(f"  {key}: {value:.2f}")
        else:
            logger.warning("✗ Macro Data: No data")
    except Exception as e:
        logger.error(f"✗ Macro Data error: {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    working_sources = sum(1 for v in results.values() if v)
    total_sources = len(results)
    
    for source, status in results.items():
        status_icon = "✓" if status else "✗"
        logger.info(f"{status_icon} {source.replace('_', ' ').title()}: {'Working' if status else 'Failed'}")
    
    logger.info("=" * 60)
    logger.info(f"Result: {working_sources}/{total_sources} data sources working")
    
    if results['yahoo_finance']:
        logger.info("✓ EXCELLENT: Yahoo Finance working (unlimited free data)")
    
    if working_sources >= 3:
        logger.info("✓ GOOD: Multiple data sources available")
    elif working_sources >= 1:
        logger.info("⚠ OK: At least one data source working")
    else:
        logger.error("✗ CRITICAL: No data sources working!")
    
    logger.info("=" * 60)
    
    # Close client
    await multi_source_provider.close()
    
    return results


if __name__ == "__main__":
    asyncio.run(test_all_sources())
