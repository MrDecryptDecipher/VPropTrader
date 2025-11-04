"""API route aggregator"""

from fastapi import APIRouter
from app.api import signals, executions, analytics, websocket

# Create main API router
api_router = APIRouter(prefix="/api")

# Include sub-routers
api_router.include_router(signals.router, tags=["signals"])
api_router.include_router(executions.router, tags=["executions"])
api_router.include_router(analytics.router, tags=["analytics"])

# WebSocket router (no /api prefix for WebSocket)
ws_router = APIRouter(prefix="/ws")
ws_router.include_router(websocket.router, tags=["websocket"])
