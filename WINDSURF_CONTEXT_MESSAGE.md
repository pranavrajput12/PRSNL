# WINDSURF CONTEXT MESSAGE

## 🚨 IMPORTANT: New Task Tracking System

Before starting any work, you MUST understand our new model activity logging system:

1. **Read MODEL_ACTIVITY_LOG.md** - This tracks ALL work done by each AI model
2. **Read TASK_HANDOFF.md** - Quick overview of current tasks
3. **Read WINDSURF_TASKS.md** - Your specific tasks with IDs

## Your Workflow:
1. When starting a task, update MODEL_ACTIVITY_LOG.md with status "IN PROGRESS"
2. Track all files you modify
3. When done, update MODEL_ACTIVITY_LOG.md with status "COMPLETED"
4. Never use git commands - only update the log

## Current State:
- Frontend runs on port 3002 (NOT in Docker)
- Video support was just added by Claude
- Your job: Enhance the video UI/UX

## Example Log Entry:
```markdown
### 2025-07-06 Session
**Task ID**: WINDSURF-2025-07-06-001  
**Description**: Video display enhancement  
**Files Modified**:
- `/PRSNL/frontend/src/lib/components/VideoPlayer.svelte` (updated)
- `/PRSNL/frontend/src/routes/timeline/+page.svelte` (updated)
**Status**: ✅ COMPLETED
```

Start with WINDSURF-2025-07-06-001 from WINDSURF_TASKS.md!