# Next Steps After Successful Compilation

## ✅ Compilation Success: 0 errors, 0 warnings

Congratulations! The EA compiled successfully. Here's what to do next:

---

## 🔍 Step 1: Verify the .ex5 File Was Created

**On Windows MT5:**

Check that the compiled file exists:
```
C:\Users\Superagent\AppData\Roaming\MetaQuotes\Terminal\
2A7A61598246A894915935526B662613\MQL5\Experts\QuantSupraAI.ex5
```

You should see:
- `QuantSupraAI.mq5` (source file)
- `QuantSupraAI.ex5` (compiled executable) ← This is what you need!

---

## 🚀 Step 2: Verify Sidecar is Running on Ubuntu

**On Ubuntu server (3.111.22.56):**

```bash
# Check if Sidecar is running
curl http://localhost:8000/health

# Or from Windows, test the connection:
curl http://3.111.22.56:8000/health
```

**Expected response:**
```json
{"status":"healthy","service":"vproptrader-sidecar"}
```

**If Sidecar is NOT running, start it:**
```bash
cd ~/Sandeep/projects/Vproptrader/sidecar
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📊 Step 3: Attach EA to MT5 Chart (LOG-ONLY MODE)

**IMPORTANT: Start in LOG-ONLY mode for testing!**

### 3.1 Open a Chart
1. In MT5, open a chart for one of these symbols:
   - **NAS100** (recommended for testing)
   - XAUUSD
   - EURUSD

### 3.2 Attach the EA
1. Press **Ctrl+N** to open Navigator
2. Expand "Expert Advisors"
3. Find **QuantSupraAI**
4. Drag it onto the chart

### 3.3 Configure Settings

**In the EA settings dialog:**

**Inputs Tab:**
- `SidecarURL`: `http://3.111.22.56:8000`
- `PollInterval`: `1500` (1.5 seconds)
- `TradingSymbols`: `NAS100,XAUUSD,EURUSD`
- `MagicNumber`: `20251025`
- `LogOnlyMode`: **`true`** ← CRITICAL! Keep this TRUE for testing
- `VerboseLogging`: `true`

**Common Tab:**
- ✅ Check "Allow live trading"
- ✅ Check "Allow DLL imports" (if needed)

**Click OK**

---

## 📝 Step 4: Monitor the Logs

### 4.1 Check MT5 Experts Tab

Look at the bottom panel in MT5 (Experts tab). You should see:

```
=== Quant Ω Supra AI Expert Advisor ===
Version: 1.00
Sidecar URL: http://3.111.22.56:8000
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
Response: {"status":"healthy"...}
```

### 4.2 What to Look For

**Good Signs:**
- ✓ All modules initialized
- ✓ Sidecar connection successful
- ✓ Polling for signals every 1.5 seconds
- ✓ "LOG-ONLY MODE: Would execute..." messages (if signals received)

**Warning Signs:**
- ⚠ "Could not connect to Sidecar"
- ⚠ "WebRequest error"
- ⚠ "URL not in allowed list"

---

## 🔧 Step 5: Troubleshooting

### Issue: "WebRequest error" or "URL not allowed"

**Fix:**
1. In MT5: Tools → Options → Expert Advisors
2. Check "Allow WebRequest for listed URL"
3. Add to the list: `http://3.111.22.56:8000`
4. Click OK
5. Restart EA (remove from chart and re-attach)

### Issue: "Could not connect to Sidecar"

**Check:**
1. Is Sidecar running on Ubuntu? `curl http://3.111.22.56:8000/health`
2. Is port 8000 open? `sudo ufw status`
3. Can Windows reach Ubuntu? `ping 3.111.22.56`
4. Is the IP correct in EA settings?

### Issue: No signals received

**This is normal if:**
- Market is closed
- Outside trading hours (8:00-21:00 UTC)
- No trading opportunities detected by Sidecar
- Sidecar hasn't generated signals yet

---

## 🧪 Step 6: Test Signal Reception (Optional)

### 6.1 Check Sidecar Signals Endpoint

From Windows or Ubuntu:
```bash
curl http://3.111.22.56:8000/api/signals
```

