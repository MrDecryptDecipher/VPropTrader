import MetaTrader5 as mt5
import pandas as pd

def main():
    print("Initializing MT5...")
    if not mt5.initialize():
        print(f"❌ Initialize failed, error code = {mt5.last_error()}")
        return

    print("✅ MT5 Initialized")
    
    # Get all symbols
    symbols = mt5.symbols_get()
    if symbols is None:
        print("❌ No symbols found.")
    else:
        print(f"✅ Found {len(symbols)} symbols.")
        print("First 20 symbols:")
        for s in symbols[:20]:
            print(f" - {s.name}")
            
        # Check specifically for common pairs with wildcards
        print("\nSearching for EURUSD variants...")
        eurusd = mt5.symbols_get(group="*EURUSD*")
        if eurusd:
            for s in eurusd:
                print(f" - Found: {s.name}")
        else:
            print("❌ No EURUSD variants found.")

    mt5.shutdown()

if __name__ == "__main__":
    main()
