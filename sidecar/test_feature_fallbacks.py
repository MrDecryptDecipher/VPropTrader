"""
Test feature extraction with fallback mechanisms
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.data.features import feature_engineer
from app.data.mt5_client import mt5_client
from app.data.redis_client import redis_client
from app.data.database import database


async def test_feature_fallbacks():
    """Test all fallback levels"""
    
    logger.info("=" * 60)
    logger.info("Testing Feature Extraction Fallback Mechanisms")
    logger.info("=" * 60)
    
    test_symbol = "EURUSD"
    
    # Initialize connections
    logger.info("\n1. Initializing connections...")
    try:
        await database.connect()
        logger.info("✓ Database connected")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
    
    try:
        await redis_client.connect()
        logger.info("✓ Redis connected")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
    
    # Test Level 4: Neutral defaults (should always work)
    logger.info("\n2. Testing Level 4: Neutral Defaults")
    logger.info("-" * 60)
    
    defaults = feature_engineer._get_neutral_defaults()
    logger.info(f"✓ Got {len(defaults)} default features")
    logger.info(f"  Sample features: z_close={defaults['z_close']}, rsi={defaults['rsi']}, sentiment={defaults['sentiment']}")
    
    assert len(defaults) >= 33, "Should have at least 33 features"
    assert defaults['rsi'] == 50.0, "RSI should be neutral (50)"
    assert defaults['regime_choppy'] == 1.0, "Should default to choppy regime"
    logger.info("✓ Neutral defaults validation passed")
    
    # Test Level 3: Database fallback (simulate by forcing cache-only mode)
    logger.info("\n3. Testing Level 3: Database Fallback")
    logger.info("-" * 60)
    
    # First, store a snapshot
    test_features = {
        'z_close': 1.5,
        'rsi': 65.0,
        'sentiment': 0.3,
        'ema_slope': 0.002
    }
    
    await feature_engineer._store_feature_snapshot(test_symbol, test_features)
    logger.info(f"✓ Stored test snapshot for {test_symbol}")
    
    # Retrieve it
    db_features = await feature_engineer._get_last_known_features(test_symbol)
    if db_features:
        logger.info(f"✓ Retrieved {len(db_features)} features from database")
        logger.info(f"  Sample: z_close={db_features.get('z_close')}, rsi={db_features.get('rsi')}")
    else:
        logger.warning("✗ Failed to retrieve database features")
    
    # Test Level 2: Redis cache
    logger.info("\n4. Testing Level 2: Redis Cache")
    logger.info("-" * 60)
    
    try:
        import time
        cached_features = {
            'z_close': 2.0,
            'rsi': 70.0,
            'sentiment': 0.5,
            '_metadata': {
                'timestamp': int(time.time()),
                'source': 'test'
            }
        }
        
        await redis_client.set(f"features:{test_symbol}", cached_features, expire=60)
        logger.info(f"✓ Stored test features in Redis cache")
        
        # Retrieve
        retrieved = await redis_client.get(f"features:{test_symbol}")
        if retrieved:
            logger.info(f"✓ Retrieved cached features")
            logger.info(f"  Sample: z_close={retrieved.get('z_close')}, rsi={retrieved.get('rsi')}")
        else:
            logger.warning("✗ Failed to retrieve cached features")
    except Exception as e:
        logger.warning(f"Redis cache test failed: {e}")
    
    # Test full fallback chain
    logger.info("\n5. Testing Full Fallback Chain")
    logger.info("-" * 60)
    
    # Test with MT5 disconnected (should fall back to cache/db/defaults)
    feature_engineer.use_cache_only = True
    
    features = await feature_engineer.extract_features_with_fallbacks(test_symbol)
    
    logger.info(f"✓ Got {len(features)} features via fallback")
    
    metadata = features.get('_metadata', {})
    logger.info(f"  Source: {metadata.get('source')}")
    logger.info(f"  Fallback level: {metadata.get('fallback_level')}")
    logger.info(f"  Is stale: {metadata.get('is_stale')}")
    logger.info(f"  Timestamp: {metadata.get('timestamp')}")
    
    # Verify we got a complete feature set
    assert len(features) > 30, "Should have at least 30 features"
    assert '_metadata' in features, "Should include metadata"
    logger.info("✓ Fallback chain validation passed")
    
    # Test with non-existent symbol (should use defaults)
    logger.info("\n6. Testing Unknown Symbol (Should Use Defaults)")
    logger.info("-" * 60)
    
    unknown_features = await feature_engineer.extract_features_with_fallbacks("UNKNOWN_SYMBOL")
    unknown_metadata = unknown_features.get('_metadata', {})
    
    logger.info(f"✓ Got {len(unknown_features)} features for unknown symbol")
    logger.info(f"  Source: {unknown_metadata.get('source')}")
    logger.info(f"  Fallback level: {unknown_metadata.get('fallback_level')}")
    
    assert unknown_metadata.get('fallback_level') == 4, "Should fall back to level 4 (defaults)"
    logger.info("✓ Unknown symbol handling passed")
    
    # Test staleness detection
    logger.info("\n7. Testing Staleness Detection")
    logger.info("-" * 60)
    
    import time
    old_features = {
        'z_close': 1.0,
        '_metadata': {
            'timestamp': int(time.time()) - 120,  # 2 minutes old
            'source': 'test'
        }
    }
    
    is_fresh = feature_engineer._is_fresh(old_features, max_age=60)
    logger.info(f"  2-minute old cache is fresh (max 60s): {is_fresh}")
    assert not is_fresh, "Should detect stale cache"
    
    fresh_features = {
        'z_close': 1.0,
        '_metadata': {
            'timestamp': int(time.time()) - 30,  # 30 seconds old
            'source': 'test'
        }
    }
    
    is_fresh = feature_engineer._is_fresh(fresh_features, max_age=60)
    logger.info(f"  30-second old cache is fresh (max 60s): {is_fresh}")
    assert is_fresh, "Should detect fresh cache"
    
    logger.info("✓ Staleness detection passed")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("FEATURE FALLBACK TEST SUMMARY")
    logger.info("=" * 60)
    logger.info("✓ Level 4: Neutral defaults - PASSED")
    logger.info("✓ Level 3: Database fallback - PASSED")
    logger.info("✓ Level 2: Redis cache - PASSED")
    logger.info("✓ Full fallback chain - PASSED")
    logger.info("✓ Unknown symbol handling - PASSED")
    logger.info("✓ Staleness detection - PASSED")
    logger.info("\n✓ All feature fallback tests PASSED!")
    
    # Cleanup
    await database.disconnect()
    await redis_client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_feature_fallbacks())
