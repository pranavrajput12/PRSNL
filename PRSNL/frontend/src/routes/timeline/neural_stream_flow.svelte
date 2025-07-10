<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { getTimeline } from '$lib/api';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import SkeletonLoader from '$lib/components/SkeletonLoader.svelte';
  import Icon from '$lib/components/Icon.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import TagList from '$lib/components/TagList.svelte';
  import { browser } from '$app/environment';

  type Item = {
    id: string;
    title: string;
    url?: string;
    summary?: string;
    createdAt: string;
    tags: string[];
    type?: string;
    item_type?: string;
    file_path?: string;
    thumbnail_url?: string;
    duration?: number;
    platform?: string;
    status?: string;
  };

  type TimelineGroup = {
    date: string;
    items: Item[];
  };

  let groups: TimelineGroup[] = [];
  let isLoading = false;
  let hasMore = true;
  let page = 1;
  let error: Error | null = null;
  let scrollContainer: HTMLElement | null = null;
  let filterMode = 'all'; // all, videos, documents, links, today

  onMount(async () => {
    await loadTimeline(true);
  });

  async function loadTimeline(reset = false) {
    if (isLoading) return;
    
    try {
      isLoading = true;
      error = null;
      
      if (reset) {
        page = 1;
        groups = [];
      }

      const response = await getTimeline(page);
      
      if (response && response.items) {
        // Group items by date
        const newGroups: { [key: string]: Item[] } = {};
        
        response.items.forEach((item: Item) => {
          const date = new Date(item.createdAt).toDateString();
          if (!newGroups[date]) {
            newGroups[date] = [];
          }
          newGroups[date].push(item);
        });

        // Convert to array and sort by date
        const groupArray: TimelineGroup[] = Object.entries(newGroups).map(([date, items]) => ({
          date,
          items: items.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
        })).sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

        if (reset) {
          groups = groupArray;
        } else {
          groups = [...groups, ...groupArray];
        }

        hasMore = response.items.length >= 20;
        page++;
      }
    } catch (e) {
      console.error('Failed to load timeline:', e);
      error = e as Error;
    } finally {
      isLoading = false;
    }
  }

  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    }
  }

  function getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    
    return date.toLocaleDateString();
  }

  function getContentTypeBadge(item: Item) {
    if (item.item_type === 'video') {
      return { type: 'video', icon: 'video', label: 'VID' };
    } else if (item.file_path) {
      return { type: 'document', icon: 'file', label: 'DOC' };
    } else if (item.item_type === 'article' || (!item.item_type && item.url && !item.file_path)) {
      return { type: 'article', icon: 'link', label: 'ART' };
    } else if (item.url) {
      return { type: 'link', icon: 'external-link', label: 'LINK' };
    }
    return null;
  }

  async function handleScroll() {
    if (!scrollContainer || isLoading || !hasMore) return;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
    if (scrollTop + clientHeight >= scrollHeight - 200) {
      await loadTimeline(false);
    }
  }

  function setFilterMode(mode: string) {
    filterMode = mode;
  }
</script>

<svelte:head>
  <title>Thought Stream - Neural Interface</title>
</svelte:head>

