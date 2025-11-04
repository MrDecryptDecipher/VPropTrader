'use client';

import React, { useEffect, useState } from 'react';
import { apiClient, PerformanceMetrics } from '@/lib/api-client';
import { wsClient } from '@/lib/websocket-client';
import {
  CpuChipIcon,
  ClockIcon,
  ServerIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';

export default function PerformancePage() {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    loadMetrics();

    // Subscribe to WebSocket updates
    const unsubscribe = wsClient.on('performance', (data) => {
      if (data) {
        setMetrics(data);
        setLastUpdate(new Date());
      }
    });

    // Fallback polling every 60 seconds
    const interval = setInterval(loadMetrics, 60000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  const loadMetrics = async () => {
    try {
      const data = await apiClient.getPerformance();
      setMetrics(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading performance metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPerformanceColor = (value: number, target: number, isHigherBetter: boolean = true) => {
    const ratio = value / target;
    if (isHigherBetter) {
      if (ratio >= 1.0) return 'text-green-400';
      if (ratio >= 0.8) return 'text-yellow-400';
      return 'text-red-400';
    } else {
      if (ratio <= 1.0) return 'text-green-400';
      if (ratio <= 1.2) return 'text-yellow-400';
      return 'text-red-400';
    }
  };

  const getStatusIcon = (value: number, target: number, isHigherBetter: boolean = true) => {
    const ratio = value / target;
    const isGood = isHigherBetter ? ratio >= 0.9 : ratio <= 1.1;
    
    if (isGood) {
      return <CheckCircleIcon className="h-6 w-6 text-green-500" />;
    } else {
      return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-gray-200">Loading performance metrics...</div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center text-gray-400">
          <CpuChipIcon className="h-16 w-16 mx-auto mb-4 text-gray-600" />
          <p className="text-lg">No performance data available</p>
          <p className="text-sm mt-2">Metrics will appear once the system is running</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2 flex items-center">
            <CpuChipIcon className="h-8 w-8 mr-3 text-purple-400" />
            System Performance
          </h1>
          <p className="text-gray-400">
            Real-time system performance metrics and optimization insights • Last updated:{' '}
            {lastUpdate.toLocaleTimeString()}
          </p>
        </div>

        {/* Scanner Performance */}
        <div className="bg-gray-800 rounded-lg p-6 shadow-lg mb-8">
          <h3 className="text-lg font-semibold text-gray-200 mb-4 flex items-center">
            <ChartBarIcon className="h-5 w-5 mr-2 text-blue-400" />
            Scanner Performance
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Throughput */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Throughput</span>
                {getStatusIcon(metrics.scanner.throughput, 30, true)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.scanner.throughput, 30, true)}`}>
                {metrics.scanner.throughput.toFixed(1)} combos/sec
              </div>
              <div className="text-xs text-gray-500 mt-1">Target: ≥30 combos/sec</div>
              <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                <div
                  className={`h-2 rounded-full ${
                    metrics.scanner.throughput >= 30 ? 'bg-green-500' : 
                    metrics.scanner.throughput >= 24 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min((metrics.scanner.throughput / 40) * 100, 100)}%` }}
                />
              </div>
            </div>

            {/* Skip Rate */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Skip Rate</span>
                {getStatusIcon(metrics.scanner.skip_rate, 90, true)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.scanner.skip_rate, 90, true)}`}>
                {metrics.scanner.skip_rate.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">Target: >90%</div>
              <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                <div
                  className={`h-2 rounded-full ${
                    metrics.scanner.skip_rate >= 90 ? 'bg-green-500' : 
                    metrics.scanner.skip_rate >= 80 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${metrics.scanner.skip_rate}%` }}
                />
              </div>
            </div>

            {/* Avg Scan Time */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Avg Scan Time</span>
                {getStatusIcon(metrics.scanner.avg_scan_time * 1000, 50, false)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.scanner.avg_scan_time * 1000, 50, false)}`}>
                {(metrics.scanner.avg_scan_time * 1000).toFixed(1)}ms
              </div>
              <div className="text-xs text-gray-500 mt-1">Target: &lt;50ms</div>
              <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                <div
                  className={`h-2 rounded-full ${
                    metrics.scanner.avg_scan_time * 1000 <= 50 ? 'bg-green-500' : 
                    metrics.scanner.avg_scan_time * 1000 <= 60 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min((50 / (metrics.scanner.avg_scan_time * 1000)) * 100, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* ML Inference Performance */}
        <div className="bg-gray-800 rounded-lg p-6 shadow-lg mb-8">
          <h3 className="text-lg font-semibold text-gray-200 mb-4 flex items-center">
            <CpuChipIcon className="h-5 w-5 mr-2 text-purple-400" />
            ML Inference Performance
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* RF Latency */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Random Forest</span>
                {getStatusIcon(metrics.ml_inference.rf_latency_ms, 10, false)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.ml_inference.rf_latency_ms, 10, false)}`}>
                {metrics.ml_inference.rf_latency_ms.toFixed(1)}ms
              </div>
              <div className="text-xs text-gray-500 mt-1">Target: &lt;10ms</div>
            </div>

            {/* LSTM Latency */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">LSTM</span>
                {getStatusIcon(metrics.ml_inference.lstm_latency_ms, 15, false)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.ml_inference.lstm_latency_ms, 15, false)}`}>
                {metrics.ml_inference.lstm_latency_ms.toFixed(1)}ms
              </div>
              <div className="text-xs text-gray-500 mt-1">Target: &lt;15ms</div>
            </div>

            {/* GBT Latency */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">GBT Meta-Learner</span>
                {getStatusIcon(metrics.ml_inference.gbt_latency_ms, 20, false)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.ml_inference.gbt_latency_ms, 20, false)}`}>
                {metrics.ml_inference.gbt_latency_ms.toFixed(1)}ms
              </div>
              <div className="text-xs text-gray-500 mt-1">Target: &lt;20ms</div>
            </div>
          </div>
        </div>

        {/* Data Pipeline Performance */}
        <div className="bg-gray-800 rounded-lg p-6 shadow-lg mb-8">
          <h3 className="text-lg font-semibold text-gray-200 mb-4 flex items-center">
            <ServerIcon className="h-5 w-5 mr-2 text-green-400" />
            Data Pipeline Performance
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* MT5 Latency */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">MT5 Data</span>
                {getStatusIcon(metrics.data_pipeline.mt5_latency_ms, 100, false)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.data_pipeline.mt5_latency_ms, 100, false)}`}>
                {metrics.data_pipeline.mt5_latency_ms.toFixed(0)}ms
              </div>
              <div className="text-xs text-gray-500 mt-1">Target: &lt;100ms</div>
            </div>

            {/* Redis Latency */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Redis Cache</span>
                {getStatusIcon(metrics.data_pipeline.redis_latency_ms, 5, false)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.data_pipeline.redis_latency_ms, 5, false)}`}>
                {metrics.data_pipeline.redis_latency_ms.toFixed(1)}ms
              </div>
              <div className="text-xs text-gray-500 mt-1">Target: &lt;5ms</div>
            </div>

            {/* Feature Computation */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Features</span>
                {getStatusIcon(metrics.data_pipeline.feature_compute_ms, 30, false)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.data_pipeline.feature_compute_ms, 30, false)}`}>
                {metrics.data_pipeline.feature_compute_ms.toFixed(1)}ms
              </div>
              <div className="text-xs text-gray-500 mt-1">Target: &lt;30ms</div>
            </div>

            {/* Cache Hit Rate */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Cache Hit Rate</span>
                {getStatusIcon(metrics.data_pipeline.cache_hit_rate, 95, true)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.data_pipeline.cache_hit_rate, 95, true)}`}>
                {metrics.data_pipeline.cache_hit_rate.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 mt-1">Target: >95%</div>
            </div>
          </div>
        </div>

        {/* System Resources */}
        <div className="bg-gray-800 rounded-lg p-6 shadow-lg mb-8">
          <h3 className="text-lg font-semibold text-gray-200 mb-4 flex items-center">
            <ServerIcon className="h-5 w-5 mr-2 text-orange-400" />
            System Resources
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* CPU Usage */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">CPU Usage</span>
                {getStatusIcon(metrics.system.cpu_percent, 80, false)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.system.cpu_percent, 80, false)}`}>
                {metrics.system.cpu_percent.toFixed(1)}%
              </div>
              <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                <div
                  className={`h-2 rounded-full ${
                    metrics.system.cpu_percent <= 70 ? 'bg-green-500' : 
                    metrics.system.cpu_percent <= 85 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${metrics.system.cpu_percent}%` }}
                />
              </div>
            </div>

            {/* Memory Usage */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Memory Usage</span>
                {getStatusIcon(metrics.system.memory_percent, 80, false)}
              </div>
              <div className={`text-2xl font-bold ${getPerformanceColor(metrics.system.memory_percent, 80, false)}`}>
                {metrics.system.memory_percent.toFixed(1)}%
              </div>
              <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                <div
                  className={`h-2 rounded-full ${
                    metrics.system.memory_percent <= 70 ? 'bg-green-500' : 
                    metrics.system.memory_percent <= 85 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${metrics.system.memory_percent}%` }}
                />
              </div>
            </div>

            {/* Uptime */}
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">Uptime</span>
                <ClockIcon className="h-6 w-6 text-blue-500" />
              </div>
              <div className="text-2xl font-bold text-blue-400">
                {Math.floor(metrics.system.uptime_hours)}h {Math.floor((metrics.system.uptime_hours % 1) * 60)}m
              </div>
              <div className="text-xs text-gray-500 mt-1">System running</div>
            </div>
          </div>
        </div>

        {/* Performance Summary */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Performance Notes</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-400">
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">Scanner Optimization:</h4>
              <p>High skip rate (&gt;90%) indicates efficient pre-filtering. Target throughput of 30+ combos/sec ensures all opportunities are evaluated.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">ML Inference:</h4>
              <p>ONNX-optimized models provide sub-20ms inference. Critical for real-time decision making.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">Data Pipeline:</h4>
              <p>Redis caching reduces MT5 API calls. Feature computation is vectorized for speed.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">System Health:</h4>
              <p>Monitor CPU/memory to prevent resource exhaustion. Consider scaling if consistently &gt;80%.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
