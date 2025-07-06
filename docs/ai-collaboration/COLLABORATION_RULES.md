# AI Collaboration Rules & Boundaries

## Core Principle: NO OVERLAPPING WORK

With our simplified workflow (only Claude Code uses Git), conflicts are minimal. However, we still maintain clear boundaries to ensure smooth collaboration.

## File Ownership Rules

### Exclusive Ownership Zones

#### Claude Code Owns:
```
PRSNL/
├── backend/
│   ├── app/
│   │   ├── core/           # Business logic
│   │   ├── services/       # Service layer
│   │   ├── api/           # API endpoints (logic)
│   │   └── main.py        # App configuration
├── docs/                   # All documentation
└── Root config files       # .gitignore, README.md, etc.
```

#### Windsurf Owns:
```
PRSNL/
├── frontend/              # All SvelteKit files
│   └── src/
├── extension/             # Browser extension
├── overlay/               # Desktop overlay app
└── Any UI-related files
```

#### Gemini CLI Owns:
```
PRSNL/
├── backend/
│   ├── app/
│   │   └── db/           # Database files
│   │       └── *.sql     # SQL schemas/migrations
│   └── requirements.txt   # Python dependencies
├── docker-compose.yml     # Docker configuration
├── Dockerfile             # Container definitions
├── scripts/               # Utility scripts
└── Infrastructure files
```

### Shared Files

These files require coordination:
- `PRSNL/backend/app/config.py` - Settings (PRIMARY: Claude, REVIEW: Gemini)
- `PRSNL/Makefile` - Build commands (ALL can contribute)
- `PROGRESS_TRACKER.md` - Task tracking (ALL must update)

## Task Validation Rules

### Before Starting ANY Task:

1. **Check Ownership**: Verify you own the files you'll modify
2. **Check Progress Tracker**: Ensure no one else is working on those files
3. **Validate Scope**: Ensure task matches your role

### If You Need to Modify Another AI's File:

1. **STOP** - Don't proceed
2. **Document** in TASK_SUMMARY.md:
   ```
   BLOCKED: Need to modify [file] owned by [AI]
   Reason: [why you need to change it]
   Suggested change: [what should be changed]
   ```
3. **Wait** for human to coordinate

## Conflict Prevention

### File Locking via Progress Tracker

When starting work:
```markdown
### [TASK-001] Task Name
- **Status**: IN_PROGRESS
- **Assigned to**: [Your Name]
- **Files Being Modified**:
  - `/path/to/file1.ext` (status: editing)
  - `/path/to/file2.ext` (status: editing)
```

When done:
```markdown
- **Files Being Modified**:
  - `/path/to/file1.ext` (status: complete)
  - `/path/to/file2.ext` (status: complete)
```

### Conflict Detection

If you find someone else is editing a file you need:
1. Check PROGRESS_TRACKER.md
2. If confirmed conflict, STOP
3. Add to your TASK_SUMMARY.md:
   ```
   CONFLICT: [Other AI] is editing [file]
   My task needs: [what you need to change]
   ```

## Boundary Enforcement

### Hard Boundaries (NEVER Cross):
- Windsurf NEVER touches backend logic
- Gemini NEVER modifies frontend components
- Only Claude Code touches documentation
- NO AI except Claude uses Git

### Soft Boundaries (Need Permission):
- Config files (coordinate through human)
- Shared utilities (propose in TASK_SUMMARY.md)
- Cross-boundary features (break into parts)

## Communication Protocols

### Status Updates
All AIs must update PROGRESS_TRACKER.md:
- When starting a task
- Every 30 minutes during work
- When completing a task
- When encountering blockers

### Handoff Protocol
When work needs to transfer between AIs:
1. First AI completes their part
2. Documents in TASK_SUMMARY.md what's done and what's needed
3. Human coordinates handoff to next AI
4. Second AI continues from clear starting point

## Examples

### Good Task Division:
**Task**: Add user settings page

- **Windsurf**: Create settings UI components
- **Gemini**: Add settings table to database
- **Claude**: Create settings API and integrate

### Bad Task Assignment:
❌ "Windsurf, add user settings feature" (too broad, crosses boundaries)
❌ "Gemini, update the UI colors" (outside Gemini's domain)
❌ "Claude, create everything" (not utilizing team properly)

## Quality Standards

### All AIs Must:
1. Follow existing code patterns
2. Maintain consistent style
3. Add appropriate error handling
4. Test locally when possible
5. Document complex logic

### Review Criteria (Claude Code):
- Code follows project standards
- No security vulnerabilities
- Proper error handling
- Tests pass (when applicable)
- Documentation updated

## Emergency Protocols

### If Boundaries Are Violated:
1. Claude Code detects during review
2. Reverts problematic changes
3. Re-assigns to correct AI
4. Updates boundaries if needed

### If Severe Conflict:
1. All AIs stop work
2. Human intervenes
3. Claude Code resolves Git state
4. Work resumes with clarified boundaries

## Summary

The key to successful collaboration:
1. **Know your lane** - Work within your ownership zone
2. **Communicate clearly** - Document everything in TASK_SUMMARY.md
3. **Respect boundaries** - Don't modify others' files
4. **Track progress** - Keep PROGRESS_TRACKER.md updated
5. **No Git operations** - Unless you're Claude Code

These rules ensure smooth, conflict-free collaboration!