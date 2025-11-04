# Symbol Fix Complete - US100.e

## Changes Made

### 1. Updated EA Config (Ubuntu)
**File:** `Vproptrader/mt5_ea/config.mqh`
**Change:** `NAS100` → `US100.e`

```mql5
input string TradingSymbols = "US100.e,XAUUSD,EURUSD";
```

### 2. Updated Symbol Mapper (Sidecar)
**File:** `Vproptrader/sidecar/app/data/symbol_mapper.py`
**Added mappings for US100.e:**
- Yahoo Finance: `NQ=F`
- Twelve Data: `NAS100`
- Alpha Vantage: `NDX`
- Polygon: `I:NDX`
- Alternatives: `['NDX', '^NDX', 'NQ=F', 'NDAQ']`

## Next Steps

### On Windows MT5:

1. **Copy updated config.mqh:**
   - From Ubuntu: `/home/ubuntu/Vproptrader/mt5_ea/config.mqh`
   - To Windows: `C:\Users\Superagent\AppData\Roaming\MetaQuotes\Terminal\[BrokerID]\MQL5\Experts\config.mqh`

2. **Recompile EA:**
   - Open MetaEditor (F4)
   - Open QuantSupraAI.mq5
   - Press F7 to compile
   - Should show "0 errors"

3. **Restart MT5:**
   - Close MT5 completely
   - Reopen MT5

4. **Reattach EA:**
   - Drag QuantSupraAI onto chart
   - Verify in Inputs tab: `TradingSymbols = "US100.e,XAUUSD,EURUSD"`
   - Click OK

### On Ubuntu (Sidecar):

**Restart sidecar to load new symbol mappings:**

```bash
cd ~/Vproptrader
pm2 restart sidecar
pm2 logs sidecar --lines 50
```

## Expected Result

After these changes, you should see in MT5 log:

```
Received 2 signal(s) from Sidecar
Processing signal: US100.e SELL Q*=10.0 Lots=0.63
✓ Trade executed: Ticket #12345
```

## Verification

Check that US100.e is working:

1. **In MT5 Market Watch:**
   - Right-click US100.e
   - Select "Specification"
   - Verify:
     - Min Lot: 0.01 (or similar)
     - Max Lot: 100+ (or similar)
     - Lot Step: 0.01

2. **In EA Log:**
   - Should NO LONGER see: "Invalid lot size: 0.63 (min: 0.0, max: 0.0)"
   - Should see: "✓ Trade executed"

## Alternative: Quick Test Without Recompiling

If you want to test immediately without copying files:

1. **Remove EA from chart**
2. **Drag EA back onto chart**
3. **In Inputs tab, manually change:**
   - `TradingSymbols` from `NAS100,XAUUSD,EURUSD`
   - To: `US100.e,XAUUSD,EURUSD`
4. **Click OK**

This will work for testing, but you'll need to do it every time you reattach the EA.

## Symbol Naming Convention

Your broker uses `.e` suffix for ECN pricing:
- **US100.e** = NASDAQ 100 with ECN pricing (tighter spreads)
- **XAUUSD** = Gold vs USD (standard)
- **EURUSD** = Euro vs USD (standard)

ECN symbols typically have:
- Lower spreads
- Better execution
- Commission-based pricing

## Troubleshooting

If trades still fail after this fix:

1. **Check symbol is enabled:**
   - Market Watch → Right-click US100.e → "Show"

2. **Check trading is allowed:**
   - Tools → Options → Expert Advisors
   - ✓ "Allow automated trading"
   - ✓ "Allow DLL imports"

3. **Check account permissions:**
   - Some demo accounts restrict certain symbols
   - Contact broker if US100.e shows "Trade disabled"

4. **Check lot size:**
   - Right-click US100.e → Specification
   - Note the Min/Max lot sizes
   - EA should auto-calculate within these limits

## Status

✅ EA config updated (Ubuntu)
✅ Symbol mapper updated (Ubuntu)
⏳ Waiting for Windows MT5 update
⏳ Waiting for sidecar restart

Once you complete the Windows steps and restart the sidecar, the system will be fully operational!
