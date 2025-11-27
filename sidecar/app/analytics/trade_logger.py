"""Trade logger and daily digest generator"""

import asyncio
from loguru import logger


async def schedule_daily_digest():
    """Schedule daily digest generation"""
    logger.info("Daily digest scheduler started (stub implementation)")
    while True:
        await asyncio.sleep(86400)  # Sleep for 24 hours
