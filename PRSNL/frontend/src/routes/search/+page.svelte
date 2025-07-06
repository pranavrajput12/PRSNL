<script lang="ts">
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import { searchItems } from '$lib/api';
  
  type SearchResult = {
    id: string;
    title: string;
    url?: string;
    snippet: string;
    tags: string[];
    created_at: string;
    type?: string;
  };
  
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
  let showFilters = false;

  onMount(() => {
    // Load recent searches from localStorage
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      try {
        recentSearches = JSON.parse(saved);
      } catch (e: unknown) {
        console.error('Error parsing recent searches', e);
      }
    }
  });

  onMount(() => {
    searchInput?.focus();
  });

  function addRecentSearch(query: string): void {
    const trimmed = query.trim();
    if (!trimmed) return;
    
    // Remove if already exists
    recentSearches = recentSearches.filter(s => s !== trimmed);
    
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
      // Save to recent searches
      addRecentSearch(query.trim());

      // Search using the API
      const response = await searchItems(query);
      
      if (response && response.items) {
        results = response.items.map((item: any) => ({
          id: item.id,
          title: item.title,
          url: item.url,
          snippet: item.summary,
          tags: item.tags,
          created_at: item.createdAt,
          type: item.type
        }));
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
      if (selectedIndex < results.length - 1) {
        selectedIndex++;
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (selectedIndex > 0) {
        selectedIndex--;
      }
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      const selectedItem = results[selectedIndex];
      if (selectedItem?.url) {
        window.open(selectedItem.url, '_blank');
      }
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
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  function clearFilters() {
    dateFilter = '';
    typeFilter = '';
    tagsFilter = '';
    if (query) handleSearch();
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="container animate-in">
  <div class="search-container">
    <div class="search-header">
      <h1 class="gradient-text">Search Everything</h1>
      <p class="subtitle">Find any knowledge you've captured in seconds</p>
    </div>

    {#if error}
      <ErrorMessage 
        message="Search failed" 
        details={error.message} 
        retry={handleSearch} 
        dismiss={() => error = null} 
      />
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
          placeholder="Search your knowledge base..."
          on:input={handleSearchInput}
          on:keydown={handleKeyDown}
          class="search-input"
        />
        
        <div class="search-actions">
          {#if isLoading}
            <div class="search-spinner">
              <Spinner size="small" />
            </div>
          {/if}
          
          <button 
            class="filter-toggle {showFilters ? 'active' : ''}" 
            on:click={() => showFilters = !showFilters}
            title="Toggle filters"
          >
            <Icon name="filter" size="small" />
          </button>
        </div>
      </div>

      {#if showFilters}
        <div class="filters animate-slide">
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
      {#if results.length > 0}
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
            >
              <div class="result-icon">
                <Icon name="external-link" size="small" color="var(--accent)" />
              </div>
              
              <div class="result-content">
                <div class="result-title">
                  {@html highlightText(result.title, query)}
                </div>
                <div class="result-snippet">
                  {@html highlightText(result.snippet, query)}
                </div>
                <time>{new Date(result.created_at).toLocaleDateString()}</time>
                
                {#if result.tags?.length > 0}
                  <div class="result-tags">
                    {#each result.tags as tag}
                      <span class="tag">
                        <Icon name="tag" size="small" />
                        {tag}
                      </span>
                    {/each}
                  </div>
                {/if}
              </div>
              
              <div class="result-arrow">
                <Icon name="arrow-right" size="small" />
              </div>
            </a>
          {/each}
        </div>
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
    outline: none;
    font-size: 1.125rem;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .search-input::placeholder {
    color: var(--text-muted);
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
    
    .result-header {
      flex-direction: column;
      align-items: start;
      gap: 0.25rem;
    }
    
    .result-header time {
      margin-left: 0;
    }
    
    .tips-grid {
      grid-template-columns: 1fr;
    }
  }
</style>