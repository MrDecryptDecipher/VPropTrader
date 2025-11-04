# My Personal Setup Guide

## Your Configuration

**Ubuntu Server IP:** `3.111.22.56`
**Sidecar URL:** `http://3.111.22.56:8000`

---

## 🚀 Quick Start (30 Minutes)

### Step 1: Start Sidecar on Ubuntu (10 minutes)

You're already on the Ubuntu server, so let's start:

```bash
# 1. Navigate to project
cd ~/Sandeep/projects/Vproptrader/sidecar

# 2. Create virtual environment (first time only)
python3.11 -m venv venv

# 3. Activate it
source venv/bin/activate

# 4. Install dependencies (first time only)
pip install -r requirements.txt

# 5. Setup environment file
cp .env.example .env

# 6. Edit with your credentials
nano .env
```

**Edit .env file with your MT5 credentials:**
```bash
# MT5 Connection
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server

# FRED API (for macro data)
FRED_API_KEY=your_fred_api_key

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Database
DATABASE_PATH=./data/trades.db

# Server
HOST=0.0.0.0  # Important: Listen on all interfaces
PORT=8000
```

**Save and exit** (Ctrl+X, Y, Enter)

```bash
# 7. Start Sidecar
python -m app.main
```

**Expected output:**
```
=== Starting Quant Ω Supra AI Sidecar Service ===
Environment: production
Host: 0.0.0.0:8000
✓ MT5 connected successfully
✓ FRED API connected
✓ Calendar: 15 high-impact events loaded
✓ Sidecar Service started successfully
```

---

### Step 2: Configure Firewall (2 minutes)

**Open another terminal** (keep Sidecar running) and run:

```bash
# Allow port 8000 from anywhere
sudo ufw allow 8000/tcp

# Check status
sudo ufw status

# Should show:
# 8000/tcp    ALLOW    Anywhere
```

---

### Step 3: Test from Ubuntu (1 minute)

```bash
# Test locally
curl http://localhost:8000/health

# Test from public IP
curl http://3.111.22.56:8000/health
```

**Expected:** JSON response with system health ✓

---

### Step 4: Configure MT5 EA on Windows (15 minutes)

**On your Windows machine with MT5:**

#### A. Test Connection First

Open Command Prompt (cmd) and run:
```cmd
curl http://3.111.22.56:8000/health
```

**If you see JSON response, connection works!** ✓

**If connection fails:**
- Check Ubuntu firewall: `sudo ufw status`
- Verify Sidecar is running
- Check if port 8000 is open on your cloud provider (AWS Security Group)

#### B. Copy EA Files to Windows

**Transfer these files from Ubuntu to Windows:**

**Method 1: Download as ZIP**
```bash
# On Ubuntu, create a zip file
cd ~/Sandeep/projects/Vproptrader
zip -r mt5_ea.zip mt5_ea/

# Download using SCP or your preferred method
# Then extract on Windows
```

**Method 2: Manual Copy**
Copy these files to your MT5 Experts folder:
```
C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\XXXXX\MQL5\Experts\
```

Files needed:
- `QuantSupraAI.mq5`
- `config.mqh`
- `Include/RestClient.mqh`
- `Include/RiskManager.mqh`
- `Include/TradeEngine.mqh`
- `Include/Governors.mqh`

#### C. Edit config.mqh

Open `config.mqh` in MetaEditor and update:

```cpp
//+------------------------------------------------------------------+
//| Configuration for Quant Ω Supra AI EA                           |
//+------------------------------------------------------------------+

// ⚠️ YOUR UBUNTU SERVER IP
input string SidecarURL = "http://3.111.22.56:8000";

// Trading symbols
input string TradingSymbols = "NAS100,XAUUSD,EURUSD";

// Poll interval (1000-2000ms)
input int PollInterval = 1500;

// ⚠️ START IN LOG-ONLY MODE FOR TESTING
input bool LogOnlyMode = true;

// Risk settings
input double MaxRiskPerTrade = 0.01;
input double MaxDailyLoss = 45.0;
input double ProfitTarget = 100.0;
input double StartingEquity = 1000.0;
input double MinEquity = 900.0;
```

#### D. Compile EA

1. Open MetaEditor (F4 in MT5)
2. Open `QuantSupraAI.mq5`
3. Click Compile (F7)
4. Check for `0 error(s), 0 warning(s)`

#### E. Attach to Chart

1. Open MT5
2. Open a chart (NAS100, XAUUSD, or EURUSD)
3. Navigator → Expert Advisors → QuantSupraAI
4. Drag onto chart
5. Check "Allow live trading"
6. Click OK

**Look for smiley face icon** ✓

---

### Step 5: Verify Connection (2 minutes)

#### On Windows (MT5 Experts Log)

Toolbox (Ctrl+T) → Experts tab

**Look for:**
```
=== Quant Ω Supra AI Expert Advisor ===
Version: 1.00
Sidecar URL: http://3.111.22.56:8000
✓ REST Client initialized
✓ Risk Manager initialized
✓ Trade Engine initialized
✓ Governors initialized
Testing connection to Sidecar Service...
✓ Sidecar connection successful
EA Initialization Complete - Ready to Trade
```

#### On Ubuntu (Sidecar Logs)

```bash
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
```

**Look for:**
- `GET /api/signals` requests every 1-2 seconds
- No errors

✅ **System is connected and working!**

---

## 📊 Access Dashboard (Optional)

### Start Dashboard on Ubuntu

