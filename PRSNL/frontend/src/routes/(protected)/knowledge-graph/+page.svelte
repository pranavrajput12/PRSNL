<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import * as d3 from 'd3';
  import { getApiClient } from '$lib/api/client';
  import { currentUser, authToken } from '$lib/stores/unified-auth';
  import Icon from '$lib/components/Icon.svelte';
  import type { GraphNode, GraphEdge } from '$lib/types/knowledge-graph';
  
  // State
  let container: HTMLDivElement;
  let svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
  let simulation: d3.Simulation<GraphNode, GraphEdge>;
  
  let loading = true;
  let error: string | null = null;
  let graphData: { nodes: GraphNode[], edges: GraphEdge[], metadata: any } | null = null;
  let personaData: any = null;
  let personaEnhanced = false;
  
  // Controls
  let selectedNode: GraphNode | null = null;
  let hoveredNode: GraphNode | null = null;
  let searchQuery = '';
  let filterType = 'all';
  let depthLevel = 2;
  let showLabels = true;
  let zoomLevel = 1;
  
  // Graph dimensions
  let width = 1200;
  let height = 800;
  
  // Color scheme based on content types
  const typeColors = {
    article: '#3B82F6',
    video: '#EF4444', 
    code: '#10B981',
    recipe: '#F59E0B',
    bookmark: '#8B5CF6',
    document: '#6366F1',
    repository: '#14B8A6',
    conversation: '#EC4899',
    default: '#6B7280'
  };
  
  // Relationship colors
  const relationshipColors = {
    extends: '#10B981',
    related: '#3B82F6',
    prerequisite: '#F59E0B',
    contradicts: '#EF4444',
    implements: '#8B5CF6',
    references: '#6B7280',
    part_of: '#14B8A6',
    alternative: '#EC4899',
    duplicate: '#DC2626'
  };
  
  onMount(() => {
    // Set up container dimensions
    const rect = container.getBoundingClientRect();
    width = rect.width;
    height = rect.height || 800;
    
    // Initialize D3 SVG
    initializeSvg();
    
    // Load persona data first, then graph data
    loadPersonaData().then(() => {
      loadGraphData();
    });
    
    // Handle window resize
    window.addEventListener('resize', handleResize);
  });
  
  onDestroy(() => {
    window.removeEventListener('resize', handleResize);
    if (simulation) {
      simulation.stop();
    }
  });
  
  function initializeSvg() {
    svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);
    
    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        svg.select('.graph-container')
          .attr('transform', event.transform);
        zoomLevel = event.transform.k;
      });
    
    svg.call(zoom as any);
    
    // Add container group for zooming
    svg.append('g').attr('class', 'graph-container');
    
    // Add arrow markers for directed edges
    svg.append('defs').selectAll('marker')
      .data(Object.keys(relationshipColors))
      .enter().append('marker')
      .attr('id', d => `arrow-${d}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 30)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', d => relationshipColors[d as keyof typeof relationshipColors]);
  }
  
  async function loadPersonaData() {
    if (!$currentUser?.id || !$authToken) return;
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      const response = await api.get(`/persona/user/${$currentUser.id}`);
      personaData = response.data;
      console.log('Loaded persona data for knowledge graph enhancement');
    } catch (e: any) {
      if (e.status !== 404) {
        console.error('Error loading persona data:', e);
      }
      // 404 is expected if no persona exists yet
    }
  }
  
  async function loadGraphData(itemId?: string) {
    loading = true;
    error = null;
    
    if (!$authToken) {
      error = 'Authentication required';
      loading = false;
      return;
    }
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      
      let response;
      if (itemId) {
        // Load graph centered on specific item
        response = await api.get(`/knowledge-graph/visual/${itemId}`, {
          params: { depth: depthLevel, limit: 100 }
        });
      } else {
        // Load full graph
        response = await api.get('/knowledge-graph/visual/full', {
          params: {
            content_type: filterType !== 'all' ? filterType : undefined,
            limit: 200,
            threshold: 0.7
          }
        });
      }
      
      graphData = response.data;
      
      // Enhance graph with persona insights if available
      if (personaData) {
        enhanceGraphWithPersona();
      }
      
      renderGraph();
    } catch (e: any) {
      error = e.message || 'Failed to load knowledge graph';
      console.error('Error loading graph:', e);
    } finally {
      loading = false;
    }
  }
  
  function renderGraph() {
    if (!graphData || !svg) return;
    
    const container = svg.select('.graph-container');
    
    // Clear existing elements
    container.selectAll('*').remove();
    
    // Create force simulation
    simulation = d3.forceSimulation(graphData.nodes)
      .force('link', d3.forceLink(graphData.edges)
        .id((d: any) => d.id)
        .distance(d => 100 / (d.strength || 0.5)))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));
    
    // Add edges
    const link = container.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(graphData.edges)
      .enter().append('line')
      .attr('stroke', d => relationshipColors[d.relationship as keyof typeof relationshipColors] || '#999')
      .attr('stroke-opacity', d => d.strength)
      .attr('stroke-width', d => Math.sqrt(d.strength * 4))
      .attr('marker-end', d => `url(#arrow-${d.relationship})`);
    
    // Add edge labels
    const linkLabel = container.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(graphData.edges)
      .enter().append('text')
      .attr('font-size', 10)
      .attr('fill', '#666')
      .attr('text-anchor', 'middle')
      .text(d => d.relationship);
    
    // Add nodes
    const node = container.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(graphData.nodes)
      .enter().append('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any);
    
    // Add circles
    node.append('circle')
      .attr('r', d => getPersonaEnhancedSize(d))
      .attr('fill', d => getPersonaEnhancedColor(d))
      .attr('stroke', '#fff')
      .attr('stroke-width', d => personaEnhanced && d.personaCategory !== 'normal' ? 3 : 2)
      .on('click', handleNodeClick)
      .on('mouseenter', handleNodeHover)
      .on('mouseleave', () => hoveredNode = null);
    
    // Add labels
    if (showLabels) {
      node.append('text')
        .attr('dx', 12)
        .attr('dy', 4)
        .text(d => d.title)
        .style('font-size', '12px')
        .style('pointer-events', 'none');
    }
    
    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      
      linkLabel
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2);
      
      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });
  }
  
  // D3 drag handlers
  function dragstarted(event: any, d: any) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  
  function dragged(event: any, d: any) {
    d.fx = event.x;
    d.fy = event.y;
  }
  
  function dragended(event: any, d: any) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }
  
  // Event handlers
  function handleNodeClick(event: MouseEvent, node: GraphNode) {
    selectedNode = node;
    // Load subgraph centered on this node
    loadGraphData(node.id);
  }
  
  function handleNodeHover(event: MouseEvent, node: GraphNode) {
    hoveredNode = node;
  }
  
  function handleResize() {
    const rect = container.getBoundingClientRect();
    width = rect.width;
    height = rect.height || 800;
    
    if (svg) {
      svg.attr('width', width).attr('height', height);
      if (simulation) {
        simulation.force('center', d3.forceCenter(width / 2, height / 2));
        simulation.alpha(0.3).restart();
      }
    }
  }
  
  function filterGraph() {
    loadGraphData(selectedNode?.id);
  }
  
  function resetView() {
    selectedNode = null;
    filterType = 'all';
    depthLevel = 2;
    loadGraphData();
  }
  
  function toggleLabels() {
    showLabels = !showLabels;
    renderGraph();
  }
  
  function enhanceGraphWithPersona() {
    if (!graphData || !personaData) return;
    
    personaEnhanced = true;
    
    // Extract persona insights
    const technicalProfile = personaData.technical_profile;
    const learningStyle = personaData.learning_style;
    const lifePhase = personaData.life_phase;
    
    // Primary interests from technical profile
    const primaryLanguages = technicalProfile?.primary_languages || [];
    const domains = technicalProfile?.domains || [];
    const preferredFormats = learningStyle?.preferred_formats || [];
    
    // Enhance nodes with persona-based importance
    graphData.nodes = graphData.nodes.map(node => {
      let personaRelevance = node.importance || 1;
      let personaCategory = 'normal';
      
      // Boost relevance based on technical profile matches
      if (node.title || node.summary) {
        const nodeText = `${node.title} ${node.summary}`.toLowerCase();
        
        // Check for language matches
        const languageMatch = primaryLanguages.some(lang => 
          nodeText.includes(lang.toLowerCase())
        );
        if (languageMatch) {
          personaRelevance += 0.3;
          personaCategory = 'technical-match';
        }
        
        // Check for domain matches
        const domainMatch = domains.some(domain => 
          nodeText.includes(domain.toLowerCase())
        );
        if (domainMatch) {
          personaRelevance += 0.2;
          personaCategory = personaCategory === 'technical-match' ? 'high-relevance' : 'domain-match';
        }
        
        // Check for learning format matches
        const formatMatch = preferredFormats.some(format => 
          nodeText.includes(format.toLowerCase()) || 
          (format === 'hands-on' && (nodeText.includes('tutorial') || nodeText.includes('practice'))) ||
          (format === 'visual' && (nodeText.includes('diagram') || nodeText.includes('chart')))
        );
        if (formatMatch) {
          personaRelevance += 0.15;
          personaCategory = personaCategory === 'normal' ? 'format-match' : personaCategory;
        }
      }
      
      // Life phase adjustments
      if (lifePhase === 'early_career' && (node.type === 'tutorial' || node.type === 'course')) {
        personaRelevance += 0.2;
      } else if (lifePhase === 'experienced' && (node.type === 'reference' || node.type === 'documentation')) {
        personaRelevance += 0.15;
      }
      
      return {
        ...node,
        personaRelevance: Math.min(3, personaRelevance), // Cap at 3x
        personaCategory,
        originalImportance: node.importance
      };
    });
    
    // Sort nodes by persona relevance for better layout
    graphData.nodes.sort((a, b) => (b.personaRelevance || 0) - (a.personaRelevance || 0));
    
    console.log('Enhanced graph with persona insights:', {
      totalNodes: graphData.nodes.length,
      highRelevanceNodes: graphData.nodes.filter(n => n.personaCategory === 'high-relevance').length,
      technicalMatches: graphData.nodes.filter(n => n.personaCategory === 'technical-match').length,
      domainMatches: graphData.nodes.filter(n => n.personaCategory === 'domain-match').length
    });
  }
  
  function getPersonaEnhancedColor(node: any) {
    if (!personaEnhanced) {
      return typeColors[node.type as keyof typeof typeColors] || typeColors.default;
    }
    
    switch (node.personaCategory) {
      case 'high-relevance': return '#00ff64'; // Bright green for high relevance
      case 'technical-match': return '#00d4ff'; // Bright blue for technical matches
      case 'domain-match': return '#ff6b00'; // Orange for domain matches
      case 'format-match': return '#ff00dd'; // Magenta for format matches
      default: return typeColors[node.type as keyof typeof typeColors] || typeColors.default;
    }
  }
  
  function getPersonaEnhancedSize(node: any) {
    if (!personaEnhanced) {
      return 10 + (node.importance || 1) * 5;
    }
    
    const baseSize = 10;
    const personaMultiplier = node.personaRelevance || 1;
    return baseSize + personaMultiplier * 8; // Larger size for more relevant nodes
  }
  
  function navigateToItem(itemId: string) {
    // Navigate to item detail page
    window.location.href = `/items/${itemId}`;
  }
  
  function togglePersonaEnhancement() {
    if (!personaData) {
      // Navigate to persona analysis if no data available
      window.location.href = '/dreamscape/analysis';
      return;
    }
    
    if (personaEnhanced) {
      // Disable persona enhancement
      personaEnhanced = false;
      // Reset node properties
      if (graphData) {
        graphData.nodes = graphData.nodes.map(node => ({
          ...node,
          importance: node.originalImportance || node.importance,
          personaRelevance: undefined,
          personaCategory: 'normal'
        }));
      }
    } else {
      // Enable persona enhancement
      enhanceGraphWithPersona();
    }
    
    // Re-render the graph
    renderGraph();
  }
