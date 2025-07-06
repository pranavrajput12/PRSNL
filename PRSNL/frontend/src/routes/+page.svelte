<script lang="ts">
  import { onMount } from 'svelte';
  
  let recentItems: any[] = [];
  let stats = {
    totalItems: 0,
    todayItems: 0,
    totalTags: 0
  };
  
  onMount(async () => {
    // TODO: Fetch from API
    // const res = await fetch('/api/dashboard');
    // const data = await res.json();
    // recentItems = data.recentItems;
    // stats = data.stats;
  });
</script>

<div class="container">
  <div class="hero">
    <h1>Your Personal Knowledge Vault</h1>
    <p>Capture anything with a single keystroke. Search everything instantly.</p>
    <div class="quick-actions">
      <a href="/capture" class="action-card">
        <h3>Quick Capture</h3>
        <p>Save URLs, text, or files instantly</p>
        <span class="keyboard-hint">⌘N</span>
      </a>
      <a href="/search" class="action-card">
        <h3>Search Everything</h3>
        <p>Find anything you've saved</p>
        <span class="keyboard-hint">⌘K</span>
      </a>
    </div>
  </div>
  
  <div class="stats">
    <div class="stat">
      <div class="stat-value">{stats.totalItems}</div>
      <div class="stat-label">Total Items</div>
    </div>
    <div class="stat">
      <div class="stat-value">{stats.todayItems}</div>
      <div class="stat-label">Today</div>
    </div>
    <div class="stat">
      <div class="stat-value">{stats.totalTags}</div>
      <div class="stat-label">Tags</div>
    </div>
  </div>
  
  <div class="recent">
    <h2>Recent Captures</h2>
    {#if recentItems.length > 0}
      <div class="items-grid">
        {#each recentItems as item}
          <div class="item-card">
            <h4>{item.title}</h4>
            <p>{item.summary}</p>
            <time>{new Date(item.created_at).toLocaleDateString()}</time>
          </div>
        {/each}
      </div>
    {:else}
      <p class="empty-state">No items yet. Press <span class="keyboard-hint">⌘N</span> to capture your first item.</p>
    {/if}
  </div>
</div>

<style>
  .hero {
    text-align: center;
    padding: 3rem 0;
  }
  
  .hero h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }
  
  .hero p {
    color: var(--text-secondary);
    font-size: 1.125rem;
    margin-bottom: 2rem;
  }
  
  .quick-actions {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    max-width: 600px;
    margin: 0 auto;
  }
  
  .action-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    transition: all 0.2s;
    display: block;
    position: relative;
  }
  
  .action-card:hover {
    background: var(--bg-tertiary);
    border-color: var(--accent);
    transform: translateY(-2px);
  }
  
  .action-card h3 {
    margin: 0 0 0.5rem;
    color: var(--text-primary);
  }
  
  .action-card p {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
  
  .action-card .keyboard-hint {
    position: absolute;
    top: 1rem;
    right: 1rem;
  }
  
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 3rem 0;
  }
  
  .stat {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    text-align: center;
  }
  
  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent);
  }
  
  .stat-label {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
  
  .recent {
    margin: 3rem 0;
  }
  
  .items-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
  }
  
  .item-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
  }
  
  .item-card h4 {
    margin: 0 0 0.5rem;
  }
  
  .item-card p {
    color: var(--text-secondary);
    font-size: 0.875rem;
    margin: 0 0 0.5rem;
  }
  
  .item-card time {
    color: var(--text-muted);
    font-size: 0.75rem;
  }
  
  .empty-state {
    text-align: center;
    color: var(--text-secondary);
    padding: 2rem;
  }
</style>