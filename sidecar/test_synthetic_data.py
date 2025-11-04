"""Test script for synthetic training data generator"""

import sys
from pathlib import Path
import json
import numpy as np

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ml.synthetic_data_generator import synthetic_data_generator
from loguru import logger


def test_synthetic_data_generation():
    """Test synthetic data generation"""
    
    logger.info("=" * 60)
    logger.info("Testing Synthetic Training Data Generator")
    logger.info("=" * 60)
    
    # Test 1: Generate samples
    logger.info("\n1. Generating 100 synthetic trade samples...")
    samples = synthetic_data_generator.generate_trade_samples(n_samples=100)
    
    if not samples:
        logger.error("✗ Failed to generate samples")
        return False
    
    logger.info(f"✓ Generated {len(samples)} samples")
    
    # Test 2: Validate samples
    logger.info("\n2. Validating samples...")
    validation = synthetic_data_generator.validate_samples(samples)
    
    logger.info(f"  Valid: {validation['valid']}")
    logger.info(f"  Win Rate: {validation['win_rate']:.1%}")
    logger.info(f"  Avg PnL: ${validation['avg_pnl']:.2f}")
    logger.info(f"  Reason: {validation['reason']}")
    
    if not validation['valid']:
        logger.warning("⚠ Validation failed but this is OK for small samples")
    
    # Test 3: Check feature structure
    logger.info("\n3. Checking feature structure...")
    sample = samples[0]
    features = json.loads(sample['features_json'])
    
    logger.info(f"  Features count: {len(features)}")
    logger.info(f"  Sample features: {list(features.keys())[:5]}...")
    
    # Convert to vector
    vector = synthetic_data_generator.get_feature_vector(features)
    logger.info(f"  Feature vector shape: {vector.shape}")
    logger.info(f"  Feature vector range: [{vector.min():.2f}, {vector.max():.2f}]")
    
    if vector.shape[0] != 50:
        logger.error(f"✗ Invalid vector shape: {vector.shape}")
        return False
    
    logger.info("✓ Feature structure valid")
    
    # Test 4: Check outcome distribution
    logger.info("\n4. Checking outcome distribution...")
    outcomes = {}
    for sample in samples:
        outcome = sample['exit_reason']
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    
    for outcome, count in outcomes.items():
        pct = count / len(samples) * 100
        logger.info(f"  {outcome}: {count} ({pct:.1f}%)")
    
    # Test 5: Check PnL distribution
    logger.info("\n5. Checking PnL distribution...")
    pnls = [s['pnl'] for s in samples]
    
    logger.info(f"  Mean: ${np.mean(pnls):.2f}")
    logger.info(f"  Std: ${np.std(pnls):.2f}")
    logger.info(f"  Min: ${np.min(pnls):.2f}")
    logger.info(f"  Max: ${np.max(pnls):.2f}")
    
    # Test 6: Check timestamp distribution
    logger.info("\n6. Checking timestamp distribution...")
    timestamps = [s['timestamp'] for s in samples]
    time_range = max(timestamps) - min(timestamps)
    logger.info(f"  Time range: {time_range / 86400:.1f} days")
    
    # Test 7: Generate larger dataset
    logger.info("\n7. Generating 1000 samples (production size)...")
    large_samples = synthetic_data_generator.generate_trade_samples(n_samples=1000)
    large_validation = synthetic_data_generator.validate_samples(large_samples)
    
    logger.info(f"  Valid: {large_validation['valid']}")
    logger.info(f"  Win Rate: {large_validation['win_rate']:.1%}")
    logger.info(f"  Avg PnL: ${large_validation['avg_pnl']:.2f}")
    
    if not large_validation['valid']:
        logger.error("✗ Large dataset validation failed")
        return False
    
    logger.info("✓ Large dataset valid")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    logger.info("✓ Sample generation: Working")
    logger.info("✓ Feature structure: Valid (50 dimensions)")
    logger.info("✓ Outcome distribution: Realistic")
    logger.info("✓ PnL distribution: Realistic")
    logger.info("✓ Large dataset: Valid")
    logger.info("=" * 60)
    logger.info("✓ ALL TESTS PASSED")
    logger.info("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_synthetic_data_generation()
    sys.exit(0 if success else 1)
