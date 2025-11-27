"""
Reinforcement Learning Agent (PPO)
Manages active trades by optimizing for PnL and Drawdown.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import logging
import numpy as np

logger = logging.getLogger(__name__)

class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(ActorCritic, self).__init__()
        
        # Actor
        self.actor_fc1 = nn.Linear(state_dim, 64)
        self.actor_fc2 = nn.Linear(64, 64)
        self.actor_out = nn.Linear(64, action_dim)
        
        # Critic
        self.critic_fc1 = nn.Linear(state_dim, 64)
        self.critic_fc2 = nn.Linear(64, 64)
        self.critic_out = nn.Linear(64, 1)

    def forward(self):
        raise NotImplementedError

    def act(self, state):
        x = F.relu(self.actor_fc1(state))
        x = F.relu(self.actor_fc2(x))
        action_probs = F.softmax(self.actor_out(x), dim=-1)
        return action_probs

    def evaluate(self, state):
        x = F.relu(self.critic_fc1(state))
        x = F.relu(self.critic_fc2(x))
        value = self.critic_out(x)
        return value

class PPOAgent:
    """
    Proximal Policy Optimization Agent.
    """
    def __init__(self, state_dim=5, action_dim=5):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy = ActorCritic(state_dim, action_dim).to(self.device)
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=0.002)
        self.policy.eval()
        
        # Actions: 0=Hold, 1=Close 25%, 2=Close 50%, 3=Close 100%, 4=Move SL to BE
        self.actions = ["HOLD", "CLOSE_25", "CLOSE_50", "CLOSE_100", "MOVE_SL_BE"]

    def select_action(self, state):
        """
        state: [PnL, Volatility, RSI, MACD, TimeHeld]
        """
        try:
            state_tensor = torch.FloatTensor(state).to(self.device)
            with torch.no_grad():
                action_probs = self.policy.act(state_tensor)
            
            # Greedy for inference, Sample for training
            # For production safety, we might want deterministic or highly confident actions
            action_idx = torch.argmax(action_probs).item()
            
            return self.actions[action_idx], action_probs.cpu().numpy()
            
        except Exception as e:
            logger.error(f"RL Action selection failed: {e}")
            return "HOLD", np.zeros(5)

# Global instance
rl_agent = PPOAgent()
