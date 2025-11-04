'use client';

import React, { useEffect, useState } from 'react';
import { apiClient, OverviewData } from '@/lib/api-client';
import { wsClient } from '@/lib/websocket-client';
import EquityChart from '@/components/EquityChart';
import PnLGauge from '@/components/PnLGauge';
import DrawdownMeter from '@/components/DrawdownMeter';
import TradeStats from '@/components/TradeStats';
import ConnectionStatus from '@/components/ConnectionStatus';
import MarketTimer from '@/components/MarketTimer';
import { 
  ArrowUpIcon, 
  ArrowDownIcon, 
  XMarkIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';

interface ActivePosition {
  symbol: string;
  action: 'BUY' | 'SELL';
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  lots: number;
  duration_minutes: number;
  alpha_id: string;
}

export default function Home() {
  const [overview, setOverview] = useState<OverviewData>({
    equity: 1000,
    pnl_today: 0,
    pnl_total: 0,
    drawdown_current: 0,
    drawdown_max: 0,
    target_progress: 0,
    trades_today: 0,
    win_rate: 0,
    sharpe: 0,
    sortino: 0,
    calmar: 0,
  });
  const [activePositions, setActivePositions] = useState<ActivePosition[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [closingAll, setClosingAll] = useState(false);

  useEffect(() => {
    // Initial load
    loadOverview();
    loadActivePositions();

    // Subscribe to real-time PnL updates
    const unsubscribePnL = wsClient.on('pnl', (data) => {
      setOverview((prev) => ({
        ...prev,
        pnl_today: data.pnl_today || prev.pnl_today,
        pnl_total: data.pnl_total || prev.pnl_total,
        equity: data.equity || prev.equity,
      }));
      setLastUpdate(new Date());
    });

    // Subscribe to trade updates
    const unsubscribeTrade = wsClient.on('trade', (data) => {
      // Reload overview when trade completes
      loadOverview();
      loadActivePositions();
    });

    // Subscribe to position updates
    const unsubscribePosition = wsClient.on('position', (data) => {
      if (data) {
        setActivePositions(data);
        setLastUpdate(new Date());
      }
    });

    // Refresh every 5 seconds as fallback
    const interval = setInterval(() => {
      loadOverview();
      loadActivePositions();
    }, 5000);

    return () => {
      unsubscribePnL();
      unsubscribeTrade();
      unsubscribePosition();
      clearInterval(interval);
    };
  }, []);

  const loadOverview = async () => {
    try {
      const data = await apiClient.getOverview();
      setOverview(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading overview:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadActivePositions = async () => {
    try {
      const data = await apiClient.getActivePositions();
      setActivePositions(data);
    } catch (error) {
      console.error('Error loading active positions:', error);
    }
  };

  const handleCloseAll = async () => {
    if (!confirm('Are you sure you want to close ALL open positions? This action cannot be undone.')) {
      return;
    }

    setClosingAll(true);
    try {
      await apiClient.closeAllPositions();
      setActivePositions([]);
      loadOverview();
    } catch (error) {
      console.error('Error closing all positions:', error);
      alert('Failed to close all positions. Please try again or close manually.');
    } finally {
      setClosingAll(false);
    }
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const formatCurrency = (value: number) => {
    return `$${value >= 0 ? '+' : ''}${value.toFixed(2)}`;
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-200 mb-2">Loading Dashboard...</div>
          <div className="text-gray-400">Connecting to Sidecar Service</div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">
              Quant Ω Supra AI Dashboard
            </h1>
            <p className="text-sm text-gray-400">
              Memory-Adaptive Prop Trading System
            </p>
          </div>
          <div className="flex items-center space-x-6">
            <div className="text-right">
              <div className="text-sm text-gray-400">Account Equity</div>
              <div className="text-2xl font-bold text-blue-400">
                ${overview.equity.toFixed(2)}
              </div>
            </div>
            <ConnectionStatus />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        {/* Market Timer */}
        <div className="mb-8">
          <MarketTimer />
        </div>

        {/* Active Positions */}
        {activePositions.length > 0 && (
          <div className="mb-8">
            <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-200 flex items-center">
                  <span className="inline-block w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                  Active Positions ({activePositions.length})
                </h3>
                <button
                  onClick={handleCloseAll}
                  disabled={closingAll}
                  className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
                  {closingAll ? 'Closing...' : 'Close All'}
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Symbol
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Action
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Alpha
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Entry
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Current
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        PnL
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Lots
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Duration
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {activePositions.map((position, index) => (
                      <tr key={index} className="hover:bg-gray-700/50">
                        <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-200">
                          {position.symbol}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <span className={`flex items-center px-2 py-1 text-xs font-semibold rounded ${
                            position.action === 'BUY' 
                              ? 'bg-green-900/50 text-green-400' 
                              : 'bg-red-900/50 text-red-400'
                          }`}>
                            {position.action === 'BUY' ? (
                              <ArrowUpIcon className="h-3 w-3 mr-1" />
                            ) : (
                              <ArrowDownIcon className="h-3 w-3 mr-1" />
                            )}
                            {position.action}
                          </span>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-300">
                          {position.alpha_id}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-300">
                          {position.entry_price.toFixed(5)}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-300">
                          {position.current_price.toFixed(5)}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className={`text-sm font-semibold ${
                            position.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {formatCurrency(position.pnl)}
                          </div>
                          <div className="text-xs text-gray-500">
                            {(position.pnl_percent * 100).toFixed(2)}%
                          </div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-300">
                          {position.lots}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-300">
                          {formatDuration(position.duration_minutes)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-600/30 rounded-md">
                <div className="flex items-start">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mr-2 mt-0.5" />
                  <div className="text-sm text-yellow-200">
                    <strong>Emergency Stop:</strong> Use "Close All" button to immediately close all positions in case of emergency. 
                    This will send market orders to close all open trades.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Equity Chart */}
        <div className="mb-8">
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <EquityChart />
          </div>
        </div>

        {/* Middle Row - PnL, Drawdown, Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <PnLGauge
            pnlToday={overview.pnl_today}
            pnlTotal={overview.pnl_total}
            targetProgress={overview.target_progress}
          />
          <DrawdownMeter
            currentDrawdown={overview.drawdown_current}
            maxDrawdown={overview.drawdown_max}
          />
          <TradeStats
            tradesToday={overview.trades_today}
            winRate={overview.win_rate}
            sharpe={overview.sharpe}
            sortino={overview.sortino}
            calmar={overview.calmar}
          />
        </div>

        {/* Bottom Row - Quick Info */}
        <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-200 mb-2">System Status</h3>
              <div className="flex items-center space-x-4 text-sm text-gray-400">
                <span>Last Update: {lastUpdate.toLocaleTimeString()}</span>
                <span>•</span>
                <span>Trades Today: {overview.trades_today}</span>
                <span>•</span>
                <span>Win Rate: {(overview.win_rate * 100).toFixed(1)}%</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-400 mb-1">Target Progress</div>
              <div className="text-3xl font-bold text-blue-400">
                {overview.target_progress.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
