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
      isConnected = connectionResponse && connectionResponse.length > 0;

      if (isConnected) {
        // Load repositories
        const reposResponse = await api.get('/github/repos');
        repos = reposResponse || [];
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
      if (response.auth_url) {
        window.location.href = response.auth_url;
      }
    } catch (error) {
      console.error('Failed to connect to GitHub:', error);
    }
  }

  async function syncRepos() {
    loading = true;
    try {
      await api.post('/github/repos/sync', { force_refresh: false });
      await loadRepos();
    } catch (error) {
      console.error('Failed to sync repositories:', error);
    } finally {
      loading = false;
    }
  }

  async function disconnectGitHub() {
    if (!confirm('Are you sure you want to disconnect your GitHub account?')) {
      return;
    }

    loading = true;
    try {
      // Get the first account ID
      const accounts = await api.get('/github/accounts');
      if (accounts && accounts.length > 0) {
        await api.delete(`/github/accounts/${accounts[0].id}`);
        isConnected = false;
        repos = [];
        selected = null;
      }
    } catch (error) {
      console.error('Failed to disconnect GitHub:', error);
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
        <button class="connect-btn github-style" onclick={connectGitHub}>
          <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor" class="github-logo">
            <path
              d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
            />
          </svg>
          Connect GitHub
        </button>
      </div>
    </div>
  {:else if repos.length === 0}
    <div class="no-repos">
      <p>No repositories found.</p>
      <div class="no-repos-actions">
        <button class="sync-btn" onclick={syncRepos}> 🔄 Sync Repositories </button>
        <button class="disconnect-btn" onclick={disconnectGitHub}> 🔌 Disconnect GitHub </button>
      </div>
    </div>
  {:else}
    <div class="repo-selection">
      <div class="repo-header">
        <h3>Select Repository</h3>
        <div class="header-actions">
          <button class="sync-btn" onclick={syncRepos}> 🔄 Sync </button>
          <button class="disconnect-btn" onclick={disconnectGitHub}> 🔌 Disconnect </button>
        </div>
      </div>

      <div class="repo-list">
        {#each repos as repo}
          <div class="repo-item" class:selected={selected?.id === repo.id}>
            <div class="repo-content" onclick={() => (selected = repo)}>
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

            <div class="repo-actions">
              <a
                href="/code-cortex/codemirror/repo/{repo.id}"
                class="view-analyses-btn"
                title="View Analysis History"
              >
                📊 View Analyses
              </a>
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

  /* GitHub Style Button */
  .connect-btn.github-style {
    background: #24292e;
    color: white;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    transition: all 0.2s;
    box-shadow:
      0 1px 0 rgba(27, 31, 35, 0.04),
      inset 0 1px 0 rgba(255, 255, 255, 0.03);
  }

  .connect-btn.github-style:hover {
    background: #2c313a;
    opacity: 1;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .github-logo {
    width: 20px;
    height: 20px;
  }

  .no-repos {
    text-align: center;
    padding: 2rem;
  }

  .no-repos p {
    margin-bottom: 1rem;
    color: var(--text-secondary);
  }

  .no-repos-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: center;
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

  .disconnect-btn {
    padding: 0.5rem 1rem;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 6px;
    color: #ef4444;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.875rem;
  }

  .disconnect-btn:hover {
    background: rgba(239, 68, 68, 0.2);
    border-color: rgba(239, 68, 68, 0.5);
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

  .header-actions {
    display: flex;
    gap: 0.5rem;
  }

  .repo-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 300px;
    overflow-y: auto;
  }

  .repo-item {
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--surface-3);
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .repo-item:hover {
    border-color: var(--primary);
    background: var(--surface-4);
  }

  .repo-item.selected {
    border-color: var(--primary);
    background: rgba(59, 130, 246, 0.1);
  }

  .repo-content {
    padding: 1rem;
    cursor: pointer;
    flex: 1;
  }

  .repo-actions {
    padding: 0 1rem 1rem 1rem;
    border-top: 1px solid var(--border);
    background: var(--surface-2);
  }

  .view-analyses-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--primary);
    color: white;
    text-decoration: none;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s;
  }

  .view-analyses-btn:hover {
    background: var(--primary-dark);
    transform: translateY(-1px);
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

  .stars,
  .visibility {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
</style>
