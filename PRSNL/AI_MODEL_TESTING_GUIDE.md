# AI Model Testing Guide - PRSNL v2.0

This guide explains how to test and verify the Azure OpenAI model integrations in PRSNL.

## Prerequisites

1. Backend running: `cd PRSNL && docker-compose up -d`
2. Frontend running: `cd PRSNL/frontend && npm run dev`
3. Azure OpenAI models configured in `.env`:
   - `AZURE_OPENAI_DEPLOYMENT=gpt-4.1`
   - `AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002`
   - `AZURE_OPENAI_WHISPER_DEPLOYMENT=whisper`

## Test Scripts

### 1. Quick Model Test
**Purpose**: Quickly verify each model is working

```bash
# Test all models
python quick_model_test.py all

# Test specific model
python quick_model_test.py whisper
python quick_model_test.py vision
python quick_model_test.py embedding
```

**What it tests:**
- **Whisper**: Captures a YouTube video and checks for transcription
- **Vision**: Analyzes a test image and returns tags/description
- **Embedding**: Tests semantic search functionality

### 2. Comprehensive Model Test
**Purpose**: Full test suite with detailed data flow analysis

```bash
python test_azure_models.py
```

**What it tests:**
- All three models with real data
- WebSocket connections
- Frontend API endpoints
- Response times and latency
- Data structure validation

### 3. Real-time Data Flow Monitor
**Purpose**: Monitor live data flow from models to frontend

```bash
python test_model_data_flow.py
```

**Features:**
- Real-time WebSocket monitoring
- Model latency tracking
- Frontend endpoint verification
- Detailed status report

### 4. Live AI Model Monitor
**Purpose**: Interactive dashboard showing model activity

```bash
python monitor_ai_models.py
```

**Features:**
- Live dashboard with model status
- Real-time event tracking
- Automatic test triggering
- WebSocket message monitoring

## Expected Results

### Whisper (Video Transcription)
✅ **Working**: Video transcription appears in item metadata within 10-30 seconds
❌ **Not Working**: No transcription after 30 seconds, check:
- Whisper deployment exists in Azure
- `AZURE_OPENAI_WHISPER_DEPLOYMENT` in `.env`
- Backend logs: `docker logs prsnl_backend -f`

### GPT-4.1 Vision (Image Analysis)
✅ **Working**: Returns tags, description, and extracted text
❌ **Not Working**: Error 400/500, check:
- GPT-4.1 deployment supports vision
- `AZURE_OPENAI_DEPLOYMENT` in `.env`
- Image size and format

### text-embedding-ada-002 (Semantic Search)
✅ **Working**: Semantic search returns relevance scores
❌ **Not Working**: No semantic results, check:
- Embedding model deployed in Azure
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` in `.env`
- Items have embeddings generated

## Debugging Tips

### 1. Check Backend Logs
```bash
# View real-time logs
docker logs prsnl_backend -f

# Search for specific model
docker logs prsnl_backend 2>&1 | grep -i whisper
docker logs prsnl_backend 2>&1 | grep -i vision
docker logs prsnl_backend 2>&1 | grep -i embedding
```

### 2. Verify Model Deployments
```bash
# Check environment variables
docker exec prsnl_backend env | grep AZURE

# Test direct API calls
curl -X POST http://localhost:8000/api/vision/analyze \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "test", "image_path": "test.png"}'
```

### 3. Frontend Console
Open browser developer tools and check:
- Network tab for API calls
- Console for WebSocket messages
- Response data structure

## Common Issues

### Issue: Whisper not transcribing videos
**Solution**: 
1. Verify Whisper deployment name matches `.env`
2. Check if video files are being downloaded
3. Ensure ffmpeg is installed in container

### Issue: Vision analysis returns generic results
**Solution**:
1. Verify GPT-4.1 deployment has vision capabilities
2. Check image encoding is correct
3. Test with different image formats

### Issue: Semantic search not finding relevant results
**Solution**:
1. Wait for embeddings to generate (can take 1-2 minutes)
2. Verify embedding model is deployed
3. Check if items have non-null embedding vectors

## Manual Testing via Frontend

1. **Test Whisper**: 
   - Go to http://localhost:3002/capture
   - Enter a YouTube URL
   - Check video details page for transcription

2. **Test Vision**:
   - Capture an article with images
   - Check if images are extracted and stored
   - Look for image analysis in metadata

3. **Test Embeddings**:
   - Go to http://localhost:3002/search
   - Toggle "Semantic Search"
   - Search for conceptual terms
   - Check relevance scores

## API Endpoints for Testing

```bash
# Whisper (indirectly through video capture)
POST /api/capture
{
  "url": "https://youtube.com/watch?v=VIDEO_ID",
  "title": "Test Video"
}

# Vision
POST /api/vision/analyze
{
  "image_base64": "base64_encoded_image",
  "image_path": "test.jpg"
}

# Embeddings (through search)
GET /api/search?query=test&semantic=true

# WebSocket (for real-time updates)
ws://localhost:8000/ws/chat/{client_id}
```

## Success Criteria

All models are working correctly when:
1. ✅ Videos show transcriptions in metadata
2. ✅ Images return meaningful analysis
3. ✅ Semantic search shows relevance scores
4. ✅ WebSocket delivers real-time updates
5. ✅ Frontend displays all AI-generated content

Run the comprehensive test to verify:
```bash
python test_azure_models.py
```

If all tests pass, your AI integration is working perfectly! 🎉