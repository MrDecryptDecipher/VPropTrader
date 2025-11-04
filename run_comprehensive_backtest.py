#!/usr/bin/env python3
"""
Complete Comprehensive Backtesting System
Tests the VPropTrader system with real historical data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sidecar'))

from datetime import datetime, timedelta
import pandas as pd
import json
from loguru import logger

from app.backtest.engine import BacktestEngine, BacktestConfig


def main():
    """Run comprehensive backtest"""
    
    print("\n" + "="*80)
    print("VPROPTRADER COMPREHENSIVE BACKTEST")
    print("="*80)
    
    # Configure backtest
    config = BacktestConfig(
        initial_capital=1000.0,
        symbols=['NAS100', 'XAUUSD', 'EURUSD'],
        max_concurrent_trades=3,
        max_es95=10.0,
        min_q_star=3.0,
        walk_forward=False  # Simple backtest first
    )
    
    print(f"\nConfiguration:")
    print(f"  Initial Capital: ${config.initial_capital}")
    print(f"  Symbols: {config.symbols}")
    print(f"  Max Concurrent Trades: {config.max_concurrent_trades}")
    print(f"  Max ES95: ${config.max_es95}")
    print(f"  Min Q*: {config.min_q_star}")
    
    # Create engine
    engine = BacktestEngine(config)
    
    # Run backtest
    print("\n🚀 Starting backtest...")
    results = engine.run()
    
    if 'error' in results:
        print(f"\n❌ Backtest failed: {results['error']}")
        return
    
    # Print results
    print_results(results)
    
    # Save results
    save_results(results)
    
    print("\n✅ Backtest complete!")


def print_results(results: dict):
    """Print comprehensive results"""
    
    metrics = results.get('metrics', {})
    
    print("\n" + "="*80)
    print("BACKTEST RESULTS")
    print("="*80)
    
    # Summary
    print(f"\n📊 SUMMARY")
    print(f"{'─'*50}")
    print(f"Total Trades:       {metrics.get('total_trades', 0)}")
    print(f"Winning Trades:     {metrics.get('winning_trades', 0)}")
    print(f"Losing Trades:      {metrics.get('losing_trades', 0)}")
    print(f"Win Rate:           {metrics.get('win_rate', 0):.1f}%")
    print(f"Total PnL:          ${metrics.get('total_pnl', 0):.2f}")
    print(f"Final Equity:       ${metrics.get('final_equity', 0):.2f}")
    print(f"Total Return:       {metrics.get('total_return_pct', 0):.2f}%")
    
    # Risk Metrics
    risk = metrics.get('risk_metrics', {})
    if risk:
        print(f"\n📈 RISK METRICS")
        print(f"{'─'*50}")
        print(f"Sharpe Ratio:       {risk.get('sharpe_ratio', 0):.2f}")
        print(f"Sortino Ratio:      {risk.get('sortino_ratio', 0):.2f}")
        print(f"Profit Factor:      {risk.get('profit_factor', 0):.2f}")
        print(f"Average Win:        ${risk.get('avg_win', 0):.2f}")
        print(f"Average Loss:       ${risk.get('avg_loss', 0):.2f}")
    
    # Drawdown
    dd = metrics.get('drawdown', {})
    if dd:
        print(f"\n📉 DRAWDOWN")
        print(f"{'─'*50}")
        print(f"Max Drawdown:       ${dd.get('max_drawdown', 0):.2f}")
        print(f"Max DD %:           {dd.get('max_drawdown_pct', 0):.2f}%")
    
    # By Symbol
    by_symbol = results.get('by_symbol', {})
    if by_symbol:
        print(f"\n🎯 PERFORMANCE BY SYMBOL")
        print(f"{'─'*50}")
        for symbol, stats in by_symbol.items():
            print(f"{symbol}: {stats}")
    
    # By Alpha
    by_alpha = results.get('by_alpha', {})
    if by_alpha:
        print(f"\n🧠 PERFORMANCE BY ALPHA")
        print(f"{'─'*50}")
        for alpha_id, stats in by_alpha.items():
            print(f"{alpha_id}: {stats}")


def save_results(results: dict):
    """Save results to file"""
    
    # Convert to JSON-serializable format
    output = {
        'timestamp': datetime.now().isoformat(),
        'metrics': results.get('metrics', {}),
        'trade_count': len(results.get('trades', []))
    }
    
    # Convert nested dict keys to strings
    def convert_keys(obj):
        if isinstance(obj, dict):
            return {str(k): convert_keys(v) for k, v in obj.items()}
        return obj
    
    output['by_symbol'] = convert_keys(results.get('by_symbol', {}))
    output['by_alpha'] = convert_keys(results.get('by_alpha', {}))
    output['by_session'] = convert_keys(results.get('by_session', {}))
    
    filename = 'backtest_results.json'
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n📁 Results saved to: {filename}")


if __name__ == "__main__":
    main()
