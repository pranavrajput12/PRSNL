<script>
  import { onMount } from 'svelte';
  import { API_BASE_URL } from '$lib/constants';
  import Icon from '$lib/components/Icon.svelte';
  import Spinner from '$lib/components/Spinner.svelte';
  import ProcessingProgress from '$lib/components/ProcessingProgress.svelte';
  import AnimatedButton from '$lib/components/AnimatedButton.svelte';

  let files = [];
  let isDragging = false;
  let isProcessing = false;
  let importResults = null;
  let error = null;
  let autoFetch = true;
  let importType = 'bookmarks';
  let progress = 0;
  let currentItem = '';
  let fileInput;

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
    files = newFiles.filter((file) => {
      if (importType === 'bookmarks') {
        return file.type === 'text/html' || file.name.endsWith('.html');
      } else if (importType === 'json') {
        return file.type === 'application/json' || file.name.endsWith('.json');
      } else if (importType === 'notes') {
        return (
          file.type === 'text/plain' ||
          file.type === 'text/markdown' ||
          file.name.endsWith('.txt') ||
          file.name.endsWith('.md')
        );
      }
      return false;
    });

    if (files.length === 0 && newFiles.length > 0) {
      error = `Please select valid ${importType} files`;
    } else {
      error = null;
    }
  }

  async function importData() {
    if (files.length === 0) return;

    isProcessing = true;
    error = null;
    progress = 0;

    try {
      const formData = new FormData();
      files.forEach((file) => formData.append('files', file));
      formData.append('type', importType);
      formData.append('auto_fetch', autoFetch.toString());

      const response = await fetch(`${API_BASE_URL}/api/import-data`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Import failed: ${response.statusText}`);
      }

      importResults = await response.json();
      files = [];
    } catch (err) {
      error = err.message;
    } finally {
      isProcessing = false;
      progress = 0;
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

<div class="neural-import-console">
  <!-- Import Type Selection - RAM-style modules -->
  <div class="import-type-selector">
    <div class="type-ram-slots">
      <button
        class="ram-module {importType === 'bookmarks' ? 'active' : ''}"
        on:click={() => (importType = 'bookmarks')}
      >
        <div class="ram-body">
          <div class="ram-label">BOOKMARKS</div>
          <div class="ram-specs">Chrome • Safari • Firefox</div>
          <div class="ram-contacts">
            {#each Array(8) as _, i}
              <div class="ram-contact"></div>
            {/each}
          </div>
        </div>
        <div class="ram-notch"></div>
      </button>

      <button
        class="ram-module {importType === 'json' ? 'active' : ''}"
        on:click={() => (importType = 'json')}
      >
        <div class="ram-body">
          <div class="ram-label">PRSNL EXPORT</div>
          <div class="ram-specs">JSON • Backup Files</div>
          <div class="ram-contacts">
            {#each Array(8) as _, i}
              <div class="ram-contact"></div>
            {/each}
          </div>
        </div>
        <div class="ram-notch"></div>
      </button>

      <button
        class="ram-module {importType === 'notes' ? 'active' : ''}"
        on:click={() => (importType = 'notes')}
      >
        <div class="ram-body">
          <div class="ram-label">NOTES</div>
          <div class="ram-specs">TXT • Markdown • MD</div>
          <div class="ram-contacts">
            {#each Array(8) as _, i}
              <div class="ram-contact"></div>
            {/each}
          </div>
        </div>
        <div class="ram-notch"></div>
      </button>
    </div>
  </div>

  <!-- File Drop Zone - Motherboard CPU socket style -->
  <div class="cpu-socket-container">
    <div class="socket-header">
      <div class="socket-label">DATA IMPORT SOCKET</div>
      <div class="socket-type">LGA-{importType.toUpperCase()}</div>
    </div>

    <div
      class="cpu-socket {isDragging ? 'receiving' : ''} {files.length > 0 ? 'loaded' : ''}"
      on:dragover={handleDragOver}
      on:dragleave={handleDragLeave}
      on:drop={handleDrop}
    >
      <div class="socket-pins">
        {#each Array(64) as _, i}
          <div class="socket-pin" style="--index: {i}"></div>
        {/each}
      </div>

      <div class="drop-zone-content">
        {#if files.length === 0}
          <div class="drop-icon">
            <Icon name="upload" size="xx-large" color="var(--info)" />
          </div>
          <h3>Drop {importType} files here</h3>
          <p>or click to browse files</p>
          <input
            type="file"
            multiple
            accept={importType === 'bookmarks'
              ? '.html'
              : importType === 'json'
                ? '.json'
                : '.txt,.md'}
            on:change={handleFileSelect}
            style="display: none;"
            bind:this={fileInput}
          />
          <AnimatedButton variant="secondary" on:click={() => fileInput?.click()}>
            Browse Files
          </AnimatedButton>
        {:else}
          <div class="files-loaded">
            <Icon name="check-circle" size="large" color="var(--synapse-teal)" />
            <h4>{files.length} file{files.length !== 1 ? 's' : ''} loaded</h4>
            {#each files as file, i}
              <div class="file-chip">
                <span class="file-name">{file.name}</span>
                <span class="file-size">{formatFileSize(file.size)}</span>
                <button class="remove-file" on:click={() => removeFile(i)}>×</button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Import Options - Circuit board style -->
  <div class="import-options-board">
    <div class="circuit-trace"></div>
    <div class="option-component">
      <label class="switch-component">
        <input type="checkbox" bind:checked={autoFetch} />
        <div class="switch-slider"></div>
        <span class="component-label">AUTO-FETCH CONTENT</span>
      </label>
    </div>
  </div>

  <!-- Process Button - Power button style -->
  <div class="power-section">
    <button
      class="power-button {isProcessing ? 'processing' : ''}"
      disabled={files.length === 0 || isProcessing}
      on:click={importData}
    >
      <div class="power-ring">
        <div class="power-core">
          {#if isProcessing}
            <Spinner size="medium" />
          {:else}
            <Icon name="power" size="large" color="var(--text-primary)" />
          {/if}
        </div>
      </div>
      <span class="power-label">
        {isProcessing ? 'IMPORTING...' : 'IMPORT DATA'}
      </span>
    </button>
  </div>

  <!-- Progress Display -->
  {#if isProcessing}
    <div class="progress-display">
      <ProcessingProgress />
    </div>
  {/if}

  <!-- Results Display - LED status panel -->
  {#if importResults}
    <div class="status-panel">
      <div class="panel-header">
        <div class="status-led success"></div>
        <span>IMPORT COMPLETE</span>
      </div>
      <div class="results-grid">
        <div class="result-stat">
          <div class="stat-value">{importResults.imported || 0}</div>
          <div class="stat-label">Items Imported</div>
        </div>
        <div class="result-stat">
          <div class="stat-value">{importResults.failed || 0}</div>
          <div class="stat-label">Failed</div>
        </div>
        <div class="result-stat">
          <div class="stat-value">{importResults.duplicates || 0}</div>
          <div class="stat-label">Duplicates</div>
        </div>
      </div>
    </div>
  {/if}

  <!-- Error Display -->
  {#if error}
    <div class="error-panel">
      <div class="panel-header">
        <div class="status-led error"></div>
        <span>IMPORT ERROR</span>
      </div>
      <p>{error}</p>
    </div>
  {/if}
</div>

<style>
  .neural-import-console {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    border-radius: 1rem;
    position: relative;
  }

  /* Import Type Selection - RAM Modules */
  .import-type-selector {
    margin-bottom: 3rem;
  }

  .type-ram-slots {
    display: flex;
    gap: 2rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  .ram-module {
    position: relative;
    width: 200px;
    height: 80px;
    background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
    border: 2px solid var(--border);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    overflow: visible;
  }

  .ram-module:hover {
    border-color: var(--info);
    box-shadow: 0 0 20px rgba(74, 158, 255, 0.3);
  }

  .ram-module.active {
    border-color: var(--info);
    background: linear-gradient(135deg, var(--info) 0%, var(--info) 100%);
    box-shadow: 0 0 30px rgba(74, 158, 255, 0.5);
  }

  .ram-body {
    padding: 8px 12px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .ram-label {
    font-size: 0.9rem;
    font-weight: 700;
    color: white;
    text-align: center;
    margin-bottom: 4px;
  }

  .ram-specs {
    font-size: 0.7rem;
    color: rgba(255, 255, 255, 0.8);
    text-align: center;
  }

  .ram-notch {
    position: absolute;
    top: -2px;
    left: 50%;
    transform: translateX(-50%);
    width: 20px;
    height: 8px;
    background: var(--bg-secondary);
    border-radius: 0 0 4px 4px;
  }

  .ram-contacts {
    position: absolute;
    bottom: -4px;
    left: 12px;
    right: 12px;
    height: 4px;
    display: flex;
    gap: 2px;
  }

  .ram-contact {
    flex: 1;
    height: 100%;
    background: linear-gradient(180deg, var(--highlight) 0%, var(--warning) 100%);
    border-radius: 0 0 1px 1px;
  }

  /* CPU Socket Style Drop Zone */
  .cpu-socket-container {
    margin-bottom: 3rem;
    text-align: center;
  }

  .socket-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding: 0 2rem;
  }

  .socket-label {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--info);
  }

  .socket-type {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .cpu-socket {
    position: relative;
    width: 400px;
    height: 400px;
    margin: 0 auto;
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
    border: 3px solid var(--border);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    overflow: hidden;
  }

  .cpu-socket.receiving {
    border-color: var(--info);
    box-shadow: 0 0 40px rgba(74, 158, 255, 0.5);
  }

  .cpu-socket.loaded {
    border-color: var(--synapse-teal);
    box-shadow: 0 0 40px var(--synapse-teal-40);
  }

  .socket-pins {
    position: absolute;
    top: 10px;
    left: 10px;
    right: 10px;
    bottom: 10px;
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    grid-template-rows: repeat(8, 1fr);
    gap: 4px;
    opacity: 0.3;
  }

  .socket-pin {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, var(--text-muted) 0%, var(--bg-secondary) 100%);
    border-radius: 2px;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
  }

  .drop-zone-content {
    position: relative;
    z-index: 2;
    text-align: center;
    color: white;
  }

  .drop-icon {
    margin-bottom: 1rem;
  }

  .files-loaded {
    max-width: 300px;
  }

  .file-chip {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(74, 158, 255, 0.2);
    padding: 8px 12px;
    border-radius: 6px;
    margin: 8px 0;
    font-size: 0.9rem;
  }

  .file-name {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .file-size {
    color: var(--text-secondary);
    font-size: 0.8rem;
  }

  .remove-file {
    background: none;
    border: none;
    color: var(--error);
    cursor: pointer;
    font-size: 1.2rem;
    font-weight: bold;
  }

  /* Import Options Board */
  .import-options-board {
    position: relative;
    background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 2rem;
    margin-bottom: 3rem;
  }

  .circuit-trace {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--info) 0%, var(--synapse-teal) 100%);
  }

  .option-component {
    display: flex;
    justify-content: center;
  }

  .switch-component {
    display: flex;
    align-items: center;
    gap: 1rem;
    cursor: pointer;
  }

  .switch-slider {
    position: relative;
    width: 60px;
    height: 30px;
    background: var(--bg-tertiary);
    border-radius: 15px;
    transition: all 0.3s ease;
  }

  .switch-slider::before {
    content: '';
    position: absolute;
    top: 3px;
    left: 3px;
    width: 24px;
    height: 24px;
    background: var(--text-muted);
    border-radius: 50%;
    transition: all 0.3s ease;
  }

  input[type='checkbox']:checked + .switch-slider {
    background: var(--info);
  }

  input[type='checkbox']:checked + .switch-slider::before {
    transform: translateX(30px);
    background: white;
  }

  .component-label {
    font-weight: 600;
    color: white;
  }

  /* Power Button */
  .power-section {
    text-align: center;
    margin-bottom: 3rem;
  }

  .power-button {
    position: relative;
    width: 120px;
    height: 120px;
    background: none;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .power-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .power-ring {
    width: 100%;
    height: 100%;
    border: 4px solid var(--border);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
  }

  .power-button:hover:not(:disabled) .power-ring {
    border-color: var(--info);
    box-shadow: 0 0 30px rgba(74, 158, 255, 0.5);
  }

  .power-button.processing .power-ring {
    border-color: var(--synapse-teal);
    box-shadow: 0 0 30px var(--synapse-teal-40);
  }

  .power-core {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .power-label {
    display: block;
    margin-top: 1rem;
    font-weight: 700;
    color: white;
  }

  /* Status Panels */
  .status-panel,
  .error-panel {
    background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 2rem;
    margin-bottom: 2rem;
  }

  .panel-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    font-weight: 700;
    color: white;
  }

  .status-led {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  .status-led.success {
    background: var(--synapse-teal);
    box-shadow: 0 0 10px var(--synapse-teal-40);
  }

  .status-led.error {
    background: var(--error);
    box-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
  }

  .results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 2rem;
  }

  .result-stat {
    text-align: center;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 900;
    color: var(--info);
    margin-bottom: 0.5rem;
  }

  .stat-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .type-ram-slots {
      flex-direction: column;
      align-items: center;
    }

    .cpu-socket {
      width: 300px;
      height: 300px;
    }

    .socket-pins {
      grid-template-columns: repeat(6, 1fr);
      grid-template-rows: repeat(6, 1fr);
    }
  }
</style>
