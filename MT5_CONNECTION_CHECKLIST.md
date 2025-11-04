# MT5 Connection Checklist

## Quick Setup Checklist

Use this checklist to connect your Windows MT5 to the Linux Sidecar service.

---

## ☑️ Pre-Requirements

- [ ] Linux machine with Sidecar installed
- [ ] Windows machine with MT5 installed
- [ ] Both machines can communicate (same network or internet)
- [ ] Python 3.11+ on Linux
- [ ] Redis running on Linux

---

## ☑️ Step 1: Linux Setup (5 minutes)

### Get IP Address
```bash
hostname -I
```
**My Linux IP:** `_________________` ← Write it down!

### Start Sidecar
```bash
cd ~/Sandeep/projects/Vproptrader/sidecar
source venv/bin/activate
python -m app.main
```

### Verify Running
```bash
curl http://localhost:8000/health
```
- [ ] Returns JSON response ✓

### Configure Firewall
```bash
sudo ufw allow 8000/tcp
sudo ufw status
```
- [ ] Port 8000 is open ✓

### Test from Network
```bash
# Should show 0.0.0.0:8000 (not 127.0.0.1:8000)
netstat -tuln | grep 8000
```
- [ ] Listening on all interfaces ✓

---

## ☑️ Step 2: Windows Setup (10 minutes)

### Test Connection from Windows
Open Command Prompt:
```cmd
ping YOUR_LINUX_IP
curl http://YOUR_LINUX_IP:8000/health
```
- [ ] Ping successful ✓
- [ ] Curl returns JSON ✓

### Copy EA Files to MT5

**MT5 Experts folder location:**
```
C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\XXXXX\MQL5\Experts\
```

**Files to copy:**
- [ ] `QuantSupraAI.mq5`
- [ ] `config.mqh`
- [ ] `Include/RestClient.mqh`
- [ ] `Include/RiskManager.mqh`
- [ ] `Include/TradeEngine.mqh`
- [ ] `Include/Governors.mqh`

### Edit config.mqh

Open in MetaEditor and update:
```cpp
input string SidecarURL = "http://YOUR_LINUX_IP:8000";  // ← Change this!
input bool LogOnlyMode = true;  // ← Keep true for testing
```

**My Sidecar URL:** `http://_________________:8000`

- [ ] SidecarURL updated with correct IP ✓
- [ ] LogOnlyMode = true ✓

### Compile EA

1. Open MetaEditor (F4)
2. Open `QuantSupraAI.mq5`
3. Click Compile (F7)
4. Check for errors

- [ ] Compilation successful (0 errors) ✓

---

## ☑️ Step 3: Attach EA to Chart (2 minutes)

### In MT5 Terminal

1. Open chart (e.g., NAS100)
2. Navigator → Expert Advisors → QuantSupraAI
3. Drag onto chart
4. Check "Allow live trading"
5. Click OK

- [ ] EA attached to chart ✓
- [ ] Smiley face icon visible ✓

### Check Experts Log

Toolbox (Ctrl+T) → Experts tab

**Look for:**
```
=== Quant Ω Supra AI Expert Advisor ===
✓ REST Client initialized
✓ Risk Manager initialized
✓ Trade Engine initialized
✓ Governors initialized
✓ Sidecar connection successful
EA Initialization Complete - Ready to Trade
```

- [ ] All components initialized ✓
- [ ] Sidecar connection successful ✓
- [ ] No errors ✓

---

## ☑️ Step 4: Verify Operation (5 minutes)

### On Windows (MT5 Experts Log)

Watch for:
- [ ] Signal requests every 1-2 seconds ✓
- [ ] "Processing signal" messages (if signals available) ✓
- [ ] "LOG-ONLY MODE: Would execute..." messages ✓
- [ ] No connection errors ✓

### On Linux (Sidecar Logs)

```bash
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
```

Watch for:
- [ ] `GET /api/signals` requests ✓
- [ ] Signal generation (if any) ✓
- [ ] No errors ✓

### Test Signals Endpoint

```bash
curl http://localhost:8000/api/signals?equity=1000
```
- [ ] Returns signals JSON ✓

---

## ☑️ Step 5: Monitor (1 hour minimum)

### Things to Check

- [ ] EA polls Sidecar every 1-2 seconds
- [ ] No connection timeouts
- [ ] Signals are generated (if market conditions allow)
- [ ] Log-only mode logs decisions correctly
- [ ] No errors in MT5 or Sidecar logs
- [ ] Latency is acceptable (<400ms)

