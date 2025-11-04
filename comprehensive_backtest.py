#!/usr/bin/env python3
"""
Advanced Comprehensive Backtesting System
- Uses real historical market data from database
- Walk-forward analysis with multiple time periods
- Realistic market simulation with slippage, spreads, and execution delays
- Multi-asset, multi-strategy testing across different market sessions
- Detailed performance analytics and strategy optimization recommendations
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sidecar'))

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from loguru import logger
import sqlite3
from dataclasses import dataclass, field
from collections import defaultdict
import json

# Import components
from app.scanner.alphas import get_all_alphas, AlphaStrategy
from app.ml.inference import ml_inference
from app.risk.position_sizing import position_sizer


@dataclass
class Trade:
    """Comprehensive trade record"""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    action: str  # BUY or SELL
    alpha_id: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    lots: float
    pnl: float
    pnl_pct: float
    equity_before: float
    equity_after: float
    exit_reason: str  # TP, SL, TIME, MANUAL
    q_star: float
    confidence: float
    p_win: float
    expected_rr: float
    actual_rr: float
    slippage: float
    spread_cost: float
    holding_time_hours: float
    mae: float  # Maximum Adverse Excursion
    mfe: float  # Maximum Favorable Excursion
    features: Dict = field(default_factory=dict)
    market_session: str = ""  # LONDON, NY, ASIAN, OVERLAP
    
    def to_dict(self) -> Dict:
        return {
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat(),
            'symbol': self.symbol,
            'action': self.action,
            'alpha_id': self.alpha_id,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
