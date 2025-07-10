# 🚀 Task Initiation Master Guide

## 📋 Always @ This File When Starting Any Task

This is your single source of truth for starting tasks properly. Use these prompts:

### 🎯 Simple Task Prompts
```bash
# Just describe what you want built:
@TASK_INITIATION_GUIDE.md Build [FEATURE_DESCRIPTION]

# Examples:
@TASK_INITIATION_GUIDE.md Build a user authentication system
@TASK_INITIATION_GUIDE.md Build a video upload feature
@TASK_INITIATION_GUIDE.md Build a search filter component
@TASK_INITIATION_GUIDE.md Build a chat interface
@TASK_INITIATION_GUIDE.md Build an admin dashboard

@TASK_INITIATION_GUIDE.md Fix the video player not loading
@TASK_INITIATION_GUIDE.md Fix search returning empty results
@TASK_INITIATION_GUIDE.md Fix database connection errors

@TASK_INITIATION_GUIDE.md Improve the loading performance
@TASK_INITIATION_GUIDE.md Improve error handling
@TASK_INITIATION_GUIDE.md Improve UI responsiveness
```

### ⚠️ CRITICAL ENVIRONMENT INFO
- **Container Runtime**: RANCHER DESKTOP (NOT Docker)
- **Frontend Port**: 3003 (Updated from 3002)
- **Backend Port**: 8000
- **DO NOT**: Use docker commands, start Docker Desktop, or suggest Docker rebuilds

### 🏗️ MANDATORY: System Architecture Repository
**BEFORE STARTING ANY FEATURE DEVELOPMENT:**
- **MUST READ**: `/docs/SYSTEM_ARCHITECTURE_REPOSITORY.md`
- **PURPOSE**: Contains API patterns, database schemas, frontend templates
- **RULE**: ALL new features must follow the established patterns
- **PREVENTS**: Breaking existing functionality and repetitive issues

### 🤖 What AI Will Do Automatically
When you tag this file, the AI will:
1. **Read Context Documentation**: Check all required files for full context
2. **Check CLAUDE.md**: Read critical project configuration (Rancher, ports, etc.)
2. **Generate Task ID**: Create unique task identifier
3. **Update CURRENT_SESSION_STATE.md**: Set active task and status
4. **Update TASK_HISTORY.md**: Add task with IN PROGRESS status
5. **Check Conflicts**: Verify no other tasks are active
6. **Identify Files**: Determine which files will be modified
7. **Run Pre-checks**: Verify system health
8. **Start Work**: Begin implementing the feature

### 📚 Required Context Documentation
**AI must read these files before starting any task:**
- **`PROJECT_STATUS.md`** - Current system state and capabilities
- **`AI_COORDINATION_COMPLETE.md`** - AI roles and responsibilities
- **`ARCHITECTURE.md`** - System architecture and patterns
- **`API_DOCUMENTATION.md`** - API contracts and endpoints
- **`TASK_HISTORY.md`** - Recent task history and active work
- **`QUICK_REFERENCE_COMPLETE.md`** - System commands and procedures
- **`DOCUMENTATION_DEPENDENCIES.md`** - Impact matrix for updates
- **`PORT_ALLOCATION.md`** - Port assignments and conflict prevention
- **`PROJECT_STRUCTURE.md`** - File organization and project layout
- **`FRONTEND_SETUP.md`** - Frontend development environment
- **`backend/docs/DATABASE_SCHEMA.md`** - Database structure and schema

---

## ⚡ Quick Start Checklist

### 1. Task Registration (REQUIRED)
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

### 2. Conflict Prevention (REQUIRED)
```bash
# Check for conflicts:
- Review "IN PROGRESS" tasks in TASK_HISTORY.md
- Verify no file locks in AI_COORDINATION_COMPLETE.md
- Check port availability: lsof -i :3002,8000,5433
- Ensure no other AI is working on same files
```

### 3. Impact Assessment (REQUIRED)
Use the matrix below to identify which files will need updates when task completes.

### 4. Resource Lock (IF NEEDED)
```markdown
# Add to TASK_HISTORY.md if editing critical files:
🔒 LOCKED by [AI]: /path/to/file.py ([start_time]-[estimated_end])
```

