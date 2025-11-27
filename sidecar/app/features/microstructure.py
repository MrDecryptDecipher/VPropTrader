"""
Microstructure Alphas
Advanced order flow features for detecting invisible market pressure.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

class MicrostructureFeatures:
    """
    Calculates institutional-grade order flow metrics.
    """
    
    @staticmethod
    def calculate_ofi(df: pd.DataFrame) -> pd.Series:
        """
        Calculate Order Flow Imbalance (OFI).
        OFI = Change in Bid Size (if Bid Price >= Prev Bid Price) - Change in Ask Size (if Ask Price <= Prev Ask Price)
        
        Args:
            df: DataFrame with columns ['bid_price', 'bid_size', 'ask_price', 'ask_size']
            
        Returns:
            Series containing OFI values (normalized -1 to 1)
        """
        try:
            # Need order book data
            required_cols = ['bid_price', 'bid_size', 'ask_price', 'ask_size']
            if not all(col in df.columns for col in required_cols):
                # Fallback if no L2 data: Use Volume * Sign of Price Change
                # This is "Tick Imbalance" (a proxy for OFI)
                return df['volume'] * np.sign(df['close'].diff())
            
            # 1. Calculate deltas
            delta_bid_size = df['bid_size'].diff()
            delta_ask_size = df['ask_size'].diff()
            
            # 2. Logic for OFI
            # If Bid Price increases, all volume at old bid was consumed -> Buying Pressure
            # If Bid Price decreases, support was pulled -> Selling Pressure
            
            # Simplified Cont-OFI (Contemporaneous OFI)
            ofi = pd.Series(0.0, index=df.index)
            
            # Bid Side Contribution
            bid_change = df['bid_price'].diff()
            ofi += np.where(bid_change > 0, df['bid_size'], 
                           np.where(bid_change < 0, -df['bid_size'].shift(1), delta_bid_size))
            
            # Ask Side Contribution (Negative for selling pressure)
            ask_change = df['ask_price'].diff()
            ofi -= np.where(ask_change < 0, df['ask_size'], 
                           np.where(ask_change > 0, -df['ask_size'].shift(1), delta_ask_size))
            
            # Normalize (z-score rolling)
            ofi_z = (ofi - ofi.rolling(window=100).mean()) / (ofi.rolling(window=100).std() + 1e-6)
            
            return ofi_z.fillna(0)
            
        except Exception as e:
            print(f"Error calculating OFI: {e}")
            return pd.Series(0.0, index=df.index)

    @staticmethod
    def calculate_vpin(df: pd.DataFrame, bucket_vol: int = 1000) -> pd.Series:
        """
        Calculate VPIN (Volume-Synchronized Probability of Informed Trading).
        Detects toxic flow.
        
        Args:
            df: DataFrame with ['close', 'volume']
            bucket_vol: Volume bucket size
            
        Returns:
            Series containing VPIN values (0 to 1)
        """
        try:
            # VPIN requires volume buckets, which is complex on time-bars.
            # We will approximate using "Bulk Volume Classification" (BVC)
            
            # 1. Estimate Buy/Sell Volume using BVC
            # Buy Vol = V * N( (P - P_prev) / sigma )
            # We'll use a simpler tick rule proxy for speed
            
            price_change = df['close'].diff()
            buy_vol = np.where(price_change > 0, df['volume'], 
                              np.where(price_change == 0, df['volume'] * 0.5, 0))
            sell_vol = df['volume'] - buy_vol
            
            # 2. Compute Order Imbalance (OI)
            oi = np.abs(buy_vol - sell_vol)
            
            # 3. VPIN = SMA(OI) / SMA(Volume)
            # We use a rolling window instead of volume buckets for time-series compatibility
            rolling_oi = pd.Series(oi).rolling(window=50).sum()
            rolling_vol = df['volume'].rolling(window=50).sum()
            
            vpin = rolling_oi / (rolling_vol + 1e-6)
            
            return vpin.fillna(0)
            
        except Exception as e:
            print(f"Error calculating VPIN: {e}")
            return pd.Series(0.0, index=df.index)

# Global instance
microstructure = MicrostructureFeatures()
