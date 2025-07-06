# AI Workspace Isolation Protocol

## Workspace Structure

```
Personal Knowledge Base/
├── PRSNL/                      # Main project (Claude Code manages)
├── workspaces/                 # Isolated AI workspaces
│   ├── windsurf/              # Windsurf's workspace
│   │   └── PRSNL/             # Their copy to work on
│   └── gemini/                # Gemini's workspace
│       └── PRSNL/             # Their copy to work on
└── staging/                    # Review area before merging
```

## Workflow Protocol

### 1. Task Assignment Phase

When assigning tasks to Windsurf or Gemini:

```bash
# Claude Code prepares their workspace
cp -r PRSNL workspaces/[ai-name]/PRSNL
cd workspaces/[ai-name]/PRSNL
git init
git add .
git commit -m "Initial workspace for [task-name]"
```

### 2. AI Work Phase

Each AI works ONLY in their designated workspace:
- **Windsurf**: `/workspaces/windsurf/PRSNL/`
- **Gemini**: `/workspaces/gemini/PRSNL/`

They should:
1. Make all changes in their workspace
2. Test locally if possible
3. Commit changes with clear messages
4. Create a summary of changes

### 3. Review Phase (Claude Code)

After AI completes work:

```bash
# Review changes
cd workspaces/[ai-name]/PRSNL
git diff

# Copy to staging
cp -r . ../../../staging/[task-name]/

# Review and test
cd ../../../staging/[task-name]/
# Run tests, check code quality

# If approved, merge to main project
cd ../../../PRSNL/
# Selective copy of approved files
```

### 4. Integration Phase

Claude Code:
1. Reviews all changes
2. Resolves any conflicts
3. Integrates into main PRSNL folder
4. Commits to main repository
5. Cleans up workspace

## Benefits

1. **Zero Overlap**: AIs can't modify each other's files
2. **Clean History**: Main repo only gets reviewed commits
3. **Easy Rollback**: Can discard entire workspace if needed
4. **Parallel Work**: Multiple AIs can work simultaneously
5. **Quality Control**: Everything reviewed before integration

## Implementation Commands

### Setup Workspaces
```bash
mkdir -p workspaces/windsurf workspaces/gemini staging
```

### Assign Task to Windsurf
```bash
# Copy current state
cp -r PRSNL workspaces/windsurf/
cd workspaces/windsurf/PRSNL
git init
git add .
git commit -m "Workspace for Chrome extension task"
```

### Review Windsurf's Work
```bash
cd workspaces/windsurf/PRSNL
git log --oneline
git diff HEAD~1

# If good, copy specific files
cp -r extension/ ../../../PRSNL/
cd ../../../PRSNL
git add extension/
git commit -m "feat: add Chrome extension (via Windsurf workspace)"
```

## Task Assignment Template

When giving tasks to other AIs:

```
TASK: [Description]
WORKSPACE: /workspaces/[your-name]/PRSNL/
 
IMPORTANT: 
- Work ONLY in your designated workspace
- Do NOT navigate to the main /PRSNL/ folder
- Do NOT push to GitHub
- Create a CHANGES.md file listing all modifications
 
Your workspace is a complete copy of the project. Make all changes there.
When done, create CHANGES.md with:
1. Files created
2. Files modified  
3. Summary of changes
4. Any setup instructions
```

## Workspace Rules

1. **Each AI owns their workspace completely**
2. **No AI accesses another's workspace**
3. **Main PRSNL/ folder is Claude Code's domain**
4. **All integration happens through Claude Code**
5. **Workspaces are temporary and can be deleted after merge**

## Example Workflow

### Task: Add Redis caching

1. **Claude assigns to Gemini**:
   ```bash
   cp -r PRSNL workspaces/gemini/
   ```

2. **Gemini works in** `/workspaces/gemini/PRSNL/`
   - Modifies docker-compose.yml
   - Creates cache.py service
   - Updates requirements.txt

3. **Gemini completes**, creates CHANGES.md

4. **Claude reviews**:
   ```bash
   cd workspaces/gemini/PRSNL
   # Reviews changes
   cp backend/app/services/cache.py ../../../PRSNL/backend/app/services/
   cp docker-compose.yml ../../../staging/
   # Tests and merges
   ```

5. **Clean up**:
   ```bash
   rm -rf workspaces/gemini/PRSNL
   ```

This completely eliminates any possibility of file conflicts!