<!--
  Generic Item View Component
  
  This component provides a fallback view for any content type that doesn't
  have a specialized component. It displays the content in a clean, readable
  format with all the basic features.
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import MarkdownViewer from '$lib/components/development/MarkdownViewer.svelte';
  import TagList from '$lib/components/TagList.svelte';
  import { formatDate } from '$lib/utils/date';
  
  export let item: any;
  export let contentType: any;
  
  const dispatch = createEventDispatcher();
  
  $: hasContent = item.content || item.processed_content;
  $: hasMarkdown = hasContent && (item.content?.includes('#') || item.content?.includes('```'));
  $: hasTags = item.tags && item.tags.length > 0;
  $: hasMetadata = item.metadata && Object.keys(item.metadata).length > 0;
  
  function handleError(error: any) {
    dispatch('error', error);
  }
</script>

<div class="generic-item-view">
  <!-- Content Section -->
  {#if hasContent}
    <section class="content-section">
      <h2>Content</h2>
      <div class="content-body">
        {#if hasMarkdown}
          <MarkdownViewer 
            content={item.content || item.processed_content} 
            enableSyntaxHighlight={true} 
            theme="neural"
            on:error={handleError}
          />
        {:else}
          <div class="plain-content">
            {item.content || item.processed_content}
          </div>
        {/if}
      </div>
    </section>
  {/if}
  
  <!-- Summary Section -->
  {#if item.summary && item.summary !== item.content}
    <section class="summary-section">
      <h2>Summary</h2>
      <p class="summary-text">{item.summary}</p>
    </section>
  {/if}
  
  <!-- Tags Section -->
  {#if hasTags}
    <section class="tags-section">
      <h2>Tags</h2>
      <TagList tags={item.tags} />
    </section>
  {/if}
  
  <!-- Metadata Section -->
  <section class="metadata-section">
    <h2>Details</h2>
    <div class="metadata-grid">
      <div class="metadata-item">
        <span class="metadata-label">Type</span>
        <span class="metadata-value">{contentType.label}</span>
      </div>
      
      <div class="metadata-item">
        <span class="metadata-label">Created</span>
        <span class="metadata-value">{formatDate(item.created_at || item.createdAt)}</span>
      </div>
      
      {#if item.url}
        <div class="metadata-item">
          <span class="metadata-label">Source</span>
          <a href={item.url} target="_blank" rel="noopener noreferrer" class="metadata-link">
            <Icon name="external-link" size="small" />
            View Original
          </a>
        </div>
      {/if}
      
      {#if item.file_path}
        <div class="metadata-item">
          <span class="metadata-label">File</span>
          <span class="metadata-value">{item.file_path.split('/').pop()}</span>
        </div>
      {/if}
      
      {#if item.status}
        <div class="metadata-item">
          <span class="metadata-label">Status</span>
          <span class="metadata-value status-{item.status}">{item.status}</span>
        </div>
      {/if}
    </div>
  </section>
  
  <!-- AI Analysis Section -->
  {#if hasMetadata && item.metadata.ai_analysis}
    <section class="ai-analysis-section">
      <h2>AI Analysis</h2>
      <div class="ai-analysis-content">
        {#if item.metadata.ai_analysis.key_points}
          <div class="analysis-subsection">
            <h3>Key Points</h3>
            <ul class="key-points-list">
              {#each item.metadata.ai_analysis.key_points as point}
                <li>{point}</li>
              {/each}
            </ul>
          </div>
        {/if}
        
        {#if item.metadata.ai_analysis.questions}
          <div class="analysis-subsection">
            <h3>Questions This Answers</h3>
            <ul class="questions-list">
              {#each item.metadata.ai_analysis.questions as question}
                <li>{question}</li>
              {/each}
            </ul>
          </div>
        {/if}
      </div>
    </section>
  {/if}
</div>

<style>
  .generic-item-view {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  section {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
  }
  
  h2 {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    color: var(--neural-green);
    font-weight: 600;
  }
  
  h3 {
    margin: 0 0 0.75rem 0;
    font-size: 1.1rem;
    color: var(--text-primary);
    font-weight: 500;
  }
  
  .content-body {
    color: var(--text-primary);
    line-height: 1.6;
  }
  
  .plain-content {
    white-space: pre-wrap;
    color: var(--text-primary);
    line-height: 1.6;
  }
  
  .summary-text {
    color: var(--text-primary);
    line-height: 1.6;
    margin: 0;
    font-size: 1.1rem;
  }
  
  .metadata-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
  }
  
  .metadata-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .metadata-item:last-child {
    border-bottom: none;
  }
  
  .metadata-label {
    font-weight: 500;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }
  
  .metadata-value {
    color: var(--text-primary);
    font-weight: 500;
  }
  
  .metadata-link {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--neural-green);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
  }
  
  .metadata-link:hover {
    color: var(--text-primary);
  }
  
  .status-pending {
    color: #f59e0b;
  }
  
  .status-processed {
    color: var(--neural-green);
  }
  
  .status-error {
    color: #ef4444;
  }
  
  .ai-analysis-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .analysis-subsection {
    background: rgba(0, 0, 0, 0.2);
    padding: 1rem;
    border-radius: 8px;
  }
  
  .key-points-list,
  .questions-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .key-points-list li,
  .questions-list li {
    padding: 0.5rem 0 0.5rem 1.5rem;
    position: relative;
    color: var(--text-primary);
    line-height: 1.5;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }
  
  .key-points-list li:last-child,
  .questions-list li:last-child {
    border-bottom: none;
  }
  
  .key-points-list li::before {
    content: '→';
    position: absolute;
    left: 0;
    color: var(--neural-green);
    font-weight: bold;
  }
  
  .questions-list li::before {
    content: '?';
    position: absolute;
    left: 0;
    color: #dc143c;
    font-weight: bold;
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .generic-item-view {
      gap: 1.5rem;
    }
    
    section {
      padding: 1rem;
    }
    
    .metadata-grid {
      grid-template-columns: 1fr;
    }
    
    .metadata-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.25rem;
    }
  }
</style>