<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Icon from './Icon.svelte';
  
  export let conversation: any;
  
  const dispatch = createEventDispatcher();
  
  // Platform configuration (matching archive page)
  const platformConfig: Record<string, { icon: string; color: string; name: string }> = {
    chatgpt: { icon: 'message-circle', color: '#10a37f', name: 'ChatGPT' },
    claude: { icon: 'brain', color: '#AA7CFF', name: 'Claude' },
    perplexity: { icon: 'search', color: '#20808D', name: 'Perplexity' },
    bard: { icon: 'sparkles', color: '#4285F4', name: 'Bard' }
  };
  
  // Neural category icons
  const categoryIcons: Record<string, string> = {
    learning: 'book-open',
    development: 'code',
    thoughts: 'message-square',
    reference: 'bookmark',
    creative: 'palette'
  };
  
  $: platform = platformConfig[conversation.platform] || {
    icon: 'message-circle',
    color: '#666',
    name: conversation.platform
  };
  
  $: categoryIcon = categoryIcons[conversation.neural_category] || 'brain';
  
  function formatTimestamp(timestamp: string | Date) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  }
  
  function handleClick() {
    dispatch('click', conversation);
  }
  
  // Extract preview - prefer AI summary if available
  $: preview = conversation.summary?.substring(0, 150) ||
               conversation.messages?.[0]?.content?.text?.substring(0, 150) || 
               'No preview available';
</script>

<article
  class="conversation-card"
  on:click={handleClick}
  on:keydown={(e) => e.key === 'Enter' && handleClick()}
  tabindex="0"
  role="button"
  style="--platform-color: {platform.color}"
>
  <header class="card-header">
    <div class="platform-badge">
      <Icon name={platform.icon} size={16} color="white" />
      <span>{platform.name}</span>
    </div>
    
    <time class="timestamp">{formatTimestamp(conversation.timestamp)}</time>
  </header>
  
  <div class="card-content">
    <h3 class="title">{conversation.title}</h3>
    
    <p class="preview">{preview}...</p>
    
    <div class="card-meta">
      {#if conversation.neural_category}
        <div class="category-tag">
          <Icon name={categoryIcon} size={14} />
          <span>{conversation.neural_category}</span>
        </div>
      {/if}
      
      <div class="message-count">
        <Icon name="message-square" size={14} />
        <span>{conversation.message_count} messages</span>
      </div>
      
      {#if conversation.processing_status === 'completed'}
        <div class="ai-processed" title="AI Intelligence Available">
          <Icon name="brain" size={14} />
        </div>
      {/if}
    </div>
  </div>
  
  <div class="card-footer">
    <a 
      href={conversation.source_url}
      target="_blank"
      rel="noopener noreferrer"
      class="source-link"
      on:click|stopPropagation
      title="View original conversation"
    >
      <Icon name="external-link" size={14} />
    </a>
  </div>
</article>

<style>
  .conversation-card {
    background: var(--bg-secondary);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.75rem;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .conversation-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--platform-color);
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .conversation-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    border-color: var(--platform-color);
  }
  
  .conversation-card:hover::before {
    opacity: 1;
  }
  
  .conversation-card:focus {
    outline: 2px solid var(--platform-color);
    outline-offset: 2px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .platform-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.75rem;
    background: var(--platform-color);
    color: white;
    border-radius: 2rem;
    font-size: 0.875rem;
    font-weight: 600;
  }
  
  .timestamp {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
  
  .card-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .title {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .preview {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    flex: 1;
  }
  
  .card-meta {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-top: auto;
    padding-top: 0.75rem;
  }
  
  .category-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.625rem;
    background: rgba(74, 158, 255, 0.1);
    border: 1px solid rgba(74, 158, 255, 0.2);
    border-radius: 1rem;
    font-size: 0.75rem;
    color: var(--accent);
    font-weight: 500;
  }
  
  .message-count {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    color: var(--text-secondary);
    font-size: 0.75rem;
  }
  
  .ai-processed {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.75rem;
    height: 1.75rem;
    background: linear-gradient(135deg, rgba(74, 158, 255, 0.2), rgba(140, 82, 255, 0.2));
    border: 1px solid rgba(140, 82, 255, 0.3);
    border-radius: 50%;
    color: var(--accent-secondary);
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0% {
      box-shadow: 0 0 0 0 rgba(140, 82, 255, 0.4);
    }
    70% {
      box-shadow: 0 0 0 8px rgba(140, 82, 255, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(140, 82, 255, 0);
    }
  }
  
  .card-footer {
    position: absolute;
    bottom: 1rem;
    right: 1rem;
  }
  
  .source-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    color: var(--text-secondary);
    transition: all 0.2s ease;
  }
  
  .source-link:hover {
    background: var(--platform-color);
    border-color: var(--platform-color);
    color: white;
    transform: scale(1.1);
  }
  
  /* Responsive adjustments */
  @media (max-width: 768px) {
    .conversation-card {
      padding: 1rem;
    }
    
    .title {
      font-size: 1rem;
    }
    
    .preview {
      -webkit-line-clamp: 2;
    }
  }
  
  /* Dark mode enhancements */
  @media (prefers-color-scheme: dark) {
    .conversation-card {
      background: rgba(255, 255, 255, 0.02);
    }
    
    .conversation-card:hover {
      background: rgba(255, 255, 255, 0.04);
    }
  }
</style>