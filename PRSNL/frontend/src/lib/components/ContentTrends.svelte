<script lang="ts">
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  
  interface DataPoint {
    date: Date;
    value: number;
    articles?: number;
    videos?: number;
    notes?: number;
    bookmarks?: number;
    label?: string;
  }
  
  // Props
  export let data: DataPoint[] = [];
  export let timeRange = 'week';
  
  // Internal state
  let svg: SVGSVGElement;
  let width = 0;
  let height = 0;
  let container: HTMLDivElement;
  let tooltip: HTMLDivElement;
  
  // Reactive statements
  $: if (data && data.length && svg) {
    setupVisualization();
  }
  
  $: if (timeRange && data && data.length && svg) {
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
    };
  });
  
  function setupVisualization() {
    // Clear previous visualization
    d3.select(svg).selectAll("*").remove();
    
    // Set margins
    const margin = { top: 20, right: 30, bottom: 40, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // Create scales
    const x = d3.scaleTime()
      .domain(d3.extent(data, d => d.date) as [Date, Date])
      .range([0, innerWidth]);
    
    const y = d3.scaleLinear()
      .domain([0, d3.max(data, d => Math.max(
        d.articles || 0,
        d.videos || 0,
        d.notes || 0,
        d.bookmarks || 0
      )) || 0])
      .nice()
      .range([innerHeight, 0]);
    
    // Create a color scale
    const color = d3.scaleOrdinal()
      .domain(['articles', 'videos', 'notes', 'bookmarks'])
      .range(['#dc143c', '#3498db', '#2ecc71', '#f39c12']);
    
    // Create the SVG group
    const g = d3.select(svg)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // Add the x-axis
    g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(getXAxis())
      .selectAll("text")
      .attr("y", "10")
      .attr("x", "-5")
      .attr("text-anchor", "end")
      .attr("transform", "rotate(-45)");
    
    // Add the y-axis
    g.append("g")
      .attr("class", "y-axis")
      .call(d3.axisLeft(y).ticks(5))
      .append("text")
      .attr("fill", "var(--text-secondary)")
      .attr("transform", "rotate(-90)")
      .attr("y", "-40")
      .attr("x", `${-innerHeight / 2}`)
      .attr("text-anchor", "middle")
      .text("Item Count");
    
    // Create line generators
    const line = d3.line<{date: Date, value: number | undefined}>()
      .x(d => x(new Date(d.date)))
      .y(d => y(d.value || 0))
      .curve(d3.curveMonotoneX);
    
    // Prepare data for lines
    const keys = ['articles', 'videos', 'notes', 'bookmarks'] as const;
    type ContentKey = typeof keys[number];
    
    const series = keys.map(key => ({
      name: key,
      values: data.map(d => ({ 
        date: d.date, 
        value: d[key as keyof Pick<DataPoint, ContentKey>] as number | undefined 
      }))
    }));
    
    // Add lines
    g.selectAll(".line")
      .data(series)
      .enter()
      .append("path")
      .attr("class", "line")
      .attr("d", d => line(d.values) || "")
      .attr("fill", "none")
      .attr("stroke", d => color(d.name) as string)
      .attr("stroke-width", "2")
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round");
    
    // Add dots
    series.forEach(s => {
      g.selectAll(`.dot-${s.name}`)
        .data(s.values)
        .enter()
        .append("circle")
        .attr("class", `dot dot-${s.name}`)
        .attr("cx", d => x(new Date(d.date)))
        .attr("cy", d => y(d.value || 0))
        .attr("r", "4")
        .attr("fill", color(s.name) as string)
        .attr("stroke", "#fff")
        .attr("stroke-width", "1.5")
        .on("mouseover", function(event: MouseEvent, d: {date: Date, value: number | undefined}) {
          showTooltip(event, {date: d.date, value: d.value || 0} as DataPoint, s.name);
        })
        .on("mouseout", hideTooltip);
    });
    
    // Add legend
    const legend = g.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${innerWidth - 120}, 0)`);
    
    keys.forEach((key, i) => {
      const legendRow = legend.append("g")
        .attr("transform", `translate(0, ${i * 20})`);
      
      legendRow.append("rect")
        .attr("width", "12")
        .attr("height", "12")
        .attr("fill", color(key) as string);
      
      legendRow.append("text")
        .attr("x", "20")
        .attr("y", "10")
        .attr("text-anchor", "start")
        .attr("dominant-baseline", "middle")
        .attr("font-size", "12px")
        .attr("fill", "var(--text-secondary)")
        .text(key.charAt(0).toUpperCase() + key.slice(1));
    });
    
    // Create tooltip
    if (!tooltip) {
      tooltip = d3.select<HTMLDivElement, unknown>(container)
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", "0")
        .style("position", "absolute")
        .style("background", "var(--bg-secondary)")
        .style("color", "var(--text-primary)")
        .style("border", "1px solid var(--border)")
        .style("border-radius", "4px")
        .style("padding", "8px 12px")
        .style("font-size", "12px")
        .style("pointer-events", "none")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("z-index", "100")
        .node() as HTMLDivElement;
    }
    
    function showTooltip(event: MouseEvent, d: DataPoint, type: string) {
      const formattedDate = new Date(d.date).toLocaleDateString();
      const formattedType = type.charAt(0).toUpperCase() + type.slice(1);
      
      d3.select(tooltip)
        .transition()
        .duration(200)
        .style("opacity", "0.9");
      
      d3.select(tooltip)
        .html(`
          <div style="font-weight: 500;">${formattedDate}</div>
          <div>${formattedType}: ${d.value}</div>
        `)
        .style("left", `${event.pageX + 10}px`)
        .style("top", `${event.pageY - 28}px`);
    }
    
    function hideTooltip() {
      d3.select(tooltip)
        .transition()
        .duration(500)
        .style("opacity", "0");
    }
    
    // Helper function to get appropriate x-axis based on timeRange
    function getXAxis() {
      switch (timeRange) {
        case 'day':
          return d3.axisBottom(x).ticks(24).tickFormat(d3.timeFormat('%H:%M'));
        case 'week':
          return d3.axisBottom(x).ticks(7).tickFormat(d3.timeFormat('%a'));
        case 'month':
          return d3.axisBottom(x).ticks(d3.timeDay.every(2)).tickFormat(d3.timeFormat('%d'));
        case 'year':
          return d3.axisBottom(x).ticks(12).tickFormat(d3.timeFormat('%b'));
        default:
          return d3.axisBottom(x).ticks(10).tickFormat(d3.timeFormat('%b %Y'));
      }
    }
  }
</script>

<div class="content-trends" bind:this={container}>
  {#if data && data.length > 0}
    <svg bind:this={svg} width={width} height={height}></svg>
  {:else}
    <div class="empty-state">
      <p>No trend data available</p>
    </div>
  {/if}
</div>

<style>
  .content-trends {
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
  
  :global(.x-axis path),
  :global(.y-axis path),
  :global(.x-axis line),
  :global(.y-axis line) {
    stroke: var(--border);
  }
  
  :global(.x-axis text),
  :global(.y-axis text) {
    fill: var(--text-secondary);
    font-size: 12px;
  }
  
  :global(.dot) {
    transition: r 0.2s ease;
  }
  
  :global(.dot:hover) {
    r: 6;
  }
</style>
