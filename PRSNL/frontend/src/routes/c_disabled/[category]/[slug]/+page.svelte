<script lang="ts">
  import { page } from '$app/stores';
  import type { PageData } from './$types';
  import Icon from '$lib/components/Icon.svelte';
  import UrlPreview from '$lib/components/UrlPreview.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import ItemCard from '$lib/components/ItemCard.svelte';

  export let data: PageData;

  $: ({ content, contentUrl, relatedContent, breadcrumbs, seo } = data);
  $: canonical = `${$page.url.origin}${seo.canonical}`;

  // Category configuration
  const categoryConfig = {
    dev: { color: '#00ff88', icon: 'code' },
    learn: { color: '#4a9eff', icon: 'book' },
    media: { color: '#f59e0b', icon: 'play' },
    ideas: { color: '#dc143c', icon: 'lightbulb' },
  };

  $: categoryInfo = categoryConfig[contentUrl.category] || categoryConfig.ideas;
</script>

<svelte:head>
  <title>{seo.title}</title>
  <meta name="description" content={seo.description} />
  <meta property="og:title" content={seo.title} />
  <meta property="og:description" content={seo.description} />
  <meta property="og:type" content={seo.type} />
  <meta property="og:url" content={canonical} />
  {#if seo.image}
    <meta property="og:image" content={seo.image} />
  {/if}
  <link rel="canonical" href={canonical} />
</svelte:head>

<div class="content-page">
  <!-- Breadcrumbs -->
  <nav class="breadcrumbs" aria-label="Breadcrumb navigation">
    <ol class="breadcrumb-list">
      {#each breadcrumbs as crumb, index}
        <li class="breadcrumb-item">
          {#if crumb.href && !crumb.active}
            <a href={crumb.href} class="breadcrumb-link">
              {crumb.label}
            </a>
          {:else}
            <span class="breadcrumb-current" aria-current="page">
              {crumb.label}
            </span>
          {/if}
          {#if index < breadcrumbs.length - 1}
            <span class="breadcrumb-separator" aria-hidden="true">></span>
          {/if}
        </li>
      {/each}
    </ol>
  </nav>

  <!-- Content Header -->
  <header class="content-header">
    <div class="content-meta">
      <span
        class="category-badge"
        style="color: {categoryInfo.color}; border-color: {categoryInfo.color};"
      >
        <Icon name={categoryInfo.icon} size="small" />
        {contentUrl.category}
      </span>
      <span class="view-count">{contentUrl.views || 0} views</span>
    </div>

    <h1 class="content-title">{content.title}</h1>

    {#if content.summary}
      <p class="content-summary">{content.summary}</p>
    {/if}

    <div class="content-actions">
      {#if content.url}
        <a href={content.url} target="_blank" rel="noopener noreferrer" class="btn-source">
          <Icon name="external-link" size="small" />
          View Source
        </a>
      {/if}

      <button
        class="btn-share"
        on:click={() => navigator.share?.({ url: canonical, title: content.title })}
      >
        <Icon name="share" size="small" />
        Share
      </button>
    </div>
  </header>

  <!-- Content Body -->
  <main class="content-main">
    {#if content.platform === 'youtube' || content.type === 'video'}
      <VideoPlayer
        videoUrl={content.video_url || content.url}
        title={content.title}
        thumbnail={content.thumbnail_url}
      />
    {:else if content.url}
      <UrlPreview url={content.url} title={content.title} />
    {/if}

    {#if content.processed_content || content.raw_content}
      <div class="content-body">
        <div class="content-text">
          {@html content.processed_content || content.raw_content}
        </div>
      </div>
    {/if}

    {#if content.transcription}
      <details class="transcription-section">
        <summary>
          <Icon name="file-text" size="small" />
          Transcription
        </summary>
        <div class="transcription-text">
          {content.transcription}
        </div>
      </details>
    {/if}
  </main>

  <!-- Related Content -->
  {#if relatedContent.length > 0}
    <aside class="related-content">
      <h2>Related Content</h2>
      <div class="related-grid">
        {#each relatedContent as item}
          <ItemCard {item} compact />
        {/each}
      </div>
    </aside>
  {/if}
</div>

<style>
  .content-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
    min-height: 100vh;
  }

  /* Breadcrumbs */
  .breadcrumbs {
    display: flex;
    align-items: center;
    margin-bottom: 2rem;
    padding: 0.75rem 1rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.875rem;
  }

  .breadcrumb-list {
    display: flex;
    align-items: center;
    list-style: none;
    margin: 0;
    padding: 0;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .breadcrumb-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .breadcrumb-link {
    color: var(--success);
    text-decoration: none;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    transition: all 0.2s ease;
  }

  .breadcrumb-link:hover {
    color: var(--brand-accent);
    background: rgba(0, 255, 136, 0.1);
  }

  .breadcrumb-current {
    color: #fff;
    font-weight: 600;
    padding: 0.25rem 0.5rem;
  }

  .breadcrumb-separator {
    color: rgba(255, 255, 255, 0.4);
    margin: 0 0.125rem;
  }

  /* Content Header */
  .content-header {
    margin-bottom: 2rem;
  }

  .content-meta {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .category-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.75rem;
    border: 1px solid;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
    text-transform: capitalize;
  }

  .view-count {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.875rem;
  }

  .content-title {
    font-size: 2.5rem;
    font-weight: 600;
    line-height: 1.2;
    margin-bottom: 1rem;
    color: #fff;
  }

  .content-summary {
    font-size: 1.125rem;
    line-height: 1.6;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 1.5rem;
  }

  .content-actions {
    display: flex;
    gap: 1rem;
  }

  .btn-source,
  .btn-share {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border: 1px solid var(--success);
    border-radius: 6px;
    background: transparent;
    color: var(--success);
    text-decoration: none;
    font-weight: 500;
    transition: all 0.2s ease;
    cursor: pointer;
  }

  .btn-source:hover,
  .btn-share:hover {
    background: var(--success);
    color: #000;
    transform: translateY(-1px);
  }

  /* Content Body */
  .content-main {
    margin-bottom: 3rem;
  }

  .content-body {
    margin-top: 2rem;
  }

  .content-text {
    line-height: 1.7;
    color: rgba(255, 255, 255, 0.9);
  }

  .content-text :global(h1),
  .content-text :global(h2),
  .content-text :global(h3) {
    color: #fff;
    margin-top: 2rem;
    margin-bottom: 1rem;
  }

  .content-text :global(p) {
    margin-bottom: 1rem;
  }

  .content-text :global(code) {
    background: rgba(0, 255, 136, 0.1);
    padding: 0.125rem 0.25rem;
    border-radius: 3px;
    font-family: 'JetBrains Mono', monospace;
  }

  .content-text :global(pre) {
    background: rgba(0, 0, 0, 0.4);
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid rgba(0, 255, 136, 0.2);
    overflow-x: auto;
    margin: 1rem 0;
  }

  /* Transcription */
  .transcription-section {
    margin-top: 2rem;
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.3);
  }

  .transcription-section summary {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    cursor: pointer;
    font-weight: 500;
    color: var(--success);
  }

  .transcription-text {
    padding: 0 1rem 1rem;
    line-height: 1.6;
    color: rgba(255, 255, 255, 0.8);
    border-top: 1px solid rgba(0, 255, 136, 0.1);
  }

  /* Related Content */
  .related-content {
    border-top: 1px solid rgba(0, 255, 136, 0.2);
    padding-top: 2rem;
  }

  .related-content h2 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: #fff;
  }

  .related-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .content-page {
      padding: 0.5rem;
    }

    .content-title {
      font-size: 2rem;
    }

    .breadcrumbs {
      font-size: 0.75rem;
      padding: 0.5rem 0.75rem;
    }

    .content-actions {
      flex-direction: column;
    }

    .related-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
