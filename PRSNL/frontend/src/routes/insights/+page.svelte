<script lang="ts">
  import { onMount } from 'svelte';
  import { getInsights } from '$lib/api';
  import type { InsightsResponse } from '$lib/types/api';
  import Icon from '$lib/components/Icon.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import TopicClusters from '$lib/components/TopicClusters.svelte';
  import ContentTrends from '$lib/components/ContentTrends.svelte';
  import KnowledgeGraph from '$lib/components/KnowledgeGraph.svelte';
  import AsyncBoundary from '$lib/components/AsyncBoundary.svelte';
  
  // State
  let isLoading = true;
  let error: Error | null = null;
  let timeRange = 'week';
  let selectedCluster: string | null = null;
  let insightsData: InsightsResponse | null = null;
  
  // Reactive statements
  $: timeRangeLabel = {
    'day': 'Today',
    'week': 'This Week',
    'month': 'This Month',
    'year': 'This Year',
    'all': 'All Time'
  }[timeRange];
  
  onMount(async () => {
    try {
      await loadInsightsData();
    } catch (e) {
      error = e as Error;
    } finally {
      isLoading = false;
    }
  });
  
  async function loadInsightsData() {
    try {
      isLoading = true;
      error = null;
      insightsData = await getInsights(timeRange);
    } catch (e) {
      console.error('Failed to load insights data:', e);
      error = e as Error;
    } finally {
      isLoading = false;
    }
  }
  
  function handleTimeRangeChange(newRange: string) {
    timeRange = newRange;
    loadInsightsData();
  }
  
  function handleClusterSelect(event: CustomEvent) {
    selectedCluster = event.detail.cluster;
  }
</script>

<svelte:head>
  <title>AI Insights | PRSNL</title>
</svelte:head>

