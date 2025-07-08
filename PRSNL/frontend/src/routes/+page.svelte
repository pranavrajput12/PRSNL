<script lang="ts">
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import { getTimeline, getTags } from '$lib/api';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import SkeletonLoader from '$lib/components/SkeletonLoader.svelte';
  import SmartFeed from '$lib/components/SmartFeed.svelte';
  import AnimatedButton from '$lib/components/AnimatedButton.svelte';
  import GlassCard from '$lib/components/GlassCard.svelte';
  import PremiumInteractions from '$lib/components/PremiumInteractions.svelte';
  
  type Item = {
    id: string;
    title: string;
    url?: string;
    summary: string;
    tags: string[];
    createdAt: string;
    type?: string;
    item_type?: string;
    file_path?: string;
    thumbnail_url?: string;
    duration?: number;
    platform?: string;
    status?: string;
  };
  
  let recentItems: Item[] = [];
  let stats = {
    totalItems: 0,
    todayItems: 0,
    totalTags: 0
  };
  
  let mounted = false;
  let isLoading = true;
  let error: Error | null = null;
  let viewMode: 'smart' | 'classic' = 'smart';
  
  onMount(async () => {
    mounted = true;
    await loadData();
  });
  
  async function loadData() {
    try {
      isLoading = true;
      error = null;
      
      console.log('Starting to load data...');
      
      // Fetch recent items from timeline
      const timelineResponse = await getTimeline(1);
      console.log('Timeline response:', timelineResponse);
      
      recentItems = timelineResponse.items?.slice(0, 6) || [];
      console.log('Recent items:', recentItems);
      console.log('First item detail:', recentItems[0]);
      
      // Calculate stats
      const today = new Date();
      const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate());
      
      let todayCount = 0;
      
      // Count today's items
      if (timelineResponse.items) {
        timelineResponse.items.forEach((item: Item) => {
          const itemDate = new Date(item.createdAt);
          if (itemDate >= todayStart) {
            todayCount++;
          }
        });
      }
      
      // Get tags
      const tagsResponse = await getTags();
      console.log('Tags response:', tagsResponse);
      
      const tagsCount = tagsResponse?.tags?.length || 0;
      
      stats = {
        totalItems: timelineResponse.total || 0,
        todayItems: todayCount,
        totalTags: tagsCount
      };
      
      console.log('Final stats:', stats);
    } catch (err) {
      console.error('Error loading data:', err);
      error = err instanceof Error ? err : new Error(String(err));
    } finally {
      isLoading = false;
    }
  }
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
      <PremiumInteractions variant="hover" intensity="medium">
        <GlassCard variant="elevated" interactive={true} glowColor="#6366f1">
          <a href="/capture" class="action-card capture-card">
            <div class="card-icon">
              <Icon name="capture" size="large" />
            </div>
            <div class="card-content">
              <h3>Quick Capture</h3>
              <p>Save URLs, text, or files instantly</p>
            </div>
            <span class="keyboard-hint floating">⌘N</span>
          </a>
        </GlassCard>
      </PremiumInteractions>
      
      <PremiumInteractions variant="hover" intensity="medium">
        <GlassCard variant="elevated" interactive={true} glowColor="#8b5cf6">
          <a href="/search" class="action-card search-card">
            <div class="card-icon">
              <Icon name="search" size="large" />
            </div>
            <div class="card-content">
              <h3>Smart Search</h3>
              <p>Find anything you've saved in seconds</p>
            </div>
            <span class="keyboard-hint floating">⌘K</span>
          </a>
        </GlassCard>
      </PremiumInteractions>
    </div>
  </div>
  
  <div class="stats-section">
    {#if error}
      <ErrorMessage 
        message="Failed to load data" 
        details={error.message} 
        retry={() => { loadData(); }} 
        dismiss={() => { error = null; }} 
      />
    {/if}

    <div class="stats-grid">
      <PremiumInteractions variant="hover" intensity="subtle">
        <GlassCard variant="gradient" interactive={true} glowColor="#6366f1">
          <div class="stat-card {mounted ? 'animate-slide' : ''}">
            <div class="stat-icon">
              <Icon name="link" size="medium" color="var(--accent)" />
            </div>
            <div class="stat-content">
              {#if isLoading}
                <div class="stat-value loading"><Spinner size="small" /></div>
              {:else}
                <div class="stat-value">{stats.totalItems}</div>
              {/if}
              <div class="stat-label">Total Items</div>
            </div>
          </div>
        </GlassCard>
      </PremiumInteractions>
      
      <PremiumInteractions variant="hover" intensity="subtle">
        <GlassCard variant="gradient" interactive={true} glowColor="#10b981">
          <div class="stat-card {mounted ? 'animate-slide' : ''}" style="animation-delay: 100ms">
            <div class="stat-icon">
              <Icon name="calendar" size="medium" color="var(--success)" />
            </div>
            <div class="stat-content">
              {#if isLoading}
                <div class="stat-value loading"><Spinner size="small" /></div>
              {:else}
                <div class="stat-value">{stats.todayItems}</div>
              {/if}
              <div class="stat-label">Today</div>
            </div>
          </div>
        </GlassCard>
      </PremiumInteractions>
      
      <PremiumInteractions variant="hover" intensity="subtle">
        <GlassCard variant="gradient" interactive={true} glowColor="#f59e0b">
          <div class="stat-card {mounted ? 'animate-slide' : ''}" style="animation-delay: 200ms">
            <div class="stat-icon">
              <Icon name="tag" size="medium" color="var(--warning)" />
            </div>
            <div class="stat-content">
              {#if isLoading}
                <div class="stat-value loading"><Spinner size="small" /></div>
              {:else}
                <div class="stat-value">{stats.totalTags}</div>
              {/if}
              <div class="stat-label">Tags</div>
            </div>
          </div>
        </GlassCard>
      </PremiumInteractions>
    </div>
  </div>
  
  <div class="recent-section">
    <div class="section-header">
      <h2>{viewMode === 'smart' ? 'Your Knowledge Feed' : 'Recent Captures'}</h2>
      <div class="view-controls">
        <button 
          class="view-toggle"
          class:active={viewMode === 'smart'}
          on:click={() => viewMode = 'smart'}
        >
          <Icon name="sparkles" size="small" />
          Smart Feed
        </button>
        <button 
          class="view-toggle"
          class:active={viewMode === 'classic'}
          on:click={() => viewMode = 'classic'}
        >
          <Icon name="grid" size="small" />
          Classic View
        </button>
        <a href="/timeline" class="view-all">
          View all
          <Icon name="arrow-right" size="small" />
        </a>
      </div>
    </div>
    
    {#if viewMode === 'smart'}
      <SmartFeed mode="smart" />
    {:else if isLoading}
      <SkeletonLoader type="card" count={6} />
    {:else if recentItems.length > 0}
      <div class="items-grid">
        {#each recentItems as item, i}
          <PremiumInteractions variant="hover" intensity="subtle">
            <GlassCard variant="default" interactive={true}>
              <div class="item-card {item.status === 'pending' ? 'pending' : ''}" style="animation-delay: {300 + i * 50}ms">
            <div class="item-header">
              <h4>{item.title}</h4>
              <div class="item-header-icons">
                {#if item.status === 'pending'}
                  <div class="pending-indicator" title="Processing...">
                    <Spinner size="small" />
                  </div>
                {/if}
                <Icon name={item.item_type === 'video' ? 'video' : 'external-link'} size="small" color="var(--text-muted)" />
              </div>
            </div>
            
            {#if item.item_type === 'video' && item.file_path}
              <div class="item-video">
                <VideoPlayer 
                  src={`/api/videos/${item.id}/stream`}
                  thumbnail={item.thumbnail_url}
                  title={item.title}
                  duration={item.duration}
                />
              </div>
            {:else if item.status === 'pending'}
              <p class="pending-message">Processing content...</p>
            {:else}
              <p>{item.summary}</p>
            {/if}
            <div class="item-footer">
              <time>{new Date(item.createdAt).toLocaleDateString()}</time>
              <div class="item-tags">
                {#each item.tags || [] as tag}
                  <span class="tag">{tag}</span>
                {/each}
              </div>
            </div>
              </div>
            </GlassCard>
          </PremiumInteractions>
        {/each}
      </div>
    {:else}
      <div class="empty-state">
        <div class="empty-icon animate-pulse">
          <Icon name="capture" size="large" color="var(--text-muted)" />
        </div>
        <p>No items yet. Press <span class="keyboard-hint">⌘N</span> to capture your first item.</p>
        <AnimatedButton 
          variant="primary" 
          size="large" 
          icon="plus"
          on:click={() => window.location.href = '/capture'}
        >
          Start Capturing
        </AnimatedButton>
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
    padding: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    text-decoration: none;
    color: inherit;
    min-height: 200px;
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
    padding: 1.75rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    transition: all var(--transition-base);
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
  
  .view-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .view-toggle {
    padding: 0.5rem 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .view-toggle:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
  
  .view-toggle.active {
    background: var(--accent);
    color: var(--accent-text);
    border-color: var(--accent);
  }
  
  .view-all {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--accent);
    font-weight: 600;
    transition: all var(--transition-fast);
    margin-left: auto;
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
    padding: 1.5rem;
    transition: all var(--transition-base);
    cursor: pointer;
    animation: fadeIn var(--transition-slow) ease-out forwards;
    opacity: 1;
    position: relative;
    overflow: hidden;
    min-height: 250px;
  }
  
  .item-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--accent), var(--accent-red));
    transform: translateX(-100%);
    transition: transform var(--transition-base);
  }
  
  .item-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--accent);
  }
  
  .item-card:hover::before {
    transform: translateX(0);
  }
  
  .item-header {
    display: flex;
    align-items: start;
    justify-content: space-between;
    margin-bottom: 0.75rem;
  }
  
  .item-header-icons {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .pending-indicator {
    display: flex;
    align-items: center;
  }
  
  .item-card.pending {
    opacity: 0.8;
    border-style: dashed;
  }
  
  .pending-message {
    color: var(--text-muted);
    font-style: italic;
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
  
  .item-video {
    margin: 0.75rem -1.5rem 1rem -1.5rem;
    border-radius: 0;
    overflow: hidden;
    background: #000;
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
  
  /* Animations */
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>