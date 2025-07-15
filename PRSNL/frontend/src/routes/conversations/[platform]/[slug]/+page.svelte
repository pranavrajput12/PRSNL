<script>
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import SkeletonLoader from '$lib/components/SkeletonLoader.svelte';
  import SafeHTML from '$lib/components/SafeHTML.svelte';
  import ConversationIntelligence from '$lib/components/ConversationIntelligence.svelte';

  let conversation = null;
  let loading = true;
  let error = null;

  // Load more functionality for messages
  let messagesPerLoad = 10;
  let loadedMessagesCount = 10;
  let loadingMore = false;
  $: displayedMessages = conversation ? conversation.messages.slice(0, loadedMessagesCount) : [];
  $: hasMoreMessages = conversation && loadedMessagesCount < conversation.messages.length;

  // Platform configuration
  const platformConfig = {
    chatgpt: { icon: 'message-circle', color: '#10a37f', name: 'ChatGPT' },
    claude: { icon: 'brain', color: '#AA7CFF', name: 'Claude' },
    perplexity: { icon: 'search', color: '#20808D', name: 'Perplexity' },
    bard: { icon: 'sparkles', color: '#4285F4', name: 'Bard' },
  };

  // Category configuration
  const categoryConfig = {
    learning: { icon: 'book-open', color: '#4a9eff' },
    development: { icon: 'code', color: '#00ff88' },
    thoughts: { icon: 'message-square', color: '#f59e0b' },
    reference: { icon: 'bookmark', color: '#8b5cf6' },
    creative: { icon: 'palette', color: '#dc143c' },
  };

  $: platform = platformConfig[$page.params.platform] || {
    icon: 'message-circle',
    color: '#666',
    name: $page.params.platform,
  };

  $: category = conversation?.neural_category ? categoryConfig[conversation.neural_category] : null;

  onMount(async () => {
    await loadConversation();
  });

  async function loadConversation() {
    try {
      loading = true;
      error = null;

      const response = await fetch(
        `/api/conversations/by-slug/${$page.params.platform}/${$page.params.slug}`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Conversation not found');
        }
        throw new Error('Failed to load conversation');
      }

      conversation = await response.json();
    } catch (err) {
      error = err.message;
      console.error('Error loading conversation:', err);
    } finally {
      loading = false;
    }
  }

  function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  }

  function formatMessageTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  }

  function getRoleIcon(role) {
    switch (role) {
      case 'user':
        return 'user';
      case 'assistant':
        return platform.icon;
      case 'system':
        return 'settings';
      default:
        return 'message-circle';
    }
  }

  function getRoleColor(role) {
    switch (role) {
      case 'user':
        return 'var(--text-primary)';
      case 'assistant':
        return platform.color;
      case 'system':
        return 'var(--text-secondary)';
      default:
        return 'var(--text-secondary)';
    }
  }

  function handleBack() {
    goto('/conversations');
  }

  async function loadMoreMessages() {
    if (loadingMore || !hasMoreMessages) return;

    loadingMore = true;

    // Simulate loading delay for smooth UX
    await new Promise((resolve) => setTimeout(resolve, 500));

    loadedMessagesCount = Math.min(
      loadedMessagesCount + messagesPerLoad,
      conversation.messages.length
    );

    loadingMore = false;
  }
</script>

<svelte:head>
  <title>{conversation?.title || 'Loading...'} - Neural Echo | PRSNL</title>
</svelte:head>

