# 🚨 Crash Recovery Guide

## Quick Recovery Commands

### When Terminal Crashes
```bash
# 1. Check what was happening
git log -1 --oneline
git status

# 2. Read session state
@CURRENT_SESSION_STATE.md Resume my last session

# 3. Check services
lsof -ti:8000  # Backend
lsof -ti:3004  # Frontend
```

## Service Recovery

### Backend Recovery
```bash
# Kill existing process if hung
lsof -ti:8000 | xargs kill -9

# Restart backend
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Frontend Recovery
```bash
# Kill existing process if hung
lsof -ti:3004 | xargs kill -9

# Restart frontend
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend
npm run dev -- --port 3004
```

### Database Recovery
```bash
# Check PostgreSQL status (ARM64 on port 5433)
psql -U pronav -p 5433 -d prsnl -c "SELECT version();"

# If needed, restart PostgreSQL
/opt/homebrew/bin/brew services restart postgresql@16
```

### DragonflyDB Recovery
```bash
# Check status
docker ps | grep dragonflydb

# Restart if needed
docker-compose restart dragonflydb
```

## Common Recovery Scenarios

### Scenario 1: Lost Context During Feature Development
1. Check last commit: `git log -1`
2. Review modified files: `git status`
3. Read CURRENT_SESSION_STATE.md for task details
4. Check which services are running
5. Continue from where you left off

### Scenario 2: API Endpoint Not Working
1. Check backend logs for errors
2. Verify database connection
3. Test with curl command from documentation
4. Check for missing imports or dependencies
5. Restart backend if needed

### Scenario 3: Frontend Build Errors
1. Clear cache: `rm -rf node_modules/.vite .svelte-kit`
2. Reinstall dependencies: `npm install`
3. Check for TypeScript errors: `npm run check`
4. Restart dev server

### Scenario 4: Database Connection Failed
1. Verify PostgreSQL is running on port 5433
2. Check pgvector extension is installed
3. Test connection: `psql -U pronav -p 5433 -d prsnl`
4. Review .env file for correct settings

## CodeMirror Specific Recovery

### If CodeMirror Analysis Fails
```bash
# Test endpoint
curl -X POST "http://localhost:8000/api/codemirror/analyze/1cbb79ce-8994-490c-87ce-56911ab03807" \
  -H "Content-Type: application/json" \
  -d '{"repo_id": "1cbb79ce-8994-490c-87ce-56911ab03807", "analysis_depth": "standard"}'

# Check job status
curl http://localhost:8000/api/persistence/status/[job_id]
```

### Common CodeMirror Issues
1. **500 Error**: Check database imports in codemirror_service.py
2. **Auth Error**: Verify auth.py returns User object
3. **Job Not Found**: Check job persistence service connection
4. **No Progress**: Monitor WebSocket for updates

## Environment Variables Recovery

### Critical Environment Variables
```bash
# Database
DATABASE_URL=postgresql://pronav@localhost:5433/prsnl

# AI Services
AZURE_OPENAI_API_KEY=[your-key]
AZURE_OPENAI_ENDPOINT=[your-endpoint]
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_DEPLOYMENT=prsnl-gpt-4
AZURE_OPENAI_LIBRECHAT_DEPLOYMENT=gpt-4.1-mini

# GitHub (if using OAuth)
GITHUB_CLIENT_ID=[your-client-id]
GITHUB_CLIENT_SECRET=[your-client-secret]
```

## Documentation References

### Key Files to Check After Crash
1. **CURRENT_SESSION_STATE.md** - Active task and progress
2. **TASK_HISTORY.md** - Recent completions
3. **CLAUDE.md** - Project configuration
4. **PROJECT_STATUS.md** - System capabilities
5. **API_DOCUMENTATION.md** - Endpoint references

## Verification Scripts

### Full System Health Check
```bash
#!/bin/bash
echo "=== SYSTEM HEALTH CHECK ==="

echo "1. Backend Health:"
curl -s http://localhost:8000/health | jq

echo "2. Frontend Status:"
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:3004/

echo "3. Database Connection:"
psql -U pronav -p 5433 -d prsnl -c "SELECT COUNT(*) FROM github_repos;"

echo "4. AI Services:"
curl -s http://localhost:8000/api/ai/health

echo "5. DragonflyDB:"
docker ps | grep dragonflydb

echo "=== HEALTH CHECK COMPLETE ==="
```

## Prevention Tips

### Before Starting Work
1. Document task in CURRENT_SESSION_STATE.md
2. Commit frequently with descriptive messages
3. Test changes incrementally
4. Keep services running in separate terminals

### During Development
1. Save files frequently
2. Run sanity checks after changes
3. Update documentation as you go
4. Use TodoWrite tool to track progress

### After Crashes
1. Don't panic - state is preserved
2. Check documentation first
3. Verify services are running
4. Resume from last known good state

---

**Remember**: The system is designed to be crash-resilient. Your work is preserved in:
- Git commits
- Database state
- Documentation files
- Session state tracking

**Next Steps After Recovery**:
1. Resume work: `@CURRENT_SESSION_STATE.md Resume my last session`
2. Complete task: `@TASK_COMPLETION_GUIDE.md Update all documentation`
3. Start new task: `@TASK_INITIATION_GUIDE.md I'm starting task [TASK_ID]`