# RealtimeSTT Integration Documentation

## Overview

PRSNL now supports real-time streaming speech-to-text using the RealtimeSTT library. This enables live transcription as users speak, providing immediate feedback and a more responsive voice interaction experience.

## Architecture

### Components

1. **RealtimeSTT Service** (`backend/app/services/realtime_stt_service.py`)
   - Manages RealtimeSTT recorder instance
   - Handles real-time transcription callbacks
   - Provides language and model configuration

2. **WebSocket Endpoint** (`/api/voice/ws/streaming`)
   - Real-time bidirectional communication
   - Streaming transcription updates
   - AI processing integration

3. **Voice Service Integration**
   - Processes transcribed text with Cortex personality
   - Generates AI responses
   - Optional TTS audio generation

## WebSocket Protocol

### Client -> Server Messages

```json
// Start streaming transcription
{
  "type": "start"
}

// Stop streaming transcription
{
  "type": "stop"
}

// Process accumulated text with AI
{
  "type": "process",
  "text": "optional text to process",  // If not provided, uses accumulated text
  "include_audio": true  // Whether to generate TTS audio response
}

// Change transcription language
{
  "type": "set_language",
  "language": "en"  // ISO language code
}

// Keepalive
{
  "type": "ping"
}
```

### Server -> Client Messages

```json
// Partial transcription (real-time updates)
{
  "type": "partial",
  "text": "Hello, I am...",
  "is_final": false
}

// Final transcription (sentence complete)
{
  "type": "final", 
  "text": "Hello, I am speaking.",
  "is_final": true
}

// Streaming status updates
{
  "type": "streaming_started",
  "status": "active"
}

{
  "type": "streaming_stopped",
  "status": "inactive",
  "accumulated_text": "All transcribed text"
}

// AI response
{
  "type": "ai_response",
  "data": {
    "user_text": "What user said",
    "ai_text": "Raw AI response",
    "personalized_text": "Cortex personality response",
    "mood": "primary"
  }
}

// Audio response (if requested)
{
  "type": "audio_response",
  "format": "mp3",
  "data": "base64_encoded_audio"
}

// Error messages
{
  "type": "error",
  "message": "Error description"
}
```

## Configuration

### RealtimeSTT Settings

The service uses optimized settings for real-time transcription:

- **Model**: "base" (balance of speed and accuracy)
- **Real-time Model**: "tiny" (for faster streaming updates)
- **Language**: "en" (default, configurable)
- **Silence Detection**: 0.4 sensitivity
- **Voice Activity Detection**: Level 3
- **Post-speech Pause**: 0.4 seconds
- **Minimum Recording**: 0.5 seconds

### Available Models

- `tiny`: Fastest, least accurate
- `base`: Good balance (default)
- `small`: Better accuracy
- `medium`: High accuracy
- `large`: Best accuracy, slowest

## Usage Example

### JavaScript/TypeScript Client

```javascript
class RealtimeSTTClient {
  constructor(wsUrl = 'ws://localhost:8000/api/voice/ws/streaming') {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.accumulatedText = [];
  }

  async connect() {
    this.ws = new WebSocket(this.wsUrl);
    
    this.ws.onopen = () => {
      console.log('Connected to RealtimeSTT');
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'partial':
        console.log('Partial:', data.text);
        // Update UI with partial text
        break;
        
      case 'final':
        console.log('Final:', data.text);
        this.accumulatedText.push(data.text);
        // Update UI with final text
        break;
        
      case 'ai_response':
        console.log('AI says:', data.data.personalized_text);
        // Display AI response
        break;
        
      case 'audio_response':
        // Play audio response
        const audio = new Audio('data:audio/mp3;base64,' + data.data);
        audio.play();
        break;
    }
  }

  startStreaming() {
    this.ws.send(JSON.stringify({ type: 'start' }));
  }

  stopStreaming() {
    this.ws.send(JSON.stringify({ type: 'stop' }));
  }

  processWithAI(text = null) {
    this.ws.send(JSON.stringify({
      type: 'process',
      text: text,
      include_audio: true
    }));
  }

  setLanguage(language) {
    this.ws.send(JSON.stringify({
      type: 'set_language',
      language: language
    }));
  }
}

// Usage
const client = new RealtimeSTTClient();
await client.connect();
client.startStreaming();

// Later...
client.stopStreaming();
client.processWithAI();
```

## Testing

Run the test script to verify the integration:

```bash
cd backend
python test_realtime_stt.py
```

The test will:
1. Connect to the WebSocket endpoint
2. Start streaming transcription
3. Listen for 30 seconds
4. Stop streaming
5. Process accumulated text with AI
6. Test language switching

## Troubleshooting

### Common Issues

1. **"RealtimeSTT not installed"**
   ```bash
   pip install RealtimeSTT>=0.1.15
   ```

2. **Microphone not detected**
   - Check system microphone permissions
   - Verify audio input device is available
   - Test with: `python -m RealtimeSTT.test`

3. **Poor transcription quality**
   - Try a larger model (small, medium)
   - Ensure clear audio input
   - Check microphone placement

4. **WebSocket connection fails**
   - Verify backend is running
   - Check authentication if required
   - Ensure port 8000 is accessible

### Performance Optimization

- Use "tiny" model for real-time updates
- Adjust silence detection sensitivity
- Increase post-speech pause for better sentence detection
- Consider chunking long transcriptions

## Security Considerations

1. **Authentication**: The endpoint uses optional authentication. In production, ensure proper auth is required.

2. **Rate Limiting**: Consider implementing rate limits to prevent abuse.

3. **Resource Management**: RealtimeSTT uses system microphone access. Ensure proper permissions and resource cleanup.

4. **Data Privacy**: Transcribed audio is processed locally using Whisper. No external API calls for transcription.

## Future Enhancements

1. **Multi-language Support**: Automatic language detection
2. **Speaker Diarization**: Identify multiple speakers
3. **Custom Vocabulary**: Domain-specific terms
4. **Noise Reduction**: Pre-processing for better accuracy
5. **Mobile SDK**: Native mobile integration