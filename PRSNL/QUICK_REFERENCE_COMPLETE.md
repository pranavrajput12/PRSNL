# 🚀 PRSNL Complete Quick Reference & Troubleshooting Guide - Phase 3

## 🎯 System Status - Mac Mini M4 Setup (2025-07-22)
- 🎤 **Voice Integration**: ✅ COMPLETED - Chatterbox TTS with emotions, Enhanced Whisper STT
- 🚨 **Mac Mini M4 Migration**: Services running but auth configuration incomplete
- ✅ **Hardware**: Mac Mini M4 (Apple Silicon) with Colima Docker runtime
- ✅ **PHASE 3 COMPLETE**: AI-powered system with intelligent features
- ✅ **LibreChat Integration**: OpenAI-compatible chat with knowledge base context
- ✅ **Azure OpenAI Dual-Model**: prsnl-gpt-4 (complex) + gpt-4.1-mini (fast)
- ✅ **Performance Infrastructure**: uvloop (2-4x boost), DragonflyDB (25x Redis)
- ✅ **AI Testing**: Verified 2-5s AI-powered responses
- ✅ **LibreChat Testing**: Verified 4.0-5.5s chat responses with streaming
- ✅ **Function Calling**: Azure OpenAI tools API working with 2023-12-01-preview
- ✅ **ARM64 PostgreSQL 16**: Port 5432 (changed from 5432!) optimized for Apple Silicon
- ✅ **Frontend Development**: Working on port 3004 (upgraded from 3003)
- ✅ **Frontend Container**: Working on port 3003 (production only)
- ✅ **Backend + AI**: Working locally on port 8000 (not Docker)
- ✅ **Chrome Extension**: Fixed and functional with GitHub auto-detection
- ✅ **CI/CD**: GitHub Actions pipeline fully operational
- ⚠️ **Auth Services**: Keycloak (8080) + FusionAuth (9011) running but need config
- 📱 **iOS App**: PRSNL APP - *separate codebase, pending integration*

---

## ⚡ Quick Start Commands

### Start All Services - Mac Mini M4 with Colima
```bash
# Start Colima (Docker runtime)
colima start

# Start ARM64 PostgreSQL 16 (port 5432 - changed!)
brew services start postgresql@16
# OR manually:
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 start

# Start DragonflyDB cache and Auth services
docker-compose up -d redis
docker-compose -f docker-compose.auth.yml up -d

# Start Backend + AI Services (Terminal 1)
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Frontend (Terminal 2)
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend && npm run dev -- --port 3004
```

### Essential URLs - Phase 3
- **Frontend Development**: http://localhost:3004
- **Frontend Container**: http://localhost:3003 (production)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **🤖 AI API**: http://localhost:8000/api/ai/
- **💬 LibreChat API**: http://localhost:8000/api/ai/

### Essential URLs - Mac Mini M4 Setup
- **Frontend Development**: http://localhost:3004
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Keycloak Admin**: http://localhost:8080 (admin/admin123)
- **FusionAuth Admin**: http://localhost:9011 (needs setup)
- **🤖 AI API**: http://localhost:8000/api/ai/
- **💬 LibreChat API**: http://localhost:8000/api/ai/

---

## 🔧 Mac Mini M4 Quick Setup Commands

### Initial Setup (One Time)
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL 16
brew install postgresql@16
brew services start postgresql@16

# Create database
createdb prsnl

# Install Colima (Docker alternative)
brew install colima docker docker-compose
colima start
```

### Storage Cleanup Commands
```bash
# Clean npm cache
npm cache clean --force

# Clean Puppeteer cache
rm -rf ~/Library/Caches/Puppeteer

# Clean old IDE caches
rm -rf ~/Library/Application\ Support/Cursor
rm -rf ~/Library/Application\ Support/Trae

