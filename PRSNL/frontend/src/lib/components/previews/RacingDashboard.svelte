<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import { getAudioManager } from '$lib/utils/audioManager';

  export let data = generateMockData();

  // Canvas setup
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let container: HTMLDivElement;
  let width = 800;
  let height = 600;
  let animationFrame: number;

  // Dashboard state
  let speed = tweened(0, { duration: 300, easing: cubicOut });
  let rpm = tweened(0, { duration: 200, easing: cubicOut });
  let fuel = tweened(75, { duration: 1000, easing: cubicOut });
  let temperature = tweened(80, { duration: 500, easing: cubicOut });
  let turboActive = false;
  let lapTimes: LapTime[] = [];
  let currentLap: LapTime | null = null;
  let trackPosition = 0;

  // Animation state
  let time = 0;
  let particles: Particle[] = [];
  let neonTrails: NeonTrail[] = [];

  // Types
  interface LapTime {
    id: string;
    time: number;
    date: Date;
    speed: number;
    items: number;
  }

  interface Particle {
    x: number;
    y: number;
    vx: number;
    vy: number;
    size: number;
    color: string;
    life: number;
  }

  interface NeonTrail {
    points: { x: number; y: number }[];
    color: string;
    width: number;
    opacity: number;
  }

  function generateMockData() {
    const now = new Date();
    const lapData = [];
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      lapData.push({
        id: `lap-${i}`,
        time: 120 + Math.random() * 60, // 2-3 minutes
        date,
        speed: 50 + Math.random() * 100,
        items: Math.floor(Math.random() * 10) + 1
      });
    }
    
    return lapData;
  }

  onMount(() => {
    ctx = canvas.getContext('2d')!;
    
    // Initialize audio
    getAudioManager().init();
    getAudioManager().createSyntheticSounds();
    getAudioManager().playBackgroundMusic('racing');
    
    // Setup canvas
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Initialize lap times
    lapTimes = data;
    
    // Start animation
    animate();
    startDriving();
    
    // Keyboard controls
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
  });

  onDestroy(() => {
    if (animationFrame) cancelAnimationFrame(animationFrame);
    window.removeEventListener('resize', resizeCanvas);
    window.removeEventListener('keydown', handleKeyDown);
    window.removeEventListener('keyup', handleKeyUp);
  });

  function resizeCanvas() {
    const rect = container.getBoundingClientRect();
    width = rect.width;
    height = rect.height;
    canvas.width = width;
    canvas.height = height;
  }

  function startDriving() {
    // Simulate driving based on recent activity
    const recentActivity = data[0].items;
    speed.set(recentActivity * 15);
    rpm.set(recentActivity * 800);
    
    // Start a new lap
    currentLap = {
      id: `lap-new`,
      time: 0,
      date: new Date(),
      speed: 0,
      items: 0
    };
    
    // Update values periodically
    setInterval(() => {
      if (currentLap) {
        currentLap.time += 0.1;
        currentLap.speed = $speed;
        
        // Simulate fuel consumption
        fuel.update(f => Math.max(0, f - 0.1));
        
        // Update temperature based on speed
        temperature.set(80 + ($speed / 200) * 40);
        
        // Track progress
        trackPosition = (trackPosition + $speed * 0.001) % 1;
      }
    }, 100);
  }

  function animate() {
    time += 0.016;
    
    // Clear canvas
    ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
    ctx.fillRect(0, 0, width, height);
    
    // Draw racing track background
    drawTrack();
    
    // Update and draw particles
    updateParticles();
    
    // Draw dashboard elements
    drawSpeedometer();
    drawRPMGauge();
    drawFuelGauge();
    drawTemperatureGauge();
    drawLapTimer();
    drawTrackProgress();
    drawPitStopAlert();
    
    // Draw neon effects
    drawNeonEffects();
    
    animationFrame = requestAnimationFrame(animate);
  }

  function drawTrack() {
    // Draw racing track grid
    ctx.strokeStyle = 'rgba(220, 20, 60, 0.1)';
    ctx.lineWidth = 1;
    
    const perspective = 400;
    const lines = 20;
    
    for (let i = 0; i < lines; i++) {
      const y = (i / lines) * height;
      const scale = perspective / (perspective + y);
      const x1 = width / 2 - (width / 2) * scale;
      const x2 = width / 2 + (width / 2) * scale;
      
      ctx.beginPath();
      ctx.moveTo(x1, y);
      ctx.lineTo(x2, y);
      ctx.stroke();
    }
    
    // Moving road lines
    const offset = (time * 100) % 50;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.lineWidth = 3;
    ctx.setLineDash([30, 20]);
    ctx.lineDashOffset = -offset;
    
    ctx.beginPath();
    ctx.moveTo(width / 2, height);
    ctx.lineTo(width / 2, 0);
    ctx.stroke();
    
    ctx.setLineDash([]);
  }

  function drawSpeedometer() {
    const centerX = width / 2;
    const centerY = height / 2 + 50;
    const radius = 150;
    
    // Draw outer ring
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 20;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI * 0.75, Math.PI * 2.25);
    ctx.stroke();
    
    // Draw speed arc
    const speedPercent = Math.min($speed / 200, 1);
    const speedAngle = Math.PI * 0.75 + speedPercent * Math.PI * 1.5;
    
    const gradient = ctx.createLinearGradient(
      centerX - radius, centerY,
      centerX + radius, centerY
    );
    gradient.addColorStop(0, '#00ff64');
    gradient.addColorStop(0.5, '#ffff00');
    gradient.addColorStop(1, '#ff0000');
    
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 20;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI * 0.75, speedAngle);
    ctx.stroke();
    
    // Draw speed ticks
    ctx.strokeStyle = '#666';
    ctx.lineWidth = 2;
    for (let i = 0; i <= 10; i++) {
      const angle = Math.PI * 0.75 + (i / 10) * Math.PI * 1.5;
      const x1 = centerX + Math.cos(angle) * (radius - 30);
      const y1 = centerY + Math.sin(angle) * (radius - 30);
      const x2 = centerX + Math.cos(angle) * (radius - 40);
      const y2 = centerY + Math.sin(angle) * (radius - 40);
      
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
    
    // Draw speed value
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 48px Space Grotesk';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(Math.round($speed).toString(), centerX, centerY);
    
    ctx.font = '16px Space Grotesk';
    ctx.fillText('KM/H', centerX, centerY + 30);
    
    // Draw needle
    const needleAngle = Math.PI * 0.75 + speedPercent * Math.PI * 1.5;
    ctx.strokeStyle = '#DC143C';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(
      centerX + Math.cos(needleAngle) * (radius - 40),
      centerY + Math.sin(needleAngle) * (radius - 40)
    );
    ctx.stroke();
    
    // Center cap
    ctx.fillStyle = '#DC143C';
    ctx.beginPath();
    ctx.arc(centerX, centerY, 10, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawRPMGauge() {
    const x = 150;
    const y = 150;
    const radius = 80;
    
    // Background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
    
    // RPM arc
    const rpmPercent = Math.min($rpm / 8000, 1);
    const rpmColor = rpmPercent > 0.8 ? '#ff0000' : '#4a9eff';
    
    ctx.strokeStyle = rpmColor;
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.arc(x, y, radius - 10, -Math.PI / 2, -Math.PI / 2 + rpmPercent * Math.PI * 2);
    ctx.stroke();
    
    // Value
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 24px Space Grotesk';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(Math.round($rpm / 1000).toString(), x, y);
    
    ctx.font = '12px Space Grotesk';
    ctx.fillText('RPM x1000', x, y + 20);
  }

  function drawFuelGauge() {
    const x = width - 150;
    const y = 150;
    const width = 120;
    const height = 60;
    
    // Background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(x - width / 2, y - height / 2, width, height);
    
    // Fuel level
    const fuelColor = $fuel < 20 ? '#ff0000' : $fuel < 50 ? '#ffa500' : '#00ff64';
    ctx.fillStyle = fuelColor;
    ctx.fillRect(x - width / 2, y - height / 2, width * ($fuel / 100), height);
    
    // Icon and text
    ctx.fillStyle = '#ffffff';
    ctx.font = '24px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('⛽', x, y);
    
    ctx.font = '14px Space Grotesk';
    ctx.fillText(`${Math.round($fuel)}%`, x, y + 40);
  }

  function drawTemperatureGauge() {
    const x = 150;
    const y = height - 150;
    const width = 120;
    const height = 20;
    
    // Background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(x - width / 2, y - height / 2, width, height);
    
    // Temperature level
    const tempPercent = ($temperature - 50) / 100;
    const tempColor = tempPercent > 0.8 ? '#ff0000' : tempPercent > 0.6 ? '#ffa500' : '#4a9eff';
    ctx.fillStyle = tempColor;
    ctx.fillRect(x - width / 2, y - height / 2, width * tempPercent, height);
    
    // Text
    ctx.fillStyle = '#ffffff';
    ctx.font = '14px Space Grotesk';
    ctx.textAlign = 'center';
    ctx.fillText(`TEMP: ${Math.round($temperature)}°C`, x, y - 20);
  }

  function drawLapTimer() {
    const x = width - 200;
    const y = height - 150;
    
    // Background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(x - 80, y - 60, 160, 120);
    
    // Current lap time
    if (currentLap) {
      ctx.fillStyle = '#00ff64';
      ctx.font = 'bold 24px Space Grotesk';
      ctx.textAlign = 'center';
      ctx.fillText(formatTime(currentLap.time), x, y);
      
      ctx.fillStyle = '#666';
      ctx.font = '12px Space Grotesk';
      ctx.fillText('CURRENT LAP', x, y - 30);
    }
    
    // Best lap
    if (lapTimes.length > 0) {
      const bestLap = lapTimes.reduce((best, lap) => lap.time < best.time ? lap : best);
      ctx.fillStyle = '#DC143C';
      ctx.font = '16px Space Grotesk';
      ctx.fillText(`BEST: ${formatTime(bestLap.time)}`, x, y + 30);
    }
  }

  function drawTrackProgress() {
    const x = width / 2;
    const y = height - 50;
    const trackWidth = 400;
    const trackHeight = 10;
    
    // Track background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(x - trackWidth / 2, y - trackHeight / 2, trackWidth, trackHeight);
    
    // Progress
    ctx.fillStyle = '#DC143C';
    ctx.fillRect(x - trackWidth / 2, y - trackHeight / 2, trackWidth * trackPosition, trackHeight);
    
    // Car position
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(x - trackWidth / 2 + trackWidth * trackPosition, y, 8, 0, Math.PI * 2);
    ctx.fill();
    
    // Checkpoints
    for (let i = 0; i < 4; i++) {
      const checkX = x - trackWidth / 2 + (i / 3) * trackWidth;
      ctx.strokeStyle = '#666';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(checkX, y - 10);
      ctx.lineTo(checkX, y + 10);
      ctx.stroke();
    }
  }

  function drawPitStopAlert() {
    if ($fuel < 20) {
      const x = width / 2;
      const y = 100;
      
      // Flashing background
      const flash = Math.sin(time * 10) > 0;
      if (flash) {
        ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
        ctx.fillRect(x - 150, y - 30, 300, 60);
      }
      
      // Alert text
      ctx.fillStyle = '#ff0000';
      ctx.font = 'bold 24px Space Grotesk';
      ctx.textAlign = 'center';
      ctx.fillText('⚠️ PIT STOP REQUIRED ⚠️', x, y);
      
      ctx.fillStyle = '#ffffff';
      ctx.font = '14px Space Grotesk';
      ctx.fillText('Low fuel - return to pit lane', x, y + 20);
    }
  }

  function updateParticles() {
    // Add exhaust particles when driving
    if ($speed > 0) {
      for (let i = 0; i < 3; i++) {
        particles.push({
          x: width / 2 + (Math.random() - 0.5) * 50,
          y: height - 100,
          vx: (Math.random() - 0.5) * 2,
          vy: Math.random() * -5 - 2,
          size: Math.random() * 5 + 3,
          color: turboActive ? '#00ffff' : '#ff6600',
          life: 1
        });
      }
    }
    
    // Update particles
    particles = particles.filter(particle => {
      particle.x += particle.vx;
      particle.y += particle.vy;
      particle.vy += 0.2; // Gravity
      particle.life -= 0.02;
      
      // Draw particle
      ctx.globalAlpha = particle.life;
      ctx.fillStyle = particle.color;
      ctx.beginPath();
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      ctx.fill();
      
      return particle.life > 0;
    });
    
    ctx.globalAlpha = 1;
  }

  function drawNeonEffects() {
    if ($speed > 100) {
      // Speed lines
      ctx.strokeStyle = 'rgba(0, 255, 255, 0.3)';
      ctx.lineWidth = 2;
      
      for (let i = 0; i < 5; i++) {
        const y = Math.random() * height;
        const length = 50 + Math.random() * 100;
        
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(length, y);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.moveTo(width, y);
        ctx.lineTo(width - length, y);
        ctx.stroke();
      }
    }
    
    // Turbo effect
    if (turboActive) {
      const gradient = ctx.createRadialGradient(
        width / 2, height / 2, 0,
        width / 2, height / 2, 300
      );
      gradient.addColorStop(0, 'rgba(0, 255, 255, 0)');
      gradient.addColorStop(1, 'rgba(0, 255, 255, 0.2)');
      
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);
    }
  }

  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  }

  function handleKeyDown(e: KeyboardEvent) {
    switch (e.key) {
      case 'ArrowUp':
        speed.update(s => Math.min(200, s + 10));
        rpm.update(r => Math.min(8000, r + 500));
        getAudioManager().playSound('engine', 0.5);
        break;
      case 'ArrowDown':
        speed.update(s => Math.max(0, s - 10));
        rpm.update(r => Math.max(0, r - 500));
        break;
      case ' ':
        turboActive = true;
        speed.update(s => Math.min(200, s + 50));
        getAudioManager().playSound('whoosh', 0.7);
        break;
    }
  }

  function handleKeyUp(e: KeyboardEvent) {
    if (e.key === ' ') {
      turboActive = false;
    }
  }

  function pitStop() {
    fuel.set(100);
    temperature.set(80);
    getAudioManager().playSound('levelup', 0.5);
  }
