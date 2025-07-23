// RealtimeSTT WebSocket Client for PRSNL

export interface RealtimeSTTMessage {
  type: string;
  text?: string;
  is_final?: boolean;
  data?: any;
  message?: string;
  status?: string;
  accumulated_text?: string;
  language?: string;
  format?: string;
}

export interface AIResponseData {
  user_text: string;
  ai_text: string;
  personalized_text: string;
  mood: string;
  emotion?: string;
}

export class RealtimeSTTClient {
  private ws: WebSocket | null = null;
  private wsUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnected = false;
  private accumulatedText: string[] = [];

  // Event handlers
  onPartialTranscription?: (text: string) => void;
  onFinalTranscription?: (text: string) => void;
  onAIResponse?: (response: AIResponseData) => void;
  onAudioResponse?: (audioData: string, format: string) => void;
  onError?: (error: string) => void;
  onConnectionChange?: (connected: boolean) => void;
  onStreamingStatusChange?: (active: boolean) => void;

  constructor(wsUrl?: string) {
    // Use environment variable or default
    this.wsUrl = wsUrl || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/voice/ws/streaming`;
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.wsUrl);

        this.ws.onopen = () => {
          console.log('Connected to RealtimeSTT WebSocket');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.onConnectionChange?.(true);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data: RealtimeSTTMessage = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.onError?.('WebSocket connection error');
        };

        this.ws.onclose = () => {
          console.log('WebSocket connection closed');
          this.isConnected = false;
          this.onConnectionChange?.(false);
          this.attemptReconnect();
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(data: RealtimeSTTMessage): void {
    switch (data.type) {
      case 'partial':
        if (data.text) {
          this.onPartialTranscription?.(data.text);
        }
        break;

      case 'final':
        if (data.text) {
          this.accumulatedText.push(data.text);
          this.onFinalTranscription?.(data.text);
        }
        break;

      case 'streaming_started':
        this.onStreamingStatusChange?.(true);
        this.accumulatedText = [];
        break;

      case 'streaming_stopped':
        this.onStreamingStatusChange?.(false);
        if (data.accumulated_text) {
          console.log('Accumulated text:', data.accumulated_text);
        }
        break;

      case 'ai_response':
        if (data.data) {
          this.onAIResponse?.(data.data as AIResponseData);
        }
        break;

      case 'audio_response':
        if (data.data && data.format) {
          this.onAudioResponse?.(data.data, data.format);
        }
        break;

      case 'error':
        if (data.message) {
          this.onError?.(data.message);
        }
        break;

      case 'language_changed':
        console.log('Language changed to:', data.language);
        break;

      case 'processing':
        console.log('Processing:', data.status);
        break;

      case 'pong':
        // Keepalive response
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.onError?.('Failed to reconnect after multiple attempts');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  startStreaming(): void {
    if (!this.isConnected || !this.ws) {
      this.onError?.('Not connected to WebSocket');
      return;
    }

    this.ws.send(JSON.stringify({ type: 'start' }));
  }

  stopStreaming(): void {
    if (!this.isConnected || !this.ws) {
      this.onError?.('Not connected to WebSocket');
      return;
    }

    this.ws.send(JSON.stringify({ type: 'stop' }));
  }

  processWithAI(text?: string, includeAudio: boolean = true): void {
    if (!this.isConnected || !this.ws) {
      this.onError?.('Not connected to WebSocket');
      return;
    }

    const message: any = {
      type: 'process',
      include_audio: includeAudio
    };

    if (text) {
      message.text = text;
    }

    this.ws.send(JSON.stringify(message));
  }

  setLanguage(language: string): void {
    if (!this.isConnected || !this.ws) {
      this.onError?.('Not connected to WebSocket');
      return;
    }

    this.ws.send(JSON.stringify({
      type: 'set_language',
      language: language
    }));
  }

  sendPing(): void {
    if (!this.isConnected || !this.ws) {
      return;
    }

    this.ws.send(JSON.stringify({ type: 'ping' }));
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  getAccumulatedText(): string {
    return this.accumulatedText.join(' ');
  }

  clearAccumulatedText(): void {
    this.accumulatedText = [];
  }

  isStreamingActive(): boolean {
    return this.isConnected;
  }
}