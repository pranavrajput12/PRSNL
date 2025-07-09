# AI Collaboration Guide for PRSNL

## 🚀 Quick Start for AI Agents

### If you're Windsurf or Gemini CLI:
1. **Read This First**: You do NOT use Git commands - just edit files
2. **When Done**: Create TASK_SUMMARY.md in the project root
3. **Core Rule**: Work within your assigned domain only

### If you're Claude Code:
1. You handle ALL Git operations
2. Review and commit work from other AIs
3. Maintain code quality and documentation

## 📋 Active AI Agents & Their Roles

### 1. Claude Code (Architecture & Review Lead)
**Role**: System architect, code reviewer, Git operations handler

**Responsibilities**:
- System architecture and design decisions
- Complex feature implementation
- Code review for all changes
- ALL Git operations (add, commit, push, pull)
- Task breakdown and delegation
- Integration of other AIs' work

**Capabilities**:
- Full codebase access and modification
- Git operations
- Complex reasoning and planning
- Cross-file refactoring
- Testing and validation

**Recent Accomplishments** (2025-01-07):
- Implemented 5 major AI features in one session
- Created Smart Categorization, Duplicate Detection services
- Built Content Summarization with digests
- Implemented Knowledge Graph with AI discovery
- Created Video Streaming with transcript analysis
- Updated all documentation comprehensively

**Typical Tasks**:
- Design new features
- Implement complex business logic
- Review and merge code from other AIs
- Create and update documentation
- Handle Git operations and conflicts

### 2. Windsurf (Frontend & Scaffolding Specialist)
**Role**: UI/UX implementation, large-scale code generation

**Responsibilities**:
- Frontend development (SvelteKit)
- Browser extension development
- Component creation and styling
- Large-scale scaffolding
- Multi-file generation

**Capabilities**:
- Rapid UI prototyping
- Component library creation
- Consistent styling across files
- Large refactoring operations
- File tree manipulation

**Typical Tasks**:
- Create new pages/routes
- Build UI components
- Implement browser extensions
- Scaffold new modules
- Create consistent component sets

**Constraints**:
- NO Git operations
- Works on local files only
- Must create TASK_SUMMARY.md

### 3. Gemini CLI (Backend & Quick Fixes)
**Role**: Backend implementation, infrastructure, small fixes

**Responsibilities**:
- Backend API development
- Database operations
- Docker configuration
- Infrastructure setup
- Quick bug fixes

**Capabilities**:
- Python/FastAPI development
- SQL and database design
- Docker and deployment configs
- Script creation
- Small targeted fixes

**Typical Tasks**:
- Create API endpoints
- Write database migrations
- Update Docker configurations
- Fix linting issues
- Create utility scripts

**Constraints**:
- NO Git operations
- Works on local files only
- Must create TASK_SUMMARY.md

## 🎯 Task Assignment Guidelines

### Best AI for the Task

#### Choose Claude Code for:
- Architecture decisions
- Complex algorithms
- Cross-cutting concerns
- Integration work
- Code review
- Git operations

#### Choose Windsurf for:
- New UI pages
- Component libraries
- Browser extensions
- Large-scale scaffolding
- Frontend refactoring
- Consistent UI updates

#### Choose Gemini CLI for:
- API endpoints
- Database changes
- Docker updates
- Bug fixes
- Configuration changes
- Utility scripts

## 🔄 Current Workflow (Simplified)

> **This is our current workflow as of January 2025**

### Core Principle
- **Other AIs** (Windsurf, Gemini): Make local changes only, NO Git operations
- **Claude Code**: Reviews all changes and handles ALL Git operations

### Why This Approach?
1. **Zero Conflicts**: Only one AI (Claude) touches Git
2. **Simple Mental Model**: Others just edit files
3. **Clean History**: All commits reviewed and properly attributed
4. **No Branch Confusion**: Linear history on main branch
5. **Easy Recovery**: Claude can always `git reset` if needed

### Workflow Steps

#### 1. Task Assignment (Human → AI)
```
TASK: [Description]

IMPORTANT:
- Make your changes in the PRSNL folder
- Do NOT use any git commands
- Do NOT push/pull/commit
- Just save your files locally
- Tell me when you're done

Create a file called TASK_SUMMARY.md listing:
1. What you built
2. Files you created/modified
3. Any setup needed
```

#### 2. AI Completes Work
- AI makes changes to files
- AI creates TASK_SUMMARY.md
- AI reports: "Task complete - ready for review"

#### 3. Review Process (Human → Claude)
```
[AI name] just completed [task description].
Please:
1. Review their changes using git status/diff
2. Test if possible
3. Commit with appropriate message
4. Push to GitHub
```

#### 4. Claude Code's Git Workflow
```bash
# Check what changed
git status
git diff

# Review changes
# Test functionality

# Commit if good
git add [files]
git commit -m "feat: [description]

Implemented by: [Windsurf/Gemini]
Reviewed by: Claude Code"

# Push
git push origin main
```

## 🛡️ Collaboration Rules & Boundaries

### Core Principle: NO OVERLAPPING WORK
With our simplified workflow (only Claude Code uses Git), conflicts are minimal. However, we still maintain clear boundaries to ensure smooth collaboration.

