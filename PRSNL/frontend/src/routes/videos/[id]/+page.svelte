<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import YouTubeEmbed from '$lib/components/YouTubeEmbed.svelte';
  import { formatDate } from '$lib/utils/date';
  
  let video: any = null;
  let loading = true;
  let activeTab: 'transcript' | 'summary' | 'moments' = 'transcript';
  let transcriptSummary = '';
  let summarizing = false;
  
  async function loadVideo() {
    try {
      loading = true;
      console.log('Loading video with ID:', $page.params.id);
      const response = await fetch(`/api/items/${$page.params.id}`);
      console.log('Response status:', response.status);
      if (response.ok) {
        const item = await response.json();
        console.log('Item data:', item);
        video = item;
        console.log('Video object:', video);
      } else {
        console.error('Failed to load video:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error loading video:', error);
    } finally {
      loading = false;
    }
  }
  
  async function summarizeTranscript() {
    if (!video.transcript || summarizing) return;
    
    try {
      summarizing = true;
      const response = await fetch('/api/summarization/item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_id: video.id,
          summary_type: 'detailed'
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        transcriptSummary = result.data.summary;
      }
    } catch (error) {
      console.error('Error summarizing transcript:', error);
    } finally {
      summarizing = false;
    }
  }
  
  function parseTranscript(transcript: string) {
    // Parse timestamp format [HH:MM:SS] or [MM:SS]
    const lines = transcript.split('\n');
    const segments = [];
    
    for (const line of lines) {
      const match = line.match(/^\[(\d+:\d+(?::\d+)?)\]\s*(.+)$/);
      if (match) {
        const [_, timestamp, text] = match;
        segments.push({ timestamp, text });
      }
    }
    
    return segments;
  }
  
  function seekToTimestamp(timestamp: string) {
    // Convert timestamp to seconds
    const parts = timestamp.split(':').reverse();
    let seconds = 0;
    
    for (let i = 0; i < parts.length; i++) {
      seconds += parseInt(parts[i]) * Math.pow(60, i);
    }
    
    // Implement video seek functionality
    console.log('Seek to:', seconds);
  }
  
  onMount(() => {
    loadVideo();
  });
</script>

{#if loading}
  <div class="loading">
    <Icon name="spinner" class="animate-spin" />
    Loading video...
  </div>
{:else if video}
  <div class="video-page">
    <div class="video-header">
      <a href="/videos" class="back-link">
        <Icon name="arrow-left" />
        Back to Videos
      </a>
      
      <div class="video-actions">
        <button class="btn btn-secondary">
          <Icon name="share" />
          Share
        </button>
        <button class="btn btn-secondary">
          <Icon name="bookmark" />
          Save
        </button>
      </div>
    </div>
    
    <div class="video-container">
      <div class="player-section">
        {#if video.platform === 'youtube' && video.url}
          <div class="youtube-player-wrapper">
            <YouTubeEmbed 
              url={video.url}
              title={video.title}
            />
          </div>
        {:else if video.file_path}
          <VideoPlayer 
            src={video.file_path}
            thumbnail={video.thumbnail_url}
            title={video.title}
            platform={video.platform}
          />
        {:else}
          <div class="video-unavailable">
            <Icon name="video-off" size="large" />
            <p>Video file not available</p>
            {#if video.url}
              <a href={video.url} target="_blank" rel="noopener noreferrer" class="btn btn-primary">
                Watch on {video.platform || 'Original Site'}
              </a>
            {/if}
          </div>
        {/if}
        
        <div class="video-info">
          <h1 class="video-title">{video.title}</h1>
          
          <div class="video-meta">
            <span class="platform">
              <Icon name={video.platform} size={16} />
              {video.platform}
            </span>
            <span class="date">
              <Icon name="calendar" size={16} />
              {formatDate(video.created_at)}
            </span>
            {#if video.duration}
              <span class="duration">
                <Icon name="clock" size={16} />
                {Math.floor(video.duration / 60)} min
              </span>
            {/if}
          </div>
          
          {#if video.summary}
            <p class="video-summary">{video.summary}</p>
          {/if}
          
          {#if video.key_topics && video.key_topics.length > 0}
            <div class="topics">
              <span class="topics-label">Topics:</span>
              {#each video.key_topics as topic}
                <span class="topic-tag">{topic}</span>
              {/each}
            </div>
          {/if}
        </div>
      </div>
      
      <div class="content-section">
        <div class="tabs">
          <button 
            class="tab"
            class:active={activeTab === 'transcript'}
            on:click={() => activeTab = 'transcript'}
          >
            <Icon name="file-text" />
            Transcript
          </button>
          <button 
            class="tab"
            class:active={activeTab === 'summary'}
            on:click={() => activeTab = 'summary'}
          >
            <Icon name="align-left" />
            Summary
          </button>
          <button 
            class="tab"
            class:active={activeTab === 'moments'}
            on:click={() => activeTab = 'moments'}
          >
            <Icon name="zap" />
            Key Moments
          </button>
        </div>
        
        <div class="tab-content">
          {#if activeTab === 'transcript'}
            {#if video.has_transcript && video.transcript}
              <div class="transcript-header">
                <h3>Full Transcript</h3>
                <button 
                  class="btn btn-primary btn-sm"
                  on:click={summarizeTranscript}
                  disabled={summarizing}
                >
                  {#if summarizing}
                    <Icon name="spinner" class="animate-spin" />
                    Summarizing...
                  {:else}
                    <Icon name="sparkles" />
                    Summarize with AI
                  {/if}
                </button>
              </div>
              
              {#if transcriptSummary}
                <div class="transcript-summary">
                  <h4>AI Summary</h4>
                  <p>{transcriptSummary}</p>
                </div>
              {/if}
              
              <div class="transcript">
                {#each parseTranscript(video.transcript) as segment}
                  <div class="transcript-segment">
                    <button 
                      class="timestamp"
                      on:click={() => seekToTimestamp(segment.timestamp)}
                    >
                      {segment.timestamp}
                    </button>
                    <span class="text">{segment.text}</span>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="empty-state">
                <Icon name="file-x" size={48} />
                <p>No transcript available for this video</p>
              </div>
            {/if}
            
          {:else if activeTab === 'summary'}
            {#if video.learning_objectives && video.learning_objectives.length > 0}
              <div class="section">
                <h3>What You'll Learn</h3>
                <ul class="objectives">
                  {#each video.learning_objectives as objective}
                    <li>{objective}</li>
                  {/each}
                </ul>
              </div>
            {/if}
            
            {#if video.chapters && video.chapters.length > 0}
              <div class="section">
                <h3>Chapters</h3>
                <div class="chapters">
                  {#each video.chapters as chapter}
                    <div class="chapter">
                      <button 
                        class="chapter-time"
                        on:click={() => seekToTimestamp(chapter.timestamp)}
                      >
                        {chapter.timestamp}
                      </button>
                      <div class="chapter-info">
                        <h4>{chapter.title}</h4>
                        <p>{chapter.description}</p>
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
            
          {:else if activeTab === 'moments'}
            {#if video.key_moments && video.key_moments.length > 0}
              <div class="key-moments">
                <h3>Key Moments</h3>
                <div class="moments-list">
                  {#each video.key_moments as moment}
                    <div class="moment">
                      <button 
                        class="moment-time"
                        on:click={() => seekToTimestamp(moment.timestamp)}
                      >
                        <Icon name="play-circle" />
                        {moment.timestamp}
                      </button>
                      <p class="moment-description">{moment.description}</p>
                    </div>
                  {/each}
                </div>
              </div>
            {:else}
              <div class="empty-state">
                <Icon name="zap-off" size={48} />
                <p>No key moments detected</p>
              </div>
            {/if}
          {/if}
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="error">
    <Icon name="alert-circle" size={48} />
    <h2>Video not found</h2>
  </div>
{/if}

<style>
  .loading, .error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    min-height: 50vh;
    color: var(--color-text-muted);
  }
  
  .video-page {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .video-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }
  
  .back-link {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--color-text-muted);
    text-decoration: none;
    transition: color 0.2s;
  }
  
  .back-link:hover {
    color: var(--color-text);
  }
  
  .video-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .video-container {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 2rem;
  }
  
  @media (max-width: 1200px) {
    .video-container {
      grid-template-columns: 1fr;
    }
  }
  
  .player-section {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .youtube-player-wrapper {
    position: relative;
    width: 100%;
    padding-bottom: 56.25%; /* 16:9 aspect ratio */
    background: #000;
    border-radius: 0.75rem;
    overflow: hidden;
  }
  
  .youtube-player-wrapper :global(.youtube-embed) {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }
  
  .video-unavailable {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 4rem 2rem;
    background: var(--color-surface);
    border-radius: 0.75rem;
    color: var(--color-text-muted);
    min-height: 400px;
  }
  
  .video-unavailable p {
    font-size: 1.125rem;
    margin: 0;
  }
  
  .video-info {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .video-title {
    font-size: 1.75rem;
    font-weight: 600;
  }
  
  .video-meta {
    display: flex;
    gap: 1.5rem;
    color: var(--color-text-muted);
    font-size: 0.875rem;
  }
  
  .video-meta span {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }
  
  .video-summary {
    color: var(--color-text-muted);
    line-height: 1.6;
  }
  
  .topics {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .topics-label {
    font-weight: 500;
    color: var(--color-text-muted);
  }
  
  .topic-tag {
    padding: 0.25rem 0.75rem;
    background-color: var(--color-primary-light);
    color: var(--color-primary);
    border-radius: 9999px;
    font-size: 0.875rem;
  }
  
  .content-section {
    background-color: var(--color-surface);
    border-radius: 0.75rem;
    overflow: hidden;
  }
  
  .tabs {
    display: flex;
    border-bottom: 1px solid var(--color-border);
  }
  
  .tab {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 1rem;
    background: none;
    border: none;
    color: var(--color-text-muted);
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .tab.active {
    color: var(--color-primary);
    border-bottom: 2px solid var(--color-primary);
  }
  
  .tab-content {
    padding: 1.5rem;
    max-height: 600px;
    overflow-y: auto;
  }
  
  .transcript-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .transcript-summary {
    padding: 1rem;
    background-color: var(--color-primary-light);
    border-radius: 0.5rem;
    margin-bottom: 1.5rem;
  }
  
  .transcript-summary h4 {
    margin-bottom: 0.5rem;
    color: var(--color-primary);
  }
  
  .transcript {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .transcript-segment {
    display: flex;
    gap: 1rem;
    align-items: start;
  }
  
  .timestamp {
    flex-shrink: 0;
    padding: 0.25rem 0.5rem;
    background-color: var(--color-background);
    border: none;
    border-radius: 0.25rem;
    color: var(--color-primary);
    font-family: monospace;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .timestamp:hover {
    background-color: var(--color-primary);
    color: white;
  }
  
  .empty-state {
    text-align: center;
    padding: 3rem;
    color: var(--color-text-muted);
  }
  
  .section {
    margin-bottom: 2rem;
  }
  
  .section h3 {
    margin-bottom: 1rem;
  }
  
  .objectives {
    list-style: none;
    padding: 0;
  }
  
  .objectives li {
    padding: 0.5rem 0;
    padding-left: 1.5rem;
    position: relative;
  }
  
  .objectives li::before {
    content: "✓";
    position: absolute;
    left: 0;
    color: var(--color-success);
  }
  
  .chapters {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .chapter {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background-color: var(--color-background);
    border-radius: 0.5rem;
  }
  
  .chapter-time {
    flex-shrink: 0;
    padding: 0.5rem 0.75rem;
    background-color: var(--color-primary);
    color: white;
    border: none;
    border-radius: 0.375rem;
    font-family: monospace;
    cursor: pointer;
    transition: opacity 0.2s;
  }
  
  .chapter-time:hover {
    opacity: 0.9;
  }
  
  .chapter-info h4 {
    margin-bottom: 0.25rem;
  }
  
  .chapter-info p {
    color: var(--color-text-muted);
    font-size: 0.875rem;
  }
  
  .moments-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .moment {
    display: flex;
    align-items: start;
    gap: 1rem;
    padding: 1rem;
    background-color: var(--color-background);
    border-radius: 0.5rem;
    border-left: 3px solid var(--color-primary);
  }
  
  .moment-time {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: none;
    border: 1px solid var(--color-primary);
    border-radius: 0.375rem;
    color: var(--color-primary);
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .moment-time:hover {
    background-color: var(--color-primary);
    color: white;
  }
  
  .moment-description {
    flex: 1;
    line-height: 1.5;
  }
  
  .btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 0.5rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-primary {
    background-color: var(--color-primary);
    color: white;
  }
  
  .btn-secondary {
    background-color: var(--color-surface);
    color: var(--color-text);
  }
  
  .btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
  
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .animate-spin {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>