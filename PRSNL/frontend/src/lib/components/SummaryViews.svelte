<!-- 
  SummaryViews.svelte
  Component for displaying AI-generated summaries with different view options
 -->
<script lang="ts" type="module">
  import { onMount } from 'svelte';
  import { aiApi } from '$lib/api';

  // Use native HTML elements instead of UI components due to import issues
  // Will fix UI component imports in a separate task

  export let itemId: string = '';
  export let summaries: {
    brief: string;
    detailed: string;
    key_points: string;
  } = {
    brief: '',
    detailed: '',
    key_points: '',
  };
  export let initialTab: 'brief' | 'detailed' | 'key_points' = 'brief';
  export let showDetailedTab: boolean = true;
  export let showKeyPointsTab: boolean = true;
  export let showActions: boolean = true;
  export let fullWidth: boolean = false;

  let loading = false;
  let error: string | null = null;
  let activeTab: 'brief' | 'detailed' | 'key_points' = initialTab;
  let copied = false;

  // Create valid tabs array based on which tabs are shown
  $: availableTabs = [
    'brief',
    ...(showDetailedTab ? ['detailed'] : []),
    ...(showKeyPointsTab ? ['key_points'] : []),
  ] as const;

  onMount(async () => {
    if (itemId && !summaries[activeTab]) {
      await generateSummary(activeTab);
    }
  });

  async function generateSummary(type: 'brief' | 'detailed' | 'key_points') {
    if (!itemId) return;

    loading = true;
    error = null;

    try {
      const result = await aiApi.summarization.item(itemId, type);
      if (result && typeof result === 'object' && 'summary' in result) {
        // Ensure we're always assigning a string value to fix TypeScript error
        const summaryText = typeof result.summary === 'string' ? result.summary : '';
        summaries[type] = summaryText;

        // If this is the first summary generated, automatically load the other types
        if (Object.values(summaries).filter(Boolean).length === 1) {
          loadAllSummaries();
        }
      }
    } catch (e) {
      console.error(`Failed to generate ${type} summary:`, e);
      error = e instanceof Error ? e.message : 'Failed to generate summary';
    } finally {
      loading = false;
    }
  }

  async function loadAllSummaries() {
    // Only load available tab types
    const types: Array<'brief' | 'detailed' | 'key_points'> = [];
    if (showDetailedTab) types.push('detailed');
    if (showKeyPointsTab) types.push('key_points');

    for (const type of types) {
      if (!summaries[type] && type !== activeTab) {
        try {
          const result = await aiApi.summarization.item(itemId, type);
          if (result && typeof result === 'object' && 'summary' in result) {
            // Ensure we're always assigning a string value to fix TypeScript error
            const summaryText = typeof result.summary === 'string' ? result.summary : '';
            summaries[type] = summaryText;
          }
        } catch (e) {
          console.error(`Failed to load ${type} summary:`, e);
        }
      }
    }
  }

  function copyToClipboard() {
    const text = summaries[activeTab];
    if (text) {
      navigator.clipboard.writeText(text);
      copied = true;
      setTimeout(() => {
        copied = false;
      }, 2000);
    }
  }

  function setActiveTab(tab: 'brief' | 'detailed' | 'key_points') {
    if (activeTab !== tab) {
      activeTab = tab;
      if (!summaries[activeTab] && itemId) {
        generateSummary(activeTab);
      }
    }
  }
</script>

