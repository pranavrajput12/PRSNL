<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import OnboardingWizard from '$lib/components/codecortex/OnboardingWizard.svelte';
  import RepoSelector from '$lib/components/codecortex/RepoSelector.svelte';
  import CodeMirrorAnalysis from '$lib/components/codecortex/CodeMirrorAnalysis.svelte';
  import PatternHistory from '$lib/components/codecortex/PatternHistory.svelte';
  import InsightsList from '$lib/components/codecortex/InsightsList.svelte';
  import AnalysisOverview from '$lib/components/codecortex/AnalysisOverview.svelte';
  import AnalysisTypeSelector from '$lib/components/codecortex/AnalysisTypeSelector.svelte';

  // State management
  let activeTab = $state('overview');
  let showOnboarding = $state(false);
  let selectedRepo = $state(null);
  let isConnected = $state(false);
  let patterns = $state([]);
  let loading = $state(false);
  let activeAnalysis = $state(null);
  let analyses = $state([]);
  let isAnalyzing = $state(false);
  let showAnalysisSelector = $state(false);

  onMount(async () => {
    // Check if user needs onboarding
    const hasSeenOnboarding = localStorage.getItem('codemirror-onboarding-seen');
    if (!hasSeenOnboarding) {
      showOnboarding = true;
    }
    
    // Load initial data
    await Promise.all([
      loadPatterns(),
      checkGitHubConnection()
    ]);
  });

  async function loadPatterns() {
    try {
      patterns = await api.get('/codemirror/patterns');
    } catch (error) {
      console.error('Failed to load patterns:', error);
      patterns = [];
    }
  }

  async function checkGitHubConnection() {
    try {
      const accounts = await api.get('/github/accounts');
      isConnected = accounts && accounts.length > 0;
    } catch (error) {
      isConnected = false;
    }
  }

  function startOnboarding() {
    showOnboarding = true;
  }

  function completeOnboarding() {
    showOnboarding = false;
    localStorage.setItem('codemirror-onboarding-seen', 'true');
  }

  function setActiveTab(tab: string) {
    activeTab = tab;
  }
  
  function startAnalysis() {
    if (!selectedRepo) {
      alert('Please select a repository first');
      return;
    }
    showAnalysisSelector = true;
  }
  
  async function handleAnalysisStart(event) {
    const { type, depth } = event.detail;
    
    if (type === 'cli') {
      // Switch to CLI tab to show instructions
      activeTab = 'cli';
      return;
    }
    
    // Web-based analysis
    isAnalyzing = true;
    try {
      const response = await api.post(`/codemirror/analyze/${selectedRepo.id}`, {
        repo_id: selectedRepo.id,
        analysis_depth: depth,
        include_patterns: true,
        include_insights: true
      });
      
      if (response.job_id) {
        // Switch to analysis tab to show progress
        activeTab = 'analysis';
        activeAnalysis = {
          id: response.job_id,
          status: 'processing',
          progress_percentage: 0,
          stage: 'initializing'
        };
        
        // Poll for status updates
        pollAnalysisStatus(response.job_id);
      }
    } catch (error) {
      console.error('Failed to start analysis:', error);
      alert('Failed to start analysis. Please try again.');
    } finally {
      isAnalyzing = false;
    }
  }
  
  function handleShowCLI() {
    showAnalysisSelector = false;
    activeTab = 'cli';
  }
  
  async function pollAnalysisStatus(jobId: string) {
    const pollInterval = setInterval(async () => {
      try {
        const status = await api.get(`/persistence/status/${jobId}`);
        
        if (status.status === 'completed') {
          clearInterval(pollInterval);
          activeAnalysis = null;
          await loadAnalyses();
          await loadPatterns();
        } else if (status.status === 'failed') {
          clearInterval(pollInterval);
          activeAnalysis = null;
          alert('Analysis failed. Please try again.');
        } else {
          activeAnalysis = {
            ...activeAnalysis,
            status: status.status,
            progress_percentage: status.progress_percentage || 0,
            stage: status.current_stage || 'processing'
          };
        }
      } catch (error) {
        console.error('Failed to poll analysis status:', error);
        clearInterval(pollInterval);
      }
    }, 2000);
  }
  
  async function loadAnalyses() {
    if (!selectedRepo) return;
    
    try {
      analyses = await api.get(`/codemirror/analyses/${selectedRepo.id}`);
    } catch (error) {
      console.error('Failed to load analyses:', error);
      analyses = [];
    }
  }
  
  // Update selectedRepo to trigger data loading
  $effect(() => {
    if (selectedRepo) {
      loadAnalyses();
    }
  });
  
  async function handleSynthesize(problem: string) {
    try {
      const solution = await api.post('/codemirror/synthesize', {
        problem_description: problem,
        file_context: selectedRepo?.name
      });
      
      // Show solution in a modal or alert for now
      alert(`Solution:\n${solution.solution}\n\nConfidence: ${(solution.confidence * 100).toFixed(0)}%`);
    } catch (error) {
      console.error('Failed to synthesize solution:', error);
      alert('Failed to generate solution. Please try again.');
    }
  }
