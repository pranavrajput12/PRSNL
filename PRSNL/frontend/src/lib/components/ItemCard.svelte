<script lang="ts">
  import { goto } from '$app/navigation';
  import Icon from './Icon.svelte';
  import VideoPlayer from './VideoPlayer.svelte';
  import type { Item, TimelineItem } from '$lib/types/api';
  
  export let item: Item | TimelineItem;
  export let view: 'feed' | 'grid' | 'list' = 'feed';
  
  // Type guard to check if item has video properties
  function hasVideoProperties(item: any): item is TimelineItem {
    return item.itemType === 'video' || item.item_type === 'video';
  }
  
  // Normalize field names
  $: itemType = item.itemType || item.item_type || 'article';
  $: createdAt = item.createdAt || item.created_at;
  $: thumbnailUrl = item.thumbnailUrl || item.thumbnail_url;
  $: filePath = item.filePath || item.file_path;
  
  function handleClick() {
    goto(`/item/${item.id}`);
  }
  
  function formatDate(dateString: string) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString();
  }
</script>

<article 
  class="item-card view-{view}"
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  tabindex="0"
  role="button"
>
  <header class="item-header">
    <div class="item-meta">
      <Icon 
        name={itemType === 'video' ? 'video' : 'link'} 
        size="small" 
        color="var(--text-muted)" 
      />
      <time>{formatDate(createdAt)}</time>
      {#if item.platform}
        <span class="platform">{item.platform}</span>
      {/if}
    </div>
    {#if item.status === 'pending'}
      <div class="status-badge pending">
        Processing
      </div>
    {/if}
  </header>
  
  <div class="item-content">
    <h3>{item.title}</h3>
    
    {#if hasVideoProperties(item) && filePath}
      <div class="video-preview">
        <VideoPlayer
          src={`/api/videos/${item.id}/stream`}
          thumbnail={thumbnailUrl}
          title={item.title}
          duration={item.duration}
          compact={true}
        />
      </div>
    {/if}
    
    {#if item.summary}
      <p class="summary">{item.summary}</p>
    {/if}
    
    {#if item.tags && item.tags.length > 0}
      <div class="tags">
        {#each item.tags as tag}
          <span class="tag">{tag}</span>
        {/each}
      </div>
    {/if}
  </div>
  
  {#if item.url}
    <footer class="item-footer">
      <a 
        href={item.url} 
        target="_blank" 
        rel="noopener noreferrer"
        on:click|stopPropagation
        class="source-link"
      >
        <Icon name="external-link" size="small" />
        <span>View source</span>
      </a>
    </footer>
  {/if}
</article>

<style>
  .item-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
  }
  
  .item-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-color: var(--accent);
  }
  
  .item-card:focus {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
  
  .item-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--success));
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .item-card:hover::before {
    transform: translateX(0);
  }
  
  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .item-meta {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: var(--text-muted);
    font-size: 0.875rem;
  }
  
  .platform {
    padding: 0.125rem 0.5rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .status-badge.pending {
    background: var(--warning-bg);
    color: var(--warning);
  }
  
  .item-content h3 {
    margin: 0 0 0.75rem;
    font-size: 1.25rem;
    line-height: 1.4;
    color: var(--text-primary);
  }
  
  .video-preview {
    margin: 1rem -1.5rem;
    border-radius: 0;
    overflow: hidden;
  }
  
  .summary {
    color: var(--text-secondary);
    line-height: 1.6;
    margin: 0 0 1rem;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
  }
  
  .tag {
    padding: 0.25rem 0.625rem;
    background: var(--bg-tertiary);
    border-radius: 100px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-weight: 600;
    transition: all 0.2s ease;
  }
  
  .tag:hover {
    background: var(--accent);
    color: white;
  }
  
  .item-footer {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }
  
  .source-link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--accent);
    font-size: 0.875rem;
    font-weight: 600;
    transition: all 0.2s ease;
  }
  
  .source-link:hover {
    transform: translateX(2px);
  }
  
  /* View-specific styles */
  .view-grid .item-content h3 {
    font-size: 1.125rem;
  }
  
  .view-grid .summary {
    -webkit-line-clamp: 2;
  }
  
  .view-list {
    padding: 1rem;
  }
  
  .view-list .item-content {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .view-list .video-preview {
    display: none;
  }
</style>