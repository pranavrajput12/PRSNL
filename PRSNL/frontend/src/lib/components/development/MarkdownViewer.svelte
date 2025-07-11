<script lang="ts">
  import { onMount } from 'svelte';
  import SafeHTML from '$lib/components/SafeHTML.svelte';
  import { lazyLoadMarkdownProcessor, loadingStates } from '$lib/utils/lazyLoad';
  
  export let content: string = '';
  export let enableSyntaxHighlight: boolean = true;
  export let enableLineNumbers: boolean = false;
  export let theme: 'dark' | 'neural' = 'neural';
  
  let renderedHTML: string = '';
  let copyNotifications: { [key: string]: boolean } = {};
  let markdownProcessor: any = null;
  let isProcessorLoading = false;
  
  $: isLoading = $loadingStates['markdown-processor'] || isProcessorLoading;
  
  $: if (content && markdownProcessor) {
    renderMarkdown();
  }
  
  async function loadProcessor() {
    if (markdownProcessor || isProcessorLoading) return;
    
    try {
      isProcessorLoading = true;
      markdownProcessor = await lazyLoadMarkdownProcessor();
      
      if (content) {
        renderMarkdown();
      }
    } catch (error) {
      console.error('Failed to load markdown processor:', error);
      // Fallback to plain text
      renderedHTML = `<pre>${content}</pre>`;
    } finally {
      isProcessorLoading = false;
    }
  }
  
  function renderMarkdown() {
    if (!markdownProcessor || !content) return;
    
    try {
      renderedHTML = markdownProcessor.marked(content);
    } catch (e) {
      console.error('Markdown parsing error:', e);
      renderedHTML = `<pre>${content}</pre>`;
    }
  }
  
  function addLineNumbers(code: string): string {
    const lines = code.split('\n');
    return lines.map((line, i) => 
      `<span class="line-number">${i + 1}</span>${line}`
    ).join('\n');
  }
  
  async function copyCode(codeBlock: HTMLElement, blockId: string) {
    const code = codeBlock.textContent || '';
    try {
      await navigator.clipboard.writeText(code);
      copyNotifications[blockId] = true;
      setTimeout(() => {
        copyNotifications[blockId] = false;
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }
  
  onMount(async () => {
    // Load markdown processor when component mounts
    await loadProcessor();
    
    // Add copy buttons to code blocks
    const codeBlocks = document.querySelectorAll('.markdown-viewer pre code');
    codeBlocks.forEach((block, index) => {
      const blockId = `code-block-${index}`;
      const pre = block.parentElement;
      if (!pre) return;
      
      // Add line numbers if enabled
      if (enableLineNumbers && block.innerHTML) {
        block.innerHTML = addLineNumbers(block.innerHTML);
      }
      
      // Create copy button
      const copyBtn = document.createElement('button');
      copyBtn.className = 'copy-button';
      copyBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
      copyBtn.title = 'Copy code';
      
      copyBtn.addEventListener('click', () => copyCode(block as HTMLElement, blockId));
      
      // Add notification span
      const notification = document.createElement('span');
      notification.className = 'copy-notification';
      notification.textContent = 'Copied!';
      notification.style.display = 'none';
      
      pre.style.position = 'relative';
      pre.appendChild(copyBtn);
      pre.appendChild(notification);
      
      // Update notification visibility
      $: if (copyNotifications[blockId]) {
        notification.style.display = 'block';
      } else {
        notification.style.display = 'none';
      }
    });
  });
</script>

{#if isLoading}
  <div class="markdown-loading">
    <div class="loading-pulse"></div>
    <span>Loading markdown processor...</span>
  </div>
{:else}
  <div class="markdown-viewer {theme}">
    <SafeHTML content={renderedHTML} />
  </div>
{/if}

<style>
  .markdown-viewer {
    color: var(--text-primary, #e0e0e0);
    line-height: 1.7;
    font-size: 1rem;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  
  /* Neural theme specific styles */
  .markdown-viewer.neural {
    --code-bg: rgba(0, 255, 136, 0.05);
    --code-border: rgba(0, 255, 136, 0.2);
    --code-text: #00ff88;
    --inline-code-bg: rgba(0, 255, 136, 0.1);
    --inline-code-text: #00ff88;
    --link-color: #00ff88;
    --link-hover: #DC143C;
  }
  
  /* Dark theme */
  .markdown-viewer.dark {
    --code-bg: #1e1e1e;
    --code-border: #333;
    --code-text: #d4d4d4;
    --inline-code-bg: #2d2d2d;
    --inline-code-text: #ce9178;
    --link-color: #4a9eff;
    --link-hover: #6bb6ff;
  }
  
  /* Headings */
  .markdown-viewer :global(h1),
  .markdown-viewer :global(h2),
  .markdown-viewer :global(h3),
  .markdown-viewer :global(h4),
  .markdown-viewer :global(h5),
  .markdown-viewer :global(h6) {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: 600;
    line-height: 1.25;
  }
  
  .markdown-viewer :global(h1) { font-size: 2em; }
  .markdown-viewer :global(h2) { font-size: 1.5em; }
  .markdown-viewer :global(h3) { font-size: 1.25em; }
  .markdown-viewer :global(h4) { font-size: 1em; }
  
  /* Paragraphs and lists */
  .markdown-viewer :global(p) {
    margin-bottom: 1em;
  }
  
  .markdown-viewer :global(ul),
  .markdown-viewer :global(ol) {
    margin-bottom: 1em;
    padding-left: 2em;
  }
  
  .markdown-viewer :global(li) {
    margin-bottom: 0.25em;
  }
  
  /* Links */
  .markdown-viewer :global(a) {
    color: var(--link-color);
    text-decoration: none;
    transition: color 0.2s ease;
  }
  
  .markdown-viewer :global(a:hover) {
    color: var(--link-hover);
    text-decoration: underline;
  }
  
  /* Inline code */
  .markdown-viewer :global(code:not(pre code)) {
    background: var(--inline-code-bg);
    color: var(--inline-code-text);
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 0.875em;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
  }
  
  /* Code blocks */
  .markdown-viewer :global(pre) {
    background: var(--code-bg);
    border: 1px solid var(--code-border);
    border-radius: 8px;
    padding: 1em;
    margin-bottom: 1em;
    overflow-x: auto;
    position: relative;
  }
  
  .markdown-viewer :global(pre code) {
    background: transparent;
    color: var(--code-text);
    padding: 0;
    font-size: 0.875em;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    line-height: 1.5;
  }
  
  /* Copy button */
  .markdown-viewer :global(.copy-button) {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 4px;
    padding: 0.25rem 0.5rem;
    cursor: pointer;
    opacity: 0;
    transition: all 0.2s ease;
    color: #00ff88;
  }
  
  .markdown-viewer :global(pre:hover .copy-button) {
    opacity: 1;
  }
  
  .markdown-viewer :global(.copy-button:hover) {
    background: rgba(0, 255, 136, 0.2);
    transform: translateY(-1px);
  }
  
  .markdown-viewer :global(.copy-notification) {
    position: absolute;
    top: 0.5rem;
    right: 3.5rem;
    background: #00ff88;
    color: #000;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    animation: fadeIn 0.2s ease;
  }
  
  /* Line numbers */
  .markdown-viewer :global(.line-number) {
    display: inline-block;
    width: 3em;
    padding-right: 1em;
    text-align: right;
    color: rgba(255, 255, 255, 0.3);
    user-select: none;
  }
  
  /* Blockquotes */
  .markdown-viewer :global(blockquote) {
    border-left: 4px solid var(--code-border);
    padding-left: 1em;
    margin-left: 0;
    margin-bottom: 1em;
    color: rgba(255, 255, 255, 0.7);
  }
  
  /* Tables */
  .markdown-viewer :global(table) {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1em;
  }
  
  .markdown-viewer :global(th),
  .markdown-viewer :global(td) {
    border: 1px solid var(--code-border);
    padding: 0.5em 1em;
    text-align: left;
  }
  
  .markdown-viewer :global(th) {
    background: var(--code-bg);
    font-weight: 600;
  }
  
  /* Syntax highlighting */
  .markdown-viewer.neural :global(.hljs-keyword) { color: #ff6b6b; }
  .markdown-viewer.neural :global(.hljs-string) { color: #4ecdc4; }
  .markdown-viewer.neural :global(.hljs-function) { color: #ffe66d; }
  .markdown-viewer.neural :global(.hljs-number) { color: #ff8cc8; }
  .markdown-viewer.neural :global(.hljs-comment) { color: #666; font-style: italic; }
  .markdown-viewer.neural :global(.hljs-class) { color: #a8e6cf; }
  .markdown-viewer.neural :global(.hljs-variable) { color: #ffd93d; }
  .markdown-viewer.neural :global(.hljs-type) { color: #95e1d3; }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  /* Loading state */
  .markdown-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    gap: 1rem;
    color: rgba(0, 255, 136, 0.7);
  }
  
  .loading-pulse {
    width: 24px;
    height: 24px;
    border: 2px solid rgba(0, 255, 136, 0.3);
    border-top: 2px solid #00ff88;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  /* Responsive */
  @media (max-width: 768px) {
    .markdown-viewer {
      font-size: 0.95rem;
    }
    
    .markdown-viewer :global(pre) {
      padding: 0.75em;
      font-size: 0.8rem;
    }
  }
</style>