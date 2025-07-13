<script lang="ts">
  import { onMount } from 'svelte';
  import type { PageData } from './$types';
  import Icon from '$lib/components/Icon.svelte';

  export let data: PageData;

  $: ({ page, pageConfig, importVariant, breadcrumbs } = data);

  // Component mapping for each system page
  let PageComponent: any = null;

  onMount(async () => {
    // Dynamically import the appropriate component based on page
    switch (page) {
      case 'import':
        if (importVariant === 'v2') {
          const { default: ImportV2 } = await import('../../import/v2/+page.svelte');
          PageComponent = ImportV2;
        } else {
          const { default: Import } = await import('../../import/+page.svelte');
          PageComponent = Import;
        }
        break;
      case 'settings':
        const { default: Settings } = await import('../../settings/+page.svelte');
        PageComponent = Settings;
        break;
      case 'docs':
        const { default: Docs } = await import('../../docs/+page.svelte');
        PageComponent = Docs;
        break;
      case 'health':
        // Create a simple health page component if it doesn't exist
        PageComponent = createHealthComponent();
        break;
      default:
        PageComponent = null;
    }
  });

  function createHealthComponent() {
    return {
      render: () => `
				<div class="health-page">
					<h2>System Health Monitor</h2>
					<p>System health monitoring page - coming soon</p>
				</div>
			`,
    };
  }
</script>

<svelte:head>
  <title>{pageConfig.title} | PRSNL</title>
  <meta name="description" content={pageConfig.description} />
  <meta property="og:title" content="{pageConfig.title} | PRSNL" />
  <meta property="og:description" content={pageConfig.description} />
</svelte:head>

<div class="system-page">
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

  <!-- Page Header -->
  <header class="page-header">
    <div class="page-icon" style="color: {pageConfig.color}">
      <Icon name={pageConfig.icon} size="large" />
    </div>
    <div class="page-info">
      <h1 class="page-title" style="color: {pageConfig.color}">
        {pageConfig.title}
      </h1>
      <p class="page-description">{pageConfig.description}</p>

      {#if page === 'import' && importVariant}
        <div class="import-variant">
          <span class="variant-label">Version:</span>
          <div class="variant-switcher">
            <a href="/s/import?v=v1" class="variant-link" class:active={importVariant === 'v1'}>
              v1
            </a>
            <a href="/s/import?v=v2" class="variant-link" class:active={importVariant === 'v2'}>
              v2
            </a>
          </div>
        </div>
      {/if}
    </div>
  </header>

  <!-- Page Content -->
  <main class="page-content">
    {#if PageComponent}
      <svelte:component this={PageComponent} />
    {:else}
      <div class="loading">
        <Icon name="loader" size="medium" />
        <span>Loading {pageConfig.title}...</span>
      </div>
    {/if}
  </main>
</div>

<style>
  .system-page {
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

  /* Page Header */
  .page-header {
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
    margin-bottom: 2rem;
    padding: 2rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 12px;
  }

  .page-icon {
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

  .page-info {
    flex: 1;
  }

  .page-title {
    font-size: 2.5rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    line-height: 1.2;
  }

  .page-description {
    font-size: 1.125rem;
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.5;
    margin: 0 0 1rem 0;
  }

  /* Import Variant Switcher */
  .import-variant {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-top: 1rem;
  }

  .variant-label {
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.6);
    font-weight: 500;
  }

  .variant-switcher {
    display: flex;
    gap: 0.5rem;
  }

  .variant-link {
    padding: 0.375rem 0.75rem;
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 4px;
    color: rgba(255, 255, 255, 0.7);
    text-decoration: none;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s ease;
  }

  .variant-link:hover {
    border-color: var(--success);
    color: var(--success);
  }

  .variant-link.active {
    background: var(--success);
    border-color: var(--success);
    color: #000;
  }

  /* Page Content */
  .page-content {
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

  /* Responsive */
  @media (max-width: 768px) {
    .system-page {
      padding: 0.5rem;
    }

    .page-header {
      flex-direction: column;
      text-align: center;
      gap: 1rem;
    }

    .page-title {
      font-size: 2rem;
    }

    .breadcrumbs {
      font-size: 0.75rem;
      padding: 0.5rem 0.75rem;
    }

    .import-variant {
      justify-content: center;
    }
  }
</style>
