"""WebSocket endpoint for live data streaming to dashboard"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from datetime import datetime
import json
import asyncio
from typing import Set

router = APIRouter(prefix="/live")

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept and store new connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)


manager = ConnectionManager()


@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live data streaming
    
    Streams real-time updates to dashboard:
    - Tick data
    - Trade executions
    - PnL updates
    - Alerts
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection message
        await manager.send_personal(
            {
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to Quant Ω Supra AI Sidecar",
            },
            websocket
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message from client (e.g., subscription requests)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                logger.debug(f"Received WebSocket message: {message}")
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal(
                        {
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                        websocket
                    )
                elif message.get("type") == "subscribe":
                    # TODO: Handle subscription to specific data streams
                    await manager.send_personal(
                        {
                            "type": "subscribed",
                            "channels": message.get("channels", []),
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                        websocket
                    )
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from WebSocket client")
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}", exc_info=True)
                break
    
    finally:
        manager.disconnect(websocket)


async def broadcast_tick(symbol: str, bid: float, ask: float):
    """Broadcast tick data to all connected clients"""
    await manager.broadcast({
        "type": "tick",
        "data": {
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
        },
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_trade(trade_data: dict):
    """Broadcast trade execution to all connected clients"""
    await manager.broadcast({
        "type": "trade",
        "data": trade_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_pnl(pnl_data: dict):
    """Broadcast PnL update to all connected clients"""
    await manager.broadcast({
        "type": "pnl",
        "data": pnl_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_alert(alert_type: str, message: str, severity: str = "info"):
    """Broadcast alert to all connected clients"""
    await manager.broadcast({
        "type": "alert",
        "data": {
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
        },
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_message(message: dict):
    """Generic broadcast function for any message type"""
    if "timestamp" not in message:
        message["timestamp"] = datetime.utcnow().isoformat()
    await manager.broadcast(message)


async def broadcast_execution(execution_result):
    """Broadcast execution result to all connected clients"""
    await manager.broadcast({
        "type": "execution",
        "data": {
            "execution_id": execution_result.execution_id,
            "signal_id": execution_result.signal_id,
            "symbol": execution_result.symbol,
            "action": execution_result.action,
            "lots": execution_result.lots,
            "entry_price": execution_result.entry_price,
            "stop_loss": execution_result.stop_loss,
            "take_profit": execution_result.take_profit,
            "order_id": execution_result.order_id,
            "status": execution_result.status,
            "message": execution_result.message,
            "latency_ms": execution_result.latency_ms,
        },
        "timestamp": execution_result.timestamp.isoformat(),
    })


async def broadcast_signal(signal):
    """Broadcast new signal to all connected clients"""
    await manager.broadcast({
        "type": "signal",
        "data": {
            "signal_id": signal.signal_id,
            "symbol": signal.symbol,
            "action": signal.action,
            "alpha_id": signal.alpha_id,
            "confidence": signal.confidence,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "position_size": signal.position_size,
            "regime": signal.regime,
            "q_star": signal.q_star,
            "rf_pwin": signal.rf_pwin,
        },
        "timestamp": signal.timestamp.isoformat(),
    })


async def broadcast_position_update(position_data: dict):
    """Broadcast position update to all connected clients"""
    await manager.broadcast({
        "type": "position",
        "data": position_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_account_update(account_data: dict):
    """Broadcast account update to all connected clients"""
    await manager.broadcast({
        "type": "account",
        "data": account_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_system_status(status: str, message: str):
    """Broadcast system status update to all connected clients"""
    await manager.broadcast({
        "type": "system_status",
        "data": {
            "status": status,
            "message": message,
        },
        "timestamp": datetime.utcnow().isoformat(),
    })


async def broadcast_model_update(model_data: dict):
    """Broadcast ML model update to all connected clients"""
    await manager.broadcast({
        "type": "model_update",
        "data": model_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


# Background tasks for periodic updates
_heartbeat_task = None
_stats_task = None


async def start_heartbeat():
    """Send periodic heartbeat to keep connections alive"""
    global _heartbeat_task
    if _heartbeat_task is not None:
        return
    
    async def heartbeat_loop():
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                if manager.active_connections:
                    await manager.broadcast({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                        "connections": len(manager.active_connections),
                    })
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    _heartbeat_task = asyncio.create_task(heartbeat_loop())
    logger.info("WebSocket heartbeat started")


async def start_stats_broadcast():
    """Periodically broadcast system statistics"""
    global _stats_task
    if _stats_task is not None:
        return
    
    async def stats_loop():
        while True:
            try:
                await asyncio.sleep(60)  # Every 60 seconds
                if manager.active_connections:
                    # Get system stats
                    from app.data.database import db
                    
                    # Get recent signal count
                    signal_query = """
                        SELECT COUNT(*) as count 
                        FROM signals 
                        WHERE timestamp >= datetime('now', '-1 hour')
                    """
                    signal_row = await db.fetch_one(signal_query)
                    signal_count = signal_row['count'] if signal_row else 0
                    
                    # Get recent execution count
                    exec_query = """
                        SELECT COUNT(*) as count 
                        FROM executions 
                        WHERE timestamp >= datetime('now', '-1 hour')
                    """
                    exec_row = await db.fetch_one(exec_query)
                    exec_count = exec_row['count'] if exec_row else 0
                    
                    # Get open positions count
                    pos_query = """
                        SELECT COUNT(*) as count 
                        FROM trades 
                        WHERE status = 'open'
                    """
                    pos_row = await db.fetch_one(pos_query)
                    pos_count = pos_row['count'] if pos_row else 0
                    
                    # Broadcast stats
                    await manager.broadcast({
                        "type": "stats",
                        "data": {
                            "signals_last_hour": signal_count,
                            "executions_last_hour": exec_count,
                            "open_positions": pos_count,
                            "active_connections": len(manager.active_connections),
                        },
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except Exception as e:
                logger.error(f"Error in stats broadcast loop: {e}")
    
    _stats_task = asyncio.create_task(stats_loop())
    logger.info("WebSocket stats broadcast started")


async def stop_background_tasks():
    """Stop all background tasks"""
    global _heartbeat_task, _stats_task
    
    if _heartbeat_task:
        _heartbeat_task.cancel()
        _heartbeat_task = None
    
    if _stats_task:
        _stats_task.cancel()
        _stats_task = None
    
    logger.info("WebSocket background tasks stopped")


# Helper function to get connection count
def get_connection_count() -> int:
    """Get number of active WebSocket connections"""
    return len(manager.active_connections)


# Helper function to check if any clients are connected
def has_active_connections() -> bool:
    """Check if there are any active WebSocket connections"""
    return len(manager.active_connections) > 0
