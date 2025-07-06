<script>
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  
  let recentItems = [];
  let stats = {
    totalItems: 0,
    todayItems: 0,
    totalTags: 0
  };
  
  let mounted = false;
  
  onMount(async () => {
    mounted = true;
    // TODO: Fetch from API
    // const res = await fetch('/api/dashboard');
    // const data = await res.json();
    // recentItems = data.recentItems;
    // stats = data.stats;
  });
</script>

<div class="container animate-in">
  <div class="hero">
    <div class="hero-badge animate-float">
      <Icon name="sparkles" size="small" />
      <span>AI-Powered Knowledge Vault</span>
    </div>
    <h1 class="red-gradient-text">Your Second Brain,<br/>Supercharged</h1>
    <p class="hero-description">Capture anything with a single keystroke. Search everything instantly.<br/>Never lose a brilliant idea again.</p>
    
    <div class="quick-actions">
      <a href="/capture" class="action-card capture-card">
        <div class="card-icon">
          <Icon name="capture" size="large" />
        </div>
        <div class="card-content">
          <h3>Quick Capture</h3>
          <p>Save URLs, text, or files instantly</p>
        </div>
        <span class="keyboard-hint floating">⌘N</span>
        <div class="card-glow"></div>
      </a>
      
      <a href="/search" class="action-card search-card">
        <div class="card-icon">
          <Icon name="search" size="large" />
        </div>
        <div class="card-content">
          <h3>Smart Search</h3>
          <p>Find anything you've saved in seconds</p>
        </div>
        <span class="keyboard-hint floating">⌘K</span>
        <div class="card-glow"></div>
      </a>
    </div>
  </div>
  
  <div class="stats-section">
    <div class="stats-grid">
      <div class="stat-card {mounted ? 'animate-slide' : ''}">
        <div class="stat-icon">
          <Icon name="link" size="medium" color="var(--accent)" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{stats.totalItems}</div>
          <div class="stat-label">Total Items</div>
        </div>
      </div>
      
      <div class="stat-card {mounted ? 'animate-slide' : ''}" style="animation-delay: 100ms">
        <div class="stat-icon">
          <Icon name="calendar" size="medium" color="var(--success)" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{stats.todayItems}</div>
          <div class="stat-label">Today</div>
        </div>
      </div>
      
      <div class="stat-card {mounted ? 'animate-slide' : ''}" style="animation-delay: 200ms">
        <div class="stat-icon">
          <Icon name="tag" size="medium" color="var(--warning)" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{stats.totalTags}</div>
          <div class="stat-label">Tags</div>
        </div>
      </div>
    </div>
  </div>
  
  <div class="recent-section">
    <div class="section-header">
      <h2>Recent Captures</h2>
      <a href="/timeline" class="view-all">
        View all
        <Icon name="arrow-right" size="small" />
      </a>
    </div>
    
    {#if recentItems.length > 0}
      <div class="items-grid">
        {#each recentItems as item, i}
          <div class="item-card" style="animation-delay: {300 + i * 50}ms">
            <div class="item-header">
              <h4>{item.title}</h4>
              <Icon name="external-link" size="small" color="var(--text-muted)" />
            </div>
            <p>{item.summary}</p>
            <div class="item-footer">
              <time>{new Date(item.created_at).toLocaleDateString()}</time>
              <div class="item-tags">
                {#each item.tags || [] as tag}
                  <span class="tag">{tag}</span>
                {/each}
              </div>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="empty-state">
        <div class="empty-icon animate-pulse">
          <Icon name="capture" size="large" color="var(--text-muted)" />
        </div>
        <p>No items yet. Press <span class="keyboard-hint">⌘N</span> to capture your first item.</p>
        <button class="btn-red" onclick="window.location.href='/capture'">
          <Icon name="plus" size="small" />
          Start Capturing
        </button>
      </div>
    {/if}
  </div>
</div>

<style>
  .hero {
    text-align: center;
    padding: 4rem 0 3rem;
    position: relative;
  }
  
  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(74, 158, 255, 0.1);
    border: 1px solid rgba(74, 158, 255, 0.3);
    border-radius: 100px;
    font-size: 0.875rem;
    color: var(--accent);
    margin-bottom: 2rem;
    font-weight: 600;
  }
  
  .hero h1 {
    font-size: 3.5rem;
    margin-bottom: 1rem;
    font-weight: 800;
    line-height: 1.1;
  }
  
  @media (max-width: 768px) {
    .hero h1 {
      font-size: 2.5rem;
    }
  }
  
  .hero-description {
    color: var(--text-secondary);
    font-size: 1.25rem;
    margin-bottom: 3rem;
    line-height: 1.6;
    font-weight: 500;
  }
  
  .quick-actions {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    max-width: 700px;
    margin: 0 auto;
  }
  
  .action-card {
    background: var(--bg-secondary);
    border: 2px solid transparent;
    border-radius: var(--radius-lg);
    padding: 2rem;
    transition: all var(--transition-base);
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    position: relative;
    overflow: hidden;
    cursor: pointer;
  }
  
  .card-icon {
    width: 60px;
    height: 60px;
    background: var(--bg-tertiary);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1.5rem;
    transition: all var(--transition-base);
  }
  
  .capture-card .card-icon {
    background: rgba(74, 158, 255, 0.1);
    color: var(--accent);
  }
  
  .search-card .card-icon {
    background: rgba(139, 92, 246, 0.1);
    color: #8b5cf6;
  }
  
  .card-content h3 {
    margin: 0 0 0.5rem;
    color: var(--text-primary);
    font-size: 1.25rem;
    font-weight: 700;
  }
  
  .card-content p {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.9375rem;
    line-height: 1.5;
  }
  
  .action-card .keyboard-hint {
    position: absolute;
    top: 1.5rem;
    right: 1.5rem;
  }
  
  .floating {
    animation: float 3s ease-in-out infinite;
  }
  
  .card-glow {
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(74, 158, 255, 0.1) 0%, transparent 70%);
    opacity: 0;
    transition: opacity var(--transition-slow);
    pointer-events: none;
  }
  
  .action-card:hover {
    transform: translateY(-4px);
    border-color: var(--border);
    box-shadow: var(--shadow-lg);
  }
  
  .action-card:hover .card-icon {
    transform: scale(1.1);
  }
  
  .action-card:hover .card-glow {
    opacity: 1;
  }
  
  .stats-section {
    margin: 6rem 0 4rem;
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
  }
  
  .stat-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.75rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    transition: all var(--transition-base);
  }
  
  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent);
  }
  
  .stat-icon {
    width: 48px;
    height: 48px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  
  .stat-content {
    flex: 1;
  }
  
  .stat-value {
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1;
    font-family: var(--font-display);
    background: linear-gradient(135deg, var(--text-primary), var(--text-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .stat-label {
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
  }
  
  .recent-section {
    margin: 4rem 0;
  }
  
  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2rem;
  }
  
  .section-header h2 {
    margin: 0;
  }
  
  .view-all {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--accent);
    font-weight: 600;
    transition: all var(--transition-fast);
  }
  
  .view-all:hover {
    transform: translateX(4px);
  }
  
  .items-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.5rem;
  }
  
  .item-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    transition: all var(--transition-base);
    cursor: pointer;
    animation: fadeIn var(--transition-slow) ease-out forwards;
    opacity: 0;
  }
  
  .item-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent);
  }
  
  .item-header {
    display: flex;
    align-items: start;
    justify-content: space-between;
    margin-bottom: 0.75rem;
  }
  
  .item-header h4 {
    margin: 0;
    font-size: 1.125rem;
    line-height: 1.4;
  }
  
  .item-card p {
    color: var(--text-secondary);
    font-size: 0.9375rem;
    line-height: 1.6;
    margin: 0 0 1rem;
  }
  
  .item-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }
  
  .item-footer time {
    color: var(--text-muted);
    font-size: 0.8125rem;
    font-weight: 500;
  }
  
  .item-tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .tag {
    padding: 0.25rem 0.625rem;
    background: var(--bg-tertiary);
    border-radius: 100px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-weight: 600;
    transition: all var(--transition-fast);
  }
  
  .tag:hover {
    background: var(--accent);
    color: white;
  }
  
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: var(--bg-secondary);
    border: 2px dashed var(--border);
    border-radius: var(--radius-lg);
  }
  
  .empty-icon {
    width: 80px;
    height: 80px;
    background: var(--bg-tertiary);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 2rem;
  }
  
  .empty-state p {
    color: var(--text-secondary);
    font-size: 1.125rem;
    margin-bottom: 2rem;
  }
  
  .btn-primary {
    background: var(--accent);
    color: white;
    border: none;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    padding: 1rem 2rem;
  }
  
  .btn-primary:hover {
    background: var(--accent-hover);
  }
  
  .btn-red {
    background: var(--man-united-red);
    color: white;
    border: none;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    padding: 1rem 2rem;
  }
  
  .btn-red:hover {
    background: var(--accent-red-hover);
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.3);
  }
  
  .red-gradient-text {
    background: linear-gradient(135deg, var(--man-united-red), #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
</style>