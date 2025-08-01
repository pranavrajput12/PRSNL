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
  let selectedNodes: Set<string> = new Set(); // Multi-selection support
  let hoveredNode: GraphNode | null = null;
  let searchQuery = '';
  let filterType = 'all';
  let relationshipFilter = 'all';
  let minConfidenceFilter = 0.5;
  let depthLevel = 2;
  let showLabels = true;
  let zoomLevel = 1;
  let searchDebounceTimer: number;
  let filteredGraphData: { nodes: GraphNode[], edges: GraphEdge[], metadata: any } | null = null;
  let hoveredEdge: GraphEdge | null = null;
  let mousePosition = { x: 0, y: 0 };
  
  // Selection modes
  let selectionMode: 'single' | 'multi' = 'single';
  let isCtrlPressed = false;
  
  // Relationship creation
  let showRelationshipModal = false;
  let relationshipType = 'related_to';
  let relationshipConfidence = 0.8;
  let relationshipContext = '';
  let creatingRelationship = false;
  
  // Relationship strength visualization
  let showRelationshipStrength = true;
  let relationshipOpacityMode = 'confidence'; // 'confidence' | 'strength' | 'uniform'
  
  // Knowledge path discovery
  let showPathDiscovery = false;
  let pathStartNode: GraphNode | null = null;
  let pathEndNode: GraphNode | null = null;
  let discoveredPaths: any[] = [];
  let discoveringPaths = false;
  let pathDiscoveryError: string | null = null;

  // Relationship suggestions
  let showRelationshipSuggestions = false;
  let relationshipSuggestions: any[] = [];
  let loadingSuggestions = false;
  let suggestionsError: string | null = null;
  let suggestionConfidenceThreshold = 0.5;
  let suggestionLimit = 10;
  let selectedSuggestionEntity: GraphNode | null = null;

  // Knowledge gap analysis
  let showGapAnalysis = false;
  let gapAnalysisData: any = null;
  let loadingGapAnalysis = false;
  let gapAnalysisError: string | null = null;
  let analysisDepth = 'standard';
  let minSeverity = 'medium';

  // Semantic clustering
  let showSemanticClustering = false;
  let clusteringData: any = null;
  let loadingClustering = false;
  let clusteringError: string | null = null;
  let clusteringAlgorithm = 'semantic';
  let minClusterSize = 3;
  let maxClusters = 8;
  let clusterMinConfidence = 0.5;
  let selectedCluster: any = null;
  let clusterHighlighted = false;

  // Analytics dashboard
  let showAnalyticsDashboard = false;
  let analyticsData: any = null;
  let loadingAnalytics = false;
  let analyticsError: string | null = null;
  
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
    
    // Add keyboard event listeners for multi-selection
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
  });
  
  onDestroy(() => {
    window.removeEventListener('resize', handleResize);
    window.removeEventListener('keydown', handleKeyDown);
    window.removeEventListener('keyup', handleKeyUp);
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
        // Load graph centered on specific item using unified API
        response = await api.get(`/unified-knowledge-graph/visual/${itemId}`, {
          params: { 
            depth: depthLevel, 
            limit: 100, 
            min_confidence: minConfidenceFilter 
          }
        });
      } else {
        // Load full graph using unified API
        response = await api.get('/unified-knowledge-graph/visual/full', {
          params: {
            entity_type: filterType !== 'all' ? filterType : undefined,
            relationship_type: relationshipFilter !== 'all' ? relationshipFilter : undefined,
            limit: 200,
            min_confidence: minConfidenceFilter
          }
        });
      }
      
      // Transform the unified API response to match existing graph structure
      graphData = {
        nodes: response.data.nodes.map(node => ({
          id: node.id,
          title: node.title,
          type: node.content_type || node.type || 'default', // Use content_type for styling
          entity_type: node.type, // Keep entity type for reference
          summary: node.summary,
          confidence: node.confidence,
          created_at: node.created_at,
          metadata: node.metadata || {},
          // Add D3-specific properties
          x: undefined,
          y: undefined,
          fx: null,
          fy: null
        })),
        edges: response.data.edges.map(edge => ({
          source: edge.source,
          target: edge.target,
          relationship: edge.relationship,
          strength: edge.strength || 1.0,
          confidence: edge.confidence
        })),
        metadata: response.data.metadata || {}
      };
      
      console.log(`Loaded unified knowledge graph: ${graphData.nodes.length} nodes, ${graphData.edges.length} edges`);
      
      // Enhance graph with persona insights if available
      if (personaData) {
        enhanceGraphWithPersona();
      }
      
      // Apply search filtering if there's a search query
      applySearchFilter();
      
      renderGraph();
    } catch (e: any) {
      error = e.message || 'Failed to load unified knowledge graph';
      console.error('Error loading unified graph:', e);
    } finally {
      loading = false;
    }
  }
  
  function applySearchFilter() {
    if (!graphData) {
      filteredGraphData = null;
      return;
    }
    
    if (!searchQuery.trim()) {
      filteredGraphData = graphData;
      return;
    }
    
    const query = searchQuery.toLowerCase().trim();
    
    // Filter nodes based on search query
    const filteredNodes = graphData.nodes.filter(node => {
      return (
        node.title.toLowerCase().includes(query) ||
        node.type.toLowerCase().includes(query) ||
        (node.summary && node.summary.toLowerCase().includes(query)) ||
        (node.entity_type && node.entity_type.toLowerCase().includes(query))
      );
    });
    
    // Get IDs of filtered nodes
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    
    // Filter edges to only include connections between visible nodes
    const filteredEdges = graphData.edges.filter(edge => 
      nodeIds.has(edge.source as string) && nodeIds.has(edge.target as string)
    );
    
    filteredGraphData = {
      nodes: filteredNodes,
      edges: filteredEdges,
      metadata: {
        ...graphData.metadata,
        filtered: true,
        search_query: query,
        original_nodes: graphData.nodes.length,
        original_edges: graphData.edges.length,
        filtered_nodes: filteredNodes.length,
        filtered_edges: filteredEdges.length
      }
    };
  }
  
  function handleSearchInput() {
    // Debounce search to avoid excessive filtering
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      applySearchFilter();
      renderGraph();
    }, 300);
  }
  
  function clearSearch() {
    searchQuery = '';
    applySearchFilter();
    renderGraph();
  }
  
  function renderGraph() {
    if (!graphData || !svg) return;
    
    // Use filtered data if available, otherwise use original data
    const dataToRender = filteredGraphData || graphData;
    
    const container = svg.select('.graph-container');
    
    // Clear existing elements
    container.selectAll('*').remove();
    
    // Create force simulation
    simulation = d3.forceSimulation(dataToRender.nodes)
      .force('link', d3.forceLink(dataToRender.edges)
        .id((d: any) => d.id)
        .distance(d => 100 / (d.strength || 0.5)))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));
    
    // Add edges with enhanced strength visualization
    const link = container.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(dataToRender.edges)
      .enter().append('line')
      .attr('stroke', d => relationshipColors[d.relationship as keyof typeof relationshipColors] || '#999')
      .attr('stroke-opacity', d => {
        if (!showRelationshipStrength) return 0.6;
        switch (relationshipOpacityMode) {
          case 'confidence': return d.confidence || 0.7;
          case 'strength': return d.strength || 1.0;
          default: return 0.6;
        }
      })
      .attr('stroke-width', d => {
        if (!showRelationshipStrength) return 2;
        const baseWidth = 1;
        const maxWidth = 6;
        const strength = d.strength || 1.0;
        const confidence = d.confidence || 0.7;
        const combinedStrength = (strength + confidence) / 2;
        return baseWidth + (combinedStrength * (maxWidth - baseWidth));
      })
      .attr('stroke-dasharray', d => {
        // Use dashed lines for low confidence relationships
        const confidence = d.confidence || 0.7;
        return confidence < 0.5 ? '4,2' : 'none';
      })
      .attr('marker-end', d => `url(#arrow-${d.relationship})`)
      .style('filter', d => {
        // Add glow effect for high-strength relationships
        if (!showRelationshipStrength) return 'none';
        const strength = d.strength || 1.0;
        const confidence = d.confidence || 0.7;
        if (strength > 0.8 && confidence > 0.8) {
          return 'drop-shadow(0 0 3px currentColor)';
        }
        return 'none';
      })
      .on('mouseenter', handleEdgeHover)
      .on('mouseleave', () => hoveredEdge = null)
      .on('mousemove', (event, d) => {
        if (hoveredEdge === d) updateMousePosition(event);
      });
    
    // Add edge labels
    const linkLabel = container.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(dataToRender.edges)
      .enter().append('text')
      .attr('font-size', 10)
      .attr('fill', '#666')
      .attr('text-anchor', 'middle')
      .text(d => d.relationship);
    
    // Add nodes
    const node = container.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(dataToRender.nodes)
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
      .on('mouseleave', () => hoveredNode = null)
      .on('mousemove', (event, d) => {
        if (hoveredNode === d) updateMousePosition(event);
      });
    
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
    
    // Apply initial selection visualization
    updateSelectedNodesVisualization();
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
  
  // Keyboard event handlers
  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Control' || event.key === 'Meta') {
      isCtrlPressed = true;
    }
    if (event.key === 'Escape') {
      // Clear all selections
      selectedNodes.clear();
      selectedNode = null;
      updateSelectedNodesVisualization();
    }
  }
  
  function handleKeyUp(event: KeyboardEvent) {
    if (event.key === 'Control' || event.key === 'Meta') {
      isCtrlPressed = false;
    }
  }
  
  // Event handlers
  function handleNodeClick(event: MouseEvent, node: GraphNode) {
    event.stopPropagation();
    
    if (selectionMode === 'multi' && isCtrlPressed) {
      // Multi-selection mode with Ctrl held
      if (selectedNodes.has(node.id)) {
        selectedNodes.delete(node.id);
      } else {
        selectedNodes.add(node.id);
      }
      selectedNodes = selectedNodes; // Trigger reactivity
      updateSelectedNodesVisualization();
    } else {
      // Single selection mode
      selectedNode = node;
      selectedNodes.clear();
      selectedNodes.add(node.id);
      selectedNodes = selectedNodes; // Trigger reactivity
      updateSelectedNodesVisualization();
      
      // Load subgraph centered on this node
      loadGraphData(node.id);
    }
  }
  
  function handleNodeHover(event: MouseEvent, node: GraphNode) {
    hoveredNode = node;
    updateMousePosition(event);
  }
  
  function handleEdgeHover(event: MouseEvent, edge: GraphEdge) {
    hoveredEdge = edge;
    updateMousePosition(event);
  }
  
  function updateMousePosition(event: MouseEvent) {
    mousePosition = { x: event.clientX, y: event.clientY };
  }
  
  function toggleRelationshipStrength() {
    showRelationshipStrength = !showRelationshipStrength;
    renderGraph();
  }
  
  function cycleOpacityMode() {
    const modes = ['confidence', 'strength', 'uniform'];
    const currentIndex = modes.indexOf(relationshipOpacityMode);
    relationshipOpacityMode = modes[(currentIndex + 1) % modes.length];
    renderGraph();
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
    selectedNodes.clear();
    selectedNodes = selectedNodes; // Trigger reactivity
    searchQuery = '';
    filterType = 'all';
    relationshipFilter = 'all';
    minConfidenceFilter = 0.5;
    depthLevel = 2;
    updateSelectedNodesVisualization();
    loadGraphData();
  }
  
  function updateSelectedNodesVisualization() {
    if (!svg) return;
    
    // Update node styles based on selection
    svg.selectAll('.node circle')
      .style('stroke', (d: any) => {
        if (selectedNodes.has(d.id)) {
          return '#00ff64'; // Bright green for selected
        } else if (hoveredNode && hoveredNode.id === d.id) {
          return '#ffffff'; // White for hovered
        }
        return '#fff'; // Default white
      })
      .style('stroke-width', (d: any) => {
        if (selectedNodes.has(d.id)) {
          return 4; // Thick stroke for selected
        } else if (personaEnhanced && d.personaCategory !== 'normal') {
          return 3;
        }
        return 2; // Default
      });
  }
  
  function toggleSelectionMode() {
    selectionMode = selectionMode === 'single' ? 'multi' : 'single';
    if (selectionMode === 'single') {
      // Clear multi-selection when switching to single mode
      if (selectedNodes.size > 1) {
        const firstSelected = Array.from(selectedNodes)[0];
        selectedNodes.clear();
        if (firstSelected) {
          selectedNodes.add(firstSelected);
        }
        selectedNodes = selectedNodes; // Trigger reactivity
        updateSelectedNodesVisualization();
      }
    }
  }
  
  function clearSelection() {
    selectedNodes.clear();
    selectedNode = null;
    selectedNodes = selectedNodes; // Trigger reactivity
    updateSelectedNodesVisualization();
  }
  
  function createRelationshipBetweenSelected() {
    if (selectedNodes.size !== 2) {
      alert('Please select exactly 2 nodes to create a relationship');
      return;
    }
    
    showRelationshipModal = true;
  }
  
  function startPathDiscovery() {
    if (selectedNodes.size !== 2) {
      alert('Please select exactly 2 nodes to discover paths between them');
      return;
    }
    
    const nodeIds = Array.from(selectedNodes);
    pathStartNode = graphData?.nodes.find(n => n.id === nodeIds[0]) || null;
    pathEndNode = graphData?.nodes.find(n => n.id === nodeIds[1]) || null;
    
    showPathDiscovery = true;
    discoverKnowledgePaths();
  }
  
  async function discoverKnowledgePaths() {
    if (!pathStartNode || !pathEndNode || !$authToken) return;
    
    discoveringPaths = true;
    pathDiscoveryError = null;
    discoveredPaths = [];
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      
      const response = await api.post('/unified-knowledge-graph/paths/discover', {
        start_entity_id: pathStartNode.id,
        end_entity_id: pathEndNode.id,
        max_depth: 5,
        min_confidence: 0.5
      });
      
      discoveredPaths = response.data.paths || [];
      console.log('✅ Discovered knowledge paths:', discoveredPaths);
      
    } catch (e: any) {
      console.error('❌ Error discovering paths:', e);
      pathDiscoveryError = e.response?.data?.detail || e.message || 'Failed to discover paths';
    } finally {
      discoveringPaths = false;
    }
  }
  
  function closePathDiscovery() {
    showPathDiscovery = false;
    pathStartNode = null;
    pathEndNode = null;
    discoveredPaths = [];
    pathDiscoveryError = null;
  }

  // Relationship Suggestions Functions
  async function loadRelationshipSuggestions(entityId: string | null = null) {
    if (!$authToken) return;
    
    loadingSuggestions = true;
    suggestionsError = null;
    relationshipSuggestions = [];
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      
      const requestBody: any = {
        limit: suggestionLimit,
        min_confidence: suggestionConfidenceThreshold
      };
      
      if (entityId) {
        requestBody.entity_id = entityId;
      }
      
      const response = await api.post('/unified-knowledge-graph/relationships/suggest', requestBody);
      
      relationshipSuggestions = response.data.suggestions || [];
      console.log('✅ Loaded relationship suggestions:', relationshipSuggestions);
      
    } catch (e: any) {
      console.error('❌ Error loading relationship suggestions:', e);
      suggestionsError = e.response?.data?.detail || e.message || 'Failed to load suggestions';
    } finally {
      loadingSuggestions = false;
    }
  }

  function openRelationshipSuggestions(entity: GraphNode | null = null) {
    selectedSuggestionEntity = entity;
    showRelationshipSuggestions = true;
    loadRelationshipSuggestions(entity?.id);
  }

  function closeRelationshipSuggestions() {
    showRelationshipSuggestions = false;
    selectedSuggestionEntity = null;
    relationshipSuggestions = [];
    suggestionsError = null;
  }

  async function applySuggestion(suggestion: any) {
    if (!$authToken) return;
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      
      const response = await api.post('/unified-knowledge-graph/relationships', {
        source_entity_id: suggestion.source_entity_id,
        target_entity_id: suggestion.target_entity_id,
        relationship_type: suggestion.suggested_relationship,
        confidence_score: suggestion.confidence_score,
        context: `AI suggested: ${suggestion.reasoning}`
      });
      
      console.log('✅ Applied relationship suggestion:', response.data);
      
      // Remove applied suggestion from list
      relationshipSuggestions = relationshipSuggestions.filter(s => 
        s.source_entity_id !== suggestion.source_entity_id || 
        s.target_entity_id !== suggestion.target_entity_id ||
        s.suggested_relationship !== suggestion.suggested_relationship
      );
      
      // Reload graph to show new relationship
      await loadGraphData();
      
    } catch (e: any) {
      console.error('❌ Error applying suggestion:', e);
      suggestionsError = e.response?.data?.detail || e.message || 'Failed to apply suggestion';
    }
  }

  // Knowledge Gap Analysis Functions
  async function runGapAnalysis() {
    if (!$authToken) return;
    
    loadingGapAnalysis = true;
    gapAnalysisError = null;
    gapAnalysisData = null;
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      
      const response = await api.post('/unified-knowledge-graph/analysis/gaps', {
        analysis_depth: analysisDepth,
        min_severity: minSeverity,
        include_suggestions: true
      });
      
      gapAnalysisData = response.data;
      console.log('✅ Gap analysis completed:', gapAnalysisData);
      
    } catch (e: any) {
      console.error('❌ Error running gap analysis:', e);
      gapAnalysisError = e.response?.data?.detail || e.message || 'Failed to analyze knowledge gaps';
    } finally {
      loadingGapAnalysis = false;
    }
  }

  async function runSemanticClustering() {
    if (!$authToken) return;
    
    loadingClustering = true;
    clusteringError = null;
    clusteringData = null;
    selectedCluster = null;
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      
      const response = await api.post('/unified-knowledge-graph/clustering/semantic', {
        clustering_algorithm: clusteringAlgorithm,
        min_cluster_size: minClusterSize,
        max_clusters: maxClusters,
        min_confidence: clusterMinConfidence,
        entity_types: filterType === 'all' ? null : [filterType]
      });
      
      clusteringData = response.data;
      console.log('✅ Semantic clustering completed:', clusteringData);
      
    } catch (e: any) {
      console.error('❌ Error running semantic clustering:', e);
      clusteringError = e.response?.data?.detail || e.message || 'Failed to perform semantic clustering';
    } finally {
      loadingClustering = false;
    }
  }

  function openSemanticClustering() {
    showSemanticClustering = true;
    if (!clusteringData) {
      runSemanticClustering();
    }
  }

  function highlightCluster(cluster: any) {
    selectedCluster = cluster;
    clusterHighlighted = true;
    
    // Highlight cluster entities in the graph
    const clusterEntityIds = new Set(cluster.entities.map((e: any) => e.id));
    
    // Update node highlights
    svg.selectAll('.node')
      .classed('cluster-highlighted', (d: any) => clusterEntityIds.has(d.id))
      .classed('cluster-dimmed', (d: any) => !clusterEntityIds.has(d.id));
    
    // Update edge highlights
    svg.selectAll('.edge')
      .classed('cluster-highlighted', (d: any) => 
        clusterEntityIds.has(d.source.id) && clusterEntityIds.has(d.target.id)
      )
      .classed('cluster-dimmed', (d: any) => 
        !clusterEntityIds.has(d.source.id) || !clusterEntityIds.has(d.target.id)
      );
  }

  function clearClusterHighlights() {
    selectedCluster = null;
    clusterHighlighted = false;
    
    // Clear highlights
    svg.selectAll('.node')
      .classed('cluster-highlighted', false)
      .classed('cluster-dimmed', false);
    
    svg.selectAll('.edge')
      .classed('cluster-highlighted', false)
      .classed('cluster-dimmed', false);
  }

  // Analytics Dashboard Functions
  async function loadAnalyticsDashboard() {
    if (!$authToken) return;
    
    loadingAnalytics = true;
    analyticsError = null;
    analyticsData = null;
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      
      // Load multiple analytics in parallel
      const [statsResponse, pathsData, suggestionsData, gapsData, clusteringData] = await Promise.all([
        api.get('/unified-knowledge-graph/stats'),
        // Run path discovery between random entities
        getRandomPathsAnalysis(api),
        // Get relationship suggestions sample
        api.post('/unified-knowledge-graph/relationships/suggest', {
          limit: 20,
          min_confidence: 0.6
        }),
        // Get gap analysis
        api.post('/unified-knowledge-graph/analysis/gaps', {
          analysis_depth: 'quick',
          min_severity: 'medium'
        }),
        // Get clustering data
        api.post('/unified-knowledge-graph/clustering/semantic', {
          clustering_algorithm: 'semantic',
          min_cluster_size: 3,
          max_clusters: 8,
          min_confidence: 0.5
        })
      ]);
      
      analyticsData = {
        stats: statsResponse.data,
        paths: pathsData,
        suggestions: suggestionsData.data,
        gaps: gapsData.data,
        clustering: clusteringData.data,
        timestamp: new Date().toISOString()
      };
      
      console.log('✅ Analytics dashboard loaded:', analyticsData);
      
    } catch (e: any) {
      console.error('❌ Error loading analytics:', e);
      analyticsError = e.response?.data?.detail || e.message || 'Failed to load analytics';
    } finally {
      loadingAnalytics = false;
    }
  }

  async function getRandomPathsAnalysis(api: any) {
    try {
      // Get a few random entities for path analysis
      if (!graphData?.nodes || graphData.nodes.length < 2) return null;
      
      const nodes = graphData.nodes;
      const randomPaths = [];
      
      // Try to find 3 random paths
      for (let i = 0; i < 3 && i < nodes.length - 1; i++) {
        const startIdx = Math.floor(Math.random() * nodes.length);
        const endIdx = Math.floor(Math.random() * nodes.length);
        
        if (startIdx !== endIdx) {
          try {
            const pathResponse = await api.post('/unified-knowledge-graph/paths/discover', {
              start_entity_id: nodes[startIdx].id,
              end_entity_id: nodes[endIdx].id,
              max_depth: 4,
              min_confidence: 0.5
            });
            
            if (pathResponse.data.paths.length > 0) {
              randomPaths.push({
                start: nodes[startIdx].title,
                end: nodes[endIdx].title,
                paths: pathResponse.data.paths.length,
                bestConfidence: pathResponse.data.paths[0]?.total_confidence || 0
              });
            }
          } catch (e) {
            // Skip failed path discoveries
          }
        }
      }
      
      return randomPaths;
    } catch (e) {
      return null;
    }
  }

  function openAnalyticsDashboard() {
    showAnalyticsDashboard = true;
    if (!analyticsData) {
      loadAnalyticsDashboard();
    }
  }

  function openGapAnalysis() {
    showGapAnalysis = true;
    if (!gapAnalysisData) {
      runGapAnalysis();
    }
  }

  function closeGapAnalysis() {
    showGapAnalysis = false;
    gapAnalysisData = null;
    gapAnalysisError = null;
  }

  function getSeverityColor(severity: string): string {
    switch (severity) {
      case 'critical': return '#dc2626';
      case 'high': return '#ea580c';
      case 'medium': return '#ca8a04';
      case 'low': return '#059669';
      default: return '#6b7280';
    }
  }

  function getSeverityIcon(severity: string): string {
    switch (severity) {
      case 'critical': return 'alert-triangle';
      case 'high': return 'alert-circle';
      case 'medium': return 'info';
      case 'low': return 'check-circle';
      default: return 'help-circle';
    }
  }
  
  function highlightPath(path: any) {
    // Highlight the path in the visualization
    if (!svg) return;
    
    // Reset all highlighting
    svg.selectAll('.node circle').style('stroke', '#fff').style('stroke-width', 2);
    svg.selectAll('.links line').style('stroke-opacity', 0.6);
    
    // Highlight path nodes
    const pathNodeIds = path.nodes.map((n: any) => n.entity_id);
    svg.selectAll('.node circle')
      .filter((d: any) => pathNodeIds.includes(d.id))
      .style('stroke', '#ff6b00')
      .style('stroke-width', 4);
    
    // Highlight path edges
    const pathEdges = path.edges;
    svg.selectAll('.links line')
      .filter((d: any) => {
        return pathEdges.some((edge: any) => 
          (edge.source_id === d.source.id && edge.target_id === d.target.id) ||
          (edge.source_id === d.target.id && edge.target_id === d.source.id)
        );
      })
      .style('stroke-opacity', 1.0)
      .style('stroke-width', 4);
  }
  
  function clearPathHighlight() {
    if (!svg) return;
    
    // Reset highlighting
    svg.selectAll('.node circle').style('stroke', '#fff').style('stroke-width', 2);
    svg.selectAll('.links line').style('stroke-opacity', 0.6);
    updateSelectedNodesVisualization();
  }
  
  function closeRelationshipModal() {
    showRelationshipModal = false;
    relationshipType = 'related_to';
    relationshipConfidence = 0.8;
    relationshipContext = '';
    creatingRelationship = false;
  }
  
  async function createRelationship() {
    if (selectedNodes.size !== 2 || !$authToken) return;
    
    creatingRelationship = true;
    const nodeIds = Array.from(selectedNodes);
    
    try {
      const api = getApiClient();
      api.setAuthToken($authToken);
      
      const response = await api.post('/unified-knowledge-graph/relationships', {
        source_entity_id: nodeIds[0],
        target_entity_id: nodeIds[1],
        relationship_type: relationshipType,
        confidence_score: relationshipConfidence,
        context: relationshipContext || null,
        metadata: {
          created_via: 'manual_ui',
          created_at: new Date().toISOString()
        }
      });
      
      console.log('✅ Relationship created successfully:', response.data);
      
      // Close modal and refresh graph
      closeRelationshipModal();
      
      // Reload graph to show new relationship
      await loadGraphData();
      
      // Show success message
      alert('Relationship created successfully!');
      
    } catch (e: any) {
      console.error('❌ Error creating relationship:', e);
      alert(`Failed to create relationship: ${e.response?.data?.detail || e.message}`);
    } finally {
      creatingRelationship = false;
    }
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
      
      {#if graphData && graphData.metadata}
        <div class="graph-stats">
          {#if filteredGraphData && filteredGraphData.metadata.filtered}
            <!-- Filtered stats -->
            <span class="stat-item filtered">
              <Icon name="circle" size="small" />
              {filteredGraphData.nodes.length} / {graphData.nodes.length} entities
            </span>
            <span class="stat-item filtered">
              <Icon name="arrow-right" size="small" />
              {filteredGraphData.edges.length} / {graphData.edges.length} relationships
            </span>
            <span class="stat-item search-indicator">
              <Icon name="search" size="small" />
              Filtered by: "{filteredGraphData.metadata.search_query}"
            </span>
          {:else}
            <!-- Normal stats -->
            <span class="stat-item">
              <Icon name="circle" size="small" />
              {graphData.metadata.total_nodes || graphData.nodes?.length || 0} entities
            </span>
            <span class="stat-item">
              <Icon name="arrow-right" size="small" />
              {graphData.metadata.total_edges || graphData.edges?.length || 0} relationships
            </span>
            {#if graphData.metadata.entity_types}
              <span class="stat-item">
                <Icon name="tag" size="small" />
                {Object.keys(graphData.metadata.entity_types).length} types
              </span>
            {/if}
          {/if}
        </div>
      {/if}
    </div>
    
    <div class="header-controls">
      <div class="control-group search-group">
        <label>
          <Icon name="search" size="small" />
          <input 
            type="text"
            placeholder="Search entities..."
            bind:value={searchQuery}
            on:input={handleSearchInput}
            class="search-input"
          />
        </label>
        {#if searchQuery}
          <button class="clear-search" on:click={clearSearch} title="Clear search">
            <Icon name="x" size="small" />
          </button>
        {/if}
      </div>
      
      <div class="control-group">
        <label>
          <Icon name="filter" size="small" />
          <select bind:value={filterType} on:change={filterGraph}>
            <option value="all">All Types</option>
            <option value="text_entity">Text Entities</option>
            <option value="knowledge_concept">Knowledge Concepts</option>
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
          <Icon name="sliders" size="small" />
          <select bind:value={relationshipFilter} on:change={filterGraph}>
            <option value="all">All Relationships</option>
            <!-- Most common relationships for filtering -->
            <option value="related_to">Related To</option>
            <option value="references">References</option>
            <option value="explains">Explains</option>
            <option value="implements">Implements</option>
            <option value="part_of">Part Of</option>
            <option value="builds_on">Builds On</option>
            <option value="prerequisite">Prerequisite</option>
            <option value="similar_to">Similar To</option>
            <option value="extends">Extends</option>
            <option value="contains">Contains</option>
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
      
      <div class="control-group">
        <label>
          <Icon name="target" size="small" />
          <input 
            type="range" 
            min="0.1" 
            max="1.0" 
            step="0.1" 
            bind:value={minConfidenceFilter}
            on:change={filterGraph}
          />
          <span>Min Confidence: {Math.round(minConfidenceFilter * 100)}%</span>
        </label>
      </div>
      
      <button class="control-button" on:click={toggleLabels}>
        <Icon name={showLabels ? 'eye-off' : 'eye'} size="small" />
        {showLabels ? 'Hide' : 'Show'} Labels
      </button>
      
      <button 
        class="control-button relationship-vis-toggle" 
        class:active={showRelationshipStrength}
        on:click={toggleRelationshipStrength}
        title="Toggle relationship strength visualization"
      >
        <Icon name="activity" size="small" />
        {showRelationshipStrength ? 'Hide' : 'Show'} Strength
      </button>
      
      {#if showRelationshipStrength}
        <button 
          class="control-button opacity-mode" 
          on:click={cycleOpacityMode}
          title="Cycle through opacity modes: {relationshipOpacityMode}"
        >
          <Icon name="layers" size="small" />
          {relationshipOpacityMode.charAt(0).toUpperCase() + relationshipOpacityMode.slice(1)}
        </button>
      {/if}
      
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
      
      <div class="selection-controls">
        <button 
          class="control-button selection-mode-toggle" 
          class:active={selectionMode === 'multi'}
          on:click={toggleSelectionMode}
          title="Toggle between single and multi-selection modes"
        >
          <Icon name={selectionMode === 'multi' ? 'check-square' : 'square'} size="small" />
          {selectionMode === 'multi' ? 'Multi-Select' : 'Single-Select'}
        </button>
        
        {#if selectedNodes.size > 0}
          <div class="selected-count">
            <Icon name="target" size="small" />
            {selectedNodes.size} selected
          </div>
          
          {#if selectedNodes.size === 2}
            <button 
              class="control-button relationship-create"
              on:click={createRelationshipBetweenSelected}
              title="Create relationship between selected nodes"
            >
              <Icon name="link" size="small" />
              Connect
            </button>
            
            <button 
              class="control-button path-discovery"
              on:click={startPathDiscovery}
              title="Discover learning paths between selected nodes"
            >
              <Icon name="route" size="small" />
              Find Paths
            </button>
          {/if}
          
          <!-- Relationship Suggestions Button -->
          <button 
            class="control-button ai-suggestions"
            on:click={() => openRelationshipSuggestions(selectedNodes.size === 1 ? graphData?.nodes.find(n => selectedNodes.has(n.id)) : null)}
            title={selectedNodes.size === 1 ? "Get AI suggestions for selected entity" : "Get general AI relationship suggestions"}
          >
            <Icon name="sparkles" size="small" />
            {selectedNodes.size === 1 ? 'AI Suggestions' : 'AI Insights'}
          </button>
          
          <!-- Knowledge Gap Analysis Button -->
          <button 
            class="control-button gap-analysis"
            on:click={openGapAnalysis}
            title="Analyze knowledge graph for gaps and missing relationships"
          >
            <Icon name="search" size="small" />
            Gap Analysis
          </button>
          
          <!-- Semantic Clustering Button -->
          <button 
            class="control-button semantic-clustering"
            on:click={openSemanticClustering}
            title="Group related entities into semantic clusters"
          >
            <Icon name="layers" size="small" />
            Clustering
          </button>
          
          <!-- Analytics Dashboard Button -->
          <button 
            class="control-button analytics-dashboard"
            on:click={openAnalyticsDashboard}
            title="View comprehensive knowledge graph analytics"
          >
            <Icon name="bar-chart" size="small" />
            Analytics
          </button>
          
          <button 
            class="control-button clear-selection"
            on:click={clearSelection}
            title="Clear all selections"
          >
            <Icon name="x" size="small" />
            Clear
          </button>
        {/if}
      </div>
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
  
  {#if selectedNode || selectedNodes.size > 1}
    <div class="node-details">
      <div class="details-header">
        {#if selectedNodes.size > 1}
          <h3>Multi-Selection ({selectedNodes.size} nodes)</h3>
        {:else}
          <h3>{selectedNode?.title}</h3>
        {/if}
        <button class="close-button" on:click={() => { selectedNode = null; clearSelection(); }}>
          <Icon name="x" size="small" />
        </button>
      </div>
      
      <div class="details-content">
        {#if selectedNodes.size > 1}
          <!-- Multi-selection view -->
          <div class="multi-selection-info">
            <p>You have selected {selectedNodes.size} nodes. Use the controls above to:</p>
            <ul>
              <li>Create relationships between nodes (select exactly 2)</li>
              <li>View individual node details by clicking them</li>
              <li>Clear selection with the Clear button</li>
            </ul>
            
            {#if selectedNodes.size === 2}
              <div class="relationship-hint">
                <Icon name="info" size="small" />
                Perfect! You can now create a relationship between these 2 nodes using the "Connect" button above.
              </div>
            {/if}
            
            <div class="selected-nodes-list">
              <h4>Selected Nodes:</h4>
              {#each Array.from(selectedNodes) as nodeId}
                {@const node = graphData?.nodes.find(n => n.id === nodeId)}
                {#if node}
                  <div class="selected-node-item">
                    <div 
                      class="node-color-dot" 
                      style="background-color: {getPersonaEnhancedColor(node)}"
                    ></div>
                    <span class="node-title">{node.title}</span>
                    <span class="node-type-small">{node.type}</span>
                  </div>
                {/if}
              {/each}
            </div>
          </div>
        {:else if selectedNode}
          <!-- Single selection view -->
          <p class="node-type">
            <span class="type-badge" style="background-color: {typeColors[selectedNode.type as keyof typeof typeColors] || typeColors.default}">
              {selectedNode.type}
            </span>
          </p>
          
          {#if selectedNode.summary}
            <p class="node-summary">{selectedNode.summary}</p>
          {/if}
        {/if}
        
        {#if selectedNode && personaEnhanced && selectedNode.personaCategory !== 'normal'}
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
        
        {#if selectedNode && selectedNode.tags?.length}
          <div class="node-tags">
            {#each selectedNode.tags as tag}
              <span class="tag">#{tag}</span>
            {/each}
          </div>
        {/if}
        
        {#if selectedNode}
          <button class="view-button" on:click={() => navigateToItem(selectedNode.id)}>
            View Full Content
            <Icon name="arrow-right" size="small" />
          </button>
        {/if}
      </div>
    </div>
  {/if}
  
  <!-- Relationship Strength Legend -->
  {#if showRelationshipStrength && graphData}
    <div class="strength-legend">
      <div class="legend-header">
        <Icon name="info" size="small" />
        <span>Relationship Strength</span>
      </div>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-line strong"></div>
          <span>Strong ({relationshipOpacityMode})</span>
        </div>
        <div class="legend-item">
          <div class="legend-line medium"></div>
          <span>Medium</span>
        </div>
        <div class="legend-item">
          <div class="legend-line weak"></div>
          <span>Weak</span>
        </div>
        <div class="legend-item">
          <div class="legend-line dashed"></div>
          <span>Low Confidence</span>
        </div>
      </div>
    </div>
  {/if}
  
  {#if hoveredNode && hoveredNode !== selectedNode}
    <div 
      class="tooltip node-tooltip" 
      style="
        opacity: 1; 
        left: {mousePosition.x + 10}px; 
        top: {mousePosition.y - 10}px;
      "
    >
      <strong>{hoveredNode.title}</strong>
      <br>
      <span class="tooltip-type">{hoveredNode.type}</span>
      {#if hoveredNode.confidence}
        <br>
        <span class="tooltip-confidence">Confidence: {Math.round(hoveredNode.confidence * 100)}%</span>
      {/if}
    </div>
  {/if}
  
  {#if hoveredEdge && showRelationshipStrength}
    <div 
      class="tooltip edge-tooltip" 
      style="
        opacity: 1; 
        left: {mousePosition.x + 10}px; 
        top: {mousePosition.y - 10}px;
      "
    >
      <strong>{hoveredEdge.relationship.replace('_', ' ')}</strong>
      <br>
      <span class="tooltip-strength">Strength: {Math.round((hoveredEdge.strength || 1.0) * 100)}%</span>
      {#if hoveredEdge.confidence}
        <br>
        <span class="tooltip-confidence">Confidence: {Math.round(hoveredEdge.confidence * 100)}%</span>
      {/if}
      {#if hoveredEdge.context}
        <br>
        <span class="tooltip-context">{hoveredEdge.context}</span>
      {/if}
    </div>
  {/if}
  
  <!-- Relationship Creation Modal -->
  {#if showRelationshipModal}
    <div class="modal-overlay" on:click={closeRelationshipModal}>
      <div class="modal-content" on:click|stopPropagation>
        <div class="modal-header">
          <h3>Create Relationship</h3>
          <button class="close-button" on:click={closeRelationshipModal}>
            <Icon name="x" size="small" />
          </button>
        </div>
        
        <div class="modal-body">
          <!-- Selected Nodes Preview -->
          <div class="relationship-preview">
            {#each Array.from(selectedNodes) as nodeId, index}
              {@const node = graphData?.nodes.find(n => n.id === nodeId)}
              {#if node}
                <div class="relationship-node">
                  <div 
                    class="node-preview-dot" 
                    style="background-color: {getPersonaEnhancedColor(node)}"
                  ></div>
                  <div class="node-preview-info">
                    <div class="node-preview-title">{node.title}</div>
                    <div class="node-preview-type">{node.type}</div>
                  </div>
                </div>
                {#if index === 0}
                  <div class="relationship-arrow">
                    <Icon name="arrow-right" size="medium" />
                  </div>
                {/if}
              {/if}
            {/each}
          </div>
          
          <!-- Relationship Type Selection -->
          <div class="form-group">
            <label for="relationship-type">
              <Icon name="link" size="small" />
              Relationship Type
            </label>
            <select id="relationship-type" bind:value={relationshipType}>
              <!-- Temporal relationships -->
              <option value="precedes">Precedes</option>
              <option value="follows">Follows</option>
              <option value="concurrent">Concurrent</option>
              <option value="enables">Enables</option>
              <option value="depends_on">Depends On</option>
              
              <!-- Content relationships -->
              <option value="discusses">Discusses</option>
              <option value="implements">Implements</option>
              <option value="references">References</option>
              <option value="explains">Explains</option>
              <option value="demonstrates">Demonstrates</option>
              
              <!-- Structural relationships -->
              <option value="contains">Contains</option>
              <option value="part_of">Part Of</option>
              <option value="similar_to">Similar To</option>
              <option value="related_to" selected>Related To</option>
              <option value="opposite_of">Opposite Of</option>
              
              <!-- Cross-modal relationships -->
              <option value="visualizes">Visualizes</option>
              <option value="describes">Describes</option>
              <option value="transcribes">Transcribes</option>
              <option value="summarizes">Summarizes</option>
              <option value="extends">Extends</option>
              
              <!-- Learning relationships -->
              <option value="prerequisite">Prerequisite</option>
              <option value="builds_on">Builds On</option>
              <option value="reinforces">Reinforces</option>
              <option value="applies">Applies</option>
              <option value="teaches">Teaches</option>
            </select>
          </div>
          
          <!-- Confidence Score -->
          <div class="form-group">
            <label for="relationship-confidence">
              <Icon name="trending-up" size="small" />
              Confidence Score: {Math.round(relationshipConfidence * 100)}%
            </label>
            <input 
              id="relationship-confidence"
              type="range" 
              min="0.1" 
              max="1.0" 
              step="0.1" 
              bind:value={relationshipConfidence}
            />
          </div>
          
          <!-- Context/Description -->
          <div class="form-group">
            <label for="relationship-context">
              <Icon name="message-square" size="small" />
              Context (Optional)
            </label>
            <textarea 
              id="relationship-context"
              placeholder="Describe why these entities are related..."
              bind:value={relationshipContext}
              rows="3"
            ></textarea>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="modal-button secondary" on:click={closeRelationshipModal}>
            <Icon name="x" size="small" />
            Cancel
          </button>
          <button 
            class="modal-button primary" 
            on:click={createRelationship}
            disabled={creatingRelationship}
          >
            {#if creatingRelationship}
              <div class="spinner-small"></div>
              Creating...
            {:else}
              <Icon name="link" size="small" />
              Create Relationship
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Knowledge Path Discovery Modal -->
  {#if showPathDiscovery}
    <div class="modal-overlay" on:click={closePathDiscovery}>
      <div class="modal-content path-discovery-modal" on:click|stopPropagation>
        <div class="modal-header">
          <h3>Knowledge Path Discovery</h3>
          <button class="close-button" on:click={closePathDiscovery}>
            <Icon name="x" size="small" />
          </button>
        </div>
        
        <div class="modal-body">
          <!-- Path Search Summary -->
          {#if pathStartNode && pathEndNode}
            <div class="path-search-summary">
              <div class="path-endpoint">
                <div 
                  class="endpoint-dot start" 
                  style="background-color: {getPersonaEnhancedColor(pathStartNode)}"
                ></div>
                <div class="endpoint-info">
                  <div class="endpoint-name">{pathStartNode.title}</div>
                  <div class="endpoint-type">{pathStartNode.type}</div>
                </div>
              </div>
              
              <div class="path-arrow">
                <Icon name="arrow-right" size="large" />
                <span class="path-label">Learning Path</span>
              </div>
              
              <div class="path-endpoint">
                <div 
                  class="endpoint-dot end" 
                  style="background-color: {getPersonaEnhancedColor(pathEndNode)}"
                ></div>
                <div class="endpoint-info">
                  <div class="endpoint-name">{pathEndNode.title}</div>
                  <div class="endpoint-type">{pathEndNode.type}</div>
                </div>
              </div>
            </div>
          {/if}
          
          <!-- Loading State -->
          {#if discoveringPaths}
            <div class="path-loading">
              <div class="spinner"></div>
              <p>Discovering knowledge paths...</p>
            </div>
          {/if}
          
          <!-- Error State -->
          {#if pathDiscoveryError}
            <div class="path-error">
              <Icon name="alert-circle" size="medium" />
              <p>{pathDiscoveryError}</p>
              <button class="retry-button" on:click={discoverKnowledgePaths}>
                <Icon name="refresh-cw" size="small" />
                Retry
              </button>
            </div>
          {/if}
          
          <!-- Discovered Paths -->
          {#if discoveredPaths.length > 0}
            <div class="discovered-paths">
              <h4>Found {discoveredPaths.length} Learning Path{discoveredPaths.length > 1 ? 's' : ''}</h4>
              
              {#each discoveredPaths as path, index}
                <div 
                  class="path-item" 
                  on:mouseenter={() => highlightPath(path)}
                  on:mouseleave={clearPathHighlight}
                >
                  <div class="path-header">
                    <div class="path-number">#{index + 1}</div>
                    <div class="path-metrics">
                      <span class="path-length">
                        <Icon name="git-branch" size="small" />
                        {path.path_length} steps
                      </span>
                      <span class="path-confidence">
                        <Icon name="target" size="small" />
                        {Math.round(path.total_confidence * 100)}% confidence
                      </span>
                      <span class="path-difficulty difficulty-{path.learning_difficulty}">
                        <Icon name="trending-up" size="small" />
                        {path.learning_difficulty}
                      </span>
                    </div>
                  </div>
                  
                  <div class="path-nodes">
                    {#each path.nodes as node, nodeIndex}
                      <div class="path-node">
                        <div class="path-node-content">
                          <div class="path-node-name">{node.entity_name}</div>
                          <div class="path-node-type">{node.entity_type}</div>
                        </div>
                        {#if nodeIndex < path.nodes.length - 1}
                          <div class="path-relationship">
                            <Icon name="arrow-right" size="small" />
                            <span class="relationship-label">
                              {path.edges[nodeIndex]?.relationship_type?.replace('_', ' ') || 'connects'}
                            </span>
                          </div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                </div>
              {/each}
            </div>
          {:else if !discoveringPaths && !pathDiscoveryError}
            <div class="no-paths">
              <Icon name="search" size="large" />
              <p>No learning paths found between these entities.</p>
              <p class="no-paths-suggestion">Try selecting entities that are more closely related or adjust the search parameters.</p>
            </div>
          {/if}
        </div>
        
        <div class="modal-footer">
          <button class="modal-button secondary" on:click={closePathDiscovery}>
            <Icon name="x" size="small" />
            Close
          </button>
          {#if discoveredPaths.length > 0}
            <button class="modal-button primary" on:click={clearPathHighlight}>
              <Icon name="eye-off" size="small" />
              Clear Highlights
            </button>
          {/if}
        </div>
      </div>
    </div>
  {/if}

  <!-- AI Relationship Suggestions Modal -->
  {#if showRelationshipSuggestions}
    <div class="modal-overlay" on:click={closeRelationshipSuggestions}>
      <div class="modal-content relationship-suggestions-modal" on:click|stopPropagation>
        <div class="modal-header">
          <h3>AI Relationship Suggestions</h3>
          <button class="close-button" on:click={closeRelationshipSuggestions}>
            <Icon name="x" size="small" />
          </button>
        </div>
        
        <div class="modal-body">
          <!-- Entity Context -->
          {#if selectedSuggestionEntity}
            <div class="suggestion-context">
              <div class="context-entity">
                <div 
                  class="entity-dot" 
                  style="background-color: {typeColors[selectedSuggestionEntity.type] || typeColors.default}"
                ></div>
                <div class="entity-info">
                  <div class="entity-name">{selectedSuggestionEntity.title}</div>
                  <div class="entity-type">{selectedSuggestionEntity.type}</div>
                </div>
              </div>
              <p class="context-description">
                AI-powered suggestions for relationships involving this entity
              </p>
            </div>
          {:else}
            <div class="suggestion-context">
              <p class="context-description">
                General AI-powered relationship suggestions for the knowledge graph
              </p>
            </div>
          {/if}

          <!-- Settings Controls -->
          <div class="suggestions-settings">
            <div class="setting-group">
              <label for="confidence-threshold">Confidence Threshold</label>
              <input 
                id="confidence-threshold"
                type="range" 
                min="0.1" 
                max="1.0" 
                step="0.1" 
                bind:value={suggestionConfidenceThreshold}
                on:change={() => loadRelationshipSuggestions(selectedSuggestionEntity?.id)}
              />
              <span class="setting-value">{suggestionConfidenceThreshold.toFixed(1)}</span>
            </div>
            <div class="setting-group">
              <label for="suggestion-limit">Max Suggestions</label>
              <select 
                id="suggestion-limit"
                bind:value={suggestionLimit}
                on:change={() => loadRelationshipSuggestions(selectedSuggestionEntity?.id)}
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={20}>20</option>
              </select>
            </div>
          </div>

          <!-- Loading State -->
          {#if loadingSuggestions}
            <div class="loading-suggestions">
              <div class="spinner"></div>
              <p>Analyzing entities and generating AI suggestions...</p>
            </div>
          {/if}

          <!-- Error State -->
          {#if suggestionsError}
            <div class="error-message">
              <Icon name="alert-circle" size="small" />
              <span>{suggestionsError}</span>
            </div>
          {/if}

          <!-- Suggestions List -->
          {#if relationshipSuggestions.length > 0}
            <div class="suggestions-list">
              <h4>Suggested Relationships ({relationshipSuggestions.length})</h4>
              
              {#each relationshipSuggestions as suggestion, index}
                <div class="suggestion-item" class:high-confidence={suggestion.confidence_score >= 0.7}>
                  <div class="suggestion-header">
                    <div class="suggestion-relationship">
                      <span class="entity-name">{suggestion.source_entity_name}</span>
                      <div class="relationship-arrow">
                        <span class="relationship-type">{suggestion.suggested_relationship}</span>
                        <Icon name="arrow-right" size="small" />
                      </div>
                      <span class="entity-name">{suggestion.target_entity_name}</span>
                    </div>
                    <div class="suggestion-confidence">
                      <div class="confidence-bar">
                        <div 
                          class="confidence-fill" 
                          style="width: {(suggestion.confidence_score * 100)}%"
                        ></div>
                      </div>
                      <span class="confidence-value">{(suggestion.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  
                  <div class="suggestion-details">
                    <p class="suggestion-reasoning">{suggestion.reasoning}</p>
                    {#if suggestion.semantic_similarity}
                      <div class="suggestion-metrics">
                        <span class="metric">
                          <Icon name="target" size="tiny" />
                          Semantic: {(suggestion.semantic_similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                    {/if}
                  </div>
                  
                  <div class="suggestion-actions">
                    <button 
                      class="suggestion-button apply"
                      on:click={() => applySuggestion(suggestion)}
                      title="Apply this suggestion to the knowledge graph"
                    >
                      <Icon name="check" size="small" />
                      Apply
                    </button>
                    <button 
                      class="suggestion-button dismiss"
                      on:click={() => relationshipSuggestions = relationshipSuggestions.filter((_, i) => i !== index)}
                      title="Dismiss this suggestion"
                    >
                      <Icon name="x" size="small" />
                      Dismiss
                    </button>
                  </div>
                </div>
              {/each}
            </div>
          {:else if !loadingSuggestions && !suggestionsError}
            <div class="no-suggestions">
              <Icon name="lightbulb-off" size="large" />
              <h4>No Suggestions Found</h4>
              <p>Try lowering the confidence threshold or selecting a different entity.</p>
            </div>
          {/if}
        </div>
        
        <div class="modal-footer">
          <button class="modal-button secondary" on:click={closeRelationshipSuggestions}>
            <Icon name="x" size="small" />
            Close
          </button>
          <button 
            class="modal-button primary" 
            on:click={() => loadRelationshipSuggestions(selectedSuggestionEntity?.id)}
            disabled={loadingSuggestions}
          >
            <Icon name="refresh-cw" size="small" />
            Refresh
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Knowledge Gap Analysis Modal -->
  {#if showGapAnalysis}
    <div class="modal-overlay" on:click={closeGapAnalysis}>
      <div class="modal-content gap-analysis-modal" on:click|stopPropagation>
        <div class="modal-header">
          <h3>Knowledge Gap Analysis</h3>
          <button class="close-button" on:click={closeGapAnalysis}>
            <Icon name="x" size="small" />
          </button>
        </div>
        
        <div class="modal-body">
          <!-- Analysis Controls -->
          <div class="analysis-controls">
            <div class="control-group">
              <label for="analysis-depth">Analysis Depth</label>
              <select 
                id="analysis-depth"
                bind:value={analysisDepth}
                on:change={() => gapAnalysisData = null}
              >
                <option value="quick">Quick</option>
                <option value="standard">Standard</option>
                <option value="comprehensive">Comprehensive</option>
              </select>
            </div>
            <div class="control-group">
              <label for="min-severity">Minimum Severity</label>
              <select 
                id="min-severity"
                bind:value={minSeverity}
                on:change={() => gapAnalysisData = null}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <button 
              class="run-analysis-button"
              on:click={runGapAnalysis}
              disabled={loadingGapAnalysis}
            >
              {#if loadingGapAnalysis}
                <div class="spinner-small"></div>
                Analyzing...
              {:else}
                <Icon name="play" size="small" />
                Run Analysis
              {/if}
            </button>
          </div>

          <!-- Loading State -->
          {#if loadingGapAnalysis}
            <div class="loading-analysis">
              <div class="spinner"></div>
              <p>Analyzing knowledge graph structure and identifying gaps...</p>
            </div>
          {/if}

          <!-- Error State -->
          {#if gapAnalysisError}
            <div class="error-message">
              <Icon name="alert-circle" size="small" />
              <span>{gapAnalysisError}</span>
            </div>
          {/if}

          <!-- Analysis Results -->
          {#if gapAnalysisData && !loadingGapAnalysis}
            <div class="analysis-results">
              <!-- Overall Summary -->
              <div class="analysis-summary">
                <h4>Analysis Summary</h4>
                <div class="summary-grid">
                  <div class="summary-item">
                    <div class="summary-value">{(gapAnalysisData.overall_completeness * 100).toFixed(0)}%</div>
                    <div class="summary-label">Overall Completeness</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-value">{gapAnalysisData.gaps.length}</div>
                    <div class="summary-label">Gaps Identified</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-value">{gapAnalysisData.domains.length}</div>
                    <div class="summary-label">Domains Analyzed</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-value">{gapAnalysisData.analysis_summary.relationship_density.toFixed(1)}</div>
                    <div class="summary-label">Relationship Density</div>
                  </div>
                </div>
              </div>

              <!-- Knowledge Gaps -->
              {#if gapAnalysisData.gaps.length > 0}
                <div class="gaps-section">
                  <h4>Knowledge Gaps ({gapAnalysisData.gaps.length})</h4>
                  <div class="gaps-list">
                    {#each gapAnalysisData.gaps as gap, index}
                      <div class="gap-item" class:high-severity={gap.severity === 'critical' || gap.severity === 'high'}>
                        <div class="gap-header">
                          <div class="gap-severity">
                            <Icon name={getSeverityIcon(gap.severity)} size="small" style="color: {getSeverityColor(gap.severity)}" />
                            <span class="severity-label" style="color: {getSeverityColor(gap.severity)}">{gap.severity.toUpperCase()}</span>
                          </div>
                          <div class="gap-confidence">
                            {(gap.confidence_score * 100).toFixed(0)}% confidence
                          </div>
                        </div>
                        
                        <div class="gap-content">
                          <h5 class="gap-title">{gap.title}</h5>
                          <p class="gap-description">{gap.description}</p>
                          
                          {#if gap.domain}
                            <div class="gap-domain">Domain: {gap.domain}</div>
                          {/if}
                          
                          {#if gap.affected_entities.length > 0}
                            <div class="affected-entities">
                              <strong>Affected:</strong> {gap.affected_entities.join(', ')}
                            </div>
                          {/if}
                          
                          {#if gap.suggested_actions.length > 0}
                            <div class="suggested-actions">
                              <strong>Suggested Actions:</strong>
                              <ul>
                                {#each gap.suggested_actions as action}
                                  <li>{action}</li>
                                {/each}
                              </ul>
                            </div>
                          {/if}
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Knowledge Domains -->
              {#if gapAnalysisData.domains.length > 0}
                <div class="domains-section">
                  <h4>Knowledge Domains ({gapAnalysisData.domains.length})</h4>
                  <div class="domains-grid">
                    {#each gapAnalysisData.domains as domain}
                      <div class="domain-card" class:weak-domain={domain.completeness_score < 0.5}>
                        <div class="domain-header">
                          <h5 class="domain-name">{domain.domain_name}</h5>
                          <div class="domain-score">
                            {(domain.completeness_score * 100).toFixed(0)}%
                          </div>
                        </div>
                        
                        <div class="domain-metrics">
                          <div class="metric">
                            <span class="metric-label">Entities:</span>
                            <span class="metric-value">{domain.entity_count}</span>
                          </div>
                          <div class="metric">
                            <span class="metric-label">Density:</span>
                            <span class="metric-value">{domain.relationship_density.toFixed(2)}</span>
                          </div>
                          <div class="metric">
                            <span class="metric-label">Connected:</span>
                            <span class="metric-value">{(domain.interconnectedness * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                        
                        {#if domain.key_entities.length > 0}
                          <div class="key-entities">
                            <strong>Key Entities:</strong> {domain.key_entities.join(', ')}
                          </div>
                        {/if}
                        
                        {#if domain.missing_concepts.length > 0}
                          <div class="missing-concepts">
                            <strong>Missing Concepts:</strong> {domain.missing_concepts.join(', ')}
                          </div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Recommendations -->
              {#if gapAnalysisData.recommendations.length > 0}
                <div class="recommendations-section">
                  <h4>Recommendations</h4>
                  <div class="recommendations-list">
                    {#each gapAnalysisData.recommendations as recommendation, index}
                      <div class="recommendation-item">
                        <Icon name="lightbulb" size="small" />
                        <span>{recommendation}</span>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          {/if}
        </div>
        
        <div class="modal-footer">
          <button class="modal-button secondary" on:click={closeGapAnalysis}>
            <Icon name="x" size="small" />
            Close
          </button>
          {#if gapAnalysisData}
            <button 
              class="modal-button primary" 
              on:click={runGapAnalysis}
              disabled={loadingGapAnalysis}
            >
              <Icon name="refresh-cw" size="small" />
              Refresh Analysis
            </button>
          {/if}
        </div>
      </div>
    </div>
  {/if}

  <!-- Semantic Clustering Modal -->
  {#if showSemanticClustering}
    <div class="modal-overlay" on:click={() => showSemanticClustering = false}>
      <div class="modal-content semantic-clustering-modal" on:click|stopPropagation>
        <div class="modal-header">
          <h3>Semantic Clustering</h3>
          <button class="close-button" on:click={() => showSemanticClustering = false}>
            <Icon name="x" size="small" />
          </button>
        </div>
        
        <div class="modal-body">
          <!-- Clustering Controls -->
          <div class="clustering-controls">
            <div class="control-group">
              <label for="clustering-algorithm">Algorithm</label>
              <select 
                id="clustering-algorithm"
                bind:value={clusteringAlgorithm}
                on:change={() => clusteringData = null}
              >
                <option value="semantic">Semantic (content-based)</option>
                <option value="structural">Structural (relationship-based)</option>
                <option value="hybrid">Hybrid (combined)</option>
              </select>
            </div>
            <div class="control-group">
              <label for="min-cluster-size">Min Cluster Size</label>
              <input 
                id="min-cluster-size"
                type="number"
                bind:value={minClusterSize}
                min="2"
                max="20"
                on:input={() => clusteringData = null}
              />
            </div>
            <div class="control-group">
              <label for="max-clusters">Max Clusters</label>
              <input 
                id="max-clusters"
                type="number"
                bind:value={maxClusters}
                min="3"
                max="25"
                on:input={() => clusteringData = null}
              />
            </div>
            <div class="control-group">
              <label for="cluster-confidence">Min Confidence</label>
              <input 
                id="cluster-confidence"
                type="range"
                bind:value={clusterMinConfidence}
                min="0.1"
                max="1.0"
                step="0.1"
                on:input={() => clusteringData = null}
              />
              <span class="confidence-value">{clusterMinConfidence.toFixed(1)}</span>
            </div>
            <button 
              class="run-clustering-button"
              on:click={runSemanticClustering}
              disabled={loadingClustering}
            >
              {#if loadingClustering}
                <div class="spinner-small"></div>
                Clustering...
              {:else}
                <Icon name="layers" size="small" />
                Run Clustering
              {/if}
            </button>
          </div>

          <!-- Loading State -->
          {#if loadingClustering}
            <div class="loading-clustering">
              <div class="spinner"></div>
              <p>Analyzing entity relationships and grouping similar concepts...</p>
            </div>
          {/if}

          <!-- Error State -->
          {#if clusteringError}
            <div class="error-message">
              <Icon name="alert-circle" size="small" />
              <span>{clusteringError}</span>
            </div>
          {/if}

          <!-- Clustering Results -->
          {#if clusteringData && !loadingClustering}
            <div class="clustering-results">
              <!-- Overall Summary -->
              <div class="clustering-summary">
                <h4>Clustering Summary</h4>
                <div class="summary-grid">
                  <div class="summary-item">
                    <div class="summary-value">{clusteringData.clusters.length}</div>
                    <div class="summary-label">Clusters Found</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-value">{clusteringData.total_entities_clustered}</div>
                    <div class="summary-label">Entities Clustered</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-value">{clusteringData.unclustered_entities.length}</div>
                    <div class="summary-label">Unclustered</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-value">{clusteringData.clustering_metadata.relationships_considered}</div>
                    <div class="summary-label">Relationships Used</div>
                  </div>
                </div>
              </div>

              <!-- Cluster List -->
              {#if clusteringData.clusters.length > 0}
                <div class="clusters-section">
                  <div class="clusters-header">
                    <h4>Entity Clusters ({clusteringData.clusters.length})</h4>
                    {#if clusterHighlighted}
                      <button class="clear-highlights-button" on:click={clearClusterHighlights}>
                        <Icon name="eye-off" size="small" />
                        Clear Highlights
                      </button>
                    {/if}
                  </div>
                  
                  <div class="clusters-list">
                    {#each clusteringData.clusters as cluster, index}
                      <div 
                        class="cluster-card" 
                        class:selected={selectedCluster?.cluster_id === cluster.cluster_id}
                        on:click={() => highlightCluster(cluster)}
                        on:keydown={(e) => e.key === 'Enter' && highlightCluster(cluster)}
                        role="button"
                        tabindex="0"
                      >
                        <div class="cluster-header">
                          <div class="cluster-info">
                            <h5 class="cluster-name">{cluster.cluster_name}</h5>
                            <div class="cluster-meta">
                              <span class="cluster-type">{cluster.cluster_type}</span>
                              <span class="cluster-domain">{cluster.domain}</span>
                            </div>
                          </div>
                          <div class="cluster-stats">
                            <div class="cohesion-score">
                              <span class="score-value">{cluster.cohesion_score.toFixed(2)}</span>
                              <span class="score-label">Cohesion</span>
                            </div>
                            <div class="entity-count">
                              <span class="count-value">{cluster.entities.length}</span>
                              <span class="count-label">Entities</span>
                            </div>
                          </div>
                        </div>
                        
                        <div class="cluster-description">
                          {cluster.description}
                        </div>
                        
                        {#if cluster.keywords.length > 0}
                          <div class="cluster-keywords">
                            <strong>Keywords:</strong>
                            <div class="keywords-list">
                              {#each cluster.keywords as keyword}
                                <span class="keyword-tag">{keyword}</span>
                              {/each}
                            </div>
                          </div>
                        {/if}
                        
                        <div class="cluster-entities">
                          <strong>Entities:</strong>
                          <div class="entities-list">
                            {#each cluster.entities.slice(0, 5) as entity}
                              <span class="entity-name">{entity.title}</span>
                            {/each}
                            {#if cluster.entities.length > 5}
                              <span class="entity-more">+{cluster.entities.length - 5} more</span>
                            {/if}
                          </div>
                        </div>
                        
                        {#if cluster.central_entity}
                          <div class="central-entity">
                            <strong>Central Entity:</strong> {cluster.central_entity.title}
                          </div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Unclustered Entities -->
              {#if clusteringData.unclustered_entities.length > 0}
                <div class="unclustered-section">
                  <h4>Unclustered Entities ({clusteringData.unclustered_entities.length})</h4>
                  <div class="unclustered-list">
                    {#each clusteringData.unclustered_entities as entity}
                      <span class="unclustered-entity">{entity.title}</span>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          {/if}
        </div>
        
        <div class="modal-footer">
          <button class="modal-button secondary" on:click={() => showSemanticClustering = false}>
            <Icon name="x" size="small" />
            Close
          </button>
          {#if clusteringData}
            <button 
              class="modal-button primary" 
              on:click={runSemanticClustering}
              disabled={loadingClustering}
            >
              <Icon name="refresh-cw" size="small" />
              Refresh Clustering
            </button>
          {/if}
        </div>
      </div>
    </div>
  {/if}

  <!-- Analytics Dashboard Modal -->
  {#if showAnalyticsDashboard}
    <div class="modal-overlay" on:click={() => showAnalyticsDashboard = false}>
      <div class="modal-content analytics-dashboard-modal" on:click|stopPropagation>
        <div class="modal-header">
          <h3>Knowledge Graph Analytics</h3>
          <button class="close-button" on:click={() => showAnalyticsDashboard = false}>
            <Icon name="x" size="small" />
          </button>
        </div>
        
        <div class="modal-body">
          <!-- Loading State -->
          {#if loadingAnalytics}
            <div class="loading-analytics">
              <div class="spinner"></div>
              <p>Loading comprehensive knowledge graph analytics...</p>
            </div>
          {/if}

          <!-- Error State -->
          {#if analyticsError}
            <div class="error-message">
              <Icon name="alert-circle" size="small" />
              <span>{analyticsError}</span>
              <button class="retry-button" on:click={loadAnalyticsDashboard}>
                <Icon name="refresh-cw" size="small" />
                Retry
              </button>
            </div>
          {/if}

          <!-- Analytics Results -->
          {#if analyticsData && !loadingAnalytics}
            <div class="analytics-results">
              
              <!-- Overall Statistics -->
              <div class="analytics-section">
                <h4>Graph Overview</h4>
                <div class="stats-grid">
                  <div class="stat-card">
                    <div class="stat-value">{analyticsData.stats.total_entities || 0}</div>
                    <div class="stat-label">Total Entities</div>
                    <div class="stat-detail">
                      {#each Object.entries(analyticsData.stats.entity_types || {}) as [type, count]}
                        <span class="entity-type-stat">{type}: {count}</span>
                      {/each}
                    </div>
                  </div>
                  
                  <div class="stat-card">
                    <div class="stat-value">{analyticsData.stats.total_relationships || 0}</div>
                    <div class="stat-label">Total Relationships</div>
                    <div class="stat-detail">
                      Avg confidence: {(analyticsData.stats.avg_relationship_confidence || 0).toFixed(2)}
                    </div>
                  </div>
                  
                  <div class="stat-card">
                    <div class="stat-value">{analyticsData.clustering?.clusters?.length || 0}</div>
                    <div class="stat-label">Semantic Clusters</div>
                    <div class="stat-detail">
                      {analyticsData.clustering?.total_entities_clustered || 0} entities clustered
                    </div>
                  </div>
                  
                  <div class="stat-card">
                    <div class="stat-value">{analyticsData.gaps?.gaps?.length || 0}</div>
                    <div class="stat-label">Knowledge Gaps</div>
                    <div class="stat-detail">
                      {((analyticsData.gaps?.overall_completeness || 0) * 100).toFixed(0)}% complete
                    </div>
                  </div>
                </div>
              </div>

              <!-- Knowledge Paths Analysis -->
              {#if analyticsData.paths && analyticsData.paths.length > 0}
                <div class="analytics-section">
                  <h4>Knowledge Path Analysis</h4>
                  <div class="paths-analysis">
                    {#each analyticsData.paths as pathData}
                      <div class="path-item">
                        <div class="path-connection">
                          <span class="path-start">{pathData.start}</span>
                          <Icon name="arrow-right" size="small" />
                          <span class="path-end">{pathData.end}</span>
                        </div>
                        <div class="path-stats">
                          <span class="path-count">{pathData.paths} paths</span>
                          <span class="path-confidence">{(pathData.bestConfidence * 100).toFixed(0)}% confidence</span>
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Top Clusters -->
              {#if analyticsData.clustering?.clusters?.length > 0}
                <div class="analytics-section">
                  <h4>Top Knowledge Clusters</h4>
                  <div class="clusters-preview">
                    {#each analyticsData.clustering.clusters.slice(0, 3) as cluster}
                      <div class="cluster-preview-card">
                        <div class="cluster-preview-header">
                          <h5>{cluster.cluster_name}</h5>
                          <div class="cluster-preview-stats">
                            <span class="cohesion">{cluster.cohesion_score.toFixed(2)}</span>
                            <span class="entity-count">{cluster.entities.length}</span>
                          </div>
                        </div>
                        <div class="cluster-preview-meta">
                          <span class="cluster-preview-type">{cluster.cluster_type}</span>
                          <span class="cluster-preview-domain">{cluster.domain}</span>
                        </div>
                        {#if cluster.keywords?.length > 0}
                          <div class="cluster-preview-keywords">
                            {#each cluster.keywords.slice(0, 3) as keyword}
                              <span class="preview-keyword">{keyword}</span>
                            {/each}
                          </div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Knowledge Gaps Summary -->
              {#if analyticsData.gaps?.gaps?.length > 0}
                <div class="analytics-section">
                  <h4>Critical Knowledge Gaps</h4>
                  <div class="gaps-summary">
                    {#each analyticsData.gaps.gaps.slice(0, 5) as gap}
                      <div class="gap-summary-item" class:critical={gap.severity === 'critical'} class:high={gap.severity === 'high'}>
                        <div class="gap-summary-header">
                          <span class="gap-severity-badge {gap.severity}">{gap.severity}</span>
                          <span class="gap-title">{gap.title}</span>
                        </div>
                        <div class="gap-description">{gap.description}</div>
                        {#if gap.domain}
                          <div class="gap-domain">Domain: {gap.domain}</div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Relationship Suggestions -->
              {#if analyticsData.suggestions?.suggestions?.length > 0}
                <div class="analytics-section">
                  <h4>AI Relationship Opportunities</h4>
                  <div class="suggestions-summary">
                    <div class="suggestions-stats">
                      <span class="suggestions-count">{analyticsData.suggestions.suggestions.length} potential relationships identified</span>
                      <span class="avg-confidence">Avg confidence: {(analyticsData.suggestions.suggestions.reduce((sum, s) => sum + s.confidence_score, 0) / analyticsData.suggestions.suggestions.length).toFixed(2)}</span>
                    </div>
                    <div class="top-suggestions">
                      {#each analyticsData.suggestions.suggestions.slice(0, 3) as suggestion}
                        <div class="suggestion-preview">
                          <div class="suggestion-entities">
                            <span class="suggestion-source">{suggestion.source_entity_name}</span>
                            <span class="suggestion-relationship">{suggestion.suggested_relationship}</span>
                            <span class="suggestion-target">{suggestion.target_entity_name}</span>
                          </div>
                          <div class="suggestion-confidence">{(suggestion.confidence_score * 100).toFixed(0)}%</div>
                        </div>
                      {/each}
                    </div>
                  </div>
                </div>
              {/if}

              <!-- Domain Analysis -->
              {#if analyticsData.gaps?.domains?.length > 0}
                <div class="analytics-section">
                  <h4>Domain Health</h4>
                  <div class="domains-health">
                    {#each analyticsData.gaps.domains as domain}
                      <div class="domain-health-card">
                        <div class="domain-name">{domain.domain_name}</div>
                        <div class="domain-metrics">
                          <div class="domain-metric">
                            <span class="metric-label">Completeness</span>
                            <div class="metric-bar">
                              <div class="metric-fill" style="width: {domain.completeness_score * 100}%"></div>
                            </div>
                            <span class="metric-value">{(domain.completeness_score * 100).toFixed(0)}%</span>
                          </div>
                          <div class="domain-stats">
                            <span>{domain.entity_count} entities</span>
                            <span>{(domain.interconnectedness * 100).toFixed(0)}% connected</span>
                          </div>
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

            </div>
          {/if}
        </div>
        
        <div class="modal-footer">
          <button class="modal-button secondary" on:click={() => showAnalyticsDashboard = false}>
            <Icon name="x" size="small" />
            Close
          </button>
          {#if analyticsData}
            <button 
              class="modal-button primary" 
              on:click={loadAnalyticsDashboard}
              disabled={loadingAnalytics}
            >
              <Icon name="refresh-cw" size="small" />
              Refresh Analytics
            </button>
          {/if}
        </div>
      </div>
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
  
  .graph-stats {
    display: flex;
    gap: 1rem;
    margin-top: 0.5rem;
    flex-wrap: wrap;
  }
  
  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    background: rgba(0, 255, 150, 0.1);
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.8rem;
    color: var(--neural-green);
    border: 1px solid rgba(0, 255, 150, 0.2);
  }
  
  .stat-item.filtered {
    background: rgba(255, 165, 0, 0.1);
    color: #ffa500;
    border-color: rgba(255, 165, 0, 0.2);
  }
  
  .stat-item.search-indicator {
    background: rgba(99, 102, 241, 0.1);
    color: #6366f1;
    border-color: rgba(99, 102, 241, 0.2);
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .header-controls {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
  }
  
  .search-group {
    position: relative;
    min-width: 200px;
  }
  
  .search-input {
    width: 100%;
    padding: 0.5rem 2.5rem 0.5rem 0.5rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    color: var(--text-primary);
    font-size: 0.9rem;
  }
  
  .search-input:focus {
    outline: none;
    border-color: var(--neural-green);
    box-shadow: 0 0 0 2px rgba(0, 255, 150, 0.2);
  }
  
  .search-input::placeholder {
    color: var(--text-secondary);
  }
  
  .clear-search {
    position: absolute;
    right: 0.5rem;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 2px;
    transition: all 0.2s;
  }
  
  .clear-search:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.1);
  }
  
  .relationship-vis-toggle.active {
    background: rgba(168, 85, 247, 0.2);
    border-color: #a855f7;
    color: #a855f7;
  }
  
  .opacity-mode {
    background: rgba(59, 130, 246, 0.2);
    border-color: #3b82f6;
    color: #3b82f6;
    font-size: 0.8rem;
    text-transform: capitalize;
  }
  
  .opacity-mode:hover {
    background: rgba(59, 130, 246, 0.3);
    transform: translateY(-1px);
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
  
  .selection-controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding-left: 1rem;
    border-left: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .selection-mode-toggle.active {
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.2);
    border-color: var(--neural-green);
    color: var(--neural-green);
  }
  
  .selected-count {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    background: rgba(0, 255, 150, 0.1);
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.8rem;
    color: var(--neural-green);
    border: 1px solid rgba(0, 255, 150, 0.2);
  }
  
  .relationship-create {
    background: rgba(34, 197, 94, 0.2);
    border-color: #22c55e;
    color: #22c55e;
  }
  
  .relationship-create:hover {
    background: rgba(34, 197, 94, 0.3);
    transform: translateY(-1px);
  }
  
  .clear-selection {
    background: rgba(239, 68, 68, 0.2);
    border-color: #ef4444;
    color: #ef4444;
  }
  
  .clear-selection:hover {
    background: rgba(239, 68, 68, 0.3);
    transform: translateY(-1px);
  }
  
  .path-discovery {
    background: rgba(255, 165, 0, 0.2);
    border-color: #ffa500;
    color: #ffa500;
  }
  
  .path-discovery:hover {
    background: rgba(255, 165, 0, 0.3);
    transform: translateY(-1px);
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
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  :global(.links line:hover) {
    stroke-width: 4px !important;
    filter: brightness(1.3) !important;
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
    position: fixed;
    padding: 0.5rem 1rem;
    background: rgba(0, 0, 0, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    pointer-events: none;
    z-index: 1000;
    font-size: 0.9rem;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
  }
  
  .node-tooltip {
    /* Node-specific tooltip styling can go here */
  }
  
  .edge-tooltip {
    border-color: rgba(168, 85, 247, 0.3);
    background: rgba(168, 85, 247, 0.1);
  }
  
  .tooltip-strength {
    color: #a855f7;
    font-weight: 600;
  }
  
  .tooltip-confidence {
    color: #10b981;
    font-weight: 500;
  }
  
  .tooltip-context {
    color: var(--text-secondary);
    font-style: italic;
    font-size: 0.8rem;
    max-width: 200px;
    white-space: normal;
    word-wrap: break-word;
  }
  
  .tooltip-type {
    color: var(--text-secondary);
    font-size: 0.8rem;
    text-transform: uppercase;
  }
  
  .multi-selection-info {
    padding: 1rem 0;
  }
  
  .multi-selection-info ul {
    margin: 0.5rem 0;
    padding-left: 1.5rem;
    color: var(--text-secondary);
  }
  
  .multi-selection-info li {
    margin: 0.25rem 0;
  }
  
  .relationship-hint {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.2);
    border-radius: 0.5rem;
    padding: 0.75rem;
    margin: 1rem 0;
    color: #22c55e;
    font-size: 0.9rem;
  }
  
  .selected-nodes-list {
    margin-top: 1rem;
  }
  
  .selected-nodes-list h4 {
    margin: 0 0 0.5rem 0;
    color: var(--neural-green);
    font-size: 0.9rem;
  }
  
  .selected-node-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem;
    margin: 0.25rem 0;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 0.25rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .node-color-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  
  .node-title {
    flex: 1;
    color: var(--text-primary);
    font-weight: 500;
    font-size: 0.9rem;
  }
  
  .node-type-small {
    color: var(--text-secondary);
    font-size: 0.8rem;
    text-transform: uppercase;
    background: rgba(255, 255, 255, 0.1);
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
  }
  
  @media (max-width: 768px) {
    .graph-header {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }
    
    .header-controls {
      width: 100%;
      flex-direction: column;
      gap: 0.75rem;
    }
    
    .control-group {
      width: 100%;
    }
    
    .search-group {
      min-width: unset;
      width: 100%;
    }
    
    .control-group label {
      width: 100%;
    }
    
    .control-group select,
    .control-group input[type="range"] {
      width: 100%;
    }
    
    .node-details {
      width: calc(100% - 2rem);
      left: 1rem;
      right: 1rem;
    }
    
    .selection-controls {
      flex-wrap: wrap;
      padding-left: 0;
      border-left: none;
      border-top: 1px solid rgba(255, 255, 255, 0.2);
      padding-top: 0.5rem;
      margin-top: 0.5rem;
      width: 100%;
    }
    
    .graph-stats {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
    
    .stat-item {
      width: auto;
      min-width: fit-content;
    }
  }
  
  /* Relationship Creation Modal */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    backdrop-filter: blur(5px);
  }
  
  .modal-content {
    background: rgba(0, 0, 0, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    width: 90%;
    max-width: 500px;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .modal-header h3 {
    margin: 0;
    color: var(--neural-green);
    font-size: 1.25rem;
  }
  
  .modal-body {
    padding: 1.5rem;
  }
  
  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    padding: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .relationship-preview {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin-bottom: 2rem;
    padding: 1rem;
    background: rgba(0, 255, 150, 0.05);
    border: 1px solid rgba(0, 255, 150, 0.1);
    border-radius: 8px;
  }
  
  .relationship-node {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    min-width: 0;
    flex: 1;
  }
  
  .node-preview-dot {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  
  .node-preview-info {
    min-width: 0;
    flex: 1;
  }
  
  .node-preview-title {
    color: var(--text-primary);
    font-weight: 600;
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .node-preview-type {
    color: var(--text-secondary);
    font-size: 0.75rem;
    text-transform: uppercase;
  }
  
  .relationship-arrow {
    color: var(--neural-green);
    flex-shrink: 0;
  }
  
  .form-group {
    margin-bottom: 1.5rem;
  }
  
  .form-group label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
    font-weight: 500;
    font-size: 0.9rem;
  }
  
  .form-group select,
  .form-group input[type="range"],
  .form-group textarea {
    width: 100%;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 0.9rem;
  }
  
  .form-group select,
  .form-group textarea {
    padding: 0.75rem;
  }
  
  .form-group select {
    cursor: pointer;
  }
  
  .form-group select:focus,
  .form-group textarea:focus {
    outline: none;
    border-color: var(--neural-green);
    box-shadow: 0 0 0 2px rgba(0, 255, 150, 0.2);
  }
  
  .form-group input[type="range"] {
    padding: 0.5rem 0;
    background: transparent;
    cursor: pointer;
  }
  
  .form-group textarea {
    resize: vertical;
    min-height: 80px;
    font-family: inherit;
  }
  
  .modal-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.9rem;
  }
  
  .modal-button.secondary {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .modal-button.secondary:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }
  
  .modal-button.primary {
    background: var(--neural-green);
    color: #000;
    border: 1px solid var(--neural-green);
  }
  
  .modal-button.primary:hover:not(:disabled) {
    background: #00ff64;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 255, 100, 0.3);
  }
  
  .modal-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
  
  .spinner-small {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(0, 0, 0, 0.3);
    border-top: 2px solid #000;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @media (max-width: 768px) {
    .modal-content {
      width: 95%;
      margin: 1rem;
    }
    
    .relationship-preview {
      flex-direction: column;
      text-align: center;
    }
    
    .relationship-arrow {
      transform: rotate(90deg);
    }
    
    .modal-footer {
      flex-direction: column;
    }
    
    .modal-button {
      width: 100%;
      justify-content: center;
    }
  }
  
  /* Relationship Strength Legend */
  .strength-legend {
    position: absolute;
    bottom: 2rem;
    left: 2rem;
    background: rgba(0, 0, 0, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 1rem;
    backdrop-filter: blur(10px);
    z-index: 100;
  }
  
  .legend-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    color: var(--neural-green);
    font-weight: 600;
    font-size: 0.9rem;
  }
  
  .legend-items {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }
  
  .legend-line {
    width: 30px;
    height: 2px;
    background: #999;
    border-radius: 1px;
  }
  
  .legend-line.strong {
    height: 4px;
    background: var(--neural-green);
    box-shadow: 0 0 4px rgba(0, 255, 150, 0.5);
  }
  
  .legend-line.medium {
    height: 3px;
    background: #3b82f6;
  }
  
  .legend-line.weak {
    height: 1px;
    background: #6b7280;
    opacity: 0.6;
  }
  
  .legend-line.dashed {
    height: 2px;
    background: repeating-linear-gradient(
      to right,
      #999 0px,
      #999 4px,
      transparent 4px,
      transparent 8px
    );
  }
  
  @media (max-width: 768px) {
    .strength-legend {
      bottom: 1rem;
      left: 1rem;
      right: 1rem;
      width: calc(100% - 2rem);
    }
    
    .legend-items {
      flex-direction: row;
      flex-wrap: wrap;
      justify-content: space-around;
    }
    
    .legend-item {
      flex-direction: column;
      text-align: center;
      gap: 0.25rem;
    }
  }
  
  /* Knowledge Path Discovery Modal */
  .path-discovery-modal {
    max-width: 800px;
    max-height: 90vh;
  }
  
  .path-search-summary {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: rgba(255, 165, 0, 0.05);
    border: 1px solid rgba(255, 165, 0, 0.1);
    border-radius: 8px;
  }
  
  .path-endpoint {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex: 1;
  }
  
  .endpoint-dot {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  
  .endpoint-dot.start {
    box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
  }
  
  .endpoint-dot.end {
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
  }
  
  .endpoint-info {
    flex: 1;
    min-width: 0;
  }
  
  .endpoint-name {
    color: var(--text-primary);
    font-weight: 600;
    font-size: 1rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .endpoint-type {
    color: var(--text-secondary);
    font-size: 0.8rem;
    text-transform: uppercase;
  }
  
  .path-arrow {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    color: #ffa500;
    flex-shrink: 0;
  }
  
  .path-label {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
  }
  
  .path-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 3rem;
    color: var(--text-secondary);
  }
  
  .path-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 2rem;
    background: rgba(239, 68, 68, 0.05);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 8px;
    color: #ef4444;
    text-align: center;
  }
  
  .retry-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 4px;
    color: #ef4444;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .retry-button:hover {
    background: rgba(239, 68, 68, 0.2);
    transform: translateY(-1px);
  }
  
  .discovered-paths h4 {
    margin: 0 0 1rem 0;
    color: var(--neural-green);
    font-size: 1.1rem;
  }
  
  .path-item {
    margin-bottom: 1.5rem;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    transition: all 0.2s;
    cursor: pointer;
  }
  
  .path-item:hover {
    background: rgba(255, 165, 0, 0.05);
    border-color: rgba(255, 165, 0, 0.2);
    transform: translateY(-2px);
  }
  
  .path-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .path-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: #ffa500;
    color: #000;
    border-radius: 50%;
    font-weight: 700;
    font-size: 0.9rem;
  }
  
  .path-metrics {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .path-length,
  .path-confidence {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    color: var(--text-secondary);
    font-size: 0.8rem;
  }
  
  .path-difficulty {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
  }
  
  .difficulty-easy {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.3);
  }
  
  .difficulty-medium {
    background: rgba(255, 165, 0, 0.2);
    color: #ffa500;
    border: 1px solid rgba(255, 165, 0, 0.3);
  }
  
  .difficulty-hard {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  
  .path-nodes {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .path-node {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .path-node-content {
    flex: 1;
    min-width: 0;
    padding: 0.75rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
  }
  
  .path-node-name {
    color: var(--text-primary);
    font-weight: 500;
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .path-node-type {
    color: var(--text-secondary);
    font-size: 0.7rem;
    text-transform: uppercase;
    margin-top: 0.25rem;
  }
  
  .path-relationship {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    color: #ffa500;
    flex-shrink: 0;
  }
  
  .relationship-label {
    font-size: 0.7rem;
    text-transform: capitalize;
    white-space: nowrap;
  }
  
  .no-paths {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 3rem;
    color: var(--text-secondary);
    text-align: center;
  }
  
  .no-paths-suggestion {
    font-size: 0.9rem;
    color: var(--text-secondary);
    opacity: 0.8;
  }

  /* AI Relationship Suggestions Modal */
  .relationship-suggestions-modal {
    max-width: 900px;
    max-height: 90vh;
  }

  .suggestion-context {
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: rgba(0, 255, 100, 0.05);
    border: 1px solid rgba(0, 255, 100, 0.1);
    border-radius: 8px;
  }

  .context-entity {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.75rem;
  }

  .entity-dot {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .entity-info .entity-name {
    color: var(--text-primary);
    font-weight: 500;
    font-size: 1rem;
  }

  .entity-info .entity-type {
    color: var(--text-secondary);
    font-size: 0.8rem;
    text-transform: uppercase;
    margin-top: 0.25rem;
  }

  .context-description {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin: 0;
  }

  .suggestions-settings {
    display: flex;
    gap: 2rem;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
  }

  .setting-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex: 1;
  }

  .setting-group label {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .setting-group input[type="range"] {
    width: 100%;
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    appearance: none;
    cursor: pointer;
  }

  .setting-group input[type="range"]::-webkit-slider-thumb {
    appearance: none;
    width: 18px;
    height: 18px;
    background: var(--neural-green);
    border-radius: 50%;
    cursor: pointer;
    border: 2px solid #000;
  }

  .setting-group select {
    padding: 0.5rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    color: var(--text-primary);
    font-size: 0.9rem;
  }

  .setting-value {
    color: var(--neural-green);
    font-weight: 500;
    font-size: 0.9rem;
  }

  .loading-suggestions {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 3rem;
    color: var(--text-secondary);
  }

  .suggestions-list h4 {
    color: var(--neural-green);
    margin-bottom: 1rem;
    font-size: 1.1rem;
  }

  .suggestion-item {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    transition: all 0.2s ease;
  }

  .suggestion-item:hover {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .suggestion-item.high-confidence {
    border-color: rgba(0, 255, 100, 0.2);
    background: rgba(0, 255, 100, 0.02);
  }

  .suggestion-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .suggestion-relationship {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex: 1;
  }

  .suggestion-relationship .entity-name {
    color: var(--text-primary);
    font-weight: 500;
    font-size: 0.9rem;
  }

  .relationship-arrow {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    color: var(--neural-green);
  }

  .relationship-type {
    font-size: 0.7rem;
    text-transform: uppercase;
    font-weight: 500;
    letter-spacing: 0.5px;
  }

  .suggestion-confidence {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .confidence-bar {
    width: 60px;
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    overflow: hidden;
  }

  .confidence-fill {
    height: 100%;
    background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);
    transition: width 0.3s ease;
  }

  .confidence-value {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 500;
    min-width: 35px;
  }

  .suggestion-details {
    margin-bottom: 1rem;
  }

  .suggestion-reasoning {
    color: var(--text-secondary);
    font-size: 0.9rem;
    line-height: 1.4;
    margin: 0 0 0.5rem 0;
  }

  .suggestion-metrics {
    display: flex;
    gap: 1rem;
  }

  .metric {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    color: var(--text-secondary);
    font-size: 0.8rem;
  }

  .suggestion-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: flex-end;
  }

  .suggestion-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .suggestion-button.apply {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
  }

  .suggestion-button.apply:hover {
    background: rgba(16, 185, 129, 0.3);
    border-color: #10b981;
    transform: translateY(-1px);
  }

  .suggestion-button.dismiss {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  .suggestion-button.dismiss:hover {
    background: rgba(239, 68, 68, 0.3);
    border-color: #ef4444;
    transform: translateY(-1px);
  }

  .no-suggestions {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 3rem;
    color: var(--text-secondary);
    text-align: center;
  }

  .no-suggestions h4 {
    color: var(--text-primary);
    margin: 0;
  }

  .no-suggestions p {
    margin: 0;
    font-size: 0.9rem;
    opacity: 0.8;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .relationship-suggestions-modal {
      width: 95%;
      margin: 1rem;
    }

    .suggestions-settings {
      flex-direction: column;
    }

    .suggestion-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .suggestion-actions {
      justify-content: center;
      width: 100%;
    }

    .suggestion-button {
      flex: 1;
      justify-content: center;
    }
  }

  /* Knowledge Gap Analysis Modal */
  .gap-analysis-modal {
    max-width: 1000px;
    max-height: 90vh;
    overflow-y: auto;
  }

  /* Semantic Clustering Modal */
  .semantic-clustering-modal {
    max-width: 1000px;
    max-height: 90vh;
    overflow-y: auto;
  }

  .clustering-controls {
    display: flex;
    gap: 1rem;
    align-items: end;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
  }

  .run-clustering-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.2s ease;
    height: fit-content;
  }

  .run-clustering-button:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }

  .run-clustering-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .loading-clustering {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 2rem;
    color: #e2e8f0;
  }

  .clustering-results {
    animation: fadeIn 0.3s ease-in;
  }

  .clustering-summary {
    margin-bottom: 2rem;
  }

  .clusters-section {
    margin-bottom: 2rem;
  }

  .clusters-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .clear-highlights-button {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.2s ease;
  }

  .clear-highlights-button:hover {
    background: rgba(239, 68, 68, 0.2);
    border-color: rgba(239, 68, 68, 0.5);
  }

  .clusters-list {
    display: grid;
    gap: 1rem;
  }

  .cluster-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .cluster-card:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(102, 126, 234, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  .cluster-card.selected {
    background: rgba(102, 126, 234, 0.1);
    border-color: rgba(102, 126, 234, 0.5);
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
  }

  .cluster-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
  }

  .cluster-info {
    flex: 1;
  }

  .cluster-name {
    font-size: 1rem;
    font-weight: 600;
    color: #f1f5f9;
    margin: 0 0 0.25rem 0;
  }

  .cluster-meta {
    display: flex;
    gap: 0.75rem;
    font-size: 0.75rem;
  }

  .cluster-type {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    font-weight: 500;
  }

  .cluster-domain {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    font-weight: 500;
  }

  .cluster-stats {
    display: flex;
    gap: 1rem;
    text-align: center;
  }

  .cohesion-score, .entity-count {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.125rem;
  }

  .score-value, .count-value {
    font-size: 1.125rem;
    font-weight: 700;
    color: #667eea;
  }

  .score-label, .count-label {
    font-size: 0.6875rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }

  .cluster-description {
    color: #cbd5e1;
    font-size: 0.875rem;
    line-height: 1.4;
    margin-bottom: 0.75rem;
  }

  .cluster-keywords {
    margin-bottom: 0.75rem;
  }

  .keywords-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
    margin-top: 0.375rem;
  }

  .keyword-tag {
    background: rgba(139, 92, 246, 0.2);
    color: #8b5cf6;
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .cluster-entities {
    margin-bottom: 0.75rem;
  }

  .entities-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
    margin-top: 0.375rem;
  }

  .entity-name {
    background: rgba(255, 255, 255, 0.05);
    color: #e2e8f0;
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .entity-more {
    background: rgba(107, 114, 128, 0.3);
    color: #9ca3af;
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-style: italic;
  }

  .central-entity {
    color: #fbbf24;
    font-size: 0.875rem;
  }

  .unclustered-section {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .unclustered-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
    margin-top: 0.75rem;
  }

  .unclustered-entity {
    background: rgba(107, 114, 128, 0.2);
    color: #9ca3af;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    border: 1px dashed rgba(107, 114, 128, 0.3);
  }

  .confidence-value {
    margin-left: 0.5rem;
    color: #94a3b8;
    font-size: 0.875rem;
    font-weight: 500;
  }

  /* Cluster highlighting styles */
  .node.cluster-highlighted {
    stroke: #667eea !important;
    stroke-width: 3px !important;
    filter: drop-shadow(0 0 8px rgba(102, 126, 234, 0.8));
  }

  .node.cluster-dimmed {
    opacity: 0.3;
  }

  .edge.cluster-highlighted {
    stroke: #667eea !important;
    stroke-width: 3px !important;
    opacity: 1 !important;
  }

  .edge.cluster-dimmed {
    opacity: 0.2;
  }

  /* Analytics Dashboard Modal */
  .analytics-dashboard-modal {
    max-width: 1200px;
    max-height: 90vh;
    overflow-y: auto;
  }

  .loading-analytics {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 3rem;
    color: #e2e8f0;
  }

  .analytics-results {
    animation: fadeIn 0.3s ease-in;
  }

  .analytics-section {
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
  }

  .analytics-section h4 {
    color: #f1f5f9;
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0.5rem;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .stat-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 1rem;
    text-align: center;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: #667eea;
    margin-bottom: 0.25rem;
  }

  .stat-label {
    font-size: 0.875rem;
    color: #94a3b8;
    font-weight: 500;
    margin-bottom: 0.5rem;
  }

  .stat-detail {
    font-size: 0.75rem;
    color: #cbd5e1;
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .entity-type-stat {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.6875rem;
  }

  .paths-analysis {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .path-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 0.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .path-connection {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
  }

  .path-start, .path-end {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .path-stats {
    display: flex;
    gap: 0.75rem;
    font-size: 0.75rem;
  }

  .path-count {
    color: #94a3b8;
  }

  .path-confidence {
    color: #667eea;
    font-weight: 500;
  }

  .clusters-preview {
    display: grid;
    gap: 1rem;
  }

  .cluster-preview-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 1rem;
  }

  .cluster-preview-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .cluster-preview-header h5 {
    color: #f1f5f9;
    font-size: 0.875rem;
    font-weight: 600;
    margin: 0;
    flex: 1;
  }

  .cluster-preview-stats {
    display: flex;
    gap: 0.75rem;
    font-size: 0.75rem;
  }

  .cluster-preview-stats .cohesion {
    color: #667eea;
    font-weight: 600;
  }

  .cluster-preview-stats .entity-count {
    color: #94a3b8;
  }

  .cluster-preview-meta {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .cluster-preview-type {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.6875rem;
    font-weight: 500;
  }

  .cluster-preview-domain {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.6875rem;
    font-weight: 500;
  }

  .cluster-preview-keywords {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .preview-keyword {
    background: rgba(139, 92, 246, 0.2);
    color: #8b5cf6;
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.6875rem;
  }

  .gaps-summary {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .gap-summary-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 0.75rem;
  }

  .gap-summary-item.critical {
    border-left: 3px solid #dc2626;
    background: rgba(220, 38, 38, 0.05);
  }

  .gap-summary-item.high {
    border-left: 3px solid #f59e0b;
    background: rgba(245, 158, 11, 0.05);
  }

  .gap-summary-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .gap-severity-badge {
    padding: 0.125rem 0.5rem;
    border-radius: 3px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .gap-severity-badge.critical {
    background: rgba(220, 38, 38, 0.2);
    color: #dc2626;
  }

  .gap-severity-badge.high {
    background: rgba(245, 158, 11, 0.2);
    color: #f59e0b;
  }

  .gap-severity-badge.medium {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
  }

  .gap-title {
    color: #f1f5f9;
    font-weight: 500;
    flex: 1;
  }

  .gap-description {
    color: #cbd5e1;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
  }

  .gap-domain {
    color: #94a3b8;
    font-size: 0.75rem;
    font-style: italic;
  }

  .suggestions-summary {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .suggestions-stats {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 6px;
  }

  .suggestions-count {
    color: #f1f5f9;
    font-weight: 500;
  }

  .avg-confidence {
    color: #667eea;
    font-size: 0.875rem;
  }

  .top-suggestions {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .suggestion-preview {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 4px;
  }

  .suggestion-entities {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
  }

  .suggestion-source, .suggestion-target {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.75rem;
  }

  .suggestion-relationship {
    color: #94a3b8;
    font-size: 0.75rem;
    font-style: italic;
  }

  .suggestion-confidence {
    color: #667eea;
    font-weight: 600;
    font-size: 0.75rem;
  }

  .domains-health {
    display: grid;
    gap: 1rem;
  }

  .domain-health-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 1rem;
  }

  .domain-name {
    color: #f1f5f9;
    font-weight: 600;
    margin-bottom: 0.75rem;
  }

  .domain-metrics {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .domain-metric {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .metric-label {
    color: #94a3b8;
    font-size: 0.875rem;
    min-width: 80px;
  }

  .metric-bar {
    flex: 1;
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    overflow: hidden;
  }

  .metric-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    transition: width 0.3s ease;
  }

  .metric-value {
    color: #667eea;
    font-weight: 600;
    font-size: 0.875rem;
    min-width: 40px;
    text-align: right;
  }

  .domain-stats {
    display: flex;
    gap: 1rem;
    font-size: 0.75rem;
    color: #cbd5e1;
  }

  .retry-button {
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid rgba(59, 130, 246, 0.3);
    color: #3b82f6;
    padding: 0.5rem 0.75rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-left: 1rem;
    transition: all 0.2s ease;
  }

  .retry-button:hover {
    background: rgba(59, 130, 246, 0.3);
    border-color: rgba(59, 130, 246, 0.5);
  }

  .analysis-controls {
    display: flex;
    gap: 1rem;
    align-items: end;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .control-group label {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .control-group select {
    padding: 0.5rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    color: var(--text-primary);
    font-size: 0.9rem;
  }

  .run-analysis-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--neural-green);
    color: #000;
    border: none;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
  }

  .run-analysis-button:hover:not(:disabled) {
    background: #00ff64;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 255, 100, 0.3);
  }

  .run-analysis-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .loading-analysis {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 3rem;
    color: var(--text-secondary);
  }

  .analysis-results {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .analysis-summary h4 {
    color: var(--neural-green);
    margin-bottom: 1rem;
    font-size: 1.1rem;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .summary-item {
    text-align: center;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
  }

  .summary-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--neural-green);
    margin-bottom: 0.25rem;
  }

  .summary-label {
    font-size: 0.8rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .gaps-section h4,
  .domains-section h4,
  .recommendations-section h4 {
    color: var(--text-primary);
    margin-bottom: 1rem;
    font-size: 1.1rem;
  }

  .gaps-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .gap-item {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.2s ease;
  }

  .gap-item:hover {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .gap-item.high-severity {
    border-color: rgba(234, 88, 12, 0.3);
    background: rgba(234, 88, 12, 0.05);
  }

  .gap-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .gap-severity {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .severity-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .gap-confidence {
    font-size: 0.8rem;
    color: var(--text-secondary);
    font-weight: 500;
  }

  .gap-title {
    color: var(--text-primary);
    font-size: 1rem;
    margin: 0 0 0.5rem 0;
    font-weight: 500;
  }

  .gap-description {
    color: var(--text-secondary);
    font-size: 0.9rem;
    line-height: 1.4;
    margin: 0 0 0.75rem 0;
  }

  .gap-domain,
  .affected-entities {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
  }

  .suggested-actions {
    margin-top: 0.75rem;
  }

  .suggested-actions strong {
    color: var(--text-primary);
    font-size: 0.8rem;
  }

  .suggested-actions ul {
    margin: 0.5rem 0 0 1rem;
    padding: 0;
  }

  .suggested-actions li {
    color: var(--text-secondary);
    font-size: 0.8rem;
    line-height: 1.4;
    margin-bottom: 0.25rem;
  }

  .domains-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
  }

  .domain-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.2s ease;
  }

  .domain-card:hover {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .domain-card.weak-domain {
    border-color: rgba(234, 88, 12, 0.3);
    background: rgba(234, 88, 12, 0.05);
  }

  .domain-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .domain-name {
    color: var(--text-primary);
    font-size: 1rem;
    margin: 0;
    font-weight: 500;
  }

  .domain-score {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--neural-green);
  }

  .domain-metrics {
    display: flex;
    justify-content: space-between;
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
  }

  .metric {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }

  .metric-label {
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .metric-value {
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .key-entities,
  .missing-concepts {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
    line-height: 1.4;
  }

  .key-entities strong,
  .missing-concepts strong {
    color: var(--text-primary);
  }

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
    background: rgba(0, 255, 100, 0.05);
    border: 1px solid rgba(0, 255, 100, 0.1);
    border-radius: 6px;
    color: var(--text-secondary);
    font-size: 0.9rem;
    line-height: 1.4;
  }

  .recommendation-item :global(.icon) {
    color: var(--neural-green);
    flex-shrink: 0;
    margin-top: 0.1rem;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .gap-analysis-modal, .semantic-clustering-modal {
      width: 95%;
      margin: 1rem;
    }

    .analysis-controls, .clustering-controls {
      flex-direction: column;
      align-items: stretch;
    }

    .cluster-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .cluster-stats {
      align-self: flex-end;
    }

    .summary-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .domains-grid {
      grid-template-columns: 1fr;
    }

    .gap-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .domain-metrics {
      flex-direction: column;
      gap: 0.5rem;
    }

    .metric {
      flex-direction: row;
      justify-content: space-between;
    }
  }
</style>