<script lang="ts" type="module">
  export let size: 'tiny' | 'small' | 'medium' | 'large' = 'medium';
  export let center = false;
  export let fullPage = false;
  export let message = '';

  // Size in pixels
  const sizeMap = {
    tiny: 12,
    small: 16,
    medium: 24,
    large: 40,
  };

  const pixelSize = sizeMap[size];
</script>

<div class="spinner-container" class:center class:full-page={fullPage}>
  <div
    class="spinner"
    style="width: {pixelSize}px; height: {pixelSize}px; border-width: {Math.max(
      2,
      pixelSize / 10
   )}px;"
  ></div>

  {#if message}
    <div class="message">{message}</div>
  {/if}
</div>

<style>
  .spinner-container {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .center {
    display: flex;
    margin: 0 auto;
  }

  .full-page {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--bg-primary);
    opacity: 0.9;
    z-index: 100;
  }

  .spinner {
    border-radius: 50%;
    border-style: solid;
    border-color: var(--border);
    border-top-color: var(--accent);
    animation: spin 0.8s linear infinite;
  }

  .message {
    margin-top: 1rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
