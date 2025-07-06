<script>
  import { onMount } from 'svelte';
  import { captureItem, getRecentTags } from '$lib/api';
  import { addNotification } from '$lib/stores/app';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import UrlPreview from '$lib/components/UrlPreview.svelte';
  import TagAutocomplete from '$lib/components/TagAutocomplete.svelte';

  let url = '';
  let title = '';
  let highlight = '';
  let tags = [];
  let isSubmitting = false;
  let message = '';
  let messageType = '';
  let error = null;
  let recentTags = [];
  let isLoadingTags = false;
  let isDragging = false;
  let progress = 0;
  let progressInterval;

  // Focus on URL input on mount
  let urlInput;
  let dropZone;

  onMount(() => {
    urlInput?.focus();

    // Load recent tags
    loadRecentTags();

    // Setup paste handler for quick capture
    window.addEventListener('paste', handlePaste);

    // Setup drag and drop
    setupDragAndDrop();

    return () => {
      window.removeEventListener('paste', handlePaste);
      if (progressInterval) clearInterval(progressInterval);
    };
  });

  function setupDragAndDrop() {
    if (!dropZone) return;

    dropZone.addEventListener('dragenter', (e) => {
      e.preventDefault();
      isDragging = true;
    });

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      isDragging = true;
    });

    dropZone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      isDragging = false;
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      isDragging = false;

      const items = e.dataTransfer.items;

      for (let i = 0; i < items.length; i++) {
        if (items[i].kind === 'string' && items[i].type === 'text/uri-list') {
          items[i].getAsString((droppedUrl) => {
            url = droppedUrl;
          });
        } else if (items[i].kind === 'string' && items[i].type === 'text/plain') {
          items[i].getAsString((text) => {
            if (text.startsWith('http://') || text.startsWith('https://')) {
              url = text;
            } else {
              highlight = text;
            }
          });
        }
      }
    });
  }

  function handlePaste(e) {
    // Only handle paste if not focused in an input
    if (document.activeElement.tagName === 'INPUT' || 
        document.activeElement.tagName === 'TEXTAREA') {
      return;
    }

    const clipboardData = e.clipboardData || window.clipboardData;
    const pastedText = clipboardData.getData('text');

    if (pastedText) {
      e.preventDefault();

      if (pastedText.startsWith('http://') || pastedText.startsWith('https://')) {
        url = pastedText;
        urlInput?.focus();
      } else {
        highlight = pastedText;
      }
    }
  }

  async function loadRecentTags() {
    try {
      isLoadingTags = true;
      const data = await getRecentTags();
      recentTags = data.tags || [];
    } catch (err) {
      console.error('Failed to load tags:', err);
    } finally {
      isLoadingTags = false;
    }
  }

  function handleTagsUpdate(event) {
    tags = event.detail.tags;
  }

  async function handleSubmit() {
    if (!url && !highlight) {
      message = 'Please enter a URL or highlight text';
      messageType = 'error';
      return;
    }

    try {
      isSubmitting = true;
      message = 'Capturing...';
      messageType = 'info';

      // Start progress indicator
      startProgressIndicator();

      await captureItem({
        url,
        title,
        highlight,
        tags
      });

      message = 'Successfully captured!';
      messageType = 'success';

      // Add notification
      addNotification('Item captured successfully', 'success');

      // Reset form
      setTimeout(() => {
        url = '';
        title = '';
        highlight = '';
        tags = [];
        window.location.href = '/';
      }, 1000);
    } catch (err) {
      error = err;
      message = err instanceof Error ? err.message : 'Failed to capture. Please try again.';
      messageType = 'error';
    } finally {
      isSubmitting = false;
      clearInterval(progressInterval);
      progress = 0;
    }
  }

  function startProgressIndicator() {
    progress = 0;
    clearInterval(progressInterval);

    progressInterval = setInterval(() => {
      // Simulate progress, but slow down as we approach 90%
      if (progress < 90) {
        progress += (90 - progress) / 10;
      }
    }, 100);
  }

  // Keyboard shortcuts
  function handleKeydown(e) {
    // CMD/CTRL + Enter to submit
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
    // Escape to go back
    if (e.key === 'Escape') {
      e.preventDefault();
      window.location.href = '/';
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="container">
  <div class="capture-container" bind:this={dropZone} class:dragging={isDragging}>
    <div class="drag-overlay" class:active={isDragging}>
      <div class="drag-content">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        <h2>Drop URL or text here</h2>
      </div>
    </div>

    <h1>Capture</h1>

    {#if error}
      <ErrorMessage 
        message="Failed to capture item" 
        details={error.message} 
        retry={() => error = null} 
      />
    {/if}

    <form on:submit|preventDefault={handleSubmit}>
      <div class="form-group">
        <label for="url">URL</label>
        <input 
          type="text" 
          id="url" 
          bind:this={urlInput}
          bind:value={url} 
          placeholder="https://example.com" 
          disabled={isSubmitting}
        />

        {#if url}
          <UrlPreview {url} />
        {/if}
      </div>

      <div class="form-group">
        <label for="title">Title</label>
        <input 
          type="text" 
          id="title" 
          bind:value={title} 
          placeholder="Page title" 
          disabled={isSubmitting}
        />
      </div>

      <div class="form-group">
        <label for="highlight">Highlight</label>
        <textarea 
          id="highlight" 
          bind:value={highlight} 
          placeholder="Text highlight or notes" 
          rows="4"
          disabled={isSubmitting}
        ></textarea>
      </div>

      <div class="form-group">
        <label for="tags">Tags</label>
        <TagAutocomplete
          value=""
          placeholder="Add tags..."
          disabled={isSubmitting}
          on:tags={handleTagsUpdate}
        />

        {#if isLoadingTags}
          <div class="tag-suggestions">
            <Spinner size="small" />
            <span>Loading tags...</span>
          </div>
        {:else if recentTags.length > 0}
          <div class="tag-suggestions">
            <span>Recent tags:</span>
            {#each recentTags as tag}
              <button 
                type="button" 
                class="tag-button"
                on:click={() => {
                  if (!tags.includes(tag)) {
                    tags = [...tags, tag];
                  }
                }}
              >
                {tag}
              </button>
            {/each}
          </div>
        {/if}
      </div>

      {#if message}
        <div class="message {messageType}">
          {message}
        </div>
      {/if}

      {#if isSubmitting}
        <div class="progress-bar">
          <div class="progress-fill" style="width: {progress}%"></div>
        </div>
      {/if}

      <div class="form-actions">
        <button 
          type="submit" 
          class="primary" 
          disabled={isSubmitting}
        >
          {#if isSubmitting}
            <Spinner size="small" />
            Capturing...
          {:else}
            Capture
          {/if}
        </button>
        <button 
          type="button" 
          on:click={() => window.history.back()}
          disabled={isSubmitting}
        >
          Cancel
        </button>
        <div class="keyboard-shortcut">Cmd+Enter to submit</div>
      </div>
    </form>
  </div>
</div>

<style>
  .capture-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    position: relative;
    min-height: 400px;
    transition: all 0.3s ease;
  }

  .dragging {
    background: var(--bg-secondary);
    border: 2px dashed var(--accent);
    border-radius: var(--radius);
  }

  .drag-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
    z-index: 10;
  }

  .drag-overlay.active {
    opacity: 1;
  }

  .drag-content {
    text-align: center;
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  h1 {
    margin-bottom: 2rem;
    color: var(--text-primary);
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
    font-weight: 500;
  }

  input, textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 1rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  input:focus, textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent-muted);
    outline: none;
  }

  .form-actions {
    display: flex;
    gap: 1rem;
    margin-top: 2rem;
    align-items: center;
    flex-wrap: wrap;
  }

  button {
    padding: 0.75rem 1.5rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  button:hover {
    background: var(--bg-hover);
    transform: translateY(-1px);
  }

  button:active {
    transform: translateY(0);
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  button.primary {
    background: var(--accent);
    color: var(--accent-text);
    border-color: var(--accent);
  }

  button.primary:hover {
    background: var(--accent-hover);
  }

  .message {
    padding: 0.75rem;
    border-radius: var(--radius);
    margin-bottom: 1rem;
    animation: fadeIn 0.3s ease;
  }

  .message.success {
    background: var(--success-bg);
    color: var(--success);
  }

  .message.error {
    background: var(--error-bg);
    color: var(--error);
  }

  .message.info {
    background: var(--info-bg);
    color: var(--info);
  }

  .tag-suggestions {
    margin-top: 0.5rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
  }

  .tag-button {
    padding: 0.25rem 0.5rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .tag-button:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .keyboard-shortcut {
    font-size: 0.8125rem;
    color: var(--text-secondary);
    margin-left: auto;
  }

  .progress-bar {
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
    margin: 1rem 0;
  }

  .progress-fill {
    height: 100%;
    background: var(--accent);
    transition: width 0.3s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>