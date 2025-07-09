<script lang="ts">
  import { onMount } from 'svelte';
  import { spring, tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  
  interface DataPoint {
    date: Date;
    value: number;
    articles?: number;
    videos?: number;
    notes?: number;
    bookmarks?: number;
    label?: string;
  }
  
  interface DNAStrand {
    x: number;
    y: number;
    z: number;
    color: string;
    size: number;
    type: 'articles' | 'videos' | 'notes' | 'bookmarks';
    date: Date;
    value: number;
    angle: number;
    height: number;
    pulsePhase: number;
  }
  
  interface DNAConnection {
    strand1: DNAStrand;
    strand2: DNAStrand;
    strength: number;
    color: string;
  }
  
  // Props
  export let data: DataPoint[] = [];
  export let timeRange = 'week';
  
  // Internal state
  let container: HTMLDivElement;
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let width = 0;
  let height = 0;
  let dnaStrands: DNAStrand[] = [];
  let dnaConnections: DNAConnection[] = [];
  let hoveredStrand: DNAStrand | null = null;
  let animationFrame: number;
  let time = 0;
  let helixRotation = 0;
  let verticalOffset = 0;
  
  // DNA colors representing different content types
  const dnaColors = {
    articles: '#DC143C',    // Manchester Red
    videos: '#4169E1',      // Royal Blue
    notes: '#32CD32',       // Lime Green
    bookmarks: '#FFD700'    // Gold
  };
  
  // 3D projection settings
  const camera = {
    x: 0,
    y: 0,
    z: 800,
    fov: 400
  };
  
  const helixRadius = 80;
  const helixPitch = 150; // Height between full rotations
  
  $: if (data && data.length && canvas) {
    generateDNAHelix();
    startAnimation();
  }
  
  $: if (timeRange && data && data.length && canvas) {
    generateDNAHelix();
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
          generateDNAHelix();
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
  
  function generateDNAHelix() {
    if (!data || data.length === 0) return;
    
    dnaStrands = [];
    dnaConnections = [];
    
    const maxValue = Math.max(...data.map(d => d.value));
    const contentTypes = ['articles', 'videos', 'notes', 'bookmarks'] as const;
    
    data.forEach((point, timeIndex) => {
      const heightPosition = (timeIndex / (data.length - 1)) * helixPitch * 2 - helixPitch;
      
      contentTypes.forEach((type, typeIndex) => {
        const value = point[type] || 0;
        if (value === 0) return;
        
        // Create two strands (double helix)
        for (let strandIndex = 0; strandIndex < 2; strandIndex++) {
          const baseAngle = (timeIndex / data.length) * Math.PI * 8 + strandIndex * Math.PI;
          const typeOffset = (typeIndex * Math.PI) / 2;
          const angle = baseAngle + typeOffset;
          
          const x = Math.cos(angle) * helixRadius;
          const z = Math.sin(angle) * helixRadius;
          const y = heightPosition + (typeIndex * 10);
          
          const strand: DNAStrand = {
            x,
            y,
            z,
            color: dnaColors[type],
            size: Math.max(3, (value / maxValue) * 15),
            type,
            date: point.date,
            value,
            angle,
            height: heightPosition,
            pulsePhase: Math.random() * Math.PI * 2
          };
          
          dnaStrands.push(strand);
        }
      });
    });
    
    // Create connections between complementary strands
    generateDNAConnections();
  }
  
  function generateDNAConnections() {
    const strandGroups = groupStrandsByTime();
    
    Object.values(strandGroups).forEach(timeGroup => {
      const typeGroups = groupStrandsByType(timeGroup);
      
      // Create connections between different content types at same time
      const typeKeys = Object.keys(typeGroups);
      for (let i = 0; i < typeKeys.length - 1; i++) {
        const type1 = typeKeys[i];
        const type2 = typeKeys[i + 1];
        
        const strands1 = typeGroups[type1];
        const strands2 = typeGroups[type2];
        
        if (strands1.length > 0 && strands2.length > 0) {
          const strand1 = strands1[0];
          const strand2 = strands2[0];
          
          const connection: DNAConnection = {
            strand1,
            strand2,
            strength: Math.min(strand1.value, strand2.value) / 10,
            color: blendColors(strand1.color, strand2.color)
          };
          
          dnaConnections.push(connection);
        }
      }
    });
  }
  
  function groupStrandsByTime() {
    return dnaStrands.reduce((acc, strand) => {
      const timeKey = strand.date.getTime();
      if (!acc[timeKey]) acc[timeKey] = [];
      acc[timeKey].push(strand);
      return acc;
    }, {} as Record<number, DNAStrand[]>);
  }
  
  function groupStrandsByType(strands: DNAStrand[]) {
    return strands.reduce((acc, strand) => {
      if (!acc[strand.type]) acc[strand.type] = [];
      acc[strand.type].push(strand);
      return acc;
    }, {} as Record<string, DNAStrand[]>);
  }
  
  function blendColors(color1: string, color2: string): string {
    const c1 = hexToRgb(color1);
    const c2 = hexToRgb(color2);
    if (!c1 || !c2) return color1;
    
    const blended = {
      r: Math.round((c1.r + c2.r) / 2),
      g: Math.round((c1.g + c2.g) / 2),
      b: Math.round((c1.b + c2.b) / 2)
    };
    
    return `rgb(${blended.r}, ${blended.g}, ${blended.b})`;
  }
  
  function hexToRgb(hex: string) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }
  
  function startAnimation() {
    function animate() {
      if (!ctx || !canvas) return;
      
      time += 0.02;
      helixRotation += 0.008;
      verticalOffset = Math.sin(time * 0.5) * 20;
      
      // Clear canvas with molecular background
      const gradient = ctx.createRadialGradient(
        width / 2, height / 2, 0,
        width / 2, height / 2, Math.max(width, height) / 2
      );
      gradient.addColorStop(0, '#0F0F23');
      gradient.addColorStop(0.5, '#1A1A3E');
      gradient.addColorStop(1, '#000011');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);
      
      // Add molecular background pattern
      drawMolecularBackground();
      
      // Sort strands by z-depth for proper 3D rendering
      const sortedStrands = [...dnaStrands].sort((a, b) => {
        const aZ = rotateZ(a.x, a.z, helixRotation);
        const bZ = rotateZ(b.x, b.z, helixRotation);
        return bZ - aZ;
      });
      
      // Draw connections first (behind strands)
      drawDNAConnections();
      
      // Draw DNA strands
      sortedStrands.forEach(strand => {
        drawDNAStrand(strand);
      });
      
      // Draw helix backbone
      drawHelixBackbone();
      
      // Update pulsing
      dnaStrands.forEach(strand => {
        strand.pulsePhase += 0.04;
      });
      
      animationFrame = requestAnimationFrame(animate);
    }
    
    animate();
  }
  
  function project3D(x: number, y: number, z: number) {
    // Apply rotation
    const rotatedX = rotateX(x, z, helixRotation);
    const rotatedZ = rotateZ(x, z, helixRotation);
    
    // Apply vertical offset
    const offsetY = y + verticalOffset;
    
    // Project to 2D
    const distance = camera.z - rotatedZ;
    const scale = camera.fov / distance;
    
    return {
      x: width / 2 + rotatedX * scale,
      y: height / 2 + offsetY * scale,
      z: rotatedZ,
      scale
    };
  }
  
  function rotateX(x: number, z: number, angle: number) {
    return x * Math.cos(angle) - z * Math.sin(angle);
  }
  
  function rotateZ(x: number, z: number, angle: number) {
    return x * Math.sin(angle) + z * Math.cos(angle);
  }
  
  function drawMolecularBackground() {
    ctx.fillStyle = 'rgba(70, 130, 180, 0.1)';
    for (let i = 0; i < 50; i++) {
      const x = Math.random() * width;
      const y = Math.random() * height;
      const size = Math.random() * 3 + 1;
      
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  
  function drawDNAStrand(strand: DNAStrand) {
    const pos = project3D(strand.x, strand.y, strand.z);
    
    // Pulsing effect
    const pulse = 1 + Math.sin(strand.pulsePhase) * 0.3;
    const size = strand.size * pos.scale * pulse;
    
    // Create 3D sphere gradient
    const gradient = ctx.createRadialGradient(
      pos.x - size * 0.3, pos.y - size * 0.3, 0,
      pos.x, pos.y, size
    );
    
    const lightColor = lightenColor(strand.color, 60);
    const darkColor = darkenColor(strand.color, 40);
    
    gradient.addColorStop(0, lightColor);
    gradient.addColorStop(0.6, strand.color);
    gradient.addColorStop(1, darkColor);
    
    // Draw main sphere
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, size, 0, Math.PI * 2);
    ctx.fill();
    
    // Add phosphorescent glow
    ctx.fillStyle = `${strand.color}30`;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, size * 2, 0, Math.PI * 2);
    ctx.fill();
    
    // Add highlight
    ctx.fillStyle = `rgba(255, 255, 255, 0.4)`;
    ctx.beginPath();
    ctx.arc(pos.x - size * 0.3, pos.y - size * 0.3, size * 0.3, 0, Math.PI * 2);
    ctx.fill();
    
    // Check for hover
    if (hoveredStrand === strand) {
      ctx.strokeStyle = '#00FFFF';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, size + 8, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }
  
  function drawDNAConnections() {
    dnaConnections.forEach(connection => {
      const pos1 = project3D(connection.strand1.x, connection.strand1.y, connection.strand1.z);
      const pos2 = project3D(connection.strand2.x, connection.strand2.y, connection.strand2.z);
      
      // Create connection gradient
      const gradient = ctx.createLinearGradient(pos1.x, pos1.y, pos2.x, pos2.y);
      gradient.addColorStop(0, `${connection.strand1.color}80`);
      gradient.addColorStop(0.5, `${connection.color}60`);
      gradient.addColorStop(1, `${connection.strand2.color}80`);
      
      // Draw connection line
      ctx.strokeStyle = gradient;
      ctx.lineWidth = connection.strength * 3;
      ctx.lineCap = 'round';
      
      // Add slight curve for organic feel
      const midX = (pos1.x + pos2.x) / 2;
      const midY = (pos1.y + pos2.y) / 2 + Math.sin(time + connection.strand1.angle) * 10;
      
      ctx.beginPath();
      ctx.moveTo(pos1.x, pos1.y);
      ctx.quadraticCurveTo(midX, midY, pos2.x, pos2.y);
      ctx.stroke();
    });
  }
  
  function drawHelixBackbone() {
    const backbonePoints = [];
    
    // Create backbone path
    for (let i = 0; i <= 100; i++) {
      const angle = (i / 100) * Math.PI * 8;
      const height = (i / 100) * helixPitch * 2 - helixPitch;
      
      const x = Math.cos(angle) * (helixRadius + 20);
      const z = Math.sin(angle) * (helixRadius + 20);
      
      backbonePoints.push(project3D(x, height, z));
    }
    
    // Draw backbone
    ctx.strokeStyle = 'rgba(100, 150, 200, 0.3)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    backbonePoints.forEach((point, index) => {
      if (index === 0) {
        ctx.moveTo(point.x, point.y);
      } else {
        ctx.lineTo(point.x, point.y);
      }
    });
    
    ctx.stroke();
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
    
    hoveredStrand = null;
    
    for (const strand of dnaStrands) {
      const pos = project3D(strand.x, strand.y, strand.z);
      const size = strand.size * pos.scale;
      
      const dx = mouseX - pos.x;
      const dy = mouseY - pos.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance < size + 5) {
        hoveredStrand = strand;
        break;
      }
    }
  }
  
  function getContentTypeLabel(type: string) {
    return type.charAt(0).toUpperCase() + type.slice(1);
  }
  
  function formatDate(date: Date) {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: timeRange === 'all' ? 'numeric' : undefined
    });
  }
