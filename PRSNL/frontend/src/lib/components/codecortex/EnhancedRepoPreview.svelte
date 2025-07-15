<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import type { RepoFile } from '$lib/types';
  
  interface Props {
    repoId: string;
    repoName: string;
    repoUrl?: string;
    onFileSelect?: (file: RepoFile) => void;
    onAnalyze?: () => void;
  }
  
  let { repoId, repoName, repoUrl, onFileSelect, onAnalyze }: Props = $props();
  
  // State
  let loading = $state(true);
  let fileTree = $state([]);
  let selectedFile = $state(null);
  let expandedFolders = $state(new Set());
  let searchQuery = $state('');
  let showSearch = $state(false);
  let repoStats = $state({
    stars: 0,
    forks: 0,
    language: 'Unknown',
    size: 0,
    lastUpdated: null
  });
  
  // File type icons mapping
  const fileIcons = {
    js: '📜',
    ts: '📘',
    jsx: '⚛️',
    tsx: '⚛️',
    py: '🐍',
    java: '☕',
    cpp: '🔧',
    c: '🔨',
    go: '🐹',
    rs: '🦀',
    md: '📝',
    json: '📋',
    yml: '⚙️',
    yaml: '⚙️',
    html: '🌐',
    css: '🎨',
    scss: '🎨',
    svg: '🖼️',
    png: '🖼️',
    jpg: '🖼️',
    gif: '🖼️',
    pdf: '📄',
    txt: '📃',
    sh: '💻',
    docker: '🐳',
    git: '🔧'
  };
  
  const folderIcon = '📁';
  const folderOpenIcon = '📂';
  
  onMount(async () => {
    await loadRepoData();
  });
  
  async function loadRepoData() {
    loading = true;
    try {
      // Load repository stats
      const stats = await api.get(`/github/repos/${repoId}/stats`);
      if (stats) {
        repoStats = stats;
      }
      
      // Load file tree
      const files = await api.get(`/github/repos/${repoId}/tree`);
      fileTree = buildFileTree(files || []);
    } catch (error) {
      console.error('Failed to load repo data:', error);
    } finally {
      loading = false;
    }
  }
  
  function buildFileTree(files) {
    const tree = {};
    
    files.forEach(file => {
      const parts = file.path.split('/');
      let current = tree;
      
      parts.forEach((part, index) => {
        if (index === parts.length - 1) {
          // It's a file
          current[part] = {
            type: 'file',
            name: part,
            path: file.path,
            size: file.size,
            extension: part.split('.').pop()
          };
        } else {
          // It's a folder
          if (!current[part]) {
            current[part] = {
              type: 'folder',
              name: part,
              children: {}
            };
          }
          current = current[part].children;
        }
      });
    });
    
    return treeToArray(tree);
  }
  
  function treeToArray(tree, path = '') {
    return Object.keys(tree).map(key => {
      const item = tree[key];
      if (item.type === 'folder') {
        return {
          ...item,
          path: path ? `${path}/${key}` : key,
          children: treeToArray(item.children, path ? `${path}/${key}` : key)
        };
      }
      return item;
    }).sort((a, b) => {
      // Folders first, then files
      if (a.type !== b.type) return a.type === 'folder' ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
  }
  
  function toggleFolder(path: string) {
    if (expandedFolders.has(path)) {
      expandedFolders.delete(path);
    } else {
      expandedFolders.add(path);
    }
    expandedFolders = new Set(expandedFolders);
  }
  
  function selectFile(file) {
    selectedFile = file;
    if (onFileSelect) {
      onFileSelect(file);
    }
  }
  
  function getFileIcon(extension: string) {
    return fileIcons[extension] || '📄';
  }
  
  function formatSize(bytes: number) {
    if (!bytes) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }
  
  function formatDate(date: string) {
    if (!date) return 'Unknown';
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }
  
  function filterTree(items, query) {
    if (!query) return items;
    
    return items.reduce((acc, item) => {
      if (item.type === 'file' && item.name.toLowerCase().includes(query.toLowerCase())) {
        acc.push(item);
      } else if (item.type === 'folder') {
        const filteredChildren = filterTree(item.children, query);
        if (filteredChildren.length > 0) {
          acc.push({
            ...item,
            children: filteredChildren
          });
        }
      }
      return acc;
    }, []);
  }
  
  let filteredTree = $derived(filterTree(fileTree, searchQuery));
</script>

<div class="repo-preview">
  <!-- Repository Header -->
  <div class="repo-header">
    <div class="repo-title">
      <span class="repo-icon">📚</span>
      <h2>{repoName}</h2>
      {#if repoUrl}
        <a href={repoUrl} target="_blank" class="github-link" title="View on GitHub">
          <svg viewBox="0 0 16 16" width="20" height="20">
            <path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
        </a>
      {/if}
    </div>
    
    <div class="repo-actions">
      <button class="search-btn" onclick={() => showSearch = !showSearch} title="Search files">
        🔍
      </button>
      {#if onAnalyze}
        <button class="analyze-btn" onclick={onAnalyze}>
          🚀 Analyze Repository
        </button>
      {/if}
    </div>
  </div>
  
  <!-- Repository Stats -->
  <div class="repo-stats">
    <div class="stat">
      <span class="stat-icon">⭐</span>
      <span class="stat-value">{repoStats.stars || 0}</span>
      <span class="stat-label">Stars</span>
    </div>
    <div class="stat">
      <span class="stat-icon">🔱</span>
      <span class="stat-value">{repoStats.forks || 0}</span>
      <span class="stat-label">Forks</span>
    </div>
    <div class="stat">
      <span class="stat-icon">💻</span>
      <span class="stat-value">{repoStats.language}</span>
      <span class="stat-label">Language</span>
    </div>
    <div class="stat">
      <span class="stat-icon">💾</span>
      <span class="stat-value">{formatSize(repoStats.size * 1024)}</span>
      <span class="stat-label">Size</span>
    </div>
    <div class="stat">
      <span class="stat-icon">📅</span>
      <span class="stat-value">{formatDate(repoStats.lastUpdated)}</span>
      <span class="stat-label">Updated</span>
    </div>
  </div>
  
  <!-- Search Bar -->
  {#if showSearch}
    <div class="search-bar">
      <input
        type="text"
        placeholder="Search files..."
        bind:value={searchQuery}
        class="search-input"
      />
      {#if searchQuery}
        <button class="clear-search" onclick={() => searchQuery = ''}>
          ✕
        </button>
      {/if}
    </div>
  {/if}
  
  <!-- File Explorer -->
  <div class="file-explorer">
    {#if loading}
      <div class="loading-state">
        <div class="spinner"></div>
        <span>Loading repository structure...</span>
      </div>
    {:else if filteredTree.length === 0}
      <div class="empty-state">
        {#if searchQuery}
          <p>No files found matching "{searchQuery}"</p>
        {:else}
          <p>No files found in this repository</p>
        {/if}
      </div>
    {:else}
      <div class="file-tree">
        {#each filteredTree as item}
          <FileTreeItem 
            {item} 
            depth={0} 
            {expandedFolders}
            {selectedFile}
            onToggle={toggleFolder}
            onSelect={selectFile}
            {getFileIcon}
          />
        {/each}
      </div>
    {/if}
  </div>
</div>

<!-- Recursive File Tree Item Component -->
{#snippet FileTreeItem({ item, depth, expandedFolders, selectedFile, onToggle, onSelect, getFileIcon })}
  <div class="tree-item" style="padding-left: {depth * 20}px">
    {#if item.type === 'folder'}
      <button 
        class="folder-item"
        onclick={() => onToggle(item.path)}
      >
        <span class="folder-icon">
          {expandedFolders.has(item.path) ? folderOpenIcon : folderIcon}
        </span>
        <span class="item-name">{item.name}</span>
        <span class="item-count">{item.children?.length || 0}</span>
      </button>
      
      {#if expandedFolders.has(item.path)}
        <div class="folder-children">
          {#each item.children as child}
            <FileTreeItem 
              item={child} 
              depth={depth + 1} 
              {expandedFolders}
              {selectedFile}
              {onToggle}
              {onSelect}
              {getFileIcon}
            />
          {/each}
        </div>
      {/if}
    {:else}
      <button 
        class="file-item {selectedFile?.path === item.path ? 'selected' : ''}"
        onclick={() => onSelect(item)}
      >
        <span class="file-icon">{getFileIcon(item.extension)}</span>
        <span class="item-name">{item.name}</span>
      </button>
    {/if}
  </div>
{/snippet}

<style>
  .repo-preview {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  /* Header */
  .repo-header {
    padding: 1.5rem;
    background: var(--surface-3);
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .repo-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .repo-icon {
    font-size: 1.5rem;
  }
  
  .repo-title h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  .github-link {
    color: var(--text-secondary);
    transition: color 0.2s;
    display: flex;
    align-items: center;
  }
  
  .github-link:hover {
    color: var(--text-primary);
  }
  
  .repo-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .search-btn {
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 1rem;
  }
  
  .search-btn:hover {
    background: var(--surface-4);
    border-color: var(--primary);
  }
  
  .analyze-btn {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .analyze-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  }
  
  /* Stats */
  .repo-stats {
    display: flex;
    padding: 1rem 1.5rem;
    background: var(--surface-3);
    border-bottom: 1px solid var(--border);
    gap: 2rem;
    overflow-x: auto;
  }
  
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    min-width: 80px;
  }
  
  .stat-icon {
    font-size: 1.25rem;
  }
  
  .stat-value {
    font-weight: 600;
    color: var(--text-primary);
  }
  
  .stat-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }
  
  /* Search Bar */
  .search-bar {
    padding: 1rem 1.5rem;
    background: var(--surface-3);
    border-bottom: 1px solid var(--border);
    position: relative;
  }
  
  .search-input {
    width: 100%;
    padding: 0.5rem 1rem;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 0.875rem;
  }
  
  .search-input:focus {
    outline: none;
    border-color: var(--primary);
  }
  
  .clear-search {
    position: absolute;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    background: transparent;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.25rem;
  }
  
  /* File Explorer */
  .file-explorer {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .loading-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem;
    color: var(--text-secondary);
    gap: 1rem;
  }
  
  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  /* File Tree */
  .file-tree {
    font-size: 0.875rem;
  }
  
  .tree-item {
    user-select: none;
  }
  
  .folder-item,
  .file-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.375rem 0.5rem;
    background: transparent;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    text-align: left;
    border-radius: 4px;
    transition: all 0.1s;
  }
  
  .folder-item:hover,
  .file-item:hover {
    background: var(--surface-3);
    color: var(--text-primary);
  }
  
  .file-item.selected {
    background: var(--primary-alpha);
    color: var(--primary);
  }
  
  .folder-icon,
  .file-icon {
    font-size: 1rem;
    flex-shrink: 0;
  }
  
  .item-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .item-count {
    font-size: 0.75rem;
    color: var(--text-secondary);
    background: var(--surface-4);
    padding: 0.125rem 0.375rem;
    border-radius: 10px;
  }
  
  .folder-children {
    margin-top: 2px;
  }
  
  /* Custom properties fallback */
  :global(:root) {
    --surface-2: #1a1a2e;
    --surface-3: #16213e;
    --surface-4: #0f3460;
    --border: rgba(255, 255, 255, 0.1);
    --text-primary: rgba(255, 255, 255, 0.9);
    --text-secondary: rgba(255, 255, 255, 0.6);
    --primary: #3b82f6;
    --primary-alpha: rgba(59, 130, 246, 0.1);
  }
</style>