# AI Agents Overview

## Active AI Agents

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

## Task Assignment Guidelines

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

## Collaboration Protocol

### 1. Task Assignment
Human assigns task to appropriate AI based on the guidelines above.

### 2. Execution
- Windsurf/Gemini: Make local changes, create TASK_SUMMARY.md
- Claude Code: Implement directly, handle Git operations

### 3. Integration
- Human asks Claude Code to review and commit work from other AIs
- Claude Code reviews, tests, and pushes to GitHub

### 4. Verification
- Human or Claude Code verifies the implementation
- Any fixes go through the same workflow

## Communication Standards

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

## Important Reminders

### For ALL AI Agents:
1. Stay within your assigned scope
2. Document your work clearly
3. Test locally when possible
4. Ask for clarification if needed

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