---

## 📊 Task Type Impact Matrix

### 🎨 Frontend Tasks (Windsurf)
**Typical Changes**: UI components, styling, simple interactions
**Files to Update on Completion**:
- ✅ `TASK_HISTORY.md` (status update)
- ⚠️ `PROJECT_STATUS.md` (if major UI changes)
- ⚠️ `QUICK_REFERENCE_COMPLETE.md` (if new commands/procedures)

**Sanity Checks Required**:
```bash
npm run dev -- --port 3002  # Verify frontend starts
curl http://localhost:3002/  # Verify accessible
npm run check               # TypeScript validation
```

**Example Tasks**:
- Update loading spinners
- Add hover effects
- Format timestamps
- Add empty state messages

### 🔧 Backend API Tasks (Claude)
**Typical Changes**: API endpoints, business logic, integrations
**Files to Update on Completion**:
- ✅ `TASK_HISTORY.md` (status update)
- ✅ `API_DOCUMENTATION.md` (new/changed endpoints)
- ✅ `PROJECT_STATUS.md` (system state changes)
- ✅ `QUICK_REFERENCE_COMPLETE.md` (new commands/endpoints)
- ⚠️ `AI_COORDINATION_COMPLETE.md` (if workflow changes)

**Sanity Checks Required**:
```bash
curl http://localhost:8000/health    # Backend health
curl http://localhost:8000/docs      # API docs accessible
pytest -v                          # Run tests
```

**Example Tasks**:
- Create new API endpoints
- Fix web scraping issues
- Implement AI services
- Database schema changes

### 💾 Database Tasks (Claude/Gemini)
**Typical Changes**: Schema, queries, migrations
**Files to Update on Completion**:
- ✅ `TASK_HISTORY.md` (status update)
- ✅ `DATABASE_SCHEMA.md` (schema changes)
- ✅ `QUICK_REFERENCE_COMPLETE.md` (new DB commands)
- ⚠️ `PROJECT_STATUS.md` (if major schema changes)

**Sanity Checks Required**:
```bash
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "SELECT version();"
psql "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl" -c "SELECT COUNT(*) FROM items;"
```

**Example Tasks**:
- Add new database columns
- Create indexes
- Database backup scripts
- Migration scripts

### 🤖 AI Service Tasks (Claude)
**Typical Changes**: AI integrations, LLM services, embeddings
**Files to Update on Completion**:
- ✅ `TASK_HISTORY.md` (status update)
- ✅ `AI_COORDINATION_COMPLETE.md` (AI workflow changes)
- ✅ `PROJECT_STATUS.md` (system capabilities)
- ✅ `QUICK_REFERENCE_COMPLETE.md` (new AI commands)
- ⚠️ `API_DOCUMENTATION.md` (if new AI endpoints)

**Sanity Checks Required**:
```bash
curl -X POST http://localhost:8000/api/ai-suggest -H "Content-Type: application/json" -d '{"url": "https://example.com"}'
# Test specific AI service endpoints
```

**Example Tasks**:
- Azure OpenAI integration
- Embedding service implementation
- Vision AI processing
- Web scraping improvements

### 🧠 Simple Backend Tasks (Gemini)
**Typical Changes**: Scripts, utilities, tests
**Files to Update on Completion**:
- ✅ `TASK_HISTORY.md` (status update)
- ⚠️ `QUICK_REFERENCE_COMPLETE.md` (if new scripts/commands)

**Sanity Checks Required**:
```bash
python3 scripts/[script_name].py  # Test script execution
pytest tests/[test_file].py       # Run new tests
```

**Example Tasks**:
- Test data generation scripts
- Database backup scripts
- Health check endpoints
- Unit tests

### 📚 Documentation Tasks (Claude)
**Typical Changes**: Documentation updates, guides, references
**Files to Update on Completion**:
- ✅ `TASK_HISTORY.md` (status update)
- ✅ Relevant documentation files
- ⚠️ `PROJECT_STATUS.md` (if major doc restructure)

**Sanity Checks Required**:
```bash
# Verify links work, formatting is correct
# Check for broken references
```

---

## 🎯 Task Dependency Templates

