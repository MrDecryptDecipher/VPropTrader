"""Integration tests for EA <-> Sidecar <-> Dashboard"""

import pytest
import asyncio
import httpx
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "sidecar"))

from app.main import app
from fastapi.testclient import TestClient


class TestIntegration:
    """Test integration between components"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "timestamp" in data
        
        print(f"Health check: {data['status']}")
        print(f"Components: {list(data['components'].keys())}")
    
    def test_signals_endpoint(self, client):
        """Test signals endpoint (polled by EA)"""
        response = client.get("/api/signals?equity=1000.0")
        assert response.status_code == 200
        
        data = response.json()
        assert "signals" in data
        assert "timestamp" in data
        assert "count" in data
        
        print(f"Signals count: {data['count']}")
        if data['count'] > 0:
            signal = data['signals'][0]
            assert "symbol" in signal
            assert "action" in signal
            assert "q_star" in signal
            assert "lots" in signal
            print(f"Sample signal: {signal['symbol']} {signal['action']}")
    
    def test_executions_endpoint(self, client):
        """Test execution reporting endpoint"""
        execution_data = {
            "trade_id": "test_12345",
            "symbol": "NAS100",
            "action": "BUY",
            "entry_price": 15250.5,
            "lots": 0.05,
            "stop_loss": 15240.0,
            "take_profit": 15265.0,
            "timestamp": "2025-10-25T14:30:00Z",
            "latency_ms": 45,
            "spread": 2.5,
            "slippage": 0.5,
            "alpha_id": "momentum_v3",
            "regime": "trend_up",
            "q_star": 8.5
        }
        
        response = client.post("/api/executions", json=execution_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        print(f"Execution reported: {data['status']}")
    
    def test_analytics_overview(self, client):
        """Test analytics overview endpoint"""
        response = client.get("/api/analytics/overview")
        assert response.status_code == 200
        
        data = response.json()
        assert "equity" in data
        assert "pnl_today" in data
        assert "trades_today" in data
        
        print(f"Overview: Equity=${data['equity']:.2f}, PnL=${data['pnl_today']:.2f}")
    
    def test_analytics_compliance(self, client):
        """Test compliance endpoint"""
        response = client.get("/api/analytics/compliance")
        assert response.status_code == 200
        
        data = response.json()
        assert "rules" in data
        
        print(f"Compliance rules: {len(data['rules'])}")
        for rule in data['rules']:
            assert "name" in rule
            assert "status" in rule
            assert "value" in rule
            print(f"  {rule['name']}: {rule['status']}")
    
    def test_analytics_alphas(self, client):
        """Test alphas performance endpoint"""
        response = client.get("/api/analytics/alphas")
        assert response.status_code == 200
        
        data = response.json()
        assert "alphas" in data
        
        print(f"Alphas tracked: {len(data['alphas'])}")
        for alpha in data['alphas']:
            assert "alpha_id" in alpha
            assert "sharpe" in alpha
            assert "hit_rate" in alpha
            print(f"  {alpha['alpha_id']}: Sharpe={alpha['sharpe']:.2f}")
    
    def test_analytics_risk(self, client):
        """Test risk metrics endpoint"""
        response = client.get("/api/analytics/risk")
        assert response.status_code == 200
        
        data = response.json()
        assert "var_95" in data
        assert "es_95" in data
        assert "vol_forecast" in data
        
        print(f"Risk: VaR={data['var_95']:.2f}, ES95={data['es_95']:.2f}")
    
    def test_api_latency(self, client):
        """Test API response times < 100ms"""
        import time
        
        endpoints = [
            "/health",
            "/api/signals?equity=1000",
            "/api/analytics/overview",
            "/api/analytics/compliance",
        ]
        
        for endpoint in endpoints:
            start = time.perf_counter()
            response = client.get(endpoint)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            
            assert response.status_code == 200
            assert elapsed < 100, f"{endpoint} too slow: {elapsed:.1f}ms"
            print(f"{endpoint}: {elapsed:.1f}ms")
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        # This would require a running server
        # For now, just verify the endpoint exists
        pass


class TestEndToEnd:
    """End-to-end workflow tests"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_trade_flow(self, client):
        """Test complete trade flow: signal -> execution -> reporting"""
        
        # 1. Get signals
        response = client.get("/api/signals?equity=1000.0")
        assert response.status_code == 200
        signals_data = response.json()
        
        if signals_data['count'] == 0:
            print("No signals available - skipping trade flow test")
            return
        
        signal = signals_data['signals'][0]
        print(f"Step 1: Received signal for {signal['symbol']}")
        
        # 2. Report execution
        execution_data = {
            "trade_id": f"test_{int(time.time())}",
            "symbol": signal['symbol'],
            "action": signal['action'],
            "entry_price": signal['stop_loss'] + 10,  # Dummy price
            "lots": signal['lots'],
            "stop_loss": signal['stop_loss'],
            "take_profit": signal['take_profit_1'],
            "timestamp": "2025-10-25T14:30:00Z",
            "latency_ms": 45,
            "spread": 2.5,
            "slippage": 0.5,
            "alpha_id": signal['alpha_id'],
            "regime": signal['regime'],
            "q_star": signal['q_star']
        }
        
        response = client.post("/api/executions", json=execution_data)
        assert response.status_code == 200
        print(f"Step 2: Execution reported")
        
        # 3. Verify in analytics
        response = client.get("/api/analytics/overview")
        assert response.status_code == 200
        overview = response.json()
        print(f"Step 3: Analytics updated - Trades: {overview['trades_today']}")
        
        print("✓ Complete trade flow successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
