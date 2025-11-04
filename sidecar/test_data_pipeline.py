"""
Comprehensive Test Suite for Continuous Data Pipeline

Tests all components of the high-frequency data collection system:
- Data validators
- Feature computation
- Circuit breakers
- Symbol mapping
- Redis/SQLite storage
- End-to-end collection cycle
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from app.data.data_validator import DataValidator, ValidationResult
from app.data.base_fetcher import MarketData
from app.data.circuit_breaker import CircuitBreaker, CircuitBreakerOpen, CircuitState
from app.data.symbol_mapper import SymbolMapper
from app.core.metrics import MetricsCollector


class TestDataValidator:
    """Test data validation and quality scoring"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = DataValidator(quality_threshold=0.8)
    
    def test_valid_data(self):
        """Test validation of good quality data"""
        bar = MarketData(
            symbol="NAS100",
            timestamp=datetime.now(),
            open=15000.0,
            high=15010.0,
            low=14990.0,
            close=15005.0,
            volume=1000,
            source="yahoo"
        )
        
        result = self.validator.validate(bar)
        assert result.is_valid
        assert result.quality_score > 0.8
        assert len(result.issues) == 0
    
    def test_invalid_ohlc_relationship(self):
        """Test detection of invalid OHLC relationships"""
        bar = MarketData(
            symbol="NAS100",
            timestamp=datetime.now(),
            open=15000.0,
            high=14990.0,  # High < Open (invalid)
            low=14990.0,
            close=15005.0,
            volume=1000,
            source="yahoo"
        )
        
        result = self.validator.validate(bar)
        assert not result.is_valid
        assert "OHLC relationship" in str(result.issues)
    
    def test_zero_volume(self):
        """Test handling of zero volume"""
        bar = MarketData(
            symbol="NAS100",
            timestamp=datetime.now(),
            open=15000.0,
            high=15010.0,
            low=14990.0,
            close=15005.0,
            volume=0,  # Zero volume
            source="yahoo"
        )
        
        result = self.validator.validate(bar)
        assert result.quality_score < 1.0  # Reduced quality
        assert any("volume" in issue.lower() for issue in result.issues)
    
    def test_stale_data(self):
        """Test detection of stale data"""
        old_timestamp = datetime.now() - timedelta(minutes=10)
        bar = MarketData(
            symbol="NAS100",
            timestamp=old_timestamp,
            open=15000.0,
            high=15010.0,
            low=14990.0,
            close=15005.0,
            volume=1000,
            source="yahoo"
        )
        
        result = self.validator.validate(bar)
        assert result.quality_score < 1.0
        assert any("stale" in issue.lower() for issue in result.issues)
    
    def test_batch_validation(self):
        """Test batch validation with mixed quality data"""
        bars = [
            MarketData("NAS100", datetime.now(), 15000, 15010, 14990, 15005, 1000, "yahoo"),
            MarketData("XAUUSD", datetime.now(), 2000, 2010, 1990, 2005, 500, "yahoo"),
            MarketData("EURUSD", datetime.now(), 1.1, 1.11, 1.09, 1.105, 0, "yahoo"),  # Zero volume
        ]
        
        valid_bars, quality_score = self.validator.validate_batch(bars)
        
        assert len(valid_bars) >= 2  # At least 2 should pass
        assert 0.0 <= quality_score <= 1.0


class TestCircuitBreaker:
    """Test circuit breaker pattern"""
    
    @pytest.mark.asyncio
    async def test_closed_state_success(self):
        """Test normal operation in CLOSED state"""
        breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=1)
        
        async def successful_call():
            return "success"
        
        result = await breaker.call(successful_call)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_open_after_failures(self):
        """Test circuit opens after threshold failures"""
        breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=1)
        
        async def failing_call():
            raise Exception("API Error")
        
        # Trigger failures
        for i in range(3):
            try:
                await breaker.call(failing_call)
            except Exception:
                pass
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count >= 3
        
        # Next call should fail fast
        with pytest.raises(CircuitBreakerOpen):
            await breaker.call(failing_call)
    
    @pytest.mark.asyncio
    async def test_half_open_recovery(self):
        """Test recovery through HALF_OPEN state"""
        breaker = CircuitBreaker(failure_threshold=2, timeout_seconds=1)
        
        async def failing_call():
            raise Exception("API Error")
        
        async def successful_call():
            return "success"
        
        # Open the circuit
        for i in range(2):
            try:
                await breaker.call(failing_call)
            except Exception:
                pass
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout
        await asyncio.sleep(1.1)
        
        # Successful call should close circuit
        result = await breaker.call(successful_call)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
    
    def test_get_stats(self):
        """Test statistics collection"""
        breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        
        stats = breaker.get_stats()
        assert stats["state"] == "CLOSED"
        assert stats["failure_threshold"] == 5
        assert stats["timeout_seconds"] == 60
        assert stats["total_calls"] == 0


