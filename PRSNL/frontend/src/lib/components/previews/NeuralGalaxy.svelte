<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { spring } from 'svelte/motion';
  import { getAudioManager } from '$lib/utils/audioManager';

  export let data = generateMockData();

  // Canvas setup
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let container: HTMLDivElement;
  let width = 800;
  let height = 600;
  let animationFrame: number;

  // Galaxy state
  let galaxyNodes: GalaxyNode[] = [];
  let particles: Particle[] = [];
  let connections: Connection[] = [];
  let hoveredNode: GalaxyNode | null = null;
  let selectedNode: GalaxyNode | null = null;

  // Controls
  let zoomLevel = 1;
  let timeProgress = 1;
  let rotation = { x: 0, y: 0, z: 0 };
  let autoRotate = true;

  // Animation
  let time = 0;
  const rotationSpeed = 0.001;

  // Types
  interface GalaxyNode {
    id: string;
    name: string;
    x: number;
    y: number;
    z: number;
    size: number;
    color: string;
    type: 'galaxy' | 'system' | 'planet';
    children: GalaxyNode[];
    parent: GalaxyNode | null;
    value: number;
    glowIntensity: number;
    pulsePhase: number;
    orbitRadius: number;
    orbitSpeed: number;
    orbitAngle: number;
  }

  interface Particle {
    x: number;
    y: number;
    z: number;
    vx: number;
    vy: number;
    vz: number;
    size: number;
    color: string;
    life: number;
    maxLife: number;
  }

  interface Connection {
    from: GalaxyNode;
    to: GalaxyNode;
    strength: number;
    pulseOffset: number;
  }

  function generateMockData() {
    return [
      { id: '1', name: 'Technology', count: 45, group: 'major' },
      { id: '2', name: 'Philosophy', count: 32, group: 'major' },
      { id: '3', name: 'Science', count: 28, group: 'major' },
      { id: '4', name: 'Art & Design', count: 23, group: 'medium' },
      { id: '5', name: 'History', count: 19, group: 'medium' },
      { id: '6', name: 'Psychology', count: 15, group: 'medium' },
      { id: '7', name: 'Music', count: 12, group: 'minor' },
      { id: '8', name: 'Literature', count: 10, group: 'minor' },
    ];
  }

  onMount(() => {
    ctx = canvas.getContext('2d')!;
    
    // Initialize audio
    const audioManager = getAudioManager();
    audioManager.init();
    audioManager.createSyntheticSounds();
    audioManager.playBackgroundMusic('space');
    
    // Setup canvas
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Initialize galaxy
    createGalaxyStructure();
    createNebula();
    animate();
    
    // Mouse interactions
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('click', handleClick);
    canvas.addEventListener('wheel', handleWheel);
  });

  onDestroy(() => {
    if (animationFrame) cancelAnimationFrame(animationFrame);
    window.removeEventListener('resize', resizeCanvas);
    const audioManager = getAudioManager();
    audioManager.destroy();
  });

  function resizeCanvas() {
    const rect = container.getBoundingClientRect();
    width = rect.width;
    height = rect.height;
    canvas.width = width;
    canvas.height = height;
  }

  function createGalaxyStructure() {
    galaxyNodes = [];
    connections = [];
    
    // Create central galaxy hub
    const centerX = 0;
    const centerY = 0;
    const centerZ = 0;
    
    // Create topic clusters as solar systems
    data.forEach((topic, i) => {
      const angle = (i / data.length) * Math.PI * 2;
      const radius = 200 + Math.random() * 100;
      
      const system: GalaxyNode = {
        id: topic.id,
        name: topic.name,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius * 0.5,
        z: centerZ + Math.sin(angle) * radius * 0.3,
        size: Math.sqrt(topic.count) * 10,
        color: getTopicColor(topic.group),
        type: 'system',
        children: [],
        parent: null,
        value: topic.count,
        glowIntensity: 0.8,
        pulsePhase: Math.random() * Math.PI * 2,
        orbitRadius: radius,
        orbitSpeed: 0.0002 + Math.random() * 0.0003,
        orbitAngle: angle
      };
      
      // Create planets (individual items) for each system
      const planetCount = Math.min(topic.count, 8);
      for (let j = 0; j < planetCount; j++) {
        const planetAngle = (j / planetCount) * Math.PI * 2;
        const planetRadius = 30 + j * 10;
        
        const planet: GalaxyNode = {
          id: `${topic.id}-${j}`,
          name: `Item ${j + 1}`,
          x: system.x + Math.cos(planetAngle) * planetRadius,
          y: system.y + Math.sin(planetAngle) * planetRadius * 0.3,
          z: system.z + Math.sin(planetAngle) * planetRadius * 0.2,
          size: 3 + Math.random() * 3,
          color: system.color,
          type: 'planet',
          children: [],
          parent: system,
          value: 1,
          glowIntensity: 0.5,
          pulsePhase: Math.random() * Math.PI * 2,
          orbitRadius: planetRadius,
          orbitSpeed: 0.001 + Math.random() * 0.002,
          orbitAngle: planetAngle
        };
        
        system.children.push(planet);
        galaxyNodes.push(planet);
      }
      
      galaxyNodes.push(system);
      
      // Create connections between related systems
      if (i > 0) {
        const prevSystem = galaxyNodes.find(n => n.id === data[i - 1].id);
        if (prevSystem) {
          connections.push({
            from: system,
            to: prevSystem,
            strength: 0.5 + Math.random() * 0.5,
            pulseOffset: Math.random() * Math.PI * 2
          });
        }
      }
    });
  }

  function createNebula() {
    // Create background nebula particles
    for (let i = 0; i < 200; i++) {
      particles.push({
        x: (Math.random() - 0.5) * width * 2,
        y: (Math.random() - 0.5) * height * 2,
        z: (Math.random() - 0.5) * 500,
        vx: (Math.random() - 0.5) * 0.2,
        vy: (Math.random() - 0.5) * 0.2,
        vz: (Math.random() - 0.5) * 0.1,
        size: Math.random() * 3,
        color: `hsl(${280 + Math.random() * 60}, 70%, ${40 + Math.random() * 20}%)`,
        life: 1,
        maxLife: 1
      });
    }
  }

  function getTopicColor(group: string): string {
    const colors = {
      major: '#DC143C',
      medium: '#4a9eff',
      minor: '#00ff64'
    };
    return colors[group] || '#ffffff';
  }

  function project3D(x: number, y: number, z: number) {
    const perspective = 800;
    const scale = perspective / (perspective + z * zoomLevel);
    
    return {
      x: x * scale + width / 2,
      y: y * scale + height / 2,
      scale: scale
    };
  }

  function animate() {
    time += 0.016;
    
    // Clear canvas
    ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
    ctx.fillRect(0, 0, width, height);
    
    // Draw nebula background
    drawNebula();
    
    // Update rotation
    if (autoRotate) {
      rotation.y += rotationSpeed;
    }
    
    // Sort nodes by depth for proper rendering
    const sortedNodes = [...galaxyNodes].sort((a, b) => {
      const aRotated = rotatePoint(a.x, a.y, a.z);
      const bRotated = rotatePoint(b.x, b.y, b.z);
      return bRotated.z - aRotated.z;
    });
    
    // Draw connections
    drawConnections();
    
    // Draw nodes
    sortedNodes.forEach(node => {
      updateNode(node);
      drawNode(node);
    });
    
    // Draw UI
    drawZoomIndicator();
    drawTimelineIndicator();
    
    animationFrame = requestAnimationFrame(animate);
  }

  function rotatePoint(x: number, y: number, z: number) {
    // Rotate around Y axis
    const cosY = Math.cos(rotation.y);
    const sinY = Math.sin(rotation.y);
    const x1 = x * cosY - z * sinY;
    const z1 = x * sinY + z * cosY;
    
    // Rotate around X axis
    const cosX = Math.cos(rotation.x);
    const sinX = Math.sin(rotation.x);
    const y1 = y * cosX - z1 * sinX;
    const z2 = y * sinX + z1 * cosX;
    
    return { x: x1, y: y1, z: z2 };
  }

  function updateNode(node: GalaxyNode) {
    // Update orbit
    if (node.parent && node.type === 'planet') {
      node.orbitAngle += node.orbitSpeed;
      node.x = node.parent.x + Math.cos(node.orbitAngle) * node.orbitRadius;
      node.y = node.parent.y + Math.sin(node.orbitAngle) * node.orbitRadius * 0.3;
      node.z = node.parent.z + Math.sin(node.orbitAngle) * node.orbitRadius * 0.2;
    } else if (node.type === 'system') {
      // Slowly orbit around center
      node.orbitAngle += node.orbitSpeed * 0.5;
      node.x = Math.cos(node.orbitAngle) * node.orbitRadius;
      node.y = Math.sin(node.orbitAngle) * node.orbitRadius * 0.5;
      node.z = Math.sin(node.orbitAngle) * node.orbitRadius * 0.3;
    }
    
    // Update pulse
    node.glowIntensity = 0.5 + Math.sin(time * 2 + node.pulsePhase) * 0.3;
  }

  function drawNode(node: GalaxyNode) {
    const rotated = rotatePoint(node.x, node.y, node.z);
    const projected = project3D(rotated.x, rotated.y, rotated.z);
    
    // Skip if behind camera
    if (projected.scale <= 0) return;
    
    const size = node.size * projected.scale;
    
    // Draw glow
    const gradient = ctx.createRadialGradient(
      projected.x, projected.y, 0,
      projected.x, projected.y, size * 3
    );
    gradient.addColorStop(0, node.color + 'ff');
    gradient.addColorStop(0.5, node.color + '40');
    gradient.addColorStop(1, node.color + '00');
    
    ctx.fillStyle = gradient;
    ctx.globalAlpha = node.glowIntensity;
    ctx.fillRect(projected.x - size * 3, projected.y - size * 3, size * 6, size * 6);
    
    // Draw core
    ctx.globalAlpha = 1;
    ctx.fillStyle = node.color;
    ctx.beginPath();
    ctx.arc(projected.x, projected.y, size, 0, Math.PI * 2);
    ctx.fill();
    
    // Draw label for systems when zoomed in
    if (node.type === 'system' && zoomLevel > 1.5) {
      ctx.font = `${12 * projected.scale}px 'Space Grotesk'`;
      ctx.fillStyle = '#ffffff';
      ctx.textAlign = 'center';
      ctx.fillText(node.name, projected.x, projected.y - size - 10);
    }
    
    // Highlight on hover
    if (node === hoveredNode) {
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(projected.x, projected.y, size + 5, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  function drawConnections() {
    ctx.globalAlpha = 0.3;
    
    connections.forEach(conn => {
      const from = rotatePoint(conn.from.x, conn.from.y, conn.from.z);
      const to = rotatePoint(conn.to.x, conn.to.y, conn.to.z);
      
      const projFrom = project3D(from.x, from.y, from.z);
      const projTo = project3D(to.x, to.y, to.z);
      
      if (projFrom.scale <= 0 || projTo.scale <= 0) return;
      
      // Draw connection line with pulse
      const pulse = Math.sin(time * 3 + conn.pulseOffset) * 0.5 + 0.5;
      ctx.strokeStyle = `rgba(220, 20, 60, ${conn.strength * pulse})`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(projFrom.x, projFrom.y);
      ctx.lineTo(projTo.x, projTo.y);
      ctx.stroke();
    });
    
    ctx.globalAlpha = 1;
  }

  function drawNebula() {
    // Update and draw nebula particles
    particles.forEach(particle => {
      particle.x += particle.vx;
      particle.y += particle.vy;
      particle.z += particle.vz;
      
      // Wrap around
      if (particle.x < -width) particle.x = width;
      if (particle.x > width) particle.x = -width;
      if (particle.y < -height) particle.y = height;
      if (particle.y > height) particle.y = -height;
      
      const rotated = rotatePoint(particle.x, particle.y, particle.z);
      const projected = project3D(rotated.x, rotated.y, rotated.z);
      
      if (projected.scale <= 0) return;
      
      ctx.fillStyle = particle.color;
      ctx.globalAlpha = 0.3 * particle.life;
      ctx.beginPath();
      ctx.arc(projected.x, projected.y, particle.size * projected.scale, 0, Math.PI * 2);
      ctx.fill();
    });
    
    ctx.globalAlpha = 1;
  }

  function drawZoomIndicator() {
    const x = width - 100;
    const y = height / 2;
    const height = 200;
    
    // Draw track
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(x, y - height / 2);
    ctx.lineTo(x, y + height / 2);
    ctx.stroke();
    
    // Draw handle
    const handleY = y - height / 2 + (1 - (zoomLevel - 0.5) / 2.5) * height;
    ctx.fillStyle = '#DC143C';
    ctx.beginPath();
    ctx.arc(x, handleY, 10, 0, Math.PI * 2);
    ctx.fill();
    
    // Labels
    ctx.fillStyle = '#666';
    ctx.font = '12px Space Grotesk';
    ctx.textAlign = 'center';
    ctx.fillText('Galaxy', x, y - height / 2 - 10);
    ctx.fillText('Planet', x, y + height / 2 + 20);
  }

  function drawTimelineIndicator() {
    const x = width / 2;
    const y = height - 50;
    const width = 300;
    
    // Draw track
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(x - width / 2, y);
    ctx.lineTo(x + width / 2, y);
    ctx.stroke();
    
    // Draw handle
    const handleX = x - width / 2 + timeProgress * width;
    ctx.fillStyle = '#00ff64';
    ctx.beginPath();
    ctx.arc(handleX, y, 10, 0, Math.PI * 2);
    ctx.fill();
    
    // Labels
    ctx.fillStyle = '#666';
    ctx.font = '12px Space Grotesk';
    ctx.textAlign = 'center';
    ctx.fillText('Past', x - width / 2, y + 25);
    ctx.fillText('Present', x + width / 2, y + 25);
  }

  function handleMouseMove(e: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Check hover on nodes
    let foundHover = false;
    galaxyNodes.forEach(node => {
      const rotated = rotatePoint(node.x, node.y, node.z);
      const projected = project3D(rotated.x, rotated.y, rotated.z);
      
      if (projected.scale <= 0) return;
      
      const dx = mouseX - projected.x;
      const dy = mouseY - projected.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      
      if (dist < node.size * projected.scale + 10) {
        if (hoveredNode !== node) {
          hoveredNode = node;
          getAudioManager().playSound('whoosh', 0.3);
        }
        foundHover = true;
      }
    });
    
    if (!foundHover) hoveredNode = null;
  }

  function handleClick(e: MouseEvent) {
    if (hoveredNode) {
      selectedNode = hoveredNode;
      getAudioManager().playSound('whoosh', 0.5);
      
      // Zoom to selected node
      if (hoveredNode.type === 'system') {
        zoomLevel = 2;
      } else if (hoveredNode.type === 'planet') {
        zoomLevel = 3;
      }
    }
  }

  function handleWheel(e: WheelEvent) {
    e.preventDefault();
    zoomLevel = Math.max(0.5, Math.min(3, zoomLevel - e.deltaY * 0.001));
  }

  function handleZoomChange(e: Event) {
    zoomLevel = parseFloat((e.target as HTMLInputElement).value);
    getAudioManager().playSound('whoosh', 0.2);
  }

  function handleTimeChange(e: Event) {
    timeProgress = parseFloat((e.target as HTMLInputElement).value);
    // Update data based on time
  }
</script>

<div class="galaxy-container" bind:this={container}>
  <canvas bind:this={canvas}></canvas>
  
  <div class="controls">
    <div class="control-group zoom-control">
      <label>Zoom Level</label>
      <input 
        type="range" 
        min="0.5" 
        max="3" 
        step="0.1" 
        bind:value={zoomLevel}
        on:input={handleZoomChange}
      />
      <div class="zoom-labels">
        <span>Galaxy</span>
        <span>System</span>
        <span>Planet</span>
      </div>
    </div>
    
    <div class="control-group time-control">
      <label>Time Travel</label>
      <input 
        type="range" 
        min="0" 
        max="1" 
        step="0.01" 
        bind:value={timeProgress}
        on:input={handleTimeChange}
      />
      <div class="time-labels">
        <span>Past</span>
        <span>Present</span>
      </div>
    </div>
    
    <button class="toggle-rotation" on:click={() => autoRotate = !autoRotate}>
      {autoRotate ? 'Pause' : 'Resume'} Rotation
    </button>
  </div>
  
  {#if hoveredNode}
    <div class="info-panel">
      <h3>{hoveredNode.name}</h3>
      <p>Type: {hoveredNode.type}</p>
      <p>Items: {hoveredNode.value}</p>
    </div>
  {/if}
  
  <div class="achievement" class:show={selectedNode}>
    <span class="icon">🌟</span>
    <span>New constellation discovered!</span>
  </div>
</div>

<style>
  .galaxy-container {
    position: relative;
    width: 100%;
    height: 100vh;
    background: #000;
    overflow: hidden;
  }
  
  canvas {
    width: 100%;
    height: 100%;
    cursor: crosshair;
  }
  
  .controls {
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 30px;
    background: rgba(0, 0, 0, 0.8);
    padding: 20px;
    border-radius: 20px;
    border: 1px solid #333;
    backdrop-filter: blur(10px);
  }
  
  .control-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  .control-group label {
    color: #00ff64;
    font-family: 'Space Grotesk';
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .control-group input[type="range"] {
    width: 200px;
    height: 6px;
    background: #333;
    border-radius: 3px;
    outline: none;
    -webkit-appearance: none;
  }
  
  .control-group input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 20px;
    height: 20px;
    background: #DC143C;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 0 10px #DC143C;
  }
  
  .zoom-labels,
  .time-labels {
    display: flex;
    justify-content: space-between;
    color: #666;
    font-size: 12px;
    font-family: 'Space Grotesk';
  }
  
  .toggle-rotation {
    background: #DC143C;
    border: none;
    color: white;
    padding: 10px 20px;
    border-radius: 10px;
    font-family: 'Space Grotesk';
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .toggle-rotation:hover {
    background: #B91C3C;
    transform: translateY(-2px);
  }
  
  .info-panel {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.8);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #DC143C;
    color: white;
    font-family: 'Space Grotesk';
    backdrop-filter: blur(10px);
  }
  
  .info-panel h3 {
    margin: 0 0 10px 0;
    color: #00ff64;
  }
  
  .info-panel p {
    margin: 5px 0;
    color: #ccc;
    font-size: 14px;
  }
  
  .achievement {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0);
    background: rgba(220, 20, 60, 0.9);
    padding: 20px 40px;
    border-radius: 20px;
    color: white;
    font-family: 'Space Grotesk';
    font-size: 18px;
    display: flex;
    align-items: center;
    gap: 15px;
    transition: transform 0.5s ease;
  }
  
  .achievement.show {
    transform: translate(-50%, -50%) scale(1);
  }
  
  .achievement .icon {
    font-size: 30px;
  }
</style>