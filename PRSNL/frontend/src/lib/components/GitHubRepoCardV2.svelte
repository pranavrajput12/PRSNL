<script lang="ts">
  import { fade } from 'svelte/transition';
  import Icon from './Icon.svelte';

  export let repository: any = null;
  export let variant: 'default' | 'compact' | 'featured' = 'default';
  export let theme: 'dark' | 'light' = 'dark';

  // Computed properties
  $: owner = repository?.owner || {};
  $: repo = repository?.repo || {};
  $: stats = repository?.stats || {};
  $: languages = repository?.languages || {};
  $: topics = repository?.topics || [];
  $: isPrivate = repo.private || false;
  $: primaryLanguage = repo.language || 'Unknown';
  $: lastUpdated = repository?.last_updated || new Date().toISOString();

  // Language colors (GitHub standard)
  const languageColors: Record<string, string> = {
    JavaScript: '#f1e05a',
    TypeScript: '#3178c6',
    Python: '#3572A5',
    Java: '#b07219',
    Go: '#00ADD8',
    Rust: '#dea584',
    'C++': '#f34b7d',
    C: '#555555',
    Ruby: '#701516',
    PHP: '#4F5D95',
    Swift: '#FA7343',
    Kotlin: '#A97BFF',
    Dart: '#00B4AB',
    Vue: '#41b883',
    React: '#61dafb',
  };

  // Calculate language percentages
  $: languageData = Object.entries(languages)
    .map(([name, bytes]: [string, any]) => ({
      name,
      bytes,
      percentage: 0,
      color: languageColors[name] || '#8b949e'
    }))
    .sort((a, b) => b.bytes - a.bytes)
    .slice(0, 5);

  $: {
    const total = languageData.reduce((sum, lang) => sum + lang.bytes, 0);
    languageData.forEach(lang => {
      lang.percentage = total > 0 ? (lang.bytes / total) * 100 : 0;
    });
  }

  function formatNumber(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return num.toString();
  }

  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 1) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  }

  function handleRepoClick() {
    if (repository?.url) {
      window.open(repository.url, '_blank', 'noopener,noreferrer');
    }
  }
</script>

