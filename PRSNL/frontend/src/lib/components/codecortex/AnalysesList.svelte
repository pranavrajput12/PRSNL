<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';

  interface Props {
    limit?: number;
    repoId?: string;
    showViewAll?: boolean;
  }

  let { limit = 10, repoId = null, showViewAll = true }: Props = $props();

  let analyses = $state([]);
  let loading = $state(true);

  onMount(async () => {
    await loadAnalyses();
  });

  async function loadAnalyses() {
    loading = true;
    try {
      let url = `/codemirror/analyses?limit=${limit}`;
      if (repoId) {
        url = `/codemirror/analyses/${repoId}?limit=${limit}`;
      }

      const data = await api.get(url);
      analyses = data || [];
    } catch (error) {
      console.error('Failed to load analyses:', error);
      analyses = [];
    } finally {
      loading = false;
    }
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'completed':
        return '✅';
      case 'processing':
        return '🔄';
      case 'failed':
        return '❌';
      case 'pending':
        return '⏳';
      default:
        return '❓';
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'completed':
        return 'var(--success, #10b981)';
      case 'processing':
        return 'var(--warning, #f59e0b)';
      case 'failed':
        return 'var(--error, #ef4444)';
      case 'pending':
        return 'var(--info, #3b82f6)';
      default:
        return 'var(--text-secondary)';
    }
  }

  function formatDate(date: string) {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function getProgressColor(progress: number) {
    if (progress >= 80) return '#10b981';
    if (progress >= 50) return '#f59e0b';
    return '#3b82f6';
  }
</script>

<div class="analyses-list">
  <div class="list-header">
    <h3>Recent Analyses</h3>
    {#if showViewAll}
      <a href="/code-cortex/codemirror?tab=analysis" class="view-all-link"> View All → </a>
    {/if}
  </div>

  {#if loading}
    <div class="loading-state">
      <div class="skeleton-card"></div>
      <div class="skeleton-card"></div>
      <div class="skeleton-card"></div>
    </div>
  {:else if analyses.length === 0}
    <div class="empty-state">
      <p>No analyses found</p>
      <a href="/code-cortex/codemirror" class="start-link"> Start your first analysis → </a>
    </div>
  {:else}
    <div class="analyses-grid">
      {#each analyses as analysis}
        <a href="/code-cortex/codemirror/analysis/{analysis.id}" class="analysis-item">
          <div class="analysis-header">
            <div class="repo-info">
              <h4>
                {analysis.repository_name ||
                  analysis.repo_full_name ||
                  analysis.repo_name ||
                  'Unknown Repository'}
              </h4>
              <span class="analysis-date">{formatDate(analysis.created_at)}</span>
            </div>
            <span class="status-badge" style="color: {getStatusColor(analysis.status)}">
              {getStatusIcon(analysis.status)}
              {analysis.status}
            </span>
          </div>

          {#if analysis.status === 'processing'}
            {@const progress =
              analysis.progress_percentage || analysis.progress || analysis.job_progress || 0}
            {#if progress > 0}
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  style="width: {progress}%; background: {getProgressColor(progress)}"
                ></div>
              </div>
            {/if}
          {/if}

          <div class="analysis-stats">
            {#if analysis.patterns_found !== null}
              <div class="stat">
                <span class="stat-icon">🔍</span>
                <span class="stat-value">{analysis.patterns_found}</span>
                <span class="stat-label">patterns</span>
              </div>
            {/if}
            {#if analysis.insights_generated !== null}
              <div class="stat">
                <span class="stat-icon">💡</span>
                <span class="stat-value">{analysis.insights_generated}</span>
                <span class="stat-label">insights</span>
              </div>
            {/if}
            {#if analysis.quality_score !== null}
              <div class="stat">
                <span class="stat-icon">⭐</span>
                <span class="stat-value">{analysis.quality_score}/100</span>
                <span class="stat-label">quality</span>
              </div>
            {/if}
          </div>

          {#if analysis.analysis_depth}
            <div class="analysis-meta">
              <span class="depth-badge">{analysis.analysis_depth} analysis</span>
            </div>
          {/if}
        </a>
      {/each}
    </div>
  {/if}
</div>

<style>
  .analyses-list {
    background: var(--surface-2, #1a1a2e);
    border: 1px solid var(--border, rgba(255, 255, 255, 0.1));
    border-radius: 12px;
    padding: 1.5rem;
  }

  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .list-header h3 {
    margin: 0;
    font-size: 1.25rem;
    color: var(--text-primary, white);
  }

  .view-all-link,
  .start-link {
    color: var(--primary, #3b82f6);
    text-decoration: none;
    font-size: 0.875rem;
    transition: opacity 0.2s;
  }

  .view-all-link:hover,
  .start-link:hover {
    opacity: 0.8;
  }

  /* Loading State */
  .loading-state {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .skeleton-card {
    height: 120px;
    background: var(--surface-3, #16213e);
    border-radius: 8px;
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  }

  .empty-state p {
    margin: 0 0 1rem 0;
  }

  /* Analyses Grid */
  .analyses-grid {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .analysis-item {
    display: block;
    background: var(--surface-3, #16213e);
    border: 1px solid var(--border, rgba(255, 255, 255, 0.1));
    border-radius: 8px;
    padding: 1.25rem;
    text-decoration: none;
    transition: all 0.2s;
  }

  .analysis-item:hover {
    background: var(--surface-4, #0f3460);
    border-color: var(--primary-alpha, rgba(59, 130, 246, 0.3));
    transform: translateY(-1px);
  }

  .analysis-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .repo-info h4 {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary, white);
  }

  .analysis-date {
    font-size: 0.75rem;
    color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  }

  .status-badge {
    font-size: 0.875rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  /* Progress Bar */
  .progress-bar {
    height: 4px;
    background: var(--surface-2, #1a1a2e);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 1rem;
  }

  .progress-fill {
    height: 100%;
    transition: width 0.3s ease;
  }

  /* Stats */
  .analysis-stats {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 0.75rem;
  }

  .stat {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.875rem;
  }

  .stat-icon {
    font-size: 1rem;
  }

  .stat-value {
    font-weight: 600;
    color: var(--text-primary, white);
  }

  .stat-label {
    color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  }

  /* Meta */
  .analysis-meta {
    display: flex;
    gap: 0.5rem;
  }

  .depth-badge {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    background: var(--primary-alpha, rgba(59, 130, 246, 0.1));
    color: var(--primary, #3b82f6);
    border-radius: 4px;
    text-transform: capitalize;
  }
</style>