**Expected response:**
```json
{
  "signals": [
    {
      "symbol": "NAS100",
      "action": "BUY",
      "confidence": 0.85,
      "q_star": 2.3,
      ...
    }
  ]
}
```

### 6.2 Watch EA Process Signals

If signals are available, you should see in MT5 Experts tab:
```
Received 1 signal(s) from Sidecar
Processing signal: NAS100 BUY Q*=2.3 Lots=0.5
LOG-ONLY MODE: Would execute BUY 0.5 lots of NAS100
```

---

## ✅ Step 7: Verify Everything is Working

**Checklist:**
- [ ] EA attached to chart with smiley face icon
- [ ] "Log-Only Mode: YES" in initialization
- [ ] Sidecar connection successful
- [ ] Polling for signals every 1.5 seconds
- [ ] No error messages in Experts tab
- [ ] If signals available, seeing "LOG-ONLY MODE: Would execute..." messages

---

## 🎯 Step 8: Monitor for 30 Minutes

Let the EA run in LOG-ONLY mode for at least 30 minutes to verify:

1. **Stable connection** - No disconnections from Sidecar
2. **Signal processing** - If signals come, they're logged correctly
3. **Risk checks** - Validation messages appear
4. **No crashes** - EA stays running without errors

**What you should see:**
```
[Time] Polling Sidecar for signals...
[Time] Received 0 signal(s) from Sidecar
[Time] Polling Sidecar for signals...
[Time] Received 1 signal(s) from Sidecar
[Time] Processing signal: NAS100 BUY Q*=2.3 Lots=0.5
[Time] LOG-ONLY MODE: Would execute BUY 0.5 lots of NAS100
```

---

## 🚨 Step 9: BEFORE Going Live

**DO NOT disable Log-Only mode until:**

1. ✅ EA runs stable for at least 24 hours in log-only mode
2. ✅ You've verified signal processing is correct
3. ✅ You've reviewed all risk limits in config.mqh
4. ✅ You're using a DEMO account first
5. ✅ You understand all the risk parameters
6. ✅ You've tested with small position sizes

**Risk Limits (Review These):**
- Daily Loss Limit: -$45
- Total Loss Limit: -$100
- Equity Disable: $900
- Max Open Positions: 3
- Daily Profit Cap: 1.8%

---

## 📊 Step 10: Monitor Dashboard (Optional)

If you have the dashboard running:

```bash
# On Ubuntu
cd ~/Sandeep/projects/Vproptrader/dashboard
npm run dev
```

Access at: `http://3.111.22.56:3000`

You should see:
- Connection status
- Real-time PnL (should be $0 in log-only mode)
- Signal history
- Risk metrics

---

## 🎉 Success Criteria

**You're ready for the next phase when:**

1. ✅ EA runs without errors for 24+ hours
2. ✅ Signals are being received and logged correctly
3. ✅ All risk checks are working
4. ✅ No connection issues with Sidecar
5. ✅ You understand the system behavior

---

## 📞 Next Phase: Demo Trading

**After successful log-only testing:**

1. Switch to a **DEMO account** in MT5
2. Change `LogOnlyMode` to `false` in EA settings
3. Start with minimum position sizes
4. Monitor closely for first few trades
5. Verify executions match expectations
6. Check risk limits are enforced

**Only after successful demo trading should you consider live trading.**

---

## 🔍 Monitoring Commands

**Check Sidecar health:**
```bash
curl http://3.111.22.56:8000/health
```

**Check available signals:**
```bash
curl http://3.111.22.56:8000/api/signals
```

**View Sidecar logs:**
```bash
# If running in terminal
# Check the terminal where Sidecar is running

# If running as service
sudo journalctl -u vproptrader-sidecar -f
```

---

## 📋 Current Status

- ✅ EA compiled successfully (0 errors, 0 warnings)
- ✅ All files in place
- ⏳ Ready for testing in LOG-ONLY mode
- ⏳ Awaiting 24-hour stability test
- ⏳ Demo trading phase
- ⏳ Live trading (future)

---

**Remember: ALWAYS start with Log-Only mode, then Demo account, then Live with small sizes!**

**Date:** 2025-10-26  
**Status:** ✅ Compiled - Ready for Testing  
**Mode:** LOG-ONLY (Safe Testing)
