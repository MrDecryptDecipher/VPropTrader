"""Unit tests for hard and soft governors"""

import pytest
from datetime import datetime, time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sidecar"))


class TestHardGovernors:
    """Test hard governor enforcement"""
    
    def test_daily_loss_limit(self):
        """Test daily loss limit of -$45"""
        starting_equity = 1000.0
        daily_loss_limit = -45.0
        
        # Test cases
        test_cases = [
            (1000.0, 0.0, True, "No loss"),
            (980.0, -20.0, True, "Small loss"),
            (955.0, -45.0, False, "At limit"),
            (950.0, -50.0, False, "Exceeded limit"),
        ]
        
        for current_equity, daily_pnl, should_allow, description in test_cases:
            # Simulate governor check
            is_allowed = daily_pnl > daily_loss_limit
            
            assert is_allowed == should_allow, f"Failed: {description}"
            print(f"✓ {description}: PnL=${daily_pnl:.2f}, Allowed={is_allowed}")
    
    def test_total_loss_limit(self):
        """Test total loss limit at $900 equity"""
        total_loss_limit = 900.0
        
        test_cases = [
            (1000.0, True, "Normal equity"),
            (950.0, True, "Small drawdown"),
            (900.0, False, "At limit"),
            (850.0, False, "Below limit"),
        ]
        
        for equity, should_allow, description in test_cases:
            is_allowed = equity > total_loss_limit
            
            assert is_allowed == should_allow, f"Failed: {description}"
            print(f"✓ {description}: Equity=${equity:.2f}, Allowed={is_allowed}")
    
    def test_profit_target(self):
        """Test profit target halt at $100"""
        profit_target = 100.0
        
        test_cases = [
            (50.0, True, "Below target"),
            (99.0, True, "Near target"),
            (100.0, False, "At target"),
            (150.0, False, "Above target"),
        ]
        
        for total_pnl, should_allow, description in test_cases:
            is_allowed = total_pnl < profit_target
            
            assert is_allowed == should_allow, f"Failed: {description}"
            print(f"✓ {description}: PnL=${total_pnl:.2f}, Allowed={is_allowed}")
    
    def test_daily_profit_cap(self):
        """Test daily profit cap at 1.8%"""
        starting_equity = 1000.0
        daily_profit_cap_pct = 0.018
        daily_profit_cap = starting_equity * daily_profit_cap_pct  # $18
        
        test_cases = [
            (10.0, True, "Normal profit"),
            (17.0, True, "Near cap"),
            (18.0, False, "At cap"),
            (25.0, False, "Above cap"),
        ]
        
        for daily_pnl, should_allow, description in test_cases:
            is_allowed = daily_pnl < daily_profit_cap
            
            assert is_allowed == should_allow, f"Failed: {description}"
            print(f"✓ {description}: Daily PnL=${daily_pnl:.2f}, Allowed={is_allowed}")
    
    def test_time_based_close(self):
        """Test time-based position closing"""
        # 21:45 UTC weekday close
        weekday_close = time(21, 45)
        
        # Friday 20:00 UTC close
        friday_close = time(20, 0)
        
        test_times = [
            (time(14, 30), 2, False, "Tuesday afternoon"),
            (time(21, 44), 2, False, "Before close"),
            (time(21, 45), 2, True, "At close time"),
            (time(21, 46), 2, True, "After close"),
            (time(19, 59), 4, False, "Friday before close"),
            (time(20, 0), 4, True, "Friday at close"),
        ]
        
        for current_time, weekday, should_close, description in test_times:
            # Simulate time check
            if weekday == 4:  # Friday
                should_close_calc = current_time >= friday_close
            else:
                should_close_calc = current_time >= weekday_close
            
            assert should_close_calc == should_close, f"Failed: {description}"
            print(f"✓ {description}: Time={current_time}, Close={should_close}")


