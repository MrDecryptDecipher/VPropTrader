"""
Performance Analyzer
Calculates comprehensive performance metrics for backtest results
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Comprehensive performance statistics"""
    # Return metrics
    total_return: float
    total_return_pct: float
    cagr: float
    monthly_returns: List[float]
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    avg_drawdown: float
    
    # Trade metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_win_loss_ratio: float
    largest_win: float
    largest_loss: float
    
    # Consistency metrics
    max_consecutive_wins: int
    max_consecutive_losses: int
    avg_holding_hours: float
    avg_mae: float
    avg_mfe: float
    mae_mfe_ratio: float
    
    # VPropTrader compliance
    worst_daily_loss: float
    total_loss: float
    max_daily_profit: float
    daily_loss_violations: int
    total_loss_violations: int


class PerformanceAnalyzer:
    """Analyze backtest performance"""
    
    def calculate_metrics(
        self,
        trades_df: pd.DataFrame,
        initial_capital: float,
        equity_curve: pd.Series
    ) -> PerformanceMetrics:
        """Calculate all performance metrics"""
        
        if trades_df.empty:
            return self._get_empty_metrics()
        
        # Return metrics
        total_return = equity_curve.iloc[-1] - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        # CAGR
        days = (trades_df['exit_time'].max() - trades_df['entry_time'].min()).days
        years = max(days / 365.25, 1/365.25)
        cagr = (((equity_curve.iloc[-1] / initial_capital) ** (1/years)) - 1) * 100
        
        # Monthly returns
        monthly_returns = self._calculate_monthly_returns(trades_df, initial_capital)
        
        # Risk metrics
        returns = trades_df['pnl'] / initial_capital
        sharpe = self._calculate_sharpe(returns)
        sortino = self._calculate_sortino(returns)
        
        max_dd, max_dd_pct, avg_dd = self._calculate_drawdowns(equity_curve, initial_capital)
        
        calmar = cagr / max_dd_pct if max_dd_pct > 0 else 0
        
        # Trade metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        wins = trades_df[trades_df['pnl'] > 0]['pnl']
        losses = trades_df[trades_df['pnl'] < 0]['pnl']
        
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        
        profit_factor = abs(wins.sum() / losses.sum()) if len(losses) > 0 and losses.sum() != 0 else float('inf')
        avg_win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        largest_win = wins.max() if len(wins) > 0 else 0
        largest_loss = losses.min() if len(losses) > 0 else 0
        
        # Consistency metrics
        max_cons_wins, max_cons_losses = self._calculate_streaks(trades_df)
        
        avg_holding = trades_df['holding_hours'].mean()
        avg_mae = trades_df['mae'].mean()
        avg_mfe = trades_df['mfe'].mean()
        mae_mfe_ratio = avg_mae / avg_mfe if avg_mfe > 0 else 0
        
        # VPropTrader compliance
        daily_pnl = trades_df.groupby(trades_df['exit_time'].dt.date)['pnl'].sum()
        worst_daily = daily_pnl.min()
        max_daily = daily_pnl.max()
        total_loss = min(0, total_return)
        
        daily_violations = len(daily_pnl[daily_pnl < -50])
        total_violations = 1 if total_loss < -100 else 0
        
        return PerformanceMetrics(
            total_return=total_return,
            total_return_pct=total_return_pct,
            cagr=cagr,
            monthly_returns=monthly_returns,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            avg_drawdown=avg_dd,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_win_loss_ratio=avg_win_loss_ratio,
            largest_win=largest_win,
            largest_loss=largest_loss,
            max_consecutive_wins=max_cons_wins,
            max_consecutive_losses=max_cons_losses,
            avg_holding_hours=avg_holding,
            avg_mae=avg_mae,
            avg_mfe=avg_mfe,
            mae_mfe_ratio=mae_mfe_ratio,
            worst_daily_loss=worst_daily,
            total_loss=total_loss,
            max_daily_profit=max_daily,
            daily_loss_violations=daily_violations,
            total_loss_violations=total_violations
        )
    
    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        excess_returns = returns - risk_free_rate
        return (excess_returns.mean() / returns.std()) * np.sqrt(252)
    
    def _calculate_sortino(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sortino ratio"""
        if len(returns) == 0:
            return 0.0
        excess_returns = returns - risk_free_rate
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        return (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)
    
    def _calculate_drawdowns(
        self,
        equity_curve: pd.Series,
        initial_capital: float
    ) -> tuple:
        """Calculate drawdown metrics"""
        running_max = equity_curve.expanding().max()
        drawdown = equity_curve - running_max
        max_dd = abs(drawdown.min())
        max_dd_pct = (max_dd / initial_capital) * 100
        avg_dd = abs(drawdown[drawdown < 0].mean()) if len(drawdown[drawdown < 0]) > 0 else 0
        return max_dd, max_dd_pct, avg_dd
    
    def _calculate_streaks(self, trades_df: pd.DataFrame) -> tuple:
        """Calculate win/loss streaks"""
        wins = (trades_df['pnl'] > 0).astype(int)
        
        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for win in wins:
            if win:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
        
        return max_win_streak, max_loss_streak
    
    def _calculate_monthly_returns(
        self,
        trades_df: pd.DataFrame,
        initial_capital: float
    ) -> List[float]:
        """Calculate monthly returns"""
        monthly = trades_df.groupby(trades_df['exit_time'].dt.to_period('M'))['pnl'].sum()
        return [(pnl / initial_capital) * 100 for pnl in monthly]
    
    def _get_empty_metrics(self) -> PerformanceMetrics:
        """Return empty metrics"""
        return PerformanceMetrics(
            total_return=0, total_return_pct=0, cagr=0, monthly_returns=[],
            sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0,
            max_drawdown=0, max_drawdown_pct=0, avg_drawdown=0,
            total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0, profit_factor=0, avg_win=0, avg_loss=0,
            avg_win_loss_ratio=0, largest_win=0, largest_loss=0,
            max_consecutive_wins=0, max_consecutive_losses=0,
            avg_holding_hours=0, avg_mae=0, avg_mfe=0, mae_mfe_ratio=0,
            worst_daily_loss=0, total_loss=0, max_daily_profit=0,
            daily_loss_violations=0, total_loss_violations=0
        )
