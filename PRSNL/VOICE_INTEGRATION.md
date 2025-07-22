# 🎤 PRSNL Voice Integration Documentation

## Overview
PRSNL now includes comprehensive voice capabilities with emotion-aware text-to-speech (TTS) and enhanced speech-to-text (STT) functionality. The system supports natural voice interactions with emotional intelligence and customizable voice preferences.

## Key Features

### 🗣️ Text-to-Speech (TTS)
- **Chatterbox TTS Integration**: Primary TTS engine with emotion control
- **7 Emotion States**: neutral, happy, sad, angry, excited, calm, friendly
- **Voice Customization**: Speed (0.5x-2.0x), pitch (-50 to +50)
- **SSML Support**: Fixed to prevent tags from being spoken
- **Multiple Backend Support**: Abstraction layer for Chatterbox and Edge-TTS

### 👂 Speech-to-Text (STT) 
- **Enhanced Whisper Model**: Upgraded from 'base' to 'small' for better accuracy
- **Improved Recognition**: Better handling of technical terms and accents
- **Multi-language Support**: Supports multiple languages with auto-detection
- **Real-time Transcription**: Fast processing for voice interactions

### 🤖 Voice AI Crew
- **Specialized Agents**: Voice-specific CrewAI implementation
- **Context-Aware Responses**: Natural conversation flow
- **Emotional Intelligence**: Maps conversation tone to appropriate emotions
- **Intelligent Coordination**: Orchestrates voice interactions seamlessly

### ⚙️ Voice Settings
- **User Preferences**: Per-user voice configuration storage
- **Settings UI**: Comprehensive voice settings page
- **Model Selection**: Choose between different TTS backends
- **Real-time Preview**: Test voice settings before saving

## API Endpoints

### Voice Settings
```bash
# Get user settings
GET /api/user/settings

# Update voice settings
PUT /api/user/settings
{
  "voice_settings": {
    "tts_model": "chatterbox",
    "emotion": "friendly",
    "speed": 1.0,
    "pitch": 0
  }
}
```

### Text-to-Speech
```bash
# Convert text to speech
POST /api/voice/tts
{
  "text": "Hello! I'm excited to help.",
  "emotion": "excited",
  "speed": 1.0,
  "pitch": 0,
  "model": "chatterbox"
}
```

### Speech-to-Text
```bash
# Transcribe audio
POST /api/voice/transcribe
Content-Type: multipart/form-data
- audio: <audio file>
- language: "en" (optional)
```

### Voice Models
```bash
# List available models
GET /api/voice/models
```

## Emotion Guide

### Available Emotions
1. **neutral** - Default, balanced tone for general conversations
2. **happy** - Upbeat and cheerful for positive interactions
3. **sad** - Subdued and melancholic for empathetic responses
4. **angry** - Intense and forceful for urgent messages
5. **excited** - Energetic and enthusiastic for exciting news
6. **calm** - Soothing and relaxed for meditation or relaxation
7. **friendly** - Warm and welcoming for greetings and support

### Emotion Usage Examples
```python
# Greeting
{"text": "Welcome back! How can I help you today?", "emotion": "friendly"}

# Exciting news
{"text": "Great news! Your task is complete!", "emotion": "excited"}

# Error handling
{"text": "I understand this is frustrating. Let me help.", "emotion": "calm"}

# Urgent notification
{"text": "Critical alert! Immediate action required.", "emotion": "angry"}
```

## Implementation Details

### TTS Manager Architecture
```python
# Abstract base class for TTS backends
class TTSBackend(ABC):
    @abstractmethod
    async def generate_speech(self, text: str, **kwargs) -> bytes:
        pass

# Chatterbox implementation
class ChatterboxTTS(TTSBackend):
    def __init__(self):
        self.model = ChatTTS()
        self.emotion_seeds = {
            "neutral": 42,
            "happy": 123,
            "sad": 789,
            # ... etc
        }

# TTS Manager handles backend selection
class TTSManager:
    def get_backend(self, model: str) -> TTSBackend:
        if model == "chatterbox":
            return ChatterboxTTS()
        elif model == "edge-tts":
            return EdgeTTS()
```

### Voice Crew Structure
```yaml
Voice Crew:
  - Voice Response Agent:
      role: "Natural conversation specialist"
      goal: "Create engaging voice interactions"
      
  - Context Analyzer:
      role: "Conversation context expert"
      goal: "Understand user intent and context"
      
  - Emotion Mapper:
      role: "Emotional intelligence specialist"
      goal: "Map conversation tone to TTS emotions"
      
  - Voice Coordinator:
      role: "Voice interaction orchestrator"
      goal: "Coordinate seamless voice experiences"
```

