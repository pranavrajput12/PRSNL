<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import MarkdownViewer from '$lib/components/development/MarkdownViewer.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import { getItem } from '$lib/api';
  import { formatDate } from '$lib/utils/date';
  import type { Item } from '$lib/types/api';

  let item: Item | null = null;
  let loading = true;
  let error: string | null = null;
  let readingProgress = 0;
  let showTableOfContents = false;
  let headings: Array<{text: string, level: number, id: string}> = [];
  let copyNotification = false;

  $: itemId = $page.params.id;
  $: readingTime = Math.ceil((item?.content || '').split(/\s+/).length / 200);
  $: wordCount = (item?.content || '').split(/\s+/).length;
  $: hasAIAnalysis = item?.metadata?.ai_analysis;
  $: hasActionableInsights = item?.metadata?.actionable_insights;

  onMount(() => {
    loadItem();
    handleScroll();
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  });

  async function loadItem() {
    try {
      loading = true;
      error = null;
      item = await getItem(itemId);
      extractHeadings();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load article';
    } finally {
      loading = false;
    }
  }

  function extractHeadings() {
    if (!item?.content) return;
    
    const matches = item.content.matchAll(/^(#{1,6})\s+(.+)$/gm);
    headings = Array.from(matches).map((match, index) => ({
      level: match[1].length,
      text: match[2],
      id: `heading-${index}`
    }));
    
    showTableOfContents = headings.length > 3;
  }

  function handleScroll() {
    const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    readingProgress = (winScroll / height) * 100;
  }

  function scrollToHeading(id: string) {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      copyNotification = true;
      setTimeout(() => (copyNotification = false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }

  function share() {
    if (navigator.share && item) {
      navigator.share({
        title: item.title,
        text: item.summary || '',
        url: window.location.href
      });
    }
  }
</script>

<svelte:head>
  {#if item}
    <title>{item.title} - PRSNL</title>
    <meta name="description" content={item.summary || ''} />
  {/if}
</svelte:head>

<!-- Reading Progress Bar -->
<div class="reading-progress" style="width: {readingProgress}%"></div>

<div class="article-container">
  {#if loading}
    <div class="loading-container">
      <Spinner size="large" />
    </div>
  {:else if error}
    <ErrorMessage message={error} />
  {:else if item}
    <article class="article-content">
      <!-- Article Header -->
      <header class="article-header">
        <div class="article-meta">
          <time datetime={item.created_at}>
            {formatDate(item.created_at)}
          </time>
          <span class="separator">•</span>
          <span class="reading-time">
            <Icon name="clock" size={14} />
            {readingTime} min read
          </span>
          <span class="separator">•</span>
          <span class="word-count">{wordCount.toLocaleString()} words</span>
        </div>

        <h1 class="article-title">{item.title}</h1>

        {#if item.summary}
          <p class="article-summary">{item.summary}</p>
        {/if}

        {#if item.tags && item.tags.length > 0}
          <div class="article-tags">
            {#each item.tags as tag}
              <span class="tag">{tag}</span>
            {/each}
          </div>
        {/if}

        <!-- Article Actions -->
        <div class="article-actions">
          <button class="action-btn" on:click={copyLink} title="Copy link">
            <Icon name={copyNotification ? 'check' : 'link'} />
            <span>{copyNotification ? 'Copied!' : 'Copy Link'}</span>
          </button>
          
          <button class="action-btn" on:click={share} title="Share">
            <Icon name="share" />
            <span>Share</span>
          </button>

          {#if item.url}
            <a href={item.url} target="_blank" rel="noopener noreferrer" class="action-btn">
              <Icon name="external-link" />
              <span>View Original</span>
            </a>
          {/if}
        </div>
      </header>

      <!-- Table of Contents -->
      {#if showTableOfContents}
        <aside class="table-of-contents">
          <h3>Table of Contents</h3>
          <nav>
            {#each headings as heading}
              <button
                class="toc-item level-{heading.level}"
                on:click={() => scrollToHeading(heading.id)}
              >
                {heading.text}
              </button>
            {/each}
          </nav>
        </aside>
      {/if}

      <!-- Article Body -->
      <div class="article-body">
        {#if item.content}
          <MarkdownViewer 
            content={item.content} 
            enableSyntaxHighlight={true}
          />
        {:else}
          <p class="no-content">No content available</p>
        {/if}
      </div>

      <!-- Actionable Insights -->
      {#if hasActionableInsights}
        <section class="actionable-insights">
          <h3>
            <Icon name="zap" />
            Actionable Insights
          </h3>
          <div class="insights-content">
            {#if item.metadata.actionable_insights.tips?.length > 0}
              <div class="insight-category">
                <h4>💡 Tips & Best Practices</h4>
                <ul class="insights-list">
                  {#each item.metadata.actionable_insights.tips as tip}
                    <li class="insight-item {tip.importance}">
                      {tip.content}
                      {#if tip.context}
                        <span class="context">— {tip.context}</span>
                      {/if}
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}
            
            {#if item.metadata.actionable_insights.steps?.length > 0}
              <div class="insight-category">
                <h4>📋 Steps & Instructions</h4>
                <ol class="insights-list numbered">
                  {#each item.metadata.actionable_insights.steps as step}
                    <li class="insight-item {step.importance}">
                      {step.content}
                      {#if step.context}
                        <span class="context">— {step.context}</span>
                      {/if}
                    </li>
                  {/each}
                </ol>
              </div>
            {/if}
            
            {#if item.metadata.actionable_insights.methods?.length > 0}
              <div class="insight-category">
                <h4>🔧 Methods & Techniques</h4>
                <ul class="insights-list">
                  {#each item.metadata.actionable_insights.methods as method}
                    <li class="insight-item {method.importance}">
                      {method.content}
                      {#if method.context}
                        <span class="context">— {method.context}</span>
                      {/if}
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}
            
            {#if item.metadata.actionable_insights.takeaways?.length > 0}
              <div class="insight-category">
                <h4>🎯 Key Takeaways</h4>
                <ul class="insights-list">
                  {#each item.metadata.actionable_insights.takeaways as takeaway}
                    <li class="insight-item {takeaway.importance}">
                      {takeaway.content}
                      {#if takeaway.context}
                        <span class="context">— {takeaway.context}</span>
                      {/if}
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}
          </div>
        </section>
      {/if}

      <!-- AI Analysis -->
      {#if hasAIAnalysis}
        <section class="ai-analysis">
          <h3>
            <Icon name="cpu" />
            AI Analysis
          </h3>
          <div class="analysis-content">
            {#if item.metadata?.ai_analysis?.key_topics}
              <div class="analysis-section">
                <h4>Key Topics</h4>
                <div class="topics">
                  {#each item.metadata.ai_analysis.key_topics as topic}
                    <span class="topic-pill">{topic}</span>
                  {/each}
                </div>
              </div>
            {/if}
            
            {#if item.metadata?.ai_analysis?.summary}
              <div class="analysis-section">
                <h4>Summary</h4>
                <p>{item.metadata.ai_analysis.summary}</p>
              </div>
            {/if}
          </div>
        </section>
      {/if}
    </article>

    <!-- Bottom Actions -->
    <div class="bottom-actions">
      <button class="btn-secondary" on:click={() => goto('/timeline')}>
        <Icon name="arrow-left" />
        Back to Timeline
      </button>
      
      <button class="btn-primary" on:click={() => goto(`/items/${itemId}/edit`)}>
        <Icon name="edit" />
        Edit Article
      </button>
    </div>
  {/if}
</div>

<style>
  .reading-progress {
    position: fixed;
    top: 0;
    left: 0;
    height: 3px;
    background: var(--color-primary);
    z-index: 1000;
    transition: width 0.3s ease;
  }

  .article-container {
    max-width: 800px;
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

  .article-content {
    background: var(--color-surface);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
  }

  .article-header {
    padding: 3rem 3rem 2rem;
    border-bottom: 1px solid var(--color-border);
  }

  .article-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--color-text-secondary);
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
  }

  .separator {
    opacity: 0.5;
  }

  .reading-time,
  .word-count {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .article-title {
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1.2;
    margin: 0 0 1.5rem;
    color: var(--color-text);
  }

  .article-summary {
    font-size: 1.25rem;
    line-height: 1.6;
    color: var(--color-text-secondary);
    margin-bottom: 1.5rem;
  }

  .article-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 2rem;
  }

  .tag {
    padding: 0.25rem 0.75rem;
    background: var(--color-primary-light);
    color: var(--color-primary);
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .article-actions {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
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
    text-decoration: none;
  }

  .action-btn:hover {
    background: var(--color-primary-light);
    border-color: var(--color-primary);
    color: var(--color-primary);
  }

  .table-of-contents {
    padding: 2rem 3rem;
    border-bottom: 1px solid var(--color-border);
    background: var(--color-background);
  }

  .table-of-contents h3 {
    font-size: 1.125rem;
    margin-bottom: 1rem;
    color: var(--color-text-secondary);
  }

  .table-of-contents nav {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .toc-item {
    text-align: left;
    padding: 0.5rem 0;
    background: none;
    border: none;
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: color 0.2s ease;
  }

  .toc-item:hover {
    color: var(--color-primary);
  }

  .toc-item.level-2 { padding-left: 1rem; }
  .toc-item.level-3 { padding-left: 2rem; }
  .toc-item.level-4 { padding-left: 3rem; }
  .toc-item.level-5 { padding-left: 4rem; }
  .toc-item.level-6 { padding-left: 5rem; }

  .article-body {
    padding: 3rem;
    font-size: 1.125rem;
    line-height: 1.8;
    color: var(--color-text);
  }

  .article-body :global(h1),
  .article-body :global(h2),
  .article-body :global(h3),
  .article-body :global(h4),
  .article-body :global(h5),
  .article-body :global(h6) {
    margin-top: 2rem;
    margin-bottom: 1rem;
    font-weight: 700;
  }

  .article-body :global(p) {
    margin-bottom: 1.5rem;
  }

  .article-body :global(blockquote) {
    margin: 2rem 0;
    padding-left: 1.5rem;
    border-left: 4px solid var(--color-primary);
    font-style: italic;
    color: var(--color-text-secondary);
  }

  .article-body :global(pre) {
    margin: 2rem 0;
    padding: 1.5rem;
    background: var(--color-background);
    border-radius: 8px;
    overflow-x: auto;
  }

  .article-body :global(code) {
    font-family: 'Fira Code', monospace;
    font-size: 0.9em;
  }

  .article-body :global(a) {
    color: var(--color-primary);
    text-decoration: underline;
  }

  .article-body :global(a:hover) {
    text-decoration: none;
  }

  .article-body :global(img) {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 2rem 0;
  }

  .article-body :global(ul),
  .article-body :global(ol) {
    margin-bottom: 1.5rem;
    padding-left: 2rem;
  }

  .article-body :global(li) {
    margin-bottom: 0.5rem;
  }

  .no-content {
    text-align: center;
    color: var(--color-text-secondary);
    padding: 4rem 0;
  }

  .ai-analysis {
    padding: 2rem 3rem;
    background: var(--color-background);
    border-top: 1px solid var(--color-border);
  }

  .ai-analysis h3 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    color: var(--color-primary);
  }

  .analysis-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .analysis-section h4 {
    font-size: 1rem;
    margin-bottom: 0.75rem;
    color: var(--color-text-secondary);
  }

  .topics {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .topic-pill {
    padding: 0.375rem 0.75rem;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 20px;
    font-size: 0.875rem;
  }

  .actionable-insights {
    padding: 2rem 3rem;
    background: var(--color-background);
    border-top: 1px solid var(--color-border);
  }

  .actionable-insights h3 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    color: var(--color-primary);
  }

  .insights-content {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .insight-category h4 {
    font-size: 1.125rem;
    margin-bottom: 1rem;
    color: var(--color-text);
  }

  .insights-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .insights-list.numbered {
    counter-reset: step-counter;
  }

  .insight-item {
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    background: var(--color-surface);
    border-radius: 8px;
    border-left: 4px solid var(--color-border);
    line-height: 1.6;
    transition: all 0.2s ease;
  }

  .insights-list.numbered .insight-item {
    position: relative;
    padding-left: 2.5rem;
  }

  .insights-list.numbered .insight-item::before {
    counter-increment: step-counter;
    content: counter(step-counter);
    position: absolute;
    left: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    width: 1.5rem;
    height: 1.5rem;
    background: var(--color-primary);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .insight-item.high {
    border-left-color: var(--color-primary);
    background: var(--color-primary-light);
  }

  .insight-item.medium {
    border-left-color: var(--color-success);
  }

  .insight-item.low {
    border-left-color: var(--color-text-secondary);
  }

  .insight-item:hover {
    transform: translateX(4px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .insight-item .context {
    display: block;
    margin-top: 0.25rem;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    font-style: italic;
  }

  .bottom-actions {
    display: flex;
    justify-content: space-between;
    margin-top: 3rem;
    gap: 1rem;
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
    .article-header {
      padding: 2rem 1.5rem 1.5rem;
    }

    .article-title {
      font-size: 2rem;
    }

    .article-summary {
      font-size: 1.125rem;
    }

    .article-body {
      padding: 2rem 1.5rem;
      font-size: 1rem;
    }

    .table-of-contents {
      padding: 1.5rem;
    }

    .ai-analysis {
      padding: 1.5rem;
    }

    .bottom-actions {
      flex-direction: column;
    }

    .btn-primary,
    .btn-secondary {
      width: 100%;
      justify-content: center;
    }
  }
</style>