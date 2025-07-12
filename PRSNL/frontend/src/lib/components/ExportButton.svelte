<script lang="ts" type="module">
  import { createEventDispatcher } from 'svelte';
  import Icon from './Icon.svelte';
  import { insights, exportInProgress } from '$lib/stores/insights';

  // Props
  export let disabled: boolean = false;

  // State
  let isOpen: boolean = false;
  let exportFormats = [
    { id: 'pdf', label: 'PDF Report', icon: 'file-text' },
    { id: 'csv', label: 'CSV Data', icon: 'file' },
    { id: 'json', label: 'JSON Data', icon: 'code' },
  ];

  // Event dispatcher
  const dispatch = createEventDispatcher<{
    exportStart: { format: string };
    exportComplete: { format: string };
    exportError: { error: Error };
  }>();

  // Handle export request
  async function handleExport(format: 'pdf' | 'csv' | 'json') {
    isOpen = false;

    try {
      dispatch('exportStart', { format });
      await insights.exportInsights(format);
      dispatch('exportComplete', { format });
    } catch (e) {
      const error = e as Error;
      dispatch('exportError', { error });
    }
  }

  // Handle dropdown toggle
  function toggleDropdown() {
    if (!disabled && !$exportInProgress) {
      isOpen = !isOpen;
    }
  }

  // Close dropdown when clicking outside
  function handleClickOutside(event: MouseEvent) {
    const target = event.target as Node;
    if (isOpen && dropdownMenu && !dropdownMenu.contains(target) && !exportBtn.contains(target)) {
      isOpen = false;
    }
  }

  // DOM references
  let dropdownMenu: HTMLDivElement;
  let exportBtn: HTMLButtonElement;
</script>

<!-- Handle clicks outside the dropdown to close it -->
<svelte:window on:click={handleClickOutside} />

<div class="export-button-container">
  <button
    bind:this={exportBtn}
    class="export-button"
    class:disabled
    on:click={toggleDropdown}
    aria-haspopup="true"
    aria-expanded={isOpen}
  >
    {#if $exportInProgress}
      <span class="spinner"></span>
      Exporting...
    {:else}
      <Icon name="download" />
      Export
    {/if}
  </button>

  {#if isOpen}
    <div bind:this={dropdownMenu} class="dropdown-menu" role="menu">
      {#each exportFormats as format}
        <button
          class="dropdown-item"
          on:click={() => handleExport(format.id as 'pdf' | 'csv' | 'json')}
          role="menuitem"
        >
          <Icon name={format.icon} />
          {format.label}
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .export-button-container {
    position: relative;
  }

  .export-button {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background-color: var(--accent);
    color: var(--text-on-accent);
    border: none;
    border-radius: var(--border-radius);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  .export-button:hover:not(.disabled) {
    background-color: var(--accent-dark);
  }

  .export-button.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .dropdown-menu {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    background-color: var(--bg-tertiary);
    border-radius: var(--border-radius);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    min-width: 180px;
    z-index: 100;
    overflow: hidden;
    animation: slideDown 0.2s ease;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .dropdown-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    color: var(--text-primary);
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  .dropdown-item:hover {
    background-color: var(--bg-hover);
  }

  .dropdown-item:not(:last-child) {
    border-bottom: 1px solid var(--border);
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid var(--text-on-accent);
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    display: inline-block;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
