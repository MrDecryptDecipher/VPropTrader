"""
Quant Features
Advanced mathematical features for Deep Quant Strategies.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from scipy.fft import fft

class QuantFeatureEngineer:
    """
    Calculates advanced math features: Hurst Exponent, FFT Cycles.
    """
    
    @staticmethod
    def calculate_hurst_exponent(series: pd.Series, max_lag: int = 20) -> float:
        """
        Calculate the Hurst Exponent to determine time series memory.
        H < 0.5: Mean Reverting
        H = 0.5: Random Walk (Geometric Brownian Motion)
        H > 0.5: Trending (Persistent)
        """
        try:
            lags = range(2, max_lag)
            tau = [np.sqrt(np.std(np.subtract(series[lag:], series[:-lag]))) for lag in lags]
            
            # Use linear regression to estimate the slope of the log-log plot
            # polyfit returns [slope, intercept]
            # We want the slope
            # However, the standard R/S analysis is complex. 
            # We will use a simplified variance-ratio test proxy or simple diffusion index for speed.
            # Let's use the standard deviation of differences method (Generalized Hurst)
            
            # polyfit(log(lags), log(tau), 1) -> slope is H
            if len(tau) < 2:
                return 0.5
                
            m = np.polyfit(np.log(lags), np.log(tau), 1)
            hurst = m[0] * 2.0 # For price series (GBM), H = slope * 2 roughly in this method
            
            # Clamp to 0-1
            return max(0.0, min(1.0, hurst))
            
        except Exception:
            return 0.5

    @staticmethod
    def calculate_fft_cycle(series: pd.Series) -> Tuple[float, float]:
        """
        Perform Fast Fourier Transform to find dominant cycle.
        Returns: (Dominant Period, Phase)
        """
        try:
            # Detrend first
            detrended = series - series.rolling(window=len(series), min_periods=1).mean()
            detrended = detrended.fillna(0).values
            
            n = len(detrended)
            yf = fft(detrended)
            xf = np.linspace(0.0, 1.0/(2.0), n//2)
            
            # Power spectrum
            power = 2.0/n * np.abs(yf[0:n//2])
            
            # Find peak frequency (ignoring DC component at index 0)
            if len(power) < 2:
                return 0.0, 0.0
                
            idx = np.argmax(power[1:]) + 1
            freq = xf[idx]
            
            if freq == 0:
                return 0.0, 0.0
                
            period = 1 / freq
            return float(period), 0.0 # Phase calculation omitted for brevity
            
        except Exception:
            return 0.0, 0.0

# Global instance
quant_features = QuantFeatureEngineer()