<div class="conversation-page">
  {#if loading}
    <div class="loading-container">
      <SkeletonLoader type="text" />
      <SkeletonLoader type="paragraph" />
      <SkeletonLoader type="paragraph" />
    </div>
  {:else if error}
    <div class="error-container">
      <Icon name="alert-circle" size={48} />
      <h2>Error loading conversation</h2>
      <p>{error}</p>
      <button on:click={handleBack} class="back-button">
        <Icon name="arrow-left" size={16} />
        Back to Neural Echo
      </button>
    </div>
  {:else if conversation}
    <!-- Header -->
    <header class="conversation-header">
      <div class="header-top">
        <button on:click={handleBack} class="back-button">
          <Icon name="arrow-left" size={20} />
          <span>Neural Echo</span>
        </button>

        <a
          href={conversation.source_url}
          target="_blank"
          rel="noopener noreferrer"
          class="source-button"
          title="View original ChatGPT conversation"
        >
          <Icon name="external-link" size={16} />
          <span>View on {platform.name}</span>
        </a>
      </div>

      <div class="header-content">
        <div class="platform-indicator" style="--platform-color: {platform.color}">
          <Icon name={platform.icon} size={24} color="white" />
          <span>{platform.name}</span>
        </div>

        <h1 class="conversation-title">{conversation.title}</h1>

        <div class="conversation-meta">
          <time>{formatTimestamp(conversation.timestamp)}</time>
          <span class="separator">•</span>
          <span>{conversation.message_count} messages</span>
          {#if conversation.total_tokens}
            <span class="separator">•</span>
            <span>{conversation.total_tokens.toLocaleString()} tokens</span>
          {/if}
        </div>

        <div class="meta-tags">
          {#if category}
            <div class="category-badge" style="--category-color: {category.color}">
              <Icon name={category.icon} size={16} />
              <span>{conversation.neural_category}</span>
              {#if conversation.categorization_confidence}
                <span class="confidence"
                  >{Math.round(conversation.categorization_confidence * 100)}%</span
                >
              {/if}
            </div>
          {/if}

          {#if conversation.tags && conversation.tags.length > 0}
            <div class="tags-list">
              {#each conversation.tags as tag}
                <span class="tag">{tag}</span>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </header>

    <!-- AI Intelligence Analysis -->
    <div class="intelligence-section">
      <ConversationIntelligence conversationId={conversation.id} />
    </div>

    <!-- Messages Thread -->
    <div class="messages-container">
      <!-- Messages Info -->
      <div class="messages-info">
        <span>Showing {displayedMessages.length} of {conversation.messages.length} messages</span>
      </div>

      {#each displayedMessages as message, index}
        <div class="message {message.role}" style="--role-color: {getRoleColor(message.role)}">
          <div class="message-header">
            <div class="message-role">
              <Icon name={getRoleIcon(message.role)} size={20} />
              <span>{message.role === 'user' ? 'You' : platform.name}</span>
            </div>
            <time>{formatMessageTime(message.timestamp)}</time>
          </div>

          <div class="message-content">
            {#if message.content_text}
              <p>{message.content_text}</p>
            {:else if message.content?.text}
              <p>{message.content.text}</p>
            {:else if message.content?.markdown}
              <SafeHTML html={message.content.markdown} />
            {:else if message.content?.html}
              <SafeHTML html={message.content.html} />
            {:else}
              <p><em>No content available</em></p>
            {/if}
          </div>

          {#if index < displayedMessages.length - 1}
            <div class="message-divider"></div>
          {/if}
        </div>
      {/each}

      <!-- Load More Button -->
      {#if hasMoreMessages}
        <div class="load-more-container">
          <button
            on:click={loadMoreMessages}
            class="load-more-btn"
            disabled={loadingMore}
            class:loading={loadingMore}
          >
            {#if loadingMore}
              <div class="spinner"></div>
              <span>Loading messages...</span>
            {:else}
              <Icon name="chevron-down" size={20} />
              <span
                >Load {Math.min(
                  messagesPerLoad,
                  conversation.messages.length - loadedMessagesCount
                )} more messages</span
              >
            {/if}
          </button>
        </div>
      {:else if conversation && conversation.messages.length > messagesPerLoad}
        <div class="all-loaded">
          <Icon name="check-circle" size={20} />
          <span>All messages loaded</span>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .conversation-page {
    min-height: 100vh;
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  .loading-container,
  .error-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 50vh;
    gap: 1rem;
    text-align: center;
  }

  .error-container h2 {
    margin: 0;
    color: var(--error);
  }

  /* Header Styles */
  .conversation-header {
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .back-button {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .back-button:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    transform: translateX(-2px);
  }

  .source-button {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--accent);
    color: white;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    text-decoration: none;
    transition: all 0.2s ease;
  }

  .source-button:hover {
    background: var(--accent-hover);
    transform: translateY(-1px);
  }

  .header-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .platform-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 1rem;
    background: var(--platform-color);
    color: white;
    border-radius: 2rem;
    font-size: 1rem;
    font-weight: 600;
    width: fit-content;
  }

  .conversation-title {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.3;
    color: var(--text-primary);
  }

  .conversation-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .separator {
    opacity: 0.5;
  }

  .meta-tags {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .category-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.875rem;
    background: rgba(var(--category-color-rgb), 0.1);
    border: 1px solid var(--category-color);
    border-radius: 2rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--category-color);
  }

  .confidence {
    opacity: 0.7;
    font-size: 0.75rem;
  }

  .tags-list {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .tag {
    padding: 0.25rem 0.625rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  /* Intelligence Section */
  .intelligence-section {
    margin: 2rem 0;
  }

  /* Messages Styles */
  .messages-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  /* Messages Info Styles */
  .messages-info {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 1rem;
  }

  /* Load More Styles */
  .load-more-container {
    display: flex;
    justify-content: center;
    padding: 2rem 0;
    margin-top: 2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .load-more-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 2rem;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 2rem;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
  }

  .load-more-btn:hover:not(:disabled) {
    background: var(--accent-hover);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(74, 158, 255, 0.3);
  }

  .load-more-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    transform: none;
  }

  .load-more-btn.loading {
    padding-left: 2.5rem;
  }

  .spinner {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    position: absolute;
    left: 1rem;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .all-loaded {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 1.5rem;
    margin-top: 2rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .all-loaded :global(svg) {
    color: var(--success, #10b981);
  }

  .message {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 0.75rem;
    padding: 1.5rem;
    position: relative;
    transition: all 0.2s ease;
  }

  .message:hover {
    background: rgba(255, 255, 255, 0.03);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .message.user {
    border-left: 3px solid var(--accent);
  }

  .message.assistant {
    border-left: 3px solid var(--role-color);
  }

  .message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .message-role {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: var(--role-color);
  }

  .message-header time {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .message-content {
    color: var(--text-primary);
    line-height: 1.6;
  }

  .message-content :global(p) {
    margin: 0 0 1rem 0;
  }

  .message-content :global(p:last-child) {
    margin-bottom: 0;
  }

  .message-content :global(pre) {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    padding: 1rem;
    overflow-x: auto;
    margin: 1rem 0;
  }

  .message-content :global(code) {
    background: rgba(255, 255, 255, 0.1);
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
    font-size: 0.875em;
  }

  .message-content :global(pre code) {
    background: none;
    padding: 0;
  }

  .message-content :global(ul),
  .message-content :global(ol) {
    margin: 0 0 1rem 0;
    padding-left: 1.5rem;
  }

  .message-content :global(li) {
    margin-bottom: 0.5rem;
  }

  .message-content :global(blockquote) {
    border-left: 3px solid var(--accent);
    margin: 1rem 0;
    padding-left: 1rem;
    color: var(--text-secondary);
  }

  .message-divider {
    position: absolute;
    bottom: -0.75rem;
    left: 50%;
    transform: translateX(-50%);
    width: 40px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .conversation-page {
      padding: 1rem;
    }

    .conversation-title {
      font-size: 1.5rem;
    }

    .conversation-meta {
      flex-wrap: wrap;
    }

    .message {
      padding: 1rem;
    }

    .header-top {
      flex-wrap: wrap;
      gap: 1rem;
    }

    .load-more-btn {
      padding: 0.875rem 1.5rem;
      font-size: 0.875rem;
    }

    .load-more-btn.loading {
      padding-left: 2rem;
    }

    .spinner {
      left: 0.75rem;
      width: 16px;
      height: 16px;
    }
  }

  /* Dark mode enhancements */
  @media (prefers-color-scheme: dark) {
    .message {
      background: rgba(255, 255, 255, 0.01);
    }

    .message:hover {
      background: rgba(255, 255, 255, 0.02);
    }
  }
</style>
