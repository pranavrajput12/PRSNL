<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import { getItem } from '$lib/api';
  
  let course: any = null;
  let currentModuleIndex = 0;
  let currentVideo: any = null;
  let progress: Record<string, boolean> = {};
  let loading = true;
  
  // Load progress from localStorage
  function loadProgress() {
    const saved = localStorage.getItem(`course_progress_${course.topic}`);
    if (saved) {
      progress = JSON.parse(saved);
    }
  }
  
  // Save progress to localStorage
  function saveProgress() {
    localStorage.setItem(`course_progress_${course.topic}`, JSON.stringify(progress));
  }
  
  // Mark video as completed
  function markCompleted(videoId: string) {
    progress[videoId] = true;
    saveProgress();
    
    // Auto-advance to next video if available
    if (currentModuleIndex < course.modules.length - 1) {
      setTimeout(() => {
        currentModuleIndex++;
        loadCurrentVideo();
      }, 1000);
    }
  }
  
  // Load current video details
  async function loadCurrentVideo() {
    if (!course.modules[currentModuleIndex]) return;
    
    const module = course.modules[currentModuleIndex];
    try {
      const item = await getItem(module.video_id);
      currentVideo = {
        ...item,
        ...item.metadata?.video,
        ...module
      };
    } catch (error) {
      console.error('Error loading video:', error);
    }
  }
  
  // Calculate overall progress
  function calculateProgress() {
    const completed = Object.values(progress).filter(Boolean).length;
    return Math.round((completed / course.modules.length) * 100);
  }
  
  onMount(() => {
    // Parse course data from URL params
    const urlParams = new URLSearchParams(window.location.search);
    const courseData = urlParams.get('data');
    
    if (courseData) {
      try {
        course = JSON.parse(decodeURIComponent(courseData));
        loading = false;
        loadProgress();
        loadCurrentVideo();
      } catch (error) {
        console.error('Error parsing course data:', error);
        loading = false;
      }
    } else {
      loading = false;
    }
  });
  
  function selectModule(index: number) {
    currentModuleIndex = index;
    loadCurrentVideo();
  }
</script>

