<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import RepositoryCodePreview from '$lib/components/RepositoryCodePreview.svelte';
  import GitHubRepoCardV2 from '$lib/components/GitHubRepoCardV2.svelte';

  interface Repository {
    id: string;
    title: string;
    url: string;
    repository_metadata: {
      repo_url: string;
      repo_name: string;
      owner: string;
      description: string;
      stars: number;
      language: string;
      tech_stack: string[];
      category: string;
      difficulty: string;
      ai_analysis: {
        purpose: string;
        key_features: string[];
        confidence: number;
      };
    };
    created_at: string;
  }

  let repositories: Repository[] = [];
  let loading = true;
  let selectedRepository: Repository | null = null;
  let searchQuery = '';
  let selectedLanguage = '';
  let selectedCategory = '';
  let sortBy = 'recent';

  let availableLanguages: string[] = [];
  let availableCategories: string[] = [];

  onMount(async () => {
    await loadRepositories();
  });

  async function loadRepositories() {
    try {
      loading = true;

      // Fetch repositories from development API
      const response = await fetch('/api/development/repositories?limit=50');
      if (!response.ok) throw new Error('Failed to fetch repositories');

      const data = await response.json();
      repositories = (data.items || []).map((item) => ({
        ...item,
        repository_metadata:
          typeof item.repository_metadata === 'string'
            ? JSON.parse(item.repository_metadata)
            : item.repository_metadata,
      }));

      // Extract unique languages and categories for filters
      availableLanguages = [
        ...new Set(repositories.map((r) => r.repository_metadata?.language).filter(Boolean)),
      ].sort();

      availableCategories = [
        ...new Set(repositories.map((r) => r.repository_metadata?.category).filter(Boolean)),
      ].sort();
    } catch (error) {
      console.error('Error loading repositories:', error);
    } finally {
      loading = false;
    }
  }

  $: filteredRepositories = repositories
    .filter((repo) => {
      if (
        searchQuery &&
        !repo.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !repo.repository_metadata?.description?.toLowerCase().includes(searchQuery.toLowerCase())
      ) {
        return false;
      }
      if (selectedLanguage && repo.repository_metadata?.language !== selectedLanguage) {
        return false;
      }
      if (selectedCategory && repo.repository_metadata?.category !== selectedCategory) {
        return false;
      }
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'stars':
          return (b.repository_metadata?.stars || 0) - (a.repository_metadata?.stars || 0);
        case 'name':
          return (
            a.repository_metadata?.repo_name?.localeCompare(
              b.repository_metadata?.repo_name || ''
            ) || 0
          );
        case 'recent':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

  function formatStars(stars: number): string {
    if (stars >= 1000) {
      return `${(stars / 1000).toFixed(1)}k`;
    }
    return stars.toString();
  }

  function getLanguageColor(language: string): string {
    const colors: Record<string, string> = {
      javascript: '#f7df1e',
      typescript: '#3178c6',
      python: '#3776ab',
      java: '#ed8b00',
      go: '#00add8',
      rust: '#000000',
      cpp: '#00599c',
      csharp: '#239120',
      php: '#777bb4',
      ruby: '#cc342d',
      swift: '#fa7343',
      kotlin: '#7f52ff',
    };
    return colors[language?.toLowerCase()] || '#666';
  }

  function getCategoryIcon(category: string): string {
    const icons: Record<string, string> = {
      frontend: '🎨',
      backend: '⚙️',
      fullstack: '🌐',
      ai: '🤖',
      devops: '🚀',
      mobile: '📱',
      desktop: '💻',
      library: '📚',
      tool: '🔧',
      framework: '🏗️',
    };
    return icons[category?.toLowerCase()] || '📁';
  }

  function selectRepository(repo: Repository) {
    selectedRepository = repo;
  }

  function closePreview() {
    selectedRepository = null;
  }

  function goBack() {
    goto('/code-cortex');
  }

  // Transform repository data for GitHubRepoCardV2 component
  function transformRepositoryData(repo: Repository) {
    return {
      owner: {
        login: repo.repository_metadata?.owner || 'Unknown',
        avatar_url: `https://github.com/${repo.repository_metadata?.owner}.png`,
      },
      repo: {
        name: repo.repository_metadata?.repo_name || 'Unknown',
        full_name: repo.repository_metadata?.repo_name || 'Unknown',
        description: repo.repository_metadata?.description || 'No description available',
        language: repo.repository_metadata?.language || 'Unknown',
        private: false,
        stargazers_count: repo.repository_metadata?.stars || 0,
        forks_count: 0,
      },
      stats: {
        stars: repo.repository_metadata?.stars || 0,
        forks: 0,
        watchers: 0,
      },
      languages: repo.repository_metadata?.language
        ? {
            [repo.repository_metadata.language]: 100,
          }
        : {},
      topics: repo.repository_metadata?.tech_stack || [],
      last_updated: repo.created_at,
      url: repo.repository_metadata?.repo_url || repo.url,
    };
  }
</script>

<div class="open-source-page">
  <div class="page-header">
    <button class="back-button" on:click={goBack}>
      <Icon name="arrow-left" size="20" />
      Code Cortex
    </button>

    <div class="header-content">
      <h1>
        <Icon name="star" size="28" />
        Open Source Integrations
      </h1>
      <p>Saved repositories with code preview and AI analysis</p>
    </div>
  </div>

  <div class="controls-section">
    <div class="search-bar">
      <Icon name="search" size="20" />
      <input type="text" placeholder="Search repositories..." bind:value={searchQuery} />
    </div>

    <div class="filters">
      <select bind:value={selectedLanguage}>
        <option value="">All Languages</option>
        {#each availableLanguages as language}
          <option value={language}>{language}</option>
        {/each}
      </select>

      <select bind:value={selectedCategory}>
        <option value="">All Categories</option>
        {#each availableCategories as category}
          <option value={category}>{category}</option>
        {/each}
      </select>

      <select bind:value={sortBy}>
        <option value="recent">Recent</option>
        <option value="stars">Stars</option>
        <option value="name">Name</option>
      </select>
    </div>
  </div>

  {#if loading}
    <div class="loading">
      <Icon name="loader" size="32" class="animate-spin" />
      <span>Loading repositories...</span>
    </div>
  {:else if filteredRepositories.length === 0}
    <div class="empty-state">
      <Icon name="github" size="64" />
      <h2>No repositories found</h2>
      <p>
        {#if repositories.length === 0}
          Start by capturing some repositories in the <a href="/capture">Capture page</a>
        {:else}
          Try adjusting your filters or search query
        {/if}
      </p>
    </div>
  {:else}
    <div class="repositories-grid">
      {#each filteredRepositories as repo}
        <div class="repo-card-wrapper" on:click={() => goto(`/code-cortex/open-source/${repo.id}`)}>
          <GitHubRepoCardV2
            repository={transformRepositoryData(repo)}
            variant="featured"
            theme="dark"
          />

          <!-- Add custom metadata overlay -->
          <div class="repo-metadata-overlay">
            {#if repo.repository_metadata?.category}
              <span class="category-tag">
                {getCategoryIcon(repo.repository_metadata.category)}
                {repo.repository_metadata.category}
              </span>
            {/if}

            {#if repo.repository_metadata?.difficulty}
              <span class="difficulty-tag difficulty-{repo.repository_metadata.difficulty}">
                {repo.repository_metadata.difficulty}
              </span>
            {/if}

            <span class="ai-confidence">
              AI: {Math.round((repo.repository_metadata?.ai_analysis?.confidence || 0) * 100)}%
            </span>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Repository Code Preview Modal -->
  {#if selectedRepository}
    <div class="preview-modal" on:click={closePreview}>
      <div class="modal-content" on:click|stopPropagation>
        <div class="modal-header">
          <h2>
            <Icon name="github" size="24" />
            {selectedRepository.repository_metadata?.repo_name}
          </h2>
          <button class="close-button" on:click={closePreview}>
            <Icon name="x" size="24" />
          </button>
        </div>

        <div class="modal-body">
          <RepositoryCodePreview
            repositoryUrl={selectedRepository.repository_metadata?.repo_url ||
              selectedRepository.url}
            height="600px"
          />
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .open-source-page {
    min-height: 100vh;
    background: #0a0a0a;
    color: #e0e0e0;
    padding: 2rem;
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .back-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: transparent;
    border: 1px solid #333;
    color: #00ff88;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 1rem;
  }

  .back-button:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: #00ff88;
  }

  .header-content h1 {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 2.5rem;
    margin: 0 0 0.5rem 0;
    color: #00ff88;
    font-weight: 700;
  }

  .header-content p {
    font-size: 1.1rem;
    color: #888;
    margin: 0;
  }

  .controls-section {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }

  .search-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
    min-width: 300px;
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 0.75rem 1rem;
  }

  .search-bar input {
    flex: 1;
    background: transparent;
    border: none;
    color: #e0e0e0;
    font-size: 1rem;
    outline: none;
  }

  .search-bar input::placeholder {
    color: #666;
  }

  .filters {
    display: flex;
    gap: 1rem;
  }

  .filters select {
    background: #1a1a1a;
    border: 1px solid #333;
    color: #e0e0e0;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .filters select:focus {
    border-color: #00ff88;
    outline: none;
  }

  .loading,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
    color: #666;
  }

  .empty-state h2 {
    margin: 1rem 0 0.5rem 0;
    color: #e0e0e0;
  }

  .empty-state a {
    color: #00ff88;
    text-decoration: none;
  }

  .empty-state a:hover {
    text-decoration: underline;
  }

  .repositories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
    gap: 1.5rem;
  }

  .repo-card-wrapper {
    position: relative;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .repo-card-wrapper:hover {
    transform: translateY(-4px);
  }

  .repo-metadata-overlay {
    position: absolute;
    top: 1rem;
    right: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-end;
    z-index: 10;
  }

  .category-tag {
    padding: 0.25rem 0.75rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .difficulty-tag {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: capitalize;
  }

  .difficulty-beginner {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.3);
  }

  .difficulty-intermediate {
    background: rgba(251, 191, 36, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.3);
  }

  .difficulty-advanced {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  .ai-confidence {
    font-weight: 500;
    padding: 0.25rem 0.75rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    border-radius: 16px;
    font-size: 0.75rem;
  }

  /* Preview Modal */
  .preview-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 2rem;
  }

  .modal-content {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 12px;
    width: 100%;
    max-width: 1200px;
    max-height: 90vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #333;
  }

  .modal-header h2 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    color: #e0e0e0;
  }

  .close-button {
    background: transparent;
    border: none;
    color: #666;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 6px;
    transition: all 0.2s ease;
  }

  .close-button:hover {
    color: #e0e0e0;
    background: rgba(255, 255, 255, 0.1);
  }

  .modal-body {
    flex: 1;
    overflow: hidden;
    padding: 1rem;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .open-source-page {
      padding: 1rem;
    }

    .repositories-grid {
      grid-template-columns: 1fr;
    }

    .controls-section {
      flex-direction: column;
    }

    .filters {
      justify-content: stretch;
    }

    .filters select {
      flex: 1;
    }

    .preview-modal {
      padding: 1rem;
    }

    .modal-header {
      padding: 1rem;
    }

    .modal-body {
      padding: 0.5rem;
    }
  }

  /* Animation */
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>
