'use client';

import React from 'react';

interface PnLGaugeProps {
  pnlToday: number;
  pnlTotal: number;
  targetProgress: number;
}

export default function PnLGauge({ pnlToday, pnlTotal, targetProgress }: PnLGaugeProps) {
  const todayColor = pnlToday >= 0 ? 'text-green-500' : 'text-red-500';
  const totalColor = pnlTotal >= 0 ? 'text-green-500' : 'text-red-500';

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
      <h3 className="text-lg font-semibold text-gray-200 mb-4">Profit & Loss</h3>
      
      <div className="space-y-4">
        {/* Today's PnL */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-gray-400">Today</span>
            <span className={`text-2xl font-bold ${todayColor}`}>
              ${pnlToday >= 0 ? '+' : ''}{pnlToday.toFixed(2)}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${pnlToday >= 0 ? 'bg-green-500' : 'bg-red-500'}`}
              style={{ width: `${Math.min(Math.abs(pnlToday) / 100 * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Total PnL */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-gray-400">Total</span>
            <span className={`text-2xl font-bold ${totalColor}`}>
              ${pnlTotal >= 0 ? '+' : ''}{pnlTotal.toFixed(2)}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${pnlTotal >= 0 ? 'bg-green-500' : 'bg-red-500'}`}
              style={{ width: `${Math.min(Math.abs(pnlTotal) / 100 * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Target Progress */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-gray-400">Target Progress</span>
            <span className="text-lg font-semibold text-blue-400">
              {targetProgress.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="h-2 rounded-full bg-blue-500"
              style={{ width: `${Math.min(targetProgress, 100)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
