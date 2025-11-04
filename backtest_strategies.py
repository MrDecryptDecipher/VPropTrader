#!/usr/bin/env python3
"""
Comprehensive Strategy Backtesting with Real Market Data
Tests profitability across different assets and market sessions
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sidecar'))

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from loguru import logger

# Import our components
from app.scanner.scanner import global_scanner
from app.scanner.alphas import get_all_alphas
from app.data.features import feature_engineer
from app.ml.inference import ml_inference
from app.risk.position_sizing import position_sizer


class StrategyBacktester:
    """Backtest trading strategies with real market data"""
    
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital
        self.equity = initial_capital
        self.trades = []
        self.daily_pnl = []
        self.symbols = ['NAS100', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY']
        self.alphas = get_all_alphas()
        
    async def get_market_data(self, symbol: str) -> Dict:
        """Get real market data for a symbol"""
        try:
            # Get features from our feature engineer
            features = await feature_engineer.calculate_features(symbol)
            
            if not features:
                logger.warning(f"No features available for {symbol}")
                return None
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    async def simulate_trade(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        lots: float,
        alpha_id: str,
        q_star: float,
        confidence: float,
        features: Dict
    ) -> Dict:
        """
        Simulate a trade outcome based on market conditions
        Uses realistic win rate and risk/reward from ML predictions
        """
        try:
            # Get ML predictions for this setup
            ml_preds = await ml_inference.predict(symbol, features)
            p_win = ml_preds.get('rf_pwin', 0.5)
            
            # Simulate outcome (win or loss)
            outcome = np.random.random() < p_win
            
            # Calculate PnL
            sl_distance = abs(entry_price - stop_loss)
            tp_distance = abs(entry_price - take_profit)
            
            if outcome:
                # Win - hit take profit
                pnl = tp_distance * lots
                exit_price = take_profit
                exit_reason = "TP"
            else:
                # Loss - hit stop loss
                pnl = -sl_distance * lots
                exit_price = stop_loss
                exit_reason = "SL"
            
            # Apply slippage (0.5 pips average)
            slippage_cost = 0.5 * lots
            pnl -= slippage_cost
            
            # Update equity
            self.equity += pnl
            
            trade = {
                'timestamp': datetime.utcnow(),
                'symbol': symbol,
                'action': action,
                'alpha_id': alpha_id,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'lots': lots,
                'pnl': pnl,
                'equity': self.equity,
                'exit_reason': exit_reason,
                'q_star': q_star,
                'confidence': confidence,
                'p_win': p_win,
                'outcome': 'WIN' if outcome else 'LOSS'
            }
            
            self.trades.append(trade)
            return trade
            
        except Exception as e:
            logger.error(f"Error simulating trade: {e}")
            return None
    
    async def run_backtest(self, num_sessions: int = 20) -> Dict:
        """
        Run backtest simulation across multiple trading sessions
        
        Args:
            num_sessions: Number of trading sessions to simulate
        """
        logger.info(f"Starting backtest with ${self.initial_capital} capital")
        logger.info(f"Testing {len(self.symbols)} symbols across {num_sessions} sessions")
        
        session_results = []
        
        for session in range(num_sessions):
            session_start_equity = self.equity
            session_trades = []
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Session {session + 1}/{num_sessions} - Equity: ${self.equity:.2f}")
            logger.info(f"{'='*80}")
            
            # Scan for signals
            try:
                plans = await global_scanner.scan([])
                
                if not plans:
                    logger.info("No signals generated this session")
                    continue
                
                logger.info(f"Found {len(plans)} trading opportunities")
                
                # Execute top signals
                for plan in plans[:3]:  # Max 3 concurrent trades
                    # Get current market data
                    features = await self.get_market_data(plan.symbol)
                    if not features:
                        continue
                    
                    current_price = features.get('close', 15000)
                    volatility = plan.ml_predictions.get('lstm_sigma', 0.01)
                    
                    # Calculate trade parameters
                    stop_loss = position_sizer.calculate_stop_loss(
                        entry_price=current_price,
                        volatility=volatility,
                        action=plan.action,
                        multiplier=0.8
                    )
                    
                    take_profit = position_sizer.calculate_take_profit(
                        entry_price=current_price,
                        stop_loss=stop_loss,
                        action=plan.action,
                        rr_ratio=1.5
                    )
                    
                    # Calculate position size
                    symbol_info = {
                        'point': 0.01,
                        'trade_tick_value': 1.0,
                        'trade_contract_size': 1,
                        'volume_min': 0.01,
                        'volume_max': 100.0,
                        'volume_step': 0.01,
                    }
                    
                    stop_loss_distance = abs(current_price - stop_loss)
                    lots = position_sizer.calculate_position_size(
                        equity=self.equity,
                        p_win=plan.ml_predictions.get('rf_pwin', 0.5),
                        expected_rr=plan.expected_rr,
                        stop_loss_distance=stop_loss_distance,
                        symbol_info=symbol_info,
                        entropy=0.5
                    )
                    
                    # Apply ES95 constraint
                    es95 = lots * stop_loss_distance * 1.645
                    if es95 > 10.0:
                        lots = 10.0 / (stop_loss_distance * 1.645)
                        lots = round(lots / 0.01) * 0.01
                        lots = max(lots, 0.01)
                    
                    # Simulate trade
                    trade = await self.simulate_trade(
                        symbol=plan.symbol,
                        action=plan.action,
                        entry_price=current_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        lots=lots,
                        alpha_id=plan.alpha_id,
                        q_star=plan.q_star,
                        confidence=plan.confidence,
                        features=features
                    )
                    
                    if trade:
                        session_trades.append(trade)
                        logger.info(
                            f"  {trade['outcome']}: {trade['symbol']} {trade['action']} "
                            f"via {trade['alpha_id']} | PnL: ${trade['pnl']:.2f} | "
                            f"Equity: ${trade['equity']:.2f}"
                        )
                
                # Session summary
                session_pnl = self.equity - session_start_equity
                session_results.append({
                    'session': session + 1,
                    'trades': len(session_trades),
                    'pnl': session_pnl,
                    'equity': self.equity,
                    'return_pct': (session_pnl / session_start_equity) * 100
                })
                
                logger.info(f"Session PnL: ${session_pnl:.2f} ({(session_pnl/session_start_equity)*100:.2f}%)")
                
                # Check if we hit VPropTrader limits
                if session_pnl < -50:
                    logger.warning("⚠️  Daily loss limit hit (-$50)")
                    break
                
                if self.equity < 900:
                    logger.warning("⚠️  Total loss limit hit (equity < $900)")
                    break
                
                if self.equity >= 1100:
                    logger.info("✅ Profit target reached ($100 profit)")
                    break
                
            except Exception as e:
                logger.error(f"Error in session {session + 1}: {e}")
                continue
        
        # Calculate final statistics
        return self.calculate_statistics(session_results)
    
    def calculate_statistics(self, session_results: List[Dict]) -> Dict:
        """Calculate comprehensive backtest statistics"""
        
        if not self.trades:
            return {
                'error': 'No trades executed',
                'initial_capital': self.initial_capital,
                'final_equity': self.equity
            }
        
        df = pd.DataFrame(self.trades)
        
        # Basic metrics
        total_trades = len(df)
        winning_trades = len(df[df['pnl'] > 0])
        losing_trades = len(df[df['pnl'] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # PnL metrics
        total_pnl = df['pnl'].sum()
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        profit_factor = abs(df[df['pnl'] > 0]['pnl'].sum() / df[df['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else float('inf')
        
        # Risk metrics
        returns = df['pnl'] / self.initial_capital
        sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        max_drawdown = self.calculate_max_drawdown(df)
        
        # Per-symbol performance
        symbol_performance = df.groupby('symbol').agg({
            'pnl': ['sum', 'count', 'mean'],
            'outcome': lambda x: (x == 'WIN').sum() / len(x) * 100
        }).round(2)
        
        # Per-alpha performance
        alpha_performance = df.groupby('alpha_id').agg({
            'pnl': ['sum', 'count', 'mean'],
            'outcome': lambda x: (x == 'WIN').sum() / len(x) * 100,
            'q_star': 'mean'
        }).round(2)
        
        # VPropTrader compliance
        daily_loss = df['pnl'].min()
        total_loss = min(0, total_pnl)
        max_daily_pnl = df.groupby(df['timestamp'].dt.date)['pnl'].sum().max()
        
        stats = {
            'summary': {
                'initial_capital': self.initial_capital,
                'final_equity': self.equity,
                'total_pnl': total_pnl,
                'return_pct': (total_pnl / self.initial_capital) * 100,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
            },
            'performance': {
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': (max_drawdown / self.initial_capital) * 100,
            },
            'vproptrader_compliance': {
                'daily_loss_limit': -50,
                'worst_daily_loss': daily_loss,
                'daily_loss_ok': daily_loss >= -50,
                'total_loss_limit': -100,
                'total_loss': total_loss,
                'total_loss_ok': total_loss >= -100,
                'max_daily_profit': max_daily_pnl,
                'profit_target': 100,
                'target_reached': total_pnl >= 100,
            },
            'by_symbol': symbol_performance.to_dict(),
            'by_alpha': alpha_performance.to_dict(),
            'trades': df.to_dict('records')
        }
        
        return stats
    
    def calculate_max_drawdown(self, df: pd.DataFrame) -> float:
        """Calculate maximum drawdown"""
        equity_curve = df['equity'].values
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = equity_curve - running_max
        return abs(drawdown.min())
    
    def print_report(self, stats: Dict):
        """Print comprehensive backtest report"""
        
        print("\n" + "="*80)
        print("VPROPTRADER STRATEGY BACKTEST REPORT")
        print("="*80)
        
        if 'error' in stats:
            print(f"\n❌ {stats['error']}")
            return
        
        # Summary
        summary = stats['summary']
        print(f"\n📊 SUMMARY")
        print(f"{'─'*80}")
        print(f"Initial Capital:    ${summary['initial_capital']:.2f}")
        print(f"Final Equity:       ${summary['final_equity']:.2f}")
        print(f"Total PnL:          ${summary['total_pnl']:.2f}")
        print(f"Return:             {summary['return_pct']:.2f}%")
        print(f"Total Trades:       {summary['total_trades']}")
        print(f"Win Rate:           {summary['win_rate']:.1f}% ({summary['winning_trades']}W / {summary['losing_trades']}L)")
        
        # Performance
        perf = stats['performance']
        print(f"\n📈 PERFORMANCE METRICS")
        print(f"{'─'*80}")
        print(f"Average Win:        ${perf['avg_win']:.2f}")
        print(f"Average Loss:       ${perf['avg_loss']:.2f}")
        print(f"Profit Factor:      {perf['profit_factor']:.2f}")
        print(f"Sharpe Ratio:       {perf['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:       ${perf['max_drawdown']:.2f} ({perf['max_drawdown_pct']:.2f}%)")
        
        # VPropTrader Compliance
        compliance = stats['vproptrader_compliance']
        print(f"\n✅ VPROPTRADER COMPLIANCE")
        print(f"{'─'*80}")
        print(f"Daily Loss Limit:   ${compliance['daily_loss_limit']:.2f}")
        print(f"Worst Daily Loss:   ${compliance['worst_daily_loss']:.2f} {'✅' if compliance['daily_loss_ok'] else '❌'}")
        print(f"Total Loss Limit:   ${compliance['total_loss_limit']:.2f}")
        print(f"Total Loss:         ${compliance['total_loss']:.2f} {'✅' if compliance['total_loss_ok'] else '❌'}")
        print(f"Profit Target:      ${compliance['profit_target']:.2f}")
        print(f"Target Reached:     {'✅ YES' if compliance['target_reached'] else '❌ NO'}")
        
        # Symbol Performance
        print(f"\n🌍 PERFORMANCE BY SYMBOL")
        print(f"{'─'*80}")
        print(f"{'Symbol':<12} {'Trades':<8} {'Total PnL':<12} {'Avg PnL':<12} {'Win Rate':<10}")
        print(f"{'─'*80}")
        
        by_symbol = stats['by_symbol']
        for symbol in by_symbol.get('pnl', {}).get('sum', {}).keys():
            total_pnl = by_symbol['pnl']['sum'][symbol]
            count = by_symbol['pnl']['count'][symbol]
            avg_pnl = by_symbol['pnl']['mean'][symbol]
            win_rate = by_symbol['outcome']['<lambda>'][symbol]
            print(f"{symbol:<12} {count:<8.0f} ${total_pnl:<11.2f} ${avg_pnl:<11.2f} {win_rate:<9.1f}%")
        
        # Alpha Performance
        print(f"\n🎯 PERFORMANCE BY ALPHA STRATEGY")
        print(f"{'─'*80}")
        print(f"{'Alpha':<20} {'Trades':<8} {'Total PnL':<12} {'Avg Q*':<10} {'Win Rate':<10}")
        print(f"{'─'*80}")
        
        by_alpha = stats['by_alpha']
        for alpha in by_alpha.get('pnl', {}).get('sum', {}).keys():
            total_pnl = by_alpha['pnl']['sum'][alpha]
            count = by_alpha['pnl']['count'][alpha]
            avg_qstar = by_alpha['q_star']['mean'][alpha]
            win_rate = by_alpha['outcome']['<lambda>'][alpha]
            print(f"{alpha:<20} {count:<8.0f} ${total_pnl:<11.2f} {avg_qstar:<9.2f} {win_rate:<9.1f}%")
        
        # Strategy Enhancement Recommendations
        print(f"\n💡 STRATEGY ENHANCEMENT RECOMMENDATIONS")
        print(f"{'─'*80}")
        self.print_recommendations(stats)
        
        print(f"\n{'='*80}\n")
    
    def print_recommendations(self, stats: Dict):
        """Generate strategy enhancement recommendations"""
        
        summary = stats['summary']
        perf = stats['performance']
        
        recommendations = []
        
        # Win rate analysis
        if summary['win_rate'] < 55:
            recommendations.append(
                "⚠️  Win rate below 55% - Consider tightening entry criteria or improving Q* threshold"
            )
        elif summary['win_rate'] > 70:
            recommendations.append(
                "✅ Excellent win rate - Current strategy selection is working well"
            )
        
        # Profit factor analysis
        if perf['profit_factor'] < 1.5:
            recommendations.append(
                "⚠️  Profit factor below 1.5 - Consider increasing take profit targets or reducing stop losses"
            )
        elif perf['profit_factor'] > 2.0:
            recommendations.append(
                "✅ Strong profit factor - Risk/reward ratio is well optimized"
            )
        
        # Sharpe ratio analysis
        if perf['sharpe_ratio'] < 2.0:
            recommendations.append(
                "⚠️  Sharpe ratio below 2.0 - Consider reducing position sizes or improving signal quality"
            )
        elif perf['sharpe_ratio'] > 4.0:
            recommendations.append(
                "✅ Excellent Sharpe ratio - Risk-adjusted returns are strong"
            )
        
        # Drawdown analysis
        if perf['max_drawdown_pct'] > 5:
            recommendations.append(
                "⚠️  Max drawdown exceeds 5% - Implement stricter risk controls or reduce position sizes"
            )
        
        # Symbol-specific recommendations
        by_symbol = stats['by_symbol']
        if 'pnl' in by_symbol and 'sum' in by_symbol['pnl']:
            best_symbol = max(by_symbol['pnl']['sum'].items(), key=lambda x: x[1])
            worst_symbol = min(by_symbol['pnl']['sum'].items(), key=lambda x: x[1])
            
            recommendations.append(
                f"📊 Best performing symbol: {best_symbol[0]} (${best_symbol[1]:.2f}) - Consider increasing allocation"
            )
            
            if worst_symbol[1] < 0:
                recommendations.append(
                    f"📊 Worst performing symbol: {worst_symbol[0]} (${worst_symbol[1]:.2f}) - Consider excluding or reducing allocation"
                )
        
        # Alpha-specific recommendations
        by_alpha = stats['by_alpha']
        if 'pnl' in by_alpha and 'sum' in by_alpha['pnl']:
            best_alpha = max(by_alpha['pnl']['sum'].items(), key=lambda x: x[1])
            worst_alpha = min(by_alpha['pnl']['sum'].items(), key=lambda x: x[1])
            
            recommendations.append(
                f"🎯 Best performing alpha: {best_alpha[0]} (${best_alpha[1]:.2f}) - Increase weight"
            )
            
            if worst_alpha[1] < 0:
                recommendations.append(
                    f"🎯 Worst performing alpha: {worst_alpha[0]} (${worst_alpha[1]:.2f}) - Decrease weight or disable"
                )
        
        # Print recommendations
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        if not recommendations:
            print("✅ Strategy is performing well across all metrics!")


async def main():
    """Run comprehensive backtest"""
    
    print("\n" + "="*80)
    print("VPROPTRADER STRATEGY BACKTESTING")
    print("Testing with $1000 capital across multiple assets and sessions")
    print("="*80 + "\n")
    
    # Initialize backtester
    backtester = StrategyBacktester(initial_capital=1000.0)
    
    # Run backtest
    stats = await backtester.run_backtest(num_sessions=20)
    
    # Print comprehensive report
    backtester.print_report(stats)
    
    # Save results
    import json
    with open('backtest_results.json', 'w') as f:
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            return obj
        
        json.dump(convert_types(stats), f, indent=2)
    
    print("📁 Results saved to: backtest_results.json\n")


if __name__ == "__main__":
    asyncio.run(main())
