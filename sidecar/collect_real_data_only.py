#!/usr/bin/env python3
"""
REAL DATA COLLECTION ONLY - NO SYNTHETIC DATA
Collects real market data and trains models with real data only
"""

import asyncio
import pandas as pd
from datetime import datetime
from loguru import logger

from app.data.enhanced_data_collector import enhanced_collector
from app.data.database import db
from app.core import settings


async def store_real_bars_properly(symbol: str, df: pd.DataFrame, source: str):
    """Store REAL collected bars in database properly"""
    logger.info(f"Storing {len(df)} REAL bars from {source} for {symbol}...")
    
    stored_count = 0
    for _, row in df.iterrows():
        try:
            # Convert timestamp to unix timestamp
            if hasattr(row['time'], 'timestamp'):
                ts = int(row['time'].timestamp())
            else:
                ts = int(pd.Timestamp(row['time']).timestamp())
            
            # Insert into historical_bars table (correct table name)
            await db.connection.execute("""
                INSERT OR REPLACE INTO historical_bars 
                (symbol, timeframe, timestamp, open, high, low, close, volume, is_synthetic)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                symbol,
                'H1',
                ts,
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                int(row.get('volume', 0))
            ))
            stored_count += 1
        except Exception as e:
            logger.debug(f"Error storing bar: {e}")
    
    await db.connection.commit()
    logger.success(f"✓ Stored {stored_count}/{len(df)} REAL bars in database")
    return stored_count


async def train_models_with_real_data(symbol: str):
    """Train ML models using ONLY real collected data"""
    logger.info(f"Training models for {symbol} with REAL data only...")
    
    try:
        # Get REAL bars from database (is_synthetic = 0)
        rows = await db.fetch_all("""
            SELECT timestamp, open, high, low, close, volume
            FROM historical_bars
            WHERE symbol = ? AND is_synthetic = 0
            ORDER BY timestamp ASC
        """, (symbol,))
        
        if not rows or len(rows) < 100:
            logger.error(f"Insufficient REAL data for {symbol}: {len(rows) if rows else 0} bars")
            return False
        
        logger.info(f"Found {len(rows)} REAL bars for training")
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(row) for row in rows])
        
        # Calculate features from REAL data
        from app.data.features import feature_engineer
        
        training_samples = []
        for i in range(50, len(df)):  # Need history for features
            window = df.iloc[i-50:i+1]
            
            # Extract features from REAL data
            features = {
                'symbol': symbol,
                'close': float(window['close'].iloc[-1]),
                'high': float(window['high'].iloc[-1]),
                'low': float(window['low'].iloc[-1]),
                'open': float(window['open'].iloc[-1]),
                'volume': int(window['volume'].iloc[-1]),
                # Calculate technical indicators from REAL data
                'rsi': float(calculate_rsi(window['close'])),
                'ema_slope': float(calculate_ema_slope(window['close'])),
                'atr': float(calculate_atr(window)),
                'realized_vol': float(window['close'].pct_change().std()),
            }
            
            # Determine outcome from REAL data (next bar direction)
            if i < len(df) - 1:
                next_close = df['close'].iloc[i+1]
                current_close = df['close'].iloc[i]
                outcome = 1 if next_close > current_close else 0
                
                training_samples.append({
                    'features': features,
                    'outcome': outcome,
                    'pnl': float(next_close - current_close)
                })
        
        if len(training_samples) < 100:
            logger.error(f"Insufficient training samples: {len(training_samples)}")
            return False
        
        logger.info(f"Created {len(training_samples)} training samples from REAL data")
        
        # Train Random Forest with REAL data
        from app.ml.random_forest import random_forest_model
        
        X = []
        y = []
        for sample in training_samples:
            feat_vector = [
                sample['features']['close'],
                sample['features']['rsi'],
                sample['features']['ema_slope'],
                sample['features']['atr'],
                sample['features']['realized_vol'],
            ]
            X.append(feat_vector)
            y.append(sample['outcome'])
        
        import numpy as np
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"Training Random Forest with {len(X)} REAL samples...")
        accuracy = random_forest_model.train(X, y, symbol)
        
        if accuracy:
            logger.success(f"✓ Random Forest trained: accuracy={accuracy:.3f}")
        
        # Train LSTM with REAL data
        from app.ml.lstm_model import lstm_model
        
        logger.info(f"Training LSTM with {len(X)} REAL samples...")
        val_loss = lstm_model.train(X, y, symbol)
        
        if val_loss:
            logger.success(f"✓ LSTM trained: val_loss={val_loss:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error training models: {e}", exc_info=True)
        return False


def calculate_rsi(prices, period=14):
    """Calculate RSI from REAL price data"""
    deltas = prices.diff()
    gain = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0


def calculate_ema_slope(prices, period=20):
    """Calculate EMA slope from REAL price data"""
    ema = prices.ewm(span=period).mean()
    slope = (ema.iloc[-1] - ema.iloc[-2]) / ema.iloc[-2] if len(ema) > 1 else 0
    return slope


def calculate_atr(window, period=14):
    """Calculate ATR from REAL OHLC data"""
    high = window['high']
    low = window['low']
    close = window['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else tr.mean()


async def main():
    """Collect REAL data and train with REAL data only"""
    logger.info("="*70)
    logger.info("REAL DATA COLLECTION AND TRAINING - NO SYNTHETIC DATA")
    logger.info("="*70)
    
    # Connect to database
    await db.connect()
    
    results = {}
    
    for symbol in settings.symbols_list:
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing {symbol} - REAL DATA ONLY")
        logger.info(f"{'='*70}\n")
        
        # Step 1: Collect REAL data
        logger.info(f"Step 1: Collecting REAL market data for {symbol}...")
        df, source, count = await enhanced_collector.collect_best_available(symbol, target_bars=1000)
        
        if df is not None and count > 0:
            logger.success(f"✓ Collected {count} REAL bars from {source}")
            
            # Store REAL data properly
            stored = await store_real_bars_properly(symbol, df, source)
            
            if stored > 0:
                # Step 2: Train with REAL data only
                logger.info(f"\nStep 2: Training models with {stored} REAL bars...")
                trained = await train_models_with_real_data(symbol)
                
                results[symbol] = {
                    'real_bars': stored,
                    'source': source,
                    'trained': trained
                }
            else:
                results[symbol] = {'real_bars': 0, 'source': source, 'trained': False}
        else:
            logger.error(f"✗ Failed to collect REAL data for {symbol}")
            results[symbol] = {'real_bars': 0, 'source': 'failed', 'trained': False}
        
        await asyncio.sleep(2)  # Rate limit protection
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("SUMMARY - REAL DATA ONLY")
    logger.info(f"{'='*70}\n")
    
    for symbol, result in results.items():
        status = "✓ SUCCESS" if result['trained'] else "✗ FAILED"
        logger.info(f"{symbol}: {status}")
        logger.info(f"  REAL bars: {result['real_bars']} (from {result['source']})")
        logger.info(f"  Models trained: {'Yes' if result['trained'] else 'No'}\n")
    
    successful = sum(1 for r in results.values() if r['trained'])
    logger.info(f"Total: {successful}/{len(results)} symbols trained with REAL data")
    
    if successful > 0:
        logger.success("\n✓ REAL DATA COLLECTION AND TRAINING COMPLETE!")
        logger.info("Restart sidecar: pm2 restart vproptrader-sidecar")
    else:
        logger.error("\n✗ TRAINING FAILED - Check logs above")
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
