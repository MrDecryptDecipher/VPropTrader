"""Logging configuration with rotation"""

import sys
from pathlib import Path
from loguru import logger
from .config import settings


def setup_logging():
    """Configure loguru logger with rotation and formatting"""
    
    # Remove default handler
    logger.remove()
    
    # Console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # File handler with rotation
    log_path = Path("./logs")
    log_path.mkdir(exist_ok=True)
    
    logger.add(
        log_path / "sidecar_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="00:00",  # Rotate at midnight
        retention="30 days",  # Keep logs for 30 days
        compression="zip",  # Compress old logs
    )
    
    # Error file handler
    logger.add(
        log_path / "errors_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="00:00",
        retention="90 days",
        compression="zip",
    )
    
    logger.info(f"Logging initialized - Level: {settings.log_level}, Environment: {settings.environment}")
    
    return logger
