# AI Collaboration Guide

## Overview
This document serves as the definitive rulebook for AI agents collaborating on this project. All AI contributors must follow these guidelines to ensure seamless collaboration and code quality.

## AI Agents & Roles

### Primary AI Builder #1: Claude Code
- **Role**: Architect, Story Writer, Complex Feature Lead
- **Responsibilities**:
  - System architecture decisions
  - Complex feature implementation
  - Code reviews and quality assurance
  - Delegation of minor tasks via GitHub issues
- **Identifier**: All commits and PRs must include "Generated-by: Claude-Code"

### Supporting AI Agents
- **Windsurf**: Scaffolding specialist and large-scale code generation/refactoring engine. See [WINDSURF.md](WINDSURF.md) for details.
- **Gemini CLI**: Minor edits and quick fixes (assigned via GitHub issues). See [GEMINI.md](GEMINI.md) for details.

## Core Principles

### 1. Strict Agent Boundaries
- **No agent shall modify another agent's active work**
- **Each agent must reject out-of-scope tasks**
- **See [BOUNDARIES.md](BOUNDARIES.md) for detailed conflict prevention**
- **When in doubt: REJECT and ESCALATE**

### 2. Git as Single Source of Truth
- All work must be performed within the repository
- No external code or modifications outside the repo
- All decisions and implementations must be tracked in git history
- **IMPORTANT**: Only Claude Code performs Git operations
- Windsurf & Gemini make local changes only

### 3. Branch Strategy (Claude Code Only)
- **Main**: Production-ready code only
- **Simplified Workflow**: All work happens on main branch
- **No Feature Branches**: Since only Claude commits, branching is unnecessary
- **Linear History**: Clean, simple commit history

### 4. Commit Standards
- **Format**: Follow [Conventional Commits](https://www.conventionalcommits.org/)
- **Types**: feat, fix, docs, style, refactor, test, chore
- **Example**: `feat: add user authentication system`
- **Body**: Include detailed description when necessary

## Fail-Safe Mechanisms

### Task Validation Requirements
1. Check for active PRs: `gh pr list --state open`
2. Verify no conflicting branches: `git branch -a | grep -E "(cc-|ws-|gc-)"`
3. Validate task scope matches assigned role
4. Reject tasks that overlap with other agents' work

### Git Operation Requirements
- **Claude Code**: Handles ALL git operations (add, commit, push, pull)
- **Windsurf**: Local file changes only, NO git commands
- **Gemini CLI**: Local file changes only, NO git commands

## Task Breakdown Protocol

### Complex Task Handling
When receiving a complex task, Claude Code must:
1. Analyze the full scope of work required
2. Break down into discrete sub-tasks
3. Assign each sub-task to appropriate AI agent:
   - **Claude Code**: Architecture, complex logic, system design
   - **Windsurf**: Scaffolding, multi-file generation, large refactors
   - **Gemini CLI**: Minor fixes, small updates, documentation tweaks
4. Create GitHub issues for delegated tasks
5. Update PROGRESS_TRACKER.md with complete breakdown

### Task Delegation Example
```
User Request: "Build a user authentication system"
↓
Claude Code breaks down into:
1. Design auth architecture (Claude Code)
2. Create auth module structure (Windsurf via issue)
3. Implement core auth logic (Claude Code)
4. Generate CRUD endpoints (Windsurf via issue)
5. Fix any linting issues (Gemini CLI via issue)
```

## Progress Tracking Requirements

### All AI Agents MUST:
1. **Before Starting**: Update PROGRESS_TRACKER.md with task details
2. **During Work**: Update progress every 30 minutes
3. **File Locking**: Mark files as "editing" to prevent conflicts
4. **After Completion**: Update status and move to completed section

### Progress Update Protocol
- **Windsurf/Gemini**: Update PROGRESS_TRACKER.md locally
- **Claude Code**: Commits and pushes all progress updates
- **No Git commands** for Windsurf/Gemini

## Workflow Rules

### Before Starting Any Task

#### For Claude Code:
1. **Always** run `git pull` to sync with latest changes
2. Check PROGRESS_TRACKER.md for active work
3. Review recent commits
4. Plan task breakdown

#### For Windsurf/Gemini:
1. Wait for task assignment from human
2. Work in local files only
3. Create TASK_SUMMARY.md when complete
4. NO git operations

### During Development
1. Update PROGRESS_TRACKER.md every 30 minutes
2. Make atomic commits with clear messages
3. Run all tests before committing
4. Ensure pre-commit hooks pass
5. Use repo-relative paths for all cross-file references
6. Document complex logic inline when necessary

### Submitting Work

#### For Windsurf/Gemini:
1. Save all files locally
2. Create TASK_SUMMARY.md listing changes
3. Tell human "Task complete"
4. Wait for Claude Code to review and commit

#### For Claude Code:
1. Review local changes with `git status` and `git diff`
2. Test changes if possible
3. Commit with clear message including attribution
4. Push directly to main branch

## Quality Standards

### Code Quality
- All unit tests must pass
- Pre-commit hooks must pass
- Code must follow project's style guide
- No hardcoded values or secrets
- Proper error handling required

### Documentation
- Update README when adding new features
- Document API changes
- Include JSDoc/docstrings for public functions
- Update this guide when workflow changes

## Communication Protocol

### Task Assignment
- **Complex Features**: Assigned directly to Claude Code
- **Minor Edits**: Created as GitHub issues and assigned to Gemini CLI
- **Bug Fixes**: Assigned based on complexity

### Conflict Resolution
1. Git conflicts must be resolved locally before pushing
2. If uncertain about architectural decisions, create an issue for discussion
3. Never force push to shared branches

## File Structure Guidelines
```
project-root/
├── PRSNL/              # Main application
│   ├── backend/        # FastAPI application
│   ├── frontend/       # SvelteKit UI
│   ├── extension/      # Browser extension
│   ├── docker/         # Docker configs
│   ├── scripts/        # Utility scripts
│   └── tests/          # Test suites
├── docs/               # Project documentation
│   ├── ARCHITECTURE.md
│   └── IMPLEMENTATION_PLAN.md
├── .github/
│   ├── workflows/      # CI/CD pipelines
│   └── ISSUE_TEMPLATE/ # Issue templates
├── AI_COLLABORATION_GUIDE.md
├── PROGRESS_TRACKER.md
└── README.md
```

## Prohibited Actions

### For ALL AI Agents:
- ❌ Working outside the repository
- ❌ Modifying files without task assignment
- ❌ Creating conflicts with other agents' work

### For Windsurf/Gemini Specifically:
- ❌ ANY git commands (add, commit, push, pull, etc.)
- ❌ Creating or switching branches
- ❌ Viewing git history or status

### For Claude Code:
- ❌ Committing without reviewing
- ❌ Force pushing
- ❌ Modifying git history

## Getting Started Checklist
- [ ] Clone the repository
- [ ] Set up pre-commit hooks
- [ ] Verify test suite runs successfully
- [ ] Read existing documentation
- [ ] Check open issues and PRs
- [ ] Create your first feature branch

---

*This document is the authoritative guide for all AI collaboration. Any updates must be reviewed and approved through the standard PR process.*