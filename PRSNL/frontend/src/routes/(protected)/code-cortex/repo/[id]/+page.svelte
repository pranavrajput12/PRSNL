<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import MonacoEditor from '$lib/components/MonacoEditor.svelte';

  interface Repository {
    id: string;
    name: string;
    full_name: string;
    description: string;
    language: string;
    stars: number;
    forks: number;
    is_private: boolean;
    default_branch: string;
    last_synced: string;
    slug: string;
    html_url: string;
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

      // Fetch repository details using the GitHub API
      const response = await fetch(`/api/github/repos/by-slug/${repositoryId}`, {
        headers: {
          'X-PRSNL-Integration': 'frontend',
        },
      });

      if (!response.ok) {
        throw new Error('Repository not found');
      }

      repository = await response.json();

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
      const [owner, repo] = repository.full_name.split('/');

      // Common files to fetch
      const commonFiles = [
        'README.md',
        'README.rst',
        'README.txt',
        'package.json',
        'requirements.txt',
        'Cargo.toml',
        'composer.json',
        'pom.xml',
        'go.mod',
        'Dockerfile',
        'docker-compose.yml',
        'LICENSE',
        'LICENSE.md',
        'LICENSE.txt',
        '.gitignore',
        '.env.example',
        'tsconfig.json',
        'webpack.config.js',
        'src/index.js',
        'src/main.py',
        'src/app.py',
        'main.go',
        'index.html',
      ];

      const fetchedFiles: RepositoryFile[] = [];

      for (const fileName of commonFiles) {
        try {
          const response = await fetch(
            `https://api.github.com/repos/${owner}/${repo}/contents/${fileName}`
          );
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
                type: 'file',
              });
            }
          }
        } catch (fileError) {
          console.debug(`Could not fetch ${fileName}:`, fileError);
        }
      }

      files = fetchedFiles;

      // Auto-select README or first file
      const readmeFile = files.find((f) => f.name.toLowerCase().startsWith('readme'));
      selectedFile = readmeFile || files[0] || null;
    } catch (error) {
      console.error('Error loading repository files:', error);
    }
  }

  async function loadReadmeContent() {
    const readmeFile = files.find((f) => f.name.toLowerCase().startsWith('readme'));
    if (readmeFile) {
      readmeContent = readmeFile.content;
    }
  }

  async function generateAIInsights() {
    if (!repository) return;

    try {
      isAIAnalyzing = true;

      // Use AI suggest API to analyze repository
      const response = await fetch('/api/ai-suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: `Analyze this repository and provide practical usage suggestions: ${repository.name} - ${repository.description}`,
          context: {
            language: repository.language,
            stars: repository.stars,
            forks: repository.forks,
          },
        }),
      });

      if (response.ok) {
        const data = await response.json();
        aiSuggestions = [
          ...(data.suggestions || []),
          'Consider this for your current projects',
          'Check compatibility with your tech stack',
          'Review documentation for implementation details',
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
      js: 'javascript',
      ts: 'typescript',
      py: 'python',
      rb: 'ruby',
      php: 'php',
      java: 'java',
      go: 'go',
      rs: 'rust',
      cpp: 'cpp',
      c: 'c',
      cs: 'csharp',
      html: 'html',
      css: 'css',
      scss: 'scss',
      json: 'json',
      yml: 'yaml',
      yaml: 'yaml',
      xml: 'xml',
      md: 'markdown',
      txt: 'plaintext',
      sh: 'shell',
      sql: 'sql',
      dockerfile: 'dockerfile',
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
      javascript: '#f7df1e',
      typescript: '#3178c6',
      python: '#3776ab',
      java: '#ed8b00',
      go: '#00add8',
      rust: '#000000',
      cpp: '#00599c',
      csharp: '#239120',
      php: '#777bb4',
      ruby: '#cc342d',
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
      window.open(repository.html_url, '_blank');
    }
  }

  function goBack() {
    goto('/code-cortex/codemirror');
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
  <title>{repository?.name || 'Repository'} - PRSNL</title>
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
        Back to CodeMirror
      </button>
    </div>
  {:else if repository}
    <!-- Header Section -->
    <div class="repository-header">
      <div class="header-navigation">
        <button class="back-button" on:click={goBack}>
          <Icon name="arrow-left" size="16" />
          CodeMirror
        </button>

        <div class="breadcrumb">
          <Icon name="github" size="16" />
          <span>{repository.full_name.split('/')[0]}</span>
          <Icon name="chevron-right" size="14" />
          <span>{repository.name}</span>
        </div>
      </div>

      <div class="repository-info">
        <div class="repo-title-section">
          <h1>{repository.name}</h1>
          <div class="repo-stats">
            <div class="stat">
              <Icon name="star" size="16" />
              <span>{formatNumber(repository.stars)}</span>
            </div>
            <div class="stat">
              <Icon name="git-fork" size="16" />
              <span>{formatNumber(repository.forks)}</span>
            </div>
            <div class="stat language-stat" style="color: {getLanguageColor(repository.language)}">
              <div
                class="language-dot"
                style="background: {getLanguageColor(repository.language)}"
              ></div>
              <span>{repository.language}</span>
            </div>
          </div>
        </div>

        <div class="repo-actions">
          <button class="action-button primary" on:click={openInGitHub}>
            <Icon name="external-link" size="16" />
            View on GitHub
          </button>
          <button class="action-button" on:click={() => copyToClipboard(repository.html_url)}>
            <Icon name="copy" size="16" />
            Copy URL
          </button>
          <button class="action-button" on:click={() => (activeTab = 'ai-analysis')}>
            <Icon name="zap" size="16" />
            AI Analysis
          </button>
        </div>
      </div>

      <div class="repository-description">
        <p>{repository.description}</p>
        <div class="metadata-tags">
          <span class="tech-tag">{repository.language}</span>
          {#if repository.is_private}
            <span class="difficulty-tag difficulty-private">Private</span>
          {:else}
            <span class="difficulty-tag difficulty-public">Public</span>
          {/if}
        </div>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tab-navigation">
      <button
        class="tab-button"
        class:active={activeTab === 'overview'}
        on:click={() => (activeTab = 'overview')}
      >
        <Icon name="home" size="16" />
        Overview
      </button>

      <button
        class="tab-button"
        class:active={activeTab === 'readme'}
        on:click={() => (activeTab = 'readme')}
      >
        <Icon name="book-open" size="16" />
        README
      </button>

      <button
        class="tab-button"
        class:active={activeTab === 'files'}
        on:click={() => (activeTab = 'files')}
      >
        <Icon name="folder" size="16" />
        Files ({files.length})
      </button>

      <button
        class="tab-button"
        class:active={activeTab === 'ai-analysis'}
        on:click={() => (activeTab = 'ai-analysis')}
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
          on:click={() => (sidebarCollapsed = !sidebarCollapsed)}
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
                    <span>{formatNumber(repository.stars)} stars</span>
                  </div>
                  <div class="stat-item">
                    <Icon name="code" size="16" />
                    <span>{repository.language}</span>
                  </div>
                  <div class="stat-item">
                    <Icon name="git-fork" size="16" />
                    <span>{formatNumber(repository.forks)} forks</span>
                  </div>
                  <div class="stat-item">
                    <Icon name="calendar" size="16" />
                    <span>Last synced {new Date(repository.last_synced).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            </div>
          {:else if activeTab === 'files'}
            <div class="files-sidebar">
              <div class="file-search">
                <Icon name="search" size="16" />
                <input type="text" placeholder="Search files..." bind:value={searchQuery} />
              </div>

              <div class="file-tree">
                {#each files.filter((f) => f.name
                    .toLowerCase()
                    .includes(searchQuery.toLowerCase())) as file}
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
                <h3>Repository Information</h3>
                <p>{repository.description}</p>
                <div class="repo-details">
                  <div class="detail-item">
                    <strong>Language:</strong>
                    {repository.language}
                  </div>
                  <div class="detail-item">
                    <strong>Stars:</strong>
                    {formatNumber(repository.stars)}
                  </div>
                  <div class="detail-item">
                    <strong>Forks:</strong>
                    {formatNumber(repository.forks)}
                  </div>
                  <div class="detail-item">
                    <strong>Default Branch:</strong>
                    {repository.default_branch}
                  </div>
                </div>
              </div>

              <div class="overview-card">
                <h3>Quick Actions</h3>
                <div class="quick-actions">
                  <button class="quick-action" on:click={() => (activeTab = 'readme')}>
                    <Icon name="book-open" size="20" />
                    Read Documentation
                  </button>
                  <button class="quick-action" on:click={() => (activeTab = 'files')}>
                    <Icon name="code" size="20" />
                    Browse Code
                  </button>
                  <button class="quick-action" on:click={openInGitHub}>
                    <Icon name="external-link" size="20" />
                    View on GitHub
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
                  <button
                    class="action-btn"
                    on:click={() => copyToClipboard(selectedFile?.content || '')}
                  >
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
                <h3>Repository Analysis</h3>
                <p>AI-powered analysis of {repository.name}</p>
                <div class="assessment-grid">
                  <div class="assessment-item">
                    <span class="label">Primary Language:</span>
                    <span class="value">{repository.language}</span>
                  </div>
                  <div class="assessment-item">
                    <span class="label">Community Stars:</span>
                    <span class="value">{formatNumber(repository.stars)}</span>
                  </div>
                  <div class="assessment-item">
                    <span class="label">Forks:</span>
                    <span class="value">{formatNumber(repository.forks)}</span>
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
  .loading-screen,
  .error-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    text-align: center;
    gap: 1rem;
  }

  .loading-screen h2,
  .error-screen h2 {
    color: #00ff88;
    margin: 0;
  }

  .loading-screen p,
  .error-screen p {
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

  .tech-tag,
  .difficulty-tag {
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

  .difficulty-tag {
    border: 1px solid;
  }

  .difficulty-public {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
    border-color: rgba(34, 197, 94, 0.3);
  }
  .difficulty-private {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border-color: rgba(239, 68, 68, 0.3);
  }

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

  .control-button:hover,
  .control-button.active {
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
  .ai-suggestions {
    margin-bottom: 2rem;
  }

  .suggestion-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .suggestion-list li {
    padding: 0.5rem 0;
    border-bottom: 1px solid #2a2a2a;
    color: #ccc;
    font-size: 0.875rem;
  }

  .suggestion-list li:last-child {
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
    margin: 0 0 1rem 0;
  }

  .repo-details {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #ccc;
    font-size: 0.875rem;
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

  .markdown-content :global(h1) {
    color: #00ff88;
    margin-top: 0;
  }
  .markdown-content :global(h2) {
    color: #00ff88;
    margin-top: 2rem;
  }
  .markdown-content :global(h3) {
    color: #00ff88;
    margin-top: 1.5rem;
  }
  .markdown-content :global(code) {
    background: rgba(0, 255, 136, 0.1);
    color: #00ff88;
    padding: 0.125rem 0.25rem;
    border-radius: 4px;
    font-family: 'Monaco', monospace;
  }

  .no-readme,
  .no-file-selected {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 400px;
    text-align: center;
    color: #666;
  }

  .no-readme h3,
  .no-file-selected h3 {
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

  /* Animation */
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>
