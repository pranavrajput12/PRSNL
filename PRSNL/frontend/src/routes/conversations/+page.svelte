<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Icon from '$lib/components/Icon.svelte';
  import ConversationCard from '$lib/components/ConversationCard.svelte';
  import SkeletonLoader from '$lib/components/SkeletonLoader.svelte';
  import { goto } from '$app/navigation';

  export let data;

  let conversations = [];
  let loading = true;
  let error = null;
  let selectedPlatform = null;
  let selectedCategory = null;
  let searchQuery = '';
  let stats = null;

  // Platform configuration
  const platforms = [
    { id: 'chatgpt', name: 'ChatGPT', icon: 'message-circle', color: '#10a37f' },
    { id: 'claude', name: 'Claude', icon: 'brain', color: '#AA7CFF' },
    { id: 'perplexity', name: 'Perplexity', icon: 'search', color: '#20808D' },
    { id: 'bard', name: 'Bard', icon: 'sparkles', color: '#4285F4' }
  ];

  // Neural categories
  const categories = [
    { id: 'learning', name: 'Learning', icon: 'book-open' },
    { id: 'development', name: 'Development', icon: 'code' },
    { id: 'thoughts', name: 'Thoughts', icon: 'message-square' },
    { id: 'reference', name: 'Reference', icon: 'bookmark' },
    { id: 'creative', name: 'Creative', icon: 'palette' }
  ];

  onMount(async () => {
    await loadConversations();
    await loadStats();
  });

  async function loadConversations() {
    try {
      loading = true;
      error = null;

      const params = new URLSearchParams();
      if (selectedPlatform) params.append('platform', selectedPlatform);
      if (selectedCategory) params.append('category', selectedCategory);
      if (searchQuery) params.append('search', searchQuery);

      const response = await fetch(`/api/conversations/?${params}`);
      if (!response.ok) {
        throw new Error('Failed to load conversations');
      }

      conversations = await response.json();
    } catch (err) {
      error = err.message;
      console.error('Error loading conversations:', err);
    } finally {
      loading = false;
    }
  }

  async function loadStats() {
    try {
      const response = await fetch('/api/conversations/stats/summary');
      if (response.ok) {
        stats = await response.json();
      }
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  }

  function filterByPlatform(platform) {
    selectedPlatform = selectedPlatform === platform ? null : platform;
    loadConversations();
  }

  function filterByCategory(category) {
    selectedCategory = selectedCategory === category ? null : category;
    loadConversations();
  }

  function handleSearch(event) {
    if (event.key === 'Enter') {
      loadConversations();
    }
  }

  function clearSearch() {
    searchQuery = '';
    loadConversations();
  }

  function navigateToConversation(conversation) {
    goto(`/conversations/${conversation.platform}/${conversation.slug}`);
  }
</script>

<svelte:head>
  <title>Neural Echo - AI Conversations | PRSNL</title>
</svelte:head>

<div class="neural-echo-container">
  <!-- Header Section -->
  <header class="echo-header">
    <div class="header-content">
      <div class="title-section">
        <h1 class="echo-title">
          <span class="neural-icon">🗲</span>
          Neural Echo
        </h1>
        <p class="echo-subtitle">Your AI conversations, echoing through the neural network</p>
      </div>
      
      {#if stats}
        <div class="stats-badges">
          <div class="stat-badge">
            <span class="stat-value">{stats.total_conversations || 0}</span>
            <span class="stat-label">Conversations</span>
          </div>
          <div class="stat-badge">
            <span class="stat-value">{stats.total_messages || 0}</span>
            <span class="stat-label">Messages</span>
          </div>
          <div class="stat-badge">
            <span class="stat-value">{stats.platforms_count || 0}</span>
            <span class="stat-label">Platforms</span>
          </div>
        </div>
      {/if}
    </div>
  </header>

  <!-- Search and Filters -->
  <div class="controls-section">
    <div class="search-container">
      <Icon name="search" size={20} />
      <input
        type="text"
        placeholder="Search conversations..."
        bind:value={searchQuery}
        on:keydown={handleSearch}
        class="search-input"
      />
      {#if searchQuery}
        <button on:click={clearSearch} class="clear-search">
          <Icon name="x" size={16} />
        </button>
      {/if}
    </div>

    <!-- Platform Filters -->
    <div class="filter-group">
      <span class="filter-label">Platform:</span>
      <div class="filter-chips">
        {#each platforms as platform}
          <button
            class="filter-chip {selectedPlatform === platform.id ? 'active' : ''}"
            style="--chip-color: {platform.color}"
            on:click={() => filterByPlatform(platform.id)}
          >
            <Icon name={platform.icon} size={16} />
            {platform.name}
          </button>
        {/each}
      </div>
    </div>

    <!-- Category Filters -->
    <div class="filter-group">
      <span class="filter-label">Category:</span>
      <div class="filter-chips">
        {#each categories as category}
          <button
            class="filter-chip {selectedCategory === category.id ? 'active' : ''}"
            on:click={() => filterByCategory(category.id)}
          >
            <Icon name={category.icon} size={16} />
            {category.name}
          </button>
        {/each}
      </div>
    </div>
  </div>

  <!-- Conversations Grid -->
  <div class="conversations-grid">
    {#if loading}
      {#each Array(6) as _}
        <SkeletonLoader type="card" />
      {/each}
    {:else if error}
      <div class="error-state">
        <Icon name="alert-circle" size={48} />
        <p>{error}</p>
        <button on:click={loadConversations} class="retry-button">Try Again</button>
      </div>
    {:else if conversations.length === 0}
      <div class="empty-state">
        <div class="empty-icon">🧠</div>
        <h3>No conversations yet</h3>
        <p>Import your first AI conversation using the PRSNL Chrome extension</p>
      </div>
    {:else}
      {#each conversations as conversation}
        <ConversationCard
          {conversation}
          on:click={() => navigateToConversation(conversation)}
        />
      {/each}
    {/if}
  </div>
</div>

<style>
  .neural-echo-container {
    min-height: 100vh;
    padding: 2rem;
  }

  .echo-header {
    margin-bottom: 3rem;
    background: linear-gradient(135deg, rgba(74, 158, 255, 0.1), rgba(140, 82, 255, 0.1));
    border-radius: 1rem;
    padding: 2rem;
    border: 1px solid rgba(74, 158, 255, 0.2);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 2rem;
  }

  .title-section {
    flex: 1;
  }

  .echo-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .neural-icon {
    font-size: 3rem;
    filter: drop-shadow(0 0 10px rgba(74, 158, 255, 0.5));
  }

  .echo-subtitle {
    color: var(--text-secondary);
    margin: 0.5rem 0 0 0;
    font-size: 1.1rem;
  }

  .stats-badges {
    display: flex;
    gap: 2rem;
  }

  .stat-badge {
    text-align: center;
    padding: 1rem 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 0.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .stat-value {
    display: block;
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
  }

  .stat-label {
    display: block;
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
  }

  .controls-section {
    margin-bottom: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .search-container {
    position: relative;
    max-width: 500px;
  }

  .search-container :global(svg) {
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-secondary);
  }

  .search-input {
    width: 100%;
    padding: 0.75rem 1rem 0.75rem 3rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    color: var(--text-primary);
    font-size: 1rem;
    transition: all 0.2s ease;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--accent);
    background: rgba(255, 255, 255, 0.08);
  }

  .clear-search {
    position: absolute;
    right: 0.5rem;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.25rem;
    transition: all 0.2s ease;
  }

  .clear-search:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.1);
  }

  .filter-group {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .filter-label {
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
  }

  .filter-chips {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .filter-chip {
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 2rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .filter-chip:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
  }

  .filter-chip.active {
    background: var(--chip-color, var(--accent));
    color: white;
    border-color: transparent;
  }

  .conversations-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .error-state,
  .empty-state {
    grid-column: 1 / -1;
    text-align: center;
    padding: 4rem 2rem;
  }

  .error-state {
    color: var(--error);
  }

  .empty-state {
    color: var(--text-secondary);
  }

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    filter: grayscale(0.5) opacity(0.5);
  }

  .empty-state h3 {
    font-size: 1.5rem;
    margin: 0 0 0.5rem 0;
    color: var(--text-primary);
  }

  .retry-button {
    margin-top: 1rem;
    padding: 0.5rem 1.5rem;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .retry-button:hover {
    background: var(--accent-hover);
    transform: translateY(-1px);
  }

  @media (max-width: 768px) {
    .neural-echo-container {
      padding: 1rem;
    }

    .echo-header {
      padding: 1.5rem;
    }

    .header-content {
      flex-direction: column;
      align-items: flex-start;
    }

    .stats-badges {
      width: 100%;
      justify-content: space-between;
    }

    .conversations-grid {
      grid-template-columns: 1fr;
    }
  }
</style>