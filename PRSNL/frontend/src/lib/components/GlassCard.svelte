<script lang="ts">
  import { spring } from 'svelte/motion';
  import { onMount } from 'svelte';
  
  export let variant: 'default' | 'elevated' | 'gradient' = 'default';
  export let interactive = true;
  export let glowColor = '#6366f1';
  
  let card: HTMLElement;
  let mouseX = spring(50, { stiffness: 50, damping: 20 });
  let mouseY = spring(50, { stiffness: 50, damping: 20 });
  let rotateX = spring(0, { stiffness: 50, damping: 20 });
  let rotateY = spring(0, { stiffness: 50, damping: 20 });
  let isHovering = false;
  
  // Holographic effect coordinates
  let holoX = 0;
  let holoY = 0;
  
  function handleMouseMove(e: MouseEvent) {
    if (!card || !interactive) return;
    
    const rect = card.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    
    mouseX.set(x);
    mouseY.set(y);
    
    // 3D rotation based on mouse position
    const rotX = ((y - 50) / 50) * -15;
    const rotY = ((x - 50) / 50) * 15;
    
    rotateX.set(rotX);
    rotateY.set(rotY);
    
    // Update holographic effect
    holoX = x;
    holoY = y;
  }
  
  function handleMouseEnter() {
    if (!interactive) return;
    isHovering = true;
  }
  
  function handleMouseLeave() {
    if (!interactive) return;
    isHovering = false;
    mouseX.set(50);
    mouseY.set(50);
    rotateX.set(0);
    rotateY.set(0);
  }
  
  // Animated gradient background
  let gradientAngle = spring(0);
  
  onMount(() => {
    const interval = setInterval(() => {
      gradientAngle.update(a => a + 1);
    }, 50);
    
    return () => clearInterval(interval);
  });
</script>

<div
  bind:this={card}
  class="glass-card {variant}"
  class:interactive
  class:hovering={isHovering}
  on:mousemove={handleMouseMove}
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  style="
    --mouse-x: {$mouseX}%;
    --mouse-y: {$mouseY}%;
    --rotate-x: {$rotateX}deg;
    --rotate-y: {$rotateY}deg;
    --glow-color: {glowColor};
    transform: perspective(1000px) rotateX(var(--rotate-x)) rotateY(var(--rotate-y));
  "
>
  <!-- Animated gradient background -->
  {#if variant === 'gradient'}
    <div 
      class="gradient-bg"
      style="
        background: linear-gradient(
          {$gradientAngle}deg,
          rgba(99, 102, 241, 0.1),
          rgba(139, 92, 246, 0.1),
          rgba(236, 72, 153, 0.1),
          rgba(99, 102, 241, 0.1)
        );
      "
    />
  {/if}
  
  <!-- Glass effect layers -->
  <div class="glass-layer" />
  <div class="frost-layer" />
  
  <!-- Holographic effect -->
  {#if interactive && isHovering}
    <div 
      class="holographic"
      style="
        background: radial-gradient(
          circle at {holoX}% {holoY}%,
          rgba(255, 255, 255, 0.3) 0%,
          transparent 50%
        );
      "
    />
  {/if}
  
  <!-- Glow effect -->
  <div 
    class="glow"
    style="
      opacity: {isHovering ? 0.8 : 0.4};
      background: radial-gradient(
        circle at var(--mouse-x) var(--mouse-y),
        var(--glow-color) 0%,
        transparent 70%
      );
    "
  />
  
  <!-- Border gradient -->
  <div class="border-gradient" />
  
  <!-- Content -->
  <div class="card-content">
    <slot />
  </div>
  
  <!-- Reflection -->
  {#if variant === 'elevated'}
    <div class="reflection" />
  {/if}
</div>

<style>
  .glass-card {
    position: relative;
    border-radius: 1.5rem;
    overflow: hidden;
    transition: transform 0.2s ease;
    transform-style: preserve-3d;
  }
  
  .interactive {
    cursor: pointer;
  }
  
  /* Variants */
  .default {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .elevated {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 
      0 8px 32px rgba(0, 0, 0, 0.3),
      0 2px 8px rgba(0, 0, 0, 0.2);
  }
  
  .gradient {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  /* Layers */
  .glass-layer {
    position: absolute;
    inset: 0;
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.1) 0%,
      rgba(255, 255, 255, 0.05) 50%,
      rgba(255, 255, 255, 0.02) 100%
    );
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }
  
  .frost-layer {
    position: absolute;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.02'/%3E%3C/svg%3E");
    mix-blend-mode: overlay;
  }
  
  .gradient-bg {
    position: absolute;
    inset: -50%;
    opacity: 0.3;
    animation: rotate 20s linear infinite;
  }
  
  @keyframes rotate {
    to {
      transform: rotate(360deg);
    }
  }
  
  /* Effects */
  .holographic {
    position: absolute;
    inset: 0;
    pointer-events: none;
    mix-blend-mode: overlay;
  }
  
  .glow {
    position: absolute;
    inset: -50%;
    pointer-events: none;
    filter: blur(60px);
    transition: opacity 0.3s ease;
  }
  
  .border-gradient {
    position: absolute;
    inset: 0;
    border-radius: inherit;
    padding: 1px;
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.2),
      rgba(255, 255, 255, 0.05)
    );
    -webkit-mask: 
      linear-gradient(#fff 0 0) content-box, 
      linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    opacity: 0.5;
    transition: opacity 0.3s ease;
  }
  
  .hovering .border-gradient {
    opacity: 0.8;
  }
  
  /* Content */
  .card-content {
    position: relative;
    z-index: 1;
    padding: 1.5rem;
  }
  
  /* Reflection for elevated variant */
  .reflection {
    position: absolute;
    bottom: -30%;
    left: 5%;
    right: 5%;
    height: 30%;
    background: inherit;
    border-radius: inherit;
    opacity: 0.2;
    filter: blur(10px);
    transform: scaleY(-1) translateZ(-10px);
  }
  
  /* Hover state */
  .interactive.hovering {
    transform: 
      perspective(1000px) 
      rotateX(var(--rotate-x)) 
      rotateY(var(--rotate-y))
      translateZ(10px);
  }
  
  .elevated.hovering {
    box-shadow: 
      0 12px 48px rgba(0, 0, 0, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.3);
  }
</style>