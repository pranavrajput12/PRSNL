<!--
  Share Button Component
  
  Provides share functionality with native Web Share API fallback.
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  
  const dispatch = createEventDispatcher();
  
  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let variant: 'default' | 'outline' | 'ghost' = 'default';
  export let disabled = false;
  
  function handleShare() {
    dispatch('share');
  }
</script>

<button 
  class="share-button {variant} {size}"
  on:click={handleShare}
  {disabled}
  title="Share this content"
>
  <Icon name="share" size={size === 'large' ? 'medium' : 'small'} />
  <span class="share-text">Share</span>
</button>

<style>
  .share-button {
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
  
  .share-button:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    transform: translateY(-1px);
  }
  
  .share-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .share-text {
    font-size: 0.875rem;
  }
  
  /* Size variations */
  .share-button.small {
    padding: 0.5rem;
    gap: 0.25rem;
  }
  
  .share-button.small .share-text {
    font-size: 0.75rem;
  }
  
  .share-button.large {
    padding: 1rem 1.25rem;
    gap: 0.75rem;
  }
  
  .share-button.large .share-text {
    font-size: 1rem;
  }
  
  /* Variant styles */
  .share-button.outline {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
  }
  
  .share-button.ghost {
    background: transparent;
    border: none;
  }
  
  /* Mobile - hide text on small screens */
  @media (max-width: 768px) {
    .share-text {
      display: none;
    }
    
    .share-button {
      min-width: 44px;
      justify-content: center;
    }
  }
</style>