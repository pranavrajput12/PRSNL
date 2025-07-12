<script lang="ts" type="module">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import Icon from '$lib/components/Icon.svelte';
  import ItemCard from '$lib/components/ItemCard.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import type { Item } from '$lib/types/api';
  import { getTimeline } from '$lib/api';

  let thoughts: Item[] = [];
  let isLoading = true;
  let error: Error | null = null;
  let searchQuery = '';
  let selectedType = 'all';
  let sortBy = 'recent';

  $: filteredThoughts = thoughts.filter(thought => {
    const matchesSearch = !searchQuery || 
      thought.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      thought.content?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      thought.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesType = selectedType === 'all' || thought.type === selectedType;
    
    return matchesSearch && matchesType;
  }).sort((a, b) => {
    if (sortBy === 'recent') {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    } else if (sortBy === 'title') {
      return (a.title || '').localeCompare(b.title || '');
    }
    return 0;
  });

  $: thoughtTypes = [...new Set(thoughts.map(t => t.type))].filter(Boolean);

  async function loadThoughts() {
    try {
      isLoading = true;
      error = null;
      
      const response = await getTimeline();
      if (response.success) {
        thoughts = response.data.items || [];
      } else {
        throw new Error(response.error || 'Failed to load thoughts');
      }
    } catch (err) {
      console.error('Error loading thoughts:', err);
      error = err as Error;
    } finally {
      isLoading = false;
    }
  }

  function handleThoughtClick(thought: Item) {
    const slug = thought.slug || `item-${thought.id}`;
    goto(`/thoughts/${slug}`);
  }

  onMount(() => {
    loadThoughts();
  });
</script>

<svelte:head>
  <title>Thoughts - PRSNL</title>
  <meta name="description" content="Browse your personal knowledge thoughts and insights" />
</svelte:head>

<div class="thoughts-container">
  <header class="thoughts-header">
    <div class="header-content">
      <h1 class="page-title">
        <Icon name="brain" size={32} />
        Thoughts
      </h1>
      <p class="page-description">Your personal knowledge collection</p>
    </div>

    <div class="thoughts-controls">
      <div class="search-box">
        <Icon name="search" size={16} />
        <input
          type="text"
          placeholder="Search thoughts..."
          bind:value={searchQuery}
          class="search-input"
        />
      </div>

      <div class="filter-controls">
        <select bind:value={selectedType} class="type-filter">
          <option value="all">All Types</option>
          {#each thoughtTypes as type}
            <option value={type}>{type}</option>
          {/each}
        </select>

        <select bind:value={sortBy} class="sort-filter">
          <option value="recent">Most Recent</option>
          <option value="title">Alphabetical</option>
        </select>
      </div>
    </div>
  </header>

  <main class="thoughts-content">
    {#if isLoading}
      <div class="loading-container">
        <Spinner />
        <p>Loading thoughts...</p>
      </div>
    {:else if error}
      <ErrorMessage message={error.message} />
      <div class="error-actions">
        <button on:click={loadThoughts} class="btn-primary">
          <Icon name="refresh-cw" size={16} />
          Try Again
        </button>
      </div>
    {:else if filteredThoughts.length === 0}
      <div class="empty-state">
        <Icon name="brain" size={64} />
        <h2>No thoughts found</h2>
        <p>
          {#if searchQuery}
            No thoughts match your search for "{searchQuery}"
          {:else}
            Start capturing your thoughts and they'll appear here
          {/if}
        </p>
        <button on:click={() => goto('/capture')} class="btn-primary">
          <Icon name="plus" size={16} />
          Add First Thought
        </button>
      </div>
    {:else}
      <div class="thoughts-stats">
        <span class="stat">
          {filteredThoughts.length} thought{filteredThoughts.length !== 1 ? 's' : ''}
          {#if searchQuery}matching "{searchQuery}"{/if}
        </span>
      </div>

      <div class="thoughts-grid">
        {#each filteredThoughts as thought (thought.id)}
          <div class="thought-card-wrapper">
            <ItemCard 
              item={thought} 
              on:click={() => handleThoughtClick(thought)}
            />
          </div>
        {/each}
      </div>
    {/if}
  </main>
</div>

<style>
  .thoughts-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  .thoughts-header {
    margin-bottom: 2rem;
  }

  .header-content {
    margin-bottom: 2rem;
  }

  .page-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
  }

  .page-description {
    font-size: 1.125rem;
    color: var(--text-secondary);
    margin: 0;
  }

  .thoughts-controls {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
  }

  .search-box {
    position: relative;
    flex: 1;
    min-width: 300px;
  }

  .search-box :global(svg) {
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-secondary);
    pointer-events: none;
  }

  .search-input {
    width: 100%;
    padding: 0.75rem 1rem 0.75rem 2.5rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    background: var(--background-secondary);
    color: var(--text-primary);
    font-size: 1rem;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-alpha);
  }

  .filter-controls {
    display: flex;
    gap: 0.5rem;
  }

  .type-filter,
  .sort-filter {
    padding: 0.75rem 1rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    background: var(--background-secondary);
    color: var(--text-primary);
    font-size: 0.875rem;
    cursor: pointer;
  }

  .thoughts-content {
    min-height: 400px;
  }

  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 4rem;
  }

  .empty-state {
    text-align: center;
    padding: 4rem;
    color: var(--text-secondary);
  }

  .empty-state :global(svg) {
    opacity: 0.5;
    margin-bottom: 1.5rem;
  }

  .empty-state h2 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
  }

  .empty-state p {
    margin-bottom: 2rem;
  }

  .thoughts-stats {
    margin-bottom: 1.5rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .thoughts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .thought-card-wrapper {
    height: fit-content;
  }

  .error-actions {
    display: flex;
    justify-content: center;
    margin-top: 1rem;
  }

  .btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: var(--accent);
    color: var(--accent-text);
    border: none;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-primary:hover {
    background: var(--accent-hover);
  }

  @media (max-width: 768px) {
    .thoughts-container {
      padding: 1rem;
    }

    .page-title {
      font-size: 2rem;
    }

    .thoughts-controls {
      flex-direction: column;
      align-items: stretch;
    }

    .search-box {
      min-width: auto;
    }

    .filter-controls {
      justify-content: space-between;
    }

    .thoughts-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
