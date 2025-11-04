'use client';

import React, { useEffect, useState } from 'react';
import { wsClient } from '@/lib/websocket-client';
import { apiClient } from '@/lib/api-client';

export default function ConnectionStatus() {
  const [wsStatus, setWsStatus] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');
  const [apiHealthy, setApiHealthy] = useState(false);

  useEffect(() => {
    // Check API health
    const checkHealth = async () => {
      const healthy = await apiClient.healthCheck();
      setApiHealthy(healthy);
    };

    checkHealth();
    const healthInterval = setInterval(checkHealth, 10000);

    // Monitor WebSocket connection
    const updateWsStatus = () => {
      setWsStatus(wsClient.getConnectionStatus());
    };

    const unsubscribe = wsClient.on('connection', updateWsStatus);
    updateWsStatus();

    // Connect WebSocket
    wsClient.connect();

    return () => {
      unsubscribe();
      clearInterval(healthInterval);
    };
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500 animate-pulse';
      case 'disconnected':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="flex items-center space-x-4 text-sm">
      {/* API Status */}
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${apiHealthy ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-gray-400">API</span>
      </div>

      {/* WebSocket Status */}
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${getStatusColor(wsStatus)}`} />
        <span className="text-gray-400">Live</span>
      </div>
    </div>
  );
}
