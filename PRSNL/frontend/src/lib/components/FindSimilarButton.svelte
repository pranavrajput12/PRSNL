<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Icon from './Icon.svelte';
  
  // Props
  export let itemId: string;
  export let disabled: boolean = false;
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let variant: 'button' | 'icon' | 'link' = 'button';
  
  // Event dispatcher
  const dispatch = createEventDispatcher<{
    click: { itemId: string };
  }>();
  
  // Handle click
  function handleClick() {
    if (!disabled) {
      dispatch('click', { itemId });
    }
  }
</script>

{#if variant === 'button'}
  <button
    class="find-similar-button {size}"
    {disabled}
    on:click={handleClick}
    aria-label="Find similar items"
    title="Find similar items"
  >
    <Icon name="link-2" />
    <span>Find Similar</span>
  </button>
{:else if variant === 'icon'}
  <button
    class="find-similar-icon {size}"
    {disabled}
    on:click={handleClick}
    aria-label="Find similar items"
    title="Find similar items"
  >
    <Icon name="link-2" />
  </button>
{:else}
  <button
    class="find-similar-link {size}"
    {disabled}
    on:click={handleClick}
    aria-label="Find similar items"
  >
    <Icon name="link-2" size={size === 'large' ? 'medium' : 'small'} />
    <span>Similar</span>
  </button>
{/if}

<style>
  .find-similar-button,
  .find-similar-icon,
  .find-similar-link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
    font-weight: 500;
  }
  
  .find-similar-button {
    padding: 0.5rem 0.75rem;
    background-color: var(--accent-transparent);
    color: var(--accent);
    border-radius: var(--border-radius);
    font-size: 0.875rem;
  }
  
  .find-similar-button:hover:not([disabled]) {
    background-color: var(--accent);
    color: var(--text-on-accent);
  }
  
  .find-similar-button.small {
    padding: 0.35rem 0.6rem;
    font-size: 0.8rem;
  }
  
  .find-similar-button.large {
    padding: 0.6rem 1rem;
    font-size: 0.95rem;
  }
  
  .find-similar-icon {
    padding: 0.5rem;
    border-radius: 50%;
    background-color: var(--accent-transparent);
    color: var(--accent);
  }
  
  .find-similar-icon:hover:not([disabled]) {
    background-color: var(--accent);
    color: var(--text-on-accent);
  }
  
  .find-similar-icon.small {
    padding: 0.35rem;
  }
  
  .find-similar-icon.large {
    padding: 0.6rem;
  }
  
  .find-similar-link {
    padding: 0;
    background-color: transparent;
    color: var(--accent);
    font-size: 0.85rem;
  }
  
  .find-similar-link:hover:not([disabled]) {
    color: var(--accent-dark);
    text-decoration: underline;
  }
  
  .find-similar-link.small {
    font-size: 0.8rem;
  }
  
  .find-similar-link.large {
    font-size: 0.9rem;
  }
  
  [disabled] {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
