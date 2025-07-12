<script lang="ts">
  import Icon from '$lib/components/Icon.svelte';

  export let repoData: any = null;
  export let compact: boolean = false;

  $: stats = repoData?.stats || {};
  $: owner = repoData?.owner || {};
  $: repo = repoData?.repo || {};
  $: languages = repoData?.languages || {};
  $: recentCommits = repoData?.recent_commits || [];

  // Calculate language percentages
  $: languageStats = calculateLanguageStats(languages);

  function calculateLanguageStats(langs: Record<string, number>) {
    const total = Object.values(langs).reduce((sum, bytes) => sum + bytes, 0);
    return Object.entries(langs)
      .map(([lang, bytes]) => ({
        name: lang,
        bytes,
        percentage: total > 0 ? (bytes / total) * 100 : 0,
      }))
      .sort((a, b) => b.bytes - a.bytes)
      .slice(0, 5); // Top 5 languages
  }

  function formatNumber(num: number): string {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
  }

  function getLanguageColor(language: string): string {
    const colors: Record<string, string> = {
      JavaScript: '#f1e05a',
      TypeScript: '#3178c6',
      Python: '#3572A5',
      Java: '#b07219',
      Go: '#00ADD8',
      Rust: '#dea584',
      'C++': '#f34b7d',
      C: '#555555',
      Shell: '#89e051',
      HTML: '#e34c26',
      CSS: '#563d7c',
      Vue: '#41b883',
      React: '#61dafb',
      Swift: '#FA7343',
      Kotlin: '#A97BFF',
      Ruby: '#701516',
      PHP: '#4F5D95',
      'C#': '#178600',
      Dart: '#00B4AB',
      Scala: '#c22d40',
      Elixir: '#6e4a7e',
      Haskell: '#5e5086',
      Clojure: '#db5855',
      R: '#198CE7',
      MATLAB: '#e16737',
      Perl: '#0298c3',
      Lua: '#000080',
      'Vim script': '#199f4b',
      PowerShell: '#012456',
    };
    return colors[language] || '#8b8b8b';
  }

  function formatDate(dateString: string): string {
    if (!dateString) return 'Unknown';
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
</script>

{#if repoData}
  <div class="github-repo-card" class:compact>
    <!-- Header with owner info -->
    <div class="repo-header">
      <div class="owner-info">
        <img src={owner.avatar_url} alt={owner.login} class="owner-avatar" />
        <div class="repo-names">
          <a
            href="https://github.com/{owner.login}"
            target="_blank"
            rel="noopener noreferrer"
            class="owner-name"
          >
            {owner.login}
          </a>
          <h3 class="repo-name">
            <a href={repoData.url} target="_blank" rel="noopener noreferrer">
              {repo.name}
            </a>
            {#if repo.private}
              <span class="private-badge">Private</span>
            {/if}
          </h3>
        </div>
      </div>

      <a
        href={repoData.url}
        target="_blank"
        rel="noopener noreferrer"
        class="github-link"
        title="View on GitHub"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path
            d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
          />
        </svg>
      </a>
    </div>

    <!-- Description -->
    {#if repo.description && !compact}
      <p class="repo-description">{repo.description}</p>
    {/if}

    <!-- Stats bar -->
    <div class="stats-bar">
      <div class="stat">
        <Icon name="star" size="small" />
        <span>{formatNumber(stats.stars || 0)}</span>
      </div>
      <div class="stat">
        <Icon name="git-branch" size="small" />
        <span>{formatNumber(stats.forks || 0)}</span>
      </div>
      <div class="stat">
        <Icon name="eye" size="small" />
        <span>{formatNumber(stats.watchers || 0)}</span>
      </div>
      <div class="stat">
        <Icon name="alert-circle" size="small" />
        <span>{stats.open_issues || 0}</span>
      </div>
      {#if repo.license}
        <div class="stat">
          <Icon name="file-text" size="small" />
          <span>{repo.license}</span>
        </div>
      {/if}
    </div>

    <!-- Language breakdown -->
    {#if languageStats.length > 0 && !compact}
      <div class="languages-section">
        <div class="language-bar">
          {#each languageStats as lang}
            <div
              class="language-segment"
              style="width: {lang.percentage}%; background-color: {getLanguageColor(lang.name)}"
              title="{lang.name}: {lang.percentage.toFixed(1)}%"
            ></div>
          {/each}
        </div>
        <div class="language-list">
          {#each languageStats as lang}
            <div class="language-item">
              <span class="language-dot" style="background-color: {getLanguageColor(lang.name)}"
              ></span>
              <span class="language-name">{lang.name}</span>
              <span class="language-percent">{lang.percentage.toFixed(1)}%</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Topics -->
    {#if repoData.topics && repoData.topics.length > 0 && !compact}
      <div class="topics-section">
        {#each repoData.topics as topic}
          <span class="topic-tag">{topic}</span>
        {/each}
      </div>
    {/if}

    <!-- Recent commits (if available) -->
    {#if recentCommits.length > 0 && !compact}
      <div class="commits-section">
        <h4 class="section-title">Recent Commits</h4>
        <div class="commits-list">
          {#each recentCommits.slice(0, 3) as commit}
            <div class="commit-item">
              <div class="commit-message">{commit.message}</div>
              <div class="commit-meta">
                <span class="commit-author">{commit.author}</span>
                <span class="commit-date">{formatDate(commit.date)}</span>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Footer with additional info -->
    <div class="repo-footer">
      <div class="footer-info">
        {#if repo.language}
          <span class="primary-language">
            <span class="language-dot" style="background-color: {getLanguageColor(repo.language)}"
            ></span>
            {repo.language}
          </span>
        {/if}
        <span class="last-updated">
          Updated {formatDate(repoData.last_updated)}
        </span>
      </div>

      <div class="repo-actions">
        {#if repo.homepage}
          <a
            href={repo.homepage}
            target="_blank"
            rel="noopener noreferrer"
            class="action-link"
            title="Visit homepage"
          >
            <Icon name="globe" size="small" />
          </a>
        {/if}
        <a
          href="{repoData.url}/issues"
          target="_blank"
          rel="noopener noreferrer"
          class="action-link"
          title="View issues"
        >
          <Icon name="message-circle" size="small" />
        </a>
        <button
          class="action-link"
          title="Copy clone URL"
          on:click={() => navigator.clipboard.writeText(repo.clone_url)}
        >
          <Icon name="copy" size="small" />
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .github-repo-card {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    color: #00ff88;
    font-family: 'JetBrains Mono', monospace;
    transition: all 0.3s ease;
  }

  .github-repo-card:hover {
    border-color: #00ff88;
    box-shadow: 0 8px 25px rgba(0, 255, 136, 0.2);
  }

  .github-repo-card.compact {
    padding: 1rem;
  }

  .repo-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .owner-info {
    display: flex;
    gap: 0.75rem;
    align-items: center;
  }

  .owner-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    border: 2px solid rgba(0, 255, 136, 0.3);
  }

  .repo-names {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .owner-name {
    color: rgba(0, 255, 136, 0.7);
    text-decoration: none;
    font-size: 0.875rem;
    transition: color 0.2s;
  }

  .owner-name:hover {
    color: #00ff88;
  }

  .repo-name {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .repo-name a {
    color: #00ff88;
    text-decoration: none;
    transition: color 0.2s;
  }

  .repo-name a:hover {
    color: #dc143c;
  }

  .private-badge {
    font-size: 0.75rem;
    padding: 0.125rem 0.5rem;
    background: rgba(220, 20, 60, 0.2);
    color: #dc143c;
    border-radius: 12px;
    font-weight: 500;
  }

  .github-link {
    color: rgba(0, 255, 136, 0.7);
    transition: all 0.2s;
  }

  .github-link:hover {
    color: #00ff88;
    transform: translateY(-2px);
  }

  .repo-description {
    margin: 0 0 1rem 0;
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.5;
  }

  .stats-bar {
    display: flex;
    gap: 1.5rem;
    padding: 0.75rem 0;
    border-top: 1px solid rgba(0, 255, 136, 0.2);
    border-bottom: 1px solid rgba(0, 255, 136, 0.2);
    margin-bottom: 1rem;
  }

  .stat {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: rgba(0, 255, 136, 0.8);
    font-size: 0.875rem;
  }

  .languages-section {
    margin-bottom: 1rem;
  }

  .language-bar {
    display: flex;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 0.75rem;
    background: rgba(0, 0, 0, 0.4);
  }

  .language-segment {
    transition: opacity 0.2s;
  }

  .language-segment:hover {
    opacity: 0.8;
  }

  .language-list {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .language-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
  }

  .language-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }

  .language-name {
    color: rgba(255, 255, 255, 0.9);
  }

  .language-percent {
    color: rgba(255, 255, 255, 0.5);
  }

  .topics-section {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .topic-tag {
    padding: 0.25rem 0.75rem;
    background: rgba(0, 255, 136, 0.1);
    color: #00ff88;
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 16px;
    font-size: 0.75rem;
    transition: all 0.2s;
  }

  .topic-tag:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .commits-section {
    margin-bottom: 1rem;
  }

  .section-title {
    margin: 0 0 0.75rem 0;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: rgba(0, 255, 136, 0.8);
  }

  .commits-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .commit-item {
    padding: 0.5rem;
    background: rgba(0, 0, 0, 0.4);
    border-radius: 6px;
    border-left: 3px solid rgba(0, 255, 136, 0.3);
  }

  .commit-message {
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 0.25rem;
  }

  .commit-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.5);
  }

  .repo-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 1rem;
    border-top: 1px solid rgba(0, 255, 136, 0.2);
  }

  .footer-info {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 0.875rem;
  }

  .primary-language {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: rgba(255, 255, 255, 0.8);
  }

  .last-updated {
    color: rgba(255, 255, 255, 0.5);
  }

  .repo-actions {
    display: flex;
    gap: 0.5rem;
  }

  .action-link {
    padding: 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 6px;
    color: rgba(0, 255, 136, 0.8);
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
  }

  .action-link:hover {
    background: rgba(0, 255, 136, 0.2);
    color: #00ff88;
    transform: translateY(-2px);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .stats-bar {
      flex-wrap: wrap;
      gap: 1rem;
    }

    .language-list {
      gap: 0.75rem;
    }

    .repo-footer {
      flex-direction: column;
      gap: 1rem;
      align-items: flex-start;
    }
  }
</style>
