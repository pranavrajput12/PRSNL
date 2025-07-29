<!--
  UNIFIED CONTENT PAGE
  Route: /library/[type]/[id]
  
  This is the unified page component that renders all content types
  using the new routing system. It replaces multiple scattered pages
  and uses the existing SPT (Single Page Templates) system.
  
  Features:
  - Dynamic content type rendering
  - Consistent navigation and breadcrumbs
  - SEO optimization
  - Mobile-responsive design
  - Accessibility support
-->

<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import Breadcrumbs from '$lib/components/navigation/Breadcrumbs.svelte';
  import ContentTypeIndicator from '$lib/components/ContentTypeIndicator.svelte';
  import ShareButton from '$lib/components/ShareButton.svelte';
  import BookmarkButton from '$lib/components/BookmarkButton.svelte';
  
  // Content-specific components (reuse existing SPT components)
  import ArticleView from '$lib/components/content/ArticleView.svelte';
  import VideoView from '$lib/components/content/VideoView.svelte';
  import RecipeView from '$lib/components/content/RecipeView.svelte';
  import BookmarkView from '$lib/components/content/BookmarkView.svelte';
  import DocumentView from '$lib/components/content/DocumentView.svelte';
  import CodeView from '$lib/components/content/CodeView.svelte';
  import RepositoryView from '$lib/components/content/RepositoryView.svelte';
  import ConversationView from '$lib/components/content/ConversationView.svelte';
  import GenericItemView from '$lib/components/content/GenericItemView.svelte';
  
  import type { PageData } from './$types';
  
  export let data: PageData;
  
  $: ({ item, contentType, metadata, breadcrumbs } = data);
  $: contentTypeId = contentType.type;
  $: isLoading = !item;
  
  // Actions state
  let copyNotification = false;
  let showQuickActions = false;
  
  onMount(() => {
    // Track page view for analytics
    trackPageView();
    
    // Set up keyboard shortcuts
    setupKeyboardShortcuts();
  });
  
  function trackPageView() {
    // Analytics tracking
    if (typeof gtag !== 'undefined') {
      gtag('event', 'page_view', {
        page_title: metadata.title,
        page_location: window.location.href,
        content_type: contentTypeId,
        content_id: item.id
      });
    }
  }
  
  function setupKeyboardShortcuts() {
    function handleKeydown(e: KeyboardEvent) {
      // ESC - Close any open modals or go back
      if (e.key === 'Escape') {
        if (showQuickActions) {
          showQuickActions = false;
        } else {
          history.back();
        }
      }
      
      // B - Bookmark toggle
      if (e.key === 'b' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        toggleBookmark();
      }
      
      // S - Share
      if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        shareContent();
      }
      
      // A - Quick actions
      if (e.key === 'a' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        showQuickActions = !showQuickActions;
      }
    }
    
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }
  
  async function copyToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      copyNotification = true;
      setTimeout(() => copyNotification = false, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }
  
  async function shareContent() {
    const shareData = {
      title: item.title,
      text: item.summary || item.description,
      url: window.location.href
    };
    
    if (navigator.share && navigator.canShare(shareData)) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        console.log('Share cancelled');
      }
    } else {
      // Fallback to copying URL
      await copyToClipboard(window.location.href);
    }
  }
  
  function toggleBookmark() {
    // Implement bookmark toggle logic
    console.log('Toggle bookmark for:', item.id);
  }
  
  function goBack() {
    // Smart back navigation - go to appropriate list view
    const listRoute = contentType.listRoute;
    goto(listRoute);
  }
  
  // Dynamic component selection based on content type
  function getContentComponent(type: string) {
    const componentMap = {
      'article': ArticleView,
      'video': VideoView,
      'recipe': RecipeView,
      'bookmark': BookmarkView,
      'document': DocumentView,  
      'code': CodeView,
      'repository': RepositoryView,
      'conversation': ConversationView
    };
    
    return componentMap[type as keyof typeof componentMap] || GenericItemView;
  }
  
  $: ContentComponent = getContentComponent(contentTypeId);
</script>

