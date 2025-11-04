"""
Metrics Collection - Monitoring and observability for data pipeline

This module provides comprehensive metrics collection for the continuous data pipeline,
including counters, gauges, and histograms for performance monitoring.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict, deque
import asyncio
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and tracks metrics for the data pipeline
    
    Metrics Types:
    - Counters: Monotonically increasing values (e.g., total API calls)
    - Gauges: Point-in-time values (e.g., cache hit rate)
    - Histograms: Distribution of values (e.g., latency percentiles)
    """
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize metrics collector
        
        Args:
            window_size: Number of samples to keep for histogram calculations
        """
        self.window_size = window_size
        
        # Counters (cumulative)
        self.counters: Dict[str, int] = defaultdict(int)
        
        # Gauges (current values)
        self.gauges: Dict[str, float] = {}
        
        # Histograms (sliding window of values)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        
        # Metadata
        self.start_time = datetime.now()
        self.last_reset = datetime.now()
        
        logger.info(f"MetricsCollector initialized with window_size={window_size}")
    
    # ===== Counter Methods =====
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter by value"""
        self.counters[name] += value
    
    def get_counter(self, name: str) -> int:
        """Get current counter value"""
        return self.counters.get(name, 0)
    
    def reset_counter(self, name: str):
        """Reset a counter to zero"""
        self.counters[name] = 0
    
    # ===== Gauge Methods =====
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge to a specific value"""
        self.gauges[name] = value
    
    def get_gauge(self, name: str) -> Optional[float]:
        """Get current gauge value"""
        return self.gauges.get(name)
    
    # ===== Histogram Methods =====
    
    def record_value(self, name: str, value: float):
        """Record a value in a histogram"""
        self.histograms[name].append(value)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a histogram
        
        Returns:
            Dictionary with min, max, mean, p50, p95, p99
        """
        values = list(self.histograms.get(name, []))
        
        if not values:
            return {
                "count": 0,
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "mean": sum(sorted_values) / count,
            "p50": sorted_values[int(count * 0.50)],
            "p95": sorted_values[int(count * 0.95)] if count > 20 else sorted_values[-1],
            "p99": sorted_values[int(count * 0.99)] if count > 100 else sorted_values[-1],
        }
    
    # ===== Data Pipeline Specific Metrics =====
    
    def record_api_call(self, source: str, success: bool, latency_ms: float):
        """Record an API call with source, success status, and latency"""
        # Counters
        self.increment_counter(f"api_calls_total")
        self.increment_counter(f"api_calls_{source}")
        
        if success:
            self.increment_counter(f"api_calls_{source}_success")
        else:
            self.increment_counter(f"api_calls_{source}_failure")
        
        # Histogram
        self.record_value(f"api_latency_{source}", latency_ms)
        self.record_value(f"api_latency_all", latency_ms)
    
    def record_data_point(self, symbol: str, source: str):
        """Record a successfully collected data point"""
        self.increment_counter("data_points_collected")
        self.increment_counter(f"data_points_{symbol}")
        self.increment_counter(f"data_points_source_{source}")
    
    def record_cache_access(self, hit: bool):
        """Record a cache access (hit or miss)"""
        self.increment_counter("cache_accesses")
        if hit:
            self.increment_counter("cache_hits")
        else:
            self.increment_counter("cache_misses")
        
        # Update cache hit rate gauge
        total = self.get_counter("cache_accesses")
        hits = self.get_counter("cache_hits")
        self.set_gauge("cache_hit_rate", hits / total if total > 0 else 0.0)
    
    def record_feature_computation(self, symbol: str, computation_time_ms: float):
        """Record feature computation time"""
        self.increment_counter("features_computed")
        self.increment_counter(f"features_computed_{symbol}")
        self.record_value("feature_computation_time", computation_time_ms)
    
    def record_signal_generation(self, latency_ms: float):
        """Record signal generation latency"""
        self.increment_counter("signals_generated")
        self.record_value("signal_generation_latency", latency_ms)
    
    def record_collection_cycle(self, latency_ms: float, symbols_collected: int):
        """Record a complete collection cycle"""
        self.increment_counter("collection_cycles")
        self.record_value("collection_cycle_latency", latency_ms)
        self.set_gauge("last_collection_symbols", symbols_collected)
        self.set_gauge("last_collection_time", time.time())
    
    def update_data_freshness(self, symbol: str, age_seconds: float):
        """Update data freshness gauge for a symbol"""
        self.set_gauge(f"data_freshness_{symbol}", age_seconds)
        
        # Update overall freshness (max age across all symbols)
        all_freshness = [
            v for k, v in self.gauges.items() 
            if k.startswith("data_freshness_")
        ]
        if all_freshness:
            self.set_gauge("data_freshness_max", max(all_freshness))
    
    def set_active_symbols(self, count: int):
        """Set the number of active symbols being tracked"""
        self.set_gauge("active_symbols", count)
    
    # ===== Reporting Methods =====
    
    def get_all_metrics(self) -> Dict:
        """Get all metrics in a structured format"""
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self.histograms.keys()
            }
        }
    
    def get_summary(self) -> Dict:
        """Get a summary of key metrics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate rates
        api_calls_rate = self.get_counter("api_calls_total") / uptime if uptime > 0 else 0
        data_points_rate = self.get_counter("data_points_collected") / uptime if uptime > 0 else 0
        
        # Get latency stats
        collection_latency = self.get_histogram_stats("collection_cycle_latency")
        signal_latency = self.get_histogram_stats("signal_generation_latency")
        
        return {
            "uptime_seconds": uptime,
            "data_points_collected": self.get_counter("data_points_collected"),
            "data_points_per_second": data_points_rate,
            "api_calls_total": self.get_counter("api_calls_total"),
            "api_calls_per_second": api_calls_rate,
            "cache_hit_rate": self.get_gauge("cache_hit_rate") or 0.0,
            "active_symbols": self.get_gauge("active_symbols") or 0,
            "data_freshness_max": self.get_gauge("data_freshness_max") or 0.0,
            "collection_latency_p95_ms": collection_latency.get("p95", 0.0),
            "signal_latency_p95_ms": signal_latency.get("p95", 0.0),
            "features_computed": self.get_counter("features_computed"),
            "signals_generated": self.get_counter("signals_generated"),
        }
    
    def get_source_health(self) -> Dict[str, Dict]:
        """Get health metrics for each data source"""
        sources = set()
        for key in self.counters.keys():
            if key.startswith("api_calls_") and not key.endswith(("_success", "_failure", "_total")):
                source = key.replace("api_calls_", "")
                sources.add(source)
        
        health = {}
        for source in sources:
            total = self.get_counter(f"api_calls_{source}")
            success = self.get_counter(f"api_calls_{source}_success")
            failure = self.get_counter(f"api_calls_{source}_failure")
            
            success_rate = success / total if total > 0 else 0.0
            latency_stats = self.get_histogram_stats(f"api_latency_{source}")
            
            health[source] = {
                "total_calls": total,
                "success_calls": success,
                "failed_calls": failure,
                "success_rate": success_rate,
                "latency_p95_ms": latency_stats.get("p95", 0.0),
                "latency_mean_ms": latency_stats.get("mean", 0.0),
                "is_healthy": success_rate > 0.8 and latency_stats.get("p95", 0) < 5000
            }
        
        return health
    
    def reset_all(self):
        """Reset all metrics"""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.last_reset = datetime.now()
        logger.info("All metrics reset")
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format
        
        Returns:
            String in Prometheus exposition format
        """
        lines = []
        
        # Export counters
        for name, value in self.counters.items():
            metric_name = f"vproptrader_{name.replace('-', '_')}"
            lines.append(f"# TYPE {metric_name} counter")
            lines.append(f"{metric_name} {value}")
        
        # Export gauges
        for name, value in self.gauges.items():
            metric_name = f"vproptrader_{name.replace('-', '_')}"
            lines.append(f"# TYPE {metric_name} gauge")
            lines.append(f"{metric_name} {value}")
        
        # Export histogram summaries
        for name in self.histograms.keys():
            stats = self.get_histogram_stats(name)
            metric_name = f"vproptrader_{name.replace('-', '_')}"
            
            lines.append(f"# TYPE {metric_name} summary")
            lines.append(f"{metric_name}{{quantile=\"0.5\"}} {stats['p50']}")
            lines.append(f"{metric_name}{{quantile=\"0.95\"}} {stats['p95']}")
            lines.append(f"{metric_name}{{quantile=\"0.99\"}} {stats['p99']}")
            lines.append(f"{metric_name}_count {stats['count']}")
        
        return "\n".join(lines)


# Global metrics collector instance
metrics_collector = MetricsCollector()
