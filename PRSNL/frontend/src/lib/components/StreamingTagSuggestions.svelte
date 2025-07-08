<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, scale, fly } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import Icon from './Icon.svelte';
  import { createStreamingConnection, type StreamingWebSocket } from '$lib/utils/websocket';
  
  export let content: string = '';
  export let selectedTags: string[] = [];
  export let onTagSelect: (tag: string) => void = () => {};
  export let maxSuggestions: number = 8;
  export let autoSuggest: boolean = true;
  
  let suggestions: Array<{ tag: string; confidence: number }> = [];
  let isLoading = false;
  let error: string | null = null;
  let ws: StreamingWebSocket | null = null;
  let debounceTimer: NodeJS.Timeout | null = null;
  let animatingTags = new Set<string>();
  
  // Connect to WebSocket for streaming suggestions
  function connectWebSocket() {
    ws = createStreamingConnection('/api/ws/tags/stream', {
      onTyping: () => {
        isLoading = true;
        error = null;
      },
      onChunk: (data) => {
        // Handle streaming tag suggestions
        if (data && typeof data === 'object' && data.tag) {
          const newTag = { tag: data.tag, confidence: data.confidence || 0.5 };
          
          // Add with animation
          animatingTags.add(data.tag);
          suggestions = [...suggestions, newTag].slice(0, maxSuggestions);
          
          // Remove from animating set after animation completes
          setTimeout(() => {
            animatingTags.delete(data.tag);
            animatingTags = animatingTags;
          }, 300);
        }
      },
      onComplete: (data) => {
        isLoading = false;
        if (data.suggestions) {
          suggestions = data.suggestions.slice(0, maxSuggestions);
        }
      },
      onError: (errorMessage) => {
        isLoading = false;
        error = errorMessage;
        console.error('Tag suggestion error:', errorMessage);
      }
    });
    
    ws.connect();
  }
  
  // Request tag suggestions
  function requestSuggestions() {
    if (!content.trim() || !ws?.isConnected) return;
    
    // Clear existing suggestions with animation
    suggestions = [];
    error = null;
    
    ws.send({
      type: 'suggest_tags',
      content: content,
      existing_tags: selectedTags,
      max_suggestions: maxSuggestions
    });
  }
  
  // Debounced content change handler
  function handleContentChange() {
    if (!autoSuggest) return;
    
    if (debounceTimer) clearTimeout(debounceTimer);
    
    debounceTimer = setTimeout(() => {
      requestSuggestions();
    }, 500);
  }
  
  // Handle tag selection
  function selectTag(tag: string) {
    if (!selectedTags.includes(tag)) {
      onTagSelect(tag);
      
      // Remove from suggestions with animation
      suggestions = suggestions.filter(s => s.tag !== tag);
    }
  }
  
  // Manual refresh
  export function refresh() {
    requestSuggestions();
  }
  
  // Get confidence color
  function getConfidenceColor(confidence: number): string {
    if (confidence >= 0.8) return 'var(--color-success)';
    if (confidence >= 0.6) return 'var(--color-warning)';
    return 'var(--color-text-muted)';
  }
  
  // Get confidence label
  function getConfidenceLabel(confidence: number): string {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  }
  
  // React to content changes
  $: if (content && autoSuggest) {
    handleContentChange();
  }
  
  onMount(() => {
    connectWebSocket();
  });
  
  onDestroy(() => {
    if (debounceTimer) clearTimeout(debounceTimer);
    if (ws) ws.close();
  });
</script>

