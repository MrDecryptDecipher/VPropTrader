"""
Macro Features
Calculates Macro Regime (Risk-On/Off, Inflationary/Deflationary).
"""

import logging
from typing import Dict, Any

try:
    from app.data.macro_client import macro_client
except ImportError:
    macro_client = None

logger = logging.getLogger(__name__)

class MacroFeatureEngineer:
    """
    Analyzes macro data to determine market regime.
    """
    
    async def calculate_regime(self) -> Dict[str, Any]:
        """
        Determine the current Macro Regime.
        
        Regimes:
        - GOLDILOCKS: Growth +, Inflation - (Risk-On)
        - REFLATION: Growth +, Inflation + (Commodities/Value)
        - STAGFLATION: Growth -, Inflation + (Defensive/Cash)
        - DEFLATION/RECESSION: Growth -, Inflation - (Bonds)
        """
        regime = "NEUTRAL"
        score = 0.0
        details = {}
        
        if not macro_client:
            return {'regime': regime, 'score': score, 'details': details}
            
        try:
            # 1. Fetch Data
            yields = macro_client.fetch_yield_curve()
            inflation = macro_client.fetch_inflation_expectations()
            vix = macro_client.fetch_vix()
            
            # 2. Analyze
            # Yield Curve Inversion = Recession Signal
            is_inverted = yields.get('spread_10y2y', 0) < 0
            
            # VIX > 30 = Panic/Crash
            is_panic = vix > 30
            
            # Simple Regime Logic
            if is_panic:
                regime = "PANIC"
                score = -1.0 # Max Risk-Off
            elif is_inverted:
                regime = "RECESSION_WARNING"
                score = -0.5 # Defensive
            elif inflation > 3.0:
                regime = "INFLATIONARY"
                score = 0.0 # Selective (Energy/Value)
            else:
                regime = "GOLDILOCKS"
                score = 1.0 # Max Risk-On (Tech/Growth)
                
            details = {
                'yield_spread': yields.get('spread_10y2y'),
                'inflation_exp': inflation,
                'vix': vix,
                'is_inverted': is_inverted
            }
            
            logger.info(f"🌍 Macro Regime: {regime} (Score: {score})")
            
        except Exception as e:
            logger.error(f"Error calculating macro regime: {e}")
            
        return {'regime': regime, 'score': score, 'details': details}

# Global instance
macro_features = MacroFeatureEngineer()
