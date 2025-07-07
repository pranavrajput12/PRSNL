<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import KnowledgeCard from '$lib/components/KnowledgeCard.svelte';
  import AsyncBoundary from '$lib/components/AsyncBoundary.svelte';
  import type { Item } from '$lib/types/api';
  
  let item: Item | null = null;
  let isLoading = true;
  let error: Error | null = null;
  let activeTab = 'overview';
  let showQuickActions = false;
  let copiedNotification = false;
  
  $: itemId = $page.params.id;
  $: isBookmark = item?.status === 'bookmark';
  $: hasAIAnalysis = item?.metadata?.ai_analysis;
  $: readingTime = item?.metadata?.ai_analysis?.reading_time || 
                   Math.ceil((item?.content || '').split(/\s+/).length / 200);
  
  onMount(() => {
    loadItem();
  });
  
  async function loadItem() {
    try {
      isLoading = true;
      const response = await fetch(`/api/items/${itemId}`);
      if (!response.ok) throw new Error('Failed to load item');
      item = await response.json();
    } catch (e) {
      error = e as Error;
    } finally {
      isLoading = false;
    }
  }
  
  async function copyToClipboard(text: string) {
    await navigator.clipboard.writeText(text);
    copiedNotification = true;
    setTimeout(() => copiedNotification = false, 2000);
  }
  
  function formatContent(content: string): string {
    if (!content) return '';
    
    // Convert numbered lists to proper HTML
    content = content.replace(/^(\d+)\.\s+(.+)$/gm, '<li class="numbered">$2</li>');
    content = content.replace(/(<li class="numbered">.*<\/li>\n?)+/g, '<ol class="formatted-list">$&</ol>');
    
    // Convert bullet points to proper HTML
    content = content.replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>');
    content = content.replace(/(<li>.*<\/li>\n?)+/g, '<ul class="formatted-list">$&</ul>');
    
    // Convert headers (lines ending with :)
    content = content.replace(/^(.+):$/gm, '<h4 class="content-header">$1</h4>');
    
    // Convert paragraphs
    content = content.replace(/\n\n/g, '</p><p>');
    content = '<p>' + content + '</p>';
    
    return content;
  }
  
  function getDifficultyColor(difficulty: string): string {
    switch(difficulty?.toLowerCase()) {
      case 'beginner': return 'success';
      case 'intermediate': return 'warning';
      case 'advanced': return 'danger';
      default: return 'secondary';
    }
  }
</script>

