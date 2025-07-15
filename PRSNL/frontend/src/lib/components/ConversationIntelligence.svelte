<script>
  import { onMount } from 'svelte';
  import Icon from './Icon.svelte';
  import SkeletonLoader from './SkeletonLoader.svelte';
  import AIProcessingIndicator from './AIProcessingIndicator.svelte';

  export let conversationId;
  export let showFullAnalysis = true;

  let intelligence = null;
  let loading = true;
  let error = null;
  let activeTab = 'summary';

  // Real-time progress tracking
  let processingStartTime = null;
  let currentProgress = 0;
  let currentStage = 'analyzing';

  const tabs = [
    { id: 'summary', name: 'Summary', icon: 'file-text' },
    { id: 'learning', name: 'Learning Journey', icon: 'trending-up' },
    { id: 'concepts', name: 'Key Concepts', icon: 'cpu' },
    { id: 'insights', name: 'Insights & Gaps', icon: 'lightbulb' },
    { id: 'technical', name: 'Technical Content', icon: 'code' },
    { id: 'actionable', name: 'Actionable Insights', icon: 'target' },
  ];

  onMount(async () => {
    await loadIntelligence();
  });

  // Calculate real progress based on API response data
  function calculateProgress(intelligenceData) {
    if (!intelligenceData) return { progress: 0, stage: 'analyzing' };

    let progress = 0;
    let stage = 'analyzing';

    // Stage 1 (0-25%): Basic processing started
    if (intelligenceData.status === 'processing' || intelligenceData.status === 'completed') {
      progress = 0.25;
      stage = 'extracting';
    }

    // Stage 2 (25-50%): Summary and basic data available
    if (intelligenceData.summary && intelligenceData.summary.text) {
      progress = 0.5;
      stage = 'synthesizing';
    }

    // Stage 3 (50-75%): Key concepts and topics identified
    if (
      intelligenceData.concepts &&
      intelligenceData.concepts.topics &&
      intelligenceData.concepts.topics.length > 0
    ) {
      progress = 0.65;
    }

    // Stage 4 (65-85%): Learning journey and insights available
    if (intelligenceData.learning_journey && intelligenceData.learning_journey.narrative) {
      progress = 0.75;
    }

    // Stage 5 (75-90%): Multi-agent intelligence data present (check for actual content)
    const hasTechnicalContent =
      intelligenceData.technical_content &&
      (intelligenceData.technical_content.technologies?.length > 0 ||
        intelligenceData.technical_content.code_snippets?.length > 0 ||
        intelligenceData.technical_content.implementation_patterns?.length > 0);

    const hasActionableInsights =
      intelligenceData.actionable_insights &&
      (intelligenceData.actionable_insights.best_practices?.length > 0 ||
        intelligenceData.actionable_insights.immediate_actions?.length > 0 ||
        intelligenceData.actionable_insights.tools_and_resources?.length > 0);

    if (intelligenceData.technical_content || intelligenceData.actionable_insights) {
      progress = 0.85;
      stage = 'finalizing';
    }

    // Stage 6 (90-100%): All data complete AND actually contains meaningful content
    const hasCompleteData =
      intelligenceData.status === 'completed' &&
      intelligenceData.summary &&
      intelligenceData.summary.text &&
      intelligenceData.concepts &&
      intelligenceData.concepts.topics &&
      intelligenceData.concepts.topics.length > 0;

    // Only reach 100% if we have meaningful data OR if explicitly completed (even with empty data)
    if (hasCompleteData) {
      if (hasTechnicalContent || hasActionableInsights) {
        progress = 1.0; // Complete with meaningful multi-agent data
      } else if (intelligenceData.status === 'completed') {
        progress = 0.95; // Complete but with limited multi-agent insights
      }
      stage = 'finalizing';
    }

    // Special case: Force 100% completion after a delay when status is completed
    // This ensures users see completion even if multi-agent data is sparse
    if (intelligenceData.status === 'completed' && progress >= 0.85) {
      progress = 1.0;
      stage = 'finalizing';
    }

    return { progress, stage };
  }

  async function loadIntelligence() {
    try {
      loading = true;
      error = null;

      const response = await fetch(`/api/conversations/intelligence/${conversationId}`);

      if (!response.ok) {
        throw new Error('Failed to load intelligence data');
      }

      intelligence = await response.json();

      // Track processing start time on first processing status
      if (intelligence.status === 'processing' && !processingStartTime) {
        processingStartTime = Date.now();
      }

      // Calculate real progress based on available data
      const progressInfo = calculateProgress(intelligence);
      currentProgress = progressInfo.progress;
      currentStage = progressInfo.stage;

      console.log('Progress update:', {
        status: intelligence.status,
        progress: currentProgress,
        stage: currentStage,
        hasData: {
          summary: !!intelligence.summary,
          concepts: !!intelligence.concepts,
          technical: !!intelligence.technical_content,
          actionable: !!intelligence.actionable_insights,
        },
      });

      // If still processing, poll for updates more frequently during active processing
      if (intelligence.status === 'processing') {
        setTimeout(loadIntelligence, 2000); // Poll every 2 seconds for better UX
      }
    } catch (err) {
      error = err.message;
      console.error('Error loading intelligence:', err);
    } finally {
      loading = false;
    }
  }

  function getStatusIcon(status) {
    switch (status) {
      case 'completed':
        return 'check-circle';
      case 'processing':
        return 'loader';
      case 'failed':
        return 'alert-circle';
      default:
        return 'clock';
    }
  }

  function getStatusColor(status) {
    switch (status) {
      case 'completed':
        return 'var(--success)';
      case 'processing':
        return 'var(--accent)';
      case 'failed':
        return 'var(--error)';
      default:
        return 'var(--text-secondary)';
    }
  }
