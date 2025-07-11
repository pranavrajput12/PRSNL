<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { spring, tweened } from 'svelte/motion';
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

  // Ecosystem state
  let creatures: Creature[] = [];
  let plants: Plant[] = [];
  let weather: Weather = { type: 'sunny', intensity: 0.5 };
  let season: 'spring' | 'summer' | 'autumn' | 'winter' = 'spring';
  let terrainParticles: Particle[] = [];
  let feedingMode = false;
  let selectedCreature: Creature | null = null;
  let biodiversityScore = tweened(0, { duration: 1000, easing: cubicOut });

  // Animation state
  let time = 0;
  let dayNightCycle = 0;

  // Types
  interface Creature {
    id: string;
    type: 'article' | 'video' | 'note' | 'bookmark';
    x: number;
    y: number;
    size: number;
    age: number;
    health: number;
    speed: number;
    direction: number;
    color: string;
    emoji: string;
    behavior: 'wander' | 'feed' | 'rest' | 'socialize';
    target: { x: number; y: number } | null;
  }

  interface Plant {
    x: number;
    y: number;
    size: number;
    growth: number;
    type: string;
    color: string;
    swayPhase: number;
  }

  interface Weather {
    type: 'sunny' | 'rainy' | 'cloudy' | 'snowy';
    intensity: number;
  }

  interface Particle {
    x: number;
    y: number;
    vx: number;
    vy: number;
    size: number;
    color: string;
    life: number;
    type: string;
  }

  function generateMockData() {
    return {
      articles: 25,
      videos: 18,
      notes: 32,
      bookmarks: 15,
      totalItems: 90
    };
  }

  onMount(() => {
    ctx = canvas.getContext('2d')!;
    
    // Initialize audio
    getAudioManager().init();
    getAudioManager().createSyntheticSounds();
    getAudioManager().playBackgroundMusic('nature');
    
    // Setup canvas
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Initialize ecosystem
    createEcosystem();
    calculateBiodiversity();
    animate();
    
    // Mouse interactions
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('click', handleClick);
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

  function createEcosystem() {
    // Create creatures based on content types
    const creatureTypes = [
      { type: 'article', emoji: '📚', color: '#DC143C', count: Math.min(data.articles, 10) },
      { type: 'video', emoji: '🎬', color: '#4a9eff', count: Math.min(data.videos, 10) },
      { type: 'note', emoji: '📝', color: '#00ff64', count: Math.min(data.notes, 10) },
      { type: 'bookmark', emoji: '🔖', color: '#ffa500', count: Math.min(data.bookmarks, 10) }
    ];
    
    creatureTypes.forEach(({ type, emoji, color, count }) => {
      for (let i = 0; i < count; i++) {
        creatures.push({
          id: `${type}-${i}`,
          type: type as any,
          x: Math.random() * width,
          y: height - 100 - Math.random() * (height - 200),
          size: 20 + Math.random() * 20,
          age: Math.random() * 100,
          health: 0.8 + Math.random() * 0.2,
          speed: 0.5 + Math.random() * 1,
          direction: Math.random() * Math.PI * 2,
          color,
          emoji,
          behavior: 'wander',
          target: null
        });
      }
    });
    
    // Create plants
    for (let i = 0; i < 20; i++) {
      plants.push({
        x: Math.random() * width,
        y: height - 50 - Math.random() * 150,
        size: 30 + Math.random() * 50,
        growth: Math.random(),
        type: ['tree', 'flower', 'grass'][Math.floor(Math.random() * 3)],
        color: `hsl(${100 + Math.random() * 40}, 70%, 40%)`,
        swayPhase: Math.random() * Math.PI * 2
      });
    }
  }

  function calculateBiodiversity() {
    const totalCreatures = creatures.length;
    const uniqueTypes = new Set(creatures.map(c => c.type)).size;
    const typeBalance = 1 - Math.abs(0.25 - (creatures.filter(c => c.type === 'article').length / totalCreatures));
    const healthAverage = creatures.reduce((sum, c) => sum + c.health, 0) / totalCreatures;
    
    const score = ((uniqueTypes / 4) * 0.4 + typeBalance * 0.3 + healthAverage * 0.3) * 100;
    biodiversityScore.set(score);
  }

  function animate() {
    time += 0.016;
    dayNightCycle = (time * 0.05) % (Math.PI * 2);
    
    // Clear canvas with sky gradient
    drawSky();
    
    // Draw terrain
    drawTerrain();
    
    // Update weather
    updateWeather();
    
    // Draw plants
    drawPlants();
    
    // Update and draw creatures
    updateCreatures();
    drawCreatures();
    
    // Draw UI elements
    drawSeasonIndicator();
    drawBiodiversityMeter();
    drawWeatherEffects();
    
    animationFrame = requestAnimationFrame(animate);
  }

  function drawSky() {
    const daylight = Math.max(0, Math.cos(dayNightCycle));
    
    // Sky gradient based on time of day
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    
    if (daylight > 0.7) {
      // Day
      gradient.addColorStop(0, '#87CEEB');
      gradient.addColorStop(1, '#98D8E8');
    } else if (daylight > 0.3) {
      // Sunset/Sunrise
      gradient.addColorStop(0, '#FF6B35');
      gradient.addColorStop(0.5, '#F7931E');
      gradient.addColorStop(1, '#FDB462');
    } else {
      // Night
      gradient.addColorStop(0, '#0a0a0a');
      gradient.addColorStop(1, '#1a1a1a');
    }
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    
    // Stars at night
    if (daylight < 0.3) {
      ctx.fillStyle = 'white';
      for (let i = 0; i < 100; i++) {
        const x = (i * 137.5) % width;
        const y = (i * 89) % (height * 0.6);
        const size = Math.sin(time + i) * 0.5 + 1;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    
    // Sun/Moon
    const celestialX = width / 2 + Math.cos(dayNightCycle - Math.PI / 2) * 300;
    const celestialY = height / 2 + Math.sin(dayNightCycle - Math.PI / 2) * 300;
    
    if (daylight > 0.1) {
      // Sun
      ctx.fillStyle = '#FFD700';
      ctx.beginPath();
      ctx.arc(celestialX, celestialY, 40, 0, Math.PI * 2);
      ctx.fill();
    } else {
      // Moon
      ctx.fillStyle = '#F0F0F0';
      ctx.beginPath();
      ctx.arc(celestialX, celestialY, 30, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawTerrain() {
    // Ground
    const groundGradient = ctx.createLinearGradient(0, height - 100, 0, height);
    const seasonColors = {
      spring: ['#90EE90', '#228B22'],
      summer: ['#7CFC00', '#006400'],
      autumn: ['#DAA520', '#8B4513'],
      winter: ['#F0F8FF', '#B0C4DE']
    };
    
    const [topColor, bottomColor] = seasonColors[season];
    groundGradient.addColorStop(0, topColor);
    groundGradient.addColorStop(1, bottomColor);
    
    ctx.fillStyle = groundGradient;
    ctx.fillRect(0, height - 100, width, 100);
    
    // Texture
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 20; i++) {
      const y = height - 100 + i * 5;
      ctx.beginPath();
      ctx.moveTo(0, y);
      for (let x = 0; x < width; x += 10) {
        ctx.lineTo(x, y + Math.sin(x * 0.05 + time) * 2);
      }
      ctx.stroke();
    }
  }

  function drawPlants() {
    plants.forEach(plant => {
      ctx.save();
      ctx.translate(plant.x, plant.y);
      
      // Sway in wind
      const sway = Math.sin(time + plant.swayPhase) * 0.1;
      ctx.rotate(sway);
      
      if (plant.type === 'tree') {
        // Tree trunk
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(-5, 0, 10, -plant.size * 0.4);
        
        // Leaves
        ctx.fillStyle = plant.color;
        ctx.beginPath();
        ctx.arc(0, -plant.size * 0.4, plant.size * 0.3 * plant.growth, 0, Math.PI * 2);
        ctx.fill();
        
        // Seasonal effects
        if (season === 'autumn') {
          ctx.fillStyle = '#FF6347';
          ctx.beginPath();
          ctx.arc(-10, -plant.size * 0.3, plant.size * 0.15, 0, Math.PI * 2);
          ctx.fill();
        }
      } else if (plant.type === 'flower') {
        // Stem
        ctx.strokeStyle = '#228B22';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -plant.size * plant.growth);
        ctx.stroke();
        
        // Petals
        ctx.fillStyle = plant.color;
        for (let i = 0; i < 6; i++) {
          ctx.save();
          ctx.translate(0, -plant.size * plant.growth);
          ctx.rotate((i / 6) * Math.PI * 2);
          ctx.beginPath();
          ctx.ellipse(0, -10, 5, 10, 0, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        }
      }
      
      ctx.restore();
    });
  }

  function updateCreatures() {
    creatures.forEach(creature => {
      // Update behavior
      if (Math.random() < 0.01) {
        const behaviors = ['wander', 'feed', 'rest', 'socialize'];
        creature.behavior = behaviors[Math.floor(Math.random() * behaviors.length)] as any;
      }
      
      // Execute behavior
      switch (creature.behavior) {
        case 'wander':
          creature.direction += (Math.random() - 0.5) * 0.2;
          creature.x += Math.cos(creature.direction) * creature.speed;
          creature.y += Math.sin(creature.direction) * creature.speed * 0.5;
          break;
          
        case 'feed':
          if (!creature.target) {
            const nearestPlant = plants.reduce((nearest, plant) => {
              const dist = Math.hypot(plant.x - creature.x, plant.y - creature.y);
              return dist < Math.hypot(nearest.x - creature.x, nearest.y - creature.y) ? plant : nearest;
            });
            creature.target = { x: nearestPlant.x, y: nearestPlant.y };
          }
          
          if (creature.target) {
            const dx = creature.target.x - creature.x;
            const dy = creature.target.y - creature.y;
            const dist = Math.hypot(dx, dy);
            
            if (dist > 5) {
              creature.x += (dx / dist) * creature.speed;
              creature.y += (dy / dist) * creature.speed;
            } else {
              creature.health = Math.min(1, creature.health + 0.01);
              creature.target = null;
              creature.behavior = 'wander';
            }
          }
          break;
          
        case 'rest':
          creature.speed = 0.1;
          break;
          
        case 'socialize':
          const nearbyCreature = creatures.find(c => 
            c !== creature && 
            c.type === creature.type &&
            Math.hypot(c.x - creature.x, c.y - creature.y) < 100
          );
          
          if (nearbyCreature) {
            const dx = nearbyCreature.x - creature.x;
            const dy = nearbyCreature.y - creature.y;
            creature.x += dx * 0.01;
            creature.y += dy * 0.01;
          }
          break;
      }
      
      // Boundaries
      creature.x = Math.max(creature.size, Math.min(width - creature.size, creature.x));
      creature.y = Math.max(100, Math.min(height - 100 - creature.size, creature.y));
      
      // Age and health
      creature.age += 0.01;
      creature.health -= 0.0001;
      
      // Growth
      if (creature.health > 0.8 && creature.age < 50) {
        creature.size = Math.min(40, creature.size + 0.01);
      }
    });
    
    // Remove dead creatures
    creatures = creatures.filter(c => c.health > 0);
    
    // Breeding
    if (creatures.length < 40 && Math.random() < 0.001) {
      const parent = creatures[Math.floor(Math.random() * creatures.length)];
      if (parent && parent.health > 0.7) {
        creatures.push({
          ...parent,
          id: `${parent.type}-${Date.now()}`,
          x: parent.x + (Math.random() - 0.5) * 50,
          y: parent.y + (Math.random() - 0.5) * 50,
          size: 10,
          age: 0,
          health: 1,
          behavior: 'wander',
          target: null
        });
        getAudioManager().playSound('chirp', 0.3);
      }
    }
  }

  function drawCreatures() {
    creatures.forEach(creature => {
      ctx.save();
      ctx.translate(creature.x, creature.y);
      
      // Shadow
      ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
      ctx.beginPath();
      ctx.ellipse(0, creature.size / 2, creature.size * 0.8, creature.size * 0.3, 0, 0, Math.PI * 2);
      ctx.fill();
      
      // Body bounce animation
      const bounce = Math.abs(Math.sin(time * 5 + creature.age)) * 5;
      ctx.translate(0, -bounce);
      
      // Health indicator
      if (creature.health < 0.5) {
        ctx.strokeStyle = '#ff0000';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(0, -creature.size, creature.size + 5, 0, Math.PI * 2);
        ctx.stroke();
      }
      
      // Creature body
      ctx.fillStyle = creature.color;
      ctx.beginPath();
      ctx.arc(0, 0, creature.size, 0, Math.PI * 2);
      ctx.fill();
      
      // Emoji
      ctx.font = `${creature.size * 1.2}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(creature.emoji, 0, 0);
      
      // Selection indicator
      if (creature === selectedCreature) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(0, 0, creature.size + 10, 0, Math.PI * 2);
        ctx.stroke();
      }
      
      ctx.restore();
    });
  }

  function updateWeather() {
    // Change weather occasionally
    if (Math.random() < 0.001) {
      const weatherTypes = ['sunny', 'rainy', 'cloudy', 'snowy'];
      weather.type = weatherTypes[Math.floor(Math.random() * weatherTypes.length)] as any;
      weather.intensity = 0.3 + Math.random() * 0.7;
    }
    
    // Add weather particles
    if (weather.type === 'rainy' && Math.random() < weather.intensity) {
      terrainParticles.push({
        x: Math.random() * width,
        y: -10,
        vx: 0,
        vy: 5 + Math.random() * 5,
        size: 1 + Math.random() * 2,
        color: 'rgba(100, 149, 237, 0.6)',
        life: 1,
        type: 'rain'
      });
    } else if (weather.type === 'snowy' && Math.random() < weather.intensity * 0.5) {
      terrainParticles.push({
        x: Math.random() * width,
        y: -10,
        vx: (Math.random() - 0.5) * 2,
        vy: 1 + Math.random() * 2,
        size: 2 + Math.random() * 3,
        color: 'rgba(255, 255, 255, 0.8)',
        life: 1,
        type: 'snow'
      });
    }
    
    // Update particles
    terrainParticles = terrainParticles.filter(particle => {
      particle.x += particle.vx;
      particle.y += particle.vy;
      
      if (particle.type === 'rain') {
        // Rain falls straight
        if (particle.y > height - 100) {
          // Splash effect
          for (let i = 0; i < 3; i++) {
            terrainParticles.push({
              x: particle.x,
              y: particle.y,
              vx: (Math.random() - 0.5) * 2,
              vy: -Math.random() * 3,
              size: 1,
              color: 'rgba(100, 149, 237, 0.4)',
              life: 0.5,
              type: 'splash'
            });
          }
          return false;
        }
      } else if (particle.type === 'snow') {
        // Snow drifts
        particle.x += Math.sin(time * 2 + particle.y * 0.01) * 0.5;
        if (particle.y > height - 100) {
          return false;
        }
      }
      
      particle.life -= 0.01;
      return particle.life > 0 && particle.y < height;
    });
  }

  function drawWeatherEffects() {
    // Draw particles
    terrainParticles.forEach(particle => {
      ctx.globalAlpha = particle.life;
      ctx.fillStyle = particle.color;
      
      if (particle.type === 'rain') {
        ctx.fillRect(particle.x, particle.y, particle.size, particle.size * 10);
      } else {
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fill();
      }
    });
    
    ctx.globalAlpha = 1;
    
    // Weather overlay
    if (weather.type === 'cloudy') {
      ctx.fillStyle = `rgba(200, 200, 200, ${weather.intensity * 0.3})`;
      ctx.fillRect(0, 0, width, height);
    }
  }

  function drawSeasonIndicator() {
    const x = 50;
    const y = 50;
    
    // Season wheel
    const seasons = ['spring', 'summer', 'autumn', 'winter'];
    const colors = ['#90EE90', '#FFD700', '#FF8C00', '#87CEEB'];
    const currentIndex = seasons.indexOf(season);
    
    seasons.forEach((s, i) => {
      const angle = (i / 4) * Math.PI * 2 - Math.PI / 2;
      const isActive = i === currentIndex;
      
      ctx.fillStyle = isActive ? colors[i] : '#333';
      ctx.beginPath();
      ctx.arc(x, y, isActive ? 25 : 20, angle, angle + Math.PI / 2);
      ctx.lineTo(x, y);
      ctx.closePath();
      ctx.fill();
    });
    
    // Center
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(x, y, 10, 0, Math.PI * 2);
    ctx.fill();
    
    // Label
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 16px Space Grotesk';
    ctx.textAlign = 'center';
    ctx.fillText(season.toUpperCase(), x, y + 50);
  }

  function drawBiodiversityMeter() {
    const x = width - 150;
    const y = 50;
    const radius = 40;
    
    // Background circle
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.stroke();
    
    // Score arc
    const scoreAngle = ($biodiversityScore / 100) * Math.PI * 2;
    const scoreColor = $biodiversityScore > 70 ? '#00ff64' : 
                      $biodiversityScore > 40 ? '#ffa500' : '#ff0000';
    
    ctx.strokeStyle = scoreColor;
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.arc(x, y, radius, -Math.PI / 2, -Math.PI / 2 + scoreAngle);
    ctx.stroke();
    
    // Score text
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 20px Space Grotesk';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(Math.round($biodiversityScore).toString(), x, y);
    
    ctx.font = '12px Space Grotesk';
    ctx.fillText('BIODIVERSITY', x, y + 60);
  }

  function handleMouseMove(e: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Check hover on creatures
    selectedCreature = null;
    creatures.forEach(creature => {
      const dist = Math.hypot(mouseX - creature.x, mouseY - creature.y);
      if (dist < creature.size) {
        selectedCreature = creature;
      }
    });
  }

  function handleClick(e: MouseEvent) {
    if (feedingMode && selectedCreature) {
      selectedCreature.health = Math.min(1, selectedCreature.health + 0.2);
      selectedCreature.size = Math.min(40, selectedCreature.size + 2);
      getAudioManager().playSound('chirp', 0.5);
      
      // Create happy particles
      for (let i = 0; i < 10; i++) {
        const angle = (i / 10) * Math.PI * 2;
        terrainParticles.push({
          x: selectedCreature.x,
          y: selectedCreature.y,
          vx: Math.cos(angle) * 3,
          vy: Math.sin(angle) * 3 - 2,
          size: 3,
          color: '#FFD700',
          life: 1,
          type: 'joy'
        });
      }
    }
  }

  function changeSeason() {
    const seasons = ['spring', 'summer', 'autumn', 'winter'] as const;
    const currentIndex = seasons.indexOf(season);
    season = seasons[(currentIndex + 1) % 4];
    
    // Update plant colors
    plants.forEach(plant => {
      if (season === 'autumn') {
        plant.color = `hsl(${20 + Math.random() * 40}, 70%, 50%)`;
      } else if (season === 'winter') {
        plant.growth *= 0.5;
      } else if (season === 'spring') {
        plant.growth = Math.min(1, plant.growth + 0.3);
        plant.color = `hsl(${100 + Math.random() * 40}, 70%, 40%)`;
      }
    });
  }

  function feedCreatures() {
    feedingMode = !feedingMode;
    if (feedingMode) {
      getAudioManager().playSound('chirp', 0.3);
    }
  }
</script>

<div class="terrarium-container" bind:this={container}>
  <canvas bind:this={canvas}></canvas>
  
  <div class="controls">
    <button class="season-btn" on:click={changeSeason}>
      Change Season
    </button>
    
    <button class="feed-btn" class:active={feedingMode} on:click={feedCreatures}>
      {feedingMode ? 'Feeding Mode ON' : 'Feed Creatures'}
    </button>
    
    <div class="weather-control">
      <label>Weather</label>
      <select bind:value={weather.type}>
        <option value="sunny">☀️ Sunny</option>
        <option value="rainy">🌧️ Rainy</option>
        <option value="cloudy">☁️ Cloudy</option>
        <option value="snowy">❄️ Snowy</option>
      </select>
    </div>
  </div>
  
  <div class="ecosystem-stats">
    <h3>Ecosystem Health</h3>
    <div class="stat-grid">
      <div class="stat">
        <span class="stat-icon">📚</span>
        <span class="stat-value">{creatures.filter(c => c.type === 'article').length}</span>
        <span class="stat-label">Articles</span>
      </div>
      <div class="stat">
        <span class="stat-icon">🎬</span>
        <span class="stat-value">{creatures.filter(c => c.type === 'video').length}</span>
        <span class="stat-label">Videos</span>
      </div>
      <div class="stat">
        <span class="stat-icon">📝</span>
        <span class="stat-value">{creatures.filter(c => c.type === 'note').length}</span>
        <span class="stat-label">Notes</span>
      </div>
      <div class="stat">
        <span class="stat-icon">🔖</span>
        <span class="stat-value">{creatures.filter(c => c.type === 'bookmark').length}</span>
        <span class="stat-label">Bookmarks</span>
      </div>
    </div>
    
    <div class="health-status">
      {#if $biodiversityScore > 70}
        <p class="status-good">🌳 Thriving ecosystem!</p>
      {:else if $biodiversityScore > 40}
        <p class="status-medium">🌿 Growing steadily</p>
      {:else}
        <p class="status-poor">🌱 Needs more diversity</p>
      {/if}
    </div>
  </div>
  
  {#if selectedCreature}
    <div class="creature-info">
      <h3>{selectedCreature.emoji} {selectedCreature.type}</h3>
      <p>Age: {Math.floor(selectedCreature.age)}</p>
      <p>Health: {Math.round(selectedCreature.health * 100)}%</p>
      <p>Behavior: {selectedCreature.behavior}</p>
      {#if feedingMode}
        <p class="feed-hint">Click to feed!</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .terrarium-container {
    position: relative;
    width: 100%;
    height: 100vh;
    overflow: hidden;
    font-family: 'Space Grotesk';
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
    gap: 20px;
    background: rgba(0, 0, 0, 0.8);
    padding: 20px;
    border-radius: 20px;
    border: 1px solid #00ff64;
    backdrop-filter: blur(10px);
  }
  
  .season-btn,
  .feed-btn {
    background: #00ff64;
    border: none;
    color: #000;
    padding: 10px 20px;
    border-radius: 10px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .season-btn:hover,
  .feed-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(0, 255, 100, 0.5);
  }
  
  .feed-btn.active {
    background: #DC143C;
    color: white;
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.5);
  }
  
  .weather-control {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  
  .weather-control label {
    color: #00ff64;
    font-size: 12px;
    text-transform: uppercase;
  }
  
  .weather-control select {
    background: rgba(0, 0, 0, 0.5);
    color: white;
    border: 1px solid #00ff64;
    padding: 8px 15px;
    border-radius: 8px;
    font-family: 'Space Grotesk';
    cursor: pointer;
  }
  
  .ecosystem-stats {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.8);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #00ff64;
    backdrop-filter: blur(10px);
    color: white;
  }
  
  .ecosystem-stats h3 {
    margin: 0 0 15px 0;
    color: #00ff64;
    font-size: 18px;
    text-transform: uppercase;
  }
  
  .stat-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
    margin-bottom: 15px;
  }
  
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
  }
  
  .stat-icon {
    font-size: 24px;
  }
  
  .stat-value {
    font-size: 20px;
    font-weight: 700;
    color: #00ff64;
  }
  
  .stat-label {
    font-size: 12px;
    color: #999;
  }
  
  .health-status p {
    margin: 0;
    padding: 10px;
    border-radius: 8px;
    text-align: center;
    font-weight: 600;
  }
  
  .status-good {
    background: rgba(0, 255, 100, 0.2);
    color: #00ff64;
  }
  
  .status-medium {
    background: rgba(255, 165, 0, 0.2);
    color: #ffa500;
  }
  
  .status-poor {
    background: rgba(220, 20, 60, 0.2);
    color: #DC143C;
  }
  
  .creature-info {
    position: absolute;
    bottom: 150px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.9);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #ffffff;
    color: white;
    text-align: center;
    backdrop-filter: blur(10px);
  }
  
  .creature-info h3 {
    margin: 0 0 10px 0;
    color: #00ff64;
  }
  
  .creature-info p {
    margin: 5px 0;
    color: #ccc;
    font-size: 14px;
  }
  
  .feed-hint {
    color: #DC143C !important;
    font-weight: 600;
    animation: pulse 1s ease-in-out infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
</style>