<script lang="ts">
  export let url: string;
  export let title: string = '';
  export let width: string = '100%';
  export let height: string = '100%';
  export let autoplay: boolean = false;

  // Extract video ID from YouTube URL
  function getYouTubeVideoId(url: string): string | null {
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
      /youtube\.com\/watch\?.*v=([^&\n?#]+)/,
    ];

    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match && match[1]) {
        return match[1];
      }
    }

    return null;
  }

  $: videoId = getYouTubeVideoId(url);
  $: embedUrl = videoId
    ? `https://www.youtube.com/embed/${videoId}${autoplay ? '?autoplay=1' : ''}`
    : null;
</script>

{#if embedUrl}
  <div class="youtube-embed">
    <iframe
      src={embedUrl}
      {title}
      {width}
      {height}
      frameborder="0"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
      allowfullscreen
    ></iframe>
  </div>
{:else}
  <div class="embed-error">
    <p>Unable to embed video from URL: {url}</p>
  </div>
{/if}

<style>
  .youtube-embed {
    position: relative;
    width: 100%;
    height: 100%;
    background: #000;
  }

  iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }

  .embed-error {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    background: var(--color-surface);
    color: var(--color-text-muted);
    border-radius: 0.5rem;
  }
</style>
