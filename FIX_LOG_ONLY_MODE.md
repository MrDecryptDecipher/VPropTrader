# Fix: EA Stuck in "Log Only Mode"

## Problem
You can see the EA is in "log only mode" but you can't edit the `EnableAutoTrading` parameter because the EA is already running.

## Solution: Remove and Re-attach the EA

### Step 1: Remove the EA from the Chart
1. Look at the top-right corner of your chart where you see "QuantSupraAI"
2. **Right-click on the EA name** (or right-click on the chart)
3. Select **"Expert Advisors" → "Remove"**
4. The EA will disappear from the chart

### Step 2: Re-attach the EA with New Settings
1. Press **Ctrl+N** to open the Navigator panel (or View → Navigator)
2. Expand the **"Expert Advisors"** folder
3. Find **"QuantSupraAI"** in the list
4. **Drag it onto your chart** (any chart, any symbol)
5. A setup dialog will appear immediately

### Step 3: Change EnableAutoTrading BEFORE Clicking OK
In the setup dialog that appears:
1. Click the **"Inputs"** tab
2. Find **`EnableAutoTrading`** in the list
3. Change it from **`false`** to **`true`**
4. **Now click OK**

### Step 4: Verify It's Enabled
Look at the MT5 "Experts" tab (bottom panel):
- You should now see: **"Auto Trading: ENABLED"**
- The EA will start executing real trades!

## Alternative Method: Use a .set File

If you want to save these settings permanently:

### Create a Settings File
1. When the setup dialog appears (Step 2 above)
2. Change `EnableAutoTrading` to `true`
3. Click **"Save"** button (not OK yet)
4. Save it as: `QuantSupraAI_LIVE.set`
5. Now click **OK**

### Load Settings File Later
Next time you attach the EA:
1. Drag EA onto chart
2. Click **"Load"** button
3. Select `QuantSupraAI_LIVE.set`
4. Click **OK**

## Quick Checklist

Before you click OK, make sure:
- ✅ `EnableAutoTrading` = **true**
- ✅ `SidecarURL` = **http://127.0.0.1:8000** (or your server IP)
- ✅ `MaxES95` = **10.0** (or your risk preference)
- ✅ `MaxConcurrentTrades` = **3** (or your preference)
- ✅ `TradingSymbols` = **NAS100,XAUUSD,EURUSD** (or your symbols)

## What You'll See After Enabling

In the "Experts" tab, you should see:
```
QuantSupraAI EA Starting...
✅ Connected to sidecar successfully
✅ Symbol NAS100 ready for trading
✅ Symbol XAUUSD ready for trading
✅ Symbol EURUSD ready for trading
QuantSupraAI EA initialized successfully
Auto Trading: ENABLED    ← This confirms it's live!
Debug Mode: DISABLED
Scan Interval: 60 seconds
Max ES95: $10.0
Max Concurrent Trades: 3
```

## Troubleshooting

### "I removed the EA but can't find it in Navigator"
1. Press **F4** to open MetaEditor
2. Find `QuantSupraAI.mq5` in the Navigator (left panel)
3. Right-click → **Compile**
4. Close MetaEditor
5. Back in MT5, press **Ctrl+N** to refresh Navigator
6. The EA should now appear

### "The setup dialog doesn't appear when I drag it"
The EA might be set to use saved settings:
1. Go to **Tools → Options**
2. Click **Expert Advisors** tab
3. Uncheck **"Use saved settings"** (if checked)
4. Try dragging the EA again

### "I changed it to true but it still says log only mode"
Check the MT5 toolbar:
1. Look for the **"AutoTrading"** button (looks like a traffic light or play button)
2. Make sure it's **GREEN** (not red)
3. If it's red, click it to enable
4. Remove and re-attach the EA

## Safety Reminder

⚠️ **Once you set `EnableAutoTrading = true`, the EA will execute REAL trades!**

Make sure:
- Your sidecar is running and generating signals
- You've tested on demo first
- You understand the risk parameters
- You're ready to monitor the system

---

**Current Status:** Log only mode = Safe (no trades executed)
**After Change:** Live trading mode = Real trades will be executed!
