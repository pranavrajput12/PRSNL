# CRITICAL ERROR LOG - PRSNL Project [ARCHIVED]

⚠️ **THIS FILE HAS BEEN MERGED INTO TROUBLESHOOTING_GUIDE.md**

Please refer to:
- **📚 Complete Guide**: `/PRSNL/TROUBLESHOOTING_GUIDE.md`
- **🔧 Quick Fixes**: See "Recent Critical Issues" section
- **📝 Patterns**: See "Common Patterns" section

---

*Last Updated: 2025-07-08 by Claude*

## 🚨 RECENT CRITICAL ISSUES (2025-07-08)

### 1. Frontend Server Not Running - Connection Refused ✅ FIXED
- **Issue**: localhost refused to connect, ERR_CONNECTION_REFUSED
- **Root Cause**: Frontend development server was not running
- **What Happened**: 
  - Frontend server was either never started or had crashed
  - No process was listening on port 3002
  - Backend was running fine in Docker on port 8000
- **Fix Applied**:
  ```bash
  cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend
  npm run dev
  ```
- **Status**: RESOLVED - Frontend now accessible at http://localhost:3002
- **Additional Issue**: http://prsnl:3002 doesn't work
  - Need to add /etc/hosts entry: `127.0.0.1 prsnl`
  - Or use localhost:3002 directly
- **Prevention**: 
  - Always check if both frontend AND backend are running
  - Use `lsof -i :3002` to verify port is in use
  - Consider using PM2 or similar for process management

### 2. Backend 500 Error - Import Issues ✅ FIXED
- **Issue**: Frontend showing "Failed to load feed" with 500 error
- **Root Cause**: Multiple import errors in new AI service modules
  - Missing `app.models.item` module
  - Missing `app.core.auth` module  
  - Database function naming mismatch
- **Fix Applied**:
  - Created missing auth.py module
  - Added database function alias
  - Temporarily disabled problematic routes (video_streaming, analytics, etc.)
- **Status**: RESOLVED - Backend running, core features working
- **Side Effect**: Video library page won't work until routes are re-enabled

## 🚨 PREVIOUS CRITICAL ISSUES (2025-07-07)

### 1. Search Returning Empty Results ✅ FIXED
- **Issue**: Search was returning 200 OK but with empty results
- **Root Cause**: Frontend was looking for `data.results` but API returns `data.items`
- **Fix**: Updated `/frontend/src/routes/search/+page.svelte` line 172
- **Status**: RESOLVED

### 2. Frontend Build Errors - Premium Components 🔥 PARTIALLY FIXED
- **Issue**: Multiple component errors preventing site from loading
- **Components Affected**:
  - AnimatedButton - Top-level return in reactive statement
  - FloatingActionButton - actionSprings not a store error
  - Chat page - Stores must be declared at top level
- **Temporary Fix**: 
  - Fixed AnimatedButton onMount issue
  - REMOVED FloatingActionButton completely
  - Fixed chat page orb animations
- **Status**: SITE IS UP but some premium features disabled

### 3. Error 500 / Connection Refused ✅ FIXED
- **Issue**: Website was completely down
- **Root Cause**: Frontend server crashed due to component errors
- **Fix**: Removed problematic components and restarted server
- **Status**: RESOLVED - Site accessible at http://localhost:3002

## 📋 TODO TOMORROW (2025-07-08)

### High Priority Fixes:
1. **Properly fix FloatingActionButton component**
   - Rewrite without store subscription issues
   - Test thoroughly before re-enabling

2. **Fix remaining premium component issues**
   - Review all premium components for similar store issues
   - Ensure proper lifecycle management

3. **Test Video Streaming**
   - Capture a YouTube video
   - Verify playback works
   - Check transcript extraction

4. **Fix Attachments Table Error**
   - Create missing attachments table
   - Non-critical but shows in logs

### Code Quality:
1. **Remove unused CSS selectors** (warnings in console)
2. **Fix A11y warnings** (non-critical but should address)
3. **Clean up commented code**

## 🔧 CURRENT INFRASTRUCTURE STATUS

### What's Working:
- ✅ Frontend: http://localhost:3002
- ✅ Backend API: http://localhost:8000
- ✅ Search functionality
- ✅ Timeline view
- ✅ Capture page
- ✅ Chat interface (with reduced animations)

### What's Disabled:
- ❌ FloatingActionButton (removed due to errors)
- ⚠️ Some premium micro-interactions

### Docker Status:
```
prsnl_backend   - ✅ Running
prsnl_db        - ✅ Running  
prsnl_redis     - ✅ Running
```

## 🚀 QUICK RECOVERY COMMANDS

If site goes down again:
```bash
# 1. Kill any stuck processes
pkill -f "vite dev"

# 2. Restart frontend
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend
npm run dev -- --port 3002

# 3. Check backend
docker ps
docker logs prsnl_backend --tail 50

# 4. Test endpoints
curl -s "http://localhost:8000/api/search?query=test" | jq .
curl -s -o /dev/null -w "%{http_code}" http://localhost:3002/
```

## 📝 LESSONS LEARNED

1. **Svelte Store Restrictions**: Stores must be declared at component top level, not inside loops or reactive statements
2. **Component Testing**: Always test new components in isolation before integration
3. **Error Recovery**: Keep a working baseline, disable features rather than breaking the whole site
4. **MCP Usage**: User requested using MCP tools more - consider for future debugging

---

**Note**: Website is functional but with reduced features. Full fix scheduled for tomorrow.