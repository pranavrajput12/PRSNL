<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import Icon from '$lib/components/Icon.svelte';
  import type { DevelopmentItem } from '$lib/api/development';

  let project: DevelopmentItem | null = null;
  let relatedProjects: DevelopmentItem[] = [];
  let loading = true;
  let error: string | null = null;

  // UI State
  let activeTab = 'overview'; // overview, progress, milestones, ai-analysis
  let sidebarCollapsed = false;
  let progressMode = 'visual'; // visual, detailed, timeline

  // AI Analysis & Learning Path
  let aiInsights: string[] = [];
  let learningPath: string[] = [];
  let isAIAnalyzing = false;

  // Progress tracking (simulated - would come from API)
  let projectProgress = 0;
  let milestones: any[] = [];
  let currentSkills: string[] = [];
  let nextSkills: string[] = [];

  $: projectId = $page.params.id;

  onMount(async () => {
    if (projectId) {
      await loadProject();
    }
  });

  async function loadProject() {
    try {
      loading = true;
      error = null;

      // Fetch project details
      const response = await fetch(`/api/development/docs?content_type=progress`);
      if (!response.ok) throw new Error('Failed to fetch project');

      const projects = await response.json();
      project = projects.find((p: DevelopmentItem) => p.id === projectId);

      if (!project) throw new Error('Project not found');

      // Load related projects
      await loadRelatedProjects();

      // Generate progress data and AI insights
      await generateProgressData();
      await generateAIInsights();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unknown error';
    } finally {
      loading = false;
    }
  }

  async function loadRelatedProjects() {
    if (!project) return;

    try {
      const response = await fetch(`/api/development/docs?content_type=progress&limit=6`);
      if (response.ok) {
        const projects = await response.json();
        relatedProjects = projects
          .filter(
            (p: DevelopmentItem) =>
              p.id !== project?.id &&
              (p.project_category === project?.project_category ||
                p.programming_language === project?.programming_language ||
                p.learning_path === project?.learning_path ||
                p.tags.some((tag) => project?.tags.includes(tag)))
          )
          .slice(0, 5);
      }
    } catch (err) {
      console.error('Failed to load related projects:', err);
    }
  }

  async function generateProgressData() {
    if (!project) return;

    // Simulate progress calculation based on project data
    const hash = project.id.split('').reduce((a, b) => a + b.charCodeAt(0), 0);
    projectProgress = hash % 100;

    // Generate milestones based on difficulty and category
    const difficultyMilestones = {
      1: ['Setup Environment', 'Complete Tutorial', 'Build First Project'],
      2: ['Advanced Concepts', 'Real-world Application', 'Best Practices'],
      3: ['Complex Implementation', 'Performance Optimization', 'Expert Techniques'],
      4: ['Advanced Architecture', 'Scalability', 'Industry Standards'],
      5: ['Innovation', 'Teaching Others', 'Contribution to Community'],
    };

    const level = project.difficulty_level || 2;
    milestones = (difficultyMilestones[level] || difficultyMilestones[2]).map(
      (milestone, index) => ({
        id: index + 1,
        title: milestone,
        completed: index < Math.floor(projectProgress / 33),
        description: `${milestone} for ${project.project_category || 'development'}`,
      })
    );

    // Generate current and next skills
    const allSkills = project.tags.concat(
      project.programming_language ? [project.programming_language] : []
    );
    currentSkills = allSkills.slice(0, Math.max(1, Math.floor(allSkills.length * 0.6)));
    nextSkills = allSkills.slice(currentSkills.length);
  }

  async function generateAIInsights() {
    if (!project) return;

    try {
      isAIAnalyzing = true;
      // Simulate AI analysis - replace with actual AI service call
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const category = project.project_category || 'development';
      const difficulty = getDifficultyLabel(project.difficulty_level || 2);
      const isCareerFocused = project.is_career_related;

      aiInsights = [
        `This ${difficulty.toLowerCase()} ${category.toLowerCase()} project is ${isCareerFocused ? 'highly valuable' : 'beneficial'} for your professional growth.`,
        `Current progress: ${projectProgress}% complete. You're ${projectProgress > 50 ? 'well on your way' : 'getting started'} with this learning journey.`,
        `Learning path focus: ${project.learning_path || 'General skill development'} with emphasis on practical application.`,
        `Skill development: Building expertise in ${currentSkills.join(', ')} and progressing toward ${nextSkills.slice(0, 2).join(', ')}.`,
        `Time investment: Based on difficulty level, expect ${getEstimatedTimeCommitment(project.difficulty_level || 2)} to complete.`,
      ];

      // Generate learning path recommendations
      learningPath = [
        `Foundation: ${currentSkills[0] || project.programming_language || 'Core concepts'}`,
        `Practice: Build ${Math.floor(Math.random() * 3) + 2}-${Math.floor(Math.random() * 3) + 5} projects`,
        `Advanced: ${nextSkills[0] || 'Advanced techniques'}`,
        `Mastery: ${nextSkills[1] || 'Expert-level implementation'}`,
        `Contribution: Share knowledge and mentor others`,
      ];
    } catch (err) {
      console.error('AI analysis failed:', err);
    } finally {
      isAIAnalyzing = false;
    }
  }

  function getDifficultyColor(level: number): string {
    const colors = {
      1: '#10b981', // Green
      2: '#3b82f6', // Blue
      3: '#f59e0b', // Amber
      4: '#ef4444', // Red
      5: '#8b5cf6', // Purple
    };
    return colors[level] || '#6b7280';
  }

  function getDifficultyLabel(level: number): string {
    const labels = {
      1: 'Beginner',
      2: 'Intermediate',
      3: 'Advanced',
      4: 'Expert',
      5: 'Master',
    };
    return labels[level] || 'Unknown';
  }

  function getLanguageIcon(language: string): string {
    const icons = {
      python: '🐍',
      javascript: '🟨',
      typescript: '🔷',
      java: '☕',
      go: '🐹',
      rust: '🦀',
      cpp: '⚡',
    };
    return icons[language] || '💻';
  }

  function getEstimatedTimeCommitment(level: number): string {
    const times = {
      1: '2-4 weeks',
      2: '1-3 months',
      3: '3-6 months',
      4: '6-12 months',
      5: '1+ years',
    };
    return times[level] || '2-6 months';
  }

  function getProgressColor(progress: number): string {
    if (progress < 25) return '#ef4444'; // Red
    if (progress < 50) return '#f59e0b'; // Orange
    if (progress < 75) return '#3b82f6'; // Blue
    return '#10b981'; // Green
  }

  function getProgressLabel(progress: number): string {
    if (progress < 25) return 'Getting Started';
    if (progress < 50) return 'Making Progress';
    if (progress < 75) return 'Well Underway';
    return 'Nearly Complete';
  }

  function getCategoryIcon(category: string): string {
    const icons = {
      Frontend: '🎨',
      Backend: '⚙️',
      DevOps: '🚀',
      Mobile: '📱',
      'AI/ML': '🤖',
      'Data Science': '📊',
      'Game Development': '🎮',
      Desktop: '💻',
      'Web Development': '🌐',
      'API Development': '🔌',
      Documentation: '📚',
    };
    return icons[category] || '📁';
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  }

  function handleBackToList() {
    goto('/code-cortex/projects');
  }

  function handleOpenExternal() {
    if (project?.url) {
      window.open(project.url, '_blank');
    }
  }

  function handleUpdateProgress(newProgress: number) {
    projectProgress = newProgress;
    // In a real app, this would update the backend
    generateProgressData();
  }
