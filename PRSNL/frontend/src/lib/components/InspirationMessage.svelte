<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';

  export let messages: string[] = [];
  export let interval = 5000; // Change message every 5 seconds
  export let position: 'top' | 'bottom' | 'center' = 'bottom';
  export let size: 'small' | 'medium' | 'large' = 'medium';

  let currentIndex = 0;
  let currentMessage = messages[0] || '';
  let intervalId: NodeJS.Timeout;
  let isVisible = true;

  const sizeClasses = {
    small: 'text-sm',
    medium: 'text-base',
    large: 'text-lg'
  };

  const positionClasses = {
    top: 'top-8',
    bottom: 'bottom-8',
    center: 'top-1/2 -translate-y-1/2'
  };

  function nextMessage() {
    isVisible = false;
    setTimeout(() => {
      currentIndex = (currentIndex + 1) % messages.length;
      currentMessage = messages[currentIndex];
      isVisible = true;
    }, 300);
  }

  onMount(() => {
    if (messages.length > 1) {
      intervalId = setInterval(nextMessage, interval);
    }
  });

  onDestroy(() => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  });
</script>

{#if messages.length > 0 && isVisible}
  <div class="inspiration-container {positionClasses[position]}">
    <div
      in:fly={{ y: 20, duration: 600, easing: cubicOut }}
      out:fade={{ duration: 300 }}
      class="inspiration-message {sizeClasses[size]}"
    >
      <span class="message-text">
        {currentMessage}
      </span>
      <div class="message-glow"></div>
    </div>
  </div>
{/if}

<style>
  .inspiration-container {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    z-index: 10;
    pointer-events: none;
  }

  .inspiration-message {
    position: relative;
    display: inline-block;
    padding: 0.75rem 1.5rem;
    background: rgba(139, 92, 246, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 9999px;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 500;
    letter-spacing: 0.025em;
    animation: float 6s ease-in-out infinite;
  }

  .message-text {
    position: relative;
    z-index: 2;
  }

  .message-glow {
    position: absolute;
    inset: -2px;
    background: linear-gradient(45deg, #8b5cf6, #ec4899);
    border-radius: 9999px;
    opacity: 0.3;
    filter: blur(10px);
    z-index: 1;
    animation: pulse 3s ease-in-out infinite;
  }

  @keyframes float {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-10px);
    }
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 0.3;
      transform: scale(1);
    }
    50% {
      opacity: 0.5;
      transform: scale(1.05);
    }
  }

  /* Responsive adjustments */
  @media (max-width: 640px) {
    .inspiration-message {
      padding: 0.5rem 1rem;
      font-size: 0.875rem;
    }
  }
</style>