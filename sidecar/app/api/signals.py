"""Signals API endpoint - polled by MT5 EA"""

from fastapi import APIRouter
from app.memory.short_term_memory import short_term_memory as episodic_memory
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
from ..data.symbol_mapper import SymbolMapper

router = APIRouter(prefix="/signals")
symbol_mapper = SymbolMapper()


class Signal(BaseModel):
    """Trading signal model"""
    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="BUY, SELL, or HOLD")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    q_star: float = Field(..., description="Q* quality score")
    es95: float = Field(..., description="Expected Shortfall at 95%")
    stop_loss: float = Field(..., description="Stop loss price")
    take_profit_1: float = Field(..., description="First take profit price")
    take_profit_2: float = Field(..., description="Second take profit price")
    lots: float = Field(..., gt=0, description="Position size in lots")
    alpha_id: str = Field(..., description="Alpha strategy identifier")
    regime: str = Field(..., description="Market regime")
    features: Dict[str, float] = Field(default_factory=dict, description="Feature values at decision time")


class SignalsResponse(BaseModel):
    """Response model for signals endpoint"""
    signals: list[Signal] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    count: int = Field(default=0)


@router.get("", response_model=SignalsResponse)
async def get_signals(
    equity: Optional[float] = 1000.0,
    include_features: bool = False
):
    """
    Get trading signals for MT5 EA
    
    This endpoint is polled by the EA every 1-2 seconds.
    Returns up to 3 high-quality trading signals (A/A+ grade).
    
    Args:
        equity: Current account equity (for position sizing)
        include_features: Include full feature dict in response
    
    Returns:
        SignalsResponse with list of trading signals
    """
    try:
        from app.scanner.scanner import global_scanner
        from app.data.mt5_client import mt5_client
        from app.risk.position_sizing import position_sizer
        
        logger.debug(f"Signals requested by EA (equity: ${equity:.2f})")
        
        # Get existing positions to check correlation
        existing_positions = []
        if mt5_client.connected:
            try:
                positions = mt5_client.get_positions()
                existing_positions = [pos['symbol'] for pos in positions]
                logger.debug(f"Existing positions: {existing_positions}")
            except Exception as e:
                logger.warning(f"Could not fetch positions: {e}")
        
        # Run scanner
        plans = await global_scanner.scan(existing_positions)
        
        # Import execution quality filters
        from app.execution.quality_filters import execution_filters
        
        # Check if trading is paused due to poor execution conditions
        if execution_filters.trading_paused:
            logger.warning(f"Trading paused: {execution_filters.pause_reason}")
            return SignalsResponse(
                signals=[],
                timestamp=datetime.utcnow(),
                count=0,
            )
        
        # Convert plans to signals with proper risk calculations
        # Apply execution quality filters to each plan
        signals = []
        filtered_count = 0
        for plan in plans:
            try:
                # Get current price and spread from MT5 or features
                current_price = plan.features.get('close', 15000)  # Fallback
                spread = plan.features.get('spread', 2.0)  # Fallback spread in pips
                
                if mt5_client.connected:
                    try:
                        tick = mt5_client.get_tick(plan.symbol)
                        if tick:
                            current_price = tick.get('bid' if plan.action == 'SELL' else 'ask', current_price)
                            # Calculate spread in pips
                            bid = tick.get('bid', current_price)
                            ask = tick.get('ask', current_price)
                            spread = abs(ask - bid) * 10000  # Convert to pips
                    except Exception as e:
                        logger.debug(f"Could not get tick for {plan.symbol}: {e}")
                
                # Apply execution quality filters
                
                # 1. Check spread
                spread_ok, spread_reason = execution_filters.check_spread(plan.symbol, spread)
                if not spread_ok:
                    logger.info(f"Filtered {plan.symbol}: {spread_reason}")
                    filtered_count += 1
                    continue
                
                # 2. Check latency (use a default value since we don't have actual latency here)
                # In production, this would come from actual execution timing
                latency_ok, latency_reason = execution_filters.check_latency(50.0)  # Assume 50ms latency
                if not latency_ok:
                    logger.warning(f"Filtered {plan.symbol}: {latency_reason}")
                    filtered_count += 1
                    continue
                
                # 3. Check quote flicker
                flicker_ok, flicker_reason = execution_filters.check_quote_flicker(plan.symbol)
                if not flicker_ok:
                    logger.info(f"Filtered {plan.symbol}: {flicker_reason}")
                    filtered_count += 1
                    continue
                
                volatility = plan.ml_predictions.get('lstm_sigma', 0.01)
                
                # Calculate stop loss
                stop_loss = position_sizer.calculate_stop_loss(
                    entry_price=current_price,
                    volatility=volatility,
                    action=plan.action,
                    multiplier=0.8
                )
                
                # Calculate take profits
                take_profit_1 = position_sizer.calculate_take_profit(
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    action=plan.action,
                    rr_ratio=1.5
                )
                
                take_profit_2 = position_sizer.calculate_take_profit(
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    action=plan.action,
                    rr_ratio=2.4
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
                
                # Get symbol info from MT5 if available
                if mt5_client.connected:
                    try:
                        mt5_symbol_info = mt5_client.get_symbol_info(plan.symbol)
                        if mt5_symbol_info:
                            symbol_info.update(mt5_symbol_info)
                    except Exception as e:
                        logger.debug(f"Could not get symbol info for {plan.symbol}: {e}")
                
                stop_loss_distance = abs(current_price - stop_loss)
                
                lots = position_sizer.calculate_position_size(
                    equity=equity,
                    p_win=plan.ml_predictions.get('rf_pwin', 0.5),
                    expected_rr=plan.expected_rr,
                    stop_loss_distance=stop_loss_distance,
                    symbol_info=symbol_info,
                    entropy=0.5
                )
                
                # Apply volatility targeting
                realized_vol = plan.features.get('realized_vol', volatility)
                lots = position_sizer.apply_volatility_target(
                    lots=lots,
                    realized_vol=realized_vol
                )
                
                # 4. Predict slippage and check if acceptable
                predicted_slippage, slippage_ok = execution_filters.predict_slippage(
                    symbol=plan.symbol,
                    order_size=lots,
                    volatility=volatility,
                    spread=spread
                )
                
                if not slippage_ok:
                    logger.info(f"Filtered {plan.symbol}: Predicted slippage {predicted_slippage:.2f} pips too high")
                    filtered_count += 1
                    continue
                
                # Create signal
                signal = Signal(
                    symbol=plan.symbol,
                    action=plan.action,
                    confidence=plan.confidence,
                    q_star=plan.q_star,
                    es95=plan.es95,
                    stop_loss=stop_loss,
                    take_profit_1=take_profit_1,
                    take_profit_2=take_profit_2,
                    lots=lots,
                    alpha_id=plan.alpha_id,
                    regime=plan.ml_predictions.get('regime', 'unknown'),
                    features=plan.features if include_features else {}
                )
                signals.append(signal)
                
                logger.info(
                    f"Signal generated: {plan.symbol} {plan.action} @ {current_price:.2f}, "
                    f"SL={stop_loss:.2f}, TP1={take_profit_1:.2f}, TP2={take_profit_2:.2f}, "
                    f"Lots={lots:.2f}, Q*={plan.q_star:.2f}"
                )
                
            except Exception as e:
                logger.error(f"Error converting plan to signal: {e}", exc_info=True)
                continue
        
        # Log filtering statistics
        total_plans = len(plans)
        if filtered_count > 0:
            logger.info(
                f"Execution quality filters: {filtered_count}/{total_plans} plans filtered "
                f"({(filtered_count/total_plans*100):.1f}%), {len(signals)} signals passed"
            )
        
        # Translate generic symbols to broker-specific symbols for MT5 EA
        # Sidecar analyzes with generic symbols (e.g., "NAS100"), EA executes with broker symbols (e.g., "US100.e")
        for signal in signals:
            # Convert generic symbol to broker symbol
            broker_symbol = symbol_mapper.to_broker_symbol(signal.symbol)
            if broker_symbol:
                logger.debug(f"Translating symbol: {signal.symbol} -> {broker_symbol}")
                signal.symbol = broker_symbol
            else:
                logger.warning(f"No broker mapping for symbol: {signal.symbol}, keeping as-is")
        
        for signal in signals:
            if signal.symbol in symbol_map:
                original_symbol = signal.symbol
                signal.symbol = symbol_map[signal.symbol]
                logger.debug(f"Mapped symbol: {original_symbol} → {signal.symbol}")
        
        return SignalsResponse(
            signals=signals,
            timestamp=datetime.utcnow(),
            count=len(signals),
        )
        
    except Exception as e:
        logger.error(f"Error generating signals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating signals: {str(e)}")



@router.get("/scanner/stats")
async def get_scanner_stats():
    """
    Get scanner performance statistics
    
    Returns statistics about scanner performance including:
    - Scan count and throughput
    - Skip rate (should be >90%)
    - Average signals per scan
    - Performance metrics
    """
    try:
        from app.scanner.scanner import global_scanner
        
        stats = global_scanner.get_stats()
        
        return {
            "status": "ok",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error getting scanner stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scanner/reset")
async def reset_scanner_stats():
    """Reset scanner statistics"""
    try:
        from app.scanner.scanner import global_scanner
        
        global_scanner.reset_stats()
        
        return {
            "status": "ok",
            "message": "Scanner statistics reset",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error resetting scanner stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
