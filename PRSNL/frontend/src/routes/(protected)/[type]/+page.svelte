<!--
  Content Type Library Page
  
  Shows all content items of a specific type with filtering by categories and tags
  Routes: /articles, /videos, /code, etc.
-->

<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import ContentTypeIndicator from '$lib/components/ContentTypeIndicator.svelte';
  import Breadcrumbs from '$lib/components/navigation/Breadcrumbs.svelte';
  import { getBreadcrumbs } from '$lib/config/routingSchema';
  import { categorizationService } from '$lib/services/categorizationService';
  import BookmarkButton from '$lib/components/BookmarkButton.svelte';
  import ShareButton from '$lib/components/ShareButton.svelte';
  import type { PageData } from './$types';
  
  export let data: PageData;
  
  // ===========================
  // REACTIVE DECLARATIONS
  // ===========================
  
  $: breadcrumbs = getBreadcrumbs($page.url.pathname);
  $: contentType = data.contentType;
  $: content = data.content;
  $: filters = data.filters;
  $: stats = data.stats;
  
  // ===========================
  // STATE MANAGEMENT
  // ===========================
  
  let isLoading = false;
  let selectedCategory: string | null = filters.category;
  let selectedTags: string[] = [...filters.tags];
  let sortBy = filters.sortBy;
  let sortOrder = filters.sortOrder;
  let showFilters = false;
  
  // ===========================
  // FILTERING LOGIC
  // ===========================
  
  async function applyFilters() {
    isLoading = true;
    
    // Build new URL with filters
    const url = new URL($page.url);
    url.searchParams.delete('page'); // Reset to page 1 when filtering
    
    if (selectedCategory) {
      url.searchParams.set('category', selectedCategory);
    } else {
      url.searchParams.delete('category');
    }
    
    if (selectedTags.length > 0) {
      url.searchParams.set('tags', selectedTags.join(','));
    } else {
      url.searchParams.delete('tags');
    }
    
    url.searchParams.set('sort', sortBy);
    url.searchParams.set('order', sortOrder);
    
    await goto(url.toString(), { invalidateAll: true });
    isLoading = false;
  }
  
  function clearFilters() {
    selectedCategory = null;
    selectedTags = [];
    sortBy = 'updated_date';
    sortOrder = 'desc';
    applyFilters();
  }
  
  function toggleTag(tag: string) {
    if (selectedTags.includes(tag)) {
      selectedTags = selectedTags.filter(t => t !== tag);
    } else {
      selectedTags = [...selectedTags, tag];
    }
  }
  
  // ===========================
  // PAGINATION
  // ===========================
  
  function loadMore() {
    const url = new URL($page.url);
    url.searchParams.set('page', (filters.page + 1).toString());
    goto(url.toString(), { invalidateAll: true });
  }
  
  // ===========================
  // COMPUTED VALUES
  // ===========================
  
  $: hasActiveFilters = selectedCategory || selectedTags.length > 0;
  $: activeCategories = stats.categories.filter(cat => cat.count > 0);
  $: popularTags = stats.tags.slice(0, 20);
  
  // ===========================
  // UTILITY FUNCTIONS
  // ===========================
  
  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
  
  function truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }
</script>

<svelte:head>
  <title>{contentType.label} - Library - PRSNL</title>
  <meta name="description" content="Browse {content.total} {contentType.label.toLowerCase()} in your knowledge base" />
</svelte:head>

