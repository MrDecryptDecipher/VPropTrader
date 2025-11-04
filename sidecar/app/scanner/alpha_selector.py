"""Reinforcement Bandit for Alpha Selection per Regime"""

import numpy as np
from typing import Dict, List, Optional
from loguru import logger
from collections import defaultdict
import json
from pathlib import Path

from app.core import settings


class ThompsonSamplingBandit:
    """
    Thompson Sampling bandit for alpha selection
    
    Maintains Beta distributions for each (regime, alpha) pair
    and selects alphas based on sampling from these distributions
    """
    
    def __init__(self):
        # Beta distribution parameters: {regime: {alpha_id: (alpha, beta)}}
        self.params = defaultdict(lambda: defaultdict(lambda: (1.0, 1.0)))
        
        # Performance tracking
        self.pulls = defaultdict(lambda: defaultdict(int))
        self.rewards = defaultdict(lambda: defaultdict(list))
        
        self.state_file = Path(settings.model_path) / "bandit_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def select_alpha(self, regime: str, available_alphas: list[str]) -> str:
        """
        Select best alpha for current regime using Thompson Sampling
        
        Args:
            regime: Current market regime
            available_alphas: List of available alpha IDs
        
        Returns:
            Selected alpha ID
        """
        if not available_alphas:
            raise ValueError("No alphas available")
        
        # Sample from Beta distributions
        samples = {}
        for alpha_id in available_alphas:
            alpha, beta = self.params[regime][alpha_id]
            # Sample from Beta(alpha, beta)
            sample = np.random.beta(alpha, beta)
            samples[alpha_id] = sample
        
        # Select alpha with highest sample
        selected = max(samples.items(), key=lambda x: x[1])[0]
        
        logger.debug(
            f"Bandit selection for {regime}: {selected} "
            f"(samples: {', '.join(f'{k}={v:.3f}' for k, v in samples.items())})"
        )
        
        return selected
    
    def update(
        self,
        regime: str,
        alpha_id: str,
        reward: float,
        sharpe: Optional[float] = None
    ):
        """
        Update bandit with trade outcome
        
        Args:
            regime: Market regime
            alpha_id: Alpha that was used
            reward: Trade outcome (1 for win, 0 for loss, or continuous reward)
            sharpe: Optional Sharpe ratio for this alpha
        """
        # Convert reward to [0, 1] range if needed
        if reward < 0:
            reward = 0.0
        elif reward > 1:
            reward = min(reward / 10.0, 1.0)  # Scale down large rewards
        
        # Update Beta parameters
        alpha, beta = self.params[regime][alpha_id]
        
        # Bayesian update
        alpha_new = alpha + reward
        beta_new = beta + (1 - reward)
        
        self.params[regime][alpha_id] = (alpha_new, beta_new)
        
        # Track statistics
        self.pulls[regime][alpha_id] += 1
        self.rewards[regime][alpha_id].append(reward)
        
        # Keep only last 100 rewards
        if len(self.rewards[regime][alpha_id]) > 100:
            self.rewards[regime][alpha_id] = self.rewards[regime][alpha_id][-100:]
        
        logger.debug(
            f"Bandit update: {regime}/{alpha_id} - "
            f"reward={reward:.3f}, α={alpha_new:.2f}, β={beta_new:.2f}"
        )
    
    def get_alpha_weights(self, regime: str) -> Dict[str, float]:
        """
        Get current weights (expected values) for all alphas in regime
        
        Args:
            regime: Market regime
        
        Returns:
            Dict of {alpha_id: weight}
        """
        weights = {}
        
        for alpha_id, (alpha, beta) in self.params[regime].items():
            # Expected value of Beta(alpha, beta) = alpha / (alpha + beta)
            expected_value = alpha / (alpha + beta)
            weights[alpha_id] = expected_value
        
        return weights
    
    def get_statistics(self, regime: Optional[str] = None) -> Dict:
        """
        Get bandit statistics
        
        Args:
            regime: Optional regime to filter by
        
        Returns:
            Dict with statistics
        """
        stats = {}
        
        regimes = [regime] if regime else self.params.keys()
        
        for reg in regimes:
            stats[reg] = {}
            
            for alpha_id in self.params[reg].keys():
                alpha, beta = self.params[reg][alpha_id]
                pulls = self.pulls[reg][alpha_id]
                rewards_list = self.rewards[reg][alpha_id]
                
                avg_reward = np.mean(rewards_list) if rewards_list else 0.0
                
                stats[reg][alpha_id] = {
                    'alpha': alpha,
                    'beta': beta,
                    'expected_value': alpha / (alpha + beta),
                    'pulls': pulls,
                    'avg_reward': avg_reward,
                    'recent_rewards': len(rewards_list),
                }
        
        return stats
    
    def save(self) -> bool:
        """Save bandit state to disk"""
        try:
            state = {
                'params': {
                    regime: {
                        alpha_id: list(params)
                        for alpha_id, params in alphas.items()
                    }
                    for regime, alphas in self.params.items()
                },
                'pulls': {
                    regime: dict(alphas)
                    for regime, alphas in self.pulls.items()
                },
                'rewards': {
                    regime: {
                        alpha_id: rewards
                        for alpha_id, rewards in alphas.items()
                    }
                    for regime, alphas in self.rewards.items()
                },
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"✓ Bandit state saved to {self.state_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving bandit state: {e}")
            return False
    
    def load(self) -> bool:
        """Load bandit state from disk"""
        if not self.state_file.exists():
            logger.warning(f"Bandit state file not found: {self.state_file}")
            return False
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # Restore params
            self.params = defaultdict(lambda: defaultdict(lambda: (1.0, 1.0)))
            for regime, alphas in state.get('params', {}).items():
                for alpha_id, params in alphas.items():
                    self.params[regime][alpha_id] = tuple(params)
            
            # Restore pulls
            self.pulls = defaultdict(lambda: defaultdict(int))
            for regime, alphas in state.get('pulls', {}).items():
                for alpha_id, count in alphas.items():
                    self.pulls[regime][alpha_id] = count
            
            # Restore rewards
            self.rewards = defaultdict(lambda: defaultdict(list))
            for regime, alphas in state.get('rewards', {}).items():
                for alpha_id, rewards in alphas.items():
                    self.rewards[regime][alpha_id] = rewards
            
            logger.info(f"✓ Bandit state loaded from {self.state_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading bandit state: {e}")
            return False
    
    def reset_alpha(self, regime: str, alpha_id: str):
        """Reset a specific alpha's parameters"""
        self.params[regime][alpha_id] = (1.0, 1.0)
        self.pulls[regime][alpha_id] = 0
        self.rewards[regime][alpha_id] = []
        logger.info(f"Reset bandit for {regime}/{alpha_id}")


# Global bandit instance
alpha_bandit = ThompsonSamplingBandit()
