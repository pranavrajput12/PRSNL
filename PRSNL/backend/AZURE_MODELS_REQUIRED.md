# Azure OpenAI Models Required for PRSNL

## Current Status
- **Available**: gpt-4.1 (deployment name: gpt-4.1)
- **Needed**: text-embedding-ada-002, whisper, gpt-4-vision (optional)

## Features Requiring Additional Models

### 1. Text Embedding Model (text-embedding-ada-002) - CRITICAL
**Required for:**
- ✅ Duplicate detection (semantic similarity) - IMPLEMENTED with fallback
- ✅ Smart categorization (clustering) - IMPLEMENTED with fallback
- ❌ Knowledge graph (relationship discovery) - REQUIRES EMBEDDINGS
- ❌ Second brain (semantic search) - REQUIRES EMBEDDINGS
- ❌ Find similar items feature - REQUIRES EMBEDDINGS
- ❌ Video/content embeddings for search - REQUIRES EMBEDDINGS

**Note**: Knowledge graph and second brain modules are heavily dependent on embeddings for:
- Semantic similarity calculations
- Content relationship discovery
- Neural search capabilities

**Current workaround**: Features will fail or use fallback methods

### 2. Whisper Model - IMPORTANT
**Required for:**
- ❌ Video transcription
- ❌ Audio content processing
- ❌ Voice notes transcription

**Current workaround**: Videos marked as "failed" status

### 3. GPT-4 Vision - OPTIONAL (already have gpt-4.1)
**Required for:**
- ❌ Screenshot analysis
- ❌ Image content extraction
- ❌ Visual content understanding

**Current workaround**: Can use regular GPT-4.1 for text-only processing

## Implementation Notes

### Unified AI Service Configuration
The `unified_ai_service.py` already has placeholder for embedding model:
```python
self.embedding_deployment = "text-embedding-ada-002"  # You may need to deploy this
```

### Features Currently Disabled/Limited
1. **Embeddings**: 
   - `generate_embeddings()` method will fail without text-embedding-ada-002
   - Affects duplicate detection, categorization clustering, semantic search

2. **Video Processing**:
   - `transcription_service.py` needs Whisper model
   - Videos fail to process without transcription

3. **Image Analysis**:
   - `vision_processor.py` could benefit from GPT-4 Vision
   - Currently using regular GPT-4 for alt text

## TODO When Models Are Added

1. **Update .env file** with new deployment names:
   ```
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
   AZURE_OPENAI_WHISPER_DEPLOYMENT=whisper
   AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4-vision
   ```

2. **Update unified_ai_service.py**:
   - Set correct embedding deployment name
   - Add vision model support
   - Add whisper transcription method

3. **Update transcription_service.py**:
   - Use Azure Whisper instead of fallback
   - Enable video transcription

4. **Test affected features**:
   - Duplicate detection with embeddings
   - Video processing with transcription
   - Knowledge graph relationships
   - Second brain semantic search

## Priority Order
1. **text-embedding-ada-002** - Most critical, affects many features
2. **whisper** - Important for video/audio content
3. **gpt-4-vision** - Nice to have, can work without it