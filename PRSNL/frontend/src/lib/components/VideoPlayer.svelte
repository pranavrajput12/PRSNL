<script lang="ts" type="module">
  import { onMount, onDestroy } from 'svelte';
  import Icon from './Icon.svelte';
  import {
    mediaSettings,
    activateVideo,
    deactivateVideo,
    registerVideoView,
    unregisterVideoView,
    recordLoadTime,
    recordBufferingEvent,
    canLoadMoreVideos,
  } from '$lib/stores/media';

  export let src: string;
  // Add support for url prop as alias to src (for compatibility)
  export let url: string | undefined = undefined;
  export let thumbnail: string | undefined = undefined;
  export let thumbnailUrl: string | undefined = thumbnail;
  export let title: string = '';
  export let duration: number | undefined = undefined;
  export let autoplay: boolean = false;
  export let platform: string | undefined = undefined;
  export let lazyLoad: boolean = true;
  // Use url as fallback if src is not provided
  $: actualSrc = src || url || '';
  export let videoId: string = actualSrc.split('/').pop() || Math.random().toString(36).substring(2, 9);
  export let showControls: boolean = true;

  // Helper function to ensure thumbnail URLs are properly formatted
  function formatThumbnailUrl(url: string | undefined): string | undefined {
    if (!url) return undefined;

    // If it's already a full URL or starts with /media/, return as is
    if (url.startsWith('http') || url.startsWith('/media/')) {
      return url;
    }

    // If it starts with /app/media/, convert to /media/
    if (url.startsWith('/app/media/')) {
      return url.replace('/app/media/', '/media/');
    }

    // Fallback: don't use invalid thumbnail URLs
    return undefined;
  }

  // Process thumbnail URLs
  $: processedThumbnail = formatThumbnailUrl(thumbnail);
  $: processedThumbnailUrl = formatThumbnailUrl(thumbnailUrl);

  let isPlaying = false;
  let isLoading = false;
  let isError = false;
  let errorMessage = '';
  let videoElement: HTMLVideoElement;
  let progress = 0;
  let buffered = 0;
  let volume = 1;
  let isMuted = false;
  let isFullscreen = false;
  let observer: IntersectionObserver | null = null;
  let isInViewport = false;
  let videoContainer: HTMLDivElement;
  let loadStartTime = 0;
  let isActive = false;
  let progressiveImg: HTMLImageElement | null = null;
  let progressiveLoaded = false;
  let canLoad = true;
  let retryCount = 0;
  let maxRetries = 3;

  // Subscribe to canLoadMoreVideos store
  $: canLoad = $canLoadMoreVideos;

  onMount(() => {
    if (lazyLoad) {
      setupIntersectionObserver();
    } else {
      isInViewport = true;
      registerVideoView(videoId);
    }

    if (processedThumbnailUrl && $mediaSettings.enableProgressiveLoading) {
      loadProgressiveImage();
    }

    if (autoplay && isInViewport && canLoad) {
      setTimeout(() => {
        if (videoElement) {
          activateVideo(videoId);
          isActive = true;
          videoElement.play().catch((err) => {
            console.error('Autoplay failed:', err);
          });
        }
      }, 100);
    }

    // Add keyboard event listener
    document.addEventListener('keydown', handleKeydown);

    // Add buffering detection
    if (videoElement) {
      videoElement.addEventListener('waiting', handleBuffering);
    }

    return () => {
      if (videoElement) {
        videoElement.removeEventListener('waiting', handleBuffering);
      }
    };
  });

  onDestroy(() => {
    document.removeEventListener('keydown', handleKeydown);
    if (observer) {
      observer.disconnect();
    }
    if (isActive) {
      deactivateVideo(videoId);
    }
    unregisterVideoView(videoId);
  });

  function setupIntersectionObserver() {
    observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        const wasInViewport = isInViewport;
        isInViewport = entry.isIntersecting;

        // Register/unregister video view for performance tracking
        if (isInViewport && !wasInViewport) {
          registerVideoView(videoId);

          // Preload video if autoplay is enabled and we can load more videos
          if ($mediaSettings.autoplayInViewport && canLoad && !isPlaying) {
            activateVideo(videoId);
            isActive = true;
            if (videoElement) {
              videoElement.play().catch((err) => console.error('Autoplay failed:', err));
            }
          }
        } else if (!isInViewport && wasInViewport) {
          unregisterVideoView(videoId);
        }

        // Pause video when out of viewport
        if (!isInViewport && isPlaying && videoElement) {
          videoElement.pause();
          isPlaying = false;

          // If network saving mode is on, unload video when out of viewport
          if ($mediaSettings.networkSavingMode && isActive) {
            deactivateVideo(videoId);
            isActive = false;
            // Reset video element to free up resources
            if (videoElement) {
              videoElement.removeAttribute('src');
              videoElement.load();
            }
          }
        }
      },
      { threshold: 0.2, rootMargin: '100px' }
    );

    if (videoContainer) {
      observer.observe(videoContainer);
    }
  }

  function formatDuration(seconds: number): string {
    if (!seconds) return '0:00';

    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function loadProgressiveImage() {
    if (!processedThumbnailUrl) return;

    progressiveImg = new Image();
    progressiveImg.onload = () => {
      progressiveLoaded = true;
    };
    progressiveImg.src = processedThumbnailUrl;
  }

  function handleBuffering() {
    recordBufferingEvent(videoId);
  }

  function togglePlay() {
    if (!videoElement || !isInViewport) return;

    if (isPlaying) {
      videoElement.pause();
    } else {
      // Activate this video in the store if not already active
      if (!isActive) {
        activateVideo(videoId);
        isActive = true;
      }

      videoElement.play().catch((err) => {
        isError = true;
        errorMessage = 'Failed to play video. Please try again.';
        console.error('Play error:', err);

        // Retry logic for common network errors
        if (
          retryCount < maxRetries &&
          err instanceof Error &&
          (err.name === 'NetworkError' || err.name === 'AbortError')
        ) {
          retryCount++;
          setTimeout(() => {
            isError = false;
            if (videoElement) {
              videoElement.load();
              videoElement.play().catch((e) => console.error('Retry failed:', e));
            }
          }, 1000 * retryCount); // Exponential backoff
        }
      });
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    // Only handle events when video is in viewport and focused
    if (
      !isInViewport ||
      document.activeElement?.tagName === 'INPUT' ||
      document.activeElement?.tagName === 'TEXTAREA'
    ) {
      return;
    }

    // Space to play/pause
    if (e.key === ' ' && videoElement && videoContainer.matches(':hover')) {
      e.preventDefault();
      togglePlay();
    }

    // Arrow keys for seeking when video is focused or hovered
    if (videoElement && videoContainer.matches(':hover')) {
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        videoElement.currentTime += 10; // Forward 10 seconds
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        videoElement.currentTime -= 10; // Back 10 seconds
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        videoElement.volume = Math.min(1, videoElement.volume + 0.1);
        volume = videoElement.volume;
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        videoElement.volume = Math.max(0, videoElement.volume - 0.1);
        volume = videoElement.volume;
      } else if (e.key === 'm') {
        e.preventDefault();
        videoElement.muted = !videoElement.muted;
        isMuted = videoElement.muted;
      } else if (e.key === 'f') {
        e.preventDefault();
        toggleFullscreen();
      }
    }
  }

  function updateProgress() {
    if (videoElement && videoElement.duration) {
      progress = (videoElement.currentTime / videoElement.duration) * 100;

      // Update buffered
      if (videoElement.buffered.length > 0) {
        buffered =
          (videoElement.buffered.end(videoElement.buffered.length - 1) / videoElement.duration) *
          100;
      }
    }
  }

  function handleLoadStart() {
    isLoading = true;
    loadStartTime = performance.now();
  }

  function handleCanPlay() {
    isLoading = false;
    const loadTime = performance.now() - loadStartTime;
    recordLoadTime(videoId, loadTime);
  }

  function handleError() {
    isLoading = false;
    isError = true;
    errorMessage = 'Failed to load video. Please try again.';

    // If we have retries left, try again with exponential backoff
    if (retryCount < maxRetries) {
      retryCount++;
      setTimeout(() => {
        isError = false;
        if (videoElement) {
          videoElement.load();
        }
      }, 1000 * retryCount);
    } else if (isActive) {
      deactivateVideo(videoId);
      isActive = false;
    }
  }

  function toggleFullscreen() {
    if (!videoContainer) return;

    if (!document.fullscreenElement) {
      videoContainer.requestFullscreen().catch((err) => {
        console.error('Error attempting to enable fullscreen:', err);
      });
      isFullscreen = true;
    } else {
      document.exitFullscreen();
      isFullscreen = false;
    }
  }

  function handleSeek(e: MouseEvent) {
    if (!videoElement) return;

    const progressBar = e.currentTarget as HTMLDivElement;
    const rect = progressBar.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    videoElement.currentTime = pos * (videoElement.duration || 0);
  }

  // handleProgressClick is now merged with handleSeek
</script>

<div class="video-player" bind:this={videoContainer}>
  {#if !isPlaying}
    <div class="video-thumbnail" on:click={togglePlay}>
      <!-- Use progressive loading for thumbnails if enabled -->
      {#if processedThumbnailUrl && $mediaSettings.enableProgressiveLoading}
        <img
          src={processedThumbnailUrl || ''}
          alt={title}
          loading="lazy"
          style="filter: {progressiveLoaded
            ? 'none'
            : 'blur(10px)'}; transition: filter 0.3s ease-in-out;"
        />
      {:else if processedThumbnail}
        <img src={processedThumbnail || ''} alt={title} loading="lazy" />
      {:else}
        <!-- Placeholder when no thumbnail is available -->
        <div class="thumbnail-placeholder">
          <Icon name="video" size="large" color="var(--text-muted)" />
        </div>
      {/if}

      {#if isLoading}
        <div class="loading-overlay">
          <div class="spinner"></div>
        </div>
      {:else}
        <div class="play-overlay">
          <div class="play-icon">
            <Icon name="play" size="medium" color="white" />
          </div>
        </div>
      {/if}

      {#if duration}
        <div class="duration">{formatDuration(duration)}</div>
      {/if}

      {#if platform}
        <div class="platform-badge">
          <Icon name="video" size="small" color="white" />
          {platform}
        </div>
      {/if}

      <!-- Show network saving indicator when active -->
      {#if $mediaSettings.networkSavingMode}
        <div class="network-saving-badge">
          <Icon name="wifi-off" size="small" color="white" />
          Data saver
        </div>
      {/if}
    </div>
  {/if}

  {#if isError}
    <div class="error-container">
      <Icon name="alert-circle" size="large" />
      <p>{errorMessage}</p>
      <button
        class="retry-btn"
        on:click={() => {
          isError = false;
          if (videoElement) {
            videoElement.load();
          }
        }}>Retry</button
      >
    </div>
  {/if}

  <video
    bind:this={videoElement}
    class:hidden={thumbnail && !isPlaying}
    preload={$mediaSettings.preloadStrategy}
    on:play={() => (isPlaying = true)}
    on:pause={() => (isPlaying = false)}
    on:ended={() => (isPlaying = false)}
    on:timeupdate={updateProgress}
    on:loadstart={handleLoadStart}
    on:canplay={handleCanPlay}
    on:error={handleError}
    on:stalled={handleBuffering}
    on:waiting={handleBuffering}
  >
    {#if isInViewport || !$mediaSettings.networkSavingMode}
      <source src={actualSrc || ''} type="video/mp4" />
    {/if}
    Your browser does not support the video tag.
  </video>

  {#if isPlaying || (!thumbnail && !isError)}
    <div class="custom-controls">
      <div class="progress-container" on:click={handleSeek}>
        <div class="progress-bar">
          <div class="buffered" style="width: {buffered}%"></div>
          <div class="progress" style="width: {progress}%"></div>
        </div>
      </div>

      <div class="controls-row">
        <button class="control-btn" on:click={togglePlay}>
          {#if isPlaying}
            <Icon name="pause" size="small" />
          {:else}
            <Icon name="play" size="small" />
          {/if}
        </button>

        <button
          class="control-btn"
          on:click={() => {
            if (videoElement) {
              videoElement.muted = !videoElement.muted;
              isMuted = videoElement.muted;
            }
          }}
        >
          {#if isMuted}
            <Icon name="volume-x" size="small" />
          {:else}
            <Icon name="volume-2" size="small" />
          {/if}
        </button>

        {#if videoElement}
          <div class="time-display">
            {formatDuration(videoElement.currentTime || 0)} / {formatDuration(
              videoElement.duration || 0
            )}
          </div>
        {/if}

        <div class="spacer"></div>

        <button class="control-btn" on:click={toggleFullscreen}>
          {#if isFullscreen}
            <Icon name="minimize" size="small" />
          {:else}
            <Icon name="maximize" size="small" />
          {/if}
        </button>
      </div>
    </div>
  {/if}

  {#if isLoading && (!thumbnail || isPlaying)}
    <div class="loading-overlay">
      <div class="spinner"></div>
    </div>
  {/if}
</div>

<style>
  .video-player {
    position: relative;
    width: 100%;
    background: #000;
    border-radius: var(--radius);
    overflow: hidden;
    aspect-ratio: 16 / 9;
  }

  .video-thumbnail {
    position: relative;
    cursor: pointer;
    transition: opacity var(--transition-base);
    width: 100%;
    height: 100%;
  }

  .video-thumbnail:hover {
    opacity: 0.9;
  }

  .video-thumbnail img {
    width: 100%;
    height: 100%;
    display: block;
    object-fit: cover;
  }

  .thumbnail-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-tertiary);
  }

  .play-overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60px;
    height: 60px;
    background: rgba(0, 0, 0, 0.7);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-base);
  }

  .video-thumbnail:hover .play-overlay {
    background: var(--man-united-red);
    transform: translate(-50%, -50%) scale(1.1);
  }

  .play-icon {
    width: 24px;
    height: 24px;
    color: white;
    margin-left: 3px;
  }

  .duration {
    position: absolute;
    bottom: 8px;
    right: 8px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 600;
    z-index: 2;
  }

  .platform-badge {
    position: absolute;
    top: 8px;
    left: 8px;
    background: var(--man-united-red);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 4px;
    z-index: 2;
  }

  .loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 3;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: var(--man-united-red);
    animation: spin 1s ease-in-out infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .error-container {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: white;
    padding: 1rem;
    text-align: center;
    z-index: 4;
  }

  .error-container p {
    margin: 1rem 0;
  }

  .retry-btn {
    background: var(--man-united-red);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: var(--radius);
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-base);
  }

  .retry-btn:hover {
    background: var(--accent-red-hover);
    transform: translateY(-2px);
  }

  video {
    width: 100%;
    height: 100%;
    display: block;
    object-fit: contain;
  }

  video.hidden {
    display: none;
  }

  .custom-controls {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
    padding: 0.5rem;
    opacity: 0;
    transition: opacity var(--transition-base);
    z-index: 2;
  }

  .video-player:hover .custom-controls {
    opacity: 1;
  }

  .progress-container {
    width: 100%;
    height: 8px;
    cursor: pointer;
    padding: 4px 0;
  }

  .progress-bar {
    position: relative;
    height: 4px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
    overflow: hidden;
  }

  .buffered {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: rgba(255, 255, 255, 0.4);
    transition: width 0.2s ease;
  }

  .progress {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: var(--man-united-red);
    transition: width 0.1s ease;
  }

  .controls-row {
    display: flex;
    align-items: center;
    padding: 0.5rem 0;
  }

  .control-btn {
    background: transparent;
    border: none;
    color: white;
    padding: 0.25rem;
    margin-right: 0.5rem;
    cursor: pointer;
    opacity: 0.8;
    transition: opacity var(--transition-fast);
  }

  .control-btn:hover {
    opacity: 1;
  }

  .time-display {
    color: white;
    font-size: 0.75rem;
    margin-right: 0.5rem;
  }

  .spacer {
    flex: 1;
  }

  @media (max-width: 768px) {
    .video-player {
      aspect-ratio: 16 / 10;
    }

    .platform-badge {
      font-size: 0.7rem;
      padding: 2px 6px;
    }

    .time-display {
      display: none;
    }
  }
</style>
