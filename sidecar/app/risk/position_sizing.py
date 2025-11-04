"""Position Sizing with Fractional Kelly and Risk Management"""

import numpy as np
from typing import Dict, Optional
from loguru import logger
from app.core import settings


class PositionSizer:
    """Calculate position sizes using Kelly criterion with entropy penalty"""
    
    def __init__(self):
        self.max_risk_per_trade = 0.01  # 1% of equity per trade
        self.kelly_fraction = 0.5  # Half Kelly for safety
        self.target_daily_vol = 0.01  # 1% daily volatility target
    
    def calculate_kelly_size(
        self,
        p_win: float,
        expected_rr: float,
        entropy: float = 0.5
    ) -> float:
        """
        Calculate fractional Kelly position size with entropy penalty
        
        Formula: f = 0.5 * (E[R] / Var[R]) * (1 - H/H_max)
        
        Args:
            p_win: Probability of winning (from ML model)
            expected_rr: Expected risk-reward ratio
            entropy: Signal entropy (0 = certain, 1 = random)
        
        Returns:
            Position size as fraction of equity
        """
        try:
            # Expected return
            expected_return = p_win * expected_rr - (1 - p_win)
            
            # Variance of returns (simplified)
            # Var[R] ≈ p * (RR)^2 + (1-p) * 1^2 - E[R]^2
            variance = p_win * (expected_rr ** 2) + (1 - p_win) - (expected_return ** 2)
            
            if variance <= 0:
                return 0.0
            
            # Kelly fraction
            kelly = expected_return / variance
            
            # Entropy penalty (H_max = log(2) for binary outcome)
            h_max = np.log(2)
            entropy_penalty = 1 - (entropy / h_max)
            
            # Fractional Kelly with entropy adjustment
            position_fraction = self.kelly_fraction * kelly * entropy_penalty
            
            # Clip to reasonable range
            position_fraction = np.clip(position_fraction, 0.0, self.max_risk_per_trade)
            
            return float(position_fraction)
            
        except Exception as e:
            logger.error(f"Error calculating Kelly size: {e}")
            return 0.0
    
    def calculate_position_size(
        self,
        equity: float,
        p_win: float,
        expected_rr: float,
        stop_loss_distance: float,
        symbol_info: Dict,
        entropy: float = 0.5
    ) -> float:
        """
        Calculate position size in lots
        
        Args:
            equity: Account equity
            p_win: Probability of winning
            expected_rr: Expected risk-reward ratio
            stop_loss_distance: Distance to stop loss in price units
            symbol_info: Symbol information (point, tick_value, etc.)
            entropy: Signal entropy
        
        Returns:
            Position size in lots
        """
        try:
            # Kelly fraction of equity
            kelly_fraction = self.calculate_kelly_size(p_win, expected_rr, entropy)
            risk_amount = equity * kelly_fraction
            
            # Calculate lot size based on stop loss
            point = symbol_info.get('point', 0.0001)
            tick_value = symbol_info.get('trade_tick_value', 1.0)
            contract_size = symbol_info.get('trade_contract_size', 100000)
            
            # Risk per lot = stop_loss_distance * tick_value
            if stop_loss_distance > 0:
                risk_per_lot = stop_loss_distance * tick_value
                lots = risk_amount / risk_per_lot if risk_per_lot > 0 else 0
            else:
                lots = 0
            
            # Apply volume constraints
            volume_min = symbol_info.get('volume_min', 0.01)
            volume_max = symbol_info.get('volume_max', 100.0)
            volume_step = symbol_info.get('volume_step', 0.01)
            
            # Round to volume step
            lots = round(lots / volume_step) * volume_step
            
            # Clip to min/max
            lots = np.clip(lots, volume_min, volume_max)
            
            logger.debug(
                f"Position sizing: Kelly={kelly_fraction:.4f}, "
                f"Risk=${risk_amount:.2f}, Lots={lots:.2f}"
            )
            
            return float(lots)
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.01  # Minimum safe size
    
    def apply_volatility_target(
        self,
        lots: float,
        realized_vol: float,
        target_vol: Optional[float] = None
    ) -> float:
        """
        Rescale position size to maintain target volatility
        
        Args:
            lots: Initial position size
            realized_vol: Realized volatility
            target_vol: Target volatility (default: 1% daily)
        
        Returns:
            Adjusted position size
        """
        if target_vol is None:
            target_vol = self.target_daily_vol
        
        try:
            if realized_vol > 0:
                vol_scalar = target_vol / realized_vol
                adjusted_lots = lots * vol_scalar
                
                # Don't scale up too much
                adjusted_lots = min(adjusted_lots, lots * 1.5)
                
                logger.debug(
                    f"Vol-target rescaling: {lots:.2f} → {adjusted_lots:.2f} "
                    f"(realized_vol={realized_vol:.4f})"
                )
                
                return float(adjusted_lots)
            
            return lots
            
        except Exception as e:
            logger.error(f"Error applying volatility target: {e}")
            return lots
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        volatility: float,
        action: str,
        multiplier: float = 0.8
    ) -> float:
        """
        Calculate stop loss level
        
        Formula: SL = entry ± (multiplier * volatility)
        
        Args:
            entry_price: Entry price
            volatility: Volatility estimate
            action: 'BUY' or 'SELL'
            multiplier: Volatility multiplier (default: 0.8)
        
        Returns:
            Stop loss price
        """
        sl_distance = entry_price * volatility * multiplier
        
        if action == 'BUY':
            return entry_price - sl_distance
        else:  # SELL
            return entry_price + sl_distance
    
    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        action: str,
        rr_ratio: float = 1.5
    ) -> float:
        """
        Calculate take profit level
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            action: 'BUY' or 'SELL'
            rr_ratio: Risk-reward ratio
        
        Returns:
            Take profit price
        """
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * rr_ratio
        
        if action == 'BUY':
            return entry_price + tp_distance
        else:  # SELL
            return entry_price - tp_distance


# Global position sizer instance
position_sizer = PositionSizer()
