# 🧠 GEMINI - Backend AI Infrastructure Tasks

## 📚 REQUIRED READING BEFORE ANY TASK
Always review these files before starting work:

### Documentation to Read First:
1. `/PRSNL/PROJECT_STATUS.md` - Current project state and context
2. `/PRSNL/MODEL_COORDINATION_RULES.md` - Port assignments and rules
3. `/PRSNL/backend/API_DOCUMENTATION.md` - API structure and patterns
4. `/PRSNL/ARCHITECTURE.md` - System design and data flow

### Files to Update After Each Task:
1. `/PRSNL/CONSOLIDATED_TASK_TRACKER.md` - Mark task complete
2. `/PRSNL/MODEL_ACTIVITY_LOG.md` - Log your changes
3. `/PRSNL/backend/API_DOCUMENTATION.md` - If you add/modify endpoints
4. `/PRSNL/PROJECT_STATUS.md` - Update progress section

---

## 🎯 ACTIVE TASKS

### Task GEMINI-001: Analytics API Endpoints
**Priority**: HIGH
**Status**: COMPLETED

**Files to Create:**
```
/PRSNL/backend/app/api/analytics.py
```

**Files to Modify:**
```
/PRSNL/backend/app/main.py              # Add router
/PRSNL/backend/app/db/database.py       # Add analytics queries
/PRSNL/backend/app/models/schemas.py    # Add response models
```

**Files to Reference:**
```
/PRSNL/backend/app/api/search.py        # Example API structure
/PRSNL/backend/app/api/timeline.py      # Pagination pattern
/PRSNL/backend/app/services/embedding_service.py  # For semantic analysis
```

**Requirements:**
1. Create endpoints:
   - `GET /api/analytics/trends` - Content trends over time
   - `GET /api/analytics/topics` - Topic clustering data
   - `GET /api/analytics/insights` - AI-generated insights
   - `GET /api/analytics/usage` - User activity patterns

2. Database queries to implement:
   ```python
   # In database.py
   async def get_content_trends(conn, timeframe: str)
   async def get_topic_clusters(conn, limit: int = 10)
   async def get_usage_analytics(conn, start_date, end_date)
   ```

3. Response schemas in schemas.py:
   ```python
   class TrendData(BaseModel):
       date: datetime
       articles: int
       videos: int
       notes: int
       bookmarks: int
   
   class TopicCluster(BaseModel):
       topic: str
       count: int
       items: List[UUID]
       keywords: List[str]
   ```

---

### Task GEMINI-002: Complete LLM Streaming
**Priority**: HIGH
**Status**: COMPLETED

**Files to Complete:**
```
/PRSNL/backend/app/services/llm_processor.py  # Finish streaming methods
/PRSNL/backend/app/api/ws.py                  # Add streaming endpoints
```

**Files to Reference:**
```
/PRSNL/backend/app/services/ai_router.py      # AI provider selection
/PRSNL/backend/app/core/websocket_manager.py  # WebSocket handling
```

**Requirements:**
1. Complete streaming implementation in llm_processor.py:
   - Finish `_stream_process_with_ollama()`
   - Implement `_stream_process_with_azure()`
   - Add proper error handling and reconnection

2. WebSocket endpoints in ws.py:
   - `/ws/ai/stream` - Stream AI responses
   - `/ws/ai/suggestions` - Live tag suggestions
   - Implement heartbeat/ping-pong

---

### Task GEMINI-003: Performance Optimization
**Priority**: MEDIUM
**Status**: COMPLETED

**Files to Optimize:**
```
/PRSNL/backend/app/services/embedding_service.py  # Batch processing
/PRSNL/backend/app/worker.py                      # Background tasks
/PRSNL/backend/app/db/database.py                 # Query optimization
```

**Files to Create:**
```
/PRSNL/backend/app/services/cache.py              # Redis caching layer
/PRSNL/backend/app/db/migrations/003_add_indexes.sql
```

**Requirements:**
1. Implement Redis caching for:
   - Embedding results
   - AI responses
   - Search results

2. Database optimizations:
   - Add indexes for common queries
   - Implement connection pooling improvements
   - Add query result caching

3. Background task improvements:
   - Batch embedding generation
   - Async video processing
   - Queue prioritization

---

## 🛠️ DEVELOPMENT WORKFLOW

### Before Starting:
```bash
cd /PRSNL/backend
source venv/bin/activate  # Or create: python3 -m venv venv
pip install -r requirements.txt
```

### Testing Your Changes:
```bash
# Run backend
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/

# Check API docs
open http://localhost:8000/docs
```

### Environment Variables:
```bash
# Check .env file for required vars
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_ENDPOINT=xxx
DATABASE_URL=postgresql://user:pass@localhost/prsnl
REDIS_URL=redis://localhost:6379
```

---

## 📝 COMMIT MESSAGE FORMAT
```
feat(backend): [GEMINI-XXX] Brief description

- Detailed change 1
- Detailed change 2

Updates: CONSOLIDATED_TASK_TRACKER.md, MODEL_ACTIVITY_LOG.md
```

---

## ⚠️ CRITICAL REMINDERS
1. **NEVER** change port assignments (Backend = 8000)
2. **ALWAYS** update tracking files after completing work
3. **TEST** all endpoints before marking complete
4. **DOCUMENT** new APIs in API_DOCUMENTATION.md
5. **CHECK** for existing patterns before implementing new ones