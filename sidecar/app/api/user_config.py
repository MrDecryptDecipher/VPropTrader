"""
User Config API
Endpoints for Electron App to configure Prop Firm settings.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.data.user_db import user_db, PropFirmConfig, PropRules

router = APIRouter()

class ConfigRequest(BaseModel):
    user_id: int = 1 # Default for single user
    firm: PropFirmConfig
    rules: PropRules

@router.on_event("startup")
async def startup_db():
    await user_db.init_db()

@router.post("/config/prop-firm")
async def save_prop_config(config: ConfigRequest):
    """Save Prop Firm credentials and rules."""
    try:
        firm_id = await user_db.save_prop_config(config.user_id, config.firm, config.rules)
        return {"status": "success", "firm_id": firm_id, "message": "Configuration saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/prop-firm")
async def get_prop_config():
    """Get current active configuration."""
    try:
        config = await user_db.get_active_config()
        if not config:
            return {"status": "empty", "message": "No active configuration found"}
        return {"status": "success", "data": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