# Clean Xcode iOS Device Support (if not needed)
rm -rf ~/Library/Developer/Xcode/iOS\ DeviceSupport/*
```

---

## 🎤 Voice Testing Commands

```bash
# Test TTS with emotion
curl -X POST http://localhost:8000/api/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello! I'm excited to help you today.", "emotion": "excited"}' \
  -o test_output.mp3

# Test voice transcription
curl -X POST http://localhost:8000/api/voice/transcribe \
  -F "audio=@test_audio.wav"

# Get voice models
curl http://localhost:8000/api/voice/models

# Update voice settings
curl -X PUT http://localhost:8000/api/user/settings \
  -H "Content-Type: application/json" \
  -d '{
    "voice_settings": {
      "tts_model": "chatterbox",
      "emotion": "friendly",
      "speed": 1.0,
      "pitch": 0
    }
  }'

# Get current voice settings
curl http://localhost:8000/api/user/settings | jq .voice_settings

# Test different emotions
for emotion in neutral happy sad angry excited calm friendly; do
  echo "Testing emotion: $emotion"
  curl -X POST http://localhost:8000/api/voice/tts \
    -H "Content-Type: application/json" \
    -d "{\"text\": \"This is a test of the $emotion emotion.\", \"emotion\": \"$emotion\"}" \
    -o "test_${emotion}.mp3"
done
```

## 🤖 Phase 3 AI Commands

### AI Services
```bash
# Check AI service status
curl http://localhost:8000/api/ai/health

# Test AI-powered suggestions
curl -X POST http://localhost:8000/api/ai-suggest \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a learning path for FastAPI", "context": {"knowledge": ["Python basics"]}}'

# Test content summarization
curl -X POST http://localhost:8000/api/summarization/summarize/batch \
  -H "Content-Type: application/json" \
  -d '{"item_ids": ["123e4567-e89b-12d3-a456-426614174000"]}'

# Get available models
curl http://localhost:8000/api/ai/models

# AI health check
curl http://localhost:8000/api/ai/health
```

### LibreChat OpenAI-Compatible API
```bash
# Chat completion with knowledge base context
curl -X POST http://localhost:8000/api/ai/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-PRSNL-Integration: test-client" \
  -d '{
    "model": "prsnl-gpt-4",
    "messages": [{"role": "user", "content": "How does PRSNL work as a second brain?"}],
    "temperature": 0.7,
    "max_tokens": 150
  }'

# Streaming chat completion
curl -X POST http://localhost:8000/api/ai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "prsnl-gpt-4", 
    "messages": [{"role": "user", "content": "Explain AI benefits"}],
    "stream": true
  }'

# List available models
curl http://localhost:8000/api/ai/models

# LibreChat health check
curl http://localhost:8000/api/ai/health
```

### Conversation Intelligence - Multi-Agent Analysis
```bash
# Process conversation intelligence with specialized AI agents
curl -X POST http://localhost:8000/api/conversations/intelligence/550e8400-e29b-41d4-a716-446655440000/process \
  -H "Content-Type: application/json"

# Get conversation intelligence results
curl http://localhost:8000/api/conversations/intelligence/550e8400-e29b-41d4-a716-446655440000

# Process batch intelligence for multiple conversations
curl -X POST http://localhost:8000/api/conversations/intelligence/batch/process \
  -H "Content-Type: application/json"

# Filter batch processing by platform
curl -X POST "http://localhost:8000/api/conversations/intelligence/batch/process?platform=chatgpt" \
  -H "Content-Type: application/json"
```

### 🔐 Authentication System - NEW (2025-07-16)
```bash
# Register new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "name": "John Doe"
  }'

# Login with email/password
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'

# Refresh access token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'

# Send magic link (passwordless login)
curl -X POST http://localhost:8000/api/auth/send-magic-link \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Verify email with token
curl -X POST http://localhost:8000/api/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "verification_token_from_email"}'

# Get current user profile (requires auth)
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Update user profile
curl -X PUT http://localhost:8000/api/auth/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Doe"}'

# Resend verification email
curl -X POST http://localhost:8000/api/auth/resend-verification \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Job Persistence System - NEW (2025-07-13)
```bash
# Check job persistence service health
curl http://localhost:8000/api/persistence/health

# Get job status
curl http://localhost:8000/api/persistence/status/media_image_20250713_abc123

# List all jobs with filtering
curl "http://localhost:8000/api/persistence/jobs?job_type=media_image&status=completed&limit=10"

# Update job progress
curl -X PUT "http://localhost:8000/api/persistence/update?job_id=test_job&status=processing&progress=50&stage=analysis&message=Processing%20image"

# Save job results
curl -X POST http://localhost:8000/api/persistence/save \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test_job_123",
    "result_data": {"ocr_text": "Sample text", "confidence": 0.95},
    "status": "completed"
  }'

# Create new job
curl -X POST http://localhost:8000/api/persistence/create \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "media_image",
    "input_data": {"file_path": "/uploads/test.jpg"},
    "tags": ["media", "test"]
  }'
```

### Azure OpenAI Testing
```bash
# Test prsnl-gpt-4 (complex reasoning)
curl -X POST http://localhost:8000/api/ai-suggest \
  -H "Content-Type: application/json" \
  -d '{"goal": "Test complex reasoning", "current_knowledge": ["basics"]}'

# Test gpt-4.1-mini (fast responses for LibreChat)  
curl -X POST http://localhost:8000/api/ai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "prsnl-gpt-4", "messages": [{"role": "user", "content": "Quick test"}]}'
```

---

## 🏗️ Infrastructure Commands

### DragonflyDB Cache (Replaced Redis)
```bash
# Start DragonflyDB container
docker-compose up -d redis  # Still named 'redis' in compose for compatibility

# Check DragonflyDB status
docker ps | grep dragonfly

# Connect to DragonflyDB CLI
docker exec -it prsnl_redis redis-cli

# Monitor cache operations
docker logs prsnl_redis -f
```

### Rate Limiting (slowapi only)
```python
# All rate limiting now uses slowapi decorators
from app.middleware.rate_limit import capture_limiter, search_limiter

@router.post("/capture")
@capture_limiter  # 10 requests per minute
async def capture_item():
    pass
```

### HTTP Client (httpx standardized)
```python
# All HTTP requests now use httpx
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
    data = response.json()
```

---

## 📋 Task Management Commands

### Start a New Task
```bash
# Just describe what you want built:
@TASK_INITIATION_GUIDE.md Build [FEATURE_DESCRIPTION]

# Examples:
@TASK_INITIATION_GUIDE.md Build a user authentication system
@TASK_INITIATION_GUIDE.md Build a video upload feature
@TASK_INITIATION_GUIDE.md Fix the search returning empty results
```

### Complete a Task
```bash
# When you're done with any task:
@TASK_COMPLETION_GUIDE.md Update all documentation
```

### Resume After Session Interruption
```bash
# If session was interrupted:
@CURRENT_SESSION_STATE.md Resume my last session
```

### Check Task Dependencies
```bash
# Reference the impact matrix for documentation updates
@DOCUMENTATION_DEPENDENCIES.md What files need updating for [TASK_TYPE] changes?

# Example:
@DOCUMENTATION_DEPENDENCIES.md What files need updating for Backend API changes?
```

### Task Status Commands
```bash
# Check active tasks
grep -A 2 "IN PROGRESS" TASK_HISTORY.md

# Check completed tasks today
grep -A 2 "$(date +%Y-%m-%d)" TASK_HISTORY.md

# Check file locks
grep "LOCKED" TASK_HISTORY.md

# Check port availability
lsof -i :3003,8000,5432
```

### Pre-Task Verification
```bash
#!/bin/bash
# Pre-task verification script
echo "=== PRE-TASK VERIFICATION ==="
echo "1. Check active tasks:"
grep -A 2 "IN PROGRESS" TASK_HISTORY.md

echo "2. Check port availability:"
lsof -i :3003,8000,5432

echo "3. Check service health:"
curl -s http://localhost:8000/health | jq .status
curl -s -o /dev/null -w "%{http_code}" http://localhost:3004/

echo "4. Check file locks:"
grep "LOCKED" TASK_HISTORY.md

echo "=== READY TO START TASK ==="
```

---

## 🔧 Common Operations

### Test System Health
```bash
# Check all services
curl http://localhost:8000/health      # Backend
curl http://localhost:3004/           # Frontend
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "SELECT version();"  # Database
```

### Test Content Ingest
```bash
# Ingest a YouTube video
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "tags": ["test"]}'

# Ingest an article
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "tags": ["article", "test"]}'
```

### Check Database Content
```bash
# View all items by type
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "
SELECT type, COUNT(*) as count FROM items GROUP BY type ORDER BY count DESC;"

# View recent items
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "
SELECT id, title, type, created_at FROM items ORDER BY created_at DESC LIMIT 10;"

# View video metadata
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "
SELECT id, title, metadata->'video_metadata'->'platform' as platform, duration
FROM items WHERE type = 'video' LIMIT 5;"
```

### Test API Endpoints
```bash
# Get timeline
curl "http://localhost:8000/api/timeline?limit=5" | jq

# Get video stream URL
curl "http://localhost:8000/api/videos/{video_id}/stream-url" | jq

# Get item details
curl "http://localhost:8000/api/items/{item_id}" | jq

# Test AI suggestions
curl -X POST "http://localhost:8000/api/ai-suggest" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' | jq
```

### 🧪 Comprehensive Capture System Testing

**Complete test matrix covering all content types and AI settings:**

```bash
# Test 1: URL with auto content type + AI ON
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "content_type": "auto", "enable_summarization": true, "tags": ["test"]}'

# Test 2: URL with link content type + AI OFF  
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "content_type": "link", "enable_summarization": false, "tags": ["github"]}'

# Test 3: Text content with note type + AI ON
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"content": "This is a test note with important information.", "content_type": "note", "enable_summarization": true, "tags": ["note"]}'

# Test 4: Highlight text with article type + AI OFF
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"highlight": "Artificial intelligence is transforming industries.", "content_type": "article", "enable_summarization": false, "tags": ["ai"]}'

# Test 5: File upload with document processing + AI ON
curl -X POST "http://localhost:8000/api/file/upload" \
  -F "files=@/tmp/final_test_doc.txt" \
  -F "content_type=document" \
  -F "enable_summarization=true" \
  -F "tags=[\"document\", \"test\"]"

# Test 6: YouTube video with auto detection + AI ON
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "content_type": "auto", "enable_summarization": true, "tags": ["video", "youtube"]}'
```

### 📁 File Upload API Testing

```bash
# Check file processing status
curl "http://localhost:8000/api/file/status/{file_id}" | jq

# Get file content and metadata
curl "http://localhost:8000/api/file/content/{file_id}" | jq

# Get file storage statistics
curl "http://localhost:8000/api/file/stats" | jq

# Delete a file and associated item
curl -X DELETE "http://localhost:8000/api/file/{file_id}" | jq
```

### ✅ Expected Success Indicators

**All tests should return:**
- Status 201 (Created) for successful captures
- Valid UUID for item_id and file_id
- Proper item_type detection (article, video, document, note)
- Processing status (completed for simple content, processing for AI-enabled)

**Database verification:**
```bash
# Check all captured items
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "
SELECT id, title, content_type, enable_summarization, status, type, has_files 
FROM items ORDER BY created_at DESC LIMIT 10;"

# Check file processing
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "
SELECT f.id, f.original_filename, f.processing_status, i.title 
FROM files f JOIN items i ON f.item_id = i.id ORDER BY f.created_at DESC;"
```

---

## 🚨 Troubleshooting Guide

### 🔴 Critical Issues & Solutions

#### Services Not Starting
```bash
# Check what's using ports
lsof -i :8000  # Backend
lsof -i :3003  # Frontend
lsof -i :5432  # PostgreSQL

# Kill processes if needed
kill -9 $(lsof -ti :8000)

# Check PostgreSQL status
pg_ctl status -D /opt/homebrew/var/postgresql@16
```

#### Database Connection Issues
```bash
# Test database connection
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "SELECT NOW();"

# Check if database exists
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/postgres" -c "\l"

# Create database if missing
createdb -h 127.0.0.1 -p 5432 -U prsnl prsnl

# Check pgvector extension
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

#### Frontend API Connection Issues
**Symptom**: ERR_CONNECTION_REFUSED on localhost:3004 (development) or localhost:3003 (container)
**Fix**:
```bash
# Ensure frontend is running
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend
npm run dev

# Check if port 3003 is occupied
lsof -i :3003
```

#### Backend API Errors
**Symptom**: 500 Internal Server Error
**Fix**:
```bash
# Check backend logs
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Test specific endpoint
curl -v http://localhost:8000/health
```

### 🎨 Frontend Issues

#### Empty Search Results
**Symptom**: Search returns 200 OK but no results shown
**Root Cause**: Frontend expects `data.results` but API returns `data.items`
**Fix**: Update frontend to use correct field name
```typescript
// In search components
results = data.items || [];  // NOT data.results
```

#### Video Player Not Working
**Symptom**: Videos not loading or playing
**Check**:
```bash
# Verify video data in database
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "
SELECT id, title, thumbnail_url, 
       metadata->'video_metadata'->'platform' as platform,
       metadata->'video_metadata'->'embed_url' as embed_url
FROM items WHERE type = 'video' AND id = 'YOUR_VIDEO_ID';"
```

#### Component Import Errors
**Common missing variables**:
```svelte
<script lang="ts">
  // Add these if missing
  let loading = false;
  let error: string | null = null;
  let items: any[] = [];
  
  // For video components
  let videoQuality: 'standard' | 'high' = 'standard';
  
  // For search components
  let query = '';
  let results: any[] = [];
</script>
```

### 🔧 Backend Issues

#### Import Errors
**Error**: `ImportError: cannot import name 'service_name'`
**Fix**: Add singleton instantiation at end of service file
```python
# At the end of service files
service_name = ServiceClass()
```

#### API Route 404 Errors
**Check**:
```python
# In main.py - ensure router is included
app.include_router(router_name, prefix="/api")

# In route file - check decorator
@router.post("/endpoint")  # This becomes /api/endpoint
```

#### Database Schema Issues
**Error**: "column does not exist"
**Fix**: Add missing columns
```sql
-- Common missing columns
ALTER TABLE items ADD COLUMN IF NOT EXISTS platform VARCHAR(50);
ALTER TABLE items ADD COLUMN IF NOT EXISTS duration INTEGER;
ALTER TABLE items ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;
```

#### Web Scraping "Untitled" Errors
**Symptom**: AI suggestions return "Untitled" instead of content
**Status**: ✅ FIXED (2025-07-09)
**Fix Applied**: Removed HTTP compression headers, focus on meta-tag extraction only

### 💾 Database Issues

#### Missing Tables
```sql
-- Check if tables exist
\dt

-- Recreate items table if missing
CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500),
    url TEXT,
    type VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    thumbnail_url TEXT,
    duration INTEGER
);
```

#### Empty Timeline
**Common Causes**:
1. Items have status 'failed' instead of 'completed'
2. No items in database
3. API filtering too restrictive

**Fix**:
```sql
-- Check item statuses
SELECT status, COUNT(*) FROM items GROUP BY status;

-- Update failed items
UPDATE items SET status = 'completed' WHERE status = 'failed';

-- Check recent items
SELECT id, title, type, created_at FROM items ORDER BY created_at DESC LIMIT 5;
```

### 🤖 AI Service Issues

#### Azure OpenAI Connection Errors
**Error**: "Connection error" or "API key not found"
**Fix**: Ensure environment variables are set in backend/.env
```bash
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

#### Embeddings Service Failures
**Fix**: Make embeddings optional (already implemented)
```python
try:
    embeddings = await embedding_service.generate(content)
except Exception as e:
    logger.warning(f"Embeddings generation failed: {e}")
    embeddings = None  # Continue without embeddings
```

---

## 📁 Important File Locations

### 🗂️ Documentation (Post-Consolidation)
- **Main Status**: `/PRSNL/PROJECT_STATUS.md`
- **AI Coordination**: `/PRSNL/AI_COORDINATION_COMPLETE.md`
- **Task Tracking**: `/PRSNL/TASK_HISTORY.md`
- **Quick Reference**: `/PRSNL/QUICK_REFERENCE_COMPLETE.md` (this file)
- **Architecture**: `/PRSNL/ARCHITECTURE.md`
- **API Documentation**: `/PRSNL/API_DOCUMENTATION.md`

### 🔧 Backend Files
- **Main API**: `/backend/app/main.py`
- **Video Capture**: `/backend/app/api/capture.py`
- **Video Endpoints**: `/backend/app/api/videos.py`
- **Timeline API**: `/backend/app/api/timeline.py`
- **Items API**: `/backend/app/api/items.py`
- **Web Scraper**: `/backend/app/services/scraper.py`
- **AI Suggestions**: `/backend/app/api/ai_suggest.py`

### 🎨 Frontend Files
- **Video Player**: `/frontend/src/lib/components/StreamingVideoPlayer.svelte`
- **Video Library**: `/frontend/src/routes/videos/+page.svelte`
- **Individual Video**: `/frontend/src/routes/videos/[id]/+page.svelte`
- **API Client**: `/frontend/src/lib/api.ts`
- **Search Page**: `/frontend/src/routes/search/+page.svelte`
- **Timeline**: `/frontend/src/routes/timeline/+page.svelte`

---

## 🏗️ System Architecture

### Database Configuration
```bash
Database: prsnl
User: prsnl
Password: prsnl123
Host: 127.0.0.1
Port: 5432
Connection: postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl
```

### Video Metadata Structure
```json
{
  "video_metadata": {
    "platform": "youtube",
    "embed_url": "https://www.youtube.com/embed/...",
    "streaming_url": "https://www.youtube.com/watch?v=...",
    "downloaded": false,
    "video_info": {
      "title": "...",
      "duration": 123,
      "thumbnail": "https://...",
      "platform": "youtube"
    },
    "ai_analysis": {
      "summary": "...",
      "tags": [...],
      "key_points": [...]
    }
  }
}
```

### Environment Info
- **Architecture**: ARM64 (Apple Silicon)
- **Python**: 3.11+
- **Node.js**: 18+
- **PostgreSQL**: 16 (compiled for ARM64)
- **pgvector**: Compiled from source
- **AI Service**: Azure OpenAI (no Ollama)
- **iOS App**: PRSNL APP - separate Swift codebase

---

## 📊 Current System Statistics

### Content Statistics
- **Total Items**: ~30
- **Videos**: 7 functional video items
- **Bookmarks**: 17 imported bookmarks
- **Articles**: 6 processed articles (with meta-tag extraction)

### Functional Features
- ✅ **Video Streaming**: YouTube embed streaming
- ✅ **Video Download**: On-demand download for offline viewing
- ✅ **Web Scraping**: Meta-tag based content extraction
- ✅ **AI Suggestions**: Proper content analysis (no more "Untitled")
- ✅ **Search**: Keyword and semantic search
- ✅ **Timeline**: Chronological content display
- ✅ **Import**: Bookmark HTML import

### System Health
- **Backend**: Fully operational
- **Frontend**: Responsive and functional
- **Database**: Stable with proper schema
- **AI Services**: Azure OpenAI integrated
- **Documentation**: Streamlined and organized

---

## 🎯 Common Diagnostic Commands

### System Health Check
```bash
# Full system check
echo "=== SYSTEM HEALTH CHECK ==="
echo "1. PostgreSQL:"
pg_ctl status -D /opt/homebrew/var/postgresql@16

echo "2. Backend:"
curl -s http://localhost:8000/health | jq

echo "3. Frontend:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3004/

echo "4. Database Content:"
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "SELECT type, COUNT(*) FROM items GROUP BY type;"

echo "5. Port Usage:"
lsof -i :8000,3003,5432
```

### Content Verification
```bash
# Check recent captures
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "
SELECT id, title, type, url, created_at 
FROM items 
ORDER BY created_at DESC 
LIMIT 10;"

# Check video content specifically
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "
SELECT id, title, duration, thumbnail_url,
       metadata->'video_metadata'->'platform' as platform
FROM items 
WHERE type = 'video';"
```

### Performance Check
```bash
# API response times
time curl -s http://localhost:8000/api/timeline?limit=10 > /dev/null
time curl -s http://localhost:8000/api/search?query=test > /dev/null

# Database performance
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables 
WHERE tablename = 'items';"
```

---

## 🚀 Emergency Recovery

### If Everything Breaks
```bash
# 1. Stop all services
pkill -f uvicorn
pkill -f "npm run dev"

# 2. Restart PostgreSQL
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 restart

# 3. Restart backend
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Restart frontend
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend
npm run dev

# 5. Test everything
curl http://localhost:8000/health
curl http://localhost:3004/
```

### Reset Database (Nuclear Option)
```bash
# CAUTION: This will delete all data
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/postgres" -c "DROP DATABASE IF EXISTS prsnl;"
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/postgres" -c "CREATE DATABASE prsnl;"
psql "postgresql://prsnl:prsnl123@127.0.0.1:5432/prsnl" -c "CREATE EXTENSION vector;"

# Then restart backend to recreate tables
```

---

## 📞 When All Else Fails

### Debug Steps
1. **Check logs**: Look for error messages in terminal output
2. **Browser DevTools**: Check Network tab for failed requests
3. **Database query**: Verify data exists and is correct format
4. **API test**: Use curl to test endpoints directly
5. **Port conflicts**: Ensure no other services using same ports
6. **Environment**: Verify all environment variables are set
7. **Restart**: Try restarting services in correct order

### Common Fixes
- **Clear browser cache**: Hard refresh (Cmd+Shift+R)
- **Restart services**: Kill and restart in correct order
- **Check file permissions**: Ensure all files are readable
- **Verify network**: Test on different browser/device
- **Check firewall**: Ensure ports aren't blocked

---

**Last Updated**: 2025-07-09  
**System Version**: PRSNL v3.0  
**Documentation Status**: Consolidated and Complete

This guide consolidates all troubleshooting knowledge and serves as the single source of truth for system management and problem resolution.