<script lang="ts" type="module">
  import { onMount, onDestroy } from 'svelte';
  import { spring, tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import { getAudioManager } from '$lib/utils/audioManager';

  export let personalityData = generateMockPersonality();

  // Canvas setup
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let container: HTMLDivElement;
  let width = 800;
  let height = 600;
  let animationFrame: number;

  // Avatar state
  let avatar: Avatar;
  let particles: Particle[] = [];
  let auraRings: AuraRing[] = [];
  let skillNodes: SkillNode[] = [];
  let achievements: Achievement[] = [];

  // Animation state
  let time = 0;
  let level = tweened(1, { duration: 1000, easing: cubicOut });
  let experience = tweened(0, { duration: 500, easing: cubicOut });
  let selectedSkill: SkillNode | null = null;

  // Types
  interface Avatar {
    x: number;
    y: number;
    size: number;
    color: string;
    auraColor: string;
    personality: string;
    level: number;
    exp: number;
    traits: string[];
    mood: string;
    evolution: number;
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

  interface AuraRing {
    radius: number;
    rotation: number;
    speed: number;
    color: string;
    opacity: number;
    thickness: number;
  }

  interface SkillNode {
    id: string;
    name: string;
    x: number;
    y: number;
    level: number;
    maxLevel: number;
    unlocked: boolean;
    connections: string[];
    icon: string;
    description: string;
  }

  interface Achievement {
    id: string;
    name: string;
    description: string;
    icon: string;
    unlocked: boolean;
    timestamp: Date;
  }

  function generateMockPersonality() {
    return {
      type: 'explorer',
      name: 'The Digital Explorer',
      level: 15,
      exp: 3250,
      traits: ['Curious', 'Diverse interests', 'Adventurous', 'Open-minded'],
      confidence: 0.85,
      stats: {
        knowledge_breadth: 78,
        learning_speed: 65,
        retention_rate: 82,
        curiosity_index: 91,
        consistency_score: 73,
      },
    };
  }

  onMount(() => {
    ctx = canvas.getContext('2d')!;

    // Initialize audio
    const audioManager = getAudioManager();
    audioManager.init();
    audioManager.createSyntheticSounds();
    audioManager.playBackgroundMusic('rpg');

    // Setup canvas
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Initialize avatar
    createAvatar();
    createSkillTree();
    generateAchievements();
    animate();

    // Mouse interactions
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('click', handleClick);

    // Set initial values
    level.set(personalityData.level);
    experience.set(personalityData.exp % 1000);
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

  function createAvatar() {
    const colors = {
      explorer: '#DC143C',
      specialist: '#4a9eff',
      connector: '#00ff64',
      practitioner: '#ffa500',
    };

    avatar = {
      x: width / 2,
      y: height / 2,
      size: 60,
      color: colors[personalityData.type] || '#DC143C',
      auraColor: colors[personalityData.type] || '#DC143C',
      personality: personalityData.name,
      level: personalityData.level,
      exp: personalityData.exp,
      traits: personalityData.traits,
      mood: 'active',
      evolution: 0,
    };

    // Create aura rings
    for (let i = 0; i < 3; i++) {
      auraRings.push({
        radius: 80 + i * 30,
        rotation: 0,
        speed: 0.01 + i * 0.005,
        color: avatar.auraColor,
        opacity: 0.3 - i * 0.1,
        thickness: 3 - i,
      });
    }
  }

  function createSkillTree() {
    const skills = [
      {
        id: 'speed-reader',
        name: 'Speed Reader',
        icon: '📚',
        description: 'Read articles 2x faster',
      },
      {
        id: 'video-binger',
        name: 'Video Binger',
        icon: '🎬',
        description: 'Process videos efficiently',
      },
      { id: 'note-master', name: 'Note Master', icon: '📝', description: 'Enhanced note-taking' },
      { id: 'tag-wizard', name: 'Tag Wizard', icon: '🏷️', description: 'Auto-tag accuracy +50%' },
      {
        id: 'memory-palace',
        name: 'Memory Palace',
        icon: '🏛️',
        description: 'Perfect recall ability',
      },
      {
        id: 'pattern-seeker',
        name: 'Pattern Seeker',
        icon: '🔍',
        description: 'Find hidden connections',
      },
    ];

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = 150;

    skills.forEach((skill, i) => {
      const angle = (i / skills.length) * Math.PI * 2 - Math.PI / 2;
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;

      skillNodes.push({
        id: skill.id,
        name: skill.name,
        x,
        y,
        level: Math.floor(Math.random() * 3),
        maxLevel: 5,
        unlocked: i < 3 || Math.random() > 0.5,
        connections: i > 0 ? [skills[i - 1].id] : [],
        icon: skill.icon,
        description: skill.description,
      });
    });
  }

  function generateAchievements() {
    achievements = [
      {
        id: 'first-steps',
        name: 'First Steps',
        description: 'Captured your first item',
        icon: '👶',
        unlocked: true,
        timestamp: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      },
      {
        id: 'centurion',
        name: 'Centurion',
        description: 'Collected 100 items',
        icon: '💯',
        unlocked: true,
        timestamp: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000),
      },
      {
        id: 'tag-master',
        name: 'Tag Master',
        description: 'Used 50 unique tags',
        icon: '🏷️',
        unlocked: true,
        timestamp: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
      },
      {
        id: 'knowledge-seeker',
        name: 'Knowledge Seeker',
        description: 'Read for 100 hours total',
        icon: '🧠',
        unlocked: false,
        timestamp: new Date(),
      },
    ];
  }

  function animate() {
    time += 0.016;

    // Clear canvas
    ctx.fillStyle = 'rgba(10, 10, 10, 0.9)';
    ctx.fillRect(0, 0, width, height);

    // Draw background
    drawBackground();

    // Update particles
    updateParticles();

    // Draw skill tree connections
    drawSkillConnections();

    // Draw avatar
    drawAvatar();

    // Draw skill nodes
    drawSkillNodes();

    // Draw UI
    drawLevelBar();
    drawStats();
    drawAchievements();

    animationFrame = requestAnimationFrame(animate);
  }

  function drawBackground() {
    // Draw mystical background pattern
    ctx.strokeStyle = 'rgba(220, 20, 60, 0.05)';
    ctx.lineWidth = 1;

    // Hexagon grid
    const size = 30;
    for (let y = 0; y < height + size; y += size * 1.5) {
      for (let x = 0; x < width + size; x += size * 1.73) {
        const offset = (y / (size * 1.5)) % 2 === 0 ? 0 : size * 0.865;
        drawHexagon(x + offset, y, size);
      }
    }
  }

  function drawHexagon(x: number, y: number, size: number) {
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const angle = (i / 6) * Math.PI * 2;
      const px = x + Math.cos(angle) * size;
      const py = y + Math.sin(angle) * size;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.stroke();
  }

  function updateParticles() {
    // Add new particles
    if (Math.random() < 0.1) {
      const angle = Math.random() * Math.PI * 2;
      const distance = avatar.size + 20;
      particles.push({
        x: avatar.x + Math.cos(angle) * distance,
        y: avatar.y + Math.sin(angle) * distance,
        vx: (Math.random() - 0.5) * 2,
        vy: -Math.random() * 2 - 1,
        size: Math.random() * 3 + 2,
        color: avatar.auraColor,
        life: 1,
        type: 'aura',
      });
    }

    // Update existing particles
    particles = particles.filter((particle) => {
      particle.x += particle.vx;
      particle.y += particle.vy;
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

  function drawAvatar() {
    // Update aura
    auraRings.forEach((ring, i) => {
      ring.rotation += ring.speed;

      // Draw aura ring
      ctx.strokeStyle = ring.color;
      ctx.lineWidth = ring.thickness;
      ctx.globalAlpha = ring.opacity * (0.8 + Math.sin(time * 2 + i) * 0.2);

      ctx.beginPath();
      ctx.arc(avatar.x, avatar.y, ring.radius, 0, Math.PI * 2);
      ctx.stroke();

      // Draw energy lines
      const segments = 8;
      for (let j = 0; j < segments; j++) {
        const angle = ring.rotation + (j / segments) * Math.PI * 2;
        const x1 = avatar.x + Math.cos(angle) * (ring.radius - 10);
        const y1 = avatar.y + Math.sin(angle) * (ring.radius - 10);
        const x2 = avatar.x + Math.cos(angle) * (ring.radius + 10);
        const y2 = avatar.y + Math.sin(angle) * (ring.radius + 10);

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }
    });

    ctx.globalAlpha = 1;

    // Draw avatar body
    const gradient = ctx.createRadialGradient(
      avatar.x,
      avatar.y,
      0,
      avatar.x,
      avatar.y,
      avatar.size
    );
    gradient.addColorStop(0, avatar.color + 'ff');
    gradient.addColorStop(0.7, avatar.color + 'cc');
    gradient.addColorStop(1, avatar.color + '66');

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(avatar.x, avatar.y, avatar.size, 0, Math.PI * 2);
    ctx.fill();

    // Draw avatar symbol
    ctx.fillStyle = '#ffffff';
    ctx.font = `bold ${avatar.size * 0.8}px Space Grotesk`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('🧭', avatar.x, avatar.y);

    // Draw level indicator
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(avatar.x, avatar.y, avatar.size + 5, 0, Math.PI * 2);
    ctx.stroke();

    // Level text
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 16px Space Grotesk';
    ctx.fillText(`Lv ${$level}`, avatar.x, avatar.y + avatar.size + 25);
  }

  function drawSkillConnections() {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 2;

    skillNodes.forEach((node) => {
      node.connections.forEach((targetId) => {
        const target = skillNodes.find((n) => n.id === targetId);
        if (!target) return;

        ctx.beginPath();
        ctx.moveTo(node.x, node.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      });
    });
  }

  function drawSkillNodes() {
    skillNodes.forEach((node) => {
      const isHovered = selectedSkill === node;

      // Draw node background
      ctx.fillStyle = node.unlocked ? (node.level > 0 ? avatar.auraColor : '#333333') : '#1a1a1a';
      ctx.strokeStyle = isHovered ? '#ffffff' : node.unlocked ? avatar.auraColor : '#333333';
      ctx.lineWidth = isHovered ? 3 : 2;

      ctx.beginPath();
      ctx.arc(node.x, node.y, 30, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Draw icon
      ctx.fillStyle = node.unlocked ? '#ffffff' : '#666666';
      ctx.font = '24px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.icon, node.x, node.y);

      // Draw level dots
      const dotRadius = 3;
      const dotSpacing = 8;
      const startX = node.x - ((node.maxLevel - 1) * dotSpacing) / 2;

      for (let i = 0; i < node.maxLevel; i++) {
        ctx.fillStyle = i < node.level ? '#00ff64' : '#333333';
        ctx.beginPath();
        ctx.arc(startX + i * dotSpacing, node.y + 40, dotRadius, 0, Math.PI * 2);
        ctx.fill();
      }

      // Draw name on hover
      if (isHovered) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        ctx.fillRect(node.x - 60, node.y - 70, 120, 30);
        ctx.fillStyle = '#ffffff';
        ctx.font = '12px Space Grotesk';
        ctx.fillText(node.name, node.x, node.y - 55);
      }
    });
  }

  function drawLevelBar() {
    const barWidth = 300;
    const barHeight = 20;
    const x = (width - barWidth) / 2;
    const y = height - 100;

    // Background
    ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.fillRect(x, y, barWidth, barHeight);

    // Experience fill
    const expPercent = ($experience % 1000) / 1000;
    const gradient = ctx.createLinearGradient(x, y, x + barWidth, y);
    gradient.addColorStop(0, '#00ff64');
    gradient.addColorStop(1, '#4a9eff');

    ctx.fillStyle = gradient;
    ctx.fillRect(x, y, barWidth * expPercent, barHeight);

    // Border
    ctx.strokeStyle = avatar.auraColor;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, barWidth, barHeight);

    // Text
    ctx.fillStyle = '#ffffff';
    ctx.font = '14px Space Grotesk';
    ctx.textAlign = 'center';
    ctx.fillText(`${Math.floor($experience)} / 1000 XP`, x + barWidth / 2, y - 10);
  }

  function drawStats() {
    const stats = personalityData.stats;
    const x = 50;
    const y = 100;
    const spacing = 30;

    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(x - 10, y - 30, 200, Object.keys(stats).length * spacing + 40);

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 16px Space Grotesk';
    ctx.fillText('Character Stats', x, y - 10);

    Object.entries(stats).forEach(([key, value], i) => {
      const statY = y + 20 + i * spacing;
      const label = key.replace(/_/g, ' ').toUpperCase();

      // Label
      ctx.fillStyle = '#999999';
      ctx.font = '12px Space Grotesk';
      ctx.fillText(label, x, statY);

      // Bar background
      ctx.fillStyle = '#333333';
      ctx.fillRect(x, statY + 5, 150, 10);

      // Bar fill
      ctx.fillStyle = avatar.auraColor;
      ctx.fillRect(x, statY + 5, 150 * (value / 100), 10);

      // Value
      ctx.fillStyle = '#ffffff';
      ctx.fillText(value.toString(), x + 160, statY + 13);
    });
  }

  function drawAchievements() {
    const x = width - 250;
    const y = 100;
    const size = 40;
    const spacing = 50;

    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(x - 10, y - 30, 220, 250);

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 16px Space Grotesk';
    ctx.fillText('Achievements', x, y - 10);

    achievements.slice(0, 4).forEach((achievement, i) => {
      const achX = x + (i % 2) * (size + spacing);
      const achY = y + 20 + Math.floor(i / 2) * (size + spacing);

      // Background
      ctx.fillStyle = achievement.unlocked ? '#333333' : '#1a1a1a';
      ctx.fillRect(achX, achY, size, size);

      // Icon
      ctx.fillStyle = achievement.unlocked ? '#ffffff' : '#666666';
      ctx.font = '24px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(achievement.icon, achX + size / 2, achY + size / 2);

      // Border
      ctx.strokeStyle = achievement.unlocked ? '#00ff64' : '#333333';
      ctx.lineWidth = 2;
      ctx.strokeRect(achX, achY, size, size);
    });
  }

  function handleMouseMove(e: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Check hover on skill nodes
    let foundHover = false;
    skillNodes.forEach((node) => {
      const dx = mouseX - node.x;
      const dy = mouseY - node.y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < 30) {
        selectedSkill = node;
        foundHover = true;
      }
    });

    if (!foundHover) selectedSkill = null;
  }

  function handleClick(e: MouseEvent) {
    if (selectedSkill && selectedSkill.unlocked && selectedSkill.level < selectedSkill.maxLevel) {
      selectedSkill.level++;
      experience.update((exp) => exp + 100);
      getAudioManager().playSound('levelup', 0.5);

      // Check for level up
      if ($experience >= 1000) {
        level.update((l) => l + 1);
        experience.set(0);

        // Create celebration particles
        for (let i = 0; i < 20; i++) {
          const angle = (i / 20) * Math.PI * 2;
          particles.push({
            x: avatar.x,
            y: avatar.y,
            vx: Math.cos(angle) * 5,
            vy: Math.sin(angle) * 5,
            size: Math.random() * 5 + 3,
            color: '#00ff64',
            life: 1,
            type: 'levelup',
          });
        }
      }
    }
  }
</script>

<div class="avatar-container" bind:this={container}>
  <canvas bind:this={canvas}></canvas>

  <div class="personality-info">
    <h2>{personalityData.name}</h2>
    <p class="personality-type">{personalityData.type.toUpperCase()}</p>
    <div class="traits">
      {#each personalityData.traits as trait}
        <span class="trait">{trait}</span>
      {/each}
    </div>
    <div class="confidence">
      Confidence: {Math.round(personalityData.confidence * 100)}%
    </div>
  </div>

  <div class="level-display">
    <div class="level-number">Lv {$level}</div>
    <div class="level-title">Digital Explorer</div>
  </div>

  <div class="controls">
    <button on:click={() => experience.update((exp) => exp + 250)}> Gain Experience </button>
    <button
      on:click={() => {
        achievements[3].unlocked = true;
        getAudioManager().playSound('levelup', 0.7);
      }}
    >
      Unlock Achievement
    </button>
  </div>

  {#if selectedSkill}
    <div class="skill-tooltip">
      <h3>{selectedSkill.name}</h3>
      <p>{selectedSkill.description}</p>
      <p>Level: {selectedSkill.level}/{selectedSkill.maxLevel}</p>
      {#if selectedSkill.unlocked && selectedSkill.level < selectedSkill.maxLevel}
        <p class="upgrade-hint">Click to upgrade!</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .avatar-container {
    position: relative;
    width: 100%;
    height: 100vh;
    background: #0a0a0a;
    overflow: hidden;
  }

  canvas {
    width: 100%;
    height: 100%;
    cursor: pointer;
  }

  .personality-info {
    position: absolute;
    top: 20px;
    left: 20px;
    background: rgba(0, 0, 0, 0.8);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #dc143c;
    color: white;
    font-family: 'Space Grotesk';
    backdrop-filter: blur(10px);
  }

  .personality-info h2 {
    margin: 0 0 5px 0;
    color: #dc143c;
    font-size: 24px;
  }

  .personality-type {
    margin: 0 0 15px 0;
    color: #999;
    font-size: 14px;
    letter-spacing: 2px;
  }

  .traits {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 15px;
  }

  .trait {
    background: #dc143c;
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
  }

  .confidence {
    color: #00ff64;
    font-size: 14px;
    font-weight: 600;
  }

  .level-display {
    position: absolute;
    top: 20px;
    right: 20px;
    text-align: center;
    color: white;
    font-family: 'Space Grotesk';
  }

  .level-number {
    font-size: 48px;
    font-weight: 800;
    color: #00ff64;
    text-shadow: 0 0 20px rgba(0, 255, 100, 0.5);
  }

  .level-title {
    font-size: 16px;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 2px;
  }

  .controls {
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 20px;
  }

  .controls button {
    background: #dc143c;
    border: none;
    color: white;
    padding: 15px 30px;
    border-radius: 10px;
    font-family: 'Space Grotesk';
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .controls button:hover {
    background: #b91c3c;
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(220, 20, 60, 0.5);
  }

  .skill-tooltip {
    position: absolute;
    bottom: 150px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.9);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #00ff64;
    color: white;
    font-family: 'Space Grotesk';
    text-align: center;
    backdrop-filter: blur(10px);
  }

  .skill-tooltip h3 {
    margin: 0 0 10px 0;
    color: #00ff64;
  }

  .skill-tooltip p {
    margin: 5px 0;
    color: #ccc;
    font-size: 14px;
  }

  .upgrade-hint {
    color: #00ff64 !important;
    font-weight: 600;
    animation: pulse 1s ease-in-out infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
</style>
