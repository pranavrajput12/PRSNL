<script lang="ts">
  import { goto } from '$app/navigation';
  import Icon from './Icon.svelte';
  import VideoPlayer from './VideoPlayer.svelte';
  import TagList from './TagList.svelte';
  import { aiApi } from '$lib/api';
  import type { Item, TimelineItem } from '$lib/types/api';
  import { getTypeIcon } from '$lib/stores/contentTypes';

  export let item: Item | TimelineItem;
  export let view: 'feed' | 'grid' | 'list' = 'feed';
  export let showAiActions: boolean = true;

  // Type guard to check if item has video properties
  function hasVideoProperties(item: any): item is TimelineItem {
    const type = item.type || item.itemType || item.item_type;
    return type === 'video';
  }

  // Normalize field names
  $: itemType = item.type || item.itemType || item.item_type || 'article';
  $: createdAt = item.createdAt || item.created_at;
  $: thumbnailUrl = item.thumbnailUrl || item.thumbnail_url;
  $: filePath = item.filePath || item.file_path;
  $: category = item.category || item.metadata?.category;
  $: confidence = item.confidence || item.metadata?.confidence || 1;
  $: aiProcessed = item.ai_processed || item.metadata?.ai_processed || false;

  // Track if embeddings are available for "Find Similar" feature
  $: embeddingsAvailable = item.metadata?.embedding !== undefined;

  let categorizeLoading = false;
  let summarizeLoading = false;
  let findSimilarLoading = false;
  let transcriptLoading = false;

  function handleClick() {
    // Use the new permalink URL if available, fallback to old format
    const targetUrl = item.permalink || `/item/${item.id}`;
    goto(targetUrl);
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

  // AI Action handlers
  async function categorize(e: MouseEvent) {
    e.stopPropagation();
    categorizeLoading = true;
    try {
      await aiApi.categorize.single(item.id);
      window.location.reload(); // Refresh to show new category
    } catch (err) {
      console.error('Failed to categorize item:', err);
    } finally {
      categorizeLoading = false;
    }
  }

  async function summarize(e: MouseEvent) {
    e.stopPropagation();
    summarizeLoading = true;
    try {
      await aiApi.summarization.item(item.id, 'brief');
      window.location.reload(); // Refresh to show summary
    } catch (err) {
      console.error('Failed to summarize item:', err);
    } finally {
      summarizeLoading = false;
    }
  }

  async function findSimilar(e: MouseEvent) {
    e.stopPropagation();
    findSimilarLoading = true;
    try {
      goto(`/similar/${item.id}`);
    } catch (err) {
      console.error('Failed to find similar items:', err);
      findSimilarLoading = false;
    }
  }

  async function generateTranscript(e: MouseEvent) {
    e.stopPropagation();
    transcriptLoading = true;
    try {
      const response = await fetch(`/api/video-streaming/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ item_id: item.id }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate transcript');
      }

      window.location.reload(); // Refresh to show transcript
    } catch (err) {
      console.error('Failed to generate transcript:', err);
      alert('Failed to generate transcript. The video might not have captions available.');
    } finally {
      transcriptLoading = false;
    }
  }

  // Check if item is a video and doesn't have transcript
  $: isVideo = itemType === 'video';
  $: hasTranscript = item.transcription && item.transcription.length > 0;
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
      <Icon name={getTypeIcon(itemType)} size="small" color="var(--text-muted)" />
      <time>{formatDate(createdAt)}</time>
      {#if item.platform}
        <span class="platform">{item.platform}</span>
      {/if}

      <!-- AI Processed Indicator -->
      {#if aiProcessed}
        <span class="ai-badge">✨ AI Enhanced</span>
      {/if}

      <!-- Category with confidence indicator -->
      {#if category}
        <span
          class="category-badge"
          style="opacity: {confidence}; background-color: {confidence > 0.7
            ? 'var(--ai-success)'
            : confidence > 0.4
              ? 'var(--ai-warning)'
              : 'var(--ai-error)'}"
        >
          {category}
        </span>
      {/if}
    </div>

    {#if item.status === 'pending'}
      <div class="status-badge pending">Processing</div>
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

    <TagList tags={item.tags} itemId={item.id} />
  </div>

  <footer class="item-footer">
    {#if item.url}
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
    {/if}

    <!-- AI Action Buttons -->
    {#if showAiActions}
      <div class="ai-actions">
        <button
          class="ai-action-btn"
          class:loading={categorizeLoading}
          disabled={categorizeLoading}
          on:click={categorize}
        >
          <Icon name="tag" size="small" />
          <span>Categorize</span>
          {#if categorizeLoading}<span class="loading-spinner"></span>{/if}
        </button>

        <button
          class="ai-action-btn"
          class:loading={summarizeLoading}
          disabled={summarizeLoading}
          on:click={summarize}
        >
          <Icon name="file-text" size="small" />
          <span>Summarize</span>
          {#if summarizeLoading}<span class="loading-spinner"></span>{/if}
        </button>

        {#if embeddingsAvailable}
          <button
            class="ai-action-btn"
            class:loading={findSimilarLoading}
            disabled={findSimilarLoading}
            on:click={findSimilar}
          >
            <Icon name="search" size="small" />
            <span>Find Similar</span>
            {#if findSimilarLoading}<span class="loading-spinner"></span>{/if}
          </button>
        {/if}

        {#if isVideo && !hasTranscript}
          <button
            class="ai-action-btn transcript-btn"
            class:loading={transcriptLoading}
            disabled={transcriptLoading}
            on:click={generateTranscript}
            title="Generate transcript for this video"
          >
            <Icon name="file-text" size="small" />
            <span>Generate Transcript</span>
            {#if transcriptLoading}<span class="loading-spinner"></span>{/if}
          </button>
        {/if}
      </div>
    {/if}
  </footer>
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
  /* AI-specific styles */
  .ai-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.125rem 0.5rem;
    background: var(--ai-accent-light, rgba(79, 70, 229, 0.1));
    border: 1px solid var(--ai-accent, #4f46e5);
    color: var(--ai-accent, #4f46e5);
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
  }

  .category-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.125rem 0.5rem;
    background-color: var(--ai-success-light, rgba(16, 185, 129, 0.1));
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--ai-success, #10b981);
    margin-left: 0.5rem;
  }

  .ai-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-top: 1rem;
  }

  .ai-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.75rem;
    background-color: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
  }

  .ai-action-btn:hover {
    background-color: var(--ai-accent-light, rgba(79, 70, 229, 0.1));
    border-color: var(--ai-accent, #4f46e5);
    color: var(--ai-accent, #4f46e5);
  }

  .ai-action-btn:active {
    transform: translateY(1px);
  }

  .ai-action-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .loading-spinner {
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: var(--ai-accent, #4f46e5);
    animation: spin 1s linear infinite;
    margin-left: 0.375rem;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* View-specific styles for AI features */
  .view-grid .ai-actions {
    flex-direction: column;
    gap: 0.5rem;
  }

  .view-list .ai-actions {
    flex-direction: row;
    gap: 0.5rem;
    margin-top: 0;
    margin-left: auto;
  }

  /* For mobile responsiveness */
  @media (max-width: 640px) {
    .ai-actions {
      flex-direction: column;
      gap: 0.5rem;
    }
  }

  .transcript-btn {
    background-color: var(--bg-tertiary);
    border-color: var(--accent-red, #dc1430);
    color: var(--accent-red, #dc1430);
  }

  .transcript-btn:hover {
    background-color: rgba(220, 20, 48, 0.1);
    border-color: var(--accent-red, #dc1430);
    color: var(--accent-red, #dc1430);
  }
</style>
