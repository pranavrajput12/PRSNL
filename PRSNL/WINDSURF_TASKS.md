# 🚀 WINDSURF - Frontend AI Enhancement Tasks

## Your Assigned Tasks:

### Task 1: Semantic Search UI
**Priority**: P0 - User-facing search enhancement
**Files to create/modify**:
1. `/frontend/src/routes/search/+page.svelte` - Enhance search page
2. `/frontend/src/lib/components/SimilarItems.svelte` - New component
3. `/frontend/src/lib/components/SearchFilters.svelte` - Enhanced filters
4. `/frontend/src/lib/api.ts` - Add new API calls

**Key Features to Implement**:

1. **"Find Similar" Button**:
```svelte
<!-- Add to each search result item -->
<button on:click={() => findSimilar(item.id)} class="btn-ghost">
  <Icon name="sparkles" size="small" />
  Find similar
</button>
```

2. **Visual Similarity Indicators**:
```svelte
<!-- Show relevance score as visual indicator -->
<div class="relevance-indicator">
  <div class="relevance-bar" style="width: {item.score * 100}%"></div>
  <span class="relevance-text">{Math.round(item.score * 100)}% match</span>
</div>
```

3. **Natural Language Search**:
```svelte
<!-- Update search input placeholder and add examples -->
<input 
  placeholder="Try: 'articles about AI from last week' or 'videos similar to machine learning'"
  on:input={handleNaturalLanguageSearch}
/>
```

### Task 2: AI Insights Dashboard
**Priority**: P1 - Content intelligence visualization
**Files to create**:
1. `/frontend/src/routes/insights/+page.svelte` - Main insights page
2. `/frontend/src/lib/components/TopicClusters.svelte` - D3.js visualization
3. `/frontend/src/lib/components/ContentTrends.svelte` - Trends chart
4. `/frontend/src/lib/components/KnowledgeGraph.svelte` - Interactive graph

**Dashboard Layout**:
```svelte
<!-- /frontend/src/routes/insights/+page.svelte -->
<script>
  import TopicClusters from '$lib/components/TopicClusters.svelte';
  import ContentTrends from '$lib/components/ContentTrends.svelte';
  import KnowledgeGraph from '$lib/components/KnowledgeGraph.svelte';
  
  let timeRange = 'week';
  let selectedCluster = null;
</script>

<div class="insights-dashboard">
  <h1>AI Insights</h1>
  
  <div class="insights-grid">
    <div class="insight-card">
      <h2>Topic Clusters</h2>
      <TopicClusters bind:selectedCluster />
    </div>
    
    <div class="insight-card">
      <h2>Content Trends</h2>
      <ContentTrends {timeRange} />
    </div>
    
    <div class="insight-card full-width">
      <h2>Knowledge Graph</h2>
      <KnowledgeGraph {selectedCluster} />
    </div>
  </div>
</div>
```

### Task 3: Streaming UI Components
**Priority**: P1 - Real-time AI feedback
**Files to create**:
1. `/frontend/src/lib/components/StreamingText.svelte` - Typewriter effect
2. `/frontend/src/lib/components/LiveTags.svelte` - Real-time tag suggestions
3. `/frontend/src/lib/stores/websocket.ts` - WebSocket store

**Streaming Text Component**:
```svelte
<!-- StreamingText.svelte -->
<script>
  export let text = '';
  export let speed = 30;
  
  let displayText = '';
  let index = 0;
  
  $: if (text) {
    animateText();
  }
  
  function animateText() {
    if (index < text.length) {
      displayText += text[index];
      index++;
      setTimeout(animateText, speed);
    }
  }
</script>

<span class="streaming-text">{displayText}<span class="cursor">|</span></span>

<style>
  .cursor {
    animation: blink 1s infinite;
  }
  @keyframes blink {
    50% { opacity: 0; }
  }
</style>
```

## Design Guidelines:
- Use Manchester United red (#dc143c) for AI-powered features
- Add subtle animations for AI interactions
- Show loading states with skeleton loaders
- Make features discoverable but not intrusive

## Testing:
1. Test similar items: Click "Find similar" on any search result
2. Test insights: Navigate to `/insights` and interact with visualizations
3. Test streaming: Type in capture form and watch live suggestions

## Success Criteria:
- [ ] "Find similar" returns relevant items
- [ ] Insights dashboard loads within 2 seconds
- [ ] Streaming text feels natural and smooth
- [ ] All visualizations are interactive
- [ ] Mobile responsive design

Start with the semantic search UI as it directly improves the user experience!