### Dashboard (Optional)

If running:
```
http://YOUR_LINUX_IP:3000
```

- [ ] Dashboard loads ✓
- [ ] Shows connection status ✓
- [ ] Displays account info ✓

---

## ☑️ Step 6: Enable Live Trading (When Ready)

**⚠️ ONLY after successful log-only testing!**

### Update Configuration

1. Edit `config.mqh`:
   ```cpp
   input bool LogOnlyMode = false;  // ← Change to false
   ```
2. Recompile (F7)
3. Remove EA from chart
4. Attach EA again

- [ ] LogOnlyMode = false ✓
- [ ] Recompiled successfully ✓
- [ ] EA reattached ✓

### Enable AutoTrading

In MT5 toolbar:
- [ ] Click AutoTrading button (turns green) ✓

### Monitor First Trade

- [ ] First signal received
- [ ] Trade executed
- [ ] Stop loss set correctly
- [ ] Take profit set correctly
- [ ] Execution reported to Sidecar
- [ ] PnL tracking works
- [ ] No errors

---

## 🔧 Troubleshooting

### Connection Failed

**Problem:** EA can't connect to Sidecar

**Check:**
- [ ] Linux IP address is correct
- [ ] Sidecar is running: `curl http://localhost:8000/health`
- [ ] Firewall allows port 8000: `sudo ufw status`
- [ ] Can ping from Windows: `ping YOUR_LINUX_IP`
- [ ] Can curl from Windows: `curl http://YOUR_LINUX_IP:8000/health`

**Fix:**
```bash
# On Linux
sudo ufw allow 8000/tcp
sudo systemctl restart vprop-sidecar  # If running as service
```

### Compilation Errors

**Problem:** EA won't compile

**Check:**
- [ ] All Include files are present
- [ ] config.mqh is in same directory
- [ ] Using MT5 (not MT4)
- [ ] No syntax errors

### No Signals

**Problem:** EA connects but no signals

**Check:**
- [ ] Trading hours (London 07:00-10:00 or NY 13:30-16:00 UTC)
- [ ] Symbols available in MT5
- [ ] Market is open
- [ ] Test endpoint: `curl http://localhost:8000/api/signals?equity=1000`

**Note:** System is selective (>90% skip rate), no signals is normal if no A/A+ setups.

---

## 📋 Quick Reference

### My Configuration

**Linux Machine:**
- IP Address: `_________________`
- Sidecar URL: `http://_________________:8000`
- Location: `~/Sandeep/projects/Vproptrader/sidecar/`

**Windows Machine:**
- MT5 Data Folder: `C:\Users\_______\AppData\Roaming\MetaQuotes\Terminal\`
- EA Location: `...\MQL5\Experts\QuantSupraAI.mq5`

**Trading Symbols:**
- [ ] NAS100
- [ ] XAUUSD
- [ ] EURUSD
- [ ] Other: `_________________`

### Essential Commands

**Linux:**
```bash
# Start Sidecar
cd ~/Sandeep/projects/Vproptrader/sidecar && source venv/bin/activate && python -m app.main

# Check health
curl http://localhost:8000/health

# View logs
tail -f logs/app.log

# Get IP
hostname -I
```

**Windows:**
```cmd
# Test connection
curl http://YOUR_LINUX_IP:8000/health

# Ping
ping YOUR_LINUX_IP
```

---

## ✅ Success Criteria

### Initial Setup
- [x] Sidecar running on Linux
- [x] EA compiled on Windows
- [x] EA attached to MT5 chart
- [x] Connection successful
- [x] No errors in logs

### Log-Only Testing (1 hour)
- [ ] EA polls Sidecar continuously
- [ ] Signals received (if available)
- [ ] Decisions logged correctly
- [ ] No connection issues
- [ ] Latency acceptable

### Live Trading (When enabled)
- [ ] First trade executed
- [ ] Stop loss/take profit set
- [ ] PnL tracked correctly
- [ ] Compliance monitored
- [ ] No violations

---

## 🎯 Next Steps

1. ✅ Complete this checklist
2. ✅ Test in log-only mode (1 hour minimum)
3. ✅ Review all logs
4. ✅ Verify zero errors
5. 🎯 Enable live trading (when confident)
6. 📊 Monitor performance
7. 🏆 Pass VProp challenge!

---

**Setup Date:** `_________________`
**Tested By:** `_________________`
**Status:** `_________________`

---

*Last Updated: 2025-10-25*
*Version: 1.0.0*
