# Simplified AI Workflow

> **This is our current workflow as of January 2025**

## Core Principle
- **Other AIs** (Windsurf, Gemini): Make local changes only, NO Git operations
- **Claude Code**: Reviews all changes and handles ALL Git operations

## Why This Approach?
1. **Zero Conflicts**: Only one AI (Claude) touches Git
2. **Simple Mental Model**: Others just edit files
3. **Clean History**: All commits reviewed and properly attributed
4. **No Branch Confusion**: Linear history on main branch
5. **Easy Recovery**: Claude can always `git reset` if needed

## Workflow Steps

### 1. Task Assignment (Human → AI)
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

### 2. AI Completes Work
- AI makes changes to files
- AI creates TASK_SUMMARY.md
- AI reports: "Task complete - ready for review"

### 3. Review Process (Human → Claude)
```
[AI name] just completed [task description].
Please:
1. Review their changes using git status/diff
2. Test if possible
3. Commit with appropriate message
4. Push to GitHub
```

### 4. Claude Code's Git Workflow
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

## Rules by Role

### For Windsurf & Gemini CLI
✅ **DO**:
- Edit and save files locally
- Create new files as needed
- Update existing files
- Create TASK_SUMMARY.md when done
- Test your changes locally if possible

❌ **DON'T**:
- Use ANY git commands (add, commit, push, pull, status, diff, log, etc.)
- Create or switch branches
- Look at git history
- Create pull requests
- Worry about merge conflicts

### For Claude Code
✅ **DO**:
- Pull latest before reviewing
- Review all changes carefully
- Test changes when possible
- Commit with clear messages
- Attribute work properly in commits
- Push to main after committing
- Handle any Git issues that arise

❌ **DON'T**:
- Commit without reviewing
- Force push (unless absolutely necessary)
- Modify git history on main
- Skip attribution in commits

## Example Task Flows

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

## Common Questions

**Q: What if I need to see what files exist?**
A: Use file system commands (ls, find, etc.), not git commands

**Q: What if I need to know what something does?**
A: Read the files directly, check comments, or ask for clarification

**Q: What if I make a mistake?**
A: Just fix it locally. Claude will review everything before committing

**Q: What if files conflict with my changes?**
A: Make your changes anyway. Claude will handle conflicts during review

## Summary
This workflow is intentionally simple. If you're not Claude Code, just:
1. Edit files
2. Save files
3. Document what you did
4. Say "done"

That's it! No Git complexity, no branch management, no merge conflicts.