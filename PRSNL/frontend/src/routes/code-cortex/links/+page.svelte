<script lang="ts">
  import { onMount } from 'svelte';
  import {
    getDevelopmentDocs,
    getDevelopmentCategories,
    searchDevelopmentContent,
    type DevelopmentItem,
    type DevelopmentDocsFilters,
  } from '$lib/api/development';
  import Icon from '$lib/components/Icon.svelte';

  let links: DevelopmentItem[] = [];
  let categories = [];
  let loading = true;
  let selectedCategory = '';
  let selectedLanguage = '';
  let searchQuery = '';

  // Enhanced search options
  let searchMode: 'semantic' | 'keyword' | 'hybrid' = 'semantic';
  let isUsingEnhancedSearch = false;
  let searchStats: any = null;
  let searchTimeout: ReturnType<typeof setTimeout> | undefined;

  // Pagination
  let currentPage = 0;
  let itemsPerPage = 20;
  let hasMore = true;

  onMount(async () => {
    await loadCategories();
    await loadLinks();
  });

  async function loadCategories() {
    try {
      categories = await getDevelopmentCategories();
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  }

  async function loadLinks(reset = false) {
    try {
      loading = true;

      // Use enhanced search if there's a search query
      if (searchQuery.trim()) {
        await performEnhancedSearch(reset);
      } else {
        await performRegularLoad(reset);
      }
    } catch (error) {
      console.error('Error loading links:', error);
    } finally {
      loading = false;
    }
  }

  async function performEnhancedSearch(reset = false) {
    isUsingEnhancedSearch = true;

    const searchResult = await searchDevelopmentContent(searchQuery, {
      searchMode: searchMode,
      limit: reset ? itemsPerPage : itemsPerPage * (currentPage + 1),
      filters: {
        category: selectedCategory,
        language: selectedLanguage,
      },
    });

    // Filter to only show items with URLs (links)
    const linkItems = searchResult.results.filter(
      (item) => item.url && item.url.startsWith('http')
    );

    if (reset) {
      links = linkItems;
      currentPage = 0;
    } else {
      links = linkItems;
    }

    searchStats = searchResult.searchStats;
    hasMore = linkItems.length >= itemsPerPage;

    console.log('Enhanced links search:', {
      query: searchQuery,
      mode: searchMode,
      results: linkItems.length,
      stats: searchStats,
    });
  }

  async function performRegularLoad(reset = false) {
    isUsingEnhancedSearch = false;
    searchStats = null;

    const filters: DevelopmentDocsFilters = {
      limit: itemsPerPage,
      offset: reset ? 0 : currentPage * itemsPerPage,
    };

    if (selectedCategory) filters.category = selectedCategory;
    if (selectedLanguage) filters.language = selectedLanguage;

    const newLinks = await getDevelopmentDocs(filters);

    // Filter to only show items with URLs (links)
    const linkItems = newLinks.filter((item) => item.url && item.url.startsWith('http'));

    if (reset) {
      links = linkItems;
      currentPage = 0;
    } else {
      links = [...links, ...linkItems];
    }

    hasMore = newLinks.length === itemsPerPage;
  }

  function handleFilterChange() {
    loadLinks(true);
  }

  function handleSearchInput() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      loadLinks(true);
    }, 300);
  }

  function clearSearch() {
    searchQuery = '';
    loadLinks(true);
  }

  function loadMore() {
    currentPage++;
    loadLinks();
  }

  function getLanguageIcon(language: string): string {
    const icons = {
      python: '🐍',
      javascript: '🟨',
      typescript: '🔷',
      java: '☕',
      go: '🐹',
      rust: '🦀',
      cpp: '⚡',
      html: '🌐',
      css: '🎨',
    };
    return icons[language] || '💻';
  }

  function getDomain(url: string): string {
    try {
      return new URL(url).hostname.replace('www.', '');
    } catch {
      return 'unknown';
    }
  }

  function getDomainIcon(domain: string): string {
    const icons = {
      'github.com': '🐙',
      'gitlab.com': '🦊',
      'stackoverflow.com': '📚',
      'medium.com': '📝',
      'dev.to': '💻',
      'youtube.com': '📺',
      'docs.google.com': '📄',
      'notion.so': '📝',
    };
    return icons[domain] || '🔗';
  }
