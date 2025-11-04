"""Alpha Strategy Modules - Trading Signal Generators"""

import numpy as np
from typing import Dict, Optional, Tuple
from loguru import logger
from abc import ABC, abstractmethod


class AlphaStrategy(ABC):
    """Base class for alpha strategies"""
    
    def __init__(self, alpha_id: str):
        self.alpha_id = alpha_id
        self.weight = 1.0  # Adaptive weight
        self.stats = {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'pnl': 0.0,
            'sharpe': 0.0,
        }
    
    @abstractmethod
    def generate_signal(self, features: Dict) -> Optional[Dict]:
        """
        Generate trading signal from features
        
        Returns:
            Dict with action, confidence, stop_loss, take_profit
            or None if no signal
        """
        pass
    
    def update_stats(self, pnl: float, outcome: str):
        """Update strategy statistics"""
        self.stats['trades'] += 1
        self.stats['pnl'] += pnl
        
        if outcome in ['TP1', 'TP2']:
            self.stats['wins'] += 1
        else:
            self.stats['losses'] += 1


class MomentumAlpha(AlphaStrategy):
    """Momentum/Trend-following strategy"""
    
    def __init__(self):
        super().__init__("momentum_v3")
    
    def generate_signal(self, features: Dict) -> Optional[Dict]:
        """
        Momentum signal based on:
        - EMA slope
        - Multi-timeframe alignment
        - ROC indicators
        """
        try:
            ema_slope = features.get('ema_slope', 0)
            m5_trend = features.get('m5_trend', 0)
            m15_trend = features.get('m15_trend', 0)
            roc_5 = features.get('roc_5', 0)
            roc_10 = features.get('roc_10', 0)
            regime_trend = features.get('regime_trend', 0)
            
            logger.debug(f"Momentum features: ema_slope={ema_slope:.6f}, roc_5={roc_5:.6f}, roc_10={roc_10:.6f}")
            
            # BOOTSTRAP MODE: Relaxed conditions for testing with historical data
            # Production will use stricter thresholds with live tick data
            
            # Bullish momentum (relaxed thresholds)
            if (ema_slope > 0.0003 and  # Reduced from 0.001
                roc_5 > 0.0005):  # Reduced from 0.002
                
                confidence = min(0.85, abs(ema_slope) * 200 + 0.5)
                
                return {
                    'action': 'BUY',
                    'confidence': confidence,
                    'expected_rr': 1.8,
                    'reason': 'Bullish momentum (bootstrap mode)',
                }
            
            # Bearish momentum (relaxed thresholds)
            elif (ema_slope < -0.0003 and  # Reduced from -0.001
                  roc_5 < -0.0005):  # Reduced from -0.002
                
                confidence = min(0.85, abs(ema_slope) * 200 + 0.5)
                
                return {
                    'action': 'SELL',
                    'confidence': confidence,
                    'expected_rr': 1.8,
                    'reason': 'Bearish momentum (bootstrap mode)',
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in momentum alpha: {e}")
            return None


class MeanReversionAlpha(AlphaStrategy):
    """Mean reversion strategy"""
    
    def __init__(self):
        super().__init__("mean_revert_v2")
    
    def generate_signal(self, features: Dict) -> Optional[Dict]:
        """
        Mean reversion signal based on:
        - BB position (overbought/oversold)
        - RSI extremes
        - Low volatility regime
        """
        try:
            bb_position = features.get('bb_position', 0.5)
            rsi = features.get('rsi', 50)
            regime_revert = features.get('regime_revert', 0)
            bb_width = features.get('bb_width', 0)
            
            logger.debug(f"MeanRev features: bb_pos={bb_position:.3f}, rsi={rsi:.1f}, bb_width={bb_width:.4f}")
            
            # BOOTSTRAP MODE: Relaxed mean reversion conditions
            # Oversold - expect bounce (relaxed thresholds)
            if bb_position < 0.3 and rsi < 40:  # Relaxed from 0.2 and 30
                confidence = 0.6 + (40 - rsi) / 100
                
                return {
                    'action': 'BUY',
                    'confidence': min(0.85, confidence),
                    'expected_rr': 1.5,
                    'reason': 'Oversold mean reversion (bootstrap)',
                }
            
            # Overbought - expect pullback (relaxed thresholds)
            elif bb_position > 0.7 and rsi > 60:  # Relaxed from 0.8 and 70
                confidence = 0.6 + (rsi - 60) / 100
                
                return {
                    'action': 'SELL',
                    'confidence': min(0.85, confidence),
                    'expected_rr': 1.5,
                    'reason': 'Overbought mean reversion (bootstrap)',
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in mean reversion alpha: {e}")
            return None


class BreakoutAlpha(AlphaStrategy):
    """Breakout strategy"""
    
    def __init__(self):
        super().__init__("breakout_v2")
    
    def generate_signal(self, features: Dict) -> Optional[Dict]:
        """
        Breakout signal based on:
        - Price position in range
        - Volume surge
        - Volatility expansion
        """
        try:
            price_position = features.get('price_position', 0.5)
            rvol = features.get('rvol', 1.0)
            vol_ratio = features.get('vol_ratio', 1.0)
            bb_width = features.get('bb_width', 0)
            
            # Breakout conditions: high volume + volatility expansion
            if rvol > 1.5 and vol_ratio > 1.3:
                # Upside breakout
                if price_position > 0.9 and bb_width > 0.025:
                    confidence = 0.75 + min(0.15, (rvol - 1.5) / 10)
                    
                    return {
                        'action': 'BUY',
                        'confidence': confidence,
                        'expected_rr': 2.5,
                        'reason': 'Upside breakout with volume',
                    }
                
                # Downside breakout
                elif price_position < 0.1 and bb_width > 0.025:
                    confidence = 0.75 + min(0.15, (rvol - 1.5) / 10)
                    
                    return {
                        'action': 'SELL',
                        'confidence': confidence,
                        'expected_rr': 2.5,
                        'reason': 'Downside breakout with volume',
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in breakout alpha: {e}")
            return None


class VolumeAlpha(AlphaStrategy):
    """Volume-based strategy"""
    
    def __init__(self):
        super().__init__("volume_v1")
    
    def generate_signal(self, features: Dict) -> Optional[Dict]:
        """
        Volume signal based on:
        - CVD (Cumulative Volume Delta)
        - VPIN (informed trading)
        - Volume trend
        """
        try:
            cvd = features.get('cvd', 0)
            vpin = features.get('vpin', 0)
            volume_trend = features.get('volume_trend', 0)
            rvol = features.get('rvol', 1.0)
            
            # Strong buying pressure
            if cvd > 1000 and vpin > 0.6 and volume_trend > 0.2 and rvol > 1.3:
                confidence = 0.7 + min(0.2, vpin - 0.6)
                
                return {
                    'action': 'BUY',
                    'confidence': confidence,
                    'expected_rr': 1.8,
                    'reason': 'Strong buying volume',
                }
            
            # Strong selling pressure
            elif cvd < -1000 and vpin > 0.6 and volume_trend > 0.2 and rvol > 1.3:
                confidence = 0.7 + min(0.2, vpin - 0.6)
                
                return {
                    'action': 'SELL',
                    'confidence': confidence,
                    'expected_rr': 1.8,
                    'reason': 'Strong selling volume',
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in volume alpha: {e}")
            return None


class SentimentAlpha(AlphaStrategy):
    """Sentiment-driven strategy"""
    
    def __init__(self):
        super().__init__("sentiment_v1")
    
    def generate_signal(self, features: Dict) -> Optional[Dict]:
        """
        Sentiment signal based on:
        - Market sentiment score
        - Macro indicators (VIX, DXY)
        """
        try:
            sentiment = features.get('sentiment', 0)
            vix_z = features.get('vix_z', 0)
            dxy_z = features.get('dxy_z', 0)
            
            # Strong positive sentiment + low fear
            if sentiment > 0.5 and vix_z < -1.0:
                confidence = 0.65 + min(0.25, sentiment - 0.5)
                
                return {
                    'action': 'BUY',
                    'confidence': confidence,
                    'expected_rr': 1.5,
                    'reason': 'Positive sentiment, low fear',
                }
            
            # Strong negative sentiment + high fear
            elif sentiment < -0.5 and vix_z > 1.0:
                confidence = 0.65 + min(0.25, abs(sentiment) - 0.5)
                
                return {
                    'action': 'SELL',
                    'confidence': confidence,
                    'expected_rr': 1.5,
                    'reason': 'Negative sentiment, high fear',
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in sentiment alpha: {e}")
            return None


class CorrelationArbitrageAlpha(AlphaStrategy):
    """Correlation arbitrage strategy"""
    
    def __init__(self):
        super().__init__("corr_arb_v1")
    
    def generate_signal(self, features: Dict) -> Optional[Dict]:
        """
        Correlation arbitrage based on:
        - Cross-asset correlations
        - Divergence from normal relationships
        """
        try:
            corr_nas100 = features.get('corr_nas100', 0)
            corr_xauusd = features.get('corr_xauusd', 0)
            dxy_z = features.get('dxy_z', 0)
            
            # Example: Gold typically inverse to USD
            # If DXY strong but gold not falling, expect gold to catch up
            if dxy_z > 1.5 and corr_xauusd > -0.3:  # Correlation broken
                confidence = 0.65
                
                return {
                    'action': 'SELL',  # Sell gold
                    'confidence': confidence,
                    'expected_rr': 1.6,
                    'reason': 'Gold-USD correlation divergence',
                }
            
            # Opposite scenario
            elif dxy_z < -1.5 and corr_xauusd < 0.3:
                confidence = 0.65
                
                return {
                    'action': 'BUY',  # Buy gold
                    'confidence': confidence,
                    'expected_rr': 1.6,
                    'reason': 'Gold-USD correlation convergence',
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in correlation arbitrage alpha: {e}")
            return None


# Alpha registry
ALPHA_STRATEGIES = {
    'momentum_v3': MomentumAlpha(),
    'mean_revert_v2': MeanReversionAlpha(),
    'breakout_v2': BreakoutAlpha(),
    'volume_v1': VolumeAlpha(),
    'sentiment_v1': SentimentAlpha(),
    'corr_arb_v1': CorrelationArbitrageAlpha(),
}


def get_alpha(alpha_id: str) -> Optional[AlphaStrategy]:
    """Get alpha strategy by ID"""
    return ALPHA_STRATEGIES.get(alpha_id)


def get_all_alphas() -> Dict[str, AlphaStrategy]:
    """Get all alpha strategies"""
    return ALPHA_STRATEGIES
