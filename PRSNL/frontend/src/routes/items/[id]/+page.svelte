<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import MarkdownViewer from '$lib/components/development/MarkdownViewer.svelte';
  import GitHubRepoCard from '$lib/components/development/GitHubRepoCard.svelte';
  import { getItem } from '$lib/api';
  import type { Item } from '$lib/types/api';
  
  let item: Item | null = null;
  let loading = true;
  let error: string | null = null;
  let activeTab = 'overview';
  let copyNotification = false;
  
  $: itemId = $page.params.id;
  $: isDevelopment = item?.type === 'development';
  $: hasRichPreview = item?.metadata?.rich_preview && item.metadata.rich_preview.type !== 'error';
  $: githubData = hasRichPreview ? item?.metadata?.rich_preview : null;
  $: readmeContent = githubData?.readme?.full_content || '';
  $: hasReadme = readmeContent.length > 0;
  
  onMount(() => {
    loadItem();
  });
  
  async function loadItem() {
    try {
      loading = true;
      error = null;
      item = await getItem(itemId);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load item';
    } finally {
      loading = false;
    }
  }
  
  async function copyToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      copyNotification = true;
      setTimeout(() => copyNotification = false, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }
  
  function getDifficultyBadge(level: number | undefined) {
    if (!level) return null;
    const levels = {
      1: { label: 'Beginner', color: '#10b981' },
      2: { label: 'Intermediate', color: '#3b82f6' },
      3: { label: 'Advanced', color: '#f59e0b' },
      4: { label: 'Expert', color: '#ef4444' },
      5: { label: 'Master', color: '#8b5cf6' }
    };
    return levels[level as keyof typeof levels];
  }
  
  function getLanguageIcon(language: string | undefined): string {
    if (!language) return '💻';
    const icons: Record<string, string> = {
      'python': '🐍',
      'javascript': '🟨',
      'typescript': '🔷',
      'java': '☕',
      'go': '🐹',
      'rust': '🦀',
      'cpp': '⚡',
      'c': '🔵',
      'csharp': '🟢',
      'php': '🐘',
      'ruby': '💎',
      'swift': '🦉',
      'kotlin': '🟪',
      'dart': '🎯',
      'r': '📊',
      'julia': '🟣',
      'scala': '🔴',
      'haskell': '🔶',
      'elixir': '💜',
      'clojure': '🟩',
      'lua': '🌙',
      'perl': '🦪',
      'shell': '🐚',
      'powershell': '🔷'
    };
    return icons[language.toLowerCase()] || '💻';
  }
</script>

<svelte:head>
  <title>{item?.title || 'Loading...'} - Code Cortex | PRSNL</title>
</svelte:head>

