<script lang="ts">
  import { onMount } from 'svelte';
  import { getApiClient } from '$lib/api/client';
  import { currentUser } from '$lib/stores/unified-auth';
  import Icon from '$lib/components/Icon.svelte';
  
  // Analysis state
  let analysisState = 'idle'; // idle, running, completed, error
  let analysisProgress = 0;
  let currentAgent = '';
  let analysisResult: any = null;
  let error: string | null = null;
  
  // Analysis configuration
  let analysisDepth = 'standard';
  let focusAreas: string[] = [];
  let backgroundAnalysis = false;
  
  // Agent progress tracking
  const agents = [
    { id: 'technical', name: 'Technical Profile Agent', progress: 0, status: 'pending' },
    { id: 'lifestyle', name: 'Lifestyle Pattern Agent', progress: 0, status: 'pending' },
    { id: 'learning', name: 'Learning Style Agent', progress: 0, status: 'pending' },
    { id: 'cross_domain', name: 'Cross-Domain Agent', progress: 0, status: 'pending' },
    { id: 'orchestrator', name: 'Persona Orchestrator', progress: 0, status: 'pending' }
  ];
  
  let agentStates = [...agents];
  
  // Focus area options
  const focusAreaOptions = [
    'technical_skills',
    'learning_patterns',
    'lifestyle_preferences',
    'cross_domain_connections',
    'project_recommendations'
  ];

  onMount(() => {
    // Check if there's existing persona data
    loadExistingPersona();
  });

  async function loadExistingPersona() {
    if (!$currentUser?.id) return;
    
    try {
      const api = getApiClient();
      const response = await api.get(`/persona/user/${$currentUser.id}`);
      analysisResult = response.data;
      analysisState = 'completed';
      updateAgentStates('completed');
    } catch (e: any) {
      if (e.response?.status !== 404) {
        console.error('Error loading existing persona:', e);
      }
      // 404 is expected if no persona exists yet
    }
  }

  async function startAnalysis() {
    if (!$currentUser?.id || analysisState === 'running') return;
    
    analysisState = 'running';
    analysisProgress = 0;
    currentAgent = 'Initializing...';
    error = null;
    analysisResult = null;
    
    // Reset agent states
    agentStates = agents.map(agent => ({ ...agent, progress: 0, status: 'pending' }));
    
    try {
      const api = getApiClient();
      
      // Start the analysis
      updateAgentStates('running', 0);
      currentAgent = 'Technical Profile Agent';
      
      const response = await api.post('/persona/analyze', {
        user_id: $currentUser.id,
        analysis_depth: analysisDepth,
        focus_areas: focusAreas,
        background: backgroundAnalysis
      });
      
      if (backgroundAnalysis) {
        // For background analysis, start polling for results
        pollAnalysisProgress();
      } else {
        // For synchronous analysis, simulate progress and show final result
        await simulateAnalysisProgress();
        
        if (response.data.status === 'completed') {
          analysisResult = response.data.persona_data;
          analysisState = 'completed';
          updateAgentStates('completed');
        } else {
          throw new Error('Analysis failed to complete');
        }
      }
    } catch (e: any) {
      error = e.message || 'Analysis failed';
      analysisState = 'error';
      updateAgentStates('error');
      console.error('Analysis error:', e);
    }
  }

  async function simulateAnalysisProgress() {
    const agentNames = [
      'Technical Profile Agent',
      'Lifestyle Pattern Agent', 
      'Learning Style Agent',
      'Cross-Domain Agent',
      'Persona Orchestrator'
    ];
    
    for (let i = 0; i < agentNames.length; i++) {
      currentAgent = agentNames[i];
      agentStates[i].status = 'running';
      
      // Simulate agent work with progress updates
      for (let progress = 0; progress <= 100; progress += 10) {
        agentStates[i].progress = progress;
        analysisProgress = ((i * 100) + progress) / agentNames.length;
        await new Promise(resolve => setTimeout(resolve, 200));
      }
      
      agentStates[i].status = 'completed';
      agentStates[i].progress = 100;
    }
    
    analysisProgress = 100;
    currentAgent = 'Analysis Complete';
  }

  async function pollAnalysisProgress() {
    // Poll for background analysis completion
    const pollInterval = setInterval(async () => {
      try {
        const api = getApiClient();
        const response = await api.get(`/persona/user/${$currentUser.id}`);
        
        if (response.data) {
          analysisResult = response.data;
          analysisState = 'completed';
          updateAgentStates('completed');
          clearInterval(pollInterval);
        }
      } catch (e) {
        // Continue polling if not ready yet
      }
    }, 2000);
    
    // Stop polling after 5 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (analysisState === 'running') {
        error = 'Analysis timeout - please try again';
        analysisState = 'error';
      }
    }, 300000);
  }

  function updateAgentStates(status: string, progress = 100) {
    agentStates = agentStates.map(agent => ({
      ...agent,
      status,
      progress: status === 'completed' ? 100 : progress
    }));
  }

  function toggleFocusArea(area: string) {
    if (focusAreas.includes(area)) {
      focusAreas = focusAreas.filter(a => a !== area);
    } else {
      focusAreas = [...focusAreas, area];
    }
  }

  function resetAnalysis() {
    analysisState = 'idle';
    analysisProgress = 0;
    currentAgent = '';
    analysisResult = null;
    error = null;
    agentStates = [...agents];
  }

  function exportPersona() {
    if (!analysisResult) return;
    
    const dataStr = JSON.stringify(analysisResult, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `persona-analysis-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  }
</script>

<div class="analysis-page">
  <header class="analysis-header">
    <div class="header-content">
      <div class="breadcrumb">
        <a href="/dreamscape">Dreamscape</a>
        <Icon name="chevron-right" size="small" />
        <span>Persona Analysis</span>
      </div>
      
      <h1>Deep Persona Analysis</h1>
      <p class="subtitle">Multi-agent AI system analyzing your behavioral patterns and preferences</p>
    </div>
  </header>

  <main class="analysis-content">
    {#if analysisState === 'idle'}
      <!-- Configuration Panel -->
      <div class="config-panel">
        <div class="config-section">
          <h2>Analysis Configuration</h2>
          
          <div class="config-grid">
            <div class="config-group">
              <label for="depth">Analysis Depth</label>
              <select id="depth" bind:value={analysisDepth}>
                <option value="light">Light - Quick Overview</option>
                <option value="standard">Standard - Comprehensive</option>
                <option value="deep">Deep - Detailed Insights</option>
              </select>
            </div>
            
            <div class="config-group">
              <label>Processing Mode</label>
              <div class="radio-group">
                <label class="radio-option">
                  <input type="radio" bind:group={backgroundAnalysis} value={false} />
                  <span>Synchronous - Watch Progress</span>
                </label>
                <label class="radio-option">
                  <input type="radio" bind:group={backgroundAnalysis} value={true} />
                  <span>Background - Get Notified</span>
                </label>
              </div>
            </div>
          </div>
          
          <div class="focus-areas">
            <h3>Focus Areas (Optional)</h3>
            <div class="focus-grid">
              {#each focusAreaOptions as area}
                <button 
                  class="focus-button"
                  class:active={focusAreas.includes(area)}
                  on:click={() => toggleFocusArea(area)}
                >
                  <Icon name={focusAreas.includes(area) ? 'check-circle' : 'circle'} size="small" />
                  {area.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </button>
              {/each}
            </div>
          </div>
        </div>
        
        <div class="agents-preview">
          <h3>AI Agent System</h3>
          <div class="agents-grid">
            {#each agents as agent}
              <div class="agent-card">
                <div class="agent-icon">
                  <Icon name="cpu" />
                </div>
                <div class="agent-info">
                  <h4>{agent.name}</h4>
                  <p class="agent-description">
                    {#if agent.id === 'technical'}
                      Analyzes your coding skills, languages, and technical preferences
                    {:else if agent.id === 'lifestyle'}
                      Identifies your interests, activity patterns, and lifestyle choices
                    {:else if agent.id === 'learning'}
                      Determines your learning style, pace, and educational preferences
                    {:else if agent.id === 'cross_domain'}
                      Discovers connections between different areas of interest
                    {:else if agent.id === 'orchestrator'}
                      Synthesizes all insights into a comprehensive persona
                    {/if}
                  </p>
                </div>
              </div>
            {/each}
          </div>
        </div>
        
        <div class="start-section">
          <button class="start-analysis-button" on:click={startAnalysis}>
            <Icon name="play" />
            Begin Persona Analysis
          </button>
          <p class="analysis-note">
            Analysis typically takes 2-5 minutes depending on your data complexity
          </p>
        </div>
      </div>
    
    {:else if analysisState === 'running'}
      <!-- Progress Panel -->
      <div class="progress-panel">
        <div class="progress-header">
          <h2>Analysis in Progress</h2>
          <div class="progress-stats">
            <div class="overall-progress">
              <div class="progress-circle">
                <svg viewBox="0 0 36 36" class="circular-chart">
                  <path class="circle-bg"
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path class="circle"
                    stroke-dasharray="{analysisProgress}, 100"
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <text x="18" y="20.35" class="percentage">{Math.round(analysisProgress)}%</text>
                </svg>
              </div>
              <div class="progress-info">
                <div class="current-agent">{currentAgent}</div>
                <div class="progress-description">
                  {#if analysisProgress < 20}
                    Analyzing technical behavior patterns...
                  {:else if analysisProgress < 40}
                    Identifying lifestyle and interest patterns...
                  {:else if analysisProgress < 60}
                    Determining learning preferences...
                  {:else if analysisProgress < 80}
                    Discovering cross-domain connections...
                  {:else if analysisProgress < 100}
                    Synthesizing comprehensive persona...
                  {:else}
                    Analysis complete!
                  {/if}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="agents-progress">
          {#each agentStates as agent, index}
            <div class="agent-progress" class:active={agent.status === 'running'} class:completed={agent.status === 'completed'}>
              <div class="agent-header">
                <div class="agent-icon-small">
                  {#if agent.status === 'completed'}
                    <Icon name="check-circle" />
                  {:else if agent.status === 'running'}
                    <div class="spinner-small"></div>
                  {:else}
                    <Icon name="circle" />
                  {/if}
                </div>
                <span class="agent-name">{agent.name}</span>
                <span class="agent-percent">{agent.progress}%</span>
              </div>
              <div class="agent-progress-bar">
                <div class="progress-fill" style="width: {agent.progress}%"></div>
              </div>
            </div>
          {/each}
        </div>
        
        <div class="progress-actions">
          <button class="cancel-button" on:click={resetAnalysis}>
            <Icon name="x" />
            Cancel Analysis
          </button>
        </div>
      </div>
    
    {:else if analysisState === 'error'}
      <!-- Error Panel -->
      <div class="error-panel">
        <div class="error-content">
          <Icon name="alert-circle" size="large" />
          <h2>Analysis Failed</h2>
          <p>{error}</p>
          <div class="error-actions">
            <button class="retry-button" on:click={startAnalysis}>
              <Icon name="refresh-cw" />
              Retry Analysis
            </button>
            <button class="back-button" on:click={resetAnalysis}>
              <Icon name="arrow-left" />
              Start Over
            </button>
          </div>
        </div>
      </div>
    
    {:else if analysisState === 'completed'}
      <!-- Results Panel -->
      <div class="results-panel">
        <div class="results-header">
          <div class="results-title">
            <h2>Persona Analysis Complete</h2>
            <div class="analysis-metadata">
              Analyzed on {new Date(analysisResult.analysis_timestamp).toLocaleDateString()}
              • Life Phase: <span class="life-phase">{analysisResult.life_phase || 'Unknown'}</span>
            </div>
          </div>
          <div class="results-actions">
            <button class="export-button" on:click={exportPersona}>
              <Icon name="download" />
              Export Report
            </button>
            <button class="rerun-button" on:click={resetAnalysis}>
              <Icon name="refresh-cw" />
              Run New Analysis
            </button>
          </div>
        </div>
        
        <div class="results-content">
          <!-- Technical Profile -->
          {#if analysisResult.technical_profile}
            <div class="result-section">
              <h3>
                <Icon name="cpu" />
                Technical Profile
              </h3>
              <div class="profile-content">
                <div class="skill-breakdown">
                  <h4>Primary Languages</h4>
                  <div class="skill-tags">
                    {#each analysisResult.technical_profile.primary_languages || [] as language}
                      <span class="skill-tag">{language}</span>
                    {/each}
                  </div>
                </div>
                <div class="skill-breakdown">
                  <h4>Technical Domains</h4>
                  <div class="skill-tags">
                    {#each analysisResult.technical_profile.domains || [] as domain}
                      <span class="skill-tag domain">{domain}</span>
                    {/each}
                  </div>
                </div>
                <div class="skill-breakdown">
                  <h4>Preferred Tools</h4>
                  <div class="skill-tags">
                    {#each analysisResult.technical_profile.tools || [] as tool}
                      <span class="skill-tag tool">{tool}</span>
                    {/each}
                  </div>
                </div>
              </div>
            </div>
          {/if}
          
          <!-- Lifestyle Profile -->
          {#if analysisResult.lifestyle_profile}
            <div class="result-section">
              <h3>
                <Icon name="user" />
                Lifestyle Patterns
              </h3>
              <div class="profile-content">
                <div class="lifestyle-insights">
                  <h4>Primary Interests</h4>
                  <div class="interest-cloud">
                    {#each analysisResult.lifestyle_profile.interests || [] as interest}
                      <span class="interest-tag">{interest}</span>
                    {/each}
                  </div>
                </div>
                {#if analysisResult.lifestyle_profile.activity_patterns}
                  <div class="activity-summary">
                    <h4>Activity Preferences</h4>
                    <div class="activity-chart">
                      {#each Object.entries(analysisResult.lifestyle_profile.activity_patterns) as [period, preference]}
                        <div class="activity-bar">
                          <span class="period-label">{period}</span>
                          <div class="preference-bar">
                            <div class="preference-fill" style="width: {preference * 100}%"></div>
                          </div>
                          <span class="preference-value">{Math.round(preference * 100)}%</span>
                        </div>
                      {/each}
                    </div>
                  </div>
                {/if}
              </div>
            </div>
          {/if}
          
          <!-- Learning Style -->
          {#if analysisResult.learning_style}
            <div class="result-section">
              <h3>
                <Icon name="graduation-cap" />
                Learning Style
              </h3>
              <div class="profile-content">
                <div class="learning-breakdown">
                  <h4>Preferred Learning Methods</h4>
                  <div class="method-tags">
                    {#each analysisResult.learning_style.preferred_formats || [] as format}
                      <span class="method-tag">{format}</span>
                    {/each}
                  </div>
                </div>
                <div class="learning-characteristics">
                  <div class="characteristic">
                    <span class="char-label">Attention Span</span>
                    <span class="char-value">{analysisResult.learning_style.attention_span || 'Medium'}</span>
                  </div>
                  <div class="characteristic">
                    <span class="char-label">Complexity Preference</span>
                    <span class="char-value">{analysisResult.learning_style.complexity_preference || 'Moderate'}</span>
                  </div>
                </div>
              </div>
            </div>
          {/if}
          
          <!-- Cross-Domain Insights -->
          {#if analysisResult.cross_domain_insights}
            <div class="result-section">
              <h3>
                <Icon name="git-merge" />
                Cross-Domain Connections
              </h3>
              <div class="profile-content">
                <div class="connections-content">
                  {#if analysisResult.cross_domain_insights.connections?.length > 0}
                    <div class="connection-list">
                      {#each analysisResult.cross_domain_insights.connections as connection}
                        <div class="connection-item">
                          <div class="connection-nodes">
                            <span class="connection-node">{connection.from}</span>
                            <Icon name="arrow-right" size="small" />
                            <span class="connection-node">{connection.to}</span>
                          </div>
                          <p class="connection-description">{connection.description}</p>
                        </div>
                      {/each}
                    </div>
                  {:else}
                    <p class="no-connections">Cross-domain analysis will develop over time as more data is collected.</p>
                  {/if}
                </div>
              </div>
            </div>
          {/if}
          
          <!-- Recommendations -->
          {#if analysisResult.recommendations?.length > 0}
            <div class="result-section">
              <h3>
                <Icon name="lightbulb" />
                Personalized Recommendations
              </h3>
              <div class="profile-content">
                <div class="recommendations-list">
                  {#each analysisResult.recommendations as recommendation}
                    <div class="recommendation-item">
                      <Icon name="arrow-right" size="small" />
                      <p>{recommendation}</p>
                    </div>
                  {/each}
                </div>
              </div>
            </div>
          {/if}
        </div>
        
        <div class="results-footer">
          <div class="next-steps">
            <h3>What's Next?</h3>
            <div class="next-actions">
              <a href="/dreamscape/learning" class="next-action">
                <Icon name="book" />
                <span>Explore Learning Assistant</span>
              </a>
              <a href="/dreamscape/insights" class="next-action">
                <Icon name="layers" />
                <span>View Tag Insights</span>
              </a>
              <a href="/knowledge-graph" class="next-action">
                <Icon name="git-branch" />  
                <span>Enhanced Knowledge Graph</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  .analysis-page {
    min-height: 100vh;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  /* Header */
  .analysis-header {
    background: rgba(0, 0, 0, 0.4);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    padding: 2rem;
  }

  .header-content {
    max-width: 1200px;
    margin: 0 auto;
  }

  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .breadcrumb a {
    color: var(--neural-green);
    text-decoration: none;
  }

  .breadcrumb a:hover {
    text-decoration: underline;
  }

  .analysis-header h1 {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0 0 0.5rem;
    background: linear-gradient(135deg, var(--neural-green), var(--accent-red));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* Main Content */
  .analysis-content {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  /* Configuration Panel */
  .config-panel {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .config-section h2 {
    margin: 0 0 1.5rem;
    color: var(--text-primary);
  }

  .config-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-bottom: 2rem;
  }

  .config-group label {
    display: block;
    margin-bottom: 0.5rem;
    color: var(--text-secondary);
    font-weight: 500;
  }

  .config-group select {
    width: 100%;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    padding: 0.75rem;
    border-radius: var(--radius);
    font-size: 1rem;
  }

  .radio-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .radio-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: var(--radius);
    transition: background var(--transition-base);
  }

  .radio-option:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  .focus-areas h3 {
    margin: 0 0 1rem;
    color: var(--text-secondary);
  }

  .focus-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem;
  }

  .focus-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-secondary);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
    text-align: left;
  }

  .focus-button:hover,
  .focus-button.active {
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.1);
    border-color: var(--neural-green);
    color: var(--neural-green);
  }

  /* Agents Preview */
  .agents-preview h3 {
    margin: 0 0 1rem;
    color: var(--text-primary);
  }

  .agents-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
  }

  .agent-card {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    transition: all var(--transition-base);
  }

  .agent-card:hover {
    background: rgba(255, 255, 255, 0.05);
    transform: translateY(-2px);
  }

  .agent-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--neural-green), #00C851);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #000;
    flex-shrink: 0;
  }

  .agent-info h4 {
    margin: 0 0 0.5rem;
    color: var(--text-primary);
    font-size: 0.9rem;
  }

  .agent-description {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.8rem;
    line-height: 1.4;
  }

  /* Start Section */
  .start-section {
    text-align: center;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.02);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .start-analysis-button {
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
    margin: 0 auto 1rem;
    box-shadow: 0 8px 24px rgba(0, 255, 100, 0.3);
  }

  .start-analysis-button:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(0, 255, 100, 0.4);
  }

  .analysis-note {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  /* Progress Panel */
  .progress-panel {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    padding: 2rem;
  }

  .progress-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .overall-progress {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    margin: 2rem 0;
  }

  .progress-circle {
    width: 120px;
    height: 120px;
  }

  .circular-chart {
    display: block;
    margin: 0 auto;
    max-width: 120px;
    max-height: 120px;
  }

  .circle-bg {
    fill: none;
    stroke: rgba(255, 255, 255, 0.1);
    stroke-width: 2.8;
  }

  .circle {
    fill: none;
    stroke-width: 2.8;
    stroke-linecap: round;
    animation: progress 1s ease-in-out forwards;
    stroke: var(--neural-green);
  }

  .percentage {
    fill: var(--text-primary);
    font-family: var(--font-mono);
    font-size: 0.5em;
    text-anchor: middle;
  }

  .progress-info {
    text-align: left;
  }

  .current-agent {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--neural-green);
    margin-bottom: 0.5rem;
  }

  .progress-description {
    color: var(--text-secondary);
  }

  /* Agent Progress */
  .agents-progress {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin: 2rem 0;
  }

  .agent-progress {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    padding: 1rem;
    transition: all var(--transition-base);
  }

  .agent-progress.active {
    border-color: var(--neural-green);
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.05);
  }

  .agent-progress.completed {
    border-color: rgba(var(--neural-green-rgb, 0, 255, 100), 0.5);
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.1);
  }

  .agent-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
  }

  .agent-icon-small {
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .agent-name {
    flex: 1;
    font-weight: 500;
    color: var(--text-primary);
  }

  .agent-percent {
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-family: var(--font-mono);
  }

  .agent-progress-bar {
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--neural-green), #00C851);
    transition: width 0.3s ease;
  }

  /* Error Panel */
  .error-panel {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 400px;
  }

  .error-content {
    text-align: center;
    max-width: 400px;
  }

  .error-content h2 {
    color: var(--accent-red);
    margin: 1rem 0;
  }

  .error-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 2rem;
  }

  .retry-button,
  .back-button,
  .cancel-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
  }

  .retry-button {
    background: var(--neural-green);
    color: #000;
    border-color: var(--neural-green);
  }

  .back-button,
  .cancel-button {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
  }

  .retry-button:hover,
  .back-button:hover,
  .cancel-button:hover {
    transform: translateY(-2px);
  }

  /* Results Panel */
  .results-panel {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
  }

  .results-title h2 {
    margin: 0 0 0.5rem;
    color: var(--neural-green);
  }

  .analysis-metadata {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .life-phase {
    color: var(--text-primary);
    font-weight: 600;
    text-transform: capitalize;
  }

  .results-actions {
    display: flex;
    gap: 1rem;
  }

  .export-button,
  .rerun-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
  }

  .export-button {
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.1);
    color: var(--neural-green);
    border-color: var(--neural-green);
  }

  .rerun-button {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
  }

  .results-content {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .result-section {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    padding: 2rem;
  }

  .result-section h3 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0 0 1.5rem;
    color: var(--text-primary);
    font-size: 1.3rem;
  }

  .profile-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  /* Skill Tags */
  .skill-breakdown h4,
  .lifestyle-insights h4,
  .learning-breakdown h4 {
    margin: 0 0 0.75rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .skill-tags,
  .method-tags {
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

  .skill-tag.tool {
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.2);
    color: var(--neural-green);
    border-color: rgba(var(--neural-green-rgb, 0, 255, 100), 0.3);
  }

  .method-tag {
    padding: 0.25rem 0.75rem;
    background: rgba(245, 158, 11, 0.2);
    color: #FBBF24;
    border-radius: var(--radius);
    font-size: 0.8rem;
    border: 1px solid rgba(245, 158, 11, 0.3);
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

  /* Activity Chart */
  .activity-chart {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .activity-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .period-label {
    width: 80px;
    font-size: 0.9rem;
    color: var(--text-secondary);
    text-transform: capitalize;
  }

  .preference-bar {
    flex: 1;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }

  .preference-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--neural-green), #00C851);
    transition: width 0.5s ease;
  }

  .preference-value {
    width: 40px;
    text-align: right;
    font-size: 0.8rem;
    color: var(--text-secondary);
    font-family: var(--font-mono);
  }

  /* Learning Characteristics */
  .learning-characteristics {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .characteristic {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: var(--radius);
  }

  .char-label {
    color: var(--text-secondary);
  }

  .char-value {
    color: var(--text-primary);
    font-weight: 600;
    text-transform: capitalize;
  }

  /* Connections */
  .connection-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .connection-item {
    padding: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: var(--radius);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .connection-nodes {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .connection-node {
    padding: 0.25rem 0.75rem;
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.2);
    color: var(--neural-green);
    border-radius: var(--radius);
    font-size: 0.8rem;
    font-weight: 600;
  }

  .connection-description {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
    line-height: 1.4;
  }

  .no-connections {
    color: var(--text-secondary);
    font-style: italic;
    text-align: center;
    padding: 2rem;
  }

  /* Recommendations */
  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .recommendation-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: var(--radius);
    border-left: 3px solid var(--neural-green);
  }

  .recommendation-item p {
    margin: 0;
    color: var(--text-primary);
    line-height: 1.5;
  }

  /* Results Footer */
  .results-footer {
    padding: 2rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
  }

  .next-steps h3 {
    margin: 0 0 1rem;
    color: var(--text-primary);
  }

  .next-actions {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .next-action {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    color: var(--text-primary);
    text-decoration: none;
    transition: all var(--transition-base);
  }

  .next-action:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  }

  /* Animations */
  .spinner-small {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(var(--neural-green-rgb, 0, 255, 100), 0.3);
    border-top: 2px solid var(--neural-green);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes progress {
    0% {
      stroke-dasharray: 0 100;
    }
  }

  /* Responsive */
  @media (max-width: 768px) {
    .analysis-header,
    .analysis-content {
      padding: 1rem;
    }

    .config-grid {
      grid-template-columns: 1fr;
    }

    .agents-grid {
      grid-template-columns: 1fr;
    }

    .results-header {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }

    .results-actions {
      width: 100%;
      justify-content: flex-start;
    }

    .overall-progress {
      flex-direction: column;
      gap: 1rem;
    }
  }
</style>