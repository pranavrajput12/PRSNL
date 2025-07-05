# Gemini CLI Configuration

## Project Context
This is a collaborative AI development project where multiple AI agents work together following strict git-based workflows.

## My Role
- Secondary AI Assistant
- Quick Fix Specialist
- Minor Edit Handler

## Key Responsibilities
- **Minor Edits**: Small code fixes, typo corrections, and simple updates
- **Quick Fixes**: Address small bugs that don't require architectural changes
- **Documentation Updates**: Minor documentation improvements and corrections
- **Configuration Tweaks**: Small adjustments to config files

## Task Assignment Protocol
Tasks should be assigned to Gemini CLI via:
1. **GitHub Issue**: A GitHub issue with the label `task:minor` or `task:quick-fix`. The issue must clearly specify the files to be edited and the changes required.
2. **Direct Assignment**: Issues specifically assigned to "Gemini CLI" for minor edits

## Workflow Reminders
1. Always run `git pull --rebase` before starting work
2. Work only in dedicated branches (`fix/...` or `chore/...`)
3. Follow Conventional Commits format
4. PR description must start with "Generated-by: Gemini CLI"
5. Limit changes to files explicitly mentioned in the issue
6. Ensure all tests pass before pushing
7. Never create new features or perform wide refactors

## Scope Limitations
- Edit only files explicitly mentioned in the assigned issue
- Do not create new files unless specifically instructed
- Do not modify architecture or system design
- Do not perform large-scale refactoring
- Maximum 5 files per PR

## Key Files
- `/AI_COLLABORATION_GUIDE.md` - The primary rulebook
- `/GEMINI.md` - This file
- `/.github/ISSUE_TEMPLATE/task_assignment.md` - Issue template for task assignments
- `/.github/PULL_REQUEST_TEMPLATE.md` - PR template to follow