# Simplified AI Workflow

## Core Principle
- **Other AIs**: Make local changes only, NO Git operations
- **Claude Code**: Reviews all changes and handles ALL Git operations

## Simple Workflow

### 1. Task Assignment (Human to Windsurf/Gemini)
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

### 2. Review Process (Human to Claude)
```
Windsurf/Gemini just completed [task description].
Please:
1. Review their changes using git status/diff
2. Test if possible
3. Commit with appropriate message
4. Push to GitHub
```

### 3. Claude Code's Git Workflow
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

## Benefits of This Approach

1. **Dead Simple**: No complex workspace management
2. **No Conflicts**: Only Claude handles Git
3. **Clear History**: All commits go through Claude's review
4. **No Branch Confusion**: Everything on main, linear history
5. **Easy Recovery**: Can always `git reset` if needed

## Task Assignment Templates

### For UI/Frontend Tasks (Windsurf)
```
Please create [UI component/page] in the PRSNL/frontend folder.

Requirements:
- [Requirement 1]
- [Requirement 2]

Don't use git. Just save files and tell me when done.
Create TASK_SUMMARY.md with what you built.
```

### For Backend/Infra Tasks (Gemini)
```
Please create [backend feature] in the PRSNL/backend folder.

Requirements:
- [Requirement 1]
- [Requirement 2]

Don't use git. Just save files and tell me when done.
Create TASK_SUMMARY.md with what you built.
```

## Important Rules

### For Windsurf/Gemini:
1. **NEVER** use git commands
2. **NEVER** create branches
3. **NEVER** push/pull/commit
4. Just edit and save files
5. Create TASK_SUMMARY.md when done

### For Claude Code:
1. **ALWAYS** review before committing
2. **ALWAYS** test if possible
3. **ALWAYS** attribute work in commit message
4. **ALWAYS** push after committing

## Handling Conflicts

Since only Claude uses Git, conflicts are minimal. If they occur:

1. Claude detects during review
2. Claude resolves before committing
3. Claude might ask human for clarification
4. Clean commit after resolution

## Example Flow

### 1. Human to Windsurf:
```
Please add a help page to the frontend showing keyboard shortcuts.
Don't use git, just create the files.
```

### 2. Windsurf creates:
- `PRSNL/frontend/src/routes/help/+page.svelte`
- `TASK_SUMMARY.md`

### 3. Human to Claude:
```
Windsurf added a help page. Please review and commit.
```

### 4. Claude:
```bash
git status
# sees new file

git diff
# reviews code

git add PRSNL/frontend/src/routes/help/+page.svelte
git commit -m "feat: add help page with keyboard shortcuts

Implemented by: Windsurf
Reviewed by: Claude Code"

git push origin main
```

## This Eliminates

- ❌ Complex workspace isolation
- ❌ Branch management
- ❌ Merge conflicts between AIs
- ❌ Permission issues
- ❌ Sync problems

## This Ensures

- ✅ Single source of truth
- ✅ Clean Git history  
- ✅ Code review on everything
- ✅ Simple mental model
- ✅ Easy to understand and follow

Much simpler!