```bash
# In a new terminal
cd ~/Sandeep/projects/Vproptrader/dashboard

# Install dependencies (first time only)
npm install

# Create environment file
cp .env.example .env.local

# Edit it
nano .env.local
```

**Add:**
```
NEXT_PUBLIC_API_URL=http://3.111.22.56:8000
```

```bash
# Start dashboard
npm run dev
```

### Access from Windows

Open browser:
```
http://3.111.22.56:3000
```

**Note:** You may need to open port 3000 in firewall:
```bash
sudo ufw allow 3000/tcp
```

---

## 🧪 Test in Log-Only Mode (1 Hour)

**Monitor for at least 1 hour:**

### On Windows (MT5)
- Watch Experts tab
- Should see signal requests every 1-2 seconds
- May see "Processing signal" messages
- Should see "LOG-ONLY MODE: Would execute..." messages

### On Ubuntu (Sidecar)
```bash
# Watch logs
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log

# Or use monitoring script
cd ~/Sandeep/projects/Vproptrader
bash scripts/monitor.sh
```

### What to Check
- [ ] EA polls Sidecar continuously
- [ ] No connection errors
- [ ] Signals generated (if market conditions allow)
- [ ] Log-only mode logs decisions
- [ ] Latency acceptable (<400ms)
- [ ] No errors in logs

---

## 🎯 Enable Live Trading (When Ready)

**⚠️ ONLY after successful log-only testing!**

### On Windows

1. Edit `config.mqh`:
   ```cpp
   input bool LogOnlyMode = false;  // ← Change to false
   ```

2. Recompile (F7)

3. Remove EA from chart

4. Attach EA again

5. **Enable AutoTrading** (click button in MT5 toolbar)

### Monitor First Trade

- [ ] Signal received
- [ ] Trade executed
- [ ] Stop loss set
- [ ] Take profit set
- [ ] PnL tracked
- [ ] No errors

---

## 🔧 Useful Commands

### Ubuntu (Sidecar)

```bash
# Start Sidecar
cd ~/Sandeep/projects/Vproptrader/sidecar
source venv/bin/activate
python -m app.main

# Check health
curl http://localhost:8000/health
curl http://3.111.22.56:8000/health

# View logs
tail -f logs/app.log

# Monitor system
cd ~/Sandeep/projects/Vproptrader
bash scripts/monitor.sh

# Run tests
bash scripts/run_tests.sh
```

### Windows (Testing)

```cmd
REM Test connection
curl http://3.111.22.56:8000/health

REM Test signals
curl http://3.111.22.56:8000/api/signals?equity=1000

REM Ping server
ping 3.111.22.56
```

---

## 🆘 Troubleshooting

### Can't Connect from Windows

**Problem:** `curl http://3.111.22.56:8000/health` fails

**Check:**

1. **Ubuntu firewall:**
   ```bash
   sudo ufw status
   sudo ufw allow 8000/tcp
   ```

2. **Sidecar running:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Listening on all interfaces:**
   ```bash
   netstat -tuln | grep 8000
   # Should show: 0.0.0.0:8000
   ```

4. **AWS Security Group** (if using AWS):
   - Go to EC2 → Security Groups
   - Add inbound rule: TCP port 8000 from 0.0.0.0/0

5. **Check Sidecar config:**
   ```bash
   # In sidecar/app/core/config.py
   # Should have: host: str = "0.0.0.0"
   ```

### EA Shows Connection Error

**Check MT5 Experts log for specific error:**

- `Connection timeout` → Check firewall/security group
- `404 Not Found` → Verify Sidecar URL is correct
- `Connection refused` → Sidecar not running

### No Signals

**This is normal!** System is selective (>90% skip rate).

**Check:**
- Trading hours (London 07:00-10:00 or NY 13:30-16:00 UTC)
- Market is open
- Test endpoint: `curl http://3.111.22.56:8000/api/signals?equity=1000`

---

## 📋 Your Checklist

### Initial Setup
- [ ] Sidecar running on Ubuntu (3.111.22.56)
- [ ] Firewall port 8000 open
- [ ] Can curl health endpoint from Ubuntu
- [ ] Can curl health endpoint from Windows
- [ ] EA files copied to Windows MT5
- [ ] config.mqh updated with 3.111.22.56
- [ ] EA compiled successfully
- [ ] EA attached to chart
- [ ] Smiley face icon visible

### Testing
- [ ] Connection successful in MT5 log
- [ ] Signal requests every 1-2 seconds
- [ ] No errors in MT5 log
- [ ] No errors in Sidecar log
- [ ] Tested for 1 hour minimum
- [ ] Log-only mode working correctly

### Production
- [ ] Paper trading complete (1 week)
- [ ] Zero violations
- [ ] Performance acceptable
- [ ] Ready to enable live trading

---

## 🎉 Quick Summary

**Your Setup:**
- Ubuntu Server: `3.111.22.56`
- Sidecar: `http://3.111.22.56:8000`
- Dashboard: `http://3.111.22.56:3000`

**Next Steps:**
1. ✅ Start Sidecar on Ubuntu
2. ✅ Open firewall port 8000
3. ✅ Test connection from Windows
4. ✅ Configure and attach EA
5. 🧪 Test in log-only mode (1 hour)
6. 📊 Paper trade (1 week)
7. 🚀 Go live!

**Need Help?**
- Check `START_HERE.md` for complete guide
- See `WINDOWS_MT5_SETUP.md` for detailed Windows setup
- Review `TROUBLESHOOTING.md` for common issues

---

*Your Personal Setup Guide*
*Ubuntu IP: 3.111.22.56*
*Created: 2025-10-25*
