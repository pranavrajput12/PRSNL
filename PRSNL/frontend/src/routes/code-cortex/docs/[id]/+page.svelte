<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import MarkdownViewer from '$lib/components/development/MarkdownViewer.svelte';
  import type { DevelopmentItem } from '$lib/api/development';

  let doc: DevelopmentItem | null = null;
  let relatedDocs: DevelopmentItem[] = [];
  let loading = true;
  let error: string | null = null;
  
  // UI State
  let activeTab = 'overview'; // overview, content, related, ai-analysis
  let sidebarCollapsed = false;
  let previewMode = 'rendered'; // rendered, raw, split
  
  // AI Analysis
  let aiInsights: string[] = [];
  let isAIAnalyzing = false;

  $: docId = $page.params.id;

  onMount(async () => {
    if (docId) {
      await loadDocument();
    }
  });

  async function loadDocument() {
    try {
      loading = true;
      error = null;

      // Fetch document details
      const response = await fetch(`/api/development/docs?content_type=knowledge`);
      if (!response.ok) throw new Error('Failed to fetch documentation');
      
      const docs = await response.json();
      doc = docs.find((d: DevelopmentItem) => d.id === docId);
      
      if (!doc) throw new Error('Documentation not found');

      // Load related documentation
      await loadRelatedDocs();
      
      // Generate AI insights
      await generateAIInsights();
      
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unknown error';
    } finally {
      loading = false;
    }
  }

  async function loadRelatedDocs() {
    if (!doc) return;
    
    try {
      const response = await fetch(`/api/development/docs?content_type=knowledge&limit=6`);
      if (response.ok) {
        const docs = await response.json();
        relatedDocs = docs
          .filter((d: DevelopmentItem) => 
            d.id !== doc?.id && 
            (d.project_category === doc?.project_category ||
             d.programming_language === doc?.programming_language ||
             d.tags.some(tag => doc?.tags.includes(tag)))
          )
          .slice(0, 5);
      }
    } catch (err) {
      console.error('Failed to load related docs:', err);
    }
  }

  async function generateAIInsights() {
    if (!doc) return;
    
    try {
      isAIAnalyzing = true;
      // Simulate AI analysis - replace with actual AI service call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      aiInsights = [
        `This ${doc.project_category?.toLowerCase() || 'documentation'} covers key concepts with ${doc.difficulty_level ? 'difficulty level ' + doc.difficulty_level : 'intermediate complexity'}.`,
        `The content is ${doc.is_career_related ? 'career-relevant' : 'educational'} and includes practical examples.`,
        `Related topics: ${doc.tags.slice(0, 3).join(', ')}`,
        `Estimated reading time: ${Math.ceil((doc.summary?.length || 500) / 200)} minutes`
      ];
    } catch (err) {
      console.error('AI analysis failed:', err);
    } finally {
      isAIAnalyzing = false;
    }
  }

  function getDifficultyColor(level: number): string {
    const colors = {
      1: '#10b981', // Green
      2: '#3b82f6', // Blue  
      3: '#f59e0b', // Amber
      4: '#ef4444', // Red
      5: '#8b5cf6', // Purple
    };
    return colors[level] || '#6b7280';
  }

  function getDifficultyLabel(level: number): string {
    const labels = {
      1: 'Beginner',
      2: 'Intermediate', 
      3: 'Advanced',
      4: 'Expert',
      5: 'Master',
    };
    return labels[level] || 'Unknown';
  }

  function getLanguageIcon(language: string): string {
    const icons = {
      python: '🐍',
      javascript: '🟨',
      typescript: '🔷',
      java: '☕',
      go: '🐹',
      rust: '🦀',
      cpp: '⚡',
    };
    return icons[language] || '💻';
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long', 
      day: 'numeric'
    });
  }

  function handleBackToList() {
    goto('/code-cortex/docs');
  }

  function handleOpenExternal() {
    if (doc?.url) {
      window.open(doc.url, '_blank');
    }
  }
</script>

<svelte:head>
  <title>{doc?.title || 'Documentation'} - Code Cortex | PRSNL</title>
</svelte:head>

