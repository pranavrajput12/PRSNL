/**
 * CodeMirror Real-time Service
 *
 * Enterprise-grade WebSocket client for real-time synchronization
 * between CLI and Web interfaces.
 */

import { writable, type Writable, get } from 'svelte/store';

export interface RealtimeEvent {
  event_id: string;
  event_type:
    | 'analysis_started'
    | 'analysis_progress'
    | 'analysis_completed'
    | 'insight_added'
    | 'pattern_detected';
  source: 'cli' | 'web' | 'system';
  user_id: string;
  repo_id?: string;
  analysis_id?: string;
  timestamp: string;
  data: Record<string, any>;
  checksum?: string;
}

export interface AnalysisProgress {
  analysis_id: string;
  progress: number;
  stage: string;
  details?: Record<string, any>;
  insights?: any[];
  patterns?: any[];
}

interface ConnectionState {
  connected: boolean;
  reconnectAttempts: number;
  lastError?: string;
}

class CodeMirrorRealtimeService {
  private ws: WebSocket | null = null;
  private reconnectTimeout: number | null = null;
  private heartbeatInterval: number | null = null;
  private eventHandlers: Map<string, Set<(event: RealtimeEvent) => void>> = new Map();

  // Stores
  public connectionState: Writable<ConnectionState> = writable({
    connected: false,
    reconnectAttempts: 0,
  });

  public activeAnalyses: Writable<Map<string, AnalysisProgress>> = writable(new Map());

  // Configuration
  private maxReconnectAttempts = 10;
  private reconnectBaseDelay = 2000; // 2 seconds

  constructor() {
    // Auto-connect when service is created
    if (typeof window !== 'undefined') {
      this.connect();
    }
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    try {
      // Get auth token (optional for now)
      const token = localStorage.getItem('prsnl_token') || 'no-auth-required';

      // Build WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/codemirror/ws/sync?token=${token}`;

      // Create WebSocket connection
      this.ws = new WebSocket(wsUrl);

      // Set up event handlers
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      this.connectionState.update((state) => ({
        ...state,
        lastError: error.message,
      }));
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.clearTimers();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.connectionState.set({
      connected: false,
      reconnectAttempts: 0,
    });
  }

  /**
   * Subscribe to specific analysis updates
   */
  subscribeToAnalysis(analysisId: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected');
      return;
    }

    this.ws.send(
      JSON.stringify({
        type: 'subscribe',
        channels: [`analysis:${analysisId}`],
      })
    );
  }

  /**
   * Register event handler
   */
  on(eventType: string, handler: (event: RealtimeEvent) => void): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }

    this.eventHandlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.eventHandlers.get(eventType)?.delete(handler);
    };
  }

  /**
   * Send event to server
   */
  send(event: Partial<RealtimeEvent>): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('Cannot send event: WebSocket not connected');
      return;
    }

    this.ws.send(JSON.stringify(event));
  }

  private handleOpen(): void {
    console.log('WebSocket connected');

    this.connectionState.update((state) => ({
      connected: true,
      reconnectAttempts: 0,
    }));

    // Start heartbeat
    this.startHeartbeat();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);

      // Handle different message types
      switch (data.type) {
        case 'initial_state':
          this.handleInitialState(data);
          break;

        case 'heartbeat_ack':
          // Heartbeat acknowledged
          break;

        default:
          // Handle as realtime event
          this.handleRealtimeEvent(data);
          break;
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }

  private handleRealtimeEvent(event: RealtimeEvent): void {
    // Update analysis progress if applicable
    if (event.analysis_id) {
      const progress = get(this.activeAnalyses);

      switch (event.event_type) {
        case 'analysis_started':
          progress.set(event.analysis_id, {
            analysis_id: event.analysis_id,
            progress: 0,
            stage: 'started',
            details: event.data,
          });
          break;

        case 'analysis_progress':
          const current = progress.get(event.analysis_id) || {
            analysis_id: event.analysis_id,
            progress: 0,
            stage: 'unknown',
            insights: [],
            patterns: [],
          };

          progress.set(event.analysis_id, {
            ...current,
            progress: event.data.progress || current.progress,
            stage: event.data.stage || current.stage,
            details: { ...current.details, ...event.data.details },
          });
          break;

        case 'insight_added':
          const analysisWithInsight = progress.get(event.analysis_id);
          if (analysisWithInsight) {
            analysisWithInsight.insights = [
              ...(analysisWithInsight.insights || []),
              event.data.insight,
            ];
            progress.set(event.analysis_id, analysisWithInsight);
          }
          break;

        case 'analysis_completed':
          const completed = progress.get(event.analysis_id);
          if (completed) {
            completed.progress = 100;
            completed.stage = 'completed';
            progress.set(event.analysis_id, completed);
          }
          break;
      }

      this.activeAnalyses.set(progress);
    }

    // Trigger event handlers
    const handlers = this.eventHandlers.get(event.event_type);
    if (handlers) {
      handlers.forEach((handler) => handler(event));
    }

    // Also trigger wildcard handlers
    const wildcardHandlers = this.eventHandlers.get('*');
    if (wildcardHandlers) {
      wildcardHandlers.forEach((handler) => handler(event));
    }
  }

  private handleInitialState(data: any): void {
    if (data.analyses) {
      const progress = new Map<string, AnalysisProgress>();

      data.analyses.forEach((analysis: any) => {
        progress.set(analysis.id, {
          analysis_id: analysis.id,
          progress: analysis.progress_percentage || 0,
          stage: analysis.current_stage || analysis.status,
          details: {
            analysis_type: analysis.analysis_type,
            created_at: analysis.created_at,
          },
        });
      });

      this.activeAnalyses.set(progress);
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);

    this.connectionState.update((state) => ({
      ...state,
      lastError: 'WebSocket error occurred',
    }));
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket closed:', event.code, event.reason);

    this.connectionState.update((state) => ({
      ...state,
      connected: false,
    }));

    this.clearTimers();

    // Schedule reconnect unless explicitly closed
    if (event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    const state = get(this.connectionState);

    if (state.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    // Calculate exponential backoff
    const delay = Math.min(
      this.reconnectBaseDelay * Math.pow(2, state.reconnectAttempts),
      60000 // Max 60 seconds
    );

    console.log(`Reconnecting in ${delay / 1000} seconds...`);

    this.connectionState.update((s) => ({
      ...s,
      reconnectAttempts: s.reconnectAttempts + 1,
    }));

    this.reconnectTimeout = window.setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(
          JSON.stringify({
            type: 'heartbeat',
            timestamp: new Date().toISOString(),
          })
        );
      }
    }, 30000); // 30 seconds
  }

  private clearTimers(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
}

// Export singleton instance
export const realtimeService = new CodeMirrorRealtimeService();
