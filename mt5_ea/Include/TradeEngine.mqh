//+------------------------------------------------------------------+
//|                                                  TradeEngine.mqh |
//|                        Trade Execution Engine                    |
//+------------------------------------------------------------------+
#property copyright "Quant Ω Supra AI"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include "Structures.mqh"

//+------------------------------------------------------------------+
//| Trade Engine Class                                               |
//+------------------------------------------------------------------+
class CTradeEngine
{
private:
    CTrade m_trade;
    int    m_magicNumber;
    bool   m_logOnlyMode;
    int    m_slippage;
    
public:
    //--- Constructor
    CTradeEngine(int magicNumber, bool logOnlyMode = false)
    {
        m_magicNumber = magicNumber;
        m_logOnlyMode = logOnlyMode;
        m_slippage = 10;
        m_trade.SetExpertMagicNumber(m_magicNumber);
        m_trade.SetDeviationInPoints(m_slippage);
        m_trade.SetTypeFilling(ORDER_FILLING_FOK);
        m_trade.SetAsyncMode(false);
    }
    
    //--- Execute buy order
    bool ExecuteBuy(string symbol, double lots, double sl, double tp)
    {
        if(m_logOnlyMode)
        {
            Print("LOG-ONLY: Would BUY ", lots, " lots of ", symbol, " SL:", sl, " TP:", tp);
            return true;
        }
        
        // Normalize prices
        int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
        double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
        sl = NormalizeDouble(sl, digits);
        tp = NormalizeDouble(tp, digits);
        
        // Validate SL/TP
        double minStop = SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL) * SymbolInfoDouble(symbol, SYMBOL_POINT);
        if(ask - sl < minStop)
        {
            Print("Stop loss too close: ", ask - sl, " < ", minStop);
            sl = ask - minStop;
        }
        if(tp - ask < minStop)
        {
            Print("Take profit too close: ", tp - ask, " < ", minStop);
            tp = ask + minStop;
        }
        
        // Execute order
        if(m_trade.Buy(lots, symbol, ask, sl, tp, "QuantSupraAI"))
        {
            Print("BUY executed: ", symbol, " ", lots, " lots @ ", ask, " SL:", sl, " TP:", tp);
            return true;
        }
        else
        {
            Print("BUY failed: ", m_trade.ResultRetcode(), " - ", m_trade.ResultRetcodeDescription());
            return false;
        }
    }
    
    //--- Execute sell order
    bool ExecuteSell(string symbol, double lots, double sl, double tp)
    {
        if(m_logOnlyMode)
        {
            Print("LOG-ONLY: Would SELL ", lots, " lots of ", symbol, " SL:", sl, " TP:", tp);
            return true;
        }
        
        // Normalize prices
        int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
        double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
        sl = NormalizeDouble(sl, digits);
        tp = NormalizeDouble(tp, digits);
        
        // Validate SL/TP
        double minStop = SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL) * SymbolInfoDouble(symbol, SYMBOL_POINT);
        if(sl - bid < minStop)
        {
            Print("Stop loss too close: ", sl - bid, " < ", minStop);
            sl = bid + minStop;
        }
        if(bid - tp < minStop)
        {
            Print("Take profit too close: ", bid - tp, " < ", minStop);
            tp = bid - minStop;
        }
        
        // Execute order
        if(m_trade.Sell(lots, symbol, bid, sl, tp, "QuantSupraAI"))
        {
            Print("SELL executed: ", symbol, " ", lots, " lots @ ", bid, " SL:", sl, " TP:", tp);
            return true;
        }
        else
        {
            Print("SELL failed: ", m_trade.ResultRetcode(), " - ", m_trade.ResultRetcodeDescription());
            return false;
        }
    }
    
    //--- Close all positions
    void CloseAllPositions()
    {
        for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
            ulong ticket = PositionGetTicket(i);
            if(ticket > 0)
            {
                if(PositionGetInteger(POSITION_MAGIC) == m_magicNumber)
                {
                    string symbol = PositionGetString(POSITION_SYMBOL);
                    if(m_trade.PositionClose(ticket, m_slippage))
                    {
                        Print("Position closed: ", ticket, " ", symbol);
                    }
                    else
                    {
                        Print("Failed to close position: ", ticket, " - ", m_trade.ResultRetcodeDescription());
                    }
                }
            }
        }
    }
    
    //--- Partial close
    bool PartialClose(ulong ticket, double percentage)
    {
        if(!PositionSelectByTicket(ticket))
        {
            Print("Position not found: ", ticket);
            return false;
        }
        
        double currentVolume = PositionGetDouble(POSITION_VOLUME);
        double closeVolume = NormalizeDouble(currentVolume * percentage, 2);
        
        if(closeVolume < SymbolInfoDouble(PositionGetString(POSITION_SYMBOL), SYMBOL_VOLUME_MIN))
        {
            Print("Close volume too small: ", closeVolume);
            return false;
        }
        
        if(m_trade.PositionClosePartial(ticket, closeVolume, m_slippage))
        {
            Print("Partial close: ", ticket, " ", closeVolume, " lots (", percentage * 100, "%)");
            return true;
        }
        else
        {
            Print("Partial close failed: ", m_trade.ResultRetcodeDescription());
            return false;
        }
    }
    
    //--- Get last trade result
    uint GetLastResult() { return m_trade.ResultRetcode(); }
    string GetLastResultDescription() { return m_trade.ResultRetcodeDescription(); }
    ulong GetLastDeal() { return m_trade.ResultDeal(); }
    ulong GetLastOrder() { return m_trade.ResultOrder(); }
    
    //--- Execute signal from Sidecar
    ulong ExecuteSignal(SignalData &signal)
    {
        if(signal.action == "BUY")
        {
            if(ExecuteBuy(signal.symbol, signal.lots, signal.stopLoss, signal.takeProfit1))
            {
                return m_trade.ResultOrder();
            }
        }
        else if(signal.action == "SELL")
        {
            if(ExecuteSell(signal.symbol, signal.lots, signal.stopLoss, signal.takeProfit1))
            {
                return m_trade.ResultOrder();
            }
        }
        
        return 0;
    }
    
    //--- Monitor existing positions
    void MonitorPositions()
    {
        for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
            ulong ticket = PositionGetTicket(i);
            if(ticket <= 0)
                continue;
            
            if(PositionGetInteger(POSITION_MAGIC) != m_magicNumber)
                continue;
            
            // Check if position needs adjustment (trailing stop, partial close, etc.)
            // This is a placeholder - actual logic would be more complex
            double currentProfit = PositionGetDouble(POSITION_PROFIT);
            if(currentProfit < 0)
            {
                // Could implement trailing stop loss here
            }
        }
    }
};

//+------------------------------------------------------------------+