## Configuration

### Environment Variables
```bash
# Voice model settings
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

# TTS settings
DEFAULT_TTS_MODEL=chatterbox
DEFAULT_TTS_EMOTION=friendly
DEFAULT_TTS_SPEED=1.0
```

### User Settings Schema
```python
class VoiceSettings(BaseModel):
    tts_model: str = "chatterbox"
    voice_id: str = "default"
    emotion: str = "friendly"
    speed: float = 1.0
    pitch: int = 0
    language: str = "en"
```

## Testing Voice Features

### Quick Test Commands
```bash
# Test TTS with different emotions
for emotion in neutral happy sad angry excited calm friendly; do
  curl -X POST http://localhost:8000/api/voice/tts \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"Testing $emotion emotion.\", \"emotion\": \"$emotion\"}" \
    -o "test_${emotion}.mp3"
done

# Test voice transcription
curl -X POST http://localhost:8000/api/voice/transcribe \
  -F "audio=@sample.wav"

# Update and test settings
curl -X PUT http://localhost:8000/api/user/settings \
  -H "Content-Type: application/json" \
  -d '{"voice_settings": {"emotion": "excited", "speed": 1.2}}'
```

### Frontend Voice Chat
1. Navigate to the Mind Palace (Chat) page
2. Click the microphone button to start recording
3. Speak your message
4. Click stop to send the audio
5. Receive voice response with appropriate emotion

## Troubleshooting

### Common Issues

#### TTS Not Working
- Check if Chatterbox is installed: `pip install chatterbox-tts`
- Verify CUDA availability for GPU acceleration
- Check audio output format compatibility

#### STT Poor Accuracy
- Ensure Whisper 'small' model is downloaded
- Check audio input quality (16kHz recommended)
- Verify language settings match audio language

#### WebSocket Connection Issues
- Confirm WebSocket endpoints in PUBLIC_ROUTES
- Check authentication token if using protected routes
- Verify CORS settings for WebSocket connections

#### Missing Voice Settings
- Run database migration for user_settings table
- Check if settings are being saved properly
- Verify user_id is correctly set

## Future Enhancements

### Planned Features
1. **Voice Cloning**: Custom voice profiles
2. **Multi-language TTS**: Support for more languages
3. **Voice Commands**: Control PRSNL with voice
4. **Conversation Memory**: Remember voice preferences per conversation
5. **Offline Mode**: Local-only voice processing
6. **Voice Analytics**: Track voice interaction patterns

### Performance Optimizations
1. **GPU Acceleration**: CUDA support for faster processing
2. **Model Caching**: Pre-load frequently used models
3. **Streaming TTS**: Real-time audio generation
4. **Batch Processing**: Handle multiple requests efficiently

## Integration Examples

### React/Svelte Component
```javascript
// Voice chat component
async function sendVoiceMessage(audioBlob) {
  const formData = new FormData();
  formData.append('audio', audioBlob);
  
  // Transcribe audio
  const transcription = await fetch('/api/voice/transcribe', {
    method: 'POST',
    body: formData
  }).then(r => r.json());
  
  // Get AI response
  const response = await getAIResponse(transcription.text);
  
  // Convert response to speech
  const audioResponse = await fetch('/api/voice/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: response.text,
      emotion: response.emotion || 'friendly'
    })
  }).then(r => r.blob());
  
  // Play audio
  const audioUrl = URL.createObjectURL(audioResponse);
  const audio = new Audio(audioUrl);
  audio.play();
}
```

### Python Integration
```python
import requests

class VoiceClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def text_to_speech(self, text, emotion="friendly"):
        response = requests.post(
            f"{self.base_url}/api/voice/tts",
            json={
                "text": text,
                "emotion": emotion,
                "speed": 1.0
            }
        )
        return response.content
    
    def speech_to_text(self, audio_file):
        with open(audio_file, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/voice/transcribe",
                files={'audio': f}
            )
        return response.json()
```

## Security Considerations

### Authentication
- Voice endpoints currently use auth bypasses (temporary)
- Production should implement proper JWT validation
- Rate limiting recommended for voice endpoints

### Privacy
- Audio files are processed in memory only
- No permanent storage of voice recordings
- User preferences encrypted in database

### Resource Limits
- Maximum audio file size: 25MB
- Maximum text length for TTS: 5000 characters
- Rate limits: 10 requests per minute per user

---

**Last Updated**: 2025-07-22  
**Version**: 1.0.0  
**Status**: Production Ready

This documentation provides comprehensive guidance for using and extending PRSNL's voice capabilities.