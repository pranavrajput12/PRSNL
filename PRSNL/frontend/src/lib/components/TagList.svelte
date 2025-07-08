<script>
  import Icon from './Icon.svelte';
  
  export let tags = [];
  export let maxTags = 5;
  export let itemId = '';
  
  let expanded = false;
  
  $: visibleTags = expanded ? tags : tags.slice(0, maxTags);
  $: remainingCount = tags.length - maxTags;
  $: hasMore = tags.length > maxTags;
</script>

{#if tags?.length > 0}
  <div class="item-tags">
    {#each visibleTags as tag}
      <span class="tag">
        <Icon name="tag" size="small" />
        {tag}
      </span>
    {/each}
    
    {#if hasMore}
      <button 
        class="more-tags-btn"
        on:click|stopPropagation={() => expanded = !expanded}
        title={expanded ? 'Show less' : `Show ${remainingCount} more`}
      >
        {#if expanded}
          <Icon name="chevron-up" size="small" />
          Less
        {:else}
          <Icon name="plus" size="small" />
          +{remainingCount}
        {/if}
      </button>
    {/if}
  </div>
{/if}

<style>
  .item-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
  }
  
  .tag {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    color: var(--text-secondary);
    white-space: nowrap;
  }
  
  .more-tags-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    color: var(--accent);
    cursor: pointer;
    transition: all var(--transition-fast);
    font-weight: 500;
  }
  
  .more-tags-btn:hover {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
  }
</style>