<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { searchItems, getSimilarItems } from '$lib/api';
  import Icon from '$lib/components/Icon.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import SkeletonLoader from '$lib/components/SkeletonLoader.svelte';
  import AsyncBoundary from '$lib/components/AsyncBoundary.svelte';
  import { mediaSettings, recordMemoryUsage } from '$lib/stores/media';
  import type { SearchResult, Item } from '$lib/types/api';

  let query = '';
  let results: SearchResult[] = [];
  let isLoading = false;
  let error: Error | null = null;
  let hasSearched = false;
  let searchTimeout: ReturnType<typeof setTimeout> | undefined;
  let selectedIndex = -1;
  let recentSearches: string[] = [];
  let searchInput: HTMLInputElement | null = null;
  let dateFilter = '';
  let typeFilter = '';
  let tagsFilter = '';
  let videoPlatformFilter = '';
  let showFilters = false;

  // Semantic search options
  let searchMode: 'keyword' | 'semantic' | 'hybrid' = 'keyword';
  let showSimilarItems = false;
  let similarItemsFor: SearchResult | null = null;
  let similarItems: Item[] = [];
  let loadingSimilar = false;

  // Video performance optimization variables
  let visibleItems = new Set<string>();
  let videoObserver: IntersectionObserver | null = null;
  let performanceMetricsInterval: number | null = null;
  let scrollContainer: HTMLElement | null = null;

  // Setup video lazy loading with IntersectionObserver
  function setupVideoLazyLoading() {
    videoObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const id = entry.target.getAttribute('data-item-id');
          if (id) {
            if (entry.isIntersecting) {
              visibleItems.add(id);
            } else {
              visibleItems.delete(id);
            }
          }
        });
        visibleItems = new Set(visibleItems); // Trigger reactivity
      },
      { threshold: 0.1, rootMargin: '100px' }
    );
  }

  // Action to observe video items
  function observeVideo(node: HTMLElement) {
    const itemId = node.getAttribute('data-item-id');
    if (itemId && videoObserver) {
      videoObserver.observe(node);
    }

    return {
      destroy() {
        if (videoObserver && node) {
          videoObserver.unobserve(node);
        }
      }
    };
  }

  onMount(() => {
    if (searchInput) {
      searchInput.focus();
    }
    loadRecentSearches();

    // Set up video lazy loading
    setupVideoLazyLoading();

    // Set up performance monitoring if enabled
    if ($mediaSettings.logPerformanceMetrics) {
      performanceMetricsInterval = window.setInterval(() => {
        recordMemoryUsage();
      }, 5000);
    }

    // Set up scroll container reference
    scrollContainer = document.querySelector('.search-results');
  });

  onDestroy(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    // Clean up video observer
    if (videoObserver) {
      videoObserver.disconnect();
      videoObserver = null;
    }

    // Clean up performance monitoring interval
    if (performanceMetricsInterval) {
      clearInterval(performanceMetricsInterval);
      performanceMetricsInterval = null;
    }
  });

  // Load recent searches from localStorage
  function loadRecentSearches() {
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      try {
        recentSearches = JSON.parse(saved);
      } catch (e) {
        console.error('Error parsing recent searches', e);
        recentSearches = [];
      }
    }
  }

  function addRecentSearch(query: string): void {
    const trimmed = query.trim();
    if (!trimmed) return;

    // Remove if already exists
    recentSearches = recentSearches.filter((s) => s !== trimmed);

    // Add to beginning
    recentSearches = [trimmed, ...recentSearches].slice(0, 5);

    // Save to localStorage
    try {
      localStorage.setItem('recentSearches', JSON.stringify(recentSearches));
    } catch (e: unknown) {
      console.error('Error saving recent searches', e);
    }
  }

  async function handleSearch() {
    if (!query.trim()) {
      results = [];
      hasSearched = false;
      return;
    }

    isLoading = true;
    selectedIndex = -1;
    error = null;
    hasSearched = true;

    try {
      addRecentSearch(query);

      const searchFilters: any = {};
      if (dateFilter) searchFilters.date = dateFilter;
      if (typeFilter) searchFilters.type = typeFilter;
      if (tagsFilter) searchFilters.tags = tagsFilter;

      // Add semantic search parameters
      searchFilters.mode = searchMode;
      searchFilters.limit = 20;

      const data = await searchItems(query, searchFilters);
      console.log('Search results:', data);

      if (data && Array.isArray(data.items)) {
        results = data.items.map((item: any) => ({
          id: item.id,
          title: item.title,
          url: item.url,
          snippet: item.summary,
          tags: item.tags,
          created_at: item.createdAt,
          type: item.type,
          isVideo: item.type === 'video' || (item.tags && item.tags.includes('video')),
          videoPlatform: item.videoPlatform || (item.tags && (item.tags.includes('youtube') ? 'YouTube' : item.tags.includes('instagram') ? 'Instagram' : item.tags.includes('twitter') ? 'Twitter' : item.tags.includes('tiktok') ? 'TikTok' : null)),
          thumbnailUrl: item.thumbnailUrl
        }));

        // Apply video platform filter if selected
        if (videoPlatformFilter) {
          results = results.filter((item) => item.videoPlatform?.toLowerCase() === videoPlatformFilter.toLowerCase());
        }
      } else {
        results = [];
      }
    } catch (err) {
      console.error('Search error:', err);
      error = err instanceof Error ? err : new Error(String(err));
      results = [];
    } finally {
      isLoading = false;
    }
  }

  // Debounced search
  function handleSearchInput() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(handleSearch, 300);
  }

  // Keyboard navigation
  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, results.length - 1);
      document.querySelector(`.result-item[data-index="${selectedIndex}"]`)?.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, -1);
      document.querySelector(`.result-item[data-index="${selectedIndex}"]`)?.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      const url = results[selectedIndex].url;
      if (url) window.location.href = url;
    } else if (e.key === 'Escape') {
      e.preventDefault();
      if (query || results.length > 0) {
        query = '';
        results = [];
        hasSearched = false;
      } else {
        window.location.href = '/';
      }
    }
  }

  function highlightText(text: string, query: string): string {
    if (!query) return text;

    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  function escapeRegExp(string: string): string {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function clearFilters() {
    dateFilter = '';
    typeFilter = '';
    tagsFilter = '';
    videoPlatformFilter = '';
    if (query) handleSearch();
  }

  // Find similar items to a specific result
  async function findSimilar(item: SearchResult) {
    if (!item || !item.id) return;

    similarItemsFor = item;
    showSimilarItems = true;
    loadingSimilar = true;
    similarItems = [];

    try {
      const response = await getSimilarItems(item.id, 5);
      similarItems = response;
    } catch (err) {
      console.error('Error fetching similar items:', err);
    } finally {
      loadingSimilar = false;
    }
  }

  // Close similar items sidebar
  function closeSimilarItems() {
    showSimilarItems = false;
    similarItemsFor = null;
    similarItems = [];
  }

  // Format similarity score as percentage
  function formatSimilarityScore(score: number | undefined): string {
    if (score === undefined) return '';
    return `${Math.round(score * 100)}%`;
  }

  // Get color based on similarity score
  function getSimilarityColor(score: number | undefined): string {
    if (score === undefined) return 'var(--text-muted)';

    if (score >= 0.9) return 'var(--success)';
    if (score >= 0.7) return 'var(--accent)';
    if (score >= 0.5) return 'var(--warning)';
    return 'var(--text-muted)';
  }
</script>

<svelte:window on:keydown={handleKeyDown} />

<div class="container animate-in">
  <div class="search-container">
    <div class="search-header">
      <h1 class="gradient-text">Search Everything</h1>
      <p class="subtitle">Find any knowledge you've captured in seconds</p>
    </div>

    {#if error}
      <ErrorMessage message="Search failed" details={error.message} retry={handleSearch} dismiss={() => error = null} />
    {/if}

    <div class="search-box-container">
      <div class="search-box {isLoading ? 'loading' : ''}">
        <div class="search-icon">
          <Icon name="search" size="medium" color="var(--text-muted)" />
        </div>

        <input
          type="text"
          bind:value={query}
          bind:this={searchInput}
          placeholder="Search for anything..."
          on:input={handleSearchInput}
          on:keydown={(e) => e.key === 'Enter' && handleSearch()}
          autocomplete="off"
        />

        <div class="search-actions">
          {#if isLoading}
            <Spinner size="small" />
          {:else if query}
            <button class="clear-btn" on:click={() => { query = ''; results = []; hasSearched = false; }}>
              <Icon name="close" size="small" />
            </button>
          {/if}

          <button
            class="filter-btn"
            class:active={showFilters}
            on:click={() => showFilters = !showFilters}
            title="Toggle filters"
          >
            <Icon name="filter" size="small" />
          </button>
        </div>
      </div>

      {#if showFilters}
        <div class="filters animate-slide">
          <!-- Search Mode Toggle -->
          <div class="filter-group search-mode">
            <label id="search-mode-label" for="search-mode-group">Search Mode</label>
            <div id="search-mode-group" class="mode-toggle" role="radiogroup" aria-labelledby="search-mode-label">
              <button
                class="mode-btn {searchMode === 'keyword' ? 'active' : ''}"
                on:click={() => { searchMode = 'keyword'; if (query) handleSearch(); }}
                role="radio"
                aria-checked={searchMode === 'keyword'}
              >
                <Icon name="search" size="small" />
                Keyword
              </button>
              <button
                class="mode-btn {searchMode === 'semantic' ? 'active' : ''}"
                on:click={() => { searchMode = 'semantic'; if (query) handleSearch(); }}
                role="radio"
                aria-checked={searchMode === 'semantic'}
              >
                <Icon name="brain" size="small" />
                Semantic
              </button>
              <button
                class="mode-btn {searchMode === 'hybrid' ? 'active' : ''}"
                on:click={() => { searchMode = 'hybrid'; if (query) handleSearch(); }}
                role="radio"
                aria-checked={searchMode === 'hybrid'}
              >
                <Icon name="sparkles" size="small" />
                Hybrid
              </button>
            </div>
          </div>
          <div class="filter-group">
            <label for="date-filter">
              <Icon name="calendar" size="small" />
              Date
            </label>
            <select id="date-filter" bind:value={dateFilter} on:change={handleSearch}>
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
            <select id="type-filter" bind:value={typeFilter} on:change={handleSearch}>
              <option value="">All types</option>
              <option value="url">URLs</option>
              <option value="text">Text</option>
              <option value="file">Files</option>
              <option value="video">Videos</option>
            </select>
          </div>

          {#if typeFilter === 'video'}
            <div class="filter-group">
              <label for="video-platform-filter">
                <Icon name="video" size="small" />
                Platform
              </label>
              <select id="video-platform-filter" bind:value={videoPlatformFilter} on:change={handleSearch}>
                <option value="">All platforms</option>
                <option value="youtube">YouTube</option>
                <option value="instagram">Instagram</option>
                <option value="twitter">Twitter</option>
                <option value="tiktok">TikTok</option>
              </select>
            </div>
          {/if}

          <div class="filter-group">
            <label for="tags-filter">
              <Icon name="tag" size="small" />
              Tags
            </label>
            <input
              id="tags-filter"
              bind:value={tagsFilter}
              on:input={handleSearchInput}
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
    </div>

    <div class="results-container">
      {#if isLoading && hasSearched}
        <SkeletonLoader type="search" count={3} />
      {:else if results.length > 0}
        <div class="results-header">
          <div class="results-count">
            <Icon name="check" size="small" color="var(--success)" />
            Found {results.length} result{results.length !== 1 ? 's' : ''}
          </div>

          <div class="search-tips">
            Use <span class="keyboard-hint">↑↓</span> to navigate, <span class="keyboard-hint">Enter</span> to open
          </div>
        </div>

        <div class="results-list">
          {#each results as result, index}
            <a
              href="/item/{result.id}"
              class="result-item {index === selectedIndex ? 'selected' : ''}"
              on:mouseenter={() => selectedIndex = index}
              style="animation-delay: {index * 50}ms"
              data-index={index}
            >
              <div class="result-icon">
                <Icon name="external-link" size="small" color="var(--accent)" />
              </div>

              <div class="result-content">
                <div class="result-header-row">
                  <h3>
                    {@html highlightText(result.title, query)}
                    {#if result.isVideo}
                      <span class="result-type video">
                        <Icon name="video" size="small" />
                        Video
                        {#if result.videoPlatform}
                          • {result.videoPlatform}
                        {/if}
                      </span>
                    {/if}
                  </h3>

                  <!-- Similarity score for semantic search -->
                  {#if (searchMode === 'semantic' || searchMode === 'hybrid') && result.similarity_score !== undefined}
                    <div class="similarity-score" style="color: {getSimilarityColor(result.similarity_score)}">
                      <div class="score-bar">
                        <div
                          class="score-fill"
                          style="width: {result.similarity_score * 100}%; background-color: {getSimilarityColor(result.similarity_score)}"
                        ></div>
                      </div>
                      <span class="score-text">{formatSimilarityScore(result.similarity_score)}</span>
                    </div>
                  {/if}
                </div>

                <p class="result-snippet">{@html highlightText(result.snippet, query)}</p>

                {#if result.match_type}
                  <div class="match-type-indicator">
                    <span class="match-badge {result.match_type}">
                      <Icon
                        name={result.match_type === 'semantic' ? 'brain' : result.match_type === 'keyword' ? 'search' : 'sparkles'}
                        size="small"
                      />
                      {result.match_type === 'semantic' ? 'Semantic match' : result.match_type === 'keyword' ? 'Keyword match' : 'Semantic & Keyword match'}
                    </span>
                  </div>
                {/if}

                {#if result.tags && result.tags.length > 0}
                  <div class="result-tags">
                    {#each result.tags.slice(0, 5) as tag}
                      <span class="tag">
                        <Icon name="tag" size="small" />
                        {tag}
                      </span>
                    {/each}
                  </div>
                {/if}

                <!-- Find Similar button -->
                <button 
                  class="btn-find-similar" 
                  on:click|preventDefault|stopPropagation={() => findSimilar(result)}
                  type="button"
                >
                  <Icon name="brain" size="small" />
                  Find Similar
                </button>
              </div>

              <div class="result-arrow">
                <Icon name="arrow-right" size="small" />
              </div>
            </a>
          {/each}
        </div>

        <!-- Similar Items Sidebar -->
        {#if showSimilarItems}
          <div class="similar-items-sidebar animate-slide-in">
            <div class="sidebar-header">
              <h3>
                <Icon name="brain" size="small" />
                Similar Items
              </h3>
              <button class="close-btn" on:click={closeSimilarItems}>
                <Icon name="close" size="small" />
              </button>
            </div>

            {#if similarItemsFor}
              <div class="similar-to-item">
                <h4>Similar to:</h4>
                <div class="similar-source">
                  <p class="title">{similarItemsFor.title || 'Untitled'}</p>
                </div>
              </div>
            {/if}

            <div class="similar-items-list">
              {#if loadingSimilar}
                <div class="loading-similar">
                  <Spinner size="medium" />
                  <p>Finding similar items...</p>
                </div>
              {:else if similarItems.length === 0}
                <div class="no-similar-items">
                  <p>No similar items found</p>
                </div>
              {:else}
                {#each similarItems as item}
                  <a href="/items/{item.id}" class="similar-item">
                    <div class="similar-item-content">
                      <h4>{item.title || 'Untitled'}</h4>
                      <p class="snippet">{item.snippet}</p>

                      {#if item.similarity_score !== undefined}
                        <div class="similarity-score" style="color: {getSimilarityColor(item.similarity_score)}">
                          <div class="score-bar">
                            <div
                              class="score-fill"
                              style="width: {item.similarity_score * 100}%; background-color: {getSimilarityColor(item.similarity_score)}"
                            ></div>
                          </div>
                          <span class="score-text">{formatSimilarityScore(item.similarity_score)}</span>
                        </div>
                      {/if}
                    </div>
                  </a>
                {/each}
              {/if}
            </div>
          </div>
        {/if}
      {:else if hasSearched && !isLoading}
        <div class="empty-state">
          <div class="empty-icon animate-pulse">
            <Icon name="search" size="large" color="var(--text-muted)" />
          </div>
          <h3>No results found</h3>
          <p>Try different keywords or check your filters</p>
          <div class="empty-actions">
            <button class="btn-red" on:click={() => window.location.href = '/capture'}>
              <Icon name="plus" size="small" />
              Capture something new
            </button>
            <button class="btn-ghost" on:click={clearFilters}>
              <Icon name="filter" size="small" />
              Clear filters
            </button>
          </div>
        </div>
      {:else if !hasSearched}
        <div class="search-tips-container">
          <div class="tips-grid">
            <div class="tip-card">
              <div class="tip-icon">
                <Icon name="search" size="medium" color="var(--accent)" />
              </div>
              <h4>Smart Search</h4>
              <p>Search across all your captured content, including titles, URLs, and highlights</p>
            </div>

            <div class="tip-card">
              <div class="tip-icon">
                <Icon name="tag" size="medium" color="var(--success)" />
              </div>
              <h4>Use Tags</h4>
              <p>Filter by tags like #important or #work to find specific content quickly</p>
            </div>

            <div class="tip-card">
              <div class="tip-icon">
                <Icon name="filter" size="medium" color="var(--warning)" />
              </div>
              <h4>Advanced Filters</h4>
              <p>Use date and type filters to narrow down your search results</p>
            </div>

            <div class="tip-card">
              <div class="tip-icon">
                <Icon name="sparkles" size="medium" color="var(--info)" />
              </div>
              <h4>Keyboard Shortcuts</h4>
              <p>Navigate with arrow keys, press Enter to open, or Escape to clear</p>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .search-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }

  .search-header {
    text-align: center;
    margin-bottom: 3rem;
  }

  h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
    font-weight: 800;
  }

  .subtitle {
    color: var(--text-secondary);
    font-size: 1.25rem;
    font-weight: 500;
    margin: 0;
  }

  .search-box-container {
    margin-bottom: 2rem;
  }

  .search-box {
    position: relative;
    display: flex;
    align-items: center;
    background: var(--bg-secondary);
    border: 2px solid transparent;
    border-radius: var(--radius-lg);
    padding: 0.75rem 1rem;
    transition: all var(--transition-base);
    box-shadow: var(--shadow-sm);
  }

  .search-box:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.1), var(--shadow-md);
  }

  .search-box.loading {
    border-color: var(--accent);
  }

  .search-icon {
    margin-right: 1rem;
    transition: all var(--transition-base);
  }

  .search-input {
    flex: 1;
    background: transparent;
    border: none;
    font-weight: 400;
  }

  .search-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .search-spinner {
    margin-right: 0.5rem;
  }
  
  .filter-toggle {
    padding: 0.5rem;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
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
    margin-top: 1rem;
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
  
  .results-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
  }
  
  .results-count {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  .search-tips {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-muted);
  }
  
  .results-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .result-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    transition: all var(--transition-base);
    animation: fadeIn var(--transition-slow) ease-out forwards;
    opacity: 0;
    cursor: pointer;
  }
  
  .result-item:hover,
  .result-item.selected {
    background: var(--bg-tertiary);
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }
  
  .result-icon {
    width: 40px;
    height: 40px;
    background: rgba(74, 158, 255, 0.1);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  
  .result-content {
    flex: 1;
  }
  
  .result-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }
  
  .result-header h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.4;
  }
  
  .result-header time {
    color: var(--text-muted);
    font-size: 0.8125rem;
    font-weight: 500;
    flex-shrink: 0;
    margin-left: 1rem;
  }
  
  .result-snippet {
    color: var(--text-secondary);
    font-size: 0.9375rem;
    line-height: 1.6;
    margin: 0 0 0.75rem;
  }
  
  .result-video {
    margin: 0.75rem 0;
    max-width: 400px;
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transition: transform var(--transition-base), box-shadow var(--transition-base);
  }
  
  .result-video:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
  }
  
  .result-type {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 12px;
    margin-left: 8px;
    vertical-align: middle;
  }
  
  .result-type.video {
    background-color: var(--man-united-red);
    color: white;
  }
  
  .result-tags {
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
  
  .result-arrow {
    color: var(--text-muted);
    transition: all var(--transition-fast);
  }
  
  .result-item:hover .result-arrow {
    color: var(--accent);
    transform: translateX(4px);
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
  
  .empty-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .search-tips-container {
    padding: 2rem 0;
  }
  
  .tips-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
  }
  
  .tip-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    text-align: center;
    transition: all var(--transition-base);
    animation: fadeIn var(--transition-slow) ease-out forwards;
    opacity: 0;
  }
  
  .tip-card:nth-child(1) { animation-delay: 100ms; }
  .tip-card:nth-child(2) { animation-delay: 200ms; }
  .tip-card:nth-child(3) { animation-delay: 300ms; }
  .tip-card:nth-child(4) { animation-delay: 400ms; }
  
  .tip-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-md);
    border-color: var(--border);
  }
  
  .tip-icon {
    width: 60px;
    height: 60px;
    background: var(--bg-tertiary);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1rem;
    transition: all var(--transition-base);
  }
  
  .tip-card:hover .tip-icon {
    transform: scale(1.1);
  }
  
  .tip-card h4 {
    margin: 0 0 0.75rem;
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
  }
  
  .tip-card p {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.9375rem;
    line-height: 1.6;
  }
  
  :global(mark) {
    background: rgba(74, 158, 255, 0.3);
    color: inherit;
    padding: 0.1rem 0.2rem;
    border-radius: 3px;
    font-weight: 600;
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
  
  .result-header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 0.5rem;
  }
  
  .result-header-row h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .similar-item .result-snippet {
    margin-bottom: 0.75rem;
    color: var(--text-secondary);
    line-height: 1.5;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    line-clamp: 3;
    -webkit-box-orient: vertical;
  }
  
  .search-results {
    flex: 1;
    padding: 2rem 0;
    display: none;
  }
  
  .search-results.has-results {
    display: block;
  }
  
  .search-results.with-sidebar {
    display: grid;
    grid-template-columns: 1fr 350px;
    gap: 1.5rem;
  }
  
  .search-mode-indicator {
    display: flex;
    align-items: center;
  }
  
  .mode-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .mode-badge.semantic {
    background-color: rgba(var(--accent-rgb), 0.15);
    color: var(--accent);
  }
  
  .mode-badge.hybrid {
    background-color: rgba(var(--success-rgb), 0.15);
    color: var(--success);
  }
  
  .filter-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0.5rem;
    border-radius: var(--radius);
    transition: all var(--transition-fast);
  }
  
  .filter-btn:hover, .filter-btn.active {
    background: var(--bg-tertiary);
    color: var(--accent);
  }
  
  .filter-group.search-mode {
    grid-column: 1 / -1;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1rem;
    margin-bottom: 1rem;
  }
  
  .mode-toggle {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }
  
  .mode-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-fast);
  }
  
  .mode-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
  
  .mode-btn.active {
    background: var(--accent);
    border-color: var(--accent);
    color: white;
  }
  

  
  .similarity-score {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    font-weight: 600;
    white-space: nowrap;
  }
  
  .score-bar {
    width: 60px;
    height: 6px;
    background-color: var(--bg-tertiary);
    border-radius: 3px;
    overflow: hidden;
  }
  
  .score-fill {
    height: 100%;
    border-radius: 3px;
  }
  
  .match-type-indicator {
    margin-bottom: 0.75rem;
  }
  
  .match-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .match-badge.semantic {
    background-color: rgba(var(--accent-rgb), 0.15);
    color: var(--accent);
  }
  
  .match-badge.keyword {
    background-color: rgba(var(--text-muted-rgb), 0.15);
    color: var(--text-muted);
  }
  
  .match-badge.both {
    background-color: rgba(var(--success-rgb), 0.15);
    color: var(--success);
  }
  
  .btn-find-similar {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background-color: rgba(var(--accent-rgb), 0.1);
    color: var(--accent);
    border: none;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    margin-top: 0.5rem;
  }
  
  .btn-find-similar:hover {
    background-color: var(--accent);
    color: white;
  }
  
  @media (max-width: 768px) {
    h1 {
      font-size: 2rem;
    }
    
    .filters {
      grid-template-columns: 1fr;
    }
    
    .results-header {
      flex-direction: column;
      align-items: start;
      gap: 0.5rem;
    }
    
    .result-header-row {
      flex-direction: column;
      align-items: start;
      gap: 0.25rem;
    }
    
    .tips-grid {
      grid-template-columns: 1fr;
    }
    
    .search-results.with-sidebar {
      grid-template-columns: 1fr;
    }
    
    .similar-items-sidebar {
      position: fixed;
      top: 0;
      right: 0;
      bottom: 0;
      width: 100%;
      max-width: 350px;
      z-index: 100;
    }
  }
  /* Similar items sidebar */
  .similar-items-sidebar {
    background: var(--bg-secondary);
    border-radius: var(--radius);
    border: 1px solid var(--border);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: fit-content;
    max-height: calc(100vh - 200px);
  }
  
  .sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--border);
  }
  
  .sidebar-header h3 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 1rem;
  }
  
  .close-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0.25rem;
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .close-btn:hover {
    color: var(--accent);
    background: var(--bg-tertiary);
  }
  
  .similar-to-item {
    padding: 1rem;
    border-bottom: 1px solid var(--border);
  }
  
  .similar-to-item h4 {
    margin: 0 0 0.5rem;
    font-size: 0.875rem;
    color: var(--text-muted);
  }
  
  .similar-source {
    padding: 0.5rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius);
  }
  
  .similar-source .title {
    margin: 0;
    font-weight: 600;
  }
  
  .similar-items-list {
    padding: 1rem;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .loading-similar, .no-similar-items {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem 0;
    color: var(--text-muted);
    text-align: center;
  }
  
  .loading-similar p, .no-similar-items p {
    margin-top: 1rem;
  }
  
  .similar-item {
    display: block;
    padding: 1rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius);
    text-decoration: none;
    color: inherit;
    transition: all var(--transition-fast);
  }
  
  .similar-item:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-sm);
  }
  
  .similar-item h4 {
    margin: 0 0 0.5rem;
    font-size: 0.875rem;
    color: var(--text-primary);
  }
  
  /* Animation for sidebar */
  .animate-slide-in {
    animation: slideIn var(--transition-base) ease-out forwards;
  }
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
</style>