<div class="summary-views" class:full-width={fullWidth}>
  <header>
    <h3>AI-Generated Summary</h3>
    {#if showActions}
      <div class="actions">
        <button
          class="btn btn-outline btn-sm"
          on:click={copyToClipboard}
          disabled={!summaries[activeTab]}
        >
          {copied ? '✓ Copied!' : 'Copy'}
        </button>
        <button
          class="btn btn-outline btn-sm"
          on:click={() => generateSummary(activeTab)}
          disabled={loading}
        >
          Regenerate
        </button>
      </div>
    {/if}
  </header>

  <div class="tabs-container">
    <div class="tab-list">
      {#each availableTabs as tab}
        <button
          class="tab-button"
          class:active={activeTab === tab}
          on:click={() => setActiveTab(tab)}
        >
          {tab === 'key_points' ? 'Key Points' : tab.charAt(0).toUpperCase() + tab.slice(1)}
        </button>
      {/each}
    </div>

    <div class="tab-content">
      {#if loading}
        <div class="loading-container">
          <div class="spinner"></div>
          <p>Generating {activeTab.replace('_', ' ')} summary...</p>
        </div>
      {:else if error}
        <div class="error">
          <p>{error}</p>
          <button class="btn btn-secondary" on:click={() => generateSummary(activeTab)}
            >Try Again</button
          >
        </div>
      {:else if summaries[activeTab]}
        <div class="summary-content">
          {#if activeTab === 'key_points'}
            <ul>
              {#each summaries[activeTab].split('\n').filter((line) => line.trim()) as point}
                <li>{point.replace(/^-\s*/, '')}</li>
              {/each}
            </ul>
          {:else}
            <p>{summaries[activeTab]}</p>
          {/if}
        </div>
      {:else}
        <div class="empty-state">
          <p>No {activeTab.replace('_', ' ')} summary available</p>
          <button class="btn btn-primary" on:click={() => generateSummary(activeTab)}
            >Generate</button
          >
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .summary-views {
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    padding: 1rem;
    background-color: var(--card-bg);
    max-width: 800px;
  }

  .summary-views.full-width {
    max-width: 100%;
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

  .actions {
    display: flex;
    gap: 0.5rem;
  }

  .tabs-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .tab-list {
    display: flex;
    border-bottom: 1px solid var(--border-color);
    gap: 0.25rem;
  }

  .tab-button {
    padding: 0.5rem 1rem;
    background: none;
    border: none;
    border-radius: var(--radius) var(--radius) 0 0;
    cursor: pointer;
    color: var(--text-color);
    opacity: 0.6;
    transition: all 0.2s ease;
  }

  .tab-button.active {
    background-color: var(--background-color);
    border: 1px solid var(--border-color);
    border-bottom: none;
    opacity: 1;
    font-weight: 500;
    color: var(--ai-primary);
  }

  .tab-button:hover:not(.active) {
    opacity: 0.8;
    background-color: var(--background-color-hover);
  }

  .tab-content {
    padding: 1rem 0;
  }

  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    min-height: 200px;
  }

  .spinner {
    width: 30px;
    height: 30px;
    border: 3px solid var(--border-color);
    border-top: 3px solid var(--ai-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .summary-content {
    padding: 1.5rem;
    background-color: var(--background-color);
    border-radius: var(--radius);
    border: 1px solid var(--border-color);
    line-height: 1.6;
    font-size: 0.95rem;
    max-height: 400px;
    overflow-y: auto;
  }

  .summary-content p {
    margin: 0 0 1rem 0;
  }

  .summary-content ul {
    margin: 0;
    padding-left: 1.5rem;
  }

  .summary-content li {
    margin-bottom: 0.5rem;
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
    min-height: 200px;
    justify-content: center;
  }

  /* Button styles to replace UI component */
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    padding: 0.5rem 1rem;
  }

  .btn-sm {
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
  }

  .btn-outline {
    border: 1px solid var(--border-color);
    background-color: transparent;
    color: var(--text-color);
  }

  .btn-outline:hover {
    background-color: var(--background-color-hover);
  }

  .btn-primary {
    background-color: var(--ai-primary);
    color: white;
    border: none;
  }

  .btn-primary:hover {
    opacity: 0.9;
  }

  .btn-secondary {
    background-color: var(--background-color);
    border: 1px solid var(--border-color);
    color: var(--text-color);
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Global AI color variables */
  :global(:root) {
    --ai-primary: #6366f1; /* Indigo for AI features */
    --ai-success: #10b981; /* Green for high confidence */
    --ai-warning: #f59e0b; /* Amber for medium confidence */
    --ai-error: #ef4444; /* Red for low confidence */
    --ai-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --background-color-hover: rgba(0, 0, 0, 0.05);
  }
</style>
