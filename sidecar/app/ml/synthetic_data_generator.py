"""Synthetic Training Data Generator - Creates realistic trade samples for ML training"""

import numpy as np
import pandas as pd
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from loguru import logger


class SyntheticDataGenerator:
    """
    Generates synthetic training data for ML models
    
    Purpose: Bootstrap ML models before real trades exist
    Quality: Realistic feature distributions and outcome correlations
    """
    
    def __init__(self):
        self.feature_names = [
            # Price features (10)
            'z_close', 'z_high', 'z_low', 'ema_slope', 'roc_5', 'roc_10',
            'rsi', 'price_position', 'm5_trend', 'm15_trend',
            
            # Volume features (5)
            'rvol', 'cvd', 'vwap_distance', 'volume_trend', 'vpin',
            
            # Volatility features (6)
            'atr_z', 'bb_width', 'bb_position', 'realized_vol', 'vol_ratio',
            
            # Macro features (5)
            'dxy_z', 'vix_z', 'ust10y_z', 'ust2y_z', 'yield_curve',
            
            # Sentiment (1)
            'sentiment',
            
            # Correlation features (3)
            'corr_nas100', 'corr_xauusd', 'corr_eurusd',
            
            # Regime (3)
            'regime_trend', 'regime_revert', 'regime_choppy',
        ]
        
        # Outcome distribution (65% win rate)
        self.outcome_distribution = {
            'TP1': 0.45,  # 45% hit TP1
            'TP2': 0.20,  # 20% hit TP2
            'SL': 0.35,   # 35% hit SL
        }
        
        # PnL parameters
        self.pnl_params = {
            'TP1': {'mean': 12, 'std': 4},   # Avg +$12
            'TP2': {'mean': 20, 'std': 6},   # Avg +$20
            'SL': {'mean': -10, 'std': 3},   # Avg -$10
        }
    
    async def generate_bars(
        self,
        symbol: str,
        count: int = 1000,
        base_price: float = 15000.0,
        volatility: float = 0.02,
        start_time: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Generate synthetic OHLCV bars for bootstrapping
        
        Args:
            symbol: Trading symbol
            count: Number of bars to generate
            base_price: Starting price
            volatility: Price volatility (std dev as fraction of price)
            start_time: Starting timestamp (defaults to 30 days ago)
        
        Returns:
            DataFrame with columns: time, open, high, low, close, volume
        """
        logger.info(f"Generating {count} synthetic bars for {symbol}...")
        
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=30)
        
        bars = []
        current_price = base_price
        current_time = start_time
        
        for i in range(count):
            # Generate realistic OHLC
            # Price follows geometric Brownian motion
            price_change = np.random.normal(0, volatility * current_price)
            new_price = current_price + price_change
            
            # Ensure positive price
            new_price = max(new_price, base_price * 0.5)
            
            # Generate OHLC with realistic relationships
            open_price = current_price
            close_price = new_price
            
            # High and low based on volatility
            intrabar_range = abs(np.random.normal(0, volatility * current_price * 0.5))
            high_price = max(open_price, close_price) + intrabar_range
            low_price = min(open_price, close_price) - intrabar_range
            
            # Volume (log-normal distribution)
            volume = int(np.random.lognormal(10, 1))
            
            bars.append({
                'time': current_time,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
            
            # Update for next bar
            current_price = new_price
            current_time += timedelta(hours=1)  # 1-hour bars
        
        df = pd.DataFrame(bars)
        logger.success(f"✓ Generated {len(df)} synthetic bars for {symbol}")
        
        return df
    
    def generate_trade_samples(
        self, 
        n_samples: int = 1000,
        symbols: list[str] = None
    ) -> list[Dict]:
        """
        Generate synthetic trade outcomes
        
        Args:
            n_samples: Number of samples to generate
            symbols: List of symbols to use
        
        Returns:
            List of trade dicts with features, outcomes, and PnL
        """
        if symbols is None:
            symbols = ['NAS100', 'XAUUSD', 'EURUSD']
        
        logger.info(f"Generating {n_samples} synthetic trade samples...")
        
        samples = []
        
        # Distribute timestamps over last 30 days
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)
        
        for i in range(n_samples):
            # Random timestamp
            timestamp = start_time + (end_time - start_time) * np.random.random()
            
            # Random symbol
            symbol = np.random.choice(symbols)
            
            # Generate realistic features
            features = self._generate_realistic_features(symbol)
            
            # Determine outcome based on feature quality
            exit_reason, pnl = self._determine_outcome(features)
            
            # Create sample
            sample = {
                'symbol': symbol,
                'features_json': json.dumps(features),
                'exit_reason': exit_reason,
                'pnl': pnl,
                'timestamp': int(timestamp.timestamp()),
                'is_synthetic': 1
            }
            
            samples.append(sample)
        
        # Log statistics
        tp1_count = sum(1 for s in samples if s['exit_reason'] == 'TP1')
        tp2_count = sum(1 for s in samples if s['exit_reason'] == 'TP2')
        sl_count = sum(1 for s in samples if s['exit_reason'] == 'SL')
        win_rate = (tp1_count + tp2_count) / n_samples * 100
        avg_pnl = np.mean([s['pnl'] for s in samples])
        
        logger.info(f"✓ Generated {n_samples} synthetic trades:")
        logger.info(f"  TP1: {tp1_count} ({tp1_count/n_samples*100:.1f}%)")
        logger.info(f"  TP2: {tp2_count} ({tp2_count/n_samples*100:.1f}%)")
        logger.info(f"  SL: {sl_count} ({sl_count/n_samples*100:.1f}%)")
        logger.info(f"  Win Rate: {win_rate:.1f}%")
        logger.info(f"  Avg PnL: ${avg_pnl:.2f}")
        
        return samples
    
    def _generate_realistic_features(self, symbol: str) -> Dict:
        """
        Generate realistic feature values
        
        Features follow realistic distributions:
        - Z-scores: Normal(-1, 1)
        - Indicators: Bounded ranges
        - Correlations: [-1, 1]
        - Regime: One-hot encoded
        """
        features = {}
        
        # Price features - z-scores around 0
        features['z_close'] = np.random.normal(0, 0.8)
        features['z_high'] = features['z_close'] + abs(np.random.normal(0, 0.3))
        features['z_low'] = features['z_close'] - abs(np.random.normal(0, 0.3))
        
        # EMA slope - small values
        features['ema_slope'] = np.random.normal(0, 0.002)
        
        # ROC - rate of change
        features['roc_5'] = np.random.normal(0, 0.01)
        features['roc_10'] = np.random.normal(0, 0.015)
        
        # RSI - bounded [0, 100], centered around 50
        features['rsi'] = np.clip(np.random.normal(50, 15), 0, 100)
        
        # Price position in range [0, 1]
        features['price_position'] = np.random.beta(2, 2)  # Bell curve around 0.5
        
        # Multi-timeframe trends [-1, 1]
        features['m5_trend'] = np.random.choice([-1, 0, 1], p=[0.3, 0.4, 0.3])
        features['m15_trend'] = np.random.choice([-1, 0, 1], p=[0.3, 0.4, 0.3])
        
        # Volume features
        features['rvol'] = np.random.lognormal(0, 0.5)  # Typically > 1
        features['cvd'] = np.random.normal(0, 500)
        features['vwap_distance'] = np.random.normal(0, 0.01)
        features['volume_trend'] = np.random.normal(0, 0.3)
        features['vpin'] = np.random.beta(2, 5)  # Skewed toward 0
        
        # Volatility features
        features['atr_z'] = np.random.normal(0, 1)
        features['bb_width'] = np.random.lognormal(-3, 0.5)  # Small positive values
        features['bb_position'] = np.random.beta(2, 2)  # [0, 1]
        features['realized_vol'] = np.random.lognormal(-4, 0.5)  # Small positive
        features['vol_ratio'] = np.random.lognormal(0, 0.3)  # Around 1
        
        # Macro features - z-scores
        features['dxy_z'] = np.random.normal(0, 1)
        features['vix_z'] = np.random.normal(0, 1)
        features['ust10y_z'] = np.random.normal(0, 1)
        features['ust2y_z'] = np.random.normal(0, 1)
        features['yield_curve'] = np.random.normal(0.5, 0.5)  # Typically positive
        
        # Sentiment [-1, 1]
        features['sentiment'] = np.random.normal(0, 0.4)
        
        # Correlations [-1, 1]
        features['corr_nas100'] = np.random.uniform(-0.5, 0.5)
        features['corr_xauusd'] = np.random.uniform(-0.5, 0.5)
        features['corr_eurusd'] = np.random.uniform(-0.5, 0.5)
        
        # Regime - one-hot encoded (one must be 1, others 0)
        regime = np.random.choice(['trend', 'revert', 'choppy'], p=[0.4, 0.3, 0.3])
        features['regime_trend'] = 1.0 if regime == 'trend' else 0.0
        features['regime_revert'] = 1.0 if regime == 'revert' else 0.0
        features['regime_choppy'] = 1.0 if regime == 'choppy' else 0.0
        
        return features
    
    def _determine_outcome(self, features: Dict) -> Tuple[str, float]:
        """
        Determine trade outcome based on feature quality
        
        Better features → Higher probability of TP
        
        Args:
            features: Feature dict
        
        Returns:
            (exit_reason, pnl)
        """
        # Calculate "quality score" from features
        quality_score = 0.0
        
        # Strong trend increases win probability
        if features['regime_trend'] == 1.0:
            quality_score += 0.15
            if abs(features['ema_slope']) > 0.001:
                quality_score += 0.10
        
        # Mean reversion in revert regime
        if features['regime_revert'] == 1.0:
            if features['bb_position'] < 0.2 or features['bb_position'] > 0.8:
                quality_score += 0.10
        
        # Volume confirmation
        if features['rvol'] > 1.5:
            quality_score += 0.08
        
        # RSI extremes in revert regime
        if features['regime_revert'] == 1.0:
            if features['rsi'] < 30 or features['rsi'] > 70:
                quality_score += 0.10
        
        # Multi-timeframe alignment
        if features['m5_trend'] == features['m15_trend'] and features['m5_trend'] != 0:
            quality_score += 0.12
        
        # Low volatility in choppy regime reduces quality
        if features['regime_choppy'] == 1.0:
            quality_score -= 0.15
        
        # Adjust outcome probabilities based on quality
        base_tp_prob = 0.65  # Base 65% win rate
        adjusted_tp_prob = np.clip(base_tp_prob + quality_score, 0.3, 0.85)
        
        # Determine outcome
        rand = np.random.random()
        
        if rand < adjusted_tp_prob * 0.69:  # 45% of 65% = TP1
            exit_reason = 'TP1'
        elif rand < adjusted_tp_prob:  # Remaining 20% = TP2
            exit_reason = 'TP2'
        else:
            exit_reason = 'SL'
        
        # Generate PnL based on outcome
        params = self.pnl_params[exit_reason]
        pnl = np.random.normal(params['mean'], params['std'])
        
        # Add some noise based on volatility
        vol_factor = features['realized_vol'] / 0.01  # Normalize
        pnl *= (0.8 + 0.4 * vol_factor)  # ±20% based on volatility
        
        return exit_reason, round(pnl, 2)
    
    def get_feature_vector(self, features: Dict) -> np.ndarray:
        """
        Convert features dict to ordered numpy array
        
        Args:
            features: Feature dict
        
        Returns:
            50-dimensional feature vector
        """
        vector = np.array([features.get(name, 0.0) for name in self.feature_names])
        
        # Pad to 50 dimensions if needed
        if len(vector) < 50:
            vector = np.pad(vector, (0, 50 - len(vector)), constant_values=0.0)
        
        return vector[:50]
    
    def validate_samples(self, samples: list[Dict]) -> Dict:
        """
        Validate generated samples for quality
        
        Args:
            samples: List of generated samples
        
        Returns:
            Dict with validation metrics
        """
        if not samples:
            return {'valid': False, 'reason': 'No samples'}
        
        # Check win rate
        winners = sum(1 for s in samples if s['exit_reason'] in ['TP1', 'TP2'])
        win_rate = winners / len(samples)
        
        # Check PnL distribution
        pnls = [s['pnl'] for s in samples]
        avg_pnl = np.mean(pnls)
        
        # Check feature validity
        try:
            for sample in samples[:10]:  # Check first 10
                features = json.loads(sample['features_json'])
                vector = self.get_feature_vector(features)
                if len(vector) != 50:
                    return {'valid': False, 'reason': 'Invalid feature vector length'}
        except Exception as e:
            return {'valid': False, 'reason': f'Feature parsing error: {e}'}
        
        # Validation criteria
        valid = (
            0.55 <= win_rate <= 0.75 and  # Win rate between 55-75%
            -5 <= avg_pnl <= 10  # Avg PnL between -$5 and +$10
        )
        
        return {
            'valid': valid,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'n_samples': len(samples),
            'reason': 'Valid' if valid else 'Out of expected ranges'
        }


# Global synthetic data generator instance
synthetic_data_generator = SyntheticDataGenerator()
synthetic_generator = synthetic_data_generator  # Alias for compatibility
