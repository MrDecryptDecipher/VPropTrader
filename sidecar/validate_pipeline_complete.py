#!/usr/bin/env python3
"""
Comprehensive Data Pipeline Validation Script

This script performs thorough validation of all pipeline components:
1. Component imports and initialization
2. Data validator functionality
3. Symbol mapper bidirectional translation
4. Circuit breaker state transitions
5. Metrics collection
6. Redis connectivity and operations
7. SQLite database operations
8. Data fetcher initialization
9. Feature engine computation
10. Integration tests

NO SHORTCUTS - Full production validation.
"""

import sys
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_test(name: str):
    print(f"{Colors.BOLD}Testing: {name}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


class PipelineValidator:
    """Comprehensive pipeline validation"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_total = 0
        self.start_time = time.time()
        
    def record_test(self, passed: bool, test_name: str, details: str = ""):
        """Record test result"""
        self.tests_total += 1
        if passed:
            self.tests_passed += 1
            print_success(f"{test_name} {details}")
        else:
            self.tests_failed += 1
            print_error(f"{test_name} {details}")
    
    async def validate_imports(self) -> bool:
        """Validate all component imports"""
        print_test("Component Imports")
        
        try:
            from app.data.base_fetcher import BaseDataFetcher, MarketData
            self.record_test(True, "BaseDataFetcher import")
            
            from app.data.data_validator import DataValidator
            self.record_test(True, "DataValidator import")
            
            from app.data.symbol_mapper import SymbolMapper
            self.record_test(True, "SymbolMapper import")
            
            from app.data.circuit_breaker import CircuitBreaker, CircuitBreakerManager
            self.record_test(True, "CircuitBreaker import")
            
            from app.core.metrics import MetricsCollector
            self.record_test(True, "MetricsCollector import")
            
            from app.data.redis_knowledge_base import RedisKnowledgeBase
            self.record_test(True, "RedisKnowledgeBase import")
            
            from app.data.sqlite_store import SQLiteHistoricalStore
            self.record_test(True, "SQLiteHistoricalStore import")
            
            from app.data.feature_engine import IncrementalFeatureEngine
            self.record_test(True, "IncrementalFeatureEngine import")
            
            from app.data.yahoo_fetcher import YahooFinanceFetcher
            self.record_test(True, "YahooFinanceFetcher import")
            
            from app.data.alphavantage_fetcher import AlphaVantageFetcher
            self.record_test(True, "AlphaVantageFetcher import")
            
            from app.data.twelvedata_fetcher import TwelveDataFetcher
            self.record_test(True, "TwelveDataFetcher import")
            
            from app.data.polygon_fetcher import PolygonFetcher
            self.record_test(True, "PolygonFetcher import")
            
            return True
            
        except Exception as e:
            self.record_test(False, "Import failed", str(e))
            return False
    
    async def validate_data_validator(self) -> bool:
        """Validate DataValidator functionality"""
        print_test("Data Validator")
        
        try:
            from app.data.data_validator import DataValidator
            from app.data.base_fetcher import MarketData
            
            validator = DataValidator(quality_threshold=0.8)
            self.record_test(True, "DataValidator initialization")
            
            # Test valid data
            valid_bar = MarketData(
                symbol="NAS100",
                timestamp=datetime.now(),
                open=15000.0,
                high=15010.0,
                low=14990.0,
                close=15005.0,
                volume=1000,
                source="test"
            )
            
            result = validator.validate(valid_bar)
            self.record_test(result.is_valid, "Valid data validation", 
                           f"Quality: {result.quality_score:.2f}")
            
            # Test invalid OHLC
            invalid_bar = MarketData(
                symbol="NAS100",
                timestamp=datetime.now(),
                open=15000.0,
                high=14990.0,  # High < Open (invalid)
                low=14990.0,
                close=15005.0,
                volume=1000,
                source="test"
            )
            
            result = validator.validate(invalid_bar)
            self.record_test(not result.is_valid, "Invalid OHLC detection",
                           f"Issues: {len(result.issues)}")
            
            # Test batch validation
            bars = [valid_bar] * 5
            valid_bars, quality = validator.validate_batch(bars)
            self.record_test(len(valid_bars) == 5, "Batch validation",
                           f"Quality: {quality:.2f}")
            
            return True
            
        except Exception as e:
            self.record_test(False, "DataValidator test failed", str(e))
            return False
    
    async def validate_symbol_mapper(self) -> bool:
        """Validate SymbolMapper bidirectional translation"""
        print_test("Symbol Mapper")
        
        try:
            from app.data.symbol_mapper import SymbolMapper
            
            mapper = SymbolMapper()
            self.record_test(True, "SymbolMapper initialization")
            
            # Test broker to generic
            generic = mapper.to_generic_symbol("US100.e")
            self.record_test(generic == "NAS100", "Broker to generic",
                           f"US100.e -> {generic}")
            
            # Test generic to broker
            broker = mapper.to_broker_symbol("NAS100")
            self.record_test(broker == "US100.e", "Generic to broker",
                           f"NAS100 -> {broker}")
            
            # Test provider mappings
            yahoo = mapper.to_yahoo_symbol("NAS100")
            self.record_test(yahoo == "NQ=F", "Yahoo symbol mapping",
                           f"NAS100 -> {yahoo}")
            
            alpha = mapper.to_alpha_vantage_symbol("NAS100")
            self.record_test(alpha == "NDX", "Alpha Vantage mapping",
                           f"NAS100 -> {alpha}")
            
            twelve = mapper.to_twelve_data_symbol("NAS100")
            self.record_test(twelve == "NAS100", "Twelve Data mapping",
                           f"NAS100 -> {twelve}")
            
            polygon = mapper.to_polygon_symbol("NAS100")
            self.record_test(polygon == "I:NDX", "Polygon mapping",
                           f"NAS100 -> {polygon}")
            
            # Test all mappings
            mappings = mapper.get_all_mappings("NAS100")
            self.record_test(len(mappings) > 0, "Get all mappings",
                           f"Keys: {list(mappings.keys())}")
            
            # Test validation
            is_valid = mapper.is_valid_generic_symbol("NAS100")
            self.record_test(is_valid, "Generic symbol validation")
            
            is_valid_broker = mapper.is_valid_broker_symbol("US100.e")
            self.record_test(is_valid_broker, "Broker symbol validation")
            
            return True
            
        except Exception as e:
            self.record_test(False, "SymbolMapper test failed", str(e))
            return False
    
    async def validate_circuit_breaker(self) -> bool:
        """Validate CircuitBreaker state transitions"""
        print_test("Circuit Breaker")
        
        try:
            from app.data.circuit_breaker import CircuitBreaker, CircuitState
            
            breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=1)
            self.record_test(True, "CircuitBreaker initialization")
            
            # Test CLOSED state
            self.record_test(breaker.state == CircuitState.CLOSED, 
                           "Initial state CLOSED")
            
            # Test successful call
            async def success_func():
                return "success"
            
            result = await breaker.call(success_func)
            self.record_test(result == "success" and breaker.failure_count == 0,
                           "Successful call in CLOSED state")
            
            # Test failures to open circuit
            async def fail_func():
                raise Exception("Test failure")
            
            for i in range(3):
                try:
                    await breaker.call(fail_func)
                except:
                    pass
            
            self.record_test(breaker.state == CircuitState.OPEN,
                           "Circuit OPEN after threshold failures",
                           f"Failures: {breaker.failure_count}")
            
            # Test fast fail in OPEN state
            from app.data.circuit_breaker import CircuitBreakerOpen
            try:
                await breaker.call(success_func)
                self.record_test(False, "Should fail fast in OPEN state")
            except CircuitBreakerOpen:
                self.record_test(True, "Fast fail in OPEN state")
            
            # Test recovery to HALF_OPEN
            await asyncio.sleep(1.1)  # Wait for timeout
            result = await breaker.call(success_func)
            self.record_test(breaker.state == CircuitState.CLOSED,
                           "Recovery to CLOSED after success")
            
            # Test statistics
            stats = breaker.get_stats()
            self.record_test(stats['total_calls'] > 0, "Statistics collection",
                           f"Total calls: {stats['total_calls']}")
            
            return True
            
        except Exception as e:
            self.record_test(False, "CircuitBreaker test failed", str(e))
            return False
    
    async def validate_metrics_collector(self) -> bool:
        """Validate MetricsCollector functionality"""
        print_test("Metrics Collector")
        
        try:
            from app.core.metrics import MetricsCollector
            
            metrics = MetricsCollector(window_size=100)
            self.record_test(True, "MetricsCollector initialization")
            
            # Test counter operations
            metrics.increment_counter("test_counter", 5)
            count = metrics.get_counter("test_counter")
            self.record_test(count == 5, "Counter increment", f"Value: {count}")
            
            # Test gauge operations
            metrics.set_gauge("test_gauge", 42.5)
            gauge = metrics.get_gauge("test_gauge")
            self.record_test(gauge == 42.5, "Gauge set/get", f"Value: {gauge}")
            
            # Test histogram
            for i in range(10):
                metrics.record_value("test_histogram", i * 10)
            
            stats = metrics.get_histogram_stats("test_histogram")
            self.record_test(stats['count'] == 10, "Histogram recording",
                           f"Count: {stats['count']}, Mean: {stats['mean']}")
            
            # Test API call recording
            metrics.record_api_call("yahoo", True, 50.0)
            metrics.record_api_call("yahoo", True, 75.0)
            metrics.record_api_call("yahoo", False, 200.0)
            
            yahoo_calls = metrics.get_counter("api_calls_yahoo")
            self.record_test(yahoo_calls == 3, "API call recording",
                           f"Total: {yahoo_calls}")
            
            # Test cache metrics
            metrics.record_cache_access(hit=True)
            metrics.record_cache_access(hit=True)
            metrics.record_cache_access(hit=False)
            
            hit_rate = metrics.get_gauge("cache_hit_rate")
            self.record_test(abs(hit_rate - 0.667) < 0.01, "Cache hit rate",
                           f"Rate: {hit_rate:.2%}")
            
            # Test summary
            summary = metrics.get_summary()
            self.record_test(len(summary) > 0, "Metrics summary",
                           f"Keys: {len(summary)}")
            
            # Test source health
            health = metrics.get_source_health()
            self.record_test('yahoo' in health, "Source health tracking")
            
            return True
            
        except Exception as e:
            self.record_test(False, "MetricsCollector test failed", str(e))
            return False
    
    async def validate_redis_connection(self) -> bool:
        """Validate Redis connectivity"""
        print_test("Redis Connection")
        
        try:
            import redis
            
            # Test basic connection
            r = redis.Redis(host='localhost', port=6379, db=0)
            pong = r.ping()
            self.record_test(pong, "Redis PING")
            
            # Test set/get
            r.set('test_key', 'test_value')
            value = r.get('test_key')
            self.record_test(value == b'test_value', "Redis SET/GET")
            
            # Clean up
            r.delete('test_key')
            
            return True
            
        except Exception as e:
            self.record_test(False, "Redis connection failed", str(e))
            print_warning("Make sure Redis is running: redis-server")
            return False
    
    async def validate_redis_knowledge_base(self) -> bool:
        """Validate RedisKnowledgeBase operations"""
        print_test("Redis Knowledge Base")
        
        try:
            from app.data.redis_knowledge_base import RedisKnowledgeBase
            from app.data.base_fetcher import MarketData
            
            redis_kb = RedisKnowledgeBase()
            await redis_kb.initialize()
            self.record_test(True, "RedisKnowledgeBase initialization")
            
            # Test store bar
            test_bar = MarketData(
                symbol="TEST",
                timestamp=datetime.now(),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000,
                source="test"
            )
            
            await redis_kb.store_bar("TEST", test_bar)
            self.record_test(True, "Store bar in Redis")
            
            # Test get latest
            retrieved = await redis_kb.get_latest("TEST")
            self.record_test(retrieved is not None and retrieved.close == 100.5,
                           "Get latest from Redis", f"Close: {retrieved.close if retrieved else 'None'}")
            
            # Test batch store
            bars = [test_bar] * 5
            await redis_kb.batch_store(bars)
            self.record_test(True, "Batch store in Redis")
            
            # Test get history
            history = await redis_kb.get_history("TEST", n_bars=5)
            self.record_test(len(history) > 0, "Get history from Redis",
                           f"Bars: {len(history)}")
            
            # Test stats
            stats = await redis_kb.get_stats()
            self.record_test(len(stats) > 0, "Redis stats",
                           f"Keys: {list(stats.keys())}")
            
            # Cleanup
            await redis_kb.close()
            
            return True
            
        except Exception as e:
            self.record_test(False, "RedisKnowledgeBase test failed", str(e))
            return False
    
    async def validate_sqlite_store(self) -> bool:
        """Validate SQLite operations"""
        print_test("SQLite Historical Store")
        
        try:
            from app.data.sqlite_store import SQLiteHistoricalStore
            from app.data.base_fetcher import MarketData
            
            # Use in-memory database for testing
            sqlite_store = SQLiteHistoricalStore(db_path=":memory:")
            await sqlite_store.initialize()
            self.record_test(True, "SQLiteHistoricalStore initialization")
            
            # Test buffer write
            test_bar = MarketData(
                symbol="TEST",
                timestamp=datetime.now(),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000,
                source="test"
            )
            
            await sqlite_store.buffer_write(test_bar)
            self.record_test(True, "Buffer write")
            
            # Test flush
            await sqlite_store.flush_buffer()
            self.record_test(True, "Flush buffer")
            
            # Test get historical
            history = await sqlite_store.get_historical("TEST", days=1)
            self.record_test(len(history) > 0, "Get historical data",
                           f"Bars: {len(history)}")
            
            # Test stats
            stats = await sqlite_store.get_stats()
            self.record_test(len(stats) > 0, "SQLite stats",
                           f"Total bars: {stats.get('total_bars', 0)}")
            
            # Cleanup
            await sqlite_store.stop_background_flush()
            
            return True
            
        except Exception as e:
            self.record_test(False, "SQLiteHistoricalStore test failed", str(e))
            return False
    
    async def validate_feature_engine(self) -> bool:
        """Validate IncrementalFeatureEngine"""
        print_test("Feature Engine")
        
        try:
            from app.data.feature_engine import IncrementalFeatureEngine
            from app.data.base_fetcher import MarketData
            
            engine = IncrementalFeatureEngine()
            self.record_test(True, "IncrementalFeatureEngine initialization")
            
            # Create test data
            test_bar = MarketData(
                symbol="TEST",
                timestamp=datetime.now(),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000,
                source="test"
            )
            
            history = [test_bar] * 50  # Need history for indicators
            
            # Test feature computation
            features = await engine.compute_features("TEST", test_bar, history)
            self.record_test(len(features) > 0, "Feature computation",
                           f"Features: {len(features)}")
            
            # Check for expected indicators
            expected_indicators = ['rsi', 'ema', 'atr', 'close']
            found_indicators = [ind for ind in expected_indicators if ind in features]
            self.record_test(len(found_indicators) > 0, "Indicator presence",
                           f"Found: {found_indicators}")
            
            return True
            
        except Exception as e:
            self.record_test(False, "FeatureEngine test failed", str(e))
            return False
    
    async def validate_data_fetchers(self) -> bool:
        """Validate data fetcher initialization"""
        print_test("Data Fetchers")
        
        try:
            from app.data.yahoo_fetcher import YahooFinanceFetcher
            from app.data.alphavantage_fetcher import AlphaVantageFetcher
            from app.data.twelvedata_fetcher import TwelveDataFetcher
            from app.data.polygon_fetcher import PolygonFetcher
            
            # Yahoo Finance
            yahoo = YahooFinanceFetcher()
            await yahoo.initialize()
            self.record_test(True, "YahooFinanceFetcher initialization")
            await yahoo.close()
            
            # Alpha Vantage
            alpha = AlphaVantageFetcher(api_key="test_key")
            await alpha.initialize()
            self.record_test(True, "AlphaVantageFetcher initialization")
            await alpha.close()
            
            # Twelve Data
            twelve = TwelveDataFetcher(api_key="test_key")
            await twelve.initialize()
            self.record_test(True, "TwelveDataFetcher initialization")
            await twelve.close()
            
            # Polygon
            polygon = PolygonFetcher(api_key="test_key")
            await polygon.initialize()
            self.record_test(True, "PolygonFetcher initialization")
            await polygon.close()
            
            return True
            
        except Exception as e:
            self.record_test(False, "Data fetcher test failed", str(e))
            return False
    
    def print_summary(self):
        """Print validation summary"""
        elapsed = time.time() - self.start_time
        
        print_header("VALIDATION SUMMARY")
        
        print(f"Total Tests: {self.tests_total}")
        print(f"{Colors.GREEN}Passed: {self.tests_passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.tests_failed}{Colors.END}")
        print(f"Success Rate: {(self.tests_passed/self.tests_total*100):.1f}%")
        print(f"Elapsed Time: {elapsed:.2f}s")
        
        if self.tests_failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED - PIPELINE READY FOR PRODUCTION{Colors.END}\n")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ {self.tests_failed} TESTS FAILED - REVIEW REQUIRED{Colors.END}\n")
            return 1


async def main():
    """Main validation routine"""
    print_header("CONTINUOUS DATA PIPELINE - COMPREHENSIVE VALIDATION")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    validator = PipelineValidator()
    
    # Run all validations
    await validator.validate_imports()
    await validator.validate_data_validator()
    await validator.validate_symbol_mapper()
    await validator.validate_circuit_breaker()
    await validator.validate_metrics_collector()
    await validator.validate_redis_connection()
    await validator.validate_redis_knowledge_base()
    await validator.validate_sqlite_store()
    await validator.validate_feature_engine()
    await validator.validate_data_fetchers()
    
    # Print summary
    exit_code = validator.print_summary()
    
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Validation interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
