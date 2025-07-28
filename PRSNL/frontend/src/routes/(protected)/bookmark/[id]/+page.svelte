<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import { getItem, updateItem } from '$lib/api';
  import { formatDate } from '$lib/utils/date';
  import { extractDomain } from '$lib/utils/url';
  import type { Item } from '$lib/types/api';

  let item: Item | null = null;
  let loading = true;
  let error: string | null = null;
  let iframeError = false;
  let showPreview = true;
  let copyNotification = false;
  let bookmarkSaved = false;
  let activeView: 'preview' | 'content' | 'metadata' = 'preview';

  $: itemId = $page.params.id;
  $: domain = item?.url ? extractDomain(item.url) : '';
  $: favicon = item?.url ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : '';
  $: isBookmarked = item?.status === 'bookmark' || bookmarkSaved;
  $: hasActionableInsights = item?.metadata?.actionable_insights;
  
  onMount(() => {
    loadItem();
  });

  async function loadItem() {
    try {
      loading = true;
      error = null;
      item = await getItem(itemId);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load bookmark';
    } finally {
      loading = false;
    }
  }

  function handleIframeError() {
    iframeError = true;
    showPreview = false;
  }

  async function copyLink() {
    try {
      if (item?.url) {
        await navigator.clipboard.writeText(item.url);
        copyNotification = true;
        setTimeout(() => (copyNotification = false), 2000);
      }
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }

  async function toggleBookmark() {
    if (!item) return;
    
    try {
      const newStatus = isBookmarked ? 'pending' : 'bookmark';
      await updateItem(item.id, { status: newStatus });
      bookmarkSaved = !isBookmarked;
    } catch (err) {
      console.error('Failed to update bookmark status:', err);
    }
  }

  function share() {
    if (navigator.share && item?.url) {
      navigator.share({
        title: item.title,
        text: item.summary || '',
        url: item.url
      });
    }
  }

  function extractMetadata(item: Item) {
    const metadata = item.metadata || {};
    const extracted: Record<string, any> = {};
    
    // Common metadata fields
    const fields = [
      'author', 'publisher', 'date_published', 'reading_time',
      'word_count', 'language', 'keywords', 'description'
    ];
    
    fields.forEach(field => {
      if (metadata[field]) {
        extracted[field] = metadata[field];
      }
    });
    
    return extracted;
  }
</script>

<svelte:head>
  {#if item}
    <title>{item.title} - PRSNL Bookmark</title>
    <meta name="description" content={item.summary || ''} />
  {/if}
</svelte:head>

<div class="bookmark-container">
  {#if loading}
    <div class="loading-container">
      <Spinner size="large" />
    </div>
  {:else if error}
    <ErrorMessage message={error} />
  {:else if item}
    <div class="bookmark-content">
      <!-- Header -->
      <header class="bookmark-header">
        <div class="site-info">
          <img src={favicon} alt="{domain} favicon" class="favicon" on:error={(e) => e.target.style.display = 'none'} />
          <div class="site-details">
            <h1 class="bookmark-title">{item.title}</h1>
            <a href={item.url} target="_blank" rel="noopener noreferrer" class="original-link">
              {item.url}
              <Icon name="external-link" size={16} />
            </a>
          </div>
        </div>

        <div class="bookmark-actions">
          <button class="action-btn" on:click={toggleBookmark} class:bookmarked={isBookmarked}>
            <Icon name={isBookmarked ? 'bookmark-solid' : 'bookmark'} />
            <span>{isBookmarked ? 'Saved' : 'Save'}</span>
          </button>
          
          <button class="action-btn" on:click={copyLink} title="Copy link">
            <Icon name={copyNotification ? 'check' : 'link'} />
            <span>{copyNotification ? 'Copied!' : 'Copy'}</span>
          </button>
          
          <button class="action-btn" on:click={share} title="Share">
            <Icon name="share" />
            <span>Share</span>
          </button>
        </div>
      </header>

      <!-- View Tabs -->
      <div class="view-tabs">
        <button 
          class="tab" 
          class:active={activeView === 'preview'}
          on:click={() => activeView = 'preview'}
          disabled={iframeError}
        >
          <Icon name="globe" size={16} />
          Preview
        </button>
        <button 
          class="tab" 
          class:active={activeView === 'content'}
          on:click={() => activeView = 'content'}
        >
          <Icon name="file-text" size={16} />
          Content
        </button>
        <button 
          class="tab" 
          class:active={activeView === 'metadata'}
          on:click={() => activeView = 'metadata'}
        >
          <Icon name="info" size={16} />
          Metadata
        </button>
      </div>

      <!-- Content Area -->
      <div class="content-area">
        {#if activeView === 'preview' && showPreview && !iframeError}
          <div class="preview-container">
            <div class="preview-controls">
              <p class="preview-notice">
                <Icon name="info-circle" size={14} />
                Some websites may not allow embedding. 
                <a href={item.url} target="_blank" rel="noopener noreferrer">Open in new tab</a>
              </p>
            </div>
            <div class="iframe-wrapper">
              <iframe
                src={item.url}
                title="Website preview"
                frameborder="0"
                sandbox="allow-scripts allow-same-origin"
                on:error={handleIframeError}
              />
            </div>
          </div>
        {:else if activeView === 'content'}
          <div class="content-view">
            {#if item.summary}
              <section class="content-section">
                <h3>Summary</h3>
                <p>{item.summary}</p>
              </section>
            {/if}
            
            {#if hasActionableInsights}
              <section class="content-section actionable-insights">
                <h3>🎯 Actionable Insights</h3>
                
                {#if item.metadata.actionable_insights.tips?.length > 0}
                  <div class="insight-group">
                    <h4>💡 Tips</h4>
                    <ul class="insight-list">
                      {#each item.metadata.actionable_insights.tips as tip}
                        <li>{tip.content}</li>
                      {/each}
                    </ul>
                  </div>
                {/if}
                
                {#if item.metadata.actionable_insights.steps?.length > 0}
                  <div class="insight-group">
                    <h4>📋 Steps</h4>
                    <ol class="insight-list">
                      {#each item.metadata.actionable_insights.steps as step}
                        <li>{step.content}</li>
                      {/each}
                    </ol>
                  </div>
                {/if}
                
                {#if item.metadata.actionable_insights.methods?.length > 0}
                  <div class="insight-group">
                    <h4>🔧 Methods</h4>
                    <ul class="insight-list">
                      {#each item.metadata.actionable_insights.methods as method}
                        <li>{method.content}</li>
                      {/each}
                    </ul>
                  </div>
                {/if}
                
                {#if item.metadata.actionable_insights.takeaways?.length > 0}
                  <div class="insight-group">
                    <h4>🎯 Key Takeaways</h4>
                    <ul class="insight-list">
                      {#each item.metadata.actionable_insights.takeaways as takeaway}
                        <li>{takeaway.content}</li>
                      {/each}
                    </ul>
                  </div>
                {/if}
              </section>
            {/if}
            
            {#if item.content}
              <section class="content-section">
                <h3>Extracted Content</h3>
                <div class="extracted-content">
                  {@html item.content}
                </div>
              </section>
            {:else}
              <div class="no-content">
                <Icon name="file-text" size={48} />
                <p>No content extracted from this bookmark.</p>
                <a href={item.url} target="_blank" rel="noopener noreferrer" class="visit-link">
                  Visit website
                  <Icon name="external-link" size={16} />
                </a>
              </div>
            {/if}
          </div>
        {:else if activeView === 'metadata'}
          <div class="metadata-view">
            <section class="metadata-section">
              <h3>Basic Information</h3>
              <dl class="metadata-list">
                <dt>Domain</dt>
                <dd>{domain}</dd>
                
                <dt>Added</dt>
                <dd>{formatDate(item.created_at)}</dd>
                
                <dt>Last Updated</dt>
                <dd>{formatDate(item.updated_at)}</dd>
                
                <dt>Type</dt>
                <dd class="type-badge">{item.type}</dd>
                
                {#if item.platform}
                  <dt>Platform</dt>
                  <dd>{item.platform}</dd>
                {/if}
              </dl>
            </section>

            {#if item.tags && item.tags.length > 0}
              <section class="metadata-section">
                <h3>Tags</h3>
                <div class="tags">
                  {#each item.tags as tag}
                    <span class="tag">{tag}</span>
                  {/each}
                </div>
              </section>
            {/if}

            {#if Object.keys(extractMetadata(item)).length > 0}
              <section class="metadata-section">
                <h3>Additional Metadata</h3>
                <dl class="metadata-list">
                  {#each Object.entries(extractMetadata(item)) as [key, value]}
                    <dt>{key.replace(/_/g, ' ')}</dt>
                    <dd>{value}</dd>
                  {/each}
                </dl>
              </section>
            {/if}
          </div>
        {:else if iframeError}
          <div class="preview-error">
            <Icon name="alert-triangle" size={48} />
            <h3>Preview Unavailable</h3>
            <p>This website doesn't allow embedding.</p>
            <a href={item.url} target="_blank" rel="noopener noreferrer" class="visit-link">
              Open website in new tab
              <Icon name="external-link" size={16} />
            </a>
          </div>
        {/if}
      </div>

      <!-- Bottom Actions -->
      <div class="bottom-actions">
        <button class="btn-secondary" on:click={() => goto('/timeline')}>
          <Icon name="arrow-left" />
          Back to Timeline
        </button>
        
        <div class="right-actions">
          <button class="btn-secondary" on:click={() => goto(`/items/${itemId}/edit`)}>
            <Icon name="edit" />
            Edit
          </button>
          
          <a href={item.url} target="_blank" rel="noopener noreferrer" class="btn-primary">
            <Icon name="external-link" />
            Visit Website
          </a>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .bookmark-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
    min-height: 100vh;
  }

  .loading-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 50vh;
  }

  .bookmark-content {
    background: var(--color-surface);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
  }

  .bookmark-header {
    padding: 2rem;
    border-bottom: 1px solid var(--color-border);
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 2rem;
    flex-wrap: wrap;
  }

  .site-info {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    flex: 1;
    min-width: 0;
  }

  .favicon {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    flex-shrink: 0;
  }

  .site-details {
    flex: 1;
    min-width: 0;
  }

  .bookmark-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0 0 0.5rem;
    color: var(--color-text);
  }

  .original-link {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    color: var(--color-text-secondary);
    text-decoration: none;
    font-size: 0.875rem;
    word-break: break-all;
  }

  .original-link:hover {
    color: var(--color-primary);
  }

  .bookmark-actions {
    display: flex;
    gap: 0.5rem;
    flex-shrink: 0;
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    color: var(--color-text);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .action-btn:hover {
    background: var(--color-primary-light);
    border-color: var(--color-primary);
    color: var(--color-primary);
  }

  .action-btn.bookmarked {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  .view-tabs {
    display: flex;
    background: var(--color-background);
    border-bottom: 1px solid var(--color-border);
  }

  .tab {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 1rem;
    background: none;
    border: none;
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
  }

  .tab:hover:not(:disabled) {
    color: var(--color-text);
    background: var(--color-surface);
  }

  .tab.active {
    color: var(--color-primary);
  }

  .tab.active::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--color-primary);
  }

  .tab:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .content-area {
    min-height: 500px;
  }

  .preview-container {
    display: flex;
    flex-direction: column;
    height: 600px;
  }

  .preview-controls {
    padding: 1rem;
    background: var(--color-background);
    border-bottom: 1px solid var(--color-border);
  }

  .preview-notice {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--color-text-secondary);
    font-size: 0.875rem;
    margin: 0;
  }

  .preview-notice a {
    color: var(--color-primary);
    text-decoration: none;
  }

  .preview-notice a:hover {
    text-decoration: underline;
  }

  .iframe-wrapper {
    flex: 1;
    position: relative;
    background: var(--color-background);
  }

  iframe {
    width: 100%;
    height: 100%;
    border: none;
  }

  .preview-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
    color: var(--color-text-secondary);
  }

  .preview-error h3 {
    margin: 1rem 0 0.5rem;
    color: var(--color-text);
  }

  .visit-link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 1rem;
    padding: 0.75rem 1.5rem;
    background: var(--color-primary);
    color: white;
    text-decoration: none;
    border-radius: 8px;
    transition: background 0.2s ease;
  }

  .visit-link:hover {
    background: var(--color-primary-dark);
  }

  .content-view {
    padding: 2rem;
  }

  .content-section {
    margin-bottom: 2rem;
  }

  .content-section h3 {
    margin-bottom: 1rem;
    color: var(--color-text);
  }

  .extracted-content {
    line-height: 1.6;
    color: var(--color-text-secondary);
  }

  .extracted-content :global(*) {
    max-width: 100%;
  }

  .no-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
    color: var(--color-text-secondary);
  }

  .no-content p {
    margin: 1rem 0;
  }

  .metadata-view {
    padding: 2rem;
  }

  .metadata-section {
    margin-bottom: 2rem;
  }

  .metadata-section h3 {
    margin-bottom: 1rem;
    color: var(--color-text);
  }

  .metadata-list {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.5rem 1rem;
  }

  .metadata-list dt {
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .metadata-list dd {
    margin: 0;
    color: var(--color-text);
  }

  .type-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    background: var(--color-primary-light);
    color: var(--color-primary);
    border-radius: 20px;
    font-size: 0.875rem;
  }

  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tag {
    padding: 0.25rem 0.75rem;
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 20px;
    font-size: 0.875rem;
  }

  .actionable-insights {
    background: var(--color-background);
    padding: 1.5rem;
    border-radius: 8px;
  }

  .actionable-insights h3 {
    margin-bottom: 1rem;
  }

  .insight-group {
    margin-bottom: 1.5rem;
  }

  .insight-group:last-child {
    margin-bottom: 0;
  }

  .insight-group h4 {
    font-size: 1rem;
    margin-bottom: 0.5rem;
    color: var(--color-text);
  }

  .insight-list {
    margin: 0;
    padding-left: 1.5rem;
    color: var(--color-text-secondary);
  }

  .insight-list li {
    margin-bottom: 0.5rem;
    line-height: 1.6;
  }

  .insight-list li:last-child {
    margin-bottom: 0;
  }

  .bottom-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2rem;
    border-top: 1px solid var(--color-border);
    gap: 1rem;
    flex-wrap: wrap;
  }

  .right-actions {
    display: flex;
    gap: 0.5rem;
  }

  .btn-primary,
  .btn-secondary {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
    text-decoration: none;
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
  }

  .btn-primary:hover {
    background: var(--color-primary-dark);
  }

  .btn-secondary {
    background: var(--color-surface);
    color: var(--color-text);
    border: 1px solid var(--color-border);
  }

  .btn-secondary:hover {
    background: var(--color-background);
  }

  @media (max-width: 768px) {
    .bookmark-header {
      flex-direction: column;
      gap: 1rem;
    }

    .bookmark-actions {
      width: 100%;
      justify-content: stretch;
    }

    .action-btn {
      flex: 1;
    }

    .bottom-actions {
      flex-direction: column;
    }

    .right-actions {
      width: 100%;
    }

    .btn-primary,
    .btn-secondary {
      width: 100%;
      justify-content: center;
    }
  }
</style>