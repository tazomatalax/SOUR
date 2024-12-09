import { RealTimeMetrics, SystemConfig } from '../types/system';
import { Metrics } from '../types/metrics';

type WebSocketCallback = (data: RealTimeMetrics) => void;

export class WebSocketManager {
  private static instance: WebSocketManager;
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout = 1000;
  private callbacks: Set<WebSocketCallback> = new Set();

  private constructor() {}

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  connect(config: SystemConfig): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    const wsEndpoint = `ws://localhost:${config.visualization.dashboard_port}/ws`;
    this.ws = new WebSocket(wsEndpoint);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data: RealTimeMetrics = JSON.parse(event.data);
        this.notifyCallbacks(data);
      } catch (error) {
        console.error('Error parsing WebSocket data:', error);
      }
    };

    this.ws.onclose = () => {
      this.handleDisconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.handleDisconnect();
    };
  }

  private handleDisconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
        this.connect({
          visualization: {
            update_interval: 5000,
            plot_history: 3600,
            dashboard_port: 8050
          }
        } as SystemConfig);
      }, this.reconnectTimeout * this.reconnectAttempts);
    }
  }

  subscribe(callback: WebSocketCallback): () => void {
    this.callbacks.add(callback);
    return () => this.callbacks.delete(callback);
  }

  private notifyCallbacks(data: RealTimeMetrics): void {
    this.callbacks.forEach(callback => callback(data));
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const websocketManager = WebSocketManager.getInstance();