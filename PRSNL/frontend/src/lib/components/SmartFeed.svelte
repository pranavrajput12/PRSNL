<script lang="ts">
  import { onMount } from 'svelte';
  import { searchItems, getTimeline } from '$lib/api';
  import type { TimelineItem, Item } from '$lib/types/api';
  import ItemCard from './ItemCard.svelte';
  import Spinner from './Spinner.svelte';
  import ErrorMessage from './ErrorMessage.svelte';
  
  export let mode: 'smart' | 'timeline' | 'graph' = 'smart';
  
  let items: (TimelineItem | Item)[] = [];
  let isLoading = false;
  let error: Error | null = null;
  let currentPage = 1;
  let hasMore = true;
  
  // Smart feed state
  let aiSuggestions: {
    query: string;
    reason: string;
  }[] = [];
  let currentFocus = 'Recent Activity';
  
  // Categories for smart organization
  const smartCategories = [
    { id: 'recent', name: 'Recent Activity', icon: 'clock' },
    { id: 'trending', name: 'Frequently Accessed', icon: 'trending' },
    { id: 'related', name: 'Related to Current', icon: 'link' },
    { id: 'discover', name: 'Discover', icon: 'sparkles' }
  ];
  
  onMount(() => {
    loadFeed();
  });
  
  async function loadFeed() {
    try {
      isLoading = true;
      error = null;
      
      if (mode === 'smart') {
        // Load smart feed with AI curation
        await loadSmartFeed();
      } else {
        // Load regular timeline
        const response = await getTimeline(currentPage);
        items = response.items || [];
        hasMore = response.hasMore || false;
      }
    } catch (err) {
      error = err instanceof Error ? err : new Error('Failed to load feed');
    } finally {
      isLoading = false;
    }
  }
  
  async function loadSmartFeed() {
    // For now, load recent items and simulate AI curation
    const response = await getTimeline(1);
    const recentItems = response.items || [];
    
    // Group items by smart categories
    const now = new Date();
    const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    // Simulate AI suggestions based on patterns
    aiSuggestions = [
      {
        query: 'typescript react',
        reason: 'Based on your recent searches'
      },
      {
        query: 'video processing',
        reason: 'Related to items you captured today'
      }
    ];
    
    items = recentItems;
  }
  
  function handleCategoryChange(categoryId: string) {
    const category = smartCategories.find(c => c.id === categoryId);
    if (category) {
      currentFocus = category.name;
      loadFeed();
    }
  }
  
  async function handleSuggestionClick(query: string) {
    try {
      isLoading = true;
      const response = await searchItems(query, { mode: 'hybrid' });
      items = response.results || [];
    } catch (err) {
      error = err instanceof Error ? err : new Error('Search failed');
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="smart-feed">
  {#if mode === 'smart'}
    <div class="feed-header">
      <h2>{currentFocus}</h2>
      <div class="feed-categories">
        {#each smartCategories as category}
          <button
            class="category-tab"
            class:active={currentFocus === category.name}
            on:click={() => handleCategoryChange(category.id)}
          >
            <span class="category-icon">{category.icon}</span>
            {category.name}
          </button>
        {/each}
      </div>
    </div>
    
    {#if aiSuggestions.length > 0}
      <div class="ai-suggestions">
        <h3>AI Suggestions</h3>
        <div class="suggestion-cards">
          {#each aiSuggestions as suggestion}
            <button
              class="suggestion-card"
              on:click={() => handleSuggestionClick(suggestion.query)}
            >
              <div class="suggestion-query">{suggestion.query}</div>
              <div class="suggestion-reason">{suggestion.reason}</div>
            </button>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
  
  {#if error}
    <ErrorMessage
      message="Failed to load feed"
      details={error.message}
      retry={loadFeed}
    />
  {/if}
  
  {#if isLoading && items.length === 0}
    <div class="loading-container">
      <Spinner size="large" />
      <p>Loading your knowledge feed...</p>
    </div>
  {:else if items.length === 0}
    <div class="empty-state">
      <h3>No items yet</h3>
      <p>Start capturing knowledge to see it here</p>
    </div>
  {:else}
    <div class="feed-items">
      {#each items as item}
        <ItemCard {item} view="feed" />
      {/each}
    </div>
    
    {#if hasMore && mode !== 'smart'}
      <div class="load-more">
        <button
          on:click={() => {
            currentPage++;
            loadFeed();
          }}
          disabled={isLoading}
        >
          {isLoading ? 'Loading...' : 'Load More'}
        </button>
      </div>
    {/if}
  {/if}
</div>

<style>
  .smart-feed {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .feed-header {
    margin-bottom: 2rem;
  }
  
  .feed-header h2 {
    margin-bottom: 1rem;
    color: var(--text-primary);
  }
  
  .feed-categories {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }
  
  .category-tab {
    padding: 0.5rem 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .category-tab:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
  
  .category-tab.active {
    background: var(--accent);
    color: var(--accent-text);
    border-color: var(--accent);
  }
  
  .category-icon {
    font-size: 1.2rem;
  }
  
  .ai-suggestions {
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: var(--bg-secondary);
    border-radius: var(--radius);
    border: 1px solid var(--border);
  }
  
  .ai-suggestions h3 {
    margin-bottom: 1rem;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .suggestion-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
  }
  
  .suggestion-card {
    padding: 1rem;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
  }
  
  .suggestion-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-color: var(--accent);
  }
  
  .suggestion-query {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }
  
  .suggestion-reason {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
  
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 300px;
    gap: 1rem;
  }
  
  .loading-container p {
    color: var(--text-secondary);
  }
  
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-secondary);
  }
  
  .empty-state h3 {
    margin-bottom: 0.5rem;
    color: var(--text-primary);
  }
  
  .feed-items {
    display: grid;
    gap: 1.5rem;
  }
  
  .load-more {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
  }
  
  .load-more button {
    padding: 0.75rem 2rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .load-more button:hover:not(:disabled) {
    background: var(--bg-hover);
  }
  
  .load-more button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>