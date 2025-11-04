# How to Enable Live Trading on Windows MT5

## The Parameter Name is: EnableAutoTrading

**IMPORTANT:** The parameter is called `EnableAutoTrading`, NOT `EnableLiveTrading`

## Step-by-Step Visual Guide

### Step 1: Locate the EA on Your Chart
Look at the top-right corner of your MT5 chart. You should see:
```
QuantSupraAI
😊 (smiley face icon)
```

### Step 2: Access EA Properties
**Method A - Right-click the EA name:**
1. Right-click on "QuantSupraAI" text in the top-right corner
2. Select "Expert Advisor properties" or "Properties"

**Method B - Via Expert Advisors tab:**
1. Look at the bottom panel (Terminal window)
2. Click the "Expert Advisors" tab
3. Find "QuantSupraAI" in the list
4. Right-click → Properties

**Method C - Via Chart:**
1. Right-click anywhere on the chart
2. Select "Expert Advisors" → "Properties"

### Step 3: Find the Inputs Tab
In the Properties window that opens:
1. Click the **"Inputs"** tab (or "Input parameters")
2. Scroll through the list of parameters

### Step 4: Locate EnableAutoTrading
You'll see a list like this:
```
Parameter Name              | Value
----------------------------|-------
SidecarURL                  | http://127.0.0.1:8000
ScanInterval                | 60
MaxES95                     | 10.0
MaxConcurrentTrades         | 3
EnableAutoTrading           | false    ← THIS ONE!
EnableDebugMode             | false
TradingSymbols              | NAS100,XAUUSD,EURUSD
```

### Step 5: Change the Value
1. Click on the row with **`EnableAutoTrading`**
2. Double-click the "false" value (or click the dropdown)
3. Change it to **`true`**
4. Click **OK**

### Step 6: Verify It's Enabled
Look at the MT5 "Experts" tab (bottom panel):
- You should see: `Auto Trading: ENABLED`
- The EA will now execute real trades!

## What If I Don't See the EA?

### Check 1: Is the EA Attached to a Chart?
- Look for the smiley face 😊 icon in the top-right corner
- If not there, the EA is not running

### Check 2: Is AutoTrading Enabled in MT5?
- Look at the top toolbar
- Find the "AutoTrading" button (looks like a play button or traffic light)
- It should be GREEN
- If it's RED, click it to enable

### Check 3: Are EAs Allowed?
1. Go to **Tools → Options**
2. Click **Expert Advisors** tab
3. Make sure these are checked:
   - ✅ Allow automated trading
   - ✅ Allow DLL imports
   - ✅ Allow WebRequest for listed URL

## Troubleshooting

### "I don't see QuantSupraAI anywhere"
The EA is not installed. You need to:
1. Copy the EA files to your Windows MT5
2. Compile the EA
3. Attach it to a chart

See: `MT5_EA_COMPLETE_GUIDE.md` for installation instructions

### "I see the EA but no Properties option"
Try this:
1. Remove the EA from the chart (right-click → Expert Advisors → Remove)
2. Open Navigator (Ctrl+N)
3. Expand "Expert Advisors"
4. Drag "QuantSupraAI" onto a chart
5. The setup dialog will appear immediately
6. Change `EnableAutoTrading` to `true` before clicking OK

### "The parameter list is empty"
The EA didn't compile correctly. You need to:
1. Open MetaEditor (F4)
2. Open QuantSupraAI.mq5
3. Compile it (F7)
4. Fix any errors
5. Try attaching it again

## Quick Reference

| What You're Looking For | Actual Name |
|------------------------|-------------|
| ❌ EnableLiveTrading | ✅ EnableAutoTrading |
| ❌ LiveTrading | ✅ EnableAutoTrading |
| ❌ GoLive | ✅ EnableAutoTrading |

## After Enabling

Once you set `EnableAutoTrading = true`:
- The EA will scan markets every 60 seconds
- It will fetch signals from your sidecar (http://127.0.0.1:8000)
- It will execute trades automatically when high-quality signals are found
- You'll see trade activity in the "Trade" and "History" tabs

## Safety Note

⚠️ **This will execute REAL trades with REAL money!**

Make sure:
- Your sidecar is running and generating good signals
- You've tested on a demo account first
- You understand the risk parameters (MaxES95, MaxConcurrentTrades)
- You're monitoring the system actively

---

**Need help?** Check the MT5 "Experts" tab for log messages from the EA.
