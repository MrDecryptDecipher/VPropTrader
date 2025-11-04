//+------------------------------------------------------------------+
//|                                                QuantSupraAI.mq5 |
//|                        Quant Ω Supra AI Expert Advisor           |
//|                        Memory-Adaptive Prop Trading System       |
//+------------------------------------------------------------------+
#property copyright "Quant Ω Supra AI"
#property link      ""
#property version   "1.00"
#property strict

#include "config.mqh"
#include "Include/Structures.mqh"
#include "Include/RestClient.mqh"
#include "Include/RiskManager.mqh"
#include "Include/TradeEngine.mqh"
#include "Include/Governors.mqh"

//--- Global variables
datetime g_lastPollTime = 0;
datetime g_lastTradeTime = 0;
bool g_eaEnabled = true;
double g_dailyPnL = 0.0;
double g_totalPnL = 0.0;
double g_startingEquity = 0.0;
double g_peakEquity = 0.0;
int g_tradesToday = 0;
datetime g_sessionStartTime = 0;

//--- Module instances (initialized in OnInit)
CRestClient *restClient;
CRiskManager *riskManager;
CTradeEngine *tradeEngine;
CGovernors *governors;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== Quant Ω Supra AI Expert Advisor ===");
    Print("Version: 1.00");
    Print("Sidecar URL: ", SidecarURL);
    Print("Poll Interval: ", PollInterval, " ms");
    Print("Log-Only Mode: ", LogOnlyMode ? "YES" : "NO");
    Print("Symbols: ", TradingSymbols);
    Print("========================================");
    
    // Initialize starting equity
    g_startingEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    g_peakEquity = g_startingEquity;
    g_sessionStartTime = TimeCurrent();
    
    // Initialize REST client
    restClient = new CRestClient(SidecarURL, 5000);
    if(restClient == NULL)
    {
        Print("ERROR: Failed to create REST client");
        return(INIT_FAILED);
    }
    Print("✓ REST Client initialized");
    
    // Initialize risk manager
    riskManager = new CRiskManager();
    if(riskManager == NULL)
    {
        Print("ERROR: Failed to create Risk Manager");
        return(INIT_FAILED);
    }
    Print("✓ Risk Manager initialized");
    
    // Initialize trade engine
    tradeEngine = new CTradeEngine(MagicNumber, LogOnlyMode);
    if(tradeEngine == NULL)
    {
        Print("ERROR: Failed to create Trade Engine");
        return(INIT_FAILED);
    }
    Print("✓ Trade Engine initialized");
    
    // Initialize governors
    governors = new CGovernors();
    if(governors == NULL)
    {
        Print("ERROR: Failed to create Governors");
        return(INIT_FAILED);
    }
    Print("✓ Governors initialized");
    
    // Verify connection to Sidecar
    Print("Testing connection to Sidecar Service...");
    string response;
    if(restClient.Get("/health", response))
    {
        Print("✓ Sidecar connection successful");
        Print("Response: ", response);
    }
    else
    {
        Print("⚠ WARNING: Could not connect to Sidecar - will retry on demand");
    }
    
    // Set up timer for regular polling (every 1.5 seconds)
    EventSetTimer(PollInterval / 1000);  // Convert ms to seconds
    Print("✓ Timer set to ", PollInterval / 1000, " seconds");
    
    Print("========================================");
    Print("EA Initialization Complete - Ready to Trade");
    Print("========================================");
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Kill timer
    EventKillTimer();
    
    Print("========================================");
    Print("EA Shutting Down - Reason: ", reason);
    Print("========================================");
    
    // Print final statistics
    double finalEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    double totalPnL = finalEquity - g_startingEquity;
    double maxDD = ((g_peakEquity - finalEquity) / g_peakEquity) * 100;
    
    Print("Final Statistics:");
    Print("  Starting Equity: $", g_startingEquity);
    Print("  Final Equity: $", finalEquity);
    Print("  Total PnL: $", totalPnL);
    Print("  Max Drawdown: ", maxDD, "%");
    Print("  Trades Today: ", g_tradesToday);
    
    // Close all positions on shutdown
    if(PositionsTotal() > 0 && tradeEngine != NULL)
    {
        Print("Closing all open positions...");
        tradeEngine.CloseAllPositions();
    }
    
    // Send final status to Sidecar
    if(restClient != NULL)
    {
        string jsonData = StringFormat(
            "{\"event\":\"ea_shutdown\",\"reason\":%d,\"equity\":%.2f,\"pnl\":%.2f,\"trades\":%d}",
            reason, finalEquity, totalPnL, g_tradesToday
        );
        string response;
        restClient.Post("/api/events", jsonData, response);
    }
    
    // Cleanup
    if(restClient != NULL) delete restClient;
    if(riskManager != NULL) delete riskManager;
    if(tradeEngine != NULL) delete tradeEngine;
    if(governors != NULL) delete governors;
    
    Print("========================================");
    Print("EA Deinitialization Complete");
    Print("========================================");
}

