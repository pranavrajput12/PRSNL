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
    <h1 class="cpu-die-text">Import Data</h1>
    <p>Import your bookmarks, notes, or data from other sources</p>
  </header>
  
  <div class="import-options">
    <button 
      class="option-card cpu-die-card {importType === 'bookmarks' ? 'active' : ''}"
      on:click={() => importType = 'bookmarks'}
    >
      <div class="chip-pattern">
        <div class="die-core"></div>
        <div class="die-pins">
          <div class="pin" style="--pos: 0"></div>
          <div class="pin" style="--pos: 1"></div>
          <div class="pin" style="--pos: 2"></div>
          <div class="pin" style="--pos: 3"></div>
        </div>
      </div>
      <Icon name="bookmark" size="large" />
      <h3>Bookmarks</h3>
      <p>Import from Chrome, Safari, or Firefox</p>
    </button>
    
    <button 
      class="option-card cpu-die-card {importType === 'json' ? 'active' : ''}"
      on:click={() => importType = 'json'}
    >
      <div class="chip-pattern">
        <div class="die-core"></div>
        <div class="die-pins">
          <div class="pin" style="--pos: 0"></div>
          <div class="pin" style="--pos: 1"></div>
          <div class="pin" style="--pos: 2"></div>
          <div class="pin" style="--pos: 3"></div>
        </div>
      </div>
      <Icon name="file-code" size="large" />
      <h3>PRSNL Export</h3>
      <p>Import from PRSNL JSON export</p>
    </button>
    
    <button 
      class="option-card cpu-die-card {importType === 'notes' ? 'active' : ''}"
      on:click={() => importType = 'notes'}
    >
      <div class="chip-pattern">
        <div class="die-core"></div>
        <div class="die-pins">
          <div class="pin" style="--pos: 0"></div>
          <div class="pin" style="--pos: 1"></div>
          <div class="pin" style="--pos: 2"></div>
          <div class="pin" style="--pos: 3"></div>
        </div>
      </div>
      <Icon name="file-text" size="large" />
      <h3>Notes</h3>
      <p>Import text or markdown files</p>
    </button>
  </div>
  
  <div class="steps-guide cpu-substrate">
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
          <p>Drag and drop your exported file below, or click to browse and select it from your computer</p>
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
    class="drop-zone cpu-socket {isDragging ? 'dragging' : ''}"
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
    on:drop={handleDrop}
  >
    <div class="socket-pins">
      {#each Array(16) as _, i}
        <div class="socket-pin" style="--index: {i}"></div>
      {/each}
    </div>
    
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
  
  /* CPU Die Text Effect */
  .cpu-die-text {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
    position: relative;
    display: inline-block;
    padding: 0.5rem 1rem;
  }
  
  .cpu-die-text::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      linear-gradient(45deg, 
        rgba(139, 69, 19, 0.1) 0%,
        transparent 25%,
        transparent 75%,
        rgba(139, 69, 19, 0.1) 100%
      ),
      radial-gradient(circle at 25% 25%, rgba(220, 20, 60, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 75% 75%, rgba(220, 20, 60, 0.1) 0%, transparent 50%);
    border: 2px solid rgba(139, 69, 19, 0.2);
    border-radius: 4px;
    z-index: -1;
  }
  
  .import-options {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  /* CPU Die Card Design */
  .cpu-die-card {
    position: relative;
    padding: 2rem 1.5rem 1.5rem;
    background: var(--bg-secondary);
    border: 2px solid rgba(139, 69, 19, 0.3);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
    overflow: hidden;
  }
  
  .chip-pattern {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    width: 24px;
    height: 24px;
  }
  
  .die-core {
    width: 12px;
    height: 12px;
    background: rgba(139, 69, 19, 0.4);
    border: 1px solid rgba(139, 69, 19, 0.6);
    margin: 6px auto;
  }
  
  .die-pins {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }
  
  .pin {
    position: absolute;
    width: 2px;
    height: 6px;
    background: rgba(220, 20, 60, 0.6);
  }
  
  .pin[style*="--pos: 0"] { top: 0; left: 4px; }
  .pin[style*="--pos: 1"] { top: 0; right: 4px; }
  .pin[style*="--pos: 2"] { bottom: 0; left: 4px; }
  .pin[style*="--pos: 3"] { bottom: 0; right: 4px; }
  
  .cpu-die-card:hover {
    background: var(--bg-tertiary);
    border-color: rgba(139, 69, 19, 0.5);
    transform: translateY(-2px);
  }
  
  .cpu-die-card.active {
    background: var(--bg-tertiary);
    border-color: var(--man-united-red);
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.2);
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
  
  /* CPU Substrate Design for Steps */
  .cpu-substrate {
    position: relative;
    background: var(--bg-secondary);
    border: 2px solid rgba(139, 69, 19, 0.2);
    border-radius: 8px;
    padding: 2rem;
    margin-bottom: 2rem;
    overflow: hidden;
  }
  
  .cpu-substrate::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      repeating-linear-gradient(
        90deg,
        transparent 0px,
        rgba(139, 69, 19, 0.05) 1px,
        transparent 2px,
        transparent 20px
      ),
      repeating-linear-gradient(
        0deg,
        transparent 0px,
        rgba(139, 69, 19, 0.05) 1px,
        transparent 2px,
        transparent 20px
      );
    z-index: 0;
  }
  
  .steps-guide h3,
  .steps {
    position: relative;
    z-index: 1;
  }
  
  /* CPU Socket Drop Zone */
  .cpu-socket {
    position: relative;
    border: 2px dashed rgba(139, 69, 19, 0.4);
    border-radius: 8px;
    padding: 3rem;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
    margin-bottom: 2rem;
    background: var(--bg-secondary);
    overflow: hidden;
  }
  
  .socket-pins {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 0;
  }
  
  .socket-pin {
    position: absolute;
    width: 4px;
    height: 4px;
    background: rgba(139, 69, 19, 0.3);
    border-radius: 50%;
  }
  
  .socket-pin:nth-child(1) { top: 10px; left: 10px; }
  .socket-pin:nth-child(2) { top: 10px; right: 10px; }
  .socket-pin:nth-child(3) { bottom: 10px; left: 10px; }
  .socket-pin:nth-child(4) { bottom: 10px; right: 10px; }
  .socket-pin:nth-child(5) { top: 10px; left: 50%; transform: translateX(-50%); }
  .socket-pin:nth-child(6) { bottom: 10px; left: 50%; transform: translateX(-50%); }
  .socket-pin:nth-child(7) { left: 10px; top: 50%; transform: translateY(-50%); }
  .socket-pin:nth-child(8) { right: 10px; top: 50%; transform: translateY(-50%); }
  .socket-pin:nth-child(9) { top: 30px; left: 30px; }
  .socket-pin:nth-child(10) { top: 30px; right: 30px; }
  .socket-pin:nth-child(11) { bottom: 30px; left: 30px; }
  .socket-pin:nth-child(12) { bottom: 30px; right: 30px; }
  .socket-pin:nth-child(13) { top: 50px; left: 50px; }
  .socket-pin:nth-child(14) { top: 50px; right: 50px; }
  .socket-pin:nth-child(15) { bottom: 50px; left: 50px; }
  .socket-pin:nth-child(16) { bottom: 50px; right: 50px; }
  
  .cpu-socket:hover {
    border-color: rgba(139, 69, 19, 0.6);
    background: var(--bg-tertiary);
  }
  
  .cpu-socket.dragging {
    border-color: var(--man-united-red);
    background: rgba(220, 20, 60, 0.05);
  }
  
  .cpu-socket.dragging .socket-pin {
    background: rgba(220, 20, 60, 0.5);
  }
  
  .drop-zone-content {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    cursor: pointer;
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
  
  .file-list {
    background: var(--bg-secondary);
    border: 1px solid rgba(139, 69, 19, 0.2);
    border-radius: 8px;
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
    background: var(--bg-tertiary);
    border-radius: 6px;
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
    border-radius: 4px;
    color: var(--error);
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .remove-btn:hover {
    background: rgba(255, 0, 0, 0.2);
  }
  
  .import-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 2rem;
    background: var(--man-united-red);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    margin: 0 auto;
  }
  
  .import-btn:hover:not(:disabled) {
    background: var(--accent-red-hover);
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(220, 20, 60, 0.3);
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
    border-radius: 6px;
    color: var(--error);
    margin-top: 1rem;
  }
  
  .results-card {
    background: var(--bg-secondary);
    border: 2px solid rgba(139, 69, 19, 0.2);
    border-radius: 8px;
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
    color: var(--man-united-red);
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
    background: rgba(220, 20, 60, 0.1);
    color: var(--man-united-red);
    border-radius: 6px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
    margin-top: 1rem;
  }
  
  .view-items-btn:hover {
    background: rgba(220, 20, 60, 0.2);
    transform: translateY(-2px);
  }
  
  /* Preserve original step styles */
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
    background: var(--man-united-red);
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
    
    .cpu-substrate {
      padding: 1rem;
    }
    
    .step {
      flex-direction: column;
      text-align: center;
    }
  }
</style>