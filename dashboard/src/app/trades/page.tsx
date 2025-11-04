'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { wsClient } from '@/lib/websocket-client';
import {
  ClockIcon,
  CurrencyDollarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  FunnelIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

interface TradeRecord {
  trade_id: string;
  timestamp: string;
  symbol: string;
  action: 'BUY' | 'SELL';
  alpha_id: string;
  regime: string;
  entry_price: number;
  exit_price: number;
  lots: number;
  pnl: number;
  pnl_percent: number;
  duration_minutes: number;
  exit_reason: string;
  q_star: number;
  rf_pwin: number;
  stop_loss: number;
  take_profit: number;
  spread_z: number;
  slippage: number;
  latency_ms: number;
  risk_dollars: number;
}

export default function TradesPage() {
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<keyof TradeRecord>('timestamp');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [filterSymbol, setFilterSymbol] = useState<string>('');
  const [filterAlpha, setFilterAlpha] = useState<string>('');
  const [filterDateFrom, setFilterDateFrom] = useState<string>('');
  const [filterDateTo, setFilterDateTo] = useState<string>('');
  const [selectedTrade, setSelectedTrade] = useState<TradeRecord | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [page, setPage] = useState(1);
  const [totalTrades, setTotalTrades] = useState(0);
  const perPage = 50;

  useEffect(() => {
    loadTrades();

    // Subscribe to WebSocket updates for new trades
    const unsubscribe = wsClient.on('trade', (data) => {
      if (data) {
        // Add new trade to the beginning of the list
        setTrades(prev => [data, ...prev.slice(0, perPage - 1)]);
        setTotalTrades(prev => prev + 1);
        setLastUpdate(new Date());
      }
    });

    return () => {
      unsubscribe();
    };
  }, [page, filterSymbol, filterAlpha, filterDateFrom, filterDateTo]);

  const loadTrades = async () => {
    try {
      const params: any = {
        page,
        per_page: perPage,
      };
      
      if (filterSymbol) params.symbol = filterSymbol;
      if (filterAlpha) params.alpha_id = filterAlpha;
      if (filterDateFrom) params.date_from = filterDateFrom;
      if (filterDateTo) params.date_to = filterDateTo;
      
      const data = await apiClient.getTrades(params);
      setTrades(data.trades || []);
      setTotalTrades(data.total || 0);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading trades:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (column: keyof TradeRecord) => {
    if (sortBy === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDirection('desc');
    }
  };

  const sortedTrades = [...trades].sort((a, b) => {
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

  const formatCurrency = (value: number) => {
    return `$${value >= 0 ? '+' : ''}${value.toFixed(2)}`;
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const getExitReasonColor = (reason: string) => {
    switch (reason.toLowerCase()) {
      case 'tp1':
      case 'tp2':
        return 'text-green-400 bg-green-900/30';
      case 'sl':
        return 'text-red-400 bg-red-900/30';
      case 'time_stop':
        return 'text-yellow-400 bg-yellow-900/30';
      case 'adverse_bars':
        return 'text-orange-400 bg-orange-900/30';
      default:
        return 'text-gray-400 bg-gray-900/30';
    }
  };

  const uniqueSymbols = [...new Set(trades.map(t => t.symbol))];
  const uniqueAlphas = [...new Set(trades.map(t => t.alpha_id))];

  const totalPages = Math.ceil(totalTrades / perPage);
  const profitableTrades = trades.filter(t => t.pnl > 0).length;
  const totalPnL = trades.reduce((sum, t) => sum + t.pnl, 0);
  const avgPnL = trades.length > 0 ? totalPnL / trades.length : 0;
  const winRate = trades.length > 0 ? (profitableTrades / trades.length) * 100 : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-gray-200">Loading trades...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2 flex items-center">
            <DocumentTextIcon className="h-8 w-8 mr-3 text-blue-400" />
            Trade History
          </h1>
          <p className="text-gray-400">
            Complete trade history with filtering and analysis • Last updated:{' '}
            {lastUpdate.toLocaleTimeString()}
          </p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Total Trades</h3>
                <p className="text-2xl font-bold text-blue-400">{totalTrades}</p>
              </div>
              <DocumentTextIcon className="h-10 w-10 text-blue-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Win Rate</h3>
                <p className={`text-2xl font-bold ${
                  winRate >= 65 ? 'text-green-400' : winRate >= 50 ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {winRate.toFixed(1)}%
                </p>
              </div>
              <div className={`text-3xl ${
                winRate >= 65 ? 'text-green-500' : winRate >= 50 ? 'text-yellow-500' : 'text-red-500'
              }`}>
                {winRate >= 50 ? '↑' : '↓'}
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Total PnL</h3>
                <p className={`text-2xl font-bold ${
                  totalPnL >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {formatCurrency(totalPnL)}
                </p>
              </div>
              <CurrencyDollarIcon className={`h-10 w-10 ${
                totalPnL >= 0 ? 'text-green-500' : 'text-red-500'
              }`} />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Avg PnL</h3>
                <p className={`text-2xl font-bold ${
                  avgPnL >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {formatCurrency(avgPnL)}
                </p>
              </div>
              <div className={`text-3xl ${
                avgPnL >= 0 ? 'text-green-500' : 'text-red-500'
              }`}>
                {avgPnL >= 0 ? '↑' : '↓'}
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <div className="flex items-center mb-4">
            <FunnelIcon className="h-5 w-5 mr-2 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-200">Filters</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Symbol</label>
              <select
                value={filterSymbol}
                onChange={(e) => setFilterSymbol(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Symbols</option>
                {uniqueSymbols.map(symbol => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Alpha Strategy</label>
              <select
                value={filterAlpha}
                onChange={(e) => setFilterAlpha(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Strategies</option>
                {uniqueAlphas.map(alpha => (
                  <option key={alpha} value={alpha}>{alpha}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">From Date</label>
              <input
                type="date"
                value={filterDateFrom}
                onChange={(e) => setFilterDateFrom(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">To Date</label>
              <input
                type="date"
                value={filterDateTo}
                onChange={(e) => setFilterDateTo(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="mt-4 flex space-x-4">
            <button
              onClick={loadTrades}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Apply Filters
            </button>
            <button
              onClick={() => {
                setFilterSymbol('');
                setFilterAlpha('');
                setFilterDateFrom('');
                setFilterDateTo('');
                setPage(1);
              }}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Trades Table */}
        <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden mb-8">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('timestamp')}
                  >
                    <div className="flex items-center">
                      Time
                      {sortBy === 'timestamp' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('symbol')}
                  >
                    <div className="flex items-center">
                      Symbol
                      {sortBy === 'symbol' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Action
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600"
                    onClick={() => handleSort('alpha_id')}
                  >
                    <div className="flex items-center">
                      Alpha
                      {sortBy === 'alpha_id' && (
                        sortDirection === 'asc' ? <ArrowUpIcon className="h-4 w-4 ml-1" /> : <ArrowDownIcon className="h-4 w-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Entry/Exit
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Exit Reason
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Q* Score
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {sortedTrades.map((trade) => (
                  <tr 
                    key={trade.trade_id} 
                    className="hover:bg-gray-700/50 cursor-pointer"
                    onClick={() => setSelectedTrade(trade)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {formatTime(trade.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-200">
                      {trade.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${
                        trade.action === 'BUY' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'
                      }`}>
                        {trade.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {trade.alpha_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      <div>{trade.entry_price.toFixed(5)}</div>
                      <div className="text-xs text-gray-500">{trade.exit_price.toFixed(5)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-semibold ${
                        trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {formatCurrency(trade.pnl)}
                      </span>
                      <div className="text-xs text-gray-500">
                        {(trade.pnl_percent * 100).toFixed(2)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {formatDuration(trade.duration_minutes)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${getExitReasonColor(trade.exit_reason)}`}>
                        {trade.exit_reason}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-semibold ${
                        trade.q_star >= 8.5 ? 'text-green-400' : trade.q_star >= 7.0 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {trade.q_star.toFixed(1)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between bg-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400">
              Showing {((page - 1) * perPage) + 1} to {Math.min(page * perPage, totalTrades)} of {totalTrades} trades
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-3 py-1 bg-gray-700 text-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
              >
                Previous
              </button>
              <span className="px-3 py-1 bg-blue-600 text-white rounded">
                {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 bg-gray-700 text-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {trades.length === 0 && (
          <div className="text-center text-gray-400 mt-12 bg-gray-800 rounded-lg p-12">
            <DocumentTextIcon className="h-16 w-16 mx-auto mb-4 text-gray-600" />
            <p className="text-lg">No trades found</p>
            <p className="text-sm mt-2">Trades will appear here once the system starts trading</p>
          </div>
        )}

        {/* Trade Detail Modal */}
        {selectedTrade && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-200">Trade Details</h3>
                <button
                  onClick={() => setSelectedTrade(null)}
                  className="text-gray-400 hover:text-gray-200"
                >
                  ✕
                </button>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Trade ID:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.trade_id}</span>
                </div>
                <div>
                  <span className="text-gray-400">Timestamp:</span>
                  <span className="ml-2 text-gray-200">{formatTime(selectedTrade.timestamp)}</span>
                </div>
                <div>
                  <span className="text-gray-400">Symbol:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.symbol}</span>
                </div>
                <div>
                  <span className="text-gray-400">Action:</span>
                  <span className={`ml-2 font-semibold ${
                    selectedTrade.action === 'BUY' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {selectedTrade.action}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Alpha Strategy:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.alpha_id}</span>
                </div>
                <div>
                  <span className="text-gray-400">Regime:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.regime}</span>
                </div>
                <div>
                  <span className="text-gray-400">Entry Price:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.entry_price.toFixed(5)}</span>
                </div>
                <div>
                  <span className="text-gray-400">Exit Price:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.exit_price.toFixed(5)}</span>
                </div>
                <div>
                  <span className="text-gray-400">Lot Size:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.lots}</span>
                </div>
                <div>
                  <span className="text-gray-400">Duration:</span>
                  <span className="ml-2 text-gray-200">{formatDuration(selectedTrade.duration_minutes)}</span>
                </div>
                <div>
                  <span className="text-gray-400">PnL:</span>
                  <span className={`ml-2 font-semibold ${
                    selectedTrade.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {formatCurrency(selectedTrade.pnl)} ({(selectedTrade.pnl_percent * 100).toFixed(2)}%)
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Exit Reason:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.exit_reason}</span>
                </div>
                <div>
                  <span className="text-gray-400">Q* Score:</span>
                  <span className={`ml-2 font-semibold ${
                    selectedTrade.q_star >= 8.5 ? 'text-green-400' : selectedTrade.q_star >= 7.0 ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {selectedTrade.q_star.toFixed(1)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">RF P(Win):</span>
                  <span className="ml-2 text-gray-200">{(selectedTrade.rf_pwin * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-gray-400">Stop Loss:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.stop_loss.toFixed(5)}</span>
                </div>
                <div>
                  <span className="text-gray-400">Take Profit:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.take_profit.toFixed(5)}</span>
                </div>
                <div>
                  <span className="text-gray-400">Spread Z-Score:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.spread_z.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-gray-400">Slippage:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.slippage.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-gray-400">Latency:</span>
                  <span className="ml-2 text-gray-200">{selectedTrade.latency_ms}ms</span>
                </div>
                <div>
                  <span className="text-gray-400">Risk:</span>
                  <span className="ml-2 text-gray-200">{formatCurrency(selectedTrade.risk_dollars)}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
