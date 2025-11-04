'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { apiClient } from '@/lib/api-client';
import { wsClient } from '@/lib/websocket-client';

// Dynamic import to avoid SSR issues with Plotly
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface EquityPoint {
  timestamp: string;
  equity: number;
  pnl: number;
}

export default function EquityChart() {
  const [equityData, setEquityData] = useState<EquityPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initial load
    loadEquityHistory();

    // Subscribe to real-time updates
    const unsubscribe = wsClient.on('equity', (data) => {
      setEquityData((prev) => {
        const newData = [...prev, {
          timestamp: data.timestamp,
          equity: data.equity,
          pnl: data.pnl,
        }];
        // Keep last 1000 points
        return newData.slice(-1000);
      });
    });

    // Refresh every 30 seconds as fallback
    const interval = setInterval(loadEquityHistory, 30000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  const loadEquityHistory = async () => {
    try {
      const history = await apiClient.getEquityHistory(1000);
      if (history.length > 0) {
        setEquityData(history);
      }
    } catch (error) {
      console.error('Error loading equity history:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading equity chart...</div>
      </div>
    );
  }

  if (equityData.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">No equity data available</div>
      </div>
    );
  }

  const timestamps = equityData.map((d) => new Date(d.timestamp));
  const equity = equityData.map((d) => d.equity);
  const pnl = equityData.map((d) => d.pnl);

  return (
    <div className="w-full">
      <Plot
        data={[
          {
            x: timestamps,
            y: equity,
            type: 'scatter',
            mode: 'lines',
            name: 'Equity',
            line: { color: '#3b82f6', width: 2 },
            fill: 'tozeroy',
            fillcolor: 'rgba(59, 130, 246, 0.1)',
          },
        ]}
        layout={{
          title: 'Account Equity',
          xaxis: {
            title: 'Time',
            type: 'date',
            gridcolor: '#374151',
          },
          yaxis: {
            title: 'Equity ($)',
            gridcolor: '#374151',
          },
          paper_bgcolor: '#1f2937',
          plot_bgcolor: '#111827',
          font: { color: '#e5e7eb' },
          margin: { t: 50, r: 30, b: 50, l: 60 },
          hovermode: 'x unified',
        }}
        config={{
          responsive: true,
          displayModeBar: false,
        }}
        style={{ width: '100%', height: '400px' }}
      />
    </div>
  );
}
