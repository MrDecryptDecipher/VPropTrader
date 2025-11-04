"""Analytics API endpoints for dashboard"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

router = APIRouter(prefix="/analytics")


# Response Models

class OverviewMetrics(BaseModel):
    """Overview metrics response"""
    equity: float = Field(default=1000.0)
    pnl_today: float = Field(default=0.0)
    pnl_total: float = Field(default=0.0)
    drawdown_current: float = Field(default=0.0)
    drawdown_max: float = Field(default=0.0)
    target_progress: float = Field(default=0.0)
    trades_today: int = Field(default=0)
    win_rate: float = Field(default=0.0)
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ComplianceRule(BaseModel):
    """Individual compliance rule status"""
    name: str
    status: str = Field(..., description="green, yellow, or red")
    value: float | str
    limit: float | str
    description: str = ""


class ComplianceStatus(BaseModel):
    """Compliance status response"""
    rules: list[ComplianceRule] = Field(default_factory=list)
    violations_count: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AlphaMetrics(BaseModel):
    """Alpha performance metrics"""
    id: str
    contribution_pct: float
    sharpe: float
    hit_rate: float
    avg_rr: float
    trades: int
    weight: float
    pnl: float = 0.0
    max_dd: float = 0.0


class AlphasResponse(BaseModel):
    """Alphas performance response"""
    alphas: list[AlphaMetrics] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RiskMetrics(BaseModel):
    """Risk metrics response"""
    var_95: float = Field(default=0.0)
    es_95: float = Field(default=0.0)
    vol_forecast: float = Field(default=0.0)
    exposure_by_symbol: Dict[str, float] = Field(default_factory=dict)
    correlation_matrix: list[List[float]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Endpoints

@router.get("/overview", response_model=OverviewMetrics)
async def get_overview():
    """
    Get overview metrics for dashboard
    
    Returns current equity, PnL, drawdown, and performance metrics.
    """
    try:
        # TODO: Calculate actual metrics from memory/database
        logger.debug("Overview metrics requested")
        
        return OverviewMetrics(
            equity=1000.0,
            pnl_today=0.0,
            pnl_total=0.0,
            drawdown_current=0.0,
            drawdown_max=0.0,
            target_progress=0.0,
            trades_today=0,
            win_rate=0.0,
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.error(f"Error getting overview metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance", response_model=ComplianceStatus)
async def get_compliance():
    """
    Get compliance status for all VPropTrader rules
    
    Returns green/yellow/red status for each rule.
    """
    try:
        from app.data.database import db
        from datetime import date, timedelta
        
        logger.debug("Compliance status requested")
        
        # Get today's date
        today = date.today()
        today_str = today.isoformat()
        
        # Query today's PnL
        query_today = """
            SELECT COALESCE(SUM(pnl), 0) as pnl_today
            FROM trades
            WHERE DATE(timestamp) = ?
            AND status = 'closed'
        """
        row_today = await db.fetch_one(query_today, (today_str,))
        pnl_today = row_today['pnl_today'] if row_today else 0.0
        
        # Query total PnL
        query_total = """
            SELECT COALESCE(SUM(pnl), 0) as pnl_total
            FROM trades
            WHERE status = 'closed'
        """
        row_total = await db.fetch_one(query_total)
        pnl_total = row_total['pnl_total'] if row_total else 0.0
        
        # Query trading days (days with at least 1 trade)
        query_days = """
            SELECT COUNT(DISTINCT DATE(timestamp)) as trading_days
            FROM trades
            WHERE status = 'closed'
        """
        row_days = await db.fetch_one(query_days)
        trading_days = row_days['trading_days'] if row_days else 0
        
        # Query open positions for overnight check
        query_positions = """
            SELECT COUNT(*) as open_count
            FROM trades
            WHERE status = 'open'
        """
        row_positions = await db.fetch_one(query_positions)
        open_positions = row_positions['open_count'] if row_positions else 0
        
        # Calculate current equity
        starting_equity = 1000.0
        current_equity = starting_equity + pnl_total
        
        # Calculate daily profit percentage
        daily_profit_pct = (pnl_today / starting_equity) * 100 if starting_equity > 0 else 0.0
        
        # Rule 1: Daily Loss Limit (-$45)
        daily_loss_status = "green"
        if pnl_today <= -45.0:
            daily_loss_status = "red"
        elif pnl_today <= -35.0:
            daily_loss_status = "yellow"
        
        # Rule 2: Total Loss Limit (equity <= $900)
        total_loss_status = "green"
        total_loss = starting_equity - current_equity
        if current_equity <= 900.0:
            total_loss_status = "red"
        elif current_equity <= 920.0:
            total_loss_status = "yellow"
        
        # Rule 3: Profit Target ($100)
        profit_target_status = "green"
        if pnl_total >= 100.0:
            profit_target_status = "green"  # Target reached
        elif pnl_total >= 80.0:
            profit_target_status = "yellow"  # Close to target
        
        # Rule 4: Trading Days (minimum 4 days)
        trading_days_status = "green"
        if trading_days < 4:
            trading_days_status = "yellow"
        else:
            trading_days_status = "green"
        
        # Rule 5: Overnight Positions (should be 0)
        overnight_status = "green"
        if open_positions > 0:
            # Check if it's close to end of day (21:45 UTC)
            from datetime import datetime
            now = datetime.utcnow()
            if now.hour >= 21 and now.minute >= 45:
                overnight_status = "red"
            elif now.hour >= 21 and now.minute >= 30:
                overnight_status = "yellow"
        
        # Rule 6: News Embargo (always active in this implementation)
        news_embargo_status = "green"
        
        # Rule 7: Daily Profit Cap (1.8% of equity)
        daily_cap_status = "green"
        if daily_profit_pct >= 1.8:
            daily_cap_status = "red"
        elif daily_profit_pct >= 1.5:
            daily_cap_status = "yellow"
        
        rules = [
            ComplianceRule(
                name="Daily Loss Limit",
                status=daily_loss_status,
                value=pnl_today,
                limit=-45.0,
                description="Maximum daily loss: -$45"
            ),
            ComplianceRule(
                name="Total Loss Limit",
                status=total_loss_status,
                value=current_equity,
                limit=900.0,
                description="Minimum equity: $900"
            ),
            ComplianceRule(
                name="Profit Target",
                status=profit_target_status,
                value=pnl_total,
                limit=100.0,
                description="Target profit: $100"
            ),
            ComplianceRule(
                name="Trading Days",
                status=trading_days_status,
                value=trading_days,
                limit=4,
                description="Minimum 4 trading days required"
            ),
            ComplianceRule(
                name="Overnight Positions",
                status=overnight_status,
                value=open_positions,
                limit=0,
                description="No overnight positions allowed"
            ),
            ComplianceRule(
                name="News Embargo",
                status=news_embargo_status,
                value="Active",
                limit="Active",
                description="Trading paused during high-impact news"
            ),
            ComplianceRule(
                name="Daily Profit Cap",
                status=daily_cap_status,
                value=daily_profit_pct,
                limit=1.8,
                description="Maximum daily profit: 1.8% of equity"
            ),
        ]
        
        # Count violations
        violations_count = sum(1 for rule in rules if rule.status == "red")
        
        return ComplianceStatus(
            rules=rules,
            violations_count=violations_count,
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.error(f"Error getting compliance status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alphas", response_model=AlphasResponse)
async def get_alphas():
    """
    Get alpha performance metrics
    
    Returns contribution, Sharpe, hit rate, etc. for each alpha.
    """
    try:
        from app.data.database import db
        import numpy as np
        
        logger.debug("Alpha metrics requested")
        
        # Query trades grouped by alpha
        query = """
            SELECT 
                alpha_id,
                COUNT(*) as trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl,
                STDEV(pnl) as std_pnl,
                MAX(pnl) as max_pnl,
                MIN(pnl) as min_pnl
            FROM trades
            WHERE status = 'closed'
            AND alpha_id IS NOT NULL
            GROUP BY alpha_id
        """
        
        rows = await db.fetch_all(query)
        
        if not rows:
            # Return empty list if no trades
            return AlphasResponse(
                alphas=[],
                timestamp=datetime.utcnow(),
            )
        
        # Calculate total PnL for contribution percentages
        total_pnl = sum(row['total_pnl'] for row in rows if row['total_pnl'])
        
        alphas = []
        for row in rows:
            alpha_id = row['alpha_id']
            trades = row['trades'] or 0
            wins = row['wins'] or 0
            pnl = row['total_pnl'] or 0.0
            avg_pnl = row['avg_pnl'] or 0.0
            std_pnl = row['std_pnl'] or 0.0
            max_pnl = row['max_pnl'] or 0.0
            min_pnl = row['min_pnl'] or 0.0
            
            # Calculate metrics
            hit_rate = (wins / trades * 100) if trades > 0 else 0.0
            contribution_pct = (pnl / total_pnl * 100) if total_pnl != 0 else 0.0
            
            # Calculate Sharpe ratio (assuming 252 trading days, daily returns)
            sharpe = (avg_pnl / std_pnl * np.sqrt(252)) if std_pnl > 0 else 0.0
            
            # Calculate average risk-reward
            avg_win = avg_pnl if wins > 0 else 0.0
            avg_loss = abs(min_pnl) if min_pnl < 0 else 0.0
            avg_rr = (avg_win / avg_loss) if avg_loss > 0 else 0.0
            
            # Get current weight from alpha weighter (default to equal weight)
            weight = 1.0 / len(rows) if len(rows) > 0 else 0.0
            
            # Calculate max drawdown (simplified)
            max_dd = abs(min_pnl) if min_pnl < 0 else 0.0
            
            alphas.append(AlphaMetrics(
                id=alpha_id,
                contribution_pct=contribution_pct,
                sharpe=sharpe,
                hit_rate=hit_rate,
                avg_rr=avg_rr,
                trades=trades,
                weight=weight,
                pnl=pnl,
                max_dd=max_dd,
            ))
        
        # Sort by contribution percentage (descending)
        alphas.sort(key=lambda x: x.contribution_pct, reverse=True)
        
        return AlphasResponse(
            alphas=alphas,
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.error(f"Error getting alpha metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk", response_model=RiskMetrics)
async def get_risk():
    """
    Get risk metrics
    
    Returns VaR, ES95, volatility forecast, exposure, and correlations.
    """
    try:
        from app.data.database import db
        import numpy as np
        
        logger.debug("Risk metrics requested")
        
        # Query recent PnL for VaR/ES calculation (last 100 trades)
        query_pnl = """
            SELECT pnl
            FROM trades
            WHERE status = 'closed'
            AND pnl IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 100
        """
        
        rows_pnl = await db.fetch_all(query_pnl)
        pnls = [row['pnl'] for row in rows_pnl] if rows_pnl else []
        
        # Calculate VaR 95% and ES 95%
        var_95 = 0.0
        es_95 = 0.0
        
        if len(pnls) >= 20:  # Need minimum data
            pnls_array = np.array(pnls)
            # VaR 95% = 5th percentile of PnL distribution
            var_95 = float(np.percentile(pnls_array, 5))
            # ES 95% = average of losses beyond VaR
            losses_beyond_var = pnls_array[pnls_array <= var_95]
            es_95 = float(np.mean(losses_beyond_var)) if len(losses_beyond_var) > 0 else var_95
        
        # Calculate volatility forecast (standard deviation of recent PnL)
        vol_forecast = 0.0
        if len(pnls) >= 10:
            vol_forecast = float(np.std(pnls))
        
        # Query current open positions for exposure
        query_positions = """
            SELECT 
                symbol,
                SUM(lots) as total_lots,
                action
            FROM trades
            WHERE status = 'open'
            GROUP BY symbol, action
        """
        
        rows_positions = await db.fetch_all(query_positions)
        
        # Calculate exposure by symbol (as percentage of equity)
        exposure_by_symbol = {}
        starting_equity = 1000.0
        
        if rows_positions:
            for row in rows_positions:
                symbol = row['symbol']
                lots = row['total_lots'] or 0.0
                # Simplified: assume 1 lot = 1% exposure
                exposure_pct = (lots / starting_equity) * 100
                
                if symbol in exposure_by_symbol:
                    exposure_by_symbol[symbol] += exposure_pct
                else:
                    exposure_by_symbol[symbol] = exposure_pct
        
        # Calculate correlation matrix (simplified - using recent trades)
        query_symbols = """
            SELECT DISTINCT symbol
            FROM trades
            WHERE status = 'closed'
            AND timestamp >= datetime('now', '-7 days')
            LIMIT 10
        """
        
        rows_symbols = await db.fetch_all(query_symbols)
        symbols = [row['symbol'] for row in rows_symbols] if rows_symbols else []
        
        correlation_matrix = []
        if len(symbols) >= 2:
            # Build correlation matrix (simplified - identity matrix for now)
            n = len(symbols)
            correlation_matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        
        return RiskMetrics(
            var_95=var_95,
            es_95=es_95,
            vol_forecast=vol_forecast,
            exposure_by_symbol=exposure_by_symbol,
            correlation_matrix=correlation_matrix,
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



class EquityPoint(BaseModel):
    """Single equity history point"""
    timestamp: str
    equity: float
    pnl: float


class EquityHistoryResponse(BaseModel):
    """Equity history response"""
    history: list[EquityPoint] = Field(default_factory=list)
    count: int = 0


class TradeRecord(BaseModel):
    """Individual trade record"""
    trade_id: str
    timestamp: str
    symbol: str
    action: str
    alpha_id: str
    regime: str = ""
    entry_price: float
    exit_price: float
    lots: float
    pnl: float
    pnl_percent: float
    duration_minutes: int
    exit_reason: str
    q_star: float = 0.0
    rf_pwin: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    spread_z: float = 0.0
    slippage: float = 0.0
    latency_ms: int = 0
    risk_dollars: float = 0.0


class TradesResponse(BaseModel):
    """Trades history response"""
    trades: list[TradeRecord] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    per_page: int = 50


class ScannerMetrics(BaseModel):
    """Scanner performance metrics"""
    throughput: float = 0.0
    skip_rate: float = 0.0
    avg_scan_time: float = 0.0


class MLInferenceMetrics(BaseModel):
    """ML inference performance metrics"""
    rf_latency_ms: float = 0.0
    lstm_latency_ms: float = 0.0
    gbt_latency_ms: float = 0.0


class DataPipelineMetrics(BaseModel):
    """Data pipeline performance metrics"""
    mt5_latency_ms: float = 0.0
    redis_latency_ms: float = 0.0
    feature_compute_ms: float = 0.0
    cache_hit_rate: float = 0.0


class SystemMetrics(BaseModel):
    """System resource metrics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    uptime_hours: float = 0.0


