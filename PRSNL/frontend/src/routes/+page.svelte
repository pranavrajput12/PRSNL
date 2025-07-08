<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import { getTimeline, getTags, searchItems } from '$lib/api';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import SkeletonLoader from '$lib/components/SkeletonLoader.svelte';
  import AnimatedButton from '$lib/components/AnimatedButton.svelte';
  import GlassCard from '$lib/components/GlassCard.svelte';
  import PremiumInteractions from '$lib/components/PremiumInteractions.svelte';
  import TagList from '$lib/components/TagList.svelte';
  import Calendar3D from '$lib/components/Calendar3D.svelte';
  
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
  let timelineItems: Item[] = [];
  let stats = {
    totalItems: 0,
    todayItems: 0,
    totalTags: 0
  };
  
  let mounted = false;
  let isLoading = true;
  let error: Error | null = null;
  
  // Search state
  let searchQuery = '';
  let searchResults: Item[] = [];
  let isSearching = false;
  let searchTimeout: ReturnType<typeof setTimeout> | undefined;
  let hasSearched = false;
  let searchMode: 'keyword' | 'semantic' | 'hybrid' = 'semantic';
  let showSearchResults = false;
  
  onMount(async () => {
    mounted = true;
    await loadData();
  });
  
  onDestroy(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
  });
  
  async function loadData() {
    try {
      isLoading = true;
      error = null;
      
      console.log('Starting to load data...');
      
      // Fetch recent items from timeline
      const timelineResponse = await getTimeline(1);
      console.log('Timeline response:', timelineResponse);
      
      // Get all items for the calendar
      timelineItems = timelineResponse.items || [];
      // Get recent items for display
      recentItems = timelineResponse.items?.slice(0, 6) || [];
      console.log('Timeline items:', timelineItems.length);
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
  
  async function handleSearch() {
    if (!searchQuery.trim()) {
      searchResults = [];
      hasSearched = false;
      showSearchResults = false;
      return;
    }
    
    isSearching = true;
    hasSearched = true;
    showSearchResults = true;
    
    try {
      const response = await searchItems(searchQuery, {
        mode: searchMode,
        limit: 10
      });
      
      // Transform results to match Item type
      searchResults = response.results.map(result => ({
        id: result.id,
        title: result.title,
        url: result.url || '',
        summary: result.snippet,
        tags: result.tags,
        createdAt: result.created_at,
        type: result.type,
        item_type: result.type,
        similarity_score: result.similarity_score
      }));
    } catch (err) {
      console.error('Search error:', err);
      searchResults = [];
    } finally {
      isSearching = false;
    }
  }
  
  function handleSearchInput() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(handleSearch, 300);
  }
  
  function clearSearch() {
    searchQuery = '';
    searchResults = [];
    hasSearched = false;
    showSearchResults = false;
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
          <a href="/insights" class="action-card insights-card">
            <div class="card-icon">
              <Icon name="sparkles" size="large" />
            </div>
            <div class="card-content">
              <h3>AI Insights</h3>
              <p>Discover patterns in your knowledge</p>
            </div>
            <span class="keyboard-hint floating">⌘I</span>
          </a>
        </GlassCard>
      </PremiumInteractions>
    </div>
  </div>
  
  <!-- Integrated Search Section -->
  <div class="search-section">
    <div class="integrated-search">
          <div class="search-header">
            <div class="search-title">
              <Icon name="search" size="medium" color="var(--accent)" />
              <h2>Smart Search</h2>
            </div>
            <div class="search-modes">
              <button
                class="mode-toggle {searchMode === 'keyword' ? 'active' : ''}"
                on:click={() => { searchMode = 'keyword'; if (searchQuery) handleSearch(); }}
              >
                <Icon name="search" size="small" />
                Keyword
              </button>
              <button
                class="mode-toggle {searchMode === 'semantic' ? 'active' : ''}"
                on:click={() => { searchMode = 'semantic'; if (searchQuery) handleSearch(); }}
              >
                <Icon name="tag" size="small" />
                Semantic
              </button>
              <button
                class="mode-toggle {searchMode === 'hybrid' ? 'active' : ''}"
                on:click={() => { searchMode = 'hybrid'; if (searchQuery) handleSearch(); }}
              >
                <Icon name="zap" size="small" />
                Hybrid
              </button>
            </div>
          </div>
          
          <div class="search-input-container">
            <div class="search-box {isSearching ? 'searching' : ''}">
              <Icon name="search" size="medium" color="var(--text-muted)" />
              <input
                type="text"
                bind:value={searchQuery}
                placeholder="Search your knowledge vault..."
                on:input={handleSearchInput}
                on:keydown={(e) => e.key === 'Enter' && handleSearch()}
                class="search-input"
              />
              {#if isSearching}
                <Spinner size="small" />
              {:else if searchQuery}
                <button class="clear-btn" on:click={clearSearch}>
                  <Icon name="close" size="small" />
                </button>
              {/if}
            </div>
          </div>
          
          {#if showSearchResults}
            <div class="search-results-container animate-slide">
              {#if isSearching}
                <SkeletonLoader type="search" count={3} />
              {:else if searchResults.length > 0}
                <div class="search-results-header">
                  <span class="results-count">
                    Found {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}
                  </span>
                  <a href="/search?q={encodeURIComponent(searchQuery)}" class="view-all-results">
                    View all results
                    <Icon name="arrow-right" size="small" />
                  </a>
                </div>
                <div class="search-results-list">
                  {#each searchResults.slice(0, 5) as result}
                    <a href="/item/{result.id}" class="search-result-item">
                      <div class="result-icon">
                        <Icon name={result.item_type === 'video' ? 'video' : 'link'} size="small" />
                      </div>
                      <div class="result-content">
                        <h4>{result.title}</h4>
                        <p>{result.summary}</p>
                        {#if searchMode !== 'keyword' && result.similarity_score}
                          <div class="similarity-indicator">
                            <div class="similarity-bar">
                              <div class="similarity-fill" style="width: {result.similarity_score * 100}%"></div>
                            </div>
                            <span class="similarity-text">{Math.round(result.similarity_score * 100)}% match</span>
                          </div>
                        {/if}
                      </div>
                      <Icon name="arrow-right" size="small" class="result-arrow" />
                    </a>
                  {/each}
                </div>
              {:else if hasSearched}
                <div class="no-results">
                  <Icon name="search" size="large" color="var(--text-muted)" />
                  <p>No results found for "{searchQuery}"</p>
                  <span>Try different keywords or search modes</span>
                </div>
              {/if}
            </div>
          {/if}
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
  
  <div class="calendar-section">
    <div class="section-header">
      <h2>Your Knowledge Calendar</h2>
      <a href="/timeline" class="view-all">
        View Timeline
        <Icon name="arrow-right" size="small" />
      </a>
    </div>
    
    {#if isLoading}
      <SkeletonLoader type="card" count={1} />
    {:else}
      <Calendar3D 
        items={timelineItems} 
        onDateClick={(date, items) => {
          const dateStr = date.toISOString().split('T')[0];
          window.location.href = `/timeline?date=${dateStr}`;
        }}
      />
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
  
  .insights-card .card-icon {
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
  
  .calendar-section {
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
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
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
  
  /* Integrated Search Styles */
  .search-section {
    margin: 3rem auto;
    max-width: 1200px;
    padding: 0 2rem;
  }
  
  .integrated-search {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 2rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }
  
  .search-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
  }
  
  .search-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .search-title h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
  }
  
  .search-modes {
    display: flex;
    gap: 0.5rem;
  }
  
  .mode-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
  }
  
  .mode-toggle:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
  
  .mode-toggle.active {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
  }
  
  .search-input-container {
    margin-bottom: 1.5rem;
  }
  
  .search-box {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    background: var(--bg-tertiary);
    border: 2px solid var(--border);
    border-radius: var(--radius-lg);
    transition: all var(--transition-base);
  }
  
  .search-box:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.1);
    background: var(--bg-secondary);
  }
  
  .search-box.searching {
    border-color: var(--accent);
  }
  
  .search-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    font-size: 1.125rem;
    color: var(--text-primary);
    font-weight: 500;
  }
  
  .search-input::placeholder {
    color: var(--text-muted);
    font-weight: 400;
  }
  
  .clear-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0.5rem;
    border-radius: var(--radius);
    transition: all var(--transition-fast);
  }
  
  .clear-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
  
  .search-results-container {
    background: var(--bg-tertiary);
    border-radius: var(--radius);
    padding: 1.5rem;
  }
  
  .search-results-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
  }
  
  .results-count {
    color: var(--text-secondary);
    font-weight: 600;
  }
  
  .view-all-results {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--accent);
    font-weight: 600;
    transition: all var(--transition-fast);
  }
  
  .view-all-results:hover {
    transform: translateX(4px);
  }
  
  .search-results-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .search-result-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    text-decoration: none;
    color: inherit;
    transition: all var(--transition-base);
  }
  
  .search-result-item:hover {
    background: var(--bg-hover);
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: var(--shadow-sm);
  }
  
  .result-icon {
    width: 40px;
    height: 40px;
    background: rgba(74, 158, 255, 0.1);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    color: var(--accent);
  }
  
  .result-content {
    flex: 1;
    min-width: 0;
  }
  
  .result-content h4 {
    margin: 0 0 0.25rem;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .result-content p {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: 1.5;
  }
  
  .similarity-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }
  
  .similarity-bar {
    width: 60px;
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
  }
  
  .similarity-fill {
    height: 100%;
    background: var(--accent);
    transition: width var(--transition-base);
  }
  
  .similarity-text {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 600;
  }
  
  .result-arrow {
    color: var(--text-muted);
    transition: all var(--transition-fast);
  }
  
  .search-result-item:hover .result-arrow {
    color: var(--accent);
    transform: translateX(4px);
  }
  
  .no-results {
    text-align: center;
    padding: 3rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
  }
  
  .no-results p {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  .no-results span {
    color: var(--text-muted);
    font-size: 0.875rem;
  }
  
  @media (max-width: 768px) {
    .search-header {
      flex-direction: column;
      align-items: start;
      gap: 1rem;
    }
    
    .search-modes {
      width: 100%;
    }
    
    .mode-toggle {
      flex: 1;
      font-size: 0.75rem;
      padding: 0.5rem;
    }
  }
</style>