<script lang="ts">
  import { onMount } from 'svelte';
  import { spring, tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';

  export let variant: 'hover' | 'click' | 'focus' = 'hover';
  export let intensity: 'subtle' | 'medium' | 'strong' = 'medium';

  let element: HTMLElement;
  let isInteracting = false;

  // Motion values
  const scale = spring(1, { stiffness: 300, damping: 20 });
  const rotate = spring(0, { stiffness: 200, damping: 15 });
  const glow = tweened(0, { duration: 300, easing: cubicOut });
  const rippleScale = tweened(0, { duration: 600 });
  const magnetX = spring(0, { stiffness: 150, damping: 15 });
  const magnetY = spring(0, { stiffness: 150, damping: 15 });

  // Particle system
  let particles: Array<{ id: number; x: number; y: number; vx: number; vy: number; life: number }> =
    [];
  let particleId = 0;

  const intensityConfig = {
    subtle: { scale: 1.02, rotate: 1, glow: 0.3, particles: 2 },
    medium: { scale: 1.05, rotate: 3, glow: 0.5, particles: 5 },
    strong: { scale: 1.08, rotate: 5, glow: 0.8, particles: 10 },
  };

  function handleMouseEnter() {
    if (variant !== 'hover') return;
    isInteracting = true;
    const config = intensityConfig[intensity];
    scale.set(config.scale);
    rotate.set(config.rotate);
    glow.set(config.glow);
  }

  function handleMouseLeave() {
    if (variant !== 'hover') return;
    isInteracting = false;
    scale.set(1);
    rotate.set(0);
    glow.set(0);
    magnetX.set(0);
    magnetY.set(0);
  }

  function handleMouseMove(e: MouseEvent) {
    if (!isInteracting || variant !== 'hover') return;

    const rect = element.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;

    // Magnetic effect
    magnetX.set(x * 0.1);
    magnetY.set(y * 0.1);

    // Create particles
    const config = intensityConfig[intensity];
    for (let i = 0; i < config.particles; i++) {
      particles = [
        ...particles,
        {
          id: particleId++,
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
          vx: (Math.random() - 0.5) * 2,
          vy: (Math.random() - 0.5) * 2,
          life: 1,
        },
      ];
    }
  }

  function handleClick(e: MouseEvent) {
    if (variant !== 'click') return;

    const rect = element.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Ripple effect
    rippleScale.set(0);
    rippleScale.set(2);

    // Burst particles
    const config = intensityConfig[intensity];
    for (let i = 0; i < config.particles * 3; i++) {
      const angle = (Math.PI * 2 * i) / (config.particles * 3);
      particles = [
        ...particles,
        {
          id: particleId++,
          x,
          y,
          vx: Math.cos(angle) * 3,
          vy: Math.sin(angle) * 3,
          life: 1,
        },
      ];
    }

    // Scale bounce
    scale.set(0.95);
    setTimeout(() => scale.set(1.05), 100);
    setTimeout(() => scale.set(1), 200);
  }

  function handleFocus() {
    if (variant !== 'focus') return;
    const config = intensityConfig[intensity];
    scale.set(config.scale);
    glow.set(config.glow);
  }

  function handleBlur() {
    if (variant !== 'focus') return;
    scale.set(1);
    glow.set(0);
  }

  // Animate particles
  function animateParticles() {
    particles = particles
      .map((p) => ({
        ...p,
        x: p.x + p.vx,
        y: p.y + p.vy,
        vy: p.vy + 0.1, // gravity
        life: p.life - 0.02,
      }))
      .filter((p) => p.life > 0);

    requestAnimationFrame(animateParticles);
  }

  onMount(() => {
    animateParticles();
  });
</script>

<div
  bind:this={element}
  class="premium-interaction"
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  on:mousemove={handleMouseMove}
  on:click={handleClick}
  on:focus={handleFocus}
  on:blur={handleBlur}
  style="
    transform: scale({$scale}) rotate({$rotate}deg) translate({$magnetX}px, {$magnetY}px);
    filter: drop-shadow(0 0 {$glow * 20}px currentColor);
  "
>
  <slot />

  <!-- Particle layer -->
  <div class="particle-layer">
    {#each particles as particle (particle.id)}
      <div
        class="particle"
        style="
          left: {particle.x}px;
          top: {particle.y}px;
          opacity: {particle.life};
          transform: scale({particle.life});
        "
      />
    {/each}
  </div>

  <!-- Ripple effect -->
  {#if variant === 'click'}
    <div
      class="ripple"
      style="
        transform: scale({$rippleScale});
        opacity: {1 - $rippleScale / 2};
      "
    />
  {/if}
</div>

<style>
  .premium-interaction {
    position: relative;
    display: inline-block;
    transition: filter 0.3s ease;
    cursor: pointer;
  }

  .particle-layer {
    position: absolute;
    inset: 0;
    pointer-events: none;
    overflow: visible;
  }

  .particle {
    position: absolute;
    width: 4px;
    height: 4px;
    background: radial-gradient(circle, currentColor, transparent);
    border-radius: 50%;
    pointer-events: none;
  }

  .ripple {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle, currentColor, transparent);
    border-radius: 50%;
    transform-origin: center;
    pointer-events: none;
  }
</style>
