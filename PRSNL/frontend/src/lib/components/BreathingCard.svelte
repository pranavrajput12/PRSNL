<script lang="ts">
  import { onMount } from 'svelte';

  export let glowColor = '#8b5cf6';
  export let breathingScale = 0.02; // 2% scale change
  export let breathingDuration = 4; // seconds
  export let interactive = true;

  let cardEl: HTMLDivElement;
  let isHovering = false;
  let isFocused = false;
  let mouseX = 0;
  let mouseY = 0;

  function handleMouseMove(e: MouseEvent) {
    if (!cardEl || !interactive) return;

    const rect = cardEl.getBoundingClientRect();
    mouseX = ((e.clientX - rect.left) / rect.width) * 100;
    mouseY = ((e.clientY - rect.top) / rect.height) * 100;
  }

  function handleFocusIn() {
    isFocused = true;
  }

  function handleFocusOut() {
    isFocused = false;
  }

  onMount(() => {
    const handleGlobalFocus = (e: FocusEvent) => {
      if (cardEl && cardEl.contains(e.target as Node)) {
        handleFocusIn();
      } else {
        handleFocusOut();
      }
    };

    document.addEventListener('focusin', handleGlobalFocus);
    document.addEventListener('focusout', handleGlobalFocus);

    return () => {
      document.removeEventListener('focusin', handleGlobalFocus);
      document.removeEventListener('focusout', handleGlobalFocus);
    };
  });
</script>

<div
  bind:this={cardEl}
  on:mouseenter={() => isHovering = true}
  on:mouseleave={() => { isHovering = false; mouseX = 50; mouseY = 50; }}
  on:mousemove={handleMouseMove}
  class="breathing-card"
  style="
    --glow-color: {glowColor};
    --breathing-scale: {breathingScale};
    --breathing-duration: {breathingDuration}s;
    --mouse-x: {mouseX}%;
    --mouse-y: {mouseY}%;
    --is-focused: {isFocused ? 1 : 0};
    --is-hovering: {isHovering ? 1 : 0};
  "
>
  <div class="card-background"></div>
  <div class="card-glow"></div>
  <div class="card-content">
    <slot />
  </div>
  {#if interactive}
    <div class="interactive-glow"></div>
  {/if}
</div>

<style>
  .breathing-card {
    position: relative;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 1rem;
    padding: 2rem;
    overflow: hidden;
    transform-origin: center;
    animation: breathing var(--breathing-duration) ease-in-out infinite;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  @keyframes breathing {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(calc(1 + var(--breathing-scale)));
    }
  }

  .card-background {
    position: absolute;
    inset: 0;
    background: radial-gradient(
      circle at var(--mouse-x) var(--mouse-y),
      rgba(139, 92, 246, 0.1) 0%,
      transparent 60%
    );
    opacity: calc(var(--is-hovering) * 0.5);
    transition: opacity 0.3s ease;
  }

  .card-glow {
    position: absolute;
    inset: -2px;
    background: linear-gradient(
      45deg,
      var(--glow-color),
      #ec4899,
      var(--glow-color)
    );
    border-radius: 1rem;
    opacity: calc(0.2 + (var(--is-focused) * 0.3));
    filter: blur(20px);
    z-index: -1;
    animation: glow-rotate 8s linear infinite;
  }

  @keyframes glow-rotate {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .card-content {
    position: relative;
    z-index: 2;
  }

  .interactive-glow {
    position: absolute;
    width: 200px;
    height: 200px;
    background: radial-gradient(
      circle,
      rgba(139, 92, 246, 0.4) 0%,
      transparent 70%
    );
    border-radius: 50%;
    left: calc(var(--mouse-x) - 100px);
    top: calc(var(--mouse-y) - 100px);
    opacity: calc(var(--is-hovering) * 0.6);
    filter: blur(40px);
    pointer-events: none;
    transition: opacity 0.3s ease, left 0.1s ease, top 0.1s ease;
  }

  /* Enhanced focus state */
  .breathing-card:has(:focus-visible) {
    outline: 2px solid rgba(139, 92, 246, 0.5);
    outline-offset: 4px;
  }

  /* Reduce motion for accessibility */
  @media (prefers-reduced-motion: reduce) {
    .breathing-card {
      animation: none;
    }
    
    .card-glow {
      animation: none;
    }
    
    .interactive-glow {
      display: none;
    }
  }
</style>