<script lang="ts">
  import { onMount } from 'svelte';
  import { spring, tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import Icon from '$lib/components/Icon.svelte';
  
  export let variant: 'primary' | 'secondary' | 'ghost' = 'primary';
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let icon: string | null = null;
  export let loading = false;
  export let disabled = false;
  
  let button: HTMLButtonElement;
  let mouseX = spring(0);
  let mouseY = spring(0);
  let isHovering = false;
  let isPressed = false;
  
  // Animation values
  const shimmer = tweened(0, { duration: 2000 });
  const pulse = spring(1, { stiffness: 300, damping: 15 });
  const tilt = spring({ x: 0, y: 0 }, { stiffness: 200, damping: 20 });
  
  // Liquid morphing effect
  let morphPath = spring(
    'M 0,50 Q 25,50 50,50 T 100,50 L 100,100 L 0,100 Z',
    { stiffness: 100, damping: 15 }
  );
  
  function handleMouseMove(e: MouseEvent) {
    if (!button || disabled) return;
    
    const rect = button.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    
    mouseX.set(x);
    mouseY.set(y);
    
    // Tilt effect
    const tiltX = ((y - 50) / 50) * 10;
    const tiltY = ((x - 50) / 50) * -10;
    tilt.set({ x: tiltX, y: tiltY });
    
    // Morph liquid shape
    if (isHovering) {
      const curve = 50 + Math.sin((x / 100) * Math.PI) * 20;
      morphPath.set(`M 0,${curve} Q 25,${50 + (curve - 50) * 0.5} 50,50 T 100,${100 - curve} L 100,100 L 0,100 Z`);
    }
  }
  
  function handleMouseEnter() {
    if (disabled) return;
    isHovering = true;
    pulse.set(1.05);
    shimmer.set(1);
  }
  
  function handleMouseLeave() {
    isHovering = false;
    pulse.set(1);
    tilt.set({ x: 0, y: 0 });
    morphPath.set('M 0,50 Q 25,50 50,50 T 100,50 L 100,100 L 0,100 Z');
    shimmer.set(0);
  }
  
  function handleMouseDown() {
    if (disabled) return;
    isPressed = true;
    pulse.set(0.95);
  }
  
  function handleMouseUp() {
    isPressed = false;
    pulse.set(1.05);
    setTimeout(() => pulse.set(1), 100);
  }
  
  // Continuous shimmer animation
  onMount(() => {
    if (!disabled) {
      const interval = setInterval(() => {
        if (!isHovering) {
          shimmer.set(1);
          setTimeout(() => shimmer.set(0), 2000);
        }
      }, 4000);
      
      return () => clearInterval(interval);
    }
  });
</script>

<button
  bind:this={button}
  class="animated-button {variant} {size}"
  class:loading
  class:disabled
  {disabled}
  on:mousemove={handleMouseMove}
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  on:mousedown={handleMouseDown}
  on:mouseup={handleMouseUp}
  on:click
  style="
    transform: 
      perspective(1000px)
      rotateX({$tilt.x}deg)
      rotateY({$tilt.y}deg)
      scale({$pulse});
  "
>
  <!-- Liquid background -->
  <svg class="liquid-bg" viewBox="0 0 100 100" preserveAspectRatio="none">
    <defs>
      <linearGradient id="liquidGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:currentColor;stop-opacity:0.2" />
        <stop offset="50%" style="stop-color:currentColor;stop-opacity:0.3" />
        <stop offset="100%" style="stop-color:currentColor;stop-opacity:0.2" />
      </linearGradient>
    </defs>
    <path d={$morphPath} fill="url(#liquidGradient)" />
  </svg>
  
  <!-- Shimmer effect -->
  <div 
    class="shimmer"
    style="
      background: linear-gradient(
        105deg,
        transparent 40%,
        rgba(255, 255, 255, 0.3) 50%,
        transparent 60%
      );
      transform: translateX({-100 + $shimmer * 200}%);
    "
  />
  
  <!-- Glow effect -->
  <div 
    class="glow"
    style="
      left: {$mouseX}%;
      top: {$mouseY}%;
      opacity: {isHovering ? 0.6 : 0};
    "
  />
  
  <!-- Content -->
  <span class="button-content">
    {#if loading}
      <span class="loader">
        <span class="loader-dot" style="animation-delay: 0s" />
        <span class="loader-dot" style="animation-delay: 0.2s" />
        <span class="loader-dot" style="animation-delay: 0.4s" />
      </span>
    {:else}
      {#if icon}
        <Icon name={icon} size={size === 'small' ? 16 : size === 'large' ? 24 : 20} />
      {/if}
      <slot />
    {/if}
  </span>
  
  <!-- Ripple container -->
  <span class="ripple-container" />
</button>

<style>
  .animated-button {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-weight: 500;
    border-radius: 0.75rem;
    transition: all 0.2s ease;
    transform-style: preserve-3d;
    overflow: hidden;
    cursor: pointer;
    border: none;
    outline: none;
  }
  
  /* Size variants */
  .small {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
  
  .medium {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
  }
  
  .large {
    padding: 1rem 2rem;
    font-size: 1.125rem;
  }
  
  /* Color variants */
  .primary {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    box-shadow: 
      0 4px 15px rgba(99, 102, 241, 0.3),
      inset 0 1px 2px rgba(255, 255, 255, 0.2);
  }
  
  .primary:hover:not(.disabled) {
    box-shadow: 
      0 8px 25px rgba(99, 102, 241, 0.4),
      inset 0 1px 2px rgba(255, 255, 255, 0.3);
  }
  
  .secondary {
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
  }
  
  .secondary:hover:not(.disabled) {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.3);
  }
  
  .ghost {
    background: transparent;
    color: currentColor;
  }
  
  .ghost:hover:not(.disabled) {
    background: rgba(255, 255, 255, 0.05);
  }
  
  /* States */
  .disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .loading {
    cursor: wait;
  }
  
  /* Liquid background */
  .liquid-bg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }
  
  /* Shimmer */
  .shimmer {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }
  
  /* Glow */
  .glow {
    position: absolute;
    width: 100px;
    height: 100px;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.4), transparent);
    transform: translate(-50%, -50%);
    pointer-events: none;
    transition: opacity 0.3s ease;
  }
  
  /* Content */
  .button-content {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  /* Loader */
  .loader {
    display: flex;
    gap: 0.25rem;
  }
  
  .loader-dot {
    width: 6px;
    height: 6px;
    background: currentColor;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
  }
  
  @keyframes bounce {
    0%, 80%, 100% {
      transform: scale(0);
    }
    40% {
      transform: scale(1);
    }
  }
  
  /* Ripple container for click effects */
  .ripple-container {
    position: absolute;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
  }
</style>