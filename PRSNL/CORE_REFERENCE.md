# 🚀 PRSNL Core Reference Guide - Complete System Documentation

This consolidated reference combines essential system information, task management procedures, documentation dependencies, port allocations, session state tracking, and Docker configuration into a single authoritative source.

---

## 🎯 System Status - Mac Mini M4 Setup (2025-07-23)

### Current Environment
- 🎤 **Voice Integration**: ✅ COMPLETED - Chatterbox TTS with emotions, Enhanced Whisper STT, RealtimeSTT streaming
- 🚨 **Mac Mini M4**: ARM64 architecture with native PostgreSQL 16 
- ✅ **Hardware**: Mac Mini M4 (Apple Silicon) with Rancher Desktop Docker runtime
- ✅ **PHASE 3 COMPLETE**: AI-powered system with intelligent features
- ✅ **LibreChat Integration**: OpenAI-compatible chat with knowledge base context
- ✅ **Azure OpenAI Dual-Model**: prsnl-gpt-4 (complex) + gpt-4.1-mini (fast)
- ✅ **Performance Infrastructure**: uvloop (2-4x boost), DragonflyDB (25x Redis)
- ✅ **Authentication System**: All bypasses removed - full production security
- ✅ **ARM64 PostgreSQL 16**: Port 5432 optimized for Apple Silicon
- ✅ **Frontend Development**: Working on port 3004
- ✅ **Backend + AI**: Working locally on port 8000 (not Docker)
- ⚠️ **Auth Services**: Keycloak (8080) + FusionAuth (9011) ready for configuration

### Essential URLs
- **Frontend Development**: http://localhost:3004
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Keycloak Admin**: http://localhost:8080 (admin/admin123)
- **FusionAuth Admin**: http://localhost:9011
- **🤖 AI API**: http://localhost:8000/api/ai/
- **💬 LibreChat API**: http://localhost:8000/api/ai/

---

## ⚡ Quick Start Commands

### Start All Services - Mac Mini M4 with Rancher Desktop
```bash
# Start Rancher Desktop (Docker runtime)
# Open Rancher Desktop app from Applications

# Start ARM64 PostgreSQL 16 (port 5432)
brew services start postgresql@16
# OR manually:
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 start

# Start DragonflyDB cache
docker-compose up -d redis

# Start Backend + AI Services (Terminal 1)
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Frontend (Terminal 2)
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend && npm run dev -- --port 3004
```

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
psql "postgresql://pronav@localhost:5432/prsnl" -c "SELECT type, COUNT(*) FROM items GROUP BY type;"

echo "5. Port Usage:"
lsof -i :8000,3004,5432
```

---

## 📋 Task Management System

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
@CURRENT_SESSION_STATE.md Resume my last session
```

### Task Dependency Workflow

#### 1. Task Registration (REQUIRED)
```markdown
# Add to TASK_HISTORY.md:
### Task [AI]-2025-MM-DD-###: [Task Name]
**Status**: IN PROGRESS
**Started**: [timestamp]
**Assigned**: [AI Name]
**Type**: [Frontend/Backend/Database/AI Service/Documentation]
**Dependencies**: [List any dependent tasks or files]
**Impact**: [Which files will be modified/updated]
**Estimated Time**: [time estimate]

# Update CURRENT_SESSION_STATE.md:
**Status**: ACTIVE
**Active Task**: [TASK_ID]
**Task Type**: [TYPE]
**Assigned AI**: [AI Name]
**Started**: [timestamp]
**Files Being Modified**: [List files that will be changed]
**Progress**: Started task initiation
```

#### 2. Task Completion (REQUIRED)
```markdown
# Update in TASK_HISTORY.md:
**Status**: COMPLETED
**Completed**: [timestamp]
**Files Modified**: [List all files that were actually changed]
**Notes**: [Brief summary of what was accomplished]

# Update CURRENT_SESSION_STATE.md:
**Status**: IDLE
**Active Task**: None
**Last Completed**: [TASK_ID] at [timestamp]
**Files Modified**: [List all files that were changed]
**Progress**: Task completed successfully
```

---

## 📊 Documentation Dependencies Matrix

### Impact Matrix for Task Types

