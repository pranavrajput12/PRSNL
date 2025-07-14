<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  
  interface Props {
    selected: any;
  }
  
  let { selected = $bindable() }: Props = $props();
  
  let repos = $state([]);
  let loading = $state(false);
  let isConnected = $state(false);
  
  onMount(async () => {
    await loadRepos();
  });
  
  async function loadRepos() {
    loading = true;
    try {
      // Check GitHub connection
      const connectionResponse = await api.get('/github/accounts');
      isConnected = connectionResponse.data && connectionResponse.data.length > 0;
      
      if (isConnected) {
        // Load repositories
        const reposResponse = await api.get('/github/repos');
        repos = reposResponse.data || [];
      }
    } catch (error) {
      console.error('Failed to load repositories:', error);
      isConnected = false;
      repos = [];
    } finally {
      loading = false;
    }
  }
  
  async function connectGitHub() {
    try {
      const response = await api.get('/github/auth/login');
      if (response.data.auth_url) {
        window.location.href = response.data.auth_url;
      }
    } catch (error) {
      console.error('Failed to connect to GitHub:', error);
    }
  }
  
  async function syncRepos() {
    loading = true;
    try {
      await api.post('/github/repos/sync');
      await loadRepos();
    } catch (error) {
      console.error('Failed to sync repositories:', error);
    } finally {
      loading = false;
    }
  }
</script>

<div class="repo-selector">
  {#if loading}
    <div class="loading">Loading repositories...</div>
  {:else if !isConnected}
    <div class="connect-github">
      <div class="connect-content">
        <h3>Connect GitHub Account</h3>
        <p>Connect your GitHub account to analyze your repositories with AI.</p>
        <button class="connect-btn" onclick={connectGitHub}>
          🔗 Connect GitHub
        </button>
      </div>
    </div>
  {:else if repos.length === 0}
    <div class="no-repos">
      <p>No repositories found.</p>
      <button class="sync-btn" onclick={syncRepos}>
        🔄 Sync Repositories
      </button>
    </div>
  {:else}
    <div class="repo-selection">
      <div class="repo-header">
        <h3>Select Repository</h3>
        <button class="sync-btn" onclick={syncRepos}>
          🔄 Sync
        </button>
      </div>
      
      <div class="repo-list">
        {#each repos as repo}
          <div 
            class="repo-item"
            class:selected={selected?.id === repo.id}
            onclick={() => selected = repo}
          >
            <div class="repo-info">
              <h4>{repo.name}</h4>
              {#if repo.description}
                <p>{repo.description}</p>
              {/if}
            </div>
            
            <div class="repo-meta">
              <span class="language">{repo.language || 'Unknown'}</span>
              <span class="stars">⭐ {repo.stars || 0}</span>
              <span class="visibility">{repo.private ? '🔒' : '🌐'}</span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .repo-selector {
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--surface-2);
    padding: 1.5rem;
  }
  
  .loading {
    text-align: center;
    padding: 2rem;
    color: var(--text-secondary);
  }
  
  .connect-github {
    text-align: center;
    padding: 2rem;
  }
  
  .connect-content h3 {
    margin-bottom: 0.5rem;
    color: var(--text-primary);
  }
  
  .connect-content p {
    margin-bottom: 1.5rem;
    color: var(--text-secondary);
  }
  
  .connect-btn {
    padding: 0.75rem 1.5rem;
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .connect-btn:hover {
    opacity: 0.9;
  }
  
  .no-repos {
    text-align: center;
    padding: 2rem;
  }
  
  .no-repos p {
    margin-bottom: 1rem;
    color: var(--text-secondary);
  }
  
  .sync-btn {
    padding: 0.5rem 1rem;
    background: var(--surface-3);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .sync-btn:hover {
    background: var(--surface-4);
  }
  
  .repo-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .repo-header h3 {
    margin: 0;
    color: var(--text-primary);
  }
  
  .repo-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 300px;
    overflow-y: auto;
  }
  
  .repo-item {
    padding: 1rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--surface-3);
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .repo-item:hover {
    border-color: var(--primary);
    background: var(--surface-4);
  }
  
  .repo-item.selected {
    border-color: var(--primary);
    background: rgba(59, 130, 246, 0.1);
  }
  
  .repo-info h4 {
    margin: 0 0 0.25rem 0;
    color: var(--text-primary);
    font-size: 1rem;
  }
  
  .repo-info p {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
    line-height: 1.4;
  }
  
  .repo-meta {
    display: flex;
    gap: 1rem;
    margin-top: 0.75rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }
  
  .language {
    padding: 0.25rem 0.5rem;
    background: var(--surface-4);
    border-radius: 12px;
  }
  
  .stars, .visibility {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
</style>