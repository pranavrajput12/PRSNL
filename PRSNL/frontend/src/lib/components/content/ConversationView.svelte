<!--
  Conversation View Component
  Basic implementation for conversation content display
-->

<script lang="ts">
  import Icon from '$lib/components/Icon.svelte';
  import GenericItemView from './GenericItemView.svelte';
  
  export let item: any;
  export let contentType: any;
  
  $: hasMessages = item.messages && item.messages.length > 0;
  $: platform = item.platform || 'Unknown';
</script>

<div class="conversation-view">
  {#if hasMessages}
    <section class="conversation-messages">
      <div class="conversation-header">
        <h2>Conversation</h2>
        <div class="platform-badge">
          <Icon name="message-circle" size="small" />
          {platform}
        </div>
      </div>
      
      <div class="messages-container">
        {#each item.messages as message, index}
          <div class="message {message.role || 'user'}">
            <div class="message-header">
              <span class="message-role">{message.role || 'User'}</span>
              {#if message.timestamp}
                <span class="message-time">{new Date(message.timestamp).toLocaleTimeString()}</span>
              {/if}
            </div>
            <div class="message-content">{message.content}</div>
          </div>
        {/each}
      </div>
    </section>
  {/if}
  
  <!-- Use generic view for the rest -->
  <GenericItemView {item} {contentType} on:error />
</div>

<style>
  .conversation-view {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  .conversation-messages {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
  }
  
  .conversation-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }
  
  .conversation-header h2 {
    margin: 0;
    color: var(--neural-green);
    font-size: 1.25rem;
  }
  
  .platform-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(236, 72, 153, 0.2);
    color: #ec4899;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
  }
  
  .messages-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    max-height: 400px;
    overflow-y: auto;
  }
  
  .message {
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .message.user {
    background: rgba(0, 255, 100, 0.05);
    border-color: rgba(0, 255, 100, 0.2);
    margin-left: 2rem;
  }
  
  .message.assistant {
    background: rgba(220, 20, 60, 0.05);
    border-color: rgba(220, 20, 60, 0.2);
    margin-right: 2rem;
  }
  
  .message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  
  .message-role {
    font-weight: 600;
    text-transform: capitalize;
    font-size: 0.875rem;
  }
  
  .message.user .message-role {
    color: var(--neural-green);
  }
  
  .message.assistant .message-role {
    color: #dc143c;
  }
  
  .message-time {
    color: var(--text-secondary);
    font-size: 0.75rem;
  }
  
  .message-content {
    color: var(--text-primary);
    line-height: 1.6;
    white-space: pre-wrap;
  }
</style>