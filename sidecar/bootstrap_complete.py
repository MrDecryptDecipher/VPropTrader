#!/usr/bin/env python3
"""
Complete Bootstrap Data Collection and Model Training
Collects real market data and trains ML models for signal generation
"""

import asyncio
import sys
import pandas as pd
from datetime import datetime
from loguru import logger

from app.data.enhanced_data_collector import enhanced_collector
from app.data.database import db
from app.data.redis_client import redis_client
from app.memory.long_term_memory import long_term_memory
from app.ml.synthetic_data_generator import synthetic_generator
from app.ml.bootstrap_trainer import bootstrap_trainer
from app.core import settings


async def store_bars_in_database(symbol: str, df: pd.DataFrame, timeframe: str = 'H1'):
    """Store collected bars in database"""
    logger.info(f"Storing {len(df)} bars in database for {symbol}...")
    
    stored_count = 0
    for _, row in df.iterrows():
        try:
            await db.store_bar(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=row['time'],
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row.get('volume', 0))
            )
            stored_count += 1
        except Exception as e:
            logger.debug(f"Error storing bar: {e}")
    
    logger.success(f"✓ Stored {stored_count}/{len(df)} bars in database")
    return stored_count


async def store_bars_in_ltm(symbol: str, df: pd.DataFrame):
    """Store collected bars in Long-Term Memory as synthetic trades"""
    logger.info(f"Storing {len(df)} bars in LTM for {symbol}...")
    
    stored_count = 0
    for idx, row in df.iterrows():
        try:
            # Create a synthetic trade from the bar
            # This allows the ML models to train on historical price action
            trade_data = {
                'trade_id': f"bootstrap_{symbol}_{idx}",
                'timestamp': row['time'].isoformat() if hasattr(row['time'], 'isoformat') else str(row['time']),
                'symbol': symbol,
                'alpha_id': 'bootstrap_data',
                'regime': 'unknown',
                'features': {
                    'close': float(row['close']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'open': float(row['open']),
                    'volume': int(row.get('volume', 0)),
                    'range': float(row['high'] - row['low']),
                    'body': float(abs(row['close'] - row['open'])),
                },
                'rf_pwin': 0.5,
                'lstm_sigma': 0.01,
                'lstm_direction': 1.0 if row['close'] > row['open'] else -1.0,
                'q_star': 5.0,
                'es95': 5.0,
                'entry_price': float(row['open']),
                'stop_loss': float(row['low']),
                'take_profit_1': float(row['high']),
                'take_profit_2': float(row['high']),
                'lots': 0.01,
                'exit_price': float(row['close']),
                'exit_reason': 'TP1' if row['close'] > row['open'] else 'SL',
                'pnl': float(row['close'] - row['open']),
                'equity_before': 1000.0,
            }
            
            # Store in LTM
            await long_term_memory.add_trade(trade_data)
            stored_count += 1
        except Exception as e:
            logger.debug(f"Error storing in LTM: {e}")
    
    logger.success(f"✓ Stored {stored_count}/{len(df)} bars in LTM")
    return stored_count


async def generate_synthetic_data(symbol: str, real_bars: int, target_bars: int = 5000):
    """Generate synthetic data to supplement real data"""
    if real_bars >= target_bars:
        logger.info(f"Sufficient real data for {symbol}, skipping synthetic generation")
        return 0
    
    synthetic_needed = target_bars - real_bars
    logger.info(f"Generating {synthetic_needed} synthetic bars for {symbol}...")
    
    try:
        # Generate synthetic data based on real data patterns
        synthetic_df = await synthetic_generator.generate_bars(
            symbol=symbol,
            count=synthetic_needed,
            base_price=2700.0 if symbol == 'XAUUSD' else 15000.0,  # Approximate prices
            volatility=0.02
        )
        
        if synthetic_df is not None and len(synthetic_df) > 0:
            # Store synthetic data
            await store_bars_in_database(symbol, synthetic_df, timeframe='H1_SYNTHETIC')
            await store_bars_in_ltm(symbol, synthetic_df)
            
            logger.success(f"✓ Generated and stored {len(synthetic_df)} synthetic bars")
            return len(synthetic_df)
        else:
            logger.warning(f"Failed to generate synthetic data for {symbol}")
            return 0
    except Exception as e:
        logger.error(f"Error generating synthetic data: {e}")
        return 0


async def train_models_for_symbol(symbol: str):
    """Train ML models for a symbol"""
    logger.info(f"Training ML models for {symbol}...")
    
    try:
        # Get training data from LTM (returns tuple of X, y)
        X, y = await long_term_memory.get_training_data(limit=5000)
        
        if X is None or len(X) < 100:
            logger.warning(f"Insufficient training data for {symbol}: {len(X) if X is not None else 0} samples")
            return False
        
        logger.info(f"Training with {len(X)} samples...")
        
        # Train models using bootstrap trainer
        success = await bootstrap_trainer.train_all_models(symbol, (X, y))
        
        if success:
            logger.success(f"✓ Models trained successfully for {symbol}")
            return True
        else:
            logger.error(f"✗ Model training failed for {symbol}")
            return False
    except Exception as e:
        logger.error(f"Error training models for {symbol}: {e}", exc_info=True)
        return False


async def bootstrap_symbol(symbol: str, target_bars: int = 5000):
    """Complete bootstrap process for a single symbol"""
    logger.info(f"\n{'=' * 70}")
    logger.info(f"BOOTSTRAPPING: {symbol}")
    logger.info(f"{'=' * 70}\n")
    
    results = {
        'symbol': symbol,
        'real_bars': 0,
        'synthetic_bars': 0,
        'total_bars': 0,
        'source': 'none',
        'models_trained': False,
        'success': False
    }
    
    try:
        # Step 1: Collect real market data
        logger.info(f"Step 1: Collecting real market data for {symbol}...")
        df, source, bars_count = await enhanced_collector.collect_best_available(symbol, target_bars=target_bars)
        
        if df is not None and bars_count > 0:
            results['real_bars'] = bars_count
            results['source'] = source
            
            # Store in database
            await store_bars_in_database(symbol, df)
            
            # Store in LTM
            await store_bars_in_ltm(symbol, df)
            
            logger.success(f"✓ Step 1 complete: {bars_count} real bars collected from {source}")
        else:
            logger.warning(f"⚠ Step 1: No real data collected for {symbol}")
        
        # Step 2: Generate synthetic data if needed
        logger.info(f"\nStep 2: Checking if synthetic data is needed...")
        if results['real_bars'] < target_bars:
            synthetic_count = await generate_synthetic_data(symbol, results['real_bars'], target_bars)
            results['synthetic_bars'] = synthetic_count
            logger.success(f"✓ Step 2 complete: {synthetic_count} synthetic bars generated")
        else:
            logger.info(f"✓ Step 2 skipped: Sufficient real data available")
        
        results['total_bars'] = results['real_bars'] + results['synthetic_bars']
        
        # Step 3: Train ML models
        logger.info(f"\nStep 3: Training ML models for {symbol}...")
        if results['total_bars'] >= 100:  # Minimum for training
            models_trained = await train_models_for_symbol(symbol)
            results['models_trained'] = models_trained
            
            if models_trained:
                logger.success(f"✓ Step 3 complete: Models trained successfully")
            else:
                logger.warning(f"⚠ Step 3: Model training had issues")
        else:
            logger.warning(f"⚠ Step 3 skipped: Insufficient data for training ({results['total_bars']} bars)")
        
        # Determine overall success
        results['success'] = results['total_bars'] >= 100 and results['models_trained']
        
        if results['success']:
            logger.success(f"\n✓ BOOTSTRAP COMPLETE FOR {symbol}")
        else:
            logger.warning(f"\n⚠ BOOTSTRAP INCOMPLETE FOR {symbol}")
        
    except Exception as e:
        logger.error(f"✗ Bootstrap failed for {symbol}: {e}", exc_info=True)
        results['success'] = False
    
    return results


async def main():
    """Main bootstrap process"""
    logger.info("=" * 70)
    logger.info("VPROPTRADER COMPLETE BOOTSTRAP")
    logger.info("=" * 70)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    # Check configuration
    logger.info("Configuration Check:")
    logger.info(f"  Symbols: {', '.join(settings.symbols_list)}")
    logger.info(f"  FRED API: {'✓' if settings.fred_api_key else '✗'}")
    logger.info(f"  Twelve Data: {'✓' if hasattr(settings, 'twelve_data_key') and settings.twelve_data_key else '✗'}")
    logger.info(f"  Alpha Vantage: {'✓' if hasattr(settings, 'alpha_vantage_key') and settings.alpha_vantage_key else '✗'}")
    logger.info(f"  Polygon: {'✓' if hasattr(settings, 'polygon_key') and settings.polygon_key else '✗'}")
    logger.info("")
    
    # Initialize connections
    logger.info("Initializing connections...")
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
    
    logger.info("")
    
    # Bootstrap each symbol
    all_results = []
    for symbol in settings.symbols_list:
        result = await bootstrap_symbol(symbol, target_bars=5000)
        all_results.append(result)
        
        # Small delay between symbols to respect rate limits
        await asyncio.sleep(2)
    
    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("BOOTSTRAP SUMMARY")
    logger.info("=" * 70)
    
    for result in all_results:
        status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
        logger.info(f"\n{result['symbol']}: {status}")
        logger.info(f"  Real bars: {result['real_bars']} (from {result['source']})")
        logger.info(f"  Synthetic bars: {result['synthetic_bars']}")
        logger.info(f"  Total bars: {result['total_bars']}")
        logger.info(f"  Models trained: {'Yes' if result['models_trained'] else 'No'}")
    
    successful = sum(1 for r in all_results if r['success'])
    total = len(all_results)
    
    logger.info(f"\nOverall: {successful}/{total} symbols bootstrapped successfully")
    
    if successful > 0:
        logger.success("\n✓ BOOTSTRAP COMPLETE!")
        logger.info("\nNext steps:")
        logger.info("1. Restart the sidecar service: pm2 restart vproptrader-sidecar")
        logger.info("2. Check the MT5 EA - it should start receiving signals")
        logger.info("3. Monitor the dashboard for live trading activity")
    else:
        logger.error("\n✗ BOOTSTRAP FAILED")
        logger.info("\nTroubleshooting:")
        logger.info("1. Check your API keys in sidecar/.env")
        logger.info("2. Verify network connectivity")
        logger.info("3. Check the logs above for specific errors")
    
    # Cleanup
    await db.disconnect()
    if redis_client.connected:
        await redis_client.disconnect()
    
    logger.info(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\nBootstrap interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nBootstrap failed with error: {e}", exc_info=True)
        sys.exit(1)
