<script>
  import { onMount } from 'svelte';
  import Icon from './Icon.svelte';
  import SkeletonLoader from './SkeletonLoader.svelte';
  
  export let conversationId;
  export let showFullAnalysis = true;
  
  let intelligence = null;
  let loading = true;
  let error = null;
  let activeTab = 'summary';
  
  const tabs = [
    { id: 'summary', name: 'Summary', icon: 'file-text' },
    { id: 'learning', name: 'Learning Journey', icon: 'trending-up' },
    { id: 'concepts', name: 'Key Concepts', icon: 'cpu' },
    { id: 'insights', name: 'Insights & Gaps', icon: 'lightbulb' }
  ];
  
  onMount(async () => {
    await loadIntelligence();
  });
  
  async function loadIntelligence() {
    try {
      loading = true;
      error = null;
      
      const response = await fetch(`/api/conversations/intelligence/${conversationId}`);
      
      if (!response.ok) {
        throw new Error('Failed to load intelligence data');
      }
      
      intelligence = await response.json();
      
      // If still processing, poll for updates
      if (intelligence.status === 'processing') {
        setTimeout(loadIntelligence, 3000); // Poll every 3 seconds
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
  {#if loading && !intelligence}
    <div class="loading-state">
      <SkeletonLoader type="text" />
      <SkeletonLoader type="paragraph" />
    </div>
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
    <!-- Status Header -->
    <div class="status-header">
      <div class="status-badge" style="--status-color: {getStatusColor(intelligence.status)}">
        <Icon name={getStatusIcon(intelligence.status)} size={16} />
        <span>{intelligence.status}</span>
      </div>
      
      {#if intelligence.status === 'processing'}
        <p class="processing-message">
          AI is analyzing your conversation... This may take a moment.
        </p>
      {/if}
    </div>
    
    {#if intelligence.status === 'completed' && showFullAnalysis}
      <!-- Tab Navigation -->
      <div class="tab-nav">
        {#each tabs as tab}
          <button
            class="tab-button {activeTab === tab.id ? 'active' : ''}"
            on:click={() => activeTab = tab.id}
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
                  <strong>Category:</strong> {intelligence.concepts.category}
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
  }
</style>