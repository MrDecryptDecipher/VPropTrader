"""Executions API endpoint - receives trade reports from MT5 EA"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

router = APIRouter(prefix="/executions")


class ExecutionReport(BaseModel):
    """Trade execution report from EA"""
    trade_id: str = Field(..., description="Unique trade identifier")
    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="BUY or SELL")
    entry_price: float = Field(..., description="Actual entry price")
    lots: float = Field(..., gt=0, description="Position size in lots")
    stop_loss: float = Field(..., description="Stop loss price")
    take_profit: float = Field(..., description="Take profit price")
    timestamp: datetime = Field(..., description="Execution timestamp")
    latency_ms: int = Field(..., description="Execution latency in milliseconds")
    spread: float = Field(..., description="Spread at execution")
    slippage: float = Field(default=0.0, description="Slippage in points")
    alpha_id: Optional[str] = Field(None, description="Alpha strategy identifier")
    regime: Optional[str] = Field(None, description="Market regime at execution")
    features: Optional[Dict[str, float]] = Field(None, description="Feature values at execution")
    rf_pwin: Optional[float] = Field(None, description="Random Forest win probability")
    lstm_sigma: Optional[float] = Field(None, description="LSTM volatility forecast")
    lstm_direction: Optional[float] = Field(None, description="LSTM direction forecast")
    q_star: Optional[float] = Field(None, description="Q* confidence score")
    es95: Optional[float] = Field(None, description="Expected Shortfall at 95%")
    equity_before: Optional[float] = Field(None, description="Equity before trade")


class ExecutionResponse(BaseModel):
    """Response model for execution report"""
    status: str = Field(default="received")
    trade_id: str
    message: str = Field(default="Execution report received")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@router.post("", response_model=ExecutionResponse)
async def report_execution(execution: ExecutionReport):
    """
    Receive trade execution report from MT5 EA
    
    The EA sends this after each trade execution to update memory
    and track performance.
    
    Updates:
    1. Short-term memory (Redis)
    2. Long-term memory (FAISS + SQLite) - when trade closes
    3. Alpha weights - when trade closes
    4. Thompson Sampling bandit - when trade closes
    5. Trade logger
    6. Performance metrics
    7. WebSocket broadcast
    """
    try:
        from app.memory.short_term_memory import short_term_memory
        from app.analytics.trade_logger import trade_logger
        from app.learning.trade_recorder import trade_recorder
        from app.api.websocket import broadcast_trade
        
        logger.info(
            f"Execution report received: {execution.trade_id} | "
            f"{execution.action} {execution.lots} {execution.symbol} @ {execution.entry_price} | "
            f"Latency: {execution.latency_ms}ms | Slippage: {execution.slippage}"
        )
        
        # Convert to dict for storage
        trade_data = execution.dict()
        trade_data['status'] = 'open'
        
        # Store in short-term memory (Redis)
        await short_term_memory.add_trade(trade_data)
        
        # Log trade (will be stored in daily file)
        await trade_logger.log_trade(trade_data)

        # 🧠 Self-Learning: Record Trade Outcome
        try:
            await trade_recorder.record_trade_outcome(trade_data)
        except Exception as e:
            logger.error(f"Failed to record trade for learning: {e}")

        
        # Broadcast via WebSocket
        await broadcast_trade(trade_data)
        
        logger.debug(f"Trade {execution.trade_id} stored in memory and logged")
        
        return ExecutionResponse(
            status="received",
            trade_id=execution.trade_id,
            message="Execution report received and processed",
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.error(f"Error processing execution report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing execution report: {str(e)}"
        )


class CloseReport(BaseModel):
    """Trade close report from EA"""
    trade_id: str = Field(..., description="Trade identifier")
    exit_price: float = Field(..., description="Exit price")
    exit_reason: str = Field(..., description="TP1, TP2, SL, TIME, MANUAL")
    pnl: float = Field(..., description="Realized PnL")
    timestamp: datetime = Field(..., description="Close timestamp")
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp (alias)")
    equity_after: Optional[float] = Field(None, description="Equity after trade")


@router.post("/close", response_model=ExecutionResponse)
async def report_close(close: CloseReport):
    """
    Receive trade close report from MT5 EA
    
    The EA sends this when a trade is closed to update memory
    and calculate performance metrics.
    
    Updates:
    1. Retrieve original trade from short-term memory
    2. Update with exit data
    3. Store in long-term memory (FAISS + SQLite)
    4. Update alpha weights based on outcome
    5. Update Thompson Sampling bandit statistics
    6. Log complete trade
    7. Update performance metrics
    8. Broadcast via WebSocket
    """
    try:
        from app.memory.short_term_memory import short_term_memory
        from app.memory.long_term_memory import long_term_memory
        from app.scanner.alpha_weighting import alpha_weighting
        from app.scanner.alpha_selector import alpha_bandit
        from app.analytics.trade_logger import trade_logger
        from app.learning.trade_recorder import trade_recorder
        from app.api.websocket import broadcast_trade
        
        logger.info(
            f"Close report received: {close.trade_id} | "
            f"Exit: {close.exit_price} | Reason: {close.exit_reason} | "
            f"PnL: ${close.pnl:.2f}"
        )
        
        # Get original trade from short-term memory
        recent_trades = await short_term_memory.get_recent_trades(limit=1000)
        original_trade = None
        for trade in recent_trades:
            if trade.get('trade_id') == close.trade_id:
                original_trade = trade
                break
        
        if not original_trade:
            logger.warning(f"Original trade {close.trade_id} not found in STM")
            # Create minimal trade record
            original_trade = {
                'trade_id': close.trade_id,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': 'UNKNOWN',
                'action': 'UNKNOWN',
                'alpha_id': 'unknown',
                'regime': 'unknown',
            }
        
        # Update trade with exit data
        trade_data = original_trade.copy()
        trade_data['exit_price'] = close.exit_price
        trade_data['exit_reason'] = close.exit_reason
        trade_data['exit_time'] = (close.exit_time or close.timestamp).isoformat()
        trade_data['pnl'] = close.pnl
        trade_data['status'] = 'closed'
        
        if close.equity_after:
            trade_data['equity_after'] = close.equity_after
        
        # Calculate PnL percentage if we have entry price
        if 'entry_price' in trade_data and trade_data['entry_price'] > 0:
            price_change = abs(close.exit_price - trade_data['entry_price'])
            trade_data['pnl_percent'] = (price_change / trade_data['entry_price']) * 100
        
        # Store in long-term memory (SQLite + FAISS)
        await long_term_memory.add_trade(trade_data)
        
        # Update alpha weights based on outcome
        alpha_id = trade_data.get('alpha_id')
        if alpha_id and alpha_id != 'unknown':
            try:
                # Calculate Sharpe ratio for this trade (simplified)
                # In production, this would use recent trades for the alpha
                sharpe = 2.0 if close.pnl > 0 else -1.0  # Simplified
                
                await alpha_weighting.update_weights(
                    alpha_id=alpha_id,
                    pnl=close.pnl,
                    symbol=trade_data.get('symbol', 'UNKNOWN'),
                    sharpe=sharpe
                )
                
                logger.debug(f"Updated alpha weights for {alpha_id}")
            except Exception as e:
                logger.error(f"Error updating alpha weights: {e}")
        
        # Update Thompson Sampling bandit
        regime = trade_data.get('regime')
        if alpha_id and regime and alpha_id != 'unknown' and regime != 'unknown':
            try:
                # Reward: 1 for win, 0 for loss
                reward = 1.0 if close.exit_reason in ['TP1', 'TP2'] else 0.0
                
                alpha_bandit.update(
                    regime=regime,
                    alpha_id=alpha_id,
                    reward=reward
                )
                
                # Save bandit state
                alpha_bandit.save()
                
                logger.debug(f"Updated Thompson Sampling bandit for {regime}/{alpha_id}")
            except Exception as e:
                logger.error(f"Error updating Thompson Sampling bandit: {e}")
        
        # Log complete trade
        await trade_logger.log_trade(trade_data)

        # 🧠 Self-Learning: Record Trade Outcome
        try:
            await trade_recorder.record_trade_outcome(trade_data)
        except Exception as e:
            logger.error(f"Failed to record trade for learning: {e}")

        
        # Update performance metrics
        # This is handled automatically by the memory systems
        
        # Broadcast via WebSocket
        await broadcast_trade({
            **trade_data,
            'type': 'trade_closed',
        })
        
        logger.info(
            f"✓ Trade {close.trade_id} closed and processed | "
            f"PnL: ${close.pnl:.2f} | Reason: {close.exit_reason}"
        )
        
        return ExecutionResponse(
            status="received",
            trade_id=close.trade_id,
            message="Close report received and processed",
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.error(f"Error processing close report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing close report: {str(e)}"
        )