| Task Type | Always Update | Update When Relevant |
|-----------|---------------|---------------------|
| **Frontend UI** | `TASK_HISTORY.md` | `PROJECT_STATUS.md`, `QUICK_REFERENCE_COMPLETE.md` |
| **Backend API** | `TASK_HISTORY.md`, `API_DOCUMENTATION.md`, `PROJECT_STATUS.md`, `QUICK_REFERENCE_COMPLETE.md` | `AI_COORDINATION_COMPLETE.md` |
| **Database** | `TASK_HISTORY.md`, `DATABASE_SCHEMA.md`, `QUICK_REFERENCE_COMPLETE.md` | `PROJECT_STATUS.md` |
| **AI Service** | `TASK_HISTORY.md`, `AI_COORDINATION_COMPLETE.md`, `PROJECT_STATUS.md`, `QUICK_REFERENCE_COMPLETE.md` | `API_DOCUMENTATION.md` |
| **Documentation** | `TASK_HISTORY.md`, target files | `PROJECT_STATUS.md` |

### Critical Dependency Rules

1. **Always Update TASK_HISTORY.md** - Every single task completion
2. **API Changes → Multiple Files** - API_DOCUMENTATION.md, PROJECT_STATUS.md, QUICK_REFERENCE_COMPLETE.md
3. **Database Changes → Schema + Commands** - DATABASE_SCHEMA.md, QUICK_REFERENCE_COMPLETE.md
4. **AI Changes → Coordination + Status** - AI_COORDINATION_COMPLETE.md, PROJECT_STATUS.md
5. **Major Changes → Project Status** - PROJECT_STATUS.md for significant capabilities

### Pre-Completion Checklist
- [ ] **TASK_HISTORY.md** updated with completion status
- [ ] **Impact matrix** consulted for required file updates
- [ ] **Sanity checks** run for task type
- [ ] **Documentation consistency** verified
- [ ] **Cross-references** checked and updated

---

## 🔧 Port Allocation & Management

### Fixed Development Ports
| Service | Port | Status | Description | Config Location |
|---------|------|--------|-------------|-----------------|
| **Frontend Dev (SvelteKit)** | **3004** | **FIXED** | Main dev UI | `/PRSNL/frontend/vite.config.ts` |
| **Frontend Container** | **3003** | FIXED | Production UI | `/PRSNL/docker-compose.yml` |
| **Backend + AI** | **8000** | FIXED | REST API + AI services | Local process |
| **PostgreSQL ARM64** | **5432** | **CRITICAL** | Primary database | ARM64 PostgreSQL 16 |
| **DragonflyDB** | **6379** | FIXED | Ultra-fast cache | `/PRSNL/docker-compose.yml` |

### Port Conflict Prevention
```bash
# Check if port is in use
lsof -i :PORT

# Kill process using port (use with caution)
kill -9 $(lsof -t -i:PORT)

# Check all Docker port mappings
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

### CORS Configuration
If changing frontend port, update `/PRSNL/backend/app/config.py`:
```python
CORS_ORIGINS = ["http://localhost:3004", "http://localhost:NEW_PORT"]
```

---

## 📊 Current Session State

### Active Session Information
**Status**: COMPLETED  
**Last Updated**: 2025-07-23  
**Active Task**: None  
**Last Completed**: AUTH-STT-2025-07-23-001 - Remove Auth Bypasses & Implement RealtimeSTT  
**Environment**: Mac Mini M4 with PostgreSQL 16 (port 5432), pgvector 0.8.0, Python 3.11, Node v20.18.1  

### Recent Major Completions
1. **Remove Authentication Bypasses**: All development bypasses removed - system production-ready
2. **RealtimeSTT Integration**: Full streaming voice transcription with WebSocket support
3. **Capture System Fixes**: Tag constraints, URL duplication, progress animations resolved

### Running Services Status
- **Frontend**: http://localhost:3004 ✅ (with voice UI)
- **Backend**: http://localhost:8000 ✅ (with voice API)
- **PostgreSQL**: Port 5432 ✅
- **Voice Features**: Fully operational ✅
- **Authentication**: Production-ready ✅

---

## 🐳 Docker Configuration

### Current Docker Setup
- **Database**: Using local PostgreSQL (not Docker) for better performance
- **Connection**: `postgresql://pronav@localhost:5432/prsnl`
- **Services in Docker**: DragonflyDB (caching), optional Ollama (LLM)

### Essential Docker Commands
```bash
# Start DragonflyDB only
docker-compose up -d dragonflydb

# Start all services (excluding database)  
docker-compose up -d

# View logs
docker-compose logs -f redis

# Stop all services
docker-compose down
```

