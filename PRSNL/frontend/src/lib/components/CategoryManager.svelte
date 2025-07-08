<!-- 
  CategoryManager.svelte
  Component for displaying and managing AI-suggested categories with confidence scores
 -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { aiApi } from '$lib/api';
  import { Button } from '$lib/components/ui/button';
  import { ProgressBar } from '$lib/components/ui/progress-bar';
  import { Badge } from '$lib/components/ui/badge';
  import { Spinner } from '$lib/components/ui/spinner';
  
  export let itemId: string;
  export let currentCategory: string = '';
  export let onCategoryUpdated: (category: string) => void = () => {};
  
  let loading = false;
  let suggestion: {
    category: string;
    confidence: number;
    alternatives: Array<{category: string; confidence: number}>;
  } | null = null;
  let error: string | null = null;
  let customCategory = '';
  let showCustomInput = false;
  
  $: confidenceColor = suggestion?.confidence ? 
    suggestion.confidence > 0.8 ? 'var(--ai-success)' : 
    suggestion.confidence > 0.5 ? 'var(--ai-warning)' : 
    'var(--ai-error)' : 'var(--ai-primary)';
  
  onMount(async () => {
    if (itemId) {
      await getSuggestion();
    }
  });
  
  async function getSuggestion() {
    loading = true;
    error = null;
    
    try {
      const response = await aiApi.categorize.single(itemId);
      suggestion = response;
      if (suggestion && !currentCategory) {
        currentCategory = suggestion.category;
      }
    } catch (e) {
      console.error('Failed to get category suggestion:', e);
      error = e instanceof Error ? e.message : 'Failed to get category suggestion';
    } finally {
      loading = false;
    }
  }
  
  function acceptSuggestion() {
    if (suggestion) {
      currentCategory = suggestion.category;
      onCategoryUpdated(currentCategory);
    }
  }
  
  function selectAlternative(category: string) {
    currentCategory = category;
    onCategoryUpdated(currentCategory);
  }
  
  function saveCustomCategory() {
    if (customCategory.trim()) {
      currentCategory = customCategory.trim();
      onCategoryUpdated(currentCategory);
      showCustomInput = false;
    }
  }
</script>

<div class="category-manager">
  <header>
    <h3>Category Manager</h3>
    {#if currentCategory}
      <Badge style="background-color: var(--ai-primary);">{currentCategory}</Badge>
    {/if}
  </header>

  {#if loading}
    <div class="loading-container">
      <Spinner size="medium" />
      <p>Processing with AI...</p>
    </div>
  {:else if error}
    <div class="error">
      <p>{error}</p>
      <Button variant="secondary" on:click={getSuggestion}>Try Again</Button>
    </div>
  {:else if suggestion}
    <div class="suggestion">
      <div class="confidence-section">
        <div class="confidence-header">
          <h4>Suggested Category</h4>
          <span class="confidence-score" style="color: {confidenceColor}">
            {Math.round(suggestion.confidence * 100)}%
          </span>
        </div>
        <div class="confidence-bar" style="--confidence: {suggestion.confidence * 100}%">
          <div class="confidence-fill" style="width: {suggestion.confidence * 100}%; background-color: {confidenceColor}"></div>
        </div>
        <div class="suggestion-category">
          <strong>{suggestion.category}</strong>
        </div>
      </div>
      
      {#if suggestion.alternatives && suggestion.alternatives.length > 0}
        <div class="alternatives">
          <h4>Alternative Categories</h4>
          <div class="alternative-list">
            {#each suggestion.alternatives as alt}
              <div class="alternative-item" on:click={() => selectAlternative(alt.category)}>
                <span>{alt.category}</span>
                <div class="alt-confidence" 
                     style="width: {alt.confidence * 80}px; background-color: var(--ai-primary);">
                  {Math.round(alt.confidence * 100)}%
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
      
      <div class="actions">
        <Button variant="primary" on:click={acceptSuggestion}>Accept Suggestion</Button>
        <Button variant="outline" on:click={() => showCustomInput = !showCustomInput}>
          {showCustomInput ? 'Cancel' : 'Custom Category'}
        </Button>
      </div>
      
      {#if showCustomInput}
        <div class="custom-input">
          <input type="text" bind:value={customCategory} placeholder="Enter custom category" />
          <Button variant="secondary" on:click={saveCustomCategory}>Save</Button>
        </div>
      {/if}
    </div>
  {:else}
    <div class="empty-state">
      <p>No category suggestions available yet</p>
      <Button variant="primary" on:click={getSuggestion}>Generate Suggestions</Button>
    </div>
  {/if}
</div>

<style>
  .category-manager {
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    padding: 1rem;
    background-color: var(--card-bg);
    max-width: 500px;
  }
  
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  h3 {
    margin: 0;
    color: var(--text-color);
  }
  
  h4 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: var(--text-color-lighter);
  }
  
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }
  
  .confidence-section {
    margin-bottom: 1.5rem;
  }
  
  .confidence-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .confidence-score {
    font-weight: bold;
    font-size: 1.2rem;
  }
  
  .confidence-bar {
    height: 8px;
    background-color: var(--background-color);
    border-radius: 4px;
    overflow: hidden;
    margin: 0.5rem 0;
  }
  
  .confidence-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
  }
  
  .suggestion-category {
    font-size: 1.1rem;
    margin-top: 0.5rem;
  }
  
  .alternatives {
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
  }
  
  .alternative-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .alternative-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    border-radius: var(--radius-sm);
    background-color: var(--background-color);
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .alternative-item:hover {
    background-color: var(--hover-color);
  }
  
  .alt-confidence {
    height: 20px;
    min-width: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.8rem;
    font-weight: bold;
    transition: width 0.3s ease;
  }
  
  .actions {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
  }
  
  .custom-input {
    margin-top: 1rem;
    display: flex;
    gap: 0.5rem;
  }
  
  .custom-input input {
    flex-grow: 1;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    background-color: var(--background-color);
    color: var(--text-color);
  }
  
  .error {
    padding: 1rem;
    border-left: 4px solid var(--ai-error);
    background-color: var(--background-color);
    margin: 1rem 0;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 2rem;
    text-align: center;
  }
  
  :global(:root) {
    --ai-primary: #6366f1;      /* Indigo for AI features */
    --ai-success: #10b981;      /* Green for high confidence */
    --ai-warning: #f59e0b;      /* Amber for medium confidence */
    --ai-error: #ef4444;        /* Red for low confidence */
    --ai-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
</style>
