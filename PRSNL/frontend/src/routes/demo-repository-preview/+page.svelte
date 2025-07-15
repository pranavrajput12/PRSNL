<script lang="ts">
  import RepositoryPreview from '$lib/components/RepositoryPreview.svelte';
  import Icon from '$lib/components/Icon.svelte';

  let theme: 'dark' | 'light' = 'dark';
  let height = '700px';
  let showFeatures = false;

  const features = [
    {
      icon: 'layout',
      title: 'Clean & Modern Design',
      description: 'Minimalist interface with focus on content and readability',
    },
    {
      icon: 'folder-tree',
      title: 'File Tree Navigation',
      description: 'Hierarchical file structure with collapsible directories',
    },
    {
      icon: 'search',
      title: 'Fast File Search',
      description: 'Quick file search with keyboard shortcut (⌘P)',
    },
    {
      icon: 'code',
      title: 'Syntax Highlighting',
      description: 'Powered by Monaco Editor with language detection',
    },
    {
      icon: 'eye',
      title: 'Markdown Preview',
      description: 'Live preview for markdown files with split view',
    },
    {
      icon: 'sun',
      title: 'Theme Support',
      description: 'Beautiful dark and light themes',
    },
  ];
</script>

<div class="demo-page {theme}">
  <header class="page-header">
    <div class="header-content">
      <h1 class="page-title">
        <Icon name="github" size={32} />
        Repository Preview Component
      </h1>
      <p class="page-subtitle">
        A beautiful, functional, and clutter-free repository viewer with GitHub-like UI
      </p>
    </div>

    <div class="header-actions">
      <button
        class="theme-toggle"
        on:click={() => (theme = theme === 'dark' ? 'light' : 'dark')}
        title="Toggle theme"
      >
        <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={20} />
      </button>

      <button class="feature-toggle" on:click={() => (showFeatures = !showFeatures)}>
        <Icon name="sparkles" size={16} />
        {showFeatures ? 'Hide' : 'Show'} Features
      </button>
    </div>
  </header>

  {#if showFeatures}
    <section class="features-section">
      <div class="features-grid">
        {#each features as feature}
          <div class="feature-card">
            <div class="feature-icon">
              <Icon name={feature.icon} size={24} />
            </div>
            <h3 class="feature-title">{feature.title}</h3>
            <p class="feature-description">{feature.description}</p>
          </div>
        {/each}
      </div>
    </section>
  {/if}

  <main class="demo-container">
    <div class="demo-wrapper">
      <div class="demo-header">
        <div class="demo-info">
          <Icon name="package" size={20} />
          <span class="repo-name">awesome-project</span>
          <span class="repo-badge">Public</span>
        </div>

        <div class="demo-controls">
          <select class="height-select" bind:value={height}>
            <option value="500px">Small (500px)</option>
            <option value="700px">Medium (700px)</option>
            <option value="900px">Large (900px)</option>
          </select>
        </div>
      </div>

      <div class="preview-container">
        <RepositoryPreview repositoryUrl="https://github.com/owner/repo" {height} {theme} />
      </div>

      <div class="demo-footer">
        <div class="usage-hint">
          <Icon name="info" size={16} />
          <span
            >Try clicking on files, searching with ⌘P, or switching between code and preview modes</span
          >
        </div>
      </div>
    </div>
  </main>

  <footer class="page-footer">
    <p>Built with Svelte • Monaco Editor • Markdown Support</p>
  </footer>
</div>

<style>
  .demo-page {
    min-height: 100vh;
    background: var(--bg-page);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    transition:
      background-color 0.3s,
      color 0.3s;
  }

  /* Theme Variables */
  .demo-page.dark {
    --bg-page: #010409;
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --border-primary: #30363d;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --accent-primary: #58a6ff;
    --accent-secondary: #3fb950;
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.12);
    --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.12);
  }

  .demo-page.light {
    --bg-page: #f6f8fa;
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --bg-tertiary: #f3f4f6;
    --border-primary: #d0d7de;
    --text-primary: #24292f;
    --text-secondary: #57606a;
    --accent-primary: #0969da;
    --accent-secondary: #2da44e;
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
    --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.08);
  }

  /* Header */
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 2rem 3rem;
    background: var(--bg-primary);
    border-bottom: 1px solid var(--border-primary);
  }

  .header-content {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .page-title {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .page-subtitle {
    margin: 0;
    font-size: 1.125rem;
    color: var(--text-secondary);
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .theme-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border: 1px solid var(--border-primary);
    background: var(--bg-secondary);
    color: var(--text-primary);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .theme-toggle:hover {
    background: var(--bg-tertiary);
    transform: translateY(-1px);
  }

  .feature-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    border: 1px solid var(--border-primary);
    background: var(--bg-secondary);
    color: var(--text-primary);
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .feature-toggle:hover {
    background: var(--bg-tertiary);
    transform: translateY(-1px);
  }

  /* Features Section */
  .features-section {
    padding: 3rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-primary);
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .feature-card {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 1.5rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-primary);
    border-radius: 12px;
    transition: all 0.2s;
  }

  .feature-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }

  .feature-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    background: var(--bg-tertiary);
    color: var(--accent-primary);
    border-radius: 10px;
  }

  .feature-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .feature-description {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.5;
  }

  /* Demo Container */
  .demo-container {
    padding: 3rem;
    min-height: calc(100vh - 200px);
  }

  .demo-wrapper {
    max-width: 1400px;
    margin: 0 auto;
  }

  .demo-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
  }

  .demo-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: var(--text-primary);
  }

  .repo-name {
    font-size: 1.125rem;
    font-weight: 600;
  }

  .repo-badge {
    padding: 0.25rem 0.75rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 20px;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .height-select {
    padding: 0.5rem 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 0.875rem;
    cursor: pointer;
  }

  .preview-container {
    box-shadow: var(--shadow-md);
    border-radius: 12px;
    overflow: hidden;
  }

  .demo-footer {
    margin-top: 1.5rem;
  }

  .usage-hint {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 8px;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  /* Page Footer */
  .page-footer {
    padding: 2rem;
    text-align: center;
    background: var(--bg-primary);
    border-top: 1px solid var(--border-primary);
  }

  .page-footer p {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      gap: 1.5rem;
      padding: 1.5rem;
    }

    .header-content {
      text-align: center;
    }

    .page-title {
      font-size: 1.5rem;
    }

    .page-subtitle {
      font-size: 1rem;
    }

    .features-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .demo-container {
      padding: 1.5rem;
    }

    .demo-header {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }
  }
</style>
