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
  import Mac3D from '$lib/components/Mac3D.svelte';
  import MacMini3D from '$lib/components/MacMini3D.svelte';
  import Webcam3D from '$lib/components/Webcam3D.svelte';
  import SSD3D from '$lib/components/SSD3D.svelte';
  import GraphicsCard3D from '$lib/components/GraphicsCard3D.svelte';
  import Typewriter3D from '$lib/components/Typewriter3D.svelte';
  import Terminal3D from '$lib/components/Terminal3D.svelte';
  import { getTypeIcon } from '$lib/stores/contentTypes';
  import { goto } from '$app/navigation';

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
    totalTags: 0,
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

  // Enhanced search options
  let searchThreshold = 0.3;
  let includeDuplicates = false;
  let searchStats: any = null;

  onMount(async () => {
    mounted = true;
    // Wait for auth to be initialized before making API calls
    const { authStore } = await import('$lib/stores/unified-auth');
    // Small delay to ensure auth state is loaded
    await new Promise(resolve => setTimeout(resolve, 100));
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

      const tagsCount = Array.isArray(tagsResponse) ? tagsResponse.length : 0;

      stats = {
        totalItems: timelineResponse.total || 0,
        todayItems: todayCount,
        totalTags: tagsCount,
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
        limit: 12,
        threshold: searchThreshold,
        include_duplicates: includeDuplicates,
      });

      // Store search metadata for debugging
      searchStats = {
        total: response.total,
        searchType: response.search_type,
        deduplication: response.deduplication,
        weights: response.weights,
      };

      // Transform results to match Item type
      searchResults = response.results.map((result) => ({
        id: result.id,
        title: result.title,
        url: result.url || '',
        summary: result.snippet || '',
        tags: result.tags || [],
        createdAt: result.created_at,
        type: result.type,
        item_type: result.type,
        similarity_score: result.similarity || result.score || 0,
        search_metadata: result.search_metadata,
        component_scores: result.component_scores,
      }));

      console.log('Enhanced search results:', {
        query: searchQuery,
        mode: searchMode,
        results: searchResults.length,
        stats: searchStats,
      });
    } catch (err) {
      console.error('Enhanced search error:', err);
      searchResults = [];
      searchStats = null;
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
  <!-- Motherboard Ecosystem Navigation -->
  <div class="motherboard-hero-section">
    <div class="hero-header">
      <h1 class="hero-title">
        <span class="title-main">PRSNL</span>
        <span class="title-sub">Your Second Brain</span>
      </h1>
      <p class="hero-tagline">Never lose a brilliant idea again</p>
    </div>

    <!-- Side-by-Side Layout: Mac3D Left, Icons Right -->
    <div class="hero-layout">
      <!-- Mac3D Monitor on Left -->
      <div class="hero-mac-left">
        <Mac3D />
      </div>

      <!-- Navigation Icons Grid on Right -->
      <div class="navigation-section-right">
        <div class="navigation-icons-right">
          <div class="icon-item">
            <MacMini3D onClick={() => goto('/dashboard')} tooltip="Dashboard" />
          </div>

          <div class="icon-item">
            <Webcam3D onClick={() => goto('/capture')} tooltip="Capture" />
          </div>

          <div class="icon-item">
            <SSD3D onClick={() => goto('/timeline')} tooltip="Timeline" />
          </div>

          <div class="icon-item">
            <GraphicsCard3D onClick={() => goto('/assistant')} tooltip="Assistant" />
          </div>

          <div class="icon-item">
            <Typewriter3D onClick={() => goto('/conversations')} tooltip="Conversations" />
          </div>

          <div class="icon-item">
            <Terminal3D onClick={() => goto('/code-cortex')} tooltip="Code Cortex" />
          </div>
        </div>

        <!-- System Status Below Icons -->
        <div class="ecosystem-status">
          <div class="status-text">System Status: All Components Online</div>
          <div class="status-indicator active"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Neural Interface Scanner -->
  <div class="neural-interface-section">
    <div class="neural-search-container">
      <div class="neural-header">
        <div class="neural-title">
          <div class="brain-icon-container">
            <Icon name="brain" size="medium" color="var(--brand-accent)" />
            <div class="neural-pulse"></div>
          </div>
          <h2>Neural Interface Scanner</h2>
          <p class="neural-scanner-description">
            Advanced neural pattern recognition system that interfaces with your knowledge network
            using three distinct cognitive processing modes.
          </p>
        </div>

        <div class="brain-regions">
          <div class="brain-region-map">
            <div class="region-connections">
              <div class="synaptic-line line-1"></div>
              <div class="synaptic-line line-2"></div>
              <div class="synaptic-line line-3"></div>
            </div>

            <button
              class="brain-region prefrontal-cortex {searchMode === 'keyword' ? 'active' : ''}"
              on:click={() => {
                searchMode = 'keyword';
                if (searchQuery) handleSearch();
              }}
              title="Prefrontal Cortex - Logical Processing"
            >
              <div class="region-activity keyword-activity"></div>
              <div class="region-label">
                <span class="region-name">Prefrontal</span>
                <span class="region-type">Logical</span>
              </div>
            </button>

            <button
              class="brain-region hippocampus {searchMode === 'semantic' ? 'active' : ''}"
              on:click={() => {
                searchMode = 'semantic';
                if (searchQuery) handleSearch();
              }}
              title="Hippocampus - Memory & Associations"
            >
              <div class="region-activity semantic-activity"></div>
              <div class="region-label">
                <span class="region-name">Hippocampus</span>
                <span class="region-type">Memory</span>
              </div>
            </button>

            <button
              class="brain-region amygdala {searchMode === 'hybrid' ? 'active' : ''}"
              on:click={() => {
                searchMode = 'hybrid';
                if (searchQuery) handleSearch();
              }}
              title="Amygdala - Intuitive Connections"
            >
              <div class="region-activity hybrid-activity"></div>
              <div class="region-label">
                <span class="region-name">Amygdala</span>
                <span class="region-type">Intuitive</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      <div class="neural-probe-container">
        <div class="neural-probe {isSearching ? 'scanning' : ''}">
          <div class="probe-tip">
            <div class="synaptic-connections">
              <div class="synapse synapse-1"></div>
              <div class="synapse synapse-2"></div>
              <div class="synapse synapse-3"></div>
              <div class="synapse synapse-4"></div>
            </div>
          </div>

          <div class="probe-input-field">
            <div class="neural-interface-input">
              <input
                type="text"
                bind:value={searchQuery}
                placeholder="Interface with your neural knowledge network..."
                on:input={handleSearchInput}
                on:keydown={(e) => e.key === 'Enter' && handleSearch()}
                class="neural-input"
              />

              {#if isSearching}
                <div class="neural-processing">
                  <div class="eeg-waveform">
                    <div class="wave-line"></div>
                    <div class="wave-line"></div>
                    <div class="wave-line"></div>
                  </div>
                  <span class="processing-text">Neural processing...</span>
                </div>
              {:else if searchQuery}
                <button class="neural-clear-btn" on:click={clearSearch}>
                  <div class="synaptic-break"></div>
                </button>
              {/if}
            </div>
          </div>

          <div class="probe-connector">
            <div class="connector-pins">
              <div class="pin active"></div>
              <div class="pin active"></div>
              <div class="pin"></div>
              <div class="pin"></div>
            </div>
          </div>
        </div>
      </div>

      {#if showSearchResults}
        <div class="neural-results-container animate-slide">
          {#if isSearching}
            <div class="neural-processing-state">
              <div class="neural-scan-animation">
                <div class="scan-pulse"></div>
                <div class="scan-pulse delay-1"></div>
                <div class="scan-pulse delay-2"></div>
              </div>
              <p>Scanning neural pathways...</p>
            </div>
          {:else if searchResults.length > 0}
            <div class="neural-results-header">
              <div class="results-neural-indicator">
                <div class="neural-activity-indicator"></div>
                <span class="neural-count">
                  {searchResults.length} Memory Trace{searchResults.length !== 1 ? 's' : ''} activated
                </span>
              </div>
              <a href="/search?q={encodeURIComponent(searchQuery)}" class="expand-neural-network">
                Expand network
                <Icon name="arrow-right" size="small" />
              </a>
            </div>
            <div class="neural-results-grid">
              {#each searchResults.slice(0, 5) as result}
                <a href={result.url || `/item/${result.id}`} class="neural-result-node">
                  <div class="node-connection">
                    <div class="connection-pulse"></div>
                  </div>
                  <div class="node-content">
                    <div class="node-icon">
                      <Icon
                        name={getTypeIcon(result.type || result.item_type || 'article')}
                        size="small"
                      />
                    </div>
                    <div class="node-info">
                      <h4>{result.title}</h4>
                      <p>{result.summary}</p>
                      {#if searchMode !== 'keyword' && result.similarity_score}
                        <div class="neural-similarity">
                          <div class="similarity-wave">
                            <div
                              class="wave-strength"
                              style="width: {result.similarity_score * 100}%"
                            ></div>
                          </div>
                          <span class="similarity-strength"
                            >{Math.round(result.similarity_score * 100)}% neural match</span
                          >
                          {#if result.component_scores && searchMode === 'hybrid'}
                            <div class="component-scores">
                              {#if result.component_scores.semantic}
                                <span class="score-component semantic"
                                  >S: {Math.round(result.component_scores.semantic * 100)}%</span
                                >
                              {/if}
                              {#if result.component_scores.keyword}
                                <span class="score-component keyword"
                                  >K: {Math.round(result.component_scores.keyword * 100)}%</span
                                >
                              {/if}
                            </div>
                          {/if}
                        </div>
                      {/if}
                    </div>
                    <div class="node-transmission">
                      <div class="transmission-arrow"></div>
                    </div>
                  </div>
                </a>
              {/each}
            </div>
          {:else if hasSearched}
            <div class="neural-no-results">
              <div class="disconnected-neural-icon">
                <Icon name="brain" size="large" color="var(--text-muted)" />
                <div class="disconnection-indicator"></div>
              </div>
              <p>No Memory Traces found for "{searchQuery}"</p>
              <span
                >Try different neural interface modes or keywords to find your Memory Traces</span
              >
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </div>

  <!-- Cognitive Fingerprint Section -->
  <div class="cognitive-fingerprint-section">
    <div class="fingerprint-container">
      <div class="fingerprint-header">
        <div class="terminal-title-bar">
          <span class="terminal-indicator">●</span>
          <span class="terminal-path">cognitive_analysis.exe</span>
          <span class="terminal-status">[RUNNING]</span>
        </div>
        <h3>🧭 The Explorer</h3>
        <div class="confidence-meter">
          <div class="confidence-bar">
            <div class="confidence-fill" style="width: 49%"></div>
          </div>
          <span class="confidence-text">49% confidence</span>
        </div>
      </div>

      <div class="fingerprint-content">
        <div class="traits-metrics">
          <div class="traits-list">
            <span class="trait">curious</span>
            <span class="trait">diverse</span>
            <span class="trait">adventurous</span>
          </div>
          <div class="metrics-compact">
            <div class="metric">
              <span class="metric-label">types:</span>
              <span class="metric-value">9</span>
            </div>
            <div class="metric">
              <span class="metric-label">diversity:</span>
              <span class="metric-value">98</span>
            </div>
            <div class="metric">
              <span class="metric-label">analyzed:</span>
              <span class="metric-value">98</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="stats-section">
    {#if error}
      <ErrorMessage
        message="Failed to load data"
        details={error.message}
        retry={() => {
          loadData();
        }}
        dismiss={() => {
          error = null;
        }}
      />
    {/if}

    <div class="stats-grid">
      <!-- Memory Traces CPU Module -->
      <div class="cpu-module memory {mounted ? 'animate-slide' : ''}">
        <div class="cpu-header">
          <div class="cpu-model">NEURAL-MEM-X1</div>
          <div class="cpu-status"></div>
        </div>
        <div class="cpu-display">
          <div class="cpu-data">
            {#if isLoading}
              <div class="cpu-value"><Spinner size="small" /></div>
            {:else}
              <div class="cpu-value">{stats.totalItems}</div>
            {/if}
            <div class="cpu-label">Memory Traces</div>
            <div class="cpu-sublabel">Active Threads</div>
          </div>
          <div class="cpu-circuit"></div>
        </div>
        <div class="cpu-heatsink"></div>
        <div class="cpu-pins">
          {#each Array(12) as _, i}
            <div class="pin"></div>
          {/each}
        </div>
      </div>

      <!-- Today CPU Module -->
      <div class="cpu-module today {mounted ? 'animate-slide' : ''}" style="animation-delay: 100ms">
        <div class="cpu-header">
          <div class="cpu-model">TEMPORAL-PROC-2</div>
          <div class="cpu-status"></div>
        </div>
        <div class="cpu-display">
          <div class="cpu-data">
            {#if isLoading}
              <div class="cpu-value"><Spinner size="small" /></div>
            {:else}
              <div class="cpu-value">{stats.todayItems}</div>
            {/if}
            <div class="cpu-label">Today</div>
            <div class="cpu-sublabel">Daily Buffer</div>
          </div>
          <div class="cpu-circuit"></div>
        </div>
        <div class="cpu-heatsink"></div>
        <div class="cpu-pins">
          {#each Array(12) as _, i}
            <div class="pin"></div>
          {/each}
        </div>
      </div>

      <!-- Tags CPU Module -->
      <div class="cpu-module tags {mounted ? 'animate-slide' : ''}" style="animation-delay: 200ms">
        <div class="cpu-header">
          <div class="cpu-model">TAG-ENGINE-410</div>
          <div class="cpu-status"></div>
        </div>
        <div class="cpu-display">
          <div class="cpu-data">
            {#if isLoading}
              <div class="cpu-value"><Spinner size="small" /></div>
            {:else}
              <div class="cpu-value">{stats.totalTags}</div>
            {/if}
            <div class="cpu-label">Tags</div>
            <div class="cpu-sublabel">Index Cache</div>
          </div>
          <div class="cpu-circuit"></div>
        </div>
        <div class="cpu-heatsink"></div>
        <div class="cpu-pins">
          {#each Array(12) as _, i}
            <div class="pin"></div>
          {/each}
        </div>
      </div>
    </div>
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

<style>
  .hero {
    padding: 2rem 0;
    position: relative;
    width: 100%;
    margin-bottom: 4rem;
  }

  /* MOTHERBOARD ECOSYSTEM NAVIGATION */
  .motherboard-hero-section {
    padding: 3rem 0 4rem 0;
    position: relative;
    width: 100%;
    margin-bottom: 4rem;
    background: transparent;
    overflow: hidden;
  }

  .hero-header {
    text-align: center;
    margin-bottom: 4rem;
    position: relative;
    z-index: 2;
  }

  .hero-title {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    line-height: 1.1;
  }

  .title-main {
    font-size: 4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00ff64, #00ccff, #ff6600, #ff4081);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation:
      gradient-flow 4s ease-in-out infinite,
      title-glow 3s ease-in-out infinite;
    text-shadow: 0 0 40px rgba(0, 255, 100, 0.4);
    letter-spacing: 0.05em;
    position: relative;
  }

  .title-sub {
    font-size: 1.8rem;
    font-weight: 400;
    color: var(--text-primary);
    opacity: 0.9;
    background: linear-gradient(90deg, #888, #fff, #888);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: subtitle-shimmer 6s ease-in-out infinite;
    letter-spacing: 0.02em;
  }

  .hero-tagline {
    color: var(--text-secondary);
    font-size: 1.3rem;
    font-weight: 300;
    margin: 0;
    opacity: 0.8;
    font-style: italic;
    position: relative;
    padding: 0 2rem;
  }

  .hero-tagline::before {
    content: '"';
    position: absolute;
    left: 0;
    top: -0.2rem;
    font-size: 2rem;
    color: var(--synapse-teal);
    opacity: 0.6;
  }

  .hero-tagline::after {
    content: '"';
    position: absolute;
    right: 0;
    top: -0.2rem;
    font-size: 2rem;
    color: var(--synapse-teal);
    opacity: 0.6;
  }

  @keyframes gradient-flow {
    0% {
      background-position: 0% 50%;
    }
    50% {
      background-position: 100% 50%;
    }
    100% {
      background-position: 0% 50%;
    }
  }

  @keyframes title-glow {
    0%,
    100% {
      filter: brightness(1) drop-shadow(0 0 15px rgba(0, 255, 100, 0.3));
      transform: scale(1);
    }
    50% {
      filter: brightness(1.3) drop-shadow(0 0 30px rgba(0, 255, 100, 0.6));
      transform: scale(1.02);
    }
  }

  @keyframes subtitle-shimmer {
    0%,
    100% {
      opacity: 0.8;
    }
    50% {
      opacity: 1;
    }
  }

  /* SIDE-BY-SIDE HERO LAYOUT */
  .hero-layout {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4rem;
    max-width: 1600px;
    margin: 0 auto;
    padding: 2rem;
  }

  .hero-mac-left {
    flex: 1;
    display: flex;
    justify-content: center;
    transform: scale(1.3);
    padding: 2rem 1rem;
  }

  .navigation-section-right {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2rem;
    padding: 1rem;
  }

  .navigation-icons-right {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    justify-items: center;
    align-items: center;
    width: 100%;
    max-width: 500px;
  }

  .icon-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    transform: scale(1.8);
    transition: all 0.3s ease;
  }

  .icon-item:hover {
    transform: scale(2) translateY(-5px);
  }

  .icon-label {
    font-size: 0.9rem;
    color: var(--text-secondary);
    font-weight: 600;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .ecosystem-status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 1rem 2rem;
    background: rgba(0, 255, 100, 0.1);
    border: 1px solid var(--synapse-teal);
    border-radius: 8px;
    max-width: 400px;
    margin: 0 auto;
  }

  .status-text {
    color: var(--synapse-teal);
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--synapse-teal);
    box-shadow: 0 0 12px var(--synapse-teal);
    animation: status-heartbeat 2s ease-in-out infinite;
  }

  @keyframes status-heartbeat {
    0%,
    100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.7;
      transform: scale(1.3);
    }
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .title-main {
      font-size: 2.5rem;
    }

    .title-sub {
      font-size: 1.3rem;
    }

    .hero-tagline {
      font-size: 1.1rem;
      padding: 0 1rem;
    }

    .hero-header {
      margin-bottom: 3rem;
    }

    .hero-layout {
      flex-direction: column;
      gap: 3rem;
    }

    .hero-mac-left {
      transform: scale(1.1);
    }

    .navigation-section-right {
      padding: 0;
    }

    .navigation-icons-right {
      grid-template-columns: repeat(2, 1fr);
      gap: 1.5rem;
      max-width: 400px;
    }

    .icon-item {
      transform: scale(1.4);
    }

    .icon-item:hover {
      transform: scale(1.6) translateY(-3px);
    }

    .ecosystem-status {
      max-width: 300px;
      padding: 0.8rem 1.5rem;
    }
  }

  /* NEURAL MOTHERBOARD CONSOLE */
  .motherboard-console {
    width: 100%;
    max-width: 1000px;
    margin: 0 auto;
    background: linear-gradient(145deg, var(--bg-secondary), var(--bg-primary));
    border: 3px solid var(--bg-tertiary);
    position: relative;
    box-shadow:
      0 0 60px rgba(0, 0, 0, 0.9),
      inset 0 2px 0 rgba(255, 255, 255, 0.1);
  }

  .motherboard-console::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(
      45deg,
      var(--border),
      var(--bg-secondary),
      var(--border),
      var(--bg-tertiary)
    );
    z-index: -1;
  }

  .console-header {
    background: linear-gradient(90deg, var(--bg-tertiary), var(--bg-secondary), var(--bg-tertiary));
    padding: 15px 25px;
    border-bottom: 2px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .console-brand {
    font-family: var(--font-mono);
    font-size: 1rem;
    color: var(--synapse-teal);
    font-weight: 700;
    letter-spacing: 2px;
  }

  .console-indicators {
    display: flex;
    gap: 15px;
  }

  .indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--text-muted);
  }

  .indicator-light {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--synapse-teal);
    box-shadow: 0 0 10px currentColor;
    animation: system-pulse 2s ease-in-out infinite;
  }

  .indicator-light.red {
    background: var(--brand-accent);
  }
  .indicator-light.orange {
    background: var(--warning);
  }

  @keyframes system-pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.4;
    }
  }

  .console-content {
    padding: 80px 50px;
    position: relative;
    overflow: hidden;
  }

  /* CREATIVE BRAIN NEURAL NETWORK ANIMATION */
  .neural-brain-animation {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    overflow: hidden;
  }

  .brain-hemisphere {
    position: absolute;
    width: 200px;
    height: 150px;
    border: 2px solid rgba(78, 205, 196, 0.2);
    border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
    opacity: 0.3;
  }

  .brain-left {
    top: 20%;
    left: 10%;
    animation: brain-pulse-left 4s ease-in-out infinite;
  }

  .brain-right {
    top: 20%;
    right: 10%;
    transform: scaleX(-1);
    animation: brain-pulse-right 4s ease-in-out infinite 2s;
  }

  @keyframes brain-pulse-left {
    0%,
    100% {
      border-color: rgba(220, 20, 60, 0.2);
      transform: scale(1);
    }
    50% {
      border-color: rgba(220, 20, 60, 0.6);
      transform: scale(1.05);
    }
  }

  @keyframes brain-pulse-right {
    0%,
    100% {
      border-color: rgba(78, 205, 196, 0.2);
      transform: scaleX(-1) scale(1);
    }
    50% {
      border-color: rgba(78, 205, 196, 0.6);
      transform: scaleX(-1) scale(1.05);
    }
  }

  .neural-network {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .neuron {
    position: absolute;
    width: 6px;
    height: 6px;
    background: var(--synapse-teal);
    border-radius: 50%;
    box-shadow: 0 0 10px currentColor;
    animation: neuron-fire 3s ease-in-out infinite;
  }

  .neuron-1 {
    top: 30%;
    left: 20%;
    animation-delay: 0s;
  }
  .neuron-2 {
    top: 25%;
    left: 40%;
    animation-delay: 0.5s;
  }
  .neuron-3 {
    top: 35%;
    left: 60%;
    animation-delay: 1s;
  }
  .neuron-4 {
    top: 40%;
    left: 80%;
    animation-delay: 1.5s;
  }
  .neuron-5 {
    top: 50%;
    left: 25%;
    animation-delay: 2s;
  }
  .neuron-6 {
    top: 55%;
    left: 45%;
    animation-delay: 2.5s;
  }
  .neuron-7 {
    top: 60%;
    left: 65%;
    animation-delay: 3s;
  }
  .neuron-8 {
    top: 70%;
    left: 30%;
    animation-delay: 0.3s;
  }
  .neuron-9 {
    top: 65%;
    left: 75%;
    animation-delay: 1.8s;
  }
  .neuron-10 {
    top: 45%;
    left: 50%;
    animation-delay: 1.2s;
  }

  @keyframes neuron-fire {
    0%,
    80%,
    100% {
      opacity: 0.3;
      transform: scale(1);
      background: var(--synapse-teal);
    }
    10%,
    70% {
      opacity: 1;
      transform: scale(1.5);
      background: var(--brand-accent);
      box-shadow: 0 0 20px var(--brand-accent);
    }
  }

  .synapse {
    position: absolute;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--synapse-teal), transparent);
    opacity: 0;
    animation: synapse-fire 6s ease-in-out infinite;
  }

  .synapse-1 {
    top: 32%;
    left: 22%;
    width: 150px;
    transform: rotate(15deg);
    animation-delay: 0.5s;
  }
  .synapse-2 {
    top: 27%;
    left: 42%;
    width: 120px;
    transform: rotate(-10deg);
    animation-delay: 1s;
  }
  .synapse-3 {
    top: 52%;
    left: 27%;
    width: 180px;
    transform: rotate(25deg);
    animation-delay: 2s;
  }
  .synapse-4 {
    top: 57%;
    left: 47%;
    width: 140px;
    transform: rotate(-20deg);
    animation-delay: 2.5s;
  }
  .synapse-5 {
    top: 67%;
    left: 32%;
    width: 160px;
    transform: rotate(5deg);
    animation-delay: 0.3s;
  }

  @keyframes synapse-fire {
    0%,
    90%,
    100% {
      opacity: 0;
    }
    5%,
    85% {
      opacity: 0.8;
    }
  }

  .memory-bubbles {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .memory-bubble {
    position: absolute;
    border: 1px solid rgba(255, 165, 0, 0.3);
    border-radius: 50%;
    background: radial-gradient(circle, rgba(255, 165, 0, 0.1), transparent);
    animation: bubble-float 8s ease-in-out infinite;
  }

  .bubble-1 {
    width: 40px;
    height: 40px;
    top: 80%;
    left: 15%;
    animation-delay: 0s;
  }
  .bubble-2 {
    width: 30px;
    height: 30px;
    top: 75%;
    left: 70%;
    animation-delay: 2s;
  }
  .bubble-3 {
    width: 50px;
    height: 50px;
    top: 85%;
    left: 50%;
    animation-delay: 4s;
  }

  @keyframes bubble-float {
    0%,
    100% {
      transform: translateY(0) scale(1);
      opacity: 0.3;
    }
    50% {
      transform: translateY(-30px) scale(1.2);
      opacity: 0.8;
    }
  }

  .data-packets {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .data-packet {
    position: absolute;
    width: 4px;
    height: 4px;
    background: var(--warning);
    border-radius: 1px;
    box-shadow: 0 0 6px currentColor;
    animation: packet-travel 5s linear infinite;
  }

  .packet-1 {
    top: 20%;
    animation-delay: 0s;
  }
  .packet-2 {
    top: 40%;
    animation-delay: 1s;
  }
  .packet-3 {
    top: 60%;
    animation-delay: 2s;
  }
  .packet-4 {
    top: 80%;
    animation-delay: 3s;
  }

  @keyframes packet-travel {
    0% {
      left: -10px;
      opacity: 0;
    }
    10%,
    90% {
      opacity: 1;
    }
    100% {
      left: 100%;
      opacity: 0;
    }
  }

  .neural-header-section {
    text-align: center;
    position: relative;
    z-index: 10;
  }

  .system-badge {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    background: rgba(0, 0, 0, 0.8);
    border: 2px solid var(--border);
    padding: 12px 20px;
    font-size: 0.9rem;
    color: var(--synapse-teal);
    margin-bottom: 30px;
    position: relative;
    font-family: var(--font-mono);
  }

  .system-badge::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    right: -1px;
    bottom: -1px;
    background: linear-gradient(
      45deg,
      var(--synapse-teal),
      var(--pulse-coral),
      var(--axon-amber),
      var(--synapse-teal)
    );
    z-index: -1;
    animation: badge-border-flow 3s linear infinite;
  }

  @keyframes badge-border-flow {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .motherboard-title {
    font-size: 4.8rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 25px;
    background: linear-gradient(
      135deg,
      var(--pulse-coral) 0%,
      var(--brand-accent) 50%,
      var(--synapse-teal) 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    position: relative;
    font-family: var(--font-display);
  }

  .motherboard-title::before {
    content: '';
    position: absolute;
    bottom: -10px;
    left: 50%;
    transform: translateX(-50%);
    width: 120px;
    height: 4px;
    background: linear-gradient(90deg, var(--pulse-coral), var(--synapse-teal), var(--axon-amber));
    border-radius: 2px;
  }

  .neural-description {
    font-size: 1.4rem;
    color: var(--text-secondary);
    line-height: 1.6;
    max-width: 700px;
    margin: 0 auto;
  }

  @media (max-width: 768px) {
    .motherboard-title {
      font-size: 3rem;
    }
    .console-content {
      padding: 60px 30px;
    }
    .neural-description {
      font-size: 1.2rem;
    }
  }

  .motherboard-connection-nodes {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    z-index: 1;
  }

  .connection-node {
    position: absolute;
    width: 8px;
    height: 8px;
    background: radial-gradient(circle, var(--brand-accent), var(--brand-hover));
    border-radius: 50%;
    border: 1px solid var(--brand-accent);
    box-shadow: 0 0 10px rgba(220, 20, 60, 0.5);
    animation: node-pulse 2s ease-in-out infinite;
  }

  .node-1 {
    top: 15%;
    left: 5%;
    animation-delay: 0s;
  }

  .node-2 {
    top: 25%;
    right: 8%;
    animation-delay: 0.5s;
  }

  .node-3 {
    bottom: 25%;
    left: 15%;
    animation-delay: 1s;
  }

  .node-4 {
    bottom: 10%;
    right: 5%;
    animation-delay: 1.5s;
  }

  @keyframes node-pulse {
    0%,
    100% {
      transform: scale(1);
      opacity: 0.7;
    }
    50% {
      transform: scale(1.3);
      opacity: 1;
    }
  }

  .hero-description {
    color: var(--text-secondary);
    font-size: 1.25rem;
    margin-bottom: 0;
    line-height: 1.6;
    font-weight: 500;
    position: relative;
    z-index: 10;
    /* Embedded motherboard text effect */
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.9), rgba(42, 42, 42, 0.9));
    padding: 1.5rem 2rem;
    border-radius: 12px;
    border: 1px solid rgba(220, 20, 60, 0.2);
    backdrop-filter: blur(6px);
    box-shadow:
      inset 0 2px 4px rgba(0, 0, 0, 0.3),
      0 0 20px rgba(220, 20, 60, 0.1);
    /* PCB trace pattern overlay */
    background-image: repeating-linear-gradient(
      45deg,
      transparent,
      transparent 8px,
      rgba(78, 205, 196, 0.03) 8px,
      rgba(78, 205, 196, 0.03) 10px
    );
  }

  .processor-bay {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 2rem;
    max-width: 800px;
    margin: 0 auto;
    position: relative;
    padding: 2rem 0;
  }

  .processor-connection-line {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60px;
    height: 4px;
    background: linear-gradient(90deg, var(--brand-accent), var(--highlight), var(--brand-accent));
    border-radius: 2px;
    z-index: 1;
    opacity: 0.7;
    box-shadow: 0 0 8px rgba(220, 20, 60, 0.5);
  }

  .processor-connection-line::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(
      90deg,
      rgba(220, 20, 60, 0.2),
      rgba(255, 107, 107, 0.2),
      rgba(220, 20, 60, 0.2)
    );
    border-radius: 4px;
    z-index: -1;
  }

  .processor-card {
    display: block;
    text-decoration: none;
    color: inherit;
    width: 100%;
    height: 280px;
    perspective: 1000px;
    transition: all var(--transition-base);
    position: relative;
    z-index: 2;
  }

  .processor-card:hover {
    transform: translateY(-8px) rotateY(5deg);
    filter: brightness(1.1);
  }

  .pcb-substrate {
    position: relative;
    width: 100%;
    height: 100%;
    background: var(--bg-tertiary);
    border: 2px solid rgba(78, 205, 196, 0.4);
    border-radius: 12px;
    box-shadow:
      0 8px 32px rgba(0, 0, 0, 0.6),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    overflow: hidden;
    transition: all var(--transition-base);
  }

  .pcb-substrate::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
      45deg,
      transparent,
      transparent 2px,
      rgba(0, 150, 0, 0.02) 2px,
      rgba(0, 150, 0, 0.02) 4px
    );
    pointer-events: none;
  }

  .processor-card:hover .pcb-substrate {
    background: var(--bg-tertiary);
    border-color: rgba(78, 205, 196, 0.7);
    box-shadow:
      0 12px 40px rgba(0, 0, 0, 0.8),
      inset 0 1px 0 rgba(255, 255, 255, 0.1),
      0 0 20px rgba(220, 20, 60, 0.2);
  }

  .circuit-traces {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image:
      radial-gradient(circle at 20% 20%, rgba(78, 205, 196, 0.1) 1px, transparent 1px),
      radial-gradient(circle at 80% 20%, rgba(78, 205, 196, 0.1) 1px, transparent 1px),
      radial-gradient(circle at 20% 80%, rgba(78, 205, 196, 0.1) 1px, transparent 1px),
      radial-gradient(circle at 80% 80%, rgba(78, 205, 196, 0.1) 1px, transparent 1px),
      linear-gradient(
        90deg,
        transparent 48%,
        rgba(78, 205, 196, 0.1) 49%,
        rgba(78, 205, 196, 0.1) 51%,
        transparent 52%
      ),
      linear-gradient(
        0deg,
        transparent 48%,
        rgba(78, 205, 196, 0.1) 49%,
        rgba(78, 205, 196, 0.1) 51%,
        transparent 52%
      );
    background-size: 80px 80px;
    opacity: 0.05;
    transition: opacity var(--transition-base);
  }

  .cpu-traces {
    background-image:
      repeating-linear-gradient(
        45deg,
        transparent,
        transparent 10px,
        rgba(78, 205, 196, 0.08) 10px,
        rgba(78, 205, 196, 0.08) 12px
      ),
      repeating-linear-gradient(
        -45deg,
        transparent,
        transparent 10px,
        rgba(78, 205, 196, 0.08) 10px,
        rgba(78, 205, 196, 0.08) 12px
      );
  }

  .gpu-traces {
    background-image:
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 8px,
        rgba(78, 205, 196, 0.08) 8px,
        rgba(78, 205, 196, 0.08) 10px
      ),
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 8px,
        rgba(78, 205, 196, 0.08) 8px,
        rgba(78, 205, 196, 0.08) 10px
      );
  }

  .processor-card:hover .circuit-traces {
    opacity: 0.1;
  }

  .mounting-holes {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
  }

  .hole {
    position: absolute;
    width: 8px;
    height: 8px;
    background: var(--bg-primary);
    border-radius: 50%;
    border: 1px solid var(--border);
    box-shadow: inset 0 0 4px rgba(0, 0, 0, 0.8);
  }

  .hole.top-left {
    top: 12px;
    left: 12px;
  }

  .hole.top-right {
    top: 12px;
    right: 12px;
  }

  .hole.bottom-left {
    bottom: 12px;
    left: 12px;
  }

  .hole.bottom-right {
    bottom: 12px;
    right: 12px;
  }

  .pin-connectors {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
  }

  .pin-row {
    position: absolute;
    background: linear-gradient(45deg, var(--text-muted), var(--bg-tertiary));
    border: 1px solid var(--bg-secondary);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  }

  .pin-row.top {
    top: 0;
    left: 20%;
    right: 20%;
    height: 4px;
    background: repeating-linear-gradient(
      90deg,
      var(--text-muted),
      var(--text-muted) 3px,
      var(--bg-tertiary) 3px,
      var(--bg-tertiary) 6px
    );
  }

  .pin-row.bottom {
    bottom: 0;
    left: 20%;
    right: 20%;
    height: 4px;
    background: repeating-linear-gradient(
      90deg,
      var(--text-muted),
      var(--text-muted) 3px,
      var(--bg-tertiary) 3px,
      var(--bg-tertiary) 6px
    );
  }

  .pin-row.left {
    left: 0;
    top: 20%;
    bottom: 20%;
    width: 4px;
    background: repeating-linear-gradient(
      0deg,
      var(--text-muted),
      var(--text-muted) 3px,
      var(--bg-tertiary) 3px,
      var(--bg-tertiary) 6px
    );
  }

  .pin-row.right {
    right: 0;
    top: 20%;
    bottom: 20%;
    width: 4px;
    background: repeating-linear-gradient(
      0deg,
      var(--text-muted),
      var(--text-muted) 3px,
      var(--bg-tertiary) 3px,
      var(--bg-tertiary) 6px
    );
  }

  .silicon-die {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 70%;
    height: 60%;
    background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
    border: 2px solid var(--brand-accent);
    border-radius: 8px;
    box-shadow:
      0 4px 16px rgba(220, 20, 60, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transition: all var(--transition-base);
    overflow: hidden;
  }

  .processor-card:hover .silicon-die {
    border-color: var(--brand-accent);
    box-shadow:
      0 6px 24px rgba(220, 20, 60, 0.5),
      inset 0 1px 0 rgba(255, 255, 255, 0.15),
      0 0 12px rgba(220, 20, 60, 0.4);
  }

  .die-grid {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image:
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 6px,
        rgba(220, 20, 60, 0.1) 6px,
        rgba(220, 20, 60, 0.1) 7px
      ),
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 6px,
        rgba(220, 20, 60, 0.1) 6px,
        rgba(220, 20, 60, 0.1) 7px
      );
    opacity: 0.7;
  }

  .heat-sink {
    position: absolute;
    top: 4px;
    left: 4px;
    right: 4px;
    height: 20px;
    background: linear-gradient(90deg, var(--bg-tertiary), var(--bg-secondary), var(--bg-tertiary));
    border-radius: 4px;
    box-shadow:
      0 2px 4px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .heat-sink::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 4px;
    right: 4px;
    bottom: 2px;
    background: repeating-linear-gradient(
      90deg,
      var(--text-muted),
      var(--text-muted) 2px,
      var(--bg-tertiary) 2px,
      var(--bg-tertiary) 4px
    );
    border-radius: 2px;
  }

  .chip-content {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    width: 100%;
    padding: 1rem;
    z-index: 2;
  }

  .chip-icon {
    margin-bottom: 0.5rem;
    filter: drop-shadow(0 0 4px rgba(220, 20, 60, 0.5));
  }

  .chip-label h3 {
    margin: 0 0 0.25rem;
    font-size: 0.9rem;
    font-weight: 800;
    color: var(--brand-accent);
    text-shadow: 0 0 4px rgba(220, 20, 60, 0.5);
    letter-spacing: 0.05em;
  }

  .chip-label p {
    margin: 0;
    font-size: 0.7rem;
    color: var(--text-secondary);
    font-weight: 500;
    opacity: 0.9;
  }

  .led-indicators {
    position: absolute;
    top: 8px;
    right: 8px;
    display: flex;
    gap: 4px;
    z-index: 3;
  }

  .led {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--bg-tertiary);
    border: 1px solid var(--bg-secondary);
    transition: all var(--transition-base);
  }

  .led.active {
    background: var(--success);
    box-shadow:
      0 0 4px rgba(99, 212, 113, 0.8),
      inset 0 1px 0 rgba(255, 255, 255, 0.3);
    animation: led-pulse 2s ease-in-out infinite;
  }

  @keyframes led-pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.6;
    }
  }

  .processor-label {
    position: absolute;
    bottom: 8px;
    left: 8px;
    right: 8px;
    text-align: center;
    z-index: 3;
  }

  .model-number {
    display: block;
    font-size: 0.65rem;
    color: var(--synapse-teal);
    font-family: var(--font-mono);
    font-weight: 600;
    text-shadow: 0 0 4px rgba(99, 212, 113, 0.5);
    margin-bottom: 2px;
  }

  .specs {
    display: block;
    font-size: 0.6rem;
    color: var(--text-muted);
    font-family: var(--font-mono);
    opacity: 0.8;
  }

  .keyboard-hint.floating {
    position: absolute;
    top: -12px;
    right: -12px;
    background: rgba(0, 0, 0, 0.9);
    color: var(--brand-accent);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid var(--brand-accent);
    box-shadow: 0 2px 8px rgba(220, 20, 60, 0.3);
    z-index: 10;
    opacity: 0;
    transform: scale(0.8);
    transition: all var(--transition-base);
  }

  .processor-card:hover .keyboard-hint.floating {
    opacity: 1;
    transform: scale(1);
  }

  /* CPU vs GPU differentiation */
  .cpu-processor .silicon-die {
    background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
  }

  .gpu-processor .silicon-die {
    background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
  }

  .cpu-processor .die-grid {
    background-image:
      repeating-linear-gradient(
        45deg,
        transparent,
        transparent 4px,
        rgba(220, 20, 60, 0.1) 4px,
        rgba(220, 20, 60, 0.1) 5px
      ),
      repeating-linear-gradient(
        -45deg,
        transparent,
        transparent 4px,
        rgba(220, 20, 60, 0.1) 4px,
        rgba(220, 20, 60, 0.1) 5px
      );
  }

  .gpu-processor .die-grid {
    background-image:
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 3px,
        rgba(220, 20, 60, 0.15) 3px,
        rgba(220, 20, 60, 0.15) 4px
      ),
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 3px,
        rgba(220, 20, 60, 0.15) 3px,
        rgba(220, 20, 60, 0.15) 4px
      );
  }

  /* Hover effects for heating animation */
  .processor-card:hover .cpu-processor .die-grid {
    animation: cpu-heat 2s ease-in-out infinite;
  }

  .processor-card:hover .gpu-processor .die-grid {
    animation: gpu-heat 2s ease-in-out infinite;
  }

  @keyframes cpu-heat {
    0%,
    100% {
      background-color: rgba(220, 20, 60, 0.05);
    }
    50% {
      background-color: rgba(255, 69, 0, 0.1);
    }
  }

  @keyframes gpu-heat {
    0%,
    100% {
      background-color: rgba(220, 20, 60, 0.05);
    }
    50% {
      background-color: rgba(138, 43, 226, 0.1);
    }
  }

  /* Data flow animation */
  .processor-card:hover .circuit-traces::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(78, 205, 196, 0.3), transparent);
    animation: data-flow 1.5s ease-in-out infinite;
  }

  @keyframes data-flow {
    0% {
      left: -100%;
    }
    100% {
      left: 100%;
    }
  }

  @media (max-width: 768px) {
    .processor-bay {
      grid-template-columns: 1fr;
      gap: 1.5rem;
      padding: 1rem 0;
    }

    .processor-connection-line {
      display: none;
    }

    .processor-card {
      height: 240px;
    }

    .processor-card:hover {
      transform: translateY(-4px);
    }

    .silicon-die {
      width: 75%;
      height: 65%;
    }
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
    color: var(--text-primary);
    min-height: 200px;
    background: linear-gradient(
      135deg,
      rgba(0, 0, 0, 0.9) 0%,
      rgba(20, 20, 20, 0.95) 25%,
      rgba(10, 10, 10, 0.9) 50%,
      rgba(20, 20, 20, 0.95) 75%,
      rgba(0, 0, 0, 0.9) 100%
    );
    border: 2px solid rgba(220, 20, 60, 0.6);
    backdrop-filter: blur(6px);
    transition: all var(--transition-base);
  }

  .action-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      135deg,
      rgba(220, 20, 60, 0.15) 0%,
      rgba(220, 20, 60, 0.08) 25%,
      rgba(220, 20, 60, 0.12) 50%,
      rgba(220, 20, 60, 0.08) 75%,
      rgba(220, 20, 60, 0.15) 100%
    );
    opacity: 0;
    transition: opacity var(--transition-base);
    pointer-events: none;
  }

  .action-card h3 {
    font-family: var(--font-mono);
    font-weight: 700;
    font-size: 1.3rem;
    color: var(--text-primary);
    margin: 0.5rem 0;
    text-shadow: 0 0 10px rgba(220, 20, 60, 0.3);
  }

  .action-card p {
    font-family: var(--font-sans);
    font-weight: 400;
    color: rgba(255, 255, 255, 0.85);
    margin: 0;
    line-height: 1.5;
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
    color: var(--info);
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
    transform: translateY(-6px) scale(1.02);
    border-color: rgba(220, 20, 60, 0.9);
    box-shadow: 0 16px 40px rgba(220, 20, 60, 0.4);
    background: linear-gradient(
      135deg,
      rgba(0, 0, 0, 0.95) 0%,
      rgba(30, 30, 30, 0.98) 25%,
      rgba(15, 15, 15, 0.95) 50%,
      rgba(30, 30, 30, 0.98) 75%,
      rgba(0, 0, 0, 0.95) 100%
    );
  }

  .action-card:hover::before {
    opacity: 1;
  }

  .action-card:hover .card-icon {
    transform: scale(1.1);
  }

  .action-card:hover .card-glow {
    opacity: 1;
  }

  .stats-section {
    margin: 2rem 0 4rem;
    width: 100%;
    clear: both;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
  }

  /* NEURAL CPU MODULES */
  .cpu-module {
    position: relative;
    width: 100%;
    height: 160px;
    background: linear-gradient(145deg, var(--bg-secondary), var(--bg-primary));
    border: 3px solid var(--bg-tertiary);
    border-radius: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow:
      0 0 20px rgba(0, 0, 0, 0.8),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .cpu-module::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    right: -1px;
    bottom: -1px;
    background: linear-gradient(45deg, var(--border), var(--bg-secondary), var(--border));
    z-index: -1;
    border-radius: 2px;
  }

  .cpu-module:hover {
    transform: translateY(-2px) scale(1.01);
    box-shadow:
      0 0 30px rgba(220, 20, 60, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }

  /* CPU Header */
  .cpu-header {
    padding: 8px 12px;
    background: linear-gradient(90deg, var(--bg-secondary), var(--bg-tertiary));
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .cpu-model {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--text-muted);
    letter-spacing: 1px;
  }

  .cpu-status {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--synapse-teal);
    box-shadow: 0 0 8px currentColor;
    animation: cpu-pulse 2s ease-in-out infinite;
  }

  @keyframes cpu-pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.3;
    }
  }

  /* CPU Main Display */
  .cpu-display {
    flex: 1;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background:
      linear-gradient(90deg, transparent 0%, rgba(0, 255, 100, 0.02) 50%, transparent 100%),
      radial-gradient(circle at center, rgba(220, 20, 60, 0.05) 0%, transparent 70%);
  }

  /* CPU Data Section */
  .cpu-data {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .cpu-value {
    font-family: var(--font-mono);
    font-size: 3rem;
    font-weight: 700;
    color: var(--synapse-teal);
    line-height: 1;
    text-shadow: 0 0 10px currentColor;
    position: relative;
  }

  .cpu-value::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, currentColor, transparent);
    opacity: 0.5;
  }

  .cpu-label {
    font-family: var(--font-display);
    font-size: 0.8rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 300;
  }

  .cpu-sublabel {
    font-family: var(--font-mono);
    font-size: 0.6rem;
    color: var(--text-muted);
    margin-top: 2px;
  }

  /* CPU Circuit Pattern */
  .cpu-circuit {
    width: 80px;
    height: 80px;
    background: radial-gradient(circle, var(--bg-secondary) 30%, transparent 30%);
    background-size: 8px 8px;
    border: 2px solid var(--border);
    border-radius: 4px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .cpu-circuit::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 40px;
    height: 40px;
    border: 2px solid var(--border);
    border-radius: 2px;
    background: linear-gradient(45deg, var(--bg-secondary), var(--bg-primary));
  }

  .cpu-circuit::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 20px;
    height: 20px;
    background: var(--synapse-teal);
    border-radius: 2px;
    box-shadow: 0 0 10px currentColor;
    animation: cpu-core-pulse 1.5s ease-in-out infinite;
  }

  @keyframes cpu-core-pulse {
    0%,
    100% {
      transform: translate(-50%, -50%) scale(1);
    }
    50% {
      transform: translate(-50%, -50%) scale(1.1);
    }
  }

  /* CPU Socket Pins */
  .cpu-pins {
    position: absolute;
    bottom: -3px;
    left: 12px;
    right: 12px;
    height: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .pin {
    width: 3px;
    height: 6px;
    background: var(--text-muted);
    border-radius: 1px;
  }

  /* Type-specific styling */
  .cpu-module.memory .cpu-value {
    color: var(--brand-accent);
    text-shadow: 0 0 10px currentColor;
  }

  .cpu-module.memory .cpu-status {
    background: var(--brand-accent);
  }

  .cpu-module.memory .cpu-circuit::after {
    background: var(--brand-accent);
  }

  .cpu-module.memory .cpu-model {
    color: var(--brand-accent);
  }

  .cpu-module.today .cpu-value {
    color: var(--synapse-teal);
  }

  .cpu-module.today .cpu-status {
    background: var(--synapse-teal);
  }

  .cpu-module.today .cpu-circuit::after {
    background: var(--synapse-teal);
  }

  .cpu-module.tags .cpu-value {
    color: var(--warning);
    text-shadow: 0 0 10px currentColor;
  }

  .cpu-module.tags .cpu-status {
    background: var(--warning);
  }

  .cpu-module.tags .cpu-circuit::after {
    background: var(--warning);
  }

  .cpu-module.tags .cpu-model {
    color: var(--warning);
  }

  /* Heatsink Lines */
  .cpu-heatsink {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
      90deg,
      transparent 0px,
      transparent 2px,
      rgba(255, 255, 255, 0.02) 2px,
      rgba(255, 255, 255, 0.02) 4px
    );
    pointer-events: none;
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
    background: var(--bg-primary);
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
    background: linear-gradient(135deg, var(--man-united-red), var(--brand-accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-family: var(--font-display);
    font-size: 3.5rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 2rem;
    text-align: center;
    text-shadow: 0 0 30px rgba(220, 20, 60, 0.3);
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

  /* Neural Interface Scanner Styles */
  .neural-interface-section {
    margin: 3rem 0;
    padding: 2rem;
    background:
      linear-gradient(135deg, rgba(26, 26, 26, 0.95), rgba(42, 42, 42, 0.95)),
      radial-gradient(circle at center, rgba(220, 20, 60, 0.05), transparent 60%);
    border-radius: var(--radius-lg);
    position: relative;
    border: 2px solid rgba(78, 205, 196, 0.2);
    box-shadow:
      0 0 40px rgba(78, 205, 196, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }

  .neural-interface-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      repeating-linear-gradient(
        45deg,
        transparent,
        transparent 8px,
        rgba(78, 205, 196, 0.03) 8px,
        rgba(78, 205, 196, 0.03) 10px
      ),
      repeating-linear-gradient(
        -45deg,
        transparent,
        transparent 8px,
        rgba(78, 205, 196, 0.03) 8px,
        rgba(78, 205, 196, 0.03) 10px
      );
    border-radius: var(--radius-lg);
    pointer-events: none;
  }

  .neural-search-container {
    max-width: 900px;
    margin: 0 auto;
  }

  .neural-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .neural-title {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .brain-icon-container {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .neural-pulse {
    position: absolute;
    width: 40px;
    height: 40px;
    background: radial-gradient(circle, rgba(220, 20, 60, 0.2), transparent 70%);
    border-radius: 50%;
    animation: neural-pulse 2s ease-in-out infinite;
  }

  @keyframes neural-pulse {
    0%,
    100% {
      transform: scale(1);
      opacity: 0.8;
    }
    50% {
      transform: scale(1.3);
      opacity: 0.3;
    }
  }

  .neural-title h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    text-shadow: 0 0 10px rgba(220, 20, 60, 0.3);
  }

  .neural-scanner-description {
    color: var(--text-muted);
    font-size: 0.9rem;
    margin: 0.5rem 0 0 0;
    line-height: 1.4;
    opacity: 0.8;
  }

  .brain-regions {
    display: flex;
    align-items: center;
  }

  .brain-region-map {
    position: relative;
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.8), rgba(42, 42, 42, 0.8));
    border-radius: var(--radius-lg);
    border: 1px solid rgba(220, 20, 60, 0.2);
  }

  .region-connections {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
  }

  .synaptic-line {
    position: absolute;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(220, 20, 60, 0.6), transparent);
    opacity: 0.7;
    animation: synaptic-pulse 3s ease-in-out infinite;
  }

  .synaptic-line.line-1 {
    top: 20%;
    left: 10%;
    right: 10%;
    animation-delay: 0s;
  }

  .synaptic-line.line-2 {
    top: 50%;
    left: 20%;
    right: 20%;
    animation-delay: 1s;
  }

  .synaptic-line.line-3 {
    top: 80%;
    left: 15%;
    right: 15%;
    animation-delay: 2s;
  }

  @keyframes synaptic-pulse {
    0%,
    100% {
      opacity: 0.3;
      transform: scaleX(0.8);
    }
    50% {
      opacity: 0.8;
      transform: scaleX(1.1);
    }
  }

  .brain-region {
    position: relative;
    width: 80px;
    height: 80px;
    background: radial-gradient(circle, rgba(26, 26, 26, 0.9), rgba(42, 42, 42, 0.9));
    border: 2px solid var(--brand-accent);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all var(--transition-base);
    overflow: hidden;
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.4);
  }

  .brain-region:hover {
    border-color: var(--brand-accent);
    transform: scale(1.05);
    box-shadow: 0 0 25px rgba(220, 20, 60, 0.6);
  }

  .brain-region.active {
    border-color: var(--synapse-teal);
    background: radial-gradient(circle, rgba(78, 205, 196, 0.1), rgba(42, 42, 42, 0.9));
    box-shadow: 0 0 30px var(--synapse-teal-40);
  }

  .region-activity {
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    opacity: 0;
    transition: opacity var(--transition-base);
  }

  .brain-region.active .region-activity {
    opacity: 1;
    animation: region-activity 2s ease-in-out infinite;
  }

  .keyword-activity {
    background: radial-gradient(circle, rgba(0, 150, 255, 0.3), transparent 70%);
  }

  .semantic-activity {
    background: radial-gradient(circle, rgba(78, 205, 196, 0.3), transparent 70%);
  }

  .hybrid-activity {
    background: radial-gradient(circle, rgba(255, 100, 0, 0.3), transparent 70%);
  }

  @keyframes region-activity {
    0%,
    100% {
      transform: scale(1);
      opacity: 0.5;
    }
    50% {
      transform: scale(1.2);
      opacity: 0.8;
    }
  }

  .region-label {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    z-index: 2;
  }

  .region-name {
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--brand-accent);
    margin-bottom: 2px;
    text-shadow: 0 0 8px rgba(220, 20, 60, 0.5);
  }

  .region-type {
    font-size: 0.6rem;
    color: var(--text-muted);
    font-weight: 500;
  }

  .brain-region.active .region-name {
    color: var(--synapse-teal);
    text-shadow: 0 0 8px var(--synapse-teal-40);
  }

  .neural-probe-container {
    margin: 2rem 0;
  }

  .neural-probe {
    position: relative;
    display: flex;
    align-items: center;
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.95), rgba(42, 42, 42, 0.95));
    border: 2px solid rgba(220, 20, 60, 0.3);
    border-radius: var(--radius-lg);
    padding: 1rem;
    transition: all var(--transition-base);
    backdrop-filter: blur(6px);
  }

  .neural-probe:hover {
    border-color: rgba(220, 20, 60, 0.5);
    box-shadow: 0 0 30px rgba(220, 20, 60, 0.2);
  }

  .neural-probe.scanning {
    border-color: var(--brand-accent);
    box-shadow: 0 0 40px rgba(220, 20, 60, 0.4);
    animation: neural-scan 2s ease-in-out infinite;
  }

  @keyframes neural-scan {
    0%,
    100% {
      box-shadow: 0 0 30px rgba(220, 20, 60, 0.4);
    }
    50% {
      box-shadow:
        0 0 50px rgba(220, 20, 60, 0.6),
        inset 0 0 20px rgba(220, 20, 60, 0.1);
    }
  }

  .probe-tip {
    position: relative;
    width: 60px;
    height: 60px;
    background: radial-gradient(circle, var(--brand-accent), var(--brand-hover));
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 1rem;
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.5);
  }

  .synaptic-connections {
    position: absolute;
    width: 100%;
    height: 100%;
  }

  .synapse {
    position: absolute;
    width: 4px;
    height: 4px;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 50%;
    box-shadow: 0 0 6px rgba(255, 255, 255, 0.8);
    animation: synapse-fire 1.5s ease-in-out infinite;
  }

  .synapse-1 {
    top: 20%;
    left: 20%;
    animation-delay: 0s;
  }

  .synapse-2 {
    top: 20%;
    right: 20%;
    animation-delay: 0.3s;
  }

  .synapse-3 {
    bottom: 20%;
    left: 20%;
    animation-delay: 0.6s;
  }

  .synapse-4 {
    bottom: 20%;
    right: 20%;
    animation-delay: 0.9s;
  }

  @keyframes synapse-fire {
    0%,
    100% {
      opacity: 0.3;
      transform: scale(1);
    }
    50% {
      opacity: 1;
      transform: scale(1.5);
    }
  }

  .probe-input-field {
    flex: 1;
    position: relative;
  }

  .neural-interface-input {
    position: relative;
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .neural-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    font-size: 1.25rem;
    color: var(--text-primary);
    font-weight: 500;
    font-family: var(--font-display);
    padding: 0.5rem 0;
  }

  .neural-input::placeholder {
    color: var(--text-muted);
    font-style: italic;
  }

  .neural-processing {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .eeg-waveform {
    display: flex;
    align-items: center;
    gap: 2px;
    width: 60px;
    height: 30px;
  }

  .wave-line {
    width: 2px;
    background: var(--brand-accent);
    border-radius: 1px;
    animation: eeg-wave 1s ease-in-out infinite;
  }

  .wave-line:nth-child(1) {
    height: 20px;
    animation-delay: 0s;
  }

  .wave-line:nth-child(2) {
    height: 15px;
    animation-delay: 0.1s;
  }

  .wave-line:nth-child(3) {
    height: 25px;
    animation-delay: 0.2s;
  }

  @keyframes eeg-wave {
    0%,
    100% {
      height: 5px;
    }
    50% {
      height: 25px;
    }
  }

  .processing-text {
    font-size: 0.9rem;
    color: var(--brand-accent);
    font-weight: 600;
    animation: processing-pulse 1.5s ease-in-out infinite;
  }

  @keyframes processing-pulse {
    0%,
    100% {
      opacity: 0.7;
    }
    50% {
      opacity: 1;
    }
  }

  .neural-clear-btn {
    width: 30px;
    height: 30px;
    background: transparent;
    border: 2px solid rgba(220, 20, 60, 0.5);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all var(--transition-base);
  }

  .neural-clear-btn:hover {
    border-color: var(--brand-accent);
    background: rgba(220, 20, 60, 0.1);
    transform: scale(1.1);
  }

  .synaptic-break {
    width: 12px;
    height: 2px;
    background: var(--brand-accent);
    position: relative;
  }

  .synaptic-break::after {
    content: '';
    position: absolute;
    width: 12px;
    height: 2px;
    background: var(--brand-accent);
    transform: rotate(90deg);
  }

  .probe-connector {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-left: 1rem;
    border: 1px solid rgba(220, 20, 60, 0.3);
  }

  .connector-pins {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4px;
  }

  .pin {
    width: 6px;
    height: 6px;
    background: var(--bg-tertiary);
    border-radius: 50%;
    border: 1px solid var(--bg-secondary);
  }

  .pin.active {
    background: var(--synapse-teal);
    box-shadow: 0 0 6px var(--synapse-teal-40);
    animation: pin-pulse 2s ease-in-out infinite;
  }

  @keyframes pin-pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  /* Neural Results Styles */
  .neural-results-container {
    margin-top: 2rem;
    padding: 2rem;
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.9), rgba(42, 42, 42, 0.9));
    border: 1px solid rgba(220, 20, 60, 0.2);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(6px);
  }

  .neural-processing-state {
    text-align: center;
    padding: 3rem;
  }

  .neural-scan-animation {
    position: relative;
    width: 100px;
    height: 100px;
    margin: 0 auto 2rem;
  }

  .scan-pulse {
    position: absolute;
    width: 100%;
    height: 100%;
    border: 2px solid var(--brand-accent);
    border-radius: 50%;
    animation: scan-pulse 2s ease-in-out infinite;
  }

  .scan-pulse.delay-1 {
    animation-delay: 0.5s;
  }

  .scan-pulse.delay-2 {
    animation-delay: 1s;
  }

  @keyframes scan-pulse {
    0% {
      transform: scale(0.5);
      opacity: 1;
    }
    100% {
      transform: scale(1.5);
      opacity: 0;
    }
  }

  .neural-results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(220, 20, 60, 0.2);
  }

  .results-neural-indicator {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .neural-activity-indicator {
    width: 20px;
    height: 20px;
    background: radial-gradient(circle, var(--brand-accent), var(--brand-hover));
    border-radius: 50%;
    animation: neural-activity 1.5s ease-in-out infinite;
  }

  @keyframes neural-activity {
    0%,
    100% {
      transform: scale(1);
      opacity: 0.8;
    }
    50% {
      transform: scale(1.2);
      opacity: 1;
    }
  }

  .neural-count {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 1.1rem;
  }

  .expand-neural-network {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--brand-accent);
    font-weight: 600;
    text-decoration: none;
    transition: all var(--transition-base);
  }

  .expand-neural-network:hover {
    transform: translateX(4px);
    color: var(--brand-accent);
  }

  .neural-results-grid {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .neural-result-node {
    position: relative;
    display: flex;
    align-items: center;
    padding: 1.5rem;
    background: rgba(26, 26, 26, 0.8);
    border: 1px solid rgba(220, 20, 60, 0.2);
    border-radius: var(--radius);
    text-decoration: none;
    color: inherit;
    transition: all var(--transition-base);
    overflow: hidden;
  }

  .neural-result-node:hover {
    border-color: rgba(220, 20, 60, 0.5);
    background: rgba(220, 20, 60, 0.05);
    transform: translateX(8px);
  }

  .node-connection {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, var(--brand-accent), var(--brand-hover));
    opacity: 0;
    transition: opacity var(--transition-base);
  }

  .neural-result-node:hover .node-connection {
    opacity: 1;
  }

  .connection-pulse {
    position: absolute;
    width: 100%;
    height: 20px;
    background: linear-gradient(180deg, rgba(220, 20, 60, 0.8), transparent);
    animation: connection-pulse 2s ease-in-out infinite;
  }

  @keyframes connection-pulse {
    0% {
      top: 0;
      opacity: 1;
    }
    100% {
      top: 100%;
      opacity: 0;
    }
  }

  .node-content {
    display: flex;
    align-items: center;
    gap: 1rem;
    width: 100%;
  }

  .node-icon {
    width: 40px;
    height: 40px;
    background: radial-gradient(circle, rgba(220, 20, 60, 0.1), rgba(42, 42, 42, 0.9));
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    border: 1px solid rgba(220, 20, 60, 0.3);
  }

  .node-info {
    flex: 1;
    min-width: 0;
  }

  .node-info h4 {
    margin: 0 0 0.5rem;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .node-info p {
    margin: 0 0 0.5rem;
    font-size: 0.9rem;
    color: var(--text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: 1.4;
  }

  .neural-similarity {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .similarity-wave {
    width: 60px;
    height: 6px;
    background: rgba(220, 20, 60, 0.2);
    border-radius: 3px;
    overflow: hidden;
  }

  .wave-strength {
    height: 100%;
    background: linear-gradient(90deg, var(--brand-accent), var(--highlight));
    border-radius: 3px;
    transition: width var(--transition-base);
    animation: wave-pulse 2s ease-in-out infinite;
  }

  @keyframes wave-pulse {
    0%,
    100% {
      opacity: 0.8;
    }
    50% {
      opacity: 1;
    }
  }

  .similarity-strength {
    font-size: 0.75rem;
    color: var(--brand-accent);
    font-weight: 600;
  }

  .component-scores {
    display: flex;
    gap: 0.25rem;
    margin-top: 0.25rem;
    flex-wrap: wrap;
  }

  .score-component {
    font-size: 0.65rem;
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-weight: 500;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .score-component.semantic {
    color: var(--synapse-teal);
    border-color: rgba(78, 205, 196, 0.3);
    background: rgba(78, 205, 196, 0.1);
  }

  .score-component.keyword {
    color: var(--info);
    border-color: rgba(0, 150, 255, 0.3);
    background: rgba(0, 150, 255, 0.1);
  }

  .node-transmission {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    opacity: 0;
    transition: opacity var(--transition-base);
  }

  .neural-result-node:hover .node-transmission {
    opacity: 1;
  }

  .transmission-arrow {
    width: 0;
    height: 0;
    border-left: 8px solid var(--brand-accent);
    border-top: 6px solid transparent;
    border-bottom: 6px solid transparent;
    animation: transmission-pulse 1.5s ease-in-out infinite;
  }

  @keyframes transmission-pulse {
    0%,
    100% {
      opacity: 0.7;
      transform: translateX(0);
    }
    50% {
      opacity: 1;
      transform: translateX(4px);
    }
  }

  .neural-no-results {
    text-align: center;
    padding: 3rem;
  }

  .disconnected-neural-icon {
    position: relative;
    width: 80px;
    height: 80px;
    margin: 0 auto 2rem;
    opacity: 0.5;
  }

  .disconnection-indicator {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 100px;
    height: 2px;
    background: var(--brand-accent);
    transform-origin: center;
    transform: translate(-50%, -50%) rotate(45deg);
  }

  .disconnection-indicator::after {
    content: '';
    position: absolute;
    width: 100%;
    height: 2px;
    background: var(--brand-accent);
    transform: rotate(90deg);
  }

  .neural-no-results p {
    font-size: 1.2rem;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }

  .neural-no-results span {
    color: var(--text-muted);
    font-size: 0.9rem;
  }

  @media (max-width: 768px) {
    .neural-interface-section {
      padding: 1rem;
    }

    .neural-header {
      flex-direction: column;
      gap: 1rem;
    }

    .brain-region-map {
      flex-direction: column;
      gap: 0.5rem;
    }

    .brain-region {
      width: 60px;
      height: 60px;
    }

    .neural-probe {
      flex-direction: column;
      gap: 1rem;
    }

    .probe-tip {
      margin-right: 0;
    }

    .neural-results-header {
      flex-direction: column;
      gap: 1rem;
    }
  }

  /* CPU Motherboard Page Design */
  .container {
    position: relative;
    background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary));
    min-height: 100vh;
    overflow-x: hidden;
    display: flex;
    flex-direction: column;
  }

  .container::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100vw;
    height: 100vh;
    background: 
      /* Main PCB circuit traces */
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 40px,
        rgba(78, 205, 196, 0.12) 40px,
        rgba(78, 205, 196, 0.12) 42px
      ),
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 40px,
        rgba(78, 205, 196, 0.12) 40px,
        rgba(78, 205, 196, 0.12) 42px
      ),
      /* Connection pathways */
        radial-gradient(circle at 20% 30%, rgba(78, 205, 196, 0.15) 2px, transparent 2px),
      radial-gradient(circle at 80% 30%, rgba(78, 205, 196, 0.15) 2px, transparent 2px),
      radial-gradient(circle at 50% 70%, rgba(78, 205, 196, 0.15) 2px, transparent 2px),
      radial-gradient(circle at 20% 80%, rgba(78, 205, 196, 0.15) 2px, transparent 2px),
      radial-gradient(circle at 80% 80%, rgba(78, 205, 196, 0.15) 2px, transparent 2px);
    background-size:
      80px 80px,
      80px 80px,
      120px 120px,
      120px 120px,
      120px 120px,
      120px 120px,
      120px 120px;
    pointer-events: none;
    z-index: 0;
  }

  .container > * {
    position: relative;
    z-index: 1;
  }

  /* Neural Interface Scanner CPU Integration */
  .neural-interface-section {
    margin: 3rem 0;
    padding: 2rem;
    background:
      linear-gradient(135deg, rgba(26, 26, 26, 0.95), rgba(42, 42, 42, 0.95)),
      radial-gradient(circle at center, rgba(220, 20, 60, 0.05), transparent 60%);
    border-radius: var(--radius-lg);
    position: relative;
    border: 2px solid rgba(78, 205, 196, 0.2);
    box-shadow:
      0 0 40px rgba(78, 205, 196, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }

  .neural-interface-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      repeating-linear-gradient(
        45deg,
        transparent,
        transparent 8px,
        rgba(78, 205, 196, 0.03) 8px,
        rgba(78, 205, 196, 0.03) 10px
      ),
      repeating-linear-gradient(
        -45deg,
        transparent,
        transparent 8px,
        rgba(78, 205, 196, 0.03) 8px,
        rgba(78, 205, 196, 0.03) 10px
      );
    border-radius: var(--radius-lg);
    pointer-events: none;
  }

  /* Connect neural interface to processor cards */
  .neural-interface-section::after {
    content: '';
    position: absolute;
    bottom: -50px;
    left: 50%;
    transform: translateX(-50%);
    width: 6px;
    height: 50px;
    background: linear-gradient(180deg, rgba(220, 20, 60, 0.8), rgba(78, 205, 196, 0.8));
    border-radius: 3px;
    box-shadow: 0 0 10px rgba(220, 20, 60, 0.5);
  }

  /* Processor bay motherboard integration */
  .processor-bay::before {
    content: '';
    position: absolute;
    top: -50px;
    left: 50%;
    transform: translateX(-50%);
    width: 80px;
    height: 6px;
    background: linear-gradient(
      90deg,
      rgba(78, 205, 196, 0.8),
      rgba(220, 20, 60, 0.8),
      rgba(78, 205, 196, 0.8)
    );
    border-radius: 3px;
    box-shadow: 0 0 10px rgba(0, 255, 100, 0.5);
  }

  /* PCB mounting holes in corners */
  .container::after {
    content: '';
    position: fixed;
    top: 20px;
    left: 20px;
    width: 12px;
    height: 12px;
    background: var(--bg-primary);
    border-radius: 50%;
    border: 2px solid var(--border);
    box-shadow:
      calc(100vw - 64px) 0 0 var(--bg-primary),
      calc(100vw - 64px) 0 0 0 2px var(--border),
      0 calc(100vh - 64px) 0 var(--bg-primary),
      0 calc(100vh - 64px) 0 0 2px var(--border),
      calc(100vw - 64px) calc(100vh - 64px) 0 var(--bg-primary),
      calc(100vw - 64px) calc(100vh - 64px) 0 0 2px var(--border);
    z-index: 0;
  }

  /* Stats section as PCB components */
  .stats-section {
    position: relative;
    background:
      linear-gradient(135deg, rgba(26, 26, 26, 0.9), rgba(42, 42, 42, 0.9)),
      radial-gradient(circle at 30% 30%, rgba(78, 205, 196, 0.05), transparent 50%);
    border-radius: var(--radius-lg);
    padding: 2rem;
    margin: 2rem 0;
    border: 1px solid rgba(78, 205, 196, 0.2);
    box-shadow: 0 0 20px rgba(78, 205, 196, 0.1);
  }

  .stats-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 12px,
        rgba(78, 205, 196, 0.03) 12px,
        rgba(78, 205, 196, 0.03) 14px
      ),
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 12px,
        rgba(78, 205, 196, 0.03) 12px,
        rgba(78, 205, 196, 0.03) 14px
      );
    border-radius: var(--radius-lg);
    pointer-events: none;
  }

  /* Circuit traces connecting all sections */
  .hero::after {
    content: '';
    position: absolute;
    bottom: -30px;
    left: 50%;
    transform: translateX(-50%);
    width: 4px;
    height: 60px;
    background: linear-gradient(180deg, rgba(220, 20, 60, 0.6), rgba(78, 205, 196, 0.6));
    border-radius: 2px;
    box-shadow: 0 0 8px rgba(220, 20, 60, 0.4);
  }

  /* Power indicators */
  .hero::before {
    content: '';
    position: absolute;
    top: 20px;
    right: 20px;
    width: 8px;
    height: 8px;
    background: var(--success);
    border-radius: 50%;
    box-shadow:
      0 0 10px rgba(0, 255, 0, 0.8),
      -20px 0 0 var(--success),
      -20px 0 0 0 10px rgba(0, 255, 0, 0.8),
      -40px 0 0 var(--warning),
      -40px 0 0 0 10px rgba(255, 149, 0, 0.8);
    animation: power-indicator 2s ease-in-out infinite;
  }

  @keyframes power-indicator {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.6;
    }
  }

  /* Cognitive Fingerprint Section - Neural Design Language */
  .cognitive-fingerprint-section {
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    margin: 2rem 0;
    position: relative;
    overflow: hidden;
    font-family: var(--font-mono);
    max-width: 400px;
  }

  .cognitive-fingerprint-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background:
      linear-gradient(45deg, transparent 30%, rgba(0, 255, 100, 0.03) 50%, transparent 70%),
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 2px,
        rgba(0, 255, 100, 0.1) 2px,
        rgba(0, 255, 100, 0.1) 4px
      );
    animation: circuit-flow 8s linear infinite;
    pointer-events: none;
  }

  .cognitive-fingerprint-section::after {
    content: '█';
    position: absolute;
    top: 20px;
    right: 30px;
    color: rgba(0, 255, 100, 0.8);
    font-size: 1rem;
    animation: terminal-cursor 1s infinite;
  }

  @keyframes circuit-flow {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  @keyframes terminal-cursor {
    0%,
    50% {
      opacity: 1;
    }
    51%,
    100% {
      opacity: 0;
    }
  }

  .fingerprint-container {
    max-width: 900px;
    margin: 0 auto;
    position: relative;
    z-index: 2;
  }

  .fingerprint-header {
    margin-bottom: 3rem;
  }

  .terminal-header {
    margin-bottom: 1.5rem;
  }

  .terminal-title-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(0, 0, 0, 0.7);
    padding: 0.75rem 1.5rem;
    border-radius: 8px 8px 0 0;
    border: 1px solid rgba(0, 255, 100, 0.3);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
  }

  .terminal-indicator {
    color: #00ff64;
    font-size: 1.2rem;
    animation: pulse 2s infinite;
  }

  .terminal-path {
    color: rgba(255, 255, 255, 0.8);
    flex: 1;
  }

  .terminal-status {
    color: #00ff64;
    font-weight: bold;
    padding: 0.25rem 0.5rem;
    background: rgba(0, 255, 100, 0.1);
    border-radius: 4px;
  }

  .fingerprint-header h2 {
    font-size: 1.8rem;
    font-weight: 700;
    color: #00ff64;
    margin-bottom: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
    text-align: left;
  }

  .terminal-output {
    font-size: 1rem;
    color: rgba(255, 255, 255, 0.8);
    font-family: 'JetBrains Mono', monospace;
    margin-left: 1rem;
    border-left: 2px solid rgba(0, 255, 100, 0.3);
    padding-left: 1rem;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  .fingerprint-content {
    display: grid;
    gap: 2rem;
  }

  .explorer-profile {
    display: flex;
    align-items: center;
    gap: 2rem;
    background: rgba(255, 255, 255, 0.05);
    padding: 2rem;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .explorer-icon {
    font-size: 4rem;
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
    border-radius: 50%;
    flex-shrink: 0;
  }

  .explorer-info h3 {
    font-size: 1.8rem;
    font-weight: 700;
    color: white;
    margin-bottom: 1rem;
  }

  .confidence-meter {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .confidence-bar {
    width: 200px;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }

  .confidence-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 4px;
    transition: width 0.6s ease;
  }

  .confidence-text {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.7);
    font-weight: 600;
  }

  .explorer-info p {
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.6;
    font-size: 1rem;
  }

  .traits-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }

  .trait-section h4 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #00ff64;
    margin-bottom: 1rem;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .metrics-section h4 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #00ff64;
    margin-bottom: 1rem;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 1px;
  }

  .traits-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .trait {
    background: rgba(0, 255, 100, 0.1);
    color: #00ff64;
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    font-size: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
    border: 1px solid rgba(0, 255, 100, 0.3);
    text-transform: lowercase;
  }

  .metrics-section {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
  }

  .metric {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    background: rgba(0, 0, 0, 0.4);
    padding: 0.8rem 1rem;
    border-radius: 6px;
    border: 1px solid rgba(0, 255, 100, 0.2);
    font-family: 'JetBrains Mono', monospace;
    transition: all 0.3s ease;
  }

  .metric:hover {
    border-color: rgba(0, 255, 100, 0.5);
    box-shadow: 0 0 10px rgba(0, 255, 100, 0.2);
  }

  .metric-prefix {
    color: #00ff64;
    font-weight: bold;
    font-size: 1rem;
  }

  .metric-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex: 1;
  }

  .metric-label {
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.9rem;
  }

  .metric-value {
    color: #00ff64;
    font-weight: bold;
    font-size: 1.2rem;
    min-width: 40px;
    text-align: right;
  }

  @media (max-width: 768px) {
    .cognitive-fingerprint-section {
      padding: 2rem 1rem;
      margin: 2rem 0;
    }

    .explorer-profile {
      flex-direction: column;
      text-align: center;
      gap: 1rem;
    }

    .traits-grid {
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }

    .fingerprint-header h2 {
      font-size: 2rem;
    }

    .confidence-meter {
      justify-content: center;
    }
  }
</style>
