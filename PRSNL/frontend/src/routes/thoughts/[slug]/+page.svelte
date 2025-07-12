<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import KnowledgeCard from '$lib/components/KnowledgeCard.svelte';
  import AsyncBoundary from '$lib/components/AsyncBoundary.svelte';
  import SafeHTML from '$lib/components/SafeHTML.svelte';
  import MarkdownViewer from '$lib/components/development/MarkdownViewer.svelte';
  import GitHubRepoCard from '$lib/components/development/GitHubRepoCard.svelte';
  import type { Item } from '$lib/types/api';
  import { getItem } from '$lib/api';

  let item: Item | null = null;
  let isLoading = true;
  let error: Error | null = null;
  let activeTab = 'overview';
  let showQuickActions = false;
  let copyNotification = false;

  $: slug = $page.params.slug;
  $: isDevelopment = item?.type === 'development';
  $: hasRichPreview = item?.metadata?.rich_preview && item.metadata.rich_preview.type !== 'error';
  $: githubData = hasRichPreview ? item?.metadata?.rich_preview : null;

  async function loadItem() {
    if (!slug) return;
    
    try {
      isLoading = true;
      error = null;
      
      // Try to get item by slug first, fallback to ID if slug is numeric
      const isNumericId = /^\d+$/.test(slug);
      const response = await getItem(slug);
      
      if (response.success) {
        item = response.data;
        
        // If accessed by numeric ID but item has a proper slug, redirect
        if (isNumericId && item.slug && item.slug !== slug) {
          goto(`/thoughts/${item.slug}`, { replaceState: true });
          return;
        }
      } else {
        throw new Error(response.error || 'Failed to load thought');
      }
    } catch (err) {
      console.error('Error loading thought:', err);
      error = err as Error;
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadItem();
  });

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      copyNotification = true;
      setTimeout(() => copyNotification = false, 2000);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long', 
      day: 'numeric'
    });
  }
</script>

<svelte:head>
  {#if item}
    <title>{item.title || 'Thought'} - PRSNL</title>
    <meta name="description" content={item.summary || item.content?.substring(0, 160) || 'Personal knowledge thought'} />
    <meta property="og:title" content={item.title || 'Thought'} />
    <meta property="og:description" content={item.summary || item.content?.substring(0, 160) || 'Personal knowledge thought'} />
    <meta property="og:url" content={`/thoughts/${slug}`} />
    {#if item.thumbnail_url}
      <meta property="og:image" content={item.thumbnail_url} />
    {/if}
  {/if}
</svelte:head>

<div class="thought-container">
  {#if copyNotification}
    <div class="copy-notification">
      <Icon name="check" size={16} />
      Link copied to clipboard!
    </div>
  {/if}

  {#if isLoading}
    <div class="loading-container">
      <Spinner />
      <p>Loading thought...</p>
    </div>
  {:else if error}
    <ErrorMessage message={error.message} />
    <div class="error-actions">
      <button on:click={() => goto('/timeline')} class="btn-secondary">
        <Icon name="arrow-left" size={16} />
        Back to Timeline
      </button>
      <button on:click={loadItem} class="btn-primary">
        <Icon name="refresh-cw" size={16} />
        Try Again
      </button>
    </div>
  {:else if item}
    <article class="thought-article">
      <header class="thought-header">
        <div class="thought-meta">
          <span class="thought-type">{item.type}</span>
          <span class="thought-date">{formatDate(item.created_at)}</span>
        </div>
        
        <h1 class="thought-title">{item.title || 'Untitled Thought'}</h1>
        
        {#if item.summary}
          <p class="thought-summary">{item.summary}</p>
        {/if}

        <div class="thought-actions">
          <button on:click={copyLink} class="action-btn" title="Copy link">
            <Icon name="link" size={16} />
          </button>
          <button on:click={() => showQuickActions = !showQuickActions} class="action-btn" title="More actions">
            <Icon name="more-horizontal" size={16} />
          </button>
        </div>
      </header>

      <div class="thought-content">
        {#if isDevelopment && githubData}
          <GitHubRepoCard data={githubData} />
        {/if}

        {#if item.content_type === 'markdown'}
          <MarkdownViewer content={item.content || ''} />
        {:else}
          <SafeHTML html={item.content || ''} />
        {/if}

        {#if item.video_url}
          <VideoPlayer src={item.video_url} thumbnail={item.thumbnail_url} />
        {/if}
      </div>

      {#if item.tags && item.tags.length > 0}
        <div class="thought-tags">
          {#each item.tags as tag}
            <span class="tag" role="button" tabindex="0" 
                  on:click={() => goto(`/search?q=tag:${tag}`)}
                  on:keydown={(e) => e.key === 'Enter' && goto(`/search?q=tag:${tag}`)}>
              #{tag}
            </span>
          {/each}
        </div>
      {/if}
    </article>

    <aside class="thought-sidebar">
      <KnowledgeCard {item} />
    </aside>
  {/if}
</div>

<style>
  .thought-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 2rem;
  }

  .copy-notification {
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: var(--success-color);
    color: white;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    z-index: 1000;
    animation: slideIn 0.3s ease-out;
  }

  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 4rem;
  }

  .thought-article {
    min-width: 0;
  }

  .thought-header {
    margin-bottom: 2rem;
    position: relative;
  }

  .thought-meta {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .thought-type {
    background: var(--accent);
    color: var(--accent-text);
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    text-transform: capitalize;
  }

  .thought-title {
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 1rem;
    color: var(--text-primary);
  }

  .thought-summary {
    font-size: 1.25rem;
    color: var(--text-secondary);
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }

  .thought-actions {
    position: absolute;
    top: 0;
    right: 0;
    display: flex;
    gap: 0.5rem;
  }

  .action-btn {
    background: var(--background-secondary);
    border: 1px solid var(--border);
    border-radius: 0.375rem;
    padding: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .action-btn:hover {
    background: var(--background-tertiary);
  }

  .thought-content {
    line-height: 1.7;
    color: var(--text-primary);
  }

  .thought-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border);
  }

  .tag {
    background: var(--background-secondary);
    color: var(--text-secondary);
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .tag:hover {
    background: var(--accent);
    color: var(--accent-text);
  }

  .thought-sidebar {
    position: sticky;
    top: 2rem;
    height: fit-content;
  }

  .error-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }

  @media (max-width: 768px) {
    .thought-container {
      grid-template-columns: 1fr;
      padding: 1rem;
    }
    
    .thought-title {
      font-size: 2rem;
    }
    
    .thought-actions {
      position: static;
      margin-top: 1rem;
    }
  }

  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
</style>
