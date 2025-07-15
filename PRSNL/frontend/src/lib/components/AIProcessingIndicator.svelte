<script>
  import { onMount, onDestroy } from 'svelte';
  import { tweened } from 'svelte/motion';
  import { cubicInOut } from 'svelte/easing';

  export let progress = 0; // Real progress from 0-1
  export let currentStage = 'analyzing'; // Current processing stage
  export let processingStartTime = null; // When processing started
  export let estimatedTimeMs = 45000; // Fallback estimate

  // Smooth progress animation for visual appeal
  const animatedProgress = tweened(0, {
    duration: 800,
    easing: cubicInOut,
  });

  // Update animated progress when real progress changes
  $: animatedProgress.set(progress);

  // Floating particles state
  let particles = [];
  let particleContainer;
  let animationId;

  // Processing stages with different visual themes
  const stages = {
    analyzing: {
      name: 'Analyzing Conversation',
      description: 'Reading through your messages...',
      color: '#4F9EFF',
      icon: '🔍',
    },
    extracting: {
      name: 'Extracting Insights',
      description: 'Running specialized AI agents...',
      color: '#8C52FF',
      icon: '🧠',
    },
    synthesizing: {
      name: 'Synthesizing Knowledge',
      description: 'Connecting ideas and generating insights...',
      color: '#FF6B9D',
      icon: '⚡',
    },
    finalizing: {
      name: 'Finalizing Results',
      description: 'Preparing your personalized analysis...',
      color: '#00D9FF',
      icon: '✨',
    },
    processing: {
      name: 'Processing Intelligence',
      description: 'Multi-agent analysis in progress...',
      color: '#8C52FF',
      icon: '🤖',
    },
  };

  // Get active stage based on current stage prop
  $: activeStage = stages[currentStage] || stages['analyzing'];

  // Calculate elapsed time and estimated remaining time
  $: elapsedTime = processingStartTime ? Date.now() - processingStartTime : 0;

  // Smart time estimation based on actual progress and elapsed time
  $: estimatedRemaining = (() => {
    if (progress >= 1) return 0;
    if (progress <= 0 || !processingStartTime) return Math.round(estimatedTimeMs / 1000);

    // Calculate estimated total time based on actual progress
    const timePerProgress = elapsedTime / progress;
    const estimatedTotal = timePerProgress;
    const remaining = Math.max(0, estimatedTotal - elapsedTime);

    // Add some buffer for final stages (they sometimes take longer)
    const bufferMultiplier = progress > 0.8 ? 1.2 : 1.0;

    return Math.round((remaining * bufferMultiplier) / 1000);
  })();

  // Interactive particle system
  function createParticle(x, y) {
    return {
      id: Math.random(),
      x: x || Math.random() * 400,
      y: y || Math.random() * 200,
      vx: (Math.random() - 0.5) * 2,
      vy: (Math.random() - 0.5) * 2,
      size: Math.random() * 4 + 2,
      life: 1,
      decay: Math.random() * 0.02 + 0.01,
      color: activeStage.color,
      interactive: !!x && !!y, // User-created particles
    };
  }

  function updateParticles() {
    particles = particles
      .map((p) => ({
        ...p,
        x: p.x + p.vx,
        y: p.y + p.vy,
        life: Math.max(0, p.life - p.decay),
        vx: p.vx * 0.995,
        vy: p.vy * 0.995,
      }))
      .filter((p) => p.life > 0);

    // Add new ambient particles
    if (particles.length < 15 && Math.random() < 0.3) {
      particles.push(createParticle());
    }
  }

  function animateParticles() {
    updateParticles();
    particles = particles; // Trigger reactivity
    animationId = requestAnimationFrame(animateParticles);
  }

  function handleParticleClick(event) {
    if (!particleContainer) return;

    const rect = particleContainer.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Create burst of particles at click location
    for (let i = 0; i < 8; i++) {
      particles.push(
        createParticle(x + (Math.random() - 0.5) * 20, y + (Math.random() - 0.5) * 20)
      );
    }
  }

  onMount(() => {
    // Initialize particles
    for (let i = 0; i < 10; i++) {
      particles.push(createParticle());
    }

    // Start particle animation
    animateParticles();

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  });

  onDestroy(() => {
    if (animationId) {
      cancelAnimationFrame(animationId);
    }
  });
