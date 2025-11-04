//+------------------------------------------------------------------+
//|                                                       config.mqh |
//|                        Quant Ω Supra AI Configuration            |
//+------------------------------------------------------------------+
#property copyright "Quant Ω Supra AI"
#property version   "1.00"
#property strict

//--- Sidecar API Configuration
input string SidecarURL = "http://3.111.22.56:8002";  // Sidecar Service URL (Your Ubuntu IP via nginx)
input int    PollInterval = 1500;                    // Poll interval in ms (1-2s)
input int    RequestTimeout = 5000;                  // HTTP request timeout in ms

//--- Trading Configuration
input string TradingSymbols = "US100.e,XAUUSD,EURUSD"; // Symbols to trade
input int    MagicNumber = 20251025;                  // Magic number for EA
input bool   LogOnlyMode = true;                     // Log-only mode (START WITH TRUE FOR TESTING!)

//--- Risk Parameters (Hard-coded Guardrails)
#define DAILY_LOSS_LIMIT      -45.0    // Auto-flat at -$45 PnL
#define TOTAL_LOSS_LIMIT      -100.0   // Disable EA at -$100 total loss
#define EQUITY_DISABLE        900.0    // Disable EA below $900 equity
#define PROFIT_TARGET         100.0    // Halt entries at $100 profit
#define DAILY_PROFIT_CAP_PCT  1.8      // Daily profit cap %
#define MAX_OPEN_POSITIONS    3        // Maximum concurrent positions

//--- Time-based Guardrails
#define DAILY_CLOSE_HOUR      21       // Close all positions at 21:45 UTC
#define DAILY_CLOSE_MINUTE    45
#define FRIDAY_CLOSE_HOUR     20       // Close all positions at 20:00 UTC Friday
#define FRIDAY_CLOSE_MINUTE   0

//--- Trading Sessions (UTC)
#define LONDON_START_HOUR     7
#define LONDON_END_HOUR       10
#define NY_START_HOUR         13
#define NY_START_MINUTE       30
#define NY_END_HOUR           16

//--- Execution Quality Filters
input double MaxSpreadPercentile = 60.0;  // Max spread percentile
input int    MaxLatencyMs = 400;          // Max latency in ms
input double MaxSlippagePoints = 5.0;     // Max slippage in points

//--- Soft Governors
input int    CooldownAfterLossSec = 300;  // Cool-down after loss (5 min)
input double VolatilityCap = 0.02;        // Volatility cap (2%)
input bool   EnableProfitLock = true;     // Enable profit lock

//--- Logging
input bool   VerboseLogging = true;       // Enable verbose logging
input string LogPrefix = "QuantSupraAI";  // Log prefix

//+------------------------------------------------------------------+
