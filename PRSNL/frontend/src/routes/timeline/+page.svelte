<script lang="ts">
  import { onMount } from 'svelte';
  import { getTimeline } from '$lib/api';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  
  interface TimelineItem {
    id: string;
    title: string;
    url?: string;
    snippet: string;
    created_at: string;
    tags: string[];
  }
  
  interface TimelineGroup {
    date: string;
    items: TimelineItem[];
  }
  
  let groups: TimelineGroup[] = [];
  let isLoading = true;
  let currentPage = 1;
  let hasMore = true;
  let error: Error | null = null;
  
  onMount(() => {
    loadTimeline();
  });
  
  async function loadTimeline() {
    try {
      error = null;
      const data = await getTimeline(currentPage);
      
      // Group items by date
      const grouped = data.items.reduce((acc: any, item: TimelineItem) => {
        const date = new Date(item.created_at).toLocaleDateString();
        if (!acc[date]) {
          acc[date] = [];
        }
        acc[date].push(item);
        return acc;
      }, {});
      
      // Convert to array format
      const newGroups = Object.entries(grouped).map(([date, items]) => ({
        date,
        items: items as TimelineItem[]
      }));
      
      if (currentPage === 1) {
        groups = newGroups;
      } else {
        groups = [...groups, ...newGroups];
      }
      
      hasMore = data.hasMore;
      isLoading = false;
    } catch (err) {
      console.error('Timeline error:', err);
      error = err as Error;
      isLoading = false;
    }
  }
  
  function loadMore() {
    if (!hasMore || isLoading) return;
    currentPage++;
    loadTimeline();
  }
  
  // Infinite scroll
  function handleScroll(e: Event) {
    const element = e.target as HTMLElement;
    if (element.scrollHeight - element.scrollTop <= element.clientHeight + 100) {
      loadMore();
    }
  }
</script>

<div class="container">
  <h1>Timeline</h1>
  <p class="subtitle">Your knowledge vault over time</p>
  
  <div class="timeline" on:scroll={handleScroll}>
    {#if error}
      <ErrorMessage 
        message="Failed to load timeline" 
        details={error.message} 
        retry={loadTimeline} 
        dismiss={() => error = null} 
      />
    {:else if isLoading && currentPage === 1}
      <div class="loading">
        <Spinner size="medium" center message="Loading timeline..." />
      </div>
    {:else if groups.length === 0}
      <div class="empty-state">
        <p>No items in your vault yet</p>
        <a href="/capture" class="cta">Capture your first item</a>
      </div>
    {:else}
      {#each groups as group}
        <div class="timeline-group">
          <h2 class="date-header">{group.date}</h2>
          <div class="timeline-items">
            {#each group.items as item}
              <a href="/item/{item.id}" class="timeline-item">
                <div class="time">
                  {new Date(item.created_at).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </div>
                <div class="content">
                  <h3>{item.title}</h3>
                  {#if item.url}
                    <div class="url">{new URL(item.url).hostname}</div>
                  {/if}
                  <p>{item.snippet}</p>
                  {#if item.tags.length > 0}
                    <div class="tags">
                      {#each item.tags as tag}
                        <span class="tag">#{tag}</span>
                      {/each}
                    </div>
                  {/if}
                </div>
              </a>
            {/each}
          </div>
        </div>
      {/each}
      
      {#if hasMore}
        <div class="load-more">
          <button on:click={loadMore} disabled={isLoading}>
            {#if isLoading}
              <Spinner size="small" />
              <span>Loading...</span>
            {:else}
              Load more
            {/if}
          </button>
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .container {
    max-width: 800px;
    margin: 2rem auto;
    padding: 0 1rem;
    height: calc(100vh - 100px);
    display: flex;
    flex-direction: column;
  }
  
  h1 {
    text-align: center;
    margin-bottom: 0.5rem;
  }
  
  .subtitle {
    text-align: center;
    color: var(--text-secondary);
    margin-bottom: 2rem;
  }
  
  .timeline {
    flex: 1;
    overflow-y: auto;
    padding-right: 0.5rem;
  }
  
  .timeline-group {
    margin-bottom: 2rem;
  }
  
  .date-header {
    font-size: 1.125rem;
    color: var(--text-secondary);
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
  }
  
  .timeline-items {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .timeline-item {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    transition: all 0.2s;
  }
  
  .timeline-item:hover {
    background: var(--bg-tertiary);
    border-color: var(--accent);
  }
  
  .time {
    flex-shrink: 0;
    color: var(--text-muted);
    font-size: 0.875rem;
    font-family: var(--font-mono);
    padding-top: 0.125rem;
  }
  
  .content {
    flex: 1;
    min-width: 0;
  }
  
  .content h3 {
    margin: 0 0 0.25rem;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .url {
    font-size: 0.75rem;
    color: var(--accent);
    margin-bottom: 0.5rem;
  }
  
  .content p {
    margin: 0 0 0.5rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
    line-height: 1.5;
  }
  
  .tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .tag {
    font-size: 0.75rem;
    color: var(--text-muted);
  }
  
  .loading,
  .empty-state {
    text-align: center;
    padding: 3rem;
    color: var(--text-secondary);
  }
  
  .cta {
    display: inline-block;
    margin-top: 1rem;
    padding: 0.75rem 1.5rem;
    background: var(--accent);
    color: white;
    border-radius: var(--radius);
    transition: background 0.2s;
  }
  
  .cta:hover {
    background: var(--accent-hover);
  }
  
  .load-more {
    text-align: center;
    padding: 2rem;
  }
  
  .load-more button {
    padding: 0.75rem 2rem;
  }
</style>