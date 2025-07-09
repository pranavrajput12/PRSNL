<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { spring, tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  
  // Define interfaces for our data
  interface TopicCluster {
    id: string;
    name: string;
    count: number;
    group: string;
    percentage?: number;
  }
  
  interface TreeNode {
    id: string;
    name: string;
    count: number;
    x: number;
    y: number;
    z: number;
    size: number;
    color: string;
    depth: number;
    children: TreeNode[];
    parent: TreeNode | null;
    angle: number;
    growth: number;
    pulsePhase: number;
    branchWidth: number;
  }
  
  // Props
  export let data: TopicCluster[] = [];
  
  // Internal state
  let container: HTMLDivElement;
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let width = 0;
  let height = 0;
  let treeNodes: TreeNode[] = [];
  let hoveredNode: TreeNode | null = null;
  let animationFrame: number;
  let time = 0;
  let rotationY = 0;
  let rotationX = 0;
  
  const dispatch = createEventDispatcher();
  
  // Organic tree colors (earthy, natural tones)
  const organicColors = [
    '#8B4513', // Saddle Brown
    '#228B22', // Forest Green
    '#CD853F', // Peru
    '#2E8B57', // Sea Green
    '#A0522D', // Sienna
    '#6B8E23', // Olive Drab
    '#D2691E', // Chocolate
    '#32CD32', // Lime Green
    '#8FBC8F', // Dark Sea Green
    '#9ACD32'  // Yellow Green
  ];
  
  // 3D projection settings
  const camera = {
    x: 0,
    y: 0,
    z: 500,
    fov: 300
  };
  
  $: if (data && data.length && canvas) {
    generateOrganicTree();
    startAnimation();
  }
  
  onMount(() => {
    if (container) {
      const rect = container.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
    }
    
    if (canvas) {
      ctx = canvas.getContext('2d')!;
      canvas.width = width;
      canvas.height = height;
    }
    
    const resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        width = entry.contentRect.width;
        height = entry.contentRect.height;
        if (canvas) {
          canvas.width = width;
          canvas.height = height;
        }
        if (data && data.length) {
          generateOrganicTree();
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
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  });
  
  function generateOrganicTree() {
    const maxCount = Math.max(...data.map(d => d.count));
    const sortedData = [...data].sort((a, b) => b.count - a.count);
    
    // Create root node (trunk)
    const rootNode: TreeNode = {
      id: 'root',
      name: 'Knowledge Base',
      count: maxCount,
      x: 0,
      y: 100,
      z: 0,
      size: 15,
      color: '#8B4513',
      depth: 0,
      children: [],
      parent: null,
      angle: 0,
      growth: 1,
      pulsePhase: 0,
      branchWidth: 12
    };
    
    treeNodes = [rootNode];
    
    // Create branches for each topic
    sortedData.forEach((topic, index) => {
      const depth = Math.floor(index / 3) + 1;
      const parent = depth === 1 ? rootNode : treeNodes[Math.floor(Math.random() * treeNodes.length)];
      
      // Calculate branch position with 3D perspective
      const branchAngle = (index * 137.5) * (Math.PI / 180); // Golden angle for natural distribution
      const branchRadius = 80 + depth * 40;
      const heightOffset = -depth * 60;
      
      const node: TreeNode = {
        id: topic.id,
        name: topic.name,
        count: topic.count,
        x: Math.cos(branchAngle) * branchRadius,
        y: heightOffset,
        z: Math.sin(branchAngle) * branchRadius,
        size: Math.max(5, (topic.count / maxCount) * 20),
        color: organicColors[index % organicColors.length],
        depth,
        children: [],
        parent,
        angle: branchAngle,
        growth: 0.1 + Math.random() * 0.9,
        pulsePhase: Math.random() * Math.PI * 2,
        branchWidth: Math.max(2, (topic.count / maxCount) * 8)
      };
      
      parent.children.push(node);
      treeNodes.push(node);
    });
  }
  
  function startAnimation() {
    function animate() {
      if (!ctx || !canvas) return;
      
      time += 0.02;
      rotationY += 0.005;
      rotationX = Math.sin(time * 0.3) * 0.1;
      
      // Clear canvas with organic background
      const gradient = ctx.createRadialGradient(
        width / 2, height / 2, 0,
        width / 2, height / 2, Math.max(width, height) / 2
      );
      gradient.addColorStop(0, '#2F4F2F');
      gradient.addColorStop(1, '#1C3A1C');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);
      
      // Sort nodes by z-depth for proper 3D rendering
      const sortedNodes = [...treeNodes].sort((a, b) => {
        const aZ = rotateZ(a.x, a.z, rotationY);
        const bZ = rotateZ(b.x, b.z, rotationY);
        return bZ - aZ;
      });
      
      // Draw branches first
      drawBranches(sortedNodes);
      
      // Draw nodes (leaves/fruits)
      sortedNodes.forEach(node => {
        if (node.id !== 'root') {
          drawNode(node);
        }
      });
      
      // Draw root trunk
      drawTrunk();
      
      // Update growth animation
      treeNodes.forEach(node => {
        node.growth = Math.min(1, node.growth + 0.001);
        node.pulsePhase += 0.03;
      });
      
      animationFrame = requestAnimationFrame(animate);
    }
    
    animate();
  }
  
  function project3D(x: number, y: number, z: number) {
    // Apply rotations
    const rotatedX = rotateX(x, y, rotationX);
    const rotatedY = rotateY(x, y, rotationX);
    const rotatedZ = rotateZ(rotatedX, z, rotationY);
    const finalX = rotateX(rotatedX, rotatedZ, rotationY);
    
    // Project to 2D
    const distance = camera.z - rotatedZ;
    const scale = camera.fov / distance;
    
    return {
      x: width / 2 + finalX * scale,
      y: height / 2 + rotatedY * scale,
      z: rotatedZ,
      scale
    };
  }
  
  function rotateX(x: number, y: number, angle: number) {
    return x * Math.cos(angle) - y * Math.sin(angle);
  }
  
  function rotateY(x: number, y: number, angle: number) {
    return x * Math.sin(angle) + y * Math.cos(angle);
  }
  
  function rotateZ(x: number, z: number, angle: number) {
    return x * Math.sin(angle) + z * Math.cos(angle);
  }
  
  function drawBranches(nodes: TreeNode[]) {
    nodes.forEach(node => {
      if (node.parent) {
        const parentPos = project3D(node.parent.x, node.parent.y, node.parent.z);
        const nodePos = project3D(node.x, node.y, node.z);
        
        // Create organic branch curve
        const controlX = (parentPos.x + nodePos.x) / 2 + Math.sin(time + node.angle) * 20;
        const controlY = (parentPos.y + nodePos.y) / 2 + Math.cos(time + node.angle) * 15;
        
        // Branch gradient for 3D effect
        const gradient = ctx.createLinearGradient(
          parentPos.x, parentPos.y,
          nodePos.x, nodePos.y
        );
        gradient.addColorStop(0, '#8B4513');
        gradient.addColorStop(0.5, '#A0522D');
        gradient.addColorStop(1, '#CD853F');
        
        ctx.strokeStyle = gradient;
        ctx.lineWidth = node.branchWidth * nodePos.scale * node.growth;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        // Draw curved branch
        ctx.beginPath();
        ctx.moveTo(parentPos.x, parentPos.y);
        ctx.quadraticCurveTo(controlX, controlY, nodePos.x, nodePos.y);
        ctx.stroke();
        
        // Add branch texture
        ctx.globalAlpha = 0.3;
        ctx.strokeStyle = '#654321';
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
    });
  }
  
  function drawNode(node: TreeNode) {
    const pos = project3D(node.x, node.y, node.z);
    const size = node.size * pos.scale * node.growth;
    
    // Pulsing effect
    const pulse = 1 + Math.sin(node.pulsePhase) * 0.2;
    const finalSize = size * pulse;
    
    // Create 3D sphere gradient
    const gradient = ctx.createRadialGradient(
      pos.x - finalSize * 0.3, pos.y - finalSize * 0.3, 0,
      pos.x, pos.y, finalSize
    );
    
    const lightColor = lightenColor(node.color, 40);
    const darkColor = darkenColor(node.color, 30);
    
    gradient.addColorStop(0, lightColor);
    gradient.addColorStop(0.7, node.color);
    gradient.addColorStop(1, darkColor);
    
    // Draw main sphere
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, finalSize, 0, Math.PI * 2);
    ctx.fill();
    
    // Add highlight for 3D effect
    ctx.fillStyle = `rgba(255, 255, 255, 0.3)`;
    ctx.beginPath();
    ctx.arc(pos.x - finalSize * 0.3, pos.y - finalSize * 0.3, finalSize * 0.4, 0, Math.PI * 2);
    ctx.fill();
    
    // Add shadow
    ctx.fillStyle = `rgba(0, 0, 0, 0.2)`;
    ctx.beginPath();
    ctx.arc(pos.x + finalSize * 0.2, pos.y + finalSize * 0.2, finalSize * 0.8, 0, Math.PI * 2);
    ctx.fill();
    
    // Check for hover
    if (hoveredNode === node) {
      ctx.strokeStyle = '#FFD700';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, finalSize + 5, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
  
  function drawTrunk() {
    const trunkBase = project3D(0, 150, 0);
    const trunkTop = project3D(0, 0, 0);
    
    // Create trunk gradient
    const gradient = ctx.createLinearGradient(
      trunkBase.x, trunkBase.y,
      trunkTop.x, trunkTop.y
    );
    gradient.addColorStop(0, '#4A3C28');
    gradient.addColorStop(0.5, '#8B4513');
    gradient.addColorStop(1, '#A0522D');
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.moveTo(trunkBase.x - 15, trunkBase.y);
    ctx.lineTo(trunkBase.x + 15, trunkBase.y);
    ctx.lineTo(trunkTop.x + 8, trunkTop.y);
    ctx.lineTo(trunkTop.x - 8, trunkTop.y);
    ctx.closePath();
    ctx.fill();
    
    // Add trunk texture
    ctx.strokeStyle = '#654321';
    ctx.lineWidth = 2;
    for (let i = 0; i < 5; i++) {
      const y = trunkBase.y - (i * 30);
      ctx.beginPath();
      ctx.moveTo(trunkBase.x - 12, y);
      ctx.lineTo(trunkBase.x + 12, y);
      ctx.stroke();
    }
  }
  
  function lightenColor(color: string, percent: number) {
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = (num >> 8 & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    return `#${(0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
      (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
      (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1)}`;
  }
  
  function darkenColor(color: string, percent: number) {
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) - amt;
    const G = (num >> 8 & 0x00FF) - amt;
    const B = (num & 0x0000FF) - amt;
    return `#${(0x1000000 + (R > 255 ? 255 : R < 0 ? 0 : R) * 0x10000 +
      (G > 255 ? 255 : G < 0 ? 0 : G) * 0x100 +
      (B > 255 ? 255 : B < 0 ? 0 : B)).toString(16).slice(1)}`;
  }
  
  function handleMouseMove(event: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    
    hoveredNode = null;
    
    for (const node of treeNodes) {
      if (node.id === 'root') continue;
      
      const pos = project3D(node.x, node.y, node.z);
      const size = node.size * pos.scale * node.growth;
      
      const dx = mouseX - pos.x;
      const dy = mouseY - pos.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < size + 5) {
        hoveredNode = node;
        break;
      }
    }
  }
  
  function handleClick(event: MouseEvent) {
    if (hoveredNode) {
      dispatch('clusterSelect', { cluster: hoveredNode.id });
    }
  }
</script>

<div class="organic-tree" bind:this={container}>
  {#if data && data.length > 0}
    <canvas
      bind:this={canvas}
      {width}
      {height}
      on:mousemove={handleMouseMove}
      on:click={handleClick}
      style="cursor: {hoveredNode ? 'pointer' : 'default'}"
    />
    
    <!-- Topic tooltip -->
    {#if hoveredNode}
      <div 
        class="node-tooltip"
        style="left: {project3D(hoveredNode.x, hoveredNode.y, hoveredNode.z).x + 20}px; top: {project3D(hoveredNode.x, hoveredNode.y, hoveredNode.z).y - 10}px;"
      >
        <div class="tooltip-header">
          <span class="leaf-icon" style="color: {hoveredNode.color}">🍃</span>
          <span class="node-name">{hoveredNode.name}</span>
        </div>
        <div class="tooltip-stats">
          <span class="stat">
            <span class="stat-label">Knowledge Items:</span>
            <span class="stat-value">{hoveredNode.count}</span>
          </span>
          <span class="stat">
            <span class="stat-label">Branch Depth:</span>
            <span class="stat-value">{hoveredNode.depth}</span>
          </span>
          <span class="stat">
            <span class="stat-label">Growth:</span>
            <span class="stat-value">{Math.round(hoveredNode.growth * 100)}%</span>
          </span>
        </div>
      </div>
    {/if}
    
    <!-- Tree info -->
    <div class="tree-info">
      <h3>🌳 Knowledge Tree</h3>
      <div class="tree-stats">
        <div class="stat">
          <span class="stat-value">{data.length}</span>
          <span class="stat-label">Topics</span>
        </div>
        <div class="stat">
          <span class="stat-value">{data.reduce((sum, item) => sum + item.count, 0)}</span>
          <span class="stat-label">Total Items</span>
        </div>
      </div>
      <div class="growth-indicator">
        <div class="growth-bar">
          <div class="growth-fill" style="width: {Math.min(100, (time * 5) % 100)}%"></div>
        </div>
        <span class="growth-text">Growing...</span>
      </div>
    </div>
  {:else}
    <div class="empty-state">
      <div class="empty-icon">🌱</div>
      <p>Plant the first seed of knowledge to grow your tree</p>
    </div>
  {/if}
</div>

<style>
  .organic-tree {
    width: 100%;
    height: 100%;
    min-height: 400px;
    position: relative;
    background: radial-gradient(circle at 30% 70%, #2F4F2F 0%, #1C3A1C 50%, #0F2F0F 100%);
    border-radius: 12px;
    overflow: hidden;
  }
  
  canvas {
    width: 100%;
    height: 100%;
    display: block;
  }
  
  .node-tooltip {
    position: absolute;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 12px;
    border-radius: 8px;
    font-size: 14px;
    pointer-events: none;
    z-index: 10;
    border: 1px solid rgba(139, 69, 19, 0.5);
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    max-width: 250px;
  }
  
  .tooltip-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }
  
  .leaf-icon {
    font-size: 16px;
    filter: drop-shadow(0 0 4px currentColor);
  }
  
  .node-name {
    font-weight: 600;
    color: #90EE90;
  }
  
  .tooltip-stats {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .stat {
    display: flex;
    justify-content: space-between;
    gap: 16px;
  }
  
  .stat-label {
    color: rgba(255, 255, 255, 0.7);
    font-size: 12px;
  }
  
  .stat-value {
    color: white;
    font-weight: 500;
  }
  
  .tree-info {
    position: absolute;
    top: 16px;
    left: 16px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 16px;
    border-radius: 8px;
    font-size: 14px;
    border: 1px solid rgba(139, 69, 19, 0.5);
    backdrop-filter: blur(10px);
    max-width: 200px;
  }
  
  .tree-info h3 {
    margin: 0 0 12px 0;
    font-size: 16px;
    color: #90EE90;
  }
  
  .tree-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
  }
  
  .tree-stats .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .tree-stats .stat-value {
    font-size: 18px;
    font-weight: 600;
    color: #FFD700;
  }
  
  .tree-stats .stat-label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .growth-indicator {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .growth-bar {
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    overflow: hidden;
  }
  
  .growth-fill {
    height: 100%;
    background: linear-gradient(90deg, #228B22, #32CD32, #90EE90);
    transition: width 0.3s ease;
  }
  
  .growth-text {
    font-size: 12px;
    color: #90EE90;
    text-align: center;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: rgba(255, 255, 255, 0.6);
    text-align: center;
  }
  
  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
    color: #90EE90;
    filter: drop-shadow(0 0 8px currentColor);
  }
  
  .empty-state p {
    margin: 0;
    font-size: 16px;
  }
</style>