//+------------------------------------------------------------------+
//|                                                  RiskManager.mqh |
//|                        Risk Management and Position Sizing       |
//+------------------------------------------------------------------+
#property copyright "Quant Ω Supra AI"
#property version   "1.00"
#property strict

#include "Structures.mqh"

//+------------------------------------------------------------------+
//| Risk Manager Class                                               |
//+------------------------------------------------------------------+
class CRiskManager
{
private:
    double m_equity;
    double m_balance;
    double m_dailyPnL;
    double m_totalPnL;
    double m_startingBalance;
    datetime m_lastResetTime;
    
public:
    //--- Constructor
    CRiskManager()
    {
        m_equity = AccountInfoDouble(ACCOUNT_EQUITY);
        m_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        m_startingBalance = 1000.0; // VPropTrader starting balance
        m_dailyPnL = 0.0;
        m_totalPnL = 0.0;
        m_lastResetTime = TimeCurrent();
    }
    
    //--- Update equity and PnL
    void Update()
    {
        m_equity = AccountInfoDouble(ACCOUNT_EQUITY);
        m_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        
        // Calculate total PnL
        m_totalPnL = m_equity - m_startingBalance;
        
        // Reset daily PnL at midnight
        MqlDateTime dt;
        TimeToStruct(TimeCurrent(), dt);
        MqlDateTime lastDt;
        TimeToStruct(m_lastResetTime, lastDt);
        
        if(dt.day != lastDt.day)
        {
            m_dailyPnL = 0.0;
            m_lastResetTime = TimeCurrent();
            Print("Daily PnL reset at midnight");
        }
        
        // Calculate daily PnL (simplified - actual should track from day start)
        m_dailyPnL = AccountInfoDouble(ACCOUNT_PROFIT);
    }
    
    //--- Get current PnL values
    double GetDailyPnL() { return m_dailyPnL; }
    double GetTotalPnL() { return m_totalPnL; }
    double GetEquity() { return m_equity; }
    
    //--- Validate position size
    bool ValidatePositionSize(double lots, string symbol)
    {
        // Check minimum and maximum volume
        double minVol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
        double maxVol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
        double stepVol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
        
        if(lots < minVol || lots > maxVol)
        {
            Print("Invalid lot size: ", lots, " (min: ", minVol, ", max: ", maxVol, ")");
            return false;
        }
        
        // Check if lot size is multiple of step
        // Round to step to handle floating-point precision issues
        double rounded = MathRound(lots / stepVol) * stepVol;
        double difference = MathAbs(lots - rounded);
        if(difference > stepVol * 0.01) // Allow 1% tolerance
        {
            Print("Lot size not multiple of step: ", lots, " (step: ", stepVol, ", rounded: ", rounded, ")");
            return false;
        }
        
        // Check margin requirements
        double margin;
        if(!OrderCalcMargin(ORDER_TYPE_BUY, symbol, lots, SymbolInfoDouble(symbol, SYMBOL_ASK), margin))
        {
            Print("Failed to calculate margin for ", lots, " lots of ", symbol);
            return false;
        }
        
        double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
        if(margin > freeMargin * 0.8) // Use max 80% of free margin
        {
            Print("Insufficient margin: need ", margin, ", have ", freeMargin);
            return false;
        }
        
        return true;
    }
    
    //--- Calculate position size (simplified - actual Kelly in Sidecar)
    double CalculatePositionSize(double riskAmount, double stopLossPoints, string symbol)
    {
        double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
        double tickSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
        double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
        
        if(stopLossPoints <= 0 || tickValue <= 0)
            return 0.01; // Minimum safe size
        
        // Calculate risk per lot
        double riskPerLot = (stopLossPoints / point) * tickValue;
        
        // Calculate lots
        double lots = riskAmount / riskPerLot;
        
        // Round to volume step
        double stepVol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
        lots = MathFloor(lots / stepVol) * stepVol;
        
        // Ensure within limits
        double minVol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
        double maxVol = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
        lots = MathMax(minVol, MathMin(maxVol, lots));
        
        return lots;
    }
    
    //--- Check if within risk limits
    bool IsWithinRiskLimits()
    {
        Update();
        
        // Daily loss limit
        if(m_dailyPnL <= DAILY_LOSS_LIMIT)
        {
            Print("Risk limit: Daily loss ", m_dailyPnL, " <= ", DAILY_LOSS_LIMIT);
            return false;
        }
        
        // Total loss limit
        if(m_totalPnL <= TOTAL_LOSS_LIMIT)
        {
            Print("Risk limit: Total loss ", m_totalPnL, " <= ", TOTAL_LOSS_LIMIT);
            return false;
        }
        
        // Equity threshold
        if(m_equity < EQUITY_DISABLE)
        {
            Print("Risk limit: Equity ", m_equity, " < ", EQUITY_DISABLE);
            return false;
        }
        
        // Profit target
        if(m_totalPnL >= PROFIT_TARGET)
        {
            Print("Risk limit: Profit target reached ", m_totalPnL, " >= ", PROFIT_TARGET);
            return false;
        }
        
        // Daily profit cap
        double dailyProfitPct = (m_dailyPnL / m_equity) * 100;
        if(dailyProfitPct >= DAILY_PROFIT_CAP_PCT)
        {
            Print("Risk limit: Daily profit cap ", dailyProfitPct, "% >= ", DAILY_PROFIT_CAP_PCT, "%");
            return false;
        }
        
        return true;
    }
    
    //--- Validate trading signal
    bool ValidateSignal(SignalData &signal)
    {
        // Check if signal has valid data
        if(signal.symbol == "" || signal.action == "")
        {
            Print("Invalid signal: empty symbol or action");
            return false;
        }
        
        // Check confidence threshold
        if(signal.confidence < 0.5)
        {
            Print("Signal confidence too low: ", signal.confidence);
            return false;
        }
        
        // Validate position size
        if(!ValidatePositionSize(signal.lots, signal.symbol))
        {
            return false;
        }
        
        return true;
    }
    
    //--- Check if can take new position
    bool CanTakeNewPosition()
    {
        // Check risk limits first
        if(!IsWithinRiskLimits())
        {
            return false;
        }
        
        // Check maximum open positions
        int openPositions = PositionsTotal();
        if(openPositions >= MAX_OPEN_POSITIONS)
        {
            Print("Maximum open positions reached: ", openPositions);
            return false;
        }
        
        return true;
    }
    
    //--- Check execution quality
    bool CheckExecutionQuality(string symbol, double spread)
    {
        // Get average spread
        double avgSpread = SymbolInfoInteger(symbol, SYMBOL_SPREAD) * SymbolInfoDouble(symbol, SYMBOL_POINT);
        
        // Check if spread is reasonable (not more than 2x average)
        if(spread > avgSpread * 2.0)
        {
            Print("Spread too high: ", spread, " > ", avgSpread * 2.0);
            return false;
        }
        
        // Check if market is open
        if(!SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE))
        {
            Print("Market closed for ", symbol);
            return false;
        }
        
        return true;
    }
};

//+------------------------------------------------------------------+
