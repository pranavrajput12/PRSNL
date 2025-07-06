<script lang="ts">
  import { onMount } from 'svelte';
  import { getTimeline } from '$lib/api';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import SkeletonLoader from '$lib/components/SkeletonLoader.svelte';
  import Icon from '$lib/components/Icon.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';

  type Item = {
    id: string;
    title: string;
    url?: string;
    summary: string;
    createdAt: string;
    tags: string[];
    type?: string;
    item_type?: string;
    file_path?: string;
    thumbnail_url?: string;
    duration?: number;
    platform?: string;
  };

  type TimelineGroup = {
    date: string;
    items: Item[];
  };

  let groups: TimelineGroup[] = [];
  let isLoading = false;
  let hasMore = true;
  let page = 1;
  let error: Error | null = null;
  let viewMode = 'card'; // card, compact, detailed
  let showFilters = false;
  let dateFilter = '';
  let typeFilter = '';
  let tagsFilter = '';
  let scrollContainer: HTMLElement | null = null;

  onMount(() => {
    loadTimeline(true);
    setupInfiniteScroll();
  });

  async function loadTimeline(reset = false) {
    try {
      if (reset) {
        page = 1;
        groups = [];
        hasMore = true;
      }
      
      if (!hasMore || isLoading) return;
      
      isLoading = true;
      error = null;
      
      const response = await getTimeline(page);
      
      if (response && response.items && response.items.length > 0) {
        const newGroups = groupByDate(response.items);
        
        if (reset) {
          groups = newGroups;
        } else {
          groups = mergeGroups(groups, newGroups);
        }
        
        hasMore = response.total > (page * response.pageSize);
        page += 1;
      } else {
        hasMore = false;
      }
    } catch (err) {
      console.error('Error loading timeline:', err);
      error = err instanceof Error ? err : new Error(String(err));
    } finally {
      isLoading = false;
    }
  }

  function groupByDate(items: Item[]): TimelineGroup[] {
    const grouped: Record<string, TimelineGroup> = {};
    
    items.forEach((item: Item) => {
      const date = new Date(item.createdAt);
      const dateKey = date.toDateString();
      
      if (!grouped[dateKey]) {
        grouped[dateKey] = {
          date: dateKey,
          items: []
        };
      }
      
      grouped[dateKey].items.push(item);
    });

    return Object.values(grouped);
  }

  function mergeGroups(existing: TimelineGroup[], newGroups: TimelineGroup[]): TimelineGroup[] {
    const merged = [...existing];
    
    newGroups.forEach((newGroup: TimelineGroup) => {
      const existingIndex = merged.findIndex(g => g.date === newGroup.date);
      if (existingIndex >= 0) {
        merged[existingIndex].items.push(...newGroup.items);
      } else {
        merged.push(newGroup);
      }
    });

    return merged;
  }

  function setupInfiniteScroll() {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoading) {
          loadTimeline();
        }
      },
      { threshold: 0.1 }
    );

    // Observe sentinel element
    const sentinel = document.createElement('div');
    sentinel.id = 'scroll-sentinel';
    document.body.appendChild(sentinel);
    observer.observe(sentinel);

    return () => {
      observer.disconnect();
      document.getElementById('scroll-sentinel')?.remove();
    };
  }

  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
    }
  }

  function getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else {
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
    }
  }

  function handleFilter() {
    // Reload with filters
    loadTimeline(true);
  }

  function clearFilters() {
    dateFilter = '';
    typeFilter = '';
    tagsFilter = '';
    loadTimeline(true);
  }

  function deleteItem(itemId: string): void {
    // Remove item from timeline
    groups = groups.map(group => ({
      ...group,
      items: group.items.filter(item => item.id !== itemId)
    })).filter(group => group.items.length > 0);
  }
</script>

