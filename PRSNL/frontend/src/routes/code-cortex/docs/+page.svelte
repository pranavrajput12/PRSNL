<script lang="ts">
  import { onMount } from 'svelte';
  import {
    getDevelopmentDocs,
    getDevelopmentCategories,
    searchDevelopmentContent,
    type DevelopmentItem,
    type DevelopmentDocsFilters,
  } from '$lib/api/development';
  import {
    CortexPageHeader,
    CortexTabNavigation,
    CortexContentLayout,
    CortexCard,
    CortexEmptyState,
    CortexLoadingState,
    type CortexTab,
    type CortexStat,
    type CortexAction
  } from '$lib/components/cortex';
  import Icon from '$lib/components/Icon.svelte';
  import GitHubRepoCard from '$lib/components/development/GitHubRepoCard.svelte';
  import MarkdownViewer from '$lib/components/development/MarkdownViewer.svelte';

  let docs: DevelopmentItem[] = [];
  let categories = [];
  let loading = true;
  let selectedCategory = '';
  let selectedLanguage = '';
  let selectedDifficulty: number | null = null;
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

  // UI State
  let activeTab = 'all';
  let sidebarCollapsed = false;
  let viewMode: 'grid' | 'list' = 'grid';

  // Computed stats for header
  $: headerStats = [
    { label: 'Documents', value: docs.length },
    { label: 'Categories', value: categories.length },
    { label: searchQuery ? 'Search Results' : 'Total', value: docs.length }
  ] as CortexStat[];

  // Header actions
  $: headerActions = [
    {
      label: 'Add Knowledge',
      icon: 'plus',
      onClick: () => window.location.href = '/capture',
      variant: 'primary'
    },
    {
      label: viewMode === 'grid' ? 'List View' : 'Grid View',
      icon: viewMode === 'grid' ? 'list' : 'grid',
      onClick: () => viewMode = viewMode === 'grid' ? 'list' : 'grid',
      variant: 'secondary'
    }
  ] as CortexAction[];

  // Tab configuration
  $: tabs = [
    { id: 'all', label: 'All Knowledge', icon: 'file-text', count: docs.length },
    { id: 'tutorials', label: 'Tutorials', icon: 'book-open', count: docs.filter(d => d.tags.some(tag => tag.toLowerCase().includes('tutorial'))).length },
    { id: 'guides', label: 'Guides', icon: 'map', count: docs.filter(d => d.tags.some(tag => tag.toLowerCase().includes('guide'))).length },
    { id: 'documentation', label: 'Documentation', icon: 'file-text', count: docs.filter(d => d.tags.some(tag => tag.toLowerCase().includes('documentation') || tag.toLowerCase().includes('docs'))).length },
    { id: 'learning', label: 'Learning Materials', icon: 'graduation-cap', count: docs.filter(d => d.tags.some(tag => tag.toLowerCase().includes('learning') || tag.toLowerCase().includes('course'))).length }
  ] as CortexTab[];

  // Filtered docs based on active tab
  $: filteredDocs = docs.filter(doc => {
    // Only show internal knowledge content (no external URLs, only docs with summaries or no URLs)
    const isInternalKnowledge = !doc.url || 
                               !doc.url.startsWith('http') || 
                               (doc.summary && doc.summary.length > 50); // Rich internal content
    
    if (!isInternalKnowledge) return false;
    
    // Additional filter: exclude anything that looks like a repository or tool
    const isNotRepository = !doc.url || 
                           (!doc.url.includes('github.com') && 
                            !doc.url.includes('gitlab.com') && 
                            !doc.url.includes('bitbucket.'));
    
    if (!isNotRepository) return false;
    
    switch (activeTab) {
      case 'tutorials':
        return doc.tags.some(tag => tag.toLowerCase().includes('tutorial')) ||
               doc.title.toLowerCase().includes('tutorial');
      case 'guides':
        return doc.tags.some(tag => tag.toLowerCase().includes('guide')) ||
               doc.title.toLowerCase().includes('guide');
      case 'documentation':
        return doc.tags.some(tag => tag.toLowerCase().includes('documentation') || 
                                   tag.toLowerCase().includes('docs') ||
                                   tag.toLowerCase().includes('reference')) ||
               doc.title.toLowerCase().includes('docs') ||
               doc.title.toLowerCase().includes('documentation');
      case 'learning':
        return doc.tags.some(tag => tag.toLowerCase().includes('learning') || 
                                   tag.toLowerCase().includes('course') ||
                                   tag.toLowerCase().includes('education')) ||
               doc.title.toLowerCase().includes('learn') ||
               doc.title.toLowerCase().includes('course');
      default:
        return true;
    }
  });

  onMount(async () => {
    await loadCategories();
    await loadDocs();
  });

  async function loadCategories() {
    try {
      categories = await getDevelopmentCategories();
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  }

  async function loadDocs(reset = false) {
    try {
      loading = true;

      // Use enhanced search if there's a search query
      if (searchQuery.trim()) {
        await performEnhancedSearch(reset);
      } else {
        await performRegularLoad(reset);
      }
    } catch (error) {
      console.error('Error loading docs:', error);
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
        difficulty: selectedDifficulty,
      },
    });

    // Filter to only show documentation items (exclude pure links)
    const docItems = searchResult.results.filter(
      (item) => !item.url || !item.url.startsWith('http') || item.summary
    );

    if (reset) {
      docs = docItems;
      currentPage = 0;
    } else {
      docs = docItems;
    }

    searchStats = searchResult.searchStats;
    hasMore = docItems.length >= itemsPerPage;
  }

  async function performRegularLoad(reset = false) {
    isUsingEnhancedSearch = false;
    searchStats = null;

    const filters: DevelopmentDocsFilters = {
      limit: itemsPerPage,
      offset: reset ? 0 : currentPage * itemsPerPage,
      content_type: 'knowledge',
    };

    if (selectedCategory) filters.category = selectedCategory;
    if (selectedLanguage) filters.language = selectedLanguage;
    if (selectedDifficulty) filters.difficulty = selectedDifficulty;

    const newDocs = await getDevelopmentDocs(filters);

    // Filter to only show documentation items (exclude pure links)
    const docItems = newDocs.filter(
      (item) => !item.url || !item.url.startsWith('http') || item.summary
    );

    if (reset) {
      docs = docItems;
      currentPage = 0;
    } else {
      docs = [...docs, ...docItems];
    }

    hasMore = newDocs.length === itemsPerPage;
  }

  function handleFilterChange() {
    loadDocs(true);
  }

  function handleSearchInput() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      loadDocs(true);
    }, 300);
  }

  function clearSearch() {
    searchQuery = '';
    loadDocs(true);
  }

  function loadMore() {
    currentPage++;
    loadDocs();
  }

  function getDifficultyColor(level: number): string {
    const colors = {
      1: '#10b981', // Green
      2: '#3b82f6', // Blue
      3: '#f59e0b', // Amber
      4: '#ef4444', // Red
      5: '#8b5cf6', // Purple
    };
    return colors[level] || '#6b7280';
  }

  function getDifficultyLabel(level: number): string {
    const labels = {
      1: 'Beginner',
      2: 'Intermediate',
      3: 'Advanced',
      4: 'Expert',
      5: 'Master',
    };
    return labels[level] || 'Unknown';
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
    };
    return icons[language] || '💻';
  }

  function createDocCard(doc: DevelopmentItem) {
    const tags = [
      ...(doc.programming_language ? [{ label: `${getLanguageIcon(doc.programming_language)} ${doc.programming_language}`, color: 'rgba(0, 255, 136, 0.2)' }] : []),
      ...(doc.difficulty_level ? [{ label: getDifficultyLabel(doc.difficulty_level), color: getDifficultyColor(doc.difficulty_level) + '40' }] : []),
      ...(doc.is_career_related ? [{ label: '💼 Career', color: 'rgba(220, 20, 60, 0.2)' }] : []),
      ...doc.tags.slice(0, 3).map(tag => ({ label: `#${tag}`, color: 'rgba(0, 255, 136, 0.1)' }))
    ];

    const stats = [
      ...(isUsingEnhancedSearch && doc.similarity_score ? [{ label: 'Match', value: `${Math.round(doc.similarity_score * 100)}%` }] : []),
      { label: 'Created', value: new Date(doc.created_at).toLocaleDateString() }
    ];

    const actions = [
      ...(doc.url ? [{ label: 'Open Source', icon: 'external-link', onClick: () => window.open(doc.url, '_blank') }] : [])
    ];

    return {
      title: doc.title,
      description: doc.summary || 'No description available',
      icon: 'file-text',
      tags,
      stats,
      actions,
      onClick: () => window.location.href = `/code-cortex/docs/${doc.id}`,
      variant: doc.is_career_related ? 'highlight' : 'default'
    };
  }
