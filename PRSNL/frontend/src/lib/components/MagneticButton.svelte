<script lang="ts">
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';

  export let type: 'button' | 'submit' | 'reset' = 'button';
  export let variant: 'primary' | 'secondary' | 'ghost' = 'primary';
  export let disabled = false;
  export let loading = false;
  export let icon: string | null = null;
  export let iconPosition: 'left' | 'right' = 'right';
  export let fullWidth = false;
  export let size: 'small' | 'medium' | 'large' = 'medium';

  let buttonEl: HTMLButtonElement;
  let ripples: Array<{ x: number; y: number; id: number }> = [];
  let magnetX = 0;
  let magnetY = 0;
  let isHovering = false;

  const sizeClasses = {
    small: 'px-4 py-2 text-sm',
    medium: 'px-6 py-3 text-base',
    large: 'px-8 py-4 text-lg'
  };

  const variantClasses = {
    primary: 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white',
    secondary: 'bg-white/10 border border-white/20 text-white hover:bg-white/20',
    ghost: 'text-purple-400 hover:text-purple-300 hover:bg-white/5'
  };

  function handleMouseMove(e: MouseEvent) {
    if (!buttonEl || disabled) return;

    const rect = buttonEl.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    // Calculate magnetic effect (stronger when closer to button)
    const maxDistance = 100;
    const distance = Math.sqrt(
      Math.pow(e.clientX - (rect.left + centerX), 2) +
      Math.pow(e.clientY - (rect.top + centerY), 2)
    );

    if (distance < maxDistance) {
      const strength = (1 - distance / maxDistance) * 0.3;
      magnetX = (x - centerX) * strength;
      magnetY = (y - centerY) * strength;
    } else {
      magnetX = 0;
      magnetY = 0;
    }
  }

  function handleMouseEnter() {
    isHovering = true;
  }

  function handleMouseLeave() {
    isHovering = false;
    magnetX = 0;
    magnetY = 0;
  }

  function handleClick(e: MouseEvent) {
    if (!buttonEl || disabled) return;

    const rect = buttonEl.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const id = Date.now();
    ripples = [...ripples, { x, y, id }];

    setTimeout(() => {
      ripples = ripples.filter(r => r.id !== id);
    }, 600);
  }

  onMount(() => {
    if (buttonEl) {
      const parent = buttonEl.parentElement;
      if (parent) {
        parent.addEventListener('mousemove', handleMouseMove);
        return () => {
          parent.removeEventListener('mousemove', handleMouseMove);
        };
      }
    }
  });
</script>

<button
  bind:this={buttonEl}
  {type}
  {disabled}
  on:click={handleClick}
  on:click
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  class="
    magnetic-button
    {sizeClasses[size]}
    {variantClasses[variant]}
    {fullWidth ? 'w-full' : ''}
    {disabled ? 'opacity-50 cursor-not-allowed' : ''}
  "
  style="transform: translate({magnetX}px, {magnetY}px) scale({isHovering && !disabled ? 1.05 : 1})"
>
  <span class="button-content">
    {#if loading}
      <Icon name="loader-2" class="animate-spin {size === 'small' ? 'w-4 h-4' : 'w-5 h-5'}" />
    {:else}
      {#if icon && iconPosition === 'left'}
        <Icon name={icon} class="{size === 'small' ? 'w-4 h-4' : 'w-5 h-5'}" />
      {/if}
      <slot />
      {#if icon && iconPosition === 'right' && !loading}
        <Icon name={icon} class="{size === 'small' ? 'w-4 h-4' : 'w-5 h-5'}" />
      {/if}
    {/if}
  </span>

  <!-- Ripple effects -->
  {#each ripples as ripple (ripple.id)}
    <span
      class="ripple"
      style="left: {ripple.x}px; top: {ripple.y}px"
    />
  {/each}

  <!-- Hover glow effect -->
  {#if isHovering && !disabled}
    <div class="hover-glow"></div>
  {/if}
</button>

<style>
  .magnetic-button {
    position: relative;
    font-weight: 500;
    border-radius: 0.5rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    transform-style: preserve-3d;
    backface-visibility: hidden;
  }

  .button-content {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    z-index: 2;
  }

  .ripple {
    position: absolute;
    border-radius: 50%;
    transform: translate(-50%, -50%);
    background: rgba(255, 255, 255, 0.5);
    pointer-events: none;
    animation: ripple 0.6s ease-out;
  }

  @keyframes ripple {
    from {
      width: 0;
      height: 0;
      opacity: 1;
    }
    to {
      width: 200px;
      height: 200px;
      opacity: 0;
    }
  }

  .hover-glow {
    position: absolute;
    inset: -2px;
    background: linear-gradient(45deg, #8b5cf6, #ec4899);
    border-radius: 0.5rem;
    opacity: 0;
    filter: blur(15px);
    z-index: 0;
    animation: glow-pulse 2s ease-in-out infinite;
  }

  @keyframes glow-pulse {
    0%, 100% {
      opacity: 0.3;
    }
    50% {
      opacity: 0.6;
    }
  }

  /* Reduce motion for accessibility */
  @media (prefers-reduced-motion: reduce) {
    .magnetic-button {
      transform: none !important;
      transition: background-color 0.2s;
    }
    
    .ripple {
      display: none;
    }
    
    .hover-glow {
      animation: none;
      opacity: 0.2;
    }
  }
</style>