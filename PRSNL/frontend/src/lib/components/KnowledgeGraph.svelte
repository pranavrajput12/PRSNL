<script lang="ts" type="module">
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import type { KnowledgeGraph, KnowledgeGraphNode, KnowledgeGraphLink } from '$lib/types/api';

  // Props
  export let data: KnowledgeGraph = { nodes: [], links: [] };
  export let selectedCluster: string | null = null;

  // Internal state
  let svg: SVGSVGElement;
  let width = 0;
  let height = 0;
  let container: HTMLDivElement;
  let simulation: d3.Simulation<KnowledgeGraphNode, KnowledgeGraphLink>;
  let zoomHandler: d3.ZoomBehavior<SVGSVGElement, unknown>;
  let tooltip: HTMLDivElement;

  // Reactive statements
  $: if (data && data.nodes && data.links && svg) {
    setupVisualization();
  }

  $: if (selectedCluster !== null && svg) {
    highlightCluster(selectedCluster);
  }

  onMount(() => {
    // Get container dimensions
    if (container) {
      const rect = container.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
    }

    // Set up resize handler
    const resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        width = entry.contentRect.width;
        height = entry.contentRect.height;
        if (data && data.nodes && data.links) {
          setupVisualization();
        }
      }
    });

    if (container) {
      resizeObserver.observe(container);
    }

    return () => {
      if (container) {
        resizeObserver.unobserve(container);
      }
      if (simulation) {
        simulation.stop();
      }
    };
  });

  function setupVisualization() {
    // Clear previous visualization
    d3.select(svg).selectAll('*').remove();

    // Create a color scale for node types
    const color = d3
      .scaleOrdinal()
      .domain(['article', 'video', 'note', 'bookmark', 'topic'])
      .range(['#dc143c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']);

    // Create a size scale for nodes based on importance
    const size = d3
      .scaleLinear()
      .domain([0, d3.max(data.nodes, (d) => d.importance || 1) || 1])
      .range([5, 15]);

    // Create the main SVG group that will contain our visualization
    const g = d3.select(svg).append('g');

    // Add zoom behavior
    zoomHandler = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
        g.attr('transform', event.transform.toString());
      });

    d3.select(svg).call(zoomHandler);

    // Create links
    const links = g
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(data.links)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', '0.6')
      .attr('stroke-width', (d) => String(Math.sqrt(d.value || 1)));

    // Create nodes
    const nodes = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(data.nodes)
      .enter()
      .append('g')
      .attr('class', (d) => `node node-${d.id}`)
      .attr('data-cluster', (d) => d.cluster || '')
      .style('cursor', 'pointer')
      .on('mouseover', (event: MouseEvent, d: KnowledgeGraphNode) => showNodeTooltip(event, d))
      .on('mouseout', hideTooltip)
      .on('click', (event: MouseEvent, d: KnowledgeGraphNode) => {
        if (d.id) {
          if (d.type === 'topic') {
            highlightCluster(d.id);
          } else if (d.url) {
            window.open(d.url, '_blank');
          }
        }
      })
      .call(
        d3
          .drag<SVGGElement, KnowledgeGraphNode>()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended) as any
      );

    // Add circles to nodes
    nodes
      .append('circle')
      .attr('r', (d: KnowledgeGraphNode) => String(size(d.importance || 1)))
      .attr('fill', (d: KnowledgeGraphNode) => color(d.type || 'default'))
      .attr('stroke', '#fff')
      .attr('stroke-width', '1.5');

    // Add icons to nodes based on type
    nodes
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-family', 'FontAwesome')
      .attr('font-size', (d) => `${size(d.importance || 1) * 0.8}`)
      .attr('fill', '#fff')
      .text((d) => {
        switch (d.type) {
          case 'article':
            return '\uf15c'; // file-text
          case 'video':
            return '\uf03d'; // video
          case 'note':
            return '\uf249'; // sticky-note
          case 'bookmark':
            return '\uf02e'; // bookmark
          case 'topic':
            return '\uf02c'; // tag
          default:
            return '';
        }
      });

    // Add labels to important nodes
    nodes
      .filter((d) => (d.importance || 0) > 0.7 || d.type === 'topic')
      .append('text')
      .attr('class', 'node-label')
      .text((d) => d.name || '')
      .attr('x', (d) => `${size(d.importance || 1) + 5}`)
      .attr('y', '4')
      .attr('font-size', '12px')
      .attr('fill', 'var(--text-primary)')
      .style('pointer-events', 'none');

    // Create tooltip if it doesn't exist
    if (!tooltip) {
      tooltip = d3
        .select<HTMLDivElement, unknown>(container)
        .append('div')
        .attr('class', 'tooltip')
        .style('opacity', '0')
        .style('position', 'absolute')
        .style('background', 'var(--bg-secondary)')
        .style('color', 'var(--text-primary)')
        .style('border', '1px solid var(--border)')
        .style('border-radius', '4px')
        .style('padding', '8px 12px')
        .style('font-size', '12px')
        .style('pointer-events', 'none')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.15)')
        .style('z-index', '100')
        .node() as HTMLDivElement;
    }

    // Create the force simulation
    simulation = d3
      .forceSimulation<KnowledgeGraphNode>(data.nodes)
      .force(
        'link',
        d3
          .forceLink<KnowledgeGraphNode, KnowledgeGraphLink>(data.links)
          .id((d) => d.id)
          .distance(100)
      )
      .force('charge', d3.forceManyBody<KnowledgeGraphNode>().strength(-100))
      .force('center', d3.forceCenter<KnowledgeGraphNode>(width / 2, height / 2))
      .force(
        'collision',
        d3.forceCollide<KnowledgeGraphNode>().radius((d) => Number(size(d.importance || 1)) + 15)
      )
      .on('tick', ticked);

    // Update positions on each tick
    function ticked() {
      links
        .attr('x1', (d) => (d.source as KnowledgeGraphNode).x || 0)
        .attr('y1', (d) => (d.source as KnowledgeGraphNode).y || 0)
        .attr('x2', (d) => (d.target as KnowledgeGraphNode).x || 0)
        .attr('y2', (d) => (d.target as KnowledgeGraphNode).y || 0);

      nodes.attr('transform', (d) => {
        // Keep nodes within bounds
        d.x = Math.max(20, Math.min(width - 20, d.x || 0));
        d.y = Math.max(20, Math.min(height - 20, d.y || 0));
        return `translate(${d.x || 0},${d.y || 0})`;
      });
    }

    // Drag functions
    function dragstarted(
      event: d3.D3DragEvent<SVGGElement, KnowledgeGraphNode, KnowledgeGraphNode>
    ) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, KnowledgeGraphNode, KnowledgeGraphNode>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, KnowledgeGraphNode, KnowledgeGraphNode>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Center the graph initially
    zoomHandler.translateTo(d3.select(svg), width / 2, height / 2);
  }

  function showNodeTooltip(event: MouseEvent, d: KnowledgeGraphNode) {
    const typeLabels: Record<string, string> = {
      article: 'Article',
      video: 'Video',
      note: 'Note',
      bookmark: 'Bookmark',
      topic: 'Topic',
    };

    let html = `
      <div style="font-weight: 500;">${d.name}</div>
      <div>Type: ${typeLabels[d.type as keyof typeof typeLabels] || d.type}</div>
    `;

    if (d.date) {
      html += `<div>Date: ${new Date(d.date).toLocaleDateString()}</div>`;
    }

    if (d.connections) {
      html += `<div>Connections: ${d.connections}</div>`;
    }

    // Use d3 selection methods for tooltip
    d3.select(tooltip).transition().duration(200).style('opacity', '0.9');

    d3.select(tooltip)
      .html(html)
      .style('left', `${event.pageX + 10}px`)
      .style('top', `${event.pageY - 28}px`);
  }

  function hideTooltip() {
    d3.select(tooltip).transition().duration(500).style('opacity', '0');
  }

  function highlightCluster(clusterId: string) {
    // Reset all nodes and links
    d3.select(svg).selectAll('.node').style('opacity', '0.3');

    d3.select(svg).selectAll('line').style('opacity', '0.1');

    // Highlight nodes in the selected cluster
    d3.select(svg).selectAll(`.node[data-cluster="${clusterId}"]`).style('opacity', '1');

    // Highlight links within the cluster
    d3.select(svg)
      .selectAll('line')
      .each(function (datum: unknown) {
        const link = datum as KnowledgeGraphLink;
        const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
        const targetId = typeof link.target === 'string' ? link.target : link.target.id;
        const sourceNode = data.nodes.find((n) => n.id === sourceId);
        const targetNode = data.nodes.find((n) => n.id === targetId);
        if (sourceNode?.cluster === clusterId && targetNode?.cluster === clusterId) {
          d3.select(this)
            .style('opacity', '0.8')
            .style('stroke', 'var(--accent)')
            .style('stroke-width', '2');
        }
      });

    // Zoom to the cluster
    const clusterNodes = data.nodes.filter((node) => node.cluster === clusterId);
    if (clusterNodes.length > 0) {
      zoomToNodes(clusterNodes);
    }
  }

  function highlightConnections(nodeId: string) {
    // Reset all nodes and links
    d3.select(svg).selectAll('.node').style('opacity', '0.3');

    d3.select(svg).selectAll('line').style('opacity', '0.1');

    // Highlight the selected node
    d3.select(svg).select(`.node-${nodeId}`).style('opacity', '1');

    // Find connected nodes
    const connectedLinks = data.links.filter((link: KnowledgeGraphLink) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target.id;
      return sourceId === nodeId || targetId === nodeId;
    });

    const connectedNodeIds = new Set<string>();
    connectedLinks.forEach((link: KnowledgeGraphLink) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target.id;
      connectedNodeIds.add(sourceId);
      connectedNodeIds.add(targetId);
    });

    // Highlight connected nodes
    connectedNodeIds.forEach((id) => {
      d3.select(svg).select(`.node-${id}`).style('opacity', '1');
    });

    // Highlight connected links
    d3.select(svg)
      .selectAll('line')
      .each(function (datum: unknown) {
        const link = datum as KnowledgeGraphLink;
        const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
        const targetId = typeof link.target === 'string' ? link.target : link.target.id;
        if (sourceId === nodeId || targetId === nodeId) {
          d3.select(this)
            .style('opacity', '0.8')
            .style('stroke', 'var(--accent)')
            .style('stroke-width', '2');
        }
      });

    // Zoom to the connected nodes
    const nodesToZoom = data.nodes.filter((node) => connectedNodeIds.has(node.id));
    if (nodesToZoom.length > 0) {
      zoomToNodes(nodesToZoom);
    }
  }

  function zoomToNodes(nodes: KnowledgeGraphNode[]) {
    if (!nodes.length) return;

    // Calculate the bounding box
    const padding = 50;
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;

    nodes.forEach((node) => {
      minX = Math.min(minX, node.x || 0);
      minY = Math.min(minY, node.y || 0);
      maxX = Math.max(maxX, node.x || 0);
      maxY = Math.max(maxY, node.y || 0);
    });

    // Add padding
    minX -= padding;
    minY -= padding;
    maxX += padding;
    maxY += padding;

    // Calculate scale and translate
    const dx = maxX - minX;
    const dy = maxY - minY;
    const scale = Math.min(width / dx, height / dy, 2); // Limit zoom level
    const x = (minX + maxX) / 2;
    const y = (minY + maxY) / 2;

    // Apply zoom transform
    d3.select(svg)
      .transition()
      .duration(750)
      .call(
        zoomHandler.transform as any,
        d3.zoomIdentity
          .translate(width / 2, height / 2)
          .scale(scale)
          .translate(-x, -y)
      );
  }

  function resetHighlighting() {
    d3.select(svg).selectAll('.node').style('opacity', '1');

    d3.select(svg)
      .selectAll('line')
      .style('opacity', '0.6')
      .style('stroke', '#999')
      .style('stroke-width', function (this: SVGLineElement, datum: unknown) {
        const link = datum as KnowledgeGraphLink;
        return String(Math.sqrt(link.value || 1));
      });

    // Reset zoom
    d3.select(svg)
      .transition()
      .duration(750)
      .call(
        zoomHandler.transform as any,
        d3.zoomIdentity.translate(width / 2, height / 2).scale(1)
      );
  }
