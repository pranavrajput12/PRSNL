<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { spring } from 'svelte/motion';
  import Icon from './Icon.svelte';
  
  export let message: string = '';
  export let isStreaming: boolean = false;
  export let role: 'user' | 'assistant' = 'assistant';
  export let showAvatar: boolean = true;
  export let onComplete: (() => void) | null = null;
  
  let displayedText = '';
  let currentIndex = 0;
  let streamInterval: NodeJS.Timeout | null = null;
  let cursorVisible = true;
  let cursorInterval: NodeJS.Timeout | null = null;
  let container: HTMLElement;
  
  // Spring animation for smooth appearance
  const progress = spring(0, {
    stiffness: 0.05,
    damping: 0.9
  });
  
  // Stream text character by character
  function startStreaming() {
    if (streamInterval) clearInterval(streamInterval);
    
    streamInterval = setInterval(() => {
      if (currentIndex < message.length) {
        displayedText += message[currentIndex];
        currentIndex++;
        progress.set(currentIndex / message.length);
        
        // Auto-scroll
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      } else {
        stopStreaming();
        if (onComplete) onComplete();
      }
    }, 30); // Adjust speed as needed
  }
  
  function stopStreaming() {
    if (streamInterval) {
      clearInterval(streamInterval);
      streamInterval = null;
    }
    isStreaming = false;
  }
  
  function startCursorBlink() {
    if (cursorInterval) clearInterval(cursorInterval);
    
    cursorInterval = setInterval(() => {
      cursorVisible = !cursorVisible;
    }, 500);
  }
  
  function stopCursorBlink() {
    if (cursorInterval) {
      clearInterval(cursorInterval);
      cursorInterval = null;
    }
    cursorVisible = false;
  }
  
  // React to message changes
  $: if (message && isStreaming) {
    displayedText = '';
    currentIndex = 0;
    startStreaming();
    startCursorBlink();
  } else if (message && !isStreaming) {
    displayedText = message;
    stopCursorBlink();
  }
  
  onDestroy(() => {
    stopStreaming();
    stopCursorBlink();
  });
</script>

<div class="message-container {role}" bind:this={container}>
  {#if showAvatar}
    <div class="avatar" in:fly={{ x: -20, duration: 300 }}>
      <Icon name={role === 'user' ? 'user' : 'brain'} />
    </div>
  {/if}
  
  <div class="message-content">
    <div class="message-bubble">
      {#if displayedText}
        <span class="text">{displayedText}</span>
      {/if}
      
      {#if isStreaming && cursorVisible}
        <span class="cursor" transition:fade={{ duration: 150 }}>|</span>
      {/if}
      
      {#if isStreaming && displayedText.length === 0}
        <div class="thinking-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      {/if}
    </div>
    
    {#if isStreaming && displayedText.length > 0}
      <div class="progress-bar">
        <div class="progress-fill" style="width: {$progress * 100}%"></div>
      </div>
    {/if}
  </div>
</div>

<style>
  .message-container {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    animation: slideIn 0.3s ease-out;
  }
  
  .message-container.user {
    flex-direction: row-reverse;
  }
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .avatar {
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-surface);
    border-radius: 50%;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .user .avatar {
    background: var(--color-primary);
    color: white;
  }
  
  .message-content {
    flex: 1;
    max-width: 70%;
  }
  
  .user .message-content {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }
  
  .message-bubble {
    position: relative;
    padding: 1rem 1.25rem;
    background: var(--color-surface);
    border-radius: 1.25rem;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    min-height: 2.5rem;
    display: flex;
    align-items: center;
  }
  
  .user .message-bubble {
    background: var(--color-primary);
    color: white;
  }
  
  .text {
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
  }
  
  .cursor {
    display: inline-block;
    width: 2px;
    height: 1.2em;
    background: var(--color-primary);
    margin-left: 2px;
    vertical-align: text-bottom;
  }
  
  .user .cursor {
    background: white;
  }
  
  .thinking-indicator {
    display: flex;
    gap: 4px;
  }
  
  .thinking-indicator span {
    width: 8px;
    height: 8px;
    background: var(--color-text-muted);
    border-radius: 50%;
    animation: thinking 1.4s infinite;
  }
  
  .thinking-indicator span:nth-child(1) {
    animation-delay: 0s;
  }
  
  .thinking-indicator span:nth-child(2) {
    animation-delay: 0.2s;
  }
  
  .thinking-indicator span:nth-child(3) {
    animation-delay: 0.4s;
  }
  
  @keyframes thinking {
    0%, 60%, 100% {
      transform: scale(0.8);
      opacity: 0.5;
    }
    30% {
      transform: scale(1.2);
      opacity: 1;
    }
  }
  
  .progress-bar {
    margin-top: 0.5rem;
    height: 2px;
    background: var(--color-border);
    border-radius: 1px;
    overflow: hidden;
    width: 100%;
    max-width: 200px;
  }
  
  .progress-fill {
    height: 100%;
    background: var(--color-primary);
    transition: width 0.3s ease;
    border-radius: 1px;
  }
  
  /* Dark mode adjustments */
  :global(.dark) .message-bubble {
    background: var(--color-surface);
  }
  
  :global(.dark) .user .message-bubble {
    background: var(--color-primary);
  }
  
  /* Mobile responsiveness */
  @media (max-width: 640px) {
    .message-content {
      max-width: 85%;
    }
    
    .message-bubble {
      padding: 0.75rem 1rem;
      font-size: 0.9375rem;
    }
    
    .avatar {
      width: 2rem;
      height: 2rem;
    }
  }
</style>