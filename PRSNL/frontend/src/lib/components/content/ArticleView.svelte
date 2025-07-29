<!--
  Article View Component
  
  Specialized component for displaying article content with reading features,
  table of contents, and enhanced typography.
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import MarkdownViewer from '$lib/components/development/MarkdownViewer.svelte';
  import TagList from '$lib/components/TagList.svelte';
  import { formatDate } from '$lib/utils/date';
  
  export let item: any;
  export let contentType: any;
  
  const dispatch = createEventDispatcher();
  
  $: hasContent = item.content || item.processed_content;
  $: content = item.content || item.processed_content || '';
  $: hasMarkdown = content && (content.includes('#') || content.includes('```'));
  $: readingTime = calculateReadingTime(content);
  $: wordCount = calculateWordCount(content);
  $: hasTags = item.tags && item.tags.length > 0;
  $: hasAIAnalysis = item.metadata?.ai_analysis;
  
  // Table of contents extraction
  $: tableOfContents = extractTableOfContents(content);
  $: showTOC = tableOfContents.length > 0;
  
  let activeHeading: string = '';
  let showReadingProgress = false;
  let readingProgress = 0;
  
  function calculateReadingTime(text: string): number {
    const wordsPerMinute = 200;
    const words = text.trim().split(/\s+/).length;
    return Math.ceil(words / wordsPerMinute);
  }
  
  function calculateWordCount(text: string): number {
    return text.trim().split(/\s+/).length;
  }
  
  function extractTableOfContents(content: string) {
    if (!hasMarkdown) return [];
    
    const headingRegex = /^(#{1,6})\s+(.+)$/gm;
    const headings = [];
    let match;
    
    while ((match = headingRegex.exec(content)) !== null) {
      const level = match[1].length;
      const text = match[2].trim();
      const id = text.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
      
      headings.push({
        level,
        text,
        id
      });
    }
    
    return headings;
  }
  
  function scrollToHeading(headingId: string) {
    const element = document.getElementById(headingId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      activeHeading = headingId;
    }
  }
  
  function toggleReadingMode() {
    showReadingProgress = !showReadingProgress;
    
    if (showReadingProgress) {
      window.addEventListener('scroll', updateReadingProgress);
    } else {
      window.removeEventListener('scroll', updateReadingProgress);
    }
  }
  
  function updateReadingProgress() {
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight - windowHeight;
    const scrollTop = window.pageYOffset;
    
    readingProgress = (scrollTop / documentHeight) * 100;
  }
  
  function handleError(error: any) {
    dispatch('error', error);
  }
</script>

<div class="article-view">
  <!-- Article Header -->
  <header class="article-header">
    <div class="article-meta-bar">
      <div class="reading-stats">
        <span class="stat-item">
          <Icon name="clock" size="small" />
          {readingTime} min read
        </span>
        <span class="stat-item">
          <Icon name="type" size="small" />
          {wordCount.toLocaleString()} words
        </span>
        {#if item.created_at || item.createdAt}
          <span class="stat-item">
            <Icon name="calendar" size="small" />
            {formatDate(item.created_at || item.createdAt)}
          </span>
        {/if}
      </div>
      
      <div class="reading-controls">
        <button 
          class="control-btn {showReadingProgress ? 'active' : ''}"
          on:click={toggleReadingMode}
          title="Toggle reading mode"
        >
          <Icon name="eye" size="small" />
          Reading Mode
        </button>
        
        {#if item.url}
          <a 
            href={item.url} 
            target="_blank" 
            rel="noopener noreferrer"
            class="control-btn"
            title="View original article"
          >
            <Icon name="external-link" size="small" />
            Original
          </a>
        {/if}
      </div>
    </div>
    
    <!-- Reading Progress Bar -->
    {#if showReadingProgress}
      <div class="reading-progress-container">
        <div class="reading-progress-bar" style="width: {readingProgress}%"></div>
      </div>
    {/if}
  </header>
  
  <div class="article-content-container">
    <!-- Table of Contents Sidebar -->
    {#if showTOC}
      <aside class="table-of-contents">
        <h3>Table of Contents</h3>
        <nav class="toc-nav">
          {#each tableOfContents as heading}
            <button
              class="toc-item level-{heading.level} {activeHeading === heading.id ? 'active' : ''}"
              on:click={() => scrollToHeading(heading.id)}
            >
              {heading.text}
            </button>
          {/each}
        </nav>
      </aside>
    {/if}
    
    <!-- Main Article Content -->
    <main class="article-main" class:has-toc={showTOC}>
      <!-- Article Summary -->
      {#if item.summary && item.summary !== content}
        <section class="article-summary">
          <h2>Summary</h2>
          <p class="summary-text">{item.summary}</p>
        </section>
      {/if}
      
      <!-- Article Content -->
      {#if hasContent}
        <section class="article-content">
          {#if hasMarkdown}
            <MarkdownViewer 
              {content}
              enableSyntaxHighlight={true} 
              theme="neural"
              generateIds={true}
              on:error={handleError}
            />
          {:else}
            <div class="plain-content">
              {content}
            </div>
          {/if}
        </section>
      {/if}
      
      <!-- Tags Section -->
      {#if hasTags}
        <section class="article-tags">
          <h3>Tags</h3>
          <TagList tags={item.tags} />
        </section>
      {/if}
      
      <!-- AI Analysis Section -->
      {#if hasAIAnalysis}
        <section class="ai-analysis-section">
          <h3>AI Analysis</h3>
          <div class="analysis-content">
            {#if item.metadata.ai_analysis.key_points}
              <div class="analysis-subsection">
                <h4>Key Points</h4>
                <ul class="key-points-list">
                  {#each item.metadata.ai_analysis.key_points as point}
                    <li>{point}</li>
                  {/each}
                </ul>
              </div>
            {/if}
            
            {#if item.metadata.ai_analysis.questions}
              <div class="analysis-subsection">
                <h4>Questions This Answers</h4>
                <ul class="questions-list">
                  {#each item.metadata.ai_analysis.questions as question}
                    <li>{question}</li>
                  {/each}
                </ul>
              </div>
            {/if}
            
            {#if item.metadata.ai_analysis.entities}
              <div class="analysis-subsection">
                <h4>Related Concepts</h4>
                <div class="entities-container">
                  {#each Object.entries(item.metadata.ai_analysis.entities) as [category, items]}
                    {#if Array.isArray(items) && items.length > 0}
                      <div class="entity-group">
                        <h5>{category}</h5>
                        <div class="entity-tags">
                          {#each items as entityItem}
                            <span class="entity-tag">{entityItem}</span>
                          {/each}
                        </div>
                      </div>
                    {/if}
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        </section>
      {/if}
      
      <!-- Source Information -->
      <footer class="article-footer">
        <div class="source-info">
          <h4>Source Information</h4>
          <div class="source-details">
            {#if item.url}
              <div class="source-item">
                <span class="source-label">Original URL:</span>
                <a href={item.url} target="_blank" rel="noopener noreferrer" class="source-link">
                  {item.url}
                </a>
              </div>
            {/if}
            
            <div class="source-item">
              <span class="source-label">Added to library:</span>
              <span class="source-value">{formatDate(item.created_at || item.createdAt)}</span>
            </div>
            
            {#if item.author}
              <div class="source-item">
                <span class="source-label">Author:</span>
                <span class="source-value">{item.author}</span>
              </div>
            {/if}
          </div>
        </div>
      </footer>
    </main>
  </div>
</div>

<style>
  .article-view {
    max-width: 100%;
    margin: 0 auto;
  }
  
  /* Article Header */
  .article-header {
    margin-bottom: 2rem;
    position: sticky;
    top: 0;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(10px);
    z-index: 10;
    padding: 1rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .article-meta-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 2rem;
  }
  
  .reading-stats {
    display: flex;
    gap: 1.5rem;
    align-items: center;
  }
  
  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
  
  .reading-controls {
    display: flex;
    gap: 0.5rem;
  }
  
  .control-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 20px;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
    font-size: 0.875rem;
  }
  
  .control-btn:hover,
  .control-btn.active {
    background: rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
  }
  
  /* Reading Progress */
  .reading-progress-container {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: rgba(255, 255, 255, 0.1);
  }
  
  .reading-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--neural-green), #dc143c);
    transition: width 0.1s ease;
  }
  
  /* Content Container */
  .article-content-container {
    display: grid;
    grid-template-columns: 250px 1fr;
    gap: 2rem;
    align-items: start;
  }
  
  /* Table of Contents */
  .table-of-contents {
    position: sticky;
    top: 120px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
    max-height: calc(100vh - 140px);
    overflow-y: auto;
  }
  
  .table-of-contents h3 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    color: var(--neural-green);
    font-weight: 600;
  }
  
  .toc-nav {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .toc-item {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.5rem 0;
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    transition: color 0.2s;
    font-size: 0.875rem;
    line-height: 1.4;
  }
  
  .toc-item:hover,
  .toc-item.active {
    color: var(--text-primary);
  }
  
  .toc-item.level-1 { padding-left: 0; font-weight: 600; }
  .toc-item.level-2 { padding-left: 1rem; }
  .toc-item.level-3 { padding-left: 2rem; }
  .toc-item.level-4 { padding-left: 3rem; }
  .toc-item.level-5 { padding-left: 4rem; }
  .toc-item.level-6 { padding-left: 5rem; }
  
  /* Main Article Content */
  .article-main {
    min-width: 0;
  }
  
  .article-main.has-toc {
    /* Additional styles when TOC is present */
  }
  
  .article-summary {
    background: rgba(0, 255, 100, 0.05);
    border: 1px solid rgba(0, 255, 100, 0.2);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }
  
  .article-summary h2 {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    color: var(--neural-green);
  }
  
  .summary-text {
    color: var(--text-primary);
    line-height: 1.6;
    margin: 0;
    font-size: 1.1rem;
  }
  
  .article-content {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
  }
  
  .plain-content {
    color: var(--text-primary);
    line-height: 1.8;
    font-size: 1.1rem;
    white-space: pre-wrap;
  }
  
  /* Tags Section */
  .article-tags {
    margin-bottom: 2rem;
  }
  
  .article-tags h3 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    color: var(--text-primary);
  }
  
  /* AI Analysis */
  .ai-analysis-section {
    background: rgba(220, 20, 60, 0.05);
    border: 1px solid rgba(220, 20, 60, 0.2);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }
  
  .ai-analysis-section h3 {
    margin: 0 0 1.5rem 0;
    font-size: 1.25rem;
    color: #dc143c;
  }
  
  .analysis-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .analysis-subsection {
    background: rgba(0, 0, 0, 0.2);
    padding: 1rem;
    border-radius: 8px;
  }
  
  .analysis-subsection h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    color: var(--text-primary);
  }
  
  .key-points-list,
  .questions-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .key-points-list li,
  .questions-list li {
    padding: 0.5rem 0 0.5rem 1.5rem;
    position: relative;
    color: var(--text-primary);
    line-height: 1.5;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }
  
  .key-points-list li:last-child,
  .questions-list li:last-child {
    border-bottom: none;
  }
  
  .key-points-list li::before {
    content: '→';
    position: absolute;
    left: 0;
    color: var(--neural-green);
    font-weight: bold;
  }
  
  .questions-list li::before {
    content: '?';
    position: absolute;
    left: 0;
    color: #dc143c;
    font-weight: bold;
  }
  
  .entities-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .entity-group h5 {
    margin: 0 0 0.5rem 0;
    font-size: 0.9rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .entity-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .entity-tag {
    padding: 0.25rem 0.75rem;
    background: rgba(74, 158, 255, 0.1);
    color: #4a9eff;
    border-radius: 12px;
    font-size: 0.875rem;
  }
  
  /* Article Footer */
  .article-footer {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 2rem;
  }
  
  .source-info h4 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    color: var(--text-primary);
  }
  
  .source-details {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .source-item {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .source-label {
    font-weight: 500;
    color: var(--text-secondary);
    min-width: 120px;
  }
  
  .source-value {
    color: var(--text-primary);
  }
  
  .source-link {
    color: var(--neural-green);
    text-decoration: none;
    word-break: break-all;
  }
  
  .source-link:hover {
    text-decoration: underline;
  }
  
  /* Responsive Design */
  @media (max-width: 1024px) {
    .article-content-container {
      grid-template-columns: 1fr;
    }
    
    .table-of-contents {
      position: static;
      margin-bottom: 2rem;
    }
  }
  
  @media (max-width: 768px) {
    .article-meta-bar {
      flex-direction: column;
      gap: 1rem;
    }
    
    .reading-stats {
      justify-content: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    
    .article-content {
      padding: 1.5rem;
    }
    
    .source-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.25rem;
    }
    
    .source-label {
      min-width: auto;
    }
  }
</style>