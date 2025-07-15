<script lang="ts">
  import GitHubRepoCardV2 from '$lib/components/GitHubRepoCardV2.svelte';
  import Icon from '$lib/components/Icon.svelte';

  let theme: 'dark' | 'light' = 'dark';
  let variant: 'default' | 'compact' | 'featured' = 'default';

  // Sample repository data
  const sampleRepos = [
    {
      id: '1',
      url: 'https://github.com/vercel/next.js',
      owner: {
        login: 'vercel',
        avatar_url: 'https://avatars.githubusercontent.com/u/14985020?v=4',
      },
      repo: {
        name: 'next.js',
        description: 'The React Framework – created and maintained by Vercel.',
        private: false,
        language: 'JavaScript',
      },
      stats: {
        stars: 115234,
        forks: 24892,
        watchers: 115234,
        open_issues: 1432,
      },
      languages: {
        JavaScript: 5234567,
        TypeScript: 3456789,
        CSS: 234567,
        MDX: 123456,
      },
      topics: ['react', 'nextjs', 'javascript', 'vercel', 'framework', 'frontend', 'ssr', 'ssg'],
      last_updated: '2024-01-15T10:30:00Z',
      recent_commits: [
        {
          message: 'fix: improve build performance',
          date: '2024-01-15T10:30:00Z',
          author: 'timneutkens',
        },
        {
          message: 'feat: add app router improvements',
          date: '2024-01-14T15:45:00Z',
          author: 'shuding',
        },
      ],
    },
    {
      id: '2',
      url: 'https://github.com/microsoft/vscode',
      owner: {
        login: 'microsoft',
        avatar_url: 'https://avatars.githubusercontent.com/u/6154722?v=4',
      },
      repo: {
        name: 'vscode',
        description: 'Visual Studio Code - Open Source ("Code - OSS")',
        private: false,
        language: 'TypeScript',
      },
      stats: {
        stars: 152453,
        forks: 26784,
        watchers: 152453,
        open_issues: 5234,
      },
      languages: {
        TypeScript: 8234567,
        JavaScript: 1234567,
        CSS: 456789,
        HTML: 234567,
      },
      topics: ['editor', 'typescript', 'electron', 'microsoft', 'vscode'],
      last_updated: '2024-01-14T08:15:00Z',
    },
    {
      id: '3',
      url: 'https://github.com/tailwindlabs/tailwindcss',
      owner: {
        login: 'tailwindlabs',
        avatar_url: 'https://avatars.githubusercontent.com/u/67109815?v=4',
      },
      repo: {
        name: 'tailwindcss',
        description: 'A utility-first CSS framework for rapid UI development.',
        private: false,
        language: 'JavaScript',
      },
      stats: {
        stars: 73456,
        forks: 3892,
        watchers: 73456,
        open_issues: 123,
      },
      languages: {
        JavaScript: 4567890,
        CSS: 2345678,
        TypeScript: 123456,
      },
      topics: ['css', 'css-framework', 'tailwind', 'utility-classes'],
      last_updated: '2024-01-13T14:20:00Z',
    },
    {
      id: '4',
      url: 'https://github.com/facebook/react',
      owner: {
        login: 'facebook',
        avatar_url: 'https://avatars.githubusercontent.com/u/69631?v=4',
      },
      repo: {
        name: 'react',
        description: 'The library for web and native user interfaces.',
        private: false,
        language: 'JavaScript',
      },
      stats: {
        stars: 215678,
        forks: 45234,
        watchers: 215678,
        open_issues: 1123,
      },
      languages: {
        JavaScript: 7890123,
        TypeScript: 456789,
        'C++': 234567,
      },
      topics: ['react', 'javascript', 'library', 'frontend', 'ui'],
      last_updated: '2024-01-15T12:00:00Z',
    },
    {
      id: '5',
      url: 'https://github.com/rust-lang/rust',
      owner: {
        login: 'rust-lang',
        avatar_url: 'https://avatars.githubusercontent.com/u/5430905?v=4',
      },
      repo: {
        name: 'rust',
        description: 'Empowering everyone to build reliable and efficient software.',
        private: false,
        language: 'Rust',
      },
      stats: {
        stars: 87654,
        forks: 11234,
        watchers: 87654,
        open_issues: 8765,
      },
      languages: {
        Rust: 12345678,
        Python: 234567,
        Shell: 123456,
      },
      topics: ['rust', 'programming-language', 'compiler', 'systems-programming'],
      last_updated: '2024-01-15T09:30:00Z',
    },
    {
      id: '6',
      url: 'https://github.com/privaterepo/internal-tools',
      owner: {
        login: 'mycompany',
        avatar_url: 'https://avatars.githubusercontent.com/u/1234567?v=4',
      },
      repo: {
        name: 'internal-tools',
        description: 'Internal development tools and utilities for our engineering team.',
        private: true,
        language: 'Python',
      },
      stats: {
        stars: 42,
        forks: 8,
        watchers: 42,
        open_issues: 3,
      },
      languages: {
        Python: 345678,
        JavaScript: 123456,
        Shell: 23456,
      },
      topics: ['internal', 'tools', 'automation', 'devops'],
      last_updated: '2024-01-12T16:45:00Z',
    },
  ];

  $: displayRepos = variant === 'compact' ? sampleRepos : sampleRepos.slice(0, 4);
