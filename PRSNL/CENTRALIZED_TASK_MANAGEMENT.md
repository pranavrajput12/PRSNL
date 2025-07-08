# 📊 CENTRALIZED TASK MANAGEMENT

## 🎯 Overview
This document defines the centralized task management system for all AI models working on PRSNL.

## 📁 Key Files and Their Purpose

### 1. **PROJECT_STATUS.md** (Main Reference)
- **Purpose**: Current system state and high-level status
- **Updated By**: All models
- **When**: After major changes or milestones
- **Path**: `/PRSNL/PROJECT_STATUS.md`

### 2. **CONSOLIDATED_TASK_TRACKER.md**
- **Purpose**: Detailed task history and completion tracking
- **Updated By**: Model completing the task
- **When**: When starting and completing tasks
- **Path**: `/PRSNL/CONSOLIDATED_TASK_TRACKER.md`

### 3. **MODEL_ACTIVITY_LOG.md**
- **Purpose**: Daily activity log and real-time updates
- **Updated By**: Active model
- **When**: During work sessions
- **Path**: `/PRSNL/MODEL_ACTIVITY_LOG.md`

### 4. Model-Specific Task Files
- **CLAUDE_TASKS.md**: Complex features and integration work
- **WINDSURF_TASKS.md**: Simple frontend UI tasks
- **GEMINI_TASKS.md**: Simple backend scripts and tests

## 📋 Task Allocation Process

### Step 1: Check Current Status
```bash
# Claude checks before starting work
1. Read PROJECT_STATUS.md - Understand system state
2. Read MODEL_ACTIVITY_LOG.md - Check for active work
3. Read your specific task file (e.g., CLAUDE_TASKS.md)
```

### Step 2: Claim a Task
```markdown
# In CONSOLIDATED_TASK_TRACKER.md, update:
### Task CLAUDE-2025-01-08-001: [Task Name]
**Status**: IN PROGRESS
**Started**: 2025-01-08 14:30
**Assigned**: Claude
```

### Step 3: Log Activity
```markdown
# In MODEL_ACTIVITY_LOG.md, add:
### 2025-01-08 - Claude
#### [Task Name] (CLAUDE-2025-01-08-001)
- **14:30**: Started work on feature X
- **14:45**: Fixed issue Y in file Z
- **15:00**: Completed implementation
```

### Step 4: Complete Task
```markdown
# In CONSOLIDATED_TASK_TRACKER.md:
**Status**: COMPLETED
**Completed**: 2025-01-08 15:00

# In your task file, move to completed section
```

## 🚦 Task Priority System

### Priority Levels
- **🔴 CRITICAL**: System breaking, chat/search not working
- **🟡 HIGH**: Important features, user-requested items
- **🟢 MEDIUM**: Enhancements, optimizations
- **⚪ LOW**: Nice-to-have, UI polish

### Task Assignment by Model

#### Claude (Complex Tasks)
- All CRITICAL issues
- System architecture changes
- API design and implementation
- Complex bug fixes
- Integration work
- AI feature implementation

#### Windsurf (Simple Frontend)
- UI styling updates
- Add tooltips and hover states
- Update loading spinners
- Format timestamps
- Add icons
- Simple component creation

#### Gemini (Simple Backend)
- Write unit tests
- Create data scripts
- Add logging
- Generate documentation
- Database backup scripts
- Performance metrics collection

## 📝 Task ID Format
```
[MODEL]-[YYYY-MM-DD]-[###]

Examples:
CLAUDE-2025-01-08-001
WINDSURF-2025-01-08-001
GEMINI-2025-01-08-001
```

## 🔄 Handoff Protocol

When handing off work:
```markdown
## Handoff: Claude → Windsurf
**Date**: 2025-01-08 15:00
**Task**: Add loading states to search page
**Status**: Backend API complete, needs UI work
**Files**: 
- Backend: /api/search.py (complete)
- Frontend: /routes/search/+page.svelte (needs work)
**Notes**: API returns loading status in response.status field
```

## ⚠️ Conflict Prevention

### File Locking
```markdown
# In MODEL_ACTIVITY_LOG.md:
🔒 LOCKED by Claude: /backend/app/main.py (14:30-15:00)
```

### Check Before Editing
```bash
# Search for locked files
grep "LOCKED" MODEL_ACTIVITY_LOG.md
```

## 📊 Weekly Cleanup

Every week, archive old completed tasks:
1. Move completed tasks older than 7 days to archive section
2. Clear old entries from MODEL_ACTIVITY_LOG.md
3. Update summary statistics in PROJECT_STATUS.md

## 🚫 Deprecated Files

The following files are no longer used:
- `/docs/progress/MODEL_TASK_TRACKER.md` (use CONSOLIDATED_TASK_TRACKER.md)
- Individual progress files (consolidated into central tracking)
- Temporary handoff files (use MODEL_ACTIVITY_LOG.md)

## ✅ Quick Reference

### For Claude
1. Check: PROJECT_STATUS.md → MODEL_ACTIVITY_LOG.md → CLAUDE_TASKS.md
2. Work on: Complex features, bugs, integration
3. Update: All three tracking files

### For Windsurf
1. Check: PROJECT_STATUS.md → WINDSURF_TASKS.md
2. Work on: Simple UI tasks from your list
3. Update: CONSOLIDATED_TASK_TRACKER.md when done

### For Gemini
1. Check: PROJECT_STATUS.md → GEMINI_TASKS.md
2. Work on: Simple backend tasks from your list
3. Update: CONSOLIDATED_TASK_TRACKER.md when done