//+------------------------------------------------------------------+
//| Expert timer function - called every PollInterval seconds        |
//+------------------------------------------------------------------+
void OnTimer()
{
    // Check if EA is enabled
    if(!g_eaEnabled)
        return;
    
    datetime currentTime = TimeCurrent();
    g_lastPollTime = currentTime;
    
    // Update account info
    UpdateAccountInfo();
    
    // Update peak equity for drawdown calculation
    double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    if(currentEquity > g_peakEquity)
        g_peakEquity = currentEquity;
    
    // Check hard governors first (immutable)
    if(!governors.CheckHardGovernors())
    {
        Print("HARD GOVERNOR TRIGGERED - EA DISABLED");
        g_eaEnabled = false;
        tradeEngine.CloseAllPositions();
        return;
    }
    
    // Check time-based governors
    if(governors.ShouldCloseAllPositions())
    {
        Print("Time-based close triggered (21:45 UTC or Friday 20:00)");
        tradeEngine.CloseAllPositions();
        return;
    }
    
    // Check soft governors (adaptive)
    if(!governors.CheckSoftGovernors())
    {
        // Soft governor pause - don't disable EA, just skip this cycle
        return;
    }
    
    // Check trading schedule (London/NY sessions only)
    if(!governors.IsInTradingSession())
    {
        return;  // Outside trading hours
    }
    
    // Monitor existing positions
    tradeEngine.MonitorPositions();
    
    // Check if we can take new positions
    if(!riskManager.CanTakeNewPosition())
    {
        return;  // Risk limits reached
    }
    
    // Poll Sidecar for signals
    PollSignals();
    
    // Status logging
    if(VerboseLogging)
    {
        static datetime lastStatusTime = 0;
        if(currentTime - lastStatusTime >= 60)
        {
            lastStatusTime = currentTime;
            Print("Status - Enabled: ", g_eaEnabled, 
                  " | Daily PnL: $", DoubleToString(g_dailyPnL, 2),
                  " | Total PnL: $", DoubleToString(g_totalPnL, 2),
                  " | Trades Today: ", g_tradesToday);
        }
    }
}

//+------------------------------------------------------------------+
//| Expert tick function - for position monitoring                   |
//+------------------------------------------------------------------+
void OnTick()
{
    // Just monitor existing positions on each tick
    if(g_eaEnabled && tradeEngine != NULL)
    {
        tradeEngine.MonitorPositions();
    }
}

//+------------------------------------------------------------------+
//| Poll Sidecar for trading signals                                 |
//+------------------------------------------------------------------+
void PollSignals()
{
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    string endpoint = StringFormat("/api/signals?equity=%.2f", equity);
    string response;
    
    if(!restClient.Get(endpoint, response))
    {
        Print("Failed to get signals from Sidecar");
        return;
    }
    
    // Parse signals response
    ProcessSignals(response);
}

//+------------------------------------------------------------------+
//| Process signals from Sidecar                                     |
//+------------------------------------------------------------------+
void ProcessSignals(string jsonResponse)
{
    // Parse JSON response
    // Expected format: {"signals": [...], "timestamp": "...", "count": N}
    
    // Extract signals array
    int signalsStart = StringFind(jsonResponse, "\"signals\":[");
    if(signalsStart < 0)
    {
        Print("No signals in response");
        return;
    }
    
    // Count signals
    int signalCount = 0;
    int pos = signalsStart;
    while(pos >= 0 && pos < StringLen(jsonResponse))
    {
        pos = StringFind(jsonResponse, "\"symbol\":", pos + 1);
        if(pos > 0)
            signalCount++;
        else
            break;
    }
    
    if(signalCount == 0)
    {
        Print("No trading signals available");
        return;
    }
    
    Print("Received ", signalCount, " signal(s) from Sidecar");
    
    // Process each signal
    pos = signalsStart;
    for(int i = 0; i < signalCount; i++)
    {
        // Extract signal data
        SignalData signal;
        if(ExtractSignal(jsonResponse, pos, signal))
        {
            ProcessSingleSignal(signal);
        }
        
        // Move to next signal
        pos = StringFind(jsonResponse, "\"symbol\":", pos + 1);
    }
}

