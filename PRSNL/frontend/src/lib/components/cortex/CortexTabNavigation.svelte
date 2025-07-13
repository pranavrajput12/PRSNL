<script lang="ts">
  import Icon from '../Icon.svelte';

  export let tabs: Array<{
    id: string,
    label: string,
    icon?: string,
    count?: number,
    disabled?: boolean
  }> = [];
  export let activeTab: string = '';
  export let onTabChange: (tabId: string) => void = () => {};
  export let variant: 'default' | 'pills' | 'underline' = 'default';
</script>

<div class="cortex-tab-navigation {variant}">
  <div class="tab-list" role="tablist">
    {#each tabs as tab}
      <button
        class="tab-button"
        class:active={activeTab === tab.id}
        class:disabled={tab.disabled}
        role="tab"
        aria-selected={activeTab === tab.id}
        disabled={tab.disabled}
        on:click={() => !tab.disabled && onTabChange(tab.id)}
      >
        {#if tab.icon}
          <Icon name={tab.icon} size="16" />
        {/if}
        <span class="tab-label">{tab.label}</span>
        {#if tab.count !== undefined}
          <span class="tab-count">{tab.count}</span>
        {/if}
      </button>
    {/each}
  </div>
</div>

<style>
  .cortex-tab-navigation {
    margin-bottom: 2rem;
  }

  .tab-list {
    display: flex;
    gap: 0.25rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 0.25rem;
  }

  .tab-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: transparent;
    border: none;
    color: #888;
    cursor: pointer;
    transition: all 0.2s ease;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    white-space: nowrap;
  }

  .tab-button:hover:not(.disabled) {
    color: #00ff88;
    background: rgba(0, 255, 136, 0.1);
  }

  .tab-button.active {
    color: #000;
    background: #00ff88;
  }

  .tab-button.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .tab-count {
    background: rgba(0, 0, 0, 0.2);
    color: inherit;
    padding: 0.2rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    min-width: 20px;
    text-align: center;
  }

  .tab-button.active .tab-count {
    background: rgba(0, 0, 0, 0.2);
    color: #000;
  }

  /* Pills variant */
  .cortex-tab-navigation.pills .tab-list {
    background: transparent;
    border: none;
    gap: 0.5rem;
    padding: 0;
  }

  .cortex-tab-navigation.pills .tab-button {
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 20px;
  }

  .cortex-tab-navigation.pills .tab-button.active {
    border-color: #00ff88;
  }

  /* Underline variant */
  .cortex-tab-navigation.underline .tab-list {
    background: transparent;
    border: none;
    border-bottom: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 0;
    padding: 0;
    gap: 0;
  }

  .cortex-tab-navigation.underline .tab-button {
    border-radius: 0;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
  }

  .cortex-tab-navigation.underline .tab-button.active {
    background: transparent;
    color: #00ff88;
    border-bottom-color: #00ff88;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .tab-list {
      overflow-x: auto;
      scrollbar-width: none;
      -ms-overflow-style: none;
    }

    .tab-list::-webkit-scrollbar {
      display: none;
    }

    .tab-button {
      padding: 0.75rem 1rem;
      font-size: 0.8rem;
    }
  }
</style>