{#if loading}
  <div class="loading-container">
    <div class="neural-pulse"></div>
    <p>Loading development content...</p>
  </div>
{:else if error}
  <div class="error-container">
    <Icon name="alert-circle" size="large" />
    <h2>Error loading item</h2>
    <p>{error}</p>
    <button on:click={() => goto('/code-cortex')} class="back-button">
      Back to Code Cortex
    </button>
  </div>
{:else if item}
  <div class="development-item-page">
    <!-- Header -->
    <header class="item-header">
      <div class="header-nav">
        <button on:click={() => goto('/code-cortex')} class="back-link">
          <Icon name="arrow-left" size="small" />
          Code Cortex
        </button>
        
        <div class="header-actions">
          {#if item.url}
            <a href={item.url} target="_blank" rel="noopener noreferrer" class="action-button" title="Open original">
              <Icon name="external-link" size="small" />
            </a>
          {/if}
          <button on:click={() => copyToClipboard(item.url || window.location.href)} class="action-button" title="Copy link">
            <Icon name="link" size="small" />
          </button>
        </div>
      </div>
      
      <div class="header-content">
        <h1 class="item-title">{item.title}</h1>
        
        <div class="item-meta">
          {#if item.programming_language}
            <span class="meta-badge language">
              {getLanguageIcon(item.programming_language)} {item.programming_language}
            </span>
          {/if}
          
          {#if item.difficulty_level}
            {@const difficulty = getDifficultyBadge(item.difficulty_level)}
            {#if difficulty}
              <span class="meta-badge difficulty" style="background: {difficulty.color}20; color: {difficulty.color}">
                {difficulty.label}
              </span>
            {/if}
          {/if}
          
          {#if item.project_category}
            <span class="meta-badge category">
              {item.project_category}
            </span>
          {/if}
          
          {#if item.is_career_related}
            <span class="meta-badge career">
              💼 Career
            </span>
          {/if}
          
          <span class="meta-badge date">
            <Icon name="calendar" size="small" />
            {new Date(item.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </header>
    
    <!-- GitHub Repository Card (if available) -->
    {#if hasRichPreview && githubData}
      <section class="github-section">
        <GitHubRepoCard repoData={githubData} />
      </section>
    {/if}
    
    <!-- Tabs -->
    <nav class="tab-navigation">
      <button 
        class="tab-button" 
        class:active={activeTab === 'overview'}
        on:click={() => activeTab = 'overview'}
      >
        <Icon name="layout" size="small" />
        Overview
      </button>
      
      {#if hasReadme}
        <button 
          class="tab-button" 
          class:active={activeTab === 'readme'}
          on:click={() => activeTab = 'readme'}
        >
          <Icon name="file-text" size="small" />
          README
        </button>
      {/if}
      
      {#if item.content || item.processed_content}
        <button 
          class="tab-button" 
          class:active={activeTab === 'content'}
          on:click={() => activeTab = 'content'}
        >
          <Icon name="align-left" size="small" />
          Content
        </button>
      {/if}
      
      {#if item.code_snippets && item.code_snippets.length > 0}
        <button 
          class="tab-button" 
          class:active={activeTab === 'code'}
          on:click={() => activeTab = 'code'}
        >
          <Icon name="code" size="small" />
          Code Snippets
        </button>
      {/if}
      
      {#if item.metadata?.ai_analysis}
        <button 
          class="tab-button" 
          class:active={activeTab === 'insights'}
          on:click={() => activeTab = 'insights'}
        >
          <Icon name="brain" size="small" />
          AI Insights
        </button>
      {/if}
    </nav>
    
    <!-- Tab Content -->
    <div class="tab-content">
      {#if activeTab === 'overview'}
        <section class="overview-section">
          {#if item.summary}
            <div class="content-card">
              <h2>Summary</h2>
              <p class="summary-text">{item.summary}</p>
            </div>
          {/if}
          
          {#if item.tags && item.tags.length > 0}
            <div class="content-card">
              <h2>Tags</h2>
              <div class="tags-container">
                {#each item.tags as tag}
                  <span class="tag">#{tag}</span>
                {/each}
              </div>
            </div>
          {/if}
          
          {#if item.learning_path}
            <div class="content-card">
              <h2>Learning Path</h2>
              <p>{item.learning_path}</p>
            </div>
          {/if}
        </section>
        
      {:else if activeTab === 'readme' && hasReadme}
        <section class="readme-section">
          <div class="content-card full-width">
            <MarkdownViewer content={readmeContent} enableSyntaxHighlight={true} theme="neural" />
          </div>
        </section>
        
      {:else if activeTab === 'content'}
        <section class="content-section">
          <div class="content-card full-width">
            {#if item.content?.includes('#') || item.content?.includes('```')}
              <MarkdownViewer content={item.content} enableSyntaxHighlight={true} theme="neural" />
            {:else}
              <div class="plain-content">
                {item.content || item.processed_content || 'No content available'}
              </div>
            {/if}
          </div>
        </section>
        
      {:else if activeTab === 'code' && item.code_snippets}
        <section class="code-section">
          {#each item.code_snippets as snippet, index}
            <div class="content-card">
              <h3>Code Snippet {index + 1}</h3>
              <pre><code>{snippet}</code></pre>
            </div>
          {/each}
        </section>
        
      {:else if activeTab === 'insights' && item.metadata?.ai_analysis}
        {@const analysis = item.metadata.ai_analysis}
        <section class="insights-section">
          {#if analysis.key_points && analysis.key_points.length > 0}
            <div class="content-card">
              <h2>Key Points</h2>
              <ul class="key-points">
                {#each analysis.key_points as point}
                  <li>{point}</li>
                {/each}
              </ul>
            </div>
          {/if}
          
          {#if analysis.questions && analysis.questions.length > 0}
            <div class="content-card">
              <h2>Questions This Answers</h2>
              <ul class="questions">
                {#each analysis.questions as question}
                  <li>{question}</li>
                {/each}
              </ul>
            </div>
          {/if}
          
          {#if analysis.entities}
            <div class="content-card">
              <h2>Related Concepts</h2>
              <div class="entities">
                {#each Object.entries(analysis.entities) as [category, items]}
                  {#if Array.isArray(items) && items.length > 0}
                    <div class="entity-group">
                      <h4>{category}</h4>
                      <div class="entity-items">
                        {#each items as item}
                          <span class="entity-tag">{item}</span>
                        {/each}
                      </div>
                    </div>
                  {/if}
                {/each}
              </div>
            </div>
          {/if}
        </section>
      {/if}
    </div>
    
    <!-- Copy Notification -->
    {#if copyNotification}
      <div class="copy-notification">
        <Icon name="check" size="small" />
        Copied to clipboard!
      </div>
    {/if}
  </div>
{/if}

<style>
  .development-item-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    color: #00ff88;
    font-family: 'JetBrains Mono', monospace;
  }
  
  /* Loading State */
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 50vh;
    gap: 1rem;
  }
  
  .neural-pulse {
    width: 40px;
    height: 40px;
    border: 2px solid rgba(0, 255, 136, 0.3);
    border-top: 2px solid #00ff88;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  /* Error State */
  .error-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 50vh;
    gap: 1rem;
    text-align: center;
  }
  
  .error-container h2 {
    color: #DC143C;
    margin: 0;
  }
  
  /* Header */
  .item-header {
    margin-bottom: 2rem;
  }
  
  .header-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }
  
  .back-link {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: rgba(0, 255, 136, 0.7);
    background: none;
    border: none;
    cursor: pointer;
    font-family: inherit;
    font-size: 0.9rem;
    transition: color 0.2s;
    padding: 0.5rem 1rem;
    margin-left: -1rem;
  }
  
  .back-link:hover {
    color: #00ff88;
  }
  
  .header-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .action-button {
    padding: 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 6px;
    color: rgba(0, 255, 136, 0.8);
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .action-button:hover {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
    transform: translateY(-2px);
  }
  
  .header-content {
    margin-bottom: 1rem;
  }
  
  .item-title {
    font-size: 2rem;
    margin: 0 0 1rem 0;
    background: linear-gradient(45deg, #00ff88, #DC143C);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
  }
  
  .item-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }
  
  .meta-badge {
    padding: 0.375rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }
  
  .meta-badge.language {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }
  
  .meta-badge.category {
    background: rgba(74, 158, 255, 0.2);
    color: #4a9eff;
  }
  
  .meta-badge.career {
    background: rgba(220, 20, 60, 0.2);
    color: #DC143C;
  }
  
  .meta-badge.date {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.6);
  }
  
  /* GitHub Section */
  .github-section {
    margin-bottom: 2rem;
  }
  
  /* Tab Navigation */
  .tab-navigation {
    display: flex;
    gap: 0.5rem;
    border-bottom: 1px solid rgba(0, 255, 136, 0.3);
    margin-bottom: 2rem;
    overflow-x: auto;
  }
  
  .tab-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: rgba(0, 255, 136, 0.6);
    cursor: pointer;
    font-family: inherit;
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.2s;
    white-space: nowrap;
  }
  
  .tab-button:hover {
    color: rgba(0, 255, 136, 0.8);
  }
  
  .tab-button.active {
    color: #00ff88;
    border-bottom-color: #00ff88;
  }
  
  /* Tab Content */
  .tab-content {
    min-height: 400px;
  }
  
  /* Content Cards */
  .content-card {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }
  
  .content-card.full-width {
    padding: 2rem;
  }
  
  .content-card h2 {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    color: #00ff88;
  }
  
  .content-card h3 {
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    color: rgba(0, 255, 136, 0.9);
  }
  
  .summary-text {
    line-height: 1.6;
    color: rgba(255, 255, 255, 0.9);
  }
  
  /* Tags */
  .tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .tag {
    padding: 0.375rem 0.75rem;
    background: rgba(0, 255, 136, 0.1);
    color: rgba(0, 255, 136, 0.8);
    border-radius: 16px;
    font-size: 0.875rem;
  }
  
  /* Plain Content */
  .plain-content {
    white-space: pre-wrap;
    line-height: 1.6;
    color: rgba(255, 255, 255, 0.9);
  }
  
  /* Code Section */
  .code-section pre {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
    overflow-x: auto;
  }
  
  .code-section code {
    color: #00ff88;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.875rem;
  }
  
  /* Insights Section */
  .key-points, .questions {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .key-points li, .questions li {
    padding: 0.75rem 0 0.75rem 2rem;
    position: relative;
    border-bottom: 1px solid rgba(0, 255, 136, 0.1);
  }
  
  .key-points li:last-child, .questions li:last-child {
    border-bottom: none;
  }
  
  .key-points li::before {
    content: "→";
    position: absolute;
    left: 0;
    color: #00ff88;
    font-weight: bold;
  }
  
  .questions li::before {
    content: "?";
    position: absolute;
    left: 0;
    color: #DC143C;
    font-weight: bold;
  }
  
  .entity-group {
    margin-bottom: 1.5rem;
  }
  
  .entity-group:last-child {
    margin-bottom: 0;
  }
  
  .entity-group h4 {
    margin: 0 0 0.75rem 0;
    color: rgba(0, 255, 136, 0.8);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .entity-items {
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
  
  /* Copy Notification */
  .copy-notification {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    background: #00ff88;
    color: #000;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    animation: slideUp 0.3s ease;
    z-index: 1000;
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
  
  /* Back Button */
  .back-button {
    padding: 0.75rem 1.5rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    border-radius: 8px;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.2s;
  }
  
  .back-button:hover {
    background: rgba(0, 255, 136, 0.2);
    transform: translateY(-2px);
  }
  
  /* Responsive */
  @media (max-width: 768px) {
    .development-item-page {
      padding: 1rem;
    }
    
    .item-title {
      font-size: 1.5rem;
    }
    
    .tab-button {
      padding: 0.5rem 1rem;
      font-size: 0.875rem;
    }
    
    .content-card {
      padding: 1rem;
    }
  }
</style>