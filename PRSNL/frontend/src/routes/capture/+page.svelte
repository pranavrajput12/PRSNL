<script lang="ts">
  import { onMount } from 'svelte';
  import { captureItem, getRecentTags } from '$lib/api';
  import { addNotification } from '$lib/stores/app';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  
  let url = '';
  let text = '';
  let tags = '';
  let isSubmitting = false;
  let message = '';
  let messageType: 'success' | 'error' | '' = '';
  let error: Error | null = null;
  let recentTags: string[] = [];
  let isLoadingTags = false;
  
  // Focus on URL input on mount
  let urlInput: HTMLInputElement;
  onMount(() => {
    urlInput?.focus();
    
    // Check for clipboard content
    navigator.clipboard.readText().then(content => {
      if (content && content.startsWith('http')) {
        url = content;
      }
    }).catch(() => {
      // Clipboard access denied
    });
    
    // Load recent tags for suggestions
    loadRecentTags();
  });
  
  async function loadRecentTags() {
    try {
      isLoadingTags = true;
      const response = await getRecentTags();
      recentTags = response.tags || [];
    } catch (err) {
      console.error('Failed to load tags:', err);
    } finally {
      isLoadingTags = false;
    }
  }
  
  async function handleSubmit() {
    if (!url && !text) {
      message = 'Please provide a URL or text to capture';
      messageType = 'error';
      return;
    }
    
    isSubmitting = true;
    message = '';
    error = null;
    
    try {
      const parsedTags = tags.split(',').map(t => t.trim()).filter(Boolean);
      
      const response = await captureItem({
        url: url || undefined,
        title: undefined, // The backend will extract title from URL if needed
        highlight: text || undefined,
        tags: parsedTags
      });
      
      message = 'Captured successfully!';
      messageType = 'success';
      
      // Add notification that will show in the main app
      addNotification({
        type: 'success',
        message: 'Item captured successfully',
        timeout: 3000
      });
      
      // Clear form
      url = '';
      text = '';
      tags = '';
      
      // Redirect after short delay
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
    } catch (err) {
      error = err as Error;
      message = err instanceof Error ? err.message : 'Failed to capture. Please try again.';
      messageType = 'error';
    } finally {
      isSubmitting = false;
    }
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
  <div class="capture-form">
    <h1>Quick Capture</h1>
    <p class="subtitle">Save a URL or text snippet to your vault</p>
    
    <form on:submit|preventDefault={handleSubmit}>
      <div class="form-group">
        <label for="url">URL</label>
        <input
          bind:this={urlInput}
          bind:value={url}
          type="url"
          id="url"
          placeholder="https://example.com/article"
          disabled={isSubmitting}
        />
        <div class="hint">Paste a URL to capture its content</div>
      </div>
      
      <div class="or-divider">OR</div>
      
      <div class="form-group">
        <label for="text">Text</label>
        <textarea
          bind:value={text}
          id="text"
          rows="6"
          placeholder="Paste or type any text you want to save..."
          disabled={isSubmitting}
        />
        <div class="hint">Any text, code snippet, or note</div>
      </div>
      
      <div class="form-group">
        <label for="tags">Tags</label>
        <input
          bind:value={tags}
          type="text"
          id="tags"
          placeholder="article, important, todo"
          disabled={isSubmitting}
        />
        <div class="hint">Comma-separated tags for organization</div>
        
        {#if recentTags.length > 0}
          <div class="recent-tags">
            <span class="recent-tags-label">Recent:</span>
            {#each recentTags as tag}
              <button 
                type="button" 
                class="tag-suggestion"
                on:click={() => {
                  const currentTags = tags.split(',').map(t => t.trim()).filter(Boolean);
                  if (!currentTags.includes(tag)) {
                    tags = currentTags.length > 0 
                      ? `${tags}, ${tag}` 
                      : tag;
                  }
                }}
              >
                {tag}
              </button>
            {/each}
          </div>
        {/if}
      </div>
      
      {#if error}
        <ErrorMessage 
          message="Failed to capture item" 
          details={error.message} 
          retry={handleSubmit} 
          dismiss={() => error = null} 
        />
      {:else if message}
        <div class="message {messageType}">
          {message}
        </div>
      {/if}
      
      <div class="actions">
        <button type="submit" class="primary" disabled={isSubmitting}>
          {#if isSubmitting}
            <Spinner size="small" />
            <span>Capturing...</span>
          {:else}
            <span>Capture</span>
            <span class="keyboard-hint">⌘↵</span>
          {/if}
        </button>
        <button type="button" on:click={() => window.location.href = '/'} disabled={isSubmitting}>
          Cancel
          <span class="keyboard-hint">ESC</span>
        </button>
      </div>
    </form>
  </div>
</div>

<style>
  .capture-form {
    max-width: 600px;
    margin: 2rem auto;
    padding: 2rem;
  }
  
  h1 {
    text-align: center;
    margin-bottom: 0.5rem;
  }
  
  .subtitle {
    text-align: center;
    color: var(--text-secondary);
    margin-bottom: 2rem;
  }
  
  form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  label {
    font-weight: 500;
    font-size: 0.875rem;
  }
  
  input, textarea {
    width: 100%;
    font-size: 1rem;
  }
  
  textarea {
    resize: vertical;
    min-height: 100px;
  }
  
  .hint {
    font-size: 0.75rem;
    color: var(--text-muted);
  }
  
  .or-divider {
    text-align: center;
    color: var(--text-muted);
    position: relative;
    margin: 0.5rem 0;
  }
  
  .or-divider::before,
  .or-divider::after {
    content: '';
    position: absolute;
    top: 50%;
    width: calc(50% - 2rem);
    height: 1px;
    background: var(--border);
  }
  
  .or-divider::before {
    left: 0;
  }
  
  .or-divider::after {
    right: 0;
  }
  
  .message {
    padding: 0.75rem;
    border-radius: var(--radius);
    font-size: 0.875rem;
  }
  
  .message.success {
    background: rgba(0, 200, 100, 0.1);
    color: rgb(0, 200, 100);
    border: 1px solid rgba(0, 200, 100, 0.3);
  }
  
  .message.error {
    background: rgba(255, 100, 100, 0.1);
    color: rgb(255, 100, 100);
    border: 1px solid rgba(255, 100, 100, 0.3);
  }
  
  .actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-top: 1rem;
  }
  
  button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  button.primary {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
  }
  
  button.primary:hover {
    background: var(--accent-hover);
    border-color: var(--accent-hover);
  }
  
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>