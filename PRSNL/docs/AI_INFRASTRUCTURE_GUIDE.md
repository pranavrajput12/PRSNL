# AI Infrastructure Guide - PRSNL v4.2.0

## Overview

PRSNL's AI infrastructure has been significantly enhanced with:
- **Guardrails-AI** for automatic output validation
- **whisper.cpp** for high-accuracy offline transcription
- **Unified AI Service** for consistent AI interactions

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Frontend Requests                   │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│              UnifiedAIService                        │
│  - Content Analysis                                  │
│  - Summary Generation                                │
│  - Tag Generation                                    │
│  - Embedding Creation                                │
└────────────────┬───────────────┬────────────────────┘
                 │               │
        ┌────────▼─────┐   ┌─────▼──────────────┐
        │ Azure OpenAI │   │ AIValidationService │
        │   GPT-4      │   │  (Guardrails-AI)   │
        └──────────────┘   └────────────────────┘
                                      │
                           ┌──────────▼──────────┐
                           │ Validated Output    │
                           │ - Type Safe         │
                           │ - Schema Compliant  │
                           │ - Error Handled    │
                           └─────────────────────┘
```

## AI Services

### 1. UnifiedAIService
Central hub for all AI operations:
- **Location**: `/backend/app/services/unified_ai_service.py`
- **Features**:
  - Content analysis with validation
  - Summary generation (brief/detailed/key points)
  - Smart tag generation
  - Embedding creation
  - Automatic output validation

### 2. AIValidationService
Ensures AI output quality:
- **Location**: `/backend/app/services/ai_validation_service.py`
- **Features**:
  - Pydantic schema validation
  - Guardrails-AI integration
  - Automatic output repair
  - Graceful error handling

### 3. WhisperCppTranscriptionService
High-accuracy offline transcription:
- **Location**: `/backend/app/services/whisper_cpp_transcription.py`
- **Features**:
  - 99 language support
  - 5 model sizes (tiny to large)
  - Word-level timestamps
  - CPU-optimized performance
  - Fully offline operation

## AI Processing Flow

### Content Analysis
```python
# Automatic validation included
analysis = await unified_ai_service.analyze_content(
    content="Your content here",
    enable_key_points=True,
    enable_entities=True
)

# Response is guaranteed to have:
{
    "title": str,              # 5-100 chars
    "summary": str,            # 20-500 chars
    "detailed_summary": str,   # 50-2000 chars
    "category": str,           # From predefined list
    "tags": List[str],         # 1-10 lowercase tags
    "key_points": List[str],   # 3-7 points
    "entities": Dict,          # People, orgs, tech, concepts
    "sentiment": str,          # positive/neutral/negative/mixed
    "difficulty_level": str,   # beginner/intermediate/advanced
    "reading_time": int        # 1-120 minutes
}
```

### Transcription
```python
# Using whisper.cpp for all transcription
from app.services.whisper_cpp_transcription import whisper_cpp_service

result = await whisper_cpp_service.transcribe_audio(
    audio_path="path/to/audio.mp3",
    model_name="base",  # tiny/base/small/medium/large
    language="en",
    word_timestamps=True
)

# Response includes:
{
    "text": str,
    "confidence": float,
    "word_count": int,
    "duration": float,
    "words": List[Dict],  # With timestamps
    "service": "whisper.cpp"
}
```

## Validation Rules

### Content Analysis Validation
| Field | Rules | Default if Invalid |
|-------|-------|-------------------|
| title | 5-100 chars, no generic suffixes | "Untitled Content" |
| summary | 20-500 chars | "Content analysis unavailable" |
| tags | 1-10 items, lowercase, alphanumeric | ["general"] |
| category | Must be from enum | "other" |
| key_points | 3-7 items, min 10 chars each | ["Content captured", "Analysis pending", "Review required"] |
| sentiment | positive/neutral/negative/mixed | "neutral" |
| reading_time | 1-120 minutes | 5 |

### Tag Generation Rules
- Automatically converted to lowercase
- Duplicates removed
- Whitespace stripped
- Maximum 10 tags enforced
- Empty tags filtered
- Only alphanumeric + hyphens allowed

## Configuration

### Environment Variables
```bash
# Azure OpenAI (Required for AI features)
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01

