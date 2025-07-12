<script lang="ts" type="module">
  /**
   * ProcessingProgress component
   *
   * Shows real-time processing progress when content is being analyzed
   * Provides visual feedback on the progress of AI processing
   * Optimized for performance and accessibility
   * Integrated with WebSocket for real-time updates
   *
   * Performance optimizations:
   * - Efficient progress animations with CSS transitions
   * - Reduced repaints with will-change
   * - Debounced progress updates
   * - Reduced motion support
   * - Optimized DOM updates
   * - RAF-based animation for smoother rendering
   * - Throttled ARIA announcements
   * - Skeleton loading states
   */

  import { onMount, onDestroy, tick, createEventDispatcher } from 'svelte';
  import Icon from './Icon.svelte';
  import { fade, fly } from 'svelte/transition';
  import { websocketStore, connectionStatus, MessageType } from '$lib/stores/websocket';

  // Props with TypeScript types and default values
  export let progress: number = 0; // Progress value (0-100)
  export let status: string = 'Processing'; // Status text
  export let active: boolean = false; // Whether the processing is active
  export let showPercentage: boolean = true; // Whether to show percentage
  export let animated: boolean = true; // Whether to show animation
  export let showIcon: boolean = true; // Whether to show the icon
  export let variant: 'default' | 'compact' | 'minimal' = 'default'; // Display variant
  export let color: string = 'var(--accent)'; // Progress bar color
  export let timeout: number = 0; // Auto-hide after completion (ms, 0 = never)
  export let ariaLabel: string = ''; // Custom aria-label (defaults to status if empty)
  export let showSkeletonOnStart: boolean = true; // Show skeleton loader when starting at 0%
  export let announceInterval: number = 10; // Announce progress every X percent (for screen readers)
  export let itemId: string | null = null; // Optional item ID for direct WebSocket requests
  export let autoConnect: boolean = false; // Whether to automatically connect to WebSocket

  // Set up event dispatcher for component events
  const dispatch = createEventDispatcher<{
    complete: { finalProgress: number };
    update: { progress: number };
    visibilityChange: { visible: boolean };
    connectionChange: { connected: boolean };
    statusChange: { status: string };
  }>();

  // Internal state
  let visible = active;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let debounceId: ReturnType<typeof setTimeout> | null = null;
  let rafId: number | null = null;
  let progressValue = Math.min(100, Math.max(0, progress)); // Ensure progress is between 0-100
  let displayedProgress = progressValue; // For smoother UI updates
  let progressAnnounced = false; // Track if progress has been announced to screen readers
  let lastAnnouncedProgress = -1; // Last announced progress value
  let isReducedMotion = false; // Will be set on mount
  let initialLoad = progress === 0 && showSkeletonOnStart;

  // WebSocket state
  let wsConnected = false;
  let wsMessageHandler: ((event: CustomEvent) => void) | null = null;
  let connectionUnsubscribe: (() => void) | null = null;
  let wsLastUpdated = Date.now();
  let wsError: string | null = null;

  // Screen reader announcement state
  let srAnnouncement = '';

  // Announce progress to screen readers
  function announceProgress(value: number) {
    const roundedValue = Math.round(value);

    // Announce at 100% or at intervals defined by announceInterval
    if (roundedValue === 100) {
      srAnnouncement = `${status} complete, 100%`;
      dispatch('complete', { finalProgress: roundedValue });
    } else if (
      roundedValue % announceInterval === 0 ||
      roundedValue === 25 ||
      roundedValue === 75
    ) {
      srAnnouncement = `${status}, ${roundedValue}% complete`;
    }

    // Clear after a short delay to allow for new announcements
    setTimeout(() => {
      srAnnouncement = '';
    }, 1000);
  }

  // Use RAF for smoother progress updates
  function updateProgressWithRAF(targetValue: number) {
    if (rafId) cancelAnimationFrame(rafId);

    // If reduced motion is preferred, skip animation
    if (isReducedMotion) {
      displayedProgress = Math.min(100, Math.max(0, targetValue));
      checkForAnnouncement(displayedProgress);
      return;
    }

    const startValue = displayedProgress;
    const startTime = performance.now();
    const duration = 300; // Animation duration in ms

    function animate(currentTime: number) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = 1 - Math.pow(1 - progress, 2); // Ease out quad

      // Calculate current value
      displayedProgress = startValue + (targetValue - startValue) * easedProgress;

      // Continue animation if not complete
      if (progress < 1) {
        rafId = requestAnimationFrame(animate);
      } else {
        displayedProgress = targetValue;
        rafId = null;

        // Dispatch update event when animation completes
        dispatch('update', { progress: targetValue });

        // If we've reached 100%, dispatch complete event
        if (targetValue >= 100) {
          dispatch('complete', { finalProgress: 100 });
        }
      }

      // Check if we should announce progress
      checkForAnnouncement(displayedProgress);
    }

    rafId = requestAnimationFrame(animate);
  }

  // Check if we should announce progress to screen readers
  function checkForAnnouncement(value: number) {
    const roundedValue = Math.round(value);

    if (
      !progressAnnounced ||
      Math.abs(roundedValue - lastAnnouncedProgress) >= announceInterval ||
      roundedValue === 25 ||
      roundedValue === 75 ||
      roundedValue === 100
    ) {
      announceProgress(roundedValue);
      lastAnnouncedProgress = roundedValue;
      progressAnnounced = true;
    }
  }

  // Reactive statements for progress value validation and animation
  $: {
    const newProgressValue = Math.min(100, Math.max(0, progress));
    if (newProgressValue !== progressValue) {
      // Debounce rapid updates
      if (debounceId) clearTimeout(debounceId);

      debounceId = setTimeout(() => {
        updateProgressWithRAF(newProgressValue);
        debounceId = null;
      }, 16); // ~1 frame at 60fps
    }
    progressValue = newProgressValue; // Update immediately for internal logic
  }

  // Handle timeout and visibility
  $: {
    // When progress reaches 100, start the timeout to hide if specified
    if (progressValue >= 100 && timeout > 0 && active) {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        visible = false;
      }, timeout);
    }

    // When active state changes
    if (active) {
      visible = true;
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
    }
  }

  // WebSocket message handler for progress updates
  function handleWebSocketMessage(event: CustomEvent) {
    const message = event.detail;
    wsLastUpdated = Date.now();
    wsError = null;

    if (message.type === MessageType.PROGRESS && itemId) {
      try {
        // Check if this message is for our item
        if (message.data.item_id === itemId) {
          // Update progress if changed
          if (
            typeof message.data.progress === 'number' &&
            message.data.progress !== progressValue
          ) {
            progressValue = Math.min(100, Math.max(0, message.data.progress));
            updateProgressWithRAF(progressValue);
          }

          // Update status if changed
          if (message.data.status && message.data.status !== status) {
            status = message.data.status;
            dispatch('statusChange', { status });
          }
        }
      } catch (err) {
        console.error('Error processing WebSocket progress message:', err);
      }
    } else if (message.type === MessageType.ERROR) {
      wsError = message.data.error || 'Unknown error';
      console.error('WebSocket error:', wsError);
    }
  }

  // Variables to store for cleanup
  let mediaQuery: MediaQueryList | null = null;
  let handleMotionPreferenceChange: ((e: MediaQueryListEvent) => void) | null = null;

  // Initialize visibility and check for reduced motion preference on mount
  onMount(async () => {
    visible = active;

    // Check for reduced motion preference
    if (typeof window !== 'undefined') {
      isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      // Listen for changes to reduced motion preference
      mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      handleMotionPreferenceChange = (e: MediaQueryListEvent) => {
        isReducedMotion = e.matches;
      };

      // Add event listener with proper feature detection
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handleMotionPreferenceChange);
      }
    }

    // If we're starting with progress at 0, show initial loading state
    if (progress === 0 && active && showSkeletonOnStart) {
      initialLoad = true;
      // Auto-transition to normal state after a short delay
      setTimeout(() => {
        initialLoad = false;
      }, 1000);
    }

    // Set up WebSocket connection and listeners if itemId is provided
    if (itemId) {
      // Create message handler
      wsMessageHandler = (event: CustomEvent) => handleWebSocketMessage(event);

      // Add event listener for WebSocket messages
      window.addEventListener('ws-message', wsMessageHandler);

      // Subscribe to connection status
      connectionUnsubscribe = connectionStatus.subscribe((state) => {
        const isConnected = state === 'connected';
        if (isConnected !== wsConnected) {
          wsConnected = isConnected;
          dispatch('connectionChange', { connected: wsConnected });

          // If we just connected and autoConnect is true, request processing
          if (wsConnected && autoConnect && itemId) {
            requestProcessing();
          }
        }
      });

      // Connect to WebSocket if autoConnect is true
      if (autoConnect) {
        websocketStore.connect();
      }
    }

    await tick(); // Ensure DOM is updated before any animations

    // Dispatch initial visibility
    dispatch('visibilityChange', { visible });
  });

  // Clean up any timeouts and animation frames on component destruction
  onDestroy(() => {
    if (timeoutId) clearTimeout(timeoutId);
    if (debounceId) clearTimeout(debounceId);
    if (rafId) cancelAnimationFrame(rafId);

    // Clean up WebSocket listeners
    if (wsMessageHandler) {
      window.removeEventListener('ws-message', wsMessageHandler);
    }

    if (connectionUnsubscribe) {
      connectionUnsubscribe();
    }

    // Clean up media query listener
    if (mediaQuery && handleMotionPreferenceChange && mediaQuery.removeEventListener) {
      mediaQuery.removeEventListener('change', handleMotionPreferenceChange);
    }
  });

  // Request processing via WebSocket
  function requestProcessing() {
    if (!itemId || !wsConnected) return false;

    // Reset progress
    progressValue = 0;
    displayedProgress = 0;
    status = 'Processing';
    active = true;
    visible = true;
    initialLoad = true;
    wsLastUpdated = Date.now();

    // Send processing request
    const success = websocketStore.sendMessage({
      type: MessageType.AI_REQUEST,
      data: {
        task: 'process',
        content: '',
        item_id: itemId,
      },
    });

    // Auto-transition from skeleton loader after a short delay
    setTimeout(() => {
      initialLoad = false;
    }, 1000);

    return success;
  }

  // Get appropriate icon based on progress state
  function getStatusIcon() {
    return progressValue < 100 ? 'loader' : 'check-circle';
  }

  // Format progress for screen readers
  function getAriaLabel(): string {
    if (wsError) {
      return `Error: ${wsError}`;
    }
    return ariaLabel || `${status}: ${Math.round(progressValue)}% complete`;
  }
