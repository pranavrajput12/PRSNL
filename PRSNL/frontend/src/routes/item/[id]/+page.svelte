<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  
  let item: any = null;
  let isLoading = true;
  let error: Error | null = null;
  let isEditing = false;
  let editTitle = '';
  let editSummary = '';
  let editTags = '';
  
  $: itemId = $page.params.id;
  
  onMount(() => {
    loadItem();
  });
  
  async function loadItem() {
    isLoading = true;
    error = null;
    
    try {
      const response = await fetch(`/api/items/${itemId}`);
      if (!response.ok) {
        throw new Error('Item not found');
      }
      
      item = await response.json();
      editTitle = item.title;
      editSummary = item.summary || '';
      editTags = item.tags?.join(', ') || '';
    } catch (e) {
      error = e as Error;
    } finally {
      isLoading = false;
    }
  }
  
  async function saveChanges() {
    try {
      const response = await fetch(`/api/items/${itemId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: editTitle,
          summary: editSummary,
          tags: editTags.split(',').map(t => t.trim()).filter(t => t)
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to update item');
      }
      
      item = await response.json();
      isEditing = false;
    } catch (e) {
      alert('Failed to save changes');
    }
  }
  
  async function deleteItem() {
    if (!confirm('Are you sure you want to delete this item?')) {
      return;
    }
    
    try {
      const response = await fetch(`/api/items/${itemId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete item');
      }
      
      goto('/timeline');
    } catch (e) {
      alert('Failed to delete item');
    }
  }
  
  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
</script>

<svelte:head>
  <title>{item?.title || 'Loading...'} - PRSNL</title>
</svelte:head>

<div class="container">
  {#if isLoading}
    <div class="loading">
      <Spinner size="large" />
    </div>
  {:else if error}
    <ErrorMessage 
      message="Failed to load item" 
      details={error.message}
      retry={loadItem}
    />
  {:else if item}
    <div class="item-detail">
      <div class="item-header">
        {#if isEditing}
          <input 
            type="text" 
            bind:value={editTitle}
            class="edit-title"
            placeholder="Item title..."
          />
        {:else}
          <h1>{item.title}</h1>
        {/if}
        
        <div class="actions">
          {#if isEditing}
            <button class="btn-primary" on:click={saveChanges}>
              <Icon name="check" size="small" />
              Save
            </button>
            <button class="btn-ghost" on:click={() => isEditing = false}>
              <Icon name="close" size="small" />
              Cancel
            </button>
          {:else}
            <button class="btn-ghost" on:click={() => isEditing = true}>
              <Icon name="edit" size="small" />
              Edit
            </button>
            <button class="btn-ghost delete" on:click={deleteItem}>
              <Icon name="trash" size="small" />
              Delete
            </button>
          {/if}
        </div>
      </div>
      
      <div class="item-meta">
        <div class="meta-item">
          <Icon name="calendar" size="small" />
          {formatDate(item.created_at)}
        </div>
        
        {#if item.platform}
          <div class="meta-item">
            <Icon name="video" size="small" />
            {item.platform}
          </div>
        {/if}
        
        {#if item.item_type}
          <div class="meta-item type-{item.item_type}">
            <Icon name={item.item_type === 'video' ? 'video' : 'link'} size="small" />
            {item.item_type}
          </div>
        {/if}
      </div>
      
      {#if item.item_type === 'video' && item.file_path}
        <div class="video-container">
          <VideoPlayer 
            src={`/api/videos/${item.id}/stream`}
            thumbnail={item.thumbnail_url}
            title={item.title}
            duration={item.duration}
            platform={item.platform}
          />
        </div>
      {/if}
      
      <div class="content-section">
        <h2>Summary</h2>
        {#if isEditing}
          <textarea 
            bind:value={editSummary}
            class="edit-summary"
            placeholder="Add a summary..."
            rows="4"
          />
        {:else}
          <p>{item.summary || 'No summary available'}</p>
        {/if}
      </div>
      
      {#if item.url}
        <div class="content-section">
          <h2>Source</h2>
          <a href={item.url} target="_blank" rel="noopener noreferrer" class="source-link">
            <Icon name="external-link" size="small" />
            {item.url}
          </a>
        </div>
      {/if}
      
      <div class="content-section">
        <h2>Tags</h2>
        {#if isEditing}
          <input 
            type="text"
            bind:value={editTags}
            class="edit-tags"
            placeholder="Add tags separated by commas..."
          />
        {:else}
          <div class="tags">
            {#if item.tags && item.tags.length > 0}
              {#each item.tags as tag}
                <span class="tag">{tag}</span>
              {/each}
            {:else}
              <span class="no-tags">No tags</span>
            {/if}
          </div>
        {/if}
      </div>
      
      {#if item.metadata}
        <div class="content-section">
          <h2>Additional Information</h2>
          <div class="metadata">
            {#if item.metadata.video_metadata}
              <div class="meta-group">
                <h3>Video Details</h3>
                <dl>
                  {#if item.metadata.video_metadata.width}
                    <dt>Resolution</dt>
                    <dd>{item.metadata.video_metadata.width}x{item.metadata.video_metadata.height}</dd>
                  {/if}
                  {#if item.metadata.video_metadata.view_count}
                    <dt>Views</dt>
                    <dd>{item.metadata.video_metadata.view_count.toLocaleString()}</dd>
                  {/if}
                  {#if item.metadata.video_metadata.uploader}
                    <dt>Uploader</dt>
                    <dd>{item.metadata.video_metadata.uploader}</dd>
                  {/if}
                </dl>
              </div>
            {/if}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .loading {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 50vh;
  }
  
  .item-detail {
    background: var(--bg-secondary);
    border-radius: var(--radius);
    padding: 2rem;
    animation: fadeIn var(--transition-slow) ease-out;
  }
  
  .item-header {
    display: flex;
    align-items: start;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    gap: 2rem;
  }
  
  .item-header h1 {
    margin: 0;
    font-size: 2rem;
    line-height: 1.3;
  }
  
  .actions {
    display: flex;
    gap: 0.5rem;
    flex-shrink: 0;
  }
  
  .btn-primary, .btn-ghost {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: var(--radius);
    font-weight: 600;
    transition: all var(--transition-base);
    cursor: pointer;
    border: none;
    font-size: 0.875rem;
  }
  
  .btn-primary {
    background: var(--accent);
    color: white;
  }
  
  .btn-primary:hover {
    background: var(--accent-hover);
  }
  
  .btn-ghost {
    background: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border);
  }
  
  .btn-ghost:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  .btn-ghost.delete:hover {
    background: rgba(255, 100, 100, 0.1);
    color: var(--error);
    border-color: var(--error);
  }
  
  .item-meta {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
  
  .meta-item.type-video {
    color: var(--man-united-red);
  }
  
  .video-container {
    margin: 2rem 0;
    max-width: 800px;
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  }
  
  .content-section {
    margin: 2rem 0;
  }
  
  .content-section h2 {
    font-size: 1.25rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
  }
  
  .content-section p {
    color: var(--text-secondary);
    line-height: 1.6;
  }
  
  .source-link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--accent);
    text-decoration: none;
    transition: color var(--transition-fast);
  }
  
  .source-link:hover {
    color: var(--accent-hover);
    text-decoration: underline;
  }
  
  .tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .tag {
    padding: 0.25rem 0.75rem;
    background: var(--bg-tertiary);
    border-radius: 1rem;
    font-size: 0.875rem;
    color: var(--text-primary);
  }
  
  .no-tags {
    color: var(--text-muted);
    font-style: italic;
  }
  
  .metadata {
    background: var(--bg-tertiary);
    padding: 1.5rem;
    border-radius: var(--radius);
  }
  
  .meta-group h3 {
    font-size: 1rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
  }
  
  dl {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 0.5rem 1rem;
    margin: 0;
  }
  
  dt {
    color: var(--text-muted);
    font-weight: 600;
  }
  
  dd {
    color: var(--text-secondary);
    margin: 0;
  }
  
  /* Edit mode styles */
  .edit-title {
    width: 100%;
    font-size: 2rem;
    font-weight: bold;
    background: transparent;
    border: 2px solid var(--border);
    border-radius: var(--radius);
    padding: 0.5rem 1rem;
    color: var(--text-primary);
  }
  
  .edit-summary {
    width: 100%;
    background: var(--bg-tertiary);
    border: 2px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    color: var(--text-primary);
    resize: vertical;
  }
  
  .edit-tags {
    width: 100%;
    background: var(--bg-tertiary);
    border: 2px solid var(--border);
    border-radius: var(--radius);
    padding: 0.5rem 1rem;
    color: var(--text-primary);
  }
  
  .edit-title:focus, .edit-summary:focus, .edit-tags:focus {
    outline: none;
    border-color: var(--accent);
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @media (max-width: 768px) {
    .container {
      padding: 1rem;
    }
    
    .item-detail {
      padding: 1.5rem;
    }
    
    .item-header {
      flex-direction: column;
      gap: 1rem;
    }
    
    .actions {
      width: 100%;
      justify-content: flex-start;
    }
    
    .item-meta {
      gap: 1rem;
    }
  }
</style>