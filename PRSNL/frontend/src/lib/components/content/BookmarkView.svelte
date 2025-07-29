<!--
  Bookmark View Component
  Basic implementation for bookmark content display
-->

<script lang="ts">
  import Icon from '$lib/components/Icon.svelte';
  import GenericItemView from './GenericItemView.svelte';
  
  export let item: any;
  export let contentType: any;
  
  $: domain = item.url ? new URL(item.url).hostname : '';
  $: favicon = item.url ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : '';
</script>

<div class="bookmark-view">
  {#if item.url}
    <section class="bookmark-preview">
      <div class="preview-header">
        <img src={favicon} alt="{domain} favicon" class="favicon" />
        <div class="preview-info">
          <h3>Bookmark Preview</h3>
          <a href={item.url} target="_blank" rel="noopener noreferrer" class="bookmark-url">
            {item.url}
          </a>
        </div>
        <a href={item.url} target="_blank" rel="noopener noreferrer" class="visit-btn">
          <Icon name="external-link" size="small" />
          Visit Site
        </a>
      </div>
    </section>
  {/if}
  
  <!-- Use generic view for the rest -->
  <GenericItemView {item} {contentType} on:error />
</div>

<style>
  .bookmark-view {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  .bookmark-preview {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
  }
  
  .preview-header {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .favicon {
    width: 32px;
    height: 32px;
    border-radius: 4px;
  }
  
  .preview-info {
    flex: 1;
  }
  
  .preview-info h3 {
    margin: 0 0 0.25rem 0;
    color: var(--neural-green);
    font-size: 1.1rem;
  }
  
  .bookmark-url {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.9rem;
    word-break: break-all;
  }
  
  .bookmark-url:hover {
    color: var(--text-primary);
  }
  
  .visit-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--neural-green);
    color: #000;
    text-decoration: none;
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.2s;
  }
  
  .visit-btn:hover {
    background: #00cc52;
    transform: translateY(-1px);
  }
</style>