</script>

<div class="dna-helix" bind:this={container}>
  {#if data && data.length > 0}
    <canvas
      bind:this={canvas}
      {width}
      {height}
      on:mousemove={handleMouseMove}
      style="cursor: {hoveredStrand ? 'pointer' : 'default'}"
    />
    
    <!-- DNA strand tooltip -->
    {#if hoveredStrand}
      <div 
        class="dna-tooltip"
        style="left: {project3D(hoveredStrand.x, hoveredStrand.y, hoveredStrand.z).x + 20}px; top: {project3D(hoveredStrand.x, hoveredStrand.y, hoveredStrand.z).y - 10}px;"
      >
        <div class="tooltip-header">
          <span class="dna-icon" style="color: {hoveredStrand.color}">🧬</span>
          <span class="strand-name">{getContentTypeLabel(hoveredStrand.type)}</span>
        </div>
        <div class="tooltip-stats">
          <span class="stat">
            <span class="stat-label">Date:</span>
            <span class="stat-value">{formatDate(hoveredStrand.date)}</span>
          </span>
          <span class="stat">
            <span class="stat-label">Count:</span>
            <span class="stat-value">{hoveredStrand.value}</span>
          </span>
          <span class="stat">
            <span class="stat-label">Sequence:</span>
            <span class="stat-value">{hoveredStrand.type.toUpperCase()}</span>
          </span>
        </div>
      </div>
    {/if}
    
    <!-- DNA helix legend -->
    <div class="helix-legend">
      <h3>🧬 Knowledge DNA</h3>
      <div class="legend-grid">
        {#each Object.entries(dnaColors) as [type, color]}
          <div class="legend-item">
            <div class="dna-base" style="background: {color}; box-shadow: 0 0 8px {color}50;"></div>
            <span class="legend-label">{getContentTypeLabel(type)}</span>
          </div>
        {/each}
      </div>
      <div class="helix-info">
        <div class="info-row">
          <span class="info-label">Evolution:</span>
          <span class="info-value">Active</span>
        </div>
        <div class="info-row">
          <span class="info-label">Strands:</span>
          <span class="info-value">{dnaStrands.length}</span>
        </div>
      </div>
    </div>
    
    <!-- Time progression indicator -->
    <div class="time-progression">
      <div class="progression-bar">
        <div class="progression-fill" style="height: {(time * 10) % 100}%"></div>
      </div>
      <span class="progression-label">Time Evolution</span>
    </div>
  {:else}
    <div class="empty-state">
      <div class="empty-icon">🧬</div>
      <p>No data to sequence your knowledge DNA</p>
    </div>
  {/if}
</div>

<style>
  .dna-helix {
    width: 100%;
    height: 100%;
    min-height: 400px;
    position: relative;
    background: radial-gradient(circle at 50% 50%, #0F0F23 0%, #1A1A3E 40%, #000011 100%);
    border-radius: 12px;
    overflow: hidden;
  }
  
  canvas {
    width: 100%;
    height: 100%;
    display: block;
  }
  
  .dna-tooltip {
    position: absolute;
    background: rgba(0, 0, 0, 0.95);
    color: white;
    padding: 12px;
    border-radius: 8px;
    font-size: 14px;
    pointer-events: none;
    z-index: 10;
    border: 1px solid rgba(0, 255, 255, 0.3);
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 12px rgba(0, 255, 255, 0.2);
    max-width: 250px;
  }
  
  .tooltip-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }
  
  .dna-icon {
    font-size: 16px;
    filter: drop-shadow(0 0 4px currentColor);
  }
  
  .strand-name {
    font-weight: 600;
    color: #00FFFF;
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
    font-family: 'Courier New', monospace;
  }
  
  .helix-legend {
    position: absolute;
    top: 16px;
    right: 16px;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 16px;
    border-radius: 8px;
    font-size: 14px;
    border: 1px solid rgba(0, 255, 255, 0.3);
    backdrop-filter: blur(10px);
    max-width: 200px;
  }
  
  .helix-legend h3 {
    margin: 0 0 12px 0;
    font-size: 16px;
    color: #00FFFF;
  }
  
  .legend-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 16px;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .dna-base {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.2); }
  }
  
  .legend-label {
    font-size: 12px;
    text-transform: capitalize;
  }
  
  .helix-info {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .info-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }
  
  .info-label {
    color: rgba(255, 255, 255, 0.7);
    font-size: 12px;
  }
  
  .info-value {
    color: #00FFFF;
    font-weight: 500;
    font-size: 12px;
  }
  
  .time-progression {
    position: absolute;
    bottom: 16px;
    left: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .progression-bar {
    width: 20px;
    height: 100px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    overflow: hidden;
    position: relative;
  }
  
  .progression-fill {
    width: 100%;
    background: linear-gradient(180deg, #00FFFF, #0080FF, #0040FF);
    position: absolute;
    bottom: 0;
    border-radius: 10px;
    transition: height 0.3s ease;
  }
  
  .progression-label {
    color: rgba(255, 255, 255, 0.7);
    font-size: 12px;
    writing-mode: vertical-lr;
    text-orientation: mixed;
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
    color: #00FFFF;
    filter: drop-shadow(0 0 8px currentColor);
  }
  
  .empty-state p {
    margin: 0;
    font-size: 16px;
  }
</style>