# TASK HANDOFF - Video Integration Phase

## 🎯 Current Objective
Enhance and optimize the newly implemented Instagram video download feature across all components of PRSNL.

## 📍 Current State Summary
- ✅ Basic video download working (Instagram only)
- ✅ Database schema updated for videos
- ✅ VideoPlayer component created
- ✅ Backend processing implemented
- 🚧 Needs UI enhancements
- 🚧 Needs backend optimization
- 🚧 Needs additional platform support

---

## 🌊 WINDSURF - Frontend Tasks

### Your Context
- Frontend runs on **port 3002** (NOT in Docker)
- API proxy configured to backend at localhost:8000
- Manchester United red theme (#dc143c) must be maintained
- VideoPlayer component exists but needs enhancement

### Your Tasks (in order)
1. **Read these files first**:
   - `/WINDSURF_TASKS.md` - Your detailed tasks
   - `/PRSNL/frontend/src/lib/components/VideoPlayer.svelte`
   - `/SESSION_CONTINUITY.md` - Project state

2. **Enhance Video Display** (Task: WINDSURF-2025-07-06-001)
   - Test current VideoPlayer component
   - Add loading states
   - Implement lazy loading
   - Add keyboard controls

3. **Update Capture Page** (Task: WINDSURF-2025-07-06-002)
   - Detect video URLs
   - Show video preview
   - Add video-specific options

4. **After each task**: Update `/MODEL_ACTIVITY_LOG.md`

### DO NOT
- Use git commands
- Modify backend code
- Change the port configuration

---

## ♊ GEMINI - Backend Tasks

### Your Context
- Backend runs in Docker container
- Videos stored at `/app/media/` inside container
- yt-dlp already configured for Instagram
- Database has video support schema

### Your Tasks (in order)
1. **Read these files first**:
   - `/GEMINI_TASKS.md` - Your detailed tasks
   - `/PRSNL/backend/app/services/video_processor.py`
   - `/SESSION_CONTINUITY.md` - Project state

2. **Optimize Video Processing** (Task: GEMINI-2025-07-06-001)
   - Add format validation
   - Implement compression
   - Add retry logic
   - Extract metadata

3. **Create Storage Management** (Task: GEMINI-2025-07-06-002)
   - Implement quota system
   - Add cleanup procedures
   - Create storage metrics

4. **After each task**: Update `/MODEL_ACTIVITY_LOG.md`

### DO NOT
- Use git commands
- Modify frontend code
- Change Docker ports

---

## 🤖 CLAUDE - Review Process

After Windsurf and Gemini complete their tasks, I will:

1. **Review all changes**
   - Check MODEL_ACTIVITY_LOG.md
   - Verify no conflicts
   - Test integration points

2. **Merge and integrate**
   - Combine all changes
   - Resolve any conflicts
   - Update documentation

3. **Create single commit**
   - With comprehensive message
   - Listing all contributors
   - Documenting all changes

---

## 📋 Quick Reference

### File Locations
```
Frontend (Windsurf):
/PRSNL/frontend/src/lib/components/VideoPlayer.svelte
/PRSNL/frontend/src/routes/timeline/+page.svelte
/PRSNL/frontend/src/routes/capture/+page.svelte

Backend (Gemini):
/PRSNL/backend/app/services/video_processor.py
/PRSNL/backend/app/api/capture.py
/PRSNL/backend/app/db/migrations/002_add_video_support.sql
```

### Key Commands
```bash
# Start all services (run from project root)
cd /Users/pronav/Personal Knowledge Base/PRSNL
make dev

# Frontend dev (Windsurf)
cd frontend && npm run dev  # Runs on port 3002

# Check backend logs (Gemini)
docker compose logs backend -f
```

### Testing URLs
- Frontend: http://localhost:3002
- Backend Health: http://localhost:8000/health
- Capture Test: http://localhost:3002/capture

---

## 🔄 Workflow

1. **Windsurf** works on frontend enhancements
2. **Gemini** works on backend optimization
3. Both update MODEL_ACTIVITY_LOG.md
4. **Claude** reviews and merges everything
5. Single clean commit to git

## ⚠️ Important Notes
- Work can be done in parallel (no dependencies between Windsurf and Gemini tasks)
- Always check existing code before making changes
- Maintain the existing design system and patterns
- Test your changes thoroughly
- Document any issues or blockers