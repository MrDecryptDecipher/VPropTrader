# MT5 Expert Advisor

MQL5 Expert Advisor for trade execution and risk management.

## Installation

1. Copy the entire `mt5_ea` folder to your MT5 installation:
   - Windows: `C:\Program Files\MetaTrader 5\MQL5\Experts\QuantSupraAI\`
   - Mac: `~/Library/Application Support/MetaTrader 5/MQL5/Experts/QuantSupraAI/`

2. Open MetaEditor and compile `QuantSupraAI.mq5`

3. Restart MT5 or refresh the Navigator panel

## Configuration

Before attaching the EA to a chart, configure these parameters:

- **SidecarURL**: URL of the Sidecar Service (default: http://localhost:8000)
- **PollInterval**: How often to poll for signals in ms (default: 1500)
- **TradingSymbols**: Comma-separated list of symbols (default: NAS100,XAUUSD,EURUSD)
- **LogOnlyMode**: Set to true for testing without real trades
- **MagicNumber**: Unique identifier for this EA's trades

## Usage

1. Ensure Sidecar Service is running
2. Open a chart for one of your trading symbols
3. Drag `QuantSupraAI` EA onto the chart
4. Enable AutoTrading in MT5
5. Monitor the Experts tab for logs

## Hard-Coded Guardrails

These cannot be changed during runtime:

- Daily loss limit: -$45 (auto-flat)
- Total loss limit: -$100 (disable EA)
- Equity threshold: $900 (disable EA)
- Profit target: $100 (halt entries)
- Daily close: 21:45 UTC
- Friday close: 20:00 UTC
- Daily profit cap: 1.8%

## Trading Sessions

- London: 07:00-10:00 UTC
- New York: 13:30-16:00 UTC

## Files

- `QuantSupraAI.mq5` - Main EA file
- `config.mqh` - Configuration and constants
- `Include/RestClient.mqh` - HTTP client for Sidecar communication
- `Include/RiskManager.mqh` - Risk management and position sizing
- `Include/TradeEngine.mqh` - Trade execution
- `Include/Governors.mqh` - Hard and soft governors
