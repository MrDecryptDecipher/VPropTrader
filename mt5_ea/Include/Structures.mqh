//+------------------------------------------------------------------+
//|                                                   Structures.mqh |
//|                        Common Data Structures                    |
//+------------------------------------------------------------------+
#property copyright "Quant Ω Supra AI"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| Signal data structure                                            |
//+------------------------------------------------------------------+
struct SignalData
{
    string symbol;          // Trading symbol (e.g., "EURUSD")
    string action;          // Trade action: "BUY", "SELL", or "HOLD"
    double confidence;      // Signal confidence (0.0 - 1.0)
    double qStar;          // Q* value from ML model
    double es95;           // Expected Shortfall at 95%
    double stopLoss;       // Stop loss price
    double takeProfit1;    // First take profit target
    double takeProfit2;    // Second take profit target
    double lots;           // Position size in lots
    string alphaId;        // Alpha strategy identifier
    string regime;         // Market regime classification
};

//+------------------------------------------------------------------+