### Database Management
```bash
# Backup local database
pg_dump -U pronav prsnl > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U pronav prsnl < backup_file.sql

# Test connection
psql -U pronav -d prsnl -c "SELECT 1;"
```

---

## 🎤 Enhanced Voice Integration Commands (v8.2)

### Voice Service Health Check
```bash
# Check voice service status and configuration
curl http://localhost:8000/api/voice/health

# Should return: {"status": "healthy", "tts_engine": "piper", "knowledge_base": "integrated"}
```

### Knowledge-Enhanced Voice Testing
```bash
# Test voice with knowledge base integration (primary endpoint)
curl -X POST http://localhost:8000/api/voice/test \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Tell me about the PRSNL voice system features",
    "settings": {
      "gender": "female",
      "ttsEngine": "piper",
      "useCrewAI": true,
      "emotionStrength": 0.8
    }
  }' \
  -o knowledge_voice_response.mp3

# Test with different knowledge queries
curl -X POST http://localhost:8000/api/voice/test \
  -H "Content-Type: application/json" \
  -d '{"text": "How does the voice integration work with the knowledge base?"}' \
  -o knowledge_test.mp3
```

### Voice Testing Interface
```bash
# Access enhanced voice testing page with live transcription
open http://localhost:3004/test-voice

# Features available:
# - Knowledge base query testing
# - Live transcription with animated waveforms
# - Voice settings configuration
# - Real-time WebSocket voice communication
# - Conversation history with speaker labels
```

### WebSocket Voice Communication
```bash
# Connect to voice WebSocket for real-time interaction
# URL: ws://localhost:8000/api/voice/ws

# Example JavaScript WebSocket usage:
# const ws = new WebSocket('ws://localhost:8000/api/voice/ws');
# ws.send(JSON.stringify({type: 'start_recording'}));
# ws.send(audio_blob); // Send audio data
# ws.send(JSON.stringify({type: 'end_recording'}));
```

### TTS System Testing
```bash
# Test Piper TTS (primary engine) - superior quality
curl -X POST http://localhost:8000/api/voice/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Testing Piper TTS quality", "settings": {"ttsEngine": "piper"}}' \
  -o piper_test.mp3

# Test with different speech rates based on mood
curl -X POST http://localhost:8000/api/voice/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Let me explain this slowly", "settings": {"mood": "explaining"}}' \
  -o explaining_voice.mp3
```

### Voice System Features
1. **Knowledge Base Integration**: Voice responses use PRSNL documentation
2. **Piper TTS Primary**: Superior natural voice quality
3. **Multi-Backend TTS**: Automatic fallback (Piper → Chatterbox → Edge-TTS)
4. **Speech Rate Control**: Mood-based speed adjustment (0.75-0.95x)
5. **Live Transcription**: Real-time display with animated waveforms
6. **Cortex Personality**: Mood-based voice responses with emotional intelligence
7. **Cross-Platform**: Works across entire application, not just test pages

### Voice Troubleshooting
```bash
# Check if voice service is running
curl -f http://localhost:8000/api/voice/health || echo "Voice service not responding"

# Test basic voice functionality
curl -X POST http://localhost:8000/api/voice/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Voice test"}' \
  -o voice_test.mp3 && echo "Voice test successful"

# Check WebSocket connectivity
# Open browser console at http://localhost:3004/test-voice
# Look for "WebSocket connected!" message

# Verify knowledge base integration
curl -X POST http://localhost:8000/api/voice/test \
  -H "Content-Type: application/json" \
  -d '{"text": "What is PRSNL?"}' \
  -o knowledge_check.mp3
# Response should include knowledge-based information, not generic response
```

---

## 🤖 AI Services Testing

### Core AI Endpoints
```bash
# Check AI service status
curl http://localhost:8000/api/ai/health

# Test AI-powered suggestions
curl -X POST http://localhost:8000/api/ai-suggest \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a learning path for FastAPI", "context": {"knowledge": ["Python basics"]}}'

# LibreChat OpenAI-compatible API
curl -X POST http://localhost:8000/api/ai/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-PRSNL-Integration: test-client" \
  -d '{
    "model": "prsnl-gpt-4",
    "messages": [{"role": "user", "content": "How does PRSNL work as a second brain?"}],
    "temperature": 0.7,
    "max_tokens": 150
  }'
```