<div class="neural-stream-container">
  <!-- Neural activity background -->
  <div class="neural-activity">
    <div class="activity-pulse"></div>
    <div class="activity-pulse"></div>
    <div class="activity-pulse"></div>
    <div class="activity-pulse"></div>
  </div>

  <!-- Stream header -->
  <div class="stream-header">
    <h1 class="stream-title">Neural Thought Stream</h1>
    <div class="stream-controls">
      <button 
        class="control-button {filterMode === 'all' ? 'active' : ''}"
        on:click={() => setFilterMode('all')}
      >
        All Traces
      </button>
      <button 
        class="control-button {filterMode === 'videos' ? 'active' : ''}"
        on:click={() => setFilterMode('videos')}
      >
        Videos
      </button>
      <button 
        class="control-button {filterMode === 'documents' ? 'active' : ''}"
        on:click={() => setFilterMode('documents')}
      >
        Documents
      </button>
      <button 
        class="control-button {filterMode === 'links' ? 'active' : ''}"
        on:click={() => setFilterMode('links')}
      >
        Links
      </button>
      <button 
        class="control-button {filterMode === 'today' ? 'active' : ''}"
        on:click={() => setFilterMode('today')}
      >
        Today
      </button>
    </div>
  </div>

  <!-- Neural flow line -->
  <div class="neural-flow-line"></div>

  <!-- Timeline content -->
  <div 
    class="stream-content" 
    bind:this={scrollContainer}
    on:scroll={handleScroll}
  >
    {#if error}
      <ErrorMessage 
        message="Failed to load thought stream" 
        details={error.message} 
        retry={() => loadTimeline(true)} 
        dismiss={() => { error = null; }} 
      />
    {:else if groups.length === 0 && !isLoading}
      <div class="empty-state">
        <div class="empty-icon">
          <Icon name="brain" size="large" color="var(--text-muted)" />
        </div>
        <h3>No neural traces detected</h3>
        <p>Start capturing content to build your thought stream</p>
        <a href="/capture" class="btn-primary">
          <Icon name="plus" size="small" />
          Begin neural capture
        </a>
      </div>
    {:else}
      {#each groups as group, groupIndex}
        <div class="stream-section">
          <!-- Date node -->
          <div class="section-date">
            <div class="date-node"></div>
            <div class="date-label">{formatDate(group.date)}</div>
          </div>

          <!-- Memory traces -->
          {#each group.items as item, itemIndex}
            {@const badge = getContentTypeBadge(item)}
            <div class="memory-trace">
              <div class="trace-connection"></div>
              
              <div class="trace-header">
                <div class="trace-main">
                  <a href="/item/{item.id}" class="trace-title">
                    {item.title || 'Untitled'}
                    {#if item.status === 'pending'}
                      <span class="processing-indicator">
                        <Spinner size="tiny" />
                        Processing...
                      </span>
                    {/if}
                  </a>
                  {#if item.summary}
                    <div class="trace-summary">{item.summary}</div>
                  {/if}
                </div>
                
                <div class="trace-badges">
                  {#if badge}
                    <div class="trace-badge {badge.type}">
                      <Icon name={badge.icon} size="small" />
                      {badge.label}
                    </div>
                  {/if}
                </div>
              </div>

              {#if item.item_type === 'video' && item.thumbnail_url}
                <div class="trace-video">
                  <VideoPlayer 
                    videoUrl={item.url} 
                    thumbnailUrl={item.thumbnail_url}
                    title={item.title}
                    duration={item.duration}
                    platform={item.platform}
                  />
                </div>
              {/if}

              <div class="trace-footer">
                <div class="trace-time">{getRelativeTime(item.createdAt)}</div>
                {#if item.tags && item.tags.length > 0}
                  <div class="trace-tags">
                    {#each item.tags.slice(0, 3) as tag}
                      <span class="trace-tag">#{tag}</span>
                    {/each}
                    {#if item.tags.length > 3}
                      <span class="trace-tag-more">+{item.tags.length - 3}</span>
                    {/if}
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/each}

      {#if isLoading}
        <div class="loading-section">
          <SkeletonLoader type="card" count={3} />
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .neural-stream-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
    position: relative;
    min-height: 100vh;
  }

  .neural-activity {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: -1;
  }

  .activity-pulse {
    position: absolute;
    width: 4px;
    height: 4px;
    background: #00ff64;
    border-radius: 50%;
    animation: pulse-activity 4s linear infinite;
  }

  @keyframes pulse-activity {
    0% { 
      opacity: 0;
      transform: scale(0.5);
    }
    50% { 
      opacity: 1;
      transform: scale(1);
    }
    100% { 
      opacity: 0;
      transform: scale(0.5);
    }
  }

  .activity-pulse:nth-child(1) { top: 20%; left: 10%; animation-delay: 0s; }
  .activity-pulse:nth-child(2) { top: 40%; left: 85%; animation-delay: 1s; }
  .activity-pulse:nth-child(3) { top: 70%; left: 20%; animation-delay: 2s; }
  .activity-pulse:nth-child(4) { top: 60%; left: 70%; animation-delay: 3s; }

  .stream-header {
    text-align: center;
    margin-bottom: 3rem;
    position: relative;
  }

  .stream-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #DC143C, #00ff64);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1.5rem;
  }

  .stream-controls {
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .control-button {
    background: rgba(26, 26, 26, 0.9);
    border: 1px solid rgba(0, 255, 100, 0.3);
    color: #00ff64;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-family: inherit;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
  }

  .control-button:hover {
    border-color: #DC143C;
    color: #DC143C;
    box-shadow: 0 0 15px rgba(220, 20, 60, 0.3);
  }

  .control-button.active {
    background: rgba(220, 20, 60, 0.2);
    border-color: #DC143C;
    color: #DC143C;
  }

  .neural-flow-line {
    position: absolute;
    left: 60px;
    top: 200px;
    bottom: 0;
    width: 2px;
    background: linear-gradient(180deg, 
      transparent 0%, 
      rgba(0, 255, 100, 0.5) 20%, 
      rgba(220, 20, 60, 0.5) 80%, 
      transparent 100%);
    animation: flow-pulse 3s ease-in-out infinite;
  }

  @keyframes flow-pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }

  .stream-content {
    position: relative;
    max-height: 80vh;
    overflow-y: auto;
    padding-right: 1rem;
  }

  .stream-section {
    position: relative;
    margin-bottom: 3rem;
  }

  .section-date {
    position: relative;
    margin-bottom: 2rem;
  }

  .date-node {
    position: absolute;
    left: 52px;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    background: #DC143C;
    border-radius: 50%;
    border: 3px solid #0a0a0a;
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.5);
    animation: node-pulse 2s ease-in-out infinite;
  }

  @keyframes node-pulse {
    0%, 100% { transform: translateY(-50%) scale(1); }
    50% { transform: translateY(-50%) scale(1.2); }
  }

  .date-label {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 1.1rem;
    color: #00ff64;
    margin-left: 80px;
    padding: 0.5rem 1rem;
    background: rgba(0, 255, 100, 0.1);
    border: 1px solid rgba(0, 255, 100, 0.3);
    border-radius: 8px;
    display: inline-block;
  }

  .memory-trace {
    position: relative;
    margin-left: 80px;
    margin-bottom: 1.5rem;
    background: rgba(26, 26, 26, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
  }

  .memory-trace:hover {
    border-color: rgba(220, 20, 60, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  }

  .trace-connection {
    position: absolute;
    left: -28px;
    top: 1.5rem;
    width: 24px;
    height: 2px;
    background: linear-gradient(90deg, rgba(0, 255, 100, 0.5), rgba(220, 20, 60, 0.5));
    animation: connection-flow 2s ease-in-out infinite;
  }

  @keyframes connection-flow {
    0% { background-position: 0% 50%; }
    100% { background-position: 100% 50%; }
  }

  .trace-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .trace-main {
    flex: 1;
  }

  .trace-title {
    font-weight: 600;
    font-size: 1.1rem;
    color: #e0e0e0;
    text-decoration: none;
    margin-bottom: 0.5rem;
    display: block;
    line-height: 1.4;
  }

  .trace-title:hover {
    color: #DC143C;
  }

  .processing-indicator {
    color: #00ff64;
    font-size: 0.875rem;
    font-weight: 400;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    margin-left: 0.5rem;
  }

  .trace-summary {
    color: #a0a0a0;
    line-height: 1.5;
    margin-top: 0.5rem;
  }

  .trace-badges {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .trace-badge {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .trace-badge.video {
    background: rgba(220, 20, 60, 0.2);
    color: #DC143C;
    border: 1px solid rgba(220, 20, 60, 0.3);
  }

  .trace-badge.document {
    background: rgba(74, 158, 255, 0.2);
    color: #4a9eff;
    border: 1px solid rgba(74, 158, 255, 0.3);
  }

  .trace-badge.link {
    background: rgba(0, 255, 100, 0.2);
    color: #00ff64;
    border: 1px solid rgba(0, 255, 100, 0.3);
  }

  .trace-badge.article {
    background: rgba(168, 85, 247, 0.2);
    color: #a855f7;
    border: 1px solid rgba(168, 85, 247, 0.3);
  }

  .trace-video {
    margin: 1rem 0;
    border-radius: 12px;
    overflow: hidden;
  }

  .trace-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
  }

  .trace-time {
    color: #666;
  }

  .trace-tags {
    display: flex;
    gap: 0.5rem;
  }

  .trace-tag {
    background: rgba(0, 255, 100, 0.1);
    color: #00ff64;
    padding: 0.25rem 0.5rem;
    border-radius: 8px;
    font-size: 0.75rem;
  }

  .trace-tag-more {
    color: #666;
    font-size: 0.75rem;
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    margin-left: 80px;
  }

  .empty-icon {
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .empty-state h3 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    color: #e0e0e0;
  }

  .empty-state p {
    color: #a0a0a0;
    margin-bottom: 2rem;
  }

  .btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: linear-gradient(135deg, #DC143C, #B91C3C);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 25px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
  }

  .btn-primary:hover {
    background: linear-gradient(135deg, #B91C3C, #991B1B);
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.5);
    transform: translateY(-2px);
  }

  .loading-section {
    margin-left: 80px;
    padding: 1rem;
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .neural-stream-container {
      padding: 1rem;
    }

    .stream-title {
      font-size: 2rem;
    }

    .stream-controls {
      gap: 0.5rem;
    }

    .control-button {
      padding: 0.375rem 0.75rem;
      font-size: 0.8rem;
    }

    .neural-flow-line {
      left: 30px;
    }

    .date-node {
      left: 22px;
    }

    .date-label {
      margin-left: 50px;
    }

    .memory-trace {
      margin-left: 50px;
    }

    .trace-connection {
      left: -18px;
    }

    .empty-state {
      margin-left: 50px;
    }

    .loading-section {
      margin-left: 50px;
    }
  }
</style>