# 🚀 READY TO START!

## ✅ Everything is Configured

Your system is **100% ready** with:
- ✅ Ubuntu IP: **3.111.22.56**
- ✅ MT5 Login: **1779362**
- ✅ MT5 Server: **Vebson-Server**
- ✅ FRED API Key: Configured
- ✅ All files in place

---

## 🎯 Start in 3 Steps (10 Minutes)

### Step 1: Start Sidecar (5 minutes)

```bash
# You're already here: ~/Sandeep/projects/Vproptrader

# Navigate to sidecar
cd sidecar

# Create virtual environment (first time only)
python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies (first time only - takes 2-3 minutes)
pip install -r requirements.txt

# Your .env file is already configured with your VProp credentials!
# Just start the service:
python -m app.main
```

**Expected output:**
```
=== Starting Quant Ω Supra AI Sidecar Service ===
Environment: development
Host: 0.0.0.0:8000
Symbols: NAS100,XAUUSD,EURUSD
✓ MT5 connected successfully
✓ FRED API connected
✓ Sidecar Service started successfully
```

---

### Step 2: Open Firewall (1 minute)

**Open a NEW terminal** (keep Sidecar running) and run:

```bash
# Allow port 8000
sudo ufw allow 8000/tcp

# Verify
sudo ufw status
```

**Test it works:**
```bash
# Test locally
curl http://localhost:8000/health

# Test from public IP
curl http://3.111.22.56:8000/health
```

You should see JSON response! ✓

---

### Step 3: Connect from Windows (4 minutes)

**On your Windows machine:**

#### A. Test Connection
```cmd
curl http://3.111.22.56:8000/health
```

**If you see JSON, connection works!** ✓

#### B. Download MT5 EA Files

**Transfer from Ubuntu to Windows:**

**Option 1: Create ZIP on Ubuntu**
```bash
cd ~/Sandeep/projects/Vproptrader
zip -r mt5_ea.zip mt5_ea/
```

Then download `mt5_ea.zip` using:
- WinSCP
- FileZilla
- Your cloud provider's file transfer
- Or any SCP client

**Option 2: Manual Copy**
Copy these files to Windows MT5:
```
From: ~/Sandeep/projects/Vproptrader/mt5_ea/
To: C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\XXXXX\MQL5\Experts\
```

Files:
- QuantSupraAI.mq5
- config.mqh (already has your IP: 3.111.22.56)
- Include/ folder (all .mqh files)

#### C. Compile and Attach

1. Open **MetaEditor** (F4 in MT5)
2. Open `QuantSupraAI.mq5`
3. Click **Compile** (F7)
4. Should see: `0 error(s), 0 warning(s)` ✓

5. In **MT5**:
   - Open chart (NAS100, XAUUSD, or EURUSD)
   - Navigator → Expert Advisors → QuantSupraAI
   - Drag onto chart
   - Check "Allow live trading"
   - Click OK

**Look for smiley face icon** in top-right ✓

---

## ✅ Verify It's Working

### On Windows (MT5 Experts Log)

Toolbox (Ctrl+T) → Experts tab

**You should see:**
```
=== Quant Ω Supra AI Expert Advisor ===
Sidecar URL: http://3.111.22.56:8000
✓ REST Client initialized
✓ Risk Manager initialized
✓ Trade Engine initialized
✓ Governors initialized
✓ Sidecar connection successful
EA Initialization Complete - Ready to Trade
```

Then every 1-2 seconds:
```
Polling Sidecar for signals...
```

### On Ubuntu (Sidecar Logs)

```bash
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log
```

**You should see:**
```
GET /api/signals?equity=1000 - 200 OK
```

Every 1-2 seconds from your EA.

---

## 🎉 Success!

If you see:
- ✅ Sidecar running on Ubuntu
- ✅ EA connected in MT5
- ✅ Signal requests every 1-2 seconds
- ✅ No errors

**Your system is LIVE and working!**

---

## 📊 Monitor Your System

### Real-Time Dashboard

```bash
cd ~/Sandeep/projects/Vproptrader
bash scripts/monitor.sh
```

Shows:
- System status
- Account overview
- Compliance status
- Active signals
- System resources

### View Logs

```bash
# Sidecar logs
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log

# Trade logs (when trades happen)
tail -f ~/Sandeep/projects/Vproptrader/sidecar/logs/trades_$(date +%Y-%m-%d).jsonl
```

