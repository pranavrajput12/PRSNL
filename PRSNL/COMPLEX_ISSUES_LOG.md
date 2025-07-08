# 📋 PRSNL Complex Issues Log & Solutions [ARCHIVED]

⚠️ **THIS FILE HAS BEEN MERGED INTO TROUBLESHOOTING_GUIDE.md**

Please refer to:
- **📚 Complete Guide**: `/PRSNL/TROUBLESHOOTING_GUIDE.md`
- **🔧 Common Patterns**: See "Common Patterns" section
- **💡 Solutions**: Organized by category (Frontend, Backend, Docker, etc.)

---

## 🔥 Recurring Issues and Fixes

### 1. Missing Python Import/Instantiation Errors
**Issue**: `ImportError: cannot import name 'embedding_service' from 'app.services.embedding_service'`
**Root Cause**: Class is defined but singleton instance not created
**Fix**: Add instantiation at end of file
```python
# At the end of embedding_service.py
embedding_service = EmbeddingService()
```

### 2. Svelte Component Variable Declaration Errors
**Issue**: Variables used but not declared in Svelte components
**Common Missing Variables**:
- `LiveTags.svelte`: `newTagInput`, `filteredSuggestions`, `debounceMs`, `isReducedMotion`, `tagListElement`
- `capture/+page.svelte`: `ItemType`, `videoQuality`

**Fix**: Add declarations in script section
```svelte
<script lang="ts">
  let newTagInput = '';
  let filteredSuggestions: string[] = [];
  let debounceMs = 300;
  let isReducedMotion = false;
  let tagListElement: HTMLDivElement;
  
  // For capture page
  type ItemType = 'note' | 'article' | 'video' | 'image';
  let videoQuality: 'standard' | 'high' = 'standard';
</script>
```

### 3. API Route 404 Errors
**Issue**: `/api/ai-suggest` returning 404
**Root Cause**: Route prefix mismatch
**Fix**: Ensure correct route registration
```python
# In ai_suggest.py
@router.post("/suggest")  # This becomes /api/suggest, not /api/ai-suggest

# To fix, either:
# 1. Change client to use /api/suggest
# 2. Or change route to @router.post("/ai-suggest")
```

### 4. Azure OpenAI Connection Errors
**Issue**: "Connection error" when trying to use embeddings
**Root Cause**: Azure OpenAI credentials not configured
**Fix**: Update .env file with real credentials
```env
AZURE_OPENAI_API_KEY=your_actual_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

### 5. Single Entry Page Timeout
**Issue**: Request timeout on single item page
**Root Cause**: Multiple potential causes:
1. Large embedding calculations
2. Missing database indexes
3. Circular imports
4. WebSocket connection issues

**Fix**: 
```python
# 1. Add database indexes (already in migration 005)
# 2. Add request timeout handling
@router.get("/items/{item_id}")
async def get_item(
    item_id: str,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    try:
        # Add timeout to query
        async with asyncio.timeout(5.0):  # 5 second timeout
            result = await db_connection.fetchrow(...)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timeout")
```

### 6. Backend Startup Failures
**Issue**: Backend crashes on startup with various import errors
**Common Causes**:
1. Missing Tag class in schemas.py
2. Outdated AI service references
3. Missing environment variables

**Fix**: Run debug script or manually fix:
```bash
# Run the debug script
python3 debug_and_fix.py

# Or manually:
# 1. Remove Tag import from export.py
# 2. Update AI service references in health check
# 3. Ensure all required env vars are set
```

### 7. WebSocket Connection Reset
**Issue**: Connection reset when accessing certain endpoints
**Root Cause**: Unhandled exceptions in route handlers
**Fix**: Add proper error handling
```python
try:
    # Route logic
except Exception as e:
    logger.error(f"Unhandled error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### 8. Frontend Build Errors
**Issue**: TypeScript errors in Svelte components
**Common Errors**:
1. Type assertions in templates
2. Missing type imports
3. Incorrect event handler syntax

**Fix**:
```svelte
<!-- Wrong -->
on:click={() => handleChange(id as 'keyword' | 'semantic')}

<!-- Right -->
on:click={() => handleChange(id)}

<!-- Ensure type safety in script section instead -->
```

### 9. Docker/Service Issues
**Issue**: Services not starting or port conflicts
**Fix**: 
```bash
# Check and kill processes on ports
lsof -i :8000  # Backend
lsof -i :3002  # Frontend
lsof -i :5432  # PostgreSQL

# Kill specific process
kill -9 <PID>

# Or use the debug script which handles this automatically
```

### 10. Missing Semantic Search Endpoint
**Issue**: `/api/search/semantic` returns 404
**Root Cause**: Endpoint not implemented
**Fix**: Added in search.py
```python
@router.get("/search/semantic")
async def semantic_search(
    query: str,
    mode: str = "hybrid",
    limit: int = 20,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    # Implementation
```

## 🛠️ Automated Debug Script

Created `debug_and_fix.py` that automatically:
1. Checks environment setup
2. Fixes missing .env file
3. Configures Azure OpenAI
4. Fixes common import issues
5. Checks and starts services
6. Reports issues that need manual attention

## 🚀 Quick Fix Commands

```bash
# Run debug script
python3 debug_and_fix.py

# Kill all services and restart
pkill -f uvicorn
pkill -f "npm run dev"
docker compose down
docker compose up -d db

# Start backend with proper logging
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000 --log-level debug

# Start frontend
cd frontend && npm run dev -- --port 3002
```

## 📝 Prevention Strategies

1. **Use Type Checking**: Run `mypy` for Python and `npm run check` for Svelte
2. **Test Imports**: Always test after adding new imports
3. **Environment Template**: Keep .env.example updated
4. **Automated Testing**: Add tests for common issues
5. **Pre-commit Hooks**: Add hooks to catch these issues before commit

## 🔍 Debugging Tips

1. **Check Logs First**: Always check `/tmp/uvicorn.log` and browser console
2. **Verify Services**: Ensure PostgreSQL, Redis, and all dependencies are running
3. **Test Endpoints**: Use curl to test API endpoints directly
4. **Check Environment**: Verify all required environment variables are set
5. **Use Debug Script**: Run the automated debug script for quick fixes

---
*Last Updated: 2025-07-07*