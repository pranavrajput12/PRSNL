<script lang="ts">
  import Icon from './Icon.svelte';

  export let title: string;
  export let icon: string = 'file-text';
  export let collapsible: boolean = false;
  export let collapsed: boolean = false;
  export let accent: string = 'primary';

  function toggle() {
    if (collapsible) {
      collapsed = !collapsed;
    }
  }
</script>

<div class="knowledge-card {accent}" class:collapsed>
  <div class="card-header" on:click={toggle} class:clickable={collapsible}>
    <div class="header-left">
      <Icon name={icon} size="small" />
      <h3>{title}</h3>
    </div>
    {#if collapsible}
      <button class="toggle-btn" on:click|stopPropagation={toggle}>
        <Icon name={collapsed ? 'chevron-down' : 'chevron-up'} size="small" />
      </button>
    {/if}
  </div>
  {#if !collapsed}
    <div class="card-content">
      <slot />
    </div>
  {/if}
</div>

<style>
  .knowledge-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 1.5rem;
    overflow: hidden;
    transition: all 0.3s ease;
  }

  .knowledge-card.primary {
    border-color: var(--accent-dim);
  }

  .knowledge-card.success {
    border-color: var(--success);
  }

  .knowledge-card.warning {
    border-color: var(--warning);
  }

  .knowledge-card.collapsed {
    margin-bottom: 0.75rem;
  }

  .card-header {
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border);
  }

  .card-header.clickable {
    cursor: pointer;
  }

  .card-header.clickable:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .header-left h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .toggle-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    color: var(--text-secondary);
    transition: color 0.2s;
  }

  .toggle-btn:hover {
    color: var(--text-primary);
  }

  .card-content {
    padding: 1.5rem;
  }

  .collapsed .card-header {
    border-bottom: none;
  }
</style>
