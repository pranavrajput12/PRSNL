<script lang="ts">
  export let message = 'An error occurred';
  export let details = '';
  export let retry: (() => void) | null = null;
  export let dismiss: (() => void) | null = null;
  
  // Only render if we have a meaningful message
  $: shouldRender = message && message !== '' && message !== 'An error occurred';
</script>

{#if shouldRender}
<div class="error-container">
  <div class="error-icon">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="12" y1="8" x2="12" y2="12"></line>
      <line x1="12" y1="16" x2="12.01" y2="16"></line>
    </svg>
  </div>

  <div class="error-content">
    <h3>{message}</h3>
    {#if details}
      <p>{details}</p>
    {/if}

    <div class="error-actions">
      {#if retry}
        <button class="retry" on:click={retry}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"
            />
          </svg>
          Try again
        </button>
      {/if}

      {#if dismiss}
        <button class="dismiss" on:click={dismiss}>Dismiss</button>
      {/if}
    </div>
  </div>
</div>
{/if}

<style>
  .error-container {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    background-color: rgba(255, 100, 100, 0.1);
    border: 1px solid rgba(255, 100, 100, 0.3);
    border-radius: var(--radius);
    margin: 1rem 0;
  }

  .error-icon {
    color: rgb(255, 100, 100);
    flex-shrink: 0;
  }

  .error-content {
    flex: 1;
  }

  h3 {
    margin: 0 0 0.5rem;
    font-size: 1rem;
    font-weight: 500;
    color: rgb(255, 100, 100);
  }

  p {
    margin: 0 0 1rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .error-actions {
    display: flex;
    gap: 0.5rem;
  }

  button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
    border-radius: var(--radius);
    cursor: pointer;
    transition: all 0.2s;
  }

  .retry {
    background-color: rgb(255, 100, 100);
    color: white;
    border: none;
  }

  .retry:hover {
    background-color: rgb(220, 80, 80);
  }

  .dismiss {
    background-color: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border);
  }

  .dismiss:hover {
    background-color: var(--bg-tertiary);
  }
</style>
