"""
Complete Backtest Engine - Missing components from engine.py
Handles trade simulation and walk-forward analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from loguru import logger

from ..data.historical_data_loader import historical_loader
from ..data.historical_features import historical_feature_calculator
from .trade_simulator import TradeSimulator


def _simulate_trade_to_time(trade_info: Dict, current_time: datetime, symbol_data: Dict) -> Dict:
    """Simulate trade execution up to current time"""
    symbol = trade_info['symbol']
    
    if symbol not in symbol_data:
        return None
    
    df = symbol_data[symbol]
    
    # Get bars between entry and current time
    entry_time = trade_info['entry_time']
    relevant_bars = df[(df.index >= entry_time) & (df.index <= current_time)]
    
    if relevant_bars.empty:
        return None
    
    # Check if trade should exit
    simulator = TradeSimulator()
    
    result = simulator.simulate_trade(
        symbol=symbol,
        action=trade_info['action'],
        entry_price=trade_info['entry_price'],
        stop_loss=trade_info['stop_loss'],
        take_profit=trade_info['take_profit'],
        lots=trade_info['lots'],
        entry_time=entry_time,
        bars_df=relevant_bars,
        max_holding_hours=48
    )
    
    # Check if trade completed
    if result.exit_time <= current_time:
        return result
    
    return None


def _force_close_trade(trade_info: Dict, close_time: datetime, symbol_data: Dict) -> Dict:
    """Force close a trade at specified time"""
    symbol = trade_info['symbol']
    
    if symbol not in symbol_data:
        return None
    
    df = symbol_data[symbol]
    
    # Get bars up to close time
    entry_time = trade_info['entry_time']
    relevant_bars = df[(df.index >= entry_time) & (df.index <= close_time)]
    
    if relevant_bars.empty:
        return None
    
    simulator = TradeSimulator()
    
    result = simulator.simulate_trade(
        symbol=symbol,
        action=trade_info['action'],
        entry_price=trade_info['entry_price'],
        stop_loss=trade_info['stop_loss'],
        take_profit=trade_info['take_profit'],
        lots=trade_info['lots'],
        entry_time=entry_time,
        bars_df=relevant_bars,
        max_holding_hours=1  # Force immediate close
    )
    
    return result


def _build_equity_curve(trades: List) -> pd.DataFrame:
    """Build equity curve from trades"""
    if not trades:
        return pd.DataFrame()
    
    equity_data = []
    cumulative_pnl = 0
    
    for trade in trades:
        cumulative_pnl += trade.pnl
        equity_data.append({
            'time': trade.exit_time,
            'equity': 1000 + cumulative_pnl,
            'pnl': cumulative_pnl
        })
    
    df = pd.DataFrame(equity_data)
    df.set_index('time', inplace=True)
    
    return df


def _calculate_daily_returns(equity_curve: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily returns from equity curve"""
    if equity_curve.empty:
        return pd.DataFrame()
    
    daily = equity_curve.resample('D').last().ffill()
    daily['return'] = daily['equity'].pct_change()
    
    return daily


def _calculate_performance_metrics(results) -> Dict:
    """Calculate performance metrics from backtest results"""
    if not results.trades:
        return {}
    
    trades_df = pd.DataFrame([{
        'pnl': t.pnl,
        'pnl_pct': t.pnl_pct,
        'holding_hours': t.holding_hours,
        'exit_reason': t.exit_reason,
        'mae': t.mae,
        'mfe': t.mfe,
        'slippage_cost': t.slippage_cost,
        'spread_cost': t.spread_cost,
        'is_winner': t.pnl > 0
    } for t in results.trades])
    
    total_trades = len(trades_df)
    winning_trades = trades_df['is_winner'].sum()
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': total_trades - winning_trades,
        'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
        'total_pnl': trades_df['pnl'].sum(),
        'avg_trade_pnl': trades_df['pnl'].mean(),
        'avg_holding_hours': trades_df['holding_hours'].mean()
    }


def _calculate_compliance_metrics(results) -> Dict:
    """Calculate VPropTrader compliance metrics"""
    if not results.trades:
        return {}
    
    # Check daily loss limits
    trades_by_date = {}
    for trade in results.trades:
        date = trade.entry_time.date()
        if date not in trades_by_date:
            trades_by_date[date] = []
        trades_by_date[date].append(trade.pnl)
    
    daily_pnl = [sum(trades) for trades in trades_by_date.values()]
    worst_day = min(daily_pnl) if daily_pnl else 0
    
    total_pnl = sum(t.pnl for t in results.trades)
    
    return {
        'worst_daily_loss': worst_day,
        'daily_loss_compliant': worst_day >= -50,
        'total_loss': min(0, total_pnl),
        'total_loss_compliant': total_pnl >= -100,
        'profit_target_reached': total_pnl >= 100
    }


def _calculate_alpha_performance(results) -> Dict:
    """Calculate performance by alpha strategy"""
    if not results.trades:
        return {}
    
    alpha_stats = {}
    
    for trade in results.trades:
        alpha_id = trade.alpha_id
        
        if alpha_id not in alpha_stats:
            alpha_stats[alpha_id] = {
                'trades': 0,
                'wins': 0,
                'total_pnl': 0
            }
        
        alpha_stats[alpha_id]['trades'] += 1
        if trade.pnl > 0:
            alpha_stats[alpha_id]['wins'] += 1
        alpha_stats[alpha_id]['total_pnl'] += trade.pnl
    
    # Calculate win rates
    for alpha_id in alpha_stats:
        stats = alpha_stats[alpha_id]
        stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
    
    return alpha_stats


def _calculate_symbol_performance(results) -> Dict:
    """Calculate performance by symbol"""
    if not results.trades:
        return {}
    
    symbol_stats = {}
    
    for trade in results.trades:
        symbol = trade.symbol
        
        if symbol not in symbol_stats:
            symbol_stats[symbol] = {
                'trades': 0,
                'wins': 0,
                'total_pnl': 0
            }
        
        symbol_stats[symbol]['trades'] += 1
        if trade.pnl > 0:
            symbol_stats[symbol]['wins'] += 1
        symbol_stats[symbol]['total_pnl'] += trade.pnl
    
    # Calculate win rates
    for symbol in symbol_stats:
        stats = symbol_stats[symbol]
        stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
    
    return symbol_stats