<!-- SEO Meta Tags -->
<svelte:head>
  <title>{metadata.title}</title>
  <meta name="description" content={metadata.description} />
  
  <!-- Open Graph -->
  <meta property="og:title" content={metadata.openGraph.title} />
  <meta property="og:description" content={metadata.openGraph.description} />
  <meta property="og:type" content={metadata.openGraph.type} />
  <meta property="og:url" content={metadata.openGraph.url} />
  {#if metadata.openGraph.image}
    <meta property="og:image" content={metadata.openGraph.image} />
  {/if}
  
  <!-- Twitter -->
  <meta name="twitter:card" content={metadata.twitter.card} />
  <meta name="twitter:title" content={metadata.twitter.title} />
  <meta name="twitter:description" content={metadata.twitter.description} />
  {#if metadata.twitter.image}
    <meta name="twitter:image" content={metadata.twitter.image} />
  {/if}
  
  <!-- Canonical URL -->
  <link rel="canonical" href={metadata.openGraph.url} />
  
  <!-- JSON-LD Structured Data -->
  {@html `<script type="application/ld+json">${JSON.stringify(metadata.jsonLd)}</script>`}
</svelte:head>

{#if isLoading}
  <div class="loading-container">
    <div class="loading-spinner"></div>
    <p>Loading {contentType.label.toLowerCase()}...</p>
  </div>
{:else}
  <div class="unified-content-page">
    <!-- Header Section -->
    <header class="content-header">
      <!-- Breadcrumb Navigation -->
      <nav class="breadcrumb-nav" aria-label="Breadcrumb">
        <Breadcrumbs items={breadcrumbs} />
      </nav>
      
      <!-- Content Header -->
      <div class="header-main">
        <div class="header-left">
          <button 
            class="back-button" 
            on:click={goBack}
            aria-label="Go back to {contentType.label}"
          >
            <Icon name="arrow-left" size="small" />
            <span class="back-text">{contentType.label}</span>
          </button>
          
          <div class="header-content">
            <div class="title-section">
              <h1 class="content-title">{item.title || 'Untitled'}</h1>
              <ContentTypeIndicator 
                type={contentTypeId} 
                label={contentType.label}
                color={contentType.color}
                icon={contentType.icon}
              />
            </div>
            
            {#if item.summary || item.description}
              <p class="content-summary">{item.summary || item.description}</p>
            {/if}
          </div>
        </div>
        
        <div class="header-actions">
          <button 
            class="action-button"
            on:click={() => showQuickActions = !showQuickActions}
            aria-label="Quick actions"
            aria-expanded={showQuickActions}
          >
            <Icon name="more-horizontal" size="small" />
          </button>
          
          <BookmarkButton itemId={item.id} />
          <ShareButton on:share={shareContent} />
          
          {#if item.url}
            <a 
              href={item.url} 
              target="_blank" 
              rel="noopener noreferrer"
              class="action-button external-link"
              aria-label="Open original source"
            >
              <Icon name="external-link" size="small" />
            </a>
          {/if}
        </div>
      </div>
      
      <!-- Quick Actions Menu -->
      {#if showQuickActions}
        <div class="quick-actions-menu">
          <button class="quick-action" on:click={() => copyToClipboard(window.location.href)}>
            <Icon name="link" size="small" />
            Copy Link
          </button>
          <button class="quick-action" on:click={() => copyToClipboard(item.title)}>
            <Icon name="copy" size="small" />
            Copy Title
          </button>
          {#if item.url}
            <button class="quick-action" on:click={() => copyToClipboard(item.url)}>
              <Icon name="external-link" size="small" />
              Copy Source URL
            </button>
          {/if}
        </div>
      {/if}
    </header>
    
    <!-- Content Section -->
    <main class="content-main" role="main">
      <!-- Dynamic Content Component -->
      <svelte:component 
        this={ContentComponent} 
        {item} 
        {contentType}
        on:error={(e) => console.error('Content component error:', e.detail)}
      />
    </main>
    
    <!-- Copy Notification -->
    {#if copyNotification}
      <div class="copy-notification" role="alert">
        <Icon name="check" size="small" />
        Copied to clipboard!
      </div>
    {/if}
  </div>
{/if}

<style>
  .unified-content-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
    min-height: 100vh;
  }
  
  /* Loading State */
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    gap: 1rem;
    color: var(--text-secondary);
  }
  
  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(0, 255, 136, 0.3);
    border-top: 3px solid var(--neural-green);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  /* Header Section */
  .content-header {
    margin-bottom: 2rem;
    position: relative;
  }
  
  .breadcrumb-nav {
    margin-bottom: 1rem;
  }
  
  .header-main {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 2rem;
  }
  
  .header-left {
    flex: 1;
    min-width: 0;
  }
  
  .back-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
    background: none;
    border: none;
    cursor: pointer;
    font-family: inherit;
    font-size: 0.9rem;
    margin-bottom: 1rem;
    padding: 0.5rem 0;
    transition: color 0.2s;
  }
  
  .back-button:hover {
    color: var(--text-primary);
  }
  
  .back-text {
    font-weight: 500;
  }
  
  .title-section {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.5rem;
  }
  
  .content-title {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    line-height: 1.2;
  }
  
  .content-summary {
    color: var(--text-secondary);
    line-height: 1.6;
    margin: 0;
    font-size: 1.1rem;
  }
  
  /* Header Actions */
  .header-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-shrink: 0;
  }
  
  .action-button {
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
  }
  
  .action-button:hover {
    background: rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    transform: translateY(-1px);
  }
  
  /* Quick Actions Menu */
  .quick-actions-menu {
    position: absolute;
    top: 100%;
    right: 0;
    background: var(--bg-secondary);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 0.5rem;
    z-index: 10;
    min-width: 200px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  }
  
  .quick-action {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.75rem;
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    border-radius: 6px;
    font-family: inherit;
    font-size: 0.9rem;
    transition: all 0.2s;
    text-align: left;
  }
  
  .quick-action:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
  }
  
  /* Content Main */
  .content-main {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 2rem;
    backdrop-filter: blur(10px);
  }
  
  /* Copy Notification */
  .copy-notification {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    background: var(--neural-green);
    color: #000;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    animation: slideUp 0.3s ease;
    z-index: 1000;
  }
  
  @keyframes slideUp {
    from {
      transform: translateX(-50%) translateY(100%);
      opacity: 0;
    }
    to {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .unified-content-page {
      padding: 1rem 0.5rem;
    }
    
    .header-main {
      flex-direction: column;
      gap: 1rem;
    }
    
    .header-actions {
      align-self: flex-end;
    }
    
    .content-title {
      font-size: 1.5rem;
    }
    
    .title-section {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
  }
</style>