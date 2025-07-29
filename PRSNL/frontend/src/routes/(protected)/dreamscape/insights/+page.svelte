<script lang="ts">
  import { onMount } from 'svelte';
  import { getApiClient } from '$lib/api/client';
  import { currentUser, authToken } from '$lib/stores/unified-auth';
  import Icon from '$lib/components/Icon.svelte';
  import * as d3 from 'd3';
  
  // State
  let loading = true;
  let error: string | null = null;
  let personaData: any = null;
  let tagClusters: any[] = [];
  let selectedCluster: any = null;
  let analysisMode = 'automatic'; // automatic, manual, hybrid
  
  // Visualization
  let clusterContainer: HTMLDivElement;
  let clusterViz: any = null;
  
  // Sample tag clusters (would come from ML analysis)
  let sampleClusters = [
    {
      id: 'web-dev-cluster',
      name: 'Web Development',
      tags: ['javascript', 'react', 'html', 'css', 'node.js', 'express', 'mongodb'],
      strength: 0.89,
      size: 147,
      color: '#3B82F6',
      connections: ['mobile-dev-cluster', 'data-viz-cluster'],
      projects: [
        { name: 'E-commerce Platform', relevance: 0.95 },
        { name: 'Portfolio Website', relevance: 0.87 },
        { name: 'REST API Service', relevance: 0.82 }
      ],
      insights: [
        'Strong focus on full-stack JavaScript development',
        'MERN stack appears to be your preferred technology',
        'Consider exploring TypeScript for better code quality'
      ]
    },
    {
      id: 'data-science-cluster',
      name: 'Data Science & Analytics',
      tags: ['python', 'pandas', 'numpy', 'scikit-learn', 'jupyter', 'matplotlib', 'data-analysis'],
      strength: 0.76,
      size: 89,
      color: '#10B981',
      connections: ['machine-learning-cluster', 'data-viz-cluster'],
      projects: [
        { name: 'Customer Analytics Dashboard', relevance: 0.92 },
        { name: 'Predictive Model', relevance: 0.78 },
        { name: 'Data Pipeline', relevance: 0.71 }
      ],
      insights: [
        'Emerging interest in data-driven decision making',
        'Python ecosystem mastery is developing well',
        'Opportunity to bridge web dev skills with data science'
      ]
    },
    {
      id: 'mobile-dev-cluster',
      name: 'Mobile Development',
      tags: ['react-native', 'flutter', 'ios', 'android', 'mobile-ui', 'app-store'],
      strength: 0.64,
      size: 52,
      color: '#8B5CF6',
      connections: ['web-dev-cluster', 'ui-design-cluster'],
      projects: [
        { name: 'Task Management App', relevance: 0.85 },
        { name: 'Weather App', relevance: 0.72 }
      ],
      insights: [
        'Cross-platform development approach preferred',
        'Strong connection to existing web development skills',
        'UI/UX considerations are important to your work'
      ]
    },
    {
      id: 'ui-design-cluster',
      name: 'UI/UX Design',
      tags: ['figma', 'design-systems', 'user-experience', 'prototyping', 'usability', 'accessibility'],
      strength: 0.58,
      size: 34,
      color: '#F59E0B',
      connections: ['web-dev-cluster', 'mobile-dev-cluster'],
      projects: [
        { name: 'Design System', relevance: 0.89 },
        { name: 'User Research Study', relevance: 0.73 }
      ],
      insights: [
        'Design thinking influences your development approach',
        'Strong emphasis on user-centered design',
        'Accessibility considerations are well integrated'
      ]
    },
    {
      id: 'devops-cluster',
      name: 'DevOps & Infrastructure',
      tags: ['docker', 'kubernetes', 'aws', 'ci-cd', 'monitoring', 'deployment', 'automation'],
      strength: 0.45,
      size: 28,
      color: '#EF4444',
      connections: ['web-dev-cluster', 'data-science-cluster'],
      projects: [
        { name: 'Automated Deployment Pipeline', relevance: 0.91 },
        { name: 'Container Orchestration', relevance: 0.67 }
      ],
      insights: [
        'Infrastructure automation is becoming important',
        'Cloud-first approach to deployment',
        'Monitoring and observability are key interests'
      ]
    }
  ];

  onMount(async () => {
    await loadPersonaData();
    await loadTagClusters();
    initializeVisualization();
  });

  async function loadPersonaData() {
    if (!$currentUser?.id || !$authToken) return;
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      const response = await api.get(`/persona/user/${$currentUser.id}`);
      personaData = response.data;
    } catch (e: any) {
      if (e.status !== 404) {
        console.error('Error loading persona:', e);
      }
    }
  }

  async function loadTagClusters() {
    loading = true;
    error = null;
    
    try {
      // In a real implementation, this would call the ML clustering API
      // For now, we'll use sample data enhanced with persona insights
      tagClusters = sampleClusters;
      
      if (personaData) {
        enhanceClustersWithPersona();
      }
    } catch (e: any) {
      error = e.message || 'Failed to load tag clusters';
      console.error('Error loading clusters:', e);
    } finally {
      loading = false;
    }
  }

  function enhanceClustersWithPersona() {
    if (!personaData?.technical_profile) return;
    
    const techProfile = personaData.technical_profile;
    const primaryLanguages = techProfile.primary_languages || [];
    const domains = techProfile.domains || [];
    
    // Adjust cluster strengths based on persona insights
    tagClusters = tagClusters.map(cluster => {
      let personalizedStrength = cluster.strength;
      
      // Boost strength if cluster aligns with user's primary languages
      const languageMatch = cluster.tags.some(tag => 
        primaryLanguages.some(lang => lang.toLowerCase().includes(tag.toLowerCase()))
      );
      if (languageMatch) personalizedStrength += 0.1;
      
      // Boost strength if cluster aligns with user's domains
      const domainMatch = domains.some(domain => 
        cluster.name.toLowerCase().includes(domain.toLowerCase())
      );
      if (domainMatch) personalizedStrength += 0.15;
      
      return {
        ...cluster,
        personalizedStrength: Math.min(1, personalizedStrength),
        personaMatch: languageMatch || domainMatch
      };
    });
    
    // Sort by personalized strength
    tagClusters.sort((a, b) => (b.personalizedStrength || 0) - (a.personalizedStrength || 0));
  }

  function initializeVisualization() {
    if (!clusterContainer || tagClusters.length === 0) return;
    
    const width = 800;
    const height = 600;
    
    // Create SVG
    const svg = d3.select(clusterContainer)
      .html('') // Clear existing content
      .append('svg')
      .attr('width', width)
      .attr('height', height);
    
    // Create force simulation
    const simulation = d3.forceSimulation(tagClusters)
      .force('charge', d3.forceManyBody().strength(-1000))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => Math.sqrt(d.size) * 2));
    
    // Create cluster nodes
    const nodes = svg.selectAll('.cluster-node')
      .data(tagClusters)
      .enter().append('g')
      .attr('class', 'cluster-node')
      .style('cursor', 'pointer')
      .on('click', (event, d) => selectCluster(d));
    
    // Add circles for clusters
    nodes.append('circle')
      .attr('r', d => Math.sqrt(d.size) * 1.5)
      .attr('fill', d => d.color)
      .attr('opacity', 0.7)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);
    
    // Add cluster names
    nodes.append('text')
      .text(d => d.name)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.3em')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('fill', '#fff');
    
    // Add connection lines
    const connections = [];
    tagClusters.forEach(cluster => {
      cluster.connections?.forEach(connectionId => {
        const target = tagClusters.find(c => c.id === connectionId);
        if (target) {
          connections.push({ source: cluster, target });
        }
      });
    });
    
    svg.selectAll('.connection-line')
      .data(connections)
      .enter().append('line')
      .attr('class', 'connection-line')
      .attr('stroke', '#666')
      .attr('stroke-width', 1)
      .attr('opacity', 0.4);
    
    // Update positions on simulation tick
    simulation.on('tick', () => {
      nodes.attr('transform', d => `translate(${d.x},${d.y})`);
      
      svg.selectAll('.connection-line')
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
    });
    
    clusterViz = { svg, simulation };
  }

  function selectCluster(cluster: any) {
    selectedCluster = cluster;
  }

  function closeClusterDetails() {
    selectedCluster = null;
  }

  async function runAnalysis() {
    loading = true;
    error = null;
    
    try {
      // Simulate running ML analysis
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // In a real implementation, this would call the clustering API
      // For now, we'll just refresh the current data
      await loadTagClusters();
      
      if (clusterViz) {
        initializeVisualization();
      }
    } catch (e: any) {
      error = e.message || 'Analysis failed';
    } finally {
      loading = false;
    }
  }

  function getClusterStatusColor(strength: number) {
    if (strength >= 0.8) return '#10B981'; // Strong
    if (strength >= 0.6) return '#F59E0B'; // Moderate
    return '#6B7280'; // Weak
  }

  function getClusterStatusLabel(strength: number) {
    if (strength >= 0.8) return 'Strong';
    if (strength >= 0.6) return 'Moderate';
    return 'Emerging';
  }