</script>

<div class="knowledge-graph" bind:this={container}>
  {#if data && data.nodes && data.nodes.length > 0}
    <svg bind:this={svg} {width} {height}></svg>
    <div class="controls">
      <button class="reset-button" on:click={resetHighlighting}>
        <span class="icon">⟲</span> Reset View
      </button>
    </div>
  {:else}
    <div class="empty-state">
      <p>No knowledge graph data available</p>
    </div>
  {/if}
</div>

<style>
  .knowledge-graph {
    width: 100%;
    height: 100%;
    min-height: 400px;
    position: relative;
    background: var(--bg-primary);
    border-radius: 8px;
    overflow: hidden;
  }

  svg {
    width: 100%;
    height: 100%;
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
  }

  .controls {
    position: absolute;
    bottom: 20px;
    right: 20px;
    z-index: 10;
  }

  .reset-button {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 8px 12px;
    color: var(--text-primary);
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease;
  }

  .reset-button:hover {
    background: var(--bg-hover);
  }

  .icon {
    font-size: 16px;
  }

  :global(.node-label) {
    text-shadow:
      1px 1px 2px var(--bg-primary),
      -1px 1px 2px var(--bg-primary),
      1px -1px 2px var(--bg-primary),
      -1px -1px 2px var(--bg-primary);
  }
</style>
