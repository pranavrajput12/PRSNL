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

  let categories = [];
  let stats = {
    by_category: {},
    by_language: {},
    by_difficulty: {},
  };
  let projectsByCategory: Record<string, DevelopmentItem[]> = {};
  let allProjects: DevelopmentItem[] = [];
  let loading = true;
  let selectedCategory = '';

  // UI State
  let activeTab = 'overview';
  let sidebarCollapsed = false;
  let viewMode: 'grid' | 'list' | 'kanban' = 'grid';
  let sortBy: 'recent' | 'difficulty' | 'name' | 'progress' = 'recent';

  // Project status tracking (simulated - would come from API in real implementation)
  const projectStatuses = ['planning', 'in-progress', 'review', 'completed', 'on-hold'];
  
  // Computed stats for header
  $: headerStats = [
    { label: 'Projects', value: allProjects.length },
    { label: 'Categories', value: Object.keys(stats.by_category).length },
    { label: 'In Progress', value: Math.floor(allProjects.length * 0.6) }, // Simulated
    { label: 'Completed', value: Math.floor(allProjects.length * 0.3) } // Simulated
  ] as CortexStat[];

  // Header actions
  $: headerActions = [
    {
      label: 'New Project',
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
    { id: 'overview', label: 'Overview', icon: 'pie-chart', count: Object.keys(stats.by_category).length },
    { id: 'all', label: 'All Progress', icon: 'list', count: allProjects.length },
    { id: 'in-progress', label: 'In Progress', icon: 'play', count: Math.floor(allProjects.length * 0.6) },
    { id: 'completed', label: 'Completed', icon: 'check', count: Math.floor(allProjects.length * 0.3) },
    { id: 'goals', label: 'Learning Goals', icon: 'target', count: Math.floor(allProjects.length * 0.1) }
  ] as CortexTab[];

  // Filtered projects based on active tab
  $: filteredProjects = (() => {
    // Only show items with learning progress tracking (learning paths, difficulty levels, or progress indicators)
    let projects = allProjects.filter(p => 
      p.learning_path || 
      p.difficulty_level || 
      p.is_career_related ||
      (p.tags && p.tags.some(tag => 
        tag.toLowerCase().includes('progress') ||
        tag.toLowerCase().includes('learning') ||
        tag.toLowerCase().includes('skill') ||
        tag.toLowerCase().includes('course') ||
        tag.toLowerCase().includes('certification') ||
        tag.toLowerCase().includes('goal')
      )) ||
      p.title.toLowerCase().includes('learn') ||
      p.title.toLowerCase().includes('skill') ||
      p.title.toLowerCase().includes('course')
    );
    
    // Filter by category
    if (selectedCategory) {
      projects = projects.filter(p => p.project_category === selectedCategory);
    }
    
    // Filter by tab
    switch (activeTab) {
      case 'in-progress':
        return projects.filter(p => getProjectStatus(p) === 'in-progress');
      case 'completed':
        return projects.filter(p => getProjectStatus(p) === 'completed');
      case 'goals':
        return projects.filter(p => 
          getProjectStatus(p) === 'planning' ||
          p.tags.some(tag => tag.toLowerCase().includes('goal')) ||
          p.title.toLowerCase().includes('goal')
        );
      case 'all':
        return projects;
      default:
        return projects;
    }
  })();

  // Sorted projects
  $: sortedProjects = filteredProjects.sort((a, b) => {
    switch (sortBy) {
      case 'difficulty':
        return (b.difficulty_level || 0) - (a.difficulty_level || 0);
      case 'name':
        return a.title.localeCompare(b.title);
      case 'progress':
        return getProjectProgress(b) - getProjectProgress(a);
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

      // Load all projects
      await loadAllProjects();
      await loadProjectsByCategory();
    } catch (error) {
      console.error('Error loading projects data:', error);
    } finally {
      loading = false;
    }
  });

  async function loadAllProjects() {
    try {
      const projects = await getDevelopmentDocs({ 
        limit: 100,
        content_type: 'progress'
      });
      allProjects = projects;
    } catch (error) {
      console.error('Error loading all projects:', error);
    }
  }

  async function loadProjectsByCategory() {
    try {
      for (const category of categories) {
        const projects = await getDevelopmentDocs({
          category: category.name,
          limit: 10,
          content_type: 'progress'
        });
        projectsByCategory[category.name] = projects;
      }
      projectsByCategory = { ...projectsByCategory }; // Trigger reactivity
    } catch (error) {
      console.error('Error loading projects by category:', error);
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

  // Simulated project status (would come from API)
  function getProjectStatus(project: DevelopmentItem): string {
    const hash = project.id.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
    return projectStatuses[hash % projectStatuses.length];
  }

  // Simulated project progress (would come from API)
  function getProjectProgress(project: DevelopmentItem): number {
    const hash = project.id.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
    return (hash % 100);
  }

  function getStatusColor(status: string): string {
    const colors = {
      planning: '#6b7280',
      'in-progress': '#3b82f6',
      review: '#f59e0b',
      completed: '#10b981',
      'on-hold': '#ef4444'
    };
    return colors[status] || '#6b7280';
  }

  function getStatusIcon(status: string): string {
    const icons = {
      planning: 'edit',
      'in-progress': 'play',
      review: 'eye',
      completed: 'check',
      'on-hold': 'pause'
    };
    return icons[status] || 'circle';
  }

  function createProjectCard(project: DevelopmentItem) {
    const status = getProjectStatus(project);
    const progress = getProjectProgress(project);
    
    const tags = [
      { label: `${getCategoryIcon(project.project_category)} ${project.project_category}`, color: getCategoryColor(project.project_category) + '40' },
      ...(project.programming_language ? [{ label: `${getLanguageIcon(project.programming_language)} ${project.programming_language}`, color: 'rgba(0, 255, 136, 0.2)' }] : []),
      ...(project.difficulty_level ? [{ label: getDifficultyLabel(project.difficulty_level), color: getDifficultyColor(project.difficulty_level) + '40' }] : []),
      { label: status.charAt(0).toUpperCase() + status.slice(1), color: getStatusColor(status) + '40' }
    ];

    const stats = [
      { label: 'Progress', value: `${progress}%` },
      { label: 'Status', value: status.charAt(0).toUpperCase() + status.slice(1) },
      { label: 'Created', value: new Date(project.created_at).toLocaleDateString() }
    ];

    const actions = [
      { label: 'View Details', icon: 'eye', onClick: () => window.location.href = project.permalink || `/item/${project.id}` },
      ...(project.url ? [{ label: 'Source', icon: 'external-link', onClick: () => window.open(project.url, '_blank') }] : [])
    ];

    return {
      title: project.title,
      description: project.summary || 'No description available',
      icon: 'folder',
      iconColor: getCategoryColor(project.project_category),
      tags,
      stats,
      actions,
      onClick: () => window.location.href = project.permalink || `/item/${project.id}`,
      variant: status === 'completed' ? 'highlight' : 'default'
    };
  }

  function createCategoryCard(categoryName: string, count: number) {
    const category = categories.find(c => c.name === categoryName);
    return {
      title: categoryName,
      description: category?.description || `${count} projects in this category`,
      icon: getCategoryIcon(categoryName),
      iconColor: getCategoryColor(categoryName),
      tags: [{ label: `${count} projects`, color: getCategoryColor(categoryName) + '40' }],
      stats: [{ label: 'Projects', value: count }],
      actions: [{ label: 'View Projects', icon: 'arrow-right', onClick: () => { activeTab = 'all'; selectedCategory = categoryName; } }],
      onClick: () => { activeTab = 'all'; selectedCategory = categoryName; },
      variant: 'default'
    };
  }
</script>

<svelte:head>
  <title>Progress - Code Cortex | PRSNL</title>
</svelte:head>

<div class="projects-page">
  <CortexPageHeader
    title="Learning Progress"
    description="Track your personal learning journey and project status"
    icon="trending-up"
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
    sidebarTitle="Project Management"
    collapsible={true}
  >
    <div slot="sidebar" class="sidebar-content">
      <!-- Project Filters -->
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
            <option value="difficulty">Difficulty</option>
            <option value="name">Name</option>
            <option value="progress">Progress</option>
          </select>
        </div>
      </div>

      <!-- Project Statistics -->
      <div class="filter-section">
        <h4>Project Stats</h4>
        <div class="project-stats">
          <div class="stat-row">
            <span class="stat-label">Total Projects</span>
            <span class="stat-value">{allProjects.length}</span>
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
          {#each projectStatuses as status}
            {@const count = filteredProjects.filter(p => getProjectStatus(p) === status).length}
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
          message="Loading project categories..." 
          variant="pulse"
          size="md"
        />
      {:else if activeTab === 'overview'}
        <!-- Category Overview -->
        <div class="overview-section">
          <div class="section-header">
            <h2>Category Overview</h2>
            <p>Explore your projects organized by technology and domain</p>
          </div>
          
          {#if Object.keys(stats.by_category).length === 0}
            <CortexEmptyState
              icon="folder-plus"
              title="No project categories found"
              description="Start organizing your development projects by adding content with different categories."
              actionLabel="Add Projects"
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
        <!-- Projects Listing -->
        <div class="projects-section">
          {#if sortedProjects.length === 0}
            <CortexEmptyState
              icon="folder-x"
              title="No projects found"
              description="Try adjusting your filters or add some projects to get started."
              actionLabel="Add Projects"
              actionHref="/capture"
              size="md"
            />
          {:else}
            {#if viewMode === 'kanban'}
              <!-- Kanban View -->
              <div class="kanban-board">
                {#each projectStatuses as status}
                  {@const statusProjects = sortedProjects.filter(p => getProjectStatus(p) === status)}
                  {#if statusProjects.length > 0}
                    <div class="kanban-column">
                      <div class="kanban-header" style="border-color: {getStatusColor(status)}">
                        <Icon name={getStatusIcon(status)} size="16" style="color: {getStatusColor(status)}" />
                        <h3>{status.charAt(0).toUpperCase() + status.slice(1)}</h3>
                        <span class="kanban-count">{statusProjects.length}</span>
                      </div>
                      <div class="kanban-items">
                        {#each statusProjects as project}
                          <div class="kanban-card" on:click={() => window.location.href = project.permalink || `/item/${project.id}`}>
                            <h4>{project.title}</h4>
                            <div class="kanban-meta">
                              {#if project.programming_language}
                                <span class="meta-tag">{getLanguageIcon(project.programming_language)} {project.programming_language}</span>
                              {/if}
                              <span class="meta-tag">{project.project_category}</span>
                            </div>
                            <div class="progress-bar">
                              <div class="progress-fill" style="width: {getProjectProgress(project)}%; background-color: {getStatusColor(status)}"></div>
                            </div>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}
                {/each}
              </div>
            {:else}
              <div class="projects-container {viewMode}">
                {#each sortedProjects as project}
                  {#if viewMode === 'grid'}
                    <CortexCard {...createProjectCard(project)} size="md" />
                  {:else}
                    <!-- List view for projects -->
                    <div class="project-list-item">
                      <div class="project-list-header">
                        <div class="project-list-title">
                          <Icon name={getStatusIcon(getProjectStatus(project))} size="20" style="color: {getStatusColor(getProjectStatus(project))}" />
                          <a href={project.permalink || `/item/${project.id}`}>
                            {project.title}
                          </a>
                        </div>
                        <div class="project-list-meta">
                          <span class="meta-tag">{project.project_category}</span>
                          {#if project.programming_language}
                            <span class="meta-tag">{getLanguageIcon(project.programming_language)} {project.programming_language}</span>
                          {/if}
                          <span class="meta-date">{new Date(project.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      {#if project.summary}
                        <p class="project-list-summary">{project.summary}</p>
                      {/if}
                      <div class="project-list-footer">
                        <div class="progress-indicator">
                          <span class="progress-label">{getProjectProgress(project)}% complete</span>
                          <div class="progress-bar">
                            <div class="progress-fill" style="width: {getProjectProgress(project)}%; background-color: {getStatusColor(getProjectStatus(project))}"></div>
                          </div>
                        </div>
                        <span class="status-badge" style="background-color: {getStatusColor(getProjectStatus(project))}40; color: {getStatusColor(getProjectStatus(project))}">
                          {getProjectStatus(project)}
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
  .projects-page {
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

  .project-stats {
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

  .projects-container.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .projects-container.list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .learning-list-item {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.2s ease;
  }

  .learning-list-item:hover {
    border-color: rgba(0, 255, 136, 0.4);
    background: rgba(0, 255, 136, 0.05);
  }

  .learning-list-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .learning-list-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .learning-list-title a {
    color: #00ff88;
    text-decoration: none;
    font-weight: 500;
  }

  .learning-list-title a:hover {
    color: #dc143c;
  }

  .learning-list-meta {
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
    color: #666;
  }

  .learning-list-summary {
    margin: 0 0 1rem 0;
    color: #ccc;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .learning-list-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }

  .progress-indicator {
    flex: 1;
  }

  .progress-label {
    font-size: 0.75rem;
    color: #888;
    margin-bottom: 0.25rem;
    display: block;
  }

  .progress-bar {
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s ease;
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

  /* Responsive */
  @media (max-width: 768px) {
    .projects-page {
      padding: 1rem;
    }

    .overview-grid,
    .projects-container.grid {
      grid-template-columns: 1fr;
    }

    .kanban-board {
      grid-template-columns: 1fr;
    }

    .learning-list-header {
      flex-direction: column;
      gap: 0.5rem;
    }

    .learning-list-meta {
      align-self: flex-start;
    }

    .learning-list-footer {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }
  }
</style>