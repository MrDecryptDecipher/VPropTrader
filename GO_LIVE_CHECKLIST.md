# VPropTrader - Go Live Checklist

## ⚠️ CRITICAL WARNING

You are about to trade with REAL MONEY. Please read this entire document carefully.

## Current Status

✅ **Backtest Complete**: 44.61% return on historical data
✅ **System Tested**: All components working
✅ **Risk Management**: ES95 constraints implemented
⚠️ **Live Trading**: NOT YET ACTIVATED

## Prerequisites Before Going Live

### 1. MT5 Account Setup
- [ ] VPropTrader account funded with $1,000
- [ ] MT5 platform installed and logged in
- [ ] Account credentials configured in `YOUR_ACCOUNT.env`
- [ ] MT5 EA compiled and loaded on chart
- [ ] EA shows "Connected" status

### 2. System Components Running
- [ ] Sidecar API running (`pm2 list` shows "online")
- [ ] Dashboard accessible at http://your-ip:3000
- [ ] MT5 EA connected to sidecar
- [ ] WebSocket connection established
- [ ] Real-time data flowing

### 3. Risk Parameters Verified
- [ ] Max ES95 = $10.00 (configured)
- [ ] Max concurrent trades = 3 (configured)
- [ ] Daily loss limit = $50.00 (configured)
- [ ] Total loss limit = $100.00 (configured)
- [ ] Position sizing working correctly

### 4. Testing Completed
- [ ] Paper trading tested (if available)
- [ ] Signal generation working
- [ ] Trade execution tested
- [ ] Stop loss/take profit working
- [ ] Risk limits enforced

## How to Start Live Trading

### Step 1: Verify System Status

```bash
cd ~/Sandeep/projects/Vproptrader

# Check sidecar is running
pm2 list

# Check recent logs
pm2 logs sidecar --lines 50

# Verify MT5 connection
tail -f expertslog.txt
```

### Step 2: Enable Live Trading in MT5 EA

The MT5 EA has a safety switch. To enable live trading:

1. Open MT5 platform
2. Go to Expert Advisors tab
3. Find "QuantSupraAI" EA
4. Right-click → Properties
5. In Inputs tab, find `EnableLiveTrading`
6. Change from `false` to `true`
7. Click OK

**The EA will now execute real trades based on signals from the sidecar.**

### Step 3: Monitor Actively

Once live:

1. **Dashboard**: Monitor at http://your-ip:3000
2. **MT5 Terminal**: Watch the "Trade" tab
3. **Logs**: Keep `pm2 logs sidecar` running
4. **Alerts**: Set up notifications for:
   - New trades opened
   - Trades closed
   - Daily loss approaching limit
   - ES95 limit approached

### Step 4: First Hour Monitoring

**CRITICAL**: Stay at your computer for the first hour of live trading.

Watch for:
- ✅ Signals generated correctly
- ✅ Trades executed at expected prices
- ✅ Stop loss/take profit set correctly
- ✅ Position sizes within ES95 limits
- ✅ No unexpected errors

If anything looks wrong, **IMMEDIATELY**:
1. Set `EnableLiveTrading = false` in MT5 EA
2. Close any open positions manually
3. Review logs to identify the issue

## Risk Management Rules

### Daily Limits
- **Max Daily Loss**: $50.00
- **Action**: System stops trading for the day if hit
- **Manual Override**: Not recommended

### Total Limits  
- **Max Total Loss**: $100.00
- **Action**: System stops all trading if hit
- **Recovery**: Requires manual review and restart

### Position Limits
- **Max ES95 per trade**: $10.00
- **Max concurrent trades**: 3
- **Max holding time**: 48 hours

### Emergency Stop
If you need to stop trading immediately:

```bash
# Stop the sidecar
pm2 stop sidecar

# In MT5, disable AutoTrading (click the AutoTrading button)

# Manually close all open positions
```

## Expected Behavior

### Normal Trading Day
- System scans markets every hour
- Generates 0-3 signals per day (highly selective)
- Opens trades when high-quality signals found
- Manages trades automatically with SL/TP
- Closes trades when targets hit or time limit reached

### Performance Expectations
Based on backtest:
- **Win Rate**: ~32% (low but profitable)
- **Profit Factor**: ~2.93 (excellent)
- **Average Trade**: Small losses, occasional large wins
- **Monthly Return**: Variable, expect 10-20% in good months

