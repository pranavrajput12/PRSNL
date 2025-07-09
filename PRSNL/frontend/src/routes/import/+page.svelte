<script>
  import { onMount } from 'svelte';
  import { API_BASE_URL } from '$lib/constants';
  import Icon from '$lib/components/Icon.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import ProcessingProgress from '$lib/components/ProcessingProgress.svelte';
  
  let files = [];
  let isDragging = false;
  let isProcessing = false;
  let importResults = null;
  let error = null;
  let autoFetch = true;
  let importType = 'bookmarks';
  let progress = 0;
  let currentItem = '';
  
  function handleDragOver(e) {
    e.preventDefault();
    isDragging = true;
  }
  
  function handleDragLeave(e) {
    e.preventDefault();
    isDragging = false;
  }
  
  function handleDrop(e) {
    e.preventDefault();
    isDragging = false;
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  }
  
  function handleFileSelect(e) {
    const selectedFiles = Array.from(e.target.files);
    handleFiles(selectedFiles);
  }
  
  function handleFiles(newFiles) {
    files = newFiles.filter(file => {
      if (importType === 'bookmarks') {
        return file.type === 'text/html' || file.name.endsWith('.html');
      } else if (importType === 'json') {
        return file.type === 'application/json' || file.name.endsWith('.json');
      } else if (importType === 'notes') {
        return file.type === 'text/plain' || file.type === 'text/markdown' || 
               file.name.endsWith('.txt') || file.name.endsWith('.md');
      }
      return false;
    });
    
    if (files.length === 0) {
      error = `Please select valid ${importType} files`;
    } else {
      error = null;
    }
  }
  
  async function startImport() {
    if (files.length === 0) return;
    
    isProcessing = true;
    error = null;
    importResults = null;
    progress = 0;
    
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        currentItem = file.name;
        progress = ((i + 1) / files.length) * 100;
        
        const formData = new FormData();
        formData.append('file', file);
        
        if (importType === 'bookmarks') {
          formData.append('auto_fetch', autoFetch.toString());
        }
        
        const response = await fetch(`${API_BASE_URL}/import/${importType}`, {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          throw new Error(`Import failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (!importResults) {
          importResults = {
            imported: 0,
            skipped: 0,
            errors: [],
            total: 0
          };
        }
        
        importResults.imported += result.imported || 0;
        importResults.skipped += result.skipped || 0;
        importResults.total += result.total || 0;
        if (result.errors) {
          importResults.errors.push(...result.errors);
        }
      }
      
      // Clear files after successful import
      files = [];
    } catch (err) {
      error = err.message;
    } finally {
      isProcessing = false;
      currentItem = '';
    }
  }
  
  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  function removeFile(index) {
    files = files.filter((_, i) => i !== index);
  }
</script>

<div class="container">
  <header class="page-header">
    <h1>Import Data</h1>
    <p>Import your bookmarks, notes, or data from other sources</p>
  </header>
  
  <div class="import-options">
    <button 
      class="option-card {importType === 'bookmarks' ? 'active' : ''}"
      on:click={() => importType = 'bookmarks'}
    >
      <Icon name="bookmark" size="large" />
      <h3>Bookmarks</h3>
      <p>Import from Chrome, Safari, or Firefox</p>
    </button>
    
    <button 
      class="option-card {importType === 'json' ? 'active' : ''}"
      on:click={() => importType = 'json'}
    >
      <Icon name="file-code" size="large" />
      <h3>PRSNL Export</h3>
      <p>Import from PRSNL JSON export</p>
    </button>
    
    <button 
      class="option-card {importType === 'notes' ? 'active' : ''}"
      on:click={() => importType = 'notes'}
    >
      <Icon name="file-text" size="large" />
      <h3>Notes</h3>
      <p>Import text or markdown files</p>
    </button>
  </div>
  
  <!-- Step by step guide -->
  <div class="steps-guide">
    <h3>How to export and import your bookmarks:</h3>
    <div class="steps">
      <div class="step">
        <div class="step-number">1</div>
        <div class="step-content">
          <h4>Export from your browser</h4>
          <p>
            {#if importType === 'bookmarks'}
              <strong>Chrome:</strong> Menu → Bookmarks → Bookmark Manager → ⋮ → Export bookmarks<br>
              <strong>Safari:</strong> File → Export → Bookmarks<br>
              <strong>Firefox:</strong> Menu → Bookmarks → Manage Bookmarks → Import and Backup → Export
            {:else if importType === 'json'}
              Go to your PRSNL dashboard → Settings → Export Data → Download JSON
            {:else}
              Prepare your text files (.txt) or markdown files (.md) with your notes
            {/if}
          </p>
        </div>
      </div>
      
      <div class="step">
        <div class="step-number">2</div>
        <div class="step-content">
          <h4>Select your file</h4>
          <p>
            Drag and drop your exported file below, or click to browse and select it from your computer
          </p>
        </div>
      </div>
      
      <div class="step">
        <div class="step-number">3</div>
        <div class="step-content">
          <h4>Import and organize</h4>
          <p>
            {#if importType === 'bookmarks'}
              Click "Start Import" - we'll fetch page content and organize your bookmarks automatically
            {:else if importType === 'json'}
              Click "Start Import" to restore your PRSNL data with all tags and metadata
            {:else}
              Click "Start Import" to convert your notes into searchable PRSNL items
            {/if}
          </p>
        </div>
      </div>
    </div>
  </div>
  
  {#if importType === 'bookmarks'}
    <div class="settings-section">
      <label class="checkbox-label">
        <input 
          type="checkbox" 
          bind:checked={autoFetch}
          disabled={isProcessing}
        />
        <span>Auto-fetch page content (slower but more complete)</span>
      </label>
    </div>
  {/if}
  
  <div 
    class="drop-zone {isDragging ? 'dragging' : ''}"
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
    on:drop={handleDrop}
  >
    <input 
      type="file" 
      id="file-input" 
      multiple
      accept={importType === 'bookmarks' ? '.html' : importType === 'json' ? '.json' : '.txt,.md'}
      on:change={handleFileSelect}
      style="display: none;"
    />
    
    <label for="file-input" class="drop-zone-content">
      <Icon name="upload-cloud" size="xlarge" />
      <h3>Drop files here or click to browse</h3>
      <p>
        {#if importType === 'bookmarks'}
          HTML bookmark files exported from your browser
        {:else if importType === 'json'}
          JSON files exported from PRSNL
        {:else}
          Text (.txt) or Markdown (.md) files
        {/if}
      </p>
    </label>
  </div>
  
  {#if files.length > 0}
    <div class="file-list">
      <h3>Selected Files</h3>
      {#each files as file, i}
        <div class="file-item">
          <Icon name="file" size="small" />
          <span class="file-name">{file.name}</span>
          <span class="file-size">{formatFileSize(file.size)}</span>
          <button 
            class="remove-btn"
            on:click={() => removeFile(i)}
            disabled={isProcessing}
          >
            <Icon name="x" size="small" />
          </button>
        </div>
      {/each}
    </div>
    
    <button 
      class="import-btn"
      on:click={startImport}
      disabled={isProcessing}
    >
      {#if isProcessing}
        <Spinner size="small" />
        Importing...
      {:else}
        <Icon name="upload" size="small" />
        Start Import
      {/if}
    </button>
  {/if}
  
  {#if isProcessing}
    <ProcessingProgress 
      {progress}
      status={`Importing ${currentItem}...`}
      active={true}
    />
  {/if}
  
  {#if error}
    <div class="error-message">
      <Icon name="alert-circle" size="small" />
      {error}
    </div>
  {/if}
  
  {#if importResults}
    <div class="results-card">
      <h3>Import Complete!</h3>
      <div class="results-stats">
        <div class="stat">
          <span class="stat-value">{importResults.imported}</span>
          <span class="stat-label">Imported</span>
        </div>
        <div class="stat">
          <span class="stat-value">{importResults.skipped}</span>
          <span class="stat-label">Skipped</span>
        </div>
        <div class="stat">
          <span class="stat-value">{importResults.errors.length}</span>
          <span class="stat-label">Errors</span>
        </div>
      </div>
      
      {#if importResults.errors.length > 0}
        <details class="error-details">
          <summary>View errors</summary>
          <ul>
            {#each importResults.errors as error}
              <li>{error.item}: {error.error}</li>
            {/each}
          </ul>
        </details>
      {/if}
      
      <a href="/" class="view-items-btn">
        View Imported Items
      </a>
    </div>
  {/if}
</div>

<style>
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .page-header {
    text-align: center;
    margin-bottom: 3rem;
  }
  
  .page-header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, var(--text-primary), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .import-options {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .option-card {
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
    text-align: center;
  }
  
  .option-card:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-2px);
  }
  
  .option-card.active {
    background: rgba(74, 158, 255, 0.1);
    border-color: var(--accent);
    box-shadow: 0 0 20px rgba(74, 158, 255, 0.2);
  }
  
  .option-card h3 {
    margin: 0.5rem 0;
    font-size: 1.1rem;
  }
  
  .option-card p {
    margin: 0;
    font-size: 0.9rem;
    color: var(--text-secondary);
  }
  
  .settings-section {
    margin-bottom: 2rem;
  }
  
  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }
  
  .drop-zone {
    border: 2px dashed rgba(255, 255, 255, 0.2);
    border-radius: var(--radius);
    padding: 3rem;
    text-align: center;
    transition: all var(--transition-base);
    cursor: pointer;
    margin-bottom: 2rem;
  }
  
  .drop-zone:hover {
    border-color: rgba(255, 255, 255, 0.4);
    background: rgba(255, 255, 255, 0.02);
  }
  
  .drop-zone.dragging {
    border-color: var(--accent);
    background: rgba(74, 158, 255, 0.05);
  }
  
  .drop-zone-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    cursor: pointer;
  }
  
  .file-list {
    background: rgba(255, 255, 255, 0.05);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }
  
  .file-list h3 {
    margin-bottom: 1rem;
  }
  
  .file-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-sm);
    margin-bottom: 0.5rem;
  }
  
  .file-name {
    flex: 1;
  }
  
  .file-size {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }
  
  .remove-btn {
    padding: 0.25rem;
    background: rgba(255, 0, 0, 0.1);
    border: none;
    border-radius: var(--radius-sm);
    color: var(--error);
    cursor: pointer;
    transition: all var(--transition-base);
  }
  
  .remove-btn:hover {
    background: rgba(255, 0, 0, 0.2);
  }
  
  .import-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 2rem;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: var(--radius);
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-base);
    margin: 0 auto;
  }
  
  .import-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(74, 158, 255, 0.3);
  }
  
  .import-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .error-message {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    background: rgba(255, 0, 0, 0.1);
    border: 1px solid rgba(255, 0, 0, 0.3);
    border-radius: var(--radius);
    color: var(--error);
    margin-top: 1rem;
  }
  
  .results-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    padding: 2rem;
    text-align: center;
    margin-top: 2rem;
  }
  
  .results-stats {
    display: flex;
    justify-content: center;
    gap: 3rem;
    margin: 2rem 0;
  }
  
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .stat-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--accent);
  }
  
  .stat-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }
  
  .error-details {
    margin-top: 1rem;
    text-align: left;
  }
  
  .error-details summary {
    cursor: pointer;
    color: var(--error);
  }
  
  .error-details ul {
    margin-top: 0.5rem;
    padding-left: 1.5rem;
    font-size: 0.9rem;
    color: var(--text-secondary);
  }
  
  .view-items-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: rgba(74, 158, 255, 0.1);
    color: var(--accent);
    border-radius: var(--radius);
    text-decoration: none;
    font-weight: 600;
    transition: all var(--transition-base);
    margin-top: 1rem;
  }
  
  .view-items-btn:hover {
    background: rgba(74, 158, 255, 0.2);
    transform: translateY(-2px);
  }
  
  /* Step guide styles */
  .steps-guide {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    padding: 2rem;
    margin-bottom: 2rem;
  }
  
  .steps-guide h3 {
    margin-bottom: 1.5rem;
    color: var(--text-primary);
  }
  
  .steps {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .step {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .step-number {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    background: var(--accent);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.1rem;
  }
  
  .step-content h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
    color: var(--text-primary);
  }
  
  .step-content p {
    margin: 0;
    color: var(--text-secondary);
    line-height: 1.6;
  }
  
  .step-content strong {
    color: var(--text-primary);
  }
  
  @media (max-width: 768px) {
    .import-options {
      grid-template-columns: 1fr;
    }
    
    .steps-guide {
      padding: 1rem;
    }
    
    .step {
      flex-direction: column;
      text-align: center;
    }
  }
</style>