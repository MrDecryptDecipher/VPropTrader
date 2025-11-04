'use client';

import React from 'react';

interface DrawdownMeterProps {
  currentDrawdown: number;
  maxDrawdown: number;
}

export default function DrawdownMeter({ currentDrawdown, maxDrawdown }: DrawdownMeterProps) {
  const currentPercent = currentDrawdown * 100;
  const maxPercent = maxDrawdown * 100;

  const getColor = (dd: number) => {
    if (dd < 0.3) return 'bg-green-500';
    if (dd < 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const currentColor = getColor(currentDrawdown);
  const maxColor = getColor(maxDrawdown);

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
      <h3 className="text-lg font-semibold text-gray-200 mb-4">Drawdown</h3>
      
      <div className="space-y-4">
        {/* Current Drawdown */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-400">Current</span>
            <span className="text-xl font-bold text-gray-200">
              {currentPercent.toFixed(2)}%
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3">
            <div
              className={`h-3 rounded-full ${currentColor}`}
              style={{ width: `${Math.min(currentPercent / 1.5 * 100, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0%</span>
            <span>Target: &lt;0.6%</span>
            <span>Max: 1.5%</span>
          </div>
        </div>

        {/* Max Drawdown */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-400">Peak Drawdown</span>
            <span className="text-xl font-bold text-gray-200">
              {maxPercent.toFixed(2)}%
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3">
            <div
              className={`h-3 rounded-full ${maxColor}`}
              style={{ width: `${Math.min(maxPercent / 1.5 * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Status Indicator */}
        <div className="pt-2 border-t border-gray-700">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Status</span>
            <div className="flex items-center">
              <div className={`w-3 h-3 rounded-full ${currentColor} mr-2`} />
              <span className="text-sm font-medium text-gray-200">
                {currentPercent < 0.6 ? 'Healthy' : currentPercent < 1.0 ? 'Warning' : 'Critical'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
