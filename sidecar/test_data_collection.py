#!/usr/bin/env python3
"""Simple test script to verify data collection works"""

import asyncio
from loguru import logger

# Test imports
try:
    from app.data.enhanced_data_collector import enhanced_collector
    from app.data.symbol_mapper import symbol_mapper
    from app.core import settings
    logger.success("✓ All imports successful")
except Exception as e:
    logger.error(f"✗ Import failed: {e}")
    exit(1)

async def test_symbol_mappings():
    """Test symbol mappings"""
    logger.info("\n" + "="*60)
    logger.info("TESTING SYMBOL MAPPINGS")
    logger.info("="*60)
    
    for symbol in settings.symbols_list:
        logger.info(f"\n{symbol}:")
        mappings = symbol_mapper.get_all_mappings(symbol)
        for provider, mapped_symbol in mappings.items():
            if provider != 'alternatives':
                logger.info(f"  {provider:15s}: {mapped_symbol}")
            else:
                logger.info(f"  alternatives: {', '.join(mapped_symbol)}")

async def test_api_keys():
    """Test API key configuration"""
    logger.info("\n" + "="*60)
    logger.info("TESTING API KEY CONFIGURATION")
    logger.info("="*60)
    
    keys = {
        'FRED API': settings.fred_api_key,
        'Twelve Data': getattr(settings, 'twelve_data_key', None),
        'Alpha Vantage': getattr(settings, 'alpha_vantage_key', None),
        'Polygon': getattr(settings, 'polygon_key', None),
    }
    
    for name, key in keys.items():
        if key:
            masked = key[:8] + "..." + key[-4:] if len(key) > 12 else key
            logger.success(f"✓ {name:15s}: {masked}")
        else:
            logger.warning(f"✗ {name:15s}: Not configured")

async def test_single_symbol_collection():
    """Test data collection for a single symbol"""
    logger.info("\n" + "="*60)
    logger.info("TESTING DATA COLLECTION FOR EURUSD")
    logger.info("="*60)
    
    try:
        df, source, count = await enhanced_collector.collect_best_available(
            'EURUSD',
            target_bars=100
        )
        
        if df is not None and count > 0:
            logger.success(f"\n✓ SUCCESS!")
            logger.info(f"  Source: {source}")
            logger.info(f"  Bars collected: {count}")
            logger.info(f"  Date range: {df['time'].min()} to {df['time'].max()}")
            logger.info(f"  Price range: ${df['close'].min():.4f} - ${df['close'].max():.4f}")
            return True
        else:
            logger.error(f"\n✗ FAILED: No data collected (source: {source})")
            return False
    except Exception as e:
        logger.error(f"\n✗ FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("VPROPTRADER DATA COLLECTION TEST")
    logger.info("="*60)
    
    # Test 1: Symbol mappings
    await test_symbol_mappings()
    
    # Test 2: API keys
    await test_api_keys()
    
    # Test 3: Actual data collection
    success = await test_single_symbol_collection()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    if success:
        logger.success("\n✓ ALL TESTS PASSED!")
        logger.info("\nYou can now run the full bootstrap:")
        logger.info("  python3 bootstrap_complete.py")
    else:
        logger.error("\n✗ TESTS FAILED")
        logger.info("\nTroubleshooting:")
        logger.info("1. Check your API keys in .env file")
        logger.info("2. Verify network connectivity")
        logger.info("3. Try testing individual APIs with curl")

if __name__ == "__main__":
    asyncio.run(main())
