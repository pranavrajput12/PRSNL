# Standard Operating Procedure (SOP) Checklists

## Claude Code SOP Checklist

### ✅ Task Receipt Checklist
- [ ] Read the complete user request
- [ ] Identify if it's a complex/architectural task
- [ ] Check PROGRESS_TRACKER.md for conflicts
- [ ] Determine if task needs breakdown

### ✅ Task Breakdown Checklist
- [ ] Analyze full scope of work
- [ ] Identify architectural components (mine)
- [ ] Identify scaffolding needs (→ Windsurf)
- [ ] Identify minor fixes needed (→ Gemini CLI)
- [ ] Update PROGRESS_TRACKER.md with breakdown
- [ ] Create GitHub issues for delegated work

### ✅ Before Starting Work
- [ ] `git pull --rebase`
- [ ] `cat PROGRESS_TRACKER.md`
- [ ] `gh pr list --state open`
- [ ] Create branch: `feat/cc-[name]`
- [ ] Update PROGRESS_TRACKER.md status

### ✅ During Work
- [ ] Update progress every 30 minutes
- [ ] Mark files as "editing" in tracker
- [ ] Commit frequently with clear messages
- [ ] Follow architectural patterns

### ✅ Completion
- [ ] Update PROGRESS_TRACKER.md to COMPLETED
- [ ] Create PR with "Generated-by: Claude-Code"
- [ ] Verify all sub-tasks are assigned

---

## Windsurf SOP Checklist

### ✅ Task Validation Checklist
- [ ] Verify GitHub issue exists with label
- [ ] OR verify Claude Code directive
- [ ] Confirm it's scaffolding/refactoring work
- [ ] Check it's not a single-file edit
- [ ] Check it's not an architecture decision

### ✅ Pre-Work Checklist
- [ ] `git pull --rebase`
- [ ] `cat PROGRESS_TRACKER.md` - check for conflicts
- [ ] `gh pr list --state open`
- [ ] `git branch -a | grep -E "(cc-|gc-)"`
- [ ] Verify no file conflicts exist

### ✅ Starting Work
- [ ] Update PROGRESS_TRACKER.md with task
- [ ] List ALL files to be created/modified
- [ ] Create branch: `scaffold/ws-[name]`
- [ ] Mark files as "editing"

### ✅ During Scaffolding
- [ ] Follow existing patterns
- [ ] Generate comprehensive file structure
- [ ] Include test files
- [ ] Update progress every 30 minutes
- [ ] Keep generated code consistent

### ✅ Completion
- [ ] All requested files generated
- [ ] Tests scaffolded alongside code
- [ ] PROGRESS_TRACKER.md updated to COMPLETED
- [ ] PR created with "Generated-by: Windsurf"

---

## Gemini CLI SOP Checklist

### ✅ Task Validation Checklist
- [ ] GitHub issue has specific file paths
- [ ] Count files: must be ≤ 5
- [ ] Verify it's a minor fix/edit
- [ ] Confirm not creating features
- [ ] Confirm not refactoring

### ✅ Pre-Work Checklist
- [ ] `git pull --rebase`
- [ ] `cat PROGRESS_TRACKER.md` - check conflicts
- [ ] `gh pr list --state open`
- [ ] Verify target files aren't locked
- [ ] Count files again: ≤ 5

### ✅ Starting Work
- [ ] Update PROGRESS_TRACKER.md
- [ ] Create branch: `fix/gc-[issue-num]`
- [ ] List exact files being edited
- [ ] Mark files as "editing"

### ✅ During Work
- [ ] Make ONLY requested changes
- [ ] Don't refactor or "improve"
- [ ] Stay within specified files
- [ ] Update progress if > 30 min

### ✅ Completion
- [ ] Verify only requested changes made
- [ ] File count still ≤ 5
- [ ] PROGRESS_TRACKER.md updated
- [ ] PR with "Generated-by: Gemini CLI"

---

## Universal Rules (All AIs)

### ❌ REJECT If:
- [ ] Files are marked "editing" by another AI
- [ ] Task is outside your scope
- [ ] Request is vague or unclear
- [ ] Would conflict with open PRs
- [ ] No clear acceptance criteria

### 🚨 Emergency Protocol:
- [ ] STOP all work
- [ ] Document the issue
- [ ] Update PROGRESS_TRACKER.md with BLOCKED
- [ ] Create GitHub issue with `conflict-detected`
- [ ] Wait for human intervention

---

## Quick Reference: Who Does What?

| Task Type | Owner | Example |
|-----------|-------|---------|
| Architecture Design | Claude Code | "Design the API structure" |
| Complex Features | Claude Code | "Implement authentication logic" |
| Module Scaffolding | Windsurf | "Create user module structure" |
| Large Refactoring | Windsurf | "Rename all API endpoints" |
| Boilerplate Generation | Windsurf | "Generate CRUD for 5 models" |
| Typo Fixes | Gemini CLI | "Fix typo in README.md" |
| Config Updates | Gemini CLI | "Update version in package.json" |
| Small Bug Fixes | Gemini CLI | "Fix missing import in auth.js" |

## Progress Tracker States

```
PLANNING → IN_PROGRESS → REVIEW → COMPLETED
                ↓
             BLOCKED
```

Remember: When in doubt, REJECT and ESCALATE!