//+------------------------------------------------------------------+
//| Extract signal data from JSON                                    |
//+------------------------------------------------------------------+
bool ExtractSignal(string json, int startPos, SignalData &signal)
{
    // Extract symbol
    signal.symbol = ExtractStringValue(json, "symbol", startPos);
    
    // Extract action
    signal.action = ExtractStringValue(json, "action", startPos);
    
    // Extract numeric values
    signal.confidence = ExtractDoubleValue(json, "confidence", startPos);
    signal.qStar = ExtractDoubleValue(json, "q_star", startPos);
    signal.es95 = ExtractDoubleValue(json, "es95", startPos);
    signal.stopLoss = ExtractDoubleValue(json, "stop_loss", startPos);
    signal.takeProfit1 = ExtractDoubleValue(json, "take_profit_1", startPos);
    signal.takeProfit2 = ExtractDoubleValue(json, "take_profit_2", startPos);
    signal.lots = ExtractDoubleValue(json, "lots", startPos);
    
    // Extract alpha_id and regime
    signal.alphaId = ExtractStringValue(json, "alpha_id", startPos);
    signal.regime = ExtractStringValue(json, "regime", startPos);
    
    return (signal.symbol != "" && signal.action != "");
}

//+------------------------------------------------------------------+
//| Process a single trading signal                                  |
//+------------------------------------------------------------------+
void ProcessSingleSignal(SignalData &signal)
{
    Print("Processing signal: ", signal.symbol, " ", signal.action, 
          " Q*=", signal.qStar, " Lots=", signal.lots);
    
    // Skip if action is HOLD
    if(signal.action == "HOLD")
        return;
    
    // Check if symbol is in our trading list
    if(!IsSymbolAllowed(signal.symbol))
    {
        Print("Symbol ", signal.symbol, " not in allowed list");
        return;
    }
    
    // Validate signal
    if(!riskManager.ValidateSignal(signal))
    {
        Print("Signal validation failed for ", signal.symbol);
        return;
    }
    
    // Check execution quality filters
    double spread = SymbolInfoDouble(signal.symbol, SYMBOL_ASK) - 
                    SymbolInfoDouble(signal.symbol, SYMBOL_BID);
    
    if(!riskManager.CheckExecutionQuality(signal.symbol, spread))
    {
        Print("Execution quality check failed for ", signal.symbol);
        return;
    }
    
    // Log-only mode check
    if(LogOnlyMode)
    {
        Print("LOG-ONLY MODE: Would execute ", signal.action, " ", 
              signal.lots, " lots of ", signal.symbol);
        return;
    }
    
    // Execute trade
    ulong ticket = tradeEngine.ExecuteSignal(signal);
    
    if(ticket > 0)
    {
        Print("✓ Trade executed: Ticket #", ticket);
        g_tradesToday++;
        g_lastTradeTime = TimeCurrent();
        
        // Report execution to Sidecar
        ReportExecution(ticket, signal);
    }
    else
    {
        Print("✗ Trade execution failed for ", signal.symbol);
    }
}

