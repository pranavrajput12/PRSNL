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
- **Windsurf**: [Role to be defined]
- **Cursor**: Minor edits and quick fixes (assigned via GitHub issues)

## Core Principles

### 1. Git as Single Source of Truth
- All work must be performed within the repository
- No external code or modifications outside the repo
- All decisions and implementations must be tracked in git history

### 2. Branch Strategy
- **Main/Master**: Production-ready code only
- **Feature Branches**: One branch per task/feature
- **Naming Convention**: `feature/<task-description>` or `fix/<issue-description>`
- **No Direct Commits**: Never commit directly to main/master

### 3. Commit Standards
- **Format**: Follow [Conventional Commits](https://www.conventionalcommits.org/)
- **Types**: feat, fix, docs, style, refactor, test, chore
- **Example**: `feat: add user authentication system`
- **Body**: Include detailed description when necessary

## Workflow Rules

### Before Starting Any Task
1. **Always** run `git pull --rebase` to sync with latest changes
2. Review all open Pull Requests to avoid duplicate work
3. Check GitHub issues for assigned tasks
4. Create a new feature branch from main/master

### During Development
1. Make atomic commits with clear messages
2. Run all tests before committing
3. Ensure pre-commit hooks pass
4. Use repo-relative paths for all cross-file references
5. Document complex logic inline when necessary

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
- **Minor Edits**: Created as GitHub issues and assigned to Cursor
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