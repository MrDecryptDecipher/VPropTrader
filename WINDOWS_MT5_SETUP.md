# Windows MT5 Setup Guide

## Overview

This guide shows you how to connect your Windows MT5 installation to the Sidecar service running on Linux (Ubuntu).

**Architecture:**
```
┌─────────────────────────┐
│   Windows Machine       │
│   ┌─────────────────┐   │
│   │   MT5 Terminal  │   │
│   │   + EA          │   │
│   └────────┬────────┘   │
└────────────┼────────────┘
             │ HTTP/REST
             │ (Port 8000)
             ▼
┌─────────────────────────┐
│   Linux Machine         │
│   (Ubuntu/VPS)          │
│   ┌─────────────────┐   │
│   │ Sidecar Service │   │
│   │ + Dashboard     │   │
│   └─────────────────┘   │
└─────────────────────────┘
```

---

## Step 1: Get Your Linux Machine IP Address

On your Linux machine (where Sidecar is running):

```bash
# Get IP address
hostname -I
# Or
ip addr show | grep "inet " | grep -v 127.0.0.1
```

**Example output:** `192.168.1.100` (local network) or `45.67.89.123` (VPS)

**Save this IP address** - you'll need it for the EA configuration.

---

## Step 2: Ensure Sidecar is Running on Linux

On your Linux machine:

```bash
# Check if Sidecar is running
curl http://localhost:8000/health

# If not running, start it:
cd ~/Sandeep/projects/Vproptrader/sidecar
source venv/bin/activate
python -m app.main

# Or if deployed as service:
sudo systemctl status vprop-sidecar
sudo systemctl start vprop-sidecar
```

**Verify it's accessible from network:**
```bash
# On Linux, check what IP it's listening on
netstat -tuln | grep 8000

# Should show: 0.0.0.0:8000 (listening on all interfaces)
```

---

## Step 3: Configure Firewall on Linux

Allow Windows to connect to port 8000:

```bash
# Ubuntu firewall
sudo ufw allow 8000/tcp
sudo ufw status

# Or if using iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save
```

**Test from Windows:**
Open Command Prompt on Windows and test:
```cmd
curl http://YOUR_LINUX_IP:8000/health
```

If you see JSON response, connection works! ✓

---

## Step 4: Copy MT5 EA to Windows

### Option A: Manual Copy

1. On Linux, zip the MT5 EA folder:
   ```bash
   cd ~/Sandeep/projects/Vproptrader
   zip -r mt5_ea.zip mt5_ea/
   ```

2. Transfer to Windows using:
   - **SCP/SFTP** (WinSCP, FileZilla)
   - **Shared folder** (if VM)
   - **USB drive**
   - **Email/Cloud** (Google Drive, Dropbox)

3. Extract on Windows to:
   ```
   C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\XXXXX\MQL5\Experts\
   ```

### Option B: Direct Download (if you have the files accessible)

Just copy these files to MT5 Experts folder:
- `QuantSupraAI.mq5`
- `config.mqh`
- `Include/RestClient.mqh`
- `Include/RiskManager.mqh`
- `Include/TradeEngine.mqh`
- `Include/Governors.mqh`

---

## Step 5: Configure EA for Your Network

On Windows, open `config.mqh` in MetaEditor and update:

```cpp
//+------------------------------------------------------------------+
//| Configuration for Quant Ω Supra AI EA                           |
//+------------------------------------------------------------------+

// ⚠️ IMPORTANT: Change this to your Linux machine IP
input string SidecarURL = "http://192.168.1.100:8000";  // ← YOUR LINUX IP HERE

// Trading symbols (comma-separated)
input string TradingSymbols = "NAS100,XAUUSD,EURUSD";

// Poll interval in milliseconds (1000-2000ms recommended)
input int PollInterval = 1500;

// Log-only mode (true = no real trades, false = live trading)
input bool LogOnlyMode = true;  // ← Start with true for testing

// Risk settings
input double MaxRiskPerTrade = 0.01;  // 1% per trade
input double MaxDailyLoss = 45.0;     // $45 daily loss limit
input double ProfitTarget = 100.0;    // $100 profit target

// VProp account settings
input double StartingEquity = 1000.0;
input double MinEquity = 900.0;       // Stop trading below this

//+------------------------------------------------------------------+
```

**Key changes:**
1. Replace `192.168.1.100` with **your actual Linux IP**
2. Keep `LogOnlyMode = true` for initial testing
3. Adjust symbols if needed

