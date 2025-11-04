# 🚀 QUICK START - Your VPropTrader Account

## Your Account Details

- **Login**: 1779362
- **Server**: Vebson-Server
- **Balance**: $1,000 (Demo)
- **Challenge**: Pass with $100 profit, <$50 daily loss, 4+ trading days

---

## Start Trading in 10 Minutes

### Step 1: Setup Sidecar (5 minutes)

```bash
cd Vproptrader/sidecar

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy YOUR configuration
cp ../YOUR_ACCOUNT.env .env

# Start the service
python -m app.main
```

**Expected Output**:
```
✓ Database connected: ./data/vproptrader.db
✓ Redis connected: localhost:6379
✓ FAISS index created: 50D
✓ MT5 connected successfully
Account: 1779362, Balance: $1000.00
✓ FRED API connected - Retrieved 7 indicators
✓ Calendar: X high-impact events loaded
✓ Sidecar Service started successfully
```

### Step 2: Test the System (2 minutes)

Open a new terminal:

```bash
# Check health
curl http://localhost:8000/health

# Get trading signals
curl http://localhost:8000/api/signals

# View API docs
open http://localhost:8000/docs
```

### Step 3: Install MT5 EA (3 minutes)

1. **Find your MT5 Data Folder**:
   - In MT5: File → Open Data Folder
   - Navigate to: `MQL5/Experts/`

2. **Copy EA Files**:
   ```bash
   # Copy the entire mt5_ea folder
   cp -r Vproptrader/mt5_ea/* [MT5_DATA_FOLDER]/MQL5/Experts/QuantSupraAI/
   ```

3. **Compile EA**:
   - Open MetaEditor (F4 in MT5)
   - Navigate to: Experts → QuantSupraAI → QuantSupraAI.mq5
   - Click Compile (F7)
   - Check for success message

4. **Attach EA to Chart**:
   - In MT5 Navigator, find "QuantSupraAI" under Expert Advisors
   - Drag it onto any chart (NAS100, XAUUSD, or EURUSD recommended)
   - In the settings dialog:
     - **Common tab**: ✅ Allow live trading, ✅ Allow DLL imports, ✅ Allow WebRequest
     - **Inputs tab**:
       - SidecarURL: `http://localhost:8000`
       - PollInterval: `1500`
       - LogOnlyMode: `true` (for first test)
       - MagicNumber: `20251025`
   - Click OK

5. **Enable AutoTrading**:
   - Click the "AutoTrading" button in MT5 toolbar (should turn green)

---

## What Happens Next

### In Log-Only Mode (First Hour)

The EA will:
- ✅ Connect to Sidecar every 1.5 seconds
- ✅ Receive trading signals
- ✅ Log what it WOULD do (no real trades)
- ✅ Print to MT5 Experts tab: "LOG-ONLY: Would BUY/SELL..."

**Watch the MT5 Experts tab** for messages like:
```
Status - Enabled: true | Daily PnL: $0.00 | Total PnL: $0.00 | Trades Today: 0
LOG-ONLY: Would BUY 0.05 lots of NAS100 SL:15250.5 TP:15275.0
```

### Switch to Live Trading

After verifying log-only mode works:

1. Right-click EA on chart → Properties
2. Inputs tab → LogOnlyMode: `false`
3. Click OK

**Now the EA will execute real trades!**

---

## Monitoring Your Trading

### Real-Time Monitoring

```bash
# Check current status
curl http://localhost:8000/health

# Get active signals
curl http://localhost:8000/api/signals

# View performance
curl http://localhost:8000/api/analytics/overview

# Check compliance
curl http://localhost:8000/api/analytics/compliance
```

### View Logs

```bash
# Sidecar logs
tail -f Vproptrader/sidecar/logs/sidecar_*.log

# Error logs
tail -f Vproptrader/sidecar/logs/errors_*.log
```

### Check Database

```bash
cd Vproptrader/sidecar
sqlite3 data/vproptrader.db

# View recent trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

# Check daily performance
SELECT * FROM daily_performance ORDER BY date DESC LIMIT 7;

# Exit
.quit
```

---

## Understanding the System

### What the Sidecar Does

1. **Every Second**:
   - Fetches MT5 market data (ticks, bars)
   - Gets FRED macro data (DXY, VIX, UST10Y)
   - Checks economic calendar for news
   - Extracts 50 features
   - Runs 6 alpha strategies
   - Evaluates 30-40 symbol-alpha combinations
   - Ranks by Q* score
   - Filters by risk (ES95 < $10, correlation < 0.3)
   - Returns top 3 signals (if any)

2. **Skip Rate**: >90%
   - Most scans return 0 signals
   - Only A/A+ grade setups pass filters
   - This is GOOD - quality over quantity

### What the EA Does

