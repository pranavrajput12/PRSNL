<script lang="ts">
  import { onMount } from 'svelte';
  import MonacoEditor from './MonacoEditor.svelte';
  import Icon from './Icon.svelte';

  export let repositoryUrl: string = '';
  export let defaultFile: string = 'README.md';
  export let height: string = '400px';

  interface RepositoryFile {
    name: string;
    content: string;
    language: string;
    size: number;
    type: 'file' | 'directory';
  }

  let files: RepositoryFile[] = [];
  let selectedFile: RepositoryFile | null = null;
  let loading = false;
  let error: string | null = null;
  let monacoEditor: MonacoEditor;

  function detectLanguageFromFilename(filename: string): string {
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    const languageMap: Record<string, string> = {
      js: 'javascript',
      ts: 'typescript',
      py: 'python',
      java: 'java',
      cpp: 'cpp',
      c: 'cpp',
      h: 'cpp',
      cs: 'csharp',
      php: 'php',
      rb: 'ruby',
      go: 'go',
      rs: 'rust',
      swift: 'swift',
      kt: 'kotlin',
      scala: 'scala',
      sh: 'shell',
      bash: 'shell',
      sql: 'sql',
      html: 'html',
      css: 'css',
      scss: 'scss',
      sass: 'scss',
      less: 'less',
      json: 'json',
      xml: 'xml',
      yaml: 'yaml',
      yml: 'yaml',
      toml: 'toml',
      md: 'markdown',
      dockerfile: 'dockerfile',
      txt: 'plaintext',
    };
    return languageMap[ext] || 'plaintext';
  }

  // Common repository files to fetch
  const commonFiles = [
    'README.md',
    'package.json',
    'requirements.txt',
    'Cargo.toml',
    'composer.json',
    'pom.xml',
    'go.mod',
    'Dockerfile',
    'LICENSE',
    '.gitignore',
  ];

  onMount(async () => {
    if (repositoryUrl) {
      await fetchRepositoryFiles();
    }
  });

  async function fetchRepositoryFiles() {
    loading = true;
    error = null;

    try {
      // Extract owner and repo from GitHub URL
      const match = repositoryUrl.match(/github\.com\/([^\/]+)\/([^\/]+)/);
      if (!match) {
        throw new Error('Invalid GitHub repository URL');
      }

      const [, owner, repo] = match;
      const repoName = repo.replace('.git', '');

      // Fetch common files from the repository
      const fetchedFiles: RepositoryFile[] = [];

      for (const fileName of commonFiles) {
        try {
          const response = await fetch(
            `https://api.github.com/repos/${owner}/${repoName}/contents/${fileName}`
          );

          if (response.ok) {
            const data = await response.json();

            if (data.type === 'file' && data.content) {
              // Decode base64 content
              const content = atob(data.content);
              const language = detectLanguageFromFilename(fileName);

              fetchedFiles.push({
                name: fileName,
                content: content.slice(0, 10000), // Limit content size
                language,
                size: data.size,
                type: 'file',
              });
            }
          }
        } catch (fileError) {
          console.warn(`Failed to fetch ${fileName}:`, fileError);
        }
      }

      files = fetchedFiles;

      // Select default file or first available file
      if (files.length > 0) {
        const defaultFileObj = files.find((f) => f.name === defaultFile);
        selectedFile = defaultFileObj || files[0];
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to fetch repository files';
      console.error('Repository fetch error:', err);
    } finally {
      loading = false;
    }
  }

  function selectFile(file: RepositoryFile) {
    selectedFile = file;
  }

  function getFileIcon(fileName: string): string {
    const ext = fileName.split('.').pop()?.toLowerCase() || '';
    const iconMap: Record<string, string> = {
      md: 'file-text',
      json: 'braces',
      js: 'file-code',
      ts: 'file-code',
      py: 'file-code',
      rb: 'file-code',
      php: 'file-code',
      java: 'file-code',
      html: 'file-code',
      css: 'file-code',
      dockerfile: 'package',
      txt: 'file-text',
      license: 'shield',
      gitignore: 'eye-off',
      yml: 'settings',
      yaml: 'settings',
      toml: 'settings',
      xml: 'file-code',
    };

    if (fileName.toLowerCase() === 'readme.md') return 'book-open';
    if (fileName.toLowerCase() === 'dockerfile') return 'package';
    if (fileName.toLowerCase() === 'license') return 'shield';
    if (fileName.toLowerCase() === '.gitignore') return 'eye-off';

    return iconMap[ext] || 'file';
  }

  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  $: repositoryName = repositoryUrl.split('/').slice(-2).join('/').replace('.git', '');
</script>

<div class="repository-code-preview">
  <div class="header">
    <h3 class="title">
      <Icon name="github" size="20" />
      {repositoryName || 'Repository Code Preview'}
    </h3>

    {#if repositoryUrl}
      <button
        class="refresh-btn"
        on:click={fetchRepositoryFiles}
        disabled={loading}
        title="Refresh files"
      >
        <Icon name="refresh-cw" size="16" />
      </button>
    {/if}
  </div>

  {#if loading}
    <div class="loading">
      <Icon name="loader" size="24" class="animate-spin" />
      <span>Fetching repository files...</span>
    </div>
  {:else if error}
    <div class="error">
      <Icon name="alert-circle" size="24" />
      <span>{error}</span>
      <button class="retry-btn" on:click={fetchRepositoryFiles}> Try Again </button>
    </div>
  {:else if files.length === 0}
    <div class="empty">
      <Icon name="folder" size="48" />
      <h4>No files available</h4>
      <p>Enter a repository URL to preview code files</p>
    </div>
  {:else}
    <div class="content">
      <!-- File list sidebar -->
      <div class="file-list">
        <div class="file-list-header">
          <Icon name="folder" size="16" />
          <span>Files ({files.length})</span>
        </div>

        <div class="file-items">
          {#each files as file}
            <button
              class="file-item"
              class:selected={selectedFile?.name === file.name}
              on:click={() => selectFile(file)}
              title={file.name}
            >
              <Icon name={getFileIcon(file.name)} size="16" />
              <span class="file-name">{file.name}</span>
              <span class="file-size">{formatFileSize(file.size)}</span>
            </button>
          {/each}
        </div>
      </div>

      <!-- Code editor -->
      <div class="code-editor">
        {#if selectedFile}
          <div class="editor-header">
            <div class="file-info">
              <Icon name={getFileIcon(selectedFile.name)} size="16" />
              <span class="file-name">{selectedFile.name}</span>
              <span class="language-badge">{selectedFile.language}</span>
            </div>

            <div class="editor-actions">
              <button
                class="action-btn"
                title="Copy content"
                on:click={() => navigator.clipboard.writeText(selectedFile?.content || '')}
              >
                <Icon name="copy" size="14" />
              </button>
            </div>
          </div>

          <MonacoEditor
            bind:this={monacoEditor}
            value={selectedFile.content}
            language={selectedFile.language}
            theme="vs-dark"
            readOnly={true}
            {height}
            minimap={false}
          />
        {:else}
          <div class="no-file-selected">
            <Icon name="file" size="48" />
            <h4>Select a file to preview</h4>
            <p>Choose a file from the list to view its contents</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .repository-code-preview {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    background: var(--color-surface-variant);
    border-bottom: 1px solid var(--color-border);
  }

  .title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--color-on-surface);
  }

  .refresh-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--color-on-surface-variant);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .refresh-btn:hover:not(:disabled) {
    background: var(--color-primary-container);
    color: var(--color-primary);
  }

  .refresh-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .loading,
  .error,
  .empty,
  .no-file-selected {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1.5rem;
    text-align: center;
    gap: 1rem;
    color: var(--color-on-surface-variant);
  }

  .error {
    color: var(--color-error);
  }

  .retry-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--color-primary);
    border-radius: 6px;
    background: transparent;
    color: var(--color-primary);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .retry-btn:hover {
    background: var(--color-primary);
    color: var(--color-on-primary);
  }

  .content {
    display: flex;
    height: 500px;
  }

  .file-list {
    width: 280px;
    border-right: 1px solid var(--color-border);
    background: var(--color-surface-variant);
    display: flex;
    flex-direction: column;
  }

  .file-list-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-on-surface-variant);
    border-bottom: 1px solid var(--color-border);
  }

  .file-items {
    flex: 1;
    overflow-y: auto;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.5rem 1rem;
    border: none;
    background: transparent;
    text-align: left;
    cursor: pointer;
    transition: all 0.2s ease;
    color: var(--color-on-surface);
    font-size: 0.875rem;
  }

  .file-item:hover {
    background: var(--color-primary-container);
  }

  .file-item.selected {
    background: var(--color-primary-container);
    color: var(--color-primary);
    font-weight: 500;
  }

  .file-name {
    flex: 1;
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
  }

  .file-size {
    font-size: 0.75rem;
    color: var(--color-on-surface-variant);
  }

  .code-editor {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .editor-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    background: var(--color-surface-variant);
    border-bottom: 1px solid var(--color-border);
  }

  .file-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: var(--color-on-surface);
  }

  .language-badge {
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    background: var(--color-primary-container);
    color: var(--color-primary);
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
    justify-content: center;
    width: 28px;
    height: 28px;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: var(--color-on-surface-variant);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .action-btn:hover {
    background: var(--color-primary-container);
    color: var(--color-primary);
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .content {
      flex-direction: column;
      height: auto;
    }

    .file-list {
      width: 100%;
      height: 200px;
    }

    .code-editor {
      height: 400px;
    }
  }

  /* Scrollbar styling */
  .file-items::-webkit-scrollbar {
    width: 6px;
  }

  .file-items::-webkit-scrollbar-track {
    background: transparent;
  }

  .file-items::-webkit-scrollbar-thumb {
    background: var(--color-outline);
    border-radius: 3px;
  }

  .file-items::-webkit-scrollbar-thumb:hover {
    background: var(--color-outline-variant);
  }

  /* Animation for loading spinner */
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
