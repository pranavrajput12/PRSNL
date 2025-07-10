<script lang="ts">
  import { onMount } from 'svelte';
  import { getDevelopmentStats, getDevelopmentCategories, getDevelopmentDocs, type DevelopmentItem } from '$lib/api/development';
  import Icon from '$lib/components/Icon.svelte';
  
  let categories = [];
  let stats = {
    by_category: {},
    by_language: {},
    by_difficulty: {}
  };
  let projectsByCategory: Record<string, DevelopmentItem[]> = {};
  let loading = true;
  let selectedCategory = '';
  let selectedView = 'grid'; // 'grid' or 'list'
  
  onMount(async () => {
    try {
      const [categoriesData, statsData] = await Promise.all([
        getDevelopmentCategories(),
        getDevelopmentStats()
      ]);
      
      categories = categoriesData;
      stats = statsData;
      
      // Load projects for each category
      await loadProjectsByCategory();
    } catch (error) {
      console.error('Error loading projects data:', error);
    } finally {
      loading = false;
    }
  });
  
  async function loadProjectsByCategory() {
    try {
      for (const category of categories) {
        const projects = await getDevelopmentDocs({
          category: category.name,
          limit: 10
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
      'Frontend': '🎨',
      'Backend': '⚙️',
      'DevOps': '🚀',
      'Mobile': '📱',
      'AI/ML': '🤖',
      'Data Science': '📊',
      'Game Development': '🎮',
      'Desktop': '💻',
      'Web Development': '🌐',
      'API Development': '🔌',
      'Documentation': '📚'
    };
    return icons[categoryName] || '📁';
  }
  
  function getCategoryColor(categoryName: string): string {
    const colors = {
      'Frontend': '#3b82f6',
      'Backend': '#10b981',
      'DevOps': '#f59e0b',
      'Mobile': '#8b5cf6',
      'AI/ML': '#ef4444',
      'Data Science': '#06b6d4',
      'Game Development': '#ec4899',
      'Desktop': '#6b7280',
      'Web Development': '#84cc16',
      'API Development': '#f97316',
      'Documentation': '#14b8a6'
    };
    return colors[categoryName] || '#6b7280';
  }
  
  function getLanguageIcon(language: string): string {
    const icons = {
      'python': '🐍',
      'javascript': '🟨',
      'typescript': '🔷',
      'java': '☕',
      'go': '🐹',
      'rust': '🦀',
      'cpp': '⚡',
      'html': '🌐',
      'css': '🎨'
    };
    return icons[language] || '💻';
  }
  
  function getDifficultyColor(level: number): string {
    const colors = {
      1: '#10b981', // Green
      2: '#3b82f6', // Blue  
      3: '#f59e0b', // Amber
      4: '#ef4444', // Red
      5: '#8b5cf6'  // Purple
    };
    return colors[level] || '#6b7280';
  }
  
  function getDifficultyLabel(level: number): string {
    const labels = {
      1: 'Beginner',
      2: 'Intermediate',
      3: 'Advanced',
      4: 'Expert',
      5: 'Master'
    };
    return labels[level] || 'Unknown';
  }
  
  $: filteredCategories = selectedCategory 
    ? categories.filter(cat => cat.name === selectedCategory)
    : categories;
</script>

<svelte:head>
  <title>Projects - Code Cortex | PRSNL</title>
</svelte:head>

<div class="projects-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-left">
      <a href="/code-cortex" class="back-link">
        <Icon name="arrow-left" size="small" />
        Code Cortex
      </a>
      <div class="header-content">
        <h1>📋 Project Categories</h1>
        <p>Organized development projects and learning paths</p>
      </div>
    </div>
    
    <div class="header-controls">
      <div class="view-toggle">
        <button 
          class="view-btn {selectedView === 'grid' ? 'active' : ''}"
          on:click={() => selectedView = 'grid'}
        >
          <Icon name="grid" size="small" />
          Grid
        </button>
        <button 
          class="view-btn {selectedView === 'list' ? 'active' : ''}"
          on:click={() => selectedView = 'list'}
        >
          <Icon name="list" size="small" />
          List
        </button>
      </div>
      
      <select bind:value={selectedCategory} class="category-filter">
        <option value="">All Categories</option>
        {#each categories as category}
          <option value={category.name}>{category.name}</option>
        {/each}
      </select>
    </div>
  </div>

  {#if loading}
    <div class="loading-state">
      <div class="neural-pulse"></div>
      <span>Loading project categories...</span>
    </div>
  {:else}
    <!-- Category Overview -->
    {#if !selectedCategory}
      <div class="overview-section">
        <h2>Category Overview</h2>
        <div class="overview-grid">
          {#each Object.entries(stats.by_category) as [categoryName, count]}
            {@const category = categories.find(cat => cat.name === categoryName)}
            <div class="overview-card" style="border-color: {getCategoryColor(categoryName)}">
              <div class="overview-icon" style="color: {getCategoryColor(categoryName)}">
                {getCategoryIcon(categoryName)}
              </div>
              <div class="overview-content">
                <h3>{categoryName}</h3>
                <p>{count} items</p>
                {#if category?.description}
                  <span class="overview-desc">{category.description}</span>
                {/if}
              </div>
              <button 
                class="overview-action"
                on:click={() => selectedCategory = categoryName}
              >
                View →
              </button>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Projects by Category -->
    <div class="projects-section">
      {#each filteredCategories as category}
        {@const projects = projectsByCategory[category.name] || []}
        {#if projects.length > 0}
          <div class="category-section">
            <div class="category-header">
              <div class="category-info">
                <span class="category-icon" style="color: {getCategoryColor(category.name)}">
                  {getCategoryIcon(category.name)}
                </span>
                <div>
                  <h2>{category.name}</h2>
                  {#if category.description}
                    <p class="category-description">{category.description}</p>
                  {/if}
                </div>
              </div>
              <div class="category-stats">
                <span class="stat-badge">{projects.length} items</span>
                {#if selectedCategory}
                  <button class="clear-filter" on:click={() => selectedCategory = ''}>
                    Show All
                  </button>
                {/if}
              </div>
            </div>

            <div class="projects-grid {selectedView}">
              {#each projects as project}
                <article class="project-card">
                  <div class="project-header">
                    <div class="project-meta">
                      {#if project.programming_language}
                        <span class="language-tag">
                          {getLanguageIcon(project.programming_language)} {project.programming_language}
                        </span>
                      {/if}
                      {#if project.difficulty_level}
                        <span 
                          class="difficulty-tag"
                          style="background: {getDifficultyColor(project.difficulty_level)}20; color: {getDifficultyColor(project.difficulty_level)}"
                        >
                          {getDifficultyLabel(project.difficulty_level)}
                        </span>
                      {/if}
                      {#if project.is_career_related}
                        <span class="career-tag">💼 Career</span>
                      {/if}
                    </div>
                    
                    <h3 class="project-title">
                      {#if project.url}
                        <a href={project.url} target="_blank" rel="noopener noreferrer">{project.title}</a>
                      {:else}
                        {project.title}
                      {/if}
                    </h3>
                  </div>
                  
                  {#if project.summary}
                    <p class="project-summary">{project.summary}</p>
                  {/if}
                  
                  <div class="project-footer">
                    <div class="project-tags">
                      {#each project.tags.slice(0, 3) as tag}
                        <span class="tag">#{tag}</span>
                      {/each}
                      {#if project.tags.length > 3}
                        <span class="tag-more">+{project.tags.length - 3}</span>
                      {/if}
                    </div>
                    
                    <div class="project-actions">
                      <span class="project-date">{new Date(project.created_at).toLocaleDateString()}</span>
                      {#if project.url}
                        <a href={project.url} target="_blank" rel="noopener noreferrer" class="project-link">
                          <Icon name="external-link" size="small" />
                        </a>
                      {/if}
                    </div>
                  </div>
                </article>
              {/each}
            </div>
          </div>
        {/if}
      {/each}
    </div>

    <!-- Empty State -->
    {#if !loading && categories.length === 0}
      <div class="empty-state">
        <div class="empty-icon">📋</div>
        <h3>No project categories found</h3>
        <p>Start organizing your development projects by adding content with different categories.</p>
        <a href="/capture" class="add-projects-btn">Add Projects</a>
      </div>
    {/if}
  {/if}
</div>

<style>
  .projects-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    color: #00ff88;
    font-family: 'JetBrains Mono', monospace;
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
    gap: 2rem;
  }
  
  .header-left {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    flex: 1;
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
    background: linear-gradient(45deg, #00ff88, #DC143C);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .header-content p {
    margin: 0.5rem 0 0 0;
    opacity: 0.8;
  }
  
  .header-controls {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .view-toggle {
    display: flex;
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 8px;
    overflow: hidden;
  }
  
  .view-btn {
    background: transparent;
    border: none;
    color: rgba(0, 255, 136, 0.7);
    padding: 0.5rem 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
  }
  
  .view-btn.active {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }
  
  .category-filter {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 6px;
    padding: 0.5rem 1rem;
    color: #00ff88;
    font-family: inherit;
    font-size: 0.9rem;
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
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .overview-section {
    margin-bottom: 3rem;
  }
  
  .overview-section h2 {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    color: #00ff88;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .overview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
  }
  
  .overview-card {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid;
    border-radius: 12px;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.3s ease;
    cursor: pointer;
  }
  
  .overview-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 255, 136, 0.2);
  }
  
  .overview-icon {
    font-size: 2rem;
    min-width: 50px;
    text-align: center;
  }
  
  .overview-content {
    flex: 1;
  }
  
  .overview-content h3 {
    margin: 0 0 0.25rem 0;
    font-size: 1.1rem;
    color: #00ff88;
  }
  
  .overview-content p {
    margin: 0;
    font-size: 0.9rem;
    opacity: 0.8;
  }
  
  .overview-desc {
    font-size: 0.8rem;
    opacity: 0.6;
    display: block;
    margin-top: 0.25rem;
  }
  
  .overview-action {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .overview-action:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }
  
  .category-section {
    margin-bottom: 3rem;
  }
  
  .category-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(0, 255, 136, 0.3);
  }
  
  .category-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .category-icon {
    font-size: 2rem;
  }
  
  .category-header h2 {
    margin: 0;
    font-size: 1.5rem;
    color: #00ff88;
  }
  
  .category-description {
    margin: 0.25rem 0 0 0;
    opacity: 0.7;
    font-size: 0.9rem;
  }
  
  .category-stats {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .stat-badge {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.875rem;
  }
  
  .clear-filter {
    background: rgba(220, 20, 60, 0.1);
    border: 1px solid rgba(220, 20, 60, 0.3);
    color: #DC143C;
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 0.875rem;
  }
  
  .clear-filter:hover {
    background: rgba(220, 20, 60, 0.2);
    border-color: #DC143C;
  }
  
  .projects-grid {
    display: grid;
    gap: 1.5rem;
  }
  
  .projects-grid.grid {
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  }
  
  .projects-grid.list {
    grid-template-columns: 1fr;
  }
  
  .project-card {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
  }
  
  .project-card:hover {
    border-color: #00ff88;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 255, 136, 0.2);
  }
  
  .project-header {
    margin-bottom: 1rem;
  }
  
  .project-meta {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
  }
  
  .language-tag, .difficulty-tag, .career-tag {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-weight: 500;
  }
  
  .language-tag {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }
  
  .career-tag {
    background: rgba(220, 20, 60, 0.2);
    color: #DC143C;
  }
  
  .project-title {
    margin: 0;
    font-size: 1.1rem;
    line-height: 1.4;
  }
  
  .project-title a {
    color: #00ff88;
    text-decoration: none;
    transition: color 0.3s ease;
  }
  
  .project-title a:hover {
    color: #DC143C;
  }
  
  .project-summary {
    margin: 0 0 1rem 0;
    opacity: 0.8;
    font-size: 0.9rem;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .project-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }
  
  .project-tags {
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
  
  .project-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .project-date {
    font-size: 0.75rem;
    color: rgba(0, 255, 136, 0.6);
  }
  
  .project-link {
    color: rgba(0, 255, 136, 0.7);
    transition: color 0.3s ease;
  }
  
  .project-link:hover {
    color: #00ff88;
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
  
  .add-projects-btn {
    background: linear-gradient(45deg, #00ff88, #DC143C);
    color: black;
    padding: 0.75rem 2rem;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    transition: transform 0.3s ease;
    display: inline-block;
  }
  
  .add-projects-btn:hover {
    transform: translateY(-2px);
  }
  
  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .projects-page {
      padding: 1rem;
    }
    
    .page-header {
      flex-direction: column;
      gap: 1rem;
    }
    
    .header-controls {
      justify-content: space-between;
      width: 100%;
    }
    
    .overview-grid {
      grid-template-columns: 1fr;
    }
    
    .projects-grid.grid {
      grid-template-columns: 1fr;
    }
    
    .category-header {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }
  }
</style>