class TestSymbolMapper:
    """Test symbol mapping functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mapper = SymbolMapper()
    
    def test_broker_to_generic(self):
        """Test broker symbol to generic symbol conversion"""
        assert self.mapper.to_generic_symbol("US100.e") == "NAS100"
        assert self.mapper.to_generic_symbol("XAUUSD") == "XAUUSD"
        assert self.mapper.to_generic_symbol("EURUSD") == "EURUSD"
    
    def test_generic_to_broker(self):
        """Test generic symbol to broker symbol conversion"""
        assert self.mapper.to_broker_symbol("NAS100") == "US100.e"
        assert self.mapper.to_broker_symbol("XAUUSD") == "XAUUSD"
    
    def test_generic_to_providers(self):
        """Test generic symbol to data provider symbols"""
        assert self.mapper.to_yahoo_symbol("NAS100") == "NQ=F"
        assert self.mapper.to_twelve_data_symbol("NAS100") == "NAS100"
        assert self.mapper.to_alpha_vantage_symbol("NAS100") == "NDX"
        assert self.mapper.to_polygon_symbol("NAS100") == "I:NDX"
    
    def test_get_all_mappings(self):
        """Test getting all mappings for a symbol"""
        mappings = self.mapper.get_all_mappings("NAS100")
        
        assert mappings["generic"] == "NAS100"
        assert mappings["broker"] == "US100.e"
        assert "yahoo" in mappings["providers"]
        assert len(mappings["broker_variants"]) >= 1
    
    def test_is_valid_symbol(self):
        """Test symbol validation"""
        assert self.mapper.is_valid_generic_symbol("NAS100")
        assert self.mapper.is_valid_broker_symbol("US100.e")
        assert not self.mapper.is_valid_generic_symbol("INVALID")


class TestMetricsCollector:
    """Test metrics collection"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.metrics = MetricsCollector(window_size=100)
    
    def test_counter_operations(self):
        """Test counter increment and retrieval"""
        self.metrics.increment_counter("test_counter", 5)
        assert self.metrics.get_counter("test_counter") == 5
        
        self.metrics.increment_counter("test_counter", 3)
        assert self.metrics.get_counter("test_counter") == 8
    
    def test_gauge_operations(self):
        """Test gauge set and retrieval"""
        self.metrics.set_gauge("test_gauge", 42.5)
        assert self.metrics.get_gauge("test_gauge") == 42.5
        
        self.metrics.set_gauge("test_gauge", 100.0)
        assert self.metrics.get_gauge("test_gauge") == 100.0
    
    def test_histogram_stats(self):
        """Test histogram statistics calculation"""
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for v in values:
            self.metrics.record_value("test_histogram", v)
        
        stats = self.metrics.get_histogram_stats("test_histogram")
        assert stats["count"] == 10
        assert stats["min"] == 10
        assert stats["max"] == 100
        assert stats["mean"] == 55.0
        assert stats["p50"] == 50
    
    def test_api_call_recording(self):
        """Test API call metrics recording"""
        self.metrics.record_api_call("yahoo", True, 50.0)
        self.metrics.record_api_call("yahoo", True, 75.0)
        self.metrics.record_api_call("yahoo", False, 200.0)
        
        assert self.metrics.get_counter("api_calls_yahoo") == 3
        assert self.metrics.get_counter("api_calls_yahoo_success") == 2
        assert self.metrics.get_counter("api_calls_yahoo_failure") == 1
        
        latency_stats = self.metrics.get_histogram_stats("api_latency_yahoo")
        assert latency_stats["count"] == 3
    
    def test_cache_hit_rate(self):
        """Test cache hit rate calculation"""
        self.metrics.record_cache_access(hit=True)
        self.metrics.record_cache_access(hit=True)
        self.metrics.record_cache_access(hit=False)
        
        hit_rate = self.metrics.get_gauge("cache_hit_rate")
        assert hit_rate == pytest.approx(2/3, rel=0.01)
    
    def test_get_summary(self):
        """Test metrics summary generation"""
        self.metrics.increment_counter("data_points_collected", 1000)
        self.metrics.set_gauge("active_symbols", 3)
        self.metrics.record_value("collection_cycle_latency", 50.0)
        
        summary = self.metrics.get_summary()
        assert "data_points_collected" in summary
        assert "active_symbols" in summary
        assert summary["data_points_collected"] == 1000
        assert summary["active_symbols"] == 3


@pytest.mark.asyncio
async def test_integration_data_flow():
    """
    Integration test: Simulate complete data flow
    
    Tests the flow: Fetch -> Validate -> Store -> Retrieve
    """
    from app.data.redis_knowledge_base import RedisKnowledgeBase
    from app.data.sqlite_store import SQLiteHistoricalStore
    
    # Initialize components
    redis_kb = RedisKnowledgeBase()
    sqlite_store = SQLiteHistoricalStore(db_path=":memory:")  # In-memory for testing
    validator = DataValidator()
    
    try:
        await redis_kb.initialize()
        await sqlite_store.initialize()
        
        # Create test data
        test_bar = MarketData(
            symbol="NAS100",
            timestamp=datetime.now(),
            open=15000.0,
            high=15010.0,
            low=14990.0,
            close=15005.0,
            volume=1000,
            source="test"
        )
        
        # Validate
        result = validator.validate(test_bar)
        assert result.is_valid
        
        # Store in Redis
        await redis_kb.store_bar("NAS100", test_bar)
        
        # Store in SQLite
        await sqlite_store.buffer_write(test_bar)
        await sqlite_store.flush_buffer()
        
        # Retrieve from Redis
        retrieved = await redis_kb.get_latest("NAS100")
        assert retrieved is not None
        assert retrieved.close == 15005.0
        
        # Retrieve from SQLite
        historical = await sqlite_store.get_historical("NAS100", days=1)
        assert len(historical) > 0
        
        print("✓ Integration test passed: Data flow working correctly")
        
    finally:
        await redis_kb.close()
        await sqlite_store.stop_background_flush()


if __name__ == "__main__":
    print("Running Continuous Data Pipeline Tests...")
    print("=" * 60)
    
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
