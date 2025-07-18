<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { fade, fly, scale } from 'svelte/transition';
  import Icon from './Icon.svelte';
  import { floatingChatStore, floatingChatActions, getPageType, getQuickActions } from '$lib/stores/floating-chat';
  import { createStreamingConnection, type StreamingWebSocket } from '$lib/utils/websocket';
  import type { FloatingChatMessage } from '$lib/stores/floating-chat';

  let inputMessage = '';
  let messagesContainer: HTMLElement;
  let ws: StreamingWebSocket | null = null;
  let currentStreamingMessage: FloatingChatMessage | null = null;
  let quickActions: string[] = [];

  $: isOpen = $floatingChatStore.isOpen;
  $: messages = $floatingChatStore.messages;
  $: isLoading = $floatingChatStore.isLoading;
  $: position = $floatingChatStore.position;
  
  // Update quick actions based on current page
  $: {
    const pageType = getPageType($page.url.pathname);
    quickActions = getQuickActions(pageType);
  }

  // Get page context
  function getPageContext() {
    const pathname = $page.url.pathname;
    const pageType = getPageType(pathname);
    
    return {
      url: pathname,
      pageType,
      pageTitle: document.title,
      params: $page.params,
      query: Object.fromEntries($page.url.searchParams),
      // Add item ID if on item detail page
      itemId: pathname.startsWith('/items/') ? $page.params.id : null,
      // Add search query if present
      searchQuery: $page.url.searchParams.get('q')
    };
  }

  // Connect to WebSocket
  function connectWebSocket() {
    const clientId = `floating-${Math.random().toString(36).substring(7)}`;
    
    ws = createStreamingConnection(`/ws/floating-chat/${clientId}`, {
      onConnect: () => {
        console.debug('[FloatingChat] Connected');
      },
      onChunk: (text) => {
        if (currentStreamingMessage) {
          currentStreamingMessage.content += text;
          messages = messages;
          scrollToBottom();
        }
      },
      onComplete: (data) => {
        if (currentStreamingMessage) {
          currentStreamingMessage = null;
          floatingChatActions.setLoading(false);
        }
      },
      onError: (error) => {
        console.error('[FloatingChat] Error:', error);
        floatingChatActions.setLoading(false);
      }
    });

    ws.connect();
  }

  // Send message
  async function sendMessage(message: string = inputMessage) {
    if (!message.trim() || isLoading) return;

    // Add user message
    floatingChatActions.addMessage({
      type: 'user',
      content: message
    });

    inputMessage = '';
    floatingChatActions.setLoading(true);

    // Create assistant message placeholder
    currentStreamingMessage = floatingChatActions.addMessage({
      type: 'assistant',
      content: ''
    });

    scrollToBottom();

    // Send with page context
    if (ws?.isConnected) {
      const context = getPageContext();
      
      ws.send({
        message,
        context: {
          page: context,
          timestamp: new Date().toISOString()
        }
      });
    } else {
      // Reconnect if needed
      connectWebSocket();
      setTimeout(() => sendMessage(message), 500);
    }
  }

  // Scroll to bottom
  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  // Handle key press
  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  // Global keyboard shortcut
  function handleGlobalKeyPress(event: KeyboardEvent) {
    // Cmd/Ctrl + J to toggle floating chat
    if ((event.metaKey || event.ctrlKey) && event.key === 'j') {
      event.preventDefault();
      floatingChatActions.toggle();
    }
    
    // Escape to close
    if (event.key === 'Escape' && isOpen) {
      floatingChatActions.close();
    }
  }

  onMount(() => {
    connectWebSocket();
    document.addEventListener('keydown', handleGlobalKeyPress);
  });

  onDestroy(() => {
    if (ws) {
      ws.close();
    }
    document.removeEventListener('keydown', handleGlobalKeyPress);
  });
</script>

