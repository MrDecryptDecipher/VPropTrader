"""
User Database Manager
Handles storage of User identity, Prop Firm credentials, and Trading Rules.
"""

import aiosqlite
import logging
import os
import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DB_PATH = "data/user_config.db"

class PropFirmConfig(BaseModel):
    firm_name: str
    login: str
    password: str
    server: str
    
class PropRules(BaseModel):
    max_daily_loss: float
    max_total_loss: float
    profit_target: float
    trading_hours_start: str # "09:00"
    trading_hours_end: str   # "17:00"
    timezone: str = "UTC"

class UserDB:
    """
    Async SQLite wrapper for User Data.
    """
    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def init_db(self):
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Users Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    email TEXT
                )
            """)
            
            # Prop Firms Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS prop_firms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    firm_name TEXT,
                    login TEXT,
                    password TEXT, -- In production, encrypt this!
                    server TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            
            # Rules Table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    firm_id INTEGER,
                    max_daily_loss REAL,
                    max_total_loss REAL,
                    profit_target REAL,
                    trading_hours_start TEXT,
                    trading_hours_end TEXT,
                    timezone TEXT,
                    FOREIGN KEY(firm_id) REFERENCES prop_firms(id)
                )
            """)
            await db.commit()
            logger.info("User DB initialized.")

    async def save_prop_config(self, user_id: int, config: PropFirmConfig, rules: PropRules):
        """Save Prop Firm credentials and rules."""
        async with aiosqlite.connect(self.db_path) as db:
            # Insert/Update Firm
            cursor = await db.execute("""
                INSERT INTO prop_firms (user_id, firm_name, login, password, server)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, config.firm_name, config.login, config.password, config.server))
            firm_id = cursor.lastrowid
            
            # Insert Rules
            await db.execute("""
                INSERT INTO rules (firm_id, max_daily_loss, max_total_loss, profit_target, 
                                 trading_hours_start, trading_hours_end, timezone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (firm_id, rules.max_daily_loss, rules.max_total_loss, rules.profit_target,
                  rules.trading_hours_start, rules.trading_hours_end, rules.timezone))
            
            await db.commit()
            return firm_id

    async def get_active_config(self):
        """Get the currently active prop firm config and rules."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Get latest active firm
            async with db.execute("""
                SELECT * FROM prop_firms WHERE is_active = 1 ORDER BY id DESC LIMIT 1
            """) as cursor:
                firm = await cursor.fetchone()
                
            if not firm:
                return None
                
            # Get rules for this firm
            async with db.execute("SELECT * FROM rules WHERE firm_id = ?", (firm['id'],)) as cursor:
                rules = await cursor.fetchone()
                
            return {
                'firm': dict(firm),
                'rules': dict(rules) if rules else {}
            }

# Global instance
user_db = UserDB()
