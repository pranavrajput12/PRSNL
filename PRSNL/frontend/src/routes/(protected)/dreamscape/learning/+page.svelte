<script lang="ts">
  import { onMount } from 'svelte';
  import { getApiClient } from '$lib/api/client';
  import { currentUser } from '$lib/stores/unified-auth';
  import Icon from '$lib/components/Icon.svelte';
  
  // Learning state
  let loading = true;
  let error: string | null = null;
  let personaData: any = null;
  let learningPath: any = null;
  let currentModule: any = null;
  let progress = 0;
  
  // Learning configuration
  let learningGoals: string[] = [];
  let preferredFormats: string[] = [];
  let difficultyLevel = 'beginner';
  let timeCommitment = '30-minutes';
  
  // Available options
  const goalOptions = [
    'skill_development',
    'career_advancement', 
    'personal_projects',
    'certification_prep',
    'knowledge_expansion'
  ];
  
  const formatOptions = [
    'hands-on',
    'visual',
    'reading',
    'video',
    'interactive'
  ];
  
  // Sample learning modules (would come from API)
  let availableModules = [
    {
      id: 'js-fundamentals',
      title: 'JavaScript Fundamentals',
      description: 'Master the core concepts of JavaScript programming',
      difficulty: 'beginner',
      estimatedTime: '4 hours',
      format: 'hands-on',
      prerequisites: [],
      skills: ['variables', 'functions', 'objects', 'arrays'],
      progress: 0,
      status: 'available'
    },
    {
      id: 'react-basics',
      title: 'React Component Basics',
      description: 'Learn to build modern web applications with React',
      difficulty: 'intermediate',
      estimatedTime: '6 hours',
      format: 'visual',
      prerequisites: ['js-fundamentals'],
      skills: ['components', 'props', 'state', 'hooks'],
      progress: 0,
      status: 'locked'
    },
    {
      id: 'data-structures',
      title: 'Data Structures & Algorithms',
      description: 'Essential computer science concepts for problem solving',
      difficulty: 'intermediate',
      estimatedTime: '8 hours',
      format: 'interactive',
      prerequisites: ['js-fundamentals'],
      skills: ['arrays', 'trees', 'graphs', 'sorting'],
      progress: 0,
      status: 'available'
    }
  ];

  onMount(async () => {
    await loadPersonaData();
    await generateLearningPath();
  });

  async function loadPersonaData() {
    if (!$currentUser?.id) return;
    
    loading = true;
    error = null;
    
    try {
      const api = getApiClient();
      const response = await api.get(`/persona/user/${$currentUser.id}`);
      personaData = response.data;
      extractLearningPreferences();
    } catch (e: any) {
      if (e.status !== 404) {
        error = e.message || 'Failed to load persona data';
        console.error('Error loading persona:', e);
      }
      // 404 is expected if no persona exists yet
    } finally {
      loading = false;
    }
  }

  function extractLearningPreferences() {
    if (!personaData?.learning_style) return;
    
    const learningStyle = personaData.learning_style;
    preferredFormats = learningStyle.preferred_formats || ['hands-on'];
    
    // Extract learning goals from persona insights
    if (personaData.life_phase === 'early_career') {
      learningGoals = ['skill_development', 'career_advancement'];
    } else if (personaData.life_phase === 'mid_career') {
      learningGoals = ['personal_projects', 'knowledge_expansion'];
    }
    
    // Set difficulty based on technical profile
    const techProfile = personaData.technical_profile;
    if (techProfile?.skill_levels) {
      const avgSkillLevel = Object.values(techProfile.skill_levels).includes('advanced') ? 'advanced' : 
                           Object.values(techProfile.skill_levels).includes('intermediate') ? 'intermediate' : 'beginner';
      difficultyLevel = avgSkillLevel;
    }
  }

  async function generateLearningPath() {
    // Simulate AI-generated learning path based on persona
    learningPath = {
      id: 'personalized-path-1',
      title: 'Your Personalized Learning Journey',
      description: 'AI-curated path based on your technical profile and learning style',
      estimatedCompletion: '4-6 weeks',
      modules: availableModules.slice(0, 3),
      adaptiveFeatures: [
        'Difficulty adjustment based on progress',
        'Content format matching your preferences',
        'Spaced repetition for retention',
        'Project-based application'
      ]
    };
    
    // Update module availability based on preferences
    updateModuleRecommendations();
  }

  function updateModuleRecommendations() {
    availableModules = availableModules.map(module => {
      // Match difficulty preference
      const difficultyMatch = module.difficulty === difficultyLevel;
      
      // Match format preference
      const formatMatch = preferredFormats.includes(module.format);
      
      // Calculate recommendation score
      let score = 0;
      if (difficultyMatch) score += 3;
      if (formatMatch) score += 2;
      
      return {
        ...module,
        recommendationScore: score,
        recommended: score >= 3
      };
    });
    
    // Sort by recommendation score
    availableModules.sort((a, b) => (b.recommendationScore || 0) - (a.recommendationScore || 0));
  }

  function toggleLearningGoal(goal: string) {
    if (learningGoals.includes(goal)) {
      learningGoals = learningGoals.filter(g => g !== goal);
    } else {
      learningGoals = [...learningGoals, goal];
    }
    updateModuleRecommendations();
  }

  function toggleFormat(format: string) {
    if (preferredFormats.includes(format)) {
      preferredFormats = preferredFormats.filter(f => f !== format);
    } else {
      preferredFormats = [...preferredFormats, format];
    }
    updateModuleRecommendations();
  }

  function startModule(module: any) {
    if (module.status === 'locked') return;
    
    currentModule = module;
    // In a real implementation, this would navigate to the learning module
    console.log('Starting module:', module.title);
  }

  function getDifficultyColor(difficulty: string) {
    switch (difficulty) {
      case 'beginner': return '#10B981';
      case 'intermediate': return '#F59E0B';
      case 'advanced': return '#EF4444';
      default: return '#6B7280';
    }
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'completed': return 'check-circle';
      case 'in-progress': return 'play-circle';
      case 'locked': return 'lock';
      default: return 'circle';
    }
  }

  function formatGoalName(goal: string) {
    return goal.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  function formatFormatName(format: string) {
    return format.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
</script>

<div class="learning-assistant-page">
  <header class="learning-header">
    <div class="header-content">
      <div class="breadcrumb">
        <a href="/dreamscape">Dreamscape</a>
        <Icon name="chevron-right" size="small" />
        <span>AI Learning Assistant</span>
      </div>
      
      <h1>AI Learning Assistant</h1>
      <p class="subtitle">Personalized curriculum powered by your behavioral patterns</p>
    </div>
  </header>

  <main class="learning-content">
    {#if loading}
      <div class="loading-state">
        <div class="neural-loading">
          <div class="brain-pulse"></div>
          <p>Analyzing your learning preferences...</p>
        </div>
      </div>
    {:else if error}
      <div class="error-state">
        <Icon name="alert-circle" size="large" />
        <p>{error}</p>
        <button on:click={loadPersonaData}>Retry</button>
      </div>
    {:else}
      <div class="learning-dashboard">
        <!-- Learning Preferences Panel -->
        <div class="preferences-panel">
          <div class="panel-header">
            <h2>
              <Icon name="settings" />
              Learning Preferences
            </h2>
            {#if personaData}
              <div class="persona-indicator">
                <Icon name="zap" size="small" />
                AI-Optimized
              </div>
            {/if}
          </div>
          
          <div class="panel-content">
            <div class="preference-section">
              <h3>Learning Goals</h3>
              <div class="preference-grid">
                {#each goalOptions as goal}
                  <button 
                    class="preference-button"
                    class:active={learningGoals.includes(goal)}
                    on:click={() => toggleLearningGoal(goal)}
                  >
                    <Icon name={learningGoals.includes(goal) ? 'check-circle' : 'circle'} size="small" />
                    {formatGoalName(goal)}
                  </button>
                {/each}
              </div>
            </div>
            
            <div class="preference-section">
              <h3>Preferred Formats</h3>
              <div class="preference-grid">
                {#each formatOptions as format}
                  <button 
                    class="preference-button"
                    class:active={preferredFormats.includes(format)}
                    on:click={() => toggleFormat(format)}
                  >
                    <Icon name={preferredFormats.includes(format) ? 'check-circle' : 'circle'} size="small" />
                    {formatFormatName(format)}
                  </button>
                {/each}
              </div>
            </div>
            
            <div class="preference-section">
              <h3>Difficulty Level</h3>
              <div class="difficulty-selector">
                {#each ['beginner', 'intermediate', 'advanced'] as level}
                  <button 
                    class="difficulty-button"
                    class:active={difficultyLevel === level}
                    style="border-color: {getDifficultyColor(level)}"
                    on:click={() => { difficultyLevel = level; updateModuleRecommendations(); }}
                  >
                    {level.charAt(0).toUpperCase() + level.slice(1)}
                  </button>
                {/each}
              </div>
            </div>
            
            <div class="preference-section">
              <h3>Time Commitment</h3>
              <select bind:value={timeCommitment} class="time-selector">
                <option value="15-minutes">15 minutes/day</option>
                <option value="30-minutes">30 minutes/day</option>
                <option value="1-hour">1 hour/day</option>
                <option value="2-hours">2+ hours/day</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Learning Path Panel -->
        {#if learningPath}
          <div class="learning-path-panel">
            <div class="panel-header">
              <h2>
                <Icon name="map" />
                Your Learning Path
              </h2>
              <div class="path-metadata">
                {learningPath.estimatedCompletion}
              </div>
            </div>
            
            <div class="panel-content">
              <div class="path-description">
                <h3>{learningPath.title}</h3>
                <p>{learningPath.description}</p>
              </div>
              
              <div class="adaptive-features">
                <h4>Adaptive Features</h4>
                <div class="features-list">
                  {#each learningPath.adaptiveFeatures as feature}
                    <div class="feature-item">
                      <Icon name="check-circle" size="small" />
                      <span>{feature}</span>
                    </div>
                  {/each}
                </div>
              </div>
              
              <!-- Progress Overview -->
              <div class="progress-overview">
                <h4>Overall Progress</h4>
                <div class="progress-bar-container">
                  <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress}%"></div>
                  </div>
                  <span class="progress-text">{progress}% Complete</span>
                </div>
              </div>
            </div>
          </div>
        {/if}

        <!-- Learning Modules Grid -->
        <div class="modules-section">
          <div class="section-header">
            <h2>
              <Icon name="book-open" />
              Learning Modules
            </h2>
            <div class="module-filters">
              <button class="filter-button active">
                <Icon name="star" size="small" />
                Recommended
              </button>
              <button class="filter-button">
                <Icon name="layers" size="small" />
                All Modules
              </button>
            </div>
          </div>
          
          <div class="modules-grid">
            {#each availableModules as module}
              <div class="module-card" class:recommended={module.recommended}>
                <div class="module-header">
                  <div class="module-status">
                    <Icon name={getStatusIcon(module.status)} size="small" />
                  </div>
                  <div class="module-difficulty" style="color: {getDifficultyColor(module.difficulty)}">
                    {module.difficulty}
                  </div>
                  {#if module.recommended}
                    <div class="recommended-badge">
                      <Icon name="star" size="small" />
                      Recommended
                    </div>
                  {/if}
                </div>
                
                <div class="module-content">
                  <h3>{module.title}</h3>
                  <p class="module-description">{module.description}</p>
                  
                  <div class="module-metadata">
                    <div class="metadata-item">
                      <Icon name="clock" size="small" />
                      <span>{module.estimatedTime}</span>
                    </div>
                    <div class="metadata-item">
                      <Icon name="tag" size="small" />
                      <span>{formatFormatName(module.format)}</span>
                    </div>
                  </div>
                  
                  <div class="module-skills">
                    <h4>Skills You'll Learn</h4>
                    <div class="skills-tags">
                      {#each module.skills as skill}
                        <span class="skill-tag">{skill}</span>
                      {/each}
                    </div>
                  </div>
                  
                  {#if module.prerequisites.length > 0}
                    <div class="prerequisites">
                      <h4>Prerequisites</h4>
                      <div class="prereq-list">
                        {#each module.prerequisites as prerequisite}
                          <span class="prereq-tag">{prerequisite}</span>
                        {/each}
                      </div>
                    </div>
                  {/if}
                  
                  <div class="module-progress">
                    {#if module.progress > 0}
                      <div class="progress-bar-small">
                        <div class="progress-fill-small" style="width: {module.progress}%"></div>
                      </div>
                      <span class="progress-text-small">{module.progress}% Complete</span>
                    {/if}
                  </div>
                </div>
                
                <div class="module-actions">
                  <button 
                    class="module-button"
                    class:primary={module.status !== 'locked'}
                    class:disabled={module.status === 'locked'}
                    on:click={() => startModule(module)}
                    disabled={module.status === 'locked'}
                  >
                    {#if module.status === 'locked'}
                      <Icon name="lock" size="small" />
                      Locked
                    {:else if module.status === 'completed'}
                      <Icon name="refresh-cw" size="small" />
                      Review
                    {:else if module.status === 'in-progress'}
                      <Icon name="play" size="small" />
                      Continue
                    {:else}
                      <Icon name="play" size="small" />
                      Start Module
                    {/if}
                  </button>
                </div>
              </div>
            {/each}
          </div>
        </div>

        <!-- Learning Analytics Panel -->
        <div class="analytics-panel">
          <div class="panel-header">
            <h2>
              <Icon name="trending-up" />
              Learning Analytics
            </h2>
          </div>
          
          <div class="panel-content">
            <div class="analytics-grid">
              <div class="analytic-card">
                <div class="analytic-icon">
                  <Icon name="zap" />
                </div>
                <div class="analytic-content">
                  <h3>Learning Velocity</h3>
                  <div class="analytic-value">
                    {#if personaData?.behavioral_metrics?.learning_velocity}
                      {Math.round(personaData.behavioral_metrics.learning_velocity * 100)}%
                    {:else}
                      --
                    {/if}
                  </div>
                  <div class="analytic-trend">
                    <Icon name="trending-up" size="small" />
                    Accelerating
                  </div>
                </div>
              </div>
              
              <div class="analytic-card">
                <div class="analytic-icon">
                  <Icon name="target" />
                </div>
                <div class="analytic-content">
                  <h3>Focus Score</h3>
                  <div class="analytic-value">
                    {#if personaData?.learning_style?.attention_span}
                      {personaData.learning_style.attention_span === 'long' ? '85' : 
                       personaData.learning_style.attention_span === 'medium' ? '65' : '45'}%
                    {:else}
                      --
                    {/if}
                  </div>
                  <div class="analytic-trend">
                    <Icon name="arrow-up" size="small" />
                    Improving
                  </div>
                </div>
              </div>
              
              <div class="analytic-card">
                <div class="analytic-icon">
                  <Icon name="layers" />
                </div>
                <div class="analytic-content">
                  <h3>Skill Diversity</h3>
                  <div class="analytic-value">
                    {#if personaData?.behavioral_metrics?.diversity_score}
                      {Math.round(personaData.behavioral_metrics.diversity_score * 100)}%
                    {:else}
                      --
                    {/if}
                  </div>
                  <div class="analytic-trend">
                    <Icon name="shuffle" size="small" />
                    Multi-domain
                  </div>
                </div>
              </div>
              
              <div class="analytic-card">
                <div class="analytic-icon">
                  <Icon name="calendar" />
                </div>
                <div class="analytic-content">
                  <h3>Consistency</h3>
                  <div class="analytic-value">7 days</div>
                  <div class="analytic-trend">
                    <Icon name="calendar-check" size="small" />
                    Current streak
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  .learning-assistant-page {
    min-height: 100vh;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  /* Header */
  .learning-header {
    background: rgba(0, 0, 0, 0.4);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    padding: 2rem;
  }

  .header-content {
    max-width: 1400px;
    margin: 0 auto;
  }

  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .breadcrumb a {
    color: var(--neural-green);
    text-decoration: none;
  }

  .breadcrumb a:hover {
    text-decoration: underline;
  }

  .learning-header h1 {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0 0 0.5rem;
    background: linear-gradient(135deg, var(--neural-green), var(--accent-red));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* Main Content */
  .learning-content {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  .learning-dashboard {
    display: grid;
    grid-template-columns: 350px 1fr;
    gap: 2rem;
  }

  /* Loading States */
  .loading-state, .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    text-align: center;
  }

  .neural-loading {
    position: relative;
  }

  .brain-pulse {
    width: 80px;
    height: 80px;
    background: radial-gradient(circle, var(--neural-green), transparent);
    border-radius: 50%;
    animation: pulse-glow 2s ease-in-out infinite;
    margin-bottom: 2rem;
  }

  @keyframes pulse-glow {
    0%, 100% {
      transform: scale(1);
      opacity: 0.8;
    }
    50% {
      transform: scale(1.2);
      opacity: 1;
    }
  }

  /* Panel Styles */
  .preferences-panel,
  .learning-path-panel,
  .analytics-panel {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(20px);
    overflow: hidden;
    margin-bottom: 2rem;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.02);
  }

  .panel-header h2 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 1.2rem;
    color: var(--text-primary);
  }

  .persona-indicator {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem;
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.2);
    color: var(--neural-green);
    border-radius: var(--radius);
    font-size: 0.8rem;
    font-weight: 600;
  }

  .path-metadata {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .panel-content {
    padding: 1.5rem;
  }

  /* Preferences */
  .preference-section {
    margin-bottom: 2rem;
  }

  .preference-section h3 {
    margin: 0 0 1rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .preference-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }

  .preference-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-secondary);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
    text-align: left;
    width: 100%;
  }

  .preference-button:hover,
  .preference-button.active {
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.1);
    border-color: var(--neural-green);
    color: var(--neural-green);
  }

  .difficulty-selector {
    display: flex;
    gap: 0.5rem;
  }

  .difficulty-button {
    flex: 1;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.03);
    border: 2px solid rgba(255, 255, 255, 0.1);
    color: var(--text-secondary);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
    text-transform: capitalize;
  }

  .difficulty-button:hover,
  .difficulty-button.active {
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-primary);
  }

  .time-selector {
    width: 100%;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    padding: 0.75rem;
    border-radius: var(--radius);
    font-size: 1rem;
  }

  /* Learning Path */
  .path-description h3 {
    margin: 0 0 0.5rem;
    color: var(--neural-green);
  }

  .path-description p {
    margin: 0 0 1.5rem;
    color: var(--text-secondary);
    line-height: 1.5;
  }

  .adaptive-features h4,
  .progress-overview h4 {
    margin: 0 0 1rem;
    color: var(--text-secondary);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .features-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 2rem;
  }

  .feature-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-primary);
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
    background: linear-gradient(90deg, var(--neural-green), #00C851);
    transition: width 0.5s ease;
  }

  .progress-text {
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-family: var(--font-mono);
  }

  /* Modules Section */
  .modules-section {
    grid-column: 1 / -1;
    margin-top: 2rem;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .section-header h2 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    color: var(--text-primary);
  }

  .module-filters {
    display: flex;
    gap: 0.5rem;
  }

  .filter-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-secondary);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
  }

  .filter-button:hover,
  .filter-button.active {
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.1);
    border-color: var(--neural-green);
    color: var(--neural-green);
  }

  .modules-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .module-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    transition: all var(--transition-base);
    position: relative;
    overflow: hidden;
  }

  .module-card:hover {
    background: rgba(255, 255, 255, 0.05);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }

  .module-card.recommended {
    border-color: var(--neural-green);
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.05);
  }

  .module-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .module-status {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .module-difficulty {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: capitalize;
    padding: 0.25rem 0.5rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
  }

  .recommended-badge {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.2);
    color: var(--neural-green);
    border-radius: var(--radius);
    font-size: 0.7rem;
    font-weight: 600;
  }

  .module-content h3 {
    margin: 0 0 0.5rem;
    color: var(--text-primary);
    font-size: 1.2rem;
  }

  .module-description {
    margin: 0 0 1rem;
    color: var(--text-secondary);
    line-height: 1.4;
  }

  .module-metadata {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .metadata-item {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    color: var(--text-secondary);
    font-size: 0.8rem;
  }

  .module-skills h4,
  .prerequisites h4 {
    margin: 0 0 0.5rem;
    color: var(--text-secondary);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .skills-tags,
  .prereq-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    margin-bottom: 1rem;
  }

  .skill-tag {
    padding: 0.25rem 0.5rem;
    background: rgba(var(--neural-green-rgb, 0, 255, 100), 0.2);
    color: var(--neural-green);
    border-radius: var(--radius);
    font-size: 0.7rem;
    border: 1px solid rgba(var(--neural-green-rgb, 0, 255, 100), 0.3);
  }

  .prereq-tag {
    padding: 0.25rem 0.5rem;
    background: rgba(245, 158, 11, 0.2);
    color: #FBBF24;
    border-radius: var(--radius);
    font-size: 0.7rem;
    border: 1px solid rgba(245, 158, 11, 0.3);
  }

  .module-progress {
    margin: 1rem 0;
  }

  .progress-bar-small {
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 0.25rem;
  }

  .progress-fill-small {
    height: 100%;
    background: linear-gradient(90deg, var(--neural-green), #00C851);
    transition: width 0.3s ease;
  }

  .progress-text-small {
    color: var(--text-secondary);
    font-size: 0.7rem;
    font-family: var(--font-mono);
  }

  .module-actions {
    margin-top: 1rem;
  }

  .module-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.75rem 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
    justify-content: center;
  }

  .module-button.primary {
    background: linear-gradient(135deg, var(--neural-green), #00e652);
    color: #000;
    border-color: var(--neural-green);
  }

  .module-button.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .module-button:hover:not(.disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  .module-button.primary:hover:not(.disabled) {
    box-shadow: 0 4px 12px rgba(0, 255, 100, 0.3);
  }

  /* Analytics Panel */
  .analytics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }

  .analytic-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius);
    transition: all var(--transition-base);
  }

  .analytic-card:hover {
    background: rgba(255, 255, 255, 0.05);
    transform: translateY(-2px);
  }

  .analytic-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--neural-green), #00C851);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #000;
    flex-shrink: 0;
  }

  .analytic-content h3 {
    margin: 0 0 0.25rem;
    color: var(--text-secondary);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .analytic-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  .analytic-trend {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    color: var(--neural-green);
    font-size: 0.7rem;
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .learning-dashboard {
      grid-template-columns: 1fr;
    }

    .modules-grid {
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    }
  }

  @media (max-width: 768px) {
    .learning-header,
    .learning-content {
      padding: 1rem;
    }

    .modules-grid {
      grid-template-columns: 1fr;
    }

    .analytics-grid {
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    }

    .module-metadata {
      flex-direction: column;
      gap: 0.5rem;
    }
  }
</style>