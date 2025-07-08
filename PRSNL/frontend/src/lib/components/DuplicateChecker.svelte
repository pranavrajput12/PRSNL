<!-- 
  DuplicateChecker.svelte
  Component for checking and managing duplicate content with similarity scores
 -->
<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { aiApi } from '$lib/api';
  import { Button } from '$lib/components/ui/button';
  import { Spinner } from '$lib/components/ui/spinner';
  import type { Item } from '$lib/types/api';
  
  export let url: string = '';
  export let title: string = '';
  export let content: string = '';
  export let checkOnMount: boolean = true;
  export let autoCheck: boolean = false;
  
  let loading = false;
  let duplicates: Array<{
    id: string;
    title: string;
    url: string;
    similarity: number;
    created_at?: string;
    createdAt?: string;
    summary?: string;
  }> = [];
  let error: string | null = null;
  let selectedDuplicate: string | null = null;
  let compareMode = false;
  let debounceTimer: NodeJS.Timeout;
  
  const dispatch = createEventDispatcher<{
    duplicatesFound: { duplicates: typeof duplicates };
    merge: { keepId: string, duplicateIds: string[] };
  }>();
  
  $: if (autoCheck && (url || title) && !loading) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      checkDuplicates();
    }, 500);
  }
  
  onMount(async () => {
    if (checkOnMount && url && title) {
      await checkDuplicates();
    }
  });
  
  async function checkDuplicates() {
    if (!url && !title) return;
    
    loading = true;
    error = null;
    
    try {
      const response = await aiApi.duplicates.check(url, title, content);
      duplicates = response.duplicates || [];
      
      if (duplicates.length > 0) {
        dispatch('duplicatesFound', { duplicates });
      }
    } catch (e) {
      console.error('Failed to check duplicates:', e);
      error = e instanceof Error ? e.message : 'Failed to check for duplicates';
    } finally {
      loading = false;
    }
  }
  
  function toggleCompareMode(id: string) {
    if (selectedDuplicate === id) {
      selectedDuplicate = null;
      compareMode = false;
    } else {
      selectedDuplicate = id;
      compareMode = true;
    }
  }
  
  function handleMerge(keepId: string, duplicateId: string) {
    dispatch('merge', { keepId, duplicateIds: [duplicateId] });
  }
  
  function getSimilarityColor(score: number): string {
    if (score >= 0.9) return 'var(--ai-error)';
    if (score >= 0.7) return 'var(--ai-warning)';
    return 'var(--ai-success)';
  }
  
  function formatDate(dateString: string | undefined): string {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  }
</script>

<div class="duplicate-checker">
  <header>
    <h3>Duplicate Checker</h3>
    {#if !autoCheck}
      <Button variant="secondary" on:click={checkDuplicates} disabled={loading}>Check Now</Button>
    {/if}
  </header>

  {#if loading}
    <div class="loading-container">
      <Spinner size="medium" />
      <p>Checking for duplicates...</p>
    </div>
  {:else if error}
    <div class="error">
      <p>{error}</p>
      <Button variant="secondary" on:click={checkDuplicates}>Try Again</Button>
    </div>
  {:else if duplicates.length > 0}
    <div class="duplicates-found">
      <p class="warning">⚠️ {duplicates.length} potential {duplicates.length === 1 ? 'duplicate' : 'duplicates'} found</p>
      
      <div class="duplicate-list">
        {#each duplicates as dup}
          <div class="duplicate-item">
            <div class="duplicate-header">
              <div class="duplicate-title">
                <h4>{dup.title}</h4>
                <span class="date">{formatDate(dup.created_at || dup.createdAt)}</span>
              </div>
              <div class="similarity-badge" 
                   style="background-color: {getSimilarityColor(dup.similarity)}">
                {Math.round(dup.similarity * 100)}%
              </div>
            </div>
            
            <div class="duplicate-content">
              <div class="url">{dup.url}</div>
              {#if dup.summary}
                <div class="summary">{dup.summary}</div>
              {/if}
            </div>
            
            <div class="duplicate-actions">
              <Button variant="outline" size="sm" on:click={() => toggleCompareMode(dup.id)}>
                {selectedDuplicate === dup.id ? 'Hide Comparison' : 'Compare'}
              </Button>
              <Button variant="secondary" size="sm" on:click={() => handleMerge(dup.id, url)}>
                Keep This Version
              </Button>
              <Button variant="primary" size="sm" on:click={() => handleMerge(url, dup.id)}>
                Keep My Version
              </Button>
            </div>
            
            {#if selectedDuplicate === dup.id && compareMode}
              <div class="comparison-view">
                <div class="comparison-column">
                  <h5>Existing Item</h5>
                  <div class="comparison-content">
                    <h6>{dup.title}</h6>
                    <div class="url">{dup.url}</div>
                    {#if dup.summary}
                      <div class="summary">{dup.summary}</div>
                    {/if}
                  </div>
                </div>
                <div class="comparison-divider"></div>
                <div class="comparison-column">
                  <h5>New Item</h5>
                  <div class="comparison-content">
                    <h6>{title}</h6>
                    <div class="url">{url}</div>
                    {#if content}
                      <div class="summary">{content.substring(0, 200)}...</div>
                    {/if}
                  </div>
                </div>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {:else if !autoCheck}
    <div class="no-duplicates">
      <p>✅ No duplicates found</p>
    </div>
  {/if}
</div>

<style>
  .duplicate-checker {
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    padding: 1rem;
    background-color: var(--card-bg);
    max-width: 800px;
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
    margin: 0;
    font-size: 1rem;
  }
  
  h5 {
    margin: 0 0 0.5rem 0;
    font-size: 0.9rem;
    color: var(--text-color-lighter);
  }
  
  h6 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
  }
  
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }
  
  .warning {
    color: var(--ai-warning);
    font-weight: 500;
    margin: 0 0 1rem 0;
  }
  
  .duplicate-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .duplicate-item {
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    padding: 1rem;
    background-color: var(--background-color);
  }
  
  .duplicate-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
  }
  
  .duplicate-title {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .date {
    font-size: 0.8rem;
    color: var(--text-color-lighter);
  }
  
  .similarity-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 1rem;
    color: white;
    font-size: 0.8rem;
    font-weight: bold;
    min-width: 3rem;
    text-align: center;
  }
  
  .duplicate-content {
    margin-bottom: 1rem;
  }
  
  .url {
    font-size: 0.85rem;
    color: var(--text-color-lighter);
    margin-bottom: 0.5rem;
    word-break: break-all;
  }
  
  .summary {
    font-size: 0.9rem;
    color: var(--text-color);
    line-height: 1.4;
  }
  
  .duplicate-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
  }
  
  .comparison-view {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px dashed var(--border-color);
    display: flex;
    gap: 1rem;
  }
  
  .comparison-column {
    flex: 1;
  }
  
  .comparison-content {
    padding: 0.75rem;
    background-color: var(--background-color-darker);
    border-radius: var(--radius);
    border: 1px solid var(--border-color);
  }
  
  .comparison-divider {
    width: 1px;
    background-color: var(--border-color);
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
  
  .no-duplicates {
    display: flex;
    justify-content: center;
    padding: 1.5rem;
  }
  
  :global(:root) {
    --ai-primary: #6366f1;      /* Indigo for AI features */
    --ai-success: #10b981;      /* Green for high confidence */
    --ai-warning: #f59e0b;      /* Amber for medium confidence */
    --ai-error: #ef4444;        /* Red for low confidence */
    --ai-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
</style>
