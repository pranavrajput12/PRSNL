<script lang="ts">
  import Icon from '../Icon.svelte';

  export let message: string = 'Loading...';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let variant: 'spinner' | 'pulse' | 'skeleton' = 'spinner';
  export let showMessage: boolean = true;
</script>

{#if variant === 'spinner'}
  <div class="cortex-loading-state spinner {size}">
    <div class="loading-spinner">
      <Icon name="loader" size={size === 'sm' ? '24' : size === 'lg' ? '48' : '32'} class="animate-spin" />
    </div>
    {#if showMessage}
      <span class="loading-message">{message}</span>
    {/if}
  </div>
{:else if variant === 'pulse'}
  <div class="cortex-loading-state pulse {size}">
    <div class="neural-pulse"></div>
    {#if showMessage}
      <span class="loading-message">{message}</span>
    {/if}
  </div>
{:else if variant === 'skeleton'}
  <div class="cortex-loading-state skeleton {size}">
    <div class="skeleton-lines">
      <div class="skeleton-line"></div>
      <div class="skeleton-line short"></div>
      <div class="skeleton-line medium"></div>
    </div>
    {#if showMessage}
      <span class="loading-message">{message}</span>
    {/if}
  </div>
{/if}

<style>
  .cortex-loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    color: #00ff88;
    text-align: center;
  }

  .cortex-loading-state.sm {
    padding: 1.5rem;
    min-height: 100px;
  }

  .cortex-loading-state.md {
    padding: 2rem;
    min-height: 150px;
  }

  .cortex-loading-state.lg {
    padding: 3rem;
    min-height: 200px;
  }

  /* Spinner Variant */
  .loading-spinner {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  /* Pulse Variant */
  .neural-pulse {
    width: 50px;
    height: 50px;
    border: 3px solid rgba(0, 255, 136, 0.3);
    border-top: 3px solid #00ff88;
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
  }

  .cortex-loading-state.sm .neural-pulse {
    width: 30px;
    height: 30px;
    border-width: 2px;
  }

  .cortex-loading-state.lg .neural-pulse {
    width: 70px;
    height: 70px;
    border-width: 4px;
  }

  @keyframes pulse {
    0%, 100% {
      border-top-color: #00ff88;
      transform: scale(1);
    }
    50% {
      border-top-color: #00cc6a;
      transform: scale(1.1);
    }
  }

  /* Skeleton Variant */
  .skeleton-lines {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    width: 100%;
    max-width: 300px;
  }

  .skeleton-line {
    height: 1rem;
    background: linear-gradient(90deg, 
      rgba(0, 255, 136, 0.1) 25%, 
      rgba(0, 255, 136, 0.3) 50%, 
      rgba(0, 255, 136, 0.1) 75%
    );
    background-size: 200% 100%;
    border-radius: 4px;
    animation: shimmer 2s infinite;
  }

  .skeleton-line.short {
    width: 60%;
  }

  .skeleton-line.medium {
    width: 80%;
  }

  .cortex-loading-state.sm .skeleton-line {
    height: 0.75rem;
  }

  .cortex-loading-state.lg .skeleton-line {
    height: 1.25rem;
  }

  @keyframes shimmer {
    0% {
      background-position: -200% 0;
    }
    100% {
      background-position: 200% 0;
    }
  }

  /* Loading Message */
  .loading-message {
    font-size: 0.875rem;
    opacity: 0.8;
    animation: fadeInOut 2s ease-in-out infinite;
  }

  .cortex-loading-state.sm .loading-message {
    font-size: 0.75rem;
  }

  .cortex-loading-state.lg .loading-message {
    font-size: 1rem;
  }

  @keyframes fadeInOut {
    0%, 100% { opacity: 0.8; }
    50% { opacity: 0.4; }
  }

  /* Spin Animation */
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  /* Container Animation */
  .cortex-loading-state {
    animation: slideIn 0.3s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>