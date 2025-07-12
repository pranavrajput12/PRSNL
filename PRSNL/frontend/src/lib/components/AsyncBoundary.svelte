<script lang="ts" type="module">
  import Spinner from './Spinner.svelte';
  import ErrorMessage from './ErrorMessage.svelte';
  import ErrorBoundary from './ErrorBoundary.svelte';
  import { onMount } from 'svelte';

  export let loading = false;
  export let error: Error | null = null;
  export let fallback: 'minimal' | 'full' = 'minimal';
  export let loadingMessage = 'Loading...';
  export let minLoadingTime = 0;

  let startTime: number;
  let showLoading = loading;

  $: {
    if (loading && !startTime) {
      startTime = Date.now();
      showLoading = true;
    } else if (!loading && startTime) {
      // Ensure minimum loading time for smooth UX
      const elapsed = Date.now() - startTime;
      if (elapsed < minLoadingTime) {
        setTimeout(() => {
          showLoading = false;
          startTime = 0;
        }, minLoadingTime - elapsed);
      } else {
        showLoading = false;
        startTime = 0;
      }
    }
  }
</script>

<ErrorBoundary {fallback}>
  {#if showLoading}
    <div class="loading-container">
      <Spinner />
      {#if loadingMessage}
        <p class="loading-message">{loadingMessage}</p>
      {/if}
    </div>
  {:else if error}
    <ErrorMessage message={error.message} />
  {:else}
    <slot />
  {/if}
</ErrorBoundary>

<style>
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    min-height: 200px;
  }

  .loading-message {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
</style>