### Simple Task Template
```markdown
## Task: [TASK_ID] - [Task Name]
**Type**: [Frontend/Backend/Database/AI Service/Documentation]
**Assigned**: [AI Name]
**Dependencies**: None
**Files to Modify**: [List files that will be changed]
**Files to Update Post-Completion**: [Use impact matrix above]
**Estimated Time**: [time]
**Sanity Checks**: [Use commands from impact matrix]
```

### Complex Task Template
```markdown
## Task: [TASK_ID] - [Task Name]
**Type**: [Frontend/Backend/Database/AI Service/Documentation]
**Assigned**: [AI Name]
**Dependencies**: 
- Depends on: [TASK_ID] (must complete first)
- Blocks: [TASK_ID] (prevents this from starting)
**Files to Modify**: [List files that will be changed]
**Files to Update Post-Completion**: [Use impact matrix above]
**Estimated Time**: [time]
**Sanity Checks**: [Use commands from impact matrix]
**Coordination Needed**: [Yes/No - if Yes, specify with whom]
```

---

## 🔄 Pre-Task Verification Script

```bash
#!/bin/bash
# Copy this to QUICK_REFERENCE_COMPLETE.md for easy access

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

## 📋 Common Task Patterns

### Pattern 1: Frontend UI Polish (Windsurf)
```markdown
**Before Starting**:
- Check no other frontend tasks in progress
- Verify frontend is running on port 3002
- Ensure no TypeScript errors: npm run check

**During Task**:
- Make only visual/styling changes
- Don't modify API calls or business logic
- Test in browser immediately

**Files to Update After**:
- TASK_HISTORY.md (status)
- Usually no other files needed
```

### Pattern 2: Backend API Development (Claude)
```markdown
**Before Starting**:
- Check no conflicting backend tasks
- Verify backend is running on port 8000
- Review API_DOCUMENTATION.md for existing patterns

**During Task**:
- Follow existing architectural patterns
- Add proper error handling
- Write/update tests

**Files to Update After**:
- TASK_HISTORY.md (status)
- API_DOCUMENTATION.md (new endpoints)
- PROJECT_STATUS.md (system changes)
- QUICK_REFERENCE_COMPLETE.md (new commands)
```

### Pattern 3: Database Changes (Claude/Gemini)
```markdown
**Before Starting**:
- Backup database if major changes
- Check no other database tasks in progress
- Verify database connection

**During Task**:
- Test changes on small dataset first
- Use transactions for safety
- Document schema changes

**Files to Update After**:
- TASK_HISTORY.md (status)
- DATABASE_SCHEMA.md (schema changes)
- QUICK_REFERENCE_COMPLETE.md (new DB commands)
```

---

## 🚨 Critical Reminders

### Always Do This:
1. **Tag this file** when starting any task
2. **Add to TASK_HISTORY.md** with IN PROGRESS status
3. **Check for conflicts** before starting
4. **Identify impact** using the matrix above
5. **Run sanity checks** to verify system is healthy

### Never Do This:
1. **Start without documentation** - Always update TASK_HISTORY.md first
2. **Work on locked files** - Check for file locks
3. **Skip impact assessment** - Know what needs updating
4. **Ignore dependencies** - Check if other tasks are blocked
5. **Change ports** - Use assigned ports only

### If You're Blocked:
1. **STOP** - Don't proceed with conflicting work
2. **Document** in TASK_HISTORY.md: "BLOCKED: [reason]"
3. **Notify** through user communication
4. **Wait** for resolution before continuing

---

## 🎯 Success Metrics

### Task Initiation Success:
- [ ] Task properly documented in TASK_HISTORY.md
- [ ] Impact assessment completed
- [ ] No conflicts with other tasks
- [ ] Sanity checks passed
- [ ] Dependencies identified

### Common Failure Points:
- Starting without checking conflicts
- Not identifying all files that need updates
- Skipping sanity checks
- Not documenting dependencies
- Working on locked files

---

**Remember**: This guide prevents documentation fragmentation by ensuring every task starts with proper planning and impact assessment. When combined with the Task Completion Guide, it creates a complete lifecycle management system.

**Next Step**: When task is complete, always use `@TASK_COMPLETION_GUIDE.md I completed task [TASK_ID], here's what changed: [SUMMARY]`