</script>

<div class="demo-page {theme}">
  <header class="page-header">
    <div class="header-content">
      <h1 class="page-title">
        <Icon name="github" size={32} />
        GitHub Repository Cards
      </h1>
      <p class="page-subtitle">
        Beautiful, clean, and informative repository cards with multiple variants
      </p>
    </div>

    <div class="header-controls">
      <div class="variant-selector">
        <button
          class="variant-btn"
          class:active={variant === 'default'}
          on:click={() => (variant = 'default')}
        >
          Default
        </button>
        <button
          class="variant-btn"
          class:active={variant === 'compact'}
          on:click={() => (variant = 'compact')}
        >
          Compact
        </button>
        <button
          class="variant-btn"
          class:active={variant === 'featured'}
          on:click={() => (variant = 'featured')}
        >
          Featured
        </button>
      </div>

      <button
        class="theme-toggle"
        on:click={() => (theme = theme === 'dark' ? 'light' : 'dark')}
        title="Toggle theme"
      >
        <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={20} />
      </button>
    </div>
  </header>

  <main class="main-content">
    <section class="cards-section">
      <div class="cards-grid" class:compact={variant === 'compact'}>
        {#each displayRepos as repo}
          <GitHubRepoCardV2 repository={repo} {variant} {theme} />
        {/each}
      </div>
    </section>

    <section class="features-section">
      <h2 class="section-title">Features</h2>
      <div class="features-grid">
        <div class="feature">
          <Icon name="palette" size={24} />
          <h3>Beautiful Design</h3>
          <p>Clean, modern interface with careful attention to spacing and typography</p>
        </div>
        <div class="feature">
          <Icon name="layout" size={24} />
          <h3>Multiple Variants</h3>
          <p>Default, compact, and featured layouts for different use cases</p>
        </div>
        <div class="feature">
          <Icon name="moon" size={24} />
          <h3>Theme Support</h3>
          <p>Seamless dark and light theme variants with GitHub-inspired colors</p>
        </div>
        <div class="feature">
          <Icon name="trending-up" size={24} />
          <h3>Rich Information</h3>
          <p>Display stats, languages, topics, and recent activity at a glance</p>
        </div>
      </div>
    </section>
  </main>
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
    --border-color: #30363d;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --accent: #58a6ff;
  }

  .demo-page.light {
    --bg-page: #f6f8fa;
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --border-color: #d0d7de;
    --text-primary: #24292f;
    --text-secondary: #57606a;
    --accent: #0969da;
  }

  /* Header */
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 3rem 4rem;
    background: var(--bg-primary);
    border-bottom: 1px solid var(--border-color);
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
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .page-subtitle {
    margin: 0;
    font-size: 1.125rem;
    color: var(--text-secondary);
  }

  .header-controls {
    display: flex;
    align-items: center;
    gap: 1.5rem;
  }

  .variant-selector {
    display: flex;
    gap: 0.5rem;
    padding: 0.25rem;
    background: var(--bg-secondary);
    border-radius: 8px;
  }

  .variant-btn {
    padding: 0.5rem 1rem;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .variant-btn:hover {
    color: var(--text-primary);
  }

  .variant-btn.active {
    background: var(--bg-primary);
    color: var(--accent);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .theme-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border: 1px solid var(--border-color);
    background: var(--bg-secondary);
    color: var(--text-primary);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .theme-toggle:hover {
    background: var(--bg-primary);
    transform: translateY(-1px);
  }

  /* Main Content */
  .main-content {
    padding: 4rem;
  }

  .cards-section {
    margin-bottom: 6rem;
  }

  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .cards-grid.compact {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1rem;
  }

  /* Features Section */
  .features-section {
    max-width: 1000px;
    margin: 0 auto;
  }

  .section-title {
    margin: 0 0 2rem 0;
    font-size: 2rem;
    font-weight: 600;
    color: var(--text-primary);
    text-align: center;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 2rem;
  }

  .feature {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 2rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    text-align: center;
  }

  .feature h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .feature p {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.5;
  }

  /* Responsive */
  @media (max-width: 1024px) {
    .page-header {
      flex-direction: column;
      gap: 2rem;
      padding: 2rem;
    }

    .header-content {
      text-align: center;
    }

    .main-content {
      padding: 2rem;
    }

    .cards-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 640px) {
    .page-title {
      font-size: 1.75rem;
    }

    .variant-selector {
      flex-direction: column;
      width: 100%;
    }

    .variant-btn {
      width: 100%;
    }

    .features-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }
  }
</style>