</script>

<div class="knowledge-graph-page">
  <header class="graph-header">
    <div class="header-left">
      <h1>Knowledge Graph</h1>
      <p class="subtitle">Explore connections between your content</p>
    </div>
    
    <div class="header-controls">
      <div class="control-group">
        <label>
          <Icon name="filter" size="small" />
          <select bind:value={filterType} on:change={filterGraph}>
            <option value="all">All Types</option>
            <option value="article">Articles</option>
            <option value="video">Videos</option>
            <option value="code">Code</option>
            <option value="recipe">Recipes</option>
            <option value="bookmark">Bookmarks</option>
          </select>
        </label>
      </div>
      
      <div class="control-group">
        <label>
          <Icon name="git-branch" size="small" />
          <input 
            type="range" 
            min="1" 
            max="3" 
            bind:value={depthLevel}
            on:change={filterGraph}
          />
          <span>Depth: {depthLevel}</span>
        </label>
      </div>
      
      <button class="control-button" on:click={toggleLabels}>
        <Icon name={showLabels ? 'eye-off' : 'eye'} size="small" />
        {showLabels ? 'Hide' : 'Show'} Labels
      </button>
      
      <button class="control-button" on:click={resetView}>
        <Icon name="refresh-cw" size="small" />
        Reset
      </button>
      
      <button 
        class="control-button persona-toggle" 
        class:active={personaEnhanced}
        class:disabled={!personaData}
        on:click={togglePersonaEnhancement}
        title={personaData ? 'Toggle persona-based enhancement' : 'No persona data - click to analyze'}
      >
        <Icon name={personaEnhanced ? 'user-check' : 'user'} size="small" />
        {personaData ? 'Persona' : 'Analyze Me'}
      </button>
    </div>
  </header>
  
  <div class="graph-container" bind:this={container}>
    {#if loading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Building knowledge graph...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <Icon name="alert-circle" size="large" />
        <p>{error}</p>
        <button on:click={() => loadGraphData()}>Retry</button>
      </div>
    {/if}
  </div>
  
  {#if selectedNode}
    <div class="node-details">
      <div class="details-header">
        <h3>{selectedNode.title}</h3>
        <button class="close-button" on:click={() => selectedNode = null}>
          <Icon name="x" size="small" />
        </button>
      </div>
      
      <div class="details-content">
        <p class="node-type">
          <span class="type-badge" style="background-color: {typeColors[selectedNode.type as keyof typeof typeColors] || typeColors.default}">
            {selectedNode.type}
          </span>
        </p>
        
        {#if selectedNode.summary}
          <p class="node-summary">{selectedNode.summary}</p>
        {/if}
        
        {#if personaEnhanced && selectedNode.personaCategory !== 'normal'}
          <div class="persona-insights">
            <h4>Persona Insights</h4>
            <div class="persona-match-indicator">
              <div 
                class="persona-color-dot" 
                style="background-color: {getPersonaEnhancedColor(selectedNode)}"
              ></div>
              <span class="persona-match-label">
                {#if selectedNode.personaCategory === 'high-relevance'}
                  High Relevance Match
                {:else if selectedNode.personaCategory === 'technical-match'}
                  Technical Profile Match
                {:else if selectedNode.personaCategory === 'domain-match'}
                  Domain Expertise Match
                {:else if selectedNode.personaCategory === 'format-match'}
                  Learning Format Match
                {/if}
              </span>
            </div>
            {#if selectedNode.personaRelevance}
              <div class="relevance-score">
                Relevance Score: {Math.round(selectedNode.personaRelevance * 100)}%
              </div>
            {/if}
          </div>
        {/if}
        
        {#if selectedNode.tags?.length}
          <div class="node-tags">
            {#each selectedNode.tags as tag}
              <span class="tag">#{tag}</span>
            {/each}
          </div>
        {/if}
        
        <button class="view-button" on:click={() => navigateToItem(selectedNode.id)}>
          View Full Content
          <Icon name="arrow-right" size="small" />
        </button>
      </div>
    </div>
  {/if}
  
  {#if hoveredNode && hoveredNode !== selectedNode}
    <div class="tooltip" style="opacity: 1">
      <strong>{hoveredNode.title}</strong>
      <br>
      <span class="tooltip-type">{hoveredNode.type}</span>
    </div>
  {/if}
</div>

<style>
  .knowledge-graph-page {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--bg-primary);
    color: var(--text-primary);
  }
  
  .graph-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 2rem;
    background: rgba(0, 0, 0, 0.3);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .header-left h1 {
    margin: 0;
    font-size: 1.5rem;
    color: var(--neural-green);
  }
  
  .subtitle {
    margin: 0.25rem 0 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }
  
  .header-controls {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .control-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .control-group label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
  }
  
  .control-group select,
  .control-group input[type="range"] {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    padding: 0.5rem;
    border-radius: 4px;
  }
  
  .control-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .control-button:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }
  
  .persona-toggle.active {
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.2);
    border-color: var(--neural-green);
    color: var(--neural-green);
  }
  
  .persona-toggle.disabled {
    background: rgba(220, 20, 60, 0.2);
    border-color: var(--accent-red);
    color: var(--accent-red);
  }
  
  .persona-toggle.disabled:hover {
    background: rgba(220, 20, 60, 0.3);
    transform: translateY(-2px);
  }
  
  .graph-container {
    flex: 1;
    position: relative;
    overflow: hidden;
    background: radial-gradient(circle at 50% 50%, rgba(0, 255, 136, 0.05), transparent);
  }
  
  :global(.graph-container svg) {
    width: 100%;
    height: 100%;
  }
  
  :global(.node circle) {
    cursor: pointer;
    transition: all 0.2s;
  }
  
  :global(.node circle:hover) {
    r: 20;
    filter: brightness(1.2) drop-shadow(0 0 10px currentColor);
  }
  
  :global(.links line) {
    stroke-linecap: round;
  }
  
  .loading-state,
  .error-state {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    color: var(--text-secondary);
  }
  
  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(var(--neural-green-rgb), 0.3);
    border-top: 3px solid var(--neural-green);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .node-details {
    position: absolute;
    top: 2rem;
    right: 2rem;
    width: 300px;
    background: rgba(0, 0, 0, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
  }
  
  .details-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    margin-bottom: 1rem;
  }
  
  .details-header h3 {
    margin: 0;
    color: var(--neural-green);
  }
  
  .close-button {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0;
  }
  
  .type-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.8rem;
    color: white;
    text-transform: uppercase;
  }
  
  .node-summary {
    margin: 1rem 0;
    line-height: 1.5;
    color: var(--text-secondary);
  }
  
  .node-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 1rem 0;
  }
  
  .tag {
    padding: 0.25rem 0.5rem;
    background: rgba(var(--neural-green-rgb), 0.1);
    color: var(--neural-green);
    border-radius: 4px;
    font-size: 0.8rem;
  }
  
  .view-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.75rem;
    background: var(--neural-green);
    color: #000;
    border: none;
    border-radius: 4px;
    font-weight: 600;
    cursor: pointer;
    justify-content: center;
    transition: all 0.2s;
  }
  
  .view-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(var(--neural-green-rgb), 0.3);
  }
  
  .tooltip {
    position: absolute;
    padding: 0.5rem 1rem;
    background: rgba(0, 0, 0, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    pointer-events: none;
    z-index: 1000;
    font-size: 0.9rem;
  }
  
  .tooltip-type {
    color: var(--text-secondary);
    font-size: 0.8rem;
  }
  
  @media (max-width: 768px) {
    .graph-header {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }
    
    .header-controls {
      flex-wrap: wrap;
    }
    
    .node-details {
      width: calc(100% - 2rem);
      left: 1rem;
      right: 1rem;
    }
  }
</style>