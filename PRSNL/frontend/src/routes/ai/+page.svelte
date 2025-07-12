<script lang="ts">
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import { aiApi } from '$lib/api';
  import CategoryManager from '$lib/components/CategoryManager.svelte';
  import DuplicateChecker from '$lib/components/DuplicateChecker.svelte';
  import SummaryViews from '$lib/components/SummaryViews.svelte';

  let activeTab = 'categories';
  let isLoading = true;
  let error: Error | null = null;

  // Dashboard data
  let categoryStats: {
    category: string;
    count: number;
    confidence: number;
  }[] = [];
  let duplicateGroups: {
    id: string;
    items: any[];
    similarity: number;
  }[] = [];

  // Digest data
  let digestSummaries = {
    brief: '',
    detailed: '',
    key_points: '',
  };
  let isGeneratingDigest = false;
  let digestGenerationError: Error | null = null;

  let topicClusters: {
    topic: string;
    itemCount: number;
    keywords: string[];
  }[] = [];

  onMount(async () => {
    try {
      await loadDashboardData();
    } catch (e) {
      error = e as Error;
    } finally {
      isLoading = false;
    }
  });

  async function loadDashboardData() {
    try {
      isLoading = true;
      error = null;
      digestGenerationError = null;

      // Parallel requests to load different sections of the dashboard
      const [categoriesData, duplicatesData, digestBriefData, clustersData] = await Promise.all([
        aiApi.categorize.stats().catch(() => ({ categories: [] })),
        aiApi.duplicates.findAll().catch(() => ({ groups: [] })),
        aiApi.summarization.digest('brief').catch(() => ({ summary: '' })),
        aiApi.insights.topicClusters().catch(() => ({ clusters: [] })),
      ]);

      categoryStats = categoriesData.categories || [];
      duplicateGroups = duplicatesData.groups || [];
      digestSummaries.brief = digestBriefData.summary || '';
      topicClusters = clustersData.clusters || [];

      // If we have a brief digest, also try to load key points in the background
      if (digestSummaries.brief) {
        loadDigestKeyPoints();
      }
    } catch (e) {
      console.error('Failed to load AI dashboard data:', e);
      error = e as Error;
    } finally {
      isLoading = false;
    }
  }

  async function loadDigestKeyPoints() {
    try {
      const keyPointsData = await aiApi.summarization.digest('key_points');
      if (keyPointsData && keyPointsData.summary) {
        digestSummaries.key_points = keyPointsData.summary;
      }
    } catch (e) {
      console.error('Failed to load digest key points:', e);
      // Don't set the main error state - this is a background operation
    }
  }

  async function generateDigest(type: 'brief' | 'detailed' | 'key_points' = 'brief') {
    if (isGeneratingDigest) return;

    try {
      isGeneratingDigest = true;
      digestGenerationError = null;

      const result = await aiApi.summarization.digest(type);

      if (result && typeof result === 'object' && 'summary' in result) {
        digestSummaries[type] = result.summary || '';

        // If generating brief summary for the first time, also get key points
        if (type === 'brief' && !digestSummaries.key_points) {
          loadDigestKeyPoints();
        }
      }
    } catch (e) {
      console.error(`Failed to generate ${type} digest:`, e);
      digestGenerationError = e as Error;
    } finally {
      isGeneratingDigest = false;
    }
  }

  function setActiveTab(tab: string) {
    activeTab = tab;
  }

  function getTotalItemsWithDuplicates() {
    return duplicateGroups.reduce((total, group) => total + group.items.length, 0);
  }
</script>

<svelte:head>
  <title>AI Dashboard | PRSNL</title>
</svelte:head>

