"""
Online Learner (Procedural Memory)
Manages real-time adaptation of strategy weights and model parameters.
"""

import numpy as np
import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ThompsonSamplingBandit:
    """
    Multi-Armed Bandit using Thompson Sampling.
    Maintains Beta distributions (alpha, beta) for each strategy.
    """
    def __init__(self):
        self.alphas = {} # Successes + 1
        self.betas = {}  # Failures + 1
        self.state_file = "data/bandit_state.json"
        self._load_state()
        
    def update(self, strategy_id: str, reward: float):
        """
        Update the bandit with a new observation.
        Reward should be 1.0 for win, 0.0 for loss (or normalized PnL).
        """
        if strategy_id not in self.alphas:
            self.alphas[strategy_id] = 1.0
            self.betas[strategy_id] = 1.0
            
        # Update Beta parameters
        # We use a learning rate/decay to emphasize recent results if desired
        # For now, standard Bayesian update
        if reward > 0:
            self.alphas[strategy_id] += reward
        else:
            self.betas[strategy_id] += (1.0 - reward) # Assuming reward is 0 for loss
            
        self._save_state()
        logger.info(f"Updated Bandit for {strategy_id}: alpha={self.alphas[strategy_id]:.2f}, beta={self.betas[strategy_id]:.2f}")

    def get_weight(self, strategy_id: str) -> float:
        """
        Sample from the Beta distribution to get the current weight.
        """
        if strategy_id not in self.alphas:
            return 1.0 # Default neutral weight
            
        # Thompson Sampling: Sample from Beta
        sample = np.random.beta(self.alphas[strategy_id], self.betas[strategy_id])
        
        # Scale/Normalize if needed. For now, return raw probability [0, 1]
        return sample

    def _load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.alphas = data.get('alphas', {})
                    self.betas = data.get('betas', {})
        except Exception as e:
            logger.error(f"Failed to load bandit state: {e}")

    def _save_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({'alphas': self.alphas, 'betas': self.betas}, f)
        except Exception as e:
            logger.error(f"Failed to save bandit state: {e}")

class OnlineModel:
    """
    Lightweight online learning model (SGD).
    Adapts to changing market regimes.
    """
    def __init__(self):
        # In a real implementation, this would wrap sklearn.linear_model.SGDClassifier
        # For this MVP, we'll simulate the interface
        self.weights = np.zeros(10) 
        self.bias = 0.0
        self.learning_rate = 0.01
        
    def partial_fit(self, features: List[float], label: int):
        """
        Update model weights with a single example (SGD).
        """
        # Simple Perceptron update rule for demonstration
        # w = w + lr * (y - y_pred) * x
        try:
            x = np.array(features)
            y_pred = 1 if (np.dot(self.weights, x) + self.bias) > 0 else 0
            error = label - y_pred
            
            if error != 0:
                self.weights += self.learning_rate * error * x
                self.bias += self.learning_rate * error
                logger.debug(f"Online Model updated. Error: {error}")
                
        except Exception as e:
            logger.error(f"Online learning failed: {e}")

class OnlineLearner:
    """
    Facade for Online Learning components.
    """
    def __init__(self):
        self.bandit = ThompsonSamplingBandit()
        self.model = OnlineModel()
        
    def update_alpha_weights(self, trade_outcome: Dict[str, Any]):
        """
        Update strategy weights based on trade outcome.
        """
        strategy_id = trade_outcome.get('alpha_id')
        pnl = trade_outcome.get('pnl', 0)
        
        if strategy_id:
            # Normalize reward: Win = 1, Loss = 0
            # Could be more sophisticated (e.g., sigmoid of Sharpe)
            reward = 1.0 if pnl > 0 else 0.0
            self.bandit.update(strategy_id, reward)
            
    def update_model(self, trade_context: Dict[str, Any], outcome: Dict[str, Any]):
        """
        Update online model with new data point.
        """
        # Extract features from context (simplified)
        # In production, this must match the feature vector used for inference
        features = [0.0] * 10 # Placeholder
        label = 1 if outcome.get('pnl', 0) > 0 else 0
        
        self.model.partial_fit(features, label)
        
    def get_current_weight(self, strategy_id: str) -> float:
        return self.bandit.get_weight(strategy_id)

# Global instance
online_learner = OnlineLearner()
