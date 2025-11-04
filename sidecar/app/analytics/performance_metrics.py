"""Performance Metrics Calculators - Sharpe, Sortino, Calmar, VaR, ES95"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from loguru import logger


class PerformanceMetrics:
    """Calculate various performance metrics for trading strategies"""
    
    @staticmethod
    def calculate_sharpe_ratio(
        returns: np.ndarray,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sharpe Ratio
        
        Sharpe = (E[R] - Rf) / σ[R] * sqrt(periods_per_year)
        
        Args:
            returns: Array of returns
            risk_free_rate: Risk-free rate (annualized)
            periods_per_year: Trading periods per year (252 for daily)
        
        Returns:
            Sharpe ratio
        """
        try:
            if len(returns) < 2:
                return 0.0
            
            excess_returns = returns - (risk_free_rate / periods_per_year)
            
            mean_return = np.mean(excess_returns)
            std_return = np.std(excess_returns, ddof=1)
            
            if std_return == 0:
                return 0.0
            
            sharpe = (mean_return / std_return) * np.sqrt(periods_per_year)
            
            return float(sharpe)
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0
    
    @staticmethod
    def calculate_sortino_ratio(
        returns: np.ndarray,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sortino Ratio (uses downside deviation)
        
        Sortino = (E[R] - Rf) / σ_downside[R] * sqrt(periods_per_year)
        
        Args:
            returns: Array of returns
            risk_free_rate: Risk-free rate (annualized)
            periods_per_year: Trading periods per year
        
        Returns:
            Sortino ratio
        """
        try:
            if len(returns) < 2:
                return 0.0
            
            excess_returns = returns - (risk_free_rate / periods_per_year)
            
            mean_return = np.mean(excess_returns)
            
            # Downside deviation (only negative returns)
            downside_returns = excess_returns[excess_returns < 0]
            
            if len(downside_returns) == 0:
                return float('inf') if mean_return > 0 else 0.0
            
            downside_std = np.std(downside_returns, ddof=1)
            
            if downside_std == 0:
                return 0.0
            
            sortino = (mean_return / downside_std) * np.sqrt(periods_per_year)
            
            return float(sortino)
            
        except Exception as e:
            logger.error(f"Error calculating Sortino ratio: {e}")
            return 0.0
    
    @staticmethod
    def calculate_calmar_ratio(
        returns: np.ndarray,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Calmar Ratio
        
        Calmar = Annualized Return / Max Drawdown
        
        Args:
            returns: Array of returns
            periods_per_year: Trading periods per year
        
        Returns:
            Calmar ratio
        """
        try:
            if len(returns) < 2:
                return 0.0
            
            # Annualized return
            total_return = np.prod(1 + returns) - 1
            n_periods = len(returns)
            annualized_return = (1 + total_return) ** (periods_per_year / n_periods) - 1
            
            # Max drawdown
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = abs(np.min(drawdown))
            
            if max_drawdown == 0:
                return 0.0
            
            calmar = annualized_return / max_drawdown
            
            return float(calmar)
            
        except Exception as e:
            logger.error(f"Error calculating Calmar ratio: {e}")
            return 0.0
    
    @staticmethod
    def calculate_max_drawdown(returns: np.ndarray) -> Tuple[float, int, int]:
        """
        Calculate maximum drawdown
        
        Args:
            returns: Array of returns
        
        Returns:
            (max_drawdown, start_index, end_index)
        """
        try:
            if len(returns) == 0:
                return 0.0, 0, 0
            
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            
            max_dd = abs(np.min(drawdown))
            end_idx = np.argmin(drawdown)
            
            # Find start of drawdown
            start_idx = np.argmax(cumulative[:end_idx+1])
            
            return float(max_dd), int(start_idx), int(end_idx)
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0, 0, 0
    
    @staticmethod
    def calculate_var(
        returns: np.ndarray,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk (VaR)
        
        Args:
            returns: Array of returns
            confidence: Confidence level (0.95 = 95%)
        
        Returns:
            VaR value (positive number representing potential loss)
        """
        try:
            if len(returns) == 0:
                return 0.0
            
            # Historical VaR
            var = -np.percentile(returns, (1 - confidence) * 100)
            
            return float(var)
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return 0.0
    
    @staticmethod
    def calculate_es(
        returns: np.ndarray,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Expected Shortfall (ES) / Conditional VaR
        
        ES is the average of losses beyond VaR
        
        Args:
            returns: Array of returns
            confidence: Confidence level (0.95 = 95%)
        
        Returns:
            ES value (positive number representing expected loss in tail)
        """
        try:
            if len(returns) == 0:
                return 0.0
            
            # Calculate VaR threshold
            var_threshold = -np.percentile(returns, (1 - confidence) * 100)
            
            # Get returns worse than VaR
            tail_returns = returns[returns < -var_threshold]
            
            if len(tail_returns) == 0:
                return var_threshold
            
            # ES is the average of tail losses
            es = -np.mean(tail_returns)
            
            return float(es)
            
        except Exception as e:
            logger.error(f"Error calculating ES: {e}")
            return 0.0
    
    @staticmethod
    def calculate_win_rate(outcomes: list[str]) -> float:
        """
        Calculate win rate
        
        Args:
            outcomes: List of trade outcomes ('TP1', 'TP2', 'SL', etc.)
        
        Returns:
            Win rate (0.0 to 1.0)
        """
        try:
            if not outcomes:
                return 0.0
            
            wins = sum(1 for o in outcomes if o in ['TP1', 'TP2'])
            total = len(outcomes)
            
            return wins / total
            
        except Exception as e:
            logger.error(f"Error calculating win rate: {e}")
            return 0.0
    
    @staticmethod
    def calculate_profit_factor(pnls: np.ndarray) -> float:
        """
        Calculate profit factor
        
        Profit Factor = Gross Profit / Gross Loss
        
        Args:
            pnls: Array of PnL values
        
        Returns:
            Profit factor
        """
        try:
            if len(pnls) == 0:
                return 0.0
            
            gross_profit = np.sum(pnls[pnls > 0])
            gross_loss = abs(np.sum(pnls[pnls < 0]))
            
            if gross_loss == 0:
                return float('inf') if gross_profit > 0 else 0.0
            
            return float(gross_profit / gross_loss)
            
        except Exception as e:
            logger.error(f"Error calculating profit factor: {e}")
            return 0.0
    
    @staticmethod
    def calculate_all_metrics(
        returns: np.ndarray,
        pnls: np.ndarray,
        outcomes: list[str]
    ) -> Dict[str, float]:
        """
        Calculate all performance metrics
        
        Args:
            returns: Array of returns
            pnls: Array of PnL values
            outcomes: List of trade outcomes
        
        Returns:
            Dict with all metrics
        """
        try:
            metrics = {
                'sharpe_ratio': PerformanceMetrics.calculate_sharpe_ratio(returns),
                'sortino_ratio': PerformanceMetrics.calculate_sortino_ratio(returns),
                'calmar_ratio': PerformanceMetrics.calculate_calmar_ratio(returns),
                'max_drawdown': PerformanceMetrics.calculate_max_drawdown(returns)[0],
                'var_95': PerformanceMetrics.calculate_var(returns, 0.95),
                'es_95': PerformanceMetrics.calculate_es(returns, 0.95),
                'win_rate': PerformanceMetrics.calculate_win_rate(outcomes),
                'profit_factor': PerformanceMetrics.calculate_profit_factor(pnls),
                'total_return': float(np.sum(returns)),
                'avg_return': float(np.mean(returns)) if len(returns) > 0 else 0.0,
                'volatility': float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.0,
                'total_trades': len(outcomes),
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating all metrics: {e}", exc_info=True)
            return {}


# Global performance metrics calculator
performance_metrics = PerformanceMetrics()
