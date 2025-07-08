# 🤝 MODEL COORDINATION RULES FOR PRSNL

## 🚨 CRITICAL: PORT ALLOCATION

### ⚠️ PORT MANAGEMENT HAS MOVED
**See `/PRSNL/PORT_ALLOCATION.md` for the complete port allocation guide**

This document now focuses on model coordination rules only. For all port assignments, conflict prevention, and troubleshooting, refer to the centralized port allocation document.

### Quick Reference
- **Frontend**: Port 3002 (FIXED)
- **Backend**: Port 8000
- **Full Details**: `/PRSNL/PORT_ALLOCATION.md`

### Port Conflict Resolution Protocol
1. **BEFORE STARTING ANY SERVICE**:
   ```bash
   # Check if port is in use
   lsof -i :3002 | grep LISTEN
   ```

2. **IF PORT IS OCCUPIED**:
   - DO NOT kill the process
   - Notify in MODEL_ACTIVITY_LOG.md
   - Wait for the other model to complete
   - OR coordinate via user

## 📋 TASK ALLOCATION

### Model Specialization (Updated 2025-01-08)
- **🎨 CLAUDE**: Frontend, Backend, Integration, Complex Features
  - All critical path development
  - Complex AI integrations
  - System architecture decisions
  - Bug fixes and debugging
  - API design and implementation
  
- **🚀 WINDSURF**: Simple Frontend Tasks
  - CSS styling adjustments
  - Simple component creation
  - Icon/asset management
  - UI polish tasks
  - Documentation formatting
  
- **🧠 GEMINI**: Simple Backend Tasks
  - Test writing
  - Data migration scripts
  - Log analysis
  - Performance metrics collection
  - Simple CRUD endpoints

### Task Handoff Protocol
1. Update MODEL_ACTIVITY_LOG.md with:
   - Task ID
   - Status (IN PROGRESS → COMPLETED)
   - Files modified
   - Next steps

2. Create clear boundaries:
   ```
   WINDSURF working on: /frontend/src/routes/capture/+page.svelte
   CLAUDE working on: /backend/app/api/capture.py
   ```

## 🔄 Real-time Coordination

### File Lock System
When working on a file:
1. Add to MODEL_ACTIVITY_LOG.md:
   ```markdown
   🔒 LOCKED by CLAUDE: /backend/app/main.py (15:45-16:00)
   ```

2. Check before editing:
   ```bash
   grep -n "LOCKED" MODEL_ACTIVITY_LOG.md
   ```

### Shared Resources
- **Docker Compose**: Only ONE model should run docker commands at a time
- **Database Migrations**: Sequential, never parallel
- **Package Installation**: Coordinate npm/pip installs

## 📝 Communication Protocol

### Status Updates
Every 15 minutes or major milestone:
```markdown
## CLAUDE Status Update - 15:45
- ✅ Fixed timeline API response format
- 🔄 Working on video player integration
- ⏰ ETA: 10 minutes
```

### Handoff Messages
```markdown
## Handoff: CLAUDE → WINDSURF
- Backend API ready at /api/videos
- Returns: {items: [], total: 0, page: 1}
- Frontend needs to handle new format
```

## 🚦 Priority System

### Demo/Production Critical
1. 🔴 **P0**: Demo breaking bugs (fix within 5 min)
2. 🟡 **P1**: Feature completion (fix within 15 min)
3. 🟢 **P2**: Enhancements (schedule for later)

### Conflict Resolution
1. User decides priority
2. P0 always wins
3. Document decision in MODEL_ACTIVITY_LOG.md

## 🛡️ Safety Rules

### Never Do
- ❌ Kill another model's process without permission
- ❌ Force push to git
- ❌ Delete files without checking ownership
- ❌ Change ports from assigned values

### Always Do
- ✅ Check MODEL_ACTIVITY_LOG.md before starting
- ✅ Update status immediately when done
- ✅ Test changes before handoff
- ✅ Leave clean, working code

## 📊 Progress Tracking

### Task Board Format
```markdown
| Model    | Task                  | Status      | ETA   |
|----------|----------------------|-------------|-------|
| CLAUDE   | Fix timeline API     | ✅ DONE     | -     |
| WINDSURF | Video player UI      | 🔄 PROGRESS | 10min |
| GEMINI   | Monitoring setup     | ⏳ QUEUED   | 20min |
```

## 🔧 Emergency Procedures

### If Everything Breaks
1. Stop all Docker containers:
   ```bash
   docker compose down
   ```
2. Reset to last known good state
3. Coordinate recovery in MODEL_ACTIVITY_LOG.md

### Demo Emergency
- Focus on P0 issues only
- Skip non-critical features
- Ensure core flow works

---

**Remember**: We're a team! 🤖🤝🤖🤝🤖