{#if loading}
  <div class="loading">
    <Icon name="spinner" class="animate-spin" />
    Loading course...
  </div>
{:else if course}
  <div class="course-page">
    <div class="course-header">
      <div class="header-content">
        <a href="/videos" class="back-link">
          <Icon name="arrow-left" />
          Back to Videos
        </a>
        
        <div class="course-info">
          <h1 class="course-title">{course.title}</h1>
          <p class="course-description">{course.description}</p>
          
          <div class="course-meta">
            <span class="meta-item">
              <Icon name="book-open" size={16} />
              {course.modules.length} videos
            </span>
            <span class="meta-item">
              <Icon name="clock" size={16} />
              {course.total_duration || 'Duration varies'}
            </span>
            <span class="meta-item">
              <Icon name="trending-up" size={16} />
              {course.skill_level}
            </span>
          </div>
        </div>
        
        <div class="progress-section">
          <div class="progress-header">
            <span>Course Progress</span>
            <span class="progress-percentage">{calculateProgress()}%</span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill"
              style="width: {calculateProgress()}%"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="course-content">
      <div class="video-section">
        {#if currentVideo}
          <VideoPlayer 
            url={currentVideo.url}
            videoId={currentVideo.video_details?.video_id || currentVideo.video_id}
            platform={currentVideo.video_details?.platform || currentVideo.platform}
            embedHtml={currentVideo.video_details?.embed_html}
          />
          
          <div class="video-details">
            <h2 class="video-title">
              Module {currentModuleIndex + 1}: {currentVideo.title}
            </h2>
            
            {#if currentVideo.why_this_order}
              <div class="module-rationale">
                <Icon name="info" size={16} />
                {currentVideo.why_this_order}
              </div>
            {/if}
            
            {#if currentVideo.key_takeaways && currentVideo.key_takeaways.length > 0}
              <div class="takeaways">
                <h3>Key Takeaways</h3>
                <ul>
                  {#each currentVideo.key_takeaways as takeaway}
                    <li>{takeaway}</li>
                  {/each}
                </ul>
              </div>
            {/if}
            
            <div class="video-actions">
              <button 
                class="btn btn-primary"
                on:click={() => markCompleted(currentVideo.video_id || currentVideo.id)}
                disabled={progress[currentVideo.video_id || currentVideo.id]}
              >
                {#if progress[currentVideo.video_id || currentVideo.id]}
                  <Icon name="check-circle" />
                  Completed
                {:else}
                  <Icon name="circle" />
                  Mark as Complete
                {/if}
              </button>
              
              {#if currentModuleIndex < course.modules.length - 1}
                <button 
                  class="btn btn-secondary"
                  on:click={() => selectModule(currentModuleIndex + 1)}
                >
                  Next Video
                  <Icon name="arrow-right" />
                </button>
              {/if}
            </div>
          </div>
        {/if}
      </div>
      
      <div class="course-sidebar">
        <h3 class="sidebar-title">Course Content</h3>
        
        {#if course.learning_objectives && course.learning_objectives.length > 0}
          <div class="objectives-section">
            <h4>Learning Objectives</h4>
            <ul class="objectives">
              {#each course.learning_objectives as objective}
                <li>{objective}</li>
              {/each}
            </ul>
          </div>
        {/if}
        
        {#if course.prerequisites && course.prerequisites.length > 0}
          <div class="prerequisites-section">
            <h4>Prerequisites</h4>
            <ul class="prerequisites">
              {#each course.prerequisites as prereq}
                <li>{prereq}</li>
              {/each}
            </ul>
          </div>
        {/if}
        
        <div class="modules-list">
          <h4>Modules</h4>
          {#each course.modules as module, index}
            <button
              class="module-item"
              class:active={currentModuleIndex === index}
              class:completed={progress[module.video_id]}
              on:click={() => selectModule(index)}
            >
              <div class="module-number">
                {#if progress[module.video_id]}
                  <Icon name="check-circle" size={20} />
                {:else}
                  {index + 1}
                {/if}
              </div>
              <div class="module-info">
                <div class="module-title">{module.title}</div>
                {#if module.video_details?.platform}
                  <div class="module-meta">
                    <Icon name={module.video_details.platform} size={12} />
                    {module.video_details.platform}
                  </div>
                {/if}
              </div>
            </button>
          {/each}
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="error">
    <Icon name="alert-circle" size={48} />
    <h2>Course not found</h2>
    <a href="/videos" class="btn btn-primary">Browse Videos</a>
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
  
  .course-page {
    min-height: 100vh;
    background-color: var(--color-background);
  }
  
  .course-header {
    background-color: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    padding: 2rem 0;
  }
  
  .header-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 2rem;
  }
  
  .back-link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--color-text-muted);
    text-decoration: none;
    margin-bottom: 1rem;
    transition: color 0.2s;
  }
  
  .back-link:hover {
    color: var(--color-text);
  }
  
  .course-info {
    margin-bottom: 2rem;
  }
  
  .course-title {
    font-size: 2rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }
  
  .course-description {
    font-size: 1.125rem;
    color: var(--color-text-muted);
    margin-bottom: 1rem;
  }
  
  .course-meta {
    display: flex;
    gap: 2rem;
    color: var(--color-text-muted);
  }
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .progress-section {
    max-width: 400px;
  }
  
  .progress-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }
  
  .progress-percentage {
    font-weight: 600;
    color: var(--color-primary);
  }
  
  .progress-bar {
    height: 8px;
    background-color: var(--color-background);
    border-radius: 4px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background-color: var(--color-primary);
    transition: width 0.3s ease;
  }
  
  .course-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    display: grid;
    grid-template-columns: 1fr 350px;
    gap: 2rem;
  }
  
  @media (max-width: 1200px) {
    .course-content {
      grid-template-columns: 1fr;
    }
    
    .course-sidebar {
      order: -1;
    }
  }
  
  .video-section {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .video-details {
    background-color: var(--color-surface);
    padding: 1.5rem;
    border-radius: 0.75rem;
  }
  
  .video-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
  }
  
  .module-rationale {
    display: flex;
    gap: 0.5rem;
    padding: 1rem;
    background-color: var(--color-primary-light);
    color: var(--color-primary);
    border-radius: 0.5rem;
    margin-bottom: 1.5rem;
    font-size: 0.875rem;
  }
  
  .takeaways {
    margin-bottom: 1.5rem;
  }
  
  .takeaways h3 {
    font-size: 1.125rem;
    margin-bottom: 0.75rem;
  }
  
  .takeaways ul {
    list-style: none;
    padding: 0;
  }
  
  .takeaways li {
    padding: 0.5rem 0;
    padding-left: 1.5rem;
    position: relative;
  }
  
  .takeaways li::before {
    content: "→";
    position: absolute;
    left: 0;
    color: var(--color-primary);
  }
  
  .video-actions {
    display: flex;
    gap: 1rem;
  }
  
  .course-sidebar {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .sidebar-title {
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  .objectives-section,
  .prerequisites-section {
    padding: 1rem;
    background-color: var(--color-surface);
    border-radius: 0.5rem;
  }
  
  .objectives-section h4,
  .prerequisites-section h4 {
    font-size: 0.875rem;
    text-transform: uppercase;
    color: var(--color-text-muted);
    margin-bottom: 0.75rem;
  }
  
  .objectives,
  .prerequisites {
    list-style: none;
    padding: 0;
    font-size: 0.875rem;
  }
  
  .objectives li,
  .prerequisites li {
    padding: 0.375rem 0;
    padding-left: 1.25rem;
    position: relative;
  }
  
  .objectives li::before {
    content: "✓";
    position: absolute;
    left: 0;
    color: var(--color-success);
  }
  
  .prerequisites li::before {
    content: "•";
    position: absolute;
    left: 0;
    color: var(--color-text-muted);
  }
  
  .modules-list {
    background-color: var(--color-surface);
    border-radius: 0.75rem;
    padding: 1rem;
  }
  
  .modules-list h4 {
    font-size: 0.875rem;
    text-transform: uppercase;
    color: var(--color-text-muted);
    margin-bottom: 1rem;
  }
  
  .module-item {
    display: flex;
    gap: 1rem;
    width: 100%;
    padding: 0.75rem;
    background: none;
    border: none;
    border-radius: 0.5rem;
    text-align: left;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .module-item:hover {
    background-color: var(--color-background);
  }
  
  .module-item.active {
    background-color: var(--color-primary-light);
  }
  
  .module-number {
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--color-background);
    border-radius: 50%;
    font-weight: 600;
    flex-shrink: 0;
  }
  
  .module-item.completed .module-number {
    background-color: var(--color-success);
    color: white;
  }
  
  .module-item.active .module-number {
    background-color: var(--color-primary);
    color: white;
  }
  
  .module-info {
    flex: 1;
  }
  
  .module-title {
    font-size: 0.875rem;
    font-weight: 500;
    line-height: 1.4;
  }
  
  .module-meta {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
    color: var(--color-text-muted);
    margin-top: 0.25rem;
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
  
  .btn:hover {
    opacity: 0.9;
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