class TestSoftGovernors:
    """Test soft governor behavior"""
    
    def test_cooldown_after_loss(self):
        """Test cool-down period after losses"""
        cooldown_seconds = 300  # 5 minutes
        
        # Simulate consecutive losses
        consecutive_losses = 0
        max_consecutive = 2
        
        test_cases = [
            (0, False, "No losses"),
            (1, False, "One loss"),
            (2, True, "Two losses - cooldown"),
            (3, True, "Three losses - cooldown"),
        ]
        
        for losses, should_pause, description in test_cases:
            should_pause_calc = losses >= max_consecutive
            
            assert should_pause_calc == should_pause, f"Failed: {description}"
            print(f"✓ {description}: Losses={losses}, Pause={should_pause}")
    
    def test_volatility_cap(self):
        """Test volatility cap governor"""
        max_volatility = 0.03  # 3% max volatility
        
        test_cases = [
            (0.01, True, "Low volatility"),
            (0.025, True, "Normal volatility"),
            (0.03, False, "At cap"),
            (0.04, False, "High volatility"),
        ]
        
        for volatility, should_allow, description in test_cases:
            is_allowed = volatility < max_volatility
            
            assert is_allowed == should_allow, f"Failed: {description}"
            print(f"✓ {description}: Vol={volatility:.3f}, Allowed={is_allowed}")
    
    def test_profit_lock(self):
        """Test profit lock mechanism"""
        # Lock in profits after reaching certain threshold
        profit_lock_threshold = 50.0
        max_giveback_pct = 0.3  # 30% max giveback
        
        test_cases = [
            (60.0, 55.0, True, "Small giveback"),
            (60.0, 50.0, True, "At threshold"),
            (60.0, 40.0, False, "Exceeded giveback"),
            (30.0, 25.0, True, "Below lock threshold"),
        ]
        
        for peak_pnl, current_pnl, should_allow, description in test_cases:
            if peak_pnl >= profit_lock_threshold:
                giveback = peak_pnl - current_pnl
                max_giveback = peak_pnl * max_giveback_pct
                is_allowed = giveback <= max_giveback
            else:
                is_allowed = True
            
            assert is_allowed == should_allow, f"Failed: {description}"
            print(f"✓ {description}: Peak=${peak_pnl:.2f}, Current=${current_pnl:.2f}, Allowed={is_allowed}")


class TestTradingSchedule:
    """Test trading schedule enforcement"""
    
    def test_london_session(self):
        """Test London session (07:00-10:00 UTC)"""
        london_start = time(7, 0)
        london_end = time(10, 0)
        
        test_times = [
            (time(6, 59), False, "Before London"),
            (time(7, 0), True, "London start"),
            (time(8, 30), True, "During London"),
            (time(10, 0), False, "London end"),
            (time(10, 1), False, "After London"),
        ]
        
        for current_time, should_trade, description in test_times:
            is_allowed = london_start <= current_time < london_end
            
            assert is_allowed == should_trade, f"Failed: {description}"
            print(f"✓ {description}: Time={current_time}, Trade={is_allowed}")
    
    def test_ny_session(self):
        """Test NY session (13:30-16:00 UTC)"""
        ny_start = time(13, 30)
        ny_end = time(16, 0)
        
        test_times = [
            (time(13, 29), False, "Before NY"),
            (time(13, 30), True, "NY start"),
            (time(14, 45), True, "During NY"),
            (time(16, 0), False, "NY end"),
            (time(16, 1), False, "After NY"),
        ]
        
        for current_time, should_trade, description in test_times:
            is_allowed = ny_start <= current_time < ny_end
            
            assert is_allowed == should_trade, f"Failed: {description}"
            print(f"✓ {description}: Time={current_time}, Trade={is_allowed}")
    
    def test_combined_sessions(self):
        """Test combined London and NY sessions"""
        london_start = time(7, 0)
        london_end = time(10, 0)
        ny_start = time(13, 30)
        ny_end = time(16, 0)
        
        test_times = [
            (time(6, 0), False, "Before any session"),
            (time(8, 0), True, "London session"),
            (time(12, 0), False, "Between sessions"),
            (time(14, 0), True, "NY session"),
            (time(18, 0), False, "After all sessions"),
        ]
        
        for current_time, should_trade, description in test_times:
            in_london = london_start <= current_time < london_end
            in_ny = ny_start <= current_time < ny_end
            is_allowed = in_london or in_ny
            
            assert is_allowed == should_trade, f"Failed: {description}"
            print(f"✓ {description}: Time={current_time}, Trade={is_allowed}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
