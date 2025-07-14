<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import AIProcessingIndicator from '../AIProcessingIndicator.svelte';
  
  interface Props {
    selectedRepo: any;
    activeAnalysis: any;
    analyses: any[];
  }
  
  let { selectedRepo, activeAnalysis, analyses = [] }: Props = $props();
  
  const dispatch = createEventDispatcher();
  
  // Calculate progress based on job data  
  let analysisProgress = $derived(activeAnalysis ? {
    progress: (activeAnalysis.progress_percentage || 0) / 100,
    currentStage: activeAnalysis.stage || 'analyzing',
    processingStartTime: activeAnalysis.created_at ? new Date(activeAnalysis.created_at).getTime() : Date.now()
  } : null);
  
  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleString();
  }
  
  function getScoreColor(score: number | null) {
    if (!score) return 'var(--text-secondary)';
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  }
  
  function handleSynthesize(problem: string) {
    dispatch('synthesize', problem);
  }
</script>

<div class="analysis-container">
  {#if activeAnalysis && activeAnalysis.status === 'processing'}
    <div class="active-analysis">
      <h3>Analyzing {selectedRepo?.name}</h3>
      <AIProcessingIndicator 
        progress={analysisProgress.progress}
        currentStage={analysisProgress.currentStage}
        processingStartTime={analysisProgress.processingStartTime}
      />
    </div>
  {/if}
  
  {#if analyses.length > 0}
    <div class="analyses-list">
      <h3>Analysis History</h3>
      
      {#each analyses as analysis}
        <div class="analysis-card">
          <div class="analysis-header">
            <div class="analysis-info">
              <span class="analysis-type">{analysis.analysis_depth}</span>
              <span class="analysis-date">{formatDate(analysis.created_at)}</span>
            </div>
            
            {#if analysis.job_status === 'processing'}
              <span class="status-badge processing">Processing...</span>
            {:else if analysis.job_status === 'completed'}
              <span class="status-badge completed">Completed</span>
            {:else if analysis.job_status === 'failed'}
              <span class="status-badge failed">Failed</span>
            {/if}
          </div>
          
          {#if analysis.job_status === 'completed'}
            <div class="analysis-scores">
              <div class="score-item">
                <span class="score-label">Security</span>
                <span 
                  class="score-value"
                  style="color: {getScoreColor(analysis.security_score)}"
                >
                  {analysis.security_score ? `${Math.round(analysis.security_score)}%` : 'N/A'}
                </span>
              </div>
              
              <div class="score-item">
                <span class="score-label">Performance</span>
                <span 
                  class="score-value"
                  style="color: {getScoreColor(analysis.performance_score)}"
                >
                  {analysis.performance_score ? `${Math.round(analysis.performance_score)}%` : 'N/A'}
                </span>
              </div>
              
              <div class="score-item">
                <span class="score-label">Quality</span>
                <span 
                  class="score-value"
                  style="color: {getScoreColor(analysis.quality_score)}"
                >
                  {analysis.quality_score ? `${Math.round(analysis.quality_score)}%` : 'N/A'}
                </span>
              </div>
            </div>
            
            {#if analysis.results?.summary}
              <div class="analysis-summary">
                <h4>Summary</h4>
                <p>{analysis.results.summary}</p>
              </div>
            {/if}
            
            <div class="analysis-actions">
              <a 
                href="/code-cortex/codemirror/insights/{analysis.id}"
                class="action-link"
              >
                View Insights →
              </a>
              
              <button 
                class="action-button"
                onclick={() => handleSynthesize(`Issues from ${selectedRepo.name} analysis`)}
              >
                Find Solutions
              </button>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {:else if selectedRepo && !activeAnalysis}
    <div class="no-analyses">
      <p>No analyses yet for {selectedRepo.name}</p>
      <p class="hint">Click one of the analysis buttons above to start scanning your repository.</p>
    </div>
  {/if}
  
  {#if !selectedRepo}
    <div class="no-repo">
      <p>Select a repository to view analysis results</p>
    </div>
  {/if}
</div>

<style>
  .analysis-container {
    min-height: 300px;
  }
  
  .active-analysis {
    margin-bottom: 2rem;
  }
  
  .active-analysis h3 {
    margin-bottom: 1rem;
    color: var(--text-primary);
  }
  
  .analyses-list h3 {
    margin-bottom: 1.5rem;
    color: var(--text-primary);
  }
  
  .analysis-card {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
  }
  
  .analysis-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .analysis-info {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .analysis-type {
    text-transform: capitalize;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .analysis-date {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
  
  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
  }
  
  .status-badge.processing {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }
  
  .status-badge.completed {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }
  
  .status-badge.failed {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }
  
  .analysis-scores {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .score-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .score-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
  
  .score-value {
    font-size: 1.5rem;
    font-weight: 600;
  }
  
  .analysis-summary {
    margin-bottom: 1.5rem;
  }
  
  .analysis-summary h4 {
    margin-bottom: 0.5rem;
    color: var(--text-primary);
    font-size: 1rem;
  }
  
  .analysis-summary p {
    color: var(--text-secondary);
    line-height: 1.5;
  }
  
  .analysis-actions {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  
  .action-link {
    color: var(--primary);
    text-decoration: none;
    font-weight: 500;
    transition: opacity 0.2s;
  }
  
  .action-link:hover {
    opacity: 0.8;
  }
  
  .action-button {
    padding: 0.5rem 1rem;
    background: var(--surface-3);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-primary);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .action-button:hover {
    background: var(--surface-4);
  }
  
  .no-analyses, .no-repo {
    text-align: center;
    padding: 3rem;
    color: var(--text-secondary);
  }
  
  .hint {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    opacity: 0.8;
  }
</style>