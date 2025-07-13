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

  // UI State
  let activeTab = 'all';
  let sidebarCollapsed = false;
  let viewMode: 'grid' | 'list' | 'compact' = 'grid';

  // Quick filter state
  let selectedDomain = '';

  // Computed stats for header
  $: headerStats = [
    { label: 'Links', value: links.length },
    { label: 'Domains', value: [...new Set(links.map(l => getDomain(l.url)))].length },
    { label: 'GitHub', value: links.filter(l => l.url?.includes('github.com')).length }
  ] as CortexStat[];

  // Header actions
  $: headerActions = [
    {
      label: 'Add Tools & Links',
      icon: 'plus',
      onClick: () => window.location.href = '/capture',
      variant: 'primary'
    },
    {
      label: viewMode === 'grid' ? 'List View' : viewMode === 'list' ? 'Compact View' : 'Grid View',
      icon: viewMode === 'grid' ? 'list' : viewMode === 'list' ? 'grid' : 'grid',
      onClick: () => {
        if (viewMode === 'grid') viewMode = 'list';
        else if (viewMode === 'list') viewMode = 'compact';
        else viewMode = 'grid';
      },
      variant: 'secondary'
    }
  ] as CortexAction[];

  // Tab configuration based on domain analysis
  $: domainCounts = links.reduce((acc, link) => {
    const domain = getDomain(link.url);
    acc[domain] = (acc[domain] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  $: tabs = [
    { id: 'all', label: 'All Tools & Links', icon: 'link', count: links.length },
    { id: 'tools', label: 'Development Tools', icon: 'tool', count: links.filter(l => isDomainType(l.url, 'tools')).length },
    { id: 'utilities', label: 'Utilities', icon: 'settings', count: links.filter(l => isDomainType(l.url, 'utilities')).length },
    { id: 'services', label: 'Online Services', icon: 'cloud', count: links.filter(l => isDomainType(l.url, 'services')).length },
    { id: 'resources', label: 'Resource Sites', icon: 'bookmark', count: links.filter(l => isDomainType(l.url, 'resources')).length }
  ] as CortexTab[];

  // Filtered links based on active tab
  $: filteredLinks = links.filter(link => {
    // Only show external URLs (tools and utilities, not repositories or internal docs)
    const isExternalTool = link.url && 
                          link.url.startsWith('http') && 
                          !link.url.includes('github.com') && 
                          !link.url.includes('gitlab.com') && 
                          !link.url.includes('bitbucket.');
    
    if (!isExternalTool) return false;
    if (selectedDomain && getDomain(link.url) !== selectedDomain) return false;
    
    // Additional filter: focus on tools, services, and utilities
    const isToolOrService = !link.summary || 
                           link.summary.length < 200 || // Not long-form content
                           link.tags.some(tag => 
                             tag.toLowerCase().includes('tool') ||
                             tag.toLowerCase().includes('service') ||
                             tag.toLowerCase().includes('utility') ||
                             tag.toLowerCase().includes('app') ||
                             tag.toLowerCase().includes('platform')
                           ) ||
                           link.title.toLowerCase().includes('tool') ||
                           link.title.toLowerCase().includes('service') ||
                           isDomainType(link.url, 'tools') ||
                           isDomainType(link.url, 'utilities') ||
                           isDomainType(link.url, 'services');
    
    if (!isToolOrService) return false;
    
    switch (activeTab) {
      case 'tools':
        return isDomainType(link.url, 'tools') ||
               link.tags.some(tag => tag.toLowerCase().includes('tool')) ||
               link.title.toLowerCase().includes('tool');
      case 'utilities':
        return isDomainType(link.url, 'utilities') ||
               link.tags.some(tag => tag.toLowerCase().includes('utility') || tag.toLowerCase().includes('util')) ||
               link.title.toLowerCase().includes('utility');
      case 'services':
        return isDomainType(link.url, 'services') ||
               link.tags.some(tag => tag.toLowerCase().includes('service') || tag.toLowerCase().includes('platform')) ||
               link.title.toLowerCase().includes('service');
      case 'resources':
        return isDomainType(link.url, 'resources') ||
               link.tags.some(tag => tag.toLowerCase().includes('resource')) ||
               link.title.toLowerCase().includes('resource');
      default:
        return true;
    }
  });

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
  }

  async function performRegularLoad(reset = false) {
    isUsingEnhancedSearch = false;
    searchStats = null;

    const filters: DevelopmentDocsFilters = {
      limit: itemsPerPage,
      offset: reset ? 0 : currentPage * itemsPerPage,
      content_type: 'tools',
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
      'npm.js': '📦',
      'pypi.org': '🐍',
      'crates.io': '📦',
      'docker.com': '🐳',
      'vercel.com': '▲',
      'netlify.com': '🌐',
    };
    return icons[domain] || '🔗';
  }

  function isDomainType(url: string, type: string): boolean {
    if (!url) return false;
    const domain = getDomain(url);
    
    const domainTypes = {
      tools: ['app.', 'tool', 'build', 'deploy', 'ci', 'cd', 'test', 'lint', 'format', 'bundler', 'compiler'],
      utilities: ['util', 'helper', 'converter', 'generator', 'validator', 'formatter', 'parser'],
      services: ['service', 'api.', 'console', 'dashboard', 'platform', 'saas', 'cloud', 'aws', 'azure', 'gcp'],
      resources: ['resource', 'library', 'framework', 'template', 'boilerplate', 'example', 'sample']
    };

    return domainTypes[type]?.some(keyword => domain.includes(keyword) || url.toLowerCase().includes(keyword)) || false;
  }

  function getDomainColor(domain: string): string {
    const colors = {
      'github.com': '#24292e',
      'gitlab.com': '#fc6d26',
      'stackoverflow.com': '#f48024',
      'medium.com': '#00ab6c',
      'dev.to': '#0a0a0a',
      'youtube.com': '#ff0000',
      'docs.google.com': '#4285f4',
      'notion.so': '#000000',
    };
    return colors[domain] || '#00ff88';
  }

  function createLinkCard(link: DevelopmentItem) {
    const domain = getDomain(link.url);
    const tags = [
      { label: `${getDomainIcon(domain)} ${domain}`, color: getDomainColor(domain) + '40' },
      ...(link.programming_language ? [{ label: `${getLanguageIcon(link.programming_language)} ${link.programming_language}`, color: 'rgba(0, 255, 136, 0.2)' }] : []),
      ...(link.is_career_related ? [{ label: '💼 Career', color: 'rgba(220, 20, 60, 0.2)' }] : []),
      ...link.tags.slice(0, 2).map(tag => ({ label: `#${tag}`, color: 'rgba(0, 255, 136, 0.1)' }))
    ];

    const stats = [
      ...(isUsingEnhancedSearch && link.similarity_score ? [{ label: 'Match', value: `${Math.round(link.similarity_score * 100)}%` }] : []),
      { label: 'Added', value: new Date(link.created_at).toLocaleDateString() }
    ];

    const actions = [
      { label: 'Visit', icon: 'external-link', onClick: () => window.open(link.url, '_blank') },
      { label: 'Details', icon: 'info', onClick: () => window.location.href = link.type === 'development' ? `/items/${link.id}` : link.permalink || `/item/${link.id}` }
    ];

    return {
      title: link.title,
      description: link.summary || 'No description available',
      icon: 'link',
      iconColor: getDomainColor(domain),
      tags,
      stats,
      actions,
      onClick: () => window.open(link.url, '_blank'),
      variant: domain === 'github.com' ? 'highlight' : 'default'
    };
  }

  // Top domains for quick filters
  $: topDomains = Object.entries(domainCounts)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 8)
    .map(([domain, count]) => ({ domain, count }));
</script>

<svelte:head>
  <title>Tools & Links - Code Cortex | PRSNL</title>
</svelte:head>

<div class="links-page">
  <CortexPageHeader
    title="Tools & Links"
    description="External development tools, utilities, and resource links"
    icon="tool"
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
    sidebarTitle="Filters & Domains"
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
            placeholder="Search links with AI..."
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
                on:click={() => { searchMode = 'semantic'; loadLinks(true); }}
                title="AI Semantic Search"
              >
                <Icon name="brain" size="14" />
                Semantic
              </button>
              <button
                class="mode-btn {searchMode === 'keyword' ? 'active' : ''}"
                on:click={() => { searchMode = 'keyword'; loadLinks(true); }}
                title="Keyword Search"
              >
                <Icon name="search" size="14" />
                Keyword
              </button>
              <button
                class="mode-btn {searchMode === 'hybrid' ? 'active' : ''}"
                on:click={() => { searchMode = 'hybrid'; loadLinks(true); }}
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

      <!-- Quick Domain Filters -->
      <div class="filter-section">
        <h4>Top Domains</h4>
        <div class="domain-filters">
          <button 
            class="domain-filter {selectedDomain === '' ? 'active' : ''}"
            on:click={() => { selectedDomain = ''; }}
          >
            All Domains
          </button>
          {#each topDomains as {domain, count}}
            <button 
              class="domain-filter {selectedDomain === domain ? 'active' : ''}"
              on:click={() => { selectedDomain = selectedDomain === domain ? '' : domain; }}
            >
              {getDomainIcon(domain)} {domain}
              <span class="domain-count">{count}</span>
            </button>
          {/each}
        </div>
      </div>

      <!-- Regular Filters -->
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
      </div>

      <!-- Quick Actions -->
      <div class="filter-section">
        <h4>Quick Filters</h4>
        <div class="quick-actions">
          <button 
            class="quick-action"
            on:click={() => { activeTab = 'tools'; }}
          >
            🔧 Development Tools
          </button>
          <button 
            class="quick-action"
            on:click={() => { activeTab = 'utilities'; }}
          >
            ⚙️ Utilities
          </button>
          <button 
            class="quick-action"
            on:click={() => { activeTab = 'services'; }}
          >
            ☁️ Online Services
          </button>
        </div>
      </div>

      <!-- Domain Stats -->
      <div class="filter-section">
        <h4>Domain Stats</h4>
        <div class="domain-stats">
          {#each topDomains.slice(0, 5) as {domain, count}}
            <div class="domain-stat">
              <span class="domain-icon">{getDomainIcon(domain)}</span>
              <span class="domain-name">{domain}</span>
              <span class="domain-count">{count}</span>
            </div>
          {/each}
        </div>
      </div>
    </div>

    <div slot="content" class="main-content">
      {#if loading}
        <CortexLoadingState 
          message="Loading useful links..." 
          variant="spinner"
          size="md"
        />
      {:else if filteredLinks.length === 0}
        <CortexEmptyState
          icon="link-2"
          title="No links found"
          description="Try adjusting your filters or add some useful links to get started."
          actionLabel="Add Links"
          actionHref="/capture"
          size="md"
        />
      {:else}
        <div class="links-container {viewMode}">
          {#each filteredLinks as link}
            {#if viewMode === 'grid'}
              <CortexCard {...createLinkCard(link)} size="md" />
            {:else if viewMode === 'list'}
              <!-- List view for links -->
              <div class="link-list-item">
                <div class="link-list-header">
                  <div class="link-list-title">
                    <span class="domain-icon">{getDomainIcon(getDomain(link.url))}</span>
                    <a href={link.url} target="_blank" rel="noopener noreferrer">
                      {link.title}
                    </a>
                  </div>
                  <div class="link-list-meta">
                    <span class="domain-tag">{getDomain(link.url)}</span>
                    {#if link.programming_language}
                      <span class="meta-tag">{getLanguageIcon(link.programming_language)} {link.programming_language}</span>
                    {/if}
                    <span class="meta-date">{new Date(link.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                {#if link.summary}
                  <p class="link-list-summary">{link.summary}</p>
                {/if}
              </div>
            {:else}
              <!-- Compact view for links -->
              <div class="link-compact-item">
                <span class="compact-icon">{getDomainIcon(getDomain(link.url))}</span>
                <div class="compact-content">
                  <a href={link.url} target="_blank" rel="noopener noreferrer" class="compact-title">
                    {link.title}
                  </a>
                  <span class="compact-domain">{getDomain(link.url)}</span>
                </div>
                <div class="compact-actions">
                  <button 
                    class="compact-action"
                    on:click={() => window.location.href = link.type === 'development' ? `/items/${link.id}` : link.permalink || `/item/${link.id}`}
                    title="View details"
                  >
                    <Icon name="info" size="16" />
                  </button>
                </div>
              </div>
            {/if}
          {/each}
        </div>

        <!-- Load More -->
        {#if hasMore}
          <div class="load-more-section">
            <button class="load-more-btn" on:click={loadMore} disabled={loading}>
              {loading ? 'Loading...' : 'Load More Links'}
            </button>
          </div>
        {/if}
      {/if}
    </div>
  </CortexContentLayout>
</div>

<style>
  .links-page {
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

  .domain-filters {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .domain-filter {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0.75rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 4px;
    color: #888;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
  }

  .domain-filter:hover {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }

  .domain-filter.active {
    background: rgba(0, 255, 136, 0.3);
    border-color: #00ff88;
    color: #00ff88;
  }

  .domain-count {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
    padding: 0.125rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
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

  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .quick-action {
    padding: 0.5rem 0.75rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 4px;
    color: #888;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
  }

  .quick-action:hover {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }

  .domain-stats {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .domain-stat {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0;
  }

  .domain-icon {
    font-size: 1rem;
    min-width: 20px;
  }

  .domain-name {
    flex: 1;
    font-size: 0.75rem;
    color: #888;
  }

  .main-content {
    flex: 1;
  }

  .links-container.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .links-container.list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .links-container.compact {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .link-list-item {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.2s ease;
  }

  .link-list-item:hover {
    border-color: rgba(0, 255, 136, 0.4);
    background: rgba(0, 255, 136, 0.05);
  }

  .link-list-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .link-list-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .link-list-title a {
    color: #00ff88;
    text-decoration: none;
    font-weight: 500;
  }

  .link-list-title a:hover {
    color: #dc143c;
  }

  .link-list-meta {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .domain-tag {
    padding: 0.25rem 0.5rem;
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .meta-tag {
    padding: 0.25rem 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    color: #888;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .meta-date {
    font-size: 0.75rem;
    color: #666;
  }

  .link-list-summary {
    margin: 0;
    color: #ccc;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .link-compact-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.1);
    border-radius: 6px;
    transition: all 0.2s ease;
  }

  .link-compact-item:hover {
    border-color: rgba(0, 255, 136, 0.3);
    background: rgba(0, 255, 136, 0.05);
  }

  .compact-icon {
    font-size: 1.2rem;
    min-width: 24px;
    text-align: center;
  }

  .compact-content {
    flex: 1;
    min-width: 0;
  }

  .compact-title {
    display: block;
    color: #00ff88;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.875rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .compact-title:hover {
    color: #dc143c;
  }

  .compact-domain {
    display: block;
    font-size: 0.75rem;
    color: #666;
    margin-top: 0.125rem;
  }

  .compact-actions {
    display: flex;
    gap: 0.5rem;
  }

  .compact-action {
    background: transparent;
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #888;
    padding: 0.375rem;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .compact-action:hover {
    background: rgba(0, 255, 136, 0.1);
    color: #00ff88;
    border-color: #00ff88;
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

  /* Responsive */
  @media (max-width: 768px) {
    .links-page {
      padding: 1rem;
    }

    .links-container.grid {
      grid-template-columns: 1fr;
    }

    .link-list-header {
      flex-direction: column;
      gap: 0.5rem;
    }

    .link-list-meta {
      align-self: flex-start;
    }

    .compact-title {
      white-space: normal;
      overflow: visible;
      text-overflow: unset;
    }
  }
</style>