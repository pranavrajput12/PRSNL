# Task Ownership Matrix

## File/Directory Ownership Rules

### Exclusive Ownership Zones

#### Claude Code (Architecture Lead)
```
PRSNL/
├── backend/
│   ├── app/
│   │   ├── core/           # EXCLUSIVE: Claude
│   │   ├── services/       # EXCLUSIVE: Claude
│   │   └── api/           # EXCLUSIVE: Claude (API logic only)
├── docs/                   # EXCLUSIVE: Claude
├── AI_COLLABORATION_GUIDE.md
├── BOUNDARIES.md
├── PROGRESS_TRACKER.md
└── TASK_OWNERSHIP.md       # This file
```

#### Windsurf (Frontend & Extensions)
```
PRSNL/
├── frontend/              # EXCLUSIVE: Windsurf
│   └── src/
├── extension/             # EXCLUSIVE: Windsurf
├── mobile/                # EXCLUSIVE: Windsurf (future)
└── desktop/               # EXCLUSIVE: Windsurf (future)
```

#### Gemini CLI (Infrastructure & Database)
```
PRSNL/
├── backend/
│   ├── app/
│   │   └── db/
│   │       └── *.sql      # EXCLUSIVE: Gemini (SQL files only)
│   └── alembic/           # EXCLUSIVE: Gemini (migrations)
├── docker-compose.yml     # EXCLUSIVE: Gemini
├── Dockerfile             # EXCLUSIVE: Gemini
├── .env.example           # EXCLUSIVE: Gemini
├── nginx/                 # EXCLUSIVE: Gemini
└── scripts/               # SHARED: Gemini primary, others can add
```

### Shared Files (Require Coordination)
```
PRSNL/
├── backend/
│   ├── requirements.txt   # PRIMARY: Claude, REVIEW: Gemini
│   └── app/
│       └── main.py        # PRIMARY: Claude, REVIEW: Gemini
├── Makefile               # PRIMARY: Claude, CONTRIBUTIONS: All
└── README.md              # PRIMARY: Claude, CONTRIBUTIONS: All
```

## Task Assignment Protocol

### Before Starting Any Task:

1. **Check Ownership**: Verify you own the files you'll modify
2. **Declare Intent**: Update PROGRESS_TRACKER.md with:
   - Exact files you'll create/modify
   - Expected completion time
3. **Check Conflicts**: Ensure no other AI is working on those files

### If You Need to Modify Another AI's File:

1. **Create a Proposal**: 
   ```markdown
   PROPOSAL: Need to modify [file] owned by [AI]
   REASON: [specific reason]
   CHANGES: [exact changes needed]
   ```

2. **Wait for Approval**: Human will coordinate

### Task Types by Owner:

#### Claude Code Tasks:
- API endpoint logic
- Business logic implementation  
- Search algorithms
- LLM integration
- Documentation updates
- Architecture decisions

#### Windsurf Tasks:
- UI/UX implementation
- Frontend routing
- Browser extension features
- Component creation
- Frontend state management
- CSS/styling

#### Gemini CLI Tasks:
- Database schema changes
- Docker configuration
- Infrastructure setup
- Database migrations
- Deployment scripts
- Performance optimization

## Conflict Resolution

### If Overlap Detected:
1. **STOP IMMEDIATELY**
2. **Report in PROGRESS_TRACKER.md**:
   ```markdown
   CONFLICT DETECTED:
   - File: [filename]
   - My changes: [description]
   - Other AI: [name]
   - Resolution needed: [suggestion]
   ```

### Prevention Rules:
1. **Never** create files outside your ownership zone without approval
2. **Always** check git status before starting work
3. **Always** pull latest changes before starting
4. **Never** assume a file is unclaimed - check ownership first

## Example Task Breakdown:

### Task: "Add user authentication"

**Claude Code**:
- Create `backend/app/core/auth.py` (auth logic)
- Create `backend/app/api/auth.py` (API endpoints)
- Update `backend/app/models/schemas.py` (auth schemas)

**Windsurf**:
- Create `frontend/src/routes/login/+page.svelte`
- Create `frontend/src/lib/stores/auth.ts`
- Update `frontend/src/routes/+layout.svelte` (auth check)

**Gemini CLI**:
- Create `backend/app/db/migrations/001_add_users_table.sql`
- Update `docker-compose.yml` (if needed for auth service)
- Create `scripts/create_admin.py`

## File Creation Protocol:

Before creating ANY new file:

1. Check if directory exists in ownership matrix
2. If not listed, ask for ownership assignment
3. If shared directory, declare intent first
4. Create file only after confirmation

This prevents the overlap issues we just experienced!