<AsyncBoundary loading={isLoading} {error} loadingMessage="Loading item details...">
  {#if item}
  <div class="knowledge-page">
    <!-- Sticky Header with Progress -->
    <div class="sticky-header">
      <div class="header-content">
        <button class="back-btn" on:click={() => goto('/')}>
          <Icon name="arrow-left" size="small" />
          Back
        </button>
        
        <div class="header-info">
          <span class="item-type {item.item_type}">
            <Icon name={item.item_type === 'video' ? 'play-circle' : 'file-text'} size="small" />
            {item.item_type}
          </span>
          {#if isBookmark}
            <span class="bookmark-badge">
              <Icon name="bookmark" size="small" />
              Bookmark
            </span>
          {/if}
        </div>
        
        <div class="header-actions">
          <button class="action-btn" on:click={() => showQuickActions = !showQuickActions}>
            <Icon name="more-vertical" size="small" />
          </button>
          
          {#if showQuickActions}
            <div class="quick-actions">
              <button on:click={() => copyToClipboard(item.url || window.location.href)}>
                <Icon name="link" size="small" />
                Copy Link
              </button>
              <button on:click={() => window.print()}>
                <Icon name="printer" size="small" />
                Print
              </button>
              {#if item.url}
                <a href={item.url} target="_blank" rel="noopener">
                  <Icon name="external-link" size="small" />
                  Open Original
                </a>
              {/if}
            </div>
          {/if}
        </div>
      </div>
    </div>
    
    <!-- Main Content Area -->
    <div class="content-container">
      <!-- Hero Section -->
      <div class="hero-section">
        {#if item.item_type === 'video' && item.thumbnail_url}
          <div class="hero-media">
            {#if item.file_path}
              <VideoPlayer
                src={`/media/videos/${item.file_path.split('/').pop()}`}
                thumbnail={item.thumbnail_url}
                title={item.title}
              />
            {:else}
              <img src={item.thumbnail_url} alt={item.title} class="video-thumbnail" />
            {/if}
          </div>
        {/if}
        
        <div class="hero-content">
          <h1 class="title">{item.title}</h1>
          
          <div class="meta-row">
            <span class="meta-item">
              <Icon name="calendar" size="small" />
              {new Date(item.created_at).toLocaleDateString()}
            </span>
            {#if readingTime}
              <span class="meta-item">
                <Icon name="clock" size="small" />
                {readingTime} min read
              </span>
            {/if}
            {#if item.platform}
              <span class="meta-item">
                <Icon name="globe" size="small" />
                {item.platform}
              </span>
            {/if}
          </div>
          
          {#if item.tags && item.tags.length > 0}
            <div class="tag-list">
              {#each item.tags as tag}
                <span class="tag">{tag}</span>
              {/each}
            </div>
          {/if}
        </div>
      </div>
      
      <!-- Tab Navigation -->
      <div class="tab-nav">
        <button 
          class="tab-btn" 
          class:active={activeTab === 'overview'}
          on:click={() => activeTab = 'overview'}
        >
          <Icon name="layout" size="small" />
          Overview
        </button>
        <button 
          class="tab-btn" 
          class:active={activeTab === 'content'}
          on:click={() => activeTab = 'content'}
        >
          <Icon name="file-text" size="small" />
          Content
        </button>
        {#if hasAIAnalysis}
          <button 
            class="tab-btn" 
            class:active={activeTab === 'insights'}
            on:click={() => activeTab = 'insights'}
          >
            <Icon name="brain" size="small" />
            AI Insights
          </button>
        {/if}
        {#if item.metadata}
          <button 
            class="tab-btn" 
            class:active={activeTab === 'details'}
            on:click={() => activeTab = 'details'}
          >
            <Icon name="info" size="small" />
            Details
          </button>
        {/if}
      </div>
      
      <!-- Tab Content -->
      <div class="tab-content">
        {#if activeTab === 'overview'}
          <div class="overview-tab">
            <!-- Summary Card -->
            <KnowledgeCard title="Summary" icon="align-left" accent="primary">
              <p class="summary-text">
                {item.summary || "No summary available"}
              </p>
            </KnowledgeCard>
            
            <!-- Key Points -->
            {#if hasAIAnalysis && item.metadata.ai_analysis.key_points?.length > 0}
              <KnowledgeCard title="Key Takeaways" icon="list" accent="success">
                <ol class="key-points">
                  {#each item.metadata.ai_analysis.key_points as point}
                    <li>{point}</li>
                  {/each}
                </ol>
              </KnowledgeCard>
            {/if}
            
            <!-- Prerequisites/Tools -->
            {#if hasAIAnalysis && item.metadata.ai_analysis.entities}
              {#if item.metadata.ai_analysis.entities.Prerequisites?.length > 0}
                <KnowledgeCard title="Prerequisites" icon="check-circle" accent="warning">
                  <ul class="entity-list">
                    {#each item.metadata.ai_analysis.entities.Prerequisites as prereq}
                      <li>{prereq}</li>
                    {/each}
                  </ul>
                </KnowledgeCard>
              {/if}
              
              {#if item.metadata.ai_analysis.entities.Tools?.length > 0}
                <KnowledgeCard title="Tools & Resources" icon="tool" accent="info">
                  <div class="tool-grid">
                    {#each item.metadata.ai_analysis.entities.Tools as tool}
                      <span class="tool-chip">{tool}</span>
                    {/each}
                  </div>
                </KnowledgeCard>
              {/if}
            {/if}
            
            <!-- Difficulty Level -->
            {#if hasAIAnalysis && item.metadata.ai_analysis.sentiment}
              <div class="difficulty-card {getDifficultyColor(item.metadata.ai_analysis.sentiment)}">
                <Icon name="trending-up" size="small" />
                <span>Difficulty: {item.metadata.ai_analysis.sentiment}</span>
              </div>
            {/if}
          </div>
          
        {:else if activeTab === 'content'}
          <div class="content-tab">
            {#if item.content || item.transcription}
              <KnowledgeCard title="Full Content" icon="file-text">
                <div class="formatted-content">
                  {@html formatContent(item.content || item.transcription || '')}
                </div>
              </KnowledgeCard>
            {:else if isBookmark}
              <KnowledgeCard title="Content" icon="bookmark">
                <div class="bookmark-notice">
                  <Icon name="external-link" />
                  <p>This is a bookmarked item. Click below to view the original content.</p>
                  <a href={item.url} target="_blank" rel="noopener" class="primary-btn">
                    Open Original
                  </a>
                </div>
              </KnowledgeCard>
            {:else}
              <p class="no-content">No content available</p>
            {/if}
          </div>
          
        {:else if activeTab === 'insights' && hasAIAnalysis}
          <div class="insights-tab">
            <!-- Questions Answered -->
            {#if item.metadata.ai_analysis.questions?.length > 0}
              <KnowledgeCard title="Questions This Answers" icon="help-circle">
                <ul class="questions-list">
                  {#each item.metadata.ai_analysis.questions as question}
                    <li>{question}</li>
                  {/each}
                </ul>
              </KnowledgeCard>
            {/if}
            
            <!-- Skills -->
            {#if item.metadata.ai_analysis.entities?.Skills?.length > 0}
              <KnowledgeCard title="Skills You'll Learn" icon="award">
                <div class="skills-grid">
                  {#each item.metadata.ai_analysis.entities.Skills as skill}
                    <div class="skill-badge">
                      <Icon name="check" size="small" />
                      {skill}
                    </div>
                  {/each}
                </div>
              </KnowledgeCard>
            {/if}
            
            <!-- AI Tags -->
            {#if item.metadata.ai_analysis.tags?.length > 0}
              <KnowledgeCard title="AI-Generated Tags" icon="tag">
                <div class="ai-tags">
                  {#each item.metadata.ai_analysis.tags as tag}
                    <span class="ai-tag">{tag}</span>
                  {/each}
                </div>
              </KnowledgeCard>
            {/if}
          </div>
          
        {:else if activeTab === 'details'}
          <div class="details-tab">
            <KnowledgeCard title="Metadata" icon="database">
              <dl class="metadata-list">
                <dt>Created</dt>
                <dd>{new Date(item.created_at).toLocaleString()}</dd>
                
                {#if item.updated_at}
                  <dt>Updated</dt>
                  <dd>{new Date(item.updated_at).toLocaleString()}</dd>
                {/if}
                
                {#if item.duration}
                  <dt>Duration</dt>
                  <dd>{Math.floor(item.duration / 60)}:{(item.duration % 60).toString().padStart(2, '0')}</dd>
                {/if}
                
                {#if item.metadata?.video_metadata}
                  <dt>Resolution</dt>
                  <dd>{item.metadata.video_metadata.width}x{item.metadata.video_metadata.height}</dd>
                  
                  {#if item.metadata.video_metadata.view_count}
                    <dt>Views</dt>
                    <dd>{item.metadata.video_metadata.view_count.toLocaleString()}</dd>
                  {/if}
                {/if}
              </dl>
            </KnowledgeCard>
          </div>
        {/if}
      </div>
    </div>
    
    <!-- Floating Action Button -->
    <div class="fab-container">
      <button class="fab" on:click={() => copyToClipboard(item.summary || item.title)}>
        <Icon name="copy" />
      </button>
    </div>
    
    <!-- Copy Notification -->
    {#if copiedNotification}
      <div class="notification">
        <Icon name="check" size="small" />
        Copied to clipboard!
      </div>
    {/if}
  </div>
  {/if}
</AsyncBoundary>

<style>
  .knowledge-page {
    min-height: 100vh;
    background: var(--bg-primary);
  }
  
  .sticky-header {
    position: sticky;
    top: 0;
    z-index: 100;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(10px);
  }
  
  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .back-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--text-primary);
  }
  
  .back-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(-2px);
  }
  
  .header-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .item-type {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.75rem;
    background: rgba(74, 158, 255, 0.2);
    color: var(--accent);
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
  }
  
  .item-type.video {
    background: rgba(74, 222, 128, 0.2);
    color: var(--success);
  }
  
  .bookmark-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.75rem;
    background: rgba(251, 191, 36, 0.2);
    color: var(--warning);
    border-radius: 20px;
    font-size: 0.875rem;
  }
  
  .header-actions {
    position: relative;
  }
  
  .action-btn {
    padding: 0.5rem;
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-secondary);
    transition: color 0.2s;
  }
  
  .action-btn:hover {
    color: var(--text-primary);
  }
  
  .quick-actions {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: var(--shadow-md);
    min-width: 200px;
  }
  
  .quick-actions button,
  .quick-actions a {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    text-align: left;
    cursor: pointer;
    color: var(--text-primary);
    text-decoration: none;
    transition: background 0.2s;
  }
  
  .quick-actions button:hover,
  .quick-actions a:hover {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .content-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .hero-section {
    margin-bottom: 2rem;
  }
  
  .hero-media {
    margin-bottom: 2rem;
    border-radius: 12px;
    overflow: hidden;
  }
  
  .video-thumbnail {
    width: 100%;
    height: auto;
    display: block;
  }
  
  .hero-content {
    margin-bottom: 2rem;
  }
  
  .title {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1rem;
    line-height: 1.2;
  }
  
  .meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    margin-bottom: 1rem;
    color: var(--text-secondary);
  }
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }
  
  .tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
  }
  
  .tag {
    padding: 0.25rem 0.75rem;
    background: rgba(74, 158, 255, 0.2);
    color: var(--accent);
    border-radius: 20px;
    font-size: 0.875rem;
  }
  
  .tab-nav {
    display: flex;
    gap: 0.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
  }
  
  .tab-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    color: var(--text-secondary);
    font-weight: 500;
    transition: all 0.2s;
  }
  
  .tab-btn:hover {
    color: var(--text-primary);
  }
  
  .tab-btn.active {
    color: var(--accent);
    border-bottom-color: var(--accent);
  }
  
  .summary-text {
    font-size: 1.1rem;
    line-height: 1.6;
    color: var(--text-primary);
  }
  
  .key-points {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .key-points li {
    position: relative;
    padding-left: 2rem;
    margin-bottom: 1rem;
    line-height: 1.6;
  }
  
  .key-points li::before {
    content: counter(list-item);
    counter-increment: list-item;
    position: absolute;
    left: 0;
    top: 0;
    width: 1.5rem;
    height: 1.5rem;
    background: var(--accent);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    font-weight: 600;
  }
  
  .entity-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .entity-list li {
    padding: 0.5rem 0;
    padding-left: 1.5rem;
    position: relative;
  }
  
  .entity-list li::before {
    content: "•";
    position: absolute;
    left: 0;
    color: var(--accent);
    font-weight: bold;
  }
  
  .tool-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }
  
  .tool-chip {
    padding: 0.5rem 1rem;
    background: rgba(96, 165, 250, 0.2);
    color: var(--info);
    border-radius: 8px;
    font-weight: 500;
  }
  
  .difficulty-card {
    display: inline-flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    margin-top: 1rem;
  }
  
  .difficulty-card.success {
    background: rgba(74, 222, 128, 0.2);
    color: var(--success);
  }
  
  .difficulty-card.warning {
    background: rgba(251, 191, 36, 0.2);
    color: var(--warning);
  }
  
  .difficulty-card.danger {
    background: rgba(220, 20, 60, 0.2);
    color: var(--error);
  }
  
  .formatted-content {
    font-size: 1.05rem;
    line-height: 1.7;
    color: var(--text-primary);
  }
  
  .formatted-content :global(p) {
    margin-bottom: 1rem;
  }
  
  .formatted-content :global(.content-header) {
    font-size: 1.2rem;
    font-weight: 600;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    color: var(--text-primary);
  }
  
  .formatted-content :global(.formatted-list) {
    margin: 1rem 0;
    padding-left: 1.5rem;
  }
  
  .formatted-content :global(.formatted-list li) {
    margin-bottom: 0.5rem;
  }
  
  .bookmark-notice {
    text-align: center;
    padding: 2rem;
  }
  
  .bookmark-notice p {
    margin: 1rem 0;
    color: var(--text-secondary);
  }
  
  .primary-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: var(--accent);
    color: white;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.2s;
  }
  
  .primary-btn:hover {
    background: var(--accent-hover);
    transform: translateY(-1px);
  }
  
  .questions-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .questions-list li {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
  }
  
  .questions-list li:last-child {
    border-bottom: none;
  }
  
  .skills-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
  }
  
  .skill-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: rgba(74, 222, 128, 0.2);
    color: var(--success);
    border-radius: 8px;
    font-weight: 500;
  }
  
  .ai-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }
  
  .ai-tag {
    padding: 0.5rem 1rem;
    background: rgba(160, 160, 160, 0.2);
    color: var(--text-secondary);
    border-radius: 20px;
    font-size: 0.9rem;
  }
  
  .metadata-list {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 1rem;
    margin: 0;
  }
  
  .metadata-list dt {
    font-weight: 600;
    color: var(--text-secondary);
  }
  
  .metadata-list dd {
    margin: 0;
    color: var(--text-primary);
  }
  
  .fab-container {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
  }
  
  .fab {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: var(--accent);
    color: white;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-md);
    transition: all 0.2s;
  }
  
  .fab:hover {
    transform: scale(1.1);
    background: var(--accent-hover);
  }
  
  .notification {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    background: var(--success);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: var(--shadow-md);
    animation: slideUp 0.3s ease;
  }
  
  @keyframes slideUp {
    from {
      transform: translateX(-50%) translateY(100%);
      opacity: 0;
    }
    to {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }
  }
  
  .no-content {
    text-align: center;
    color: var(--text-secondary);
    padding: 3rem;
  }
  
  .loading-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 50vh;
  }
  
  /* Responsive design */
  @media (max-width: 768px) {
    .content-container {
      padding: 1rem;
    }
    
    .title {
      font-size: 1.75rem;
    }
    
    .meta-row {
      gap: 1rem;
    }
    
    .tab-btn {
      padding: 0.5rem 1rem;
      font-size: 0.875rem;
    }
    
    .skills-grid {
      grid-template-columns: 1fr;
    }
  }
  
  /* Print styles */
  @media print {
    .sticky-header,
    .tab-nav,
    .fab-container,
    .quick-actions {
      display: none;
    }
    
    .knowledge-card {
      break-inside: avoid;
    }
  }
</style>