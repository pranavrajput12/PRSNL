<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import type { DevelopmentItem } from '$lib/api/development';

  let link: DevelopmentItem | null = null;
  let relatedLinks: DevelopmentItem[] = [];
  let loading = true;
  let error: string | null = null;
  
  // UI State
  let activeTab = 'overview'; // overview, preview, related, ai-analysis
  let sidebarCollapsed = false;
  let previewMode = 'rendered'; // rendered, raw, split
  
  // AI Analysis
  let aiInsights: string[] = [];
  let isAIAnalyzing = false;

  $: linkId = $page.params.id;

  onMount(async () => {
    if (linkId) {
      await loadLink();
    }
  });

  async function loadLink() {
    try {
      loading = true;
      error = null;

      // Fetch link details
      const response = await fetch(`/api/development/docs?content_type=tools`);
      if (!response.ok) throw new Error('Failed to fetch link');
      
      const links = await response.json();
      link = links.find((l: DevelopmentItem) => l.id === linkId);
      
      if (!link) throw new Error('Link not found');

      // Load related links
      await loadRelatedLinks();
      
      // Generate AI insights
      await generateAIInsights();
      
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unknown error';
    } finally {
      loading = false;
    }
  }

  async function loadRelatedLinks() {
    if (!link) return;
    
    try {
      const response = await fetch(`/api/development/docs?content_type=tools&limit=6`);
      if (response.ok) {
        const links = await response.json();
        relatedLinks = links
          .filter((l: DevelopmentItem) => 
            l.id !== link?.id && 
            (l.project_category === link?.project_category ||
             l.programming_language === link?.programming_language ||
             l.tags.some(tag => link?.tags.includes(tag)) ||
             getDomain(l.url) === getDomain(link?.url))
          )
          .slice(0, 5);
      }
    } catch (err) {
      console.error('Failed to load related links:', err);
    }
  }

  async function generateAIInsights() {
    if (!link) return;
    
    try {
      isAIAnalyzing = true;
      // Simulate AI analysis - replace with actual AI service call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const domain = getDomain(link.url);
      const toolType = getToolType(link);
      
      aiInsights = [
        `This ${toolType} from ${domain} is ${link.is_career_related ? 'highly relevant' : 'useful'} for professional development.`,
        `Domain analysis: ${domain} is ${getDomainPopularity(domain)} in the developer community.`,
        `Tool category: ${link.project_category || 'General utility'} with ${link.tags.length} relevant tags.`,
        `Usage recommendation: ${getUsageRecommendation(link)}`,
        `Integration potential: ${getIntegrationPotential(link)}`
      ];
    } catch (err) {
      console.error('AI analysis failed:', err);
    } finally {
      isAIAnalyzing = false;
    }
  }

  function getDomain(url: string): string {
    try {
      return new URL(url).hostname.replace('www.', '');
    } catch {
      return 'unknown';
    }
  }

  function getDomainIcon(domain: string): string {
    const icons = {
      'github.com': '🐙',
      'gitlab.com': '🦊',
      'stackoverflow.com': '📚',
      'medium.com': '📝',
      'dev.to': '💻',
      'youtube.com': '📺',
      'docs.google.com': '📄',
      'notion.so': '📝',
      'npm.js': '📦',
      'pypi.org': '🐍',
      'crates.io': '📦',
      'docker.com': '🐳',
      'vercel.com': '▲',
      'netlify.com': '🌐',
      'figma.com': '🎨',
      'canva.com': '🎨',
      'slack.com': '💬',
      'discord.com': '🎮',
      'trello.com': '📋',
      'asana.com': '✅',
    };
    return icons[domain] || '🔗';
  }

  function getDomainColor(domain: string): string {
    const colors = {
      'github.com': '#24292e',
      'gitlab.com': '#fc6d26',
      'stackoverflow.com': '#f48024',
      'medium.com': '#00ab6c',
      'dev.to': '#0a0a0a',
      'youtube.com': '#ff0000',
      'docs.google.com': '#4285f4',
      'notion.so': '#000000',
      'figma.com': '#f24e1e',
      'vercel.com': '#000000',
      'netlify.com': '#00c7b7',
    };
    return colors[domain] || '#00ff88';
  }

  function getToolType(link: DevelopmentItem): string {
    if (link.tags.some(tag => tag.toLowerCase().includes('design'))) return 'design tool';
    if (link.tags.some(tag => tag.toLowerCase().includes('deploy'))) return 'deployment platform';
    if (link.tags.some(tag => tag.toLowerCase().includes('api'))) return 'API service';
    if (link.tags.some(tag => tag.toLowerCase().includes('database'))) return 'database service';
    if (link.tags.some(tag => tag.toLowerCase().includes('monitor'))) return 'monitoring tool';
    return 'development tool';
  }

  function getDomainPopularity(domain: string): string {
    const popular = ['github.com', 'stackoverflow.com', 'npm.js', 'docker.com', 'vercel.com'];
    const moderate = ['gitlab.com', 'dev.to', 'medium.com', 'figma.com', 'notion.so'];
    
    if (popular.includes(domain)) return 'extremely popular';
    if (moderate.includes(domain)) return 'well-known';
    return 'specialized';
  }

  function getUsageRecommendation(link: DevelopmentItem): string {
    if (link.is_career_related) return 'Essential for professional development';
    if (link.difficulty_level && link.difficulty_level >= 4) return 'Best for experienced developers';
    if (link.difficulty_level && link.difficulty_level <= 2) return 'Great for beginners and teams';
    return 'Suitable for all skill levels';
  }

  function getIntegrationPotential(link: DevelopmentItem): string {
    const domain = getDomain(link.url);
    if (domain.includes('api') || link.tags.some(tag => tag.toLowerCase().includes('api'))) {
      return 'High - offers API integration';
    }
    if (link.tags.some(tag => tag.toLowerCase().includes('webhook'))) {
      return 'High - supports webhooks';
    }
    if (link.tags.some(tag => tag.toLowerCase().includes('cli'))) {
      return 'Medium - CLI available';
    }
    return 'Low - primarily web-based';
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
    goto('/code-cortex/links');
  }

  function handleOpenExternal() {
    if (link?.url) {
      window.open(link.url, '_blank');
    }
  }

  function getToolCategoryIcon(category: string): string {
    const icons = {
      'design': '🎨',
      'deployment': '🚀',
      'database': '🗄️',
      'api': '🔌',
      'monitoring': '📊',
      'security': '🔒',
      'testing': '🧪',
      'documentation': '📚',
      'collaboration': '👥',
      'productivity': '⚡',
    };
    
    for (const [key, icon] of Object.entries(icons)) {
      if (category.toLowerCase().includes(key)) return icon;
    }
    return '🔧';
  }