### What's Normal
- ✅ Days with no trades (strict filtering)
- ✅ Multiple small losses in a row
- ✅ Occasional large winning trade
- ✅ Drawdowns of 5-10%
- ✅ Periods of no activity

### What's NOT Normal
- ❌ More than 10 trades per day
- ❌ Trades larger than $10 ES95
- ❌ Losses exceeding daily limit
- ❌ Trades held longer than 48 hours
- ❌ System errors or crashes

## Monitoring Commands

### Check System Health
```bash
# Sidecar status
pm2 status sidecar

# Recent activity
pm2 logs sidecar --lines 100

# Database check
sqlite3 sidecar/data/vproptrader.db "SELECT COUNT(*) FROM trades;"

# Current equity
sqlite3 sidecar/data/vproptrader.db "SELECT * FROM daily_performance ORDER BY date DESC LIMIT 1;"
```

### View Recent Trades
```bash
sqlite3 sidecar/data/vproptrader.db "SELECT * FROM trades ORDER BY entry_time DESC LIMIT 10;"
```

### Check Compliance
```bash
# Daily PnL
sqlite3 sidecar/data/vproptrader.db "SELECT date, total_pnl FROM daily_performance ORDER BY date DESC LIMIT 7;"
```

## Troubleshooting

### No Trades Being Taken
**Possible Causes**:
- Market conditions don't meet criteria (normal)
- MT5 EA not connected to sidecar
- `EnableLiveTrading` still set to false
- Risk limits already hit

**Check**:
```bash
pm2 logs sidecar | grep "signal"
```

### Trades Not Executing
**Possible Causes**:
- MT5 AutoTrading disabled
- Insufficient margin
- Symbol not available
- Network issues

**Check**:
- MT5 AutoTrading button is green
- Account has sufficient balance
- MT5 shows "Connected" to broker

### Unexpected Losses
**If losses exceed expectations**:
1. Stop trading immediately
2. Review trade history
3. Check if slippage was excessive
4. Verify stop losses were hit correctly
5. Contact support if needed

## Performance Tracking

### Daily Review
At end of each trading day, review:
- Total trades taken
- Win/loss ratio
- Total PnL
- Largest win/loss
- Any rule violations

### Weekly Review
Every week, analyze:
- Weekly PnL
- Cumulative return
- Drawdown levels
- Strategy performance by symbol
- Any adjustments needed

### Monthly Review
Every month, evaluate:
- Monthly return vs. target
- Risk-adjusted performance
- Strategy effectiveness
- System reliability
- Continue or adjust

## When to Stop Trading

**Stop immediately if**:
- Daily loss limit hit ($50)
- Total loss limit hit ($100)
- System behaving unexpectedly
- You don't understand what's happening
- Market conditions extremely volatile
- Technical issues occurring

**Consider stopping if**:
- Consecutive losing days (5+)
- Drawdown exceeds 15%
- Win rate drops below 20%
- System performance degrades
- You're uncomfortable with results

## Support & Resources

### Documentation
- `PRODUCTION_BACKTEST_RESULTS.md` - Backtest analysis
- `QUICK_START.md` - System setup guide
- `MT5_EA_COMPLETE_GUIDE.md` - EA documentation

### Logs Location
- Sidecar: `~/.pm2/logs/`
- MT5 EA: `Vproptrader/expertslog.txt`
- Database: `sidecar/data/vproptrader.db`

### Emergency Contacts
- Have broker support number ready
- Know how to manually close positions in MT5
- Keep this checklist accessible

## Final Checklist Before Going Live

- [ ] I have read and understood this entire document
- [ ] I have verified all prerequisites are met
- [ ] I understand the risks involved
- [ ] I am prepared to lose up to $100 (max loss limit)
- [ ] I will monitor actively for the first hour
- [ ] I know how to stop trading immediately if needed
- [ ] I have realistic expectations based on backtest results
- [ ] I am trading with money I can afford to lose

## Ready to Go Live?

If all checkboxes above are checked, you can proceed:

1. Start the sidecar: `pm2 start sidecar`
2. Open MT5 and load the EA
3. Enable `EnableLiveTrading = true`
4. Monitor closely

**Good luck, and trade responsibly!**

---

**Remember**: Past performance (backtest) does not guarantee future results. Live trading involves real financial risk.
