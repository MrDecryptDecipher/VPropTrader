"""
Trade Simulator
Simulates realistic trade execution with slippage, spreads, and market impact
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class SimulatedTrade:
    """Result of a simulated trade"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    exit_reason: str  # TP, SL, TIME
    slippage_cost: float
    spread_cost: float
    holding_hours: float
    mae: float  # Maximum Adverse Excursion
    mfe: float  # Maximum Favorable Excursion


class TradeSimulator:
    """Simulate realistic trade execution"""
    
    def __init__(self):
        # Spread costs by symbol (in pips)
        self.spreads = {
            'NAS100': 2.5,
            'XAUUSD': 3.0,
            'EURUSD': 1.5,
            'GBPUSD': 2.0,
            'USDJPY': 1.8,
        }
        
        # Base slippage (in pips)
        self.base_slippage = 0.5
    
    def simulate_trade(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        lots: float,
        entry_time: datetime,
        bars_df: pd.DataFrame,
        max_holding_hours: int = 48
    ) -> SimulatedTrade:
        """
        Simulate a trade from entry to exit
        
        Args:
            symbol: Trading symbol
            action: 'BUY' or 'SELL'
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            lots: Position size
            entry_time: Entry datetime
            bars_df: Future price bars for simulation
            max_holding_hours: Maximum holding time
        
        Returns:
            SimulatedTrade with results
        """
        # Calculate costs
        spread = self.spreads.get(symbol, 2.0)
        slippage = self._calculate_slippage(lots, symbol)
        
        # Adjust entry price for spread and slippage
        if action == 'BUY':
            actual_entry = entry_price + (spread + slippage) * 0.0001
        else:  # SELL
            actual_entry = entry_price - (spread + slippage) * 0.0001
        
        spread_cost = spread * lots * 0.0001 * entry_price
        slippage_cost = slippage * lots * 0.0001 * entry_price
        
        # Simulate price movement
        exit_time = entry_time
        exit_price = actual_entry
        exit_reason = "TIME"
        mae = 0.0  # Maximum Adverse Excursion
        mfe = 0.0  # Maximum Favorable Excursion
        
        # Track through each bar
        for idx, row in bars_df.iterrows():
            if idx <= entry_time:
                continue
            
            bar_time = idx
            bar_high = row['high']
            bar_low = row['low']
            bar_close = row['close']
            
            # Calculate excursions
            if action == 'BUY':
                favorable = bar_high - actual_entry
                adverse = actual_entry - bar_low
            else:  # SELL
                favorable = actual_entry - bar_low
                adverse = bar_high - actual_entry
            
            mfe = max(mfe, favorable)
            mae = max(mae, adverse)
            
            # Check stop loss
            if action == 'BUY' and bar_low <= stop_loss:
                exit_price = stop_loss - slippage * 0.0001  # Slippage on exit
                exit_time = bar_time
                exit_reason = "SL"
                break
            elif action == 'SELL' and bar_high >= stop_loss:
                exit_price = stop_loss + slippage * 0.0001
                exit_time = bar_time
                exit_reason = "SL"
                break
            
            # Check take profit
            if action == 'BUY' and bar_high >= take_profit:
                exit_price = take_profit - slippage * 0.0001
                exit_time = bar_time
                exit_reason = "TP"
                break
            elif action == 'SELL' and bar_low <= take_profit:
                exit_price = take_profit + slippage * 0.0001
                exit_time = bar_time
                exit_reason = "TP"
                break
            
            # Check max holding time
            holding_hours = (bar_time - entry_time).total_seconds() / 3600
            if holding_hours >= max_holding_hours:
                exit_price = bar_close
                exit_time = bar_time
                exit_reason = "TIME"
                break
        
        # Calculate PnL
        if action == 'BUY':
            pnl = (exit_price - actual_entry) * lots
        else:  # SELL
            pnl = (actual_entry - exit_price) * lots
        
        # Subtract costs
        pnl -= (spread_cost + slippage_cost)
        
        pnl_pct = (pnl / (actual_entry * lots)) * 100
        
        holding_hours = (exit_time - entry_time).total_seconds() / 3600
        
        return SimulatedTrade(
            entry_time=entry_time,
            exit_time=exit_time,
            entry_price=actual_entry,
            exit_price=exit_price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=exit_reason,
            slippage_cost=slippage_cost,
            spread_cost=spread_cost,
            holding_hours=holding_hours,
            mae=mae,
            mfe=mfe
        )
    
    def _calculate_slippage(self, lots: float, symbol: str) -> float:
        """Calculate slippage based on order size"""
        # Larger orders = more slippage
        size_factor = 1.0 + (lots - 0.01) * 0.1
        return self.base_slippage * size_factor
