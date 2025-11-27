"""
Prop Risk Manager
Enforces strict Prop Firm rules (Drawdown, Daily Loss, Trading Hours).
"""

import logging
from datetime import datetime, time
import pytz
from typing import Dict, Optional
from app.data.user_db import user_db

logger = logging.getLogger(__name__)

class PropRiskManager:
    """
    Guardian of the Prop Account.
    """
    def __init__(self):
        self.current_daily_loss = 0.0
        self.current_total_drawdown = 0.0
        self.rules = {}
        self.last_update = datetime.min
        
    async def load_rules(self):
        """Refresh rules from DB."""
        config = await user_db.get_active_config()
        if config and 'rules' in config:
            self.rules = config['rules']
            logger.info(f"🛡️ Risk Manager loaded rules: Max Daily Loss={self.rules.get('max_daily_loss')}")
            
    async def check_trade_allowed(self, symbol: str, size: float, current_equity: float, initial_balance: float) -> bool:
        """
        Check if a new trade violates any rules.
        """
        if not self.rules:
            await self.load_rules()
            if not self.rules:
                return True # No rules configured, allow (or block safe?) -> Allow for now
        
        # 1. Check Trading Hours
        if not self._check_trading_hours():
            logger.warning(f"⛔ Trade blocked: Outside trading hours ({self.rules.get('trading_hours_start')} - {self.rules.get('trading_hours_end')})")
            return False
            
        # 2. Check Max Total Drawdown
        # Drawdown = Initial Balance - Current Equity
        drawdown = initial_balance - current_equity
        if drawdown >= self.rules.get('max_total_loss', float('inf')):
            logger.critical(f"⛔ Trade blocked: Max Total Drawdown reached! (${drawdown:.2f})")
            return False
            
        # 3. Check Daily Loss
        # This requires tracking daily PnL reset. 
        # For now, we assume self.current_daily_loss is updated externally or via trade_recorder
        if self.current_daily_loss >= self.rules.get('max_daily_loss', float('inf')):
            logger.warning(f"⛔ Trade blocked: Max Daily Loss limit hit! (${self.current_daily_loss:.2f})")
            return False
            
        return True

    def _check_trading_hours(self) -> bool:
        """Check if current time is within allowed window."""
        start_str = self.rules.get('trading_hours_start')
        end_str = self.rules.get('trading_hours_end')
        tz_str = self.rules.get('timezone', 'UTC')
        
        if not start_str or not end_str:
            return True
            
        try:
            tz = pytz.timezone(tz_str)
            now = datetime.now(tz).time()
            start = datetime.strptime(start_str, "%H:%M").time()
            end = datetime.strptime(end_str, "%H:%M").time()
            
            if start <= end:
                return start <= now <= end
            else: # Crosses midnight
                return start <= now or now <= end
        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            return True # Fail open or closed? Open for now to avoid accidental blocks

    def update_daily_loss(self, pnl: float):
        """Update daily loss counter (reset at 00:00 server time)."""
        # Reset logic would go here
        if pnl < 0:
            self.current_daily_loss += abs(pnl)
        # Note: Real implementation needs robust daily reset logic

# Global instance
risk_manager = PropRiskManager()
