<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { getApiClient } from '$lib/api/client';
  import { currentUser, authToken } from '$lib/stores/unified-auth';
  import Icon from '$lib/components/Icon.svelte';
  
  // State
  let loading = true;
  let error: string | null = null;
  let personaData: any = null;
  let analysisRunning = false;
  let lastAnalyzed: string | null = null;
  
  // Dashboard metrics
  let engagementScore = 0;
  let diversityScore = 0;
  let learningVelocity = 0;
  let lifePhase = 'analyzing';
  
  // Component visibility
  let showTechnicalProfile = true;
  let showLifestylePanels = true;
  let showLearningInsights = true;
  let showCrossDomainConnections = true;

  onMount(async () => {
    await loadPersonaData();
  });

  async function loadPersonaData() {
    if (!$currentUser?.id || !$authToken) return;
    
    loading = true;
    error = null;
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      
      // Try to get existing persona data
      try {
        const response = await api.get(`/persona/user/${$currentUser.id}`);
        personaData = response.data;
        extractMetrics();
      } catch (e: any) {
        if (e.status === 404) {
          // No persona data exists, that's OK
          personaData = null;
        } else {
          throw e;
        }
      }
    } catch (e: any) {
      error = e.message || 'Failed to load persona data';
      console.error('Error loading persona:', e);
    } finally {
      loading = false;
    }
  }

  function extractMetrics() {
    if (!personaData) return;
    
    const metrics = personaData.behavioral_metrics || {};
    engagementScore = metrics.engagement_score || 0;
    diversityScore = metrics.diversity_score || 0;
    learningVelocity = metrics.learning_velocity || 0;
    lifePhase = personaData.life_phase || 'analyzing';
    lastAnalyzed = personaData.last_analyzed_at;
  }

  async function triggerAnalysis() {
    if (!$currentUser?.id || !$authToken || analysisRunning) return;
    
    analysisRunning = true;
    error = null;
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      
      const response = await api.post('/persona/analyze', {
        user_id: $currentUser.id,
        analysis_depth: 'standard',
        background: false
      });
      
      if (response.data.status === 'completed') {
        personaData = response.data.persona_data;
        extractMetrics();
      }
    } catch (e: any) {
      error = e.message || 'Failed to analyze persona';
      console.error('Error analyzing persona:', e);
    } finally {
      analysisRunning = false;
    }
  }

  function getLifePhaseColor(phase: string) {
    switch (phase) {
      case 'early_career': return '#10B981';
      case 'mid_career': return '#3B82F6';
      case 'experienced': return '#8B5CF6';
      default: return '#6B7280';
    }
  }

  function formatScore(score: number) {
    return Math.round(score * 100);
  }

  function navigateToAnalysis() {
    window.location.href = '/dreamscape/analysis';
  }

  function navigateToLearning() {
    window.location.href = '/dreamscape/learning';
  }

  function navigateToInsights() {
    window.location.href = '/dreamscape/insights';
  }
</script>

