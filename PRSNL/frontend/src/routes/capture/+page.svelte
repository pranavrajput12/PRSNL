<script lang="ts">
  import { onMount } from 'svelte';
  import { captureItem, getRecentTags, getAISuggestions } from '$lib/api';
  import { addNotification } from '$lib/stores/app';
  import { isVideoUrl, getVideoPlatform, estimateDownloadTime, formatTime } from '$lib/utils/url';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import UrlPreview from '$lib/components/UrlPreview.svelte';
  import TagAutocomplete from '$lib/components/TagAutocomplete.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import Icon from '$lib/components/Icon.svelte';
  import AnimatedButton from '$lib/components/AnimatedButton.svelte';
  import PremiumInteractions from '$lib/components/PremiumInteractions.svelte';

  // Form fields and state
  let url = '';
  let title = '';
  let highlight = '';
  let tags: string[] = [];
  let isSubmitting = false;
  let message = '';
  let messageType = '';
  let error: Error | null = null;
  let recentTags: string[] = [];
  let isLoadingTags = false;
  let isDragging = false;
  let progress = 0;
  let progressInterval: number | null = null;
  
  // AI suggestions state
  let isLoadingSuggestions = false;
  let suggestionsError: string | null = null;
  
  // Video-specific variables
  let isVideoDetected = false;
  let videoPlatform: string | null = null;
  let estimatedDownloadTimeSeconds = 0;
  let videoQuality: 'standard' | 'high' = 'high';
  let thumbnailPreviewUrl: string | null = null;

  // Focus on URL input on mount
  let urlInput: HTMLInputElement;
  let dropZone: HTMLDivElement;

  // Debounced AI suggestions timeout
  let aiSuggestionsTimeout: number | undefined;
  
  // Watch for URL changes to detect video URLs and get AI suggestions
  $: {
    if (url) {
      detectVideoUrl(url);
      // Debounce AI suggestions
      if (url.startsWith('http://') || url.startsWith('https://')) {
        if (aiSuggestionsTimeout) clearTimeout(aiSuggestionsTimeout);
        aiSuggestionsTimeout = setTimeout(() => loadAISuggestions(url), 500);
      }
    } else {
      resetVideoDetection();
      if (aiSuggestionsTimeout) clearTimeout(aiSuggestionsTimeout);
    }
  }

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
  
  /**
   * Detects if the URL is a video URL and updates the UI accordingly
   */
  function detectVideoUrl(urlToCheck: string): void {
    isVideoDetected = isVideoUrl(urlToCheck);
    
    if (isVideoDetected) {
      videoPlatform = getVideoPlatform(urlToCheck);
      estimatedDownloadTimeSeconds = estimateDownloadTime(urlToCheck);
      
      // Add video tag if not already present
      if (videoPlatform && !tags.includes('video')) {
        tags = [...tags, 'video'];
        
        // Add platform tag if not already present
        const platformTag = videoPlatform.toLowerCase();
        if (!tags.includes(platformTag)) {
          tags = [...tags, platformTag];
        }
      }
      
      // For Instagram, we could potentially fetch a thumbnail preview
      // This would require a backend endpoint in a real implementation
      if (videoPlatform === 'Instagram') {
        // Simulating a thumbnail URL - in a real app, this would come from an API
        thumbnailPreviewUrl = null;
      }
    } else {
      resetVideoDetection();
    }
  }
  
  /**
   * Resets video detection state
   */
  function resetVideoDetection(): void {
    isVideoDetected = false;
    videoPlatform = null;
    estimatedDownloadTimeSeconds = 0;
    thumbnailPreviewUrl = null;
  }

  function setupDragAndDrop() {
    if (!dropZone) return;

    dropZone.addEventListener('dragover', (e: DragEvent) => {
      e.preventDefault();
      isDragging = true;
    });

    dropZone.addEventListener('dragleave', (e: DragEvent) => {
      e.preventDefault();
      isDragging = false;
    });

    dropZone.addEventListener('dragenter', (e: DragEvent) => {
      e.preventDefault();
    });

    dropZone.addEventListener('drop', (e: DragEvent) => {
      e.preventDefault();
      isDragging = false;

      if (e.dataTransfer) {
        const items = e.dataTransfer.items;

        for (let i = 0; i < items.length; i++) {
          if (items[i].kind === 'string' && items[i].type === 'text/uri-list') {
            items[i].getAsString((droppedUrl: string) => {
              url = droppedUrl;
            });
          } else if (items[i].kind === 'string' && items[i].type === 'text/plain') {
            items[i].getAsString((text: string) => {
              if (text.startsWith('http://') || text.startsWith('https://')) {
                url = text;
              } else {
                highlight = text;
              }
            });
          }
        }
      }
    });
  }

  function handlePaste(e: ClipboardEvent) {
    // Only handle paste if not focused in an input
    const activeElement = document.activeElement;
    if (activeElement && (activeElement.tagName === 'INPUT' || 
        activeElement.tagName === 'TEXTAREA')) {
      return;
    }

    const clipboardData = e.clipboardData;
    if (!clipboardData) return;
    
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

  function handleTagsUpdate(event: CustomEvent) {
    tags = event.detail.tags;
  }
  
  async function loadAISuggestions(urlToAnalyze: string) {
    if (!urlToAnalyze || isLoadingSuggestions) return;
    
    try {
      isLoadingSuggestions = true;
      suggestionsError = null;
      
      const suggestions = await getAISuggestions(urlToAnalyze);
      
      // Only update if URL hasn't changed
      if (url === urlToAnalyze) {
        // Set title if empty
        if (!title && suggestions.title) {
          title = suggestions.title;
        }
        
        // Set highlight/summary if empty
        if (!highlight && suggestions.summary) {
          highlight = suggestions.summary;
        }
        
        // Add suggested tags that aren't already present
        if (suggestions.tags && suggestions.tags.length > 0) {
          const newTags = suggestions.tags.filter(tag => !tags.includes(tag));
          tags = [...tags, ...newTags];
        }
      }
    } catch (err) {
      console.error('Failed to get AI suggestions:', err);
      // Don't show error to user, just silently fail and let them enter manually
      // This prevents the 500 error from breaking the UI
      suggestionsError = null;
    } finally {
      isLoadingSuggestions = false;
    }
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

      // Include video-specific options if a video is detected
      const captureData: {
        url?: string;
        title?: string;
        highlight?: string;
        tags?: string[];
        is_video?: boolean;
        video_platform?: string | null;
        video_quality?: string;
      } = {
        url,
        title,
        highlight,
        tags
      };
      
      // Add video-specific data if detected
      if (isVideoDetected) {
        captureData.is_video = true;
        captureData.video_platform = videoPlatform;
        captureData.video_quality = videoQuality;
      }

      await captureItem(captureData);

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
        resetVideoDetection();
        window.location.href = '/';
      }, 1000);
    } catch (err) {
      error = err instanceof Error ? err : new Error(String(err));
      message = error.message || 'Failed to capture. Please try again.';
      messageType = 'error';
    } finally {
      isSubmitting = false;
      if (progressInterval !== null) {
        clearInterval(progressInterval);
      }
      progress = 0;
    }
  }

  function startProgressIndicator() {
    progress = 0;
    if (progressInterval !== null) {
      clearInterval(progressInterval);
    }

    progressInterval = window.setInterval(() => {
      // Simulate progress, but slow down as we approach 90%
      if (progress < 90) {
        progress += (90 - progress) / 10;
      }
    }, 100);
  }

  // Keyboard shortcuts
  function handleKeydown(e: KeyboardEvent) {
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
        <div class="url-input-container">
          <input 
            type="text" 
            id="url" 
            bind:this={urlInput}
            bind:value={url} 
            placeholder="https://example.com" 
            disabled={isSubmitting}
          />
          {#if isLoadingSuggestions}
            <div class="ai-indicator loading">
              <Spinner size="small" />
              <span>AI analyzing...</span>
            </div>
          {:else if isVideoDetected}
            <div class="video-indicator">
              <Icon name="video" size="small" />
              <span>{videoPlatform} Video</span>
            </div>
          {/if}
        </div>

        {#if url && !isVideoDetected}
          <UrlPreview {url} />
        {/if}
        
        {#if isVideoDetected}
          <div class="video-info">
            <div class="video-platform">
              <strong>Platform:</strong> {videoPlatform}
            </div>
            <div class="video-download-time">
              <strong>Estimated download time:</strong> {formatTime(estimatedDownloadTimeSeconds)}
            </div>
            
            <div class="video-options">
              <label class="video-quality-label">
                <span>Video Quality:</span>
                <select bind:value={videoQuality} disabled={isSubmitting}>
                  <option value="standard">Standard</option>
                  <option value="high">High</option>
                </select>
              </label>
            </div>
          </div>
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
              <PremiumInteractions variant="click" intensity="subtle">
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
              </PremiumInteractions>
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
        <AnimatedButton 
          variant="primary" 
          size="large" 
          icon={isSubmitting ? null : "download"}
          loading={isSubmitting}
          disabled={isSubmitting}
          on:click={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
        >
          {#if isSubmitting}
            Capturing...
          {:else}
            Capture
          {/if}
        </AnimatedButton>
        
        <PremiumInteractions variant="click" intensity="subtle">
          <button 
            type="button" 
            class="secondary-button"
            on:click={() => window.history.back()}
            disabled={isSubmitting}
          >
            Cancel
          </button>
        </PremiumInteractions>
        
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
  
  .url-input-container {
    position: relative;
    display: flex;
    align-items: center;
  }
  
  .video-indicator {
    display: flex;
    align-items: center;
    margin-left: 10px;
    background-color: var(--accent);
    color: white;
    padding: 4px 8px;
    border-radius: var(--radius);
    font-size: 0.8rem;
  }
  
  .video-indicator :global(svg) {
    margin-right: 5px;
  }
  
  .ai-indicator {
    display: flex;
    align-items: center;
    margin-left: 10px;
    background-color: var(--success);
    color: white;
    padding: 4px 8px;
    border-radius: var(--radius);
    font-size: 0.8rem;
  }
  
  .ai-indicator.loading {
    background-color: var(--info);
  }
  
  .ai-indicator :global(svg) {
    margin-right: 5px;
  }
  
  .video-info {
    margin-top: 10px;
    padding: 12px;
    background-color: var(--bg-secondary);
    border-radius: var(--radius);
    border-left: 3px solid var(--accent);
  }
  
  .video-platform,
  .video-download-time {
    margin-bottom: 8px;
  }
  
  .video-options {
    margin-top: 12px;
  }
  
  .video-quality-label {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .video-quality-label select {
    padding: 6px 10px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background-color: var(--bg-primary);
    color: var(--text);
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
  
  .secondary-button {
    padding: 0.75rem 1.5rem;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0.5rem;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .secondary-button:hover {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.3);
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