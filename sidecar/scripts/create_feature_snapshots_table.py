"""
Create feature_snapshots table for feature fallback mechanism
"""

import asyncio
import sqlite3
from pathlib import Path
from loguru import logger


async def create_feature_snapshots_table():
    """Create feature_snapshots table in database"""
    
    # Get database path
    db_path = Path(__file__).parent.parent / "data" / "trading.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Creating feature_snapshots table in {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Create feature_snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                features_json TEXT NOT NULL,
                timestamp INTEGER NOT NULL
            )
        """)
        
        # Create index for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_features_symbol_time 
            ON feature_snapshots(symbol, timestamp DESC)
        """)
        
        conn.commit()
        logger.info("✓ feature_snapshots table created successfully")
        
        # Verify table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='feature_snapshots'
        """)
        result = cursor.fetchone()
        
        if result:
            logger.info("✓ Table verification passed")
        else:
            logger.error("✗ Table verification failed")
            
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(create_feature_snapshots_table())