# AI Validation (Optional)
AI_VALIDATION_ENABLED=true  # Default: true
AI_VALIDATION_LEVEL=medium  # strict/medium/lenient
AI_VALIDATION_LOGGING=true  # Default: true

# Transcription Models (Auto-downloaded)
WHISPER_CPP_MODEL_DIR=storage/whisper_models  # Default
WHISPER_CPP_DEFAULT_MODEL=base  # tiny/base/small/medium/large
```

## Model Selection Guide

### whisper.cpp Models
| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny | 39MB | Fastest | Good | Quick drafts, real-time |
| base | 74MB | Fast | Better | **Default - Recommended** |
| small | 244MB | Moderate | Great | High quality content |
| medium | 769MB | Slower | Excellent | Professional use |
| large | 1550MB | Slowest | Best | Maximum accuracy |

### Automatic Model Selection
The system automatically selects models based on:
- File size: Larger files use better models
- Available resources: CPU/memory constraints
- Use case: Real-time vs batch processing

## Error Handling

### AI Output Validation Failures
When AI outputs fail validation:
1. System logs the validation error
2. Attempts to repair the output
3. Falls back to safe defaults
4. Never breaks user experience

### Transcription Failures
When transcription fails:
1. Logs detailed error information
2. Returns None (handled gracefully by UI)
3. No partial/corrupted data returned

## Performance Considerations

### AI Processing
- Validation adds ~50ms overhead
- Caching implemented for repeated requests
- Async processing for non-blocking operations

### Transcription
- Model loading: First use ~2-5 seconds
- Processing: Real-time factor < 1 for most content
- Memory: Models cached after first load

## Testing AI Features

### Test Scripts
```bash
# Test AI validation
cd backend
python scripts/test_guardrails_validation.py

# Test transcription
python scripts/test_whisper_cpp_integration.py

# Run comprehensive API tests
python scripts/test_ai_integrations.py
```

### Manual Testing
1. **Content Analysis**: POST to `/api/ai/analyze`
2. **Tag Generation**: POST to `/api/ai/tags`
3. **Transcription**: Upload audio/video through UI

## Monitoring

### Key Metrics
- AI response times
- Validation success rates
- Transcription accuracy scores
- Model usage distribution
- Error rates by service

### Logging
All AI operations are logged with:
- Request/response pairs
- Validation results
- Performance metrics
- Error details

## Best Practices

### 1. Always Use UnifiedAIService
```python
# Good
from app.services.unified_ai_service import unified_ai_service
result = await unified_ai_service.analyze_content(content)

# Avoid direct OpenAI calls
```

### 2. Handle Validation Gracefully
```python
# AI outputs are pre-validated
analysis = await unified_ai_service.analyze_content(content)
# Safe to use analysis.get("tags") - guaranteed to be valid
```

### 3. Choose Appropriate Models
```python
# For real-time transcription
result = await whisper_cpp_service.transcribe_audio(
    audio_path=path,
    model_name="tiny"  # Fast
)

# For accuracy-critical content
result = await whisper_cpp_service.transcribe_audio(
    audio_path=path,
    model_name="small"  # Accurate
)
```

## Troubleshooting

### Common Issues

1. **"Guardrails-AI not installed"**
   ```bash
   pip install guardrails-ai>=0.4.0
   ```

2. **"whisper.cpp model not found"**
   - Models download automatically on first use
   - Check internet connection
   - Verify disk space (39MB-1.5GB per model)

3. **"AI validation always failing"**
   - Check Azure OpenAI response format
   - Verify JSON mode is enabled
   - Review validation rules

4. **"Transcription too slow"**
   - Use smaller models (tiny/base)
   - Check CPU usage
   - Consider batch processing

## Future Enhancements

### Planned Improvements
1. **Multi-language support** for AI analysis
2. **Custom validation rules** per content type
3. **Speaker diarization** for transcription
4. **Real-time streaming** transcription
5. **Quality scoring** for AI outputs

---

This infrastructure ensures PRSNL's AI features are:
- ✅ Reliable and consistent
- ✅ Privacy-preserving with offline options
- ✅ High-quality with validation
- ✅ Performant and scalable