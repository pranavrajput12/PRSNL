<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import MonacoEditor from '$lib/components/MonacoEditor.svelte';

  interface Repository {
    id: string;
    title: string;
    url: string;
    repository_metadata: {
      repo_url: string;
      repo_name: string;
      owner: string;
      description: string;
      stars: number;
      forks?: number;
      language: string;
      tech_stack: string[];
      category: string;
      difficulty: string;
      license?: string;
      topics?: string[];
      ai_analysis: {
        purpose: string;
        key_features: string[];
        confidence: number;
        learning_curve?: string;
        community_size?: string;
        maintenance_status?: string;
      };
      github_data?: any;
    };
    created_at: string;
  }

  interface RepositoryFile {
    name: string;
    content: string;
    language: string;
    size: number;
    path: string;
    type: 'file' | 'directory';
  }

  let repository: Repository | null = null;
  let files: RepositoryFile[] = [];
  let selectedFile: RepositoryFile | null = null;
  let readmeContent = '';
  let loading = true;
  let error: string | null = null;
  
  // UI State
  let activeTab = 'overview'; // overview, files, readme, ai-analysis
  let sidebarCollapsed = false;
  let previewMode = 'split'; // split, code-only, preview-only
  
  // File tree state
  let expandedDirectories = new Set<string>();
  let searchQuery = '';
  
  // AI Agent Integration
  let aiSuggestions: string[] = [];
  let isAIAnalyzing = false;

  $: repositoryId = $page.params.id;

  onMount(async () => {
    if (repositoryId) {
      await loadRepository();
    }
  });

  async function loadRepository() {
    try {
      loading = true;
      error = null;

      // Fetch repository details
      const response = await fetch(`/api/development/repositories`);
      if (!response.ok) throw new Error('Failed to fetch repository');
      
      const data = await response.json();
      const repos = (data.items || []).map((item: any) => ({
        ...item,
        repository_metadata: typeof item.repository_metadata === 'string' 
          ? JSON.parse(item.repository_metadata) 
          : item.repository_metadata
      }));
      
      repository = repos.find((r: Repository) => r.id === repositoryId);
      if (!repository) throw new Error('Repository not found');

      // Load repository files
      await loadRepositoryFiles();
      
      // Load README content
      await loadReadmeContent();
      
      // Generate AI insights
      await generateAIInsights();

    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load repository';
      console.error('Repository loading error:', err);
    } finally {
      loading = false;
    }
  }

  async function loadRepositoryFiles() {
    if (!repository) return;

    try {
      const [owner, repo] = repository.repository_metadata.repo_url
        .replace('https://github.com/', '')
        .split('/');

      // Common files to fetch
      const commonFiles = [
        'README.md', 'README.rst', 'README.txt',
        'package.json', 'requirements.txt', 'Cargo.toml', 'composer.json', 'pom.xml', 'go.mod',
        'Dockerfile', 'docker-compose.yml',
        'LICENSE', 'LICENSE.md', 'LICENSE.txt',
        '.gitignore', '.env.example', 'tsconfig.json', 'webpack.config.js',
        'src/index.js', 'src/main.py', 'src/app.py', 'main.go', 'index.html'
      ];

      const fetchedFiles: RepositoryFile[] = [];

      for (const fileName of commonFiles) {
        try {
          const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${fileName}`);
          if (response.ok) {
            const data = await response.json();
            if (data.type === 'file' && data.content) {
              const content = atob(data.content);
              const language = detectLanguage(fileName);
              
              fetchedFiles.push({
                name: fileName,
                content: content.slice(0, 50000), // Limit for performance
                language,
                size: data.size,
                path: fileName,
                type: 'file'
              });
            }
          }
        } catch (fileError) {
          console.debug(`Could not fetch ${fileName}:`, fileError);
        }
      }

      files = fetchedFiles;
      
      // Auto-select README or first file
      const readmeFile = files.find(f => f.name.toLowerCase().startsWith('readme'));
      selectedFile = readmeFile || files[0] || null;

    } catch (error) {
      console.error('Error loading repository files:', error);
    }
  }

  async function loadReadmeContent() {
    const readmeFile = files.find(f => f.name.toLowerCase().startsWith('readme'));
    if (readmeFile) {
      readmeContent = readmeFile.content;
    }
  }

  async function generateAIInsights() {
    if (!repository) return;

    try {
      isAIAnalyzing = true;
      
      // Use AutoAgent to analyze repository
      const response = await fetch('/api/autoagent/analyze-repository', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: repository.repository_metadata.repo_url,
          context: 'Generate practical usage suggestions and integration tips'
        })
      });

      if (response.ok) {
        const analysis = await response.json();
        aiSuggestions = [
          ...(analysis.recommendations || []),
          'Consider this for your current projects',
          'Check compatibility with your tech stack',
          'Review documentation for implementation details'
        ];
      }
    } catch (error) {
      console.error('AI analysis error:', error);
    } finally {
      isAIAnalyzing = false;
    }
  }

  function detectLanguage(filename: string): string {
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    const languageMap: Record<string, string> = {
      js: 'javascript', ts: 'typescript', py: 'python', rb: 'ruby',
      php: 'php', java: 'java', go: 'go', rs: 'rust', cpp: 'cpp',
      c: 'c', cs: 'csharp', html: 'html', css: 'css', scss: 'scss',
      json: 'json', yml: 'yaml', yaml: 'yaml', xml: 'xml',
      md: 'markdown', txt: 'plaintext', sh: 'shell', sql: 'sql',
      dockerfile: 'dockerfile'
    };
    
    if (filename.toLowerCase() === 'dockerfile') return 'dockerfile';
    if (filename.toLowerCase() === 'makefile') return 'makefile';
    
    return languageMap[ext] || 'plaintext';
  }

  function selectFile(file: RepositoryFile) {
    selectedFile = file;
    if (activeTab !== 'files') activeTab = 'files';
  }

  function getLanguageColor(language: string): string {
    const colors: Record<string, string> = {
      javascript: '#f7df1e', typescript: '#3178c6', python: '#3776ab',
      java: '#ed8b00', go: '#00add8', rust: '#000000', cpp: '#00599c',
      csharp: '#239120', php: '#777bb4', ruby: '#cc342d'
    };
    return colors[language?.toLowerCase()] || '#64748b';
  }

  function formatNumber(num: number): string {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
  }

  function openInGitHub() {
    if (repository) {
      window.open(repository.repository_metadata.repo_url, '_blank');
    }
  }

  function goBack() {
    goto('/code-cortex/open-source');
  }

  // Render markdown content
  function renderMarkdown(content: string): string {
    // Simple markdown rendering for README
    return content
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }
</script>

<svelte:head>
  <title>{repository?.repository_metadata?.repo_name || 'Repository'} - PRSNL</title>
</svelte:head>

<div class="repository-page">
  {#if loading}
    <div class="loading-screen">
      <Icon name="loader" size="48" class="animate-spin" />
      <h2>Loading Repository...</h2>
      <p>Analyzing code structure and generating insights</p>
    </div>
  {:else if error}
    <div class="error-screen">
      <Icon name="alert-circle" size="48" />
      <h2>Repository Not Found</h2>
      <p>{error}</p>
      <button class="back-button" on:click={goBack}>
        <Icon name="arrow-left" size="16" />
        Back to Open Source
      </button>
    </div>
  {:else if repository}
    <!-- Header Section -->
    <div class="repository-header">
      <div class="header-navigation">
        <button class="back-button" on:click={goBack}>
          <Icon name="arrow-left" size="16" />
          Open Source
        </button>
        
        <div class="breadcrumb">
          <Icon name="github" size="16" />
          <span>{repository.repository_metadata.owner}</span>
          <Icon name="chevron-right" size="14" />
          <span>{repository.repository_metadata.repo_name}</span>
        </div>
      </div>

      <div class="repository-info">
        <div class="repo-title-section">
          <h1>{repository.repository_metadata.repo_name}</h1>
          <div class="repo-stats">
            <div class="stat">
              <Icon name="star" size="16" />
              <span>{formatNumber(repository.repository_metadata.stars)}</span>
            </div>
            {#if repository.repository_metadata.forks}
              <div class="stat">
                <Icon name="git-fork" size="16" />
                <span>{formatNumber(repository.repository_metadata.forks)}</span>
              </div>
            {/if}
            <div class="stat language-stat" style="color: {getLanguageColor(repository.repository_metadata.language)}">
              <div class="language-dot" style="background: {getLanguageColor(repository.repository_metadata.language)}"></div>
              <span>{repository.repository_metadata.language}</span>
            </div>
          </div>
        </div>

        <div class="repo-actions">
          <button class="action-button primary" on:click={openInGitHub}>
            <Icon name="external-link" size="16" />
            View on GitHub
          </button>
          <button class="action-button" on:click={() => copyToClipboard(repository.repository_metadata.repo_url)}>
            <Icon name="copy" size="16" />
            Copy URL
          </button>
          <button class="action-button" on:click={() => activeTab = 'ai-analysis'}>
            <Icon name="zap" size="16" />
            AI Analysis
          </button>
        </div>
      </div>

      <div class="repository-description">
        <p>{repository.repository_metadata.description}</p>
        <div class="metadata-tags">
          {#each repository.repository_metadata.tech_stack.slice(0, 5) as tech}
            <span class="tech-tag">{tech}</span>
          {/each}
          <span class="difficulty-tag difficulty-{repository.repository_metadata.difficulty}">
            {repository.repository_metadata.difficulty}
          </span>
          <span class="category-tag">{repository.repository_metadata.category}</span>
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tab-navigation">
      <button 
        class="tab-button" 
        class:active={activeTab === 'overview'}
        on:click={() => activeTab = 'overview'}
      >
        <Icon name="home" size="16" />
        Overview
      </button>
      
      <button 
        class="tab-button" 
        class:active={activeTab === 'readme'}
        on:click={() => activeTab = 'readme'}
      >
        <Icon name="book-open" size="16" />
        README
      </button>
      
      <button 
        class="tab-button" 
        class:active={activeTab === 'files'}
        on:click={() => activeTab = 'files'}
      >
        <Icon name="folder" size="16" />
        Files ({files.length})
      </button>
      
      <button 
        class="tab-button" 
        class:active={activeTab === 'ai-analysis'}
        on:click={() => activeTab = 'ai-analysis'}
      >
        <Icon name="brain" size="16" />
        AI Analysis
        {#if isAIAnalyzing}
          <Icon name="loader" size="12" class="animate-spin" />
        {/if}
      </button>

      <div class="tab-controls">
        <button 
          class="control-button"
          class:active={!sidebarCollapsed}
          on:click={() => sidebarCollapsed = !sidebarCollapsed}
          title="Toggle Sidebar"
        >
          <Icon name="sidebar" size="16" />
        </button>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="content-area" class:sidebar-collapsed={sidebarCollapsed}>
      <!-- Sidebar -->
      {#if !sidebarCollapsed}
        <div class="sidebar">
          {#if activeTab === 'overview'}
            <div class="overview-sidebar">
              <div class="quick-stats">
                <h3>Repository Statistics</h3>
                <div class="stat-grid">
                  <div class="stat-item">
                    <Icon name="star" size="16" />
                    <span>{formatNumber(repository.repository_metadata.stars)} stars</span>
                  </div>
                  <div class="stat-item">
                    <Icon name="code" size="16" />
                    <span>{repository.repository_metadata.language}</span>
                  </div>
                  <div class="stat-item">
                    <Icon name="shield" size="16" />
                    <span>{repository.repository_metadata.license || 'No License'}</span>
                  </div>
                  <div class="stat-item">
                    <Icon name="calendar" size="16" />
                    <span>Added {new Date(repository.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <div class="tech-stack-detail">
                <h3>Technology Stack</h3>
                <div class="tech-list">
                  {#each repository.repository_metadata.tech_stack as tech}
                    <div class="tech-item">{tech}</div>
                  {/each}
                </div>
              </div>

              {#if repository.repository_metadata.topics?.length}
                <div class="topics-section">
                  <h3>Topics</h3>
                  <div class="topics-list">
                    {#each repository.repository_metadata.topics as topic}
                      <span class="topic-tag">{topic}</span>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          {:else if activeTab === 'files'}
            <div class="files-sidebar">
              <div class="file-search">
                <Icon name="search" size="16" />
                <input 
                  type="text" 
                  placeholder="Search files..." 
                  bind:value={searchQuery}
                />
              </div>
              
              <div class="file-tree">
                {#each files.filter(f => f.name.toLowerCase().includes(searchQuery.toLowerCase())) as file}
                  <button 
                    class="file-item"
                    class:selected={selectedFile?.name === file.name}
                    on:click={() => selectFile(file)}
                  >
                    <Icon name={file.name.includes('.') ? 'file' : 'folder'} size="16" />
                    <span class="file-name">{file.name}</span>
                    <span class="file-size">{(file.size / 1024).toFixed(1)}KB</span>
                  </button>
                {/each}
              </div>
            </div>
          {:else if activeTab === 'ai-analysis'}
            <div class="ai-sidebar">
              <div class="ai-confidence">
                <h3>AI Analysis Confidence</h3>
                <div class="confidence-meter">
                  <div 
                    class="confidence-fill" 
                    style="width: {repository.repository_metadata.ai_analysis.confidence * 100}%"
                  ></div>
                  <span>{Math.round(repository.repository_metadata.ai_analysis.confidence * 100)}%</span>
                </div>
              </div>

              <div class="ai-insights">
                <h3>Key Features</h3>
                <ul class="feature-list">
                  {#each repository.repository_metadata.ai_analysis.key_features as feature}
                    <li>{feature}</li>
                  {/each}
                </ul>
              </div>

              {#if aiSuggestions.length > 0}
                <div class="ai-suggestions">
                  <h3>AI Suggestions</h3>
                  <ul class="suggestion-list">
                    {#each aiSuggestions as suggestion}
                      <li>{suggestion}</li>
                    {/each}
                  </ul>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/if}

      <!-- Main Content Panel -->
      <div class="main-panel">
        {#if activeTab === 'overview'}
          <div class="overview-content">
            <div class="overview-grid">
              <div class="overview-card">
                <h3>Purpose & Description</h3>
                <p>{repository.repository_metadata.ai_analysis.purpose}</p>
              </div>

              <div class="overview-card">
                <h3>Key Highlights</h3>
                <ul>
                  {#each repository.repository_metadata.ai_analysis.key_features as feature}
                    <li>{feature}</li>
                  {/each}
                </ul>
              </div>

              <div class="overview-card">
                <h3>Learning Information</h3>
                <div class="learning-info">
                  <div class="info-item">
                    <strong>Difficulty:</strong> 
                    <span class="difficulty-{repository.repository_metadata.difficulty}">
                      {repository.repository_metadata.difficulty}
                    </span>
                  </div>
                  {#if repository.repository_metadata.ai_analysis.learning_curve}
                    <div class="info-item">
                      <strong>Learning Curve:</strong> {repository.repository_metadata.ai_analysis.learning_curve}
                    </div>
                  {/if}
                  {#if repository.repository_metadata.ai_analysis.community_size}
                    <div class="info-item">
                      <strong>Community:</strong> {repository.repository_metadata.ai_analysis.community_size}
                    </div>
                  {/if}
                </div>
              </div>

              <div class="overview-card">
                <h3>Quick Actions</h3>
                <div class="quick-actions">
                  <button class="quick-action" on:click={() => activeTab = 'readme'}>
                    <Icon name="book-open" size="20" />
                    Read Documentation
                  </button>
                  <button class="quick-action" on:click={() => activeTab = 'files'}>
                    <Icon name="code" size="20" />
                    Browse Code
                  </button>
                  <button class="quick-action" on:click={openInGitHub}>
                    <Icon name="external-link" size="20" />
                    Clone Repository
                  </button>
                </div>
              </div>
            </div>
          </div>

        {:else if activeTab === 'readme'}
          <div class="readme-content">
            {#if readmeContent}
              <div class="readme-header">
                <h2>README</h2>
                <button class="copy-button" on:click={() => copyToClipboard(readmeContent)}>
                  <Icon name="copy" size="16" />
                  Copy
                </button>
              </div>
              <div class="markdown-content">
                {@html renderMarkdown(readmeContent)}
              </div>
            {:else}
              <div class="no-readme">
                <Icon name="file-text" size="48" />
                <h3>No README Found</h3>
                <p>This repository doesn't have a README file.</p>
              </div>
            {/if}
          </div>

        {:else if activeTab === 'files'}
          <div class="code-editor-section">
            {#if selectedFile}
              <div class="editor-header">
                <div class="file-info">
                  <Icon name="file" size="16" />
                  <span class="file-path">{selectedFile.name}</span>
                  <span class="language-badge">{selectedFile.language}</span>
                </div>
                <div class="editor-actions">
                  <button class="action-btn" on:click={() => copyToClipboard(selectedFile?.content || '')}>
                    <Icon name="copy" size="14" />
                    Copy
                  </button>
                  <button class="action-btn" on:click={openInGitHub}>
                    <Icon name="external-link" size="14" />
                    GitHub
                  </button>
                </div>
              </div>
              
              <MonacoEditor
                value={selectedFile.content}
                language={selectedFile.language}
                theme="vs-dark"
                readOnly={true}
                height="calc(100vh - 400px)"
                minimap={true}
              />
            {:else}
              <div class="no-file-selected">
                <Icon name="folder-open" size="48" />
                <h3>Select a File</h3>
                <p>Choose a file from the sidebar to view its contents</p>
              </div>
            {/if}
          </div>

        {:else if activeTab === 'ai-analysis'}
          <div class="ai-analysis-content">
            <div class="analysis-grid">
              <div class="analysis-card">
                <h3>Repository Purpose</h3>
                <p>{repository.repository_metadata.ai_analysis.purpose}</p>
              </div>

              <div class="analysis-card">
                <h3>Technical Assessment</h3>
                <div class="assessment-grid">
                  <div class="assessment-item">
                    <span class="label">Primary Language:</span>
                    <span class="value">{repository.repository_metadata.language}</span>
                  </div>
                  <div class="assessment-item">
                    <span class="label">Category:</span>
                    <span class="value">{repository.repository_metadata.category}</span>
                  </div>
                  <div class="assessment-item">
                    <span class="label">Difficulty:</span>
                    <span class="value difficulty-{repository.repository_metadata.difficulty}">
                      {repository.repository_metadata.difficulty}
                    </span>
                  </div>
                  <div class="assessment-item">
                    <span class="label">Community Stars:</span>
                    <span class="value">{formatNumber(repository.repository_metadata.stars)}</span>
                  </div>
                </div>
              </div>

              <div class="analysis-card">
                <h3>Integration Recommendations</h3>
                {#if aiSuggestions.length > 0}
                  <ul class="recommendation-list">
                    {#each aiSuggestions as suggestion}
                      <li>
                        <Icon name="lightbulb" size="16" />
                        {suggestion}
                      </li>
                    {/each}
                  </ul>
                {:else}
                  <p>Generating personalized recommendations...</p>
                {/if}
              </div>

              <div class="analysis-card">
                <h3>Learning Path</h3>
                <div class="learning-steps">
                  <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-content">
                      <h4>Read Documentation</h4>
                      <p>Start with the README and official docs</p>
                    </div>
                  </div>
                  <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-content">
                      <h4>Explore Examples</h4>
                      <p>Look for example files and demo projects</p>
                    </div>
                  </div>
                  <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-content">
                      <h4>Hands-on Practice</h4>
                      <p>Clone and experiment with the codebase</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .repository-page {
    min-height: 100vh;
    background: #0a0a0a;
    color: #e0e0e0;
  }

  /* Loading & Error States */
  .loading-screen, .error-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    text-align: center;
    gap: 1rem;
  }

  .loading-screen h2, .error-screen h2 {
    color: #00ff88;
    margin: 0;
  }

  .loading-screen p, .error-screen p {
    color: #888;
    margin: 0;
  }

  /* Header Section */
  .repository-header {
    padding: 2rem;
    border-bottom: 1px solid #2a2a2a;
    background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 100%);
  }

  .header-navigation {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .back-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: transparent;
    border: 1px solid #333;
    color: #00ff88;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    font-size: 0.875rem;
  }

  .back-button:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: #00ff88;
  }

  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #888;
    font-size: 0.875rem;
  }

  .repository-info {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
  }

  .repo-title-section h1 {
    font-size: 2.5rem;
    margin: 0 0 1rem 0;
    color: #e0e0e0;
    font-weight: 700;
  }

  .repo-stats {
    display: flex;
    gap: 1.5rem;
    align-items: center;
  }

  .stat {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #888;
    font-size: 0.875rem;
  }

  .language-stat {
    font-weight: 500;
  }

  .language-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .repo-actions {
    display: flex;
    gap: 0.75rem;
  }

  .action-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    border: 1px solid #333;
    background: transparent;
    color: #e0e0e0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .action-button.primary {
    background: #00ff88;
    color: #000;
    border-color: #00ff88;
  }

  .action-button:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #555;
  }

  .action-button.primary:hover {
    background: #00e67a;
  }

  .repository-description p {
    font-size: 1.1rem;
    color: #ccc;
    margin: 0 0 1rem 0;
    line-height: 1.6;
  }

  .metadata-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tech-tag, .difficulty-tag, .category-tag {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .tech-tag {
    background: rgba(100, 116, 139, 0.2);
    color: #cbd5e1;
    border: 1px solid rgba(100, 116, 139, 0.3);
  }

  .category-tag {
    background: rgba(0, 255, 136, 0.1);
    color: #00ff88;
    border: 1px solid rgba(0, 255, 136, 0.3);
  }

  .difficulty-tag {
    border: 1px solid;
  }

  .difficulty-beginner { background: rgba(34, 197, 94, 0.2); color: #22c55e; border-color: rgba(34, 197, 94, 0.3); }
  .difficulty-intermediate { background: rgba(251, 191, 36, 0.2); color: #fbbf24; border-color: rgba(251, 191, 36, 0.3); }
  .difficulty-advanced { background: rgba(239, 68, 68, 0.2); color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }

  /* Tab Navigation */
  .tab-navigation {
    display: flex;
    align-items: center;
    padding: 0 2rem;
    background: #1a1a1a;
    border-bottom: 1px solid #2a2a2a;
    gap: 0.5rem;
  }

  .tab-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 1.5rem;
    background: transparent;
    border: none;
    color: #888;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
    font-weight: 500;
    border-bottom: 2px solid transparent;
  }

  .tab-button:hover {
    color: #e0e0e0;
  }

  .tab-button.active {
    color: #00ff88;
    border-bottom-color: #00ff88;
  }

  .tab-controls {
    margin-left: auto;
    display: flex;
    gap: 0.5rem;
  }

  .control-button {
    padding: 0.5rem;
    background: transparent;
    border: 1px solid #333;
    color: #888;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .control-button:hover, .control-button.active {
    color: #00ff88;
    border-color: #00ff88;
  }

  /* Content Area */
  .content-area {
    display: flex;
    height: calc(100vh - 200px);
  }

  .content-area.sidebar-collapsed .main-panel {
    width: 100%;
  }

  /* Sidebar */
  .sidebar {
    width: 320px;
    background: #1a1a1a;
    border-right: 1px solid #2a2a2a;
    overflow-y: auto;
    padding: 1.5rem;
  }

  .sidebar h3 {
    color: #00ff88;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0 0 1rem 0;
  }

  /* Overview Sidebar */
  .quick-stats {
    margin-bottom: 2rem;
  }

  .stat-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #ccc;
    font-size: 0.875rem;
  }

  .tech-stack-detail {
    margin-bottom: 2rem;
  }

  .tech-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .tech-item {
    padding: 0.5rem;
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 6px;
    font-size: 0.875rem;
  }

  .topics-section {
    margin-bottom: 2rem;
  }

  .topics-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .topic-tag {
    padding: 0.25rem 0.5rem;
    background: rgba(100, 116, 139, 0.1);
    color: #94a3b8;
    border-radius: 12px;
    font-size: 0.75rem;
  }

  /* Files Sidebar */
  .file-search {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid #333;
    border-radius: 6px;
    padding: 0.5rem;
    margin-bottom: 1rem;
  }

  .file-search input {
    flex: 1;
    background: transparent;
    border: none;
    color: #e0e0e0;
    outline: none;
    font-size: 0.875rem;
  }

  .file-tree {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: transparent;
    border: none;
    color: #ccc;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s ease;
    text-align: left;
    width: 100%;
    font-size: 0.875rem;
  }

  .file-item:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  .file-item.selected {
    background: rgba(0, 255, 136, 0.1);
    color: #00ff88;
  }

  .file-name {
    flex: 1;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
  }

  .file-size {
    font-size: 0.75rem;
    color: #666;
  }

  /* AI Sidebar */
  .ai-confidence {
    margin-bottom: 2rem;
  }

  .confidence-meter {
    position: relative;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    height: 20px;
    overflow: hidden;
  }

  .confidence-fill {
    background: linear-gradient(90deg, #00ff88, #00e67a);
    height: 100%;
    transition: width 0.3s ease;
  }

  .confidence-meter span {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 0.75rem;
    font-weight: 600;
    color: #000;
  }

  .ai-insights, .ai-suggestions {
    margin-bottom: 2rem;
  }

  .feature-list, .suggestion-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .feature-list li, .suggestion-list li {
    padding: 0.5rem 0;
    border-bottom: 1px solid #2a2a2a;
    color: #ccc;
    font-size: 0.875rem;
  }

  .feature-list li:last-child, .suggestion-list li:last-child {
    border-bottom: none;
  }

  /* Main Panel */
  .main-panel {
    flex: 1;
    overflow-y: auto;
    background: #0a0a0a;
  }

  /* Overview Content */
  .overview-content {
    padding: 2rem;
  }

  .overview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .overview-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 1.5rem;
  }

  .overview-card h3 {
    color: #00ff88;
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
  }

  .overview-card p {
    color: #ccc;
    line-height: 1.6;
    margin: 0;
  }

  .overview-card ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .overview-card li {
    padding: 0.5rem 0;
    color: #ccc;
    border-bottom: 1px solid #2a2a2a;
  }

  .overview-card li:last-child {
    border-bottom: none;
  }

  .learning-info {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .quick-action {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.2);
    color: #e0e0e0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
  }

  .quick-action:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: #00ff88;
  }

  /* README Content */
  .readme-content {
    padding: 2rem;
  }

  .readme-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #2a2a2a;
  }

  .readme-header h2 {
    color: #00ff88;
    margin: 0;
  }

  .copy-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: transparent;
    border: 1px solid #333;
    color: #888;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .copy-button:hover {
    color: #e0e0e0;
    border-color: #555;
  }

  .markdown-content {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 2rem;
    line-height: 1.8;
    color: #e0e0e0;
  }

  .markdown-content :global(h1) { color: #00ff88; margin-top: 0; }
  .markdown-content :global(h2) { color: #00ff88; margin-top: 2rem; }
  .markdown-content :global(h3) { color: #00ff88; margin-top: 1.5rem; }
  .markdown-content :global(code) { 
    background: rgba(0, 255, 136, 0.1); 
    color: #00ff88; 
    padding: 0.125rem 0.25rem; 
    border-radius: 4px; 
    font-family: 'Monaco', monospace;
  }

  .no-readme, .no-file-selected {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 400px;
    text-align: center;
    color: #666;
  }

  .no-readme h3, .no-file-selected h3 {
    color: #888;
    margin: 1rem 0 0.5rem 0;
  }

  /* Code Editor Section */
  .code-editor-section {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: #1a1a1a;
    border-bottom: 1px solid #2a2a2a;
  }

  .file-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #e0e0e0;
  }

  .file-path {
    font-family: 'Monaco', monospace;
    font-size: 0.875rem;
  }

  .language-badge {
    padding: 0.25rem 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    color: #00ff88;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .editor-actions {
    display: flex;
    gap: 0.5rem;
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.5rem;
    background: transparent;
    border: 1px solid #333;
    color: #888;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.75rem;
  }

  .action-btn:hover {
    color: #e0e0e0;
    border-color: #555;
  }

  /* AI Analysis Content */
  .ai-analysis-content {
    padding: 2rem;
  }

  .analysis-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .analysis-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 1.5rem;
  }

  .analysis-card h3 {
    color: #00ff88;
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
  }

  .assessment-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .assessment-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #2a2a2a;
  }

  .assessment-item:last-child {
    border-bottom: none;
  }

  .assessment-item .label {
    color: #888;
    font-size: 0.875rem;
  }

  .assessment-item .value {
    color: #e0e0e0;
    font-weight: 500;
  }

  .recommendation-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .recommendation-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.75rem 0;
    color: #ccc;
    border-bottom: 1px solid #2a2a2a;
  }

  .recommendation-list li:last-child {
    border-bottom: none;
  }

  .learning-steps {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .step {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
  }

  .step-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: #00ff88;
    color: #000;
    border-radius: 50%;
    font-weight: 600;
    font-size: 0.875rem;
    flex-shrink: 0;
  }

  .step-content h4 {
    color: #e0e0e0;
    margin: 0 0 0.25rem 0;
    font-size: 0.875rem;
  }

  .step-content p {
    color: #888;
    margin: 0;
    font-size: 0.875rem;
  }

  /* Responsive Design */
  @media (max-width: 1024px) {
    .content-area {
      flex-direction: column;
      height: auto;
    }
    
    .sidebar {
      width: 100%;
      max-height: 300px;
    }
    
    .overview-grid, .analysis-grid {
      grid-template-columns: 1fr;
    }
    
    .repository-info {
      flex-direction: column;
      gap: 1rem;
    }
    
    .repo-actions {
      justify-content: flex-start;
    }
  }

  @media (max-width: 768px) {
    .repository-header {
      padding: 1rem;
    }
    
    .repo-title-section h1 {
      font-size: 1.8rem;
    }
    
    .repo-stats {
      flex-wrap: wrap;
      gap: 1rem;
    }
    
    .tab-navigation {
      padding: 0 1rem;
      overflow-x: auto;
    }
    
    .overview-content, .readme-content, .ai-analysis-content {
      padding: 1rem;
    }
  }

  /* Animation */
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>