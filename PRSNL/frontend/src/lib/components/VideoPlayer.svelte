<script lang="ts">
  export let src: string;
  export let thumbnail: string | undefined = undefined;
  export let title: string = '';
  export let duration: number | undefined = undefined;
  
  let isPlaying = false;
  let videoElement: HTMLVideoElement;
  
  function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
  
  function togglePlay() {
    if (videoElement) {
      if (isPlaying) {
        videoElement.pause();
      } else {
        videoElement.play();
      }
      isPlaying = !isPlaying;
    }
  }
</script>

<div class="video-player">
  {#if thumbnail && !isPlaying}
    <div class="video-thumbnail" on:click={togglePlay}>
      <img src={thumbnail} alt={title} />
      <div class="play-overlay">
        <svg class="play-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <polygon points="5 3 19 12 5 21 5 3" fill="currentColor"/>
        </svg>
      </div>
      {#if duration}
        <div class="duration">{formatDuration(duration)}</div>
      {/if}
    </div>
  {/if}
  
  <video
    bind:this={videoElement}
    class:hidden={thumbnail && !isPlaying}
    {src}
    controls
    preload="metadata"
    on:play={() => isPlaying = true}
    on:pause={() => isPlaying = false}
    on:ended={() => isPlaying = false}
  >
    <source {src} type="video/mp4" />
    Your browser does not support the video tag.
  </video>
</div>

<style>
  .video-player {
    position: relative;
    width: 100%;
    background: #000;
    border-radius: var(--radius);
    overflow: hidden;
  }
  
  .video-thumbnail {
    position: relative;
    cursor: pointer;
    transition: opacity var(--transition-base);
  }
  
  .video-thumbnail:hover {
    opacity: 0.9;
  }
  
  .video-thumbnail img {
    width: 100%;
    height: auto;
    display: block;
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
  }
  
  video {
    width: 100%;
    height: auto;
    display: block;
  }
  
  video.hidden {
    display: none;
  }
</style>