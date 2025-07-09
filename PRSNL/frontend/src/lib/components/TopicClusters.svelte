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
      height = Math.min(rect.height, 300); // Constrain max height
    }
    
    if (canvas) {
      ctx = canvas.getContext('2d')!;
      canvas.width = width;
      canvas.height = Math.min(height, 300); // Constrain canvas height
    }
    
    const resizeObserver = new ResizeObserver(entries => {
      for (let entry of entries) {
        width = entry.contentRect.width;
        height = Math.min(entry.contentRect.height, 300); // Constrain height
        if (canvas) {
          canvas.width = width;
          canvas.height = Math.min(height, 300); // Constrain canvas height
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
    if (!data || data.length === 0) {
      treeNodes = [];
      return;
    }

    const totalItems = data.reduce((sum, topic) => sum + topic.count, 0);
    const maxCount = Math.max(...data.map(d => d.count));
    
    // Filter topics based on milestone-based scoring system
    const filteredData = getSignificantTopics(data, totalItems);
    const sortedData = [...filteredData].sort((a, b) => b.count - a.count);
    
    // Create root node (trunk) - only show if we have significant data
    const rootNode: TreeNode = {
      id: 'root',
      name: 'Knowledge Base',
      count: totalItems,
      x: 0,
      y: 50, // Moved up to center better
      z: 0,
      size: Math.min(20, Math.max(10, totalItems / 50)), // Size based on total items
      color: '#8B4513',
      depth: 0,
      children: [],
      parent: null,
      angle: 0,
      growth: 1,
      pulsePhase: 0,
      branchWidth: Math.min(15, Math.max(8, totalItems / 30))
    };
    
    treeNodes = [rootNode];
    
    // Only create branches if we have meaningful data
    if (sortedData.length === 0) {
      return; // Just show the trunk until more data is collected
    }
    
    // Create branches with bounded growth system
    sortedData.forEach((topic, index) => {
      const { depth, layer, position } = calculateSmartPosition(index, sortedData.length, totalItems);
      const parent = findBestParent(depth, rootNode, treeNodes);
      
      // Calculate branch position with smart bounded growth
      const branchAngle = position.angle;
      const branchRadius = position.radius;
      const heightOffset = position.height;
      
      const node: TreeNode = {
        id: topic.id,
        name: topic.name,
        count: topic.count,
        x: Math.cos(branchAngle) * branchRadius,
        y: heightOffset,
        z: Math.sin(branchAngle) * branchRadius,
        size: Math.max(6, Math.min(25, (topic.count / maxCount) * 20 + 5)),
        color: organicColors[index % organicColors.length],
        depth,
        children: [],
        parent,
        angle: branchAngle,
        growth: 0.3 + Math.random() * 0.7, // Faster initial growth
        pulsePhase: Math.random() * Math.PI * 2,
        branchWidth: Math.max(3, Math.min(10, (topic.count / maxCount) * 8 + 2))
      };
      
      parent.children.push(node);
      treeNodes.push(node);
    });
  }
  
  // Milestone-based filtering: Only show topics that meet significance thresholds
  function getSignificantTopics(topics: TopicCluster[], totalItems: number) {
    // Define milestone thresholds for tree growth
    const milestones = {
      seedling: 10,    // 10+ items: Just trunk
      sapling: 50,     // 50+ items: First few branches
      young: 100,      // 100+ items: Small tree
      mature: 500,     // 500+ items: Full tree
      ancient: 1000    // 1000+ items: Massive tree
    };
    
    let minTopicSize = 1;
    let maxTopics = 3;
    
    if (totalItems >= milestones.ancient) {
      minTopicSize = 10; // Need 10+ items per topic
      maxTopics = 15;    // Up to 15 major branches
    } else if (totalItems >= milestones.mature) {
      minTopicSize = 5;  // Need 5+ items per topic
      maxTopics = 12;    // Up to 12 branches
    } else if (totalItems >= milestones.young) {
      minTopicSize = 3;  // Need 3+ items per topic
      maxTopics = 8;     // Up to 8 branches
    } else if (totalItems >= milestones.sapling) {
      minTopicSize = 2;  // Need 2+ items per topic
      maxTopics = 5;     // Up to 5 branches
    } else if (totalItems >= milestones.seedling) {
      minTopicSize = 1;  // Any topic counts
      maxTopics = 3;     // Just 3 small branches
    } else {
      return []; // Not enough data - just show trunk
    }
    
    return topics
      .filter(topic => topic.count >= minTopicSize)
      .slice(0, maxTopics);
  }
  
  // Smart positioning system that prevents infinite growth
  function calculateSmartPosition(index: number, totalTopics: number, totalItems: number) {
    // Maximum tree dimensions (bounded canvas)
    const maxHeight = 150;
    const maxRadius = 120;
    const minHeight = -100;
    
    // Calculate layer and position within layer
    const topicsPerLayer = Math.max(3, Math.ceil(Math.sqrt(totalTopics)));
    const layer = Math.floor(index / topicsPerLayer);
    const positionInLayer = index % topicsPerLayer;
    
    // Bounded depth calculation (max 3 layers to prevent infinite scrolling)
    const depth = Math.min(3, layer + 1);
    
    // Spiral positioning for natural look
    const angleStep = (2 * Math.PI) / Math.max(3, topicsPerLayer);
    const angle = positionInLayer * angleStep + layer * 0.5; // Offset each layer
    
    // Radius increases with layer but is bounded
    const baseRadius = 60;
    const radiusIncrement = Math.min(25, maxRadius / 4);
    const radius = Math.min(maxRadius, baseRadius + layer * radiusIncrement);
    
    // Height decreases with depth but is bounded
    const baseHeight = 20;
    const heightDecrement = Math.min(40, maxHeight / 4);
    const height = Math.max(minHeight, baseHeight - layer * heightDecrement);
    
    return {
      depth,
      layer,
      position: {
        angle,
        radius,
        height
      }
    };
  }
  
  // Find the best parent node for a new branch
  function findBestParent(targetDepth: number, rootNode: TreeNode, allNodes: TreeNode[]) {
    if (targetDepth === 1) {
      return rootNode;
    }
    
    // Find nodes at the previous depth level with fewer children
    const parentCandidates = allNodes.filter(node => 
      node.depth === targetDepth - 1 && node.children.length < 3
    );
    
    if (parentCandidates.length > 0) {
      // Choose the parent with the fewest children
      return parentCandidates.reduce((best, current) => 
        current.children.length < best.children.length ? current : best
      );
    }
    
    // Fallback to root if no good parent found
    return rootNode;
  }
  
  function startAnimation() {
    function animate() {
      if (!ctx || !canvas) return;
      
      try {
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
      } catch (error) {
        console.error('Canvas rendering error:', error);
        // Stop animation on error to prevent infinite loops
        if (animationFrame) {
          cancelAnimationFrame(animationFrame);
        }
      }
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
  
  // Get milestone progress percentage
  function getMilestoneProgress(totalItems: number) {
    const milestones = [10, 50, 100, 500, 1000];
    let currentMilestone = 0;
    let nextMilestone = 10;
    
    for (let i = 0; i < milestones.length; i++) {
      if (totalItems >= milestones[i]) {
        currentMilestone = milestones[i];
        nextMilestone = milestones[i + 1] || 1000;
      } else {
        break;
      }
    }
    
    if (totalItems >= 1000) return 100;
    
    const progress = ((totalItems - currentMilestone) / (nextMilestone - currentMilestone)) * 100;
    return Math.min(100, Math.max(0, progress));
  }
  
  // Get current milestone stage
  function getMilestoneStage(totalItems: number) {
    if (totalItems >= 1000) return "Ancient Grove";
    if (totalItems >= 500) return "Mature Forest";
    if (totalItems >= 100) return "Young Tree";
    if (totalItems >= 50) return "Growing Sapling";
    if (totalItems >= 10) return "Sprouting Seedling";
    return "Planting Seeds";
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
  
  .milestone-progress {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .milestone-bar {
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    overflow: hidden;
  }
  
  .milestone-fill {
    height: 100%;
    background: linear-gradient(90deg, #8B4513, #A0522D, #CD853F);
    transition: width 0.3s ease;
  }
  
  .milestone-text {
    font-size: 12px;
    color: #CD853F;
    text-align: center;
    font-weight: 500;
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