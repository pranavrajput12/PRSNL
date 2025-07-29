<!--
  Code View Component
  Basic implementation for code content display
-->

<script lang="ts">
  import Icon from '$lib/components/Icon.svelte';
  import MarkdownViewer from '$lib/components/development/MarkdownViewer.svelte';
  import GenericItemView from './GenericItemView.svelte';
  
  export let item: any;
  export let contentType: any;
  
  $: hasCode = item.code_snippets && item.code_snippets.length > 0;
  $: programmingLanguage = item.programming_language || 'text';
</script>

<div class="code-view">
  {#if hasCode}
    <section class="code-snippets">
      <h2>Code Snippets</h2>
      {#each item.code_snippets as snippet, index}
        <div class="code-snippet">
          <div class="snippet-header">
            <span class="snippet-title">Snippet {index + 1}</span>
            {#if programmingLanguage}
              <span class="language-badge">{programmingLanguage}</span>
            {/if}
          </div>
          <div class="snippet-content">
            <pre><code class="language-{programmingLanguage}">{snippet}</code></pre>
          </div>
        </div>
      {/each}
    </section>
  {/if}
  
  <!-- Use generic view for the rest -->
  <GenericItemView {item} {contentType} on:error />
</div>

<style>
  .code-view {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  .code-snippets {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
  }
  
  .code-snippets h2 {
    margin: 0 0 1rem 0;
    color: var(--neural-green);
    font-size: 1.25rem;
  }
  
  .code-snippet {
    margin-bottom: 1.5rem;
  }
  
  .code-snippet:last-child {
    margin-bottom: 0;
  }
  
  .snippet-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  
  .snippet-title {
    color: var(--text-primary);
    font-weight: 600;
  }
  
  .language-badge {
    background: rgba(132, 204, 22, 0.2);
    color: #84cc16;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }
  
  .snippet-content {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 100, 0.2);
    border-radius: 8px;
    overflow-x: auto;
  }
  
  .snippet-content pre {
    margin: 0;
    padding: 1rem;
  }
  
  .snippet-content code {
    color: var(--neural-green);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.875rem;
    line-height: 1.5;
  }
</style>