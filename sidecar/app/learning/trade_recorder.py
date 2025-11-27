"""
Trade Recorder
Listens for trade close events and stores them in Episodic Memory.
"""

import logging
from typing import Dict, Any
from datetime import datetime

# Import Episodic Memory
try:
    from app.learning.online_learner import online_learner
from app.memory.episodic_memory import episodic_memory
except ImportError:
    episodic_memory = None

logger = logging.getLogger(__name__)

class TradeRecorder:
    """
    Records trade outcomes to Episodic Memory.
    """
    
    async def record_trade_outcome(self, trade_data: Dict[str, Any]):
        """
        Process a closed trade and store it as an episode.
        
        Args:
            trade_data: Dictionary containing trade details (symbol, pnl, exit_reason, etc.)
        """
        if not episodic_memory:
            logger.warning("Episodic Memory not available. Cannot record trade.")
            return

        try:
            # 1. Reconstruct Market Context
            # Ideally, we should retrieve the EXACT context stored at entry.
            # For now, we'll use the trade_data's snapshot if available, or approximate.
            # In a real system, we'd query the 'open_trades' DB table for the initial context.
            
            market_context = trade_data.get('market_context', {})
            
            # If context is missing, we can't learn effectively, but we'll try with basic data
            if not market_context:
                market_context = {
                    'symbol': trade_data.get('symbol'),
                    'trend_strength': trade_data.get('trend_strength', 0), # Fallback
                    'volatility': trade_data.get('volatility', 0),
                    'news_sentiment': trade_data.get('news_sentiment', 0),
                }

            # 2. Extract Outcome
            outcome = {
                'pnl': trade_data.get('pnl', 0.0),
                'pnl_percent': trade_data.get('pnl_percent', 0.0),
                'win': trade_data.get('pnl', 0.0) > 0,
                'exit_reason': trade_data.get('exit_reason', 'unknown'),
                'duration_minutes': trade_data.get('duration_minutes', 0)
            }
            
            # 3. Store Episode
            episodic_memory.store_episode(market_context, outcome)
            
            logger.info(f"💾 Recorded Trade Episode: {trade_data.get('symbol')} (PnL: {outcome['pnl']})")
            
        except Exception as e:
            logger.error(f"Error recording trade episode: {e}")

# Global instance
trade_recorder = TradeRecorder()


            # 4. Online Learning Update
            try:
                online_learner.update_alpha_weights(trade_data)
                # online_learner.update_model(market_context, outcome) # Future
                logger.info(f"🧠 Online Learner updated for {trade_data.get('alpha_id', 'unknown')}")
            except Exception as e:
                logger.error(f"Online learning update failed: {e}")
        