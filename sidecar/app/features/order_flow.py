"""
Order Flow Analysis
Advanced features for detecting Whale activity and hidden liquidity.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

class OrderFlowAnalyzer:
    """
    Analyzes trade ticks for aggressive buying/selling and hidden liquidity.
    """
    
    @staticmethod
    def calculate_delta(trades_df: pd.DataFrame) -> float:
        """
        Calculate Cumulative Volume Delta (CVD) for a set of trades.
        Delta = Buy Volume - Sell Volume
        
        Args:
            trades_df: DataFrame with ['price', 'size', 'side'] (side: 'buy' or 'sell')
            
        Returns:
            Net Delta (float)
        """
        try:
            if trades_df.empty:
                return 0.0
                
            # If 'side' column exists (explicit aggressor side)
            if 'side' in trades_df.columns:
                buy_vol = trades_df[trades_df['side'] == 'buy']['size'].sum()
                sell_vol = trades_df[trades_df['side'] == 'sell']['size'].sum()
                return float(buy_vol - sell_vol)
            
            # Fallback: Tick rule (Price change direction)
            # If price > prev_price -> Buy
            # If price < prev_price -> Sell
            price_diff = trades_df['price'].diff().fillna(0)
            
            buy_vol = trades_df[price_diff > 0]['size'].sum()
            sell_vol = trades_df[price_diff < 0]['size'].sum()
            
            return float(buy_vol - sell_vol)
            
        except Exception as e:
            # logger.error(f"Error calculating Delta: {e}")
            return 0.0

    @staticmethod
    def detect_large_prints(trades_df: pd.DataFrame, threshold: float = 10.0) -> bool:
        """
        Detect if any single trade exceeded the 'Whale' threshold.
        
        Args:
            trades_df: DataFrame with ['size']
            threshold: Size threshold in lots
            
        Returns:
            True if large print detected
        """
        try:
            if trades_df.empty:
                return False
                
            max_trade = trades_df['size'].max()
            return max_trade >= threshold
            
        except Exception as e:
            return False

    @staticmethod
    def detect_icebergs(trades_df: pd.DataFrame, price_level: float, visible_liquidity: float) -> bool:
        """
        Detect Iceberg orders (Hidden Liquidity).
        Triggered if volume traded at a price level >> visible liquidity at that level.
        
        Args:
            trades_df: DataFrame of trades at this specific price level
            price_level: The price being analyzed
            visible_liquidity: Snapshot of limit order book size at this price
            
        Returns:
            True if iceberg detected
        """
        try:
            if trades_df.empty:
                return False
                
            total_volume = trades_df['size'].sum()
            
            # If we traded 150% of what was visible, there was hidden liquidity
            return total_volume > (visible_liquidity * 1.5)
            
        except Exception as e:
            return False

# Global instance
order_flow = OrderFlowAnalyzer()
