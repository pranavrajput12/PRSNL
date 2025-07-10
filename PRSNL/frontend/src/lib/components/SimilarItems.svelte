<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { getSimilarItems } from '$lib/api';
  import type { ContentItem } from '$lib/types/api';
  import Icon from './Icon.svelte';
  import RelevanceScore from './RelevanceScore.svelte';
  import { getTypeIcon } from '$lib/stores/contentTypes';
  
  // Props
  export let itemId: string;
  export let limit: number = 5;
  export let isOpen: boolean = false;
  
  // State
  let isLoading = false;
  let error: Error | null = null;
  let similarItems: any[] = [];
  
  // Event dispatcher
  const dispatch = createEventDispatcher<{
    close: void;
    select: { item: ContentItem };
  }>();
  
  // Load similar items
  async function loadSimilarItems() {
    if (!itemId) return;
    
    try {
      isLoading = true;
      error = null;
      similarItems = await getSimilarItems(itemId, limit);
    } catch (e) {
      console.error('Failed to load similar items:', e);
      error = e as Error;
    } finally {
      isLoading = false;
    }
  }
  
  // Handle item selection
  function selectItem(item: ContentItem) {
    dispatch('select', { item });
  }
  
  // Handle close
  function close() {
    dispatch('close');
  }
  
  // Load data when component mounts or itemId changes
  $: if (isOpen && itemId) {
    loadSimilarItems();
  }
</script>

<div class="similar-items" class:open={isOpen}>
  <div class="similar-items-header">
    <h2>
      <Icon name="link" />
      Similar Items
    </h2>
    <button class="close-button" on:click={close} aria-label="Close similar items panel">
      <Icon name="x" />
    </button>
  </div>
  
  <div class="similar-items-content">
    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Finding similar items...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <Icon name="alert-circle" />
        <p>Failed to load similar items</p>
        <button on:click={loadSimilarItems}>Retry</button>
      </div>
    {:else if similarItems.length === 0}
      <div class="empty-state">
        <Icon name="search" />
        <p>No similar items found</p>
      </div>
    {:else}
      <ul class="similar-items-list">
        {#each similarItems as item}
          <li>
            <button class="similar-item" on:click={() => selectItem(item)}>
              <div class="item-icon">
                <Icon name={getTypeIcon(item.type || 'article')} />
              </div>
              <div class="item-content">
                <h3>{item.title || 'Untitled'}</h3>
                {#if item.metadata?.excerpt}
                  <p class="item-excerpt">{item.metadata.excerpt}</p>
                {/if}
              </div>
              {#if item.similarity !== undefined}
                <div class="similarity-score">
                  {Math.round(item.similarity * 100)}%
                </div>
              {/if}
            </button>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>

<style>
  .similar-items {
    position: fixed;
    top: 0;
    right: 0;
    height: 100%;
    width: 350px;
    background: var(--bg-secondary);
    box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
    z-index: 100;
    display: flex;
    flex-direction: column;
    transform: translateX(100%);
    transition: transform 0.3s ease;
  }
  
  .similar-items.open {
    transform: translateX(0);
  }
  
  .similar-items-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--border);
  }
  
  .similar-items-header h2 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .close-button {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s ease;
  }
  
  .close-button:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
  
  .similar-items-content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .loading-state,
  .error-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
  }
  
  .spinner {
    width: 24px;
    height: 24px;
    border: 2px solid var(--accent-transparent);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 1rem;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .error-state button,
  .empty-state button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: var(--accent-transparent);
    color: var(--accent);
    border: none;
    border-radius: var(--border-radius);
    cursor: pointer;
    font-size: 0.9rem;
  }
  
  .similar-items-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .similar-item {
    display: flex;
    align-items: center;
    width: 100%;
    text-align: left;
    padding: 0.75rem;
    border: none;
    border-radius: var(--border-radius);
    background: none;
    cursor: pointer;
    transition: background 0.2s ease;
    margin-bottom: 0.5rem;
  }
  
  .similar-item:hover {
    background: var(--bg-hover);
  }
  
  .item-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: var(--accent-transparent);
    color: var(--accent);
    margin-right: 0.75rem;
    flex-shrink: 0;
  }
  
  .item-content {
    flex: 1;
    overflow: hidden;
  }
  
  .item-content h3 {
    font-size: 0.95rem;
    font-weight: 500;
    margin: 0 0 0.25rem 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--text-primary);
  }
  
  .item-excerpt {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  
  .similarity-score {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--accent);
    background: var(--accent-transparent);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    margin-left: 0.5rem;
  }

  @media (max-width: 768px) {
    .similar-items {
      width: 100%;
    }
  }
</style>