<div class="container animate-in">
  <div class="timeline-container">
    <div class="timeline-header">
      <div class="header-content">
        <h1 class="gradient-text">Timeline</h1>
        <p class="subtitle">Browse your captured knowledge chronologically</p>
      </div>
      
      <div class="header-actions">
        <div class="view-modes">
          <button 
            class="view-mode {viewMode === 'compact' ? 'active' : ''}"
            on:click={() => viewMode = 'compact'}
            title="Compact view"
          >
            <Icon name="timeline" size="small" />
          </button>
          <button 
            class="view-mode {viewMode === 'card' ? 'active' : ''}"
            on:click={() => viewMode = 'card'}
            title="Card view"
          >
            <Icon name="search" size="small" />
          </button>
        </div>
        
        <button 
          class="filter-toggle {showFilters ? 'active' : ''}"
          on:click={() => showFilters = !showFilters}
          title="Toggle filters"
        >
          <Icon name="filter" size="small" />
          Filters
        </button>
      </div>
    </div>

    {#if error}
      <ErrorMessage 
        message="Failed to load timeline" 
        details={error.message} 
        retry={() => loadTimeline(true)} 
        dismiss={() => error = null} 
      />
    {/if}

    {#if showFilters}
      <div class="filters animate-slide">
        <div class="filter-group">
          <label for="date-filter">
            <Icon name="calendar" size="small" />
            Date
          </label>
          <select id="date-filter" bind:value={dateFilter} on:change={handleFilter}>
            <option value="">All time</option>
            <option value="today">Today</option>
            <option value="week">This week</option>
            <option value="month">This month</option>
            <option value="year">This year</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="type-filter">
            <Icon name="link" size="small" />
            Type
          </label>
          <select id="type-filter" bind:value={typeFilter} on:change={handleFilter}>
            <option value="">All types</option>
            <option value="article">Articles</option>
            <option value="video">Videos</option>
            <option value="note">Notes</option>
            <option value="bookmark">Bookmarks</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="tags-filter">
            <Icon name="tag" size="small" />
            Tags
          </label>
          <input
            id="tags-filter"
            bind:value={tagsFilter}
            on:input={handleFilter}
            type="text"
            placeholder="Filter by tags..."
            class="tag-filter"
          />
        </div>

        <button class="btn-ghost" on:click={clearFilters}>
          <Icon name="close" size="small" />
          Clear filters
        </button>
      </div>
    {/if}

    <div class="timeline-content" class:compact={viewMode === 'compact'}>
      {#if groups.length === 0 && !isLoading}
        <div class="empty-state">
          <div class="empty-icon animate-pulse">
            <Icon name="timeline" size="large" color="var(--text-muted)" />
          </div>
          <h3>No items yet</h3>
          <p>Start capturing content to build your timeline</p>
          <button class="btn-red" on:click={() => window.location.href = '/capture'}>
            <Icon name="plus" size="small" />
            Capture your first item
          </button>
        </div>
      {:else}
        {#each groups as group, groupIndex}
          <div class="timeline-group" style="animation-delay: {groupIndex * 100}ms">
            <div class="date-separator">
              <h2>{formatDate(group.date)}</h2>
              <div class="separator-line"></div>
            </div>
            
            <div class="timeline-items">
              {#each group.items as item, itemIndex}
                <div 
                  class="timeline-item {viewMode}" 
                  style="animation-delay: {(groupIndex * 100) + (itemIndex * 50)}ms"
                >
                  <div class="item-time">
                    {getRelativeTime(item.createdAt)}
                  </div>
                  
                  <div class="item-content">
                    <div class="item-header">
                      <a href="/item/{item.id}" class="item-title">
                        {item.title}
                      </a>
                      
                      <div class="item-actions">
                        <button class="action-btn" title="Edit">
                          <Icon name="edit" size="small" />
                        </button>
                        <button class="action-btn delete" title="Delete" on:click={() => deleteItem(item.id)}>
                          <Icon name="close" size="small" />
                        </button>
                      </div>
                    </div>
                    
                    {#if item.url}
                      <div class="item-url">
                        <Icon name="external-link" size="small" />
                        <a href={item.url} target="_blank" rel="noopener">
                          {new URL(item.url).hostname}
                        </a>
                      </div>
                    {/if}
                    
                    {#if item.item_type === 'video' && item.file_path && viewMode !== 'compact'}
                      <div class="item-video">
                        <VideoPlayer 
                          src={item.file_path}
                          thumbnail={item.thumbnail_url}
                          title={item.title}
                          duration={item.duration}
                        />
                      </div>
                    {:else if viewMode !== 'compact'}
                      <p class="item-summary">{item.summary}</p>
                    {/if}
                    
                    {#if item.tags?.length > 0}
                      <div class="item-tags">
                        {#each item.tags as tag}
                          <span class="tag">
                            <Icon name="tag" size="small" />
                            {tag}
                          </span>
                        {/each}
                      </div>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/each}
      {/if}

      {#if isLoading}
        <SkeletonLoader type="timeline" count={3} />
      {/if}
    </div>

    <!-- Infinite scroll sentinel -->
    <div id="scroll-sentinel" style="height: 1px;"></div>
  </div>
</div>

<style>
  .timeline-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }
  
  .timeline-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 3rem;
    flex-wrap: wrap;
    gap: 1rem;
  }
  
  .header-content h1 {
    font-size: 3rem;
    margin-bottom: 0.5rem;
    font-weight: 800;
  }
  
  .subtitle {
    color: var(--text-secondary);
    font-size: 1.25rem;
    font-weight: 500;
    margin: 0;
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .view-modes {
    display: flex;
    gap: 0.25rem;
    background: var(--bg-secondary);
    border-radius: var(--radius);
    padding: 0.25rem;
  }
  
  .view-mode {
    padding: 0.5rem;
    background: transparent;
    border: none;
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    transition: all var(--transition-base);
  }
  
  .view-mode:hover,
  .view-mode.active {
    background: var(--accent);
    color: white;
  }
  
  .filter-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-secondary);
    font-weight: 500;
    transition: all var(--transition-base);
  }
  
  .filter-toggle:hover,
  .filter-toggle.active {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
  }
  
  .filters {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    padding: 1.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 2rem;
  }
  
  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .filter-group label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary);
  }
  
  .filter-group select,
  .tag-filter {
    padding: 0.5rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    font-size: 0.875rem;
  }
  
  .timeline-group {
    margin-bottom: 3rem;
    animation: fadeIn var(--transition-slow) ease-out forwards;
    opacity: 0;
  }
  
  .date-separator {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .date-separator h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    flex-shrink: 0;
  }
  
  .separator-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border), transparent);
  }
  
  .timeline-items {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .timeline-item {
    display: flex;
    gap: 1.5rem;
    padding: 1.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    transition: all var(--transition-base);
    animation: fadeIn var(--transition-slow) ease-out forwards;
    opacity: 0;
  }
  
  .timeline-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent);
  }
  
  .timeline-item.compact {
    padding: 1rem 1.5rem;
  }
  
  .item-time {
    color: var(--text-muted);
    font-size: 0.875rem;
    font-weight: 600;
    min-width: 60px;
    flex-shrink: 0;
  }
  
  .item-content {
    flex: 1;
  }
  
  .item-header {
    display: flex;
    align-items: start;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }
  
  .item-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    text-decoration: none;
    transition: color var(--transition-fast);
  }
  
  .item-title:hover {
    color: var(--accent);
  }
  
  .item-actions {
    display: flex;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity var(--transition-base);
  }
  
  .timeline-item:hover .item-actions {
    opacity: 1;
  }
  
  .action-btn {
    padding: 0.25rem;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-muted);
    transition: all var(--transition-fast);
  }
  
  .action-btn:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  .action-btn.delete:hover {
    background: var(--man-united-red);
    color: white;
    border-color: var(--man-united-red);
  }
  
  .item-url {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
  }
  
  .item-url a {
    color: var(--text-muted);
    font-size: 0.875rem;
    text-decoration: none;
    transition: color var(--transition-fast);
  }
  
  .item-url a:hover {
    color: var(--accent);
  }
  
  .item-summary {
    color: var(--text-secondary);
    font-size: 0.9375rem;
    line-height: 1.6;
    margin: 0 0 1rem;
  }
  
  .item-video {
    margin: 1rem 0;
    max-width: 600px;
  }
  
  .item-tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .tag {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    background: var(--bg-tertiary);
    border-radius: 100px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-weight: 600;
    transition: all var(--transition-fast);
  }
  
  .tag:hover {
    background: var(--accent);
    color: white;
  }
  
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
  }
  
  .empty-icon {
    width: 80px;
    height: 80px;
    background: var(--bg-tertiary);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 2rem;
  }
  
  .empty-state h3 {
    margin: 0 0 0.5rem;
    font-size: 1.5rem;
    color: var(--text-primary);
  }
  
  .empty-state p {
    color: var(--text-secondary);
    font-size: 1.125rem;
    margin-bottom: 2rem;
  }
  
  .btn-red {
    background: var(--man-united-red);
    color: white;
    border: none;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    padding: 1rem 2rem;
    border-radius: var(--radius);
    transition: all var(--transition-base);
  }
  
  .btn-red:hover {
    background: var(--accent-red-hover);
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.3);
    transform: translateY(-2px);
  }
  
  @media (max-width: 768px) {
    .timeline-header {
      flex-direction: column;
      align-items: stretch;
    }
    
    .header-actions {
      justify-content: space-between;
    }
    
    .timeline-item {
      flex-direction: column;
      gap: 0.75rem;
    }
    
    .item-time {
      min-width: auto;
    }
    
    .filters {
      grid-template-columns: 1fr;
    }
  }
</style>