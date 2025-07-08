<script lang="ts">
  import { spring } from 'svelte/motion';
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  
  export let type: 'success' | 'error' | 'warning' | 'info' = 'info';
  export let message: string;
  export let duration = 4000;
  export let onClose: () => void;
  
  let visible = false;
  let progress = 100;
  
  const slideY = spring(50, { stiffness: 200, damping: 20 });
  const scale = spring(0.8, { stiffness: 300, damping: 20 });
  const rotation = spring(-5, { stiffness: 100, damping: 10 });
  
  const icons = {
    success: 'check-circle',
    error: 'x-circle',
    warning: 'alert-triangle',
    info: 'info'
  };
  
  const colors = {
    success: '#10b981',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#6366f1'
  };
  
  onMount(() => {
    // Entry animation
    visible = true;
    slideY.set(0);
    scale.set(1);
    rotation.set(0);
    
    // Progress animation
    const progressInterval = setInterval(() => {
      progress -= 100 / (duration / 100);
      if (progress <= 0) {
        clearInterval(progressInterval);
        handleClose();
      }
    }, 100);
    
    return () => clearInterval(progressInterval);
  });
  
  function handleClose() {
    // Exit animation
    slideY.set(50);
    scale.set(0.8);
    rotation.set(5);
    
    setTimeout(() => {
      visible = false;
      onClose();
    }, 200);
  }
  
  // Particle effect
  let particles: Array<{id: number, x: number, y: number}> = [];
  
  $: if (visible && type === 'success') {
    // Create celebration particles
    particles = Array(10).fill(null).map((_, i) => ({
      id: i,
      x: Math.random() * 100 - 50,
      y: Math.random() * 100 - 50
    }));
  }
</script>

{#if visible}
  <div 
    class="toast {type}"
    style="
      transform: 
        translateY({$slideY}px)
        scale({$scale})
        rotate({$rotation}deg);
      --toast-color: {colors[type]};
    "
  >
    <!-- Background effects -->
    <div class="toast-glow" />
    <div class="toast-shine" />
    
    <!-- Icon with animation -->
    <div class="icon-container">
      <div class="icon-bg" />
      <Icon name={icons[type]} size={24} />
      
      <!-- Success checkmark animation -->
      {#if type === 'success'}
        <svg class="checkmark" viewBox="0 0 24 24">
          <path
            d="M20 6L9 17l-5-5"
            fill="none"
            stroke="currentColor"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      {/if}
    </div>
    
    <!-- Message -->
    <p class="message">{message}</p>
    
    <!-- Close button -->
    <button class="close-btn" on:click={handleClose}>
      <Icon name="x" size={18} />
    </button>
    
    <!-- Progress bar -->
    <div class="progress-bar">
      <div 
        class="progress-fill"
        style="width: {progress}%"
      />
    </div>
    
    <!-- Particles for success -->
    {#if type === 'success'}
      <div class="particles">
        {#each particles as particle}
          <span 
            class="particle"
            style="
              left: {particle.x}px;
              top: {particle.y}px;
              animation-delay: {particle.id * 0.1}s;
            "
          />
        {/each}
      </div>
    {/if}
  </div>
{/if}

<style>
  .toast {
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: rgba(26, 26, 26, 0.95);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 1rem 1.5rem 1rem 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    min-width: 300px;
    max-width: 500px;
    box-shadow: 
      0 10px 40px rgba(0, 0, 0, 0.4),
      0 2px 10px rgba(0, 0, 0, 0.2);
    overflow: hidden;
    z-index: 1000;
  }
  
  /* Type-specific styling */
  .success {
    border-color: rgba(16, 185, 129, 0.3);
  }
  
  .error {
    border-color: rgba(239, 68, 68, 0.3);
  }
  
  .warning {
    border-color: rgba(245, 158, 11, 0.3);
  }
  
  .info {
    border-color: rgba(99, 102, 241, 0.3);
  }
  
  /* Background effects */
  .toast-glow {
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, var(--toast-color) 0%, transparent 70%);
    opacity: 0.1;
    filter: blur(40px);
    pointer-events: none;
  }
  
  .toast-shine {
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.1),
      transparent
    );
    animation: shine 2s ease-in-out;
    pointer-events: none;
  }
  
  @keyframes shine {
    to {
      left: 100%;
    }
  }
  
  /* Icon */
  .icon-container {
    position: relative;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--toast-color);
    flex-shrink: 0;
  }
  
  .icon-bg {
    position: absolute;
    inset: 0;
    background: var(--toast-color);
    opacity: 0.1;
    border-radius: 50%;
    animation: iconPulse 2s ease-in-out infinite;
  }
  
  @keyframes iconPulse {
    0%, 100% {
      transform: scale(1);
      opacity: 0.1;
    }
    50% {
      transform: scale(1.2);
      opacity: 0.2;
    }
  }
  
  .checkmark {
    position: absolute;
    inset: 0;
    stroke-dasharray: 24;
    stroke-dashoffset: 24;
    animation: checkmarkDraw 0.6s ease-out 0.2s forwards;
  }
  
  @keyframes checkmarkDraw {
    to {
      stroke-dashoffset: 0;
    }
  }
  
  /* Message */
  .message {
    flex: 1;
    margin: 0;
    color: white;
    font-size: 0.9375rem;
    line-height: 1.5;
  }
  
  /* Close button */
  .close-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 50%;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .close-btn:hover {
    background: rgba(255, 255, 255, 0.2);
    color: white;
    transform: scale(1.1) rotate(90deg);
  }
  
  /* Progress bar */
  .progress-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: rgba(255, 255, 255, 0.1);
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: var(--toast-color);
    transition: width 0.1s linear;
    box-shadow: 0 0 10px var(--toast-color);
  }
  
  /* Particles */
  .particles {
    position: absolute;
    inset: 0;
    pointer-events: none;
    overflow: visible;
  }
  
  .particle {
    position: absolute;
    width: 4px;
    height: 4px;
    background: var(--toast-color);
    border-radius: 50%;
    animation: particleFly 1s ease-out forwards;
  }
  
  @keyframes particleFly {
    0% {
      transform: translate(0, 0) scale(0);
      opacity: 1;
    }
    100% {
      transform: translate(var(--tx, 0), var(--ty, -50px)) scale(1);
      opacity: 0;
    }
  }
</style>