</script>

<svelte:head>
  <title>Useful Links - Code Cortex | PRSNL</title>
</svelte:head>

<div class="links-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-left">
      <a href="/code-cortex" class="back-link">
        <Icon name="arrow-left" size="small" />
        Code Cortex
      </a>
      <div class="header-content">
        <h1>🔗 Useful Links</h1>
        <p>GitHub repositories, documentation sites, and development resources</p>
      </div>
    </div>
  </div>

  <!-- Filters -->
  <div class="filters-section">
    <div class="filters-grid">
      <div class="filter-group search-group">
        <label>Enhanced Search</label>
        <div class="search-container">
          <input
            type="text"
            bind:value={searchQuery}
            placeholder="Search links and repositories with AI..."
            class="filter-input search-input"
            on:input={handleSearchInput}
          />
          {#if searchQuery}
            <button class="clear-search-btn" on:click={clearSearch} title="Clear search">
              <Icon name="x" />
            </button>
          {/if}
        </div>

        {#if searchQuery}
          <div class="search-mode-toggle">
            <button
              class="mode-btn {searchMode === 'semantic' ? 'active' : ''}"
              on:click={() => {
                searchMode = 'semantic';
                loadLinks(true);
              }}
              title="AI Semantic Search - Understands meaning and context"
            >
              <Icon name="brain" size={14} />
              Semantic
            </button>
            <button
              class="mode-btn {searchMode === 'keyword' ? 'active' : ''}"
              on:click={() => {
                searchMode = 'keyword';
                loadLinks(true);
              }}
              title="Keyword Search - Exact text matching"
            >
              <Icon name="search" size={14} />
              Keyword
            </button>
            <button
              class="mode-btn {searchMode === 'hybrid' ? 'active' : ''}"
              on:click={() => {
                searchMode = 'hybrid';
                loadLinks(true);
              }}
              title="Hybrid Search - Combines semantic and keyword"
            >
              <Icon name="zap" size={14} />
              Hybrid
            </button>
          </div>

          {#if isUsingEnhancedSearch && searchStats}
            <div class="search-stats">
              <span class="stat-item">
                <Icon name="target" size={12} />
                {searchStats.searchType}
              </span>
              {#if searchStats.deduplication}
                <span class="stat-item">
                  <Icon name="filter" size={12} />
                  {searchStats.deduplication.deduplicated_count} results
                </span>
              {/if}
            </div>
          {/if}
        {/if}
      </div>

      <div class="filter-group">
        <label>Category</label>
        <select bind:value={selectedCategory} on:change={handleFilterChange} class="filter-select">
          <option value="">All Categories</option>
          {#each categories as category}
            <option value={category.name}>{category.name}</option>
          {/each}
        </select>
      </div>

      <div class="filter-group">
        <label>Language</label>
        <select bind:value={selectedLanguage} on:change={handleFilterChange} class="filter-select">
          <option value="">All Languages</option>
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="java">Java</option>
          <option value="go">Go</option>
          <option value="rust">Rust</option>
          <option value="cpp">C++</option>
        </select>
      </div>

      <div class="filter-group">
        <label>Quick Filters</label>
        <div class="quick-filters">
          <button
            class="quick-filter"
            on:click={() => {
              searchQuery = 'github.com';
              handleFilterChange();
            }}
          >
            🐙 GitHub
          </button>
          <button
            class="quick-filter"
            on:click={() => {
              searchQuery = 'docs';
              handleFilterChange();
            }}
          >
            📚 Docs
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Links Grid -->
  <div class="links-grid">
    {#each links as link}
      <article class="link-card">
        <div class="link-header">
          <div class="link-meta">
            <span class="domain-tag">
              {getDomainIcon(getDomain(link.url))}
              {getDomain(link.url)}
            </span>
            {#if link.programming_language}
              <span class="language-tag">
                {getLanguageIcon(link.programming_language)}
                {link.programming_language}
              </span>
            {/if}
            {#if link.is_career_related}
              <span class="career-tag">💼 Career</span>
            {/if}
          </div>

          <h3 class="link-title">
            <a href={link.url} target="_blank" rel="noopener noreferrer">{link.title}</a>
          </h3>
        </div>

        {#if link.summary}
          <p class="link-summary">{link.summary}</p>
        {/if}

        <div class="link-footer">
          <div class="link-tags">
            {#each link.tags.slice(0, 3) as tag}
              <span class="tag">#{tag}</span>
            {/each}
            {#if link.tags.length > 3}
              <span class="tag-more">+{link.tags.length - 3}</span>
            {/if}
          </div>

          <div class="link-actions">
            <span class="link-date">{new Date(link.created_at).toLocaleDateString()}</span>

            {#if isUsingEnhancedSearch && link.similarity_score}
              <div class="search-score">
                <Icon name="target" size={12} />
                <span class="score-value">{Math.round(link.similarity_score * 100)}%</span>
                {#if link.component_scores && searchMode === 'hybrid'}
                  <div class="component-scores">
                    {#if link.component_scores.semantic}
                      <span class="score-component semantic"
                        >S: {Math.round(link.component_scores.semantic * 100)}%</span
                      >
                    {/if}
                    {#if link.component_scores.keyword}
                      <span class="score-component keyword"
                        >K: {Math.round(link.component_scores.keyword * 100)}%</span
                      >
                    {/if}
                  </div>
                {/if}
              </div>
            {/if}

            <a
              href={link.type === 'development'
                ? `/items/${link.id}`
                : link.permalink || `/item/${link.id}`}
              class="link-button secondary"
            >
              View Details
            </a>
            <a href={link.url} target="_blank" rel="noopener noreferrer" class="link-button">
              <Icon name="external-link" size="small" />
              Visit
            </a>
          </div>
        </div>
      </article>
    {/each}
  </div>

  <!-- Load More -->
  {#if hasMore && !loading}
    <div class="load-more-section">
      <button class="load-more-btn" on:click={loadMore}> Load More Links </button>
    </div>
  {/if}

  <!-- Loading State -->
  {#if loading}
    <div class="loading-state">
      <div class="neural-pulse"></div>
      <span>Loading useful links...</span>
    </div>
  {/if}

  <!-- Empty State -->
  {#if !loading && links.length === 0}
    <div class="empty-state">
      <div class="empty-icon">🔗</div>
      <h3>No links found</h3>
      <p>Try adjusting your filters or add some development links to get started.</p>
      <a href="/capture" class="add-links-btn">Add Links</a>
    </div>
  {/if}
</div>

<style>
  .links-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    color: #00ff88;
    font-family: 'JetBrains Mono', monospace;
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .header-left {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .back-link {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: rgba(0, 255, 136, 0.7);
    text-decoration: none;
    font-size: 0.9rem;
    transition: color 0.3s ease;
  }

  .back-link:hover {
    color: #00ff88;
  }

  .header-content h1 {
    font-size: 2rem;
    margin: 0;
    background: linear-gradient(45deg, #00ff88, #dc143c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .header-content p {
    margin: 0.5rem 0 0 0;
    opacity: 0.8;
  }

  .filters-section {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }

  .filters-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr;
    gap: 1rem;
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .filter-group label {
    font-size: 0.875rem;
    color: rgba(0, 255, 136, 0.8);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .filter-input,
  .filter-select {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 6px;
    padding: 0.75rem;
    color: #00ff88;
    font-family: inherit;
    font-size: 0.9rem;
  }

  .filter-input:focus,
  .filter-select:focus {
    outline: none;
    border-color: #00ff88;
    box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
  }

  .quick-filters {
    display: flex;
    gap: 0.5rem;
  }

  .quick-filter {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 6px;
    padding: 0.5rem;
    color: #00ff88;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 0.8rem;
  }

  .quick-filter:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .links-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .link-card {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
  }

  .link-card:hover {
    border-color: #00ff88;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 255, 136, 0.2);
  }

  .link-header {
    margin-bottom: 1rem;
  }

  .link-meta {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
  }

  .domain-tag,
  .language-tag,
  .career-tag {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-weight: 500;
  }

  .domain-tag {
    background: rgba(220, 20, 60, 0.2);
    color: #dc143c;
  }

  .language-tag {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }

  .career-tag {
    background: rgba(220, 20, 60, 0.2);
    color: #dc143c;
  }

  .link-title {
    margin: 0;
    font-size: 1.1rem;
    line-height: 1.4;
  }

  .link-title a {
    color: #00ff88;
    text-decoration: none;
    transition: color 0.3s ease;
  }

  .link-title a:hover {
    color: #dc143c;
  }

  .link-summary {
    margin: 0 0 1rem 0;
    opacity: 0.8;
    font-size: 0.9rem;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .link-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }

  .link-tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    flex: 1;
  }

  .tag {
    background: rgba(0, 255, 136, 0.1);
    color: rgba(0, 255, 136, 0.8);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .tag-more {
    background: rgba(220, 20, 60, 0.1);
    color: rgba(220, 20, 60, 0.8);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .link-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .link-date {
    font-size: 0.75rem;
    color: rgba(0, 255, 136, 0.6);
  }

  .link-button {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    text-decoration: none;
    font-size: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.3rem;
    transition: all 0.3s ease;
  }

  .link-button:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .load-more-section {
    text-align: center;
    margin-bottom: 2rem;
  }

  .load-more-btn {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.75rem 2rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-family: inherit;
  }

  .load-more-btn:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    gap: 1rem;
  }

  .neural-pulse {
    width: 40px;
    height: 40px;
    border: 2px solid rgba(0, 255, 136, 0.3);
    border-top: 2px solid #00ff88;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    opacity: 0.8;
  }

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }

  .empty-state h3 {
    margin: 0 0 1rem 0;
    font-size: 1.5rem;
    color: #00ff88;
  }

  .empty-state p {
    margin: 0 0 2rem 0;
    opacity: 0.7;
  }

  .add-links-btn {
    background: linear-gradient(45deg, #00ff88, #dc143c);
    color: black;
    padding: 0.75rem 2rem;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    transition: transform 0.3s ease;
    display: inline-block;
  }

  .add-links-btn:hover {
    transform: translateY(-2px);
  }

  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .links-page {
      padding: 1rem;
    }

    .filters-grid {
      grid-template-columns: 1fr;
    }

    .links-grid {
      grid-template-columns: 1fr;
    }
  }

  /* Enhanced Search Styles (shared with docs page) */
  .search-group {
    position: relative;
  }

  .search-container {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-input {
    padding-right: 2.5rem;
  }

  .clear-search-btn {
    position: absolute;
    right: 0.5rem;
    background: none;
    border: none;
    color: #888;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 50%;
    transition: all 0.2s ease;
  }

  .clear-search-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #00ff88;
  }

  .search-mode-toggle {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: rgba(0, 255, 136, 0.05);
    border-radius: 0.5rem;
    border: 1px solid rgba(0, 255, 136, 0.2);
  }

  .mode-btn {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.25rem;
    color: #ccc;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .mode-btn:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: rgba(0, 255, 136, 0.3);
    color: #00ff88;
  }

  .mode-btn.active {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
    color: #00ff88;
  }

  .search-stats {
    display: flex;
    gap: 0.75rem;
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #888;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .search-score {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
    color: #00ff88;
    padding: 0.25rem 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    border-radius: 0.25rem;
    border: 1px solid rgba(0, 255, 136, 0.2);
  }

  .score-value {
    font-weight: 600;
  }

  .component-scores {
    display: flex;
    gap: 0.25rem;
    margin-left: 0.5rem;
  }

  .score-component {
    font-size: 0.65rem;
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-weight: 500;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .score-component.semantic {
    color: #00ff64;
    border-color: rgba(0, 255, 100, 0.3);
    background: rgba(0, 255, 100, 0.1);
  }

  .score-component.keyword {
    color: #0096ff;
    border-color: rgba(0, 150, 255, 0.3);
    background: rgba(0, 150, 255, 0.1);
  }
</style>
