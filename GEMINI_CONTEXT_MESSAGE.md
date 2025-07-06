# GEMINI CONTEXT MESSAGE

## 🚨 IMPORTANT: New Task Tracking System

Before starting any work, you MUST understand our new model activity logging system:

1. **Read MODEL_ACTIVITY_LOG.md** - This tracks ALL work done by each AI model
2. **Read TASK_HANDOFF.md** - Quick overview of current tasks
3. **Read GEMINI_TASKS.md** - Your specific tasks with IDs

## Your Workflow:
1. When starting a task, update MODEL_ACTIVITY_LOG.md with status "IN PROGRESS"
2. Track all files you modify
3. When done, update MODEL_ACTIVITY_LOG.md with status "COMPLETED"
4. Never use git commands - only update the log

## Current State:
- Backend runs in Docker on port 8000
- Video support was just added by Claude using yt-dlp
- Your job: Optimize video processing and add storage management

## Example Log Entry:
```markdown
### 2025-07-06 Session
**Task ID**: GEMINI-2025-07-06-001  
**Description**: Video processing optimization  
**Files Modified**:
- `/PRSNL/backend/app/services/video_processor.py` (updated)
- `/PRSNL/backend/app/core/background_tasks.py` (created)
**Status**: ✅ COMPLETED
```

Start with GEMINI-2025-07-06-001 from GEMINI_TASKS.md!