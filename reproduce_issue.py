import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add sidecar to path
sys.path.append(os.path.abspath("sidecar"))

# Mock environment variables
os.environ["FRED_API_KEY"] = "test"

from app.main import app

client = TestClient(app)

print("Testing POST /config/prop-firm")
response = client.post("/config/prop-firm", json={
    "user_id": 1,
    "firm": {
        "firm_name": "TestFirm",
        "login": "123",
        "password": "password",
        "server": "server"
    },
    "rules": {
        "max_daily_loss": 100.0,
        "max_total_loss": 200.0,
        "profit_target": 300.0,
        "trading_hours_start": "09:00",
        "trading_hours_end": "17:00",
        "timezone": "UTC"
    }
})

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
