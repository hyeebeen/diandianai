/**
 * Server-Sent Events (SSE) service for real-time data updates
 * Handles connections to backend SSE endpoints for live data streaming
 */

export interface SSEMessage<T = any> {
  type: string;
  data: T;
  timestamp: string;
  id?: string;
}

export interface SSEConnectionOptions {
  endpoint: string;
  token?: string;
  reconnectDelay?: number;
  maxRetries?: number;
  onMessage?: (message: SSEMessage) => void;
  onError?: (error: Event) => void;
  onOpen?: (event: Event) => void;
  onClose?: (event: Event) => void;
}

export interface GPSLocationUpdate {
  shipment_id: string;
  latitude: number;
  longitude: number;
  timestamp: string;
  speed?: number;
  heading?: number;
  altitude?: number;
  accuracy?: number;
}

export interface NotificationUpdate {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  priority?: 'low' | 'medium' | 'high';
  action_url?: string;
}

export interface ShipmentStatusUpdate {
  shipment_id: string;
  status: string;
  location?: string;
  timestamp: string;
  notes?: string;
}

export interface AIMessageUpdate {
  conversation_id: string;
  message_id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  typing?: boolean;
}

export class SSEConnection {
  private eventSource: EventSource | null = null;
  private options: SSEConnectionOptions;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private isManualClose = false;

  constructor(options: SSEConnectionOptions) {
    this.options = {
      reconnectDelay: 3000,
      maxRetries: 10,
      ...options
    };
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.isManualClose = false;

        // Build URL with authentication token
        const url = new URL(this.options.endpoint, import.meta.env.VITE_API_BASE_URL);
        if (this.options.token) {
          url.searchParams.set('token', this.options.token);
        }

        this.eventSource = new EventSource(url.toString());

        this.eventSource.onopen = (event) => {
          console.log('SSE connection opened:', this.options.endpoint);
          this.reconnectAttempts = 0;
          this.options.onOpen?.(event);
          resolve();
        };

        this.eventSource.onmessage = (event) => {
          try {
            const message: SSEMessage = JSON.parse(event.data);
            this.options.onMessage?.(message);
          } catch (error) {
            console.error('Failed to parse SSE message:', error, event.data);
          }
        };

        this.eventSource.onerror = (event) => {
          console.error('SSE connection error:', event, this.options.endpoint);
          this.options.onError?.(event);

          if (!this.isManualClose && this.reconnectAttempts < (this.options.maxRetries || 10)) {
            this.scheduleReconnect();
          } else if (this.reconnectAttempts === 0) {
            reject(new Error('Failed to establish SSE connection'));
          }
        };

        this.eventSource.onclose = (event) => {
          console.log('SSE connection closed:', this.options.endpoint);
          this.options.onClose?.(event);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;
    const delay = this.options.reconnectDelay! * Math.pow(2, Math.min(this.reconnectAttempts - 1, 3));

    console.log(`Scheduling SSE reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);

    this.reconnectTimer = setTimeout(() => {
      if (!this.isManualClose) {
        this.connect().catch(console.error);
      }
    }, delay);
  }

  close(): void {
    this.isManualClose = true;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  get readyState(): number {
    return this.eventSource?.readyState ?? EventSource.CLOSED;
  }

  get isConnected(): boolean {
    return this.readyState === EventSource.OPEN;
  }
}

export class SSEService {
  private connections: Map<string, SSEConnection> = new Map();
  private token: string | null = null;

  setAuthToken(token: string | null): void {
    this.token = token;
  }

  /**
   * Subscribe to GPS location updates for shipments
   */
  subscribeToGPSUpdates(
    onUpdate: (update: GPSLocationUpdate) => void,
    onError?: (error: Event) => void
  ): () => void {
    const connectionKey = 'gps-updates';

    const connection = new SSEConnection({
      endpoint: '/api/sse/gps',
      token: this.token || undefined,
      onMessage: (message: SSEMessage) => {
        if (message.type === 'gps_location_update') {
          onUpdate(message.data as GPSLocationUpdate);
        }
      },
      onError,
    });

    this.connections.set(connectionKey, connection);
    connection.connect().catch(console.error);

    // Return unsubscribe function
    return () => {
      connection.close();
      this.connections.delete(connectionKey);
    };
  }

  /**
   * Subscribe to shipment status updates
   */
  subscribeToShipmentUpdates(
    onUpdate: (update: ShipmentStatusUpdate) => void,
    onError?: (error: Event) => void
  ): () => void {
    const connectionKey = 'shipment-updates';

    const connection = new SSEConnection({
      endpoint: '/api/sse/shipments',
      token: this.token || undefined,
      onMessage: (message: SSEMessage) => {
        if (message.type === 'shipment_status_update') {
          onUpdate(message.data as ShipmentStatusUpdate);
        }
      },
      onError,
    });

    this.connections.set(connectionKey, connection);
    connection.connect().catch(console.error);

    return () => {
      connection.close();
      this.connections.delete(connectionKey);
    };
  }

  /**
   * Subscribe to real-time notifications
   */
  subscribeToNotifications(
    onNotification: (notification: NotificationUpdate) => void,
    onError?: (error: Event) => void
  ): () => void {
    const connectionKey = 'notifications';

    const connection = new SSEConnection({
      endpoint: '/api/sse/notifications',
      token: this.token || undefined,
      onMessage: (message: SSEMessage) => {
        if (message.type === 'notification') {
          onNotification(message.data as NotificationUpdate);
        }
      },
      onError,
    });

    this.connections.set(connectionKey, connection);
    connection.connect().catch(console.error);

    return () => {
      connection.close();
      this.connections.delete(connectionKey);
    };
  }

  /**
   * Subscribe to AI conversation updates
   */
  subscribeToAIMessages(
    conversationId: string,
    onMessage: (message: AIMessageUpdate) => void,
    onError?: (error: Event) => void
  ): () => void {
    const connectionKey = `ai-messages-${conversationId}`;

    const connection = new SSEConnection({
      endpoint: `/api/sse/ai/conversations/${conversationId}`,
      token: this.token || undefined,
      onMessage: (message: SSEMessage) => {
        if (message.type === 'ai_message') {
          onMessage(message.data as AIMessageUpdate);
        }
      },
      onError,
    });

    this.connections.set(connectionKey, connection);
    connection.connect().catch(console.error);

    return () => {
      connection.close();
      this.connections.delete(connectionKey);
    };
  }

  /**
   * Get connection status for debugging
   */
  getConnectionStatus(): Record<string, string> {
    const status: Record<string, string> = {};

    this.connections.forEach((connection, key) => {
      const state = connection.readyState;
      status[key] = state === EventSource.CONNECTING ? 'connecting' :
                   state === EventSource.OPEN ? 'open' :
                   state === EventSource.CLOSED ? 'closed' : 'unknown';
    });

    return status;
  }

  /**
   * Close all connections
   */
  disconnectAll(): void {
    this.connections.forEach((connection) => {
      connection.close();
    });
    this.connections.clear();
  }

  /**
   * Close specific connection
   */
  disconnect(connectionKey: string): void {
    const connection = this.connections.get(connectionKey);
    if (connection) {
      connection.close();
      this.connections.delete(connectionKey);
    }
  }
}

// Create singleton instance
export const sseService = new SSEService();

// Export default instance
export default sseService;