</script>

<svelte:head>
  <title>Knowledge Base - Code Cortex | PRSNL</title>
</svelte:head>

<div class="docs-page">
  <CortexPageHeader
    title="Knowledge Base"
    description="All documentation, guides, tutorials, and learning materials"
    icon="book"
    stats={headerStats}
    actions={headerActions}
  />

  <CortexTabNavigation
    {tabs}
    {activeTab}
    onTabChange={(tabId) => activeTab = tabId}
    variant="default"
  />

  <CortexContentLayout
    showSidebar={true}
    {sidebarCollapsed}
    sidebarTitle="Filters & Search"
    collapsible={true}
  >
    <div slot="sidebar" class="sidebar-content">
      <!-- Enhanced Search Section -->
      <div class="filter-section">
        <h4>Smart Search</h4>
        <div class="search-container">
          <input
            type="text"
            bind:value={searchQuery}
            placeholder="Search with AI..."
            class="search-input"
            on:input={handleSearchInput}
          />
          {#if searchQuery}
            <button class="clear-search-btn" on:click={clearSearch} title="Clear search">
              <Icon name="x" size="16" />
            </button>
          {/if}
        </div>

        {#if searchQuery}
          <div class="search-modes">
            <label class="mode-label">Search Mode:</label>
            <div class="mode-buttons">
              <button
                class="mode-btn {searchMode === 'semantic' ? 'active' : ''}"
                on:click={() => { searchMode = 'semantic'; loadDocs(true); }}
                title="AI Semantic Search"
              >
                <Icon name="brain" size="14" />
                Semantic
              </button>
              <button
                class="mode-btn {searchMode === 'keyword' ? 'active' : ''}"
                on:click={() => { searchMode = 'keyword'; loadDocs(true); }}
                title="Keyword Search"
              >
                <Icon name="search" size="14" />
                Keyword
              </button>
              <button
                class="mode-btn {searchMode === 'hybrid' ? 'active' : ''}"
                on:click={() => { searchMode = 'hybrid'; loadDocs(true); }}
                title="Hybrid Search"
              >
                <Icon name="zap" size="14" />
                Hybrid
              </button>
            </div>
          </div>

          {#if isUsingEnhancedSearch && searchStats}
            <div class="search-stats">
              <div class="stat-item">
                <Icon name="target" size="12" />
                {searchStats.searchType}
              </div>
              {#if searchStats.deduplication}
                <div class="stat-item">
                  <Icon name="filter" size="12" />
                  {searchStats.deduplication.deduplicated_count} results
                </div>
              {/if}
            </div>
          {/if}
        {/if}
      </div>

      <!-- Filters Section -->
      <div class="filter-section">
        <h4>Filters</h4>
        
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
          <label>Difficulty</label>
          <select bind:value={selectedDifficulty} on:change={handleFilterChange} class="filter-select">
            <option value="">All Levels</option>
            <option value={1}>Beginner</option>
            <option value={2}>Intermediate</option>
            <option value={3}>Advanced</option>
            <option value={4}>Expert</option>
            <option value={5}>Master</option>
          </select>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="filter-section">
        <h4>Quick Stats</h4>
        <div class="quick-stats">
          <div class="stat">
            <span class="stat-number">{filteredDocs.length}</span>
            <span class="stat-label">Showing</span>
          </div>
          <div class="stat">
            <span class="stat-number">{docs.filter(d => d.is_career_related).length}</span>
            <span class="stat-label">Career Related</span>
          </div>
        </div>
      </div>
    </div>

    <div slot="content" class="main-content">
      {#if loading}
        <CortexLoadingState 
          message="Loading documentation..." 
          variant="pulse"
          size="md"
        />
      {:else if filteredDocs.length === 0}
        <CortexEmptyState
          icon="file-x"
          title="No documentation found"
          description="Try adjusting your filters or search query, or add some documentation to get started."
          actionLabel="Add Documentation"
          actionHref="/capture"
          size="md"
        />
      {:else}
        <div class="docs-container {viewMode}">
          {#each filteredDocs as doc}
            {#if viewMode === 'grid'}
              <CortexCard {...createDocCard(doc)} size="md">
                <!-- GitHub Repository Preview -->
                {#if doc.url && doc.url.includes('github.com') && doc.metadata?.preview_data?.type === 'github_repo'}
                  <div class="repo-preview-section">
                    <GitHubRepoCard repoData={doc.metadata.preview_data} compact={true} />
                  </div>
                {/if}

                <!-- README Preview for GitHub Documents -->
                {#if doc.url && doc.url.includes('github.com') && doc.metadata?.preview_data?.readme?.snippet}
                  <div class="readme-preview">
                    <h4>📄 README Preview</h4>
                    <div class="readme-content">
                      <MarkdownViewer
                        content={doc.metadata.preview_data.readme.snippet}
                        enableSyntaxHighlight={true}
                        theme="neural"
                        compact={true}
                      />
                    </div>
                    {#if doc.metadata.preview_data.readme.full_length > doc.metadata.preview_data.readme.snippet.length}
                      <a
                        href={`/code-cortex/docs/${doc.id}`}
                        class="read-more-link"
                      >
                        Read full README ({Math.round(doc.metadata.preview_data.readme.full_length / 1000)}k chars)
                      </a>
                    {/if}
                  </div>
                {/if}
              </CortexCard>
            {:else}
              <!-- List view for docs -->
              <div class="doc-list-item">
                <div class="doc-list-header">
                  <div class="doc-list-title">
                    <Icon name="file-text" size="20" />
                    <a href={`/code-cortex/docs/${doc.id}`}>
                      {doc.title}
                    </a>
                  </div>
                  <div class="doc-list-meta">
                    {#if doc.programming_language}
                      <span class="meta-tag">{getLanguageIcon(doc.programming_language)} {doc.programming_language}</span>
                    {/if}
                    {#if doc.difficulty_level}
                      <span class="meta-tag difficulty" style="color: {getDifficultyColor(doc.difficulty_level)}">
                        {getDifficultyLabel(doc.difficulty_level)}
                      </span>
                    {/if}
                    <span class="meta-date">{new Date(doc.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                {#if doc.summary}
                  <p class="doc-list-summary">{doc.summary}</p>
                {/if}
              </div>
            {/if}
          {/each}
        </div>

        <!-- Load More -->
        {#if hasMore}
          <div class="load-more-section">
            <button class="load-more-btn" on:click={loadMore} disabled={loading}>
              {loading ? 'Loading...' : 'Load More Documentation'}
            </button>
          </div>
        {/if}
      {/if}
    </div>
  </CortexContentLayout>
</div>

<style>
  .docs-page {
    min-height: 100vh;
    background: #0a0a0a;
    color: #e0e0e0;
    padding: 2rem;
  }

  .sidebar-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    height: 100%;
  }

  .filter-section {
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(0, 255, 136, 0.1);
  }

  .filter-section:last-child {
    border-bottom: none;
  }

  .filter-section h4 {
    margin: 0 0 1rem 0;
    font-size: 0.9rem;
    color: #00ff88;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .search-container {
    position: relative;
    margin-bottom: 1rem;
  }

  .search-input {
    width: 100%;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 6px;
    padding: 0.75rem;
    padding-right: 2.5rem;
    color: #00ff88;
    font-size: 0.875rem;
  }

  .search-input:focus {
    outline: none;
    border-color: #00ff88;
    box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
  }

  .clear-search-btn {
    position: absolute;
    right: 0.5rem;
    top: 50%;
    transform: translateY(-50%);
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

  .search-modes {
    margin-bottom: 1rem;
  }

  .mode-label {
    display: block;
    font-size: 0.75rem;
    color: #888;
    margin-bottom: 0.5rem;
  }

  .mode-buttons {
    display: flex;
    gap: 0.5rem;
  }

  .mode-btn {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.5rem 0.75rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 4px;
    color: #888;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s ease;
    flex: 1;
    justify-content: center;
  }

  .mode-btn:hover {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }

  .mode-btn.active {
    background: rgba(0, 255, 136, 0.3);
    border-color: #00ff88;
    color: #00ff88;
  }

  .search-stats {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: #888;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .filter-group {
    margin-bottom: 1rem;
  }

  .filter-group label {
    display: block;
    font-size: 0.75rem;
    color: #888;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .filter-select {
    width: 100%;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 4px;
    padding: 0.5rem;
    color: #00ff88;
    font-size: 0.875rem;
  }

  .filter-select:focus {
    outline: none;
    border-color: #00ff88;
  }

  .quick-stats {
    display: flex;
    gap: 1rem;
  }

  .stat {
    text-align: center;
  }

  .stat-number {
    display: block;
    font-size: 1.5rem;
    font-weight: bold;
    color: #00ff88;
  }

  .stat-label {
    display: block;
    font-size: 0.75rem;
    color: #888;
    margin-top: 0.25rem;
  }

  .main-content {
    flex: 1;
  }

  .docs-container.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .docs-container.list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .doc-list-item {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.2s ease;
  }

  .doc-list-item:hover {
    border-color: rgba(0, 255, 136, 0.4);
    background: rgba(0, 255, 136, 0.05);
  }

  .doc-list-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .doc-list-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .doc-list-title a {
    color: #00ff88;
    text-decoration: none;
    font-weight: 500;
  }

  .doc-list-title a:hover {
    color: #dc143c;
  }

  .doc-list-meta {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .meta-tag {
    padding: 0.25rem 0.5rem;
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .meta-date {
    font-size: 0.75rem;
    color: #888;
  }

  .doc-list-summary {
    margin: 0;
    color: #ccc;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .load-more-section {
    text-align: center;
    margin-top: 2rem;
  }

  .load-more-btn {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.75rem 2rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .load-more-btn:hover:not(:disabled) {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .load-more-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Repository and README preview styles */
  .repo-preview-section {
    margin: 1rem 0;
    padding: 1rem 0;
    border-top: 1px solid rgba(0, 255, 136, 0.1);
  }

  .readme-preview {
    margin: 1rem 0;
    padding: 1rem;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
  }

  .readme-preview h4 {
    margin: 0 0 0.75rem 0;
    font-size: 0.9rem;
    color: #00ff88;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .readme-content {
    max-height: 200px;
    overflow: hidden;
    position: relative;
  }

  .readme-content::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 30px;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.4));
    pointer-events: none;
  }

  .read-more-link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.75rem;
    color: #00ff88;
    text-decoration: none;
    font-size: 0.85rem;
    padding: 0.25rem 0.5rem;
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 4px;
    transition: all 0.3s ease;
  }

  .read-more-link:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: #00ff88;
    transform: translateY(-1px);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .docs-page {
      padding: 1rem;
    }

    .docs-container.grid {
      grid-template-columns: 1fr;
    }

    .doc-list-header {
      flex-direction: column;
      gap: 0.5rem;
    }

    .doc-list-meta {
      align-self: flex-start;
    }
  }
</style>