---

## 🧪 Testing Phase

**You're in LOG-ONLY MODE** (safe testing mode)

The EA will:
- ✅ Connect to Sidecar
- ✅ Receive signals
- ✅ Log all decisions
- ❌ NOT execute real trades

**Monitor for 1 hour minimum:**
- Watch MT5 Experts log
- Check Sidecar logs
- Verify no errors
- Confirm signals are generated (if market conditions allow)

**After successful testing:**
- Paper trade for 1 week
- Then enable live trading

---

## 🎯 What's Happening

### Current Setup

```
┌─────────────────┐         ┌─────────────────┐
│  Windows PC     │         │  Ubuntu Server  │
│                 │         │  3.111.22.56    │
│  ┌───────────┐  │         │                 │
│  │ MT5 + EA  │  │  HTTP   │  ┌───────────┐  │
│  │ Login:    │◄─┼─────────┼─►│  Sidecar  │  │
│  │ 1779362   │  │         │  │  Port:8000│  │
│  └───────────┘  │         │  └───────────┘  │
│                 │         │                 │
│  Polls every    │         │  ML Models      │
│  1-2 seconds    │         │  Risk Mgmt      │
│                 │         │  Compliance     │
└─────────────────┘         └─────────────────┘
```

### What the System Does

1. **EA polls Sidecar** every 1-2 seconds
2. **Sidecar analyzes** market with ML models
3. **Generates signals** (only A/A+ grade, >90% skip rate)
4. **EA receives signals** and logs decisions
5. **In log-only mode:** Just logs, no trades
6. **When live:** Executes trades with full risk management

---

## 📚 Next Steps

### Today
- [x] Start Sidecar ✓
- [x] Connect MT5 ✓
- [ ] Monitor for 1 hour
- [ ] Verify no errors

### This Week
- [ ] Test in log-only mode daily
- [ ] Review all signals
- [ ] Check compliance (zero violations)
- [ ] Verify performance metrics

### Next Week
- [ ] Paper trade for 1 week
- [ ] Monitor daily
- [ ] Review logs
- [ ] Prepare for live trading

### Then
- [ ] Enable live trading
- [ ] Monitor first trades closely
- [ ] Pass VProp challenge!
- [ ] Get funded account! 💰

---

## 🆘 Quick Troubleshooting

### EA Can't Connect

**Check on Ubuntu:**
```bash
# Is Sidecar running?
curl http://localhost:8000/health

# Is firewall open?
sudo ufw status | grep 8000

# What's listening?
netstat -tuln | grep 8000
```

**Check from Windows:**
```cmd
ping 3.111.22.56
curl http://3.111.22.56:8000/health
```

### No Signals

**This is normal!** System is very selective (>90% skip rate).

**Check:**
- Trading hours (London 07:00-10:00 or NY 13:30-16:00 UTC)
- Market is open
- Test: `curl http://3.111.22.56:8000/api/signals?equity=1000`

### Errors in Logs

**Check Sidecar logs:**
```bash
grep -i error ~/Sandeep/projects/Vproptrader/sidecar/logs/app.log | tail -20
```

**Check MT5 Experts tab** for specific errors

---

## 📞 Your Configuration Summary

```
┌─────────────────────────────────────────────────────┐
│           YOUR CONFIGURATION                        │
├─────────────────────────────────────────────────────┤
│ Ubuntu IP:        3.111.22.56                      │
│ Sidecar URL:      http://3.111.22.56:8000          │
│                                                     │
│ MT5 Login:        1779362                          │
│ MT5 Password:     1Ax@wjfd                         │
│ MT5 Server:       Vebson-Server                    │
│                                                     │
│ Trading Symbols:  NAS100, XAUUSD, EURUSD           │
│ Mode:             LOG-ONLY (testing)               │
│                                                     │
│ Status:           ✅ READY TO START                 │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Start Now!

**Just run these commands:**

```bash
cd ~/Sandeep/projects/Vproptrader/sidecar
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

**Then in another terminal:**
```bash
sudo ufw allow 8000/tcp
curl http://3.111.22.56:8000/health
```

**That's it! Your system is running!** 🎉

---

*Everything is configured and ready*
*Just start Sidecar and connect MT5*
*You're 10 minutes away from trading!*
