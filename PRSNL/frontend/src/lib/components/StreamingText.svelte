<!-- 
  StreamingText.svelte
  A component that shows text appearing word-by-word with typing animation
-->
<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { fade } from 'svelte/transition';

  // Props
  export let text = ''; // Final text to display
  export let streamingText = ''; // Text that's currently streaming in
  export let isStreaming = false; // Whether text is currently streaming
  export let speed = 30; // Speed of typing animation (ms per word)
  export let showCursor = true; // Whether to show the typing cursor
  export let cursorBlinkSpeed = 530; // Cursor blink speed in ms
  export let autoScroll = true; // Whether to auto-scroll as text appears

  // Internal state
  let displayedText = ''; // Text currently displayed
  let words: string[] = []; // Words to display
  let currentWordIndex = 0; // Current word index
  let typingInterval: number | null = null; // Interval for typing animation
  let cursorVisible = true; // Whether cursor is currently visible
  let cursorInterval: number | null = null; // Interval for cursor blinking
  let container: HTMLElement; // Reference to container element

  const dispatch = createEventDispatcher();

  // Watch for changes to streaming text
  $: if (streamingText !== displayedText && isStreaming) {
    // Split the new streaming text into words
    words = streamingText.split(' ');

    // If we're starting fresh, reset the displayed text
    if (!displayedText) {
      displayedText = '';
      currentWordIndex = 0;
      startTyping();
    }
  }

  // When isStreaming changes to false, show the full text
  $: if (!isStreaming && text) {
    stopTyping();
    displayedText = text;
  }

  // Start the typing animation
  function startTyping() {
    // Clear any existing interval
    if (typingInterval) {
      clearInterval(typingInterval);
    }

    // Start a new interval
    typingInterval = window.setInterval(() => {
      if (currentWordIndex < words.length) {
        // Add the next word
        if (currentWordIndex === 0) {
          displayedText = words[currentWordIndex];
        } else {
          displayedText += ' ' + words[currentWordIndex];
        }

        currentWordIndex++;

        // Auto-scroll if enabled
        if (autoScroll && container) {
          setTimeout(() => {
            container.scrollTop = container.scrollHeight;
          }, 0);
        }

        // Dispatch progress event
        dispatch('progress', {
          progress: currentWordIndex / words.length,
          currentWord: currentWordIndex,
          totalWords: words.length,
        });
      } else {
        // All words displayed, stop typing
        stopTyping();

        // Dispatch complete event
        dispatch('complete');
      }
    }, speed);

    // Start cursor blinking
    startCursorBlinking();
  }

  // Stop the typing animation
  function stopTyping() {
    if (typingInterval) {
      clearInterval(typingInterval);
      typingInterval = null;
    }
  }

  // Start cursor blinking
  function startCursorBlinking() {
    if (cursorInterval) {
      clearInterval(cursorInterval);
    }

    cursorInterval = window.setInterval(() => {
      cursorVisible = !cursorVisible;
    }, cursorBlinkSpeed);
  }

  // Stop cursor blinking
  function stopCursorBlinking() {
    if (cursorInterval) {
      clearInterval(cursorInterval);
      cursorInterval = null;
    }
    cursorVisible = false;
  }

  // Clean up intervals on component destruction
  onDestroy(() => {
    stopTyping();
    stopCursorBlinking();
  });

  // Initialize cursor blinking on mount
  onMount(() => {
    if (showCursor) {
      startCursorBlinking();
    }
  });
</script>

<div class="streaming-text-container" bind:this={container}>
  <div class="streaming-text">
    {#if displayedText}
      <span>{displayedText}</span>
    {/if}

    {#if showCursor && (isStreaming || cursorVisible)}
      <span class="cursor" transition:fade={{ duration: 150 }}>|</span>
    {/if}
  </div>

  {#if isStreaming}
    <div class="typing-indicator">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
  {/if}
</div>

<style>
  .streaming-text-container {
    position: relative;
    width: 100%;
    overflow-y: auto;
    max-height: inherit;
    line-height: 1.6;
  }

  .streaming-text {
    font-family: var(--font-mono);
    color: var(--text-primary);
    white-space: pre-wrap;
    word-break: break-word;
  }

  .cursor {
    display: inline-block;
    color: var(--accent);
    font-weight: bold;
    animation: blink 0.75s step-start infinite;
    margin-left: 1px;
  }

  .typing-indicator {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 4px;
    margin-top: 8px;
    height: 20px;
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--accent);
    opacity: 0.7;
  }

  .dot:nth-child(1) {
    animation: bounce 1.2s ease-in-out infinite;
  }

  .dot:nth-child(2) {
    animation: bounce 1.2s ease-in-out 0.2s infinite;
  }

  .dot:nth-child(3) {
    animation: bounce 1.2s ease-in-out 0.4s infinite;
  }

  @keyframes blink {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0;
    }
  }

  @keyframes bounce {
    0%,
    100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-4px);
    }
  }
</style>