//+------------------------------------------------------------------+
//| Report trade execution to Sidecar                                |
//+------------------------------------------------------------------+
void ReportExecution(ulong ticket, SignalData &signal)
{
    if(!PositionSelectByTicket(ticket))
        return;
    
    double entryPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double currentPrice = PositionGetDouble(POSITION_PRICE_CURRENT);
    datetime openTime = (datetime)PositionGetInteger(POSITION_TIME);
    
    // Calculate slippage
    double expectedPrice = (signal.action == "BUY") ? 
        SymbolInfoDouble(signal.symbol, SYMBOL_ASK) :
        SymbolInfoDouble(signal.symbol, SYMBOL_BID);
    double slippage = MathAbs(entryPrice - expectedPrice);
    
    // Calculate latency
    long latencyMs = (TimeCurrent() - g_lastPollTime) * 1000;
    
    // Build JSON
    string jsonData = StringFormat(
        "{\"trade_id\":\"%llu\",\"symbol\":\"%s\",\"action\":\"%s\","
        "\"entry_price\":%.5f,\"lots\":%.2f,\"stop_loss\":%.5f,"
        "\"take_profit\":%.5f,\"timestamp\":\"%s\",\"latency_ms\":%d,"
        "\"spread\":%.5f,\"slippage\":%.5f,\"alpha_id\":\"%s\","
        "\"regime\":\"%s\",\"q_star\":%.2f}",
        ticket, signal.symbol, signal.action, entryPrice, signal.lots,
        signal.stopLoss, signal.takeProfit1, TimeToString(openTime),
        latencyMs, 
        SymbolInfoInteger(signal.symbol, SYMBOL_SPREAD) * SymbolInfoDouble(signal.symbol, SYMBOL_POINT),
        slippage, signal.alphaId, signal.regime, signal.qStar
    );
    
    string response;
    if(restClient.Post("/api/executions", jsonData, response))
    {
        Print("✓ Execution reported to Sidecar");
    }
    else
    {
        Print("⚠ Failed to report execution to Sidecar");
    }
}

//+------------------------------------------------------------------+
//| Update account information                                       |
//+------------------------------------------------------------------+
void UpdateAccountInfo()
{
    double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    
    // Calculate daily PnL
    // Reset at start of new day
    datetime currentDate = TimeCurrent() - (TimeCurrent() % 86400);
    datetime sessionDate = g_sessionStartTime - (g_sessionStartTime % 86400);
    
    if(currentDate != sessionDate)
    {
        // New day - reset counters
        g_sessionStartTime = TimeCurrent();
        g_startingEquity = currentEquity;
        g_tradesToday = 0;
        g_dailyPnL = 0.0;
        Print("New trading day started - Equity: $", currentEquity);
    }
    else
    {
        g_dailyPnL = currentEquity - g_startingEquity;
    }
    
    g_totalPnL = currentEquity - g_startingEquity;
}

//+------------------------------------------------------------------+
//| Check if symbol is in allowed trading list                       |
//+------------------------------------------------------------------+
bool IsSymbolAllowed(string symbol)
{
    // Parse TradingSymbols (comma-separated)
    string symbols[];
    int count = StringSplit(TradingSymbols, ',', symbols);
    
    for(int i = 0; i < count; i++)
    {
        string trimmed = symbols[i];
        StringTrimLeft(trimmed);
        StringTrimRight(trimmed);
        
        if(trimmed == symbol)
            return true;
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Extract string value from JSON                                   |
//+------------------------------------------------------------------+
string ExtractStringValue(string json, string key, int startPos)
{
    string searchKey = "\"" + key + "\":\"";
    int keyPos = StringFind(json, searchKey, startPos);
    
    if(keyPos < 0)
        return "";
    
    int valueStart = keyPos + StringLen(searchKey);
    int valueEnd = StringFind(json, "\"", valueStart);
    
    if(valueEnd < 0)
        return "";
    
    return StringSubstr(json, valueStart, valueEnd - valueStart);
}

//+------------------------------------------------------------------+
//| Extract double value from JSON                                   |
//+------------------------------------------------------------------+
double ExtractDoubleValue(string json, string key, int startPos)
{
    string searchKey = "\"" + key + "\":";
    int keyPos = StringFind(json, searchKey, startPos);
    
    if(keyPos < 0)
        return 0.0;
    
    int valueStart = keyPos + StringLen(searchKey);
    
    // Find end of number (comma, brace, or bracket)
    int valueEnd = valueStart;
    while(valueEnd < StringLen(json))
    {
        ushort ch = StringGetCharacter(json, valueEnd);
        if(ch == ',' || ch == '}' || ch == ']' || ch == ' ')
            break;
        valueEnd++;
    }
    
    string valueStr = StringSubstr(json, valueStart, valueEnd - valueStart);
    return StringToDouble(valueStr);
}