{#if repository}
  <article 
    class="repo-card {variant} {theme}"
    on:click={handleRepoClick}
    transition:fade={{ duration: 200 }}
  >
    <!-- Header -->
    <header class="card-header">
      <div class="repo-identity">
        <img 
          src={owner.avatar_url} 
          alt={owner.login}
          class="owner-avatar"
        />
        <div class="repo-names">
          <a 
            href="https://github.com/{owner.login}"
            target="_blank"
            rel="noopener noreferrer"
            class="owner-link"
            on:click|stopPropagation
          >
            {owner.login}
          </a>
          <h3 class="repo-name">
            {repo.name}
            {#if isPrivate}
              <span class="private-badge">
                <Icon name="lock" size={12} />
                Private
              </span>
            {/if}
          </h3>
        </div>
      </div>

      <button 
        class="github-btn"
        on:click|stopPropagation={() => window.open(repository.url, '_blank')}
        title="View on GitHub"
      >
        <Icon name="github" size={18} />
      </button>
    </header>

    <!-- Description -->
    {#if repo.description && variant !== 'compact'}
      <p class="repo-description">{repo.description}</p>
    {/if}

    <!-- Language Bar -->
    {#if languageData.length > 0 && variant !== 'compact'}
      <div class="language-section">
        <div class="language-bar">
          {#each languageData as lang}
            <div 
              class="language-segment"
              style="width: {lang.percentage}%; background-color: {lang.color}"
              title="{lang.name}: {lang.percentage.toFixed(1)}%"
            />
          {/each}
        </div>
        {#if variant === 'featured'}
          <div class="language-legend">
            {#each languageData.slice(0, 3) as lang}
              <div class="language-item">
                <span 
                  class="language-dot" 
                  style="background-color: {lang.color}"
                />
                <span class="language-name">{lang.name}</span>
                <span class="language-percent">{lang.percentage.toFixed(1)}%</span>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Topics -->
    {#if topics.length > 0 && variant !== 'compact'}
      <div class="topics-row">
        {#each topics.slice(0, 5) as topic}
          <span class="topic-tag">{topic}</span>
        {/each}
        {#if topics.length > 5}
          <span class="topic-more">+{topics.length - 5}</span>
        {/if}
      </div>
    {/if}

    <!-- Stats Footer -->
    <footer class="card-footer">
      <div class="stats-row">
        <div class="stat-item">
          <Icon name="star" size={16} />
          <span>{formatNumber(stats.stars || 0)}</span>
        </div>
        <div class="stat-item">
          <Icon name="git-branch" size={16} />
          <span>{formatNumber(stats.forks || 0)}</span>
        </div>
        {#if variant !== 'compact'}
          <div class="stat-item">
            <Icon name="eye" size={16} />
            <span>{formatNumber(stats.watchers || 0)}</span>
          </div>
          {#if stats.open_issues > 0}
            <div class="stat-item">
              <Icon name="alert-circle" size={16} />
              <span>{stats.open_issues}</span>
            </div>
          {/if}
        {/if}
      </div>

      <div class="meta-info">
        {#if primaryLanguage !== 'Unknown'}
          <div class="primary-language">
            <span 
              class="language-indicator"
              style="background-color: {languageColors[primaryLanguage] || '#8b949e'}"
            />
            {primaryLanguage}
          </div>
        {/if}
        <span class="updated-text">
          Updated {formatDate(lastUpdated)}
        </span>
      </div>
    </footer>

    <!-- Featured variant additions -->
    {#if variant === 'featured' && repository.recent_commits}
      <div class="commits-preview">
        <h4 class="commits-title">Recent Activity</h4>
        {#each repository.recent_commits.slice(0, 2) as commit}
          <div class="commit-item">
            <Icon name="git-commit" size={14} />
            <span class="commit-message">{commit.message}</span>
            <span class="commit-date">{formatDate(commit.date)}</span>
          </div>
        {/each}
      </div>
    {/if}
  </article>
{/if}

<style>
  .repo-card {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1.5rem;
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
  }

  /* Theme Variables */
  .repo-card.dark {
    --card-bg: #0d1117;
    --card-hover-bg: #161b22;
    --border-color: #30363d;
    --border-hover: #58a6ff;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --text-tertiary: #6e7681;
    --link-color: #58a6ff;
    --link-hover: #79c0ff;
    --badge-bg: rgba(88, 166, 255, 0.1);
    --badge-color: #79c0ff;
    --topic-bg: rgba(56, 139, 253, 0.1);
    --topic-border: rgba(56, 139, 253, 0.3);
    --topic-color: #79c0ff;
  }

  .repo-card.light {
    --card-bg: #ffffff;
    --card-hover-bg: #f6f8fa;
    --border-color: #d0d7de;
    --border-hover: #0969da;
    --text-primary: #24292f;
    --text-secondary: #57606a;
    --text-tertiary: #6e7781;
    --link-color: #0969da;
    --link-hover: #0860ca;
    --badge-bg: rgba(9, 105, 218, 0.1);
    --badge-color: #0969da;
    --topic-bg: rgba(9, 105, 218, 0.1);
    --topic-border: rgba(9, 105, 218, 0.3);
    --topic-color: #0969da;
  }

  .repo-card:hover {
    background: var(--card-hover-bg);
    border-color: var(--border-hover);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .repo-card.compact {
    padding: 1rem;
    gap: 0.75rem;
  }

  .repo-card.featured {
    padding: 2rem;
    gap: 1.25rem;
  }

  /* Header */
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }

  .repo-identity {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    min-width: 0;
  }

  .owner-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .repo-card.compact .owner-avatar {
    width: 32px;
    height: 32px;
  }

  .repo-names {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    min-width: 0;
  }

  .owner-link {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.875rem;
    transition: color 0.2s;
  }

  .owner-link:hover {
    color: var(--link-color);
  }

  .repo-name {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .private-badge {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.125rem 0.5rem;
    background: var(--badge-bg);
    color: var(--badge-color);
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
    flex-shrink: 0;
  }

  .github-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border: 1px solid var(--border-color);
    background: transparent;
    color: var(--text-secondary);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    flex-shrink: 0;
  }

  .github-btn:hover {
    background: var(--card-hover-bg);
    color: var(--text-primary);
    border-color: var(--border-hover);
  }

  /* Description */
  .repo-description {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* Language Section */
  .language-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .language-bar {
    display: flex;
    height: 8px;
    background: var(--border-color);
    border-radius: 4px;
    overflow: hidden;
  }

  .language-segment {
    transition: opacity 0.2s;
  }

  .language-segment:hover {
    opacity: 0.8;
  }

  .language-legend {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .language-item {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.75rem;
  }

  .language-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .language-name {
    color: var(--text-primary);
  }

  .language-percent {
    color: var(--text-tertiary);
  }

  /* Topics */
  .topics-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .topic-tag {
    padding: 0.25rem 0.625rem;
    background: var(--topic-bg);
    border: 1px solid var(--topic-border);
    color: var(--topic-color);
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
    transition: all 0.2s;
  }

  .topic-tag:hover {
    background: var(--topic-border);
  }

  .topic-more {
    padding: 0.25rem 0.625rem;
    color: var(--text-tertiary);
    font-size: 0.75rem;
  }

  /* Footer */
  .card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-top: auto;
  }

  .stats-row {
    display: flex;
    gap: 1rem;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .stat-item:hover {
    color: var(--text-primary);
  }

  .meta-info {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 0.75rem;
    color: var(--text-tertiary);
  }

  .primary-language {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .language-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  /* Commits Preview (Featured) */
  .commits-preview {
    padding-top: 1rem;
    border-top: 1px solid var(--border-color);
  }

  .commits-title {
    margin: 0 0 0.75rem 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .commit-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .commit-message {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .commit-date {
    color: var(--text-tertiary);
    flex-shrink: 0;
  }

  /* Responsive */
  @media (max-width: 640px) {
    .repo-card {
      padding: 1rem;
    }

    .card-footer {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .meta-info {
      font-size: 0.7rem;
    }
  }
</style>