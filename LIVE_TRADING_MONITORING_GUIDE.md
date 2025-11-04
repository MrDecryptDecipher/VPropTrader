# Live Trading Monitoring Guide

## System Status: READY ✅

Your VPropTrader system is now live and ready to trade!

## What to Monitor

### 1. MT5 Expert Advisor (Windows)

**Location:** MT5 Terminal → Experts tab (bottom panel)

**What to Watch For:**

#### During Trading Hours (07:00-10:00 or 13:30-16:00 UTC)
```
Scanning for signals...
Signal received: BUY XAUUSD (Quality: 0.85)
Opening position: XAUUSD BUY 0.01 lots
Position opened successfully: Ticket #12345
```

#### Outside Trading Hours
```
Time-based close triggered (21:45 UTC or Friday 20:00)
```
This is normal - the EA is protecting your capital.

#### Warning Signs
```
ERROR: Cannot connect to sidecar
HARD GOVERNOR: Daily loss limit reached
SOFT GOVERNOR: Too many consecutive losses
```
If you see these, check the troubleshooting section below.

### 2. Dashboard (Web Interface)

**URL:** `http://YOUR_SERVER_IP:3000`

**What to Monitor:**

- **Real-time P&L:** Should update as trades execute
- **Open Positions:** Shows current trades
- **Drawdown Meter:** Should stay within safe limits
- **Connection Status:** Should show "Connected"
- **Market Timer:** Shows when next trading session opens

### 3. Sidecar (Signal Generator)

**Check Status:**
```bash
pm2 status
```

Should show:
```
sidecar     │ online
dashboard   │ online
```

**View Logs:**
```bash
pm2 logs sidecar --lines 50
```

**What to Look For:**
```
Generating signals for NAS100, XAUUSD, EURUSD
Signal quality: 0.87 (HIGH)
ES95 risk: $8.50 (within limit)
```

## Trading Schedule

### London Session
- **Time:** 07:00 - 10:00 UTC
- **Best for:** EURUSD, GBPUSD
- **Volatility:** Medium-High

### New York Session
- **Time:** 13:30 - 16:00 UTC
- **Best for:** NAS100, XAUUSD
- **Volatility:** High

### No Trading
- **21:45 - 07:00 UTC:** Daily close period
- **Friday 20:00 - Monday 07:00 UTC:** Weekend close

## Expected Behavior

### First Hour of Trading
- EA scans every 60 seconds
- May not find signals immediately
- Quality threshold is high (0.75+)
- This is normal and safe

### When a Signal is Found
1. Sidecar generates signal
2. EA receives signal via REST API
3. Risk manager validates ES95 < $10
4. Position sizing calculated
5. Trade executed
6. Dashboard updates in real-time

### Position Management
- **Stop Loss:** Automatically set based on ES95
- **Take Profit:** Dynamic based on signal
- **Max Concurrent:** 3 positions
- **Auto-close:** 21:45 UTC or Friday 20:00 UTC

## Risk Limits (Hard Governors)

These will STOP trading if triggered:

| Limit | Value | Action |
|-------|-------|--------|
| Daily Loss | -$100 | Stop trading for the day |
| Total Loss | -$500 | Stop trading completely |
| Equity Threshold | $9,500 | Stop if equity drops below |
| Profit Target | $1,000 | Stop when target reached |
| Daily Profit Cap | 5% | Stop when daily profit exceeds |

## Soft Governors (Warnings)

These will pause trading temporarily:

- **Cool-down after loss:** 300 seconds (5 minutes)
- **Consecutive losses:** 3 in a row
- **High spread:** 2x normal spread
- **Profit lock:** Locks 70% of profit above $50

## Daily Checklist

### Morning (Before London Open - 06:45 UTC)
- [ ] Check sidecar is running: `pm2 status`
- [ ] Verify MT5 EA shows "Auto Trading: ENABLED"
- [ ] Check dashboard is accessible
- [ ] Review yesterday's trades
- [ ] Confirm account balance

### During Trading
- [ ] Monitor MT5 Experts tab for signals
- [ ] Watch dashboard for position updates
- [ ] Check P&L stays within limits
- [ ] Verify positions close properly

### Evening (After NY Close - 16:30 UTC)
- [ ] Review day's performance
- [ ] Check all positions closed
- [ ] Verify no errors in logs
- [ ] Note any unusual behavior

## Performance Metrics to Track

### Daily
- Number of trades
- Win rate
- Average profit per trade
- Maximum drawdown
- Sharpe ratio

### Weekly
- Total P&L
- Best/worst days
- Most profitable symbols
- Governor triggers

### Monthly
- Return on capital
- Risk-adjusted returns
- System uptime
- Signal quality trends