</script>

<svelte:head>
  <title>{project?.title || 'Learning Project'} - Code Cortex | PRSNL</title>
</svelte:head>

{#if loading}
  <div class="loading-container">
    <div class="neural-pulse"></div>
    <span>Loading learning project...</span>
  </div>
{:else if error}
  <div class="error-container">
    <Icon name="alert-circle" size="48" />
    <h2>Error Loading Project</h2>
    <p>{error}</p>
    <button class="back-button" on:click={handleBackToList}>
      <Icon name="arrow-left" size="16" />
      Back to Progress
    </button>
  </div>
{:else if project}
  <div class="project-detail-page">
    <!-- Header -->
    <div class="project-header">
      <div class="header-content">
        <div class="header-left">
          <button class="back-button" on:click={handleBackToList}>
            <Icon name="arrow-left" size="16" />
          </button>
          <div class="project-title-section">
            <h1>{project.title}</h1>
            <div class="project-meta">
              {#if project.project_category}
                <span class="meta-badge category">
                  {getCategoryIcon(project.project_category)}
                  {project.project_category}
                </span>
              {/if}
              {#if project.programming_language}
                <span class="meta-badge language">
                  {getLanguageIcon(project.programming_language)}
                  {project.programming_language}
                </span>
              {/if}
              {#if project.difficulty_level}
                <span
                  class="meta-badge difficulty"
                  style="background-color: {getDifficultyColor(
                    project.difficulty_level
                  )}40; color: {getDifficultyColor(project.difficulty_level)}"
                >
                  {getDifficultyLabel(project.difficulty_level)}
                </span>
              {/if}
              {#if project.learning_path}
                <span class="meta-badge learning-path">📚 {project.learning_path}</span>
              {/if}
              {#if project.is_career_related}
                <span class="meta-badge career">💼 Career Essential</span>
              {/if}
            </div>
            <div class="progress-summary">
              <div class="progress-bar-container">
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    style="width: {projectProgress}%; background-color: {getProgressColor(
                      projectProgress
                    )}"
                  ></div>
                </div>
                <span class="progress-text"
                  >{projectProgress}% • {getProgressLabel(projectProgress)}</span
                >
              </div>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <button
            class="action-button secondary"
            on:click={() => (sidebarCollapsed = !sidebarCollapsed)}
          >
            <Icon name={sidebarCollapsed ? 'sidebar' : 'x'} size="16" />
            {sidebarCollapsed ? 'Show' : 'Hide'} Details
          </button>
          {#if project.url}
            <button class="action-button primary" on:click={handleOpenExternal}>
              <Icon name="external-link" size="16" />
              Open Source
            </button>
          {/if}
        </div>
      </div>
    </div>

    <div class="project-layout">
      <!-- Sidebar -->
      {#if !sidebarCollapsed}
        <div class="project-sidebar">
          <div class="sidebar-section">
            <h3>📊 Progress Overview</h3>
            <div class="progress-details">
              <div class="progress-circle">
                <svg viewBox="0 0 120 120" class="circular-progress">
                  <circle cx="60" cy="60" r="50" class="progress-bg" />
                  <circle
                    cx="60"
                    cy="60"
                    r="50"
                    class="progress-bar-circle"
                    style="stroke: {getProgressColor(projectProgress)}; stroke-dasharray: {(314.16 *
                      projectProgress) /
                      100} 314.16"
                  />
                  <text x="60" y="60" class="progress-percentage">{projectProgress}%</text>
                </svg>
              </div>
              <div class="progress-stats">
                <div class="stat-item">
                  <span class="stat-label">Current Skills</span>
                  <span class="stat-value">{currentSkills.length}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Next Skills</span>
                  <span class="stat-value">{nextSkills.length}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Milestones</span>
                  <span class="stat-value"
                    >{milestones.filter((m) => m.completed).length}/{milestones.length}</span
                  >
                </div>
              </div>
            </div>
          </div>

          <div class="sidebar-section">
            <h3>🎯 Current Skills</h3>
            <div class="skills-container">
              {#each currentSkills as skill}
                <span class="skill-tag current">{skill}</span>
              {/each}
            </div>
          </div>

          <div class="sidebar-section">
            <h3>🚀 Next Skills</h3>
            <div class="skills-container">
              {#each nextSkills.slice(0, 5) as skill}
                <span class="skill-tag next">{skill}</span>
              {/each}
            </div>
          </div>

          {#if project.tags.length > 0}
            <div class="sidebar-section">
              <h3>🏷️ Tags</h3>
              <div class="tags-container">
                {#each project.tags as tag}
                  <span class="tag">{tag}</span>
                {/each}
              </div>
            </div>
          {/if}

          {#if relatedProjects.length > 0}
            <div class="sidebar-section">
              <h3>🔗 Related Projects</h3>
              <div class="related-list">
                {#each relatedProjects as relatedProject}
                  <a href="/code-cortex/projects/{relatedProject.id}" class="related-item">
                    <div class="related-icon">
                      {getCategoryIcon(relatedProject.project_category)}
                    </div>
                    <div class="related-content">
                      <div class="related-title">{relatedProject.title}</div>
                      <div class="related-category">{relatedProject.project_category}</div>
                    </div>
                  </a>
                {/each}
              </div>
            </div>
          {/if}

          <div class="sidebar-section">
            <h3>⚡ Quick Actions</h3>
            <div class="quick-actions">
              <button class="quick-action" on:click={() => (activeTab = 'overview')}>
                <Icon name="info" size="16" />
                Overview
              </button>
              <button class="quick-action" on:click={() => (activeTab = 'progress')}>
                <Icon name="trending-up" size="16" />
                Progress
              </button>
              <button class="quick-action" on:click={() => (activeTab = 'milestones')}>
                <Icon name="flag" size="16" />
                Milestones
              </button>
              <button class="quick-action" on:click={() => (activeTab = 'ai-analysis')}>
                <Icon name="brain" size="16" />
                AI Insights
              </button>
            </div>
          </div>
        </div>
      {/if}

      <!-- Main Content -->
      <div class="project-main">
        <!-- Tab Navigation -->
        <div class="tab-navigation">
          <button
            class="tab {activeTab === 'overview' ? 'active' : ''}"
            on:click={() => (activeTab = 'overview')}
          >
            <Icon name="info" size="16" />
            Overview
          </button>
          <button
            class="tab {activeTab === 'progress' ? 'active' : ''}"
            on:click={() => (activeTab = 'progress')}
          >
            <Icon name="trending-up" size="16" />
            Progress Tracking
          </button>
          <button
            class="tab {activeTab === 'milestones' ? 'active' : ''}"
            on:click={() => (activeTab = 'milestones')}
          >
            <Icon name="flag" size="16" />
            Milestones ({milestones.filter((m) => m.completed).length}/{milestones.length})
          </button>
          <button
            class="tab {activeTab === 'ai-analysis' ? 'active' : ''}"
            on:click={() => (activeTab = 'ai-analysis')}
          >
            <Icon name="brain" size="16" />
            AI Learning Path
          </button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
          {#if activeTab === 'overview'}
            <div class="overview-content">
              <div class="content-header">
                <h2>Learning Project Overview</h2>
                <p>Comprehensive details about your learning journey and progress</p>
              </div>

              {#if project.summary}
                <div class="content-section">
                  <h3>Project Description</h3>
                  <div class="summary-content">
                    {project.summary}
                  </div>
                </div>
              {/if}

              <div class="content-section">
                <h3>Learning Details</h3>
                <div class="technical-grid">
                  <div class="tech-item">
                    <span class="tech-label">Category</span>
                    <span class="tech-value">{project.project_category || 'General'}</span>
                  </div>
                  <div class="tech-item">
                    <span class="tech-label">Difficulty</span>
                    <span class="tech-value"
                      >{getDifficultyLabel(project.difficulty_level || 2)}</span
                    >
                  </div>
                  {#if project.programming_language}
                    <div class="tech-item">
                      <span class="tech-label">Language</span>
                      <span class="tech-value">{project.programming_language}</span>
                    </div>
                  {/if}
                  {#if project.learning_path}
                    <div class="tech-item">
                      <span class="tech-label">Learning Path</span>
                      <span class="tech-value">{project.learning_path}</span>
                    </div>
                  {/if}
                  <div class="tech-item">
                    <span class="tech-label">Time Commitment</span>
                    <span class="tech-value"
                      >{getEstimatedTimeCommitment(project.difficulty_level || 2)}</span
                    >
                  </div>
                  <div class="tech-item">
                    <span class="tech-label">Career Impact</span>
                    <span class="tech-value">{project.is_career_related ? 'High' : 'Medium'}</span>
                  </div>
                </div>
              </div>

              <div class="content-section">
                <h3>Current Progress Status</h3>
                <div class="progress-overview">
                  <div class="progress-visual">
                    <div class="progress-ring">
                      <div class="progress-percentage">{projectProgress}%</div>
                      <div class="progress-label">{getProgressLabel(projectProgress)}</div>
                    </div>
                  </div>
                  <div class="progress-breakdown">
                    <div class="breakdown-item">
                      <span class="breakdown-label">Skills Acquired</span>
                      <span class="breakdown-value">{currentSkills.length} skills</span>
                    </div>
                    <div class="breakdown-item">
                      <span class="breakdown-label">Skills Remaining</span>
                      <span class="breakdown-value">{nextSkills.length} skills</span>
                    </div>
                    <div class="breakdown-item">
                      <span class="breakdown-label">Milestones Complete</span>
                      <span class="breakdown-value"
                        >{milestones.filter((m) => m.completed).length}/{milestones.length}</span
                      >
                    </div>
                  </div>
                </div>
              </div>
            </div>
          {:else if activeTab === 'progress'}
            <div class="progress-tab">
              <div class="content-header">
                <h2>Progress Tracking</h2>
                <div class="progress-controls">
                  <select bind:value={progressMode} class="view-selector">
                    <option value="visual">Visual Progress</option>
                    <option value="detailed">Detailed Breakdown</option>
                    <option value="timeline">Timeline View</option>
                  </select>
                </div>
              </div>

              {#if progressMode === 'visual'}
                <div class="visual-progress">
                  <div class="progress-chart">
                    <h3>Overall Progress</h3>
                    <div class="chart-container">
                      <div class="progress-bars">
                        <div class="progress-item">
                          <span class="progress-item-label">Skills Mastered</span>
                          <div class="progress-item-bar">
                            <div
                              class="progress-item-fill"
                              style="width: {(currentSkills.length /
                                (currentSkills.length + nextSkills.length)) *
                                100}%"
                            ></div>
                          </div>
                          <span class="progress-item-value"
                            >{currentSkills.length}/{currentSkills.length + nextSkills.length}</span
                          >
                        </div>
                        <div class="progress-item">
                          <span class="progress-item-label">Milestones Completed</span>
                          <div class="progress-item-bar">
                            <div
                              class="progress-item-fill"
                              style="width: {(milestones.filter((m) => m.completed).length /
                                milestones.length) *
                                100}%"
                            ></div>
                          </div>
                          <span class="progress-item-value"
                            >{milestones.filter((m) => m.completed)
                              .length}/{milestones.length}</span
                          >
                        </div>
                        <div class="progress-item">
                          <span class="progress-item-label">Overall Progress</span>
                          <div class="progress-item-bar">
                            <div
                              class="progress-item-fill"
                              style="width: {projectProgress}%; background-color: {getProgressColor(
                                projectProgress
                              )}"
                            ></div>
                          </div>
                          <span class="progress-item-value">{projectProgress}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              {:else if progressMode === 'detailed'}
                <div class="detailed-progress">
                  <div class="skills-breakdown">
                    <div class="skills-section">
                      <h3>✅ Mastered Skills</h3>
                      <div class="skills-grid">
                        {#each currentSkills as skill}
                          <div class="skill-card mastered">
                            <span class="skill-name">{skill}</span>
                            <Icon name="check-circle" size="16" />
                          </div>
                        {/each}
                      </div>
                    </div>
                    <div class="skills-section">
                      <h3>🎯 Next Skills to Learn</h3>
                      <div class="skills-grid">
                        {#each nextSkills as skill}
                          <div class="skill-card pending">
                            <span class="skill-name">{skill}</span>
                            <Icon name="circle" size="16" />
                          </div>
                        {/each}
                      </div>
                    </div>
                  </div>
                </div>
              {:else}
                <div class="timeline-progress">
                  <h3>Learning Timeline</h3>
                  <div class="timeline">
                    <div class="timeline-item completed">
                      <div class="timeline-marker"></div>
                      <div class="timeline-content">
                        <h4>Project Started</h4>
                        <p>Began learning journey - {formatDate(project.created_at)}</p>
                      </div>
                    </div>
                    {#each milestones as milestone}
                      <div class="timeline-item {milestone.completed ? 'completed' : 'pending'}">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                          <h4>{milestone.title}</h4>
                          <p>{milestone.description}</p>
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          {:else if activeTab === 'milestones'}
            <div class="milestones-tab">
              <div class="content-header">
                <h2>Learning Milestones</h2>
                <p>Track your progress through key learning objectives</p>
              </div>

              <div class="milestones-grid">
                {#each milestones as milestone}
                  <div class="milestone-card {milestone.completed ? 'completed' : 'pending'}">
                    <div class="milestone-header">
                      <div class="milestone-status">
                        {#if milestone.completed}
                          <Icon name="check-circle" size="24" style="color: #10b981" />
                        {:else}
                          <Icon name="circle" size="24" style="color: #6b7280" />
                        {/if}
                      </div>
                      <div class="milestone-info">
                        <h3>{milestone.title}</h3>
                        <p>{milestone.description}</p>
                      </div>
                    </div>
                    <div class="milestone-actions">
                      {#if !milestone.completed}
                        <button
                          class="milestone-btn"
                          on:click={() => {
                            milestone.completed = true;
                            milestones = [...milestones];
                            handleUpdateProgress(Math.min(100, projectProgress + 15));
                          }}
                        >
                          Mark Complete
                        </button>
                      {:else}
                        <span class="completed-badge">✓ Completed</span>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          {:else if activeTab === 'ai-analysis'}
            <div class="ai-analysis-tab">
              <div class="content-header">
                <h2>AI Learning Path & Insights</h2>
                <p>AI-powered recommendations for your learning journey</p>
                <button
                  class="refresh-analysis"
                  on:click={generateAIInsights}
                  disabled={isAIAnalyzing}
                >
                  <Icon name={isAIAnalyzing ? 'loader' : 'refresh-cw'} size="16" />
                  {isAIAnalyzing ? 'Analyzing...' : 'Refresh Analysis'}
                </button>
              </div>

              {#if isAIAnalyzing}
                <div class="ai-loading">
                  <div class="neural-pulse"></div>
                  <span>AI is analyzing your learning path...</span>
                </div>
              {:else}
                <div class="ai-content">
                  {#if aiInsights.length > 0}
                    <div class="insights-section">
                      <h3>🧠 AI Insights</h3>
                      <div class="ai-insights">
                        {#each aiInsights as insight, index}
                          <div class="insight-card">
                            <div class="insight-icon">🤖</div>
                            <div class="insight-content">{insight}</div>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}

                  {#if learningPath.length > 0}
                    <div class="learning-path-section">
                      <h3>🎯 Recommended Learning Path</h3>
                      <div class="learning-path">
                        {#each learningPath as step, index}
                          <div class="path-step">
                            <div class="step-number">{index + 1}</div>
                            <div class="step-content">{step}</div>
                          </div>
                        {/each}
                      </div>
                    </div>
                  {/if}
                </div>
              {/if}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="not-found">
    <Icon name="folder-x" size="48" />
    <h2>Project Not Found</h2>
    <p>The requested learning project could not be found.</p>
    <button class="back-button" on:click={handleBackToList}>
      <Icon name="arrow-left" size="16" />
      Back to Progress
    </button>
  </div>
{/if}

<style>
  .project-detail-page {
    min-height: 100vh;
    background: #0a0a0a;
    color: #e0e0e0;
  }

  .loading-container,
  .error-container,
  .not-found {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    text-align: center;
    gap: 1rem;
    color: #e0e0e0;
  }

  .neural-pulse {
    width: 50px;
    height: 50px;
    border: 3px solid rgba(0, 255, 136, 0.3);
    border-top: 3px solid #00ff88;
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      border-top-color: #00ff88;
      transform: scale(1);
    }
    50% {
      border-top-color: #00cc6a;
      transform: scale(1.1);
    }
  }

  .project-header {
    background: rgba(0, 0, 0, 0.8);
    border-bottom: 1px solid rgba(0, 255, 136, 0.2);
    padding: 1.5rem 2rem;
    backdrop-filter: blur(10px);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    max-width: 1400px;
    margin: 0 auto;
  }

  .header-left {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
  }

  .back-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .back-button:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .project-title-section h1 {
    margin: 0 0 0.5rem 0;
    font-size: 1.75rem;
    color: #00ff88;
    line-height: 1.2;
  }

  .project-meta {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }

  .meta-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .meta-badge.category {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
  }

  .meta-badge.language {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }

  .meta-badge.learning-path {
    background: rgba(139, 92, 246, 0.2);
    color: #8b5cf6;
  }

  .meta-badge.career {
    background: rgba(220, 20, 60, 0.2);
    color: #dc143c;
  }

  .progress-summary {
    margin-top: 0.5rem;
  }

  .progress-bar-container {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .progress-bar {
    flex: 1;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .progress-text {
    font-size: 0.875rem;
    color: #888;
    white-space: nowrap;
  }

  .header-actions {
    display: flex;
    gap: 0.75rem;
  }

  .action-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .action-button.primary {
    background: rgba(0, 255, 136, 0.1);
    border-color: rgba(0, 255, 136, 0.3);
    color: #00ff88;
  }

  .action-button.primary:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .action-button.secondary {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.2);
    color: #ccc;
  }

  .action-button.secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.3);
  }

  .project-layout {
    display: flex;
    max-width: 1400px;
    margin: 0 auto;
    min-height: calc(100vh - 180px);
  }

  .project-sidebar {
    width: 320px;
    background: rgba(0, 0, 0, 0.6);
    border-right: 1px solid rgba(0, 255, 136, 0.2);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    max-height: calc(100vh - 180px);
    overflow-y: auto;
  }

  .sidebar-section h3 {
    margin: 0 0 1rem 0;
    font-size: 0.9rem;
    color: #00ff88;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .progress-details {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .progress-circle {
    display: flex;
    justify-content: center;
  }

  .circular-progress {
    width: 120px;
    height: 120px;
    transform: rotate(-90deg);
  }

  .progress-bg {
    fill: none;
    stroke: rgba(255, 255, 255, 0.1);
    stroke-width: 8;
  }

  .progress-bar-circle {
    fill: none;
    stroke-width: 8;
    stroke-linecap: round;
    transition: stroke-dasharray 0.3s ease;
  }

  .progress-percentage {
    font-size: 1.2rem;
    font-weight: bold;
    text-anchor: middle;
    dominant-baseline: middle;
    transform: rotate(90deg);
    fill: #00ff88;
  }

  .progress-stats {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stat-label {
    font-size: 0.75rem;
    color: #888;
  }

  .stat-value {
    font-size: 0.875rem;
    color: #00ff88;
    font-weight: 600;
  }

  .skills-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .skill-tag {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .skill-tag.current {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
  }

  .skill-tag.next {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
  }

  .tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .tag {
    padding: 0.25rem 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    color: #00ff88;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .related-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .related-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.1);
    border-radius: 6px;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s ease;
  }

  .related-item:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: rgba(0, 255, 136, 0.3);
  }

  .related-icon {
    font-size: 1.2rem;
    min-width: 24px;
    text-align: center;
  }

  .related-content {
    flex: 1;
    min-width: 0;
  }

  .related-title {
    font-size: 0.875rem;
    color: #e0e0e0;
    margin-bottom: 0.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .related-category {
    font-size: 0.75rem;
    color: #888;
  }

  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .quick-action {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.2);
    color: #888;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .quick-action:hover {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
  }

  .project-main {
    flex: 1;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
  }

  .tab-navigation {
    display: flex;
    border-bottom: 1px solid rgba(0, 255, 136, 0.2);
    margin-bottom: 1.5rem;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: transparent;
    border: none;
    color: #888;
    cursor: pointer;
    transition: all 0.2s ease;
    border-bottom: 2px solid transparent;
  }

  .tab:hover {
    color: #00ff88;
  }

  .tab.active {
    color: #00ff88;
    border-bottom-color: #00ff88;
  }

  .tab-content {
    flex: 1;
  }

  .content-header {
    margin-bottom: 1.5rem;
  }

  .content-header h2 {
    margin: 0 0 0.5rem 0;
    color: #00ff88;
  }

  .content-header p {
    margin: 0;
    color: #888;
    font-size: 0.875rem;
  }

  .content-section {
    margin-bottom: 2rem;
  }

  .content-section h3 {
    margin: 0 0 1rem 0;
    color: #e0e0e0;
    font-size: 1.1rem;
  }

  .summary-content {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1rem;
    line-height: 1.6;
    color: #ccc;
  }

  .technical-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .tech-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.75rem;
    background: rgba(0, 255, 136, 0.05);
    border-radius: 6px;
  }

  .tech-label {
    font-size: 0.75rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .tech-value {
    font-size: 0.875rem;
    color: #e0e0e0;
    font-weight: 500;
  }

  .progress-overview {
    display: flex;
    gap: 2rem;
    align-items: center;
  }

  .progress-visual {
    display: flex;
    justify-content: center;
  }

  .progress-ring {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 120px;
    height: 120px;
    border: 8px solid rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    position: relative;
  }

  .progress-ring::before {
    content: '';
    position: absolute;
    top: -8px;
    left: -8px;
    width: 120px;
    height: 120px;
    border: 8px solid transparent;
    border-top-color: #00ff88;
    border-radius: 50%;
    transform: rotate(calc(3.6deg * var(--progress, 0)));
    transition: transform 0.3s ease;
  }

  .progress-percentage {
    font-size: 1.5rem;
    font-weight: bold;
    color: #00ff88;
  }

  .progress-label {
    font-size: 0.75rem;
    color: #888;
    text-align: center;
  }

  .progress-breakdown {
    flex: 1;
  }

  .breakdown-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .breakdown-item:last-child {
    border-bottom: none;
  }

  .breakdown-label {
    color: #888;
    font-size: 0.875rem;
  }

  .breakdown-value {
    color: #00ff88;
    font-weight: 600;
  }

  .progress-controls {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .view-selector {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
  }

  .visual-progress {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .progress-chart {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
  }

  .progress-chart h3 {
    margin: 0 0 1rem 0;
    color: #e0e0e0;
  }

  .progress-bars {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .progress-item {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .progress-item-label {
    min-width: 140px;
    font-size: 0.875rem;
    color: #888;
  }

  .progress-item-bar {
    flex: 1;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-item-fill {
    height: 100%;
    background: #00ff88;
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .progress-item-value {
    min-width: 60px;
    font-size: 0.875rem;
    color: #00ff88;
    font-weight: 600;
    text-align: right;
  }

  .detailed-progress {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .skills-breakdown {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .skills-section h3 {
    margin: 0 0 1rem 0;
    color: #e0e0e0;
  }

  .skills-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
  }

  .skill-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    border-radius: 6px;
    transition: all 0.2s ease;
  }

  .skill-card.mastered {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #10b981;
  }

  .skill-card.pending {
    background: rgba(107, 114, 128, 0.1);
    border: 1px solid rgba(107, 114, 128, 0.3);
    color: #6b7280;
  }

  .skill-name {
    font-size: 0.875rem;
    font-weight: 500;
  }

  .timeline-progress {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .timeline {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding-left: 2rem;
    position: relative;
  }

  .timeline::before {
    content: '';
    position: absolute;
    left: 0.75rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: rgba(0, 255, 136, 0.3);
  }

  .timeline-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    position: relative;
  }

  .timeline-marker {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 2px solid;
    position: absolute;
    left: -2.25rem;
    top: 0.25rem;
  }

  .timeline-item.completed .timeline-marker {
    background: #10b981;
    border-color: #10b981;
  }

  .timeline-item.pending .timeline-marker {
    background: #0a0a0a;
    border-color: #6b7280;
  }

  .timeline-content h4 {
    margin: 0 0 0.25rem 0;
    color: #e0e0e0;
    font-size: 1rem;
  }

  .timeline-content p {
    margin: 0;
    color: #888;
    font-size: 0.875rem;
  }

  .milestones-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .milestone-card {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    padding: 1.5rem;
    transition: all 0.2s ease;
  }

  .milestone-card.completed {
    border-color: rgba(16, 185, 129, 0.4);
    background: rgba(16, 185, 129, 0.05);
  }

  .milestone-card:hover {
    border-color: rgba(0, 255, 136, 0.4);
  }

  .milestone-header {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .milestone-status {
    display: flex;
    align-items: flex-start;
    padding-top: 0.125rem;
  }

  .milestone-info h3 {
    margin: 0 0 0.5rem 0;
    color: #e0e0e0;
    font-size: 1.1rem;
  }

  .milestone-info p {
    margin: 0;
    color: #888;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .milestone-actions {
    display: flex;
    justify-content: flex-end;
  }

  .milestone-btn {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .milestone-btn:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .completed-badge {
    color: #10b981;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .refresh-analysis {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.875rem;
  }

  .refresh-analysis:hover:not(:disabled) {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .refresh-analysis:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .ai-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 2rem;
    text-align: center;
  }

  .ai-content {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .insights-section h3,
  .learning-path-section h3 {
    margin: 0 0 1rem 0;
    color: #e0e0e0;
  }

  .ai-insights {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .insight-card {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
  }

  .insight-icon {
    font-size: 1.2rem;
    min-width: 24px;
  }

  .insight-content {
    flex: 1;
    color: #ccc;
    line-height: 1.6;
  }

  .learning-path {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .path-step {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 8px;
  }

  .step-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: #8b5cf6;
    color: white;
    border-radius: 50%;
    font-weight: 600;
    font-size: 0.875rem;
  }

  .step-content {
    flex: 1;
    color: #ccc;
    font-size: 0.875rem;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .header-content {
      flex-direction: column;
      gap: 1rem;
    }

    .project-layout {
      flex-direction: column;
    }

    .project-sidebar {
      width: 100%;
      max-height: none;
    }

    .technical-grid {
      grid-template-columns: 1fr;
    }

    .milestones-grid {
      grid-template-columns: 1fr;
    }

    .skills-grid {
      grid-template-columns: 1fr;
    }

    .progress-overview {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }
  }
</style>
