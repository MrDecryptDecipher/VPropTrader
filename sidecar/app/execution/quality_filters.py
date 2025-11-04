"""Execution Quality Filters - Spread, Slippage, Latency, Quote Quality"""

import numpy as np
from typing import Dict, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
from loguru import logger

from app.data.redis_client import redis_client


class ExecutionQualityFilters:
    """
    Filters to prevent trading in poor execution conditions
    - Spread filter (60th percentile)
    - Slippage prediction
    - Latency monitoring (>400ms pause)
    - Quote flicker detection
    """
    
    def __init__(self):
        # Spread tracking
        self.spread_history = {}  # {symbol: deque of spreads}
        self.spread_window = 100  # Track last 100 spreads
        self.spread_percentile = 60  # 60th percentile threshold
        
        # Slippage prediction
        self.slippage_history = {}  # {symbol: deque of slippages}
        self.slippage_threshold = 2.0  # Max acceptable slippage in pips
        
        # Latency monitoring
        self.latency_history = deque(maxlen=50)
        self.latency_threshold = 400.0  # 400ms threshold
        self.high_latency_count = 0
        self.latency_pause_threshold = 3  # Pause after 3 high latency events
        
        # Quote flicker detection
        self.quote_history = {}  # {symbol: deque of quote times}
        self.flicker_window = 10  # seconds
        self.flicker_threshold = 20  # Max quotes per window
        
        # State
        self.trading_paused = False
        self.pause_until = None
        self.pause_reason = None
    
    def check_spread(self, symbol: str, current_spread: float) -> Tuple[bool, str]:
        """
        Check if spread is acceptable (below 60th percentile)
        
        Args:
            symbol: Trading symbol
            current_spread: Current spread in pips
        
        Returns:
            (is_acceptable, reason)
        """
        try:
            # Initialize history if needed
            if symbol not in self.spread_history:
                self.spread_history[symbol] = deque(maxlen=self.spread_window)
            
            # Add current spread to history
            self.spread_history[symbol].append(current_spread)
            
            # Need minimum history
            if len(self.spread_history[symbol]) < 20:
                return True, "Insufficient spread history"
            
            # Calculate 60th percentile
            spreads = list(self.spread_history[symbol])
            percentile_60 = np.percentile(spreads, self.spread_percentile)
            
            # Check if current spread exceeds threshold
            if current_spread > percentile_60:
                logger.warning(
                    f"Spread filter: {symbol} spread {current_spread:.2f} "
                    f"exceeds 60th percentile {percentile_60:.2f}"
                )
                return False, f"Spread too high: {current_spread:.2f} > {percentile_60:.2f}"
            
            return True, "Spread acceptable"
            
        except Exception as e:
            logger.error(f"Error in spread filter: {e}")
            return True, "Spread filter error"
    
    def predict_slippage(
        self,
        symbol: str,
        order_size: float,
        volatility: float,
        spread: float
    ) -> Tuple[float, bool]:
        """
        Predict expected slippage and check if acceptable
        
        Args:
            symbol: Trading symbol
            order_size: Order size in lots
            volatility: Current volatility
            spread: Current spread
        
        Returns:
            (predicted_slippage, is_acceptable)
        """
        try:
            # Simple slippage model
            # Slippage = base_spread + volatility_component + size_component
            
            # Base slippage from spread
            base_slippage = spread * 0.5
            
            # Volatility component (higher vol = more slippage)
            vol_slippage = volatility * 100 * 0.3
            
            # Size component (larger orders = more slippage)
            size_slippage = order_size * 0.1
            
            # Total predicted slippage
            predicted_slippage = base_slippage + vol_slippage + size_slippage
            
            # Check against threshold
            is_acceptable = predicted_slippage <= self.slippage_threshold
            
            if not is_acceptable:
                logger.warning(
                    f"Slippage prediction: {symbol} predicted slippage "
                    f"{predicted_slippage:.2f} exceeds threshold {self.slippage_threshold}"
                )
            
            return predicted_slippage, is_acceptable
            
        except Exception as e:
            logger.error(f"Error predicting slippage: {e}")
            return 0.0, True
    
    def record_actual_slippage(self, symbol: str, slippage: float):
        """Record actual slippage for model improvement"""
        try:
            if symbol not in self.slippage_history:
                self.slippage_history[symbol] = deque(maxlen=100)
            
            self.slippage_history[symbol].append(slippage)
            
        except Exception as e:
            logger.error(f"Error recording slippage: {e}")
    
    def check_latency(self, latency_ms: float) -> Tuple[bool, str]:
        """
        Check if latency is acceptable
        
        Args:
            latency_ms: Latency in milliseconds
        
        Returns:
            (is_acceptable, reason)
        """
        try:
            # Add to history
            self.latency_history.append(latency_ms)
            
            # Check if exceeds threshold
            if latency_ms > self.latency_threshold:
                self.high_latency_count += 1
                
                logger.warning(
                    f"High latency detected: {latency_ms:.1f}ms "
                    f"(count: {self.high_latency_count})"
                )
                
                # Pause trading if too many high latency events
                if self.high_latency_count >= self.latency_pause_threshold:
                    self.pause_trading(
                        duration_seconds=60,
                        reason=f"High latency: {latency_ms:.1f}ms"
                    )
                    return False, "Trading paused due to high latency"
                
                return False, f"Latency too high: {latency_ms:.1f}ms"
            
            else:
                # Reset counter on good latency
                if self.high_latency_count > 0:
                    self.high_latency_count = max(0, self.high_latency_count - 1)
            
            return True, "Latency acceptable"
            
        except Exception as e:
            logger.error(f"Error checking latency: {e}")
            return True, "Latency check error"
    
    def check_quote_flicker(self, symbol: str) -> Tuple[bool, str]:
        """
        Check for quote flicker (too many quote updates)
        
        Args:
            symbol: Trading symbol
        
        Returns:
            (is_acceptable, reason)
        """
        try:
            now = datetime.utcnow()
            
            # Initialize history if needed
            if symbol not in self.quote_history:
                self.quote_history[symbol] = deque(maxlen=100)
            
            # Add current quote time
            self.quote_history[symbol].append(now)
            
            # Count quotes in last window
            cutoff = now - timedelta(seconds=self.flicker_window)
            recent_quotes = [
                t for t in self.quote_history[symbol]
                if t > cutoff
            ]
            
            quote_count = len(recent_quotes)
            
            # Check if exceeds threshold
            if quote_count > self.flicker_threshold:
                logger.warning(
                    f"Quote flicker detected: {symbol} had {quote_count} "
                    f"quotes in {self.flicker_window}s"
                )
                return False, f"Quote flicker: {quote_count} quotes in {self.flicker_window}s"
            
            return True, "Quote quality acceptable"
            
        except Exception as e:
            logger.error(f"Error checking quote flicker: {e}")
            return True, "Quote flicker check error"
    
    def pause_trading(self, duration_seconds: int, reason: str):
        """Pause trading for specified duration"""
        self.trading_paused = True
        self.pause_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
        self.pause_reason = reason
        
        logger.warning(
            f"Trading paused for {duration_seconds}s: {reason} "
            f"(until {self.pause_until.isoformat()})"
        )
    
    def is_trading_paused(self) -> Tuple[bool, Optional[str]]:
        """Check if trading is currently paused"""
        if not self.trading_paused:
            return False, None
        
        # Check if pause has expired
        if datetime.utcnow() > self.pause_until:
            self.trading_paused = False
            self.pause_until = None
            self.pause_reason = None
            logger.info("Trading pause expired, resuming normal operation")
            return False, None
        
        return True, self.pause_reason
    
    def check_all_filters(
        self,
        symbol: str,
        spread: float,
        order_size: float,
        volatility: float,
        latency_ms: float
    ) -> Tuple[bool, list[str]]:
        """
        Check all execution quality filters
        
        Args:
            symbol: Trading symbol
            spread: Current spread
            order_size: Order size in lots
            volatility: Current volatility
            latency_ms: Execution latency
        
        Returns:
            (all_passed, list_of_failures)
        """
        failures = []
        
        # Check if trading is paused
        is_paused, pause_reason = self.is_trading_paused()
        if is_paused:
            failures.append(f"Trading paused: {pause_reason}")
            return False, failures
        
        # Check spread
        spread_ok, spread_msg = self.check_spread(symbol, spread)
        if not spread_ok:
            failures.append(spread_msg)
        
        # Check slippage prediction
        predicted_slip, slip_ok = self.predict_slippage(
            symbol, order_size, volatility, spread
        )
        if not slip_ok:
            failures.append(f"Predicted slippage too high: {predicted_slip:.2f}")
        
        # Check latency
        latency_ok, latency_msg = self.check_latency(latency_ms)
        if not latency_ok:
            failures.append(latency_msg)
        
        # Check quote flicker
        flicker_ok, flicker_msg = self.check_quote_flicker(symbol)
        if not flicker_ok:
            failures.append(flicker_msg)
        
        all_passed = len(failures) == 0
        
        if not all_passed:
            logger.info(f"Execution quality filters failed for {symbol}: {', '.join(failures)}")
        
        return all_passed, failures
    
    def get_statistics(self) -> Dict:
        """Get execution quality statistics"""
        try:
            stats = {
                'spread_tracking': {
                    symbol: {
                        'count': len(spreads),
                        'current': spreads[-1] if spreads else 0,
                        'percentile_60': np.percentile(list(spreads), 60) if len(spreads) >= 20 else 0,
                        'avg': np.mean(list(spreads)) if spreads else 0,
                    }
                    for symbol, spreads in self.spread_history.items()
                },
                'latency': {
                    'current': self.latency_history[-1] if self.latency_history else 0,
                    'avg': np.mean(list(self.latency_history)) if self.latency_history else 0,
                    'max': np.max(list(self.latency_history)) if self.latency_history else 0,
                    'high_count': self.high_latency_count,
                },
                'trading_status': {
                    'paused': self.trading_paused,
                    'pause_until': self.pause_until.isoformat() if self.pause_until else None,
                    'pause_reason': self.pause_reason,
                },
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting execution quality stats: {e}")
            return {}


# Global execution quality filters instance
execution_filters = ExecutionQualityFilters()
