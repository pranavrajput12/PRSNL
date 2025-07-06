<script lang="ts">
  import { onMount } from 'svelte';
  import { searchItems } from '$lib/api';
  import { addRecentSearch } from '$lib/stores/app';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';

  interface SearchResult {
    id: string;
    title: string;
    url?: string;
    snippet: string;
    created_at: string;
    tags: string[];
  }

  let query = '';
  let results: SearchResult[] = [];
  let isLoading = false;
  let selectedIndex = -1;
  let searchInput: HTMLInputElement;
  let dateFilter = '';
  let typeFilter = '';
  let tagsFilter = '';
  let error: Error | null = null;

  onMount(() => {
    searchInput?.focus();
  });

  async function handleSearch() {
    if (!query.trim()) {
      results = [];
      return;
    }

    isLoading = true;
    selectedIndex = -1;
    error = null;

    try {
      // Save to recent searches
      addRecentSearch(query);

      // Call the API
      const response = await searchItems(query, {
        date: dateFilter,
        type: typeFilter,
        tags: tagsFilter
      });

      results = response.items || [];
    } catch (err) {
      console.error('Search error:', err);
      error = err as Error;
      results = [];
    } finally {
      isLoading = false;
    }
  }

  // Debounced search
  let searchTimeout: ReturnType<typeof setTimeout>;
  function handleSearchInput() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(handleSearch, 300);
  }

  // Keyboard navigation
  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, results.length - 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
    } else if (e.key === 'Enter' && results[selectedIndex]) {
      e.preventDefault();
      window.location.href = `/item/${results[selectedIndex].id}`;
    } else if (e.key === 'Escape') {
      e.preventDefault();
      if (query || results.length > 0) {
        query = '';
        results = [];
      } else {
        window.location.href = '/';
      }
    }
  }

  function highlightMatch(text: string, query: string) {
    if (!query) return text;
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="container">
  <div class="search-container">
    <div class="search-header">
      <h1>Search</h1>
      <p class="subtitle">Find items in your knowledge vault</p>
    </div>

    {#if error}
      <ErrorMessage 
        message="Search failed" 
        details={error.message} 
        retry={handleSearch} 
        dismiss={() => error = null} 
      />
    {/if}

    <div class="search-box">
      <input
        bind:this={searchInput}
        bind:value={query}
        on:input={handleSearchInput}
        type="text"
        placeholder="Search for anything..."
        class="search-input"
      />
      {#if isLoading}
        <Spinner />
      {/if}
    </div>

    <div class="filters">
      <select bind:value={dateFilter} on:change={handleSearch}>
        <option value="">All time</option>
        <option value="today">Today</option>
        <option value="week">This week</option>
        <option value="month">This month</option>
        <option value="year">This year</option>
      </select>

      <select bind:value={typeFilter} on:change={handleSearch}>
        <option value="">All types</option>
        <option value="url">URLs</option>
        <option value="text">Text</option>
        <option value="file">Files</option>
      </select>

      <input
        bind:value={tagsFilter}
        on:input={handleSearchInput}
        type="text"
        placeholder="Filter by tags..."
        class="tag-filter"
      />
    </div>

    <div class="results">
      {#if results.length > 0}
        <div class="results-count">{results.length} results</div>
        <div class="results-list">
          {#each results as result, index}
            <a
              href="/item/{result.id}"
              class="result-item"
              class:selected={index === selectedIndex}
              on:mouseenter={() => selectedIndex = index}
            >
              <div class="result-header">
                <h3>{@html highlightMatch(result.title, query)}</h3>
                <time>{new Date(result.created_at).toLocaleDateString()}</time>
              </div>
              <p class="result-snippet">{@html highlightMatch(result.snippet, query)}</p>
              {#if result.tags?.length > 0}
                <div class="result-tags">
                  {#each result.tags as tag}
                    <span class="tag">{tag}</span>
                  {/each}
                </div>
              {/if}
            </a>
          {/each}
        </div>
      {:else if query || tagsFilter}
        <div class="empty-state">
          <p>No results found</p>
          <p class="hint">Try different keywords or filters</p>
        </div>
      {:else}
        <div class="empty-state">
          <p>Start typing to search</p>
          <div class="search-tips">
            <h4>Search tips:</h4>
            <ul>
              <li>Use quotes for exact phrases: "machine learning"</li>
              <li>Filter by tags using #: #important</li>
              <li>Search in titles only: title:react</li>
              <li>Use <span class="keyboard-hint">↑↓</span> to navigate results</li>
            </ul>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .search-container {
    max-width: 800px;
    margin: 2rem auto;
    padding: 0 1rem;
  }
  
  .search-header {
    margin-bottom: 2rem;
  }
  
  h1 {
    text-align: center;
    margin-bottom: 1.5rem;
  }
  
  .search-box {
    position: relative;
  }
  
  .search-input {
    width: 100%;
    padding: 1rem;
    font-size: 1.125rem;
    border: 2px solid var(--border);
    border-radius: var(--radius);
  }
  
  .search-input:focus {
    border-color: var(--accent);
  }
  
  .spinner {
    position: absolute;
    right: 1rem;
    top: 50%;
    transform: translateY(-50%);
    width: 20px;
    height: 20px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to { transform: translateY(-50%) rotate(360deg); }
  }
  
  .filters {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }
  
  .filters select,
  .tag-filter {
    flex: 1;
    padding: 0.5rem;
    font-size: 0.875rem;
  }
  
  .results-count {
    color: var(--text-secondary);
    font-size: 0.875rem;
    margin-bottom: 1rem;
  }
  
  .results-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .result-item {
    display: block;
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    transition: all 0.2s;
  }
  
  .result-item:hover,
  .result-item.selected {
    background: var(--bg-tertiary);
    border-color: var(--accent);
  }
  
  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 0.5rem;
  }
  
  .result-header h3 {
    margin: 0;
    font-size: 1rem;
    color: var(--text-primary);
  }
  
  .result-header time {
    color: var(--text-muted);
    font-size: 0.75rem;
  }
  
  .result-snippet {
    color: var(--text-secondary);
    font-size: 0.875rem;
    margin: 0 0 0.5rem;
    line-height: 1.5;
  }
  
  .result-tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .tag {
    padding: 0.25rem 0.5rem;
    background: var(--bg-tertiary);
    border-radius: 4px;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }
  
  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
  }
  
  .hint {
    font-size: 0.875rem;
    color: var(--text-muted);
  }
  
  .search-tips {
    max-width: 400px;
    margin: 2rem auto;
    text-align: left;
  }
  
  .search-tips h4 {
    margin-bottom: 0.5rem;
    color: var(--text-primary);
  }
  
  .search-tips ul {
    list-style: none;
    padding: 0;
  }
  
  .search-tips li {
    padding: 0.25rem 0;
    font-size: 0.875rem;
  }
  
  :global(mark) {
    background: rgba(74, 158, 255, 0.3);
    color: inherit;
    padding: 0.1rem 0.2rem;
    border-radius: 2px;
  }
</style>