## Troubleshooting

### EA Not Trading During Market Hours

**Check 1: Is AutoTrading enabled?**
```
Look in MT5 Experts tab for:
"Auto Trading: ENABLED"
```
If DISABLED, remove and re-attach EA with `EnableAutoTrading = true`

**Check 2: Is sidecar generating signals?**
```bash
pm2 logs sidecar --lines 20
```
Should see signal generation messages.

**Check 3: Are signals high quality?**
The EA only trades signals with quality > 0.75. Low quality = no trades (this is good!).

### Sidecar Connection Errors

**Error:** `Cannot connect to sidecar at http://127.0.0.1:8000`

**Fix:**
```bash
# Check if sidecar is running
pm2 status

# If stopped, restart it
pm2 restart sidecar

# Check logs
pm2 logs sidecar
```

### Dashboard Not Updating

**Check 1: Is dashboard running?**
```bash
pm2 status dashboard
```

**Check 2: Can you access it?**
```bash
curl http://localhost:3000
```

**Fix:**
```bash
pm2 restart dashboard
pm2 logs dashboard
```

### Positions Not Closing at 21:45 UTC

This is handled by the EA. Check:
1. EA is still running (look for smiley face icon)
2. No errors in Experts tab
3. Positions exist in MT5

If positions remain open, manually close them.

## Emergency Procedures

### Stop All Trading Immediately

**Method 1: Disable EA**
1. In MT5, click the "AutoTrading" button (toolbar)
2. It should turn RED
3. EA will stop executing new trades

**Method 2: Remove EA**
1. Right-click on chart
2. Expert Advisors → Remove
3. EA stops completely

**Method 3: Stop Sidecar**
```bash
pm2 stop sidecar
```
EA won't receive signals, so no new trades.

### Close All Open Positions

**In MT5:**
1. Go to "Trade" tab
2. Right-click on each position
3. Select "Close"

**Or use EA:**
The EA automatically closes all positions at 21:45 UTC and Friday 20:00 UTC.

## Optimization Tips

### After First Week

1. **Review signal quality distribution**
   - Are most signals 0.75-0.80 or 0.85+?
   - Higher quality = fewer but better trades

2. **Check symbol performance**
   - Which symbols are most profitable?
   - Consider focusing on best performers

3. **Analyze time-of-day patterns**
   - Are London or NY sessions better?
   - Adjust trading hours if needed

4. **Review risk parameters**
   - Is MaxES95 too conservative or aggressive?
   - Adjust based on results

### After First Month

1. **Retrain models** with live data
2. **Adjust position sizing** based on performance
3. **Fine-tune quality thresholds**
4. **Review and update governors**

## Support Commands

### Check System Status
```bash
# All services
pm2 status

# Sidecar logs
pm2 logs sidecar --lines 50

# Dashboard logs
pm2 logs dashboard --lines 50

# System resources
pm2 monit
```

### Restart Services
```bash
# Restart everything
pm2 restart all

# Restart specific service
pm2 restart sidecar
pm2 restart dashboard
```

### View Performance
```bash
# Check database
cd ~/Vproptrader/sidecar
python3 -c "from app.data.database import get_db; db = next(get_db()); print(db.execute('SELECT COUNT(*) FROM trades').fetchone())"
```

## Contact Information

### System Logs Location
- **MT5 Logs:** MT5 Data Folder → MQL5 → Logs
- **Sidecar Logs:** `~/.pm2/logs/sidecar-out.log`
- **Dashboard Logs:** `~/.pm2/logs/dashboard-out.log`

### Backup Important Data
```bash
# Backup database
cp ~/Vproptrader/sidecar/vproptrader.db ~/backups/vproptrader_$(date +%Y%m%d).db

# Backup configuration
cp ~/Vproptrader/sidecar/.env ~/backups/.env_$(date +%Y%m%d)
```

## Success Indicators

You'll know the system is working well when:

✅ EA shows "Auto Trading: ENABLED"
✅ Sidecar generates signals during market hours
✅ Dashboard shows real-time updates
✅ Trades execute within ES95 limits
✅ Positions close automatically at designated times
✅ P&L stays within governor limits
✅ No repeated error messages in logs

## Next Steps

1. **Monitor for 1 week** - Let the system run and observe
2. **Review performance** - Check metrics daily
3. **Adjust if needed** - Fine-tune based on results
4. **Scale gradually** - Increase position sizes slowly
5. **Keep learning** - Review trades and improve

---

**Remember:** The system is designed to be conservative. Fewer high-quality trades are better than many low-quality trades. Trust the process!

**Current Status:** System is LIVE and ready to trade during next market session.
