<script lang="ts">
  import Icon from '../Icon.svelte';

  export let icon: string = 'file-x';
  export let title: string = 'No items found';
  export let description: string = 'Get started by adding some content';
  export let actionLabel: string = '';
  export let actionHref: string = '';
  export let onAction: (() => void) | null = null;
  export let size: 'sm' | 'md' | 'lg' = 'md';
</script>

<div class="cortex-empty-state {size}">
  <div class="empty-icon">
    <Icon name={icon} size={size === 'sm' ? '32' : size === 'lg' ? '64' : '48'} />
  </div>
  
  <h3 class="empty-title">{title}</h3>
  
  <p class="empty-description">{description}</p>
  
  {#if actionLabel && (actionHref || onAction)}
    <div class="empty-action">
      {#if actionHref}
        <a href={actionHref} class="action-link">
          {actionLabel}
        </a>
      {:else if onAction}
        <button class="action-button" on:click={onAction}>
          {actionLabel}
        </button>
      {/if}
    </div>
  {/if}

  <slot />
</div>

<style>
  .cortex-empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #666;
    min-height: 200px;
  }

  .cortex-empty-state.sm {
    padding: 2rem;
    min-height: 150px;
  }

  .cortex-empty-state.md {
    padding: 3rem;
    min-height: 200px;
  }

  .cortex-empty-state.lg {
    padding: 4rem;
    min-height: 300px;
  }

  .empty-icon {
    margin-bottom: 1rem;
    opacity: 0.7;
  }

  .empty-title {
    margin: 0 0 0.5rem 0;
    color: #e0e0e0;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .cortex-empty-state.sm .empty-title {
    font-size: 1rem;
  }

  .cortex-empty-state.lg .empty-title {
    font-size: 1.5rem;
  }

  .empty-description {
    margin: 0 0 1.5rem 0;
    max-width: 400px;
    line-height: 1.5;
  }

  .empty-action {
    margin-top: 1rem;
  }

  .action-link,
  .action-button {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: #00ff88;
    color: #000;
    border: 1px solid #00ff88;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .action-link:hover,
  .action-button:hover {
    background: #00cc6a;
    border-color: #00cc6a;
    transform: translateY(-1px);
  }

  /* Animation */
  .cortex-empty-state {
    animation: fadeIn 0.5s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>