<!--
  Document View Component
  Basic implementation for document content display
-->

<script lang="ts">
  import Icon from '$lib/components/Icon.svelte';
  import GenericItemView from './GenericItemView.svelte';
  
  export let item: any;
  export let contentType: any;
  
  $: hasFile = item.file_path || item.url;
  $: fileName = item.file_path ? item.file_path.split('/').pop() : 'Document';
  $: fileExtension = fileName ? fileName.split('.').pop()?.toLowerCase() : '';
  $: isPDF = fileExtension === 'pdf';
</script>

<div class="document-view">
  {#if hasFile}
    <section class="document-preview">
      <div class="document-header">
        <div class="document-icon">
          <Icon name={isPDF ? 'file-text' : 'file'} size="large" />
        </div>
        <div class="document-info">
          <h3>Document</h3>
          <p class="file-name">{fileName}</p>
          {#if fileExtension}
            <span class="file-type">{fileExtension.toUpperCase()}</span>
          {/if}
        </div>
        {#if item.url || item.file_path}
          <a 
            href={item.url || item.file_path} 
            target="_blank" 
            rel="noopener noreferrer" 
            class="download-btn"
          >
            <Icon name="download" size="small" />
            {isPDF ? 'View PDF' : 'Download'}
          </a>
        {/if}
      </div>
    </section>
  {/if}
  
  <!-- Use generic view for the rest -->
  <GenericItemView {item} {contentType} on:error />
</div>

<style>
  .document-view {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  .document-preview {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
  }
  
  .document-header {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  
  .document-icon {
    color: #4a9eff;
  }
  
  .document-info {
    flex: 1;
  }
  
  .document-info h3 {
    margin: 0 0 0.25rem 0;
    color: var(--neural-green);
    font-size: 1.1rem;
  }
  
  .file-name {
    margin: 0 0 0.25rem 0;
    color: var(--text-primary);
    font-weight: 500;
  }
  
  .file-type {
    background: rgba(74, 158, 255, 0.2);
    color: #4a9eff;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .download-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(74, 158, 255, 0.2);
    color: #4a9eff;
    text-decoration: none;
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.2s;
  }
  
  .download-btn:hover {
    background: rgba(74, 158, 255, 0.3);
    transform: translateY(-1px);
  }
</style>