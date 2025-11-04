# Copy These 2 Files to Windows MT5

## Files Updated on Ubuntu (Ready to Copy)

✅ **QuantSupraAI.mq5** - Main EA with timer fix
✅ **config.mqh** - Config with US100.e symbol
✅ **symbol_mapper.py** - Sidecar mapping (already restarted)

## What to Copy

### File 1: QuantSupraAI.mq5
**From Ubuntu:**
```
/home/ubuntu/Vproptrader/mt5_ea/QuantSupraAI.mq5
```

**To Windows:**
```
C:\Users\Superagent\AppData\Roaming\MetaQuotes\Terminal\[BrokerID]\MQL5\Experts\QuantSupraAI.mq5
```

### File 2: config.mqh
**From Ubuntu:**
```
/home/ubuntu/Vproptrader/mt5_ea/config.mqh
```

**To Windows:**
```
C:\Users\Superagent\AppData\Roaming\MetaQuotes\Terminal\[BrokerID]\MQL5\Experts\config.mqh
```

## How to Copy

### Option A: WinSCP (Recommended)
1. Download WinSCP: https://winscp.net/eng/download.php
2. Connect to: `3.111.22.56` with your SSH key
3. Navigate to: `/home/ubuntu/Vproptrader/mt5_ea/`
4. Download both files to your desktop
5. Copy them to the MT5 Experts folder

### Option B: Manual Copy/Paste
1. **On Ubuntu**, read each file:
   ```bash
   cat ~/Vproptrader/mt5_ea/QuantSupraAI.mq5
   cat ~/Vproptrader/mt5_ea/config.mqh
   ```
2. **Copy the content**
3. **On Windows**, open Notepad
4. **Paste and save** to the MT5 Experts folder

## After Copying

1. **Open MetaEditor** (F4 in MT5)
2. **Open QuantSupraAI.mq5**
3. **Compile** (F7) - should show "0 errors"
4. **Close MT5 completely**
5. **Reopen MT5**
6. **Drag EA onto chart**
7. **Verify settings:**
   - Sidecar URL: `http://3.111.22.56:8002`
   - Trading Symbols: `US100.e,XAUUSD,EURUSD`
   - Log-Only Mode: `false`
8. **Click OK**

## What You'll See

### Initialization:
```
=== Quant Ω Supra AI Expert Advisor ===
Version: 1.00
Sidecar URL: http://3.111.22.56:8002
Poll Interval: 1500 ms
Log-Only Mode: NO
Symbols: US100.e,XAUUSD,EURUSD
✓ Timer set to 1 seconds
EA Initialization Complete - Ready to Trade
```

### Trading:
```
Received 2 signal(s) from Sidecar
Processing signal: US100.e SELL Q*=10.0 Lots=0.63
✓ Trade executed: Ticket #12345
✓ Execution reported to Sidecar
```

## Quick Alternative (No File Copy)

If you can't copy files right now:

1. **Remove EA from chart**
2. **Drag EA back on**
3. **In Inputs tab**, manually change:
   - `TradingSymbols` to: `US100.e,XAUUSD,EURUSD`
4. **Click OK**

This will work temporarily, but you'll need to do it every time you reattach the EA.

## Verification Checklist

After copying and recompiling:

- [ ] EA shows "✓ Timer set to 1 seconds" in log
- [ ] EA shows "Symbols: US100.e,XAUUSD,EURUSD" in log
- [ ] EA polls every 1-2 seconds
- [ ] No more "Invalid lot size" errors
- [ ] Trades execute successfully
- [ ] Positions appear in Terminal tab

## Status

| Component | Status |
|-----------|--------|
| Ubuntu EA files | ✅ Updated |
| Ubuntu sidecar | ✅ Restarted |
| Windows EA files | ⏳ Needs copy |
| Windows compilation | ⏳ After copy |
| Live trading | ⏳ After compilation |

Once you copy these 2 files and recompile, you're done! The system will start trading immediately.