### Authentication Testing (Post-Bypass Removal)
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

# Test protected endpoint (requires auth token)
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Request password reset email
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Reset password with token from email
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "password_reset_token_from_email",
    "new_password": "NewSecurePassword123!"
  }'
```

### Real-Time Progress Monitoring
```bash
# WebSocket progress updates are automatically broadcast for:
# - File processing tasks
# - Knowledge graph construction
# - AI content analysis
# - Media processing (audio/video)
# - Conversation intelligence analysis

# Test real-time progress (requires WebSocket client)
# Progress updates sent to channels: task_{task_id}, user_{user_id}
```

### Production Configuration
```bash
# Start in production mode
export ENVIRONMENT=production
./start_production.sh

# Or use development mode (default)
./start_backend.sh

# Check current environment settings
curl http://localhost:8000/health | jq '.environment'
```

---

## 🚨 Critical Troubleshooting

### Service Startup Issues
```bash
# Check what's using ports
lsof -i :8000  # Backend
lsof -i :3004  # Frontend
lsof -i :5432  # PostgreSQL

# Kill processes if needed
kill -9 $(lsof -ti :8000)

# Check PostgreSQL status
pg_ctl status -D /opt/homebrew/var/postgresql@16
```

### Database Connection Issues
```bash
# Test database connection
psql "postgresql://pronav@localhost:5432/prsnl" -c "SELECT NOW();"

# Check if database exists
psql "postgresql://pronav@localhost:5432/postgres" -c "\l"

# Check pgvector extension
psql "postgresql://pronav@localhost:5432/prsnl" -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Frontend API Connection Issues
```bash
# Ensure frontend is running
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend
npm run dev -- --port 3004

# Check if port 3004 is occupied
lsof -i :3004
```

### Emergency Recovery
```bash
# 1. Stop all services
pkill -f uvicorn
pkill -f "npm run dev"

# 2. Restart PostgreSQL
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 restart

# 3. Restart backend
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Restart frontend
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend
npm run dev -- --port 3004

# 5. Test everything
curl http://localhost:8000/health
curl http://localhost:3004/
```

---

## 📁 Important File Locations

### Core Documentation
- **Main Status**: `/PRSNL/PROJECT_STATUS.md`
- **AI Coordination**: `/PRSNL/AI_COORDINATION_COMPLETE.md`
- **Task Tracking**: `/PRSNL/TASK_HISTORY.md` 
- **Architecture**: `/PRSNL/ARCHITECTURE.md`
- **API Documentation**: `/PRSNL/API_DOCUMENTATION.md`

### Backend Files
- **Main API**: `/backend/app/main.py`
- **Voice Services**: `/backend/app/services/voice_service.py`
- **RealtimeSTT**: `/backend/app/services/realtime_stt_service.py`
- **Authentication**: `/backend/app/core/auth.py`
- **User Context**: `/backend/app/middleware/user_context.py`

### Frontend Files
- **Voice Chat**: `/frontend/src/lib/components/RealtimeVoiceChat.svelte`
- **Auth Guard**: `/frontend/src/lib/auth/auth-guard.ts`
- **API Client**: `/frontend/src/lib/api.ts`
- **RealtimeSTT Client**: `/frontend/src/lib/services/realtime-stt.ts`

---

## 🎯 System Architecture Summary

### Database Configuration
```bash
Database: prsnl
User: pronav
Host: localhost
Port: 5432
Connection: postgresql://pronav@localhost:5432/prsnl
```

### Environment Info
- **Architecture**: ARM64 (Apple Silicon)
- **Python**: 3.11+
- **Node.js**: 20.18.1
- **PostgreSQL**: 16 (ARM64 native)
- **pgvector**: 0.8.0
- **AI Service**: Azure OpenAI + RealtimeSTT
- **Container Runtime**: Rancher Desktop

### Content Statistics
- **Total Items**: ~30
- **Videos**: 7 functional video items
- **Bookmarks**: 17 imported bookmarks  
- **Articles**: 6 processed articles
- **Functional Features**: Video streaming, AI suggestions, search, timeline, voice integration

---

**Last Updated**: 2025-07-23  
**System Version**: PRSNL v8.0 with Full Authentication & Voice Integration  
**Documentation Status**: Consolidated Core Reference Complete

This comprehensive reference combines all essential system information into a single authoritative source for development, troubleshooting, and task management.