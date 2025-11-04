'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { apiClient, RiskMetrics } from '@/lib/api-client';
import { wsClient } from '@/lib/websocket-client';
import {
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export default function RiskPage() {
  const [risk, setRisk] = useState<RiskMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    loadRisk();

    // Subscribe to WebSocket updates
    const unsubscribe = wsClient.on('risk', (data) => {
      if (data) {
        setRisk(data);
        setLastUpdate(new Date());
      }
    });

    // Fallback polling every 30 seconds
    const interval = setInterval(loadRisk, 30000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  const loadRisk = async () => {
    try {
      const data = await apiClient.getRisk();
      setRisk(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading risk metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !risk) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-gray-200">Loading risk metrics...</div>
      </div>
    );
  }

  const symbols = Object.keys(risk.exposure_by_symbol);
  const exposures = Object.values(risk.exposure_by_symbol);
  const volTarget = 0.01; // 1% daily volatility target
  const volDiff = risk.vol_forecast - volTarget;
  const volStatus = Math.abs(volDiff) < 0.002 ? 'good' : volDiff > 0 ? 'high' : 'low';

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2 flex items-center">
            <ShieldExclamationIcon className="h-8 w-8 mr-3 text-blue-400" />
            Risk Monitor
          </h1>
          <p className="text-gray-400">
            Real-time risk metrics and exposure analysis • Last updated:{' '}
            {lastUpdate.toLocaleTimeString()}
          </p>
        </div>

        {/* Top Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* VaR 95 */}
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg border-2 border-red-700">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm text-gray-400">VaR 95%</h3>
              <ExclamationTriangleIcon className="h-6 w-6 text-red-500" />
            </div>
            <div className="text-3xl font-bold text-red-400">
              ${risk.var_95.toFixed(2)}
            </div>
            <p className="text-xs text-gray-500 mt-2">Max loss at 95% confidence</p>
            <div className="mt-3 text-xs">
              <span className="text-gray-400">Target: </span>
              <span className="text-gray-300">≤ $10.00</span>
            </div>
          </div>

          {/* ES 95 */}
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg border-2 border-orange-700">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm text-gray-400">ES 95%</h3>
              <ExclamationTriangleIcon className="h-6 w-6 text-orange-500" />
            </div>
            <div className="text-3xl font-bold text-orange-400">
              ${risk.es_95.toFixed(2)}
            </div>
            <p className="text-xs text-gray-500 mt-2">Avg loss beyond VaR</p>
            <div className="mt-3 text-xs">
              <span className="text-gray-400">Target: </span>
              <span className="text-gray-300">≤ $10.00</span>
            </div>
          </div>

          {/* Volatility Forecast */}
          <div className={`bg-gray-800 rounded-lg p-6 shadow-lg border-2 ${
            volStatus === 'good' ? 'border-green-700' : 
            volStatus === 'high' ? 'border-yellow-700' : 'border-blue-700'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm text-gray-400">Vol Forecast</h3>
              <ChartBarIcon className={`h-6 w-6 ${
                volStatus === 'good' ? 'text-green-500' : 
                volStatus === 'high' ? 'text-yellow-500' : 'text-blue-500'
              }`} />
            </div>
            <div className={`text-3xl font-bold ${
              volStatus === 'good' ? 'text-green-400' : 
              volStatus === 'high' ? 'text-yellow-400' : 'text-blue-400'
            }`}>
              {(risk.vol_forecast * 100).toFixed(2)}%
            </div>
            <p className="text-xs text-gray-500 mt-2">Predicted daily volatility</p>
            <div className="mt-3 text-xs">
              <span className="text-gray-400">Target: </span>
              <span className="text-gray-300">1.00%</span>
              <span className={`ml-2 ${volDiff > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                ({volDiff > 0 ? '+' : ''}{(volDiff * 100).toFixed(2)}%)
              </span>
            </div>
          </div>

          {/* Current Exposure */}
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg border-2 border-blue-700">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm text-gray-400">Total Exposure</h3>
              <ChartBarIcon className="h-6 w-6 text-blue-500" />
            </div>
            <div className="text-3xl font-bold text-blue-400">
              {(Object.values(risk.exposure_by_symbol).reduce((a, b) => a + b, 0) * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-500 mt-2">Portfolio exposure</p>
            <div className="mt-3">
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-blue-500"
                  style={{ 
                    width: `${Math.min(Object.values(risk.exposure_by_symbol).reduce((a, b) => a + b, 0) * 100, 100)}%` 
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Volatility Comparison */}
        <div className="bg-gray-800 rounded-lg p-6 shadow-lg mb-8">
          <h3 className="text-lg font-semibold mb-4">Volatility Target vs Forecast</h3>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="text-sm text-gray-400 mb-2">Target Volatility</div>
              <div className="text-4xl font-bold text-green-400">1.00%</div>
              <p className="text-xs text-gray-500 mt-1">Daily volatility target</p>
            </div>
            <div>
              <div className="text-sm text-gray-400 mb-2">Forecasted Volatility</div>
              <div className={`text-4xl font-bold ${
                volStatus === 'good' ? 'text-green-400' : 
                volStatus === 'high' ? 'text-yellow-400' : 'text-blue-400'
              }`}>
                {(risk.vol_forecast * 100).toFixed(2)}%
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {volStatus === 'good' && 'On target ✓'}
                {volStatus === 'high' && 'Above target - reducing size'}
                {volStatus === 'low' && 'Below target - can increase size'}
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Difference:</span>
              <span className={`font-semibold ${volDiff > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                {volDiff > 0 ? '+' : ''}{(volDiff * 100).toFixed(3)}%
              </span>
            </div>
          </div>
        </div>

        {/* Exposure by Symbol */}
        <div className="bg-gray-800 rounded-lg p-6 shadow-lg mb-8">
          <h3 className="text-lg font-semibold mb-4">Position Sizes by Symbol</h3>
          
          {symbols.length > 0 ? (
            <div className="space-y-4">
              {symbols.map((symbol, index) => {
                const exposure = exposures[index];
                const exposurePct = exposure * 100;
                
                return (
                  <div key={symbol} className="bg-gray-700/50 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-lg font-semibold text-gray-200">{symbol}</span>
                      <span className="text-xl font-bold text-blue-400">
                        {exposurePct.toFixed(2)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full ${
                          exposurePct > 50 ? 'bg-red-500' :
                          exposurePct > 30 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(exposurePct, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between mt-1 text-xs text-gray-500">
                      <span>0%</span>
                      <span>30% (Safe)</span>
                      <span>50% (Warning)</span>
                      <span>100%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center text-gray-400 py-8">
              <ChartBarIcon className="h-12 w-12 mx-auto mb-2 text-gray-600" />
              <p>No active positions</p>
            </div>
          )}
        </div>

        {/* Correlation Matrix Heatmap */}
        {risk.correlation_matrix.length > 0 && symbols.length > 1 && (
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <h3 className="text-lg font-semibold mb-4">Cross-Asset Correlation Matrix</h3>
            <p className="text-sm text-gray-400 mb-4">
              Correlation between symbols (target: &lt;0.3 for diversification)
            </p>
            <Plot
              data={[
                {
                  z: risk.correlation_matrix,
                  x: symbols,
                  y: symbols,
                  type: 'heatmap',
                  colorscale: [
                    [0, '#ef4444'],
                    [0.3, '#fbbf24'],
                    [0.7, '#10b981'],
                    [1, '#3b82f6']
                  ],
                  showscale: true,
                  colorbar: {
                    title: 'Correlation',
                    titleside: 'right',
                    tickmode: 'linear',
                    tick0: -1,
                    dtick: 0.5,
                  },
                },
              ]}
              layout={{
                paper_bgcolor: '#1f2937',
                plot_bgcolor: '#111827',
                font: { color: '#e5e7eb', size: 12 },
                xaxis: { 
                  gridcolor: '#374151',
                  side: 'bottom',
                },
                yaxis: { 
                  gridcolor: '#374151',
                },
                margin: { t: 30, r: 100, b: 50, l: 60 },
                height: 400,
              }}
              config={{
                responsive: true,
                displayModeBar: false,
              }}
              style={{ width: '100%', height: '400px' }}
            />
          </div>
        )}

        {/* Risk Metrics Legend */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Risk Metrics Explained</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-400">
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">VaR (Value at Risk):</h4>
              <p>Maximum expected loss at 95% confidence level. Target: ≤$10</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">ES (Expected Shortfall):</h4>
              <p>Average loss in the worst 5% of cases. Target: ≤$10</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">Volatility Forecast:</h4>
              <p>LSTM-predicted daily volatility. Target: ~1% for optimal sizing</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">Correlation:</h4>
              <p>Cross-asset correlation. Target: &lt;0.3 for diversification</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