---

## Step 6: Compile EA in MetaEditor

1. Open **MetaEditor** in MT5 (F4 or Tools → MetaQuotes Language Editor)
2. Open `QuantSupraAI.mq5`
3. Click **Compile** button (F7) or Compile → Compile
4. Check for errors in the **Errors** tab
5. Should see: `0 error(s), 0 warning(s)`

**If you see errors:**
- Make sure all Include files are in the `Include/` folder
- Check that `config.mqh` is in the same directory
- Verify syntax is correct

---

## Step 7: Attach EA to Chart

1. Open MT5 Terminal
2. Open a chart for one of your symbols (e.g., NAS100)
3. In **Navigator** panel (Ctrl+N), expand **Expert Advisors**
4. Find **QuantSupraAI**
5. **Drag and drop** onto the chart

**EA Settings Dialog:**
- Check **Allow live trading** (even in log-only mode)
- Check **Allow DLL imports** (if needed)
- Click **OK**

You should see a **smiley face** icon in the top-right corner of the chart.

---

## Step 8: Verify Connection

### Check MT5 Experts Log

1. In MT5, open **Toolbox** panel (Ctrl+T)
2. Go to **Experts** tab
3. Look for initialization messages:

```
=== Quant Ω Supra AI Expert Advisor ===
Version: 1.00
Sidecar URL: http://192.168.1.100:8000
Poll Interval: 1500 ms
Log-Only Mode: YES
Symbols: NAS100,XAUUSD,EURUSD
========================================
✓ REST Client initialized
✓ Risk Manager initialized
✓ Trade Engine initialized
✓ Governors initialized
Testing connection to Sidecar Service...
✓ Sidecar connection successful
========================================
EA Initialization Complete - Ready to Trade
========================================
```

**If you see errors:**
- `Connection failed` → Check IP address and firewall
- `Timeout` → Verify Sidecar is running
- `404 Not Found` → Check Sidecar URL is correct

### Test from Windows Command Prompt

```cmd
curl http://YOUR_LINUX_IP:8000/health
curl http://YOUR_LINUX_IP:8000/api/signals?equity=1000
```

Should return JSON responses.

---

## Step 9: Monitor Operation

### On Windows (MT5)

Watch the **Experts** tab for:
- Signal requests every 1-2 seconds
- Received signals (if any)
- Trade decisions (in log-only mode)

### On Linux (Sidecar)

```bash
# Watch Sidecar logs
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log

# Or if running as service
sudo journalctl -u vprop-sidecar -f
```

Look for:
- `GET /api/signals` requests from EA
- Signal generation
- No errors

### Dashboard (Optional)

If dashboard is running, open in browser:
- Local: `http://YOUR_LINUX_IP:3000`
- Or your Vercel URL if deployed

---

## Step 10: Test in Log-Only Mode

**What happens in log-only mode:**
- ✓ EA connects to Sidecar
- ✓ Receives trading signals
- ✓ Logs all decisions
- ✗ Does NOT execute trades

**Monitor for 1 hour:**
1. Watch MT5 Experts log
2. Check Sidecar logs
3. Verify signals are generated
4. Confirm no errors

**Example log output:**
```
Processing signal: NAS100 BUY Q*=8.5 Lots=0.05
LOG-ONLY MODE: Would execute BUY 0.05 lots of NAS100
✓ Execution reported to Sidecar
```

---

## Step 11: Enable Live Trading (When Ready)

**⚠️ ONLY after successful log-only testing!**

1. Open `config.mqh` in MetaEditor
2. Change: `input bool LogOnlyMode = false;`
3. Recompile (F7)
4. Remove EA from chart
5. Attach EA again
6. **Enable AutoTrading** in MT5 (click the AutoTrading button in toolbar)

**First trade monitoring:**
- Watch closely for first execution
- Verify stop loss and take profit are set
- Check PnL tracking
- Monitor compliance panel

---

## Troubleshooting

### EA Can't Connect to Sidecar

**Problem:** `Connection failed` or `Timeout`

**Solutions:**
1. **Verify IP address:**
   ```bash
   # On Linux
   hostname -I
   ```

2. **Check Sidecar is running:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Test from Windows:**
   ```cmd
   ping YOUR_LINUX_IP
   curl http://YOUR_LINUX_IP:8000/health
   ```

4. **Check firewall:**
   ```bash
   # On Linux
   sudo ufw status
   sudo ufw allow 8000/tcp
   ```

