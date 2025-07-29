<script lang="ts">
  import { onMount } from 'svelte';
  import type { PageData } from './$types';
  import Icon from '$lib/components/Icon.svelte';

  export let data: PageData;

  $: ({ tool, toolConfig, breadcrumbs } = data);

  // Component mapping for each tool
  let ToolComponent: any = null;

  onMount(async () => {
    // Dynamically import the appropriate component based on tool
    try {
      switch (tool) {
        case 'timeline':
          // Fix: Import without destructuring to avoid syntax errors
          const timelineModule = await import('../../(protected)/timeline/+page.svelte');
          ToolComponent = timelineModule.default;
          break;
        case 'insights':
          const insightsModule = await import('../../(protected)/insights/+page.svelte');
          ToolComponent = insightsModule.default;
          break;
        case 'chat':
          const chatModule = await import('../../(protected)/chat/+page.svelte');
          ToolComponent = chatModule.default;
          break;
        case 'visual':
          const videosModule = await import('../../(protected)/videos/+page.svelte');
          ToolComponent = videosModule.default;
          break;
        case 'code':
          const codeModule = await import('../../(protected)/code-cortex/+page.svelte');
          ToolComponent = codeModule.default;
          break;
        default:
          ToolComponent = null;
      }
    } catch (error) {
      console.error(`Error loading component for tool '${tool}':`, error);
    }
  });
</script>

<svelte:head>
  <title>{toolConfig.title} | PRSNL</title>
  <meta name="description" content={toolConfig.description} />
  <meta property="og:title" content="{toolConfig.title} | PRSNL" />
  <meta property="og:description" content={toolConfig.description} />
</svelte:head>

<div class="tool-page">
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

  <!-- Tool Header -->
  <header class="tool-header">
    <div class="tool-icon" style="color: {toolConfig.color}">
      <Icon name={toolConfig.icon} size="large" />
    </div>
    <div class="tool-info">
      <h1 class="tool-title" style="color: {toolConfig.color}">
        {toolConfig.title}
      </h1>
      <p class="tool-description">{toolConfig.description}</p>
    </div>
  </header>

  <!-- Tool Content -->
  <main class="tool-content">
    {#if ToolComponent}
      <svelte:component this={ToolComponent} />
    {:else}
      <div class="loading">
        <Icon name="loader" size="medium" />
        <span>Loading {toolConfig.title}...</span>
      </div>
    {/if}
  </main>
</div>

<style>
  .tool-page {
    max-width: 100%;
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
    max-width: 1200px;
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

  /* Tool Header */
  .tool-header {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 2rem;
    padding: 2rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 12px;
    max-width: 1200px;
  }

  .tool-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 4rem;
    height: 4rem;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.3);
    border: 2px solid currentColor;
    flex-shrink: 0;
  }

  .tool-title {
    font-size: 2.5rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    line-height: 1.2;
  }

  .tool-description {
    font-size: 1.125rem;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.5;
    margin: 0;
  }

  /* Tool Content */
  .tool-content {
    width: 100%;
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 4rem 2rem;
    color: rgba(255, 255, 255, 0.6);
    text-align: center;
  }

  /* Remove any max-width constraints for full-width tools */
  .tool-content :global(.timeline-container),
  .tool-content :global(.insights-container),
  .tool-content :global(.chat-container),
  .tool-content :global(.videos-container),
  .tool-content :global(.code-cortex-container) {
    max-width: none !important;
    width: 100% !important;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .tool-page {
      padding: 0.5rem;
    }

    .tool-header {
      flex-direction: column;
      text-align: center;
      gap: 1rem;
    }

    .tool-title {
      font-size: 2rem;
    }

    .breadcrumbs {
      font-size: 0.75rem;
      padding: 0.5rem 0.75rem;
    }
  }
</style>
