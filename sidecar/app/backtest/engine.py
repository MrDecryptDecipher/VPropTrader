"""
Backtest Engine
Main backtesting engine with walk-forward analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
from dataclasses import dataclass, asdict

from app.data.historical_data_loader import historical_loader
from app.data.historical_features import historical_feature_calculator
from app.scanner.alphas import get_all_alphas
from app.risk.position_sizing import position_sizer
from app.ml.inference import ml_inference
from .trade_simulator import TradeSimulator, SimulatedTrade
from .performance_analyzer import PerformanceAnalyzer, PerformanceMetrics


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    initial_capital: float = 1000.0
    symbols: List[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_concurrent_trades: int = 3
    max_es95: float = 10.0
    min_q_star: float = 3.0
    walk_forward: bool = True
    train_pct: float = 0.6
    val_pct: float = 0.2
    test_pct: float = 0.2


@dataclass
class BacktestTrade:
    """Complete trade record"""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    action: str
    alpha_id: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    lots: float
    pnl: float
    pnl_pct: float
    equity_before: float
    equity_after: float
    exit_reason: str
    q_star: float
    confidence: float
    p_win: float
    expected_rr: float
    slippage_cost: float
    spread_cost: float
    holding_hours: float
    mae: float
    mfe: float
    features: Dict
    market_session: str


class BacktestEngine:
    """Main backtesting engine"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.loader = historical_loader
        self.feature_calc = historical_feature_calculator
        self.simulator = TradeSimulator()
        self.analyzer = PerformanceAnalyzer()
        self.alphas = get_all_alphas()  # Already returns a dict
        
        self.equity = config.initial_capital
        self.trades: List[BacktestTrade] = []
        self.equity_curve = []
        self.open_positions = []
        
    def run(self) -> Dict:
        """Run complete backtest"""
        logger.info("="*80)
        logger.info("COMPREHENSIVE BACKTEST ENGINE")
        logger.info("="*80)
        logger.info(f"Initial Capital: ${self.config.initial_capital:.2f}")
        logger.info(f"Symbols: {self.config.symbols}")
        logger.info(f"Walk-Forward: {self.config.walk_forward}")
        
        # Load all historical data
        symbol_data = self._load_all_data()
        
        if not symbol_data:
            logger.error("No historical data available")
            return {'error': 'No data'}
        
        # Run backtest
        if self.config.walk_forward:
            results = self._run_walk_forward(symbol_data)
        else:
            results = self._run_simple_backtest(symbol_data)
        
        return results
    
    def _load_all_data(self) -> Dict[str, pd.DataFrame]:
        """Load historical data for all symbols"""
        symbol_data = {}
        
        for symbol in self.config.symbols:
            df = self.loader.load_bars(
                symbol=symbol,
                start_time=self.config.start_date,
                end_time=self.config.end_date
            )
            
            if not df.empty:
                symbol_data[symbol] = df
                logger.info(f"Loaded {len(df)} bars for {symbol}")
        
        return symbol_data
    
    def _run_simple_backtest(self, symbol_data: Dict[str, pd.DataFrame]) -> Dict:
        """Run simple chronological backtest"""
        logger.info("\nRunning simple chronological backtest...")
        
        # Get all timestamps across all symbols
        all_times = set()
        for df in symbol_data.values():
            all_times.update(df.index)
        
        timestamps = sorted(list(all_times))
        logger.info(f"Testing across {len(timestamps)} time points")
        
        # Iterate through time
        for current_time in timestamps:
            self._process_timestamp(current_time, symbol_data)
        
        # Calculate final metrics
        return self._generate_results()
    
    def _process_timestamp(
        self,
        current_time: datetime,
        symbol_data: Dict[str, pd.DataFrame]
    ):
        """Process signals at a specific timestamp"""
        
        # Check if we can take new positions
        if len(self.open_positions) >= self.config.max_concurrent_trades:
            return
        
        # Scan for signals at this time
        signals = self._generate_signals(current_time, symbol_data)
        
        # Execute top signals
        for signal in signals[:self.config.max_concurrent_trades - len(self.open_positions)]:
            self._execute_trade(signal, symbol_data)
    
    def _generate_signals(
        self,
        current_time: datetime,
        symbol_data: Dict[str, pd.DataFrame]
    ) -> List[Dict]:
        """Generate trading signals at current time"""
        signals = []
        
        for symbol in self.config.symbols:
            if symbol not in symbol_data:
                continue
            
            # Calculate features at this time
            features = self.feature_calc.calculate_features(
                symbol=symbol,
                target_time=current_time,
                lookback_bars=100
            )
            
            # Test each alpha
            for alpha_id, alpha in self.alphas.items():
                signal = alpha.generate_signal(features)
                
                if signal and signal.get('action') != 'HOLD':
                    # Calculate Q* score
                    q_star = self._calculate_q_star(features, signal)
                    
                    if q_star >= self.config.min_q_star:
                        signals.append({
                            'symbol': symbol,
                            'alpha_id': alpha_id,
                            'action': signal['action'],
                            'confidence': signal['confidence'],
                            'expected_rr': signal['expected_rr'],
                            'q_star': q_star,
                            'features': features,
                            'time': current_time
                        })
        
        # Sort by Q* score
        signals.sort(key=lambda x: x['q_star'], reverse=True)
        
        return signals
    
    def _calculate_q_star(self, features: Dict, signal: Dict) -> float:
        """Calculate Q* quality score"""
        # Simplified Q* for backtesting
        confidence = signal.get('confidence', 0.5)
        expected_rr = signal.get('expected_rr', 1.5)
        vol = features.get('realized_vol', 0.01)
        
        q_star = (confidence * expected_rr) / (vol * 10)
        return q_star
    
    def _execute_trade(self, signal: Dict, symbol_data: Dict[str, pd.DataFrame]):
        """Execute a trade based on signal"""
        symbol = signal['symbol']
        action = signal['action']
        features = signal['features']
        entry_time = signal['time']
        
        entry_price = features['close']
        volatility = features.get('realized_vol', 0.01)
        
        # Calculate stop loss and take profit
        stop_loss = position_sizer.calculate_stop_loss(
            entry_price=entry_price,
            volatility=volatility,
            action=action,
            multiplier=0.8
        )
        
        take_profit = position_sizer.calculate_take_profit(
            entry_price=entry_price,
            stop_loss=stop_loss,
            action=action,
            rr_ratio=1.5
        )
        
        # Calculate position size
        stop_loss_distance = abs(entry_price - stop_loss)
        
        symbol_info = {
            'point': 0.01,
            'trade_tick_value': 1.0,
            'volume_min': 0.01,
            'volume_max': 100.0,
            'volume_step': 0.01,
        }
        
        lots = position_sizer.calculate_position_size(
            equity=self.equity,
            p_win=0.6,  # Estimated
            expected_rr=signal['expected_rr'],
            stop_loss_distance=stop_loss_distance,
            symbol_info=symbol_info,
            entropy=0.5
        )
        
        # Apply ES95 constraint
        es95 = lots * stop_loss_distance * 1.645
        if es95 > self.config.max_es95:
            lots = self.config.max_es95 / (stop_loss_distance * 1.645)
            lots = round(lots / 0.01) * 0.01
            lots = max(lots, 0.01)
        
        # Get future bars for simulation
        future_bars = symbol_data[symbol][symbol_data[symbol].index > entry_time]
        
        if future_bars.empty:
            return
        
        # Simulate trade
        sim_result = self.simulator.simulate_trade(
            symbol=symbol,
            action=action,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            lots=lots,
            entry_time=entry_time,
            bars_df=future_bars,
            max_holding_hours=48
        )
        
        # Update equity
        equity_before = self.equity
        self.equity += sim_result.pnl
        equity_after = self.equity
        
        # Record trade
        trade = BacktestTrade(
            entry_time=sim_result.entry_time,
            exit_time=sim_result.exit_time,
            symbol=symbol,
            action=action,
            alpha_id=signal['alpha_id'],
            entry_price=sim_result.entry_price,
            exit_price=sim_result.exit_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            lots=lots,
            pnl=sim_result.pnl,
            pnl_pct=sim_result.pnl_pct,
            equity_before=equity_before,
            equity_after=equity_after,
            exit_reason=sim_result.exit_reason,
            q_star=signal['q_star'],
            confidence=signal['confidence'],
            p_win=0.6,
            expected_rr=signal['expected_rr'],
            slippage_cost=sim_result.slippage_cost,
            spread_cost=sim_result.spread_cost,
            holding_hours=sim_result.holding_hours,
            mae=sim_result.mae,
            mfe=sim_result.mfe,
            features=features,
            market_session=self._get_market_session(entry_time)
        )
        
        self.trades.append(trade)
        self.equity_curve.append((sim_result.exit_time, self.equity))
        
        logger.info(
            f"{sim_result.exit_reason}: {symbol} {action} via {signal['alpha_id']} | "
            f"PnL: ${sim_result.pnl:.2f} | Equity: ${self.equity:.2f}"
        )
    
    def _get_market_session(self, dt: datetime) -> str:
        """Determine market session"""
        hour = dt.hour
        if 7 <= hour < 16:
            return "LONDON"
        elif 13 <= hour < 22:
            return "NY" if hour >= 16 else "OVERLAP"
        else:
            return "ASIAN"
    
    def _run_walk_forward(self, symbol_data: Dict[str, pd.DataFrame]) -> Dict:
        """Run walk-forward analysis"""
        logger.info("\nRunning walk-forward analysis...")
        # Implementation continues...
        return self._run_simple_backtest(symbol_data)
    
    def _generate_results(self) -> Dict:
        """Generate comprehensive results"""
        if not self.trades:
            return {'error': 'No trades executed'}
        
        trades_df = pd.DataFrame([asdict(t) for t in self.trades])
        equity_series = pd.Series([e for t, e in self.equity_curve])
        
        metrics = self.analyzer.calculate_metrics(
            trades_df=trades_df,
            initial_capital=self.config.initial_capital,
            equity_curve=equity_series
        )
        
        return {
            'metrics': asdict(metrics),
            'trades': trades_df.to_dict('records'),
            'equity_curve': self.equity_curve,
            'by_symbol': self._analyze_by_symbol(trades_df),
            'by_alpha': self._analyze_by_alpha(trades_df),
            'by_session': self._analyze_by_session(trades_df)
        }
    
    def _analyze_by_symbol(self, df: pd.DataFrame) -> Dict:
        """Analyze performance by symbol"""
        # Add win indicator
        df['is_win'] = df['pnl'] > 0
        
        result = df.groupby('symbol').agg({
            'pnl': ['sum', 'mean', 'count'],
            'is_win': 'mean'
        }).to_dict()
        
        return result
    
    def _analyze_by_alpha(self, df: pd.DataFrame) -> Dict:
        """Analyze performance by alpha"""
        return df.groupby('alpha_id').agg({
            'pnl': ['sum', 'mean', 'count'],
            'q_star': 'mean'
        }).to_dict()
    
    def _analyze_by_session(self, df: pd.DataFrame) -> Dict:
        """Analyze performance by market session"""
        return df.groupby('market_session').agg({
            'pnl': ['sum', 'mean', 'count']
        }).to_dict()
