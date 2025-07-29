<!--
  Video View Component
  Basic implementation for video content display
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import GenericItemView from './GenericItemView.svelte';
  
  export let item: any;
  export let contentType: any;
  
  const dispatch = createEventDispatcher();
  
  $: hasVideo = item.url && (item.url.includes('youtube') || item.url.includes('vimeo') || item.thumbnail_url);
</script>

<div class="video-view">
  {#if hasVideo}
    <section class="video-section">
      <VideoPlayer
        videoUrl={item.url}
        thumbnailUrl={item.thumbnail_url}
        title={item.title}
        duration={item.duration}
        platform={item.platform}
      />
    </section>
  {/if}
  
  <!-- Use generic view for the rest -->
  <GenericItemView {item} {contentType} on:error />
</div>

<style>
  .video-view {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  .video-section {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
  }
</style>