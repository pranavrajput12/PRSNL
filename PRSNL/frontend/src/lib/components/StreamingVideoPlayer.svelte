<script lang="ts" type="module">
  import { onMount } from 'svelte';
  import Icon from './Icon.svelte';

  export let videoId: string;
  export let title: string = '';
  export let thumbnail: string | undefined = undefined;
  export let duration: number | undefined = undefined;
  export let platform: string | undefined = undefined;
  export let showControls: boolean = true;

  let videoData: any = null;
  let isLoading = true;
  let isError = false;
  let errorMessage = '';
  let isPlaying = false;
  let useEmbed = false;
  let embedUrl = '';
  let streamUrl = '';
  let isDownloaded = false;

  onMount(async () => {
    await loadVideoData();
  });

  async function loadVideoData() {
    try {
      console.log('🔵 StreamingVideoPlayer - Loading video data for ID:', videoId);
      console.log('🔵 StreamingVideoPlayer - Input props:', {
        videoId,
        title,
        thumbnail,
        duration,
        platform,
      });

      const response = await fetch(`/api/videos/${videoId}/stream-url`);
      console.log('🔵 StreamingVideoPlayer - API Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('🔴 StreamingVideoPlayer - API Error:', response.status, errorText);
        throw new Error(`Failed to get video stream URL: ${response.status} ${errorText}`);
      }

      videoData = await response.json();
      console.log('🟢 StreamingVideoPlayer - Video data received:', videoData);

      if (videoData.type === 'local') {
        // Video is downloaded, use local file
        streamUrl = videoData.url;
        isDownloaded = true;
        useEmbed = false;
        console.log('🔵 StreamingVideoPlayer - Using local video:', streamUrl);
      } else {
        // Video is streaming, use embed or direct URL
        streamUrl = videoData.url;
        embedUrl = videoData.embed_url;
        isDownloaded = false;
        console.log('🔵 StreamingVideoPlayer - Using streaming video:', { streamUrl, embedUrl });

        // For YouTube, prefer embed for better UX
        if (platform === 'youtube' && embedUrl) {
          useEmbed = true;
          console.log('🔵 StreamingVideoPlayer - Using YouTube embed');
        } else {
          useEmbed = false;
          console.log('🔵 StreamingVideoPlayer - Using direct video stream');
        }
      }

      console.log('🟢 StreamingVideoPlayer - Final configuration:', {
        useEmbed,
        streamUrl,
        embedUrl,
        isDownloaded,
        platform,
      });

      isLoading = false;
    } catch (error) {
      console.error('🔴 StreamingVideoPlayer - Error loading video data:', error);
      isError = true;
      errorMessage = `Failed to load video: ${error.message}`;
      isLoading = false;
    }
  }

  function togglePlay() {
    if (useEmbed) {
      // For embedded videos, we can't control playback directly
      // The embed player will handle it
      return;
    }

    isPlaying = !isPlaying;
  }

  function formatDuration(seconds: number): string {
    if (!seconds) return '0:00';

    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function getPlatformIcon(platform: string) {
    switch (platform) {
      case 'youtube':
        return 'youtube';
      case 'twitter':
        return 'twitter';
      case 'instagram':
        return 'instagram';
      default:
        return 'video';
    }
  }
</script>

<div class="streaming-video-player">
  {#if isLoading}
    <div class="loading-container">
      <div class="spinner"></div>
      <p>Loading video...</p>
    </div>
  {:else if isError}
    <div class="error-container">
      <Icon name="alert-circle" size="large" />
      <p>{errorMessage}</p>
      <button class="retry-btn" on:click={loadVideoData}>Retry</button>
    </div>
  {:else if useEmbed && embedUrl}
    <!-- YouTube or other platform embed -->
    <div class="embed-container">
      <iframe
        src={embedUrl}
        {title}
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
        loading="lazy"
      ></iframe>
    </div>
  {:else}
    <!-- Regular video player for downloaded videos or direct streaming -->
    <div class="video-container">
      {#if !isPlaying && thumbnail}
        <div class="video-thumbnail" on:click={togglePlay}>
          <img src={thumbnail} alt={title} />
          <div class="play-overlay">
            <div class="play-icon">
              <Icon name="play" size="medium" color="white" />
            </div>
          </div>

          {#if duration}
            <div class="duration">{formatDuration(duration)}</div>
          {/if}

          {#if platform}
            <div class="platform-badge">
              <Icon name={getPlatformIcon(platform)} size="small" color="white" />
              {platform}
            </div>
          {/if}

          {#if isDownloaded}
            <div class="download-badge">
              <Icon name="download" size="small" color="white" />
              Downloaded
            </div>
          {:else}
            <div class="streaming-badge">
              <Icon name="wifi" size="small" color="white" />
              Streaming
            </div>
          {/if}
        </div>
      {:else}
        <video
          controls={showControls}
          autoplay={isPlaying}
          on:play={() => (isPlaying = true)}
          on:pause={() => (isPlaying = false)}
          on:ended={() => (isPlaying = false)}
        >
          <source src={streamUrl} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      {/if}
    </div>
  {/if}
</div>

<style>
  .streaming-video-player {
    position: relative;
    width: 100%;
    background: #000;
    border-radius: var(--radius);
    overflow: hidden;
    aspect-ratio: 16 / 9;
  }

  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    color: white;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: var(--man-united-red);
    animation: spin 1s ease-in-out infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .error-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    color: white;
    text-align: center;
    padding: 1rem;
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
    margin-top: 1rem;
  }

  .retry-btn:hover {
    background: var(--accent-red-hover);
    transform: translateY(-2px);
  }

  .embed-container {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .embed-container iframe {
    width: 100%;
    height: 100%;
    border: none;
  }

  .video-container {
    position: relative;
    width: 100%;
    height: 100%;
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
    object-fit: cover;
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
  }

  .download-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: var(--color-success);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .streaming-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: var(--color-info);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  video {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  @media (max-width: 768px) {
    .streaming-video-player {
      aspect-ratio: 16 / 10;
    }

    .platform-badge,
    .download-badge,
    .streaming-badge {
      font-size: 0.7rem;
      padding: 2px 6px;
    }
  }
</style>