<div class="tag-suggestions">
  <div class="header">
    <h4>
      <Icon name="tag" size={16} />
      AI Tag Suggestions
    </h4>
    
    {#if !autoSuggest}
      <button 
        class="refresh-btn"
        on:click={refresh}
        disabled={isLoading}
      >
        <Icon name="refresh-cw" size={14} class={isLoading ? 'spinning' : ''} />
      </button>
    {/if}
  </div>
  
  {#if error}
    <div class="error" transition:fade={{ duration: 200 }}>
      <Icon name="alert-circle" size={14} />
      {error}
    </div>
  {/if}
  
  {#if isLoading && suggestions.length === 0}
    <div class="loading" transition:fade={{ duration: 200 }}>
      <div class="pulse-container">
        {#each Array(3) as _, i}
          <div 
            class="pulse-tag"
            style="animation-delay: {i * 0.1}s"
          ></div>
        {/each}
      </div>
      <span class="loading-text">Analyzing content...</span>
    </div>
  {/if}
  
  {#if suggestions.length > 0}
    <div class="suggestions-grid">
      {#each suggestions as suggestion (suggestion.tag)}
        <button
          class="tag-suggestion"
          class:animating={animatingTags.has(suggestion.tag)}
          on:click={() => selectTag(suggestion.tag)}
          disabled={selectedTags.includes(suggestion.tag)}
          animate:flip={{ duration: 300 }}
          in:scale={{ duration: 300, start: 0.8 }}
          out:fade={{ duration: 200 }}
        >
          <span class="tag-name">{suggestion.tag}</span>
          
          <div class="confidence-indicator">
            <div 
              class="confidence-bar"
              style="width: {suggestion.confidence * 100}%; background-color: {getConfidenceColor(suggestion.confidence)}"
            ></div>
            <span class="confidence-label">{getConfidenceLabel(suggestion.confidence)}</span>
          </div>
        </button>
      {/each}
    </div>
  {/if}
  
  {#if !isLoading && suggestions.length === 0 && !error}
    <div class="empty-state" transition:fade={{ duration: 200 }}>
      <Icon name="tag" size={24} />
      <p>Add some content to get tag suggestions</p>
    </div>
  {/if}
</div>

<style>
  .tag-suggestions {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 0.75rem;
    padding: 1rem;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .header h4 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--color-text);
    margin: 0;
  }
  
  .refresh-btn {
    padding: 0.25rem;
    background: none;
    border: none;
    color: var(--color-text-muted);
    cursor: pointer;
    border-radius: 0.25rem;
    transition: all 0.2s;
  }
  
  .refresh-btn:hover:not(:disabled) {
    background: var(--color-background);
    color: var(--color-primary);
  }
  
  .refresh-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  :global(.refresh-btn .spinning) {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .error {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--color-error-light);
    color: var(--color-error);
    border-radius: 0.5rem;
    font-size: 0.875rem;
  }
  
  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 1.5rem;
  }
  
  .pulse-container {
    display: flex;
    gap: 0.5rem;
  }
  
  .pulse-tag {
    width: 60px;
    height: 28px;
    background: var(--color-background);
    border-radius: 14px;
    animation: pulse 1.5s ease-in-out infinite;
  }
  
  @keyframes pulse {
    0%, 100% {
      opacity: 0.3;
      transform: scale(0.95);
    }
    50% {
      opacity: 0.6;
      transform: scale(1);
    }
  }
  
  .loading-text {
    font-size: 0.875rem;
    color: var(--color-text-muted);
  }
  
  .suggestions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.75rem;
  }
  
  .tag-suggestion {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
  }
  
  .tag-suggestion:hover:not(:disabled) {
    background: var(--color-primary-light);
    border-color: var(--color-primary);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(220, 20, 60, 0.15);
  }
  
  .tag-suggestion:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .tag-suggestion.animating {
    animation: tagAppear 0.3s ease-out;
  }
  
  @keyframes tagAppear {
    0% {
      transform: scale(0.8) translateY(10px);
      opacity: 0;
    }
    50% {
      transform: scale(1.05) translateY(-2px);
    }
    100% {
      transform: scale(1) translateY(0);
      opacity: 1;
    }
  }
  
  .tag-name {
    font-weight: 500;
    color: var(--color-text);
  }
  
  .confidence-indicator {
    position: relative;
    height: 4px;
    background: var(--color-border);
    border-radius: 2px;
    overflow: hidden;
  }
  
  .confidence-bar {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    transition: width 0.5s ease;
    border-radius: 2px;
  }
  
  .confidence-label {
    position: absolute;
    top: -16px;
    right: 0;
    font-size: 0.625rem;
    text-transform: uppercase;
    color: var(--color-text-muted);
    opacity: 0;
    transition: opacity 0.2s;
  }
  
  .tag-suggestion:hover .confidence-label {
    opacity: 1;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 2rem;
    color: var(--color-text-muted);
    text-align: center;
  }
  
  .empty-state p {
    font-size: 0.875rem;
    margin: 0;
  }
  
  /* Dark mode adjustments */
  :global(.dark) .tag-suggestion {
    background: var(--color-background);
  }
  
  :global(.dark) .tag-suggestion:hover:not(:disabled) {
    background: var(--color-primary-dark);
  }
  
  /* Mobile responsive */
  @media (max-width: 640px) {
    .suggestions-grid {
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    }
  }
</style>