<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { realtimeService, type AnalysisProgress } from '$lib/services/codemirror-realtime';
  import { fade, slide } from 'svelte/transition';
  
  let { analysisId = null, showAllActive = false }: { analysisId?: string | null; showAllActive?: boolean } = $props();
  
  let connectionState = $state({ connected: false, reconnectAttempts: 0 });
  let activeAnalyses = $state(new Map());
  let unsubscribers: (() => void)[] = [];
  
  // Subscribe to stores
  $effect(() => {
    const unsubConnection = realtimeService.connectionState.subscribe(state => {
      connectionState = state;
    });
    
    const unsubAnalyses = realtimeService.activeAnalyses.subscribe(analyses => {
      activeAnalyses = analyses;
    });
    
    return () => {
      unsubConnection();
      unsubAnalyses();
    };
  });
  
  onMount(() => {
    // Subscribe to specific analysis if provided
    if (analysisId) {
      realtimeService.subscribeToAnalysis(analysisId);
    }
    
    // Listen for real-time events
    unsubscribers.push(
      realtimeService.on('analysis_progress', (event) => {
        console.log('Progress update:', event);
      }),
      
      realtimeService.on('insight_added', (event) => {
        console.log('New insight:', event);
      })
    );
  });
  
  onDestroy(() => {
    unsubscribers.forEach(unsub => unsub());
  });
  
  function getProgressColor(progress: number): string {
    if (progress < 30) return 'bg-red-500';
    if (progress < 60) return 'bg-yellow-500';
    if (progress < 90) return 'bg-blue-500';
    return 'bg-green-500';
  }
  
  function getStageIcon(stage: string): string {
    const icons: Record<string, string> = {
      'initializing': '🔄',
      'scanning_files': '📂',
      'analyzing_structure': '🏗️',
      'detecting_patterns': '🔍',
      'generating_insights': '💡',
      'advanced_analysis': '🔬',
      'completed': '✅',
      'failed': '❌'
    };
    return icons[stage] || '⏳';
  }
  
  // Get analyses to display
  let displayAnalyses = $derived(
    showAllActive 
      ? Array.from(activeAnalyses.values())
      : analysisId && activeAnalyses.has(analysisId) 
        ? [activeAnalyses.get(analysisId)]
        : []
  );
</script>

<div class="realtime-progress">
  {#if !connectionState.connected}
    <div class="connection-status offline" transition:fade>
      <span class="status-icon">🔴</span>
      <span>Real-time sync offline</span>
      {#if connectionState.reconnectAttempts > 0}
        <span class="reconnect-info">
          (Reconnecting... Attempt {connectionState.reconnectAttempts})
        </span>
      {/if}
    </div>
  {:else if displayAnalyses.length === 0}
    <div class="no-analyses" transition:fade>
      <span class="icon">⏳</span>
      <span>No active analyses</span>
    </div>
  {/if}
  
  {#each displayAnalyses as analysis (analysis.analysis_id)}
    <div class="analysis-card" transition:slide>
      <div class="analysis-header">
        <span class="stage-icon">{getStageIcon(analysis.stage)}</span>
        <div class="analysis-info">
          <h4>Analysis {analysis.analysis_id.slice(0, 8)}</h4>
          <p class="stage">{analysis.stage.replace(/_/g, ' ')}</p>
        </div>
        <div class="progress-percentage">
          {analysis.progress}%
        </div>
      </div>
      
      <div class="progress-bar">
        <div 
          class="progress-fill {getProgressColor(analysis.progress)}"
          style="width: {analysis.progress}%"
        ></div>
      </div>
      
      {#if analysis.details}
        <div class="analysis-details">
          {#if analysis.details.repository}
            <div class="detail-item">
              <span class="label">Repository:</span>
              <span class="value">{analysis.details.repository}</span>
            </div>
          {/if}
          
          {#if analysis.details.files_processed}
            <div class="detail-item">
              <span class="label">Files:</span>
              <span class="value">{analysis.details.files_processed}</span>
            </div>
          {/if}
        </div>
      {/if}
      
      {#if analysis.insights && analysis.insights.length > 0}
        <div class="realtime-insights">
          <h5>Live Insights ({analysis.insights.length})</h5>
          <div class="insights-list">
            {#each analysis.insights.slice(-3) as insight}
              <div class="insight-item" transition:fade>
                <span class="insight-severity {insight.severity}">{insight.severity}</span>
                <span class="insight-title">{insight.title}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}
      
      {#if analysis.stage === 'completed'}
        <div class="completion-actions" transition:fade>
          <a href="/code-cortex/codemirror/analysis/{analysis.analysis_id}" class="view-results">
            View Full Results →
          </a>
        </div>
      {/if}
    </div>
  {/each}
</div>

<style>
  .realtime-progress {
    max-width: 600px;
    margin: 0 auto;
  }
  
  .connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    font-size: 0.875rem;
  }
  
  .connection-status.offline {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }
  
  .status-icon {
    font-size: 0.75rem;
  }
  
  .reconnect-info {
    margin-left: auto;
    font-size: 0.75rem;
    opacity: 0.8;
  }
  
  .no-analyses {
    text-align: center;
    padding: 2rem;
    color: rgba(255, 255, 255, 0.5);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }
  
  .no-analyses .icon {
    font-size: 2rem;
  }
  
  .analysis-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.75rem;
    padding: 1.5rem;
    margin-bottom: 1rem;
  }
  
  .analysis-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  .stage-icon {
    font-size: 1.5rem;
  }
  
  .analysis-info {
    flex: 1;
  }
  
  .analysis-info h4 {
    margin: 0;
    font-size: 1rem;
    color: white;
  }
  
  .stage {
    margin: 0;
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.7);
    text-transform: capitalize;
  }
  
  .progress-percentage {
    font-size: 1.25rem;
    font-weight: 600;
    color: #60a5fa;
  }
  
  .progress-bar {
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 1rem;
  }
  
  .progress-fill {
    height: 100%;
    transition: width 0.3s ease;
    border-radius: 4px;
  }
  
  .analysis-details {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 1rem;
    font-size: 0.875rem;
  }
  
  .detail-item {
    display: flex;
    gap: 0.5rem;
  }
  
  .label {
    color: rgba(255, 255, 255, 0.5);
  }
  
  .value {
    color: white;
    font-weight: 500;
  }
  
  .realtime-insights {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .realtime-insights h5 {
    margin: 0 0 0.75rem 0;
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .insights-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .insight-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 0.375rem;
    font-size: 0.875rem;
  }
  
  .insight-severity {
    padding: 0.125rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
  }
  
  .insight-severity.low {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
  }
  
  .insight-severity.medium {
    background: rgba(251, 191, 36, 0.2);
    color: #fbbf24;
  }
  
  .insight-severity.high {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }
  
  .insight-title {
    flex: 1;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .completion-actions {
    margin-top: 1rem;
    text-align: center;
  }
  
  .view-results {
    display: inline-block;
    padding: 0.5rem 1rem;
    background: rgba(96, 165, 250, 0.2);
    border: 1px solid rgba(96, 165, 250, 0.3);
    border-radius: 0.5rem;
    color: #60a5fa;
    text-decoration: none;
    font-size: 0.875rem;
    transition: all 0.2s;
  }
  
  .view-results:hover {
    background: rgba(96, 165, 250, 0.3);
    transform: translateY(-1px);
  }
</style>