</script>

<div class="ai-processing-container">
  <!-- Animated Background Layers -->
  <div class="background-layers">
    <div class="wave-layer layer-1" style="--stage-color: {activeStage.color}"></div>
    <div class="wave-layer layer-2" style="--stage-color: {activeStage.color}"></div>
    <div class="gradient-orb" style="--stage-color: {activeStage.color}"></div>
  </div>

  <!-- Interactive Particle System -->
  <div
    class="particle-container"
    bind:this={particleContainer}
    on:click={handleParticleClick}
    role="button"
    tabindex="0"
    aria-label="Click to create particles"
  >
    {#each particles as particle (particle.id)}
      <div
        class="particle"
        style="
          left: {particle.x}px;
          top: {particle.y}px;
          width: {particle.size}px;
          height: {particle.size}px;
          background: {particle.color};
          opacity: {particle.life};
          transform: scale({particle.interactive ? particle.life * 2 : 1});
        "
      ></div>
    {/each}
  </div>

  <!-- Main Content -->
  <div class="content-layer">
    <!-- Stage Indicator -->
    <div class="stage-header">
      <div class="stage-icon" style="--stage-color: {activeStage.color}">
        {activeStage.icon}
      </div>
      <div class="stage-info">
        <h3 class="stage-title">{activeStage.name}</h3>
        <p class="stage-description">{activeStage.description}</p>
      </div>
    </div>

    <!-- Advanced Progress Bar -->
    <div class="progress-container">
      <div class="progress-track">
        <div
          class="progress-fill"
          style="
            width: {$animatedProgress * 100}%;
            background: linear-gradient(90deg, {activeStage.color}, {activeStage.color}aa);
            box-shadow: 0 0 20px {activeStage.color}66;
          "
        ></div>

        <!-- Stage Markers (simplified for real-time progress) -->
        <div class="stage-markers">
          <div class="stage-marker {progress >= 0.25 ? 'active' : ''}" style="left: 25%">
            <div class="marker-dot" style="--marker-color: #4F9EFF"></div>
            <div class="marker-label">🔍</div>
          </div>
          <div class="stage-marker {progress >= 0.5 ? 'active' : ''}" style="left: 50%">
            <div class="marker-dot" style="--marker-color: #8C52FF"></div>
            <div class="marker-label">🧠</div>
          </div>
          <div class="stage-marker {progress >= 0.75 ? 'active' : ''}" style="left: 75%">
            <div class="marker-dot" style="--marker-color: #FF6B9D"></div>
            <div class="marker-label">⚡</div>
          </div>
          <div class="stage-marker {progress >= 1 ? 'active' : ''}" style="left: 100%">
            <div class="marker-dot" style="--marker-color: #00D9FF"></div>
            <div class="marker-label">✨</div>
          </div>
        </div>
      </div>

      <!-- Progress Percentage -->
      <div class="progress-text">
        <span class="percentage">{Math.round($animatedProgress * 100)}%</span>
        <span class="time-estimate">
          {estimatedRemaining}s remaining
        </span>
      </div>
    </div>

    <!-- Interactive Elements -->
    <div class="interactive-hints">
      <div class="hint-bubble">
        <span class="hint-icon">💫</span>
        <span>Click anywhere to create magic particles!</span>
      </div>

      <div class="processing-facts">
        <div class="fact-item">
          <span class="fact-icon">🤖</span>
          <span>4 AI agents working in parallel</span>
        </div>
        <div class="fact-item">
          <span class="fact-icon">🔬</span>
          <span>Progress: {Math.round($animatedProgress * 100)}% complete</span>
        </div>
        <div class="fact-item">
          <span class="fact-icon">🧬</span>
          <span>{activeStage.description}</span>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .ai-processing-container {
    position: relative;
    background: linear-gradient(135deg, #0a0e1a 0%, #1a1f35 50%, #0f1419 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 2rem;
    min-height: 400px;
    overflow: hidden;
    cursor: pointer;
  }

  /* Background Animation Layers */
  .background-layers {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    z-index: 1;
  }

  .wave-layer {
    position: absolute;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, var(--stage-color) 22 0%, transparent 70%);
    border-radius: 45%;
    animation: wave-rotate 20s linear infinite;
  }

  .layer-1 {
    top: -50%;
    left: -50%;
    animation-duration: 25s;
    animation-direction: normal;
  }

  .layer-2 {
    top: -75%;
    left: -75%;
    animation-duration: 35s;
    animation-direction: reverse;
    opacity: 0.5;
  }

  .gradient-orb {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 300px;
    height: 300px;
    margin-left: -150px;
    margin-top: -150px;
    background: radial-gradient(circle, var(--stage-color) 33 0%, transparent 60%);
    border-radius: 50%;
    animation: pulse 4s ease-in-out infinite;
  }

  @keyframes wave-rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  @keyframes pulse {
    0%,
    100% {
      transform: scale(0.8);
      opacity: 0.6;
    }
    50% {
      transform: scale(1.2);
      opacity: 0.3;
    }
  }

  /* Particle System */
  .particle-container {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: all;
    z-index: 2;
  }

  .particle {
    position: absolute;
    border-radius: 50%;
    pointer-events: none;
    transition: transform 0.1s ease;
    filter: blur(0.5px);
    box-shadow: 0 0 10px currentColor;
  }

  /* Content Layer */
  .content-layer {
    position: relative;
    z-index: 3;
    display: flex;
    flex-direction: column;
    gap: 2rem;
    height: 100%;
  }

  /* Stage Header */
  .stage-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .stage-icon {
    width: 3rem;
    height: 3rem;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--stage-color), var(--stage-color) 88);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    box-shadow: 0 0 20px var(--stage-color) 66;
    animation: icon-pulse 2s ease-in-out infinite;
  }

  @keyframes icon-pulse {
    0%,
    100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.1);
    }
  }

  .stage-info {
    flex: 1;
  }

  .stage-title {
    margin: 0 0 0.25rem 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .stage-description {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  /* Progress Bar */
  .progress-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .progress-track {
    position: relative;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    border-radius: 4px;
    transition:
      width 0.3s ease,
      background 0.5s ease;
    position: relative;
  }

  .progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    animation: shimmer 2s ease-in-out infinite;
  }

  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  /* Stage Markers */
  .stage-markers {
    position: absolute;
    top: -8px;
    left: 0;
    right: 0;
    height: 24px;
  }

  .stage-marker {
    position: absolute;
    top: 0;
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }

  .marker-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    border: 2px solid rgba(255, 255, 255, 0.5);
    transition: all 0.3s ease;
  }

  .stage-marker.active .marker-dot {
    background: var(--marker-color);
    border-color: var(--marker-color);
    box-shadow: 0 0 10px var(--marker-color);
    transform: scale(1.2);
  }

  .marker-label {
    font-size: 0.75rem;
    margin-top: 4px;
    opacity: 0.7;
  }

  .stage-marker.active .marker-label {
    opacity: 1;
    transform: scale(1.1);
  }

  /* Progress Text */
  .progress-text {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
  }

  .percentage {
    font-weight: 600;
    font-size: 1.1rem;
    color: var(--text-primary);
  }

  .time-estimate {
    color: var(--text-secondary);
  }

  /* Interactive Elements */
  .interactive-hints {
    margin-top: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .hint-bubble {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 2rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
    animation: hint-glow 3s ease-in-out infinite;
  }

  @keyframes hint-glow {
    0%,
    100% {
      box-shadow: 0 0 0 rgba(255, 255, 255, 0);
    }
    50% {
      box-shadow: 0 0 20px rgba(255, 255, 255, 0.1);
    }
  }

  .hint-icon {
    animation: bounce 2s ease-in-out infinite;
  }

  @keyframes bounce {
    0%,
    100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-4px);
    }
  }

  .processing-facts {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .fact-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
    opacity: 0.8;
  }

  .fact-icon {
    font-size: 1rem;
  }

  /* Responsive */
  @media (max-width: 640px) {
    .ai-processing-container {
      padding: 1.5rem;
      min-height: 350px;
    }

    .stage-header {
      flex-direction: column;
      text-align: center;
      gap: 0.75rem;
    }

    .processing-facts {
      gap: 0.25rem;
    }

    .fact-item {
      font-size: 0.8rem;
    }
  }
</style>