</script>

<div class="intelligence-container">
  {#if (loading && !intelligence) || (intelligence && intelligence.status === 'processing')}
    <AIProcessingIndicator
      progress={currentProgress}
      {currentStage}
      {processingStartTime}
      estimatedTimeMs={45000}
    />
  {:else if error}
    <div class="error-state">
      <Icon name="alert-triangle" size={24} />
      <p>{error}</p>
      <button on:click={loadIntelligence} class="retry-btn">
        <Icon name="refresh-cw" size={16} />
        Retry
      </button>
    </div>
  {:else if intelligence}
    {#if intelligence.status === 'completed' && showFullAnalysis}
      <!-- Status Header for Completed -->
      <div class="status-header">
        <div class="status-badge" style="--status-color: {getStatusColor(intelligence.status)}">
          <Icon name={getStatusIcon(intelligence.status)} size={16} />
          <span>{intelligence.status}</span>
        </div>
      </div>
      <!-- Tab Navigation -->
      <div class="tab-nav">
        {#each tabs as tab}
          <button
            class="tab-button {activeTab === tab.id ? 'active' : ''}"
            on:click={() => (activeTab = tab.id)}
          >
            <Icon name={tab.icon} size={16} />
            <span>{tab.name}</span>
          </button>
        {/each}
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        {#if activeTab === 'summary' && intelligence.summary}
          <div class="summary-section">
            <h3>Conversation Summary</h3>
            <p class="summary-text">{intelligence.summary.text}</p>

            <div class="summary-meta">
              <div class="meta-item">
                <Icon name="message-circle" size={16} />
                <span>Platform: {intelligence.summary.platform}</span>
              </div>
              <div class="meta-item">
                <Icon name="hash" size={16} />
                <span>Title: {intelligence.summary.title}</span>
              </div>
            </div>
          </div>
        {/if}

        {#if activeTab === 'learning' && intelligence.learning_journey}
          <div class="learning-section">
            <h3>Your Learning Journey</h3>
            <div class="journey-narrative">
              <p>{intelligence.learning_journey.narrative}</p>
            </div>

            {#if intelligence.learning_journey.key_learnings.length > 0}
              <div class="key-learnings">
                <h4>Key Learnings</h4>
                <ul class="learning-list">
                  {#each intelligence.learning_journey.key_learnings as learning}
                    <li>
                      <Icon name="check" size={16} />
                      <span>{learning}</span>
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}
          </div>
        {/if}

        {#if activeTab === 'concepts' && intelligence.concepts}
          <div class="concepts-section">
            <h3>Key Concepts & Topics</h3>

            {#if intelligence.concepts.topics.length > 0}
              <div class="topic-tags">
                {#each intelligence.concepts.topics as topic}
                  <span class="topic-tag">{topic}</span>
                {/each}
              </div>
            {/if}

            <div class="concept-meta">
              {#if intelligence.concepts.category}
                <div class="category-info">
                  <strong>Category:</strong>
                  {intelligence.concepts.category}
                  {#if intelligence.concepts.subcategory}
                    / {intelligence.concepts.subcategory}
                  {/if}
                  {#if intelligence.concepts.confidence}
                    <span class="confidence">
                      ({Math.round(intelligence.concepts.confidence * 100)}% confident)
                    </span>
                  {/if}
                </div>
              {/if}
            </div>
          </div>
        {/if}

        {#if activeTab === 'insights' && intelligence.insights}
          <div class="insights-section">
            <h3>Insights & Knowledge Gaps</h3>

            {#if intelligence.insights.knowledge_gaps.length > 0}
              <div class="knowledge-gaps">
                <h4>Areas for Further Exploration</h4>
                <ul class="gaps-list">
                  {#each intelligence.insights.knowledge_gaps as gap}
                    <li>
                      <Icon name="alert-circle" size={16} />
                      <span>{gap}</span>
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}

            {#if intelligence.insights.message_insights && intelligence.insights.message_insights.length > 0}
              <div class="message-insights">
                <h4>Key Message Insights</h4>
                {#each intelligence.insights.message_insights.slice(0, 3) as msg}
                  <div class="message-insight">
                    <div class="insight-header">
                      <span class="role-badge {msg.role}">{msg.role}</span>
                      <span class="position">Message #{msg.position}</span>
                    </div>
                    {#if msg.summary}
                      <p class="insight-summary">{msg.summary}</p>
                    {/if}
                    {#if msg.concepts.length > 0}
                      <div class="insight-concepts">
                        {#each msg.concepts as concept}
                          <span class="concept-chip">{concept}</span>
                        {/each}
                      </div>
                    {/if}
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        {/if}

        {#if activeTab === 'technical' && intelligence.technical_content}
          <div class="technical-section">
            <h3>Technical Content</h3>

            {#if intelligence.technical_content.technologies && intelligence.technical_content.technologies.length > 0}
              <div class="tech-category">
                <h4>Technologies Mentioned</h4>
                <div class="tech-tags">
                  {#each intelligence.technical_content.technologies as tech}
                    <span class="tech-tag">{tech}</span>
                  {/each}
                </div>
              </div>
            {/if}

            {#if intelligence.technical_content.code_snippets && intelligence.technical_content.code_snippets.length > 0}
              <div class="tech-category">
                <h4>Code Snippets</h4>
                <div class="code-snippets">
                  {#each intelligence.technical_content.code_snippets as snippet}
                    <div class="code-snippet">
                      <pre><code>{snippet}</code></pre>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            {#if intelligence.technical_content.implementation_patterns && intelligence.technical_content.implementation_patterns.length > 0}
              <div class="tech-category">
                <h4>Implementation Patterns</h4>
                <ul class="pattern-list">
                  {#each intelligence.technical_content.implementation_patterns as pattern}
                    <li>
                      <Icon name="cpu" size={16} />
                      <span>{pattern}</span>
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}

            {#if intelligence.technical_content.technical_recommendations && intelligence.technical_content.technical_recommendations.length > 0}
              <div class="tech-category">
                <h4>Technical Recommendations</h4>
                <ul class="recommendations-list">
                  {#each intelligence.technical_content.technical_recommendations as recommendation}
                    <li>
                      <Icon name="chevron-right" size={16} />
                      <span>{recommendation}</span>
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}

            {#if !intelligence.technical_content.technologies?.length && !intelligence.technical_content.code_snippets?.length && !intelligence.technical_content.implementation_patterns?.length && !intelligence.technical_content.technical_recommendations?.length}
              <div class="empty-state">
                <Icon name="code" size={48} />
                <p>No specific technical content detected in this conversation.</p>
              </div>
            {/if}
          </div>
        {/if}

        {#if activeTab === 'actionable' && intelligence.actionable_insights}
          <div class="actionable-section">
            <h3>Actionable Insights</h3>

            {#if intelligence.actionable_insights.best_practices && intelligence.actionable_insights.best_practices.length > 0}
              <div class="insights-category">
                <h4>Best Practices</h4>
                <ul class="practices-list">
                  {#each intelligence.actionable_insights.best_practices as practice}
                    <li>
                      <Icon name="check-circle" size={16} />
                      <span>{practice}</span>
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}

            {#if intelligence.actionable_insights.immediate_actions && intelligence.actionable_insights.immediate_actions.length > 0}
              <div class="insights-category">
                <h4>Immediate Actions</h4>
                <ul class="actions-list">
                  {#each intelligence.actionable_insights.immediate_actions as action}
                    <li>
                      <Icon name="zap" size={16} />
                      <span>{action}</span>
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}

            {#if intelligence.actionable_insights.tools_and_resources && intelligence.actionable_insights.tools_and_resources.length > 0}
              <div class="insights-category">
                <h4>Recommended Tools & Resources</h4>
                <ul class="resources-list">
                  {#each intelligence.actionable_insights.tools_and_resources as resource}
                    <li>
                      <Icon name="tool" size={16} />
                      <span>{resource}</span>
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}

            {#if intelligence.actionable_insights.implementation_steps && intelligence.actionable_insights.implementation_steps.length > 0}
              <div class="insights-category">
                <h4>Implementation Steps</h4>
                <ol class="steps-list">
                  {#each intelligence.actionable_insights.implementation_steps as step, index}
                    <li>
                      <span class="step-number">{index + 1}</span>
                      <span>{step}</span>
                    </li>
                  {/each}
                </ol>
              </div>
            {/if}

            {#if !intelligence.actionable_insights.best_practices?.length && !intelligence.actionable_insights.immediate_actions?.length && !intelligence.actionable_insights.tools_and_resources?.length && !intelligence.actionable_insights.implementation_steps?.length}
              <div class="empty-state">
                <Icon name="target" size={48} />
                <p>No specific actionable insights identified for this conversation.</p>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {:else if intelligence.status === 'completed' && !showFullAnalysis}
      <!-- Compact Summary View -->
      <div class="compact-summary">
        {#if intelligence.summary}
          <p class="summary-preview">{intelligence.summary.text}</p>
        {/if}
        {#if intelligence.concepts && intelligence.concepts.topics.length > 0}
          <div class="compact-topics">
            {#each intelligence.concepts.topics.slice(0, 5) as topic}
              <span class="topic-tag small">{topic}</span>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  {/if}
</div>

<style>
  .intelligence-container {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.75rem;
    padding: 1.5rem;
  }

  .loading-state,
  .error-state {
    text-align: center;
    padding: 2rem;
  }

  .error-state {
    color: var(--error);
  }

  .retry-btn {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.2s ease;
  }

  .retry-btn:hover {
    background: var(--accent-hover);
    transform: translateY(-1px);
  }

  /* Status Header */
  .status-header {
    margin-bottom: 1.5rem;
  }

  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.875rem;
    background: rgba(var(--status-color-rgb), 0.1);
    border: 1px solid var(--status-color);
    border-radius: 2rem;
    color: var(--status-color);
    font-size: 0.875rem;
    font-weight: 500;
  }

  .processing-message {
    margin-top: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  /* Tab Navigation */
  .tab-nav {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .tab-button {
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    transition: all 0.2s ease;
    position: relative;
  }

  .tab-button:hover {
    color: var(--text-primary);
  }

  .tab-button.active {
    color: var(--accent);
  }

  .tab-button.active::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--accent);
  }

  /* Tab Content */
  .tab-content {
    animation: fadeIn 0.3s ease;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Summary Section */
  .summary-section h3 {
    margin: 0 0 1rem 0;
    color: var(--text-primary);
  }

  .summary-text {
    line-height: 1.6;
    color: var(--text-primary);
    margin-bottom: 1.5rem;
  }

  .summary-meta {
    display: flex;
    gap: 2rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .meta-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  /* Learning Section */
  .journey-narrative {
    background: rgba(74, 158, 255, 0.05);
    border: 1px solid rgba(74, 158, 255, 0.1);
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }

  .journey-narrative p {
    margin: 0;
    line-height: 1.6;
  }

  .key-learnings h4 {
    margin: 0 0 0.75rem 0;
    color: var(--text-primary);
  }

  .learning-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .learning-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.5rem 0;
    color: var(--text-primary);
  }

  .learning-list li :global(svg) {
    color: var(--success);
    flex-shrink: 0;
    margin-top: 0.125rem;
  }

  /* Concepts Section */
  .topic-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }

  .topic-tag {
    padding: 0.375rem 0.875rem;
    background: rgba(140, 82, 255, 0.1);
    border: 1px solid rgba(140, 82, 255, 0.2);
    border-radius: 2rem;
    font-size: 0.875rem;
    color: var(--accent-secondary);
  }

  .topic-tag.small {
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
  }

  .concept-meta {
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .category-info {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .confidence {
    opacity: 0.7;
    font-size: 0.75rem;
  }

  /* Insights Section */
  .knowledge-gaps,
  .message-insights {
    margin-bottom: 2rem;
  }

  .knowledge-gaps h4,
  .message-insights h4 {
    margin: 0 0 0.75rem 0;
    color: var(--text-primary);
  }

  .gaps-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .gaps-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.5rem 0;
    color: var(--text-primary);
  }

  .gaps-list li :global(svg) {
    color: var(--warning);
    flex-shrink: 0;
    margin-top: 0.125rem;
  }

  .message-insight {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .insight-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .role-badge {
    padding: 0.25rem 0.625rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
  }

  .role-badge.user {
    background: rgba(74, 158, 255, 0.1);
    color: var(--accent);
  }

  .role-badge.assistant {
    background: rgba(16, 185, 129, 0.1);
    color: var(--success);
  }

  .position {
    color: var(--text-secondary);
    font-size: 0.75rem;
  }

  .insight-summary {
    margin: 0 0 0.75rem 0;
    color: var(--text-primary);
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .insight-concepts {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
  }

  .concept-chip {
    padding: 0.125rem 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  /* Compact Summary */
  .compact-summary {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .summary-preview {
    margin: 0;
    color: var(--text-primary);
    line-height: 1.5;
    font-size: 0.875rem;
  }

  .compact-topics {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
  }

  /* Technical Section */
  .technical-section,
  .actionable-section {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .technical-section h3,
  .actionable-section h3 {
    margin: 0 0 1rem 0;
    color: var(--text-primary);
  }

  .tech-category,
  .insights-category {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 0.5rem;
    padding: 1rem;
  }

  .tech-category h4,
  .insights-category h4 {
    margin: 0 0 0.75rem 0;
    color: var(--text-primary);
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .tech-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tech-tag {
    padding: 0.375rem 0.875rem;
    background: rgba(74, 158, 255, 0.1);
    border: 1px solid rgba(74, 158, 255, 0.2);
    border-radius: 2rem;
    font-size: 0.875rem;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
  }

  .code-snippets {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .code-snippet {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.375rem;
    overflow: hidden;
  }

  .code-snippet pre {
    margin: 0;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.875rem;
    line-height: 1.4;
    color: var(--text-primary);
    overflow-x: auto;
  }

  .pattern-list,
  .recommendations-list,
  .practices-list,
  .actions-list,
  .resources-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .pattern-list li,
  .recommendations-list li,
  .practices-list li,
  .actions-list li,
  .resources-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 0.375rem;
    color: var(--text-primary);
    font-size: 0.875rem;
    line-height: 1.4;
  }

  .pattern-list li :global(svg) {
    color: var(--accent);
    flex-shrink: 0;
    margin-top: 0.125rem;
  }

  .recommendations-list li :global(svg) {
    color: var(--accent-secondary);
    flex-shrink: 0;
    margin-top: 0.125rem;
  }

  .practices-list li :global(svg) {
    color: var(--success);
    flex-shrink: 0;
    margin-top: 0.125rem;
  }

  .actions-list li :global(svg) {
    color: var(--warning);
    flex-shrink: 0;
    margin-top: 0.125rem;
  }

  .resources-list li :global(svg) {
    color: var(--accent);
    flex-shrink: 0;
    margin-top: 0.125rem;
  }

  .steps-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .steps-list li {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 0.5rem;
    color: var(--text-primary);
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .step-number {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--accent);
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
  }

  .empty-state :global(svg) {
    opacity: 0.3;
    margin-bottom: 1rem;
  }

  .empty-state p {
    margin: 0;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .intelligence-container {
      padding: 1rem;
    }

    .tab-nav {
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }

    .summary-meta {
      flex-direction: column;
      gap: 0.5rem;
    }

    .tech-category,
    .insights-category {
      padding: 0.75rem;
    }

    .steps-list li {
      padding: 0.75rem;
      gap: 0.75rem;
    }
  }
</style>