<div class="dreamscape-dashboard">
  <header class="dashboard-header">
    <div class="header-content">
      <div class="title-section">
        <h1>
          <span class="brain-icon">🧠</span>
          Dreamscape
        </h1>
        <p class="subtitle">Your Personal Intelligence Dashboard</p>
      </div>
      
      <div class="header-actions">
        {#if personaData}
          <div class="last-analysis">
            Last analyzed: {lastAnalyzed ? new Date(lastAnalyzed).toLocaleDateString() : 'Never'}
          </div>
        {/if}
        
        <button 
          class="analysis-trigger"
          class:loading={analysisRunning}
          on:click={triggerAnalysis}
          disabled={analysisRunning}
        >
          {#if analysisRunning}
            <div class="spinner"></div>
            Analyzing...
          {:else}
            <Icon name="zap" size="small" />
            {personaData ? 'Refresh Analysis' : 'Start Analysis'}
          {/if}
        </button>
      </div>
    </div>
  </header>

  <main class="dashboard-content">
    {#if loading}
      <div class="loading-state">
        <div class="neural-loading">
          <div class="brain-pulse"></div>
          <p>Initializing Dreamscape...</p>
        </div>
      </div>
    {:else if error}
      <div class="error-state">
        <Icon name="alert-circle" size="large" />
        <p>{error}</p>
        <button on:click={loadPersonaData}>Retry</button>
      </div>
    {:else if !personaData}
      <div class="empty-state">
        <div class="empty-content">
          <div class="neural-circuit-bg">
            <div class="circuit-lines"></div>
          </div>
          <h2>Welcome to Dreamscape</h2>
          <p>Your personal intelligence system that learns from your behavior and preferences.</p>
          <div class="features-preview">
            <div class="feature-card">
              <Icon name="cpu" />
              <h3>Technical Profile</h3>
              <p>AI analysis of your coding skills and tech preferences</p>
            </div>
            <div class="feature-card">
              <Icon name="user" />
              <h3>Lifestyle Patterns</h3>
              <p>Understanding your interests and activity preferences</p>
            </div>
            <div class="feature-card">
              <Icon name="graduation-cap" />
              <h3>Learning Style</h3>
              <p>Personalized insights into how you learn best</p>
            </div>
            <div class="feature-card">
              <Icon name="git-merge" />
              <h3>Cross-Domain Insights</h3>
              <p>Discovering connections between different areas of interest</p>
            </div>
          </div>
          <button class="start-button" on:click={triggerAnalysis} disabled={analysisRunning}>
            {#if analysisRunning}
              <div class="spinner"></div>
              Creating Your Intelligence Profile...
            {:else}
              <Icon name="sparkles" />
              Begin Persona Analysis
            {/if}
          </button>
        </div>
      </div>
    {:else}
      <!-- Main Dashboard Content -->
      <div class="dashboard-grid">
        <!-- Overview Cards -->
        <div class="overview-section">
          <div class="metric-cards">
            <div class="metric-card">
              <div class="metric-icon engagement">
                <Icon name="activity" />
              </div>
              <div class="metric-content">
                <h3>Engagement</h3>
                <div class="metric-value">{formatScore(engagementScore)}%</div>
                <div class="metric-trend">
                  <Icon name="trending-up" size="small" />
                  Active learner
                </div>
              </div>
            </div>

            <div class="metric-card">
              <div class="metric-icon diversity">
                <Icon name="shuffle" />
              </div>
              <div class="metric-content">
                <h3>Diversity</h3>
                <div class="metric-value">{formatScore(diversityScore)}%</div>
                <div class="metric-trend">
                  <Icon name="layers" size="small" />
                  Multi-domain
                </div>
              </div>
            </div>

            <div class="metric-card">
              <div class="metric-icon velocity">
                <Icon name="zap" />
              </div>
              <div class="metric-content">
                <h3>Learning Velocity</h3>
                <div class="metric-value">{formatScore(learningVelocity)}%</div>
                <div class="metric-trend">
                  <Icon name="arrow-up" size="small" />
                  Accelerating
                </div>
              </div>
            </div>

            <div class="metric-card">
              <div class="metric-icon life-phase" style="background-color: {getLifePhaseColor(lifePhase)}">
                <Icon name="user-check" />
              </div>
              <div class="metric-content">
                <h3>Life Phase</h3>
                <div class="metric-value">{lifePhase.replace('_', ' ')}</div>
                <div class="metric-trend">
                  <Icon name="compass" size="small" />
                  Evolving
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Technical Profile Panel -->
        {#if showTechnicalProfile}
          <div class="panel technical-panel">
            <div class="panel-header">
              <h2>
                <Icon name="cpu" />
                Technical Profile
              </h2>
              <button class="expand-button" on:click={navigateToAnalysis}>
                <Icon name="external-link" size="small" />
              </button>
            </div>
            <div class="panel-content">
              {#if personaData.technical_profile}
                <div class="tech-skills">
                  <div class="skill-category">
                    <h4>Primary Languages</h4>
                    <div class="skill-tags">
                      {#each personaData.technical_profile.primary_languages || [] as language}
                        <span class="skill-tag">{language}</span>
                      {/each}
                    </div>
                  </div>
                  <div class="skill-category">
                    <h4>Domains</h4>
                    <div class="skill-tags">
                      {#each personaData.technical_profile.domains || [] as domain}
                        <span class="skill-tag domain">{domain}</span>
                      {/each}
                    </div>
                  </div>
                </div>
              {:else}
                <div class="panel-placeholder">
                  <Icon name="code" size="large" />
                  <p>Technical profile will appear here after analysis</p>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Lifestyle Panel -->
        {#if showLifestylePanels}
          <div class="panel lifestyle-panel">
            <div class="panel-header">
              <h2>
                <Icon name="user" />
                Lifestyle Patterns
              </h2>
              <button class="expand-button" on:click={navigateToInsights}>
                <Icon name="external-link" size="small" />
              </button>
            </div>
            <div class="panel-content">
              {#if personaData.lifestyle_profile}
                <div class="lifestyle-insights">
                  <div class="interest-cloud">
                    {#each personaData.lifestyle_profile.interests || [] as interest}
                      <span class="interest-tag">{interest}</span>
                    {/each}
                  </div>
                  <div class="activity-pattern">
                    <h4>Activity Preferences</h4>
                    <div class="time-distribution">
                      <!-- Would show time-based activity charts -->
                      <div class="time-bar">
                        <span class="time-label">Morning</span>
                        <div class="time-fill" style="width: 30%"></div>
                      </div>
                      <div class="time-bar">
                        <span class="time-label">Afternoon</span>
                        <div class="time-fill" style="width: 60%"></div>
                      </div>
                      <div class="time-bar">
                        <span class="time-label">Evening</span>
                        <div class="time-fill" style="width: 80%"></div>
                      </div>
                    </div>
                  </div>
                </div>
              {:else}
                <div class="panel-placeholder">
                  <Icon name="compass" size="large" />
                  <p>Lifestyle patterns will appear here after analysis</p>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Learning Insights Panel -->
        {#if showLearningInsights}
          <div class="panel learning-panel">
            <div class="panel-header">
              <h2>
                <Icon name="graduation-cap" />
                Learning Style
              </h2>
              <button class="expand-button" on:click={navigateToLearning}>
                <Icon name="external-link" size="small" />
              </button>
            </div>
            <div class="panel-content">
              {#if personaData.learning_style}
                <div class="learning-insights">
                  <div class="learning-method">
                    <h4>Preferred Methods</h4>
                    <div class="method-tags">
                      {#each personaData.learning_style.preferred_formats || [] as format}
                        <span class="method-tag">{format}</span>
                      {/each}
                    </div>
                  </div>
                  <div class="learning-stats">
                    <div class="stat">
                      <span class="stat-label">Attention Span</span>
                      <span class="stat-value">{personaData.learning_style.attention_span || 'Medium'}</span>
                    </div>
                    <div class="stat">
                      <span class="stat-label">Complexity Preference</span>
                      <span class="stat-value">{personaData.learning_style.complexity_preference || 'Moderate'}</span>
                    </div>
                  </div>
                </div>
              {:else}
                <div class="panel-placeholder">
                  <Icon name="book-open" size="large" />
                  <p>Learning style insights will appear here after analysis</p>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Cross-Domain Connections Panel -->
        {#if showCrossDomainConnections}
          <div class="panel connections-panel">
            <div class="panel-header">
              <h2>
                <Icon name="git-merge" />
                Cross-Domain Insights
              </h2>
              <button class="expand-button" on:click={navigateToInsights}>
                <Icon name="external-link" size="small" />
              </button>
            </div>
            <div class="panel-content">
              {#if personaData.cross_domain_insights}
                <div class="connections-preview">
                  <div class="connection-nodes">
                    <!-- Visual representation of domain connections -->
                    <div class="node-network">
                      <div class="connection-node primary">Tech</div>
                      <div class="connection-line"></div>
                      <div class="connection-node secondary">Design</div>
                    </div>
                  </div>
                  <div class="connection-suggestions">
                    <h4>Potential Synergies</h4>
                    <ul class="suggestion-list">
                      <li>Combine coding skills with design thinking</li>
                      <li>Explore data visualization opportunities</li>
                    </ul>
                  </div>
                </div>
              {:else}
                <div class="panel-placeholder">
                  <Icon name="git-branch" size="large" />
                  <p>Cross-domain connections will appear here after analysis</p>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        <!-- Quick Actions Panel -->
        <div class="panel actions-panel">
          <div class="panel-header">
            <h2>
              <Icon name="zap" />
              Quick Actions
            </h2>
          </div>
          <div class="panel-content">
            <div class="action-grid">
              <button class="action-button" on:click={navigateToAnalysis}>
                <Icon name="search" />
                <span>Deep Analysis</span>
              </button>
              <button class="action-button" on:click={navigateToLearning}>
                <Icon name="book" />
                <span>Learning Path</span>
              </button>
              <button class="action-button" on:click={navigateToInsights}>
                <Icon name="lightbulb" />
                <span>Tag Insights</span>
              </button>
              <button class="action-button" on:click={() => window.location.href = '/knowledge-graph'}>
                <Icon name="git-branch" />
                <span>Knowledge Graph</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  .dreamscape-dashboard {
    min-height: 100vh;
    background: var(--bg-primary);
    color: var(--text-primary);
    position: relative;
    overflow: hidden;
  }

  /* Header Styles */
  .dashboard-header {
    background: rgba(0, 0, 0, 0.4);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  .title-section h1 {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, var(--neural-green), var(--accent-red));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .brain-icon {
    animation: brain-pulse 2s ease-in-out infinite;
  }

  @keyframes brain-pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
  }

  .subtitle {
    margin: 0.5rem 0 0;
    color: var(--text-secondary);
    font-size: 1.1rem;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .last-analysis {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .analysis-trigger {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: linear-gradient(135deg, var(--neural-green), #00e652);
    color: #000;
    border: none;
    border-radius: var(--radius);
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-base);
    box-shadow: 0 4px 12px rgba(0, 255, 100, 0.3);
  }

  .analysis-trigger:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 255, 100, 0.4);
  }

  .analysis-trigger:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  /* Main Content Styles */
  .dashboard-content {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  /* Loading States */
  .loading-state, .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    text-align: center;
  }

  .neural-loading {
    position: relative;
  }

  .brain-pulse {
    width: 80px;
    height: 80px;
    background: radial-gradient(circle, var(--neural-green), transparent);
    border-radius: 50%;
    animation: pulse-glow 2s ease-in-out infinite;
    margin-bottom: 2rem;
  }

  @keyframes pulse-glow {
    0%, 100% {
      transform: scale(1);
      opacity: 0.8;
    }
    50% {
      transform: scale(1.2);
      opacity: 1;
    }
  }

  /* Empty State */
  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 70vh;
    position: relative;
  }

  .empty-content {
    text-align: center;
    max-width: 800px;
    position: relative;
    z-index: 2;
  }

  .neural-circuit-bg {
    position: absolute;
    top: -100px;
    left: -100px;
    right: -100px;
    bottom: -100px;
    opacity: 0.1;
    z-index: 1;
  }

  .circuit-lines {
    width: 100%;
    height: 100%;
    background: 
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 40px,
        var(--neural-green) 40px,
        var(--neural-green) 42px
      ),
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 40px,
        var(--neural-green) 40px,
        var(--neural-green) 42px
      );
    animation: circuit-flow 10s linear infinite;
  }

  @keyframes circuit-flow {
    0% { transform: translate(0, 0); }
    100% { transform: translate(42px, 42px); }
  }

  .empty-content h2 {
    font-size: 2rem;
    margin-bottom: 1rem;
    color: var(--neural-green);
  }

  .features-preview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin: 3rem 0;
  }

  .feature-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    padding: 1.5rem;
    text-align: center;
    transition: all var(--transition-base);
  }

  .feature-card:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-2px);
  }

  .feature-card h3 {
    margin: 1rem 0 0.5rem;
    color: var(--text-primary);
  }

  .start-button {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 2rem;
    background: linear-gradient(135deg, var(--neural-green), #00e652);
    color: #000;
    border: none;
    border-radius: var(--radius-lg);
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-base);
    margin: 2rem auto 0;
    box-shadow: 0 8px 24px rgba(0, 255, 100, 0.3);
  }

  .start-button:hover:not(:disabled) {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(0, 255, 100, 0.4);
  }

  /* Dashboard Grid */
  .dashboard-grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 1.5rem;
    margin-top: 2rem;
  }

  .overview-section {
    grid-column: 1 / -1;
    margin-bottom: 1rem;
  }

  .metric-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
  }

  .metric-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all var(--transition-base);
  }

  .metric-card:hover {
    background: rgba(255, 255, 255, 0.05);
    transform: translateY(-2px);
  }

  .metric-icon {
    width: 50px;
    height: 50px;
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }

  .metric-icon.engagement { background: linear-gradient(135deg, #3B82F6, #1E40AF); }
  .metric-icon.diversity { background: linear-gradient(135deg, #8B5CF6, #6B46C1); }
  .metric-icon.velocity { background: linear-gradient(135deg, var(--neural-green), #00C851); }
  .metric-icon.life-phase { background: linear-gradient(135deg, #F59E0B, #D97706); }

  .metric-content h3 {
    margin: 0 0 0.5rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  .metric-trend {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    color: var(--neural-green);
    font-size: 0.8rem;
  }

  /* Panel Styles */
  .panel {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(20px);
    overflow: hidden;
    transition: all var(--transition-base);
  }

  .panel:hover {
    background: rgba(255, 255, 255, 0.05);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }

  .technical-panel { grid-column: 1 / 7; }
  .lifestyle-panel { grid-column: 7 / -1; }
  .learning-panel { grid-column: 1 / 7; }
  .connections-panel { grid-column: 7 / -1; }
  .actions-panel { grid-column: 1 / -1; }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.02);
  }

  .panel-header h2 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 1.2rem;
    color: var(--text-primary);
  }

  .expand-button {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.5rem;
    border-radius: var(--radius);
    transition: all var(--transition-base);
  }

  .expand-button:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
  }

  .panel-content {
    padding: 1.5rem;
  }

  .panel-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 120px;
    color: var(--text-secondary);
    text-align: center;
  }

  /* Technical Panel */
  .tech-skills {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .skill-category h4 {
    margin: 0 0 0.5rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .skill-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .skill-tag {
    padding: 0.25rem 0.75rem;
    background: rgba(59, 130, 246, 0.2);
    color: #60A5FA;
    border-radius: var(--radius);
    font-size: 0.8rem;
    border: 1px solid rgba(59, 130, 246, 0.3);
  }

  .skill-tag.domain {
    background: rgba(139, 92, 246, 0.2);
    color: #A78BFA;
    border-color: rgba(139, 92, 246, 0.3);
  }

  /* Lifestyle Panel */
  .lifestyle-insights {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .interest-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .interest-tag {
    padding: 0.25rem 0.75rem;
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.2);
    color: var(--neural-green);
    border-radius: var(--radius);
    font-size: 0.8rem;
    border: 1px solid rgba(var(--neural-green-rgb, 0, 255, 100), 0.3);
  }

  .activity-pattern h4 {
    margin: 0 0 1rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .time-distribution {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .time-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .time-label {
    width: 80px;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .time-fill {
    height: 8px;
    background: linear-gradient(90deg, var(--neural-green), #00C851);
    border-radius: 4px;
    transition: width var(--transition-base);
  }

  /* Learning Panel */
  .learning-insights {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .method-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .method-tag {
    padding: 0.25rem 0.75rem;
    background: rgba(245, 158, 11, 0.2);
    color: #FBBF24;
    border-radius: var(--radius);
    font-size: 0.8rem;
    border: 1px solid rgba(245, 158, 11, 0.3);
  }

  .learning-stats {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stat-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .stat-value {
    color: var(--text-primary);
    font-weight: 600;
    text-transform: capitalize;
  }

  /* Connections Panel */
  .connections-preview {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .node-network {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 1rem 0;
  }

  .connection-node {
    padding: 0.5rem 1rem;
    border-radius: var(--radius);
    font-weight: 600;
    font-size: 0.9rem;
  }

  .connection-node.primary {
    background: rgba(59, 130, 246, 0.2);
    color: #60A5FA;
    border: 2px solid rgba(59, 130, 246, 0.3);
  }

  .connection-node.secondary {
    background: rgba(139, 92, 246, 0.2);
    color: #A78BFA;
    border: 2px solid rgba(139, 92, 246, 0.3);
  }

  .connection-line {
    width: 40px;
    height: 2px;
    background: linear-gradient(90deg, #60A5FA, #A78BFA);
    position: relative;
  }

  .connection-line::after {
    content: '';
    position: absolute;
    right: -6px;
    top: -4px;
    width: 0;
    height: 0;
    border-left: 6px solid #A78BFA;
    border-top: 5px solid transparent;
    border-bottom: 5px solid transparent;
  }

  .suggestion-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .suggestion-list li {
    padding: 0.5rem 0;
    color: var(--text-secondary);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .suggestion-list li:last-child {
    border-bottom: none;
  }

  /* Actions Panel */
  .action-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
  }

  .action-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1.5rem 1rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    color: var(--text-primary);
    cursor: pointer;
    transition: all var(--transition-base);
    text-decoration: none;
  }

  .action-button:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  }

  /* Spinner Animation */
  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(0, 0, 0, 0.3);
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .header-content {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }

    .dashboard-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .technical-panel,
    .lifestyle-panel,
    .learning-panel,
    .connections-panel,
    .actions-panel {
      grid-column: 1 / -1;
    }

    .metric-cards {
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    }

    .features-preview {
      grid-template-columns: 1fr;
    }
  }
</style>