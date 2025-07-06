# Git-Based Merge Strategy for Multi-AI Collaboration

## Overview
This document outlines the git-based strategies to prevent conflicts when multiple AI agents work simultaneously.

## Branch Protection Rules

### Main Branch Protection
```yaml
# GitHub Settings → Branches → Protection Rules
- Require pull request reviews before merging
- Dismiss stale PR approvals when new commits are pushed  
- Require branches to be up to date before merging
- Require conversation resolution before merging
- Do not allow bypassing the above settings
```

## Automated Conflict Detection

### Pre-Push Hook
Create `.git/hooks/pre-push`:
```bash
#!/bin/bash
# Check PROGRESS_TRACKER.md for conflicts

# Get files being pushed
files_changed=$(git diff --name-only origin/main...HEAD)

# Check if any files are marked as "editing" by another AI
for file in $files_changed; do
  if grep -q "$file.*editing" PROGRESS_TRACKER.md; then
    owner=$(grep "$file" PROGRESS_TRACKER.md | grep -oP 'Owner: \K[^,]+')
    if [[ "$owner" != *"$(git config user.name)"* ]]; then
      echo "ERROR: $file is being edited by $owner"
      echo "Update PROGRESS_TRACKER.md or wait for them to complete"
      exit 1
    fi
  fi
done
```

### GitHub Action for PR Validation
`.github/workflows/pr-validation.yml`:
```yaml
name: PR Conflict Check
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  check-conflicts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Check PROGRESS_TRACKER
        run: |
          # Get PR author
          PR_AUTHOR="${{ github.event.pull_request.user.login }}"
          
          # Get changed files
          CHANGED_FILES=$(git diff --name-only origin/main...HEAD)
          
          # Check each file in PROGRESS_TRACKER
          for file in $CHANGED_FILES; do
            if grep -q "$file.*editing.*(?!$PR_AUTHOR)" PROGRESS_TRACKER.md; then
              echo "::error::File $file is being edited by another AI"
              exit 1
            fi
          done
      
      - name: Check branch naming
        run: |
          BRANCH="${{ github.head_ref }}"
          if [[ ! "$BRANCH" =~ ^(feat/cc-|scaffold/ws-|fix/gc-|refactor/ws-|chore/gc-) ]]; then
            echo "::error::Branch name must follow AI naming convention"
            exit 1
          fi
```

## Smart Merge Order

### Dependency-Based Auto-Merge
`.github/workflows/smart-merge.yml`:
```yaml
name: Smart Merge Order
on:
  pull_request:
    types: [labeled]

jobs:
  auto-merge:
    if: contains(github.event.label.name, 'ready-to-merge')
    runs-on: ubuntu-latest
    steps:
      - name: Check merge order
        run: |
          # Priority order: Claude Code → Windsurf → Gemini CLI
          OPEN_PRS=$(gh pr list --state open --json number,headRefName)
          
          # If this is a Windsurf PR, check for open Claude Code PRs
          if [[ "${{ github.head_ref }}" =~ ^scaffold/ws- ]]; then
            if echo "$OPEN_PRS" | grep -q "feat/cc-"; then
              echo "::error::Claude Code PR must be merged first"
              exit 1
            fi
          fi
          
          # If this is a Gemini CLI PR, check for open higher priority PRs
          if [[ "${{ github.head_ref }}" =~ ^fix/gc- ]]; then
            if echo "$OPEN_PRS" | grep -qE "(feat/cc-|scaffold/ws-)"; then
              echo "::error::Higher priority PRs must be merged first"
              exit 1
            fi
          fi
```

## Merge Conflict Resolution

### Automated Rebase Workflow
When a PR has conflicts after another PR is merged:

```yaml
name: Auto Rebase
on:
  issue_comment:
    types: [created]

jobs:
  rebase:
    if: github.event.comment.body == '/rebase'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Rebase PR
        run: |
          git checkout ${{ github.event.pull_request.head.ref }}
          git rebase origin/main
          git push --force-with-lease
```

## PROGRESS_TRACKER.md Integration

### Auto-Update Progress Tracker
`.github/workflows/progress-tracker.yml`:
```yaml
name: Update Progress Tracker
on:
  pull_request:
    types: [opened, closed]

jobs:
  update-tracker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Update on PR open
        if: github.event.action == 'opened'
        run: |
          # Add task to IN_PROGRESS section
          # Update file status to "editing"
      
      - name: Update on PR close
        if: github.event.action == 'closed'
        run: |
          # Move task to COMPLETED
          # Update file status to "complete"
```

## Git Aliases for AIs

Add to each AI's configuration:
```bash
# ~/.gitconfig
[alias]
  # Check for conflicts before starting
  check-conflicts = "!f() { \
    git fetch origin && \
    echo 'Checking PROGRESS_TRACKER...' && \
    git show origin/main:PROGRESS_TRACKER.md | grep -E 'editing|IN_PROGRESS' && \
    echo 'Checking open PRs...' && \
    gh pr list --state open; \
  }; f"
  
  # Safe start work
  start-work = "!f() { \
    git check-conflicts && \
    git checkout -b $1 && \
    echo 'Remember to update PROGRESS_TRACKER.md!'; \
  }; f"
  
  # Safe push with checks
  safe-push = "!f() { \
    git fetch origin && \
    git rebase origin/main && \
    git push -u origin HEAD; \
  }; f"
```

## Merge Queue Implementation

### Using GitHub Merge Queue (Beta)
```yaml
# .github/merge-queue.yml
merge_queue:
  merge_method: squash
  update_method: rebase
  merge_queue_config:
    min_entries_to_merge: 1
    max_entries_to_merge: 5
    merge_timeout_minutes: 60
```

## Conflict Prevention Rules

### 1. File-Level Locking
- PROGRESS_TRACKER.md acts as distributed lock
- Files marked "editing" cannot be modified by others
- Enforced by pre-push hooks and CI

### 2. Branch Isolation
- Each AI has designated branch prefixes
- Cross-AI branch creation is rejected
- Enforced by branch protection rules

### 3. PR Merge Order
- Architectural changes (Claude Code) merge first
- Scaffolding (Windsurf) merges second
- Minor fixes (Gemini CLI) merge last
- Enforced by GitHub Actions

### 4. Automatic Conflict Resolution
- Auto-rebase on '/rebase' comment
- Smart conflict detection before work starts
- Clear error messages guide resolution

## Implementation Checklist

- [ ] Enable branch protection on main
- [ ] Add pre-push hooks to repo
- [ ] Set up GitHub Actions workflows
- [ ] Configure merge queue
- [ ] Add git aliases to AI configs
- [ ] Test conflict detection
- [ ] Document emergency procedures

## Emergency Override

For urgent fixes when automation blocks:
```bash
# Bypass with admin rights (use sparingly)
git push --force-with-lease origin main

# Document why override was needed
echo "Emergency override: [reason]" >> OVERRIDE_LOG.md
```

This git-based system ensures smooth parallel work while preventing conflicts automatically!