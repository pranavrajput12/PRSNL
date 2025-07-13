<script lang="ts">
  import { onMount } from 'svelte';
  import {
    getDevelopmentStats,
    getDevelopmentCategories,
    getDevelopmentDocs,
    type DevelopmentItem,
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

  let repositories: DevelopmentItem[] = [];
  let categories = [];
  let stats = {
    by_category: {},
    by_language: {},
    by_difficulty: {},
  };
  let repositoriesByCategory: Record<string, DevelopmentItem[]> = {};
  let loading = true;
  let selectedCategory = '';

  // UI State
  let activeTab = 'overview';
  let sidebarCollapsed = false;
  let viewMode: 'grid' | 'list' | 'kanban' = 'grid';
  let sortBy: 'recent' | 'stars' | 'name' | 'language' = 'recent';

  // Repository status tracking
  const repoStatuses = ['starred', 'analyzed', 'watching', 'forked', 'contributed'];
  
  // Computed stats for header
  $: headerStats = [
    { label: 'Repositories', value: repositories.length },
    { label: 'Languages', value: Object.keys(stats.by_language || {}).length },
    { label: 'Analyzed', value: Math.floor(repositories.length * 0.8) },
    { label: 'Starred', value: Math.floor(repositories.length * 0.4) }
  ] as CortexStat[];

  // Header actions
  $: headerActions = [
    {
      label: 'Add Integration',
      icon: 'plus',
      onClick: () => window.location.href = '/capture',
      variant: 'primary'
    },
    {
      label: viewMode === 'grid' ? 'List View' : viewMode === 'list' ? 'Kanban View' : 'Grid View',
      icon: viewMode === 'grid' ? 'list' : viewMode === 'list' ? 'columns' : 'grid',
      onClick: () => {
        if (viewMode === 'grid') viewMode = 'list';
        else if (viewMode === 'list') viewMode = 'kanban';
        else viewMode = 'grid';
      },
      variant: 'secondary'
    }
  ] as CortexAction[];

  // Tab configuration
  $: tabs = [
    { id: 'overview', label: 'Overview', icon: 'pie-chart', count: Object.keys(stats.by_category || {}).length },
    { id: 'all', label: 'All Integrations', icon: 'package', count: repositories.length },
    { id: 'libraries', label: 'Libraries', icon: 'book', count: Math.floor(repositories.length * 0.6) },
    { id: 'frameworks', label: 'Frameworks', icon: 'layers', count: Math.floor(repositories.length * 0.3) },
    { id: 'tools', label: 'Dev Tools', icon: 'tool', count: Math.floor(repositories.length * 0.1) }
  ] as CortexTab[];

  // Filtered repositories based on active tab
  $: filteredRepositories = (() => {
    // Only show open source integration repositories
    let repos = repositories.filter(r => 
      r.url && (r.url.includes('github.com') || r.url.includes('gitlab.com') || r.url.includes('bitbucket.')) &&
      r.project_category && 
      // Focus on integrations, libraries, frameworks, and dev tools
      (r.tags.some(tag => tag.toLowerCase().includes('library') || 
                          tag.toLowerCase().includes('framework') || 
                          tag.toLowerCase().includes('integration') ||
                          tag.toLowerCase().includes('tool') ||
                          tag.toLowerCase().includes('sdk') ||
                          tag.toLowerCase().includes('api')) ||
       r.project_category.toLowerCase().includes('library') ||
       r.project_category.toLowerCase().includes('framework') ||
       r.project_category.toLowerCase().includes('tool'))
    );
    
    // Filter by category
    if (selectedCategory) {
      repos = repos.filter(r => r.project_category === selectedCategory);
    }
    
    // Filter by tab
    switch (activeTab) {
      case 'libraries':
        return repos.filter(r => 
          r.tags.some(tag => tag.toLowerCase().includes('library')) ||
          r.project_category.toLowerCase().includes('library') ||
          r.title.toLowerCase().includes('library')
        );
      case 'frameworks':
        return repos.filter(r => 
          r.tags.some(tag => tag.toLowerCase().includes('framework')) ||
          r.project_category.toLowerCase().includes('framework') ||
          r.title.toLowerCase().includes('framework')
        );
      case 'tools':
        return repos.filter(r => 
          r.tags.some(tag => tag.toLowerCase().includes('tool') || tag.toLowerCase().includes('cli')) ||
          r.project_category.toLowerCase().includes('tool') ||
          r.title.toLowerCase().includes('tool')
        );
      case 'all':
        return repos;
      default:
        return repos;
    }
  })();

  // Sorted repositories
  $: sortedRepositories = filteredRepositories.sort((a, b) => {
    switch (sortBy) {
      case 'stars':
        return getRepoStars(b) - getRepoStars(a);
      case 'name':
        return a.title.localeCompare(b.title);
      case 'language':
        return (a.programming_language || '').localeCompare(b.programming_language || '');
      default: // recent
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    }
  });

  onMount(async () => {
    try {
      const [categoriesData, statsData] = await Promise.all([
        getDevelopmentCategories(),
        getDevelopmentStats(),
      ]);

      categories = categoriesData;
      stats = statsData;

      // Load all repositories
      await loadAllRepositories();
      await loadRepositoriesByCategory();
    } catch (error) {
      console.error('Error loading repository data:', error);
    } finally {
      loading = false;
    }
  });

  async function loadAllRepositories() {
    try {
      const repos = await getDevelopmentDocs({ 
        limit: 100,
        content_type: 'repositories'
      });
      repositories = repos;
    } catch (error) {
      console.error('Error loading all repositories:', error);
    }
  }

  async function loadRepositoriesByCategory() {
    try {
      for (const category of categories) {
        const repos = await getDevelopmentDocs({
          category: category.name,
          limit: 10,
          content_type: 'repositories'
        });
        repositoriesByCategory[category.name] = repos;
      }
      repositoriesByCategory = { ...repositoriesByCategory };
    } catch (error) {
      console.error('Error loading repositories by category:', error);
    }
  }

  function getCategoryIcon(categoryName: string): string {
    const icons = {
      Frontend: '🎨',
      Backend: '⚙️',
      DevOps: '🚀',
      Mobile: '📱',
      'AI/ML': '🤖',
      'Data Science': '📊',
      'Game Development': '🎮',
      Desktop: '💻',
      'Web Development': '🌐',
      'API Development': '🔌',
      Documentation: '📚',
    };
    return icons[categoryName] || '📁';
  }

  function getCategoryColor(categoryName: string): string {
    const colors = {
      Frontend: '#3b82f6',
      Backend: '#10b981',
      DevOps: '#f59e0b',
      Mobile: '#8b5cf6',
      'AI/ML': '#ef4444',
      'Data Science': '#06b6d4',
      'Game Development': '#ec4899',
      Desktop: '#6b7280',
      'Web Development': '#84cc16',
      'API Development': '#f97316',
      Documentation: '#14b8a6',
    };
    return colors[categoryName] || '#6b7280';
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

  // Simulated repository status (would come from API)
  function getRepoStatus(repo: DevelopmentItem): string {
    const hash = repo.id.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
    return repoStatuses[hash % repoStatuses.length];
  }

  // Simulated repository stars (would come from API)
  function getRepoStars(repo: DevelopmentItem): number {
    const hash = repo.id.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
    return (hash % 1000) + 1;
  }

  function getStatusColor(status: string): string {
    const colors = {
      starred: '#f59e0b',
      analyzed: '#3b82f6',
      watching: '#10b981',
      forked: '#8b5cf6',
      contributed: '#ef4444'
    };
    return colors[status] || '#6b7280';
  }

  function getStatusIcon(status: string): string {
    const icons = {
      starred: 'star',
      analyzed: 'brain',
      watching: 'eye',
      forked: 'git-branch',
      contributed: 'git-commit'
    };
    return icons[status] || 'github';
  }

  function createRepositoryCard(repo: DevelopmentItem) {
    const status = getRepoStatus(repo);
    const stars = getRepoStars(repo);
    
    const tags = [
      { label: `${getCategoryIcon(repo.project_category)} ${repo.project_category}`, color: getCategoryColor(repo.project_category) + '40' },
      ...(repo.programming_language ? [{ label: `${getLanguageIcon(repo.programming_language)} ${repo.programming_language}`, color: 'rgba(0, 255, 136, 0.2)' }] : []),
      { label: status.charAt(0).toUpperCase() + status.slice(1), color: getStatusColor(status) + '40' }
    ];

    const stats = [
      { label: 'Stars', value: `${stars}` },
      { label: 'Status', value: status.charAt(0).toUpperCase() + status.slice(1) },
      { label: 'Added', value: new Date(repo.created_at).toLocaleDateString() }
    ];

    const actions = [
      { label: 'View Repository', icon: 'github', onClick: () => window.open(repo.url, '_blank') },
      { label: 'Analysis', icon: 'brain', onClick: () => window.location.href = `/code-cortex/open-source/${repo.id}` }
    ];

    return {
      title: repo.title,
      description: repo.summary || 'No description available',
      icon: 'github',
      iconColor: getCategoryColor(repo.project_category),
      tags,
      stats,
      actions,
      onClick: () => window.location.href = `/code-cortex/open-source/${repo.id}`,
      variant: status === 'starred' ? 'highlight' : 'default'
    };
  }

  function createCategoryCard(categoryName: string, count: number) {
    const category = categories.find(c => c.name === categoryName);
    return {
      title: categoryName,
      description: category?.description || `${count} repositories in this category`,
      icon: getCategoryIcon(categoryName),
      iconColor: getCategoryColor(categoryName),
      tags: [{ label: `${count} repos`, color: getCategoryColor(categoryName) + '40' }],
      stats: [{ label: 'Repositories', value: count }],
      actions: [{ label: 'View Repos', icon: 'arrow-right', onClick: () => { activeTab = 'all'; selectedCategory = categoryName; } }],
      onClick: () => { activeTab = 'all'; selectedCategory = categoryName; },
      variant: 'default'
    };
  }
</script>

<svelte:head>
  <title>Open Source Integrations - Code Cortex | PRSNL</title>
</svelte:head>

<div class="repositories-page">
  <CortexPageHeader
    title="Open Source Integrations"
    description="Curated open source libraries and integrations for your projects"
    icon="package"
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
    sidebarTitle="Repository Filters"
    collapsible={true}
  >
    <div slot="sidebar" class="sidebar-content">
      <!-- Repository Filters -->
      <div class="filter-section">
        <h4>Filters</h4>
        
        <div class="filter-group">
          <label>Category</label>
          <select bind:value={selectedCategory} class="filter-select">
            <option value="">All Categories</option>
            {#each categories as category}
              <option value={category.name}>{category.name}</option>
            {/each}
          </select>
        </div>

        <div class="filter-group">
          <label>Sort By</label>
          <select bind:value={sortBy} class="filter-select">
            <option value="recent">Most Recent</option>
            <option value="stars">Most Stars</option>
            <option value="name">Name</option>
            <option value="language">Language</option>
          </select>
        </div>
      </div>

      <!-- Repository Statistics -->
      <div class="filter-section">
        <h4>Repository Stats</h4>
        <div class="repository-stats">
          <div class="stat-row">
            <span class="stat-label">Repositories</span>
            <span class="stat-value">{repositories.length}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Categories</span>
            <span class="stat-value">{Object.keys(stats.by_category).length}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Languages</span>
            <span class="stat-value">{Object.keys(stats.by_language).length}</span>
          </div>
        </div>
      </div>

      <!-- Category Breakdown -->
      <div class="filter-section">
        <h4>Categories</h4>
        <div class="category-breakdown">
          {#each Object.entries(stats.by_category).slice(0, 6) as [categoryName, count]}
            <div class="category-item" on:click={() => { selectedCategory = categoryName; activeTab = 'all'; }}>
              <span class="category-icon" style="color: {getCategoryColor(categoryName)}">
                {getCategoryIcon(categoryName)}
              </span>
              <span class="category-name">{categoryName}</span>
              <span class="category-count">{count}</span>
            </div>
          {/each}
        </div>
      </div>

      <!-- Status Distribution -->
      <div class="filter-section">
        <h4>Status Distribution</h4>
        <div class="status-breakdown">
          {#each repoStatuses as status}
            {@const count = filteredRepositories.filter(r => getRepoStatus(r) === status).length}
            {#if count > 0}
              <div class="status-item">
                <Icon name={getStatusIcon(status)} size="16" style="color: {getStatusColor(status)}" />
                <span class="status-name">{status.charAt(0).toUpperCase() + status.slice(1)}</span>
                <span class="status-count">{count}</span>
              </div>
            {/if}
          {/each}
        </div>
      </div>
    </div>

    <div slot="content" class="main-content">
      {#if loading}
        <CortexLoadingState 
          message="Loading repositories..." 
          variant="pulse"
          size="md"
        />
      {:else if activeTab === 'overview'}
        <!-- Category Overview -->
        <div class="overview-section">
          <div class="section-header">
            <h2>Repository Overview</h2>
            <p>Explore your GitHub repositories organized by technology and language</p>
          </div>
          
          {#if Object.keys(stats.by_category).length === 0}
            <CortexEmptyState
              icon="github"
              title="No repository categories found"
              description="Start organizing your repositories by adding GitHub repos with different technologies."
              actionLabel="Add Repository"
              actionHref="/capture"
              size="md"
            />
          {:else}
            <div class="overview-grid">
              {#each Object.entries(stats.by_category) as [categoryName, count]}
                <CortexCard {...createCategoryCard(categoryName, count)} size="md" />
              {/each}
            </div>
          {/if}
        </div>
      {:else}
        <!-- Repository Listing -->
        <div class="repository-section">
          {#if sortedRepositories.length === 0}
            <CortexEmptyState
              icon="github"
              title="No repositories found"
              description="Try adjusting your filters or add some GitHub repositories to get started."
              actionLabel="Add Repository"
              actionHref="/capture"
              size="md"
            />
          {:else}
            {#if viewMode === 'kanban'}
              <!-- Kanban View -->
              <div class="kanban-board">
                {#each repoStatuses as status}
                  {@const statusRepos = sortedRepositories.filter(r => getRepoStatus(r) === status)}
                  {#if statusRepos.length > 0}
                    <div class="kanban-column">
                      <div class="kanban-header" style="border-color: {getStatusColor(status)}">
                        <Icon name={getStatusIcon(status)} size="16" style="color: {getStatusColor(status)}" />
                        <h3>{status.charAt(0).toUpperCase() + status.slice(1)}</h3>
                        <span class="kanban-count">{statusRepos.length}</span>
                      </div>
                      <div class="kanban-items">
                        {#each statusRepos as repo}
                          <div class="kanban-card" on:click={() => window.open(repo.url, '_blank')}>
                            <h4>{repo.title}</h4>
                            <div class="kanban-meta">
                              {#if repo.programming_language}
                                <span class="meta-tag">{getLanguageIcon(repo.programming_language)} {repo.programming_language}</span>
                              {/if}
                              <span class="meta-tag">{repo.project_category}</span>
                            </div>
                            <div class="repo-stats">
                              <span class="stars">⭐ {getRepoStars(repo)}</span>
                            </div>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}
                {/each}
              </div>
            {:else}
              <div class="repositories-container {viewMode}">
                {#each sortedRepositories as repo}
                  {#if viewMode === 'grid'}
                    <CortexCard {...createRepositoryCard(repo)} size="md" />
                  {:else}
                    <!-- List view for repositories -->
                    <div class="repository-list-item">
                      <div class="repository-list-header">
                        <div class="repository-list-title">
                          <Icon name={getStatusIcon(getRepoStatus(repo))} size="20" style="color: {getStatusColor(getRepoStatus(repo))}" />
                          <a href={repo.url} target="_blank" rel="noopener noreferrer">
                            {repo.title}
                          </a>
                        </div>
                        <div class="repository-list-meta">
                          <span class="meta-tag">{repo.project_category}</span>
                          {#if repo.programming_language}
                            <span class="meta-tag">{getLanguageIcon(repo.programming_language)} {repo.programming_language}</span>
                          {/if}
                          <span class="stars-badge">⭐ {getRepoStars(repo)}</span>
                          <span class="meta-date">{new Date(repo.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      {#if repo.summary}
                        <p class="repository-list-summary">{repo.summary}</p>
                      {/if}
                      <div class="repository-list-footer">
                        <span class="status-badge" style="background-color: {getStatusColor(getRepoStatus(repo))}40; color: {getStatusColor(getRepoStatus(repo))}">
                          {getRepoStatus(repo)}
                        </span>
                      </div>
                    </div>
                  {/if}
                {/each}
              </div>
            {/if}
          {/if}
        </div>
      {/if}
    </div>
  </CortexContentLayout>
</div>

<style>
  .repositories-page {
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

  .repository-stats {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.25rem 0;
  }

  .stat-label {
    font-size: 0.75rem;
    color: #888;
  }

  .stat-value {
    font-size: 0.875rem;
    font-weight: 600;
    color: #00ff88;
  }

  .category-breakdown {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .category-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.1);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .category-item:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: rgba(0, 255, 136, 0.3);
  }

  .category-icon {
    font-size: 1rem;
    min-width: 20px;
  }

  .category-name {
    flex: 1;
    font-size: 0.75rem;
    color: #ccc;
  }

  .category-count {
    font-size: 0.75rem;
    color: #00ff88;
    background: rgba(0, 255, 136, 0.2);
    padding: 0.125rem 0.5rem;
    border-radius: 12px;
  }

  .status-breakdown {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0;
  }

  .status-name {
    flex: 1;
    font-size: 0.75rem;
    color: #ccc;
    text-transform: capitalize;
  }

  .status-count {
    font-size: 0.75rem;
    color: #888;
  }

  .main-content {
    flex: 1;
  }

  .overview-section {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .section-header h2 {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
    color: #00ff88;
  }

  .section-header p {
    margin: 0;
    color: #888;
    font-size: 0.875rem;
  }

  .overview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .repositories-container.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .repositories-container.list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .repository-list-item {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.2s ease;
  }

  .repository-list-item:hover {
    border-color: rgba(0, 255, 136, 0.4);
    background: rgba(0, 255, 136, 0.05);
  }

  .repository-list-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .repository-list-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .repository-list-title a {
    color: #00ff88;
    text-decoration: none;
    font-weight: 500;
  }

  .repository-list-title a:hover {
    color: #dc143c;
  }

  .repository-list-meta {
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

  .stars-badge {
    padding: 0.25rem 0.5rem;
    background: rgba(255, 193, 7, 0.2);
    color: #ffc107;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .meta-date {
    font-size: 0.75rem;
    color: #666;
  }

  .repository-list-summary {
    margin: 0 0 1rem 0;
    color: #ccc;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .repository-list-footer {
    display: flex;
    justify-content: flex-end;
    align-items: center;
  }

  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: capitalize;
  }

  /* Kanban View */
  .kanban-board {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    align-items: start;
  }

  .kanban-column {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    overflow: hidden;
  }

  .kanban-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    background: rgba(0, 255, 136, 0.05);
    border-bottom: 1px solid rgba(0, 255, 136, 0.2);
  }

  .kanban-header h3 {
    flex: 1;
    margin: 0;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .kanban-count {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
    padding: 0.125rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .kanban-items {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 60vh;
    overflow-y: auto;
  }

  .kanban-card {
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 6px;
    padding: 0.75rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .kanban-card:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: rgba(0, 255, 136, 0.4);
  }

  .kanban-card h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    color: #e0e0e0;
    line-height: 1.3;
  }

  .kanban-meta {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .kanban-meta .meta-tag {
    font-size: 0.7rem;
    padding: 0.125rem 0.375rem;
  }

  .repo-stats {
    display: flex;
    justify-content: flex-end;
  }

  .stars {
    font-size: 0.75rem;
    color: #ffc107;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .repositories-page {
      padding: 1rem;
    }

    .overview-grid,
    .repositories-container.grid {
      grid-template-columns: 1fr;
    }

    .kanban-board {
      grid-template-columns: 1fr;
    }

    .repository-list-header {
      flex-direction: column;
      gap: 0.5rem;
    }

    .repository-list-meta {
      align-self: flex-start;
    }
  }
</style>