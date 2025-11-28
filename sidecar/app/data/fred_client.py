"""FRED API client for macroeconomic data"""

import httpx
from loguru import logger
from app.core import settings


class FREDClient:
    """Federal Reserve Economic Data API client"""
    
    def __init__(self):
        self.api_key = settings.fred_api_key
        self.api_url = settings.fred_api_url
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info("FREDClient initialized")
    
    async def get_series(self, series_id: str):
        """Get economic data series"""
        try:
            url = f"{self.api_url}/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json"
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"FRED API error: {e}")
            return None
    
    async def get_macro_indicators(self) -> dict:
        """Get key macroeconomic indicators"""
        return {}
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
        logger.info("FREDClient closed")


# Global instance
fred_client = FREDClient()
