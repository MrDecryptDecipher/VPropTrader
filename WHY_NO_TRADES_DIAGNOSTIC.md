# Why EA Is Not Trading - Diagnostic

## Current Status

**Time:** 12:32 PM IST = 07:02 UTC  
**Session:** London (07:00-10:00 UTC) ✅  
**EA Status:** Initialized ✅  
**Sidecar:** Generating signals ✅  
**Problem:** No trades executing ❌

## Possible Causes

### 1. EA Not Receiving Ticks

The EA only runs on price ticks. If the market is slow or the chart timeframe is H1 (1 hour), ticks may be infrequent.

**Solution:** Change chart to M1 (1 minute) or M5 (5 minutes) for more frequent ticks.

### 2. AutoTrading Disabled in MT5

The MT5 "AutoTrading" button must be GREEN.

**Check:**
- Look at MT5 toolbar
- Find button that looks like a traffic light or play button
- If RED, click it to turn GREEN

### 3. Chart Symbol Mismatch

The EA is attached to XAUUSD chart, but signals might be for other symbols.

**Check:**
- EA logs show: `Symbols: NAS100,XAUUSD,EURUSD`
- Your chart: `XAUUSD.w,H1`
- The `.w` suffix might cause issues

### 4. No Verbose Logging

The EA has `VerboseLogging = true` but we're not seeing tick messages.

**This suggests:** OnTick() might not be running at all.

### 5. Time-Based Close Active

The EA checks `ShouldCloseAllPositions()` which returns true after 21:45 UTC.

**Current time:** 07:02 UTC - Should be OK ✅

## Immediate Actions

### Action 1: Enable AutoTrading
1. Look at MT5 top toolbar
2. Find "AutoTrading" button
3. Click it until it turns GREEN
4. You should hear a beep

### Action 2: Change to M1 Chart
1. Right-click on chart
2. Select "Timeframes" → "M1"
3. This will generate more ticks

### Action 3: Check Experts Tab
Look for these messages (should appear every 60 seconds):
```
Status - Enabled: true | Daily PnL: $0.00 | Total PnL: $0.00 | Trades Today: 0
```

If you DON'T see this, the EA is not running.

### Action 4: Restart EA
1. Remove EA from chart (right-click → Expert Advisors → Remove)
2. Drag it back from Navigator
3. In setup dialog:
   - Set `LogOnlyMode` = **false**
   - Set `VerboseLogging` = **true**
4. Click OK

## What You Should See

Once working, you'll see:
```
Status - Enabled: true | Daily PnL: $0.00
Received 2 signal(s) from Sidecar
Processing signal: NAS100 SELL Q*=10.0 Lots=6.27
Opening position: NAS100 SELL 6.27 lots
Position opened successfully: Ticket #12345
```

## Debug Steps

### Step 1: Verify EA is Running
Look for this in Experts tab every 60 seconds:
```
Status - Enabled: true
```

If NOT appearing → EA's OnTick() is not running

### Step 2: Check AutoTrading
- Toolbar button must be GREEN
- If RED, EA cannot trade

### Step 3: Generate Ticks
- Switch to M1 chart
- Or click on chart to force a tick

### Step 4: Check Logs
After 2-3 minutes, you should see:
- Status messages
- Signal polling attempts
- Either "No signals" or "Received X signals"

## Most Likely Issue

Based on your logs showing only initialization and no tick activity:

**The AutoTrading button is probably RED (disabled)**

This is the #1 reason EAs don't trade after initialization.

## Quick Test

In MT5, press **F1** to open help, then close it. This generates a tick and should trigger OnTick().

Watch the Experts tab - do you see any new messages?

- **YES** → EA is working, just waiting for good signals
- **NO** → AutoTrading is disabled or EA has an issue

## Next Steps

1. **Check AutoTrading button** (most likely cause)
2. **Switch to M1 chart** (more ticks)
3. **Wait 2-3 minutes** and watch for status messages
4. **If still nothing**, restart the EA

Let me know what you see in the Experts tab after trying these steps!
