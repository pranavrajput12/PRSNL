<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { goto } from '$app/navigation';
  import { jobPersistenceStore } from '$lib/stores/jobPersistence.ts';
  import RepoSelector from '$lib/components/codecortex/RepoSelector.svelte';
  import CodeMirrorAnalysis from '$lib/components/codecortex/CodeMirrorAnalysis.svelte';
  import PatternHistory from '$lib/components/codecortex/PatternHistory.svelte';
  import InsightsList from '$lib/components/codecortex/InsightsList.svelte';
  
  // Svelte 5 runes for state
  let selectedRepo = $state(null);
  let activeAnalysis = $state(null);
  let analyses = $state([]);
  let patterns = $state([]);
  let loading = $state(false);
  let activeTab = $state('analysis'); // analysis, patterns, insights
  
  onMount(async () => {
    // Load user's patterns
    await loadPatterns();
  });
  
  async function startAnalysis(depth = 'standard') {
    if (!selectedRepo) return;
    
    loading = true;
    try {
      const response = await api.post(`/code-cortex/codemirror/analyze/${selectedRepo.id}`, {
        repo_id: selectedRepo.id,
        analysis_depth: depth,
        include_patterns: true,
        include_insights: true
      });
      
      activeAnalysis = {
        job_id: response.data.job_id,
        status: 'pending',
        repo: selectedRepo
      };
      
      // Monitor job progress
      jobPersistenceStore.monitorJob(response.data.job_id);
      
      // Switch to analysis tab
      activeTab = 'analysis';
    } catch (error) {
      console.error('Failed to start analysis:', error);
    } finally {
      loading = false;
    }
  }
  
  async function loadAnalyses() {
    if (!selectedRepo) return;
    
    try {
      const response = await api.get(`/code-cortex/codemirror/analyses/${selectedRepo.id}`);
      analyses = response.data;
    } catch (error) {
      console.error('Failed to load analyses:', error);
    }
  }
  
  async function loadPatterns() {
    try {
      const response = await api.get('/code-cortex/codemirror/patterns');
      patterns = response.data;
    } catch (error) {
      console.error('Failed to load patterns:', error);
    }
  }
  
  // React to repository selection
  $effect(() => {
    if (selectedRepo) {
      loadAnalyses();
    }
  });
  
  // React to job updates
  $effect(() => {
    if (activeAnalysis?.job_id) {
      const job = $jobPersistenceStore.jobs.get(activeAnalysis.job_id);
      if (job) {
        activeAnalysis = { ...activeAnalysis, ...job };
        
        // Reload data when analysis completes
        if (job.status === 'completed') {
          loadAnalyses();
          loadPatterns();
        }
      }
    }
  });
  
  function handleSynthesizeSolution(problem) {
    // Navigate to synthesis view with problem context
    goto(`/code-cortex/codemirror/synthesize?problem=${encodeURIComponent(problem)}`);
  }
</script>

