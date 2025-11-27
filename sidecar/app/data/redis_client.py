"""Redis client for caching and pub/sub with In-Memory Fallback"""

import redis.asyncio as aioredis
from loguru import logger
from app.core import settings
import json

class RedisClient:
    """Async Redis client with In-Memory Fallback"""
    
    def __init__(self):
        self.client = None
        self.host = settings.redis_host
        self.port = settings.redis_port
        self.memory_store = {} # Fallback store
        logger.info(f"RedisClient initialized: {self.host}:{self.port}")
    
    @property
    def connected(self) -> bool:
        """Check if Redis is connected"""
        return self.client is not None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = await aioredis.from_url(
                f"redis://{self.host}:{self.port}",
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Switching to IN-MEMORY mode.")
            self.client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis closed")
    
    async def disconnect(self):
        """Alias for close"""
        await self.close()

    # --- Proxy Methods with Fallback ---

    async def get(self, key):
        if self.client:
            return await self.client.get(key)
        return self.memory_store.get(key)

    async def set(self, key, value, ex=None):
        if self.client:
            return await self.client.set(key, value, ex=ex)
        self.memory_store[key] = value
        return True

    async def delete(self, key):
        if self.client:
            return await self.client.delete(key)
        if key in self.memory_store:
            del self.memory_store[key]
            return 1
        return 0

    async def lrange(self, key, start, end):
        if self.client:
            return await self.client.lrange(key, start, end)
        # Simple list emulation
        val = self.memory_store.get(key, [])
        if not isinstance(val, list): return []
        if end == -1: return val[start:]
        return val[start:end+1]

    async def rpush(self, key, *values):
        if self.client:
            return await self.client.rpush(key, *values)
        if key not in self.memory_store:
            self.memory_store[key] = []
        if not isinstance(self.memory_store[key], list):
            return 0 # Error type mismatch
        self.memory_store[key].extend(values)
        return len(self.memory_store[key])

# Global instance
redis_client = RedisClient()
