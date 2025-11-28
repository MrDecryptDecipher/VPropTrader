"""SQLite database client"""

import aiosqlite
from pathlib import Path
from loguru import logger
from app.core import settings


class Database:
    """Async SQLite database client"""
    
    def __init__(self):
        self.db_path = Path(settings.database_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        logger.info(f"Database initialized: {self.db_path}")
    
    @property
    def connection(self):
        """Get database connection"""
        return self.conn
    
    async def connect(self):
        """Connect to database"""
        self.conn = await aiosqlite.connect(str(self.db_path))
        await self._create_tables()
        logger.info("Database connected")
    
    async def _create_tables(self):
        """Create required tables"""
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                price REAL,
                quantity REAL,
                pnl REAL
            )
        """)
        await self.conn.commit()
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("Database closed")
    
    async def disconnect(self):
        """Alias for close"""
        await self.close()


# Global instance
db = Database()
