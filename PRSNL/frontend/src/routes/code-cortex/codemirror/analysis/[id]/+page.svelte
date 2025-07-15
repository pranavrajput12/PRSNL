<script lang="ts">
  import { goto } from '$app/navigation';
  import type { PageData } from './$types';

  export let data: PageData;

  // Simple destructuring - no reactive code
  const analysisId = data.analysisId;
  const analysis = data.analysis;
  const insights = data.insights;
  const knowledgeContent = data.knowledgeContent;
  const languages = data.languages;
  const frameworks = data.frameworks;
  const fileCount = data.fileCount;

  function goBack() {
    goto('/code-cortex/codemirror');
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function getSeverityColor(severity?: string) {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'text-red-400';
      case 'high':
        return 'text-orange-400';
      case 'medium':
        return 'text-yellow-400';
      case 'low':
        return 'text-green-400';
      default:
        return 'text-gray-400';
    }
  }
</script>

<svelte:head>
  <title>Analysis Details - CodeMirror</title>
</svelte:head>

<div class="analysis-page">
  <!-- Simple Header -->
  <div class="header">
    <div class="container">
      <h1>Analysis Details</h1>
      <p>AI-powered repository intelligence</p>
    </div>
  </div>

  <!-- Main Content -->
  <div class="container">
    <!-- Analysis Header -->
    <div class="analysis-header">
      <h2>{analysis.repository_name || 'Repository Analysis'}</h2>
      <div class="analysis-meta">
        <span>📅 {formatDate(analysis.created_at)}</span>
        <span>🏷️ {analysis.analysis_depth || 'standard'}</span>
        <span>✅ Completed</span>
      </div>
      <div class="analysis-id">
        <small>Analysis ID: {analysisId}</small>
      </div>
    </div>

    <!-- Analysis Results -->
    {#if fileCount > 0 || languages.length > 0 || frameworks.length > 0}
      <div class="results-grid">
        <!-- File Count -->
        <div class="result-card">
          <h3>Files Analyzed</h3>
          <div class="big-number">{fileCount}</div>
        </div>

        <!-- Languages -->
        <div class="result-card">
          <h3>Languages</h3>
          <div class="tags">
            {#if languages.length > 0}
              {#each languages as language}
                <span class="tag tag-green">{language}</span>
              {/each}
            {:else}
              <span class="no-data">No languages detected</span>
            {/if}
          </div>
        </div>

        <!-- Frameworks -->
        <div class="result-card">
          <h3>Frameworks</h3>
          <div class="tags">
            {#if frameworks.length > 0}
              {#each frameworks as framework}
                <span class="tag tag-purple">{framework}</span>
              {/each}
            {:else}
              <span class="no-data">No frameworks detected</span>
            {/if}
          </div>
        </div>
      </div>
    {/if}

    <!-- Quality Scores -->
    {#if analysis.security_score || analysis.performance_score || analysis.quality_score}
      <div class="scores-section">
        <h3>Quality Scores</h3>
        <div class="scores-grid">
          <div class="score-item">
            <div class="score-label">Security</div>
            <div class="score-value">{analysis.security_score || 'N/A'}</div>
          </div>
          <div class="score-item">
            <div class="score-label">Performance</div>
            <div class="score-value">{analysis.performance_score || 'N/A'}</div>
          </div>
          <div class="score-item">
            <div class="score-label">Code Quality</div>
            <div class="score-value">{analysis.quality_score || 'N/A'}</div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Insights -->
    {#if insights.length > 0}
      <div class="insights-section">
        <h3>AI Insights</h3>
        <div class="insights-list">
          {#each insights as insight}
            <div class="insight-card">
              <div class="insight-header">
                <h4>{insight.title}</h4>
                <div class="insight-meta">
                  <span class="severity {getSeverityColor(insight.severity)}"
                    >{insight.severity || 'medium'}</span
                  >
                  <span class="confidence"
                    >{Math.round((insight.confidence_score || 0) * 100)}% confidence</span
                  >
                </div>
              </div>
              <p class="insight-description">{insight.description}</p>
              {#if insight.recommendation}
                <div class="recommendation">
                  <strong>Recommendation:</strong>
                  {insight.recommendation}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {:else}
      <div class="no-insights">
        <h3>No Insights Available</h3>
        <p>AI insights will appear here once the analysis is complete.</p>
      </div>
    {/if}

    <!-- Knowledge Content Summary -->
    {#if knowledgeContent && knowledgeContent.total_results > 0}
      <div class="knowledge-section">
        <h3>Related Knowledge</h3>
        <div class="knowledge-summary">
          <p>Found {knowledgeContent.total_results} related items in your knowledge base</p>
          <div class="knowledge-types">
            {#if knowledgeContent.videos?.length > 0}
              <div class="knowledge-type">📹 {knowledgeContent.videos.length} Videos</div>
            {/if}
            {#if knowledgeContent.photos?.length > 0}
              <div class="knowledge-type">🖼️ {knowledgeContent.photos.length} Images</div>
            {/if}
            {#if knowledgeContent.documents?.length > 0}
              <div class="knowledge-type">📄 {knowledgeContent.documents.length} Documents</div>
            {/if}
            {#if knowledgeContent.notes?.length > 0}
              <div class="knowledge-type">📝 {knowledgeContent.notes.length} Notes</div>
            {/if}
          </div>
        </div>
      </div>
    {/if}

    <!-- Back Button -->
    <div class="back-section">
      <button onclick={goBack} class="back-button"> ← Back to CodeMirror </button>
    </div>
  </div>
</div>

<style>
  .analysis-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #1e293b, #334155, #1e293b);
    color: white;
    font-family: system-ui, sans-serif;
  }

  .header {
    border-bottom: 1px solid #374151;
    padding: 1rem 0;
    background: rgba(0, 0, 0, 0.2);
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
  }

  .header h1 {
    font-size: 1.5rem;
    font-weight: bold;
    margin: 0;
  }

  .header p {
    color: #9ca3af;
    margin: 0.25rem 0 0 0;
    font-size: 0.875rem;
  }

  .analysis-header {
    background: rgba(31, 41, 55, 0.5);
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 2rem 0;
  }

  .analysis-header h2 {
    font-size: 1.75rem;
    font-weight: bold;
    margin: 0 0 1rem 0;
    color: white;
  }

  .analysis-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.875rem;
    color: #9ca3af;
    flex-wrap: wrap;
  }

  .analysis-id {
    margin-top: 1rem;
    font-family: monospace;
    font-size: 0.75rem;
    color: #60a5fa;
  }

  .results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
  }

  .result-card {
    background: rgba(31, 41, 55, 0.5);
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 1.5rem;
  }

  .result-card h3 {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    color: white;
  }

  .big-number {
    font-size: 2.5rem;
    font-weight: bold;
    color: #60a5fa;
  }

  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tag {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 500;
    border-radius: 9999px;
    border: 1px solid;
  }

  .tag-green {
    background: rgba(34, 197, 94, 0.1);
    color: #4ade80;
    border-color: rgba(34, 197, 94, 0.3);
  }

  .tag-purple {
    background: rgba(168, 85, 247, 0.1);
    color: #a855f7;
    border-color: rgba(168, 85, 247, 0.3);
  }

  .no-data {
    color: #9ca3af;
    font-size: 0.875rem;
  }

  .scores-section {
    background: rgba(31, 41, 55, 0.5);
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 2rem 0;
  }

  .scores-section h3 {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    color: white;
  }

  .scores-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    text-align: center;
  }

  .score-item {
    padding: 1rem;
  }

  .score-label {
    font-size: 0.875rem;
    color: #9ca3af;
    margin-bottom: 0.5rem;
  }

  .score-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #60a5fa;
  }

  .insights-section {
    background: rgba(31, 41, 55, 0.5);
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 2rem 0;
  }

  .insights-section h3 {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    color: white;
  }

  .insights-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .insight-card {
    background: rgba(55, 65, 81, 0.5);
    border: 1px solid #4b5563;
    border-radius: 6px;
    padding: 1rem;
  }

  .insight-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .insight-header h4 {
    font-size: 1rem;
    font-weight: 500;
    margin: 0;
    color: white;
  }

  .insight-meta {
    display: flex;
    gap: 0.5rem;
    font-size: 0.75rem;
  }

  .severity {
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    background: rgba(107, 114, 128, 0.5);
  }

  .confidence {
    color: #9ca3af;
  }

  .insight-description {
    color: #d1d5db;
    font-size: 0.875rem;
    margin: 0 0 0.75rem 0;
    line-height: 1.4;
  }

  .recommendation {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 4px;
    padding: 0.75rem;
    font-size: 0.875rem;
    color: #93c5fd;
  }

  .no-insights {
    text-align: center;
    padding: 3rem 1rem;
    color: #9ca3af;
  }

  .no-insights h3 {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
    color: #d1d5db;
  }

  .knowledge-section {
    background: rgba(31, 41, 55, 0.5);
    border: 1px solid #374151;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 2rem 0;
  }

  .knowledge-section h3 {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    color: white;
  }

  .knowledge-summary p {
    color: #a855f7;
    margin: 0 0 1rem 0;
  }

  .knowledge-types {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    text-align: center;
  }

  .knowledge-type {
    background: rgba(55, 65, 81, 0.5);
    border: 1px solid #4b5563;
    border-radius: 6px;
    padding: 1rem;
    color: #d1d5db;
    font-size: 0.875rem;
  }

  .back-section {
    text-align: center;
    margin: 2rem 0;
  }

  .back-button {
    background: #374151;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .back-button:hover {
    background: #4b5563;
  }

  /* Color classes for severity */
  .text-red-400 {
    color: #f87171;
  }
  .text-orange-400 {
    color: #fb923c;
  }
  .text-yellow-400 {
    color: #facc15;
  }
  .text-green-400 {
    color: #4ade80;
  }
  .text-gray-400 {
    color: #9ca3af;
  }
</style>
