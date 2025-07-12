<script lang="ts" type="module">
  import Icon from './Icon.svelte';
  import { formatDate } from '$lib/utils/date';

  export let video: any;

  // Generate YouTube thumbnail URL from video URL
  function getYouTubeThumbnail(url: string): string | null {
    if (!url || !url.includes('youtube.com/watch?v=')) return null;

    const videoIdMatch = url.match(/[?&]v=([^&]+)/);
    if (videoIdMatch && videoIdMatch[1]) {
      // Use hqdefault as it's more reliable than maxresdefault
      return `https://img.youtube.com/vi/${videoIdMatch[1]}/hqdefault.jpg`;
    }
    return null;
  }

  // Handle image loading errors with fallback
  function handleImageError(event: Event) {
    const img = event.target as HTMLImageElement;
    const src = img.src;

    // If it's a YouTube thumbnail, try fallback qualities
    if (src.includes('img.youtube.com')) {
      if (src.includes('/hqdefault.jpg')) {
        img.src = src.replace('/hqdefault.jpg', '/mqdefault.jpg');
      } else if (src.includes('/mqdefault.jpg')) {
        img.src = src.replace('/mqdefault.jpg', '/default.jpg');
      } else {
        // Final fallback - hide the image and show placeholder
        img.style.display = 'none';
        const placeholder = img.parentElement?.querySelector('.thumbnail-placeholder');
        if (placeholder) {
          placeholder.style.display = 'flex';
        }
      }
    }
  }

  $: youtubeThumbnail = video.platform === 'youtube' ? getYouTubeThumbnail(video.url) : null;
  $: displayThumbnail =
    video.thumbnail || video.thumbnail_url || video.thumbnailUrl || youtubeThumbnail;

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

  function formatDuration(seconds: number | null) {
    if (!seconds) return '';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
</script>

<a href="/videos/{video.id}" class="video-card">
  <div class="thumbnail-container">
    {#if displayThumbnail}
      <img
        src={displayThumbnail}
        alt={video.title}
        class="thumbnail"
        loading="lazy"
        on:error={handleImageError}
      />
    {/if}
    <div class="thumbnail-placeholder" style="display: {displayThumbnail ? 'none' : 'flex'}">
      <Icon name={getPlatformIcon(video.platform)} size={48} />
    </div>

    {#if video.duration}
      <div class="duration">{formatDuration(video.duration)}</div>
    {/if}

    <div class="platform-badge">
      <Icon name={getPlatformIcon(video.platform)} size={16} />
    </div>
  </div>

  <div class="content">
    <h3 class="title">{video.title}</h3>

    {#if video.summary}
      <p class="summary">{video.summary}</p>
    {/if}

    <div class="metadata">
      <div class="meta-item">
        <Icon name="calendar" size={14} />
        {formatDate(video.created_at)}
      </div>

      {#if video.has_transcript}
        <div class="meta-item transcript">
          <Icon name="file-text" size={14} />
          Transcript
        </div>
      {/if}

      {#if video.key_topics && video.key_topics.length > 0}
        <div class="topics">
          {#each video.key_topics.slice(0, 3) as topic}
            <span class="topic-tag">{topic}</span>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</a>

<style>
  .video-card {
    display: block;
    background-color: var(--color-surface);
    border-radius: 0.75rem;
    overflow: hidden;
    transition: all 0.2s;
    text-decoration: none;
    color: inherit;
  }

  .video-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  }

  .thumbnail-container {
    position: relative;
    aspect-ratio: 16 / 9;
    background-color: var(--color-background);
    overflow: hidden;
  }

  .thumbnail {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .thumbnail-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    color: var(--color-text-muted);
  }

  .duration {
    position: absolute;
    bottom: 0.5rem;
    right: 0.5rem;
    padding: 0.25rem 0.5rem;
    background-color: rgba(0, 0, 0, 0.8);
    color: white;
    font-size: 0.75rem;
    border-radius: 0.25rem;
    font-family: monospace;
  }

  .platform-badge {
    position: absolute;
    top: 0.5rem;
    left: 0.5rem;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--color-surface);
    border-radius: 50%;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .content {
    padding: 1rem;
  }

  .title {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .summary {
    font-size: 0.875rem;
    color: var(--color-text-muted);
    margin-bottom: 0.75rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .metadata {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: center;
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }

  .meta-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .meta-item.transcript {
    color: var(--color-success);
  }

  .topics {
    display: flex;
    gap: 0.25rem;
    flex-wrap: wrap;
  }

  .topic-tag {
    padding: 0.125rem 0.5rem;
    background-color: var(--color-primary-light);
    color: var(--color-primary);
    border-radius: 9999px;
    font-size: 0.75rem;
  }
</style>
