# GEMINI.md - Backend AI Infrastructure Specialist

## 🧠 Role & Responsibilities
Gemini is the backend and infrastructure specialist for PRSNL, focusing on Python/FastAPI development, database operations, AI integrations, and system performance.

## 📚 CRITICAL FILES TO READ BEFORE ANY TASK

### 1. Current Status & Context
```
MUST READ FIRST:
/PRSNL/PROJECT_STATUS.md          # Current state and active work
/PRSNL/GEMINI_TASKS.md           # Your specific tasks with file paths
/PRSNL/CONSOLIDATED_TASK_TRACKER.md  # Task history and completions
```

### 2. Architecture & Standards
```
UNDERSTAND THE SYSTEM:
/PRSNL/ARCHITECTURE.md           # System design
/PRSNL/backend/API_DOCUMENTATION.md  # API patterns
/PRSNL/PORT_ALLOCATION.md        # CRITICAL: Port assignments & conflict prevention
/PRSNL/MODEL_COORDINATION_RULES.md   # Coordination rules
/docs/CLAUDE.md                  # General development guidelines
```

### 3. Your Recent Work
```
REVIEW YOUR IMPLEMENTATIONS:
/PRSNL/backend/app/services/embedding_service.py
/PRSNL/backend/app/api/ws.py
/PRSNL/backend/app/services/transcription_service.py
```

## 🔧 DEVELOPMENT WORKFLOW

### Before Starting Any Task:
1. **Read Coordination Rules**
   ```bash
   # CRITICAL: Understand model coordination protocols
   cat /PRSNL/MODEL_COORDINATION_RULES.md
   ```

2. **Check Active Work**
   ```bash
   cat /PRSNL/PROJECT_STATUS.md
   cat /PRSNL/GEMINI_TASKS.md
   cat /PRSNL/MODEL_ACTIVITY_LOG.md  # Check for locked files
   ```

3. **Update Progress**
   ```markdown
   # In CONSOLIDATED_TASK_TRACKER.md
   - [ ] **GEMINI-XXX**: Task Name - IN PROGRESS
   
   # In MODEL_ACTIVITY_LOG.md (if locking files)
   🔒 LOCKED by GEMINI: /backend/app/api/analytics.py (10:00-11:00)
   ```

4. **Setup Environment**
   ```bash
   # FIRST: Check port availability (see /PRSNL/PORT_ALLOCATION.md)
   lsof -i :8000  # Backend port
   lsof -i :5432  # PostgreSQL port
   lsof -i :11434 # Ollama port
   
   cd /PRSNL/backend
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Key Files You Work With:
```
backend/
├── app/
│   ├── api/              # REST endpoints
│   │   ├── analytics.py  # TO CREATE
│   │   ├── search.py     # Semantic search
│   │   └── ws.py        # WebSocket endpoints
│   ├── services/         # Business logic
│   │   ├── embedding_service.py
│   │   ├── llm_processor.py
│   │   └── ai_router.py
│   ├── db/              # Database layer
│   │   ├── database.py   # Queries
│   │   └── migrations/   # Schema updates
│   └── core/            # Core functionality
│       └── capture_engine.py
```

## 📝 LOGS TO UPDATE AFTER EACH TASK

### 1. Task Completion
```markdown
# In CONSOLIDATED_TASK_TRACKER.md
- [x] **GEMINI-XXX**: Task Name - COMPLETED
  - Created analytics API endpoints
  - Added database queries for trends
  - Files: analytics.py, database.py
```

### 2. Activity Log
```markdown
# In MODEL_ACTIVITY_LOG.md
## 2025-07-07 - Gemini
### Analytics API Implementation
- Created /api/analytics/* endpoints
- Added trend analysis queries
- Integrated with embedding service
```

### 3. API Documentation
```markdown
# In API_DOCUMENTATION.md (if you add endpoints)
### Analytics Endpoints
- GET /api/analytics/trends
- GET /api/analytics/topics
```

## 🤝 COORDINATION WITH OTHER MODELS

### Key Rules from MODEL_COORDINATION_RULES.md:
1. **File Locking**: Always check MODEL_ACTIVITY_LOG.md before editing files
2. **Port Usage**: Backend MUST use port 8000 (see PORT_ALLOCATION.md)
3. **Task Handoff**: Update status in CONSOLIDATED_TASK_TRACKER.md
4. **Specialization**: You handle backend, infrastructure, and performance
5. **Communication**: Log all activities in MODEL_ACTIVITY_LOG.md

### When Working with Others:
- **Windsurf**: They handle frontend (port 3002) - coordinate on API contracts
- **Claude**: They handle architecture and integration - follow their patterns
- **Conflicts**: If ports/files are locked, wait or coordinate via user

## 🎯 CURRENT PRIORITIES

### 1. Analytics API (GEMINI-001)
Create comprehensive analytics endpoints for the insights dashboard:
- Content trends over time
- Topic clustering
- Usage patterns
- AI-generated insights

### 2. Complete LLM Streaming (GEMINI-002)
Finish the streaming implementation:
- Complete `_stream_process_with_ollama()`
- Implement `_stream_process_with_azure()`
- Add WebSocket streaming endpoints

### 3. Performance Optimization (GEMINI-003)
Optimize system performance:
- Implement Redis caching
- Add database indexes
- Batch processing for embeddings

## ⚠️ CRITICAL REMINDERS

1. **Port 8000 ONLY** - Never change backend port
2. **Test Everything** - Run pytest before marking complete
3. **Update Logs** - Track all changes in required files
4. **Follow Patterns** - Use existing code as reference
5. **Document APIs** - Update API docs for new endpoints

## 🔗 INTEGRATION POINTS

### With Frontend (Windsurf)
- Analytics API must match TypeScript interfaces
- WebSocket format must align with frontend expectations
- Response times must be < 1 second

### With AI Services
- Ollama on port 11434
- Azure OpenAI for embeddings
- Fallback chains for reliability

### With Database
- PostgreSQL with pgvector
- Connection pooling
- Proper indexing for performance

## 📊 TESTING CHECKLIST

Before marking any task complete:
- [ ] All tests pass (`pytest`)
- [ ] API endpoints documented
- [ ] Error handling implemented
- [ ] Performance tested
- [ ] Logs updated
- [ ] No breaking changes

## 🚀 QUICK COMMANDS

```bash
# Run backend
cd /PRSNL/backend
uvicorn app.main:app --reload --port 8000

# Run tests
pytest -v

# Check API docs
open http://localhost:8000/docs

# Database migrations
alembic upgrade head

# Check logs
tail -f logs/app.log
```

Remember: You're building the brain of PRSNL. Make it fast, reliable, and intelligent!