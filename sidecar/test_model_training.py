"""Test script for automated model training"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ml.bootstrap_trainer import bootstrap_trainer
from app.ml.synthetic_data_generator import synthetic_data_generator
from app.data.database import db
from loguru import logger


async def test_model_training():
    """Test automated model training pipeline"""
    
    logger.info("=" * 60)
    logger.info("Testing Automated Model Training Pipeline")
    logger.info("=" * 60)
    
    try:
        # Step 1: Connect to database
        logger.info("\n1. Connecting to database...")
        await db.connect()
        logger.info("✓ Database connected")
        
        # Step 2: Check training status
        logger.info("\n2. Checking training status...")
        status = bootstrap_trainer.get_training_status()
        
        logger.info(f"  Models path: {status['models_path']}")
        logger.info(f"  RF ONNX exists: {status['rf_onnx_exists']}")
        logger.info(f"  LSTM ONNX exists: {status['lstm_onnx_exists']}")
        logger.info(f"  RF native exists: {status['rf_native_exists']}")
        logger.info(f"  LSTM native exists: {status['lstm_native_exists']}")
        logger.info(f"  Ready for inference: {status['ready_for_inference']}")
        
        # Step 3: Generate synthetic data if needed
        logger.info("\n3. Checking training data...")
        result = await db.fetch_one(
            "SELECT COUNT(*) as count FROM trades WHERE status = 'closed'"
        )
        trade_count = result['count'] if result else 0
        
        logger.info(f"  Existing trades: {trade_count}")
        
        if trade_count < 100:
            logger.info("  Generating synthetic training data...")
            samples = synthetic_data_generator.generate_trade_samples(n_samples=200)
            
            # Store samples
            for sample in samples:
                try:
                    from datetime import datetime
                    await db.execute("""
                        INSERT INTO trades (
                            trade_id, timestamp, symbol, action, exit_reason, pnl, 
                            features_json, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f"test_{sample['timestamp']}_{sample['symbol']}",
                        datetime.fromtimestamp(sample['timestamp']),
                        sample['symbol'],
                        'BUY',
                        sample['exit_reason'],
                        sample['pnl'],
                        sample['features_json'],
                        'closed'
                    ))
                except Exception as e:
                    logger.debug(f"Error storing sample: {e}")
            
            logger.info(f"✓ Generated {len(samples)} synthetic trades")
        
        # Step 4: Train models
        logger.info("\n4. Training models...")
        success = await bootstrap_trainer.train_if_needed()
        
        if not success:
            logger.error("✗ Model training failed")
            return False
        
        logger.info("✓ Model training complete")
        
        # Step 5: Check final status
        logger.info("\n5. Checking final status...")
        final_status = bootstrap_trainer.get_training_status()
        
        logger.info(f"  RF ONNX: {final_status['rf_onnx_exists']}")
        logger.info(f"  LSTM ONNX: {final_status['lstm_onnx_exists']}")
        logger.info(f"  Ready: {final_status['ready_for_inference']}")
        
        if not final_status['ready_for_inference']:
            logger.error("✗ Models not ready for inference")
            return False
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Test Results Summary")
        logger.info("=" * 60)
        logger.info("✓ Database connection: Working")
        logger.info("✓ Training data: Available")
        logger.info("✓ Model training: Complete")
        logger.info("✓ Models ready: Yes")
        logger.info("=" * 60)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    
    finally:
        await db.disconnect()


if __name__ == "__main__":
    success = asyncio.run(test_model_training())
    sys.exit(0 if success else 1)
