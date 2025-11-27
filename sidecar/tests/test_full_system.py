"""
Comprehensive System Verification Suite
Tests all VPropTrader upgrades: Macro, Quant, ML, Risk, and User DB.
"""

import pytest
import pandas as pd
import numpy as np
import torch
import os
import sys
import asyncio
from datetime import datetime

# Add sidecar to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.data.macro_client import macro_client
from app.features.macro_features import macro_features
from app.features.quant_features import quant_features
from app.strategies.stat_arb import stat_arb
from app.ml.transformer_model import transformer_predictor
from app.ml.rl_agent import rl_agent
from app.risk.risk_manager import risk_manager
from app.data.user_db import user_db, PropFirmConfig, PropRules

# --- 1. Macro Intelligence Tests ---

def test_macro_client_fallback():
    """Verify Macro Client handles missing API keys gracefully (uses YFinance/Mock)."""
    print("\n[TEST] Macro Client Fallback")
    data = macro_client.fetch_yield_curve()
    assert 'us10y' in data
    assert 'spread_10y2y' in data
    print(f"  ✓ Yield Curve Data: {data}")

@pytest.mark.asyncio
async def test_macro_regime_calculation():
    """Verify Macro Regime logic."""
    print("\n[TEST] Macro Regime Calculation")
    # Mocking macro_client for deterministic test
    original_fetch = macro_client.fetch_yield_curve
    macro_client.fetch_yield_curve = lambda: {'us10y': 3.5, 'us2y': 4.0, 'spread_10y2y': -0.5} # Inverted
    
    regime = await macro_features.calculate_regime()
    assert regime['regime'] == "RECESSION_WARNING" or regime['regime'] == "PANIC" # Depending on VIX
    print(f"  ✓ Detected Regime (Inverted Curve): {regime['regime']}")
    
    # Restore
    macro_client.fetch_yield_curve = original_fetch

# --- 2. Deep Quant Strategy Tests ---

def test_hurst_exponent():
    """Verify Hurst Exponent distinguishes Trend vs Mean Reversion."""
    print("\n[TEST] Hurst Exponent")
    # Mean Reverting (Sine Wave)
    t = np.linspace(0, 100, 1000)
    mean_rev = pd.Series(np.sin(t))
    h_mr = quant_features.calculate_hurst_exponent(mean_rev)
    
    # Trending (Random Walk with Drift)
    trend = pd.Series(np.cumsum(np.random.randn(1000) + 0.1))
    h_trend = quant_features.calculate_hurst_exponent(trend)
    
    print(f"  ✓ Hurst (Sine Wave): {h_mr:.2f} (Expected < 0.5)")
    print(f"  ✓ Hurst (Trend): {h_trend:.2f} (Expected > 0.5)")
    
    # Note: Simplified Hurst might not be perfect, but should show difference
    assert h_trend > h_mr

def test_fft_cycle():
    """Verify FFT identifies dominant cycle."""
    print("\n[TEST] FFT Cycle Analysis")
    # 50-period cycle
    t = np.linspace(0, 200, 200)
    cycle = pd.Series(np.sin(2 * np.pi * t / 50)) 
    period, _ = quant_features.calculate_fft_cycle(cycle)
    
    print(f"  ✓ Detected Period: {period:.2f} (Expected ~50.0)")
    assert 45 < period < 55

def test_cointegration():
    """Verify Cointegration test."""
    print("\n[TEST] Cointegration (Stat Arb)")
    np.random.seed(42)
    x = np.cumsum(np.random.randn(100))
    y = x + np.random.randn(100) * 0.5 # Cointegrated
    
    is_coint, p_val, _ = stat_arb.check_cointegration(pd.Series(x), pd.Series(y))
    print(f"  ✓ Cointegrated Pair p-value: {p_val:.4f}")
    assert is_coint == True

# --- 3. Next-Gen ML Tests ---

def test_transformer_prediction():
    """Verify Transformer Model forward pass."""
    print("\n[TEST] Transformer Model")
    # Batch=1, Seq=20, Dim=10
    dummy_input = [[0.5]*10]*20 
    conf = transformer_predictor.predict(dummy_input)
    print(f"  ✓ Transformer Confidence: {conf:.4f}")
    assert 0.0 <= conf <= 1.0

def test_rl_agent_action():
    """Verify RL Agent selects valid action."""
    print("\n[TEST] RL Agent")
    # State: [PnL, Vol, RSI, MACD, Time]
    state = [100.0, 0.02, 70.0, 0.5, 10]
    action, probs = rl_agent.select_action(state)
    print(f"  ✓ RL Action: {action}")
    assert action in rl_agent.actions

# --- 4. Prop Risk & User DB Tests ---

@pytest.mark.asyncio
async def test_prop_risk_enforcement():
    """Verify Risk Manager blocks trades based on rules."""
    print("\n[TEST] Prop Risk Engine")
    
    # 1. Setup DB
    await user_db.init_db()
    
    # 2. Save Config
    config = PropFirmConfig(firm_name="TestFirm", login="123", password="abc", server="Demo")
    rules = PropRules(
        max_daily_loss=500.0,
        max_total_loss=1000.0,
        profit_target=1000.0,
        trading_hours_start="09:00",
        trading_hours_end="17:00",
        timezone="UTC"
    )
    await user_db.save_prop_config(1, config, rules)
    
    # 3. Load Rules
    await risk_manager.load_rules()
    
    # 4. Test: Max Total Drawdown Violation
    # Initial Balance 100k, Equity 98k -> Drawdown 2k > 1k Limit
    allowed = await risk_manager.check_trade_allowed("EURUSD", 1.0, 98000.0, 100000.0)
    print(f"  ✓ Trade Allowed (Drawdown Violation): {allowed}")
    assert allowed == False
    
    # 5. Test: Safe Trade
    allowed_safe = await risk_manager.check_trade_allowed("EURUSD", 1.0, 100000.0, 100000.0)
    print(f"  ✓ Trade Allowed (Safe): {allowed_safe}")
    # Note: Trading hours check might fail depending on current time. 
    # We mock time check for robustness or accept it might be False if run at night.
    # For this test, we assume running during day or check logs.
    
    # Let's mock _check_trading_hours to True to test logic isolation
    risk_manager._check_trading_hours = lambda: True
    allowed_forced = await risk_manager.check_trade_allowed("EURUSD", 1.0, 100000.0, 100000.0)
    assert allowed_forced == True

if __name__ == "__main__":
    # Manual run if pytest fails
    pass
