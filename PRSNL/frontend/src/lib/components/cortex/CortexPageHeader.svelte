<script lang="ts">
  import Icon from '../Icon.svelte';

  export let title: string;
  export let description: string;
  export let icon: string = '⚡';
  export let backUrl: string = '/code-cortex';
  export let backText: string = 'Code Cortex';
  export let stats: Array<{ label: string; value: string | number }> = [];
  export let actions: Array<{
    label: string;
    icon?: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary';
  }> = [];
</script>

<div class="cortex-page-header">
  <button class="back-button" on:click={() => (window.location.href = backUrl)}>
    <Icon name="arrow-left" size="20" />
    {backText}
  </button>

  <div class="header-content">
    <div class="header-left">
      <div class="header-info">
        <h1>
          <Icon name={icon === '⚡' ? 'zap' : icon} size="28" />
          {title}
        </h1>
        <p>{description}</p>
      </div>
    </div>

    <div class="header-right">
      {#if stats.length > 0}
        <div class="header-stats">
          {#each stats as stat}
            <div class="stat-chip">
              <span class="stat-value">{stat.value}</span>
              <span class="stat-label">{stat.label}</span>
            </div>
          {/each}
        </div>
      {/if}

      {#if actions.length > 0}
        <div class="header-actions">
          {#each actions as action}
            <button class="action-btn {action.variant || 'secondary'}" on:click={action.onClick}>
              {#if action.icon}
                <Icon name={action.icon} size="16" />
              {/if}
              {action.label}
            </button>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .cortex-page-header {
    margin-bottom: 2rem;
  }

  .back-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: transparent;
    border: 1px solid #333;
    color: #00ff88;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 1rem;
  }

  .back-button:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: #00ff88;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 2rem;
  }

  .header-info h1 {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 2.5rem;
    margin: 0 0 0.5rem 0;
    color: #00ff88;
    font-weight: 700;
  }

  .header-info p {
    font-size: 1.1rem;
    color: #888;
    margin: 0;
  }

  .header-right {
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
  }

  .header-stats {
    display: flex;
    gap: 1rem;
  }

  .stat-chip {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    text-align: center;
    min-width: 80px;
  }

  .stat-value {
    display: block;
    font-size: 1.5rem;
    font-weight: bold;
    color: #00ff88;
  }

  .stat-label {
    display: block;
    font-size: 0.875rem;
    opacity: 0.7;
    margin-top: 0.25rem;
  }

  .header-actions {
    display: flex;
    gap: 0.75rem;
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .action-btn.primary {
    background: #00ff88;
    color: #000;
    border: 1px solid #00ff88;
  }

  .action-btn.primary:hover {
    background: #00cc6a;
    border-color: #00cc6a;
  }

  .action-btn.secondary {
    background: transparent;
    color: #00ff88;
    border: 1px solid rgba(0, 255, 136, 0.3);
  }

  .action-btn.secondary:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: #00ff88;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .header-content {
      flex-direction: column;
      gap: 1rem;
    }

    .header-right {
      width: 100%;
      justify-content: space-between;
      align-items: center;
    }

    .header-stats {
      flex-wrap: wrap;
    }

    .header-actions {
      flex-wrap: wrap;
    }
  }
</style>