<div class="ai-dashboard">
  <header>
    <h1>AI Dashboard</h1>
    <p class="subtitle">AI-powered insights and management tools for your knowledge base</p>
  </header>

  <nav class="tabs">
    <button
      class="tab"
      class:active={activeTab === 'categories'}
      on:click={() => setActiveTab('categories')}
    >
      <Icon name="tag" size="small" />
      <span>Categories</span>
    </button>
    <button
      class="tab"
      class:active={activeTab === 'duplicates'}
      on:click={() => setActiveTab('duplicates')}
    >
      <Icon name="copy" size="small" />
      <span>Duplicates</span>
      {#if duplicateGroups.length > 0}
        <span class="badge">{duplicateGroups.length}</span>
      {/if}
    </button>
    <button
      class="tab"
      class:active={activeTab === 'digest'}
      on:click={() => setActiveTab('digest')}
    >
      <Icon name="file-text" size="small" />
      <span>Digest</span>
    </button>
    <button
      class="tab"
      class:active={activeTab === 'topics'}
      on:click={() => setActiveTab('topics')}
    >
      <Icon name="layers" size="small" />
      <span>Topic Clusters</span>
    </button>
  </nav>

  {#if isLoading}
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Loading AI insights...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <Icon name="alert-circle" size="large" color="var(--error)" />
      <h3>Failed to load AI dashboard</h3>
      <p>{error.message}</p>
      <button class="retry-btn" on:click={loadDashboardData}>
        <Icon name="refresh-cw" size="small" />
        <span>Try Again</span>
      </button>
    </div>
  {:else}
    <div class="dashboard-content">
      <!-- Categories Tab -->
      {#if activeTab === 'categories'}
        <section class="categories-section">
          <div class="section-header">
            <h2>Category Distribution</h2>
            <p>AI-suggested categories for your content</p>
          </div>

          {#if categoryStats.length === 0}
            <div class="empty-state">
              <Icon name="tag" size="large" color="var(--text-muted)" />
              <p>No categorized items yet</p>
              <p class="help-text">
                Add content to your knowledge base to see AI-generated categories
              </p>
            </div>
          {:else}
            <div class="category-chart">
              {#each categoryStats as stat}
                <div class="category-bar">
                  <div class="category-name">{stat.category}</div>
                  <div class="bar-container">
                    <div
                      class="bar"
                      style="width: {Math.min(
                        100,
                        (stat.count / Math.max(...categoryStats.map((s) => s.count))) * 100
                     )}%; 
                             background-color: {stat.confidence > 0.7
                        ? 'var(--ai-success)'
                        : stat.confidence > 0.4
                          ? 'var(--ai-warning)'
                          : 'var(--ai-error)'};"
                    ></div>
                  </div>
                  <div class="category-count">{stat.count} items</div>
                </div>
              {/each}
            </div>

            <div class="category-actions">
              <h3>Manage Categories</h3>
              <div class="category-manager-container">
                <CategoryManager showBulkActions={true} />
              </div>
            </div>
          {/if}
        </section>
      {/if}

      <!-- Duplicates Tab -->
      {#if activeTab === 'duplicates'}
        <section class="duplicates-section">
          <div class="section-header">
            <h2>Duplicate Content</h2>
            <p>
              {duplicateGroups.length} duplicate groups detected ({getTotalItemsWithDuplicates()} items
              affected)
            </p>
          </div>

          {#if duplicateGroups.length === 0}
            <div class="empty-state">
              <Icon name="check-circle" size="large" color="var(--success)" />
              <p>No duplicate content detected</p>
              <p class="help-text">Your knowledge base is free of duplicates</p>
            </div>
          {:else}
            <div class="duplicate-checker-container">
              <DuplicateChecker showAll={true} />
            </div>
          {/if}
        </section>
      {/if}

      <!-- Digest Tab -->
      {#if activeTab === 'digest'}
        <section class="digest-section">
          <div class="section-header">
            <h2>Content Digest</h2>
            <p>AI-generated summary of your recent content with key points</p>
          </div>

          {#if !digestSummaries.brief && !isGeneratingDigest}
            <div class="empty-state">
              <Icon name="file-text" size="large" color="var(--text-muted)" />
              <p>No digest available</p>
              <p class="help-text">Generate a digest to summarize your content</p>
              <button class="generate-btn" on:click={() => generateDigest('brief')}>
                <Icon name="refresh-cw" size="small" />
                <span>Generate Digest</span>
              </button>
            </div>
          {:else}
            <div class="digest-content">
              {#if isGeneratingDigest && !digestSummaries.brief}
                <div class="loading-container">
                  <div class="spinner"></div>
                  <p>Generating content digest...</p>
                </div>
              {:else if digestGenerationError && !digestSummaries.brief}
                <div class="error-state">
                  <Icon name="alert-circle" size="large" color="var(--error)" />
                  <h3>Failed to generate digest</h3>
                  <p>{digestGenerationError.message}</p>
                  <button class="retry-btn" on:click={() => generateDigest('brief')}>
                    <Icon name="refresh-cw" size="small" />
                    <span>Try Again</span>
                  </button>
                </div>
              {:else}
                <SummaryViews
                  summaries={digestSummaries}
                  showDetailedTab={false}
                  showKeyPointsTab={true}
                  initialTab="brief"
                  fullWidth={true}
                />

                <div class="digest-actions">
                  {#if isGeneratingDigest}
                    <button class="action-btn" disabled>
                      <div class="action-spinner"></div>
                      <span>Regenerating...</span>
                    </button>
                  {:else}
                    <button class="action-btn" on:click={() => generateDigest('brief')}>
                      <Icon name="refresh-cw" size="small" />
                      <span>Regenerate</span>
                    </button>

                    {#if !digestSummaries.key_points}
                      <button class="action-btn" on:click={() => generateDigest('key_points')}>
                        <Icon name="list" size="small" />
                        <span>Generate Key Points</span>
                      </button>
                    {/if}
                  {/if}
                </div>
              {/if}
            </div>
          {/if}
        </section>
      {/if}

      <!-- Topic Clusters Tab -->
      {#if activeTab === 'topics'}
        <section class="topics-section">
          <div class="section-header">
            <h2>Topic Clusters</h2>
            <p>AI-detected topic groups from your content</p>
          </div>

          {#if topicClusters.length === 0}
            <div class="empty-state">
              <Icon name="layers" size="large" color="var(--text-muted)" />
              <p>No topic clusters available</p>
              <p class="help-text">Add more content to see topic clusters emerge</p>
            </div>
          {:else}
            <div class="topic-clusters">
              {#each topicClusters as cluster}
                <div class="topic-card">
                  <h3>{cluster.topic}</h3>
                  <div class="item-count">{cluster.itemCount} items</div>
                  <div class="keywords">
                    {#each cluster.keywords as keyword}
                      <span class="keyword">{keyword}</span>
                    {/each}
                  </div>
                  <a
                    href={`/search?q=${encodeURIComponent(cluster.topic)}&mode=semantic`}
                    class="view-link"
                  >
                    <Icon name="search" size="small" />
                    <span>View items</span>
                  </a>
                </div>
              {/each}
            </div>
          {/if}
        </section>
      {/if}
    </div>
  {/if}
</div>

<style>
  .ai-dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }

  header {
    margin-bottom: 2rem;
    text-align: center;
  }

  h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    background: linear-gradient(90deg, var(--accent), #4f46e5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: inline-block;
  }

  .subtitle {
    color: var(--text-secondary);
    font-size: 1.125rem;
  }

  .tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    overflow-x: auto;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: none;
    border: none;
    border-radius: var(--radius);
    color: var(--text-secondary);
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s ease;
  }

  .tab:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .tab.active {
    background: var(--ai-accent-light, rgba(79, 70, 229, 0.1));
    color: var(--ai-accent, #4f46e5);
  }

  .badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 10px;
    background: var(--ai-accent, #4f46e5);
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
  }

  .loading-state,
  .error-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-left-color: var(--ai-accent, #4f46e5);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .error-state h3 {
    color: var(--error);
    margin: 1rem 0 0.5rem;
  }

  .retry-btn,
  .generate-btn,
  .action-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-secondary);
    font-weight: 600;
    cursor: pointer;
    margin-top: 1.5rem;
    transition: all 0.2s ease;
  }

  .retry-btn:hover,
  .generate-btn:hover,
  .action-btn:hover {
    background: var(--ai-accent-light, rgba(79, 70, 229, 0.1));
    border-color: var(--ai-accent, #4f46e5);
    color: var(--ai-accent, #4f46e5);
  }

  .section-header {
    margin-bottom: 2rem;
  }

  .section-header h2 {
    font-size: 1.75rem;
    margin-bottom: 0.5rem;
  }

  .section-header p {
    color: var(--text-secondary);
  }

  .empty-state {
    background: var(--bg-tertiary);
    border-radius: var(--radius);
    padding: 4rem 2rem;
  }

  .empty-state :global(svg) {
    margin-bottom: 1.5rem;
    opacity: 0.5;
  }

  .empty-state p {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
  }

  .empty-state .help-text {
    font-size: 1rem;
    font-weight: 400;
    color: var(--text-secondary);
    margin-top: 0.5rem;
  }

  /* Category section styles */
  .category-chart {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .category-bar {
    display: grid;
    grid-template-columns: 150px 1fr 80px;
    align-items: center;
    gap: 1rem;
  }

  .category-name {
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .bar-container {
    height: 12px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    overflow: hidden;
  }

  .bar {
    height: 100%;
    border-radius: 6px;
    transition: width 0.5s ease;
  }

  .category-count {
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-align: right;
  }

  .category-actions {
    margin-top: 3rem;
  }

  .category-manager-container,
  .duplicate-checker-container {
    margin-top: 1.5rem;
    padding: 1.5rem;
    background: var(--bg-secondary);
    border-radius: var(--radius);
    border: 1px solid var(--border);
  }

  /* Topic clusters styles */
  .topic-clusters {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .topic-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    transition: all 0.2s ease;
  }

  .topic-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-color: var(--ai-accent, #4f46e5);
  }

  .topic-card h3 {
    margin: 0 0 0.5rem;
    font-size: 1.25rem;
  }

  .item-count {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 1rem;
  }

  .keywords {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }

  .keyword {
    padding: 0.25rem 0.625rem;
    background: var(--bg-tertiary);
    border-radius: 100px;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .view-link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--ai-accent, #4f46e5);
    font-size: 0.875rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
  }

  .view-link:hover {
    transform: translateX(2px);
  }

  /* Digest section */
  .digest-section .loading-container,
  .digest-section .error-state {
    min-height: 300px;
  }

  .action-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid var(--border-color);
    border-top: 2px solid var(--ai-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-right: 0.5rem;
  }

  /* Digest actions */
  .digest-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .digest-content {
    background-color: var(--bg-secondary);
    border-radius: var(--radius);
    padding: 1.5rem;
    border: 1px solid var(--border);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .ai-dashboard {
      padding: 1rem;
    }

    h1 {
      font-size: 2rem;
    }

    .category-bar {
      grid-template-columns: 100px 1fr 70px;
      gap: 0.75rem;
    }

    .topic-clusters {
      grid-template-columns: 1fr;
    }
  }
</style>