<main class="content-type-page">
  <!-- Breadcrumbs -->
  <Breadcrumbs items={breadcrumbs} />
  
  <!-- Page Header -->
  <header class="page-header">
    <div class="header-content">
      <div class="header-info">
        <ContentTypeIndicator 
          type={contentType.type}
          label={contentType.label}
          icon={contentType.icon}
          color={contentType.color}
          size="large"
          variant="filled"
        />
        <div class="header-text">
          <h1>{contentType.label}</h1>
          <p class="content-description">
            {content.total.toLocaleString()} {content.total === 1 ? 'item' : 'items'} • {contentType.description}
          </p>
        </div>
      </div>
      
      <!-- Filter Toggle -->
      <button 
        class="filter-toggle {showFilters ? 'active' : ''}"
        on:click={() => showFilters = !showFilters}
      >
        <Icon name="filter" size="small" />
        Filters
        {#if hasActiveFilters}
          <span class="filter-badge">{(selectedCategory ? 1 : 0) + selectedTags.length}</span>
        {/if}
      </button>
    </div>
    
    <!-- Filters Panel -->
    {#if showFilters}
      <div class="filters-panel">
        <div class="filters-content">
          
          <!-- Categories Filter -->
          {#if activeCategories.length > 0}
            <div class="filter-group">
              <h4>
                <Icon name="folder" size="small" />
                Categories
              </h4>
              <div class="filter-options">
                <button 
                  class="filter-option {selectedCategory === null ? 'active' : ''}"
                  on:click={() => { selectedCategory = null; applyFilters(); }}
                >
                  All Categories
                </button>
                {#each activeCategories as category}
                  <button 
                    class="filter-option {selectedCategory === category.id ? 'active' : ''}"
                    on:click={() => { selectedCategory = category.id; applyFilters(); }}
                  >
                    <Icon name={category.icon} size="small" />
                    {category.label}
                    <span class="option-count">{category.count}</span>
                  </button>
                {/each}
              </div>
            </div>
          {/if}
          
          <!-- Tags Filter -->
          {#if popularTags.length > 0}
            <div class="filter-group">
              <h4>
                <Icon name="tag" size="small" />
                Popular Tags
              </h4>
              <div class="tag-cloud">
                {#each popularTags as tagStat}
                  <button 
                    class="tag-button {selectedTags.includes(tagStat.tag) ? 'active' : ''}"
                    on:click={() => { toggleTag(tagStat.tag); applyFilters(); }}
                  >
                    {tagStat.tag}
                    <span class="tag-count">{tagStat.count}</span>
                  </button>
                {/each}
              </div>
            </div>
          {/if}
          
          <!-- Sort Options -->
          <div class="filter-group">
            <h4>
              <Icon name="arrow-up-down" size="small" />
              Sort By
            </h4>
            <div class="sort-options">
              <div class="sort-group">
                <select bind:value={sortBy} on:change={applyFilters}>
                  <option value="updated_date">Last Updated</option>
                  <option value="created_date">Date Added</option>
                  <option value="title">Title</option>
                </select>
                <select bind:value={sortOrder} on:change={applyFilters}>
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </div>
            </div>
          </div>
          
          <!-- Clear Filters -->
          {#if hasActiveFilters}
            <div class="filter-actions">
              <button class="clear-filters-btn" on:click={clearFilters}>
                <Icon name="x" size="small" />
                Clear All Filters
              </button>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </header>

  <!-- Content Grid -->
  <section class="content-section">
    {#if isLoading}
      <div class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>Loading content...</p>
      </div>
    {/if}
    
    {#if content.items.length === 0}
      <!-- Empty State -->
      <div class="empty-state">
        <Icon name="inbox" size="large" />
        <h3>No {contentType.label.toLowerCase()} found</h3>
        <p>
          {#if hasActiveFilters}
            Try adjusting your filters or <button class="link-btn" on:click={clearFilters}>clear all filters</button>.
          {:else}
            No {contentType.label.toLowerCase()} have been added to your library yet.
          {/if}
        </p>
        {#if !hasActiveFilters}
          <a href="/tools/capture" class="add-content-btn">
            <Icon name="plus" size="small" />
            Add Content
          </a>
        {/if}
      </div>
    {:else}
      <!-- Content Grid -->
      <div class="content-grid">
        {#each content.items as item}
          <article class="content-item">
            <div class="item-header">
              {#if item.thumbnail}
                <div class="item-thumbnail">
                  <img src={item.thumbnail} alt="" />
                </div>
              {:else}
                <div class="item-icon">
                  <Icon name={contentType.icon} size="large" />
                </div>
              {/if}
              
              <div class="item-actions">
                <BookmarkButton itemId={item.id} size="small" />
                <ShareButton size="small" on:share={() => navigator.share?.({ url: item.url || '' })} />
              </div>
            </div>
            
            <div class="item-content">
              <h3>
                <a href="/{contentType.path}/{item.id}" data-sveltekit-preload-data="hover">
                  {truncateText(item.title, 80)}
                </a>
              </h3>
              
              {#if item.description}
                <p class="item-description">
                  {truncateText(item.description, 120)}
                </p>
              {/if}
              
              <div class="item-meta">
                <div class="meta-row">
                  {#if item.category}
                    {@const categoryConfig = categorizationService.getCategoryConfig(item.category)}
                    {#if categoryConfig}
                      <span class="category-badge" style="--category-color: {categoryConfig.color}">
                        <Icon name={categoryConfig.icon} size="small" />
                        {categoryConfig.label}
                      </span>
                    {/if}
                  {/if}
                  
                  <time class="item-date" datetime={item.updated_at}>
                    {formatDate(item.updated_at)}
                  </time>
                </div>
                
                {#if item.tags.length > 0}
                  <div class="item-tags">
                    {#each item.tags.slice(0, 3) as tag}
                      <span class="tag">{tag}</span>
                    {/each}
                    {#if item.tags.length > 3}
                      <span class="tag more">+{item.tags.length - 3}</span>
                    {/if}
                  </div>
                {/if}
              </div>
            </div>
          </article>
        {/each}
      </div>
      
      <!-- Load More -->
      {#if content.hasMore}
        <div class="load-more-section">
          <button class="load-more-btn" on:click={loadMore} disabled={isLoading}>
            <Icon name="chevron-down" size="small" />
            Load More
          </button>
        </div>
      {/if}
    {/if}
  </section>
</main>

<style>
  .content-type-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  /* Header */
  .page-header {
    margin-bottom: 2rem;
  }
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 2rem;
    margin-bottom: 1.5rem;
  }
  
  .header-info {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .header-text h1 {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 0.5rem 0;
  }
  
  .content-description {
    color: var(--text-secondary);
    margin: 0;
    font-size: 1rem;
  }
  
  /* Filter Toggle */
  .filter-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: var(--text-secondary);
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
    position: relative;
  }
  
  .filter-toggle:hover,
  .filter-toggle.active {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
  }
  
  .filter-badge {
    background: var(--neural-green);
    color: var(--background-primary);
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.125rem 0.5rem;
    border-radius: 10px;
    min-width: 20px;
    text-align: center;
  }
  
  /* Filters Panel */
  .filters-panel {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
  }
  
  .filters-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
  }
  
  .filter-group h4 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 1rem 0;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }
  
  /* Filter Options */
  .filter-options {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .filter-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
    text-align: left;
  }
  
  .filter-option:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
  }
  
  .filter-option.active {
    background: rgba(45, 212, 191, 0.1);
    border-color: var(--neural-green);
    color: var(--neural-green);
  }
  
  .option-count {
    margin-left: auto;
    font-size: 0.8rem;
    color: var(--text-muted);
  }
  
  /* Tag Cloud */
  .tag-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .tag-button {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.375rem 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.2s;
  }
  
  .tag-button:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
  }
  
  .tag-button.active {
    background: rgba(45, 212, 191, 0.2);
    border-color: var(--neural-green);
    color: var(--neural-green);
  }
  
  .tag-count {
    font-size: 0.7rem;
    color: var(--text-muted);
  }
  
  /* Sort Options */
  .sort-group {
    display: flex;
    gap: 0.5rem;
  }
  
  .sort-group select {
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }
  
  /* Filter Actions */
  .filter-actions {
    grid-column: 1 / -1;
    display: flex;
    justify-content: center;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .clear-filters-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
  }
  
  .clear-filters-btn:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
  }
  
  /* Content Grid */
  .content-section {
    position: relative;
  }
  
  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 10;
    border-radius: 12px;
  }
  
  .loading-spinner {
    width: 32px;
    height: 32px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid var(--neural-green);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }
  
  .content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }
  
  /* Content Items */
  .content-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.3s;
  }
  
  .content-item:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
  }
  
  .item-header {
    position: relative;
    height: 120px;
    background: linear-gradient(135deg, rgba(45, 212, 191, 0.1), rgba(45, 212, 191, 0.05));
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .item-thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .item-icon {
    color: var(--neural-green);
    opacity: 0.7;
  }
  
  .item-actions {
    position: absolute;
    top: 0.75rem;
    right: 0.75rem;
    display: flex;
    gap: 0.5rem;
    opacity: 0;
    transition: opacity 0.2s;
  }
  
  .content-item:hover .item-actions {
    opacity: 1;
  }
  
  .item-content {
    padding: 1.25rem;
  }
  
  .item-content h3 {
    margin: 0 0 0.5rem 0;
  }
  
  .item-content h3 a {
    color: var(--text-primary);
    text-decoration: none;
    font-weight: 600;
    font-size: 1.1rem;
    line-height: 1.4;
  }
  
  .item-content h3 a:hover {
    color: var(--neural-green);
  }
  
  .item-description {
    color: var(--text-secondary);
    font-size: 0.9rem;
    line-height: 1.5;
    margin: 0 0 1rem 0;
  }
  
  /* Item Meta */
  .item-meta {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .meta-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .category-badge {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    background: color-mix(in srgb, var(--category-color) 20%, transparent);
    border: 1px solid color-mix(in srgb, var(--category-color) 30%, transparent);
    border-radius: 12px;
    color: var(--category-color);
    font-size: 0.75rem;
    font-weight: 500;
  }
  
  .item-date {
    color: var(--text-muted);
    font-size: 0.8rem;
  }
  
  .item-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }
  
  .tag {
    padding: 0.125rem 0.5rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    color: var(--text-muted);
    font-size: 0.7rem;
  }
  
  .tag.more {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-muted);
  }
  
  /* Empty State */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
    color: var(--text-secondary);
  }
  
  .empty-state h3 {
    margin: 1rem 0 0.5rem 0;
    color: var(--text-primary);
  }
  
  .empty-state p {
    margin: 0 0 2rem 0;
    max-width: 400px;
    line-height: 1.6;
  }
  
  .link-btn {
    background: none;
    border: none;
    color: var(--neural-green);
    cursor: pointer;
    text-decoration: underline;
    font-size: inherit;
  }
  
  .add-content-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: var(--neural-green);
    color: var(--background-primary);
    text-decoration: none;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s;
  }
  
  .add-content-btn:hover {
    background: #38b2ac;
    transform: translateY(-1px);
  }
  
  /* Load More */
  .load-more-section {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
  }
  
  .load-more-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: var(--text-secondary);
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
  }
  
  .load-more-btn:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
  }
  
  .load-more-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .content-type-page {
      padding: 1rem;
    }
    
    .header-content {
      flex-direction: column;
      align-items: stretch;
      gap: 1rem;
    }
    
    .header-info {
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 0.75rem;
    }
    
    .filters-content {
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }
    
    .content-grid {
      grid-template-columns: 1fr;
    }
  }
</style>