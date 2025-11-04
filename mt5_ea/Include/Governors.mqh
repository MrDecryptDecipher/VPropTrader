//+------------------------------------------------------------------+
//|                                                    Governors.mqh |
//|                        Hard and Soft Governors                   |
//+------------------------------------------------------------------+
#property copyright "Quant Ω Supra AI"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| Governors Class                                                  |
//+------------------------------------------------------------------+
class CGovernors
{
private:
    double m_dailyPnL;
    double m_totalPnL;
    double m_equity;
    datetime m_lastLossTime;
    bool m_profitLocked;
    double m_lockedProfit;
    int m_consecutiveLosses;
    
public:
    //--- Constructor
    CGovernors()
    {
        m_dailyPnL = 0.0;
        m_totalPnL = 0.0;
        m_equity = AccountInfoDouble(ACCOUNT_EQUITY);
        m_lastLossTime = 0;
        m_profitLocked = false;
        m_lockedProfit = 0.0;
        m_consecutiveLosses = 0;
    }
    
    //--- Update PnL values
    void Update(double dailyPnL, double totalPnL)
    {
        m_dailyPnL = dailyPnL;
        m_totalPnL = totalPnL;
        m_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    }
    
    //--- Check hard governors
    bool CheckHardGovernors()
    {
        // Daily loss limit
        if(m_dailyPnL <= DAILY_LOSS_LIMIT)
        {
            Print("HARD GOVERNOR: Daily loss limit reached: $", m_dailyPnL, " <= $", DAILY_LOSS_LIMIT);
            return false;
        }
        
        // Total loss limit
        if(m_totalPnL <= TOTAL_LOSS_LIMIT)
        {
            Print("HARD GOVERNOR: Total loss limit reached: $", m_totalPnL, " <= $", TOTAL_LOSS_LIMIT);
            return false;
        }
        
        // Equity disable threshold
        if(m_equity < EQUITY_DISABLE)
        {
            Print("HARD GOVERNOR: Equity below threshold: $", m_equity, " < $", EQUITY_DISABLE);
            return false;
        }
        
        // Profit target
        if(m_totalPnL >= PROFIT_TARGET)
        {
            Print("HARD GOVERNOR: Profit target reached: $", m_totalPnL, " >= $", PROFIT_TARGET);
            return false;
        }
        
        // Daily profit cap
        double dailyProfitPct = (m_dailyPnL / m_equity) * 100;
        if(dailyProfitPct >= DAILY_PROFIT_CAP_PCT)
        {
            Print("HARD GOVERNOR: Daily profit cap reached: ", dailyProfitPct, "% >= ", DAILY_PROFIT_CAP_PCT, "%");
            return false;
        }
        
        return true;
    }
    
    //--- Check soft governors
    bool CheckSoftGovernors()
    {
        // Cool-down after loss
        if(m_lastLossTime > 0)
        {
            datetime elapsed = TimeCurrent() - m_lastLossTime;
            if(elapsed < CooldownAfterLossSec)
            {
                if(VerboseLogging)
                    Print("SOFT GOVERNOR: Cool-down active (", CooldownAfterLossSec - elapsed, "s remaining)");
                return false;
            }
        }
        
        // Consecutive losses limit
        if(m_consecutiveLosses >= 3)
        {
            Print("SOFT GOVERNOR: Too many consecutive losses: ", m_consecutiveLosses);
            return false;
        }
        
        // Volatility cap (simplified - check spread)
        for(int i = 0; i < PositionsTotal(); i++)
        {
            if(PositionSelectByTicket(PositionGetTicket(i)))
            {
                string symbol = PositionGetString(POSITION_SYMBOL);
                double spread = SymbolInfoInteger(symbol, SYMBOL_SPREAD) * SymbolInfoDouble(symbol, SYMBOL_POINT);
                double avgSpread = spread; // Simplified - should track average
                
                if(spread > avgSpread * 2.0)
                {
                    Print("SOFT GOVERNOR: High spread detected: ", spread);
                    return false;
                }
            }
        }
        
        // Profit lock
        if(EnableProfitLock && m_totalPnL > 50.0 && !m_profitLocked)
        {
            m_profitLocked = true;
            m_lockedProfit = m_totalPnL * 0.7; // Lock 70% of profit
            Print("SOFT GOVERNOR: Profit locked at $", m_lockedProfit);
        }
        
        if(m_profitLocked && m_totalPnL < m_lockedProfit)
        {
            Print("SOFT GOVERNOR: Profit lock triggered - below locked level");
            return false;
        }
        
        return true;
    }
    
    //--- Check time-based governors
    bool CheckTimeGovernors()
    {
        MqlDateTime dt;
        TimeToStruct(TimeGMT(), dt);
        
        // Daily close time (21:45 UTC)
        if(dt.hour == DAILY_CLOSE_HOUR && dt.min >= DAILY_CLOSE_MINUTE)
        {
            Print("TIME GOVERNOR: Daily close time reached");
            return false;
        }
        
        // Friday close time (20:00 UTC)
        if(dt.day_of_week == 5 && dt.hour >= FRIDAY_CLOSE_HOUR)
        {
            Print("TIME GOVERNOR: Friday close time reached");
            return false;
        }
        
        return true;
    }
    
    //--- Check if in trading session
    bool IsInTradingSession()
    {
        MqlDateTime dt;
        TimeToStruct(TimeGMT(), dt);
        
        int hour = dt.hour;
        int minute = dt.min;
        
        // London session: 07:00-10:00 UTC
        if(hour >= LONDON_START_HOUR && hour < LONDON_END_HOUR)
            return true;
        
        // NY session: 13:30-16:00 UTC
        if(hour > NY_START_HOUR || (hour == NY_START_HOUR && minute >= NY_START_MINUTE))
            if(hour < NY_END_HOUR)
                return true;
        
        return false;
    }
    
    //--- Record loss for cool-down
    void RecordLoss()
    {
        m_lastLossTime = TimeCurrent();
        m_consecutiveLosses++;
        Print("Loss recorded - consecutive losses: ", m_consecutiveLosses);
    }
    
    //--- Record win (reset consecutive losses)
    void RecordWin()
    {
        m_consecutiveLosses = 0;
    }
    
    //--- Reset cool-down
    void ResetCooldown()
    {
        m_lastLossTime = 0;
    }
    
    //--- Check if should close all positions (time-based)
    bool ShouldCloseAllPositions()
    {
        MqlDateTime dt;
        TimeToStruct(TimeCurrent(), dt);
        
        // Close all at 21:45 UTC (before daily rollover)
        if(dt.hour == 21 && dt.min >= 45)
        {
            return true;
        }
        
        // Close all on Friday at 20:00 UTC (before weekend)
        if(dt.day_of_week == 5 && dt.hour >= 20)
        {
            return true;
        }
        
        return false;
    }
};

//+------------------------------------------------------------------+
