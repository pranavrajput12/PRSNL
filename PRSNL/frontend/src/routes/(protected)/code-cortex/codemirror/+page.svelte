<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import OnboardingWizard from '$lib/components/codecortex/OnboardingWizard.svelte';
  import RepoSelector from '$lib/components/codecortex/RepoSelector.svelte';
  import AnalysisTypeSelector from '$lib/components/codecortex/AnalysisTypeSelector.svelte';
  import RealtimeAnalysisProgress from '$lib/components/codecortex/RealtimeAnalysisProgress.svelte';
  import GitHubRepoCardV2 from '$lib/components/GitHubRepoCardV2.svelte';
  import { realtimeService } from '$lib/services/codemirror-realtime';

  // Core State - Jobs Principle: Minimal, Essential State Only
  let showOnboarding = $state(false);
  let selectedRepo = $state(null);
  let isConnected = $state(false);
  let loading = $state(false);
  let activeAnalysis = $state(null);
  let timeline = $state([]);
  let repositories = $state([]);
  let showAnalysisSelector = $state(false);
  let searchQuery = $state('');
  let activeIntelligenceTab = $state('insights');
  let insights = $state([]);
  let criticalIssues = $state([]);
  let analysisHistory = $state([]);
  let activeAnalyses = $state([]); // Track all active analyses

  // Derived State - Smart Filtering
  let filteredRepositories = $derived(
    repositories.filter(
      (repo) =>
        repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (repo.description && repo.description.toLowerCase().includes(searchQuery.toLowerCase()))
    )
  );

  onMount(async () => {
    // Check onboarding need
    const hasSeenOnboarding = localStorage.getItem('codemirror-onboarding-seen');
    if (!hasSeenOnboarding) {
      showOnboarding = true;
    }

    // Load essential data only
    await Promise.all([
      checkGitHubConnection(),
      loadRepositories(),
      loadTimeline(),
      loadActiveAnalyses(),
    ]);
  });

  async function checkGitHubConnection() {
    try {
      const accounts = await api.get('/github/accounts');
      isConnected = accounts && accounts.length > 0;
    } catch (error) {
      isConnected = false;
    }
  }

  async function loadRepositories() {
    try {
      const repos = await api.get('/github/repos');
      repositories = repos || [];
    } catch (error) {
      console.error('Failed to load repositories:', error);
      repositories = [];
    }
  }

  async function loadTimeline() {
    try {
      loading = true;
      const timelineData = await api.get('/codemirror/timeline');
      const allItems = timelineData.timeline || [];

      // Separate data into the 3 sections you asked for
      insights = allItems.filter(
        (item) =>
          item.type === 'insight' && item.severity !== 'critical' && item.severity !== 'high'
      );

      // Include medium severity in critical issues since we don't have high/critical yet
      criticalIssues = allItems.filter(
        (item) =>
          item.type === 'insight' &&
          (item.severity === 'critical' || item.severity === 'high' || item.severity === 'medium')
      );

      analysisHistory = allItems.filter((item) => item.type === 'analysis');
    } catch (error) {
      console.error('Failed to load timeline:', error);
      insights = [];
      criticalIssues = [];
      analysisHistory = [];
    } finally {
      loading = false;
    }
  }

  async function loadActiveAnalyses() {
    // DON'T load old analyses - only track the one we just started
    activeAnalyses = [];
  }

  async function syncRepositories() {
    try {
      loading = true;
      await api.post('/github/repos/sync', { force_refresh: true });
      await loadRepositories();
    } catch (error) {
      console.error('Failed to sync repositories:', error);
    } finally {
      loading = false;
    }
  }

  async function disconnectGitHub() {
    if (
      !confirm('Are you sure you want to disconnect GitHub? This will remove all repository data.')
    ) {
      return;
    }

    try {
      const accounts = await api.get('/github/accounts');
      if (accounts && accounts.length > 0) {
        await api.delete(`/github/accounts/${accounts[0].id}`);
        isConnected = false;
        repositories = [];
        selectedRepo = null;
      }
    } catch (error) {
      console.error('Failed to disconnect GitHub:', error);
    }
  }

  function startOnboarding() {
    showOnboarding = true;
  }

  function completeOnboarding() {
    showOnboarding = false;
    localStorage.setItem('codemirror-onboarding-seen', 'true');
  }

  function startAnalysis() {
    if (!selectedRepo) {
      alert('Please select a repository first');
      return;
    }
    showAnalysisSelector = true;
  }

  async function handleAnalysisStart(data) {
    const { type, depth } = data;

    if (type === 'cli') {
      // Show CLI instructions in modal or guide
      alert('CLI instructions: Use prsnl-codemirror audit /path/to/repo --upload');
      return;
    }

    // Start web analysis
    showAnalysisSelector = false;

    const analysisOptions = {
      analysis_depth: depth,
      include_patterns: depth !== 'quick',
      include_insights: true,
    };

    try {
      const response = await api.post(`/codemirror/analyze/${selectedRepo.id}`, analysisOptions);

      if (response.job_id) {
        activeAnalysis = {
          id: response.job_id,
          status: 'processing',
          progress_percentage: 0,
          stage: 'initializing',
          depth: depth,
          repository: selectedRepo,
        };

        console.log('✅ Analysis started, activeAnalysis set:', activeAnalysis);

        // Switch to active analyses tab
        activeIntelligenceTab = 'active';

        // Connect to realtime service for live updates
        realtimeService.connect();

        // Start polling as backup
        pollAnalysisStatus(response.job_id);
      }
    } catch (error) {
      console.error('Failed to start analysis:', error);
      alert('Failed to start analysis. Please try again.');
    }
  }

  async function pollAnalysisStatus(jobId: string) {
    const pollInterval = setInterval(async () => {
      try {
        const status = await api.get(`/persistence/status/${jobId}`);

        if (status.status === 'completed') {
          clearInterval(pollInterval);
          activeAnalysis = null;
          await loadTimeline(); // Refresh timeline with new results
          // Disconnect realtime service
          realtimeService.disconnect();
        } else if (status.status === 'failed') {
          clearInterval(pollInterval);
          activeAnalysis = null;
          alert('Analysis failed. Please try again.');
          // Disconnect realtime service
          realtimeService.disconnect();
        } else {
          activeAnalysis = {
            ...activeAnalysis,
            status: status.status,
            progress_percentage: status.progress_percentage || 0,
            stage: status.current_stage || 'processing',
          };
        }
      } catch (error) {
        console.error('Failed to poll analysis status:', error);
        clearInterval(pollInterval);
      }
    }, 2000);
  }

  function handleViewRepository(repo) {
    // Navigate to repository detail page using slug if available, fallback to ID
    const identifier = repo.slug || repo.id;
    window.location.href = `/code-cortex/repo/${identifier}`;
  }

  function handleAnalyzeRepository(repo) {
    selectedRepo = repo;
    startAnalysis();
  }

  function handleTimelineItemClick(item) {
    if (item.type === 'analysis') {
      // Use slug if available, otherwise fall back to ID
      const identifier = item.analysis_slug || item.id;
      window.location.href = `/code-cortex/codemirror/analysis/${identifier}`;
    } else if (item.type === 'insight') {
      // Use slug if available, otherwise fall back to ID
      const identifier = item.analysis_slug || item.id;
      window.location.href = `/code-cortex/codemirror/analysis/${identifier}#insight-${item.id}`;
    }
  }

  function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  }

  function getSeverityColor(severity) {
    switch (severity) {
      case 'critical':
        return 'text-red-400 bg-red-900/30 border-red-600/30';
      case 'high':
        return 'text-orange-400 bg-orange-900/30 border-orange-600/30';
      case 'medium':
        return 'text-yellow-400 bg-yellow-900/30 border-yellow-600/30';
      case 'low':
        return 'text-green-400 bg-green-900/30 border-green-600/30';
      default:
        return 'text-gray-400 bg-gray-900/30 border-gray-600/30';
    }
  }

  function getStatusColor(status) {
    switch (status) {
      case 'completed':
        return 'text-green-400 bg-green-900/30 border-green-600/30';
      case 'processing':
        return 'text-blue-400 bg-blue-900/30 border-blue-600/30';
      case 'failed':
        return 'text-red-400 bg-red-900/30 border-red-600/30';
      default:
        return 'text-gray-400 bg-gray-900/30 border-gray-600/30';
    }
  }
