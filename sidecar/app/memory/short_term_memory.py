"""Short-Term Memory - Circular Buffer in Redis"""

import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.data.redis_client import redis_client


class ShortTermMemory:
    """
    Maintains last N trades in Redis circular buffer
    Used for online statistics and alpha weight updates
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.key_prefix = "stm:trade:"
        self.index_key = "stm:index"
        self.stats_key = "stm:stats"
    
    async def add_trade(self, trade_data: Dict) -> bool:
        """
        Add trade to short-term memory
        
        Args:
            trade_data: Complete trade record with features, outcome, PnL
        
        Returns:
            True if successful
        """
        try:
            if not redis_client.connected:
                logger.warning("Redis not connected, cannot add to STM")
                return False
            
            # Generate trade ID if not present
            trade_id = trade_data.get('trade_id', f"trade_{datetime.utcnow().timestamp()}")
            
            # Add timestamp if not present
            if 'timestamp' not in trade_data:
                trade_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Store trade data
            key = f"{self.key_prefix}{trade_id}"
            redis_client.set(key, json.dumps(trade_data), ex=7*24*3600)  # 7 days TTL
            
            # Add to index (circular buffer)
            redis_client.lpush(self.index_key, trade_id)
            redis_client.ltrim(self.index_key, 0, self.max_size - 1)
            
            # Update rolling statistics
            await self._update_stats(trade_data)
            
            logger.debug(f"Added trade {trade_id} to STM")
            return True
            
        except Exception as e:
            logger.error(f"Error adding trade to STM: {e}", exc_info=True)
            return False
    
    async def get_recent_trades(self, limit: int = 100) -> list[Dict]:
        """
        Get most recent trades
        
        Args:
            limit: Maximum number of trades to return
        
        Returns:
            List of trade records
        """
        try:
            if not redis_client.connected:
                return []
            
            # Get trade IDs from index
            trade_ids = redis_client.lrange(self.index_key, 0, limit - 1)
            
            trades = []
            for trade_id in trade_ids:
                key = f"{self.key_prefix}{trade_id.decode()}"
                data = redis_client.get(key)
                if data:
                    trades.append(json.loads(data))
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
    
    async def get_trades_by_alpha(self, alpha_id: str, limit: int = 50) -> list[Dict]:
        """Get recent trades for specific alpha"""
        try:
            all_trades = await self.get_recent_trades(limit=500)
            return [t for t in all_trades if t.get('alpha_id') == alpha_id][:limit]
        except Exception as e:
            logger.error(f"Error getting trades by alpha: {e}")
            return []
    
    async def get_trades_by_regime(self, regime: str, limit: int = 50) -> list[Dict]:
        """Get recent trades for specific regime"""
        try:
            all_trades = await self.get_recent_trades(limit=500)
            return [t for t in all_trades if t.get('regime') == regime][:limit]
        except Exception as e:
            logger.error(f"Error getting trades by regime: {e}")
            return []
    
    async def _update_stats(self, trade_data: Dict):
        """Update rolling statistics"""
        try:
            # Get current stats
            stats_data = redis_client.get(self.stats_key)
            if stats_data:
                stats = json.loads(stats_data)
            else:
                stats = {
                    'total_trades': 0,
                    'total_wins': 0,
                    'total_pnl': 0.0,
                    'by_alpha': {},
                    'by_regime': {},
                    'by_symbol': {},
                }
            
            # Update global stats
            stats['total_trades'] += 1
            if trade_data.get('exit_reason') in ['TP1', 'TP2']:
                stats['total_wins'] += 1
            stats['total_pnl'] += trade_data.get('pnl', 0.0)
            
            # Update per-alpha stats
            alpha_id = trade_data.get('alpha_id', 'unknown')
            if alpha_id not in stats['by_alpha']:
                stats['by_alpha'][alpha_id] = {
                    'trades': 0,
                    'wins': 0,
                    'pnl': 0.0,
                    'avg_latency': 0.0,
                    'avg_slippage': 0.0,
                }
            
            alpha_stats = stats['by_alpha'][alpha_id]
            alpha_stats['trades'] += 1
            if trade_data.get('exit_reason') in ['TP1', 'TP2']:
                alpha_stats['wins'] += 1
            alpha_stats['pnl'] += trade_data.get('pnl', 0.0)
            
            # Update latency and slippage (rolling average)
            if 'latency_ms' in trade_data:
                n = alpha_stats['trades']
                alpha_stats['avg_latency'] = (
                    (alpha_stats['avg_latency'] * (n - 1) + trade_data['latency_ms']) / n
                )
            
            if 'slippage' in trade_data:
                n = alpha_stats['trades']
                alpha_stats['avg_slippage'] = (
                    (alpha_stats['avg_slippage'] * (n - 1) + trade_data['slippage']) / n
                )
            
            # Update per-regime stats
            regime = trade_data.get('regime', 'unknown')
            if regime not in stats['by_regime']:
                stats['by_regime'][regime] = {'trades': 0, 'wins': 0, 'pnl': 0.0}
            
            stats['by_regime'][regime]['trades'] += 1
            if trade_data.get('exit_reason') in ['TP1', 'TP2']:
                stats['by_regime'][regime]['wins'] += 1
            stats['by_regime'][regime]['pnl'] += trade_data.get('pnl', 0.0)
            
            # Update per-symbol stats
            symbol = trade_data.get('symbol', 'unknown')
            if symbol not in stats['by_symbol']:
                stats['by_symbol'][symbol] = {'trades': 0, 'wins': 0, 'pnl': 0.0}
            
            stats['by_symbol'][symbol]['trades'] += 1
            if trade_data.get('exit_reason') in ['TP1', 'TP2']:
                stats['by_symbol'][symbol]['wins'] += 1
            stats['by_symbol'][symbol]['pnl'] += trade_data.get('pnl', 0.0)
            
            # Save updated stats
            redis_client.set(self.stats_key, json.dumps(stats), ex=7*24*3600)
            
        except Exception as e:
            logger.error(f"Error updating STM stats: {e}")
    
    async def get_stats(self) -> Dict:
        """Get current rolling statistics"""
        try:
            if not redis_client.connected:
                return {}
            
            stats_data = redis_client.get(self.stats_key)
            if stats_data:
                return json.loads(stats_data)
            return {}
            
        except Exception as e:
            logger.error(f"Error getting STM stats: {e}")
            return {}
    
    async def get_alpha_stats(self, alpha_id: str) -> Dict:
        """Get statistics for specific alpha"""
        try:
            stats = await self.get_stats()
            return stats.get('by_alpha', {}).get(alpha_id, {})
        except Exception as e:
            logger.error(f"Error getting alpha stats: {e}")
            return {}
    
    async def clear(self):
        """Clear all short-term memory"""
        try:
            if not redis_client.connected:
                return
            
            # Get all trade IDs
            trade_ids = redis_client.lrange(self.index_key, 0, -1)
            
            # Delete all trade keys
            for trade_id in trade_ids:
                key = f"{self.key_prefix}{trade_id.decode()}"
                redis_client.delete(key)
            
            # Delete index and stats
            redis_client.delete(self.index_key)
            redis_client.delete(self.stats_key)
            
            logger.info("Short-term memory cleared")
            
        except Exception as e:
            logger.error(f"Error clearing STM: {e}")


# Global short-term memory instance
short_term_memory = ShortTermMemory(max_size=1000)
