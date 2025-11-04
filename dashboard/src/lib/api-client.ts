/**
 * API Client for Sidecar Service
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Signal {
  symbol: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  q_star: number;
  es95: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  lots: number;
  alpha_id: string;
  regime: string;
  features?: Record<string, number>;
}

export interface OverviewData {
  equity: number;
  pnl_today: number;
  pnl_total: number;
  drawdown_current: number;
  drawdown_max: number;
  target_progress: number;
  trades_today: number;
  win_rate: number;
  sharpe: number;
  sortino: number;
  calmar: number;
}

export interface ComplianceRule {
  name: string;
  status: 'green' | 'yellow' | 'red';
  value: number | string;
  limit: number | string;
  description?: string;
}

export interface AlphaPerformance {
  alpha_id: string;
  contribution_pct: number;
  sharpe: number;
  hit_rate: number;
  avg_rr: number;
  trades: number;
  weight: number;
  pnl: number;
}

export interface RiskMetrics {
  var_95: number;
  es_95: number;
  vol_forecast: number;
  exposure_by_symbol: Record<string, number>;
  correlation_matrix: number[][];
}

class APIClient {
  private client: AxiosInstance;
  private retryCount: number = 3;
  private retryDelay: number = 1000;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.message);
        return Promise.reject(error);
      }
    );
  }

  private async retryRequest<T>(
    requestFn: () => Promise<T>,
    retries: number = this.retryCount
  ): Promise<T> {
    try {
      return await requestFn();
    } catch (error) {
      if (retries > 0) {
        await new Promise((resolve) => setTimeout(resolve, this.retryDelay));
        return this.retryRequest(requestFn, retries - 1);
      }
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  // Signals
  async getSignals(equity?: number): Promise<Signal[]> {
    const response = await this.retryRequest(() =>
      this.client.get('/api/signals', {
        params: equity ? { equity } : {},
      })
    );
    return response.data.signals || [];
  }

  // Analytics - Overview
  async getOverview(): Promise<OverviewData> {
    const response = await this.retryRequest(() =>
      this.client.get('/api/analytics/overview')
    );
    return response.data;
  }

  // Analytics - Compliance
  async getCompliance(): Promise<ComplianceRule[]> {
    const response = await this.retryRequest(() =>
      this.client.get('/api/analytics/compliance')
    );
    return response.data.rules || [];
  }

  // Analytics - Alphas
  async getAlphas(): Promise<AlphaPerformance[]> {
    const response = await this.retryRequest(() =>
      this.client.get('/api/analytics/alphas')
    );
    return response.data.alphas || [];
  }

  // Analytics - Risk
  async getRisk(): Promise<RiskMetrics> {
    const response = await this.retryRequest(() =>
      this.client.get('/api/analytics/risk')
    );
    return response.data;
  }

  // Scanner stats
  async getScannerStats(): Promise<any> {
    const response = await this.retryRequest(() =>
      this.client.get('/api/signals/scanner/stats')
    );
    return response.data.stats;
  }

  // Equity history (for chart)
  async getEquityHistory(limit: number = 1000): Promise<Array<{ timestamp: string; equity: number; pnl: number }>> {
    try {
      const response = await this.retryRequest(() =>
        this.client.get('/api/analytics/equity-history', {
          params: { limit },
        })
      );
      return response.data.history || [];
    } catch (error) {
      console.error('Error fetching equity history:', error);
      return [];
    }
  }

  // Active positions
  async getActivePositions(): Promise<any[]> {
    try {
      const response = await this.retryRequest(() =>
        this.client.get('/api/analytics/positions')
      );
      return response.data.positions || [];
    } catch (error) {
      console.error('Error fetching active positions:', error);
      return [];
    }
  }

  // Close all positions (emergency)
  async closeAllPositions(): Promise<void> {
    await this.retryRequest(() =>
      this.client.post('/api/executions/close-all')
    );
  }

  // Trades history
  async getTrades(params?: any): Promise<{ trades: any[]; total: number }> {
    try {
      const response = await this.retryRequest(() =>
        this.client.get('/api/analytics/trades', { params })
      );
      return {
        trades: response.data.trades || [],
        total: response.data.total || 0,
      };
    } catch (error) {
      console.error('Error fetching trades:', error);
      return { trades: [], total: 0 };
    }
  }
}

export const apiClient = new APIClient();
