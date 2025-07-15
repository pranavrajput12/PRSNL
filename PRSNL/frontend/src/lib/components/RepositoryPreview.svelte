<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, slide } from 'svelte/transition';
  import MonacoEditor from './MonacoEditor.svelte';
  import MarkdownViewer from './development/MarkdownViewer.svelte';
  import Icon from './Icon.svelte';

  export let repositoryUrl: string = '';
  export let height: string = '600px';
  export let theme: 'dark' | 'light' = 'dark';

  interface FileNode {
    name: string;
    path: string;
    type: 'file' | 'directory';
    children?: FileNode[];
    content?: string;
    language?: string;
    size?: number;
  }

  interface Tab {
    id: string;
    name: string;
    path: string;
    content: string;
    language: string;
    isDirty?: boolean;
  }

  // State
  let files: FileNode[] = [];
  let openTabs: Tab[] = [];
  let activeTabId: string = '';
  let expandedPaths = new Set<string>();
  let loading = false;
  let error: string | null = null;
  let searchQuery = '';
  let sidebarWidth = 280;
  let isResizing = false;
  let showSearch = false;
  let viewMode: 'code' | 'preview' | 'split' = 'code';

  // Computed
  $: filteredFiles = searchQuery ? filterFiles(files, searchQuery) : files;
  $: activeTab = openTabs.find(tab => tab.id === activeTabId);
  $: isMarkdownFile = activeTab?.name.endsWith('.md') || activeTab?.name.endsWith('.markdown');
  $: showPreview = isMarkdownFile && (viewMode === 'preview' || viewMode === 'split');
  $: showCode = viewMode === 'code' || viewMode === 'split';

  // Mock data for demonstration
  const mockFiles: FileNode[] = [
    {
      name: 'src',
      path: 'src',
      type: 'directory',
      children: [
        {
          name: 'components',
          path: 'src/components',
          type: 'directory',
          children: [
            {
              name: 'Button.tsx',
              path: 'src/components/Button.tsx',
              type: 'file',
              language: 'typescript',
              content: `import React from 'react';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  onClick
}) => {
  return (
    <button
      className={\`btn btn-\${variant} btn-\${size}\`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};`
            },
            {
              name: 'Card.tsx',
              path: 'src/components/Card.tsx',
              type: 'file',
              language: 'typescript',
              content: `export const Card = ({ title, children }) => (
  <div className="card">
    <h3>{title}</h3>
    <div>{children}</div>
  </div>
);`
            }
          ]
        },
        {
          name: 'utils',
          path: 'src/utils',
          type: 'directory',
          children: [
            {
              name: 'helpers.ts',
              path: 'src/utils/helpers.ts',
              type: 'file',
              language: 'typescript',
              content: 'export const formatDate = (date: Date) => date.toLocaleDateString();'
            }
          ]
        },
        {
          name: 'App.tsx',
          path: 'src/App.tsx',
          type: 'file',
          language: 'typescript',
          content: `import { Button } from './components/Button';

function App() {
  return (
    <div className="app">
      <h1>My Awesome App</h1>
      <Button onClick={() => alert('Hello!')}>
        Click me
      </Button>
    </div>
  );
}

export default App;`
        }
      ]
    },
    {
      name: 'README.md',
      path: 'README.md',
      type: 'file',
      language: 'markdown',
      content: `# Awesome Project

A modern, clean, and beautiful repository viewer component.

## Features

- 🎨 Clean and modern UI design
- 📁 Hierarchical file tree navigation
- 🔍 Fast file search
- 📝 Syntax highlighting with Monaco Editor
- 📱 Fully responsive design
- ⚡ Lightning fast performance

## Installation

\`\`\`bash
// npm install awesome-repo-viewer
\`\`\`

## Usage

\`\`\`javascript
// import { RepositoryViewer } from 'awesome-repo-viewer';

function App() {
  return (
    <RepositoryViewer 
      repository="owner/repo"
      theme="dark"
    />
  );
}
\`\`\`

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT © 2024 Awesome Team`
    },
    {
      name: 'package.json',
      path: 'package.json',
      type: 'file',
      language: 'json',
      content: `{
  "name": "awesome-project",
  "version": "1.0.0",
  "description": "A beautiful repository viewer",
  "main": "index.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "vite": "^4.0.0",
    "@types/react": "^18.2.0"
  }
}`
    }
  ];

  onMount(() => {
    // Load mock files for demonstration
    files = mockFiles;
    
    // Auto-open README if it exists
    const readme = findFile(files, 'README.md');
    if (readme && readme.type === 'file') {
      openFile(readme);
    }
  });

  function findFile(nodes: FileNode[], name: string): FileNode | null {
    for (const node of nodes) {
      if (node.name === name) return node;
      if (node.children) {
        const found = findFile(node.children, name);
        if (found) return found;
      }
    }
    return null;
  }

  function filterFiles(nodes: FileNode[], query: string): FileNode[] {
    const lowerQuery = query.toLowerCase();
    return nodes.reduce((acc: FileNode[], node) => {
      if (node.name.toLowerCase().includes(lowerQuery)) {
        acc.push(node);
      } else if (node.children) {
        const filteredChildren = filterFiles(node.children, query);
        if (filteredChildren.length > 0) {
          acc.push({ ...node, children: filteredChildren });
          // Auto-expand directories containing search results
          expandedPaths.add(node.path);
        }
      }
      return acc;
    }, []);
  }

  function toggleDirectory(path: string) {
    if (expandedPaths.has(path)) {
      expandedPaths.delete(path);
    } else {
      expandedPaths.add(path);
    }
    expandedPaths = expandedPaths;
  }

  function openFile(file: FileNode) {
    if (file.type !== 'file') return;

    const tabId = file.path;
    const existingTab = openTabs.find(tab => tab.id === tabId);

    if (existingTab) {
      activeTabId = tabId;
    } else {
      const newTab: Tab = {
        id: tabId,
        name: file.name,
        path: file.path,
        content: file.content || '',
        language: file.language || detectLanguage(file.name)
      };
      openTabs = [...openTabs, newTab];
      activeTabId = tabId;
    }
  }

  function closeTab(tabId: string, event?: Event) {
    event?.stopPropagation();
    
    const tabIndex = openTabs.findIndex(tab => tab.id === tabId);
    openTabs = openTabs.filter(tab => tab.id !== tabId);

    if (activeTabId === tabId && openTabs.length > 0) {
      // Switch to adjacent tab
      const newIndex = Math.min(tabIndex, openTabs.length - 1);
      activeTabId = openTabs[newIndex].id;
    } else if (openTabs.length === 0) {
      activeTabId = '';
    }
  }

  function detectLanguage(filename: string): string {
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    const languageMap: Record<string, string> = {
      js: 'javascript',
      ts: 'typescript',
      jsx: 'javascript',
      tsx: 'typescript',
      json: 'json',
      md: 'markdown',
      py: 'python',
      css: 'css',
      html: 'html',
      yml: 'yaml',
      yaml: 'yaml'
    };
    return languageMap[ext] || 'plaintext';
  }

  function getFileIcon(file: FileNode): string {
    if (file.type === 'directory') {
      return expandedPaths.has(file.path) ? 'folder-open' : 'folder';
    }

    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    const iconMap: Record<string, string> = {
      ts: 'file-code',
      tsx: 'file-code',
      js: 'file-code',
      jsx: 'file-code',
      json: 'braces',
      md: 'file-text',
      css: 'palette',
      html: 'globe',
      yml: 'settings',
      yaml: 'settings'
    };

    return iconMap[ext] || 'file';
  }

  function startResize(e: MouseEvent) {
    isResizing = true;
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResize);
  }

  function handleResize(e: MouseEvent) {
    if (!isResizing) return;
    sidebarWidth = Math.max(200, Math.min(400, e.clientX));
  }

  function stopResize() {
    isResizing = false;
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
  }

  // Keyboard shortcuts
  function handleKeydown(e: KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'p') {
      e.preventDefault();
      showSearch = !showSearch;
      if (showSearch) {
        setTimeout(() => {
          document.getElementById('file-search')?.focus();
        }, 100);
      }
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="repository-preview {theme}" style="height: {height}">
  <!-- File Explorer Sidebar -->
  <aside class="sidebar" style="width: {sidebarWidth}px">
    <div class="sidebar-header">
      <h3 class="sidebar-title">
        <Icon name="folder" size={16} />
        Explorer
      </h3>
      <button 
        class="icon-btn"
        on:click={() => showSearch = !showSearch}
        title="Search files (⌘P)"
      >
        <Icon name="search" size={16} />
      </button>
    </div>

    {#if showSearch}
      <div class="search-container" transition:slide={{ duration: 200 }}>
        <input
          id="file-search"
          type="text"
          placeholder="Search files..."
          bind:value={searchQuery}
          class="file-search"
        />
      </div>
    {/if}

    <div class="file-tree">
      {#each filteredFiles as file}
        <FileTreeNode 
          {file} 
          depth={0}
          {expandedPaths}
          onToggle={toggleDirectory}
          onSelect={openFile}
          {getFileIcon}
        />
      {/each}
    </div>

    <div 
      class="resize-handle"
      on:mousedown={startResize}
      class:resizing={isResizing}
    />
  </aside>

  <!-- Main Content Area -->
  <main class="main-content">
    <!-- Tabs -->
    {#if openTabs.length > 0}
      <div class="tabs-container">
        <div class="tabs">
          {#each openTabs as tab}
            <div
              class="tab"
              class:active={activeTabId === tab.id}
              role="button"
              tabindex="0"
              on:click={() => activeTabId = tab.id}
              on:keydown={(e) => e.key === 'Enter' && (activeTabId = tab.id)}
            >
              <Icon name={getFileIcon({ name: tab.name, type: 'file', path: tab.path })} size={14} />
              <span class="tab-name">{tab.name}</span>
              <button
                class="tab-close"
                on:click={(e) => closeTab(tab.id, e)}
              >
                <Icon name="x" size={14} />
              </button>
            </div>
          {/each}
        </div>

        {#if isMarkdownFile}
          <div class="view-mode-toggle">
            <button
              class="view-btn"
              class:active={viewMode === 'code'}
              on:click={() => viewMode = 'code'}
              title="Code view"
            >
              <Icon name="code" size={14} />
            </button>
            <button
              class="view-btn"
              class:active={viewMode === 'split'}
              on:click={() => viewMode = 'split'}
              title="Split view"
            >
              <Icon name="columns" size={14} />
            </button>
            <button
              class="view-btn"
              class:active={viewMode === 'preview'}
              on:click={() => viewMode = 'preview'}
              title="Preview"
            >
              <Icon name="eye" size={14} />
            </button>
          </div>
        {/if}
      </div>

      <!-- Editor/Preview Area -->
      <div class="editor-container" class:split={viewMode === 'split' && isMarkdownFile}>
        {#if activeTab}
          {#if showCode}
            <div class="editor-pane" transition:fade={{ duration: 150 }}>
              <MonacoEditor
                value={activeTab.content}
                language={activeTab.language}
                theme={theme === 'dark' ? 'vs-dark' : 'vs'}
                readOnly={true}
                height="100%"
                minimap={false}
              />
            </div>
          {/if}

          {#if showPreview}
            <div class="preview-pane" transition:fade={{ duration: 150 }}>
              <div class="preview-header">
                <Icon name="eye" size={16} />
                Preview
              </div>
              <div class="preview-content">
                <MarkdownViewer 
                  content={activeTab.content}
                  theme={theme === 'dark' ? 'neural' : 'dark'}
                />
              </div>
            </div>
          {/if}
        {/if}
      </div>
    {:else}
      <!-- Empty State -->
      <div class="empty-state">
        <Icon name="file-text" size={48} />
        <h3>No file selected</h3>
        <p>Select a file from the explorer to view its contents</p>
      </div>
    {/if}
  </main>
</div>

<!-- File Tree Node Component -->
<script context="module">
  export function FileTreeNode({ 
    file, 
    depth, 
    expandedPaths, 
    onToggle, 
    onSelect,
    getFileIcon 
  }) {
    const isExpanded = expandedPaths.has(file.path);
    const indent = depth * 20;

    function handleClick() {
      if (file.type === 'directory') {
        onToggle(file.path);
      } else {
        onSelect(file);
      }
    }

    return {
      file,
      isExpanded,
      indent,
      handleClick,
      depth,
      expandedPaths,
      onToggle,
      onSelect,
      getFileIcon
    };
  }
</script>

{#if true}
  {@const { isExpanded, indent, handleClick } = FileTreeNode({ 
    file, 
    depth, 
    expandedPaths, 
    onToggle, 
    onSelect,
    getFileIcon 
  })}
  <div class="file-node">
    <button
      class="file-item"
      class:directory={file.type === 'directory'}
      style="padding-left: {indent + 8}px"
      on:click={handleClick}
    >
      <Icon 
        name={getFileIcon(file)} 
        size={14} 
        class="file-icon {file.type}"
      />
      <span class="file-name">{file.name}</span>
    </button>

    {#if file.type === 'directory' && isExpanded && file.children}
      <div class="file-children">
        {#each file.children as child}
          <svelte:self
            file={child}
            depth={depth + 1}
            {expandedPaths}
            {onToggle}
            {onSelect}
            {getFileIcon}
          />
        {/each}
      </div>
    {/if}
  </div>
{/if}

<style>
  .repository-preview {
    display: flex;
    background: var(--bg-primary);
    border: 1px solid var(--border-primary);
    border-radius: 12px;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    position: relative;
  }

  /* Theme Variables */
  .repository-preview.dark {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --border-primary: #30363d;
    --border-secondary: #21262d;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --text-tertiary: #6e7681;
    --accent-primary: #58a6ff;
    --accent-hover: #1f6feb;
    --success: #3fb950;
    --warning: #d29922;
    --error: #f85149;
  }

  .repository-preview.light {
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --bg-tertiary: #f3f4f6;
    --border-primary: #d0d7de;
    --border-secondary: #e2e8f0;
    --text-primary: #24292f;
    --text-secondary: #57606a;
    --text-tertiary: #6e7781;
    --accent-primary: #0969da;
    --accent-hover: #0860ca;
    --success: #2da44e;
    --warning: #bf8700;
    --error: #cf222e;
  }

  /* Sidebar */
  .sidebar {
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-primary);
    display: flex;
    flex-direction: column;
    position: relative;
    min-width: 200px;
    max-width: 400px;
  }

  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-primary);
  }

  .sidebar-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .icon-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .icon-btn:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  /* Search */
  .search-container {
    padding: 0.75rem;
    border-bottom: 1px solid var(--border-primary);
  }

  .file-search {
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-primary);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 0.875rem;
    outline: none;
    transition: border-color 0.2s;
  }

  .file-search:focus {
    border-color: var(--accent-primary);
  }

  .file-search::placeholder {
    color: var(--text-tertiary);
  }

  /* File Tree */
  .file-tree {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem 0;
  }

  .file-node {
    user-select: none;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.375rem 0.75rem;
    border: none;
    background: transparent;
    color: var(--text-primary);
    font-size: 0.8125rem;
    text-align: left;
    cursor: pointer;
    transition: all 0.1s;
  }

  .file-item:hover {
    background: var(--bg-tertiary);
  }

  .file-item.directory {
    font-weight: 500;
  }

  .file-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :global(.file-icon) {
    flex-shrink: 0;
    opacity: 0.8;
  }

  :global(.file-icon.directory) {
    color: var(--accent-primary);
  }

  /* Resize Handle */
  .resize-handle {
    position: absolute;
    right: -2px;
    top: 0;
    bottom: 0;
    width: 4px;
    cursor: col-resize;
    z-index: 10;
  }

  .resize-handle:hover,
  .resize-handle.resizing {
    background: var(--accent-primary);
  }

  /* Main Content */
  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  /* Tabs */
  .tabs-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-primary);
    padding-right: 0.5rem;
  }

  .tabs {
    display: flex;
    flex: 1;
    overflow-x: auto;
    scrollbar-width: thin;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 0.75rem;
    border: none;
    border-right: 1px solid var(--border-primary);
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.8125rem;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
    min-width: 120px;
    max-width: 200px;
  }

  .tab:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .tab.active {
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .tab-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .tab-close {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border: none;
    background: transparent;
    color: var(--text-tertiary);
    border-radius: 4px;
    cursor: pointer;
    opacity: 0;
    transition: all 0.2s;
  }

  .tab:hover .tab-close,
  .tab.active .tab-close {
    opacity: 1;
  }

  .tab-close:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  /* View Mode Toggle */
  .view-mode-toggle {
    display: flex;
    gap: 0.25rem;
    padding: 0.25rem;
    background: var(--bg-tertiary);
    border-radius: 6px;
  }

  .view-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .view-btn:hover {
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .view-btn.active {
    background: var(--bg-primary);
    color: var(--accent-primary);
  }

  /* Editor Container */
  .editor-container {
    flex: 1;
    display: flex;
    background: var(--bg-primary);
    min-height: 0;
  }

  .editor-container.split {
    gap: 1px;
    background: var(--border-primary);
  }

  .editor-pane {
    flex: 1;
    min-width: 0;
    background: var(--bg-primary);
  }

  .preview-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary);
    min-width: 0;
  }

  .preview-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-primary);
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .preview-content {
    flex: 1;
    padding: 2rem;
    overflow-y: auto;
  }

  /* Empty State */
  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    color: var(--text-tertiary);
  }

  .empty-state h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .empty-state p {
    margin: 0;
    font-size: 0.875rem;
  }

  /* Scrollbar Styling */
  .file-tree::-webkit-scrollbar,
  .tabs::-webkit-scrollbar,
  .preview-content::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  .file-tree::-webkit-scrollbar-track,
  .tabs::-webkit-scrollbar-track,
  .preview-content::-webkit-scrollbar-track {
    background: transparent;
  }

  .file-tree::-webkit-scrollbar-thumb,
  .tabs::-webkit-scrollbar-thumb,
  .preview-content::-webkit-scrollbar-thumb {
    background: var(--border-primary);
    border-radius: 4px;
  }

  .file-tree::-webkit-scrollbar-thumb:hover,
  .tabs::-webkit-scrollbar-thumb:hover,
  .preview-content::-webkit-scrollbar-thumb:hover {
    background: var(--text-tertiary);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .repository-preview {
      flex-direction: column;
    }

    .sidebar {
      width: 100% !important;
      max-width: none;
      height: 200px;
      border-right: none;
      border-bottom: 1px solid var(--border-primary);
    }

    .resize-handle {
      display: none;
    }

    .editor-container.split {
      flex-direction: column;
    }
  }
</style>