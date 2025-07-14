<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  interface Props {
    patterns: any[];
  }
  
  let { patterns = [] }: Props = $props();
  
  const dispatch = createEventDispatcher();
  
  let selectedType = $state('all');
  let searchQuery = $state('');
  
  // Filter patterns based on type and search
  const filteredPatterns = $derived(patterns.filter(pattern => {
    const matchesType = selectedType === 'all' || pattern.pattern_type === selectedType;
    const matchesSearch = !searchQuery || 
      pattern.pattern_signature.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (pattern.description && pattern.description.toLowerCase().includes(searchQuery.toLowerCase()));
    
    return matchesType && matchesSearch;
  }));
  
  // Get unique pattern types
  const patternTypes = $derived(['all', ...new Set(patterns.map(p => p.pattern_type).filter(Boolean))]);
  
  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString();
  }
  
  function getPatternIcon(type: string) {
    const icons = {
      'authentication': '🔐',
      'api_call': '🌐',
      'error_handling': '⚠️',
      'data_processing': '📊',
      'ui_pattern': '🎨',
      'testing': '🧪',
      'configuration': '⚙️',
      'architecture': '🏗️',
      'other': '📝'
    };
    return icons[type] || '📝';
  }
  
  function handleSynthesize(pattern: any) {
    dispatch('synthesize', pattern.pattern_signature);
  }
</script>

<div class="pattern-history">
  <div class="pattern-controls">
    <div class="search-box">
      <input 
        type="text"
        placeholder="Search patterns..."
        bind:value={searchQuery}
        class="search-input"
      />
    </div>
    
    <div class="type-filters">
      {#each patternTypes as type}
        <button 
          class="type-filter"
          class:active={selectedType === type}
          onclick={() => selectedType = type}
        >
          {type === 'all' ? 'All' : type.replace('_', ' ')}
          {#if type === 'all'}
            ({patterns.length})
          {:else}
            ({patterns.filter(p => p.pattern_type === type).length})
          {/if}
        </button>
      {/each}
    </div>
  </div>
  
  {#if filteredPatterns.length > 0}
    <div class="patterns-grid">
      {#each filteredPatterns as pattern}
        <div class="pattern-card">
          <div class="pattern-header">
            <span class="pattern-icon">{getPatternIcon(pattern.pattern_type)}</span>
            <div class="pattern-meta">
              <span class="pattern-type">{pattern.pattern_type?.replace('_', ' ')}</span>
              <span class="pattern-occurrences">{pattern.occurrence_count} occurrences</span>
            </div>
          </div>
          
          <h4 class="pattern-signature">{pattern.pattern_signature}</h4>
          
          {#if pattern.description}
            <p class="pattern-description">{pattern.description}</p>
          {/if}
          
          <div class="pattern-footer">
            <span class="last-seen">Last seen: {formatDate(pattern.last_seen_at)}</span>
            
            <div class="pattern-actions">
              {#if pattern.solutions && pattern.solutions.length > 0}
                <span class="solution-count">
                  💡 {pattern.solutions.length} solution{pattern.solutions.length !== 1 ? 's' : ''}
                </span>
              {/if}
              
              <button 
                class="synthesize-btn"
                onclick={() => handleSynthesize(pattern)}
                title="Find solutions for this pattern"
              >
                Find Solutions
              </button>
            </div>
          </div>
          
          {#if pattern.confidence}
            <div 
              class="confidence-bar"
              style="width: {pattern.confidence * 100}%"
              title="AI confidence: {Math.round(pattern.confidence * 100)}%"
            ></div>
          {/if}
        </div>
      {/each}
    </div>
  {:else}
    <div class="no-patterns">
      {#if searchQuery || selectedType !== 'all'}
        <p>No patterns found matching your filters.</p>
      {:else}
        <p>No patterns detected yet.</p>
        <p class="hint">Patterns will appear here as you analyze more repositories.</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .pattern-history {
    min-height: 400px;
  }
  
  .pattern-controls {
    margin-bottom: 2rem;
  }
  
  .search-box {
    margin-bottom: 1rem;
  }
  
  .search-input {
    width: 100%;
    padding: 0.75rem;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 1rem;
  }
  
  .search-input::placeholder {
    color: var(--text-secondary);
  }
  
  .type-filters {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .type-filter {
    padding: 0.5rem 1rem;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 20px;
    color: var(--text-secondary);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: capitalize;
  }
  
  .type-filter:hover {
    background: var(--surface-3);
  }
  
  .type-filter.active {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
  }
  
  .patterns-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }
  
  .pattern-card {
    position: relative;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    transition: all 0.2s;
  }
  
  .pattern-card:hover {
    border-color: var(--primary);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  .pattern-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  .pattern-icon {
    font-size: 2rem;
  }
  
  .pattern-meta {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .pattern-type {
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-transform: capitalize;
  }
  
  .pattern-occurrences {
    font-size: 0.75rem;
    color: var(--text-secondary);
    opacity: 0.8;
  }
  
  .pattern-signature {
    margin: 0 0 0.75rem 0;
    font-size: 1.1rem;
    color: var(--text-primary);
    word-break: break-word;
  }
  
  .pattern-description {
    margin: 0 0 1rem 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
    line-height: 1.4;
  }
  
  .pattern-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .last-seen {
    font-size: 0.75rem;
    color: var(--text-secondary);
    opacity: 0.7;
  }
  
  .pattern-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .solution-count {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
  
  .synthesize-btn {
    padding: 0.375rem 0.75rem;
    background: var(--surface-3);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text-primary);
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .synthesize-btn:hover {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
  }
  
  .confidence-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    background: var(--primary);
    border-radius: 0 0 0 8px;
    opacity: 0.5;
    transition: width 0.3s ease;
  }
  
  .no-patterns {
    text-align: center;
    padding: 3rem;
    color: var(--text-secondary);
  }
  
  .hint {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    opacity: 0.8;
  }
  
  @media (max-width: 768px) {
    .patterns-grid {
      grid-template-columns: 1fr;
    }
  }
</style>