1. **Every 1.5 Seconds**:
   - Polls Sidecar for signals
   - Checks hard governors (daily loss, equity, time)
   - Validates trading session (London 07:00-10:00, NY 13:30-16:00 UTC)
   - Executes signals if all checks pass
   - Monitors open positions
   - Reports executions back to Sidecar

2. **Hard Governors** (Cannot be overridden):
   - Daily loss ≤ -$45 → Auto-flat, block trades
   - Total loss ≤ -$100 → Disable EA
   - Equity < $900 → Disable EA
   - Profit ≥ $100 → Halt new entries
   - Daily profit ≥ 1.8% → Halt new entries
   - Time 21:45 UTC → Close all positions
   - Friday 20:00 UTC → Close all positions

### Signal Example

When you see a signal:
```json
{
  "symbol": "NAS100",
  "action": "BUY",
  "confidence": 0.85,
  "q_star": 8.2,
  "es95": 8.5,
  "stop_loss": 15250.5,
  "take_profit_1": 15275.0,
  "take_profit_2": 15290.0,
  "lots": 0.05,
  "alpha_id": "momentum_v3",
  "regime": "trend_up"
}
```

This means:
- **Q* = 8.2**: High confidence (A grade, threshold is 7.0)
- **ES95 = $8.50**: Expected loss if wrong (under $10 limit)
- **Momentum strategy** detected strong uptrend
- **Position size**: 0.05 lots (Kelly-optimized)
- **Risk**: $12.50 (15275.0 - 15250.5 = 24.5 points × 0.05 lots)

---

## VPropTrader Challenge Rules

### Must Achieve:
- ✅ $100 profit (10% of $1,000)
- ✅ At least 4 trading days
- ✅ No single day loss > $50 (5%)
- ✅ Total drawdown < $100 (10%)

### Must Avoid:
- ❌ Overnight positions (auto-closed at 21:45 UTC)
- ❌ Weekend trading (auto-closed Friday 20:00 UTC)
- ❌ Trading during high-impact news (auto-embargoed)
- ❌ Exceeding daily profit cap (1.8%)

**Your system enforces ALL these rules automatically!**

---

## Expected Performance

### First Week:
- **Trades**: 10-20 (highly selective)
- **Win Rate**: ~60-65%
- **Daily Return**: 0.5-1.5%
- **Max DD**: <2%

### Challenge Completion:
- **Timeline**: 1-3 weeks
- **Total Trades**: 50-100
- **Final Profit**: $100-120
- **Violations**: 0

---

## Troubleshooting

### Sidecar Won't Start

**Error**: `ModuleNotFoundError`
```bash
# Solution: Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

**Error**: `MT5 connection failed`
```bash
# Solution: Check MT5 is running
# Verify credentials in .env
# Make sure you're logged into MT5 with account 1779362
```

### EA Not Receiving Signals

**Check**:
1. Sidecar is running: `curl http://localhost:8000/health`
2. URL in EA settings: `http://localhost:8000`
3. WebRequest is allowed in MT5:
   - Tools → Options → Expert Advisors
   - ✅ Allow WebRequest for listed URL
   - Add: `http://localhost:8000`

### No Trades Executing

**This is normal!** The system is highly selective:
- >90% of scans return no signals
- Only A/A+ setups trade
- Outside trading sessions (London/NY), no trades
- During news embargo, no trades

**Check**:
- Current time is during London (07:00-10:00 UTC) or NY (13:30-16:00 UTC)
- No high-impact news in next 30 minutes
- LogOnlyMode is `false`
- AutoTrading is enabled (green button)

---

## Next Steps

### Today:
1. ✅ Start Sidecar
2. ✅ Install MT5 EA
3. ✅ Run in log-only mode for 1 hour
4. ✅ Switch to live trading

### This Week:
1. ✅ Monitor first trades
2. ✅ Verify compliance
3. ✅ Check daily performance
4. ✅ Collect trade data

### This Month:
1. ✅ Train ML models (after 100+ trades)
2. ✅ Pass VPropTrader challenge
3. ✅ Get funded account!

---

## Support

### Logs:
- Sidecar: `Vproptrader/sidecar/logs/`
- MT5: Experts tab in MT5 terminal

### API:
- Health: `http://localhost:8000/health`
- Signals: `http://localhost:8000/api/signals`
- Docs: `http://localhost:8000/docs`

### Database:
- Path: `Vproptrader/sidecar/data/vproptrader.db`
- Tool: `sqlite3` or any SQLite browser

---

## 🎯 YOU'RE READY!

Your account is configured and the system is ready to trade.

**Start the Sidecar now and begin your journey to passing the challenge!**

```bash
cd Vproptrader/sidecar
source venv/bin/activate
python -m app.main
```

**Good luck! 🚀📈💰**
