<script lang="ts" type="module">
  import { onMount } from 'svelte';
  import Icon from './Icon.svelte';
  import type { InsightsResponse } from '$lib/types/api';

  export let data: InsightsResponse | null = null;
  export let timeRange: string = 'week';

  let summary: string = '';
  let isLoading: boolean = true;
  let error: Error | null = null;
  let keyMetrics: { label: string; value: number | string; icon: string; trend: number | null }[] =
    [];

  $: if (data) {
    calculateKeyMetrics(data);
    generateSummary(data);
  }

  function calculateKeyMetrics(data: InsightsResponse) {
    isLoading = true;
    error = null;

    try {
      // Total items count
      const totalItems =
        data.contentTrends && data.contentTrends.length > 0
          ? data.contentTrends[data.contentTrends.length - 1].articles +
            data.contentTrends[data.contentTrends.length - 1].videos +
            data.contentTrends[data.contentTrends.length - 1].notes +
            data.contentTrends[data.contentTrends.length - 1].bookmarks
          : 0;

      // Growth calculation
      let growth = 0;
      if (data.contentTrends && data.contentTrends.length > 1) {
        const current = data.contentTrends[data.contentTrends.length - 1];
        const previous = data.contentTrends[data.contentTrends.length - 2];

        const currentTotal = current.articles + current.videos + current.notes + current.bookmarks;
        const previousTotal =
          previous.articles + previous.videos + previous.notes + previous.bookmarks;

        growth = previousTotal > 0 ? ((currentTotal - previousTotal) / previousTotal) * 100 : 0;
      }

      // Top topic size
      const topTopicSize =
        data.topicClusters && data.topicClusters.length > 0
          ? Math.max(...data.topicClusters.map((c) => c.count))
          : 0;

      // Connection density
      const connectionDensity =
        data.knowledgeGraph?.links && data.knowledgeGraph?.nodes
          ? data.knowledgeGraph.links.length / Math.max(1, data.knowledgeGraph.nodes.length)
          : 0;

      // Top content score
      const topContentScore =
        data.topContent && data.topContent.length > 0
          ? Math.max(
              ...data.topContent.map((item) => (item.metadata?.ai_analysis?.score || 0) * 100)
            )
          : 0;

      keyMetrics = [
        {
          label: 'Total Items',
          value: totalItems,
          icon: 'database',
          trend: growth,
        },
        {
          label: 'Topics',
          value: data.topicClusters?.length || 0,
          icon: 'pie-chart',
          trend: null,
        },
        {
          label: 'Largest Topic',
          value: `${topTopicSize} items`,
          icon: 'target',
          trend: null,
        },
        {
          label: 'Connections',
          value: connectionDensity.toFixed(2),
          icon: 'git-branch',
          trend: null,
        },
        {
          label: 'Top Content Score',
          value: `${Math.round(topContentScore)}%`,
          icon: 'award',
          trend: null,
        },
      ];
    } catch (e) {
      error = e as Error;
      console.error('Error calculating metrics:', e);
    } finally {
      isLoading = false;
    }
  }

  function generateSummary(data: InsightsResponse) {
    try {
      // Generate a summary based on the data
      const topCluster =
        data.topicClusters && data.topicClusters.length > 0
          ? data.topicClusters.reduce((prev, current) =>
              prev.count > current.count ? prev : current
            )
          : null;

      const contentTrend =
        data.contentTrends && data.contentTrends.length > 1
          ? data.contentTrends[data.contentTrends.length - 1].articles +
            data.contentTrends[data.contentTrends.length - 1].videos +
            data.contentTrends[data.contentTrends.length - 1].notes +
            data.contentTrends[data.contentTrends.length - 1].bookmarks -
            (data.contentTrends[data.contentTrends.length - 2].articles +
              data.contentTrends[data.contentTrends.length - 2].videos +
              data.contentTrends[data.contentTrends.length - 2].notes +
              data.contentTrends[data.contentTrends.length - 2].bookmarks)
          : 0;

      const trendDirection =
        contentTrend > 0 ? 'growing' : contentTrend < 0 ? 'shrinking' : 'stable';

      const topContentTitle =
        data.topContent && data.topContent.length > 0 ? data.topContent[0].title : '';

      const timeRangeText = {
        day: 'today',
        week: 'this week',
        month: 'this month',
        year: 'this year',
        all: 'overall',
      }[timeRange];

      summary = `Your knowledge base is ${trendDirection} ${timeRangeText}. `;

      if (topCluster) {
        summary += `Your largest topic cluster is "${topCluster.name}" with ${topCluster.count} items. `;
      }

      if (topContentTitle) {
        summary += `Your highest value content is "${topContentTitle}". `;
      }

      if (data.knowledgeGraph?.nodes && data.knowledgeGraph.nodes.length > 0) {
        summary += `Your knowledge graph has ${data.knowledgeGraph.nodes.length} nodes with ${data.knowledgeGraph.links?.length || 0} connections.`;
      }
    } catch (e) {
      console.error('Error generating summary:', e);
      summary = 'Summary generation failed. Please try again later.';
    }
  }
</script>

<div class="insights-summary">
  {#if isLoading}
    <div class="loading">
      <span class="loader"></span>
      <p>Analyzing your knowledge base...</p>
    </div>
  {:else if error}
    <div class="error">
      <Icon name="alert-circle" />
      <p>Failed to generate insights summary: {error.message}</p>
    </div>
  {:else}
    <div class="summary-text">
      <h3>AI Summary</h3>
      <p>{summary}</p>
    </div>

    <div class="metrics-grid">
      {#each keyMetrics as metric}
        <div class="metric-card">
          <div class="metric-icon">
            <Icon name={metric.icon} />
          </div>
          <div class="metric-content">
            <h4>{metric.label}</h4>
            <div class="metric-value">
              <span>{metric.value}</span>
              {#if metric.trend !== null}
                <span
                  class="trend"
                  class:positive={metric.trend > 0}
                  class:negative={metric.trend < 0}
                >
                  <Icon
                    name={metric.trend > 0
                      ? 'trending-up'
                      : metric.trend < 0
                        ? 'trending-down'
                        : 'minus'}
                  />
                  {Math.abs(metric.trend).toFixed(1)}%
                </span>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .insights-summary {
    background-color: var(--bg-secondary);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .summary-text {
    margin-bottom: 1.5rem;
  }

  .summary-text h3 {
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
  }

  .summary-text p {
    font-size: 1rem;
    line-height: 1.5;
    color: var(--text-secondary);
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
  }

  .metric-card {
    background-color: var(--bg-tertiary);
    border-radius: var(--border-radius);
    padding: 1rem;
    display: flex;
    align-items: center;
  }

  .metric-icon {
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background-color: var(--accent-light);
    margin-right: 0.75rem;
    color: var(--accent);
  }

  .metric-content h4 {
    font-size: 0.875rem;
    margin: 0 0 0.25rem 0;
    color: var(--text-secondary);
    font-weight: 400;
  }

  .metric-value {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
    display: flex;
    align-items: center;
  }

  .trend {
    display: inline-flex;
    align-items: center;
    font-size: 0.75rem;
    margin-left: 0.5rem;
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
  }

  .trend.positive {
    background-color: var(--success-light);
    color: var(--success);
  }

  .trend.negative {
    background-color: var(--error-light);
    color: var(--error);
  }

  .loading,
  .error {
    text-align: center;
    padding: 2rem;
  }

  .loader {
    width: 2rem;
    height: 2rem;
    border: 3px solid var(--accent-light);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    display: inline-block;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
