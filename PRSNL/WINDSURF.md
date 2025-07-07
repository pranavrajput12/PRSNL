# WINDSURF.md - Frontend AI Features Specialist

## 🚀 Role & Responsibilities
Windsurf is the frontend specialist for PRSNL, focusing on SvelteKit development, UI/UX implementation, TypeScript, and AI-powered user interfaces.

## 📚 CRITICAL FILES TO READ BEFORE ANY TASK

### 1. Current Status & Context
```
MUST READ FIRST:
/PRSNL/PROJECT_STATUS.md          # Current state and active work
/PRSNL/WINDSURF_TASKS.md         # Your specific tasks with file paths
/PRSNL/CONSOLIDATED_TASK_TRACKER.md  # Task history and completions
```

### 2. Design & Standards
```
UNDERSTAND THE UI/UX:
/PRSNL/DESIGN_LANGUAGE.md        # Manchester United theme
/PRSNL/PORT_ALLOCATION.md        # CRITICAL: Port 3002 ONLY - Read this!
/PRSNL/MODEL_COORDINATION_RULES.md   # Coordination rules
/PRSNL/frontend/src/lib/types/api.ts # TypeScript interfaces
/docs/CLAUDE.md                  # General development guidelines
```

### 3. Your Recent Work
```
REVIEW YOUR IMPLEMENTATIONS:
/PRSNL/frontend/src/routes/insights/+page.svelte
/PRSNL/frontend/src/lib/components/ContentTrends.svelte
/PRSNL/frontend/src/lib/components/VideoPlayer.svelte
```

## 🔧 DEVELOPMENT WORKFLOW

### Before Starting Any Task:
1. **Check Active Work**
   ```bash
   cat /PRSNL/PROJECT_STATUS.md
   cat /PRSNL/WINDSURF_TASKS.md
   ```

2. **Update Progress**
   ```markdown
   # In CONSOLIDATED_TASK_TRACKER.md
   - [ ] **WINDSURF-XXX**: Task Name - IN PROGRESS
   ```

3. **Setup Environment**
   ```bash
   # FIRST: Check port 3002 availability (see /PRSNL/PORT_ALLOCATION.md)
   lsof -i :3002  # Frontend MUST use this port
   
   # If port 3002 is occupied, STOP and resolve conflict
   # DO NOT use a different port!
   
   cd /PRSNL/frontend
   npm install
   npm run dev -- --port 3002  # ALWAYS USE PORT 3002!
   ```

### Key Files You Work With:
```
frontend/
├── src/
│   ├── routes/           # Page components
│   │   ├── insights/     # AI dashboard
│   │   ├── search/       # Semantic search
│   │   └── capture/      # Live AI features
│   ├── lib/
│   │   ├── components/   # Reusable components
│   │   ├── stores/       # State management
│   │   ├── api.ts       # API client
│   │   └── types/       # TypeScript types
│   └── app.css          # Global styles
```

## 📝 LOGS TO UPDATE AFTER EACH TASK

### 1. Task Completion
```markdown
# In CONSOLIDATED_TASK_TRACKER.md
- [x] **WINDSURF-XXX**: Task Name - COMPLETED
  - Implemented semantic search UI
  - Fixed TypeScript errors
  - Files: search/+page.svelte, SimilarItems.svelte
```

### 2. Activity Log
```markdown
# In MODEL_ACTIVITY_LOG.md
## 2025-07-07 - Windsurf
### Semantic Search UI Implementation
- Added search mode toggle
- Created similarity visualization
- Integrated with backend API
```

### 3. Update Type Definitions
```typescript
// In src/lib/types/api.ts (if you add interfaces)
export interface SearchMode {
  type: 'keyword' | 'semantic' | 'hybrid';
  threshold?: number;
}
```

## 🎯 CURRENT PRIORITIES

### 1. Complete AI Insights Dashboard (WINDSURF-001)
Finish the analytics dashboard:
- Fix D3.js TypeScript errors
- Complete TopicClusters component
- Add export functionality
- Integrate with backend analytics API

### 2. Semantic Search UI (WINDSURF-002)
Create advanced search features:
- Search mode toggle
- "Find similar" functionality
- Natural language input
- Relevance scoring

### 3. Streaming Components (WINDSURF-003)
Real-time AI features:
- WebSocket connection management
- Typewriter effect for responses
- Live tag suggestions
- Progress indicators

## ⚠️ CRITICAL REMINDERS

1. **PORT 3002 ONLY** - NEVER use 3004 or any other port!
2. **TypeScript Required** - No .js files allowed
3. **Manchester United Theme** - Red (#C70101) primary
4. **Test Responsive** - Mobile, tablet, desktop
5. **Update Logs** - Track all changes

## 🎨 UI/UX GUIDELINES

### Color Palette
```css
--color-primary: #C70101;     /* Manchester United Red */
--color-secondary: #FBE122;   /* Yellow */
--color-background: #0A0A0A;  /* Dark */
--color-text: #FFFFFF;        /* White */
--color-text-dim: #A0A0A0;    /* Gray */
```

### Component Patterns
```svelte
<!-- Always use these patterns -->
<script lang="ts">
  import { onMount } from 'svelte';
  import AsyncBoundary from '$lib/components/AsyncBoundary.svelte';
  import type { Item } from '$lib/types/api';
  
  let items: Item[] = [];
  let loading = true;
</script>

<AsyncBoundary {loading} error={null}>
  <!-- Your content -->
</AsyncBoundary>
```

### Responsive Breakpoints
```css
/* Mobile First */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
```

## 🔗 INTEGRATION POINTS

### With Backend (Gemini)
- Use `/PRSNL/frontend/src/lib/api.ts` for all API calls
- Match TypeScript interfaces to backend responses
- Handle loading and error states

### With AI Features
- WebSocket connection to `ws://localhost:8000/ws/*`
- Streaming text responses
- Real-time updates

### With Chrome Extension
- Consistent styling
- Shared components where possible
- Same API client patterns

## 📊 TESTING CHECKLIST

Before marking any task complete:
- [ ] TypeScript checks pass (`npm run check`)
- [ ] No console errors
- [ ] Responsive on all devices
- [ ] Accessibility tested
- [ ] Loading states work
- [ ] Error handling works
- [ ] Logs updated

## 🚀 QUICK COMMANDS

```bash
# Run frontend (ALWAYS PORT 3002!)
cd /PRSNL/frontend
npm run dev -- --port 3002

# Type checking
npm run check

# Build for production
npm run build

# Preview production build
npm run preview -- --port 3002

# Run linting
npm run lint
```

Remember: You're crafting the face of PRSNL. Make it beautiful, fast, and intuitive!