<div class="codemirror-container">
  <header class="codemirror-header">
    <div class="header-content">
      <div class="title-section">
        <h1>🔍 CodeMirror</h1>
        <p class="subtitle">AI-powered repository intelligence</p>
      </div>
      
      <div class="actions">
        <a href="/code-cortex" class="btn-secondary">
          ← Back to Code Cortex
        </a>
        {#if selectedRepo}
          <div class="analysis-actions">
            <button 
              onclick={() => startAnalysis('quick')}
              disabled={loading}
              class="btn-outline"
            >
              Quick Scan
            </button>
            <button 
              onclick={() => startAnalysis('standard')}
              disabled={loading}
              class="btn-outline"
            >
              Standard Analysis
            </button>
            <button 
              onclick={() => startAnalysis('deep')}
              disabled={loading}
              class="btn-primary"
            >
              Deep Analysis
            </button>
          </div>
        {/if}
      </div>
    </div>
  </header>
  
  <div class="repo-selector-wrapper">
    <RepoSelector bind:selected={selectedRepo} />
  </div>
  
  {#if selectedRepo || patterns.length > 0}
    <div class="tabs">
      <button 
        class="tab" 
        class:active={activeTab === 'analysis'}
        onclick={() => activeTab = 'analysis'}
      >
        Analysis
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'patterns'}
        onclick={() => activeTab = 'patterns'}
      >
        Patterns ({patterns.length})
      </button>
      <button 
        class="tab" 
        class:active={activeTab === 'insights'}
        onclick={() => activeTab = 'insights'}
        disabled={!selectedRepo}
      >
        Insights
      </button>
    </div>
    
    <div class="tab-content">
      {#if activeTab === 'analysis'}
        <CodeMirrorAnalysis 
          {selectedRepo}
          {activeAnalysis}
          {analyses}
          on:synthesize={e => handleSynthesizeSolution(e.detail)}
        />
      {:else if activeTab === 'patterns'}
        <PatternHistory 
          {patterns}
          on:synthesize={e => handleSynthesizeSolution(e.detail)}
        />
      {:else if activeTab === 'insights' && selectedRepo}
        <InsightsList 
          repoId={selectedRepo.id}
          analyses={analyses}
        />
      {/if}
    </div>
  {:else}
    <div class="empty-state">
      <div class="empty-icon">🔍</div>
      <h2>Welcome to CodeMirror</h2>
      <p>Select a repository to start analyzing your code with AI-powered intelligence.</p>
      <p class="hint">CodeMirror detects patterns, finds solutions from your history, and provides actionable insights.</p>
    </div>
  {/if}
</div>

<style>
  .codemirror-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .codemirror-header {
    background: var(--surface-2);
    margin: -2rem -2rem 2rem -2rem;
    padding: 2rem;
    border-bottom: 1px solid var(--border);
  }
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
  }
  
  .title-section h1 {
    margin: 0;
    font-size: 2rem;
    color: var(--text-primary);
  }
  
  .subtitle {
    margin: 0.25rem 0 0 0;
    color: var(--text-secondary);
    font-size: 1rem;
  }
  
  .actions {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .analysis-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .btn-primary, .btn-secondary, .btn-outline {
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    text-decoration: none;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-primary {
    background: var(--primary);
    color: white;
  }
  
  .btn-primary:hover:not(:disabled) {
    opacity: 0.9;
  }
  
  .btn-secondary {
    background: var(--surface-3);
    color: var(--text-primary);
  }
  
  .btn-secondary:hover {
    background: var(--surface-4);
  }
  
  .btn-outline {
    background: transparent;
    color: var(--text-primary);
    border: 1px solid var(--border);
  }
  
  .btn-outline:hover:not(:disabled) {
    background: var(--surface-3);
  }
  
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .repo-selector-wrapper {
    margin-bottom: 2rem;
  }
  
  .tabs {
    display: flex;
    gap: 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
  }
  
  .tab {
    padding: 0.75rem 1.5rem;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-secondary);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .tab:hover:not(:disabled) {
    color: var(--text-primary);
  }
  
  .tab.active {
    color: var(--primary);
    border-bottom-color: var(--primary);
  }
  
  .tab:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .tab-content {
    min-height: 400px;
  }
  
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-secondary);
  }
  
  .empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }
  
  .empty-state h2 {
    color: var(--text-primary);
    margin-bottom: 1rem;
  }
  
  .hint {
    margin-top: 1rem;
    font-size: 0.9rem;
    opacity: 0.8;
  }
  
  @media (max-width: 768px) {
    .header-content {
      flex-direction: column;
      align-items: flex-start;
    }
    
    .actions {
      width: 100%;
      flex-direction: column;
    }
    
    .analysis-actions {
      width: 100%;
      flex-direction: column;
    }
    
    .analysis-actions button {
      width: 100%;
    }
  }
</style>