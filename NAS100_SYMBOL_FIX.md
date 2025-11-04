# NAS100 Symbol Issue - Quick Fix

## Problem
```
Invalid lot size: 0.63 (min: 0.0, max: 0.0)
Signal validation failed for NAS100
```

This means MT5 can't find symbol specifications for "NAS100". Your broker likely uses a different name.

## Solution: Find the Correct Symbol Name

### Step 1: Check Market Watch in MT5

1. **Open Market Watch** (Ctrl+M or View → Market Watch)
2. **Right-click** → Select "Show All"
3. **Search for NASDAQ symbols:**
   - Look for: `NAS100`, `US100`, `USTEC`, `NAS100.cash`, `NDX`, `NASDAQ`
   - Common broker names:
     - **IC Markets:** `NAS100` or `US100`
     - **FTMO:** `NAS100`
     - **Pepperstone:** `USTEC` or `US100`
     - **Fusion Markets:** `NAS100.cash`
     - **Exness:** `USTEC`

4. **Note the EXACT symbol name** your broker uses

### Step 2: Update config.mqh

Once you find the correct symbol name, update the config file:

**On Windows MT5:**
1. Open MetaEditor (F4)
2. Navigate to: `Experts → QuantSupraAI → config.mqh`
3. Find this line:
   ```mql5
   input string TradingSymbols = "NAS100,XAUUSD,EURUSD";
   ```
4. Replace `NAS100` with your broker's symbol name:
   ```mql5
   input string TradingSymbols = "US100,XAUUSD,EURUSD";  // Example
   ```
5. Save and recompile (F7)
6. Restart MT5 and reattach EA

### Step 3: Alternative - Change EA Input

You can also change it without editing code:

1. **Remove EA from chart**
2. **Drag EA back onto chart**
3. **In the Inputs tab**, find "TradingSymbols"
4. **Change** `NAS100,XAUUSD,EURUSD` to use your broker's symbol
5. **Click OK**

## Common Symbol Names by Broker

| Broker | NASDAQ Symbol | Gold Symbol | EUR/USD |
|--------|---------------|-------------|---------|
| IC Markets | US100 | XAUUSD | EURUSD |
| FTMO | NAS100 | XAUUSD | EURUSD |
| Pepperstone | USTEC | XAUUSD | EURUSD |
| Fusion Markets | NAS100.cash | XAUUSD | EURUSD |
| Exness | USTEC | XAUUSD | EURUSD |
| FBS | US100 | XAUUSD | EURUSD |

## How to Test

After updating the symbol name:

1. **Check the log** - should see:
   ```
   Processing signal: US100 SELL Q*=10.0 Lots=0.63
   ✓ Trade executed: Ticket #12345
   ```

2. **If still failing**, the symbol might not be enabled:
   - Right-click symbol in Market Watch
   - Select "Specification"
   - Check "Trade Mode" - should be "Full Access" or "Close Only"

## Quick Diagnostic

Run this in MT5 Script to check available symbols:

```mql5
//+------------------------------------------------------------------+
//| Script to find NASDAQ symbol                                     |
//+------------------------------------------------------------------+
void OnStart()
{
    Print("=== Searching for NASDAQ symbols ===");
    
    string symbols[] = {"NAS100", "US100", "USTEC", "NAS100.cash", "NDX", "NASDAQ"};
    
    for(int i = 0; i < ArraySize(symbols); i++)
    {
        if(SymbolSelect(symbols[i], true))
        {
            double minLot = SymbolInfoDouble(symbols[i], SYMBOL_VOLUME_MIN);
            double maxLot = SymbolInfoDouble(symbols[i], SYMBOL_VOLUME_MAX);
            double lotStep = SymbolInfoDouble(symbols[i], SYMBOL_VOLUME_STEP);
            
            Print("✓ FOUND: ", symbols[i]);
            Print("  Min Lot: ", minLot);
            Print("  Max Lot: ", maxLot);
            Print("  Lot Step: ", lotStep);
        }
        else
        {
            Print("✗ NOT FOUND: ", symbols[i]);
        }
    }
}
```

Save this as `FindNASDAQ.mq5` in Scripts folder, compile, and run it.

## After Fix

Once you use the correct symbol name, the EA will:
1. Validate lot sizes correctly
2. Execute trades successfully
3. Start making money! 💰

## Need Help?

If you can't find the NASDAQ symbol:
1. Contact your broker support
2. Check their symbol list on their website
3. Or just trade XAUUSD and EURUSD for now (remove NAS100 from the list)
