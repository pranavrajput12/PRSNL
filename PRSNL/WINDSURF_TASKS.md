# 🚀 WINDSURF - Simple Frontend Tasks

## 📚 REQUIRED READING BEFORE ANY TASK
Always review these files before starting work:

### Documentation to Read First:
1. `/PRSNL/PROJECT_STATUS.md` - Current project state and context
2. `/PRSNL/MODEL_COORDINATION_RULES.md` - **CRITICAL: PORT 3002 ONLY!**
3. `/PRSNL/DESIGN_LANGUAGE.md` - UI/UX guidelines (Manchester United theme)
4. `/PRSNL/frontend/src/lib/types/api.ts` - TypeScript interfaces

### Files to Update After Each Task:
1. `/PRSNL/CONSOLIDATED_TASK_TRACKER.md` - Mark task complete
2. `/PRSNL/MODEL_ACTIVITY_LOG.md` - Log your changes
3. `/PRSNL/PROJECT_STATUS.md` - Update progress section

---

## ⚠️ TASK REASSIGNMENT (2025-01-08)
Complex frontend tasks have been reassigned to Claude. Windsurf should focus on simple UI polish tasks.

## 🎯 NEW SIMPLE TASKS

### Task WINDSURF-SIMPLE-001: Update Loading Spinners
**Priority**: LOW
**Status**: TODO
**Estimated Time**: 30 minutes

**Task**: Replace all loading spinners with consistent animated spinner
- Use the existing Spinner component in all pages
- Ensure consistent size and color (#dc143c)
- Add loading text where appropriate

**Files to Update:**
```
/PRSNL/frontend/src/routes/+page.svelte
/PRSNL/frontend/src/routes/search/+page.svelte
/PRSNL/frontend/src/routes/timeline/+page.svelte
/PRSNL/frontend/src/routes/videos/+page.svelte
```

---

### Task WINDSURF-SIMPLE-002: Fix Empty State Messages
**Priority**: MEDIUM
**Status**: TODO
**Estimated Time**: 1 hour

**Task**: Add friendly empty state messages
- When no items in timeline: "No items yet. Start capturing content!"
- When no search results: "No results found. Try different keywords."
- When no videos: "No videos saved yet."
- Include appropriate icons

**Files to Update:**
```
/PRSNL/frontend/src/routes/+page.svelte
/PRSNL/frontend/src/routes/search/+page.svelte
/PRSNL/frontend/src/routes/videos/+page.svelte
```

---

### Task WINDSURF-SIMPLE-003: Button Hover States
**Priority**: LOW
**Status**: TODO
**Estimated Time**: 45 minutes

**Task**: Add consistent hover effects to all buttons
- Primary buttons: Darken on hover
- Secondary buttons: Add border on hover
- Icon buttons: Scale up slightly on hover
- Use CSS transitions for smooth effects

**Files to Update:**
```
/PRSNL/frontend/src/app.css
/PRSNL/frontend/src/lib/components/AnimatedButton.svelte
```

---

### Task WINDSURF-SIMPLE-004: Format Timestamps
**Priority**: MEDIUM
**Status**: TODO
**Estimated Time**: 1 hour

**Task**: Make all timestamps show relative time
- "2 hours ago" instead of full date for recent items
- "Yesterday" for items from yesterday
- Full date only for items older than 7 days
- Use existing `formatDate` utility

**Files to Update:**
```
/PRSNL/frontend/src/lib/utils/date.ts
/PRSNL/frontend/src/lib/components/ItemCard.svelte
/PRSNL/frontend/src/lib/components/VideoCard.svelte
```

---

### Task WINDSURF-SIMPLE-005: Add Tooltips
**Priority**: LOW
**Status**: TODO
**Estimated Time**: 2 hours

**Task**: Add helpful tooltips to icon buttons
- Use `title` attribute for simple tooltips
- "Delete item", "Edit item", "Share item" etc.
- Keep tooltips short and clear

**Files to Update:**
```
/PRSNL/frontend/src/lib/components/ItemCard.svelte
/PRSNL/frontend/src/routes/item/[id]/+page.svelte
/PRSNL/frontend/src/routes/videos/[id]/+page.svelte
```

---

### Task WINDSURF-SIMPLE-006: Mobile Menu Icon
**Priority**: MEDIUM
**Status**: TODO
**Estimated Time**: 1 hour

**Task**: Add hamburger menu icon for mobile
- Add menu icon to header on mobile screens
- Use existing Icon component
- Toggle sidebar visibility on click
- Add smooth slide animation

**Files to Update:**
```
/PRSNL/frontend/src/routes/+layout.svelte
```

---

## 📋 Guidelines for Simple Tasks

1. **DO NOT** modify any API calls or data fetching logic
2. **DO NOT** change component props or TypeScript interfaces  
3. **DO NOT** add new dependencies
4. **DO** focus on visual polish and user experience
5. **DO** test changes in browser before marking complete
6. **DO** keep changes small and focused

## 🚫 Tasks NOT for Windsurf

These are handled by Claude:
- WebSocket connections
- API integrations
- State management
- Complex component logic
- New feature implementation
- Bug fixes involving data flow