<div class="insights-page">
  <header class="insights-header">
    <h1>
      <Icon name="brain" />
      AI Insights
    </h1>
    
    <div class="time-range-selector">
      <span class="label">Showing data for:</span>
      <div class="dropdown">
        <button class="dropdown-toggle">
          {timeRangeLabel}
          <Icon name="chevron-down" size="small" />
        </button>
        <div class="dropdown-menu">
          <button 
            class:active={timeRange === 'day'} 
            on:click={() => handleTimeRangeChange('day')}
          >
            Today
          </button>
          <button 
            class:active={timeRange === 'week'} 
            on:click={() => handleTimeRangeChange('week')}
          >
            This Week
          </button>
          <button 
            class:active={timeRange === 'month'} 
            on:click={() => handleTimeRangeChange('month')}
          >
            This Month
          </button>
          <button 
            class:active={timeRange === 'year'} 
            on:click={() => handleTimeRangeChange('year')}
          >
            This Year
          </button>
          <button 
            class:active={timeRange === 'all'} 
            on:click={() => handleTimeRangeChange('all')}
          >
            All Time
          </button>
        </div>
      </div>
    </div>
  </header>
  
  <AsyncBoundary loading={isLoading} {error} loadingMessage="Loading insights...">
    {#if insightsData}
      <div class="insights-grid">
        <div class="insight-card">
          <div class="card-header">
            <h2>
              <Icon name="pie-chart" />
              Topic Clusters
            </h2>
            <p class="description">
              Discover how your knowledge is organized into related topics
            </p>
          </div>
          <div class="card-content">
            <TopicClusters 
              data={insightsData.topicClusters} 
              on:clusterSelect={handleClusterSelect} 
            />
          </div>
        </div>
        
        <div class="insight-card">
          <div class="card-header">
            <h2>
              <Icon name="trending-up" />
              Content Trends
            </h2>
            <p class="description">
              Track how your knowledge collection has grown over time
            </p>
          </div>
          <div class="card-content">
            <ContentTrends 
              data={insightsData?.contentTrends?.map(point => ({
                date: new Date(point.date),
                value: point.articles + point.videos + point.notes + point.bookmarks,
                articles: point.articles,
                videos: point.videos,
                notes: point.notes,
                bookmarks: point.bookmarks
              })) || []} 
              {timeRange} 
            />
          </div>
        </div>
        
        <div class="insight-card full-width">
          <div class="card-header">
            <h2>
              <Icon name="git-branch" />
              Knowledge Graph
            </h2>
            <p class="description">
              Explore connections between topics and content in your knowledge base
            </p>
          </div>
          <div class="card-content graph-container">
            <KnowledgeGraph 
              data={insightsData?.knowledgeGraph || { nodes: [], links: [] }} 
              {selectedCluster} 
            />
          </div>
        </div>
        
        <div class="insight-card">
          <div class="card-header">
            <h2>
              <Icon name="star" />
              Top Content
            </h2>
            <p class="description">
              Your most valuable knowledge items based on AI analysis
            </p>
          </div>
          <div class="card-content">
            {#if insightsData.topContent && insightsData.topContent.length > 0}
              <ul class="top-content-list">
                {#each insightsData.topContent as item}
                  <li>
                    <a href="/item/{item.id}" class="top-content-item">
                      <div class="item-icon">
                        <Icon name={item.item_type === 'video' ? 'play-circle' : 'file-text'} />
                      </div>
                      <div class="item-details">
                        <h3>{item.title}</h3>
                        <div class="item-meta">
                          <span class="item-type">{item.item_type}</span>
                          <span class="item-date">{new Date(item.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div class="item-score">
                        <div class="score-indicator" style="--score: {(item.metadata?.ai_analysis?.score || 0) * 100}%"></div>
                        <span>{Math.round((item.metadata?.ai_analysis?.score || 0) * 100)}%</span>
                      </div>
                    </a>
                  </li>
                {/each}
              </ul>
            {:else}
              <div class="empty-state">
                <Icon name="info" />
                <p>No top content available for this time period</p>
              </div>
            {/if}
          </div>
        </div>
        
        <div class="insight-card">
          <div class="card-header">
            <h2>
              <Icon name="tag" />
              Tag Analysis
            </h2>
            <p class="description">
              Distribution and relationships between your content tags
            </p>
          </div>
          <div class="card-content">
            {#if insightsData.tagAnalysis && insightsData.tagAnalysis.length > 0}
              <div class="tag-cloud">
                {#each insightsData.tagAnalysis as tag}
                  <span 
                    class="tag" 
                    style="--size: {tag.weight}; --hue: {tag.hue};"
                  >
                    {tag.name}
                  </span>
                {/each}
              </div>
            {:else}
              <div class="empty-state">
                <Icon name="info" />
                <p>No tag data available for this time period</p>
              </div>
            {/if}
          </div>
        </div>
      </div>
    {:else}
      <div class="empty-insights">
        <Icon name="database" size="large" />
        <h2>No insights available</h2>
        <p>Add more content to your knowledge base to generate AI insights</p>
      </div>
    {/if}
  </AsyncBoundary>
</div>

<style>
  .insights-page {
    padding: 2rem;
    min-height: calc(100vh - 60px);
    background: var(--bg-primary);
  }
  
  .insights-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }
  
  h1 {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-family: var(--font-display);
    font-size: 2rem;
    color: var(--text-primary);
  }
  
  .time-range-selector {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .label {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }
  
  .dropdown {
    position: relative;
  }
  
  .dropdown-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    color: var(--text-primary);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .dropdown-toggle:hover {
    background: var(--bg-hover);
  }
  
  .dropdown-menu {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 10;
    min-width: 150px;
    display: none;
  }
  
  .dropdown:hover .dropdown-menu {
    display: block;
  }
  
  .dropdown-menu button {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .dropdown-menu button:hover {
    background: var(--bg-hover);
  }
  
  .dropdown-menu button.active {
    background: var(--accent-transparent);
    color: var(--accent);
    font-weight: 500;
  }
  
  .insights-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
  
  .insight-card {
    background: var(--bg-secondary);
    border-radius: 0.75rem;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
  }
  
  .insight-card.full-width {
    grid-column: 1 / -1;
  }
  
  .card-header {
    padding: 1.25rem;
    border-bottom: 1px solid var(--border);
  }
  
  .card-header h2 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.25rem;
    margin: 0 0 0.5rem 0;
    color: var(--text-primary);
  }
  
  .description {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0;
  }
  
  .card-content {
    padding: 1.5rem;
    flex: 1;
    min-height: 250px;
  }
  
  .graph-container {
    min-height: 400px;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
    text-align: center;
    padding: 2rem;
  }
  
  .empty-state :global(svg) {
    margin-bottom: 1rem;
    opacity: 0.5;
  }
  
  .empty-insights {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 50vh;
    text-align: center;
    color: var(--text-secondary);
  }
  
  .empty-insights :global(svg) {
    font-size: 4rem;
    margin-bottom: 1.5rem;
    opacity: 0.3;
  }
  
  .empty-insights h2 {
    margin: 0 0 0.5rem 0;
    color: var(--text-primary);
  }
  
  .top-content-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .top-content-item {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    border-radius: 0.5rem;
    margin-bottom: 0.5rem;
    text-decoration: none;
    color: var(--text-primary);
    transition: all 0.2s ease;
  }
  
  .top-content-item:hover {
    background: var(--bg-hover);
  }
  
  .item-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 8px;
    background: var(--accent-transparent);
    color: var(--accent);
    margin-right: 1rem;
  }
  
  .item-details {
    flex: 1;
  }
  
  .item-details h3 {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    font-weight: 500;
  }
  
  .item-meta {
    display: flex;
    gap: 0.75rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }
  
  .item-score {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-left: 1rem;
  }
  
  .score-indicator {
    width: 50px;
    height: 4px;
    background: var(--bg-hover);
    border-radius: 2px;
    margin-bottom: 0.25rem;
    position: relative;
    overflow: hidden;
  }
  
  .score-indicator::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: var(--score);
    background: var(--accent);
    border-radius: 2px;
  }
  
  .item-score span {
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--accent);
  }
  
  .tag-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .tag {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    background: hsl(var(--hue), 70%, 40%, 0.1);
    color: hsl(var(--hue), 70%, 45%);
    font-size: calc(0.8rem + var(--size) * 0.5rem);
    font-weight: 500;
  }
  
  @media (max-width: 768px) {
    .insights-page {
      padding: 1rem;
    }
    
    .insights-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }
    
    .insights-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
