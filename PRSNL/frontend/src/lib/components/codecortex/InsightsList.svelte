<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  
  interface Props {
    repoId: string;
    analyses: any[];
  }
  
  let { repoId, analyses = [] }: Props = $props();
  
  let insights = $state([]);
  let loading = $state(false);
  let selectedAnalysis = $state('all');
  let selectedType = $state('all');
  let selectedStatus = $state('open');
  
  // Get completed analyses
  const completedAnalyses = $derived(analyses.filter(a => a.job_status === 'completed'));
  
  // Filter insights
  const filteredInsights = $derived(insights.filter(insight => {
    const matchesAnalysis = selectedAnalysis === 'all' || insight.analysis_id === selectedAnalysis;
    const matchesType = selectedType === 'all' || insight.insight_type === selectedType;
    const matchesStatus = insight.status === selectedStatus;
    
    return matchesAnalysis && matchesType && matchesStatus;
  }));
  
  // Get unique insight types
  const insightTypes = $derived(['all', ...new Set(insights.map(i => i.insight_type))]);
  
  onMount(() => {
    if (completedAnalyses.length > 0) {
      loadInsights();
    }
  });
  
  async function loadInsights() {
    if (completedAnalyses.length === 0) return;
    
    loading = true;
    try {
      const allInsights = [];
      
      // Load insights from all completed analyses
      for (const analysis of completedAnalyses) {
        const response = await api.get(`/codemirror/insights/${analysis.id}?status=${selectedStatus}`);
        
        // Add analysis info to each insight
        const insightsWithAnalysis = response.map(insight => ({
          ...insight,
          analysis_id: analysis.id,
          analysis_depth: analysis.analysis_depth,
          analysis_date: analysis.created_at
        }));
        
        allInsights.push(...insightsWithAnalysis);
      }
      
      insights = allInsights;
    } catch (error) {
      console.error('Failed to load insights:', error);
    } finally {
      loading = false;
    }
  }
  
  // Reload when status changes
  $effect(() => {
    if (selectedStatus && completedAnalyses.length > 0) {
      loadInsights();
    }
  });
  
  async function updateInsightStatus(insightId: string, newStatus: string) {
    try {
      await api.put(`/code-cortex/codemirror/insights/${insightId}/status`, null, {
        params: { status: newStatus }
      });
      
      // Update local state
      insights = insights.map(insight => 
        insight.id === insightId 
          ? { ...insight, status: newStatus }
          : insight
      );
    } catch (error) {
      console.error('Failed to update insight status:', error);
    }
  }
  
  function getSeverityColor(severity: string) {
    const colors = {
      'low': '#10b981',
      'medium': '#f59e0b',
      'high': '#ef4444',
      'critical': '#dc2626'
    };
    return colors[severity] || '#6b7280';
  }
  
  function getTypeIcon(type: string) {
    const icons = {
      'security_vulnerability': '🛡️',
      'performance_optimization': '⚡',
      'code_quality': '📝',
      'dependency_update': '📦',
      'pattern_improvement': '🔄',
      'learning_opportunity': '📚'
    };
    return icons[type] || '💡';
  }
</script>