</script>

<div class="codemirror-page">
  <!-- Header -->
  <header class="page-header">
    <div class="header-content">
      <a href="/code-cortex" class="back-link">
        ← Back to Code Cortex
      </a>
      <div class="header-title">
        <div class="title-icon">🔍</div>
        <div>
          <h1>CodeMirror</h1>
          <p class="subtitle">AI-powered repository intelligence</p>
        </div>
      </div>
      <button onclick={startOnboarding} class="help-btn">
        How it works
      </button>
    </div>
  </header>

  <!-- Hero Section -->
  {#if !isConnected && activeTab === 'overview'}
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-text">
          <h2>Unlock the intelligence hidden in your repositories</h2>
          <p class="hero-description">
            CodeMirror analyzes your code repositories using advanced AI to detect patterns, 
            suggest improvements, and provide actionable insights. Connect your GitHub repositories 
            and let AI help you understand your codebase like never before.
          </p>
          
          <!-- Key Features -->
          <div class="features-grid">
            <div class="feature-card">
              <div class="feature-icon">🎯</div>
              <h3>Pattern Detection</h3>
              <p>Automatically identify recurring code patterns and architectural decisions across your repositories.</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">💡</div>
              <h3>Smart Insights</h3>
              <p>Get AI-powered recommendations for code improvements, security fixes, and optimization opportunities.</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">🔄</div>
              <h3>Cross-Repo Analysis</h3>
              <p>Discover how solutions from one project can be applied to challenges in another.</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">⚡</div>
              <h3>CLI Integration</h3>
              <p>Analyze local repositories offline with our powerful command-line tool.</p>
            </div>
          </div>
        </div>
        
        <!-- Trust & Privacy Section -->
        <div class="trust-section">
          <div class="trust-header">
            <div class="trust-icon">🔒</div>
            <h3>Your Privacy Matters</h3>
          </div>
          <div class="trust-content">
            <div class="trust-item">
              <span class="check">✅</span>
              <span>We never store your actual code content</span>
            </div>
            <div class="trust-item">
              <span class="check">✅</span>
              <span>Only structural patterns and metadata are analyzed</span>
            </div>
            <div class="trust-item">
              <span class="check">✅</span>
              <span>All connections use encrypted OAuth (no passwords)</span>
            </div>
            <div class="trust-item">
              <span class="check">✅</span>
              <span>You can disconnect and delete data anytime</span>
            </div>
          </div>
        </div>

        <!-- CTA Section -->
        <div class="cta-section">
          <RepoSelector bind:selected={selectedRepo} />
          <p class="cta-note">
            Start by connecting your GitHub account. We'll only access repository structure and metadata.
          </p>
        </div>
      </div>
    </section>
  {/if}

  <!-- Main Interface (shown after GitHub connection) -->
  {#if isConnected || activeTab !== 'overview'}
    <main class="main-content">
      <!-- Tab Navigation -->
      <nav class="tabs">
        <button 
          class="tab {activeTab === 'overview' ? 'active' : ''}"
          onclick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          class="tab {activeTab === 'analysis' ? 'active' : ''}"
          onclick={() => setActiveTab('analysis')}
        >
          Analysis
        </button>
        <button 
          class="tab {activeTab === 'patterns' ? 'active' : ''}"
          onclick={() => setActiveTab('patterns')}
        >
          Patterns ({patterns.length})
        </button>
        <button 
          class="tab {activeTab === 'insights' ? 'active' : ''}"
          onclick={() => setActiveTab('insights')}
        >
          Insights
        </button>
        <button 
          class="tab {activeTab === 'cli' ? 'active' : ''}"
          onclick={() => setActiveTab('cli')}
        >
          CLI Tools
        </button>
      </nav>

      <!-- Tab Content -->
      <div class="tab-content">
        {#if activeTab === 'overview'}
          <div class="overview-tab">
            <div class="welcome-section">
              <h2>Welcome back to CodeMirror</h2>
              <p>Your repositories are connected and ready for AI analysis.</p>
              
              <!-- Analysis Overview Component -->
              <AnalysisOverview repoId={selectedRepo?.id} />
              
              <!-- Repository Selection -->
              <div class="repo-selection-section">
                <h3>Select Repository for Analysis</h3>
                <RepoSelector bind:selected={selectedRepo} />
                
                {#if selectedRepo}
                  <div class="selected-repo-actions">
                    <div class="selected-repo-info">
                      <h4>Selected Repository</h4>
                      <div class="repo-details">
                        <span class="repo-name">{selectedRepo.name}</span>
                        <span class="repo-language">{selectedRepo.language || 'Unknown'}</span>
                      </div>
                    </div>
                    
                    <button 
                      class="start-analysis-btn"
                      onclick={startAnalysis}
                      disabled={isAnalyzing}
                    >
                      {isAnalyzing ? '🔄 Starting...' : '🚀 Start Analysis'}
                    </button>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {/if}

        {#if activeTab === 'analysis'}
          <CodeMirrorAnalysis 
            {selectedRepo} 
            {activeAnalysis}
            {analyses}
            synthesize={handleSynthesize}
          />
        {/if}

        {#if activeTab === 'patterns'}
          <PatternHistory 
            {patterns} 
            onRefresh={loadPatterns}
            synthesize={handleSynthesize}
          />
        {/if}

        {#if activeTab === 'insights'}
          <InsightsList analysisId={selectedRepo?.id} />
        {/if}

        {#if activeTab === 'cli'}
          <div class="cli-tab">
            <div class="cli-header">
              <h2>🖥️ CLI Tool Integration</h2>
              <p>Analyze repositories locally with the CodeMirror CLI tool</p>
            </div>

            <div class="cli-install">
              <h3>1. Install the CLI tool</h3>
              <div class="code-block">
                <code># Clone the repository
git clone https://github.com/pranavrajput12/PRSNL.git
cd PRSNL/cli/prsnl-codemirror

# Install in development mode
pip install -e .</code>
                <button class="copy-btn" onclick={() => navigator.clipboard.writeText('git clone https://github.com/pranavrajput12/PRSNL.git\ncd PRSNL/cli/prsnl-codemirror\npip install -e .')}>
                  Copy
                </button>
              </div>
              <p class="install-note">Note: Public PyPI release coming soon!</p>
            </div>

            <div class="cli-usage">
              <h3>2. Analyze a repository</h3>
              <div class="code-block">
                <code>prsnl-codemirror audit /path/to/your/repo --depth standard --upload</code>
                <button class="copy-btn" onclick={() => navigator.clipboard.writeText('prsnl-codemirror audit /path/to/your/repo --depth standard --upload')}>
                  Copy
                </button>
              </div>
            </div>

            <div class="cli-features">
              <h3>CLI Features</h3>
              <div class="cli-feature-grid">
                <div class="cli-feature">
                  <strong>🔍 Offline Analysis</strong>
                  <p>Analyze repositories without uploading code</p>
                </div>
                <div class="cli-feature">
                  <strong>⚡ Fast Processing</strong>
                  <p>Local analysis with optional cloud sync</p>
                </div>
                <div class="cli-feature">
                  <strong>🔄 Sync Results</strong>
                  <p>Upload insights to your PRSNL dashboard</p>
                </div>
                <div class="cli-feature">
                  <strong>🎯 Customizable</strong>
                  <p>Configure analysis depth and patterns</p>
                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </main>
  {/if}

  <!-- Onboarding Wizard -->
  {#if showOnboarding}
    <OnboardingWizard onComplete={completeOnboarding} />
  {/if}
  
  <!-- Analysis Type Selector -->
  <AnalysisTypeSelector 
    {selectedRepo}
    bind:show={showAnalysisSelector}
    onstart={handleAnalysisStart}
    onshowCLI={handleShowCLI}
  />
</div>

<style>
  .codemirror-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white;
  }

  /* Header */
  .page-header {
    padding: 1.5rem 2rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(10px);
  }

  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .back-link {
    color: #60a5fa;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    transition: background-color 0.2s;
  }

  .back-link:hover {
    background: rgba(96, 165, 250, 0.1);
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .title-icon {
    font-size: 2rem;
  }

  .header-title h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .subtitle {
    margin: 0;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.9rem;
  }

  .help-btn {
    background: rgba(96, 165, 250, 0.2);
    border: 1px solid rgba(96, 165, 250, 0.3);
    color: #60a5fa;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .help-btn:hover {
    background: rgba(96, 165, 250, 0.3);
    transform: translateY(-1px);
  }

  /* Hero Section */
  .hero-section {
    padding: 4rem 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .hero-content {
    display: grid;
    gap: 3rem;
  }

  .hero-text h2 {
    font-size: 3rem;
    font-weight: 800;
    margin: 0 0 1rem 0;
    background: linear-gradient(135deg, #60a5fa, #a78bfa, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.1;
  }

  .hero-description {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.6;
    margin-bottom: 3rem;
  }

  /* Features Grid */
  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }

  .feature-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 1.5rem;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .feature-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  }

  .feature-icon {
    font-size: 2rem;
    margin-bottom: 1rem;
  }

  .feature-card h3 {
    margin: 0 0 0.5rem 0;
    color: #60a5fa;
    font-size: 1.1rem;
  }

  .feature-card p {
    margin: 0;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.9rem;
    line-height: 1.5;
  }

  /* Trust Section */
  .trust-section {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.2);
    border-radius: 1rem;
    padding: 2rem;
    margin-bottom: 3rem;
  }

  .trust-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }

  .trust-icon {
    font-size: 1.5rem;
  }

  .trust-header h3 {
    margin: 0;
    color: #22c55e;
    font-size: 1.3rem;
  }

  .trust-content {
    display: grid;
    gap: 0.8rem;
  }

  .trust-item {
    display: flex;
    align-items: center;
    gap: 0.8rem;
  }

  .check {
    color: #22c55e;
    font-weight: bold;
  }

  /* CTA Section */
  .cta-section {
    text-align: center;
  }

  .cta-note {
    margin-top: 1rem;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.9rem;
  }

  /* Main Content */
  .main-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  /* Tabs */
  .tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0;
  }

  .tab {
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.6);
    padding: 0.8rem 1.2rem;
    border-radius: 0.5rem 0.5rem 0 0;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.95rem;
    font-weight: 500;
  }

  .tab:hover {
    color: rgba(255, 255, 255, 0.8);
    background: rgba(255, 255, 255, 0.05);
  }

  .tab.active {
    color: white;
    background: rgba(96, 165, 250, 0.2);
    border-bottom: 2px solid #60a5fa;
  }

  /* Tab Content */
  .tab-content {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 1rem;
    padding: 2rem;
    min-height: 400px;
  }

  /* Overview Tab */
  .overview-tab {
    max-width: 1200px;
    margin: 0 auto;
  }

  .welcome-section h2 {
    margin: 0 0 0.5rem 0;
    color: #60a5fa;
    font-size: 1.5rem;
    text-align: center;
  }

  .welcome-section > p {
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 2rem;
    text-align: center;
  }
  
  .repo-selection-section {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .repo-selection-section h3 {
    margin: 0 0 1.5rem 0;
    color: rgba(255, 255, 255, 0.9);
    font-size: 1.125rem;
    text-align: center;
  }
  
  /* Selected Repository Actions */
  .selected-repo-actions {
    margin-top: 2rem;
    padding: 1.5rem;
    background: rgba(96, 165, 250, 0.1);
    border: 1px solid rgba(96, 165, 250, 0.2);
    border-radius: 1rem;
  }
  
  .selected-repo-info {
    margin-bottom: 1.5rem;
  }
  
  .selected-repo-info h3 {
    margin: 0 0 0.5rem 0;
    color: #60a5fa;
    font-size: 1.1rem;
  }
  
  .repo-details {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .repo-name {
    font-size: 1.2rem;
    font-weight: 600;
    color: white;
  }
  
  .repo-language {
    padding: 0.25rem 0.75rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .start-analysis-btn {
    width: 100%;
    padding: 1rem 2rem;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .start-analysis-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
  }
  
  .start-analysis-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  /* CLI Tab */
  .cli-tab {
    max-width: 800px;
  }

  .cli-header {
    margin-bottom: 3rem;
  }

  .cli-header h2 {
    margin: 0 0 0.5rem 0;
    color: #60a5fa;
  }

  .cli-header p {
    margin: 0;
    color: rgba(255, 255, 255, 0.7);
  }

  .cli-install,
  .cli-usage {
    margin-bottom: 2rem;
  }

  .cli-install h3,
  .cli-usage h3 {
    margin: 0 0 1rem 0;
    color: white;
  }

  .code-block {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    padding: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'Monaco', 'Menlo', monospace;
  }

  .code-block code {
    color: #60a5fa;
    font-size: 0.9rem;
    white-space: pre-wrap;
  }
  
  .install-note {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.6);
    font-style: italic;
  }

  .copy-btn {
    background: rgba(96, 165, 250, 0.2);
    border: 1px solid rgba(96, 165, 250, 0.3);
    color: #60a5fa;
    padding: 0.3rem 0.8rem;
    border-radius: 0.3rem;
    cursor: pointer;
    font-size: 0.8rem;
  }

  .copy-btn:hover {
    background: rgba(96, 165, 250, 0.3);
  }

  .cli-features h3 {
    margin: 0 0 1.5rem 0;
    color: white;
  }

  .cli-feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .cli-feature {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    padding: 1rem;
  }

  .cli-feature strong {
    display: block;
    margin-bottom: 0.5rem;
    color: #60a5fa;
  }

  .cli-feature p {
    margin: 0;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.85rem;
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .hero-text h2 {
      font-size: 2rem;
    }

    .hero-description {
      font-size: 1rem;
    }

    .features-grid {
      grid-template-columns: 1fr;
    }

    .header-content {
      flex-direction: column;
      gap: 1rem;
      text-align: center;
    }

    .tabs {
      flex-wrap: wrap;
    }

    .page-header {
      padding: 1rem;
    }

    .hero-section {
      padding: 2rem 1rem;
    }

    .main-content {
      padding: 1rem;
    }
  }
</style>