### File Ownership Rules

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

### Hard Boundaries (NEVER Cross):
- Windsurf NEVER touches backend logic
- Gemini NEVER modifies frontend components
- Only Claude Code touches documentation
- NO AI except Claude uses Git

### Soft Boundaries (Need Permission):
- Config files (coordinate through human)
- Shared utilities (propose in TASK_SUMMARY.md)
- Cross-boundary features (break into parts)

## 📝 Communication Standards

### Task Summary Format (for Windsurf/Gemini)
```markdown
# Task Summary

## Task Description
[What was requested]

## Changes Made
### Files Created:
- `/path/to/new/file1.ext` - [Purpose]
- `/path/to/new/file2.ext` - [Purpose]

### Files Modified:
- `/path/to/modified/file.ext` - [What changed]

## Setup/Testing Instructions
[Any special steps needed]

## Notes
[Any important observations or decisions made]
```

### Commit Message Format (Claude Code only)
```
type: brief description

Detailed explanation if needed.

Implemented by: [AI Name]
Reviewed by: Claude Code
```

## 🚦 Rules by Role

### For Windsurf & Gemini CLI
✅ **DO**:
- Edit and save files locally
- Create new files as needed
- Update existing files
- Create TASK_SUMMARY.md when done
- Test your changes locally if possible
- Follow existing code patterns
- Maintain consistent style
- Add appropriate error handling

❌ **DON'T**:
- Use ANY git commands (add, commit, push, pull, status, diff, log, etc.)
- Create or switch branches
- Look at git history
- Create pull requests
- Worry about merge conflicts
- Modify files outside your ownership zone
- Cross boundaries without permission

### For Claude Code
✅ **DO**:
- Pull latest before reviewing
- Review all changes carefully
- Test changes when possible
- Commit with clear messages
- Attribute work properly in commits
- Push to main after committing
- Handle any Git issues that arise
- Maintain code quality standards

❌ **DON'T**:
- Commit without reviewing
- Force push (unless absolutely necessary)
- Modify git history on main
- Skip attribution in commits

## 🎯 Example Task Flows

### Frontend Task Example
1. **Human**: "Windsurf, please add a help page showing keyboard shortcuts"
2. **Windsurf**: Creates `/frontend/src/routes/help/+page.svelte` and `TASK_SUMMARY.md`
3. **Human**: "Claude, please review and commit Windsurf's help page"
4. **Claude**: Reviews, tests, commits with proper attribution, pushes

### Backend Task Example
1. **Human**: "Gemini, please add Redis caching to the search endpoint"
2. **Gemini**: Modifies search.py, updates docker-compose.yml, creates `TASK_SUMMARY.md`
3. **Human**: "Claude, please review Gemini's caching implementation"
4. **Claude**: Reviews code, ensures it works, commits, pushes

### Good Task Division Example:
**Task**: Add user settings page
- **Windsurf**: Create settings UI components
- **Gemini**: Add settings table to database
- **Claude**: Create settings API and integrate

### Bad Task Assignment Examples:
❌ "Windsurf, add user settings feature" (too broad, crosses boundaries)
❌ "Gemini, update the UI colors" (outside Gemini's domain)
❌ "Claude, create everything" (not utilizing team properly)

## 🔧 Conflict Prevention & Resolution

### If You Need to Modify Another AI's File:
1. **STOP** - Don't proceed
2. **Document** in TASK_SUMMARY.md:
   ```
   BLOCKED: Need to modify [file] owned by [AI]
   Reason: [why you need to change it]
   Suggested change: [what should be changed]
   ```
3. **Wait** for human to coordinate

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

## 📊 Benefits of This Approach

1. **Dead Simple**: No complex workspace management
2. **No Conflicts**: Only Claude handles Git
3. **Clear History**: All commits go through Claude's review
4. **No Branch Confusion**: Everything on main, linear history
5. **Easy Recovery**: Can always `git reset` if needed
6. **Quality Control**: All code reviewed before commit
7. **Clear Attribution**: Always know who implemented what

## 🎯 Key Points Summary

1. **Simple Workflow**: Only Claude Code uses Git
2. **Clear Ownership**: Each AI has specific domains
3. **Shared Task Summary**: One TASK_SUMMARY.md for all AIs
4. **No Conflicts**: Since only one AI handles Git
5. **Know your lane**: Work within your ownership zone
6. **Communicate clearly**: Document everything in TASK_SUMMARY.md
7. **Respect boundaries**: Don't modify others' files
8. **Quality first**: Follow project standards and patterns

## 📍 Important Reminders

### For ALL AI Agents:
1. Stay within your assigned scope
2. Document your work clearly
3. Test locally when possible
4. Ask for clarification if needed
5. Follow existing code patterns
6. Maintain consistent style
7. Add appropriate error handling

### For Windsurf & Gemini:
1. **NEVER** use Git commands
2. Always create TASK_SUMMARY.md
3. Work in local files only
4. Report completion clearly

### For Claude Code:
1. Review carefully before committing
2. Always attribute work in commits
3. Handle all Git operations
4. Maintain code quality standards

**This simplified workflow ensures smooth, conflict-free collaboration while maintaining high code quality and clear attribution!**