</script>

<div class="insights-page">
  <header class="insights-header">
    <div class="header-content">
      <div class="breadcrumb">
        <a href="/dreamscape">Dreamscape</a>
        <Icon name="chevron-right" size="small" />
        <span>Tag Insights</span>
      </div>
      
      <h1>Auto-Tag Clustering</h1>
      <p class="subtitle">ML-powered discovery of themes and cross-domain connections</p>
    </div>
    
    <div class="header-actions">
      <div class="analysis-mode">
        <label>Analysis Mode:</label>
        <select bind:value={analysisMode}>
          <option value="automatic">Automatic ML</option>
          <option value="manual">Manual Curation</option>
          <option value="hybrid">Hybrid Approach</option>
        </select>
      </div>
      
      <button class="analyze-button" on:click={runAnalysis} disabled={loading}>
        {#if loading}
          <div class="spinner"></div>
          Analyzing...
        {:else}
          <Icon name="cpu" />
          Run Analysis
        {/if}
      </button>
    </div>
  </header>

  <main class="insights-content">
    {#if loading && tagClusters.length === 0}
      <div class="loading-state">
        <div class="neural-loading">
          <div class="brain-pulse"></div>
          <p>Discovering tag patterns...</p>
        </div>
      </div>
    {:else if error}
      <div class="error-state">
        <Icon name="alert-circle" size="large" />
        <p>{error}</p>
        <button on:click={loadTagClusters}>Retry</button>
      </div>
    {:else}
      <div class="insights-dashboard">
        <!-- Cluster Overview Panel -->
        <div class="overview-panel">
          <div class="panel-header">
            <h2>
              <Icon name="layers" />
              Cluster Overview
            </h2>
            <div class="cluster-count">{tagClusters.length} clusters found</div>
          </div>
          
          <div class="panel-content">
            <div class="cluster-stats">
              <div class="stat-card">
                <div class="stat-icon">
                  <Icon name="trending-up" />
                </div>
                <div class="stat-content">
                  <h3>Strongest Cluster</h3>
                  <div class="stat-value">
                    {#if tagClusters.length > 0}
                      {Math.round((tagClusters[0].personalizedStrength || tagClusters[0].strength) * 100)}%
                    {:else}
                      --
                    {/if}
                  </div>
                  <div class="stat-label">
                    {tagClusters.length > 0 ? tagClusters[0].name : 'N/A'}
                  </div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">
                  <Icon name="hash" />
                </div>
                <div class="stat-content">
                  <h3>Total Tags</h3>
                  <div class="stat-value">
                    {tagClusters.reduce((sum, cluster) => sum + cluster.tags.length, 0)}
                  </div>
                  <div class="stat-label">Across all clusters</div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-icon">
                  <Icon name="git-merge" />
                </div>
                <div class="stat-content">
                  <h3>Connections</h3>
                  <div class="stat-value">
                    {tagClusters.reduce((sum, cluster) => sum + (cluster.connections?.length || 0), 0)}
                  </div>
                  <div class="stat-label">Cross-domain links</div>
                </div>
              </div>
            </div>
            
            <div class="cluster-list">
              {#each tagClusters as cluster}
                <div 
                  class="cluster-item"
                  class:selected={selectedCluster?.id === cluster.id}
                  class:persona-match={cluster.personaMatch}
                  on:click={() => selectCluster(cluster)}
                  on:keydown={(e) => e.key === 'Enter' && selectCluster(cluster)}
                  role="button"
                  tabindex="0"
                >
                  <div class="cluster-header">
                    <div class="cluster-color" style="background-color: {cluster.color}"></div>
                    <div class="cluster-info">
                      <h4>{cluster.name}</h4>
                      <div class="cluster-metadata">
                        <span class="tag-count">{cluster.tags.length} tags</span>
                        <span class="cluster-strength" style="color: {getClusterStatusColor(cluster.personalizedStrength || cluster.strength)}">
                          {getClusterStatusLabel(cluster.personalizedStrength || cluster.strength)}
                        </span>
                        {#if cluster.personaMatch}
                          <span class="persona-badge">
                            <Icon name="user-check" size="small" />
                            Persona Match
                          </span>
                        {/if}
                      </div>
                    </div>
                  </div>
                  
                  <div class="cluster-preview">
                    <div class="tag-preview">
                      {#each cluster.tags.slice(0, 4) as tag}
                        <span class="tag-chip">{tag}</span>
                      {/each}
                      {#if cluster.tags.length > 4}
                        <span class="tag-more">+{cluster.tags.length - 4} more</span>
                      {/if}
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>

        <!-- Visualization Panel -->
        <div class="visualization-panel">
          <div class="panel-header">
            <h2>
              <Icon name="share-2" />
              Cluster Network
            </h2>
            <div class="viz-controls">
              <button class="viz-button">
                <Icon name="maximize" size="small" />
                Fullscreen
              </button>
            </div>
          </div>
          
          <div class="panel-content">
            <div class="cluster-visualization" bind:this={clusterContainer}>
              {#if !clusterViz}
                <div class="viz-placeholder">
                  <Icon name="share-2" size="large" />
                  <p>Cluster visualization will appear here</p>
                </div>
              {/if}
            </div>
          </div>
        </div>

        <!-- Cluster Details Panel -->
        {#if selectedCluster}
          <div class="details-panel">
            <div class="panel-header">
              <h2>
                <div class="cluster-color-small" style="background-color: {selectedCluster.color}"></div>
                {selectedCluster.name}
              </h2>
              <button class="close-button" on:click={closeClusterDetails}>
                <Icon name="x" size="small" />
              </button>
            </div>
            
            <div class="panel-content">
              <div class="cluster-metrics">
                <div class="metric">
                  <span class="metric-label">Strength</span>
                  <span class="metric-value">
                    {Math.round((selectedCluster.personalizedStrength || selectedCluster.strength) * 100)}%
                  </span>
                </div>
                <div class="metric">
                  <span class="metric-label">Size</span>
                  <span class="metric-value">{selectedCluster.size} items</span>
                </div>
                <div class="metric">
                  <span class="metric-label">Connections</span>
                  <span class="metric-value">{selectedCluster.connections?.length || 0}</span>
                </div>
              </div>
              
              <div class="cluster-section">
                <h4>Tags in this cluster</h4>
                <div class="full-tag-list">
                  {#each selectedCluster.tags as tag}
                    <span class="tag-chip-large">{tag}</span>
                  {/each}
                </div>
              </div>
              
              {#if selectedCluster.connections?.length > 0}
                <div class="cluster-section">
                  <h4>Connected clusters</h4>
                  <div class="connection-list">
                    {#each selectedCluster.connections as connectionId}
                      {@const connectedCluster = tagClusters.find(c => c.id === connectionId)}
                      {#if connectedCluster}
                        <div class="connection-item" on:click={() => selectCluster(connectedCluster)}>
                          <div class="cluster-color-small" style="background-color: {connectedCluster.color}"></div>
                          <span>{connectedCluster.name}</span>
                        </div>
                      {/if}
                    {/each}
                  </div>
                </div>
              {/if}
              
              {#if selectedCluster.projects?.length > 0}
                <div class="cluster-section">
                  <h4>Related projects</h4>
                  <div class="project-list">
                    {#each selectedCluster.projects as project}
                      <div class="project-item">
                        <div class="project-info">
                          <span class="project-name">{project.name}</span>
                          <div class="relevance-bar">
                            <div class="relevance-fill" style="width: {project.relevance * 100}%"></div>
                          </div>
                        </div>
                        <span class="relevance-score">{Math.round(project.relevance * 100)}%</span>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
              
              {#if selectedCluster.insights?.length > 0}
                <div class="cluster-section">
                  <h4>AI Insights</h4>
                  <div class="insights-list">
                    {#each selectedCluster.insights as insight}
                      <div class="insight-item">
                        <Icon name="lightbulb" size="small" />
                        <p>{insight}</p>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </main>
</div>

<style>
  .insights-page {
    min-height: 100vh;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  /* Header */
  .insights-header {
    background: rgba(0, 0, 0, 0.4);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    padding: 2rem;
  }

  .header-content {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 0.5rem;
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

  .insights-header h1 {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, var(--neural-green), var(--accent-red));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-top: 1rem;
  }

  .analysis-mode {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .analysis-mode label {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .analysis-mode select {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    padding: 0.5rem;
    border-radius: var(--radius);
  }

  .analyze-button {
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

  .analyze-button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 255, 100, 0.4);
  }

  .analyze-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  /* Main Content */
  .insights-content {
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

  /* Dashboard Layout */
  .insights-dashboard {
    display: grid;
    grid-template-columns: 400px 1fr;
    gap: 2rem;
    grid-template-areas: 
      "overview visualization"
      "details visualization";
  }

  /* Panel Styles */
  .overview-panel,
  .visualization-panel,
  .details-panel {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(20px);
    overflow: hidden;
  }

  .overview-panel {
    grid-area: overview;
  }

  .visualization-panel {
    grid-area: visualization;
  }

  .details-panel {
    grid-area: details;
    max-height: 600px;
    overflow-y: auto;
  }

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

  .cluster-count {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .panel-content {
    padding: 1.5rem;
  }

  /* Cluster Stats */
  .cluster-stats {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    transition: all var(--transition-base);
  }

  .stat-card:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  .stat-icon {
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

  .stat-content h3 {
    margin: 0 0 0.25rem;
    color: var(--text-secondary);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  .stat-label {
    color: var(--text-secondary);
    font-size: 0.7rem;
  }

  /* Cluster List */
  .cluster-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .cluster-item {
    padding: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
  }

  .cluster-item:hover,
  .cluster-item.selected {
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  }

  .cluster-item.persona-match {
    border-color: var(--neural-green);
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.05);
  }

  .cluster-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.75rem;
  }

  .cluster-color {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .cluster-color-small {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .cluster-info h4 {
    margin: 0 0 0.25rem;
    color: var(--text-primary);
    font-size: 1rem;
  }

  .cluster-metadata {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .cluster-strength {
    font-weight: 600;
  }

  .persona-badge {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.2);
    color: var(--neural-green);
    border-radius: var(--radius);
    font-size: 0.7rem;
    font-weight: 600;
  }

  .cluster-preview {
    margin-top: 0.5rem;
  }

  .tag-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .tag-chip {
    padding: 0.25rem 0.5rem;
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-secondary);
    border-radius: var(--radius);
    font-size: 0.7rem;
  }

  .tag-more {
    padding: 0.25rem 0.5rem;
    color: var(--text-secondary);
    font-size: 0.7rem;
    font-style: italic;
  }

  /* Visualization */
  .viz-controls {
    display: flex;
    gap: 0.5rem;
  }

  .viz-button {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-secondary);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
  }

  .viz-button:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
  }

  .cluster-visualization {
    width: 100%;
    height: 600px;
    border-radius: var(--radius);
    overflow: hidden;
    background: rgba(0, 0, 0, 0.2);
  }

  .viz-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
  }

  /* Cluster Details */
  .close-button {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.5rem;
    border-radius: var(--radius);
    transition: all var(--transition-base);
  }

  .close-button:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
  }

  .cluster-metrics {
    display: flex;
    justify-content: space-between;
    margin-bottom: 2rem;
  }

  .metric {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .metric-label {
    color: var(--text-secondary);
    font-size: 0.8rem;
    margin-bottom: 0.25rem;
  }

  .metric-value {
    color: var(--text-primary);
    font-size: 1.2rem;
    font-weight: 600;
  }

  .cluster-section {
    margin-bottom: 2rem;
  }

  .cluster-section h4 {
    margin: 0 0 1rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .full-tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tag-chip-large {
    padding: 0.5rem 0.75rem;
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    border-radius: var(--radius);
    font-size: 0.8rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .connection-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .connection-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
  }

  .connection-item:hover {
    background: rgba(255, 255, 255, 0.08);
  }

  .project-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .project-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: var(--radius);
  }

  .project-info {
    flex: 1;
    margin-right: 1rem;
  }

  .project-name {
    display: block;
    color: var(--text-primary);
    font-weight: 500;
    margin-bottom: 0.25rem;
  }

  .relevance-bar {
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
  }

  .relevance-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--neural-green), #00C851);
    transition: width 0.5s ease;
  }

  .relevance-score {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-family: var(--font-mono);
  }

  .insights-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .insight-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: var(--radius);
    border-left: 3px solid var(--neural-green);
  }

  .insight-item p {
    margin: 0;
    color: var(--text-primary);
    line-height: 1.5;
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
  @media (max-width: 1200px) {
    .insights-dashboard {
      grid-template-columns: 1fr;
      grid-template-areas: 
        "overview"
        "visualization"
        "details";
    }

    .cluster-visualization {
      height: 400px;
    }
  }

  @media (max-width: 768px) {
    .insights-header,
    .insights-content {
      padding: 1rem;
    }

    .header-actions {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .cluster-stats {
      gap: 0.75rem;
    }

    .cluster-metrics {
      flex-direction: column;
      gap: 1rem;
    }
  }
</style>