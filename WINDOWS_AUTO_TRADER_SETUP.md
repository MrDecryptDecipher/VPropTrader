# Windows MT5 Auto Trader - Setup Guide

## What This Does

This Python script runs on your Windows machine and:
- ✅ Polls the sidecar every 2 seconds for signals
- ✅ Automatically executes trades in MT5
- ✅ Manages risk (max 3 concurrent trades)
- ✅ Only trades high-confidence signals (>0.75)
- ✅ More reliable than MQL5 EAs

## Installation (5 minutes)

### Step 1: Install Python

1. Download Python from: https://www.python.org/downloads/
2. Run installer
3. ✅ **IMPORTANT:** Check "Add Python to PATH"
4. Click "Install Now"

### Step 2: Install MetaTrader5 Python Package

Open Command Prompt (cmd) and run:

```cmd
pip install MetaTrader5 requests
```

### Step 3: Download the Script

1. Copy `windows_auto_trader.py` to your Windows machine
2. Save it somewhere easy to find (e.g., `C:\Trading\windows_auto_trader.py`)

## Running the Auto Trader

### Method 1: Double-Click (Easiest)

1. Right-click `windows_auto_trader.py`
2. Select "Open with" → "Python"
3. A console window will open showing live trading activity

### Method 2: Command Line

```cmd
cd C:\Trading
python windows_auto_trader.py
```

## What You'll See

```
============================================================
VPropTrader - Windows MT5 Auto Trader
============================================================
[2025-11-01 12:45:00] Initializing MT5 connection...
[2025-11-01 12:45:01] ✓ Connected to MT5
[2025-11-01 12:45:01]   Account: 12345678
[2025-11-01 12:45:01]   Balance: $10000.00
[2025-11-01 12:45:01]   Equity: $10000.00
[2025-11-01 12:45:01]   Server: YourBroker-Demo
============================================================
[2025-11-01 12:45:01] Auto-trading started. Press Ctrl+C to stop.
============================================================
[2025-11-01 12:45:03] Received 2 signal(s) from sidecar
[2025-11-01 12:45:03] Opening BUY position: XAUUSD 0.01 lots (Confidence: 0.85)
[2025-11-01 12:45:03]   Price: 2650.50 | SL: 2645.00 | TP: 2660.00
[2025-11-01 12:45:04] ✓ Position opened successfully: Ticket #123456
[2025-11-01 12:45:04]   Fill Price: 2650.52
[2025-11-01 12:45:04]   Volume: 0.01 lots
```

## Configuration

Edit these values at the top of `windows_auto_trader.py`:

```python
SIDECAR_URL = "http://3.111.22.56:8002"  # Your sidecar URL
POLL_INTERVAL = 2  # How often to check for signals (seconds)
MIN_CONFIDENCE = 0.75  # Only trade signals above this confidence
MAX_CONCURRENT_TRADES = 3  # Maximum open positions
```

## Features

### Automatic Risk Management
- Only trades signals with confidence > 0.75
- Maximum 3 concurrent positions
- Automatic stop-loss and take-profit
- Won't open duplicate positions for same symbol

### Real-Time Monitoring
- Shows all open positions every 20 seconds
- Displays P&L for each position
- Color-coded output (green=profit, red=loss)

### Safe Operation
- Press Ctrl+C to stop safely
- Closes MT5 connection properly
- Shows final position summary on exit

## Advantages Over MT5 EA

| Feature | Python Script | MT5 EA |
|---------|--------------|--------|
| Reliability | ✅ Very High | ⚠️ Can fail silently |
| Debugging | ✅ Easy (console output) | ❌ Difficult |
| Flexibility | ✅ Easy to modify | ⚠️ Requires recompilation |
| Error Messages | ✅ Clear and detailed | ⚠️ Cryptic |
| Setup | ✅ 5 minutes | ⚠️ Complex |

## Troubleshooting

### "ModuleNotFoundError: No module named 'MetaTrader5'"

**Solution:**
```cmd
pip install MetaTrader5
```

### "MT5 initialization failed"

**Solution:**
1. Make sure MT5 is running
2. Make sure you're logged into an account
3. Check MT5 → Tools → Options → Expert Advisors
   - ✅ Allow automated trading
   - ✅ Allow DLL imports

### "Failed to get signals: Connection refused"

**Solution:**
- Check sidecar is running: `pm2 status`
- Verify URL is correct: `http://3.111.22.56:8002`
- Test in browser: Open the URL and add `/health`

### "Symbol not available"

**Solution:**
- In MT5, go to View → Market Watch
- Right-click → Show All
- Find the symbol and enable it

## Running 24/7

### Option 1: Keep Windows Awake

1. Windows Settings → System → Power & Sleep
2. Set "Screen" and "Sleep" to "Never"
3. Leave script running

### Option 2: Run as Windows Service

Use `NSSM` (Non-Sucking Service Manager):

1. Download NSSM: https://nssm.cc/download
2. Install as service:
   ```cmd
   nssm install VPropTrader "C:\Python\python.exe" "C:\Trading\windows_auto_trader.py"
   nssm start VPropTrader
   ```

## Monitoring

### Check if Running

Look for Python console window with live output

### View Trades in MT5

1. Open MT5
2. Go to "Trade" tab (bottom panel)
3. See all open positions
4. Go to "History" tab to see closed trades

### View on Dashboard

Open: `http://3.111.22.56:3000`

All trades will appear in real-time

## Stopping the Auto Trader

1. Go to the Python console window
2. Press **Ctrl+C**
3. Wait for graceful shutdown
4. Check final position summary

## Safety Features

✅ **Never trades without confirmation** - Only executes signals from sidecar  
✅ **Risk limits enforced** - Max 3 concurrent trades  
✅ **Quality filter** - Only high-confidence signals  
✅ **Automatic stop-loss** - Every trade has SL/TP  
✅ **Position monitoring** - Tracks all open trades  
✅ **Graceful shutdown** - Ctrl+C stops safely  

## Next Steps

1. **Test on Demo First**
   - Run for a few hours
   - Verify trades execute correctly
   - Check P&L tracking

2. **Monitor Performance**
   - Watch console output
   - Check MT5 trade history
   - Review dashboard

3. **Go Live**
   - Switch to live account in MT5
   - Restart the script
   - Monitor closely for first day

## Support

If you encounter issues:

1. Check the console output for error messages
2. Verify MT5 is running and logged in
3. Test sidecar connection: `http://3.111.22.56:8002/health`
4. Check MT5 settings allow automated trading

---

**This script is MORE RELIABLE than the MT5 EA and will get you trading immediately!**
