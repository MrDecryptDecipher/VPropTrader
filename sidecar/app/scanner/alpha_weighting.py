"""Adaptive Alpha Weighting System"""

import numpy as np
from typing import Dict, List
from loguru import logger
from collections import defaultdict
import json
from pathlib import Path

from app.core import settings


class AdaptiveAlphaWeighting:
    """
    Implements adaptive alpha weighting formula:
    w_i^{t+1} = w_i^t + η(Sharpe_i - mean_Sharpe) - λ * ρ_{i,portfolio}
    
    Increases weights for high-Sharpe alphas and decreases for correlated ones
    """
    
    def __init__(
        self,
        learning_rate: float = 0.01,
        correlation_penalty: float = 0.05,
        min_weight: float = 0.1,
        max_weight: float = 2.0
    ):
        self.eta = learning_rate  # η
        self.lambda_corr = correlation_penalty  # λ
        self.min_weight = min_weight
        self.max_weight = max_weight
        
        # Alpha weights: {alpha_id: weight}
        self.weights = defaultdict(lambda: 1.0)
        
        # Performance tracking: {alpha_id: {'trades': [], 'pnls': [], 'sharpe': float}}
        self.performance = defaultdict(lambda: {
            'trades': 0,
            'wins': 0,
            'pnls': [],
            'sharpe': 0.0,
            'hit_rate': 0.0,
            'avg_rr': 0.0,
        })
        
        self.state_file = Path(settings.model_path) / "alpha_weights.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def update_weights(self, portfolio_correlations: Dict[str, float]):
        """
        Update all alpha weights based on performance and correlations
        
        Args:
            portfolio_correlations: {alpha_id: correlation_with_portfolio}
        """
        try:
            # Calculate Sharpe ratios for all alphas
            sharpe_ratios = {}
            for alpha_id, perf in self.performance.items():
                sharpe_ratios[alpha_id] = perf['sharpe']
            
            if not sharpe_ratios:
                logger.debug("No alpha performance data yet")
                return
            
            # Calculate mean Sharpe
            mean_sharpe = np.mean(list(sharpe_ratios.values()))
            
            # Update each alpha's weight
            for alpha_id in sharpe_ratios.keys():
                current_weight = self.weights[alpha_id]
                sharpe_i = sharpe_ratios[alpha_id]
                corr_i = portfolio_correlations.get(alpha_id, 0.0)
                
                # Apply formula: w_i^{t+1} = w_i^t + η(Sharpe_i - mean_Sharpe) - λ * ρ_{i,port}
                sharpe_term = self.eta * (sharpe_i - mean_sharpe)
                corr_term = self.lambda_corr * corr_i
                
                new_weight = current_weight + sharpe_term - corr_term
                
                # Clip to valid range
                new_weight = np.clip(new_weight, self.min_weight, self.max_weight)
                
                self.weights[alpha_id] = new_weight
                
                logger.debug(
                    f"Weight update {alpha_id}: {current_weight:.3f} → {new_weight:.3f} "
                    f"(Sharpe={sharpe_i:.2f}, Corr={corr_i:.2f})"
                )
            
            # Normalize weights to sum to number of alphas
            self._normalize_weights()
            
            logger.info(f"✓ Alpha weights updated - Mean Sharpe: {mean_sharpe:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating alpha weights: {e}", exc_info=True)
    
    def _normalize_weights(self):
        """Normalize weights to maintain total weight = number of alphas"""
        if not self.weights:
            return
        
        total_weight = sum(self.weights.values())
        n_alphas = len(self.weights)
        
        if total_weight > 0:
            scale_factor = n_alphas / total_weight
            for alpha_id in self.weights.keys():
                self.weights[alpha_id] *= scale_factor
    
    def record_trade(
        self,
        alpha_id: str,
        pnl: float,
        outcome: str,
        risk_reward: float
    ):
        """
        Record a trade outcome for an alpha
        
        Args:
            alpha_id: Alpha identifier
            pnl: Trade PnL
            outcome: 'TP1', 'TP2', 'SL', etc.
            risk_reward: Realized risk-reward ratio
        """
        perf = self.performance[alpha_id]
        
        # Update counts
        perf['trades'] += 1
        if outcome in ['TP1', 'TP2']:
            perf['wins'] += 1
        
        # Update PnL history (keep last 100)
        perf['pnls'].append(pnl)
        if len(perf['pnls']) > 100:
            perf['pnls'] = perf['pnls'][-100:]
        
        # Calculate metrics
        perf['hit_rate'] = perf['wins'] / perf['trades']
        
        # Calculate Sharpe ratio
        if len(perf['pnls']) >= 2:
            returns = np.array(perf['pnls'])
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return > 0:
                # Annualized Sharpe (assuming ~250 trading days)
                perf['sharpe'] = (mean_return / std_return) * np.sqrt(250)
            else:
                perf['sharpe'] = 0.0
        
        # Update average RR
        if risk_reward > 0:
            if 'rr_history' not in perf:
                perf['rr_history'] = []
            perf['rr_history'].append(risk_reward)
            if len(perf['rr_history']) > 100:
                perf['rr_history'] = perf['rr_history'][-100:]
            perf['avg_rr'] = np.mean(perf['rr_history'])
        
        logger.debug(
            f"Trade recorded for {alpha_id}: PnL=${pnl:.2f}, "
            f"Sharpe={perf['sharpe']:.2f}, Hit Rate={perf['hit_rate']:.2%}"
        )
    
    def get_weight(self, alpha_id: str) -> float:
        """Get current weight for an alpha"""
        return self.weights[alpha_id]
    
    def get_all_weights(self) -> Dict[str, float]:
        """Get all alpha weights"""
        return dict(self.weights)
    
    def get_performance(self, alpha_id: str) -> Dict:
        """Get performance metrics for an alpha"""
        return dict(self.performance[alpha_id])
    
    def get_all_performance(self) -> Dict[str, Dict]:
        """Get performance metrics for all alphas"""
        return {
            alpha_id: dict(perf)
            for alpha_id, perf in self.performance.items()
        }
    
    def get_top_alphas(self, n: int = 3) -> list[str]:
        """
        Get top N alphas by weight
        
        Args:
            n: Number of top alphas to return
        
        Returns:
            List of alpha IDs sorted by weight (descending)
        """
        sorted_alphas = sorted(
            self.weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [alpha_id for alpha_id, _ in sorted_alphas[:n]]
    
    def save(self) -> bool:
        """Save weights and performance to disk"""
        try:
            state = {
                'weights': dict(self.weights),
                'performance': {
                    alpha_id: {
                        k: v if not isinstance(v, list) else v[-100:]  # Keep last 100
                        for k, v in perf.items()
                    }
                    for alpha_id, perf in self.performance.items()
                },
                'config': {
                    'learning_rate': self.eta,
                    'correlation_penalty': self.lambda_corr,
                    'min_weight': self.min_weight,
                    'max_weight': self.max_weight,
                },
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"✓ Alpha weights saved to {self.state_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving alpha weights: {e}")
            return False
    
    def load(self) -> bool:
        """Load weights and performance from disk"""
        if not self.state_file.exists():
            logger.warning(f"Alpha weights file not found: {self.state_file}")
            return False
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # Restore weights
            self.weights = defaultdict(lambda: 1.0)
            for alpha_id, weight in state.get('weights', {}).items():
                self.weights[alpha_id] = weight
            
            # Restore performance
            self.performance = defaultdict(lambda: {
                'trades': 0,
                'wins': 0,
                'pnls': [],
                'sharpe': 0.0,
                'hit_rate': 0.0,
                'avg_rr': 0.0,
            })
            for alpha_id, perf in state.get('performance', {}).items():
                self.performance[alpha_id].update(perf)
            
            # Restore config if present
            config = state.get('config', {})
            if config:
                self.eta = config.get('learning_rate', self.eta)
                self.lambda_corr = config.get('correlation_penalty', self.lambda_corr)
            
            logger.info(f"✓ Alpha weights loaded from {self.state_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading alpha weights: {e}")
            return False


# Global alpha weighting system
alpha_weighting = AdaptiveAlphaWeighting()
