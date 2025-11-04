"""Long-Term Memory - SQLite + FAISS Vector Store"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger
import json

from app.data.database import db
from app.data.vector_store import vector_store


class LongTermMemory:
    """
    Stores compressed feature → outcome pairs
    Uses SQLite for structured data and FAISS for similarity search
    """
    
    def __init__(self):
        self.feature_dim = 50  # Feature vector dimension
    
    async def add_trade(self, trade_data: Dict) -> bool:
        """
        Add trade to long-term memory
        
        Args:
            trade_data: Complete trade record
        
        Returns:
            True if successful
        """
        try:
            # Extract data
            trade_id = trade_data.get('trade_id')
            timestamp = trade_data.get('timestamp', datetime.utcnow().isoformat())
            symbol = trade_data.get('symbol')
            alpha_id = trade_data.get('alpha_id')
            regime = trade_data.get('regime')
            
            # Features
            features_dict = trade_data.get('features', {})
            features_json = json.dumps(features_dict)
            
            # ML predictions
            rf_pwin = trade_data.get('rf_pwin', 0.5)
            lstm_sigma = trade_data.get('lstm_sigma', 0.01)
            lstm_direction = trade_data.get('lstm_direction', 0.0)
            q_star = trade_data.get('q_star', 0.0)
            es95 = trade_data.get('es95', 0.0)
            
            # Trade details
            entry_price = trade_data.get('entry_price', 0.0)
            stop_loss = trade_data.get('stop_loss', 0.0)
            take_profit_1 = trade_data.get('take_profit_1', 0.0)
            take_profit_2 = trade_data.get('take_profit_2', 0.0)
            lots = trade_data.get('lots', 0.0)
            
            # Outcome
            exit_price = trade_data.get('exit_price')
            exit_reason = trade_data.get('exit_reason')
            pnl = trade_data.get('pnl')
            
            # Execution quality
            latency_ms = trade_data.get('latency_ms', 0.0)
            slippage = trade_data.get('slippage', 0.0)
            spread_z = trade_data.get('spread_z', 0.0)
            
            # Calculate equity after trade
            equity_before = trade_data.get('equity_before', 1000.0)
            equity_after = equity_before + (pnl or 0.0)
            
            # Insert into database
            query = """
                INSERT INTO trades (
                    trade_id, timestamp, symbol, alpha_id, regime,
                    features_json, rf_pwin, lstm_sigma, lstm_direction,
                    q_star, es95, entry_price, stop_loss, take_profit_1,
                    take_profit_2, lots, exit_price, exit_reason, pnl,
                    latency_ms, slippage, spread_z, equity_before, equity_after,
                    status
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """
            
            await db.execute(query, (
                trade_id, timestamp, symbol, alpha_id, regime,
                features_json, rf_pwin, lstm_sigma, lstm_direction,
                q_star, es95, entry_price, stop_loss, take_profit_1,
                take_profit_2, lots, exit_price, exit_reason, pnl,
                latency_ms, slippage, spread_z, equity_before, equity_after,
                'closed' if exit_reason else 'open'
            ))
            
            # Add feature vector to FAISS if trade is closed
            if exit_reason and features_dict:
                feature_vector = self._dict_to_vector(features_dict)
                
                # Create metadata
                metadata = {
                    'trade_id': trade_id,
                    'outcome': 1 if exit_reason in ['TP1', 'TP2'] else 0,
                    'pnl': pnl or 0.0,
                    'alpha_id': alpha_id,
                    'regime': regime,
                }
                
                vector_store.add_vector(feature_vector, metadata)
            
            logger.debug(f"Added trade {trade_id} to LTM")
            return True
            
        except Exception as e:
            logger.error(f"Error adding trade to LTM: {e}", exc_info=True)
            return False
    
    def _dict_to_vector(self, features: Dict) -> np.ndarray:
        """Convert features dict to ordered vector"""
        feature_names = [
            'z_close', 'z_high', 'z_low', 'ema_slope', 'roc_5', 'roc_10',
            'rsi', 'price_position', 'm5_trend', 'm15_trend',
            'rvol', 'cvd', 'vwap_distance', 'volume_trend', 'vpin',
            'atr_z', 'bb_width', 'bb_position', 'realized_vol', 'vol_ratio',
            'dxy_z', 'vix_z', 'ust10y_z', 'ust2y_z', 'yield_curve',
            'sentiment',
            'corr_nas100', 'corr_xauusd', 'corr_eurusd',
            'regime_trend', 'regime_revert', 'regime_choppy',
        ]
        
        vector = np.array([features.get(name, 0.0) for name in feature_names])
        
        # Pad to 50 dimensions
        if len(vector) < self.feature_dim:
            vector = np.pad(vector, (0, self.feature_dim - len(vector)), constant_values=0.0)
        
        return vector[:self.feature_dim].astype(np.float32)
    
    async def get_similar_trades(
        self,
        features: Dict,
        k: int = 10,
        outcome_filter: Optional[int] = None
    ) -> list[Dict]:
        """
        Find similar historical trades using FAISS
        
        Args:
            features: Current feature dict
            k: Number of similar trades to return
            outcome_filter: Filter by outcome (1=win, 0=loss)
        
        Returns:
            List of similar trade records
        """
        try:
            # Convert features to vector
            query_vector = self._dict_to_vector(features)
            
            # Search FAISS
            results = vector_store.search(query_vector, k=k*2)  # Get more for filtering
            
            if not results:
                return []
            
            # Filter by outcome if specified
            if outcome_filter is not None:
                results = [r for r in results if r['metadata'].get('outcome') == outcome_filter]
            
            # Limit to k results
            results = results[:k]
            
            # Fetch full trade records from database
            trade_ids = [r['metadata']['trade_id'] for r in results]
            
            trades = []
            for trade_id in trade_ids:
                query = "SELECT * FROM trades WHERE trade_id = ?"
                row = await db.fetch_one(query, (trade_id,))
                if row:
                    trades.append(dict(row))
            
            return trades
            
        except Exception as e:
            logger.error(f"Error finding similar trades: {e}")
            return []
    
    async def get_training_data(
        self,
        limit: int = 5000,
        min_date: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get training data for model retraining
        
        Args:
            limit: Maximum number of samples
            min_date: Minimum date for samples (ISO format)
        
        Returns:
            (X, y) tuple of features and labels
        """
        try:
            # Build query
            query = """
                SELECT features_json, exit_reason
                FROM trades
                WHERE status = 'closed'
                AND features_json IS NOT NULL
                AND exit_reason IS NOT NULL
            """
            
            params = []
            if min_date:
                query += " AND timestamp >= ?"
                params.append(min_date)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            # Fetch data
            rows = await db.fetch_all(query, tuple(params))
            
            if not rows:
                logger.warning("No training data available in LTM")
                return np.array([]), np.array([])
            
            # Parse features and labels
            X_list = []
            y_list = []
            
            for row in rows:
                try:
                    features = json.loads(row['features_json'])
                    feature_vector = self._dict_to_vector(features)
                    X_list.append(feature_vector)
                    
                    # Label: 1 if TP, 0 if SL
                    label = 1 if row['exit_reason'] in ['TP1', 'TP2'] else 0
                    y_list.append(label)
                    
                except Exception as e:
                    logger.debug(f"Error parsing trade data: {e}")
                    continue
            
            X = np.array(X_list)
            y = np.array(y_list)
            
            logger.info(f"Retrieved {len(X)} training samples from LTM")
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}", exc_info=True)
            return np.array([]), np.array([])
    
    async def get_trade_count(self) -> int:
        """Get total number of trades in LTM"""
        try:
            query = "SELECT COUNT(*) as count FROM trades WHERE status = 'closed'"
            row = await db.fetch_one(query)
            return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Error getting trade count: {e}")
            return 0
    
    async def get_performance_by_alpha(self, days: int = 30) -> Dict[str, Dict]:
        """Get performance metrics by alpha for last N days"""
        try:
            from datetime import timedelta
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            query = """
                SELECT 
                    alpha_id,
                    COUNT(*) as trades,
                    SUM(CASE WHEN exit_reason IN ('TP1', 'TP2') THEN 1 ELSE 0 END) as wins,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    AVG(latency_ms) as avg_latency,
                    AVG(slippage) as avg_slippage
                FROM trades
                WHERE status = 'closed'
                AND timestamp >= ?
                GROUP BY alpha_id
            """
            
            rows = await db.fetch_all(query, (cutoff,))
            
            result = {}
            for row in rows:
                alpha_id = row['alpha_id']
                result[alpha_id] = {
                    'trades': row['trades'],
                    'wins': row['wins'],
                    'win_rate': row['wins'] / row['trades'] if row['trades'] > 0 else 0,
                    'total_pnl': row['total_pnl'] or 0.0,
                    'avg_pnl': row['avg_pnl'] or 0.0,
                    'avg_latency': row['avg_latency'] or 0.0,
                    'avg_slippage': row['avg_slippage'] or 0.0,
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting performance by alpha: {e}")
            return {}
    
    async def get_performance_by_regime(self, days: int = 30) -> Dict[str, Dict]:
        """Get performance metrics by regime for last N days"""
        try:
            from datetime import timedelta
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            query = """
                SELECT 
                    regime,
                    COUNT(*) as trades,
                    SUM(CASE WHEN exit_reason IN ('TP1', 'TP2') THEN 1 ELSE 0 END) as wins,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl
                FROM trades
                WHERE status = 'closed'
                AND timestamp >= ?
                GROUP BY regime
            """
            
            rows = await db.fetch_all(query, (cutoff,))
            
            result = {}
            for row in rows:
                regime = row['regime']
                result[regime] = {
                    'trades': row['trades'],
                    'wins': row['wins'],
                    'win_rate': row['wins'] / row['trades'] if row['trades'] > 0 else 0,
                    'total_pnl': row['total_pnl'] or 0.0,
                    'avg_pnl': row['avg_pnl'] or 0.0,
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting performance by regime: {e}")
            return {}


# Global long-term memory instance
long_term_memory = LongTermMemory()
