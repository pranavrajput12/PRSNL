# 🚀 WINDSURF - Frontend AI Features Tasks

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

## 🎯 ACTIVE TASKS

### Task WINDSURF-001: Complete AI Insights Dashboard
**Priority**: HIGH
**Status**: IN PROGRESS

**Files to Complete:**
```
/PRSNL/frontend/src/routes/insights/+page.svelte   # Main dashboard page
/PRSNL/frontend/src/lib/components/ContentTrends.svelte  # Fix D3 types
/PRSNL/frontend/src/lib/components/KnowledgeGraph.svelte # Complete implementation
```

**Files to Create:**
```
/PRSNL/frontend/src/lib/components/TopicClusters.svelte
/PRSNL/frontend/src/lib/components/InsightsSummary.svelte
/PRSNL/frontend/src/lib/stores/insights.ts         # State management
```

**Files to Reference:**
```
/PRSNL/frontend/src/lib/api.ts                     # API client patterns
/PRSNL/frontend/src/lib/components/AsyncBoundary.svelte  # Loading states
/PRSNL/frontend/src/lib/types/api.ts               # InsightsResponse type
```

**Requirements:**
1. Complete dashboard components:
   - Topic clusters with interactive D3.js visualization
   - Insights summary cards with metrics
   - Time range selector (day/week/month/year)
   - Export functionality for reports

2. Fix TypeScript issues:
   ```typescript
   // ContentTrends.svelte - proper typing
   interface TrendDataPoint {
     date: Date;
     articles: number;
     videos: number;
     notes: number;
     bookmarks: number;
   }
   ```

3. Integrate with backend analytics API:
   ```typescript
   // In insights store
   const trends = await api.get('/analytics/trends');
   const topics = await api.get('/analytics/topics');
   ```

---

### Task WINDSURF-002: Semantic Search UI
**Priority**: HIGH
**Status**: NOT STARTED

**Files to Modify:**
```
/PRSNL/frontend/src/routes/search/+page.svelte     # Add semantic features
/PRSNL/frontend/src/lib/api.ts                     # Add similarity endpoints
```

**Files to Create:**
```
/PRSNL/frontend/src/lib/components/SimilarItems.svelte
/PRSNL/frontend/src/lib/components/SearchModeToggle.svelte
/PRSNL/frontend/src/lib/components/RelevanceScore.svelte
```

**Requirements:**
1. Search mode toggle:
   - Keyword search (default)
   - Semantic search
   - Hybrid search

2. Similar items component:
   - "Find similar" button on each result
   - Similarity score visualization (0-100%)
   - Preview cards for similar items

3. Natural language input:
   - Placeholder: "Ask a question or describe what you're looking for..."
   - Query understanding indicator
   - Search suggestions based on intent

---

### Task WINDSURF-003: Streaming UI Components
**Priority**: MEDIUM
**Status**: NOT STARTED

**Files to Complete:**
```
/PRSNL/frontend/src/lib/components/StreamingText.svelte
```

**Files to Create:**
```
/PRSNL/frontend/src/lib/components/ProcessingProgress.svelte
/PRSNL/frontend/src/lib/components/LiveTags.svelte
/PRSNL/frontend/src/lib/stores/websocket.ts        # WebSocket management
```

**Files to Modify:**
```
/PRSNL/frontend/src/routes/capture/+page.svelte    # Add streaming
/PRSNL/frontend/src/routes/item/[id]/+page.svelte  # Add AI insights
```

**Requirements:**
1. WebSocket connection management:
   ```typescript
   // websocket.ts
   export function connectWebSocket(endpoint: string) {
     const ws = new WebSocket(`ws://localhost:8000/ws/${endpoint}`);
     // Handle reconnection, heartbeat, etc.
   }
   ```

2. Streaming text component:
   - Typewriter effect for incoming text
   - Loading indicator during streaming
   - Error handling with retry

3. Live features during capture:
   - Real-time tag suggestions
   - Content preview with AI insights
   - Processing progress indicator

---

## 🛠️ DEVELOPMENT WORKFLOW

### Before Starting:
```bash
cd /PRSNL/frontend
npm install
```

### Running Frontend:
```bash
# MUST USE PORT 3002!
npm run dev -- --port 3002

# Run type checking
npm run check

# Run linting
npm run lint
```

### Testing Components:
```bash
# Component testing
npm run test

# E2E testing
npm run test:e2e
```

---

## 🎨 UI/UX GUIDELINES

### Manchester United Theme:
- Primary: `#C70101` (Red)
- Secondary: `#FBE122` (Yellow)
- Background: Dark (`#0A0A0A`)
- Text: High contrast white/gray

### Component Patterns:
1. **Loading States**: Use AsyncBoundary wrapper
2. **Errors**: Use ErrorMessage component
3. **Icons**: Use Icon component (Lucide icons)
4. **Animations**: Subtle, < 300ms transitions

### Responsive Design:
- Mobile-first approach
- Breakpoints: 640px, 768px, 1024px, 1280px
- Touch-friendly: 44px minimum tap targets

---

## 📝 COMMIT MESSAGE FORMAT
```
feat(frontend): [WINDSURF-XXX] Brief description

- Detailed change 1
- Detailed change 2

Updates: CONSOLIDATED_TASK_TRACKER.md, MODEL_ACTIVITY_LOG.md
```

---

## ⚠️ CRITICAL REMINDERS
1. **ALWAYS USE PORT 3002** - Never 3004 or any other port!
2. **TypeScript Required** - No plain JavaScript files
3. **Test Responsiveness** - Mobile, tablet, desktop
4. **Maintain Theme** - Manchester United colors only
5. **Update Logs** - Track all changes in required files
6. **Check API Types** - Ensure frontend matches backend