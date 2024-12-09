import { RealTimeMetrics } from '../types/system';
import { generateMockMetrics } from './mockData';

type WebSocketCallback = (data: RealTimeMetrics) => void;

export class MockWebSocketManager {
  private static instance: MockWebSocketManager;
  private callbacks: Set<WebSocketCallback> = new Set();
  private intervalId: number | null = null;
  private updateInterval = 1000; // 1 second updates

  private constructor() {}

  static getInstance(): MockWebSocketManager {
    if (!MockWebSocketManager.instance) {
      MockWebSocketManager.instance = new MockWebSocketManager();
    }
    return MockWebSocketManager.instance;
  }

  connect(): void {
    if (this.intervalId !== null) return;

    // Emit initial data immediately
    this.emitData();

    // Set up interval for continuous updates
    this.intervalId = window.setInterval(() => {
      this.emitData();
    }, this.updateInterval);
  }

  private emitData(): void {
    const mockData = generateMockMetrics();
    this.notifyCallbacks(mockData);
  }

  subscribe(callback: WebSocketCallback): () => void {
    this.callbacks.add(callback);
    return () => this.callbacks.delete(callback);
  }

  private notifyCallbacks(data: RealTimeMetrics): void {
    this.callbacks.forEach(callback => callback(data));
  }

  disconnect(): void {
    if (this.intervalId !== null) {
      window.clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
}

export const mockWebSocketManager = MockWebSocketManager.getInstance();