<!-- Floating Button -->
{#if !isOpen}
  <button
    class="floating-chat-button"
    class:bottom-left={position === 'bottom-left'}
    on:click={() => floatingChatActions.open()}
    in:scale={{ duration: 200 }}
    out:scale={{ duration: 200 }}
    title="Open chat (Cmd+J)"
  >
    <Icon name="message-circle" size={24} />
    {#if messages.length > 0}
      <span class="message-count">{messages.length}</span>
    {/if}
  </button>
{/if}

<!-- Chat Window -->
{#if isOpen}
  <div
    class="floating-chat-window"
    class:bottom-left={position === 'bottom-left'}
    in:fly={{ y: 20, duration: 300 }}
    out:fly={{ y: 20, duration: 200 }}
  >
    <!-- Header -->
    <div class="chat-header">
      <div class="header-left">
        <Icon name="brain" size={20} />
        <span>Quick Assistant</span>
      </div>
      <div class="header-actions">
        <button
          class="header-button"
          on:click={() => floatingChatActions.clearMessages()}
          title="Clear messages"
        >
          <Icon name="close" size={16} />
        </button>
        <button
          class="header-button"
          on:click={() => floatingChatActions.close()}
          title="Close (Esc)"
        >
          <Icon name="close" size={16} />
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div class="messages-container" bind:this={messagesContainer}>
      {#if messages.length === 0}
        <div class="empty-state">
          <Icon name="sparkles" size={24} />
          <p>Ask me anything about this page!</p>
          
          {#if quickActions.length > 0}
            <div class="quick-actions">
              {#each quickActions as action}
                <button
                  class="quick-action"
                  on:click={() => sendMessage(action)}
                >
                  {action}
                </button>
              {/each}
            </div>
          {/if}
        </div>
      {:else}
        {#each messages as message}
          <div class="message {message.type}">
            <div class="message-content">
              {message.content}
            </div>
          </div>
        {/each}
        
        {#if isLoading}
          <div class="loading-indicator">
            <Icon name="loader" size={16} class="animate-spin" />
            <span>Thinking...</span>
          </div>
        {/if}
      {/if}
    </div>

    <!-- Input -->
    <div class="input-container">
      <input
        type="text"
        class="chat-input"
        placeholder="Ask about this page..."
        bind:value={inputMessage}
        on:keypress={handleKeyPress}
        disabled={isLoading}
      />
      <button
        class="send-button"
        on:click={() => sendMessage()}
        disabled={!inputMessage.trim() || isLoading}
      >
        <Icon name="send" size={16} />
      </button>
    </div>
  </div>
{/if}

<style>
  /* Floating Button */
  .floating-chat-button {
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 56px;
    height: 56px;
    background: #6366f1;
    border: none;
    border-radius: 28px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: all 0.2s;
    z-index: 1000;
  }

  .floating-chat-button.bottom-left {
    right: auto;
    left: 24px;
  }

  .floating-chat-button:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  }

  .message-count {
    position: absolute;
    top: -4px;
    right: -4px;
    background: #ef4444;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.125rem 0.375rem;
    border-radius: 9999px;
    min-width: 20px;
    text-align: center;
  }

  /* Chat Window */
  .floating-chat-window {
    position: fixed;
    bottom: 96px;
    right: 24px;
    width: 380px;
    height: 600px;
    max-height: 80vh;
    background: #1a1a1a;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    z-index: 999;
  }

  .floating-chat-window.bottom-left {
    right: auto;
    left: 24px;
  }

  /* Header */
  .chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px 16px 0 0;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: white;
    font-weight: 600;
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
  }

  .header-button {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    transition: all 0.2s;
  }

  .header-button:hover {
    background: rgba(255, 255, 255, 0.2);
    color: white;
  }

  /* Messages */
  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    scroll-behavior: smooth;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    color: rgba(255, 255, 255, 0.6);
    gap: 1rem;
  }

  .empty-state p {
    margin: 0;
  }

  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    width: 100%;
    max-width: 280px;
  }

  .quick-action {
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: white;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
  }

  .quick-action:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateX(4px);
  }

  .message {
    margin-bottom: 1rem;
  }

  .message.user {
    text-align: right;
  }

  .message-content {
    display: inline-block;
    padding: 0.75rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    max-width: 85%;
    word-wrap: break-word;
    color: white;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .message.user .message-content {
    background: #6366f1;
  }

  .loading-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.875rem;
    padding: 0.5rem;
  }

  /* Input */
  .input-container {
    display: flex;
    gap: 0.5rem;
    padding: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.05);
    border-radius: 0 0 16px 16px;
  }

  .chat-input {
    flex: 1;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    color: white;
    font-size: 0.875rem;
    transition: all 0.2s;
  }

  .chat-input:focus {
    outline: none;
    border-color: #6366f1;
    background: rgba(255, 255, 255, 0.15);
  }

  .chat-input::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }

  .chat-input:disabled {
    opacity: 0.5;
  }

  .send-button {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #6366f1;
    border: none;
    border-radius: 8px;
    color: white;
    cursor: pointer;
    transition: all 0.2s;
  }

  .send-button:hover:not(:disabled) {
    background: #5558e3;
    transform: scale(1.05);
  }

  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Scrollbar */
  .messages-container::-webkit-scrollbar {
    width: 6px;
  }

  .messages-container::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
  }

  .messages-container::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
  }

  /* Responsive */
  @media (max-width: 640px) {
    .floating-chat-window {
      position: fixed;
      inset: 0;
      width: 100%;
      height: 100%;
      max-height: 100%;
      bottom: 0;
      right: 0;
      border-radius: 0;
    }

    .chat-header {
      border-radius: 0;
    }

    .input-container {
      border-radius: 0;
    }
  }

  /* Utility classes */
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>