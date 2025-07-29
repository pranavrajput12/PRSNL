<!--
  Breadcrumbs Navigation Component
  
  Provides hierarchical navigation showing the user's current location
  within the site structure.
-->

<script lang="ts">
  import Icon from '$lib/components/Icon.svelte';
  
  export let items: Array<{
    label: string;
    path: string;
    active?: boolean;
  }> = [];
  
  $: filteredItems = items.filter(item => item.label && item.label.trim());
</script>

{#if filteredItems.length > 0}
  <nav class="breadcrumbs" aria-label="Breadcrumb navigation">
    <ol class="breadcrumb-list">
      {#each filteredItems as item, index}
        <li class="breadcrumb-item">
          {#if index > 0}
            <span class="breadcrumb-separator" aria-hidden="true">
              <Icon name="chevron-right" size="small" />
            </span>
          {/if}
          
          {#if item.active || !item.path}
            <span class="breadcrumb-current" aria-current="page">
              {item.label}
            </span>
          {:else}
            <a 
              href={item.path} 
              class="breadcrumb-link"
              data-sveltekit-preload-data="hover"
            >
              {item.label}
            </a>
          {/if}
        </li>
      {/each}
    </ol>
  </nav>
{/if}

<style>
  .breadcrumbs {
    margin-bottom: 1rem;
  }
  
  .breadcrumb-list {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.25rem;
    list-style: none;
    margin: 0;
    padding: 0;
  }
  
  .breadcrumb-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
  
  .breadcrumb-separator {
    color: var(--text-muted);
    display: flex;
    align-items: center;
  }
  
  .breadcrumb-link {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.9rem;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    transition: all 0.2s;
    line-height: 1.4;
  }
  
  .breadcrumb-link:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.1);
  }
  
  .breadcrumb-current {
    color: var(--neural-green);
    font-weight: 500;
    font-size: 0.9rem;
    padding: 0.25rem 0.5rem;
    line-height: 1.4;
  }
  
  /* Responsive design */
  @media (max-width: 768px) {
    .breadcrumb-list {
      font-size: 0.85rem;
    }
    
    .breadcrumb-link,
    .breadcrumb-current {
      padding: 0.2rem 0.4rem;
      font-size: 0.85rem;
    }
  }
  
  /* Truncate long breadcrumbs on very small screens */
  @media (max-width: 480px) {
    .breadcrumb-item:not(:first-child):not(:last-child) {
      display: none;
    }
    
    .breadcrumb-item:nth-last-child(2)::after {
      content: '...';
      color: var(--text-muted);
      margin: 0 0.25rem;
    }
  }
</style>