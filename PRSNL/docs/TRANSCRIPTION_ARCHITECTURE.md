# Transcription Architecture - PRSNL v4.2.0

## Overview

PRSNL uses **whisper.cpp** exclusively for all transcription needs, providing:
- High-accuracy offline transcription
- 99 language support
- Multiple model sizes for different use cases
- Complete privacy with no cloud dependencies

## Architecture

```
┌─────────────────────────────────────────┐
│          Transcription Request          │
│      (Audio/Video file or URL)          │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│    SimplifiedTranscriptionService       │
│  - Model auto-selection                 │
│  - Language detection                   │
│  - Performance optimization             │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│      WhisperCppTranscriptionService     │
│  - Model management                     │
│  - Audio preprocessing                  │
│  - Word-level timestamps                │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│         whisper.cpp (C++)               │
│  - CPU-optimized inference              │
│  - Multi-threaded processing            │
│  - Low memory footprint                 │
└─────────────────────────────────────────┘
```

## Service Components

### 1. SimplifiedTranscriptionService
**Location**: `/backend/app/services/whisper_only_transcription.py`

Main entry point for all transcription:
- Automatic model selection based on file size
- Priority-based transcription (speed/balanced/accuracy)
- Batch transcription support
- Model management

### 2. WhisperCppTranscriptionService
**Location**: `/backend/app/services/whisper_cpp_transcription.py`

Low-level whisper.cpp integration:
- Model downloading from Hugging Face
- Audio format conversion (FFmpeg)
- Direct whisper.cpp API access
- Performance monitoring

## Model Selection Strategy

### Automatic Selection (Default)
```python
File Size → Model Selection:
- < 5MB:    base   (74MB model, fast)
- 5-20MB:   small  (244MB model, accurate)
- 20-50MB:  small  (balanced for larger files)
- > 50MB:   base   (performance consideration)
```

### Manual Selection
```python
Priority → Model:
- "speed":    tiny   (39MB, fastest)
- "balanced": base   (74MB, recommended)
- "accuracy": small  (244MB, high quality)
```

## Integration Points

### 1. Video Processing
```python
# app/services/video_processor.py
async def transcribe_video(self, video_path: str):
    result = await transcription_service.transcribe_audio(
        audio_path=video_path,
        auto_model_selection=True
    )
```

### 2. API Endpoint
```python
# app/api/ai.py
@router.post("/transcribe")
async def transcribe_audio(request: TranscriptionRequest):
    result = await transcription_service.transcribe_with_options(
        audio_path=request.audio_url,
        priority=request.priority
    )
```

### 3. Direct Usage
```python
from app.services.whisper_only_transcription import transcription_service

# Simple transcription
result = await transcription_service.transcribe_audio("audio.mp3")

# With options
result = await transcription_service.transcribe_with_options(
    audio_path="audio.mp3",
    priority="accuracy"  # Uses small model
)
```

## Configuration

### Environment Variables
```bash
# Model storage (auto-created)
WHISPER_CPP_MODEL_DIR=storage/whisper_models

# Default model
WHISPER_CPP_DEFAULT_MODEL=base

# CPU threads (auto-detected if not set)
WHISPER_CPP_THREADS=8
```

### Model Storage
Models are stored in: `backend/storage/whisper_models/`
- Auto-downloaded on first use
- Cached for subsequent runs
- Models: ggml-tiny.bin, ggml-base.bin, etc.

## Performance Characteristics

### Model Comparison
| Model | Size | RAM Usage | Speed | Accuracy |
|-------|------|-----------|-------|----------|
| tiny | 39MB | ~300MB | 10x realtime | Good |
| base | 74MB | ~500MB | 5x realtime | Better |
| small | 244MB | ~1GB | 2x realtime | Great |
| medium | 769MB | ~2.5GB | 1x realtime | Excellent |
| large | 1.5GB | ~4GB | 0.5x realtime | Best |

### Optimization Tips
1. **CPU**: Ensure AVX/AVX2 support for best performance
2. **Memory**: Models are cached, first load is slower
3. **Batch**: Process multiple files sequentially to reuse loaded model
4. **Format**: Direct WAV processing is fastest

## API Usage

### REST API
```bash
# Transcribe with default settings
curl -X POST http://localhost:8000/api/ai/transcribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "/path/to/audio.mp3",
    "priority": "balanced"
  }'

# Response
{
  "text": "Transcribed text here...",
  "confidence": 0.95,
  "word_count": 150,
  "duration": 60.5,
  "model_used": "base",
  "service": "whisper.cpp"
}
```

### Priority Options
- `"speed"`: Fast transcription with tiny model
- `"balanced"`: Default, uses base model
- `"accuracy"`: High quality with small model

## Language Support

### Supported Languages (99 total)
Major languages include:
- English, Spanish, French, German, Italian
- Chinese, Japanese, Korean
- Arabic, Hebrew, Hindi
- Russian, Polish, Portuguese
- And 80+ more

### Auto Language Detection
Coming soon - currently defaults to English

## Error Handling

### Common Errors
1. **Model not found**: Auto-downloads on first use
2. **Out of memory**: Use smaller model
3. **Unsupported format**: Converts via FFmpeg
4. **No audio content**: Returns None gracefully

### Graceful Degradation
- If model fails to load, tries smaller model
- If transcription fails, returns None (no partial data)
- All errors logged with context

## Monitoring

### Key Metrics
- Model loading time
- Transcription duration
- Real-time factor (processing time / audio duration)
- Word count and confidence scores

### Logging
```
INFO: 🎙️ Transcribing audio.mp3 with model: base
INFO: ✅ Transcription complete - 150 words
INFO: Model used: base, Confidence: 0.95
```

## Testing

### Unit Tests
```bash
# Test transcription service
cd backend
python scripts/test_whisper_cpp_integration.py
```

### Integration Tests
```bash
# Test full AI integration including transcription
python scripts/test_ai_integrations.py
```

### Manual Testing
1. Upload audio/video through UI
2. Check transcription in item details
3. Verify model selection in logs

## Migration from Hybrid Service

### Old Code (Hybrid)
```python
from app.services.hybrid_transcription import hybrid_transcription_service
result = await hybrid_transcription_service.transcribe_audio(
    audio_path=path,
    strategy=TranscriptionStrategy.AUTO
)
```

### New Code (Simplified)
```python
from app.services.whisper_only_transcription import transcription_service
result = await transcription_service.transcribe_audio(
    audio_path=path,
    auto_model_selection=True
)
```

## Benefits

1. **Simplicity**: One service, no complex routing
2. **Reliability**: No external dependencies
3. **Privacy**: All processing stays local
4. **Quality**: Consistent high accuracy
5. **Performance**: CPU-optimized implementation

## Future Enhancements

1. **Language Detection**: Auto-detect input language
2. **Speaker Diarization**: Identify different speakers
3. **Real-time Streaming**: Live transcription
4. **Custom Vocabulary**: Domain-specific terms
5. **GPU Acceleration**: For faster processing

---

This architecture ensures PRSNL provides:
- ✅ High-accuracy transcription
- ✅ Complete privacy
- ✅ Predictable performance
- ✅ Simple integration