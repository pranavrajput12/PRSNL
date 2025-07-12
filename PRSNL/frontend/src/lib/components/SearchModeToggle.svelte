<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Icon from './Icon.svelte';

  // Props
  export let mode: 'keyword' | 'semantic' | 'hybrid' = 'keyword';
  export let disabled: boolean = false;

  // Event dispatcher
  const dispatch = createEventDispatcher<{
    change: { mode: 'keyword' | 'semantic' | 'hybrid' };
  }>();

  // Mode definitions
  const modes = [
    {
      id: 'keyword',
      label: 'Keyword',
      icon: 'hash',
      description: 'Match exact words and phrases',
    },
    {
      id: 'semantic',
      label: 'Semantic',
      icon: 'lightbulb',
      description: 'Match similar meanings and concepts',
    },
    {
      id: 'hybrid',
      label: 'Hybrid',
      icon: 'layers',
      description: 'Combine both keyword and semantic matching',
    },
  ];

  // Handle mode change
  function handleChange(newMode: 'keyword' | 'semantic' | 'hybrid') {
    if (disabled || newMode === mode) return;
    mode = newMode;
    dispatch('change', { mode: newMode });
  }

  // Toggle tooltip visibility
  let activeTooltip: string | null = null;

  function showTooltip(id: string) {
    if (!disabled) {
      activeTooltip = id;
    }
  }

  function hideTooltip() {
    activeTooltip = null;
  }
</script>

<div class="search-mode-toggle" class:disabled>
  {#each modes as { id, label, icon, description }}
    <button
      class="mode-button"
      class:active={mode === id}
      on:click={() => handleChange(id)}
      on:mouseenter={() => showTooltip(id)}
      on:mouseleave={hideTooltip}
      {disabled}
      aria-pressed={mode === id}
      aria-label={`Switch to ${label} search mode`}
    >
      <Icon name={icon} />
      <span class="label">{label}</span>

      {#if activeTooltip === id}
        <div class="tooltip" role="tooltip">
          {description}
        </div>
      {/if}
    </button>
  {/each}
</div>

<style>
  .search-mode-toggle {
    display: flex;
    border-radius: var(--border-radius);
    overflow: hidden;
    border: 1px solid var(--border);
    background: var(--bg-tertiary);
  }

  .search-mode-toggle.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .mode-button {
    display: flex;
    align-items: center;
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: none;
    border-right: 1px solid var(--border);
    color: var(--text-secondary);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
  }

  .mode-button:last-child {
    border-right: none;
  }

  .mode-button.active {
    background: var(--accent);
    color: var(--text-on-accent);
    font-weight: 500;
  }

  .mode-button:not(.active):hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .label {
    margin-left: 0.5rem;
  }

  .tooltip {
    position: absolute;
    top: calc(100% + 8px);
    left: 50%;
    transform: translateX(-50%);
    background: var(--bg-tooltip);
    color: var(--text-on-tooltip);
    padding: 0.5rem 0.75rem;
    border-radius: var(--border-radius);
    font-size: 0.75rem;
    white-space: nowrap;
    z-index: 100;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    pointer-events: none;
    animation: fadeIn 0.2s ease;
  }

  .tooltip::before {
    content: '';
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 6px solid transparent;
    border-bottom-color: var(--bg-tooltip);
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translate(-50%, -4px);
    }
    to {
      opacity: 1;
      transform: translate(-50%, 0);
    }
  }

  @media (max-width: 480px) {
    .label {
      display: none;
    }

    .mode-button {
      padding: 0.5rem;
    }
  }
</style>
