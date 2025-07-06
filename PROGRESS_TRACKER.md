# Progress Tracker

> **CRITICAL**: This file is the single source of truth for all active work. ALL AI agents MUST update this file when starting, progressing, or completing tasks.

> **NEW WORKSPACE PROTOCOL**: All AI work now happens in isolated workspaces at `/workspaces/[ai-name]/`
> See AI_WORKSPACE_PROTOCOL.md for details. NO DIRECT EDITS to main PRSNL folder!

## Active Tasks

### Format
Each task entry must follow this structure:
```markdown
### [TASK-ID] Task Title
- **Status**: [PLANNING | IN_PROGRESS | REVIEW | COMPLETED | BLOCKED]
- **Assigned to**: [Claude Code | Windsurf | Gemini CLI]
- **Branch**: `branch-name`
- **Started**: YYYY-MM-DD HH:MM
- **Last Updated**: YYYY-MM-DD HH:MM
- **Files Being Modified**:
  - `/path/to/file1.ext` (status: editing/complete)
  - `/path/to/file2.ext` (status: editing/complete)
- **Blockers**: Any blocking issues
- **Sub-tasks**:
  - [ ] Sub-task 1 (Owner: AI-Name)
  - [ ] Sub-task 2 (Owner: AI-Name)
```

---

## In Progress

### [VAULT-001] Knowledge Vault - Initial Architecture & Setup
- **Status**: IN_PROGRESS
- **Assigned to**: Claude Code (Lead)
- **Branch**: `feat/cc-vault-architecture`
- **Started**: 2025-01-06 10:00
- **Last Updated**: 2025-01-06 10:30
- **Files Being Modified**:
  - `/docs/ARCHITECTURE.md` (status: complete)
  - `/docs/IMPLEMENTATION_PLAN.md` (status: complete)
  - `/README.md` (status: complete)
  - `/PRSNL/` directory structure (status: in progress)
- **Sub-tasks**:
  - [x] Design local-first architecture (Owner: Claude Code)
  - [x] Document system components (Owner: Claude Code)
  - [x] Define database schema (Owner: Claude Code)
  - [ ] Create project structure (Owner: Windsurf - Issue #TBD)
  - [ ] Scaffold FastAPI backend (Owner: Windsurf - Issue #TBD)
  - [ ] Scaffold SvelteKit frontend (Owner: Windsurf - Issue #TBD)
  - [ ] Set up Docker Compose (Owner: Claude Code)
  - [ ] Implement capture API (Owner: Claude Code)
  - [ ] Create browser extension (Owner: Windsurf - Issue #TBD)

## Completed Today

<!-- Move completed tasks here at end of day -->

## Task Queue

### Backend Development
- [ ] Implement scraper service with BeautifulSoup
- [ ] Set up Celery task queue
- [ ] Integrate Ollama for local LLM
- [ ] Create search orchestrator
- [ ] Implement pgvector hybrid search

### Frontend Development  
- [ ] Design keyboard-first UI
- [ ] Implement global hotkey overlay
- [ ] Create command palette
- [ ] Build focus reader mode

### Infrastructure
- [ ] Configure PostgreSQL with pgvector
- [ ] Set up Redis for caching
- [ ] Create backup scripts
- [ ] Write deployment documentation

---

## Update Protocol

### Before Starting Work
1. Check this file for conflicts
2. Add your task with status: PLANNING
3. List ALL files you intend to modify
4. Commit and push this update

### During Work
1. Update status to IN_PROGRESS
2. Mark files as "editing" when you start
3. Update "Last Updated" timestamp
4. Commit progress updates every 30 minutes

### After Completing Work
1. Mark files as "complete"
2. Update status to REVIEW or COMPLETED
3. Move to "Completed Today" section
4. Commit final update

### Conflict Detection
- NEVER start work on files marked as "editing" by another agent
- If you see conflicting work, update status to BLOCKED
- Create a GitHub issue tagged `conflict-detected`

## Task Breakdown Rules

### When Claude Code receives a complex task:
1. Break it into sub-tasks
2. Assign ownership:
   - Architecture & Design → Claude Code
   - Scaffolding & Multi-file generation → Windsurf
   - Minor fixes & tweaks → Gemini CLI
3. Create detailed specifications for each sub-task
4. Update this tracker with the full breakdown

### Example Task Breakdown:
```markdown
### [TASK-001] Implement User Authentication System
- **Status**: IN_PROGRESS
- **Assigned to**: Claude Code (Lead)
- **Branch**: `feat/cc-user-auth`
- **Started**: 2024-01-15 10:00
- **Last Updated**: 2024-01-15 10:30
- **Files Being Modified**:
  - `/docs/auth-architecture.md` (status: complete)
- **Sub-tasks**:
  - [x] Design authentication architecture (Owner: Claude Code)
  - [ ] Scaffold auth module structure (Owner: Windsurf)
  - [ ] Implement JWT tokens (Owner: Claude Code)
  - [ ] Create login/signup endpoints (Owner: Windsurf)
  - [ ] Add input validation (Owner: Gemini CLI)
  - [ ] Write authentication tests (Owner: Claude Code)
```

---

## Automation Notes

- This file should be updated via git commits
- Each AI must pull latest before reading
- Each AI must push immediately after updating
- Consider this file locked while any agent is updating it

## Emergency Protocol

If this file becomes corrupted or conflicts arise:
1. Stop all work immediately
2. Create backup: `cp PROGRESS_TRACKER.md PROGRESS_TRACKER.backup.md`
3. Notify human operator
4. Wait for manual resolution