</script>

<svelte:head>
  <title>CodeMirror - AI Repository Intelligence</title>
</svelte:head>

<div class="codemirror-page">
  <!-- Header - Simple, Clean, Purposeful -->
  <header class="page-header">
    <div class="header-content">
      <a href="/code-cortex" class="back-link">← Code Cortex</a>
      <div class="header-title">
        <div class="title-icon">🔍</div>
        <div>
          <h1>CodeMirror</h1>
          <p class="subtitle">AI repository intelligence</p>
        </div>
      </div>
      <button onclick={startOnboarding} class="help-btn"> How it works </button>
    </div>
  </header>

  {#if !isConnected}
    <!-- Connect GitHub CTA - Single, Clear Action -->
    <section class="connect-github">
      <div class="connect-content">
        <div class="connect-icon">🔗</div>
        <h2>Connect your GitHub repositories</h2>
        <p>Analyze your code with AI-powered insights, pattern detection, and security analysis.</p>
        <a href="/api/github/auth/login" class="connect-btn"> Connect GitHub </a>
      </div>
    </section>
  {:else}
    <main class="main-content">
      <!-- Repository Management Section -->
      <section class="repo-section">
        <div class="repo-header">
          <h2>Your Repositories</h2>
          <div class="repo-actions">
            <button class="action-btn secondary" onclick={syncRepositories} disabled={loading}>
              {loading ? '⏳ Syncing...' : '🔄 Sync Repos'}
            </button>
            <button
              class="action-btn secondary"
              onclick={() => (window.location.href = '/code-cortex/open-source')}
            >
              📂 Manage All Repos
            </button>
            <button class="action-btn danger" onclick={disconnectGitHub}>
              🔗 Disconnect GitHub
            </button>
          </div>
        </div>

        <div class="repo-selector-container">
          <input
            type="text"
            placeholder="Search repositories..."
            bind:value={searchQuery}
            class="repo-search"
          />
          <div class="repos-grid">
            {#if filteredRepositories.length === 0}
              <div class="empty-state">
                <div class="empty-icon">📁</div>
                <h3>No repositories found</h3>
                <p>
                  {#if repositories.length === 0}
                    Click "🔄 Sync Repos" to load your GitHub repositories.
                  {:else if searchQuery}
                    Try adjusting your search query.
                  {:else}
                    No repositories match your criteria.
                  {/if}
                </p>
              </div>
            {:else}
              {#each filteredRepositories.slice(0, 8) as repo}
                <div
                  class="repo-card {selectedRepo?.id === repo.id ? 'selected' : ''}"
                  onclick={() => (selectedRepo = repo)}
                >
                  <GitHubRepoCardV2
                    repository={{
                      owner: {
                        login: repo.owner_login || repo.full_name?.split('/')[0] || 'user',
                        avatar_url: repo.owner_avatar_url || 'https://github.com/github.png',
                      },
                      repo: {
                        name: repo.name,
                        full_name: repo.full_name,
                        description: repo.description,
                        language: repo.language,
                        private: repo.is_private,
                        stargazers_count: repo.stars,
                        forks_count: repo.forks,
                      },
                      stats: {
                        stars: repo.stars,
                        forks: repo.forks,
                      },
                      languages: { [repo.language || 'Unknown']: 100 },
                      last_updated: repo.last_synced,
                      url: repo.html_url || `https://github.com/${repo.full_name}`,
                    }}
                    variant="compact"
                    theme="dark"
                  />
                  <div class="repo-actions">
                    <button
                      class="action-btn primary small"
                      onclick={(e) => {
                        e.stopPropagation();
                        handleAnalyzeRepository(repo);
                      }}
                    >
                      🚀 Analyze
                    </button>
                    <button
                      class="action-btn secondary small"
                      onclick={(e) => {
                        e.stopPropagation();
                        handleViewRepository(repo);
                      }}
                    >
                      👁️ View
                    </button>
                  </div>
                </div>
              {/each}
            {/if}
          </div>

          {#if filteredRepositories.length > 8}
            <div class="show-more">
              <button
                class="action-btn secondary"
                onclick={() => (window.location.href = '/code-cortex/repositories')}
              >
                View all {repositories.length} repositories
              </button>
            </div>
          {/if}
        </div>
      </section>

      <!-- Active Analysis Progress - Only When Needed -->
      {#if activeAnalysis}
        <section class="active-analysis">
          <div class="section-header">
            <h2>🚀 Analysis in Progress</h2>
            <p>Repository: {activeAnalysis.repository?.name || 'Unknown'}</p>
          </div>

          <!-- Fallback progress display -->
          <div class="fallback-progress">
            <div class="progress-info">
              <span class="stage">Stage: {activeAnalysis.stage || 'Processing'}</span>
              <span class="percentage">{activeAnalysis.progress_percentage || 0}%</span>
            </div>
            <div class="progress-bar">
              <div
                class="progress-fill"
                style="width: {activeAnalysis.progress_percentage || 0}%"
              ></div>
            </div>
            <p class="job-id">Job ID: {activeAnalysis.id}</p>
          </div>

          <!-- Realtime component -->
          <RealtimeAnalysisProgress analysisId={activeAnalysis.id} />
        </section>
      {/if}

      <!-- Intelligence Sections - What You Actually Asked For -->
      <section class="intelligence-sections" data-testid="intelligence-sections">
        <div class="section-tabs">
          <button
            class="tab-btn {activeIntelligenceTab === 'active' ? 'active' : ''}"
            onclick={() => (activeIntelligenceTab = 'active')}
          >
            🚀 Active Analysis {#if activeAnalysis}(1){/if}
          </button>
          <button
            class="tab-btn {activeIntelligenceTab === 'insights' ? 'active' : ''}"
            onclick={() => (activeIntelligenceTab = 'insights')}
          >
            💡 Insights
          </button>
          <button
            class="tab-btn {activeIntelligenceTab === 'issues' ? 'active' : ''}"
            onclick={() => (activeIntelligenceTab = 'issues')}
          >
            🚨 Critical Issues
          </button>
          <button
            class="tab-btn {activeIntelligenceTab === 'history' ? 'active' : ''}"
            onclick={() => (activeIntelligenceTab = 'history')}
          >
            📊 Run History
          </button>
        </div>

        {#if activeIntelligenceTab === 'active'}
          <div data-testid="active-analyses-section">
            <div class="active-analyses-section">
              {#if !activeAnalysis}
                <div class="empty-state">
                  <div class="empty-icon">🚀</div>
                  <h3>No active analysis</h3>
                  <p>Start analyzing a repository to see live progress.</p>
                </div>
              {:else}
                <div class="analyses-grid">
                  <div class="analysis-card active-card">
                    <div class="analysis-header">
                      <h4>{activeAnalysis.repository?.name || 'Repository Analysis'}</h4>
                      <span class="status-badge {activeAnalysis.status}"
                        >{activeAnalysis.status}</span
                      >
                    </div>
                    <div class="analysis-progress">
                      <div class="progress-details">
                        <span class="stage">{activeAnalysis.stage}</span>
                        <span class="percentage">{activeAnalysis.progress_percentage}%</span>
                      </div>
                      <div class="progress-bar">
                        <div
                          class="progress-fill"
                          style="width: {activeAnalysis.progress_percentage}%"
                        ></div>
                      </div>
                    </div>
                    <div class="analysis-meta">
                      <span>Depth: {activeAnalysis.depth}</span>
                      <span>Job: {activeAnalysis.id?.slice(0, 8)}...</span>
                    </div>
                  </div>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        {#if activeIntelligenceTab === 'insights'}
          <div data-testid="insights-section">
            <div class="insights-section">
              {#if insights.length === 0}
                <div class="empty-state">
                  <div class="empty-icon">💡</div>
                  <h3>No insights yet</h3>
                  <p>Run repository analyses to get AI-powered insights and tips.</p>
                </div>
              {:else}
                <div class="insights-grid">
                  {#each insights as insight}
                    <div class="insight-card" onclick={() => handleTimelineItemClick(insight)}>
                      <div class="insight-header">
                        <h4>{insight.title}</h4>
                        <span class="repo-tag">{insight.repository.name}</span>
                      </div>
                      <p class="insight-description">{insight.recommendation}</p>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        {/if}

        {#if activeIntelligenceTab === 'issues'}
          <div data-testid="issues-section">
            <div class="issues-section">
              {#if criticalIssues.length === 0}
                <div class="empty-state">
                  <div class="empty-icon">🚨</div>
                  <h3>No critical issues</h3>
                  <p>All repositories are looking good!</p>
                </div>
              {:else}
                <div class="issues-grid">
                  {#each criticalIssues as issue}
                    <div
                      class="issue-card severity-{issue.severity}"
                      onclick={() => handleTimelineItemClick(issue)}
                    >
                      <div class="issue-header">
                        <h4>{issue.title}</h4>
                        <span class="severity-badge">{issue.severity.toUpperCase()}</span>
                      </div>
                      <p class="issue-description">{issue.description}</p>
                      <div class="issue-repo">{issue.repository.name}</div>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        {/if}

        {#if activeIntelligenceTab === 'history'}
          <div data-testid="history-section">
            <div class="history-section">
              {#if analysisHistory.length === 0}
                <div class="empty-state">
                  <div class="empty-icon">📊</div>
                  <h3>No analysis history</h3>
                  <p>Start analyzing repositories to see run history.</p>
                </div>
              {:else}
                <div class="history-list">
                  {#each analysisHistory as analysis}
                    <div class="history-item" onclick={() => handleTimelineItemClick(analysis)}>
                      <div class="history-icon">
                        {#if analysis.status === 'completed'}🟢
                        {:else if analysis.status === 'failed'}🔴
                        {:else}🟡{/if}
                      </div>
                      <div class="history-content">
                        <h4>{analysis.title}</h4>
                        <p>{analysis.repository.name} • {formatTimeAgo(analysis.created_at)}</p>
                      </div>
                      <div class="history-arrow">→</div>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </section>
    </main>
  {/if}

  <!-- Onboarding - Only When Needed -->
  {#if showOnboarding}
    <div data-testid="onboarding-wizard">
      <OnboardingWizard onComplete={completeOnboarding} />
    </div>
  {/if}

  <!-- Analysis Selector - Only When Triggered -->
  <div data-testid="analysis-type-selector">
    <AnalysisTypeSelector
      {selectedRepo}
      bind:show={showAnalysisSelector}
      onStart={handleAnalysisStart}
      onShowCLI={() => (showAnalysisSelector = false)}
    />
  </div>
</div>

<style>
  .codemirror-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
  }

  /* Header */
  .page-header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 1rem 2rem;
  }

  .header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 1200px;
    margin: 0 auto;
  }

  .back-link {
    color: rgba(255, 255, 255, 0.7);
    text-decoration: none;
    transition: color 0.2s;
  }

  .back-link:hover {
    color: white;
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .title-icon {
    font-size: 2rem;
  }

  .header-title h1 {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 700;
  }

  .subtitle {
    margin: 0;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.875rem;
  }

  .help-btn {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.3);
    color: #3b82f6;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .help-btn:hover {
    background: rgba(59, 130, 246, 0.2);
  }

  /* Connect GitHub */
  .connect-github {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 70vh;
    padding: 2rem;
  }

  .connect-content {
    text-align: center;
    max-width: 500px;
  }

  .connect-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }

  .connect-content h2 {
    font-size: 2rem;
    margin-bottom: 1rem;
  }

  .connect-content p {
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 2rem;
    font-size: 1.125rem;
  }

  .connect-btn {
    display: inline-block;
    background: #3b82f6;
    color: white;
    padding: 0.75rem 2rem;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    transition: background 0.2s;
  }

  .connect-btn:hover {
    background: #2563eb;
  }

  /* Main Content */
  .main-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  /* Repository Section */
  .repo-section {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 3rem;
  }

  .repo-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
  }

  .repo-header h2 {
    margin: 0;
    font-size: 1.5rem;
  }

  .repo-actions {
    display: flex;
    gap: 0.5rem;
  }

  .repo-search {
    width: 100%;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 0.75rem;
    color: white;
    margin-bottom: 1rem;
  }

  .repo-search::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }

  .repos-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .repo-card-container {
    position: relative;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.2s;
  }

  .repo-card-container:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(59, 130, 246, 0.3);
    transform: translateY(-2px);
  }

  .repo-selection-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: transparent;
    cursor: pointer;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: all 0.2s;
  }

  .repo-selection-overlay:hover {
    background: rgba(59, 130, 246, 0.1);
    opacity: 1;
  }

  .repo-selection-overlay.selected {
    background: rgba(59, 130, 246, 0.2);
    opacity: 1;
  }

  .selection-indicator {
    background: rgba(59, 130, 246, 0.9);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .repo-selection-overlay.selected .selection-indicator {
    background: rgba(34, 197, 94, 0.9);
  }

  .repo-actions {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: rgba(0, 0, 0, 0.2);
    border-top: 1px solid rgba(255, 255, 255, 0.05);
  }

  .action-btn {
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    flex: 1;
  }

  .action-btn.primary {
    background: #3b82f6;
    color: white;
  }

  .action-btn.primary:hover {
    background: #2563eb;
  }

  .action-btn.secondary {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .action-btn.secondary:hover {
    background: rgba(255, 255, 255, 0.15);
    color: white;
  }

  .action-btn.danger {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  .action-btn.danger:hover {
    background: rgba(239, 68, 68, 0.2);
    color: #dc2626;
  }
  .action-btn.small {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
  }
  .action-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .show-more {
    text-align: center;
    margin-top: 1rem;
  }

  /* Timeline */
  .timeline-section {
    margin-top: 3rem;
  }

  .timeline-header {
    margin-bottom: 2rem;
  }

  .timeline-header h2 {
    margin: 0 0 0.5rem 0;
    font-size: 1.75rem;
  }

  .timeline-header p {
    color: rgba(255, 255, 255, 0.7);
    margin: 0;
  }

  .timeline {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .timeline-item {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .timeline-item:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(59, 130, 246, 0.3);
    transform: translateY(-1px);
  }

  .timeline-content {
    flex: 1;
  }

  .timeline-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .timeline-title {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .timeline-title h3 {
    margin: 0;
    font-size: 1.125rem;
  }

  .timeline-time {
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.875rem;
  }

  .timeline-meta {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .repo-name {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.875rem;
  }

  .severity-badge,
  .status-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    border: 1px solid;
  }

  .timeline-subtitle {
    color: rgba(255, 255, 255, 0.8);
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
  }

  .timeline-description {
    color: rgba(255, 255, 255, 0.7);
    margin: 0 0 1rem 0;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .scores {
    display: flex;
    gap: 1rem;
  }

  .score {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .score-label {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.6);
  }

  .score-value {
    font-weight: 600;
    color: #3b82f6;
  }

  .timeline-arrow {
    color: rgba(255, 255, 255, 0.3);
    font-size: 1.25rem;
  }

  /* Loading and Empty States */
  .loading-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
  }

  .loading-spinner {
    width: 2rem;
    height: 2rem;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .empty-state h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.25rem;
  }

  .empty-state p {
    color: rgba(255, 255, 255, 0.7);
    margin: 0;
  }

  .active-analysis {
    margin-bottom: 2rem;
  }

  /* Intelligence Sections - Steve Jobs Style: Clean, Purposeful, No Redundancy */
  .intelligence-sections {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    overflow: hidden;
  }

  .section-tabs {
    display: flex;
    background: rgba(0, 0, 0, 0.3);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .tab-btn {
    flex: 1;
    background: none;
    border: none;
    padding: 1rem 1.5rem;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
  }

  .tab-btn:last-child {
    border-right: none;
  }

  .tab-btn:hover {
    color: white;
    background: rgba(255, 255, 255, 0.05);
  }

  .tab-btn.active {
    color: #3b82f6;
    background: rgba(59, 130, 246, 0.1);
    border-bottom: 2px solid #3b82f6;
  }

  /* Section Content Areas */
  .insights-section,
  .issues-section,
  .history-section {
    padding: 2rem;
    min-height: 400px;
  }

  /* Insights Grid */
  .insights-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .insight-card {
    background: rgba(59, 130, 246, 0.05);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .insight-card:hover {
    background: rgba(59, 130, 246, 0.1);
    border-color: rgba(59, 130, 246, 0.3);
    transform: translateY(-2px);
  }

  .insight-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
  }

  .insight-header h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: white;
    line-height: 1.3;
  }

  .repo-tag {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    margin-left: 0.5rem;
  }

  .insight-description {
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.875rem;
    line-height: 1.5;
    margin: 0;
  }

  /* Issues Grid */
  .issues-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .issue-card {
    border-radius: 8px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid;
  }

  .issue-card.severity-critical {
    background: rgba(239, 68, 68, 0.1);
    border-color: rgba(239, 68, 68, 0.3);
  }

  .issue-card.severity-high {
    background: rgba(245, 158, 11, 0.1);
    border-color: rgba(245, 158, 11, 0.3);
  }

  .issue-card:hover {
    transform: translateY(-2px);
  }

  .issue-card.severity-critical:hover {
    background: rgba(239, 68, 68, 0.15);
    border-color: rgba(239, 68, 68, 0.4);
  }

  .issue-card.severity-high:hover {
    background: rgba(245, 158, 11, 0.15);
    border-color: rgba(245, 158, 11, 0.4);
  }

  .issue-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
  }

  .issue-header h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: white;
    line-height: 1.3;
  }

  .severity-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 0.5rem;
  }

  .issue-card.severity-critical .severity-badge {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }

  .issue-card.severity-high .severity-badge {
    background: rgba(245, 158, 11, 0.2);
    color: #f59e0b;
  }

  .issue-description {
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.875rem;
    line-height: 1.5;
    margin: 0 0 0.75rem 0;
  }

  .issue-repo {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.75rem;
    margin: 0;
  }

  /* History List */
  .history-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .history-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .history-item:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(59, 130, 246, 0.3);
    transform: translateY(-1px);
  }

  .history-icon {
    font-size: 1.25rem;
    min-width: 24px;
    text-align: center;
  }

  .history-content {
    flex: 1;
  }

  .history-content h4 {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    font-weight: 500;
    color: white;
  }

  .history-content p {
    margin: 0;
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.6);
  }

  .history-arrow {
    color: rgba(255, 255, 255, 0.3);
    font-size: 1.25rem;
  }

  /* Empty States */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 4rem 2rem;
  }

  .empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .empty-state h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.25rem;
    color: white;
  }

  .empty-state p {
    margin: 0;
    color: rgba(255, 255, 255, 0.6);
    max-width: 400px;
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .intelligence-sections {
      margin: 0 -2rem;
      border-radius: 0;
      border-left: none;
      border-right: none;
    }

    .section-tabs {
      flex-direction: column;
    }

    .tab-btn {
      border-right: none;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .tab-btn:last-child {
      border-bottom: none;
    }

    .insights-grid,
    .issues-grid {
      grid-template-columns: 1fr;
    }

    .insights-section,
    .issues-section,
    .history-section {
      padding: 1.5rem;
    }

    .insight-header,
    .issue-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .repo-tag,
    .severity-badge {
      margin-left: 0;
    }
  }

  /* Active Analysis Section */
  .active-analysis {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 2rem;
    background: linear-gradient(135deg, rgba(0, 255, 136, 0.05) 0%, rgba(0, 150, 255, 0.05) 100%);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 16px;
    animation: pulse-glow 2s ease-in-out infinite;
  }

  @keyframes pulse-glow {
    0%,
    100% {
      box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
    }
    50% {
      box-shadow: 0 0 40px rgba(0, 255, 136, 0.4);
    }
  }

  .active-analysis .section-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .active-analysis h2 {
    font-size: 1.8rem;
    color: #00ff88;
    margin-bottom: 0.5rem;
  }

  .active-analysis p {
    color: #888;
    font-size: 1rem;
  }

  /* Fallback Progress Display */
  .fallback-progress {
    background: rgba(0, 0, 0, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }

  .progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .stage {
    color: #00ff88;
    font-weight: 500;
  }

  .percentage {
    font-size: 1.5rem;
    font-weight: bold;
    color: #00ff88;
  }

  .progress-bar {
    height: 20px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 1rem;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #00ff88, #00cc6a);
    border-radius: 10px;
    transition: width 0.3s ease;
  }

  .job-id {
    font-size: 0.875rem;
    color: #666;
    text-align: center;
    margin: 0;
  }

  /* Active Analyses Section */
  .active-analyses-section {
    background: rgba(17, 17, 17, 0.6);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
  }

  .analyses-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .analysis-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
  }

  .analysis-card.active-card {
    border-color: #00ff88;
    box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
  }

  .analysis-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  }

  .analysis-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .analysis-header h4 {
    margin: 0;
    color: #fff;
    font-size: 1.1rem;
  }

  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
  }

  .status-badge.processing {
    background: rgba(251, 191, 36, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.3);
  }

  .status-badge.completed {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.3);
  }

  .status-badge.failed {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  .analysis-progress {
    margin-bottom: 1rem;
  }

  .progress-details {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }

  .analysis-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: #888;
  }
</style>
