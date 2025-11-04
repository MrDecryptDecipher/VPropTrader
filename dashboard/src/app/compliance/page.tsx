'use client';

import React, { useEffect, useState } from 'react';
import { apiClient, ComplianceRule } from '@/lib/api-client';
import { wsClient } from '@/lib/websocket-client';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

export default function CompliancePage() {
  const [rules, setRules] = useState<ComplianceRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [violationsCount, setViolationsCount] = useState(0);
  const [warningsCount, setWarningsCount] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    loadCompliance();

    // Subscribe to WebSocket updates
    const unsubscribe = wsClient.on('compliance', (data) => {
      if (data.rules) {
        setRules(data.rules);
        updateCounts(data.rules);
        setLastUpdate(new Date());
      }
    });

    // Fallback polling every 10 seconds
    const interval = setInterval(loadCompliance, 10000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  const loadCompliance = async () => {
    try {
      const data = await apiClient.getCompliance();
      setRules(data);
      updateCounts(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading compliance:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateCounts = (rulesData: ComplianceRule[]) => {
    setViolationsCount(rulesData.filter((r) => r.status === 'red').length);
    setWarningsCount(rulesData.filter((r) => r.status === 'yellow').length);
  };

  // Request browser notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Send browser notifications for warnings/violations
  useEffect(() => {
    if (violationsCount > 0 && 'Notification' in window && Notification.permission === 'granted') {
      new Notification('⚠️ VProp Rule Violation', {
        body: `${violationsCount} rule(s) violated! Check compliance dashboard.`,
        icon: '/icon.png',
      });
    } else if (warningsCount > 0 && 'Notification' in window && Notification.permission === 'granted') {
      new Notification('⚠️ VProp Rule Warning', {
        body: `${warningsCount} rule(s) approaching limit. Monitor closely.`,
        icon: '/icon.png',
      });
    }
  }, [violationsCount, warningsCount]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'green':
        return 'bg-green-500';
      case 'yellow':
        return 'bg-yellow-500';
      case 'red':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'green':
        return <CheckCircleIcon className="h-8 w-8 text-green-500" />;
      case 'yellow':
        return <ExclamationTriangleIcon className="h-8 w-8 text-yellow-500" />;
      case 'red':
        return <XCircleIcon className="h-8 w-8 text-red-500" />;
      default:
        return <ShieldCheckIcon className="h-8 w-8 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'green':
        return 'Safe';
      case 'yellow':
        return 'Warning';
      case 'red':
        return 'Violated';
      default:
        return 'Unknown';
    }
  };

  const calculatePercentage = (value: number, limit: number): number => {
    if (limit === 0) return 0;
    return Math.min(Math.abs((value / limit) * 100), 100);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-gray-200">Loading compliance data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2 flex items-center">
            <ShieldCheckIcon className="h-8 w-8 mr-3 text-blue-400" />
            VProp Rule Compliance
          </h1>
          <p className="text-gray-400">
            Real-time monitoring of all 7 VPropTrader rules • Last updated:{' '}
            {lastUpdate.toLocaleTimeString()}
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Overall Status */}
          <div
            className={`rounded-lg p-6 shadow-lg ${
              violationsCount > 0
                ? 'bg-red-900/30 border-2 border-red-500'
                : warningsCount > 0
                ? 'bg-yellow-900/30 border-2 border-yellow-500'
                : 'bg-green-900/30 border-2 border-green-500'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Overall Status</h3>
                <p
                  className={`text-2xl font-bold ${
                    violationsCount > 0
                      ? 'text-red-400'
                      : warningsCount > 0
                      ? 'text-yellow-400'
                      : 'text-green-400'
                  }`}
                >
                  {violationsCount > 0
                    ? 'VIOLATED'
                    : warningsCount > 0
                    ? 'AT RISK'
                    : 'COMPLIANT'}
                </p>
              </div>
              <div>
                {violationsCount > 0 ? (
                  <XCircleIcon className="h-12 w-12 text-red-500" />
                ) : warningsCount > 0 ? (
                  <ExclamationTriangleIcon className="h-12 w-12 text-yellow-500" />
                ) : (
                  <CheckCircleIcon className="h-12 w-12 text-green-500" />
                )}
              </div>
            </div>
          </div>

          {/* Violations */}
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Violations</h3>
                <p className="text-2xl font-bold text-red-400">{violationsCount}</p>
                <p className="text-xs text-gray-500 mt-1">Critical issues</p>
              </div>
              <XCircleIcon className="h-10 w-10 text-red-500" />
            </div>
          </div>

          {/* Warnings */}
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-400 mb-1">Warnings</h3>
                <p className="text-2xl font-bold text-yellow-400">{warningsCount}</p>
                <p className="text-xs text-gray-500 mt-1">Approaching limits</p>
              </div>
              <ExclamationTriangleIcon className="h-10 w-10 text-yellow-500" />
            </div>
          </div>
        </div>

        {/* Rules Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {rules.map((rule, index) => {
            const percentage =
              typeof rule.value === 'number' && typeof rule.limit === 'number'
                ? calculatePercentage(rule.value, rule.limit)
                : 0;

            return (
              <div
                key={index}
                className={`bg-gray-800 rounded-lg p-6 shadow-lg border-2 ${
                  rule.status === 'red'
                    ? 'border-red-500'
                    : rule.status === 'yellow'
                    ? 'border-yellow-500'
                    : 'border-green-500'
                }`}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-200 mb-1">{rule.name}</h3>
                    {rule.description && (
                      <p className="text-sm text-gray-400">{rule.description}</p>
                    )}
                  </div>
                  <div className="ml-4">{getStatusIcon(rule.status)}</div>
                </div>

                {/* Status Badge */}
                <div className="mb-4">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                      rule.status === 'green'
                        ? 'bg-green-900/50 text-green-400'
                        : rule.status === 'yellow'
                        ? 'bg-yellow-900/50 text-yellow-400'
                        : 'bg-red-900/50 text-red-400'
                    }`}
                  >
                    {getStatusText(rule.status)}
                  </span>
                </div>

                {/* Values */}
                <div className="space-y-3 mb-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Current Value:</span>
                    <span className="text-lg font-bold text-gray-200">
                      {typeof rule.value === 'number'
                        ? `${rule.value >= 0 ? '+' : ''}${rule.value.toFixed(2)}`
                        : rule.value}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Limit:</span>
                    <span className="text-lg font-semibold text-gray-300">
                      {typeof rule.limit === 'number' ? rule.limit.toFixed(2) : rule.limit}
                    </span>
                  </div>
                  {typeof rule.value === 'number' && typeof rule.limit === 'number' && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400">Usage:</span>
                      <span
                        className={`text-lg font-bold ${
                          percentage >= 100
                            ? 'text-red-400'
                            : percentage >= 80
                            ? 'text-yellow-400'
                            : 'text-green-400'
                        }`}
                      >
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>

                {/* Progress Bar */}
                {typeof rule.value === 'number' && typeof rule.limit === 'number' && (
                  <div className="mt-4">
                    <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                      <div
                        className={`h-3 rounded-full transition-all duration-300 ${
                          rule.status === 'green'
                            ? 'bg-green-500'
                            : rule.status === 'yellow'
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <div className="flex justify-between mt-1 text-xs text-gray-500">
                      <span>0%</span>
                      <span>80% (Warning)</span>
                      <span>100% (Limit)</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer Info */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">Compliance Notes</h3>
          <ul className="space-y-2 text-sm text-gray-400">
            <li className="flex items-start">
              <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
              <span>
                <strong className="text-green-400">Safe (Green):</strong> Rule is within safe limits
              </span>
            </li>
            <li className="flex items-start">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mr-2 flex-shrink-0 mt-0.5" />
              <span>
                <strong className="text-yellow-400">Warning (Yellow):</strong> Rule is at 80%+ of limit
                - monitor closely
              </span>
            </li>
            <li className="flex items-start">
              <XCircleIcon className="h-5 w-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
              <span>
                <strong className="text-red-400">Violated (Red):</strong> Rule limit exceeded - trading
                may be halted
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
