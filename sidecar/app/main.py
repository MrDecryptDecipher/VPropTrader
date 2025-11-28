import asyncio
import signal
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core import settings
from app.data.database import db
from app.data.redis_client import redis_client
from app.data.vector_store import vector_store
from app.data.mt5_client import mt5_client
from app.data.calendar_scraper import calendar_scraper
from app.data.fred_client import fred_client
from app.data.high_frequency_orchestrator import HighFrequencyDataOrchestrator as DataOrchestrator

# Global state
app_state = {
    "startup_time": None,
    "shutdown_requested": False,
    "orchestrator": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    try:
        app_state["startup_time"] = datetime.utcnow()
        logger.info("=" * 60)
        logger.info(f"Starting Sidecar Service ({settings.environment})")
        logger.info("=" * 60)
        
        # Initialize Database
        await db.connect()
        logger.info("✓ Database connected")
        
        # Initialize Redis
        await redis_client.connect()
        logger.info("✓ Redis connected")
        
        # Initialize Vector Store
        # vector_store.load_index()
        logger.info("✓ Vector store loaded")
        
        # Initialize MT5
        if mt5_client.connect():
            logger.info("✓ MetaTrader 5 connected")
        else:
            logger.warning("⚠ MetaTrader 5 connection failed")
            
        # Initialize FRED Client
        fred_client.api_key = settings.fred_api_key
        logger.info("✓ FRED client initialized")
        
        # Start Data Orchestrator
        try:
            orchestrator = DataOrchestrator(symbols=settings.symbols_list, collection_interval=settings.collection_interval)
            app_state["orchestrator"] = orchestrator
            
            # Start background task
            asyncio.create_task(orchestrator.start())
            logger.info("✓ High-frequency data orchestrator started")
            
        except Exception as e:
            logger.error(f"⚠ Failed to start data orchestrator: {e}", exc_info=True)
            logger.warning("Continuing without real-time data collection")
        
        logger.info("✓ Sidecar Service started successfully")
        
        # Debug: Log all registered routes
        logger.info("Registered Routes:")
        for route in app.routes:
            if hasattr(route, "methods"):
                logger.info(f"Route: {route.methods} {route.path}")
            else:
                logger.info(f"Route: {route.path}")
        
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down Sidecar Service")
    logger.info("=" * 60)
    app_state["shutdown_requested"] = True
    
    try:
        # Stop data orchestrator
        if "orchestrator" in app_state:
            try:
                await app_state["orchestrator"].stop()
                logger.info("✓ Data orchestrator stopped")
            except Exception as e:
                logger.error(f"Error stopping orchestrator: {e}")
        
        # Save FAISS index
        vector_store.save_index()
        
        # Close connections
        mt5_client.disconnect()
        await fred_client.close()
        await calendar_scraper.close()
        await redis_client.disconnect()
        await db.disconnect()
        
        logger.info("✓ Sidecar Service shutdown complete")
        
    except Exception as e:
        logger.error(f"✗ Shutdown error: {e}", exc_info=True)


# Create FastAPI app
app = FastAPI(
    title="Quant Ω Supra AI Sidecar",
    description="Memory-Adaptive Prop Trading System - AI Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
from app.api.routes import api_router, ws_router
from app.api.user_config import router as user_config_router

app.include_router(api_router)
app.include_router(user_config_router)
app.include_router(ws_router)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.environment == "development" else "An error occurred",
            "detail": str(exc) if settings.environment == "development" else "An error occurred", # Alias for frontend compatibility
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.get("/")
async def root():
    """Root endpoint"""
    uptime = None
    if app_state["startup_time"]:
        uptime = (datetime.utcnow() - app_state["startup_time"]).total_seconds()
    
    return {
        "service": "Quant Ω Supra AI Sidecar",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "uptime_seconds": uptime,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    from app.core.metrics import metrics_collector
    
    # Return Prometheus format
    return JSONResponse(
        content={"metrics": metrics_collector.export_prometheus()},
        media_type="text/plain"
    )


@app.get("/metrics/json")
async def metrics_json():
    """JSON metrics endpoint for dashboards"""
    from app.core.metrics import metrics_collector
    
    return metrics_collector.get_all_metrics()


@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with data pipeline metrics"""
    from app.data.database import db
    from app.data.redis_client import redis_client
    from app.data.vector_store import vector_store
    from app.data.mt5_client import mt5_client
    from app.core.metrics import metrics_collector
    
    # Check Redis
    redis_status = "healthy" if redis_client.connected else "disconnected"
    redis_msg = "Connected" if redis_client.connected else "Not connected"
    
    # Check Database
    db_status = "healthy" if db.connection else "disconnected"
    db_msg = "Connected" if db.connection else "Not connected"
    
    # Check FAISS
    faiss_stats = vector_store.get_stats()
    faiss_status = "healthy" if faiss_stats.get("initialized") else "not_initialized"
    faiss_msg = f"{faiss_stats.get('total_vectors', 0)} vectors" if faiss_stats.get("initialized") else "Not initialized"
    
    # Check MT5
    mt5_status = "healthy" if mt5_client.connected else "disconnected"
    mt5_msg = "Connected"
    if mt5_client.connected and mt5_client.account_info:
        mt5_msg = f"Connected - Balance: ${mt5_client.account_info.balance:.2f}"
    elif not mt5_client.connected:
        mt5_msg = "Not connected"
    
    # Get data pipeline metrics
    pipeline_metrics = metrics_collector.get_summary()
    source_health = metrics_collector.get_source_health()
    
    # Check data pipeline health
    data_freshness = pipeline_metrics.get("data_freshness_max", 0)
    pipeline_status = "healthy"
    pipeline_msg = "Operating normally"
    
    if data_freshness > 60:
        pipeline_status = "stale"
        pipeline_msg = f"Data is {data_freshness:.0f}s old"
    elif data_freshness > 10:
        pipeline_status = "degraded"
        pipeline_msg = f"Data is {data_freshness:.0f}s old"
    
    # Overall status
    overall_status = "healthy"
    if not (db.connection and mt5_client.connected):
        overall_status = "degraded"
    if pipeline_status == "stale":
        overall_status = "unhealthy"
    
    health_status = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "mt5": {"status": mt5_status, "message": mt5_msg},
            "redis": {"status": redis_status, "message": redis_msg},
            "database": {"status": db_status, "message": db_msg},
            "faiss": {"status": faiss_status, "message": faiss_msg, "stats": faiss_stats},
            "fred_api": {"status": "configured" if settings.fred_api_key else "not_configured"},
            "models": {"status": "not_loaded", "message": "ML models not yet loaded"},
            "data_pipeline": {
                "status": pipeline_status,
                "message": pipeline_msg,
                "data_freshness_seconds": data_freshness,
                "cache_hit_rate": pipeline_metrics.get("cache_hit_rate", 0.0),
                "active_symbols": pipeline_metrics.get("active_symbols", 0),
            },
        },
        "uptime_seconds": None,
        "performance": {
            "data_points_collected": pipeline_metrics.get("data_points_collected", 0),
            "data_points_per_second": pipeline_metrics.get("data_points_per_second", 0.0),
            "collection_latency_p95_ms": pipeline_metrics.get("collection_latency_p95_ms", 0.0),
            "signal_latency_p95_ms": pipeline_metrics.get("signal_latency_p95_ms", 0.0),
            "features_computed": pipeline_metrics.get("features_computed", 0),
            "signals_generated": pipeline_metrics.get("signals_generated", 0),
        },
        "data_sources": source_health,
    }
    
    if app_state["startup_time"]:
        health_status["uptime_seconds"] = (
            datetime.utcnow() - app_state["startup_time"]
        ).total_seconds()
    
    return health_status


# Graceful shutdown handler
def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    app_state["shutdown_requested"] = True
    sys.exit(0)


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