</script>

<div class="dashboard-container" bind:this={container}>
  <canvas bind:this={canvas}></canvas>
  
  <div class="controls">
    <div class="control-info">
      <h3>Controls</h3>
      <p>↑ Accelerate</p>
      <p>↓ Brake</p>
      <p>SPACE Turbo Boost</p>
    </div>
    
    <button class="pit-stop-btn" on:click={pitStop}>
      PIT STOP
    </button>
  </div>
  
  <div class="lap-history">
    <h3>Recent Laps</h3>
    {#each lapTimes.slice(0, 5) as lap}
      <div class="lap-entry">
        <span class="lap-date">{lap.date.toLocaleDateString()}</span>
        <span class="lap-time">{formatTime(lap.time)}</span>
        <span class="lap-items">{lap.items} items</span>
      </div>
    {/each}
  </div>
  
  <div class="speed-indicator">
    <div class="speed-value">{Math.round($speed)}</div>
    <div class="speed-label">KM/H</div>
  </div>
</div>

<style>
  .dashboard-container {
    position: relative;
    width: 100%;
    height: 100vh;
    background: #000;
    overflow: hidden;
    font-family: 'Space Grotesk';
  }
  
  canvas {
    width: 100%;
    height: 100%;
  }
  
  .controls {
    position: absolute;
    bottom: 20px;
    left: 20px;
    background: rgba(0, 0, 0, 0.8);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #DC143C;
    backdrop-filter: blur(10px);
  }
  
  .control-info h3 {
    margin: 0 0 10px 0;
    color: #DC143C;
    font-size: 16px;
    text-transform: uppercase;
  }
  
  .control-info p {
    margin: 5px 0;
    color: #999;
    font-size: 14px;
  }
  
  .pit-stop-btn {
    margin-top: 15px;
    background: #DC143C;
    border: none;
    color: white;
    padding: 10px 30px;
    border-radius: 10px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 1px;
    width: 100%;
  }
  
  .pit-stop-btn:hover {
    background: #B91C3C;
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(220, 20, 60, 0.5);
  }
  
  .lap-history {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.8);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #333;
    backdrop-filter: blur(10px);
    min-width: 250px;
  }
  
  .lap-history h3 {
    margin: 0 0 15px 0;
    color: #00ff64;
    font-size: 16px;
    text-transform: uppercase;
  }
  
  .lap-entry {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #333;
    color: #999;
    font-size: 14px;
  }
  
  .lap-entry:last-child {
    border-bottom: none;
  }
  
  .lap-time {
    color: #DC143C;
    font-weight: 600;
  }
  
  .lap-items {
    color: #00ff64;
    font-size: 12px;
  }
  
  .speed-indicator {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    pointer-events: none;
  }
  
  .speed-value {
    font-size: 120px;
    font-weight: 800;
    color: rgba(255, 255, 255, 0.1);
    text-shadow: 0 0 40px rgba(220, 20, 60, 0.5);
  }
  
  .speed-label {
    font-size: 24px;
    color: rgba(255, 255, 255, 0.2);
    letter-spacing: 3px;
  }
</style>