"""Main FastAPI application entry point"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import signal
import sys
from datetime import datetime

from app.core import settings, setup_logging


# Initialize logging
setup_logging()

# Global state
app_state = {
    "startup_time": None,
    "shutdown_requested": False,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown"""
    # Startup
    app_state["startup_time"] = datetime.utcnow()
    logger.info("=" * 60)
    logger.info("Starting Quant Ω Supra AI Sidecar Service")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Host: {settings.host}:{settings.port}")
    logger.info(f"Symbols: {settings.symbols_list}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}")
    logger.info(f"Database: {settings.database_path}")
    logger.info(f"Model Path: {settings.model_path}")
    logger.info(f"FRED API: {settings.fred_api_url}")
    logger.info("=" * 60)
    
    # Initialize storage connections
    from app.data.database import db
    from app.data.redis_client import redis_client
    from app.data.vector_store import vector_store
    from app.data.mt5_client import mt5_client
    from app.data.fred_client import fred_client
    from app.data.calendar_scraper import calendar_scraper
    from app.data.correlation_engine import correlation_engine
    from app.data.sentiment_analyzer import sentiment_analyzer
    
    try:
        # Connect to database
        await db.connect()
        
        # Connect to Redis
        await redis_client.connect()
        
        # Initialize FAISS
        vector_store.initialize()
        
        # Connect to MT5
        if mt5_client.connect():
            logger.info("✓ MT5 connected successfully")
        else:
            logger.warning("⚠ MT5 connection failed - will retry on demand")
        
        # Test FRED API
        if settings.fred_api_key:
            indicators = await fred_client.get_macro_indicators()
            logger.info(f"✓ FRED API connected - Retrieved {len([v for v in indicators.values() if v is not None])} indicators")
        else:
            logger.warning("⚠ FRED API key not configured")
        
        # Fetch calendar events
        events = await calendar_scraper.fetch_events()
        logger.info(f"✓ Calendar: {len(events)} high-impact events loaded")
        
        # Initialize correlations
        if mt5_client.connected:
            await correlation_engine.update_correlations()
        
        # Load sentiment model (lazy loading)
        sentiment_analyzer.load_model()
        
        # Bootstrap data collection (if needed and MT5 available)
        bootstrap_enabled = settings.bootstrap_on_startup if hasattr(settings, 'bootstrap_on_startup') else True
        
        if bootstrap_enabled and mt5_client.connected:
            try:
                from app.data.bootstrap_collector import bootstrap_collector
                logger.info("Checking bootstrap data collection...")
                bootstrap_success = await bootstrap_collector.run_bootstrap()
                
                if bootstrap_success:
                    # Get and log data quality metrics
                    metrics = await bootstrap_collector.get_data_quality_metrics()
                    logger.info(f"✓ Bootstrap complete: {metrics.get('total_bars', 0)} bars collected")
                    logger.info(f"  Real data: {metrics.get('real_bars', 0)} bars ({100 - metrics.get('synthetic_percentage', 0):.1f}%)")
                    logger.info(f"  Synthetic data: {metrics.get('synthetic_bars', 0)} bars ({metrics.get('synthetic_percentage', 0):.1f}%)")
                else:
                    logger.warning("⚠ Bootstrap failed - system may have limited functionality")
            except Exception as e:
                logger.warning(f"Bootstrap collection skipped: {e}")
        else:
            logger.info("✓ Bootstrap collection skipped (MT5 not available or disabled)")
        
        # Train ML models if needed (bootstrap)
        try:
            from app.ml.bootstrap_trainer import bootstrap_trainer
            training_success = await bootstrap_trainer.train_if_needed()
            
            if training_success:
                logger.info("✓ ML models ready")
                
                # Get training status
                status = bootstrap_trainer.get_training_status()
                logger.info(f"  ONNX models: RF={status['rf_onnx_exists']}, LSTM={status['lstm_onnx_exists']}")
                logger.info(f"  Native models: RF={status['rf_native_exists']}, LSTM={status['lstm_native_exists']}")
            else:
                logger.warning("⚠ ML model training failed - will use rule-based fallback")
        except Exception as e:
            logger.warning(f"⚠ ML model training skipped: {e}")
        
        # Load ML models
        try:
            from app.ml.model_manager import model_manager
            model_load_success = await model_manager.load_models()
            if model_load_success:
                logger.info("✓ ML models loaded successfully")
            else:
                logger.warning("⚠ ML models not loaded - will use defaults")
        except Exception as e:
            logger.warning(f"⚠ ML models not loaded: {e}")
        
        # Start background tasks
        import asyncio
        from app.ml.retraining_engine import schedule_nightly_retrain, schedule_drift_checks
        from app.analytics.trade_logger import schedule_daily_digest
        
        # Schedule nightly retraining
        asyncio.create_task(schedule_nightly_retrain())
        logger.info("✓ Nightly retraining scheduler started")
        
        # Schedule drift checks
        asyncio.create_task(schedule_drift_checks())
        logger.info("✓ Drift detection scheduler started")
        
        # Schedule daily digest generation
        asyncio.create_task(schedule_daily_digest())
        logger.info("✓ Daily digest scheduler started")
        
        # Start high-frequency data orchestrator
        try:
            from app.data.high_frequency_orchestrator import HighFrequencyDataOrchestrator
            
            # Get API keys from settings
            api_keys = {}
            if hasattr(settings, 'alphavantage_api_key') and settings.alphavantage_api_key:
                api_keys['alphavantage'] = settings.alphavantage_api_key
            if hasattr(settings, 'twelvedata_api_key') and settings.twelvedata_api_key:
                api_keys['twelvedata'] = settings.twelvedata_api_key
            if hasattr(settings, 'polygon_api_key') and settings.polygon_api_key:
                api_keys['polygon'] = settings.polygon_api_key
            
            # Initialize orchestrator with generic symbols
            orchestrator = HighFrequencyDataOrchestrator(
                symbols=['NAS100', 'XAUUSD', 'EURUSD'],  # Generic symbols
                collection_interval=1,  # 1-second collection
                max_retries=3,
                api_keys=api_keys
            )
            
            # Start orchestrator as background task
            await orchestrator.start()
            app_state["orchestrator"] = orchestrator
            logger.info("✓ High-frequency data orchestrator started")
            
        except Exception as e:
            logger.error(f"⚠ Failed to start data orchestrator: {e}", exc_info=True)
            logger.warning("Continuing without real-time data collection")
        
        logger.info("✓ Sidecar Service started successfully")
        
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
