/**
 * WebSocket Store
 * Manages WebSocket connections and message handling
 */
import { writable, derived } from 'svelte/store';

// WebSocket connection states
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  ERROR = 'error',
}

// WebSocket message types
export enum MessageType {
  AI_REQUEST = 'ai_request',
  AI_RESPONSE = 'ai_response',
  PROGRESS = 'progress',
  ERROR = 'error',
}

// Message interfaces
export interface OutgoingMessage {
  type: MessageType;
  data: {
    task: 'analyze' | 'summarize' | 'transcribe';
    content: string;
    item_id?: string;
  };
}

export interface IncomingMessage {
  type: MessageType;
  data: {
    content?: string;
    progress?: number;
    error?: string;
  };
}

// WebSocket configuration
const WS_URL = import.meta.env.PUBLIC_WS_URL || 'ws://localhost:8000/api/ws';
const RECONNECT_INTERVAL = 2000;
const MAX_RECONNECT_ATTEMPTS = 5;

// Create stores
const createWebSocketStore = () => {
  // Internal state
  let socket: WebSocket | null = null;
  let reconnectAttempts = 0;
  let reconnectTimer: number | null = null;
  let messageQueue: OutgoingMessage[] = [];

  // Create the store
  const { subscribe, set, update } = writable({
    state: ConnectionState.DISCONNECTED,
    lastMessage: null as IncomingMessage | null,
    messages: [] as IncomingMessage[],
    error: null as Error | null,
  });

  // Event handlers
  const handleOpen = () => {
    console.log('WebSocket connected');
    reconnectAttempts = 0;

    update((state) => ({
      ...state,
      state: ConnectionState.CONNECTED,
      error: null,
    }));

    // Send any queued messages
    if (messageQueue.length > 0 && socket) {
      messageQueue.forEach((msg) => {
        socket?.send(JSON.stringify(msg));
      });
      messageQueue = [];
    }
  };

  const handleMessage = (event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data) as IncomingMessage;

      update((state) => ({
        ...state,
        lastMessage: message,
        messages: [...state.messages, message],
      }));

      // Dispatch custom event for components to listen to
      window.dispatchEvent(
        new CustomEvent('ws-message', {
          detail: message,
        })
      );
    } catch (err) {
      console.error('Error parsing WebSocket message:', err);
    }
  };

  const handleError = (event: Event) => {
    console.error('WebSocket error:', event);
    update((state) => ({
      ...state,
      state: ConnectionState.ERROR,
      error: new Error('WebSocket connection error'),
    }));
  };

  const handleClose = (event: CloseEvent) => {
    console.log('WebSocket closed:', event.code, event.reason);

    update((state) => ({
      ...state,
      state: ConnectionState.DISCONNECTED,
    }));

    // Attempt to reconnect if not closed cleanly
    if (!event.wasClean && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      reconnectTimer = window.setTimeout(() => {
        reconnectAttempts++;
        connect();
      }, RECONNECT_INTERVAL);
    }
  };

  // Connect to WebSocket
  const connect = () => {
    if (socket) {
      socket.close();
    }

    update((state) => ({
      ...state,
      state: ConnectionState.CONNECTING,
    }));

    try {
      socket = new WebSocket(WS_URL);
      socket.addEventListener('open', handleOpen);
      socket.addEventListener('message', handleMessage);
      socket.addEventListener('error', handleError);
      socket.addEventListener('close', handleClose);
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      update((state) => ({
        ...state,
        state: ConnectionState.ERROR,
        error: err instanceof Error ? err : new Error('Failed to create WebSocket'),
      }));
    }
  };

  // Disconnect from WebSocket
  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }

    if (socket) {
      socket.removeEventListener('open', handleOpen);
      socket.removeEventListener('message', handleMessage);
      socket.removeEventListener('error', handleError);
      socket.removeEventListener('close', handleClose);
      socket.close();
      socket = null;
    }

    set({
      state: ConnectionState.DISCONNECTED,
      lastMessage: null,
      messages: [],
      error: null,
    });
  };

  // Send a message through WebSocket
  const sendMessage = (message: OutgoingMessage): boolean => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
      return true;
    } else {
      // Queue message to send when connected
      messageQueue.push(message);

      // If disconnected, try to connect
      if (!socket || socket.readyState === WebSocket.CLOSED) {
        connect();
      }
      return false;
    }
  };

  // Clear message history
  const clearMessages = () => {
    update((state) => ({
      ...state,
      messages: [],
      lastMessage: null,
    }));
  };

  return {
    subscribe,
    connect,
    disconnect,
    sendMessage,
    clearMessages,
  };
};

// Create and export the WebSocket store
export const websocketStore = createWebSocketStore();

// Derived store for connection status
export const connectionStatus = derived(websocketStore, ($websocketStore) => $websocketStore.state);

// Derived store for latest message
export const latestMessage = derived(
  websocketStore,
  ($websocketStore) => $websocketStore.lastMessage
);
