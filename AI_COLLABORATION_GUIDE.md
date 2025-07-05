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

### 3. Branch Strategy
- **Main/Master**: Production-ready code only
- **Feature Branches**: One branch per task/feature
- **Naming Convention**: `feature/<task-description>` or `fix/<issue-description>`
- **No Direct Commits**: Never commit directly to main/master

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

### Branch Naming Requirements
- Claude Code: `feat/cc-*`, `fix/cc-*`, `refactor/cc-*`
- Windsurf: `feat/ws-*`, `scaffold/ws-*`, `refactor/ws-*`
- Gemini CLI: `fix/gc-*`, `chore/gc-*`

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

### Progress Update Commands
```bash
# Before any work
git pull --rebase
# Edit PROGRESS_TRACKER.md
git add PROGRESS_TRACKER.md
git commit -m "chore: update progress - starting [task]"
git push
```

## Workflow Rules

### Before Starting Any Task
1. **Always** run `git pull --rebase` to sync with latest changes
2. **CHECK PROGRESS_TRACKER.md** for active work and file locks
3. Review all open Pull Requests to avoid duplicate work
4. Check GitHub issues for assigned tasks
5. Update PROGRESS_TRACKER.md with your task
6. Create a new feature branch from main/master

### During Development
1. Update PROGRESS_TRACKER.md every 30 minutes
2. Make atomic commits with clear messages
3. Run all tests before committing
4. Ensure pre-commit hooks pass
5. Use repo-relative paths for all cross-file references
6. Document complex logic inline when necessary

### Submitting Work
1. Push feature branch to remote
2. Create Pull Request with:
   - Clear title following conventional commit format
   - Detailed description of changes
   - "Generated-by: [AI-Agent-Name]" in description
   - Link to related issue (if applicable)
3. Ensure all CI/CD checks pass
4. Mark PR as ready for review only after all tests pass

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
├── .github/
│   ├── workflows/      # CI/CD pipelines
│   └── ISSUE_TEMPLATE/ # Issue templates
├── docs/               # Project documentation
├── src/                # Source code
├── tests/              # Test files
├── .gitignore
├── README.md
└── AI_COLLABORATION_GUIDE.md
```

## Prohibited Actions
- ❌ Direct commits to main/master
- ❌ Force pushing to shared branches
- ❌ Modifying git history on shared branches
- ❌ Working outside the repository
- ❌ Ignoring pre-commit hook failures
- ❌ Creating PRs without running tests
- ❌ Modifying other AI agent's active branches

## Getting Started Checklist
- [ ] Clone the repository
- [ ] Set up pre-commit hooks
- [ ] Verify test suite runs successfully
- [ ] Read existing documentation
- [ ] Check open issues and PRs
- [ ] Create your first feature branch

---

*This document is the authoritative guide for all AI collaboration. Any updates must be reviewed and approved through the standard PR process.*