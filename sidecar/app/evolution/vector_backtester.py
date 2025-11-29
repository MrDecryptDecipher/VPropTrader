"""
Vector Backtester Module
High-performance vectorized backtesting engine using Pandas/Numpy.
"""

import pandas as pd
import numpy as np
from loguru import logger
from typing import Dict, Any, Tuple
from app.evolution.strategy_genome import StrategyGenome

class VectorBacktester:
    """
    Evaluates strategy performance using vectorized operations.
    Much faster than event-driven backtesting for initial screening.
    """
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.00007):
        self.initial_capital = initial_capital
        self.commission = commission # Standard forex commission

    def run_backtest(self, genome: StrategyGenome, data: pd.DataFrame) -> Tuple[float, Dict[str, float]]:
        """
        Executes the strategy code against the provided dataframe.
        Returns (fitness_score, metrics_dict).
        """
        try:
            # Create a copy to avoid modifying original data
            df = data.copy()
            
            # Define execution context
            # Pass imports in globals so they are available to functions defined in the code
            exec_globals = {
                "pd": pd,
                "np": np,
            }
            
            exec_locals = {
                "df": df
            }
            
            # Wrap code to ensure it produces a 'signal' column
            # The strategy code is expected to manipulate 'df' and create a 'signal' column
            # signal: 1 (Buy), -1 (Sell), 0 (Hold)
            
            wrapped_code = f"""
def strategy_logic(df):
    # Default signal
    df['signal'] = 0
    
    # User Strategy Code
{self._indent_code(genome.code)}
    
    return df

df = strategy_logic(df)
"""
            
            # Execute safely
            exec(wrapped_code, exec_globals, exec_locals)
            df = exec_locals['df']
            
            if 'signal' not in df.columns:
                logger.warning(f"Strategy {genome.id} did not produce a 'signal' column.")
                return -1.0, {}

            # Calculate Returns
            # Shift signal by 1 because signal at T acts on price move at T+1
            df['position'] = df['signal'].shift(1).fillna(0)
            
            # Log Returns: ln(Close / Close_prev)
            df['log_ret'] = np.log(df['Close'] / df['Close'].shift(1))
            
            # Strategy Returns: position * log_ret - commission
            # Commission is paid on trade entry/exit (change in position)
            df['trade_cost'] = df['position'].diff().abs() * self.commission
            df['strategy_ret'] = df['position'] * df['log_ret'] - df['trade_cost']
            
            # Calculate Metrics
            total_return = df['strategy_ret'].sum()
            std_dev = df['strategy_ret'].std()
            
            if std_dev == 0:
                sharpe = 0.0
            else:
                # Annualized Sharpe (assuming M15 bars -> 96 bars/day * 252 days)
                # Adjust scaling factor based on timeframe if needed
                sharpe = (df['strategy_ret'].mean() / std_dev) * np.sqrt(252 * 96)
                
            # Max Drawdown
            cumulative_ret = df['strategy_ret'].cumsum()
            peak = cumulative_ret.cummax()
            drawdown = peak - cumulative_ret
            max_drawdown = drawdown.max()
            
            # Sortino (Downside Deviation)
            downside_returns = df.loc[df['strategy_ret'] < 0, 'strategy_ret']
            downside_std = downside_returns.std()
            if downside_std == 0:
                sortino = 0.0
            else:
                sortino = (df['strategy_ret'].mean() / downside_std) * np.sqrt(252 * 96)

            # Fitness Function: Sharpe * (1 - Drawdown penalty)
            # We want high Sharpe and low Drawdown
            fitness = sharpe * (1.0 - min(max_drawdown, 0.9))
            
            metrics = {
                "sharpe": float(sharpe),
                "sortino": float(sortino),
                "drawdown": float(max_drawdown),
                "return": float(total_return),
                "trades": int(df['position'].diff().abs().sum() / 2)
            }
            
            return fitness, metrics

        except Exception as e:
            logger.error(f"Backtest failed for {genome.id}: {e}")
            return -10.0, {} # Heavy penalty for crashing

    def _indent_code(self, code: str) -> str:
        """Indents the user code to fit inside the wrapper function"""
        import textwrap
        # First remove any common leading whitespace
        dedented_code = textwrap.dedent(code)
        # Then add 4 spaces indentation
        lines = dedented_code.split('\n')
        return '\n'.join(['    ' + line for line in lines])
