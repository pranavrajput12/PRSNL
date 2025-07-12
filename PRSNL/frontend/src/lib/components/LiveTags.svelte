<script lang="ts" type="module">
  /**
   * LiveTags component
   *
   * Displays and manages tags with real-time AI suggestions
   * Supports adding, removing, and filtering tags
   * Optimized for performance and accessibility
   * Integrated with WebSocket for real-time updates
   */
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { slide } from 'svelte/transition';
  import Icon from './Icon.svelte';
  import { websocketStore, connectionStatus, MessageType } from '$lib/stores/websocket';

  // Props with TypeScript types and default values
  export let tags: string[] = []; // Current tags
  export let suggestedTags: string[] = []; // AI suggested tags
  export let maxTags: number = 20; // Maximum number of tags
  export let maxTagLength: number = 30; // Maximum tag length
  export let placeholder: string = 'Add a tag...'; // Input placeholder
  export let size: 'small' | 'default' | 'large' = 'default'; // Component size
  export let showHeader: boolean = true; // Show header with title
  export let title: string = 'Tags'; // Header title
  export let loading: boolean = false; // Loading state
  export let connected: boolean = false; // WebSocket connection status
  export let errorMsg: string = ''; // Error message
  export let allowCustomTags: boolean = true; // Allow custom tags
  export let allowRemoval: boolean = true; // Allow tag removal
  export let maxVisibleTags: number = 15; // Max visible tags before "more" indicator
  export let itemId: string | null = null; // Optional item ID for direct WebSocket requests

  // Set up event dispatcher
  const dispatch = createEventDispatcher<{
    update: { tags: string[] };
    connectionChange: { connected: boolean };
  }>();
  let selectedSuggestionIndex = -1;
  let tagInputRef: HTMLInputElement;
  let tagListElement: HTMLDivElement;
  let showSuggestions = false;
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let newTagInput = '';
  let uniqueSuggestedTags: string[] = [];
  let filteredSuggestions: string[] = [];
  let wsConnected = false;
  let wsMessageHandler: ((event: CustomEvent) => void) | null = null;
  let connectionUnsubscribe: (() => void) | null = null;
  let wsLastUpdated = 0;
  let debounceMs = 300;

  // Compute visible tags based on maxVisibleTags
  $: visibleTags = tags.slice(0, maxVisibleTags);

  // Check for reduced motion preference
  let isReducedMotion = false;

  // Debounced filter function for input changes with memoization
  let lastInput = '';
  let lastTags: string[] = [];
  // Debounced and throttled filter function for input changes
  function updateFilteredSuggestions() {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      filteredSuggestions = uniqueSuggestedTags.filter(
        (tag) =>
          typeof tag === 'string' &&
          !tags.includes(tag) &&
          tag.toLowerCase().includes(newTagInput.toLowerCase())
      );
    }, debounceMs);
  }

  // Handle input changes
  function handleInput() {
    updateFilteredSuggestions();
    showSuggestions = newTagInput.length > 0;
    selectedSuggestionIndex = -1;
  }

  // WebSocket message handler
  function handleWebSocketMessage(event: CustomEvent) {
    const message = event.detail;
    wsLastUpdated = Date.now();

    if (message.type === MessageType.AI_RESPONSE && message.data.content) {
      try {
        const responseData = JSON.parse(message.data.content);

        // Handle tag suggestions
        if (responseData.tags && Array.isArray(responseData.tags) && itemId) {
          // Only update if this message is for our item
          if (responseData.item_id === itemId) {
            // Deduplicate tags
            const newSuggestions = [...new Set(responseData.tags)];

            // Only update if there are actual changes to avoid unnecessary renders
            if (JSON.stringify(newSuggestions) !== JSON.stringify(suggestedTags)) {
              suggestedTags = newSuggestions;
              updateFilteredSuggestions();
            }
          }
        }

        // Handle tag updates
        if (responseData.updated_tags && Array.isArray(responseData.updated_tags) && itemId) {
          // Only update if this message is for our item
          if (responseData.item_id === itemId) {
            // Only update if there are actual changes
            if (JSON.stringify(responseData.updated_tags) !== JSON.stringify(tags)) {
              tags = responseData.updated_tags;
              dispatch('update', { tags });
            }
          }
        }
      } catch (err) {
        console.error('Error parsing WebSocket tag response:', err);
      }
    }
  }

  // Set up WebSocket connection and listeners
  onMount(() => {
    // Create message handler
    wsMessageHandler = (event: CustomEvent) => handleWebSocketMessage(event);

    // Add event listener for WebSocket messages
    window.addEventListener('ws-message', wsMessageHandler);

    // Subscribe to connection status
    connectionUnsubscribe = connectionStatus.subscribe((state) => {
      const isConnected = state === 'connected';
      if (isConnected !== wsConnected) {
        wsConnected = isConnected;
        dispatch('connectionChange', { connected: wsConnected });
      }
    });

    // Initial filter of suggestions
    updateFilteredSuggestions();
  });

  // Clean up event listeners and subscriptions
  onDestroy(() => {
    if (wsMessageHandler) {
      window.removeEventListener('ws-message', wsMessageHandler);
    }

    if (connectionUnsubscribe) {
      connectionUnsubscribe();
    }

    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
  });

  // Add a tag with WebSocket integration
  function addTag(tag: string) {
    if (!tag || tags.includes(tag) || tags.length >= maxTags) return;

    // Optimistic UI update
    tags = [...tags, tag];
    dispatch('update', { tags });

    // If we have an itemId, we can directly update via WebSocket
    if (itemId && wsConnected) {
      websocketStore.sendMessage({
        type: MessageType.AI_REQUEST,
        data: {
          task: 'update_tags',
          content: JSON.stringify({ action: 'add', tag }),
          item_id: itemId,
        },
      });
    }
  }

  // Remove a tag with WebSocket integration
  function removeTag(tag: string) {
    if (!allowRemoval) return;

    // Optimistic UI update
    const previousTags = [...tags];
    tags = tags.filter((t) => t !== tag);
    dispatch('update', { tags });

    // If we have an itemId, we can directly update via WebSocket
    if (itemId && wsConnected) {
      websocketStore.sendMessage({
        type: MessageType.AI_REQUEST,
        data: {
          task: 'update_tags',
          content: JSON.stringify({ action: 'remove', tag }),
          item_id: itemId,
        },
      });
    }
  }

  // Handle input keydown events
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && newTagInput) {
      event.preventDefault();

      // If a suggestion is selected, add that
      if (selectedSuggestionIndex >= 0 && selectedSuggestionIndex < filteredSuggestions.length) {
        addTag(filteredSuggestions[selectedSuggestionIndex]);
      } else if (allowCustomTags) {
        // Otherwise add the input value if custom tags are allowed
        const trimmedTag = newTagInput.trim();
        if (trimmedTag.length > 0 && trimmedTag.length <= maxTagLength) {
          addTag(trimmedTag);
        }
      }

      newTagInput = '';
      selectedSuggestionIndex = -1;
      showSuggestions = false;
    } else if (event.key === 'Escape') {
      showSuggestions = false;
      selectedSuggestionIndex = -1;
    } else if (event.key === 'ArrowDown' && showSuggestions) {
      event.preventDefault();
      selectedSuggestionIndex = Math.min(
        selectedSuggestionIndex + 1,
        filteredSuggestions.length - 1
      );
    } else if (event.key === 'ArrowUp' && showSuggestions) {
      event.preventDefault();
      selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, -1);
    }
  }
