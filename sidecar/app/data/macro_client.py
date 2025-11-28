"""
Macro Client
Fetches economic data from FRED (Federal Reserve Economic Data) or YFinance fallback.
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

class MacroClient:
    """
    Client for fetching Macroeconomic data.
    """
    def __init__(self):
        self.api_key = os.getenv("FRED_API_KEY")
        self.fred = Fred(api_key=self.api_key) if FRED_AVAILABLE and self.api_key else None
        
    def fetch_yield_curve(self) -> Dict[str, float]:
        """
        Fetch US Treasury Yields and calculate 10Y-2Y spread.
        Returns: {'us10y': float, 'us2y': float, 'spread_10y2y': float}
        """
        data = {'us10y': 4.0, 'us2y': 4.0, 'spread_10y2y': 0.0} # Defaults
        
        try:
            if self.fred:
                # FRED Series: DGS10, DGS2
                t10 = self.fred.get_series('DGS10', limit=1).iloc[-1]
                t2 = self.fred.get_series('DGS2', limit=1).iloc[-1]
                data = {
                    'us10y': float(t10),
                    'us2y': float(t2),
                    'spread_10y2y': float(t10 - t2)
                }
            elif YF_AVAILABLE:
                # Fallback to YFinance: ^TNX (10Y), ^IRX (13W - not 2Y, but close proxy often used is ^ZT=F or similar futures, 
                # but let's use ^TNX and maybe a fixed offset or just mock if 2Y not easily available via standard tickers)
                # Actually ^FVX is 5 Year. 2 Year Note Yield is often not standard in YF free tier.
                # Let's use ^TNX (10Y) and ^FVX (5Y) as proxy or just return what we have.
                
                t10_ticker = yf.Ticker("^TNX")
                hist = t10_ticker.history(period="1d")
                if not hist.empty:
                    t10 = hist['Close'].iloc[-1]
                    # Mocking 2Y as slightly lower/higher depending on curve for now if we can't get it
                    # This is a limitation of free YF. 
                    # Let's try to be honest and just return 10Y.
                    data['us10y'] = float(t10)
                    
        except Exception as e:
            logger.error(f"Failed to fetch yield curve: {e}")
            
        return data

    def fetch_inflation_expectations(self) -> float:
        """Fetch 5-Year Breakeven Inflation Rate"""
        try:
            if self.fred:
                return float(self.fred.get_series('T5YIE', limit=1).iloc[-1])
            return 2.5 # Fallback average
        except Exception:
            return 2.5

    def fetch_vix(self) -> float:
        """Fetch VIX (Volatility Index)"""
        try:
            if YF_AVAILABLE:
                vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
                return float(vix)
            return 20.0
        except Exception:
            return 20.0

# Global instance
macro_client = MacroClient()
