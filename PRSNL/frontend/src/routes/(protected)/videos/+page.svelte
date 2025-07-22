<script lang="ts">
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import VideoCard from '$lib/components/VideoCard.svelte';
  import { getTimeline } from '$lib/api';
  import type { Item } from '$lib/types/api';

  let videos: Item[] = [];
  let miniCourses: any[] = [];
  let loading = true;
  let selectedPlatform = 'all';
  let selectedCategory = 'all';
  let viewMode: 'timeline' | 'courses' = 'timeline';
  let searchTerm = '';

  const platforms = ['all', 'youtube', 'twitter', 'instagram'];

  async function loadVideos() {
    try {
      loading = true;
      // Use the API wrapper which handles camelCase conversion
      const data = await getTimeline(1, 100); // Get up to 100 items
      // Filter for video items only - check both type and item_type for compatibility
      videos = data.items.filter((item) => {
        const itemType = item.type || item.item_type || item.itemType;
        // Include both 'video' and 'youtube' types
        return itemType === 'video' || itemType === 'youtube';
      });
    } catch (error) {
      console.error('Error loading videos:', error);
    } finally {
      loading = false;
    }
  }

  async function loadMiniCourses() {
    try {
      // For now, show a message about needing more videos
      miniCourses = [];
      // Mini-courses will be enabled when we have more videos
    } catch (error) {
      console.error('Error loading mini-courses:', error);
    }
  }

  async function createMiniCourse(topic: string) {
    try {
      const response = await fetch('/api/video-streaming/mini-course', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          skill_level: 'beginner',
          max_videos: 10,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        // Navigate to mini-course view
        window.location.href = `/videos/course?data=${encodeURIComponent(JSON.stringify(data.data))}`;
      }
    } catch (error) {
      console.error('Error creating mini-course:', error);
    }
  }

  function filterVideos() {
    return videos.filter((video) => {
      // Platform filter
      if (selectedPlatform !== 'all' && video.platform !== selectedPlatform) return false;
      // Search filter
      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        const title = (video.title || '').toLowerCase();
        const summary = (video.summary || '').toLowerCase();
        if (!title.includes(search) && !summary.includes(search)) return false;
      }
      return true;
    });
  }

  function getVideoId(video: Item): string {
    return `VID_${String(videos.indexOf(video) + 1).padStart(3, '0')}${String.fromCharCode(65 + (videos.indexOf(video) % 26))}`;
  }

  function getVideoStatus(video: Item): string {
    if (video.status === 'pending') return 'PROCESSING';
    if (video.transcription) return 'INDEXED';
    return 'ARCHIVED';
  }

  function getNeuralScore(video: Item): number {
    // Generate a neural score based on video metadata
    let score = 75; // Base score
    if (video.transcription) score += 15;
    if (video.summary) score += 10;
    if (video.tags && video.tags.length > 0) score += 5;
    return Math.min(99, score + Math.floor(Math.random() * 10));
  }

  function formatDuration(seconds: number): string {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function getQualityIndicator(video: Item): string {
    // Random quality indicator for demo
    const qualities = ['4K', 'HD', 'SD'];
    return qualities[Math.floor(Math.random() * qualities.length)];
  }

  onMount(() => {
    loadVideos();
    loadMiniCourses();
  });
</script>

<div class="cortex-container">
  <!-- Matrix Grid Background -->
  <div class="matrix-grid"></div>

  <!-- Cortex Header -->
  <div class="cortex-header">
    <div class="cortex-title">
      <div class="neural-pulse"></div>
      VISUAL CORTEX MATRIX
    </div>
    <div class="cortex-stats">
      <div class="stat">
        <div class="stat-value">{videos.length}</div>
        <div class="stat-label">Neural Vids</div>
      </div>
      <div class="stat">
        <div class="stat-value">
          {Math.floor(videos.reduce((sum, v) => sum + (v.duration || 0), 0) / 3600)}h
        </div>
        <div class="stat-label">Runtime</div>
      </div>
      <div class="stat">
        <div class="stat-value">
          {Math.round((videos.filter((v) => v.transcription).length / videos.length) * 100) || 0}%
        </div>
        <div class="stat-label">Index Rate</div>
      </div>
    </div>
  </div>

  <!-- Matrix Controls -->
  <div class="matrix-controls">
    <div class="control-group">
      <button
        class="matrix-button"
        class:active={viewMode === 'timeline'}
        on:click={() => (viewMode = 'timeline')}
      >
        MATRIX
      </button>
      <button
        class="matrix-button"
        class:active={viewMode === 'courses'}
        on:click={() => (viewMode = 'courses')}
      >
        COURSES
      </button>
      <button class="matrix-button">NEURAL</button>
      <button class="matrix-button">ARCHIVE</button>
    </div>

    <div class="terminal-search">
      <span class="search-prompt">></span>
      <input
        type="text"
        class="search-input"
        placeholder="search neural video database..."
        bind:value={searchTerm}
      />
    </div>

    <div class="control-group">
      <select bind:value={selectedPlatform} class="matrix-select">
        {#each platforms as platform}
          <option value={platform}>
            {platform === 'all' ? 'ALL' : platform.toUpperCase()}
          </option>
        {/each}
      </select>
      <select bind:value={selectedCategory} class="matrix-select">
        <option value="all">ALL TYPES</option>
        <option value="tutorial">TUTORIAL</option>
        <option value="lecture">LECTURE</option>
        <option value="documentary">DOCS</option>
        <option value="other">OTHER</option>
      </select>
      <a href="/capture" class="matrix-button upload-btn">
        <Icon name="upload" />
        UPLOAD
      </a>
    </div>
  </div>

  {#if viewMode === 'timeline'}
    {#if loading}
      <div class="matrix-loading">
        <div class="loading-text">INITIALIZING NEURAL MATRIX...</div>
        <div class="loading-bar">
          <div class="loading-progress"></div>
        </div>
      </div>
    {:else if videos.length === 0}
      <div class="matrix-empty">
        <div class="empty-icon">⚠</div>
        <div class="empty-title">NO NEURAL DATA DETECTED</div>
        <div class="empty-message">Initialize video capture protocols to populate matrix</div>
      </div>
    {:else}
      <div class="video-matrix">
        {#each filterVideos() as video, index}
          <div class="matrix-cell">
            <div class="video-display">
              {#if video.thumbnail_url}
                <img
                  src={video.thumbnail_url}
                  alt={video.title}
                  class="video-thumbnail"
                />
              {:else}
                <div class="thumbnail-placeholder">
                  <Icon name="video" size="large" />
                </div>
              {/if}

              <div class="video-overlay">
                <button
                  class="play-command"
                  on:click={() => (window.location.href = `/videos/${video.id}`)}
                >
                  EXECUTE
                </button>
              </div>

              <div class="duration-display">{formatDuration(video.duration || 0)}</div>
              <div class="quality-indicator">{getQualityIndicator(video)}</div>
              <div class="neural-indicator"></div>
            </div>

            <div class="video-metadata">
              <div class="video-header">
                <div class="video-id">{getVideoId(video)}</div>
                <div class="video-status">{getVideoStatus(video)}</div>
              </div>

              <h3 class="video-title">{video.title || 'UNTITLED_VIDEO'}</h3>

              <p class="video-description">
                {video.summary || 'Neural analysis pending... Video indexed for processing.'}
              </p>

              <div class="video-metrics">
                <div class="metric">
                  <div class="metric-value">{video.platform || 'Unknown'}</div>
                  <div class="metric-label">Source</div>
                </div>
                <div class="metric">
                  <div class="metric-value">
                    {Math.floor(
                      (Date.now() - new Date(video.created_at || Date.now()).getTime()) / (1000 * 60 * 60 * 24)
                    )}d
                  </div>
                  <div class="metric-label">Age</div>
                </div>
                <div class="metric">
                  <div class="metric-value">{getNeuralScore(video)}%</div>
                  <div class="metric-label">Neural</div>
                </div>
              </div>

              <div class="neural-tags">
                {#if video.tags && video.tags.length > 0}
                  {#each video.tags.slice(0, 3) as tag}
                    <span class="neural-tag">{tag.toUpperCase()}</span>
                  {/each}
                {:else}
                  <span class="neural-tag">UNTAGGED</span>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {:else}
    <!-- Courses Section with Matrix styling -->
    <div class="matrix-courses">
      <div class="courses-header">
        <div class="courses-title">NEURAL COURSE GENERATOR</div>
        <div class="courses-subtitle">AI-powered learning path synthesis</div>
      </div>

      {#if videos.length < 5}
        <div class="matrix-empty">
          <div class="empty-icon">📚</div>
          <div class="empty-title">INSUFFICIENT NEURAL DATA</div>
          <div class="empty-message">
            Minimum 5 videos required for course synthesis. Current count: {videos.length}
          </div>
        </div>
      {:else}
        <div class="matrix-empty">
          <div class="empty-icon">🔬</div>
          <div class="empty-title">COURSE SYNTHESIS PROTOCOL</div>
          <div class="empty-message">Neural course generation algorithms coming online soon...</div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Matrix Footer -->
  <div class="matrix-footer">
    <div class="system-status">
      <div class="status-indicator status-active"></div>
      <div class="status-indicator status-processing"></div>
      <div class="status-indicator status-idle"></div>
      <span class="status-text">SYSTEM OPERATIONAL</span>
    </div>

    <div class="terminal-output">
      > visual_cortex_matrix_v2.1_active | {videos.length}_videos_indexed | processing_queue_clear
    </div>
  </div>
</div>

<style>
  .cortex-container {
    max-width: 100%;
    padding: 1rem;
    min-height: 100vh;
    background: #0a0a0a;
    font-family: 'JetBrains Mono', monospace;
    color: #e0e0e0;
    position: relative;
  }

  .matrix-grid {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background:
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 40px,
        rgba(0, 255, 100, 0.1) 40px,
        rgba(0, 255, 100, 0.1) 41px
      ),
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 40px,
        rgba(0, 255, 100, 0.1) 40px,
        rgba(0, 255, 100, 0.1) 41px
      );
    pointer-events: none;
    z-index: -1;
  }

  .cortex-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2rem;
    background: rgba(26, 26, 26, 0.9);
    border: 1px solid rgba(0, 255, 100, 0.3);
    border-radius: 16px;
    margin-bottom: 2rem;
    backdrop-filter: blur(20px);
  }

  .cortex-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #00ff64;
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .neural-pulse {
    width: 20px;
    height: 20px;
    background: #dc143c;
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.5);
      opacity: 0.7;
    }
  }

  .cortex-stats {
    display: flex;
    gap: 2rem;
    font-size: 0.875rem;
  }

  .stat {
    text-align: center;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #dc143c;
  }

  .stat-label {
    color: #666;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .matrix-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    background: rgba(26, 26, 26, 0.9);
    border: 1px solid rgba(220, 20, 60, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(20px);
  }

  .control-group {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .matrix-button {
    background: rgba(0, 0, 0, 0.5);
    border: 1px solid rgba(0, 255, 100, 0.3);
    color: #00ff64;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-family: inherit;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .matrix-button:hover,
  .matrix-button.active {
    border-color: #dc143c;
    color: #dc143c;
    background: rgba(220, 20, 60, 0.1);
  }
  
  .upload-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
    background: rgba(220, 20, 60, 0.1);
    border: 1px solid #dc143c;
    color: #dc143c;
    transition: all 0.3s ease;
  }
  
  .upload-btn:hover {
    background: rgba(220, 20, 60, 0.2);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(220, 20, 60, 0.3);
  }

  .terminal-search {
    background: rgba(0, 0, 0, 0.7);
    border: 1px solid rgba(0, 255, 100, 0.5);
    border-radius: 8px;
    padding: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 300px;
  }

  .search-prompt {
    color: #00ff64;
    font-weight: 600;
  }

  .search-input {
    background: transparent;
    border: none;
    color: #e0e0e0;
    font-family: inherit;
    font-size: inherit;
    flex: 1;
    outline: none;
  }

  .search-input::placeholder {
    color: #666;
  }

  .matrix-select {
    background: rgba(0, 0, 0, 0.5);
    border: 1px solid rgba(0, 255, 100, 0.3);
    color: #00ff64;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-family: inherit;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .matrix-loading {
    text-align: center;
    padding: 4rem 2rem;
    margin-left: 80px;
  }

  .loading-text {
    color: #00ff64;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    margin-bottom: 2rem;
    font-size: 1.2rem;
    letter-spacing: 2px;
  }

  .loading-bar {
    width: 300px;
    height: 8px;
    background: rgba(0, 0, 0, 0.5);
    border-radius: 4px;
    overflow: hidden;
    margin: 0 auto;
  }

  .loading-progress {
    height: 100%;
    background: linear-gradient(90deg, #dc143c, #00ff64);
    animation: loading-animation 2s ease-in-out infinite;
  }

  @keyframes loading-animation {
    0% {
      width: 0%;
    }
    50% {
      width: 70%;
    }
    100% {
      width: 100%;
    }
  }

  .matrix-empty {
    text-align: center;
    padding: 4rem 2rem;
    margin-left: 80px;
  }

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }

  .empty-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #dc143c;
    margin-bottom: 1rem;
    letter-spacing: 2px;
  }

  .empty-message {
    color: #a0a0a0;
    font-size: 0.9rem;
    line-height: 1.5;
  }

  .video-matrix {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }

  .matrix-cell {
    background: rgba(26, 26, 26, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    overflow: hidden;
    backdrop-filter: blur(15px);
    transition: all 0.3s ease;
    position: relative;
  }

  .matrix-cell::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #dc143c, #00ff64);
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .matrix-cell:hover {
    transform: translateY(-5px);
    border-color: rgba(220, 20, 60, 0.5);
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
  }

  .matrix-cell:hover::before {
    opacity: 1;
  }

  .video-display {
    position: relative;
    aspect-ratio: 16 / 9;
    background: #1a1a1a;
    overflow: hidden;
  }

  .video-thumbnail {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
  }

  .matrix-cell:hover .video-thumbnail {
    transform: scale(1.02);
  }

  .thumbnail-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.5);
    color: #666;
  }

  .video-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      45deg,
      rgba(220, 20, 60, 0.8) 0%,
      transparent 50%,
      rgba(0, 255, 100, 0.8) 100%
    );
    opacity: 0;
    transition: opacity 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .matrix-cell:hover .video-overlay {
    opacity: 1;
  }

  .play-command {
    background: rgba(0, 0, 0, 0.9);
    color: #00ff64;
    padding: 1rem 2rem;
    border: 1px solid #00ff64;
    border-radius: 8px;
    font-family: inherit;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.3s ease;
    text-transform: uppercase;
    letter-spacing: 2px;
  }

  .play-command:hover {
    background: #00ff64;
    color: #0a0a0a;
  }

  .duration-display {
    position: absolute;
    bottom: 1rem;
    right: 1rem;
    background: rgba(0, 0, 0, 0.9);
    color: #00ff64;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: inherit;
  }

  .quality-indicator {
    position: absolute;
    top: 1rem;
    left: 1rem;
    background: rgba(220, 20, 60, 0.9);
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
  }

  .neural-indicator {
    position: absolute;
    top: 1rem;
    right: 1rem;
    width: 12px;
    height: 12px;
    background: #00ff64;
    border-radius: 50%;
    animation: neural-blink 1.5s ease-in-out infinite;
  }

  @keyframes neural-blink {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.3;
    }
  }

  .video-metadata {
    padding: 1.5rem;
  }

  .video-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .video-id {
    color: #666;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .video-status {
    color: #00ff64;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .video-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: #e0e0e0;
    margin-bottom: 0.75rem;
    line-height: 1.4;
    text-transform: uppercase;
  }

  .video-description {
    color: #a0a0a0;
    font-size: 0.8rem;
    line-height: 1.5;
    margin-bottom: 1rem;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .video-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .metric {
    text-align: center;
    padding: 0.5rem;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 6px;
  }

  .metric-value {
    font-size: 0.9rem;
    font-weight: 600;
    color: #dc143c;
    text-transform: uppercase;
  }

  .metric-label {
    font-size: 0.65rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .neural-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .neural-tag {
    background: rgba(0, 255, 100, 0.1);
    color: #00ff64;
    padding: 0.25rem 0.5rem;
    border: 1px solid rgba(0, 255, 100, 0.3);
    border-radius: 6px;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .matrix-courses {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    background: rgba(26, 26, 26, 0.9);
    border: 1px solid rgba(74, 158, 255, 0.3);
    border-radius: 16px;
    backdrop-filter: blur(20px);
  }

  .courses-header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .courses-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #4a9eff;
    margin-bottom: 0.5rem;
    letter-spacing: 2px;
  }

  .courses-subtitle {
    color: #a0a0a0;
    font-size: 0.9rem;
  }

  .matrix-footer {
    background: rgba(26, 26, 26, 0.9);
    border: 1px solid rgba(74, 158, 255, 0.3);
    border-radius: 16px;
    padding: 2rem;
    backdrop-filter: blur(20px);
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 3rem;
  }

  .system-status {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .status-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    animation: status-pulse 2s ease-in-out infinite;
  }

  .status-active {
    background: #00ff64;
  }
  .status-processing {
    background: #dc143c;
    animation-delay: 0.5s;
  }
  .status-idle {
    background: #4a9eff;
    animation-delay: 1s;
  }

  @keyframes status-pulse {
    0%,
    100% {
      opacity: 0.5;
    }
    50% {
      opacity: 1;
    }
  }

  .status-text {
    color: #00ff64;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .terminal-output {
    font-size: 0.8rem;
    color: #00ff64;
    font-family: inherit;
  }

  @media (max-width: 768px) {
    .cortex-header {
      flex-direction: column;
      gap: 1rem;
      text-align: center;
    }

    .matrix-controls {
      flex-direction: column;
      gap: 1rem;
    }

    .video-matrix {
      grid-template-columns: 1fr;
    }

    .matrix-footer {
      flex-direction: column;
      gap: 1rem;
      text-align: center;
    }

    .terminal-search {
      min-width: 100%;
    }
  }
</style>
