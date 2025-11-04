'use client';

import React from 'react';

interface TradeStatsProps {
  tradesToday: number;
  winRate: number;
  sharpe: number;
  sortino: number;
  calmar: number;
}

export default function TradeStats({ tradesToday, winRate, sharpe, sortino, calmar }: TradeStatsProps) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
      <h3 className="text-lg font-semibold text-gray-200 mb-4">Performance Metrics</h3>
      
      <div className="grid grid-cols-2 gap-4">
        {/* Trades Today */}
        <div className="bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-400 mb-1">Trades Today</div>
          <div className="text-3xl font-bold text-blue-400">{tradesToday}</div>
        </div>

        {/* Win Rate */}
        <div className="bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-400 mb-1">Win Rate</div>
          <div className="text-3xl font-bold text-green-400">
            {(winRate * 100).toFixed(1)}%
          </div>
        </div>

        {/* Sharpe Ratio */}
        <div className="bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-400 mb-1">Sharpe Ratio</div>
          <div className={`text-2xl font-bold ${sharpe >= 4.0 ? 'text-green-400' : sharpe >= 2.0 ? 'text-yellow-400' : 'text-red-400'}`}>
            {sharpe.toFixed(2)}
          </div>
          <div className="text-xs text-gray-500 mt-1">Target: ≥4.0</div>
        </div>

        {/* Sortino Ratio */}
        <div className="bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-400 mb-1">Sortino Ratio</div>
          <div className="text-2xl font-bold text-purple-400">
            {sortino.toFixed(2)}
          </div>
        </div>

        {/* Calmar Ratio */}
        <div className="bg-gray-700 rounded-lg p-4 col-span-2">
          <div className="text-sm text-gray-400 mb-1">Calmar Ratio</div>
          <div className="text-2xl font-bold text-indigo-400">
            {calmar.toFixed(2)}
          </div>
          <div className="text-xs text-gray-500 mt-1">Return / Max Drawdown</div>
        </div>
      </div>
    </div>
  );
}
