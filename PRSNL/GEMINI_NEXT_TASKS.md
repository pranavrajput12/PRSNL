# Next Tasks for Gemini - Backend AI Infrastructure Specialist

## Date: 2025-07-07
## Priority: HIGH

### Task 1: Fix AI Suggestions Error Handling
**File**: `/PRSNL/backend/app/api/ai_suggest.py`
**Issue**: The AI suggestions endpoint fails silently when Azure OpenAI or scraping fails
**Requirements**:
1. Add proper fallback when Azure OpenAI is not configured
2. Use the AI Router service pattern (see `/PRSNL/backend/app/services/ai_router.py`)
3. Add better error messages for debugging
4. Implement retry logic for transient failures
5. Add logging for successful suggestions

**Test**: Try the endpoint with various URLs including invalid ones

### Task 2: Implement Analytics API Endpoints
**Files to Create**: `/PRSNL/backend/app/api/analytics.py`
**Reference**: See frontend expectations in `/PRSNL/frontend/src/routes/insights/+page.svelte`
**Requirements**:
1. Create the following endpoints:
   - `GET /api/analytics/trends` - Content trends over time
   - `GET /api/analytics/topics` - Top topics/tags analysis  
   - `GET /api/analytics/usage_patterns` - Usage statistics
   - `GET /api/analytics/ai_insights` - AI-generated insights

2. Response formats:
```python
# Trends endpoint
{
  "trends": [
    {
      "date": "2025-07-01",
      "articles": 5,
      "videos": 2,
      "notes": 3,
      "bookmarks": 1
    }
  ]
}

# Topics endpoint
{
  "topics": [
    {
      "tag": "technology",
      "count": 42,
      "percentage": 15.5
    }
  ]
}
```

3. Use efficient SQL queries with proper indexes
4. Cache results using Redis (see cache service)

### Task 3: Complete WebSocket Streaming Implementation
**Files**: 
- `/PRSNL/backend/app/services/llm_processor.py`
- `/PRSNL/backend/app/api/ws.py`

**Current Status**: Partially implemented
**Requirements**:
2. Implement `_stream_process_with_azure()` method
3. Add proper error handling for connection drops
4. Implement heartbeat/ping-pong to keep connections alive
5. Add streaming for tag suggestions

### Task 4: Optimize Database Performance
**Files**: 
- `/PRSNL/backend/app/db/migrations/`
- `/PRSNL/backend/app/db/database.py`

**Requirements**:
1. Add composite indexes for common query patterns:
   - `(created_at, item_type)` for timeline queries
   - `(tag_id, created_at)` for tag-based queries
   - Text search indexes for content/title/summary

2. Implement query optimization:
   - Use EXPLAIN ANALYZE on slow queries
   - Add query plan caching
   - Implement pagination cursors instead of offset

3. Add database connection pooling configuration

### Task 5: Implement Caching Layer
**File**: `/PRSNL/backend/app/services/cache.py`
**Requirements**:
1. Complete Redis integration for:
   - Embedding cache (key: item_id, value: embedding vector)
   - Search results cache (with TTL)
   - Analytics data cache (refresh hourly)
   - Tag suggestions cache

2. Add cache warming on startup for frequently accessed data
3. Implement cache invalidation on updates
4. Add cache hit/miss metrics

## Important Notes:
1. **ALWAYS** use port 8000 for backend
2. **ALWAYS** check `/PRSNL/MODEL_ACTIVITY_LOG.md` before starting
3. **ALWAYS** use the AI Router pattern for LLM calls
4. **NEVER** create new OpenAI clients - use existing services
5. Test all changes before marking complete

## Testing Commands:
```bash
# Test AI suggestions
curl -X POST http://localhost:8000/api/suggest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Test analytics endpoints  
curl http://localhost:8000/api/analytics/trends
curl http://localhost:8000/api/analytics/topics

# Test WebSocket
wscat -c ws://localhost:8000/ws/ai-stream/test-client
```

## References:
- Architecture: `/PRSNL/ARCHITECTURE.md`
- API Documentation: `/PRSNL/API_DOCUMENTATION.md`
- Existing patterns: `/PRSNL/backend/app/services/ai_router.py`
- Frontend expectations: `/PRSNL/frontend/src/routes/insights/+page.svelte`