{#if loading}
  <div class="loading-container">
    <div class="neural-pulse"></div>
    <span>Loading documentation...</span>
  </div>
{:else if error}
  <div class="error-container">
    <Icon name="alert-circle" size="48" />
    <h2>Error Loading Documentation</h2>
    <p>{error}</p>
    <button class="back-button" on:click={handleBackToList}>
      <Icon name="arrow-left" size="16" />
      Back to Documentation
    </button>
  </div>
{:else if doc}
  <div class="doc-detail-page">
    <!-- Header -->
    <div class="doc-header">
      <div class="header-content">
        <div class="header-left">
          <button class="back-button" on:click={handleBackToList}>
            <Icon name="arrow-left" size="16" />
          </button>
          <div class="doc-title-section">
            <h1>{doc.title}</h1>
            <div class="doc-meta">
              {#if doc.project_category}
                <span class="meta-badge category">{doc.project_category}</span>
              {/if}
              {#if doc.programming_language}
                <span class="meta-badge language">
                  {getLanguageIcon(doc.programming_language)} {doc.programming_language}
                </span>
              {/if}
              {#if doc.difficulty_level}
                <span class="meta-badge difficulty" style="background-color: {getDifficultyColor(doc.difficulty_level)}40; color: {getDifficultyColor(doc.difficulty_level)}">
                  {getDifficultyLabel(doc.difficulty_level)}
                </span>
              {/if}
              {#if doc.is_career_related}
                <span class="meta-badge career">💼 Career</span>
              {/if}
            </div>
          </div>
        </div>
        <div class="header-actions">
          <button class="action-button secondary" on:click={() => sidebarCollapsed = !sidebarCollapsed}>
            <Icon name={sidebarCollapsed ? 'sidebar' : 'x'} size="16" />
            {sidebarCollapsed ? 'Show' : 'Hide'} Details
          </button>
          {#if doc.url}
            <button class="action-button primary" on:click={handleOpenExternal}>
              <Icon name="external-link" size="16" />
              Open Source
            </button>
          {/if}
        </div>
      </div>
    </div>

    <div class="doc-layout">
      <!-- Sidebar -->
      {#if !sidebarCollapsed}
        <div class="doc-sidebar">
          <div class="sidebar-section">
            <h3>📊 Details</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Created</span>
                <span class="detail-value">{formatDate(doc.created_at)}</span>
              </div>
              {#if doc.updated_at}
                <div class="detail-item">
                  <span class="detail-label">Updated</span>
                  <span class="detail-value">{formatDate(doc.updated_at)}</span>
                </div>
              {/if}
              {#if doc.learning_path}
                <div class="detail-item">
                  <span class="detail-label">Learning Path</span>
                  <span class="detail-value">{doc.learning_path}</span>
                </div>
              {/if}
            </div>
          </div>

          {#if doc.tags.length > 0}
            <div class="sidebar-section">
              <h3>🏷️ Tags</h3>
              <div class="tags-container">
                {#each doc.tags as tag}
                  <span class="tag">{tag}</span>
                {/each}
              </div>
            </div>
          {/if}

          {#if relatedDocs.length > 0}
            <div class="sidebar-section">
              <h3>🔗 Related Docs</h3>
              <div class="related-list">
                {#each relatedDocs as relatedDoc}
                  <a href="/code-cortex/docs/{relatedDoc.id}" class="related-item">
                    <div class="related-title">{relatedDoc.title}</div>
                    {#if relatedDoc.project_category}
                      <div class="related-category">{relatedDoc.project_category}</div>
                    {/if}
                  </a>
                {/each}
              </div>
            </div>
          {/if}

          <div class="sidebar-section">
            <h3>⚡ Quick Actions</h3>
            <div class="quick-actions">
              <button class="quick-action" on:click={() => activeTab = 'overview'}>
                <Icon name="info" size="16" />
                Overview
              </button>
              <button class="quick-action" on:click={() => activeTab = 'content'}>
                <Icon name="file-text" size="16" />
                Content
              </button>
              <button class="quick-action" on:click={() => activeTab = 'ai-analysis'}>
                <Icon name="brain" size="16" />
                AI Analysis
              </button>
            </div>
          </div>
        </div>
      {/if}

      <!-- Main Content -->
      <div class="doc-main">
        <!-- Tab Navigation -->
        <div class="tab-navigation">
          <button 
            class="tab {activeTab === 'overview' ? 'active' : ''}"
            on:click={() => activeTab = 'overview'}
          >
            <Icon name="info" size="16" />
            Overview
          </button>
          <button 
            class="tab {activeTab === 'content' ? 'active' : ''}"
            on:click={() => activeTab = 'content'}
          >
            <Icon name="file-text" size="16" />
            Content
          </button>
          <button 
            class="tab {activeTab === 'related' ? 'active' : ''}"
            on:click={() => activeTab = 'related'}
          >
            <Icon name="link" size="16" />
            Related ({relatedDocs.length})
          </button>
          <button 
            class="tab {activeTab === 'ai-analysis' ? 'active' : ''}"
            on:click={() => activeTab = 'ai-analysis'}
          >
            <Icon name="brain" size="16" />
            AI Analysis
          </button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
          {#if activeTab === 'overview'}
            <div class="overview-content">
              <div class="content-header">
                <h2>Documentation Overview</h2>
                <p>Comprehensive details about this documentation</p>
              </div>
              
              {#if doc.summary}
                <div class="content-section">
                  <h3>Summary</h3>
                  <div class="summary-content">
                    {doc.summary}
                  </div>
                </div>
              {/if}

              <div class="content-section">
                <h3>Technical Details</h3>
                <div class="technical-grid">
                  <div class="tech-item">
                    <span class="tech-label">Type</span>
                    <span class="tech-value">{doc.type || 'Documentation'}</span>
                  </div>
                  {#if doc.project_category}
                    <div class="tech-item">
                      <span class="tech-label">Category</span>
                      <span class="tech-value">{doc.project_category}</span>
                    </div>
                  {/if}
                  {#if doc.programming_language}
                    <div class="tech-item">
                      <span class="tech-label">Language</span>
                      <span class="tech-value">{doc.programming_language}</span>
                    </div>
                  {/if}
                  {#if doc.difficulty_level}
                    <div class="tech-item">
                      <span class="tech-label">Difficulty</span>
                      <span class="tech-value">{getDifficultyLabel(doc.difficulty_level)}</span>
                    </div>
                  {/if}
                </div>
              </div>
            </div>

          {:else if activeTab === 'content'}
            <div class="content-tab">
              <div class="content-header">
                <h2>Documentation Content</h2>
                <div class="content-controls">
                  <select bind:value={previewMode} class="view-selector">
                    <option value="rendered">Rendered View</option>
                    <option value="raw">Raw Content</option>
                    <option value="split">Split View</option>
                  </select>
                </div>
              </div>
              
              <div class="content-viewer {previewMode}">
                {#if previewMode === 'rendered' || previewMode === 'split'}
                  <div class="rendered-content">
                    {#if doc.summary}
                      <MarkdownViewer 
                        content={doc.summary}
                        enableSyntaxHighlight={true}
                        theme="neural"
                      />
                    {:else}
                      <p>No content available for preview.</p>
                    {/if}
                  </div>
                {/if}
                
                {#if previewMode === 'raw' || previewMode === 'split'}
                  <div class="raw-content">
                    <pre><code>{doc.summary || 'No content available'}</code></pre>
                  </div>
                {/if}
              </div>
            </div>

          {:else if activeTab === 'related'}
            <div class="related-tab">
              <div class="content-header">
                <h2>Related Documentation</h2>
                <p>Similar documentation based on category and tags</p>
              </div>
              
              {#if relatedDocs.length > 0}
                <div class="related-grid">
                  {#each relatedDocs as relatedDoc}
                    <a href="/code-cortex/docs/{relatedDoc.id}" class="related-card">
                      <div class="card-header">
                        <h3>{relatedDoc.title}</h3>
                        {#if relatedDoc.project_category}
                          <span class="card-category">{relatedDoc.project_category}</span>
                        {/if}
                      </div>
                      {#if relatedDoc.summary}
                        <p class="card-summary">{relatedDoc.summary.slice(0, 120)}...</p>
                      {/if}
                      <div class="card-meta">
                        {#if relatedDoc.programming_language}
                          <span class="meta-tag">{getLanguageIcon(relatedDoc.programming_language)} {relatedDoc.programming_language}</span>
                        {/if}
                        {#if relatedDoc.difficulty_level}
                          <span class="meta-tag difficulty" style="color: {getDifficultyColor(relatedDoc.difficulty_level)}">
                            {getDifficultyLabel(relatedDoc.difficulty_level)}
                          </span>
                        {/if}
                      </div>
                    </a>
                  {/each}
                </div>
              {:else}
                <div class="empty-state">
                  <Icon name="search" size="48" />
                  <h3>No Related Documentation</h3>
                  <p>No related documentation found based on current criteria.</p>
                </div>
              {/if}
            </div>

          {:else if activeTab === 'ai-analysis'}
            <div class="ai-analysis-tab">
              <div class="content-header">
                <h2>AI Analysis</h2>
                <p>AI-powered insights about this documentation</p>
                <button 
                  class="refresh-analysis" 
                  on:click={generateAIInsights}
                  disabled={isAIAnalyzing}
                >
                  <Icon name={isAIAnalyzing ? 'loader' : 'refresh-cw'} size="16" />
                  {isAIAnalyzing ? 'Analyzing...' : 'Refresh Analysis'}
                </button>
              </div>
              
              {#if isAIAnalyzing}
                <div class="ai-loading">
                  <div class="neural-pulse"></div>
                  <span>AI is analyzing the documentation...</span>
                </div>
              {:else if aiInsights.length > 0}
                <div class="ai-insights">
                  {#each aiInsights as insight, index}
                    <div class="insight-card">
                      <div class="insight-icon">🧠</div>
                      <div class="insight-content">{insight}</div>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="empty-state">
                  <Icon name="brain" size="48" />
                  <h3>No AI Analysis Available</h3>
                  <p>Click "Refresh Analysis" to generate AI insights.</p>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="not-found">
    <Icon name="file-x" size="48" />
    <h2>Documentation Not Found</h2>
    <p>The requested documentation could not be found.</p>
    <button class="back-button" on:click={handleBackToList}>
      <Icon name="arrow-left" size="16" />
      Back to Documentation
    </button>
  </div>
{/if}

<style>
  .doc-detail-page {
    min-height: 100vh;
    background: #0a0a0a;
    color: #e0e0e0;
  }

  .loading-container,
  .error-container,
  .not-found {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    text-align: center;
    gap: 1rem;
    color: #e0e0e0;
  }

  .neural-pulse {
    width: 50px;
    height: 50px;
    border: 3px solid rgba(0, 255, 136, 0.3);
    border-top: 3px solid #00ff88;
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% {
      border-top-color: #00ff88;
      transform: scale(1);
    }
    50% {
      border-top-color: #00cc6a;
      transform: scale(1.1);
    }
  }

  .doc-header {
    background: rgba(0, 0, 0, 0.8);
    border-bottom: 1px solid rgba(0, 255, 136, 0.2);
    padding: 1.5rem 2rem;
    backdrop-filter: blur(10px);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    max-width: 1400px;
    margin: 0 auto;
  }

  .header-left {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
  }

  .back-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .back-button:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .doc-title-section h1 {
    margin: 0 0 0.5rem 0;
    font-size: 1.75rem;
    color: #00ff88;
    line-height: 1.2;
  }

  .doc-meta {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .meta-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .meta-badge.category {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
  }

  .meta-badge.language {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }

  .meta-badge.career {
    background: rgba(220, 20, 60, 0.2);
    color: #dc143c;
  }

  .header-actions {
    display: flex;
    gap: 0.75rem;
  }

  .action-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .action-button.primary {
    background: rgba(0, 255, 136, 0.1);
    border-color: rgba(0, 255, 136, 0.3);
    color: #00ff88;
  }

  .action-button.primary:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .action-button.secondary {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.2);
    color: #ccc;
  }

  .action-button.secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.3);
  }

  .doc-layout {
    display: flex;
    max-width: 1400px;
    margin: 0 auto;
    min-height: calc(100vh - 120px);
  }

  .doc-sidebar {
    width: 320px;
    background: rgba(0, 0, 0, 0.6);
    border-right: 1px solid rgba(0, 255, 136, 0.2);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    max-height: calc(100vh - 120px);
    overflow-y: auto;
  }

  .sidebar-section h3 {
    margin: 0 0 1rem 0;
    font-size: 0.9rem;
    color: #00ff88;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .detail-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .detail-value {
    font-size: 0.875rem;
    color: #e0e0e0;
    font-weight: 500;
  }

  .tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tag {
    padding: 0.25rem 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    color: #00ff88;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .related-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .related-item {
    padding: 0.75rem;
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.1);
    border-radius: 6px;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s ease;
  }

  .related-item:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: rgba(0, 255, 136, 0.3);
  }

  .related-title {
    font-size: 0.875rem;
    color: #e0e0e0;
    margin-bottom: 0.25rem;
  }

  .related-category {
    font-size: 0.75rem;
    color: #888;
  }

  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .quick-action {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.2);
    color: #888;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .quick-action:hover {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }

  .doc-main {
    flex: 1;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
  }

  .tab-navigation {
    display: flex;
    border-bottom: 1px solid rgba(0, 255, 136, 0.2);
    margin-bottom: 1.5rem;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: transparent;
    border: none;
    color: #888;
    cursor: pointer;
    transition: all 0.2s ease;
    border-bottom: 2px solid transparent;
  }

  .tab:hover {
    color: #00ff88;
  }

  .tab.active {
    color: #00ff88;
    border-bottom-color: #00ff88;
  }

  .tab-content {
    flex: 1;
  }

  .content-header {
    margin-bottom: 1.5rem;
  }

  .content-header h2 {
    margin: 0 0 0.5rem 0;
    color: #00ff88;
  }

  .content-header p {
    margin: 0;
    color: #888;
    font-size: 0.875rem;
  }

  .content-section {
    margin-bottom: 2rem;
  }

  .content-section h3 {
    margin: 0 0 1rem 0;
    color: #e0e0e0;
    font-size: 1.1rem;
  }

  .summary-content {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
    line-height: 1.6;
    color: #ccc;
  }

  .technical-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .tech-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.75rem;
    background: rgba(0, 255, 136, 0.05);
    border-radius: 6px;
  }

  .tech-label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .tech-value {
    font-size: 0.875rem;
    color: #e0e0e0;
    font-weight: 500;
  }

  .content-controls {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .view-selector {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
  }

  .content-viewer {
    display: flex;
    gap: 1rem;
  }

  .content-viewer.rendered .rendered-content {
    flex: 1;
  }

  .content-viewer.raw .raw-content {
    flex: 1;
  }

  .content-viewer.split .rendered-content,
  .content-viewer.split .raw-content {
    flex: 1;
  }

  .rendered-content,
  .raw-content {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
  }

  .raw-content pre {
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    color: #ccc;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.875rem;
  }

  .related-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
  }

  .related-card {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s ease;
  }

  .related-card:hover {
    border-color: rgba(0, 255, 136, 0.4);
    background: rgba(0, 255, 136, 0.05);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .card-header h3 {
    margin: 0;
    font-size: 1rem;
    color: #e0e0e0;
  }

  .card-category {
    font-size: 0.75rem;
    color: #888;
    background: rgba(0, 255, 136, 0.1);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
  }

  .card-summary {
    margin: 0 0 0.75rem 0;
    color: #ccc;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .card-meta {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .meta-tag {
    padding: 0.25rem 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    color: #888;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .refresh-analysis {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .refresh-analysis:hover:not(:disabled) {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .refresh-analysis:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .ai-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 2rem;
    text-align: center;
  }

  .ai-insights {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .insight-card {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
  }

  .insight-icon {
    font-size: 1.2rem;
    min-width: 24px;
  }

  .insight-content {
    flex: 1;
    color: #ccc;
    line-height: 1.6;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 3rem;
    text-align: center;
    color: #888;
  }

  .empty-state h3 {
    margin: 0;
    color: #ccc;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .header-content {
      flex-direction: column;
      gap: 1rem;
    }

    .doc-layout {
      flex-direction: column;
    }

    .doc-sidebar {
      width: 100%;
      max-height: none;
    }

    .technical-grid {
      grid-template-columns: 1fr;
    }

    .related-grid {
      grid-template-columns: 1fr;
    }

    .content-viewer.split {
      flex-direction: column;
    }
  }
</style>