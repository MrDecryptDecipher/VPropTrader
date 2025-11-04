# EA Timer Fix - Critical Update

## Problem
The EA was using `OnTick()` which only fires on price changes. On H1 charts or slow markets, this means the EA wasn't polling the sidecar regularly.

## Solution
Changed to use `OnTimer()` with `EventSetTimer()` to poll every 1.5 seconds regardless of price ticks.

## How to Apply the Fix

### On Windows (MT5):

1. **Open MetaEditor**
   - In MT5, press F4 or go to Tools → MetaQuick Language Editor

2. **Open the EA file**
   - In MetaEditor Navigator, find: `Experts → QuantSupraAI.mq5`
   - Double-click to open it

3. **Compile the EA**
   - Press F7 or click the "Compile" button
   - Check the "Errors" tab at the bottom - should show "0 error(s), 0 warning(s)"

4. **Restart MT5**
   - Close MT5 completely
   - Reopen MT5

5. **Reattach the EA**
   - Drag `QuantSupraAI` from Navigator onto your chart
   - Make sure AutoTrading is enabled (green button)

6. **Verify it's working**
   - Check the Experts tab
   - You should now see logs every 1.5 seconds like:
     ```
     Polling Sidecar for signals...
     Received X signal(s) from Sidecar
     ```

## What Changed

### Before:
- EA only checked for signals when price ticked
- On H1 charts, could wait hours between checks
- No regular polling

### After:
- EA polls sidecar every 1.5 seconds via timer
- Independent of price ticks
- Consistent signal checking
- OnTick() still monitors positions for quick SL/TP updates

## Expected Behavior After Fix

You should see in the Experts log:
```
✓ Timer set to 1 seconds
EA Initialization Complete - Ready to Trade
[Every 1.5 seconds:]
Received 2 signal(s) from Sidecar
Processing signal: NAS100 BUY Q*=10.0 Lots=0.63
✓ Trade executed: Ticket #12345
```

The EA will now actively trade!