<div class="insights-container">
  <div class="insights-controls">
    <div class="filter-row">
      <select 
        class="filter-select"
        bind:value={selectedAnalysis}
      >
        <option value="all">All Analyses</option>
        {#each completedAnalyses as analysis}
          <option value={analysis.id}>
            {analysis.analysis_depth} - {new Date(analysis.created_at).toLocaleDateString()}
          </option>
        {/each}
      </select>
      
      <select 
        class="filter-select"
        bind:value={selectedType}
      >
        <option value="all">All Types</option>
        {#each insightTypes.filter(t => t !== 'all') as type}
          <option value={type}>
            {type.replace(/_/g, ' ')}
          </option>
        {/each}
      </select>
      
      <div class="status-tabs">
        <button 
          class="status-tab"
          class:active={selectedStatus === 'open'}
          onclick={() => selectedStatus = 'open'}
        >
          Open ({insights.filter(i => i.status === 'open').length})
        </button>
        <button 
          class="status-tab"
          class:active={selectedStatus === 'acknowledged'}
          onclick={() => selectedStatus = 'acknowledged'}
        >
          Acknowledged ({insights.filter(i => i.status === 'acknowledged').length})
        </button>
        <button 
          class="status-tab"
          class:active={selectedStatus === 'applied'}
          onclick={() => selectedStatus = 'applied'}
        >
          Applied ({insights.filter(i => i.status === 'applied').length})
        </button>
      </div>
    </div>
  </div>
  
  {#if loading}
    <div class="loading">Loading insights...</div>
  {:else if filteredInsights.length > 0}
    <div class="insights-list">
      {#each filteredInsights as insight}
        <div class="insight-card">
          <div class="insight-header">
            <div class="insight-title-row">
              <span class="type-icon">{getTypeIcon(insight.insight_type)}</span>
              <h4 class="insight-title">{insight.title}</h4>
            </div>
            
            {#if insight.severity}
              <span 
                class="severity-badge"
                style="background-color: {getSeverityColor(insight.severity)}20; color: {getSeverityColor(insight.severity)}"
              >
                {insight.severity}
              </span>
            {/if}
          </div>
          
          <p class="insight-description">{insight.description}</p>
          
          <div class="recommendation">
            <h5>Recommendation</h5>
            <p>{insight.recommendation}</p>
          </div>
          
          <div class="insight-footer">
            <div class="insight-meta">
              <span class="confidence">
                Confidence: {Math.round(insight.confidence_score * 100)}%
              </span>
              <span class="analysis-info">
                From {insight.analysis_depth} analysis
              </span>
            </div>
            
            <div class="insight-actions">
              {#if insight.status === 'open'}
                <button 
                  class="action-btn acknowledge"
                  onclick={() => updateInsightStatus(insight.id, 'acknowledged')}
                >
                  Acknowledge
                </button>
                <button 
                  class="action-btn apply"
                  onclick={() => updateInsightStatus(insight.id, 'applied')}
                >
                  Mark Applied
                </button>
              {:else if insight.status === 'acknowledged'}
                <button 
                  class="action-btn apply"
                  onclick={() => updateInsightStatus(insight.id, 'applied')}
                >
                  Mark Applied
                </button>
                <button 
                  class="action-btn dismiss"
                  onclick={() => updateInsightStatus(insight.id, 'dismissed')}
                >
                  Dismiss
                </button>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {:else if completedAnalyses.length === 0}
    <div class="no-insights">
      <p>No completed analyses yet.</p>
      <p class="hint">Run an analysis to see AI-generated insights.</p>
    </div>
  {:else}
    <div class="no-insights">
      <p>No {selectedStatus} insights found.</p>
    </div>
  {/if}
</div>

<style>
  .insights-container {
    min-height: 400px;
  }
  
  .insights-controls {
    margin-bottom: 1.5rem;
  }
  
  .filter-row {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
  }
  
  .filter-select {
    padding: 0.5rem 1rem;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 0.875rem;
    cursor: pointer;
  }
  
  .status-tabs {
    display: flex;
    gap: 0.5rem;
    margin-left: auto;
  }
  
  .status-tab {
    padding: 0.5rem 1rem;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 20px;
    color: var(--text-secondary);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .status-tab:hover {
    background: var(--surface-2);
  }
  
  .status-tab.active {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
  }
  
  .loading {
    text-align: center;
    padding: 3rem;
    color: var(--text-secondary);
  }
  
  .insights-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .insight-card {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
  }
  
  .insight-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .insight-title-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .type-icon {
    font-size: 1.5rem;
  }
  
  .insight-title {
    margin: 0;
    font-size: 1.1rem;
    color: var(--text-primary);
  }
  
  .severity-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
  }
  
  .insight-description {
    margin: 0 0 1rem 0;
    color: var(--text-secondary);
    line-height: 1.5;
  }
  
  .recommendation {
    background: var(--surface-3);
    border-radius: 6px;
    padding: 1rem;
    margin-bottom: 1rem;
  }
  
  .recommendation h5 {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    color: var(--text-primary);
    font-weight: 600;
  }
  
  .recommendation p {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
    line-height: 1.4;
  }
  
  .insight-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
  }
  
  .insight-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }
  
  .insight-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .action-btn {
    padding: 0.375rem 0.75rem;
    border: none;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .action-btn.acknowledge {
    background: var(--surface-3);
    color: var(--text-primary);
  }
  
  .action-btn.acknowledge:hover {
    background: var(--surface-4);
  }
  
  .action-btn.apply {
    background: #10b981;
    color: white;
  }
  
  .action-btn.apply:hover {
    background: #059669;
  }
  
  .action-btn.dismiss {
    background: var(--surface-3);
    color: var(--text-secondary);
  }
  
  .action-btn.dismiss:hover {
    background: var(--surface-4);
  }
  
  .no-insights {
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
    .filter-row {
      flex-direction: column;
      align-items: stretch;
    }
    
    .status-tabs {
      margin-left: 0;
      justify-content: center;
    }
    
    .insight-footer {
      flex-direction: column;
      align-items: flex-start;
    }
  }
</style>