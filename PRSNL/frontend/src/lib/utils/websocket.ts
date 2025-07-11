/**
 * WebSocket utility for real-time streaming
 */

export interface WebSocketMessage {
  type: string;
  data: any;
}

export interface WebSocketOptions {
  url: string;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onOpen?: () => void;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
}

export class StreamingWebSocket {
  private ws: WebSocket | null = null;
  private options: Required<WebSocketOptions>;
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private messageQueue: any[] = [];
  private isConnecting = false;

  constructor(options: WebSocketOptions) {
    this.options = {
      reconnect: true,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      onOpen: () => {},
      onMessage: () => {},
      onError: () => {},
      onClose: () => {},
      ...options,
    };
  }

  connect(): void {
    if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.isConnecting = true;

    try {
      this.ws = new WebSocket(this.options.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.options.onOpen();

        // Send queued messages
        while (this.messageQueue.length > 0) {
          const message = this.messageQueue.shift();
          this.send(message);
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          this.options.onMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.options.onError(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnecting = false;
        this.options.onClose();

        if (this.options.reconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.isConnecting = false;

      if (this.options.reconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    this.reconnectAttempts++;
    const delay = this.options.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      // Queue message if not connected
      this.messageQueue.push(data);

      // Try to connect if not already
      if (!this.isConnecting) {
        this.connect();
      }
    }
  }

  close(): void {
    this.options.reconnect = false;

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

/**
 * Create a WebSocket connection for AI streaming
 */
export function createStreamingConnection(
  endpoint: string,
  handlers: {
    onConnect?: () => void;
    onTyping?: () => void;
    onChunk?: (text: string) => void;
    onComplete?: (data: any) => void;
    onError?: (error: any) => void;
    onContext?: (data: any) => void;
  }
): StreamingWebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.hostname;
  // In development, use the same port as frontend (Vite will proxy)
  // In production, use port 8001 (NGINX proxy)
  const port = import.meta.env.MODE === 'production' ? 8001 : window.location.port;
  const url = `${protocol}//${host}:${port}${endpoint}`;

  console.debug('[WebSocket] Creating connection to:', url);

  return new StreamingWebSocket({
    url,
    onOpen: () => {
      console.debug('[WebSocket] Connection opened');
      handlers.onConnect?.();
    },
    onMessage: (message) => {
      console.debug('[WebSocket] Message received:', message);

      switch (message.type) {
        case 'connection':
          console.debug('[WebSocket] Connection established:', message);
          break;

        case 'status':
          console.debug('[WebSocket] Status update:', message.message);
          handlers.onTyping?.();
          break;

        case 'chunk':
          handlers.onChunk?.(message.content);
          break;

        case 'complete':
          handlers.onComplete?.({
            citations: message.citations,
            context_count: message.context_count,
            conversation_id: message.conversation_id,
            suggested_items: message.suggested_items,
            insights: message.insights,
          });
          break;

        case 'error':
          console.error('[WebSocket] Error:', message.message);
          handlers.onError?.({ message: message.message });
          break;

        case 'typing':
          handlers.onTyping?.();
          break;

        case 'response_chunk':
          // Legacy format support
          handlers.onChunk?.(message.data?.text || '');
          break;

        case 'context':
          handlers.onContext?.(message.data);
          break;
      }
    },
    onError: (error) => {
      console.error('[WebSocket] Connection error:', error);
      handlers.onError?.({ message: 'WebSocket connection error' });
    },
    onClose: () => {
      console.debug('[WebSocket] Connection closed');
    },
  });
}

/**
 * Create a typed event emitter for WebSocket events
 */
export class StreamingEventEmitter extends EventTarget {
  emit(type: string, data?: any): void {
    this.dispatchEvent(new CustomEvent(type, { detail: data }));
  }

  on(type: string, handler: (event: CustomEvent) => void): void {
    this.addEventListener(type, handler as EventListener);
  }

  off(type: string, handler: (event: CustomEvent) => void): void {
    this.removeEventListener(type, handler as EventListener);
  }
}
