<!--
  Bookmark Button Component
  
  Allows users to bookmark/unbookmark content items.
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  
  const dispatch = createEventDispatcher();
  
  export let itemId: string;
  export let bookmarked = false;
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let disabled = false;
  
  let loading = false;
  
  async function toggleBookmark() {
    if (loading || disabled) return;
    
    loading = true;
    try {
      // TODO: Implement actual bookmark API call
      console.log('Toggle bookmark for item:', itemId);
      bookmarked = !bookmarked;
      
      dispatch('bookmark', {
        itemId,
        bookmarked
      });
    } catch (error) {
      console.error('Failed to toggle bookmark:', error);
    } finally {
      loading = false;
    }
  }
</script>

<button 
  class="bookmark-button {size} {bookmarked ? 'bookmarked' : ''}"
  on:click={toggleBookmark}
  disabled={disabled || loading}
  title={bookmarked ? 'Remove bookmark' : 'Add bookmark'}
>
  {#if loading}
    <div class="loading-spinner"></div>
  {:else}
    <Icon name={bookmarked ? 'bookmark-check' : 'bookmark'} size={size === 'large' ? 'medium' : 'small'} />
  {/if}
  <span class="bookmark-text">
    {bookmarked ? 'Bookmarked' : 'Bookmark'}
  </span>
</button>

<style>
  .bookmark-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    color: var(--text-secondary);
    cursor: pointer;
    font-family: inherit;
    font-weight: 500;
    transition: all 0.2s;
  }
  
  .bookmark-button:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    transform: translateY(-1px);
  }
  
  .bookmark-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .bookmark-button.bookmarked {
    background: rgba(220, 20, 60, 0.2);
    border-color: rgba(220, 20, 60, 0.3);
    color: #dc143c;
  }
  
  .bookmark-button.bookmarked:hover:not(:disabled) {
    background: rgba(220, 20, 60, 0.3);
    color: #dc143c;
  }
  
  .bookmark-text {
    font-size: 0.875rem;
  }
  
  /* Size variations */
  .bookmark-button.small {
    padding: 0.5rem;
    gap: 0.25rem;
  }
  
  .bookmark-button.small .bookmark-text {
    font-size: 0.75rem;
  }
  
  .bookmark-button.large {
    padding: 1rem 1.25rem;
    gap: 0.75rem;
  }
  
  .bookmark-button.large .bookmark-text {
    font-size: 1rem;
  }
  
  /* Loading spinner */
  .loading-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  /* Mobile - hide text on small screens */
  @media (max-width: 768px) {
    .bookmark-text {
      display: none;
    }
    
    .bookmark-button {
      min-width: 44px;
      justify-content: center;
    }
  }
</style>