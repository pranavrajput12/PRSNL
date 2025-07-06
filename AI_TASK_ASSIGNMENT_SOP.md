# Standard Operating Procedure for AI Task Assignment

## Overview
This SOP ensures seamless collaboration between multiple AI agents using isolated workspaces to prevent conflicts.

## Pre-Task Setup (Human Operator)

### 1. Pull Latest Changes
```bash
cd /Users/pronav/Personal\ Knowledge\ Base
git pull origin main
```

### 2. Prepare AI Workspace
```bash
# For Windsurf
rm -rf workspaces/windsurf/PRSNL  # Clean old workspace
cp -r PRSNL workspaces/windsurf/   # Copy fresh project

# For Gemini
rm -rf workspaces/gemini/PRSNL    # Clean old workspace
cp -r PRSNL workspaces/gemini/     # Copy fresh project
```

## Task Assignment Template

Copy and paste this exact template when assigning tasks:

```
=== TASK ASSIGNMENT ===

WORKSPACE: /workspaces/[windsurf|gemini]/PRSNL/
DO NOT WORK IN THE MAIN /PRSNL/ FOLDER!

TASK: [Specific task description]

DELIVERABLES:
1. [Specific file or feature]
2. [Another deliverable]

CONSTRAINTS:
- Work ONLY in your designated workspace
- Do NOT navigate to /Personal Knowledge Base/PRSNL/
- Do NOT push to GitHub
- Do NOT create git branches

WHEN COMPLETE:
1. Create /workspaces/[your-name]/PRSNL/CHANGES.md with:
   - List of files created
   - List of files modified
   - Summary of changes
   - Setup/testing instructions
2. Tell me "TASK COMPLETE - ready for review"

IMPORTANT: Your workspace is a complete isolated copy. All your changes stay there until I review and merge them.
```

## Post-Task Review Process (Human + Claude Code)

### 1. Ask AI for Completion Status
```
Have you completed the task and created CHANGES.md?
```

### 2. Review Changes with Claude Code
```
Claude, please review the work in /workspaces/[ai-name]/PRSNL/:
1. Check CHANGES.md
2. Review code quality
3. Test if possible
4. Merge approved changes to main PRSNL
```

### 3. Claude Code Merges
Claude will:
- Review all changes
- Copy approved files to main PRSNL
- Commit with proper attribution
- Clean up the workspace

## Quick Reference Commands

### Setup Windsurf Workspace
```bash
rm -rf workspaces/windsurf/PRSNL && cp -r PRSNL workspaces/windsurf/
```

### Setup Gemini Workspace
```bash
rm -rf workspaces/gemini/PRSNL && cp -r PRSNL workspaces/gemini/
```

### Check Windsurf's Work
```bash
ls workspaces/windsurf/PRSNL/CHANGES.md
cat workspaces/windsurf/PRSNL/CHANGES.md
```

### Check Gemini's Work
```bash
ls workspaces/gemini/PRSNL/CHANGES.md
cat workspaces/gemini/PRSNL/CHANGES.md
```

## Common Issues & Solutions

### Issue: AI tries to access main PRSNL folder
**Solution**: Remind them:
```
STOP! You must work in /workspaces/[your-name]/PRSNL/ not in the main folder.
Your workspace is at: /workspaces/[windsurf|gemini]/PRSNL/
```

### Issue: AI tries to use git
**Solution**: Tell them:
```
No git operations needed. Just work in your workspace and create CHANGES.md when done.
```

### Issue: AI is confused about the workspace
**Solution**: Clarify:
```
Your workspace /workspaces/[your-name]/PRSNL/ is a complete copy of the project.
Work there as if it's the real project. I'll handle merging your changes.
```

## Example Task Flow

### 1. Human assigns task to Windsurf:
```bash
# Prepare workspace
rm -rf workspaces/windsurf/PRSNL && cp -r PRSNL workspaces/windsurf/
```

Then tells Windsurf:
```
=== TASK ASSIGNMENT ===
WORKSPACE: /workspaces/windsurf/PRSNL/
TASK: Create a settings page for the frontend
[rest of template]
```

### 2. Windsurf works and creates:
- `/workspaces/windsurf/PRSNL/frontend/src/routes/settings/+page.svelte`
- `/workspaces/windsurf/PRSNL/CHANGES.md`

### 3. Human asks Claude Code:
```
Please review Windsurf's settings page in /workspaces/windsurf/PRSNL/
```

### 4. Claude Code reviews and merges:
```bash
# Copy approved files
cp workspaces/windsurf/PRSNL/frontend/src/routes/settings/+page.svelte PRSNL/frontend/src/routes/settings/

# Commit
git add PRSNL/frontend/src/routes/settings/
git commit -m "feat: add settings page

Created by Windsurf in isolated workspace
Reviewed and merged by Claude Code"
```

## Benefits of This System

1. **Zero Conflicts**: AIs can't interfere with each other
2. **Clean Git History**: Only reviewed code enters main branch
3. **Easy Rollback**: Can discard entire workspace if needed
4. **Parallel Work**: Multiple AIs work simultaneously
5. **Quality Control**: Everything reviewed before merging

## Remember

- Always prepare fresh workspace before tasks
- Never let AIs work in main PRSNL folder
- Always review through Claude Code before merging
- Clean up workspaces after merging