</script>

<svelte:head>
  <title>{link?.title || 'Tool/Link'} - Code Cortex | PRSNL</title>
</svelte:head>

{#if loading}
  <div class="loading-container">
    <div class="neural-pulse"></div>
    <span>Loading tool details...</span>
  </div>
{:else if error}
  <div class="error-container">
    <Icon name="alert-circle" size="48" />
    <h2>Error Loading Tool</h2>
    <p>{error}</p>
    <button class="back-button" on:click={handleBackToList}>
      <Icon name="arrow-left" size="16" />
      Back to Tools & Links
    </button>
  </div>
{:else if link}
  <div class="link-detail-page">
    <!-- Header -->
    <div class="link-header">
      <div class="header-content">
        <div class="header-left">
          <button class="back-button" on:click={handleBackToList}>
            <Icon name="arrow-left" size="16" />
          </button>
          <div class="link-title-section">
            <h1>{link.title}</h1>
            <div class="link-meta">
              <span class="meta-badge domain" style="background-color: {getDomainColor(getDomain(link.url))}40; color: {getDomainColor(getDomain(link.url))}">
                {getDomainIcon(getDomain(link.url))} {getDomain(link.url)}
              </span>
              {#if link.project_category}
                <span class="meta-badge category">
                  {getToolCategoryIcon(link.project_category)} {link.project_category}
                </span>
              {/if}
              {#if link.programming_language}
                <span class="meta-badge language">
                  {getLanguageIcon(link.programming_language)} {link.programming_language}
                </span>
              {/if}
              {#if link.is_career_related}
                <span class="meta-badge career">💼 Career Essential</span>
              {/if}
            </div>
          </div>
        </div>
        <div class="header-actions">
          <button class="action-button secondary" on:click={() => sidebarCollapsed = !sidebarCollapsed}>
            <Icon name={sidebarCollapsed ? 'sidebar' : 'x'} size="16" />
            {sidebarCollapsed ? 'Show' : 'Hide'} Details
          </button>
          <button class="action-button primary" on:click={handleOpenExternal}>
            <Icon name="external-link" size="16" />
            Visit Tool
          </button>
        </div>
      </div>
    </div>

    <div class="link-layout">
      <!-- Sidebar -->
      {#if !sidebarCollapsed}
        <div class="link-sidebar">
          <div class="sidebar-section">
            <h3>🔗 Tool Details</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Domain</span>
                <span class="detail-value">{getDomain(link.url)}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Type</span>
                <span class="detail-value">{getToolType(link)}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Added</span>
                <span class="detail-value">{formatDate(link.created_at)}</span>
              </div>
              {#if link.updated_at}
                <div class="detail-item">
                  <span class="detail-label">Updated</span>
                  <span class="detail-value">{formatDate(link.updated_at)}</span>
                </div>
              {/if}
            </div>
          </div>

          {#if link.tags.length > 0}
            <div class="sidebar-section">
              <h3>🏷️ Tags</h3>
              <div class="tags-container">
                {#each link.tags as tag}
                  <span class="tag">{tag}</span>
                {/each}
              </div>
            </div>
          {/if}

          {#if relatedLinks.length > 0}
            <div class="sidebar-section">
              <h3>🔗 Related Tools</h3>
              <div class="related-list">
                {#each relatedLinks as relatedLink}
                  <a href="/code-cortex/links/{relatedLink.id}" class="related-item">
                    <div class="related-icon">{getDomainIcon(getDomain(relatedLink.url))}</div>
                    <div class="related-content">
                      <div class="related-title">{relatedLink.title}</div>
                      <div class="related-domain">{getDomain(relatedLink.url)}</div>
                    </div>
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
              <button class="quick-action" on:click={() => activeTab = 'preview'}>
                <Icon name="eye" size="16" />
                Preview
              </button>
              <button class="quick-action" on:click={() => activeTab = 'ai-analysis'}>
                <Icon name="brain" size="16" />
                AI Analysis
              </button>
              <button class="quick-action" on:click={handleOpenExternal}>
                <Icon name="external-link" size="16" />
                Open Tool
              </button>
            </div>
          </div>
        </div>
      {/if}

      <!-- Main Content -->
      <div class="link-main">
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
            class="tab {activeTab === 'preview' ? 'active' : ''}"
            on:click={() => activeTab = 'preview'}
          >
            <Icon name="eye" size="16" />
            Preview
          </button>
          <button 
            class="tab {activeTab === 'related' ? 'active' : ''}"
            on:click={() => activeTab = 'related'}
          >
            <Icon name="link" size="16" />
            Related ({relatedLinks.length})
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
                <h2>Tool Overview</h2>
                <p>Comprehensive details about this development tool or service</p>
              </div>
              
              {#if link.summary}
                <div class="content-section">
                  <h3>Description</h3>
                  <div class="summary-content">
                    {link.summary}
                  </div>
                </div>
              {/if}

              <div class="content-section">
                <h3>Tool Information</h3>
                <div class="technical-grid">
                  <div class="tech-item">
                    <span class="tech-label">Domain</span>
                    <span class="tech-value">{getDomain(link.url)}</span>
                  </div>
                  <div class="tech-item">
                    <span class="tech-label">Type</span>
                    <span class="tech-value">{getToolType(link)}</span>
                  </div>
                  {#if link.project_category}
                    <div class="tech-item">
                      <span class="tech-label">Category</span>
                      <span class="tech-value">{link.project_category}</span>
                    </div>
                  {/if}
                  {#if link.programming_language}
                    <div class="tech-item">
                      <span class="tech-label">Language</span>
                      <span class="tech-value">{link.programming_language}</span>
                    </div>
                  {/if}
                  <div class="tech-item">
                    <span class="tech-label">Popularity</span>
                    <span class="tech-value">{getDomainPopularity(getDomain(link.url))}</span>
                  </div>
                  <div class="tech-item">
                    <span class="tech-label">Integration</span>
                    <span class="tech-value">{getIntegrationPotential(link)}</span>
                  </div>
                </div>
              </div>
            </div>

          {:else if activeTab === 'preview'}
            <div class="preview-tab">
              <div class="content-header">
                <h2>Tool Preview</h2>
                <div class="preview-controls">
                  <button class="preview-btn primary" on:click={handleOpenExternal}>
                    <Icon name="external-link" size="16" />
                    Open in New Tab
                  </button>
                </div>
              </div>
              
              <div class="preview-container">
                <div class="preview-info">
                  <div class="preview-meta">
                    <span class="preview-domain">{getDomainIcon(getDomain(link.url))} {getDomain(link.url)}</span>
                    <span class="preview-type">{getToolType(link)}</span>
                  </div>
                  <h3>{link.title}</h3>
                  {#if link.summary}
                    <p>{link.summary}</p>
                  {/if}
                </div>
                
                <div class="preview-frame">
                  <iframe 
                    src={link.url} 
                    title="Tool Preview"
                    sandbox="allow-same-origin allow-scripts allow-forms"
                    loading="lazy"
                  ></iframe>
                  <div class="preview-overlay">
                    <button class="preview-overlay-btn" on:click={handleOpenExternal}>
                      <Icon name="external-link" size="24" />
                      <span>Click to open {getDomain(link.url)}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

          {:else if activeTab === 'related'}
            <div class="related-tab">
              <div class="content-header">
                <h2>Related Tools</h2>
                <p>Similar tools and services based on category and domain</p>
              </div>
              
              {#if relatedLinks.length > 0}
                <div class="related-grid">
                  {#each relatedLinks as relatedLink}
                    <a href="/code-cortex/links/{relatedLink.id}" class="related-card">
                      <div class="card-header">
                        <div class="card-icon">{getDomainIcon(getDomain(relatedLink.url))}</div>
                        <div class="card-title-section">
                          <h3>{relatedLink.title}</h3>
                          <span class="card-domain">{getDomain(relatedLink.url)}</span>
                        </div>
                      </div>
                      {#if relatedLink.summary}
                        <p class="card-summary">{relatedLink.summary.slice(0, 120)}...</p>
                      {/if}
                      <div class="card-meta">
                        {#if relatedLink.project_category}
                          <span class="meta-tag">{relatedLink.project_category}</span>
                        {/if}
                        {#if relatedLink.programming_language}
                          <span class="meta-tag">{getLanguageIcon(relatedLink.programming_language)} {relatedLink.programming_language}</span>
                        {/if}
                      </div>
                    </a>
                  {/each}
                </div>
              {:else}
                <div class="empty-state">
                  <Icon name="search" size="48" />
                  <h3>No Related Tools</h3>
                  <p>No related tools found based on current criteria.</p>
                </div>
              {/if}
            </div>

          {:else if activeTab === 'ai-analysis'}
            <div class="ai-analysis-tab">
              <div class="content-header">
                <h2>AI Analysis</h2>
                <p>AI-powered insights about this tool and its potential</p>
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
                  <span>AI is analyzing the tool...</span>
                </div>
              {:else if aiInsights.length > 0}
                <div class="ai-insights">
                  {#each aiInsights as insight, index}
                    <div class="insight-card">
                      <div class="insight-icon">🤖</div>
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
    <Icon name="link-2" size="48" />
    <h2>Tool Not Found</h2>
    <p>The requested tool or link could not be found.</p>
    <button class="back-button" on:click={handleBackToList}>
      <Icon name="arrow-left" size="16" />
      Back to Tools & Links
    </button>
  </div>
{/if}

<style>
  .link-detail-page {
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

  .link-header {
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

  .link-title-section h1 {
    margin: 0 0 0.5rem 0;
    font-size: 1.75rem;
    color: #00ff88;
    line-height: 1.2;
  }

  .link-meta {
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

  .link-layout {
    display: flex;
    max-width: 1400px;
    margin: 0 auto;
    min-height: calc(100vh - 120px);
  }

  .link-sidebar {
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
    display: flex;
    align-items: center;
    gap: 0.75rem;
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

  .related-icon {
    font-size: 1.2rem;
    min-width: 24px;
    text-align: center;
  }

  .related-content {
    flex: 1;
    min-width: 0;
  }

  .related-title {
    font-size: 0.875rem;
    color: #e0e0e0;
    margin-bottom: 0.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .related-domain {
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

  .link-main {
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

  .preview-controls {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .preview-btn {
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

  .preview-btn.primary {
    background: rgba(0, 255, 136, 0.1);
    border-color: rgba(0, 255, 136, 0.3);
    color: #00ff88;
  }

  .preview-btn.primary:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .preview-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .preview-info {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
  }

  .preview-meta {
    display: flex;
    gap: 1rem;
    margin-bottom: 0.75rem;
  }

  .preview-domain {
    padding: 0.25rem 0.75rem;
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .preview-type {
    padding: 0.25rem 0.75rem;
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .preview-info h3 {
    margin: 0 0 0.5rem 0;
    color: #e0e0e0;
  }

  .preview-info p {
    margin: 0;
    color: #ccc;
    line-height: 1.5;
  }

  .preview-frame {
    position: relative;
    width: 100%;
    height: 600px;
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    overflow: hidden;
  }

  .preview-frame iframe {
    width: 100%;
    height: 100%;
    border: none;
  }

  .preview-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .preview-frame:hover .preview-overlay {
    opacity: 1;
  }

  .preview-overlay-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    background: rgba(0, 255, 136, 0.2);
    border: 1px solid rgba(0, 255, 136, 0.4);
    color: #00ff88;
    padding: 1rem 2rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .preview-overlay-btn:hover {
    background: rgba(0, 255, 136, 0.3);
    border-color: #00ff88;
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
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .card-icon {
    font-size: 1.5rem;
    min-width: 32px;
    text-align: center;
  }

  .card-title-section h3 {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    color: #e0e0e0;
  }

  .card-domain {
    font-size: 0.75rem;
    color: #888;
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

    .link-layout {
      flex-direction: column;
    }

    .link-sidebar {
      width: 100%;
      max-height: none;
    }

    .technical-grid {
      grid-template-columns: 1fr;
    }

    .related-grid {
      grid-template-columns: 1fr;
    }

    .preview-frame {
      height: 400px;
    }
  }
</style>