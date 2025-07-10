<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { audioManager } from '$lib/utils/audioManager';

  export let data = generateMockData();

  // Canvas setup
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let container: HTMLDivElement;
  let width = 800;
  let height = 600;
  let animationFrame: number;

  // DNA state
  let dnaStrands: DNAStrand[] = [];
  let basePairs: BasePair[] = [];
  let mutations: Mutation[] = [];
  let selectedGene: Gene | null = null;
  let hoveredStrand: DNAStrand | null = null;

  // Controls
  let rotationAngle = 0;
  let zoomLevel = 1;
  let sequencePosition = 0;
  let isSequencing = false;
  let mutationMode = false;

  // Animation
  let time = 0;
  let helixSpeed = 0.02;

  // Types
  interface DNAStrand {
    id: string;
    x: number;
    y: number;
    z: number;
    type: 'A' | 'T' | 'G' | 'C';
    color: string;
    angle: number;
    height: number;
    glowIntensity: number;
    contentType: string;
    value: number;
    date: Date;
  }

  interface BasePair {
    strand1: DNAStrand;
    strand2: DNAStrand;
    strength: number;
    phosphorescence: number;
  }

  interface Gene {
    id: string;
    name: string;
    strands: DNAStrand[];
    color: string;
    activity: number;
  }

  interface Mutation {
    position: number;
    type: string;
    timestamp: Date;
    impact: number;
  }

  function generateMockData() {
    const types = ['articles', 'videos', 'notes', 'bookmarks'];
    const data = [];
    const now = new Date();
    
    for (let i = 0; i < 30; i++) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      data.push({
        date,
        articles: Math.floor(Math.random() * 5),
        videos: Math.floor(Math.random() * 3),
        notes: Math.floor(Math.random() * 4),
        bookmarks: Math.floor(Math.random() * 2)
      });
    }
    
    return data;
  }

  onMount(() => {
    ctx = canvas.getContext('2d')!;
    
    // Initialize audio
    audioManager.init();
    audioManager.createSyntheticSounds();
    audioManager.playBackgroundMusic('lab');
    
    // Setup canvas
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Initialize DNA structure
    createDNAStructure();
    animate();
    
    // Mouse interactions
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('click', handleClick);
    canvas.addEventListener('wheel', handleWheel);
  });

  onDestroy(() => {
    if (animationFrame) cancelAnimationFrame(animationFrame);
    window.removeEventListener('resize', resizeCanvas);
  });

  function resizeCanvas() {
    const rect = container.getBoundingClientRect();
    width = rect.width;
    height = rect.height;
    canvas.width = width;
    canvas.height = height;
  }

  function createDNAStructure() {
    dnaStrands = [];
    basePairs = [];
    
    const types = ['A', 'T', 'G', 'C'] as const;
    const colors = {
      A: '#DC143C', // Adenine - Red
      T: '#4a9eff', // Thymine - Blue
      G: '#00ff64', // Guanine - Green
      C: '#ffa500'  // Cytosine - Orange
    };
    
    const contentColors = {
      articles: '#DC143C',
      videos: '#4a9eff',
      notes: '#00ff64',
      bookmarks: '#ffa500'
    };
    
    // Create DNA strands from data
    data.forEach((point, i) => {
      const height = i * 20;
      
      ['articles', 'videos', 'notes', 'bookmarks'].forEach((type, j) => {
        if (point[type] > 0) {
          const angle1 = (i / data.length) * Math.PI * 4;
          const angle2 = angle1 + Math.PI;
          
          // Create base pair
          const strand1: DNAStrand = {
            id: `${i}-${type}-1`,
            x: Math.cos(angle1) * 100,
            y: height,
            z: Math.sin(angle1) * 100,
            type: types[j % 4],
            color: contentColors[type],
            angle: angle1,
            height: height,
            glowIntensity: 0.8,
            contentType: type,
            value: point[type],
            date: point.date
          };
          
          const strand2: DNAStrand = {
            id: `${i}-${type}-2`,
            x: Math.cos(angle2) * 100,
            y: height,
            z: Math.sin(angle2) * 100,
            type: types[(j + 2) % 4], // Complementary base
            color: contentColors[type],
            angle: angle2,
            height: height,
            glowIntensity: 0.8,
            contentType: type,
            value: point[type],
            date: point.date
          };
          
          dnaStrands.push(strand1, strand2);
          
          basePairs.push({
            strand1,
            strand2,
            strength: 0.8 + Math.random() * 0.2,
            phosphorescence: Math.random()
          });
        }
      });
    });
    
    // Create some mutations for visual interest
    for (let i = 0; i < 5; i++) {
      mutations.push({
        position: Math.random() * data.length,
        type: ['insertion', 'deletion', 'substitution'][Math.floor(Math.random() * 3)],
        timestamp: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
        impact: Math.random()
      });
    }
  }

  function animate() {
    time += 0.016;
    
    // Clear canvas with glow effect
    ctx.fillStyle = 'rgba(0, 5, 10, 0.1)';
    ctx.fillRect(0, 0, width, height);
    
    // Draw background effects
    drawLabBackground();
    
    // Update rotation
    rotationAngle += helixSpeed;
    
    // Update DNA strands
    updateDNA();
    
    // Draw DNA structure
    drawDNA();
    
    // Draw UI elements
    drawSequenceBar();
    drawHealthMeter();
    drawMutationIndicators();
    
    animationFrame = requestAnimationFrame(animate);
  }

  function updateDNA() {
    dnaStrands.forEach(strand => {
      // Update rotation
      strand.angle += helixSpeed;
      strand.x = Math.cos(strand.angle) * 100 * zoomLevel;
      strand.z = Math.sin(strand.angle) * 100 * zoomLevel;
      
      // Update glow based on activity
      strand.glowIntensity = 0.5 + Math.sin(time * 2 + strand.height * 0.1) * 0.3;
      
      // Sequencing effect
      if (isSequencing) {
        const distance = Math.abs(strand.height - sequencePosition * height);
        if (distance < 50) {
          strand.glowIntensity = 1;
        }
      }
    });
    
    // Update base pair connections
    basePairs.forEach(pair => {
      pair.phosphorescence = 0.5 + Math.sin(time * 3 + pair.strand1.height * 0.05) * 0.5;
    });
  }

  function drawDNA() {
    // Sort strands by depth
    const sortedStrands = [...dnaStrands].sort((a, b) => b.z - a.z);
    
    // Draw connections first
    ctx.strokeStyle = '#00ff64';
    ctx.globalAlpha = 0.3;
    
    basePairs.forEach(pair => {
      const y1 = height / 2 - pair.strand1.height + sequencePosition * height;
      const y2 = height / 2 - pair.strand2.height + sequencePosition * height;
      
      if (y1 < -100 || y1 > height + 100) return;
      
      // Project 3D to 2D
      const x1 = width / 2 + pair.strand1.x;
      const x2 = width / 2 + pair.strand2.x;
      
      // Draw phosphate backbone
      ctx.lineWidth = 2;
      ctx.strokeStyle = `rgba(0, 255, 100, ${pair.phosphorescence * 0.5})`;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      
      // Draw hydrogen bonds
      const steps = 3;
      for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const x = x1 + (x2 - x1) * t;
        const y = y1 + (y2 - y1) * t;
        
        ctx.fillStyle = `rgba(255, 255, 255, ${pair.phosphorescence * 0.3})`;
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    });
    
    // Draw strands
    sortedStrands.forEach(strand => {
      const y = height / 2 - strand.height + sequencePosition * height;
      
      if (y < -50 || y > height + 50) return;
      
      const x = width / 2 + strand.x;
      const size = 8 + strand.value * 3;
      
      // Draw glow
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, size * 3);
      gradient.addColorStop(0, strand.color + 'ff');
      gradient.addColorStop(0.5, strand.color + '60');
      gradient.addColorStop(1, strand.color + '00');
      
      ctx.fillStyle = gradient;
      ctx.globalAlpha = strand.glowIntensity;
      ctx.fillRect(x - size * 3, y - size * 3, size * 6, size * 6);
      
      // Draw base
      ctx.globalAlpha = 1;
      ctx.fillStyle = strand.color;
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      
      // Draw base shape based on type
      ctx.beginPath();
      switch (strand.type) {
        case 'A': // Adenine - Pentagon
          drawPentagon(x, y, size);
          break;
        case 'T': // Thymine - Hexagon
          drawHexagon(x, y, size);
          break;
        case 'G': // Guanine - Square
          ctx.rect(x - size, y - size, size * 2, size * 2);
          break;
        case 'C': // Cytosine - Circle
          ctx.arc(x, y, size, 0, Math.PI * 2);
          break;
      }
      ctx.fill();
      ctx.stroke();
      
      // Draw base letter
      ctx.fillStyle = '#ffffff';
      ctx.font = `bold ${size}px Space Grotesk`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(strand.type, x, y);
      
      // Highlight on hover
      if (strand === hoveredStrand) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(x, y, size + 10, 0, Math.PI * 2);
        ctx.stroke();
      }
    });
    
    ctx.globalAlpha = 1;
  }

  function drawPentagon(x: number, y: number, size: number) {
    const sides = 5;
    for (let i = 0; i < sides; i++) {
      const angle = (i / sides) * Math.PI * 2 - Math.PI / 2;
      const px = x + Math.cos(angle) * size;
      const py = y + Math.sin(angle) * size;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.closePath();
  }

  function drawHexagon(x: number, y: number, size: number) {
    const sides = 6;
    for (let i = 0; i < sides; i++) {
      const angle = (i / sides) * Math.PI * 2;
      const px = x + Math.cos(angle) * size;
      const py = y + Math.sin(angle) * size;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.closePath();
  }

  function drawLabBackground() {
    // Draw grid
    ctx.strokeStyle = 'rgba(0, 255, 100, 0.05)';
    ctx.lineWidth = 1;
    
    const gridSize = 50;
    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    
    // Draw floating particles
    for (let i = 0; i < 50; i++) {
      const x = (Math.sin(time * 0.5 + i * 0.5) + 1) * width / 2;
      const y = (Math.cos(time * 0.3 + i * 0.7) + 1) * height / 2;
      const size = Math.sin(time * 2 + i) * 2 + 3;
      
      ctx.fillStyle = 'rgba(0, 255, 255, 0.3)';
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawSequenceBar() {
    const barWidth = width - 100;
    const barHeight = 10;
    const x = 50;
    const y = height - 50;
    
    // Draw track
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(x, y, barWidth, barHeight);
    
    // Draw progress
    ctx.fillStyle = '#00ff64';
    ctx.fillRect(x, y, barWidth * sequencePosition, barHeight);
    
    // Draw handle
    const handleX = x + barWidth * sequencePosition;
    ctx.fillStyle = '#DC143C';
    ctx.beginPath();
    ctx.arc(handleX, y + barHeight / 2, 15, 0, Math.PI * 2);
    ctx.fill();
    
    // Labels
    ctx.fillStyle = '#ffffff';
    ctx.font = '12px Space Grotesk';
    ctx.textAlign = 'left';
    ctx.fillText('START', x, y - 10);
    ctx.textAlign = 'right';
    ctx.fillText('END', x + barWidth, y - 10);
  }

  function drawHealthMeter() {
    const x = width - 150;
    const y = 50;
    const health = calculateDNAHealth();
    
    // Draw meter background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(x, y, 100, 20);
    
    // Draw health bar
    const healthColor = health > 0.7 ? '#00ff64' : health > 0.4 ? '#ffa500' : '#DC143C';
    ctx.fillStyle = healthColor;
    ctx.fillRect(x, y, 100 * health, 20);
    
    // Label
    ctx.fillStyle = '#ffffff';
    ctx.font = '14px Space Grotesk';
    ctx.textAlign = 'center';
    ctx.fillText('DNA HEALTH', x + 50, y - 10);
    ctx.fillText(`${Math.round(health * 100)}%`, x + 50, y + 15);
  }

  function drawMutationIndicators() {
    mutations.forEach(mutation => {
      const y = height / 2 - mutation.position * 20 + sequencePosition * height;
      
      if (y < 0 || y > height) return;
      
      const x = width - 50;
      
      // Draw mutation marker
      ctx.fillStyle = mutation.type === 'deletion' ? '#DC143C' : 
                      mutation.type === 'insertion' ? '#00ff64' : '#ffa500';
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x - 10, y - 10);
      ctx.lineTo(x - 10, y + 10);
      ctx.closePath();
      ctx.fill();
      
      // Pulse effect
      const pulse = Math.sin(time * 3) * 0.5 + 0.5;
      ctx.globalAlpha = pulse;
      ctx.strokeStyle = ctx.fillStyle;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x - 5, y, 10 + pulse * 5, 0, Math.PI * 2);
      ctx.stroke();
      ctx.globalAlpha = 1;
    });
  }

  function calculateDNAHealth(): number {
    // Calculate based on diversity and consistency
    const totalStrands = dnaStrands.length;
    const uniqueTypes = new Set(dnaStrands.map(s => s.contentType)).size;
    const diversity = uniqueTypes / 4;
    
    const averageValue = dnaStrands.reduce((sum, s) => sum + s.value, 0) / totalStrands;
    const consistency = Math.min(averageValue / 5, 1);
    
    return diversity * 0.5 + consistency * 0.5;
  }

  function handleMouseMove(e: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Check hover on strands
    let foundHover = false;
    dnaStrands.forEach(strand => {
      const x = width / 2 + strand.x;
      const y = height / 2 - strand.height + sequencePosition * height;
      
      if (y < -50 || y > height + 50) return;
      
      const dx = mouseX - x;
      const dy = mouseY - y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      
      if (dist < 20) {
        if (hoveredStrand !== strand) {
          hoveredStrand = strand;
          audioManager.playSound('bubble', 0.3);
        }
        foundHover = true;
      }
    });
    
    if (!foundHover) hoveredStrand = null;
  }

  function handleClick(e: MouseEvent) {
    if (hoveredStrand && mutationMode) {
      // Perform gene splicing
      audioManager.playSound('bubble', 0.5);
      
      // Create a mutation effect
      mutations.push({
        position: hoveredStrand.height / 20,
        type: 'substitution',
        timestamp: new Date(),
        impact: 0.8
      });
    }
  }

  function handleWheel(e: WheelEvent) {
    e.preventDefault();
    sequencePosition = Math.max(0, Math.min(1, sequencePosition + e.deltaY * 0.001));
  }

  function handleRotationChange(e: Event) {
    const value = parseFloat((e.target as HTMLInputElement).value);
    helixSpeed = value * 0.05;
  }

  function handleZoomChange(e: Event) {
    zoomLevel = parseFloat((e.target as HTMLInputElement).value);
    audioManager.playSound('bubble', 0.2);
  }

  function startSequencing() {
    isSequencing = true;
    sequencePosition = 0;
    
    const sequenceInterval = setInterval(() => {
      sequencePosition += 0.01;
      audioManager.playSound('bubble', 0.1);
      
      if (sequencePosition >= 1) {
        sequencePosition = 1;
        isSequencing = false;
        clearInterval(sequenceInterval);
        audioManager.playSound('levelup', 0.5);
      }
    }, 50);
  }
</script>

<div class="dna-container" bind:this={container}>
  <canvas bind:this={canvas}></canvas>
  
  <div class="controls">
    <div class="control-group">
      <label>Rotation Speed</label>
      <input 
        type="range" 
        min="0" 
        max="1" 
        step="0.01" 
        value="0.4"
        on:input={handleRotationChange}
      />
    </div>
    
    <div class="control-group">
      <label>Zoom Level</label>
      <input 
        type="range" 
        min="0.5" 
        max="2" 
        step="0.1" 
        bind:value={zoomLevel}
        on:input={handleZoomChange}
      />
    </div>
    
    <button class="sequence-btn" on:click={startSequencing} disabled={isSequencing}>
      {isSequencing ? 'Sequencing...' : 'Start Sequence'}
    </button>
    
    <button class="mutation-btn" class:active={mutationMode} on:click={() => mutationMode = !mutationMode}>
      Gene Splicing {mutationMode ? 'ON' : 'OFF'}
    </button>
  </div>
  
  {#if hoveredStrand}
    <div class="info-panel">
      <h3>Base Pair: {hoveredStrand.type}</h3>
      <p>Type: {hoveredStrand.contentType}</p>
      <p>Value: {hoveredStrand.value}</p>
      <p>Date: {hoveredStrand.date.toLocaleDateString()}</p>
    </div>
  {/if}
  
  <div class="mutation-alert" class:show={mutations.length > 5}>
    <span class="icon">⚠️</span>
    <span>High mutation rate detected!</span>
  </div>
</div>

<style>
  .dna-container {
    position: relative;
    width: 100%;
    height: 100vh;
    background: radial-gradient(ellipse at center, #001122 0%, #000511 100%);
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
    border: 1px solid #00ff64;
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
    width: 150px;
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
    background: #00ff64;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 0 10px #00ff64;
  }
  
  .sequence-btn,
  .mutation-btn {
    background: #4a9eff;
    border: none;
    color: white;
    padding: 10px 20px;
    border-radius: 10px;
    font-family: 'Space Grotesk';
    cursor: pointer;
    transition: all 0.3s ease;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 1px;
  }
  
  .sequence-btn:hover:not(:disabled) {
    background: #3a8eef;
    transform: translateY(-2px);
  }
  
  .sequence-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .mutation-btn {
    background: #DC143C;
  }
  
  .mutation-btn:hover {
    background: #B91C3C;
  }
  
  .mutation-btn.active {
    background: #00ff64;
    color: #000;
    box-shadow: 0 0 20px #00ff64;
  }
  
  .info-panel {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.8);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #00ff64;
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
  
  .mutation-alert {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0);
    background: rgba(255, 165, 0, 0.9);
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
  
  .mutation-alert.show {
    transform: translate(-50%, -50%) scale(1);
  }
  
  .mutation-alert .icon {
    font-size: 30px;
  }
</style>