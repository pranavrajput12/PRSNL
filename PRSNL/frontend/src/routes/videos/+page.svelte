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
  
  const platforms = ['all', 'youtube', 'twitter', 'instagram'];
  
  async function loadVideos() {
    try {
      loading = true;
      // Use the API wrapper which handles camelCase conversion
      const data = await getTimeline(1, 100); // Get up to 100 items
      // Filter for video items only
      videos = data.items.filter(item => item.itemType === 'video' || item.item_type === 'video');
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
          max_videos: 10
        })
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
    return videos.filter(video => {
      if (selectedPlatform !== 'all' && video.platform !== selectedPlatform) return false;
      if (selectedCategory !== 'all' && video.category !== selectedCategory) return false;
      return true;
    });
  }
  
  onMount(() => {
    loadVideos();
    loadMiniCourses();
  });
</script>

<div class="page">
  <div class="header">
    <h1 class="page-title">
      <Icon name="video" />
      Video Library
    </h1>
    
    <div class="header-actions">
      <div class="view-toggle">
        <button 
          class="toggle-btn"
          class:active={viewMode === 'timeline'}
          on:click={() => viewMode = 'timeline'}
        >
          <Icon name="grid" />
          Timeline
        </button>
        <button 
          class="toggle-btn"
          class:active={viewMode === 'courses'}
          on:click={() => viewMode = 'courses'}
        >
          <Icon name="book" />
          Courses
        </button>
      </div>
    </div>
  </div>
  
  {#if viewMode === 'timeline'}
    <div class="filters">
      <select bind:value={selectedPlatform} class="filter-select">
        {#each platforms as platform}
          <option value={platform}>
            {platform === 'all' ? 'All Platforms' : platform.charAt(0).toUpperCase() + platform.slice(1)}
          </option>
        {/each}
      </select>
      
      <select bind:value={selectedCategory} class="filter-select">
        <option value="all">All Categories</option>
        <option value="tutorial">Tutorials</option>
        <option value="lecture">Lectures</option>
        <option value="documentary">Documentaries</option>
        <option value="other">Other</option>
      </select>
      
      <div class="stats">
        {videos.length} videos • {videos.filter(v => v.transcription).length} with transcripts
      </div>
    </div>
    
    {#if loading}
      <div class="loading">
        <Icon name="spinner" class="animate-spin" />
        Loading videos...
      </div>
    {:else if videos.length === 0}
      <div class="empty-state">
        <Icon name="video" size={48} />
        <h2>No videos yet</h2>
        <p>Save some video links to see them here!</p>
      </div>
    {:else}
      <div class="video-grid">
        {#each filterVideos() as video}
          <VideoCard {video} />
        {/each}
      </div>
    {/if}
    
  {:else}
    <!-- Mini-Courses View -->
    <div class="courses-section">
      <div class="section-header">
        <h2>Create a Mini-Course</h2>
        <p>Let AI organize your videos into structured learning paths</p>
      </div>
      
      <div class="course-suggestions">
        {#if videos.length < 5}
          <div class="empty-state">
            <Icon name="book-open" size={48} />
            <h3>Need More Videos for Mini-Courses</h3>
            <p>Mini-courses require at least 5 videos in your library.</p>
            <p>You currently have {videos.length} video{videos.length !== 1 ? 's' : ''}.</p>
            <p>Add more videos to unlock this feature!</p>
          </div>
        {:else if miniCourses.length === 0}
          <div class="empty-state">
            <Icon name="sparkles" size={48} />
            <h3>Mini-Course Feature Coming Soon!</h3>
            <p>AI-powered course creation will organize your videos into learning paths.</p>
          </div>
        {:else}
          {#each miniCourses as course}
            <div class="course-suggestion">
              <h3>{course.suggested_title}</h3>
              <p>{course.video_count} videos available</p>
              <button 
                class="btn btn-primary"
                on:click={() => createMiniCourse(course.topic)}
              >
                Create Course
              </button>
            </div>
          {/each}
        {/if}
      </div>
      
      <div class="custom-course">
        <h3>Or create a custom course</h3>
        <form on:submit|preventDefault={(e) => {
          const formData = new FormData(e.target);
          createMiniCourse(formData.get('topic'));
        }}>
          <input 
            type="text" 
            name="topic"
            placeholder="Enter a topic (e.g., 'machine learning', 'web development')"
            class="input"
            required
          />
          <button type="submit" class="btn btn-primary">
            Generate Course
          </button>
        </form>
      </div>
    </div>
  {/if}
</div>

<style>
  .page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }
  
  .page-title {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 2rem;
    font-weight: 600;
    color: var(--color-text);
  }
  
  .header-actions {
    display: flex;
    gap: 1rem;
  }
  
  .view-toggle {
    display: flex;
    background-color: var(--color-surface);
    border-radius: 0.5rem;
    padding: 0.25rem;
  }
  
  .toggle-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: none;
    border: none;
    color: var(--color-text-muted);
    cursor: pointer;
    border-radius: 0.375rem;
    transition: all 0.2s;
  }
  
  .toggle-btn.active {
    background-color: var(--color-primary);
    color: white;
  }
  
  .filters {
    display: flex;
    gap: 1rem;
    align-items: center;
    margin-bottom: 2rem;
    padding: 1rem;
    background-color: var(--color-surface);
    border-radius: 0.5rem;
  }
  
  .filter-select {
    padding: 0.5rem 1rem;
    background-color: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 0.375rem;
    color: var(--color-text);
  }
  
  .stats {
    margin-left: auto;
    color: var(--color-text-muted);
    font-size: 0.875rem;
  }
  
  .video-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.5rem;
  }
  
  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 4rem;
    color: var(--color-text-muted);
  }
  
  .empty-state {
    text-align: center;
    padding: 4rem;
    color: var(--color-text-muted);
  }
  
  .empty-state h2 {
    margin-top: 1rem;
    font-size: 1.5rem;
    color: var(--color-text);
  }
  
  .courses-section {
    max-width: 800px;
    margin: 0 auto;
  }
  
  .section-header {
    text-align: center;
    margin-bottom: 3rem;
  }
  
  .section-header h2 {
    font-size: 1.75rem;
    margin-bottom: 0.5rem;
  }
  
  .section-header p {
    color: var(--color-text-muted);
  }
  
  .course-suggestions {
    display: grid;
    gap: 1rem;
    margin-bottom: 3rem;
  }
  
  .course-suggestion {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    background-color: var(--color-surface);
    border-radius: 0.75rem;
    transition: transform 0.2s;
  }
  
  .course-suggestion:hover {
    transform: translateY(-2px);
  }
  
  .course-suggestion h3 {
    font-size: 1.125rem;
    margin-bottom: 0.25rem;
  }
  
  .course-suggestion p {
    color: var(--color-text-muted);
    font-size: 0.875rem;
  }
  
  .custom-course {
    padding: 2rem;
    background-color: var(--color-surface);
    border-radius: 0.75rem;
  }
  
  .custom-course h3 {
    margin-bottom: 1rem;
  }
  
  .custom-course form {
    display: flex;
    gap: 1rem;
  }
  
  .input {
    flex: 1;
    padding: 0.75rem 1rem;
    background-color: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 0.5rem;
    color: var(--color-text);
  }
  
  .btn {
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
  
  .btn-primary:hover {
    opacity: 0.9;
  }
</style>