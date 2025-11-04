"""Comprehensive Trade Logging System"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date
from loguru import logger

from app.core import settings
from app.memory.short_term_memory import short_term_memory
from app.memory.long_term_memory import long_term_memory


class TradeLogger:
    """
    Comprehensive trade logging with:
    - Real-time logging to memory
    - Daily digest generation (JSON + CSV)
    - SQLite backup
    """
    
    def __init__(self):
        self.logs_dir = Path(settings.base_path) / "logs" / "trades"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Digest directory as per requirements
        self.digest_dir = Path(settings.base_path) / "data" / "digests"
        self.digest_dir.mkdir(parents=True, exist_ok=True)
        
        self.daily_trades = []
        self.current_date = date.today()
    
    async def log_trade(self, trade_data: Dict) -> bool:
        """
        Log a complete trade record
        
        Trade record includes:
        - timestamp, symbol, regime, alpha_id
        - features@decision
        - RF_Pwin, LSTM_sigma, Q*, ES95
        - risk$, lots, SL, TP
        - exit_reason, pnl
        - spread_z, rule_flags, latency_ms
        
        Args:
            trade_data: Complete trade record
        
        Returns:
            True if successful
        """
        try:
            # Ensure required fields
            if 'trade_id' not in trade_data:
                trade_data['trade_id'] = f"trade_{datetime.utcnow().timestamp()}"
            
            if 'timestamp' not in trade_data:
                trade_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Add to daily trades
            self.daily_trades.append(trade_data)
            
            # Check if day changed
            today = date.today()
            if today != self.current_date:
                # Generate digest for previous day
                await self.generate_daily_digest(self.current_date)
                self.daily_trades = [trade_data]
                self.current_date = today
            
            # Log to short-term memory (Redis)
            await short_term_memory.add_trade(trade_data)
            
            # Log to long-term memory (SQLite + FAISS)
            if trade_data.get('exit_reason'):  # Only closed trades
                await long_term_memory.add_trade(trade_data)
            
            # Log to file
            self._log_to_file(trade_data)
            
            logger.info(
                f"Trade logged: {trade_data['trade_id']} - "
                f"{trade_data.get('symbol')} {trade_data.get('action', 'N/A')} "
                f"via {trade_data.get('alpha_id')} - "
                f"PnL: ${trade_data.get('pnl', 0):.2f}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging trade: {e}", exc_info=True)
            return False
    
    def _log_to_file(self, trade_data: Dict):
        """Log trade to daily file"""
        try:
            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            log_file = self.logs_dir / f"trades_{today_str}.jsonl"
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(trade_data) + '\n')
                
        except Exception as e:
            logger.error(f"Error writing to log file: {e}")
    
    async def generate_daily_digest(self, target_date: Optional[date] = None) -> bool:
        """
        Generate daily digest in JSON and CSV formats
        
        Args:
            target_date: Date to generate digest for (default: yesterday)
        
        Returns:
            True if successful
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            date_str = target_date.strftime("%Y-%m-%d")
            
            logger.info(f"Generating daily digest for {date_str}")
            
            # Get trades for the day
            trades = self.daily_trades if target_date == date.today() else []
            
            if not trades:
                # Try to load from file
                log_file = self.logs_dir / f"trades_{date_str}.jsonl"
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        trades = [json.loads(line) for line in f]
            
            if not trades:
                logger.warning(f"No trades found for {date_str}")
                return False
            
            # Generate JSON digest
            digest = self._create_digest(trades, date_str)
            
            # Save JSON to data/digests/ directory
            json_file = self.digest_dir / f"{date_str}.json"
            with open(json_file, 'w') as f:
                json.dump(digest, f, indent=2)
            
            # Save CSV to data/digests/ directory
            csv_file = self.digest_dir / f"{date_str}.csv"
            self._save_csv(trades, csv_file)
            
            logger.info(
                f"✓ Daily digest generated: {len(trades)} trades, "
                f"PnL: ${digest['summary']['total_pnl']:.2f}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating daily digest: {e}", exc_info=True)
            return False
    
    def _create_digest(self, trades: list[Dict], date_str: str) -> Dict:
        """Create digest summary"""
        try:
            # Calculate summary statistics
            total_trades = len(trades)
            wins = sum(1 for t in trades if t.get('exit_reason') in ['TP1', 'TP2'])
            losses = sum(1 for t in trades if t.get('exit_reason') in ['SL', 'TIME_STOP'])
            
            pnls = [t.get('pnl', 0) for t in trades if t.get('pnl') is not None]
            total_pnl = sum(pnls)
            avg_pnl = total_pnl / len(pnls) if pnls else 0
            
            # By alpha
            by_alpha = {}
            for trade in trades:
                alpha_id = trade.get('alpha_id', 'unknown')
                if alpha_id not in by_alpha:
                    by_alpha[alpha_id] = {'trades': 0, 'wins': 0, 'pnl': 0.0}
                
                by_alpha[alpha_id]['trades'] += 1
                if trade.get('exit_reason') in ['TP1', 'TP2']:
                    by_alpha[alpha_id]['wins'] += 1
                by_alpha[alpha_id]['pnl'] += trade.get('pnl', 0)
            
            # By symbol
            by_symbol = {}
            for trade in trades:
                symbol = trade.get('symbol', 'unknown')
                if symbol not in by_symbol:
                    by_symbol[symbol] = {'trades': 0, 'wins': 0, 'pnl': 0.0}
                
                by_symbol[symbol]['trades'] += 1
                if trade.get('exit_reason') in ['TP1', 'TP2']:
                    by_symbol[symbol]['wins'] += 1
                by_symbol[symbol]['pnl'] += trade.get('pnl', 0)
            
            # Execution quality
            latencies = [t.get('latency_ms', 0) for t in trades if 'latency_ms' in t]
            slippages = [t.get('slippage', 0) for t in trades if 'slippage' in t]
            
            # Rule violations
            violations = []
            for trade in trades:
                flags = trade.get('rule_flags', [])
                if flags:
                    violations.extend(flags)
            
            digest = {
                'date': date_str,
                'generated_at': datetime.utcnow().isoformat(),
                'summary': {
                    'total_trades': total_trades,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': wins / total_trades if total_trades > 0 else 0,
                    'total_pnl': total_pnl,
                    'avg_pnl': avg_pnl,
                    'best_trade': max(pnls) if pnls else 0,
                    'worst_trade': min(pnls) if pnls else 0,
                },
                'by_alpha': by_alpha,
                'by_symbol': by_symbol,
                'execution_quality': {
                    'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
                    'max_latency_ms': max(latencies) if latencies else 0,
                    'avg_slippage': sum(slippages) / len(slippages) if slippages else 0,
                    'max_slippage': max(slippages) if slippages else 0,
                },
                'compliance': {
                    'violations_count': len(violations),
                    'violations': violations,
                },
                'trades': trades,
            }
            
            return digest
            
        except Exception as e:
            logger.error(f"Error creating digest: {e}")
            return {}
    
    def _save_csv(self, trades: list[Dict], csv_file: Path):
        """Save trades to CSV"""
        try:
            if not trades:
                return
            
            # Define CSV columns
            columns = [
                'trade_id', 'timestamp', 'symbol', 'action', 'alpha_id', 'regime',
                'rf_pwin', 'lstm_sigma', 'lstm_direction', 'q_star', 'es95',
                'entry_price', 'stop_loss', 'take_profit_1', 'take_profit_2',
                'lots', 'exit_price', 'exit_reason', 'pnl',
                'latency_ms', 'slippage', 'spread_z', 'equity_after'
            ]
            
            with open(csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(trades)
            
            logger.debug(f"CSV saved: {csv_file}")
            
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
    
    async def get_today_summary(self) -> Dict:
        """Get summary of today's trading"""
        try:
            if not self.daily_trades:
                return {
                    'trades': 0,
                    'pnl': 0.0,
                    'win_rate': 0.0,
                }
            
            wins = sum(1 for t in self.daily_trades if t.get('exit_reason') in ['TP1', 'TP2'])
            pnls = [t.get('pnl', 0) for t in self.daily_trades if t.get('pnl') is not None]
            
            return {
                'trades': len(self.daily_trades),
                'wins': wins,
                'losses': len(self.daily_trades) - wins,
                'win_rate': wins / len(self.daily_trades) if self.daily_trades else 0,
                'total_pnl': sum(pnls),
                'avg_pnl': sum(pnls) / len(pnls) if pnls else 0,
            }
            
        except Exception as e:
            logger.error(f"Error getting today summary: {e}")
            return {}


# Global trade logger instance
trade_logger = TradeLogger()


async def schedule_daily_digest():
    """
    Background task to generate daily digest at end of trading day
    
    Runs at 22:00 UTC (end of trading day) to generate digest for the day
    """
    import asyncio
    from datetime import datetime, timedelta, time
    
    logger.info("Daily digest scheduler started")
    
    while True:
        try:
            # Calculate next run time (22:00 UTC today or tomorrow)
            now = datetime.utcnow()
            target_time = time(22, 0, 0)  # 22:00 UTC
            
            # Create datetime for today at 22:00 UTC
            next_run = datetime.combine(now.date(), target_time)
            
            # If we've passed 22:00 today, schedule for tomorrow
            if now >= next_run:
                next_run = next_run + timedelta(days=1)
            
            # Calculate wait time
            wait_seconds = (next_run - now).total_seconds()
            
            logger.info(f"Next daily digest scheduled for {next_run} UTC")
            logger.info(f"Waiting {wait_seconds/3600:.1f} hours...")
            
            # Wait until scheduled time
            await asyncio.sleep(wait_seconds)
            
            # Generate digest for today
            logger.info("Generating daily digest...")
            success = await trade_logger.generate_daily_digest()
            
            if success:
                logger.info("✓ Daily digest generated successfully")
            else:
                logger.warning("Daily digest generation completed with warnings")
            
            # Wait a bit to avoid running twice
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in daily digest scheduler: {e}", exc_info=True)
            # Wait 1 hour before retrying
            await asyncio.sleep(3600)
