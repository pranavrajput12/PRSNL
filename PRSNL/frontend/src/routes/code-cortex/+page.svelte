<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import {
    getDevelopmentStats,
    getDevelopmentCategories,
    getDevelopmentDocs,
  } from '$lib/api/development';

  let stats = {
    total_items: 0,
    by_language: {},
    by_category: {},
    by_difficulty: {},
    career_related_count: 0,
    recent_activity: [],
  };

  let categories = [];
  let recentDocs = [];
  let loading = true;

  onMount(async () => {
    try {
      // Load dashboard data
      const [statsData, categoriesData, docsData] = await Promise.all([
        getDevelopmentStats(),
        getDevelopmentCategories(),
        getDevelopmentDocs({ limit: 6 }),
      ]);

      stats = statsData;
      categories = categoriesData;
      recentDocs = docsData;
    } catch (error) {
      console.error('Error loading Code Cortex data:', error);
    } finally {
      loading = false;
    }
  });

  function navigateToSection(section: string) {
    goto(`/code-cortex/${section}`);
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
      sql: '🗃️',
    };
    return icons[language] || '💻';
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
</script>

<svelte:head>
  <title>Code Cortex - Development Hub | PRSNL</title>
</svelte:head>

<div class="code-cortex-dashboard">
  <!-- Header -->
  <div class="dashboard-header">
    <div class="header-content">
      <div class="header-left">
        <div class="cortex-icon">⚡</div>
        <div class="header-text">
          <h1>Code Cortex</h1>
          <p>Your development knowledge nexus</p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-chip">
          <span class="stat-value">{stats.total_items}</span>
          <span class="stat-label">Items</span>
        </div>
        <div class="stat-chip">
          <span class="stat-value">{Object.keys(stats.by_language).length}</span>
          <span class="stat-label">Languages</span>
        </div>
        <div class="stat-chip">
          <span class="stat-value">{stats.career_related_count}</span>
          <span class="stat-label">Career</span>
        </div>
      </div>
    </div>
  </div>

  {#if loading}
    <div class="loading-state">
      <div class="neural-pulse"></div>
      <span>Initializing neural pathways...</span>
    </div>
  {:else}
    <!-- Quick Navigation -->
    <div class="nav-grid">
      <button class="nav-card" on:click={() => navigateToSection('docs')}>
        <div class="nav-icon">📚</div>
        <div class="nav-content">
          <h3>Documentation</h3>
          <p>Technical docs and guides</p>
          <span class="nav-count"
            >{categories.find((c) => c.name === 'Documentation')?.item_count || 0}</span
          >
        </div>
      </button>

      <button class="nav-card" on:click={() => navigateToSection('links')}>
        <div class="nav-icon">🔗</div>
        <div class="nav-content">
          <h3>Useful Links</h3>
          <p>GitHub repos and resources</p>
          <span class="nav-count"
            >{stats.total_items -
              (categories.find((c) => c.name === 'Documentation')?.item_count || 0)}</span
          >
        </div>
      </button>

      <button class="nav-card" on:click={() => navigateToSection('synapses')}>
        <div class="nav-icon">🧠</div>
        <div class="nav-content">
          <h3>AI Synapses</h3>
          <p>Generated connections & guides</p>
          <span class="nav-count">0</span>
        </div>
      </button>

      <button class="nav-card" on:click={() => navigateToSection('projects')}>
        <div class="nav-icon">📋</div>
        <div class="nav-content">
          <h3>Projects</h3>
          <p>Organized by category</p>
          <span class="nav-count">{Object.keys(stats.by_category).length}</span>
        </div>
      </button>
    </div>

    <!-- Statistics Dashboard -->
    <div class="stats-section">
      <h2>Development Analytics</h2>

      <div class="stats-grid">
        <!-- Languages Chart -->
        <div class="stats-card">
          <h3>Programming Languages</h3>
          <div class="language-bars">
            {#each Object.entries(stats.by_language) as [language, count]}
              <div class="language-bar">
                <div class="language-info">
                  <span class="language-icon">{getLanguageIcon(language)}</span>
                  <span class="language-name">{language}</span>
                </div>
                <div class="bar-container">
                  <div
                    class="bar-fill"
                    style="width: {(count / Math.max(...Object.values(stats.by_language))) * 100}%"
                  ></div>
                  <span class="bar-count">{count}</span>
                </div>
              </div>
            {/each}
          </div>
        </div>

        <!-- Categories Chart -->
        <div class="stats-card">
          <h3>Project Categories</h3>
          <div class="category-grid">
            {#each Object.entries(stats.by_category) as [category, count]}
              <div class="category-item">
                <div class="category-icon">
                  {#if category === 'Frontend'}🎨
                  {:else if category === 'Backend'}⚙️
                  {:else if category === 'DevOps'}🚀
                  {:else if category === 'Mobile'}📱
                  {:else if category === 'AI/ML'}🤖
                  {:else if category === 'Data Science'}📊
                  {:else}📁{/if}
                </div>
                <div class="category-details">
                  <span class="category-name">{category}</span>
                  <span class="category-count">{count}</span>
                </div>
              </div>
            {/each}
          </div>
        </div>

        <!-- Difficulty Distribution -->
        <div class="stats-card">
          <h3>Difficulty Distribution</h3>
          <div class="difficulty-chart">
            {#each Object.entries(stats.by_difficulty) as [level, count]}
              <div class="difficulty-level">
                <div class="level-indicator level-{level}"></div>
                <span class="level-label">{getDifficultyLabel(parseInt(level))}</span>
                <span class="level-count">{count}</span>
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="activity-section">
      <h2>Recent Development Activity</h2>
      <div class="activity-feed">
        {#each stats.recent_activity as activity}
          <a href={activity.type === 'development' ? `/items/${activity.id}` : (activity.permalink || `/item/${activity.id}`)} class="activity-item clickable">
            <div class="activity-icon">
              {getLanguageIcon(activity.programming_language || 'unknown')}
            </div>
            <div class="activity-content">
              <h4>{activity.title}</h4>
              <div class="activity-meta">
                {#if activity.programming_language}
                  <span class="meta-tag">{activity.programming_language}</span>
                {/if}
                {#if activity.project_category}
                  <span class="meta-tag">{activity.project_category}</span>
                {/if}
                <span class="meta-time">{new Date(activity.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </a>
        {/each}

        {#if stats.recent_activity.length === 0}
          <div class="empty-state">
            <div class="empty-icon">⚡</div>
            <p>No development activity yet</p>
            <p class="empty-subtitle">Start by capturing some documentation or code resources!</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .code-cortex-dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    color: #00ff88;
    font-family: 'JetBrains Mono', monospace;
  }

  .dashboard-header {
    background: linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(220, 20, 60, 0.1));
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
  }

  .dashboard-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='rgba(0,255,136,0.03)'%3E%3Cpath d='M20 20c0-5.5-4.5-10-10-10s-10 4.5-10 10 4.5 10 10 10 10-4.5 10-10zm10 0c0-5.5-4.5-10-10-10s-10 4.5-10 10 4.5 10 10 10 10-4.5 10-10z'/%3E%3C/g%3E%3C/svg%3E");
    pointer-events: none;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;
    z-index: 1;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .cortex-icon {
    font-size: 3rem;
    filter: drop-shadow(0 0 10px #00ff88);
    animation: electric-pulse 2s ease-in-out infinite;
  }

  @keyframes electric-pulse {
    0%,
    100% {
      filter: drop-shadow(0 0 10px #00ff88);
    }
    50% {
      filter: drop-shadow(0 0 20px #00ff88) drop-shadow(0 0 30px #00ff88);
    }
  }

  .header-text h1 {
    font-size: 2.5rem;
    margin: 0;
    background: linear-gradient(45deg, #00ff88, #dc143c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .header-text p {
    margin: 0.5rem 0 0 0;
    opacity: 0.8;
    font-size: 1.1rem;
  }

  .header-stats {
    display: flex;
    gap: 1rem;
  }

  .stat-chip {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    text-align: center;
    min-width: 80px;
  }

  .stat-value {
    display: block;
    font-size: 1.5rem;
    font-weight: bold;
    color: #00ff88;
  }

  .stat-label {
    display: block;
    font-size: 0.875rem;
    opacity: 0.7;
    margin-top: 0.25rem;
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 300px;
    gap: 1rem;
  }

  .neural-pulse {
    width: 50px;
    height: 50px;
    border: 3px solid rgba(0, 255, 136, 0.3);
    border-top: 3px solid #00ff88;
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

  .nav-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }

  .nav-card {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
  }

  .nav-card:hover {
    border-color: #00ff88;
    background: rgba(0, 255, 136, 0.05);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 255, 136, 0.2);
  }

  .nav-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0, 255, 136, 0.1), transparent);
    transition: left 0.5s ease;
  }

  .nav-card:hover::before {
    left: 100%;
  }

  .nav-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    filter: drop-shadow(0 0 5px currentColor);
  }

  .nav-content h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.25rem;
    color: #00ff88;
  }

  .nav-content p {
    margin: 0 0 1rem 0;
    opacity: 0.8;
    font-size: 0.9rem;
  }

  .nav-count {
    background: rgba(220, 20, 60, 0.2);
    color: #dc143c;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: bold;
  }

  .stats-section h2,
  .activity-section h2 {
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    color: #00ff88;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }

  .stats-card {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
  }

  .stats-card h3 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    color: #00ff88;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .language-bars,
  .category-grid,
  .difficulty-chart {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .language-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .language-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 120px;
  }

  .language-name {
    font-size: 0.9rem;
    text-transform: capitalize;
  }

  .bar-container {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .bar-fill {
    height: 8px;
    background: linear-gradient(90deg, #00ff88, #dc143c);
    border-radius: 4px;
    min-width: 4px;
  }

  .bar-count {
    font-size: 0.875rem;
    color: #00ff88;
    min-width: 20px;
  }

  .category-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem;
    border-radius: 6px;
    background: rgba(0, 255, 136, 0.05);
  }

  .category-details {
    flex: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .difficulty-level {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .level-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }

  .level-indicator.level-1 {
    background: #10b981;
  }
  .level-indicator.level-2 {
    background: #3b82f6;
  }
  .level-indicator.level-3 {
    background: #f59e0b;
  }
  .level-indicator.level-4 {
    background: #ef4444;
  }
  .level-indicator.level-5 {
    background: #8b5cf6;
  }

  .activity-feed {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .activity-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
    text-decoration: none;
    color: inherit;
    transition: all 0.3s ease;
  }

  .activity-item.clickable:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: rgba(0, 255, 136, 0.4);
    transform: translateY(-2px);
  }

  .activity-icon {
    font-size: 1.5rem;
    min-width: 40px;
    text-align: center;
  }

  .activity-content h4 {
    margin: 0 0 0.5rem 0;
    color: #00ff88;
    font-size: 1rem;
  }

  .activity-meta {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .meta-tag {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .meta-time {
    color: rgba(0, 255, 136, 0.6);
    font-size: 0.75rem;
  }

  .empty-state {
    text-align: center;
    padding: 3rem;
    opacity: 0.6;
  }

  .empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .empty-subtitle {
    font-size: 0.9rem;
    opacity: 0.7;
    margin-top: 0.5rem;
  }

  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .code-cortex-dashboard {
      padding: 1rem;
    }

    .header-content {
      flex-direction: column;
      gap: 1rem;
      text-align: center;
    }

    .nav-grid {
      grid-template-columns: 1fr;
    }

    .stats-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
