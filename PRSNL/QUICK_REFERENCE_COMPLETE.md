# 🚀 PRSNL Complete Quick Reference & Troubleshooting Guide

## 🎯 System Status (2025-07-09)
- ✅ **Video Streaming**: Fully functional
- ✅ **Frontend**: Working on port 3002
- ✅ **Backend**: Working on port 8000
- ✅ **Database**: PostgreSQL 16 on port 5433
- ✅ **Web Scraping**: Fixed meta-tag extraction
- ✅ **AI Integration**: Azure OpenAI working
- ✅ **Documentation**: Consolidated (48 → 13 files)
- 📱 **iOS App**: PRSNL APP - *separate codebase, pending integration*

---

## ⚡ Quick Start Commands

### Start All Services
```bash
# Start PostgreSQL
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 start

# Start Backend (Terminal 1)
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Frontend (Terminal 2)
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend && npm run dev
```

### Essential URLs
- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

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
lsof -i :3002,8000,5433
```

### Pre-Task Verification
```bash
#!/bin/bash
# Pre-task verification script
echo "=== PRE-TASK VERIFICATION ==="
echo "1. Check active tasks:"
grep -A 2 "IN PROGRESS" TASK_HISTORY.md

echo "2. Check port availability:"
lsof -i :3002,8000,5433

echo "3. Check service health:"
curl -s http://localhost:8000/health | jq .status
curl -s -o /dev/null -w "%{http_code}" http://localhost:3002/

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
curl http://localhost:3002/           # Frontend
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "SELECT version();"  # Database
```

### Test Content Capture
```bash
# Capture a YouTube video
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "tags": ["test"]}'

# Capture an article
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "tags": ["article", "test"]}'
```

### Check Database Content
```bash
# View all items by type
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "
SELECT type, COUNT(*) as count FROM items GROUP BY type ORDER BY count DESC;"

# View recent items
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "
SELECT id, title, type, created_at FROM items ORDER BY created_at DESC LIMIT 10;"

# View video metadata
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "
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

---

## 🚨 Troubleshooting Guide

### 🔴 Critical Issues & Solutions

#### Services Not Starting
```bash
# Check what's using ports
lsof -i :8000  # Backend
lsof -i :3002  # Frontend
lsof -i :5433  # PostgreSQL

# Kill processes if needed
kill -9 $(lsof -ti :8000)

# Check PostgreSQL status
pg_ctl status -D /opt/homebrew/var/postgresql@16
```

#### Database Connection Issues
```bash
# Test database connection
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "SELECT NOW();"

# Check if database exists
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/postgres" -c "\l"

# Create database if missing
createdb -h 127.0.0.1 -p 5433 -U prsnl prsnl

# Check pgvector extension
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

#### Frontend API Connection Issues
**Symptom**: ERR_CONNECTION_REFUSED on localhost:3002
**Fix**:
```bash
# Ensure frontend is running
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend
npm run dev

# Check if port 3002 is occupied
lsof -i :3002
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
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "
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
Port: 5433
Connection: postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl
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
curl -s -o /dev/null -w "%{http_code}" http://localhost:3002/

echo "4. Database Content:"
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "SELECT type, COUNT(*) FROM items GROUP BY type;"

echo "5. Port Usage:"
lsof -i :8000,3002,5433
```

### Content Verification
```bash
# Check recent captures
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "
SELECT id, title, type, url, created_at 
FROM items 
ORDER BY created_at DESC 
LIMIT 10;"

# Check video content specifically
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "
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
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "
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
curl http://localhost:3002/
```

### Reset Database (Nuclear Option)
```bash
# CAUTION: This will delete all data
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/postgres" -c "DROP DATABASE IF EXISTS prsnl;"
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/postgres" -c "CREATE DATABASE prsnl;"
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "CREATE EXTENSION vector;"

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