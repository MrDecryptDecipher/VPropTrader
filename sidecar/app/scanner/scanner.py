"""Global Scanner - Evaluates symbol-alpha combinations"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
import heapq
import numpy as np

from app.scanner.alphas import get_all_alphas
from app.scanner.alpha_weighting import alpha_weighting
from app.scanner.alpha_selector import alpha_bandit
from app.data.features import feature_engineer
from app.ml.inference import ml_inference
from app.data.correlation_engine import correlation_engine
from app.data.calendar_scraper import calendar_scraper
from app.risk.position_sizing import position_sizer
from app.core import settings


class TradingPlan:
    """Represents a potential trade"""
    
    def __init__(
        self,
        symbol: str,
        alpha_id: str,
        action: str,
        confidence: float,
        q_star: float,
        es95: float,
        expected_rr: float,
        features: Dict,
        ml_predictions: Dict,
        reason: str
    ):
        self.symbol = symbol
        self.alpha_id = alpha_id
        self.action = action
        self.confidence = confidence
        self.q_star = q_star
        self.es95 = es95
        self.expected_rr = expected_rr
        self.features = features
        self.ml_predictions = ml_predictions
        self.reason = reason
        self.timestamp = datetime.utcnow()
    
    def __lt__(self, other):
        """For priority queue (higher Q* = higher priority)"""
        return self.q_star > other.q_star
    
    def to_dict(self, include_features: bool = False) -> Dict:
        """
        Convert to dictionary for API response
        
        Args:
            include_features: If True, include full feature dict
        
        Returns:
            Dict representation of trading plan
        """
        result = {
            'symbol': self.symbol,
            'alpha_id': self.alpha_id,
            'action': self.action,
            'confidence': self.confidence,
            'q_star': self.q_star,
            'es95': self.es95,
            'expected_rr': self.expected_rr,
            'reason': self.reason,
            'regime': self.ml_predictions.get('regime', 'unknown'),
            'rf_pwin': self.ml_predictions.get('rf_pwin', 0.5),
            'lstm_sigma': self.ml_predictions.get('lstm_sigma', 0.01),
            'lstm_direction': self.ml_predictions.get('lstm_direction', 0.0),
            'timestamp': self.timestamp.isoformat(),
        }
        
        if include_features:
            result['features'] = self.features
        
        return result


class GlobalScanner:
    """Scans all symbol-alpha combinations for trading opportunities"""
    
    def __init__(self):
        self.symbols = settings.symbols_list
        self.alphas = get_all_alphas()
        self.max_signals = 3  # Top K signals
        self.min_q_star = 3.0  # BOOTSTRAP: Lowered for testing with historical data (production: 7.0 for A grade, 8.5 for A+)
        self.max_es95 = 10.0  # Maximum Expected Shortfall ($10)
        self.max_correlation = 0.3  # Maximum portfolio correlation
        self.scan_count = 0
        self.skip_count = 0
        self.total_evaluated = 0
        
        # Performance tracking
        self.scan_times = []
        self.signals_generated = []
        
        # Load alpha weights from disk
        alpha_weighting.load()
        
        # Load Thompson Sampling bandit state
        alpha_bandit.load()
        
        logger.info(f"Scanner initialized with {len(self.alphas)} alphas and {len(self.symbols)} symbols")
        
        # Log current alpha weights
        weights = alpha_weighting.get_all_weights()
        if weights:
            logger.info("Current alpha weights:")
            for alpha_id, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {alpha_id}: {weight:.3f}")
    
    async def scan(self, existing_positions: Optional[list[str]] = None) -> list[TradingPlan]:
        """
        Scan all symbol-alpha combinations
        
        Args:
            existing_positions: List of symbols with open positions
        
        Returns:
            List of top trading plans (max 3)
        """
        if existing_positions is None:
            existing_positions = []
        
        try:
            self.scan_count += 1
            start_time = datetime.utcnow()
            
            # Priority queue for plans
            plans = []
            evaluated = 0
            
            # Scan each symbol
            for symbol in self.symbols:
                # Check news embargo
                if await calendar_scraper.is_embargo_active(symbol):
                    logger.debug(f"Skipping {symbol} - news embargo active")
                    continue
                
                # Extract features
                features = await feature_engineer.extract_features(symbol)
                if not features:
                    continue
                
                # Get ML predictions
                ml_predictions = await ml_inference.predict(symbol)
                if not ml_predictions:
                    continue
                
                # Get current regime
                regime = ml_predictions.get('regime', 'unknown')
                
                # Use Thompson Sampling to select best alpha for this regime
                # This helps focus on alphas that perform well in current conditions
                available_alpha_ids = list(self.alphas.keys())
                if available_alpha_ids and regime != 'unknown':
                    try:
                        best_alpha_id = alpha_bandit.select_alpha(regime, available_alpha_ids)
                        logger.debug(f"Thompson Sampling selected {best_alpha_id} for {symbol} in {regime} regime")
                    except Exception as e:
                        logger.warning(f"Thompson Sampling selection failed: {e}")
                        best_alpha_id = None
                else:
                    best_alpha_id = None
                
                # Evaluate each alpha
                for alpha_id, alpha in self.alphas.items():
                    evaluated += 1
                    
                    # Get current weight for this alpha
                    alpha_weight = alpha_weighting.get_weight(alpha_id)
                    
                    # Apply Thompson Sampling boost if this alpha was selected
                    # This gives extra priority to alphas that perform well in current regime
                    bandit_boost = 1.2 if alpha_id == best_alpha_id else 1.0
                    
                    # Generate signal
                    if alpha_id in ['momentum_v3', 'mean_revert_v2']:
                        logger.info(f"Testing {symbol}/{alpha_id} with features: ema_slope={features.get('ema_slope', 0):.6f}, roc_5={features.get('roc_5', 0):.6f}, rsi={features.get('rsi', 50):.2f}, bb_pos={features.get('bb_position', 0.5):.3f}")
                    signal = alpha.generate_signal(features)
                    if not signal:
                        logger.info(f"Skipping {symbol}/{alpha_id} - No signal generated by alpha")
                        self.skip_count += 1
                        continue
                    
                    # Apply alpha weight and bandit boost to confidence
                    # This allows better-performing alphas to have more influence
                    weighted_confidence = signal['confidence'] * alpha_weight * bandit_boost
                    
                    # Calculate Q* score with weighted confidence
                    q_star = ml_inference.calculate_q_star(
                        p_win=ml_predictions.get('rf_pwin', 0.5),
                        expected_rr=signal.get('expected_rr', 1.5),
                        vol_forecast=ml_predictions.get('lstm_sigma', 0.01),
                        entropy=0.5  # Could be calculated from signal strength
                    )
                    
                    # Apply alpha weight and bandit boost to Q* score
                    # Higher weight = higher Q* = higher priority
                    weighted_q_star = q_star * alpha_weight * bandit_boost
                    
                    # Filter by weighted Q* threshold
                    if weighted_q_star < self.min_q_star:
                        logger.info(f"Skipping {symbol}/{alpha_id} - Q* too low: {weighted_q_star:.2f} < {self.min_q_star:.2f} (raw Q*={q_star:.2f}, weight={alpha_weight:.2f})")
                        self.skip_count += 1
                        continue
                    
                    # Calculate position sizing and ES95
                    # Get current price (simplified - should come from MT5)
                    current_price = features.get('close', 15000)  # Fallback
                    volatility = ml_predictions.get('lstm_sigma', 0.01)
                    
                    # Calculate stop loss
                    stop_loss = position_sizer.calculate_stop_loss(
                        entry_price=current_price,
                        volatility=volatility,
                        action=signal['action'],
                        multiplier=0.8
                    )
                    
                    stop_loss_distance = abs(current_price - stop_loss)
                    
                    # Estimate position size (simplified - needs actual equity)
                    estimated_equity = 1000  # Placeholder
                    symbol_info = {
                        'point': 0.01,
                        'trade_tick_value': 1.0,
                        'trade_contract_size': 1,
                        'volume_min': 0.01,
                        'volume_max': 100.0,
                        'volume_step': 0.01,
                    }
                    
                    # Calculate initial position size using Kelly
                    initial_position_size = position_sizer.calculate_position_size(
                        equity=estimated_equity,
                        p_win=ml_predictions.get('rf_pwin', 0.5),
                        expected_rr=signal.get('expected_rr', 1.5),
                        stop_loss_distance=stop_loss_distance,
                        symbol_info=symbol_info,
                        entropy=0.5
                    )
                    
                    # Calculate ES95 (Expected Shortfall at 95%)
                    # ES95 = position_size * stop_loss_distance * 1.645 (for 95% confidence)
                    # This represents the expected loss in the worst 5% of cases
                    initial_es95 = initial_position_size * stop_loss_distance * 1.645
                    
                    # Apply ES95 constraint: if ES95 > max_es95, scale down position
                    # Work backwards: position_size = max_es95 / (stop_loss_distance * 1.645)
                    if initial_es95 > self.max_es95:
                        # Scale down to meet ES95 limit
                        position_size = self.max_es95 / (stop_loss_distance * 1.645)
                        # Round to volume step
                        volume_step = symbol_info.get('volume_step', 0.01)
                        position_size = round(position_size / volume_step) * volume_step
                        # Ensure minimum volume
                        position_size = max(position_size, symbol_info.get('volume_min', 0.01))
                        es95 = position_size * stop_loss_distance * 1.645
                        logger.debug(
                            f"{symbol}/{alpha_id} ES95 scaled: ${initial_es95:.2f} → ${es95:.2f}, "
                            f"lots: {initial_position_size:.4f} → {position_size:.4f}"
                        )
                    else:
                        position_size = initial_position_size
                        es95 = initial_es95
                    
                    logger.info(f"{symbol}/{alpha_id} passed Q* filter - ES95=${es95:.2f}, pos_size={position_size:.4f}, sl_dist={stop_loss_distance:.2f}")
                    
                    # Filter by ES95
                    if es95 > self.max_es95:
                        logger.info(f"Skipping {symbol}/{alpha_id} - ES95 too high: ${es95:.2f} > ${self.max_es95:.2f}")
                        self.skip_count += 1
                        continue
                    
                    # Check correlation with existing positions
                    if existing_positions:
                        portfolio_corr = correlation_engine.get_portfolio_correlation(
                            symbol, existing_positions
                        )
                        if portfolio_corr > self.max_correlation:
                            logger.info(f"Skipping {symbol}/{alpha_id} - high correlation: {portfolio_corr:.2f} > {self.max_correlation:.2f}")
                            self.skip_count += 1
                            continue
                    
                    # Create trading plan with weighted values
                    bandit_info = " [TS-selected]" if alpha_id == best_alpha_id else ""
                    plan = TradingPlan(
                        symbol=symbol,
                        alpha_id=alpha_id,
                        action=signal['action'],
                        confidence=weighted_confidence,
                        q_star=weighted_q_star,
                        es95=es95,
                        expected_rr=signal['expected_rr'],
                        features=features,
                        ml_predictions=ml_predictions,
                        reason=f"{signal['reason']} (weight={alpha_weight:.2f}, regime={regime}{bandit_info})"
                    )
                    
                    # Add to priority queue
                    heapq.heappush(plans, plan)
            
            # Get top K plans
            top_plans = heapq.nsmallest(self.max_signals, plans)
            
            # Update statistics
            self.total_evaluated += evaluated
            skip_rate = (self.skip_count / max(1, self.total_evaluated)) * 100
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            self.scan_times.append(elapsed)
            self.signals_generated.append(len(top_plans))
            
            # Keep only last 100 scans for stats
            if len(self.scan_times) > 100:
                self.scan_times = self.scan_times[-100:]
                self.signals_generated = self.signals_generated[-100:]
            
            # Calculate throughput
            throughput = evaluated / elapsed if elapsed > 0 else 0
            
            logger.info(
                f"Scan #{self.scan_count}: Evaluated {evaluated} combos in {elapsed:.3f}s "
                f"({throughput:.1f} combos/s), Found {len(top_plans)} signals, "
                f"Skip rate: {skip_rate:.1f}%"
            )
            
            if top_plans:
                for plan in top_plans:
                    grade = "A+" if plan.q_star >= 8.5 else "A"
                    logger.info(
                        f"  → [{grade}] {plan.symbol} {plan.action} via {plan.alpha_id}: "
                        f"Q*={plan.q_star:.2f}, ES95=${plan.es95:.2f}, "
                        f"Conf={plan.confidence:.2f}, P(win)={plan.ml_predictions.get('rf_pwin', 0):.2f}"
                    )
            else:
                logger.debug("  No signals met criteria")
            
            return top_plans
            
        except Exception as e:
            logger.error(f"Error in scanner: {e}", exc_info=True)
            return []
    
    def get_stats(self) -> Dict:
        """Get scanner statistics"""
        avg_scan_time = np.mean(self.scan_times) if self.scan_times else 0
        avg_signals = np.mean(self.signals_generated) if self.signals_generated else 0
        
        return {
            'scan_count': self.scan_count,
            'total_evaluated': self.total_evaluated,
            'skip_count': self.skip_count,
            'skip_rate': (self.skip_count / max(1, self.total_evaluated)) * 100,
            'symbols': len(self.symbols),
            'alphas': len(self.alphas),
            'combinations_per_scan': len(self.symbols) * len(self.alphas),
            'avg_scan_time_s': avg_scan_time,
            'avg_signals_per_scan': avg_signals,
            'target_skip_rate': 90.0,  # Target >90% rejection
            'meeting_target': (self.skip_count / max(1, self.total_evaluated)) * 100 > 90.0,
            'alpha_weights': alpha_weighting.get_all_weights(),
            'alpha_performance': alpha_weighting.get_all_performance(),
            'bandit_statistics': alpha_bandit.get_statistics(),
        }
    
    def reset_stats(self):
        """Reset scanner statistics"""
        self.scan_count = 0
        self.skip_count = 0
        self.total_evaluated = 0
        self.scan_times = []
        self.signals_generated = []
        logger.info("Scanner statistics reset")
    
    async def continuous_scan(
        self,
        interval_seconds: float = 1.5,
        max_iterations: Optional[int] = None
    ):
        """
        Run continuous scanning loop
        
        Args:
            interval_seconds: Time between scans
            max_iterations: Maximum number of scans (None = infinite)
        """
        iteration = 0
        
        logger.info(f"Starting continuous scanner (interval: {interval_seconds}s)")
        
        try:
            while max_iterations is None or iteration < max_iterations:
                # Run scan
                plans = await self.scan()
                
                # TODO: Send plans to signal queue or API endpoint
                
                # Wait for next iteration
                await asyncio.sleep(interval_seconds)
                
                iteration += 1
                
        except asyncio.CancelledError:
            logger.info("Scanner stopped")
        except Exception as e:
            logger.error(f"Error in continuous scanner: {e}", exc_info=True)


# Global scanner instance
global_scanner = GlobalScanner()
