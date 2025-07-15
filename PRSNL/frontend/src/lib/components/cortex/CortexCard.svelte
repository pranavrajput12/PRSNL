<script lang="ts">
  import Icon from '../Icon.svelte';

  export let title: string = '';
  export let description: string = '';
  export let icon: string = '';
  export let iconColor: string = '#00ff88';
  export let onClick: (() => void) | null = null;
  export let href: string = '';
  export let variant: 'default' | 'highlight' | 'minimal' | 'stats' = 'default';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let tags: Array<{ label: string; color?: string }> = [];
  export let stats: Array<{ label: string; value: string | number }> = [];
  export let actions: Array<{ label: string; icon?: string; onClick: () => void }> = [];
  export let loading: boolean = false;
  export let disabled: boolean = false;

  function handleClick() {
    if (disabled || loading) return;
    if (href) {
      window.location.href = href;
    } else if (onClick) {
      onClick();
    }
  }

  $: isClickable = (onClick || href) && !disabled && !loading;
</script>

<div
  class="cortex-card {variant} {size}"
  class:clickable={isClickable}
  class:loading
  class:disabled
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  role={isClickable ? 'button' : 'article'}
  tabindex={isClickable ? 0 : -1}
>
  {#if loading}
    <div class="loading-overlay">
      <Icon name="loader" size="24" class="animate-spin" />
    </div>
  {/if}

  <div class="card-content">
    <!-- Header Section -->
    {#if title || icon}
      <div class="card-header">
        <div class="header-left">
          {#if icon}
            <div class="card-icon" style="color: {iconColor}">
              <Icon name={icon} size={size === 'sm' ? '20' : size === 'lg' ? '28' : '24'} />
            </div>
          {/if}
          {#if title}
            <h3 class="card-title">{title}</h3>
          {/if}
        </div>

        {#if actions.length > 0}
          <div class="card-actions">
            {#each actions as action}
              <button
                class="action-btn"
                on:click|stopPropagation={action.onClick}
                title={action.label}
              >
                {#if action.icon}
                  <Icon name={action.icon} size="16" />
                {:else}
                  {action.label}
                {/if}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Description -->
    {#if description}
      <p class="card-description">{description}</p>
    {/if}

    <!-- Tags -->
    {#if tags.length > 0}
      <div class="card-tags">
        {#each tags as tag}
          <span class="tag" style="background-color: {tag.color || 'rgba(0, 255, 136, 0.2)'}">
            {tag.label}
          </span>
        {/each}
      </div>
    {/if}

    <!-- Stats -->
    {#if stats.length > 0}
      <div class="card-stats">
        {#each stats as stat}
          <div class="stat">
            <span class="stat-value">{stat.value}</span>
            <span class="stat-label">{stat.label}</span>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Custom Content Slot -->
    <slot />
  </div>
</div>

<style>
  .cortex-card {
    background: linear-gradient(135deg, #1a1a1a 0%, #151515 100%);
    border: 1px solid #333;
    border-radius: 12px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
  }

  .cortex-card.clickable {
    cursor: pointer;
  }

  .cortex-card.clickable:hover:not(.disabled):not(.loading) {
    border-color: #00ff88;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 255, 136, 0.1);
  }

  .cortex-card.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .cortex-card.loading {
    cursor: wait;
  }

  /* Size Variants */
  .cortex-card.sm {
    padding: 1rem;
  }

  .cortex-card.md {
    padding: 1.5rem;
  }

  .cortex-card.lg {
    padding: 2rem;
  }

  /* Style Variants */
  .cortex-card.highlight {
    border-color: #00ff88;
    box-shadow: 0 4px 15px rgba(0, 255, 136, 0.1);
  }

  .cortex-card.minimal {
    background: transparent;
    border: 1px solid rgba(0, 255, 136, 0.1);
  }

  .cortex-card.stats {
    background: rgba(0, 255, 136, 0.05);
    border-color: rgba(0, 255, 136, 0.2);
  }

  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
  }

  .card-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
  }

  .card-icon {
    flex-shrink: 0;
  }

  .card-title {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #e0e0e0;
    line-height: 1.3;
  }

  .card-sm .card-title {
    font-size: 1rem;
  }

  .card-lg .card-title {
    font-size: 1.3rem;
  }

  .card-actions {
    display: flex;
    gap: 0.5rem;
  }

  .action-btn {
    background: transparent;
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .action-btn:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: #00ff88;
  }

  .card-description {
    margin: 0;
    color: #ccc;
    font-size: 0.875rem;
    line-height: 1.5;
    flex: 1;
  }

  .card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tag {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    color: #fff;
  }

  .card-stats {
    display: flex;
    gap: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(0, 255, 136, 0.1);
  }

  .stat {
    text-align: center;
  }

  .stat-value {
    display: block;
    font-size: 1.2rem;
    font-weight: bold;
    color: #00ff88;
  }

  .stat-label {
    display: block;
    font-size: 0.75rem;
    color: #888;
    margin-top: 0.25rem;
  }

  /* Animation */
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  /* Responsive */
  @media (max-width: 768px) {
    .card-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .card-actions {
      align-self: flex-end;
    }

    .card-stats {
      gap: 0.75rem;
    }
  }
</style>
