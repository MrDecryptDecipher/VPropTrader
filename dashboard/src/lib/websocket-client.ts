/**
 * WebSocket Client for Real-time Updates
 */

type MessageHandler = (data: any) => void;

interface WebSocketMessage {
  type: 'tick' | 'trade' | 'pnl' | 'alert' | 'equity';
  data: any;
  timestamp: string;
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private reconnectDelay: number = 1000;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private isConnecting: boolean = false;
  private shouldReconnect: boolean = true;

  constructor() {
    // Only access window on client side
    if (typeof window !== 'undefined') {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = process.env.NEXT_PUBLIC_WS_URL || 'localhost:8000';
      this.url = `${wsProtocol}//${wsHost}/ws/live`;
    } else {
      // Default URL for SSR (won't be used)
      this.url = 'ws://localhost:8000/ws/live';
    }
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    this.isConnecting = true;

    try {
      console.log('Connecting to WebSocket:', this.url);
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.notifyHandlers('connection', { status: 'connected' });
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.notifyHandlers(message.type, message.data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.notifyHandlers('connection', { status: 'error', error });
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnecting = false;
        this.ws = null;
        this.notifyHandlers('connection', { status: 'disconnected' });

        if (this.shouldReconnect) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      this.isConnecting = false;
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.notifyHandlers('connection', { status: 'failed' });
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  on(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(type);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  private notifyHandlers(type: string, data: any): void {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in ${type} handler:`, error);
        }
      });
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getConnectionStatus(): 'connected' | 'connecting' | 'disconnected' {
    if (this.ws?.readyState === WebSocket.OPEN) return 'connected';
    if (this.isConnecting) return 'connecting';
    return 'disconnected';
  }
}

// Lazy initialization to avoid SSR issues
let wsClientInstance: WebSocketClient | null = null;

export const wsClient = typeof window !== 'undefined' 
  ? new WebSocketClient() 
  : ({
      connect: () => {},
      disconnect: () => {},
      subscribe: () => () => {},
      getConnectionStatus: () => 'disconnected' as const
    } as unknown as WebSocketClient);
