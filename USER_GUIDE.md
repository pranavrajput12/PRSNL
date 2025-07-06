# User Guide: Working with Multiple AI Agents

## 🚀 Quick Start: Initiating Tasks

### The Golden Rule
**Never give the same files to multiple AIs simultaneously.** Use PROGRESS_TRACKER.md as your coordination hub.

## 📋 Task Initiation Workflow

### Step 1: Define Your Task
Before engaging any AI, clearly define:
- What needs to be built/fixed
- Which files will be affected
- Expected outcome

### Step 2: Choose Your Approach

#### Approach A: **Sequential Delegation** (Safest)
Give one task to one AI at a time:
```
You → Claude Code → (wait for PR) → Windsurf → (wait for PR) → Gemini CLI
```

#### Approach B: **Parallel Delegation** (Faster)
Give different tasks to different AIs simultaneously:
```
You → Claude Code (auth system)
    → Windsurf (database models)  
    → Gemini CLI (fix README typos)
```

#### Approach C: **Orchestrated Workflow** (Most Efficient)
Let Claude Code break down and delegate:
```
You → Claude Code → Creates issues → Windsurf & Gemini work in parallel
```

## 🎯 How to Initiate Tasks Properly

### For Complex Features
**Always start with Claude Code:**
```
"Build a user authentication system with email verification"
```
Claude Code will:
1. Design the architecture
2. Update PROGRESS_TRACKER.md with breakdown
3. Create issues for Windsurf (scaffolding)
4. Create issues for Gemini CLI (minor fixes)

### For Scaffolding Tasks
**If you know exactly what structure you need:**
```
1. Create GitHub issue with label `task:scaffold`
2. Specify exact modules/files to create
3. Assign to Windsurf
```

### For Minor Fixes
**For specific small changes:**
```
1. Create GitHub issue with label `task:minor`
2. List exact files and changes needed
3. Assign to Gemini CLI
```

## 🔒 Git-Based Conflict Prevention

### The PR Merge Strategy
1. **All AIs work in feature branches**
   - Claude Code: `feat/cc-*`
   - Windsurf: `scaffold/ws-*`
   - Gemini CLI: `fix/gc-*`

2. **You control the merge order**
   ```bash
   # Review PRs in order of dependency
   gh pr list --state open
   
   # Merge architectural changes first
   gh pr merge [claude-pr-number]
   
   # Then scaffolding
   gh pr merge [windsurf-pr-number]
   
   # Finally minor fixes
   gh pr merge [gemini-pr-number]
   ```

3. **Handling Merge Conflicts**
   - If PR has conflicts, ask the AI to rebase:
   ```
   "Your PR has conflicts. Please rebase on latest main"
   ```

## 📊 Using PROGRESS_TRACKER.md

### Before Starting Any Task
```bash
# Always check what's in progress
cat PROGRESS_TRACKER.md
```

### Safe Parallel Task Assignment
✅ **GOOD: Different files**
```
Claude Code: Working on /src/auth/* 
Windsurf: Working on /src/database/*
Gemini CLI: Working on /README.md
```

❌ **BAD: Same files**
```
Claude Code: Working on /src/auth/login.js
Windsurf: Also trying to modify /src/auth/login.js
```

## 🚦 Task Assignment Examples

### Example 1: Building a New Feature (PRSNL Example)
```
You: "Build the capture API for PRSNL"

1. Tell Claude Code the requirement
2. Claude Code creates:
   - Capture API design in /PRSNL/backend/api/capture.py
   - Updates PROGRESS_TRACKER.md
   - Issue #1: Scaffold FastAPI structure (→ Windsurf)
   - Issue #2: Implement capture engine (→ Claude Code)
   - Issue #3: Fix import paths and configs (→ Gemini CLI)
```

### Example 2: Refactoring Existing Code
```
You: "Refactor all API endpoints to use new error handling"

1. Ask Claude Code to design the new pattern
2. Claude Code creates:
   - Refactoring plan
   - Issue for Windsurf with specific pattern to apply
3. Windsurf executes the refactoring
4. Gemini CLI fixes any small issues
```

### Example 3: Multiple Parallel Tasks
```
You have 3 independent tasks:
- Task A: Build user profile feature
- Task B: Update all documentation
- Task C: Fix typos in config files

Assign simultaneously:
- Claude Code: Task A (different branch)
- Windsurf: Task B (different branch)  
- Gemini CLI: Task C (different branch)
```

## 🛡️ Fail-Safe Mechanisms

### Automatic Conflict Detection
Each AI checks before starting:
```bash
# They run automatically
gh pr list --state open
cat PROGRESS_TRACKER.md
git branch -a | grep -E "(cc-|ws-|gc-)"
```

### Manual Conflict Resolution
If two AIs accidentally work on same files:
1. Check PROGRESS_TRACKER.md to see who started first
2. Ask the second AI to stop and wait
3. Merge the first PR
4. Ask second AI to rebase and continue

## 📈 Best Practices

### DO:
- ✅ Always check PROGRESS_TRACKER.md first
- ✅ Create specific GitHub issues for delegation
- ✅ Let Claude Code orchestrate complex tasks
- ✅ Merge PRs in dependency order
- ✅ Use labels: `task:scaffold`, `task:minor`

### DON'T:
- ❌ Give vague tasks to multiple AIs
- ❌ Assign same files to multiple AIs
- ❌ Skip the PROGRESS_TRACKER.md update
- ❌ Merge PRs without reviewing
- ❌ Rush parallel assignments without checking

## 🔄 Typical Workflows

### Workflow 1: Feature Development
```
1. You → Claude Code: "Build feature X"
2. Claude Code → Designs and breaks down
3. Claude Code → Creates issues
4. Windsurf & Gemini → Work in parallel on different parts
5. You → Review and merge PRs in order
```

### Workflow 2: Bug Fix
```
1. You → Identify bug location
2. Simple bug → Gemini CLI directly
3. Complex bug → Claude Code first
```

### Workflow 3: Refactoring
```
1. You → Claude Code: "Refactor pattern X"
2. Claude Code → Creates plan
3. Windsurf → Executes refactoring
4. Gemini CLI → Cleanup
```

## 🚨 Emergency Procedures

### If Things Go Wrong:
1. Stop all AIs: "STOP - we have a conflict"
2. Check PROGRESS_TRACKER.md
3. Check all open PRs: `gh pr list`
4. Identify the conflict
5. Direct AIs to resolve

### Recovery Steps:
```bash
# Reset to clean state
git checkout main
git pull origin main

# Check status
cat PROGRESS_TRACKER.md
gh pr list --state open

# Restart with clear assignments
```

## 💡 Pro Tips

1. **Morning Routine**
   ```bash
   git pull origin main
   cat PROGRESS_TRACKER.md
   gh pr list --state open
   ```

2. **Use Issues as Task Queue**
   - Create all tasks as GitHub issues
   - Assign to appropriate AI
   - Track progress via issue status

3. **Batch Similar Work**
   - Group all scaffolding tasks → Windsurf
   - Group all minor fixes → Gemini CLI
   - Keep architectural work → Claude Code

4. **Review PRs Promptly**
   - Don't let PRs pile up
   - Merge architectural changes first
   - This prevents complex conflicts

Remember: The system is designed to prevent conflicts. Trust the process, and the AIs will coordinate smoothly!