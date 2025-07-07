<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import * as d3 from 'd3';
  
  // Props
  export let data = [];
  
  // Internal state
  let svg;
  let width = 0;
  let height = 0;
  let simulation;
  let container;
  
  const dispatch = createEventDispatcher();
  
  // Set up the visualization when data changes or component mounts
  $: if (data && data.length && svg) {
    setupVisualization();
  }
  
  onMount(() => {
    // Get container dimensions
    if (container) {
      const rect = container.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
    }
    
    // Set up resize handler
    const resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        width = entry.contentRect.width;
        height = entry.contentRect.height;
        if (data && data.length) {
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
    d3.select(svg).selectAll("*").remove();
    
    // Create a color scale
    const color = d3.scaleOrdinal()
      .domain(data.map(d => d.group))
      .range(d3.schemeCategory10);
    
    // Create a size scale for nodes based on count
    const size = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.count)])
      .range([5, 20]);
    
    // Create the force simulation
    simulation = d3.forceSimulation(data)
      .force("charge", d3.forceManyBody().strength(-50))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(d => size(d.count) + 10))
      .on("tick", ticked);
    
    // Create node elements
    const nodes = d3.select(svg)
      .selectAll("g")
      .data(data)
      .enter()
      .append("g")
      .attr("class", "node")
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        dispatch('clusterSelect', { cluster: d.id });
      })
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));
    
    // Add circles to nodes
    nodes.append("circle")
      .attr("r", d => size(d.count))
      .attr("fill", d => color(d.group))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .attr("opacity", 0.8);
    
    // Add labels to nodes
    nodes.append("text")
      .text(d => d.name)
      .attr("text-anchor", "middle")
      .attr("dy", d => size(d.count) + 15)
      .attr("font-size", d => Math.min(14, 8 + size(d.count) / 5))
      .attr("fill", "var(--text-primary)")
      .attr("pointer-events", "none");
    
    // Add tooltips
    nodes.append("title")
      .text(d => `${d.name}\nItems: ${d.count}`);
    
    // Update node positions on each tick
    function ticked() {
      nodes
        .attr("transform", d => {
          // Keep nodes within bounds
          d.x = Math.max(size(d.count), Math.min(width - size(d.count), d.x));
          d.y = Math.max(size(d.count), Math.min(height - size(d.count), d.y));
          return `translate(${d.x},${d.y})`;
        });
    }
    
    // Drag functions
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }
    
    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }
  }
</script>

<div class="topic-clusters" bind:this={container}>
  {#if data && data.length > 0}
    <svg bind:this={svg} width={width} height={height}></svg>
  {:else}
    <div class="empty-state">
      <p>No topic clusters available</p>
    </div>
  {/if}
</div>

<style>
  .topic-clusters {
    width: 100%;
    height: 100%;
    min-height: 300px;
    position: relative;
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
  
  :global(.node:hover circle) {
    opacity: 1;
    stroke: var(--accent);
    stroke-width: 2px;
  }
  
  :global(.node:hover text) {
    font-weight: 600;
  }
</style>
