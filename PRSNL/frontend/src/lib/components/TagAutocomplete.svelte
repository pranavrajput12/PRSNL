<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { getRecentTags } from '$lib/api';

  export let value = '';
  export let placeholder = 'Add tags...';
  export let disabled = false;

  const dispatch = createEventDispatcher();

  let inputElement;
  let tags = [];
  let suggestions = [];
  let activeSuggestion = -1;
  let showSuggestions = false;
  let isLoading = false;
  let error = null;

  onMount(async () => {
    await loadRecentTags();
  });

  async function loadRecentTags() {
    try {
      isLoading = true;
      const data = await getRecentTags();
      suggestions = Array.isArray(data) ? data : data.tags || [];
    } catch (err) {
      error = err;
      console.error('Failed to load tags:', err);
      // Set default suggestions on error to prevent breaking the component
      suggestions = ['tutorial', 'article', 'video', 'resource', 'tool'];
    } finally {
      isLoading = false;
    }
  }

  function handleInput() {
    const tagInput = value.trim();
    showSuggestions = tagInput.length > 0;

    if (tagInput) {
      // Filter suggestions based on input
      const filtered = suggestions.filter(
        (tag) =>
          typeof tag === 'string' &&
          tag.toLowerCase().includes(tagInput.toLowerCase()) &&
          !tags.includes(tag)
      );

      // Sort by relevance (starts with input first)
      filtered.sort((a, b) => {
        const aStartsWith =
          typeof a === 'string' && a.toLowerCase().startsWith(tagInput.toLowerCase());
        const bStartsWith =
          typeof b === 'string' && b.toLowerCase().startsWith(tagInput.toLowerCase());

        if (aStartsWith && !bStartsWith) return -1;
        if (!aStartsWith && bStartsWith) return 1;
        return 0;
      });

      suggestions = filtered.slice(0, 5); // Limit to 5 suggestions
      activeSuggestion = suggestions.length > 0 ? 0 : -1;
    } else {
      activeSuggestion = -1;
    }

    dispatch('input', { value });
  }

  function handleKeydown(event) {
    if (disabled) return;

    const tagInput = value.trim();

    if (event.key === 'Enter' && tagInput) {
      event.preventDefault();

      if (activeSuggestion >= 0 && suggestions[activeSuggestion]) {
        addTag(suggestions[activeSuggestion]);
      } else if (tagInput) {
        addTag(tagInput);
      }
    } else if (event.key === 'ArrowDown' && showSuggestions) {
      event.preventDefault();
      activeSuggestion = Math.min(activeSuggestion + 1, suggestions.length - 1);
    } else if (event.key === 'ArrowUp' && showSuggestions) {
      event.preventDefault();
      activeSuggestion = Math.max(activeSuggestion - 1, 0);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      showSuggestions = false;
    } else if (event.key === ',' && tagInput) {
      event.preventDefault();
      addTag(tagInput);
    }
  }

  function addTag(tag) {
    tag = tag.trim();
    if (tag && !tags.includes(tag)) {
      tags = [...tags, tag];
      value = '';
      showSuggestions = false;
      dispatch('tags', { tags });
    }
  }

  function removeTag(index) {
    tags = tags.filter((_, i) => i !== index);
    dispatch('tags', { tags });
  }

  function handleSuggestionClick(tag) {
    addTag(tag);
    inputElement.focus();
  }

  function handleBlur() {
    // Small delay to allow click events on suggestions
    setTimeout(() => {
      showSuggestions = false;
    }, 150);
  }
</script>

<div class="tag-autocomplete">
  <div class="tag-input-container">
    {#each tags as tag, i}
      <div class="tag">
        {tag}
        <button
          type="button"
          class="tag-remove"
          on:click={() => removeTag(i)}
          aria-label="Remove tag"
          {disabled}
        >
          ×
        </button>
      </div>
    {/each}

    <input
      bind:this={inputElement}
      bind:value
      on:input={handleInput}
      on:keydown={handleKeydown}
      on:blur={handleBlur}
      on:focus={() => handleInput()}
      placeholder={tags.length ? '' : placeholder}
      {disabled}
      class="tag-input"
    />
  </div>

  {#if showSuggestions && suggestions.length > 0}
    <div class="suggestions">
      {#each suggestions as suggestion, i}
        <button
          type="button"
          class="suggestion"
          class:active={i === activeSuggestion}
          on:click={() => handleSuggestionClick(suggestion)}
        >
          {suggestion}
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .tag-autocomplete {
    position: relative;
    width: 100%;
  }

  .tag-input-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.5rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--bg-input);
    min-height: 2.5rem;
    align-items: center;
    transition: border-color 0.2s ease;
  }

  .tag-input-container:focus-within {
    border-color: var(--accent);
  }

  .tag {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    background: var(--accent-muted);
    color: var(--accent);
    border-radius: var(--radius-sm);
    font-size: 0.875rem;
    animation: fadeIn 0.2s ease;
  }

  .tag-remove {
    background: none;
    border: none;
    color: var(--accent);
    cursor: pointer;
    font-size: 1rem;
    line-height: 1;
    padding: 0 0.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .tag-remove:hover {
    color: var(--text-primary);
  }

  .tag-input {
    flex: 1;
    min-width: 100px;
    border: none;
    background: transparent;
    color: var(--text-primary);
    font-size: 0.9375rem;
    outline: none;
    padding: 0.25rem 0;
  }

  .suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-top: 0.25rem;
    max-height: 200px;
    overflow-y: auto;
    z-index: 10;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    animation: fadeIn 0.2s ease;
  }

  .suggestion {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.5rem 0.75rem;
    background: none;
    border: none;
    color: var(--text-primary);
    cursor: pointer;
    transition: background 0.2s ease;
  }

  .suggestion:hover,
  .suggestion.active {
    background: var(--bg-hover);
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-5px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>
