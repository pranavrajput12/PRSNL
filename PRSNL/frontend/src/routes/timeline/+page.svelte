<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte';
  import { getTimeline } from '$lib/api';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import SkeletonLoader from '$lib/components/SkeletonLoader.svelte';
  import Icon from '$lib/components/Icon.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import TagList from '$lib/components/TagList.svelte';
  import { browser } from '$app/environment';
  import { mediaSettings, recordMemoryUsage } from '$lib/stores/media';

  type Item = {
    id: string;
    title: string;
    url?: string;
    summary?: string; // Make summary optional since it might be null
    createdAt: string;
    tags: string[];
    type?: string;
    item_type?: string;
    file_path?: string;
    thumbnail_url?: string;
    duration?: number;
    platform?: string;
    status?: string;
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
  let visibleItems = new Set<string>();
  let videoObserver: IntersectionObserver | null = null;
  
  // Virtual scrolling variables
  let virtualScrollEnabled = false;
  let visibleGroupIndices: number[] = [];
  let viewportHeight = 0;
  let scrollPosition = 0;
  let itemHeights: Record<string, number> = {};
  let groupHeights: number[] = [];
  let totalHeight = 0;
  let bufferSize = 3; // Number of groups to render above and below visible area
  let resizeObserver: ResizeObserver | null = null;
  let performanceMetricsInterval: number | null = null;

  onMount(async () => {
    console.log('Starting to load data...');
    
    // First, let's check the debug endpoint
    try {
      const debugResponse = await fetch('/api/admin/debug/items');
      const debugData = await debugResponse.json();
      console.log('[DEBUG] Items in database:', debugData);
    } catch (e) {
      console.error('[DEBUG] Failed to fetch debug data:', e);
    }
    
    loadTimeline(true);
    
    if (browser) {
      // Set up video lazy loading
      setupVideoLazyLoading();
      
      // Set up virtual scrolling
      if (virtualScrollEnabled) {
        setupVirtualScroll();
      } else {
        setupInfiniteScroll();
      }
      
      // Set up performance monitoring
      if ($mediaSettings.logPerformanceMetrics) {
        performanceMetricsInterval = window.setInterval(() => {
          recordMemoryUsage();
        }, 10000); // Record every 10 seconds
      }
      
      // Set up resize observer to recalculate heights when window resizes
      resizeObserver = new ResizeObserver(debounce(() => {
        calculateHeights();
        updateVisibleGroups();
      }, 200));
      
      if (scrollContainer) {
        resizeObserver.observe(scrollContainer);
      }
    }
  });
  
  onDestroy(() => {
    if (videoObserver) {
      videoObserver.disconnect();
    }
    
    if (resizeObserver) {
      resizeObserver.disconnect();
    }
    
    if (performanceMetricsInterval !== null) {
      window.clearInterval(performanceMetricsInterval);
    }
  });
  
  function setupVideoLazyLoading() {
    videoObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          const id = entry.target.getAttribute('data-item-id');
          if (id) {
            if (entry.isIntersecting) {
              visibleItems = visibleItems.add(id);
            }
          }
        });
        visibleItems = new Set(visibleItems); // Trigger reactivity
      },
      { threshold: 0.1, rootMargin: '100px' }
    );
  }

  async function loadTimeline(reset = false) {
    try {
      if (reset) {
        page = 1;
        groups = [];
        hasMore = true;
        visibleGroupIndices = [];
        groupHeights = [];
        totalHeight = 0;
      }
      
      if (!hasMore || isLoading) return;
      
      isLoading = true;
      error = null;
      
      console.log('[Timeline] Loading page:', page);
      
      // Direct API call for debugging
      try {
        const directResponse = await fetch(`/api/timeline?page=${page}`);
        const directData = await directResponse.json();
        console.log('[Timeline] Direct API response:', directData);
      } catch (e) {
        console.error('[Timeline] Direct API call failed:', e);
      }
      
      const response = await getTimeline(page);
      console.log('[Timeline] Response received:', response);
      
      if (response && response.items && response.items.length > 0) {
        console.log('[Timeline] Items received:', response.items.length);
        console.log('[Timeline] First item:', response.items[0]);
        
        const newGroups = groupByDate(response.items);
        console.log('[Timeline] Groups created:', newGroups);
        
        if (reset) {
          groups = newGroups;
        } else {
          groups = mergeGroups(groups, newGroups);
        }
        
        console.log('[Timeline] Total groups after merge:', groups.length);
        console.log('[Timeline] All groups:', groups);
        
        hasMore = response.total > (page * response.pageSize);
        page += 1;
        
        // Recalculate heights for virtual scrolling after DOM update
        if (virtualScrollEnabled) {
          await tick(); // Wait for DOM update
          calculateHeights();
          updateVisibleGroups();
        }
      } else {
        console.log('[Timeline] No items received or empty response');
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
    console.log('[groupByDate] Input items:', items);
    const grouped: Record<string, TimelineGroup> = {};
    
    items.forEach((item: Item) => {
      console.log('[groupByDate] Processing item:', item);
      console.log('[groupByDate] createdAt value:', item.createdAt);
      
      const date = new Date(item.createdAt);
      console.log('[groupByDate] Parsed date:', date);
      
      const dateKey = date.toDateString();
      console.log('[groupByDate] Date key:', dateKey);
      
      if (!grouped[dateKey]) {
        grouped[dateKey] = {
          date: dateKey,
          items: []
        };
      }
      
      grouped[dateKey].items.push(item);
    });

    const result = Object.values(grouped);
    console.log('[groupByDate] Final grouped result:', result);
    return result;
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

  // Debounce utility function to limit how often a function runs
  function debounce(func: Function, wait: number) {
    let timeout: number | null = null;
    return function(...args: any[]) {
      const later = () => {
        timeout = null;
        func(...args);
      };
      if (timeout !== null) {
        clearTimeout(timeout);
      }
      timeout = window.setTimeout(later, wait);
    };
  }

  function setupVirtualScroll() {
    // Get reference to the scroll container
    scrollContainer = document.querySelector('.timeline-content');
    if (!scrollContainer) {
      console.error('Scroll container not found');
      return;
    }
    
    // Initial calculations
    viewportHeight = window.innerHeight;
    
    // Set up scroll event listener with debounce
    scrollContainer.addEventListener('scroll', debounce(() => {
      scrollPosition = scrollContainer?.scrollTop || 0;
      updateVisibleGroups();
      
      // Load more content when approaching the bottom
      const scrollBottom = scrollPosition + viewportHeight;
      const scrollThreshold = totalHeight - (viewportHeight * 1.5);
      
      if (scrollBottom > scrollThreshold && hasMore && !isLoading) {
        loadTimeline();
      }
    }, 50));
    
    // Initial height calculation after a short delay to ensure DOM is ready
    setTimeout(() => {
      calculateHeights();
      updateVisibleGroups();
    }, 200);
    
    // Update viewport height on window resize
    window.addEventListener('resize', debounce(() => {
      viewportHeight = window.innerHeight;
      updateVisibleGroups();
    }, 200));
  }
  
  function calculateHeights() {
    if (!scrollContainer || groups.length === 0) return;
    
    // Reset heights
    groupHeights = [];
    totalHeight = 0;
    
    // Calculate heights for each group
    groups.forEach((group, index) => {
      const groupElement = scrollContainer?.querySelector(`[data-group-index="${index}"]`);
      if (groupElement) {
        const height = groupElement.getBoundingClientRect().height;
        groupHeights[index] = height;
        totalHeight += height;
      } else {
        // Estimate height if element is not rendered
        const estimatedHeight = 200 + (group.items.length * 150);
        groupHeights[index] = estimatedHeight;
        totalHeight += estimatedHeight;
      }
    });
  }
  
  function updateVisibleGroups() {
    if (!scrollContainer || groups.length === 0) return;
    
    scrollPosition = scrollContainer.scrollTop;
    const viewportBottom = scrollPosition + viewportHeight;
    
    // Find which groups are visible in the viewport
    let currentPosition = 0;
    let newVisibleIndices: number[] = [];
    
    for (let i = 0; i < groups.length; i++) {
      const groupHeight = groupHeights[i] || 0;
      const groupTop = currentPosition;
      const groupBottom = groupTop + groupHeight;
      
      // Check if group is visible or within buffer
      if (
        (groupBottom >= scrollPosition - (bufferSize * viewportHeight) && 
         groupTop <= viewportBottom + (bufferSize * viewportHeight)) ||
        // Always include first and last few groups for smoother scrolling
        i < 2 || i >= groups.length - 2
      ) {
        newVisibleIndices.push(i);
      }
      
      currentPosition += groupHeight;
    }
    
    // Update visible groups if changed
    if (JSON.stringify(newVisibleIndices) !== JSON.stringify(visibleGroupIndices)) {
      visibleGroupIndices = newVisibleIndices;
    }
  }
  
  function setupInfiniteScroll() {
    // Fallback for when virtual scrolling is disabled
    setTimeout(() => {
      const sentinel = document.getElementById('scroll-sentinel');
      if (!sentinel) {
        console.error('Scroll sentinel not found');
        return;
      }
      
      const observer = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting && hasMore && !isLoading) {
            loadTimeline();
          }
        },
        { threshold: 0.1 }
      );
      
      observer.observe(sentinel);
    }, 100);
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
  
  // Action to observe video items for lazy loading
  function observeVideo(node: HTMLElement) {
    if (videoObserver && node.getAttribute('data-item-id')) {
      videoObserver.observe(node);
      
      return {
        destroy() {
          if (videoObserver) {
            videoObserver.unobserve(node);
          }
        }
      };
    }
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

    <div class="timeline-content" class:compact={viewMode === 'compact'} bind:this={scrollContainer}>
      <!-- Debug info -->
      <!-- <div style="background: yellow; padding: 10px; margin-bottom: 10px;">
        Debug: groups.length = {groups.length}, isLoading = {isLoading}, hasMore = {hasMore}
        <button 
          style="margin-left: 10px; padding: 5px 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;"
          on:click={async () => {
            try {
              const response = await fetch('/api/admin/test/create-item', { method: 'POST' });
              const data = await response.json();
              console.log('Test item created:', data);
              alert('Test item created! Refresh the page to see it.');
            } catch (e) {
              console.error('Failed to create test item:', e);
              alert('Failed to create test item. Check console.');
            }
          }}
        >
          Create Test Item
        </button>
      </div> -->
      
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
        {#if virtualScrollEnabled}
          <!-- Virtual scrolling spacer to maintain scroll position -->
          <div class="virtual-scroll-spacer" style="height: {totalHeight}px;"></div>
          
          <!-- Only render visible groups -->
          {#each visibleGroupIndices as groupIndex (groupIndex)}
            {#if groups[groupIndex]}
              <div 
                class="timeline-group" 
                data-group-index={groupIndex}
                style="position: absolute; top: {groupHeights.slice(0, groupIndex).reduce((sum, h) => sum + h, 0)}px; width: 100%;"
              >
                <div class="date-separator">
                  <h2>{formatDate(groups[groupIndex].date)}</h2>
                  <div class="separator-line"></div>
                </div>
                
                <div class="timeline-items">
                  {#each groups[groupIndex].items as item, itemIndex}
                    <div 
                      class="timeline-item {viewMode}"
                      data-item-id={item.id}
                      use:observeVideo
                    >
                      <div class="item-time">
                        {getRelativeTime(item.createdAt)}
                        {#if item.item_type === 'video'}
                          <span class="item-type video">
                            <Icon name="video" size="small" />
                            Video
                          </span>
                        {/if}
                      </div>
                      
                      <div class="item-content">
                        <div class="item-header">
                          <a href="/item/{item.id}" class="item-title">
                            {item.title}
                            {#if item.status === 'pending'}
                              <span class="status-badge pending">
                                <Spinner size="tiny" />
                                Processing
                              </span>
                            {/if}
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
                              src={`/api/videos/${item.id}/stream`}
                              thumbnail={item.thumbnail_url}
                              thumbnailUrl={item.thumbnail_url}
                              title={item.title}
                              duration={item.duration}
                              platform={item.platform}
                              lazyLoad={true}
                              autoplay={false}
                              videoId={item.id}
                            />
                          </div>
                        {:else if viewMode !== 'compact'}
                          {#if item.status === 'pending'}
                            <p class="item-summary pending">Processing content...</p>
                          {:else}
                            <p class="item-summary">{item.summary || ''}</p>
                          {/if}
                        {/if}
                        
                        <TagList tags={item.tags} itemId={item.id} />
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          {/each}
        {:else}
          <!-- Regular rendering without virtual scrolling -->
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
                    data-item-id={item.id}
                    use:observeVideo
                  >
                    <div class="item-time">
                      {getRelativeTime(item.createdAt)}
                      {#if item.item_type === 'video'}
                        <span class="item-type video">
                          <Icon name="video" size="small" />
                          Video
                        </span>
                      {/if}
                    </div>
                    
                    <div class="item-content">
                      <div class="item-header">
                        <a href="/item/{item.id}" class="item-title">
                          {item.title}
                          {#if item.status === 'pending'}
                            <span class="status-badge pending">
                              <Spinner size="tiny" />
                              Processing
                            </span>
                          {/if}
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
                            src={`/api/videos/${item.id}/stream`}
                            thumbnail={item.thumbnail_url}
                            thumbnailUrl={item.thumbnail_url}
                            title={item.title}
                            duration={item.duration}
                            platform={item.platform}
                            lazyLoad={true}
                            autoplay={false}
                            videoId={item.id}
                          />
                        </div>
                      {:else if viewMode !== 'compact'}
                        {#if item.status === 'pending'}
                          <p class="item-summary pending">Processing content...</p>
                        {:else if item.summary}
                          <p class="item-summary">{item.summary}</p>
                        {/if}
                      {/if}
                      
                      <TagList tags={item.tags} itemId={item.id} />
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          {/each}
        {/if}
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
    display: flex;
    flex-direction: column;
    height: 100%;
    max-width: 1000px;
    margin: 0 auto;
    padding: 0 1rem;
  }
  
  .timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 0;
    border-bottom: 1px solid var(--border-color);
  }
  
  .timeline-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 0;
  }
  
  .timeline-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .timeline-content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem 0;
    position: relative; /* Required for virtual scrolling */
  }
  
  /* Virtual scrolling styles */
  .virtual-scroll-spacer {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    z-index: -1;
    pointer-events: none;
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
    opacity: 1; /* Changed from 0 to 1 as fallback */
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
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 1.5rem;
    padding: 1.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    transition: all var(--transition-base);
    animation: fadeIn var(--transition-slow) ease-out forwards;
    opacity: 1;
    position: relative;
    overflow: hidden;
  }
  
  .timeline-item::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: var(--accent);
    opacity: 0;
    transition: opacity var(--transition-base);
  }
  
  .timeline-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent);
  }
  
  .timeline-item:hover::before {
    opacity: 1;
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
  
  .item-summary.pending {
    color: var(--text-muted);
    font-style: italic;
  }
  
  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.125rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 500;
    border-radius: 100px;
    margin-left: 0.5rem;
  }
  
  .status-badge.pending {
    background: rgba(255, 170, 0, 0.1);
    color: #ff9500;
    border: 1px solid rgba(255, 170, 0, 0.3);
  }
  
  .item-video {
    margin: 1rem 0;
    max-width: 600px;
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    transition: transform var(--transition-base), box-shadow var(--transition-base);
    background: #000;
  }
  
  .item-video:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
  }
  
  .item-type {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 12px;
    margin-left: 8px;
  }
  
  .item-type.video {
    background-color: var(--man-united-red);
    color: white;
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

  /* Animation keyframes */
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>