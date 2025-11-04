"""
VPropTrader - Windows MT5 Auto Trader
Polls sidecar for signals and executes trades automatically in MT5
"""

import MetaTrader5 as mt5
import requests
import time
from datetime import datetime
import json

# Configuration
SIDECAR_URL = "http://3.111.22.56:8002"
POLL_INTERVAL = 2  # seconds
MIN_CONFIDENCE = 0.75  # Only trade signals above this confidence
MAX_CONCURRENT_TRADES = 3
MAGIC_NUMBER = 20251025

# Colors for console output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(message, color=None):
    """Print colored log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if color:
        print(f"{color}[{timestamp}] {message}{Colors.END}")
    else:
        print(f"[{timestamp}] {message}")

def initialize_mt5():
    """Initialize MT5 connection"""
    log("Initializing MT5 connection...", Colors.BLUE)
    
    if not mt5.initialize():
        log(f"MT5 initialization failed: {mt5.last_error()}", Colors.RED)
        return False
    
    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        log("Failed to get account info", Colors.RED)
        return False
    
    log(f"✓ Connected to MT5", Colors.GREEN)
    log(f"  Account: {account_info.login}")
    log(f"  Balance: ${account_info.balance:.2f}")
    log(f"  Equity: ${account_info.equity:.2f}")
    log(f"  Server: {account_info.server}")
    
    return True

def get_signals():
    """Fetch signals from sidecar"""
    try:
        equity = mt5.account_info().equity
        response = requests.get(
            f"{SIDECAR_URL}/api/signals",
            params={"equity": equity},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('signals', [])
        else:
            log(f"Failed to get signals: HTTP {response.status_code}", Colors.RED)
            return []
            
    except requests.exceptions.RequestException as e:
        log(f"Error fetching signals: {e}", Colors.RED)
        return []

def get_open_positions():
    """Get currently open positions"""
    positions = mt5.positions_get()
    if positions is None:
        return []
    return [p for p in positions if p.magic == MAGIC_NUMBER]

def symbol_has_position(symbol):
    """Check if we already have a position for this symbol"""
    positions = get_open_positions()
    return any(p.symbol == symbol for p in positions)

def execute_trade(signal):
    """Execute a trade based on signal"""
    symbol = signal['symbol']
    action = signal['action']
    lots = signal['lots']
    sl = signal['stop_loss']
    tp = signal['take_profit_1']
    confidence = signal['confidence']
    
    # Check if symbol exists
    if not mt5.symbol_select(symbol, True):
        log(f"Symbol {symbol} not available", Colors.RED)
        return False
    
    # Get symbol info
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        log(f"Failed to get {symbol} info", Colors.RED)
        return False
    
    # Check if trading is allowed
    if not symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
        log(f"Trading not allowed for {symbol}", Colors.YELLOW)
        return False
    
    # Prepare request
    order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if action == "BUY" else mt5.symbol_info_tick(symbol).bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lots,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": MAGIC_NUMBER,
        "comment": f"VPropTrader Q*={signal.get('q_star', 0):.1f}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # Send order
    log(f"Opening {action} position: {symbol} {lots} lots (Confidence: {confidence:.2f})", Colors.BLUE)
    log(f"  Price: {price:.5f} | SL: {sl:.5f} | TP: {tp:.5f}")
    
    result = mt5.order_send(request)
    
    if result is None:
        log(f"Order failed: {mt5.last_error()}", Colors.RED)
        return False
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log(f"Order failed: {result.comment} (code: {result.retcode})", Colors.RED)
        return False
    
    log(f"✓ Position opened successfully: Ticket #{result.order}", Colors.GREEN)
    log(f"  Fill Price: {result.price:.5f}")
    log(f"  Volume: {result.volume} lots")
    
    return True

def monitor_positions():
    """Monitor and log open positions"""
    positions = get_open_positions()
    
    if not positions:
        return
    
    total_profit = sum(p.profit for p in positions)
    
    log(f"Open Positions: {len(positions)} | Total P&L: ${total_profit:.2f}", 
        Colors.GREEN if total_profit >= 0 else Colors.RED)
    
    for pos in positions:
        pnl_color = Colors.GREEN if pos.profit >= 0 else Colors.RED
        log(f"  {pos.symbol} {pos.type_str} {pos.volume} lots | "
            f"P&L: ${pos.profit:.2f} | Ticket: {pos.ticket}", pnl_color)

def main():
    """Main trading loop"""
    log("=" * 60, Colors.BLUE)
    log("VPropTrader - Windows MT5 Auto Trader", Colors.BLUE)
    log("=" * 60, Colors.BLUE)
    
    # Initialize MT5
    if not initialize_mt5():
        log("Failed to initialize MT5. Exiting.", Colors.RED)
        return
    
    log(f"Sidecar URL: {SIDECAR_URL}", Colors.BLUE)
    log(f"Poll Interval: {POLL_INTERVAL}s", Colors.BLUE)
    log(f"Min Confidence: {MIN_CONFIDENCE}", Colors.BLUE)
    log(f"Max Concurrent Trades: {MAX_CONCURRENT_TRADES}", Colors.BLUE)
    log("=" * 60, Colors.BLUE)
    log("Auto-trading started. Press Ctrl+C to stop.", Colors.GREEN)
    log("=" * 60, Colors.BLUE)
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            # Monitor existing positions
            if iteration % 10 == 0:  # Every 20 seconds
                monitor_positions()
            
            # Check if we can take more positions
            open_positions = get_open_positions()
            if len(open_positions) >= MAX_CONCURRENT_TRADES:
                log(f"Max concurrent trades reached ({MAX_CONCURRENT_TRADES}). Waiting...", Colors.YELLOW)
                time.sleep(POLL_INTERVAL)
                continue
            
            # Get signals from sidecar
            signals = get_signals()
            
            if not signals:
                if iteration % 30 == 0:  # Log every minute
                    log("No signals available. Waiting...", Colors.YELLOW)
                time.sleep(POLL_INTERVAL)
                continue
            
            # Process signals
            log(f"Received {len(signals)} signal(s) from sidecar", Colors.BLUE)
            
            for signal in signals:
                # Check confidence
                if signal['confidence'] < MIN_CONFIDENCE:
                    log(f"Skipping {signal['symbol']} - Low confidence: {signal['confidence']:.2f}", Colors.YELLOW)
                    continue
                
                # Check if we already have a position for this symbol
                if symbol_has_position(signal['symbol']):
                    log(f"Skipping {signal['symbol']} - Already have position", Colors.YELLOW)
                    continue
                
                # Check if we can take more positions
                if len(get_open_positions()) >= MAX_CONCURRENT_TRADES:
                    log("Max concurrent trades reached. Skipping remaining signals.", Colors.YELLOW)
                    break
                
                # Execute trade
                execute_trade(signal)
                
                # Small delay between trades
                time.sleep(1)
            
            # Wait before next poll
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        log("\nShutting down auto-trader...", Colors.YELLOW)
        monitor_positions()
        log("Auto-trader stopped.", Colors.BLUE)
    
    finally:
        mt5.shutdown()
        log("MT5 connection closed.", Colors.BLUE)

if __name__ == "__main__":
    main()