</script>

<div class="live-tags-container {size}" aria-live="polite">
  <!-- Screen reader only announcement area -->
  <div class="sr-only" aria-live="assertive" id="tag-announcer">{srAnnouncement}</div>

  {#if showHeader}
    <div class="tags-header">
      <div class="header-title">
        <Icon name="tag" size="small" />
        <h3 id="tags-heading">{title}</h3>

        {#if loading}
          <div class="status-indicator loading" role="status" aria-label="Loading tags">
            <Icon name="loader" size="small" />
            <span class="sr-only">Loading tag suggestions</span>
          </div>
        {:else if connected}
          <div class="status-indicator connected" role="status" aria-label="Connected">
            <Icon name="check-circle" size="small" />
            <span class="sr-only">Connected to AI suggestions</span>
          </div>
        {/if}
      </div>

      {#if errorMsg}
        <div
          class="error-message"
          transition:fade|local={{ duration: isReducedMotion ? 0 : 200 }}
          role="alert"
          aria-live="assertive"
        >
          <Icon name="alert-circle" size="small" />
          <span>{errorMsg}</span>
        </div>
      {/if}
    </div>
  {/if}

  <div class="tags-container" aria-labelledby="tags-heading">
    {#if tags.length > 0}
      <div class="tags-list" role="list" bind:this={tagListElement}>
        {#each visibleTags as tag, i (tag)}
          <div
            class="tag"
            role="listitem"
            in:fly|local={{
              y: 10,
              duration: isReducedMotion ? 0 : 150,
              delay: isReducedMotion ? 0 : i * 30,
            }}
            out:fade|local={{ duration: isReducedMotion ? 0 : 100 }}
          >
            <span>{tag}</span>

            {#if allowRemoval}
              <button
                class="remove-tag"
                on:click={() => removeTag(tag)}
                aria-label="Remove tag {tag}"
              >
                <Icon name="x" size="small" />
              </button>
            {/if}
          </div>
        {/each}

        {#if tags.length > maxVisibleTags}
          <div class="tag more-tag" role="status" aria-live="polite">
            +{tags.length - maxVisibleTags} more
          </div>
        {/if}
      </div>
    {/if}

    <div class="tag-input-wrapper">
      <div class="tag-input-container">
        <div class="input-wrapper">
          <input
            type="text"
            bind:value={newTagInput}
            bind:this={tagInputRef}
            {placeholder}
            on:focus={() => (showSuggestions = true)}
            on:blur={() => setTimeout(() => (showSuggestions = false), 200)}
            on:keydown={handleKeydown}
            on:input={handleInput}
            aria-label="Add a tag"
            aria-controls="tag-suggestions"
            aria-autocomplete="list"
            aria-activedescendant={selectedSuggestionIndex >= 0
              ? `suggestion-${selectedSuggestionIndex}`
              : ''}
            autocomplete="off"
            role="combobox"
            aria-expanded={showSuggestions}
          />

          {#if newTagInput && allowCustomTags}
            <button
              class="add-tag-btn"
              on:click={() => addTag(newTagInput.trim())}
              aria-label="Add tag {newTagInput.trim()}"
              type="button"
            >
              <Icon name="plus" size="small" />
            </button>
          {/if}
        </div>

        {#if showSuggestions && filteredSuggestions.length > 0}
          <div
            class="suggestions"
            id="tag-suggestions"
            transition:fade|local={{ duration: isReducedMotion ? 0 : 150 }}
            role="listbox"
            aria-label="Tag suggestions"
          >
            {#each filteredSuggestions.slice(0, 10) as suggestion, i}
              <button
                type="button"
                class="suggestion-item"
                class:selected={i === selectedSuggestionIndex}
                on:click={() => addTag(suggestion)}
                on:mouseenter={() => (selectedSuggestionIndex = i)}
                role="option"
                aria-selected={i === selectedSuggestionIndex}
                id={`suggestion-${i}`}
              >
                <Icon name="tag" size="small" />
                <span>{suggestion}</span>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>

  {#if loading && !uniqueSuggestedTags.length}
    <!-- Skeleton loader for suggested tags -->
    <div class="suggested-tags skeleton-container" aria-hidden="true">
      <div class="suggested-header">
        <div class="skeleton-icon"></div>
        <div class="skeleton-text"></div>
      </div>

      <div class="suggestions-list">
        {#each Array(5) as _}
          <div class="skeleton-tag"></div>
        {/each}
      </div>
    </div>
  {:else if uniqueSuggestedTags.length > 0 && filteredSuggestions.length > 0}
    <div class="suggested-tags" transition:slide|local={{ duration: 300 }}>
      <div class="suggested-header" id="suggested-tags-heading">
        <Icon name="zap" size="small" />
        <span>AI Suggested Tags</span>
      </div>

      <div class="suggestions-list" role="list" aria-labelledby="suggested-tags-heading">
        {#each filteredSuggestions.slice(0, 10) as suggestion}
          <div role="listitem">
            <button
              class="suggestion-tag"
              on:click={() => addTag(suggestion)}
              aria-label="Add tag: {suggestion}"
              type="button"
            >
              <span>{suggestion}</span>
              <Icon name="plus" size="small" />
            </button>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .live-tags-container {
    width: 100%;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .live-tags-container.small {
    font-size: 0.75rem;
    padding: 0.5rem;
  }

  .live-tags-container.large {
    font-size: 1rem;
    padding: 1.25rem;
  }

  .tags-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .header-title h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-left: 0.5rem;
  }

  .status-indicator.loading {
    background-color: rgba(var(--info-rgb), 0.1);
    color: var(--info);
  }

  .status-indicator.loading :global(svg) {
    animation: spin 2s linear infinite;
  }

  .status-indicator.connected {
    background-color: rgba(var(--success-rgb), 0.1);
    color: var(--success);
  }

  .error-message {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--error);
    font-size: 0.875rem;
  }

  .tags-container {
    position: relative;
  }

  .tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
  }

  .tag {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    background: rgba(var(--accent-rgb), 0.1);
    color: var(--accent);
    padding: 0.25rem 0.5rem;
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .small .tag {
    padding: 0.15rem 0.35rem;
    font-size: 0.7rem;
  }

  .large .tag {
    padding: 0.35rem 0.75rem;
    font-size: 0.875rem;
  }

  .remove-tag {
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    color: inherit;
    opacity: 0.7;
  }

  .remove-tag:hover {
    opacity: 1;
  }

  .more-tag {
    background: rgba(var(--text-muted-rgb), 0.1);
    color: var(--text-muted);
  }

  .tag-input-wrapper {
    position: relative;
  }

  .tag-input-container {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    border: 1px dashed var(--border);
    padding: 0.5rem;
    border-radius: var(--radius);
    transition: all var(--transition-fast);
  }

  .tag-input-container:focus-within {
    border-color: var(--accent);
  }

  .tag-input-container input {
    background: none;
    border: none;
    outline: none;
    width: 100%;
    font-size: 0.875rem;
    color: var(--text-primary);
    padding: 0.25rem 0;
  }

  .small .tag-input-container input {
    font-size: 0.75rem;
  }

  .large .tag-input-container input {
    font-size: 1rem;
  }

  .suggestions {
    position: absolute;
    top: calc(100% + 0.25rem);
    left: 0;
    right: 0;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow-md);
    z-index: 10;
    max-height: 200px;
    overflow-y: auto;
  }

  .suggestion-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    width: 100%;
    background: none;
    border: none;
    text-align: left;
    cursor: pointer;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border);
    font-size: 0.875rem;
  }

  .suggestion-item:last-child {
    border-bottom: none;
  }

  .suggestion-item:hover,
  .suggestion-item.selected {
    background: var(--bg-hover);
  }

  .suggested-tags {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }

  .suggested-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
  }

  .suggestions-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .suggestion-tag {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(var(--text-muted-rgb), 0.1);
    color: var(--text-secondary);
    padding: 0.25rem 0.75rem;
    border-radius: 100px;
    font-size: 0.75rem;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .add-tag-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent);
    color: var(--text-on-accent);
    border: none;
    border-radius: 4px;
    width: 24px;
    height: 24px;
    cursor: pointer;
    transition: all var(--transition-fast);
    margin-left: 4px;
  }

  .add-tag-btn:hover {
    background: var(--accent-hover);
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .add-tag-btn:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }

  .suggestion-tag:hover {
    background: rgba(var(--accent-rgb), 0.1);
    color: var(--accent);
  }

  /* Skeleton loader styles */
  .skeleton-container {
    opacity: 0.7;
  }

  .skeleton-icon {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--bg-tertiary);
    animation: pulse 1.5s infinite ease-in-out;
  }

  .skeleton-text {
    width: 100px;
    height: 14px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    animation: pulse 1.5s infinite ease-in-out;
  }

  .skeleton-tag {
    width: 80px;
    height: 24px;
    background: var(--bg-tertiary);
    border-radius: 100px;
    animation: pulse 1.5s infinite ease-in-out;
  }

  .loading-progress {
    width: 100%;
    height: 2px;
    background: rgba(var(--accent-rgb), 0.1);
    border-radius: 2px;
    margin-top: 4px;
    overflow: hidden;
  }

  .loading-bar {
    height: 100%;
    width: 30%;
    background: var(--accent);
    border-radius: 2px;
    animation: loading-progress 1.5s infinite ease-in-out;
  }

  @keyframes pulse {
    0% {
      opacity: 0.6;
    }
    50% {
      opacity: 0.8;
    }
    100% {
      opacity: 0.6;
    }
  }

  @keyframes loading-progress {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(400%);
    }
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  /* Screen reader only class */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }

  /* Performance optimizations */
  .tag,
  .suggestion-tag,
  .tag-input-container {
    will-change: transform, opacity;
  }

  /* Reduce motion for users who prefer it */
  @media (prefers-reduced-motion: reduce) {
    .tag,
    .suggestions,
    .suggested-tags,
    .loading-bar {
      transition: none !important;
      animation: none !important;
    }

    .status-indicator.loading :global(svg) {
      animation: none !important;
    }

    .skeleton-icon,
    .skeleton-text,
    .skeleton-tag {
      animation: none !important;
      opacity: 0.7;
    }
  }
</style>