</script>

{#if visible}
  <!-- Screen reader announcements -->
  <div class="sr-only" aria-live="assertive" role="status">{srAnnouncement}</div>

  <div
    class="progress-container {variant}"
    class:active
    class:animated
    class:complete={progressValue >= 100}
    class:initial-load={initialLoad}
    role="progressbar"
    aria-valuemin="0"
    aria-valuemax="100"
    aria-valuenow={Math.round(displayedProgress)}
    aria-label={getAriaLabel()}
    aria-busy={progressValue < 100 || initialLoad}
  >
    {#if variant === 'default'}
      <div class="progress-header">
        {#if showIcon}
          <div class="icon-container" class:spin={animated && progress < 100 && !initialLoad}>
            {#if initialLoad}
              <div class="skeleton-icon" aria-hidden="true"></div>
            {:else}
              <Icon
                name={getStatusIcon()}
                size="small"
                color={progress >= 100 ? 'var(--success)' : color}
              />
            {/if}
          </div>
        {/if}
        <div class="status-text">
          {#if initialLoad}
            <div class="skeleton-text" aria-hidden="true"></div>
          {:else}
            <span class="status">{status}</span>
            {#if showPercentage}
              <span class="percentage">{Math.round(displayedProgress)}%</span>
            {/if}
          {/if}
        </div>
      </div>
    {/if}

    <div class="progress-bar-container">
      {#if initialLoad}
        <div class="progress-bar skeleton-bar" data-testid="progress-bar-skeleton"></div>
      {:else}
        <div
          class="progress-bar"
          style="width: {displayedProgress}%; background-color: {displayedProgress >= 100
            ? 'var(--success)'
            : color};"
          data-testid="progress-bar"
        ></div>
      {/if}
    </div>

    {#if variant === 'compact'}
      <div class="status-compact">
        {#if showIcon}
          <div class="icon-container" class:spin={animated && progress < 100 && !initialLoad}>
            {#if initialLoad}
              <div class="skeleton-icon" aria-hidden="true"></div>
            {:else}
              <Icon
                name={getStatusIcon()}
                size="small"
                color={progress >= 100 ? 'var(--success)' : color}
              />
            {/if}
          </div>
        {/if}

        {#if initialLoad}
          <div class="skeleton-text" aria-hidden="true"></div>
        {:else}
          <span class="status">{status}</span>
          {#if showPercentage}
            <span class="percentage">{Math.round(displayedProgress)}%</span>
          {/if}
        {/if}
      </div>
    {/if}
  </div>
{/if}

<style>
  .progress-container {
    width: 100%;
    background: var(--bg-secondary);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
    transition:
      opacity 0.2s ease-out,
      transform 0.2s ease-out;
  }

  .progress-container.compact {
    padding: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .progress-container.minimal {
    padding: 0;
    margin-bottom: 0.5rem;
    background: transparent;
    box-shadow: none;
    border: none;
  }

  /* Initial loading state */
  .progress-container.initial-load {
    background: var(--bg-secondary-hover);
  }

  .progress-header {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
    gap: 0.5rem;
  }

  .status-compact {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
    font-size: 0.875rem;
  }

  .icon-container {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
  }

  .icon-container.spin {
    animation: spin 1.5s linear infinite;
  }

  .status-text {
    flex: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .status {
    font-weight: 500;
    color: var(--text-primary);
  }

  .percentage {
    font-weight: 600;
    color: var(--text-secondary);
    margin-left: 0.5rem;
  }

  .progress-bar-container {
    width: 100%;
    height: 0.5rem;
    background: var(--bg-tertiary);
    border-radius: 999px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background-color: var(--accent);
    transition: width 0.3s ease-out;
    border-radius: 4px;
    will-change: width, transform;
  }

  /* Skeleton loading states */
  .skeleton-icon {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--bg-tertiary);
    animation: pulse 1.5s infinite ease-in-out;
  }

  .skeleton-text {
    width: 100px;
    height: 14px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    animation: pulse 1.5s infinite ease-in-out;
  }

  .skeleton-bar {
    width: 60%;
    background: var(--bg-tertiary);
    animation:
      pulse 1.5s infinite ease-in-out,
      skeleton-progress 2s infinite ease-in-out;
  }

  @keyframes pulse {
    0% {
      opacity: 0.6;
    }
    50% {
      opacity: 0.8;
    }
    100% {
      opacity: 0.6;
    }
  }

  @keyframes skeleton-progress {
    0% {
      width: 20%;
    }
    50% {
      width: 60%;
    }
    100% {
      width: 20%;
    }
  }

  /* Screen reader only class */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  /* Reduce motion for users who prefer it */
  @media (prefers-reduced-motion: reduce) {
    .progress-bar {
      transition: none;
    }

    .icon-container.spin {
      animation: none;
    }

    .skeleton-icon,
    .skeleton-text,
    .skeleton-bar {
      animation: none;
      opacity: 0.7;
    }
  }
</style>