5. **Verify Sidecar is listening on all interfaces:**
   ```bash
   # Should show 0.0.0.0:8000, not 127.0.0.1:8000
   netstat -tuln | grep 8000
   ```

   If showing 127.0.0.1, update Sidecar config:
   ```python
   # In sidecar/app/core/config.py
   host: str = "0.0.0.0"  # Not "127.0.0.1"
   ```

### EA Compiles with Errors

**Problem:** Compilation errors in MetaEditor

**Solutions:**
1. Check all Include files are present
2. Verify `config.mqh` is in same directory
3. Make sure you're using MT5 (not MT4)
4. Check MQL5 syntax is correct

### No Signals Generated

**Problem:** EA connects but no signals

**Possible reasons:**
1. **Outside trading hours** (London 07:00-10:00 UTC or NY 13:30-16:00 UTC)
2. **No high-quality setups** (system is selective, >90% skip rate)
3. **Symbols not available** in your MT5
4. **Market closed**

**Check:**
```bash
# On Linux, test signals endpoint
curl http://localhost:8000/api/signals?equity=1000
```

### High Latency

**Problem:** Slow response times

**Solutions:**
1. **Use local network** if possible (not internet)
2. **Reduce poll interval** in config.mqh (but not below 1000ms)
3. **Check network speed** between Windows and Linux
4. **Upgrade VPS** if using cloud server

---

## Network Configurations

### Same Local Network (Recommended)

**Setup:**
- Windows PC: `192.168.1.50`
- Linux PC: `192.168.1.100`
- Both on same router/network

**EA Config:**
```cpp
input string SidecarURL = "http://192.168.1.100:8000";
```

**Advantages:**
- ✓ Low latency (<10ms)
- ✓ No internet required
- ✓ More secure

### VPS (Cloud Server)

**Setup:**
- Windows PC: Home network
- Linux VPS: `45.67.89.123` (public IP)

**EA Config:**
```cpp
input string SidecarURL = "http://45.67.89.123:8000";
```

**Advantages:**
- ✓ Access from anywhere
- ✓ 24/7 uptime
- ✓ Professional setup

**Security:**
- Use HTTPS if possible
- Configure firewall to allow only your IP
- Use VPN for extra security

### Windows Subsystem for Linux (WSL)

**Setup:**
- Both on same Windows machine
- WSL IP: Check with `wsl hostname -I`

**EA Config:**
```cpp
input string SidecarURL = "http://172.x.x.x:8000";  // WSL IP
```

**Note:** WSL IP can change on restart, use `localhost` if possible.

---

## Quick Reference

### Essential Commands

**Linux (Sidecar):**
```bash
# Start Sidecar
cd ~/Sandeep/projects/Vproptrader/sidecar
source venv/bin/activate
python -m app.main

# Check status
curl http://localhost:8000/health

# View logs
tail -f logs/app.log

# Get IP
hostname -I
```

**Windows (MT5):**
```cmd
# Test connection
curl http://YOUR_LINUX_IP:8000/health

# Ping Linux
ping YOUR_LINUX_IP
```

### File Locations

**Linux:**
- Sidecar: `~/Sandeep/projects/Vproptrader/sidecar/`
- Logs: `~/Sandeep/projects/Vproptrader/sidecar/logs/`
- Config: `~/Sandeep/projects/Vproptrader/sidecar/.env`

**Windows:**
- MT5 Data: `C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\`
- Experts: `...\MQL5\Experts\`
- Logs: Check MT5 Experts tab

---

## Next Steps

1. ✅ Get Linux IP address
2. ✅ Start Sidecar on Linux
3. ✅ Configure firewall
4. ✅ Copy EA to Windows MT5
5. ✅ Update config.mqh with Linux IP
6. ✅ Compile EA
7. ✅ Attach to chart
8. ✅ Verify connection
9. ✅ Test in log-only mode (1 hour minimum)
10. 🎯 Enable live trading (when ready)

---

## Support

**Connection issues?**
- Check IP address
- Verify firewall
- Test with curl
- Check Sidecar logs

**EA issues?**
- Check MT5 Experts log
- Verify compilation
- Check config.mqh
- Ensure AutoTrading enabled

**No signals?**
- Check trading hours
- Verify symbols
- Test signals endpoint
- Review Sidecar logs

---

*Last Updated: 2025-10-25*
*Version: 1.0.0*
