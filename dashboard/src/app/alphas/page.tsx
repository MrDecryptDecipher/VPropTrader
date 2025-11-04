'use client';

import React, { useEffect, useState } from 'react';
import { apiClient, AlphaPerformance } from '@/lib/api-client';
import { wsClient } from '@/lib/websocket-client';
import {
  ChartBarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  TrophyIcon,
} from '@heroicons/react/24/outline';

export default function AlphasPage() {
  const [alphas, setAlphas] = useState<AlphaPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<keyof AlphaPerformance>('sharpe');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    loadAlphas();

    // Subscribe to WebSocket updates
    const unsubscribe = wsClient.on('alphas', (data) => {
      if (data.alphas) {
        setAlphas(data.alphas);
        setLastUpdate(new Date());
      }
    });

    // Fallback polling every 10 seconds
    const interval = setInterval(loadAlphas, 10000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  const loadAlphas = async () => {
    try {
      const data = await apiClient.getAlphas();
      setAlphas(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading alphas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (column: keyof AlphaPerformance) => {
    if (sortBy === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDirection('desc');
    }
  };

  const sortedAlphas = [...alphas].sort((a, b) => {
    const aValue = a[sortBy];
    const bValue = b[sortBy];
    
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
    }
    
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortDirection === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }
    
    return 0;
  });

  const getPerformanceColor = (value: number, metric: string) => {
    if (metric === 'sharpe') {
      if (value >= 4.0) return 'text-green-400';
      if (value >= 2.0) return 'text-yellow-400';
      return 'text-red-400';
    }
    if (metric === 'hit_rate') {
      if (value >= 0.65) return 'text-green-400';
      if (value >= 0.50) return 'text-yellow-400';
      return 'text-red-400';
    }
    return value >= 0 ? 'text-green-400' : 'text-red-400';
  };

  const getPerformanceBgColor = (value: number, metric: string) => {
    if (metric === 'sharpe') {
      if (value >= 4.0) return 'bg-green-600';
      if (value >= 2.0) return 'bg-yellow-600';
      return 'bg-red-600';
    }
    if (metric === 'hit_rate') {
      if (value >= 0.65) return 'bg-green-600';
      if (value >= 0.50) return 'bg-yellow-600';
      return 'bg-red-600';
    }
    return value >= 0 ? 'bg-green-600' : 'bg-red-600';
  };

  const totalTrades = alphas.reduce((sum, alpha) => sum + alpha.trades, 0);
  const avgSharpe = alphas.length > 0 
    ? alphas.reduce((sum, alpha) => sum + alpha.sharpe, 0) / alphas.length 
    : 0;
  const totalPnL = alphas.reduce((sum, alpha) => sum + alpha.pnl, 0);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-gray-200">Loading alpha performance...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2 flex items-center">
            <ChartBarIcon className="h-8 w-8 mr-3 text-blue-400" />
            Alpha Strategy Performance
          </h1>
          <p className="text-gray-400">
            Performance metrics for all 6 trading strategies • Last updated:{' '}
            {lastUpdate.toLocaleTimeString()}
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Total Trades</h3>
                <p className="text-2xl font-bold text-blue-400">{totalTrades}</p>
                <p className="text-xs text-gray-500 mt-1">Across all strategies</p>
              </div>
              <TrophyIcon className="h-10 w-10 text-blue-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Average Sharpe</h3>
                <p className={`text-2xl font-bold ${getPerformanceColor(avgSharpe, 'sharpe')}`}>
                  {avgSharpe.toFixed(2)}
                </p>
                <p className="text-xs text-gray-500 mt-1">Target: ≥4.0</p>
              </div>
              <ChartBarIcon className="h-10 w-10 text-yellow-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Total PnL</h3>
                <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)}
                </p>
                <p className="text-xs text-gray-500 mt-1">Combined performance</p>
              </div>
              <div className={`text-3xl ${totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {totalPnL >= 0 ? '↑' : '↓'}
              </div>
            </div>
          </div>
        </div>

        {/* Alpha Performance Table */}
        <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden mb-8">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Rank
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('alpha_id')}
                  >
                    <div className="flex items-center">
                      Strategy
                      {sortBy === 'alpha_id' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('trades')}
                  >
                    <div className="flex items-center">
                      Trades
                      {sortBy === 'trades' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('hit_rate')}
                  >
                    <div className="flex items-center">
                      Win Rate
                      {sortBy === 'hit_rate' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('sharpe')}
                  >
                    <div className="flex items-center">
                      Sharpe
                      {sortBy === 'sharpe' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('pnl')}
                  >
                    <div className="flex items-center">
                      PnL
                      {sortBy === 'pnl' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('contribution_pct')}
                  >
                    <div className="flex items-center">
                      Contribution
                      {sortBy === 'contribution_pct' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('weight')}
                  >
                    <div className="flex items-center">
                      Weight
                      {sortBy === 'weight' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('avg_rr')}
                  >
                    <div className="flex items-center">
                      Avg RR
                      {sortBy === 'avg_rr' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {sortedAlphas.map((alpha, index) => (
                  <tr key={alpha.alpha_id} className="hover:bg-gray-700/50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-2xl font-bold text-gray-500">#{index + 1}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-200">{alpha.alpha_id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-300">{alpha.trades}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-semibold ${getPerformanceColor(alpha.hit_rate, 'hit_rate')}`}>
                        {(alpha.hit_rate * 100).toFixed(1)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-semibold ${getPerformanceColor(alpha.sharpe, 'sharpe')}`}>
                        {alpha.sharpe.toFixed(2)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm font-semibold ${alpha.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${alpha.pnl >= 0 ? '+' : ''}{alpha.pnl.toFixed(2)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-semibold text-blue-400 mr-2">
                          {alpha.contribution_pct.toFixed(1)}%
                        </div>
                        <div className="w-16 bg-gray-700 rounded-full h-2">
                          <div
                            className="h-2 rounded-full bg-blue-500"
                            style={{ width: `${Math.min(alpha.contribution_pct, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-300">{alpha.weight.toFixed(3)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-300">{alpha.avg_rr.toFixed(2)}</div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Performance Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedAlphas.map((alpha, index) => (
            <div key={alpha.alpha_id} className="bg-gray-800 rounded-lg p-6 shadow-lg border-2 border-gray-700 hover:border-blue-500 transition-colors">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-200">{alpha.alpha_id}</h3>
                <div className="flex items-center space-x-2">
                  <span className="text-2xl font-bold text-blue-400">#{index + 1}</span>
                  {index === 0 && <TrophyIcon className="h-6 w-6 text-yellow-500" />}
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                {/* Contribution */}
                <div className="bg-blue-900/30 rounded p-3 border border-blue-700">
                  <div className="text-xs text-gray-400 mb-1">Contribution</div>
                  <div className="text-xl font-bold text-blue-400">
                    {alpha.contribution_pct.toFixed(1)}%
                  </div>
                </div>

                {/* Sharpe */}
                <div className={`rounded p-3 ${getPerformanceBgColor(alpha.sharpe, 'sharpe')}`}>
                  <div className="text-xs text-white mb-1">Sharpe Ratio</div>
                  <div className="text-xl font-bold text-white">
                    {alpha.sharpe.toFixed(2)}
                  </div>
                </div>

                {/* Hit Rate */}
                <div className={`rounded p-3 ${getPerformanceBgColor(alpha.hit_rate, 'hit_rate')}`}>
                  <div className="text-xs text-white mb-1">Win Rate</div>
                  <div className="text-xl font-bold text-white">
                    {(alpha.hit_rate * 100).toFixed(1)}%
                  </div>
                </div>

                {/* Avg RR */}
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-xs text-gray-400 mb-1">Avg R:R</div>
                  <div className="text-xl font-bold text-gray-200">
                    {alpha.avg_rr.toFixed(2)}
                  </div>
                </div>
              </div>

              {/* Additional Info */}
              <div className="space-y-2 text-sm border-t border-gray-700 pt-4">
                <div className="flex justify-between">
                  <span className="text-gray-400">PnL:</span>
                  <span className={`font-semibold ${alpha.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    ${alpha.pnl >= 0 ? '+' : ''}{alpha.pnl.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Trades:</span>
                  <span className="font-semibold text-gray-200">{alpha.trades}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Current Weight:</span>
                  <span className="font-semibold text-gray-200">{alpha.weight.toFixed(3)}</span>
                </div>
              </div>

              {/* Weight Progress Bar */}
              <div className="mt-4">
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Adaptive Weight</span>
                  <span>{(alpha.weight * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                    style={{ width: `${Math.min(alpha.weight * 100, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {alphas.length === 0 && (
          <div className="text-center text-gray-400 mt-12 bg-gray-800 rounded-lg p-12">
            <ChartBarIcon className="h-16 w-16 mx-auto mb-4 text-gray-600" />
            <p className="text-lg">No alpha performance data available yet</p>
            <p className="text-sm mt-2">Data will appear once trading begins</p>
          </div>
        )}

        {/* Legend */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Performance Indicators</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">Sharpe Ratio:</h4>
              <ul className="space-y-1 text-gray-400">
                <li className="flex items-center">
                  <span className="w-3 h-3 bg-green-600 rounded mr-2"></span>
                  ≥4.0 - Excellent (Target)
                </li>
                <li className="flex items-center">
                  <span className="w-3 h-3 bg-yellow-600 rounded mr-2"></span>
                  2.0-4.0 - Good
                </li>
                <li className="flex items-center">
                  <span className="w-3 h-3 bg-red-600 rounded mr-2"></span>
                  &lt;2.0 - Needs Improvement
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">Win Rate:</h4>
              <ul className="space-y-1 text-gray-400">
                <li className="flex items-center">
                  <span className="w-3 h-3 bg-green-600 rounded mr-2"></span>
                  ≥65% - Excellent (Target)
                </li>
                <li className="flex items-center">
                  <span className="w-3 h-3 bg-yellow-600 rounded mr-2"></span>
                  50-65% - Acceptable
                </li>
                <li className="flex items-center">
                  <span className="w-3 h-3 bg-red-600 rounded mr-2"></span>
                  &lt;50% - Underperforming
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
