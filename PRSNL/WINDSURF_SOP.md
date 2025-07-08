# 🚀 WINDSURF - Standard Operating Procedure

## 📋 Your Role
You handle **SIMPLE FRONTEND TASKS ONLY**. No complex logic, no API changes, no state management modifications.

## ✅ Task Checklist

### 1. Start of Session
```bash
# Read these files in order:
1. /PRSNL/CENTRALIZED_TASK_MANAGEMENT.md
2. /PRSNL/PROJECT_STATUS.md  
3. /PRSNL/WINDSURF_TASKS.md (your task list)
```

### 2. Select a Task
- Pick a task marked **TODO** from WINDSURF_TASKS.md
- Tasks are already simple and well-defined
- If unclear, ask for clarification

### 3. Before Working
```bash
# Check if anyone is working on related files
grep "LOCKED" /PRSNL/MODEL_ACTIVITY_LOG.md

# Ensure frontend is running
cd /PRSNL/frontend
npm run dev  # Should be on port 3002
```

### 4. Update Task Status
```markdown
# In CONSOLIDATED_TASK_TRACKER.md, add:
### Task WINDSURF-2025-01-08-001: Add Loading Spinners
**Status**: IN PROGRESS
**Started**: 2025-01-08 15:00
**Assigned**: Windsurf
```

### 5. Do the Work
- Make ONLY the changes specified in the task
- Don't modify business logic
- Keep Manchester United red theme (#dc143c)
- Test in browser before marking complete

### 6. Complete the Task
```markdown
# In CONSOLIDATED_TASK_TRACKER.md:
**Status**: COMPLETED
**Completed**: 2025-01-08 15:30

# In WINDSURF_TASKS.md:
Move task from TODO to COMPLETED section
```

## 🚫 What NOT to Do

### Never Touch
- API calls or data fetching logic
- State management (stores)
- Component props or interfaces
- Backend files
- Complex business logic

### Never Add
- New npm packages
- New API endpoints
- Complex animations
- New routes or pages

## ✅ What You CAN Do

### UI Polish
- Update colors and spacing
- Add hover effects
- Improve loading states
- Format dates and numbers
- Add tooltips
- Update icons

### Simple Components
- Loading spinners
- Empty state messages
- Simple animations
- Button styles
- Card layouts

## 📝 Example Tasks

### Good Task Example
```markdown
Task: Update all loading spinners to use consistent style
- Find all loading states
- Replace with Spinner component
- Ensure color is #dc143c
- Test each page
```

### Task You Should Skip
```markdown
Task: Add real-time updates to search
- Requires WebSocket (skip)
- Needs state management (skip)
- Complex logic (skip)
```

## 🎨 Design Guidelines

### Colors
- Primary: #dc143c (Manchester United red)
- Hover: #b91c1c (darker red)
- Text: #111827 (dark gray)
- Background: #ffffff (white)

### Spacing
- Use multiples of 4px or 8px
- Consistent padding on cards
- Proper margins between sections

### Typography
- Font: System font stack
- Sizes: text-sm, text-base, text-lg
- Weights: font-normal, font-medium, font-semibold

## 🧪 Testing Your Work

### Browser Testing
1. Open http://localhost:3002
2. Navigate to affected pages
3. Test on different screen sizes
4. Check hover states
5. Verify colors match design

### Quick Checks
- No console errors
- Page loads quickly
- Interactions feel smooth
- Colors are consistent
- Text is readable

## 📞 When to Ask for Help

### Ask Claude if
- Task seems too complex
- Requires API changes
- Needs new functionality
- Breaks something

### Ask User if
- Design direction unclear
- Color choice needed
- Priority unclear

## 🏁 End of Session

### Final Steps
1. Ensure all tasks marked complete
2. Test all changes work
3. Update task tracker
4. Leave clear notes if partially done

### Handoff Notes
```markdown
## Windsurf Session Summary - [Date]
**Completed**: 
- Added loading spinners (WINDSURF-001)
- Fixed hover states (WINDSURF-002)

**Notes**: 
- All spinners now use consistent style
- Hover states match design system
```

Remember: Keep it simple, make it beautiful, don't break anything!