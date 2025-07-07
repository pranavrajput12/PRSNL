<script lang="ts">
  import { onMount } from 'svelte';
  import Icon from './Icon.svelte';
  
  export let fallback: 'minimal' | 'full' = 'full';
  export let onError: ((error: Error, errorInfo: any) => void) | null = null;
  
  let hasError = false;
  let error: Error | null = null;
  
  // Capture errors in child components
  function handleError(e: Error) {
    hasError = true;
    error = e;
    
    if (onError) {
      onError(e, { componentStack: e.stack });
    }
    
    // Log to console in development
    if (import.meta.env.DEV) {
      console.error('Error caught by boundary:', e);
    }
  }
  
  // Reset error state
  function reset() {
    hasError = false;
    error = null;
  }
  
  // Listen for unhandled errors
  onMount(() => {
    const handleUnhandledError = (event: ErrorEvent) => {
      handleError(new Error(event.message));
    };
    
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      handleError(new Error(event.reason));
    };
    
    window.addEventListener('error', handleUnhandledError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    
    return () => {
      window.removeEventListener('error', handleUnhandledError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  });
</script>

{#if hasError}
  {#if fallback === 'minimal'}
    <div class="error-boundary-minimal">
      <p>Something went wrong</p>
      <button on:click={reset}>Try again</button>
    </div>
  {:else}
    <div class="error-boundary">
      <div class="error-content">
        <Icon name="alert-triangle" size="large" />
        <h2>Oops! Something went wrong</h2>
        <p class="error-message">
          {error?.message || 'An unexpected error occurred'}
        </p>
        
        {#if import.meta.env.DEV && error?.stack}
          <details class="error-details">
            <summary>Error details</summary>
            <pre>{error.stack}</pre>
          </details>
        {/if}
        
        <div class="error-actions">
          <button class="primary-btn" on:click={reset}>
            <Icon name="refresh-cw" size="small" />
            Try again
          </button>
          <button class="secondary-btn" on:click={() => window.location.href = '/'}>
            <Icon name="home" size="small" />
            Go home
          </button>
        </div>
      </div>
    </div>
  {/if}
{:else}
  <slot />
{/if}

<style>
  .error-boundary {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background: var(--bg-primary);
  }
  
  .error-content {
    text-align: center;
    max-width: 500px;
  }
  
  .error-content h2 {
    margin: 1rem 0;
    color: var(--text-primary);
  }
  
  .error-message {
    color: var(--text-secondary);
    margin-bottom: 2rem;
  }
  
  .error-details {
    margin: 2rem 0;
    text-align: left;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
  }
  
  .error-details summary {
    cursor: pointer;
    color: var(--text-secondary);
    margin-bottom: 1rem;
  }
  
  .error-details pre {
    overflow-x: auto;
    font-size: 0.875rem;
    color: var(--error);
    white-space: pre-wrap;
    word-break: break-word;
  }
  
  .error-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }
  
  .primary-btn, .secondary-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s;
    border: none;
    cursor: pointer;
  }
  
  .primary-btn {
    background: var(--accent);
    color: white;
  }
  
  .primary-btn:hover {
    background: var(--accent-hover);
    transform: translateY(-1px);
  }
  
  .secondary-btn {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border);
  }
  
  .secondary-btn:hover {
    background: var(--bg-tertiary);
  }
  
  /* Minimal error boundary */
  .error-boundary-minimal {
    padding: 1rem;
    background: rgba(220, 20, 60, 0.1);
    border: 1px solid var(--error);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }
  
  .error-boundary-minimal p {
    margin: 0;
    color: var(--error);
  }
  
  .error-boundary-minimal button {
    padding: 0.25rem 0.75rem;
    background: var(--error);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
  }
  
  .error-boundary-minimal button:hover {
    opacity: 0.9;
  }
</style>