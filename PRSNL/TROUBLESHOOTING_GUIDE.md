# 🔧 PRSNL Troubleshooting Guide

*Last Updated: 2025-07-08*

This guide consolidates all known issues, errors, and their solutions from the PRSNL project.

## 📑 Table of Contents
1. [Recent Critical Issues](#recent-critical-issues)
2. [Frontend Issues](#frontend-issues)
3. [Backend Issues](#backend-issues)
4. [Docker & Infrastructure](#docker--infrastructure)
5. [API Connection Issues](#api-connection-issues)
6. [Database Issues](#database-issues)
7. [AI Service Issues](#ai-service-issues)
8. [Common Patterns](#common-patterns)

---

## 🚨 Recent Critical Issues

### 🔴 CRITICAL: Frontend API Calls to Wrong Port (PERMANENT FIX APPLIED)
**Date**: 2025-07-08
**Severity**: CRITICAL - Completely broke all API functionality
**Status**: ✅ PERMANENTLY FIXED

**Symptoms**:
- All API calls failing with 500 errors
- Frontend making requests to `:3002/api/...` instead of `:8000/api/...`
- Error: "Failed to load resource: the server responded with a status of 500 (Internal Server Error)"

**Root Causes**:
1. Frontend pages using direct `fetch('/api/...')` instead of API library
2. Mixed dev/prod configurations with incorrect base URLs
3. Docker container using pre-built code, not reflecting changes
4. Vite server only listening on IPv6 (::1), not IPv4

**PERMANENT FIX**:
```javascript
// frontend/src/lib/api.ts
const API_BASE_URL = '/api'; // ALWAYS use relative URLs
```

```typescript
// frontend/vite.config.ts
server: {
  host: '0.0.0.0', // Listen on all interfaces
  proxy: {
    '/api': {
      target: process.env.VITE_API_URL || 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

**Updated Files**:
- `/routes/item/[id]/+page.svelte` - Use `getItem()` not fetch
- `/routes/videos/[id]/+page.svelte` - Use `getItem()` not fetch
- `/routes/videos/course/+page.svelte` - Use `getItem()` not fetch

**CORRECT SETUP (NEVER DEVIATE)**:
```bash
# Development
docker-compose -f docker-compose.dev.yml up    # Backend only
cd frontend && npm run dev                      # Frontend with hot reload

# Production
docker-compose -f docker-compose.production.yml up
```

**Prevention**:
- NEVER use direct fetch() for API calls
- ALWAYS use relative URLs (/api/...)
- ALWAYS test both dev and production setups
- Run `grep -r "fetch.*api" frontend/src` to find violations

### Frontend Server Not Running (ERR_CONNECTION_REFUSED)
**Symptoms**: 
- Browser shows "This site can't be reached"
- localhost:3002 refused to connect

**Solution**:
```bash
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend
npm run dev
```

**Prevention**: Always ensure both frontend and backend are running

### Chat Not Working
**Symptoms**: 
- Send message, get no response
- WebSocket connection fails

**Root Causes & Fixes**:
1. Proxy configuration missing WebSocket support
2. Hardcoded port instead of dynamic
3. API prefix mismatch (/api/v1 vs /api)

**Status**: ✅ FIXED (2025-01-08)

### Ollama References in System
**Issue**: Docker trying to pull Ollama image
**Fix**: Removed ALL Ollama references, using Azure OpenAI exclusively
**Status**: ✅ FIXED (2025-01-08)

---

## 🎨 Frontend Issues

### Search Returning Empty Results
**Symptom**: Search returns 200 OK but no results shown
**Root Cause**: Frontend expects `data.results` but API returns `data.items`
**Fix**: Update frontend to use correct field name
```typescript
// Before: results = data.results || [];
// After:
results = data.items || [];
```

### Svelte Component Variable Errors
**Common Missing Variables**:
```svelte
<script lang="ts">
  // LiveTags.svelte
  let newTagInput = '';
  let filteredSuggestions: string[] = [];
  let debounceMs = 300;
  let isReducedMotion = false;
  let tagListElement: HTMLDivElement;
  
  // capture/+page.svelte
  type ItemType = 'note' | 'article' | 'video' | 'image';
  let videoQuality: 'standard' | 'high' = 'standard';
</script>
```

### Top-Level Return in Reactive Statement
**Error**: "Function containing 'rewrite to avoid top-level return'"
**Fix**: Move logic to lifecycle hook
```svelte
// Before:
$: if (someCondition) return;

// After:
import { onMount } from 'svelte';
onMount(() => {
  if (someCondition) return;
});
```

### Type Mismatches
**Issue**: Property names don't match between frontend/backend
**Fix**: Ensure consistent naming (camelCase in frontend, snake_case in backend)

---

## 🔧 Backend Issues

### Import Errors - Missing Singleton
**Error**: `ImportError: cannot import name 'embedding_service'`
**Fix**: Add instantiation at end of service file
```python
# At the end of embedding_service.py
embedding_service = EmbeddingService()
```

### API Route 404 Errors
**Issue**: Route not found despite being defined
**Common Causes**:
1. Route prefix mismatch
2. Router not registered in main.py
3. Incorrect HTTP method

**Fix**:
```python
# In main.py
app.include_router(ai_suggest.router, prefix="/api")

# In ai_suggest.py
@router.post("/suggest")  # This becomes /api/suggest
```

### JSONB Field Handling
**Issue**: PostgreSQL JSONB fields returning as string
**Fix**:
```python
import json

# Handle both dict and string returns
metadata = row["metadata"] if isinstance(row.get("metadata"), dict) else (
    json.loads(row["metadata"]) if row.get("metadata") else {}
)
```

### Pydantic Validation Errors
**Common Issues**:
- Missing required fields
- Type mismatches
- JSONB fields not properly typed

**Fix**: Ensure models match database schema exactly

---

## 🐳 Docker & Infrastructure

### Port Conflicts
**Error**: "bind: address already in use"
**Check ports**:
```bash
lsof -i :3002  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
```

**Fix**: Kill conflicting process or change port

### Container Networking
**Issue**: Frontend can't reach backend
**Fix**: Use correct service names in Docker
```yaml
# Wrong: http://localhost:8000
# Right: http://backend:8000 (in Docker)
# Right: http://localhost:8000 (from host)
```

### NGINX Network Issues
**Error**: 502 Bad Gateway
**Fix**:
```bash
docker network connect prsnl_default prsnl_nginx
```

---

## 🔌 API Connection Issues

### CORS Errors
**Symptom**: "Access to fetch at ... has been blocked by CORS policy"
**Fix**: Update backend CORS settings
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### WebSocket Connection Failed
**Common Causes**:
1. Missing proxy configuration
2. Wrong WebSocket URL
3. Protocol mismatch (ws vs wss)

**Fix in vite.config.ts**:
```javascript
proxy: {
  '/ws': {
    target: 'ws://localhost:8000',
    ws: true,
    changeOrigin: true
  }
}
```

---

## 💾 Database Issues

### Missing Columns
**Error**: "column items.platform does not exist"
**Fix**: Run migrations or add columns manually
```sql
ALTER TABLE items ADD COLUMN IF NOT EXISTS platform VARCHAR(50);
ALTER TABLE items ADD COLUMN IF NOT EXISTS item_type VARCHAR(50);
ALTER TABLE items ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;
```

### Empty Timeline
**Issue**: No items showing despite data in database
**Common Causes**:
1. Items have status 'failed' instead of 'completed'
2. Timestamp filtering too restrictive
3. Join query failing

**Fix**:
```sql
UPDATE items SET status = 'completed' WHERE status = 'failed';
```

---

## 🤖 AI Service Issues

### Azure OpenAI Connection Errors
**Error**: "Connection error" or "API key not found"
**Fix**: Ensure environment variables are set
```bash
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2025-01-01-preview
```

### Embeddings Service Optional
**Issue**: System fails when embeddings not available
**Fix**: Make embeddings optional
```python
try:
    embeddings = await embedding_service.generate(content)
except Exception as e:
    logger.warning(f"Embeddings generation failed: {e}")
    embeddings = None  # Continue without embeddings
```

---

## 🔄 Common Patterns

### Pattern 1: Service Not Instantiated
**Symptom**: ImportError for service name
**Fix**: Add singleton at end of file
```python
service_name = ServiceClass()
```

### Pattern 2: Frontend/Backend Type Mismatch
**Symptom**: Data not displaying correctly
**Fix**: Check field names match exactly

### Pattern 3: Docker Service Names
**Symptom**: Connection refused in Docker
**Fix**: Use service names from docker-compose.yml

### Pattern 4: Missing Environment Variables
**Symptom**: Services fail to start
**Fix**: Check .env file has all required variables

---

## 🚀 Quick Diagnostics

### Check System Health
```bash
# Check all services
docker ps

# Check backend logs
docker logs prsnl_backend --tail 50

# Check frontend
curl http://localhost:3002

# Check API
curl http://localhost:8000/health

# Check database
docker exec -it prsnl_db psql -U postgres -d prsnl -c "SELECT COUNT(*) FROM items;"
```

### Common Fixes Script
```bash
#!/bin/bash
# Quick fixes for common issues

# Restart everything
docker-compose down
docker-compose up -d

# Clear cache
docker exec -it prsnl_redis redis-cli FLUSHALL

# Fix permissions
chmod -R 755 ./media

# Rebuild frontend
cd frontend && npm install && npm run build
```

---

## 📞 When All Else Fails

1. Check logs: `docker logs [container] --tail 100`
2. Restart services: `docker-compose restart`
3. Clear browser cache
4. Check network tab in browser DevTools
5. Verify all environment variables are set
6. Ensure ports are not blocked by firewall
7. Try incognito/private browsing mode

Remember: Most issues are either:
- Missing environment variables
- Port conflicts
- Type mismatches between frontend/backend
- Docker networking issues