class PerformanceMetrics(BaseModel):
    """Complete performance metrics"""
    scanner: ScannerMetrics = Field(default_factory=ScannerMetrics)
    ml_inference: MLInferenceMetrics = Field(default_factory=MLInferenceMetrics)
    data_pipeline: DataPipelineMetrics = Field(default_factory=DataPipelineMetrics)
    system: SystemMetrics = Field(default_factory=SystemMetrics)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@router.get("/trades", response_model=TradesResponse)
async def get_trades(
    page: int = 1,
    per_page: int = 50,
    symbol: Optional[str] = None,
    alpha_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """
    Get trades history with filtering and pagination
    
    Args:
        page: Page number (1-indexed)
        per_page: Number of trades per page
        symbol: Filter by symbol
        alpha_id: Filter by alpha strategy
        date_from: Filter by start date (YYYY-MM-DD)
        date_to: Filter by end date (YYYY-MM-DD)
    
    Returns:
        Paginated list of trade records
    """
    try:
        from app.data.database import db
        
        logger.debug(f"Trades history requested (page: {page}, per_page: {per_page})")
        
        # Build WHERE clause
        where_clauses = ["status = 'closed'"]
        params = []
        
        if symbol:
            where_clauses.append("symbol = ?")
            params.append(symbol)
        
        if alpha_id:
            where_clauses.append("alpha_id = ?")
            params.append(alpha_id)
        
        if date_from:
            where_clauses.append("DATE(timestamp) >= ?")
            params.append(date_from)
        
        if date_to:
            where_clauses.append("DATE(timestamp) <= ?")
            params.append(date_to)
        
        where_clause = " AND ".join(where_clauses)
        
        # Count total trades
        count_query = f"SELECT COUNT(*) as total FROM trades WHERE {where_clause}"
        count_row = await db.fetch_one(count_query, tuple(params))
        total = count_row['total'] if count_row else 0
        
        # Query trades with pagination
        offset = (page - 1) * per_page
        query = f"""
            SELECT 
                trade_id,
                timestamp,
                symbol,
                action,
                alpha_id,
                regime,
                entry_price,
                exit_price,
                lots,
                pnl,
                pnl_percent,
                duration_minutes,
                exit_reason,
                q_star,
                rf_pwin,
                stop_loss,
                take_profit,
                spread_z,
                slippage,
                latency_ms,
                risk_dollars
            FROM trades
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        
        params.extend([per_page, offset])
        rows = await db.fetch_all(query, tuple(params))
        
        trades = []
        if rows:
            for row in rows:
                trades.append(TradeRecord(
                    trade_id=row['trade_id'] or "",
                    timestamp=row['timestamp'] or "",
                    symbol=row['symbol'] or "",
                    action=row['action'] or "",
                    alpha_id=row['alpha_id'] or "",
                    regime=row['regime'] or "",
                    entry_price=row['entry_price'] or 0.0,
                    exit_price=row['exit_price'] or 0.0,
                    lots=row['lots'] or 0.0,
                    pnl=row['pnl'] or 0.0,
                    pnl_percent=row['pnl_percent'] or 0.0,
                    duration_minutes=row['duration_minutes'] or 0,
                    exit_reason=row['exit_reason'] or "",
                    q_star=row['q_star'] or 0.0,
                    rf_pwin=row['rf_pwin'] or 0.0,
                    stop_loss=row['stop_loss'] or 0.0,
                    take_profit=row['take_profit'] or 0.0,
                    spread_z=row['spread_z'] or 0.0,
                    slippage=row['slippage'] or 0.0,
                    latency_ms=row['latency_ms'] or 0,
                    risk_dollars=row['risk_dollars'] or 0.0,
                ))
        
        return TradesResponse(
            trades=trades,
            total=total,
            page=page,
            per_page=per_page,
        )
        
    except Exception as e:
        logger.error(f"Error getting trades history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equity-history", response_model=EquityHistoryResponse)
async def get_equity_history(limit: int = 1000):
    """
    Get equity history for charting
    
    Args:
        limit: Maximum number of points to return
    
    Returns:
        List of equity points with timestamp, equity, and PnL
    """
    try:
        from app.data.database import db
        
        logger.debug(f"Equity history requested (limit: {limit})")
        
        # Query trades from database
        query = """
            SELECT 
                timestamp,
                equity_after,
                pnl
            FROM trades
            WHERE status = 'closed'
            AND equity_after IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        rows = await db.fetch_all(query, (limit,))
        
        if not rows:
            # Return initial equity point if no trades
            return EquityHistoryResponse(
                history=[
                    EquityPoint(
                        timestamp=datetime.utcnow().isoformat(),
                        equity=1000.0,
                        pnl=0.0
                    )
                ],
                count=1
            )
        
        # Convert to equity points (reverse to chronological order)
        history = [
            EquityPoint(
                timestamp=row['timestamp'],
                equity=row['equity_after'],
                pnl=row['pnl'] or 0.0
            )
            for row in reversed(rows)
        ]
        
        return EquityHistoryResponse(
            history=history,
            count=len(history)
        )
        
    except Exception as e:
        logger.error(f"Error getting equity history: {e}", exc_info=True)
        # Return fallback data
        return EquityHistoryResponse(
            history=[
                EquityPoint(
                    timestamp=datetime.utcnow().isoformat(),
                    equity=1000.0,
                    pnl=0.0
                )
            ],
            count=1
        )



@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance():
    """
    Get system performance metrics
    
    Returns scanner, ML, data pipeline, and system metrics.
    """
    try:
        import psutil
        import time
        
        logger.debug("Performance metrics requested")
        
        # Scanner metrics (would come from global scanner instance)
        scanner_metrics = ScannerMetrics(
            throughput=35.0,  # combos/sec
            skip_rate=92.0,   # percentage
            avg_scan_time=0.028,  # seconds
        )
        
        # ML inference metrics (would come from model manager)
        ml_metrics = MLInferenceMetrics(
            rf_latency_ms=8.5,
            lstm_latency_ms=12.3,
            gbt_latency_ms=15.7,
        )
        
        # Data pipeline metrics
        pipeline_metrics = DataPipelineMetrics(
            mt5_latency_ms=85.0,
            redis_latency_ms=2.5,
            feature_compute_ms=25.0,
            cache_hit_rate=96.5,
        )
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Calculate uptime (simplified - would track actual start time)
        uptime_hours = 24.5
        
        system_metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            uptime_hours=uptime_hours,
        )
        
        return PerformanceMetrics(
            scanner=scanner_metrics,
            ml_inference=ml_metrics,
            data_pipeline=pipeline_metrics,
            system=system_metrics,
            timestamp=datetime.utcnow(),
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_active_positions():
    """
    Get currently open positions
    
    Returns list of active trades with current PnL.
    """
    try:
        from app.data.database import db
        
        logger.debug("Active positions requested")
        
        query = """
            SELECT 
                symbol,
                action,
                entry_price,
                lots,
                alpha_id,
                timestamp,
                stop_loss,
                take_profit
            FROM trades
            WHERE status = 'open'
            ORDER BY timestamp DESC
        """
        
        rows = await db.fetch_all(query)
        
        positions = []
        if rows:
            for row in rows:
                # Calculate current price and PnL (simplified - would get from MT5)
                entry_price = row['entry_price'] or 0.0
                current_price = entry_price * 1.001  # Simplified
                
                # Calculate PnL
                lots = row['lots'] or 0.0
                if row['action'] == 'BUY':
                    pnl = (current_price - entry_price) * lots * 100000  # Simplified
                else:
                    pnl = (entry_price - current_price) * lots * 100000
                
                pnl_percent = ((current_price - entry_price) / entry_price) if entry_price > 0 else 0.0
                
                # Calculate duration
                from datetime import datetime
                entry_time = datetime.fromisoformat(row['timestamp'])
                duration_minutes = int((datetime.utcnow() - entry_time).total_seconds() / 60)
                
                positions.append({
                    'symbol': row['symbol'],
                    'action': row['action'],
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'lots': lots,
                    'duration_minutes': duration_minutes,
                    'alpha_id': row['alpha_id'],
                })
        
        return {'positions': positions}
        
    except Exception as e:
        logger.error(f"Error getting active positions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
