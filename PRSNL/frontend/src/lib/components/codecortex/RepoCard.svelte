<script lang="ts">
  interface Props {
    repo: {
      id: string;
      name: string;
      full_name?: string;
      description?: string;
      language?: string;
      html_url?: string;
    };
    onSelect?: (repo: any) => void;
    onView?: (repo: any) => void;
    selected?: boolean;
  }
  
  let { repo, onSelect, onView, selected = false }: Props = $props();
  
  function handleClick() {
    if (onSelect) {
      onSelect(repo);
    }
  }
  
  function handleView(e) {
    e.stopPropagation();
    if (onView) {
      onView(repo);
    }
  }
  
  // Language colors (GitHub-style)
  const languageColors = {
    JavaScript: '#f1e05a',
    TypeScript: '#3178c6',
    Python: '#3572A5',
    Java: '#b07219',
    Go: '#00ADD8',
    Rust: '#dea584',
    Ruby: '#701516',
    PHP: '#4F5D95',
    'C++': '#f34b7d',
    C: '#555555',
    Swift: '#FA7343',
    Kotlin: '#A97BFF',
    Dart: '#00B4AB',
    Vue: '#41b883',
    React: '#61dafb',
    HTML: '#e34c26',
    CSS: '#563d7c'
  };
  
  function getLanguageColor(language: string) {
    return languageColors[language] || '#6e7681';
  }
</script>

<button 
  class="repo-card {selected ? 'selected' : ''}"
  onclick={handleClick}
>
  <div class="repo-header">
    <h3 class="repo-name">{repo.name}</h3>
    {#if repo.html_url}
      <a 
        href={repo.html_url} 
        target="_blank" 
        class="github-link"
        onclick={(e) => e.stopPropagation()}
        title="View on GitHub"
      >
        <svg viewBox="0 0 16 16" width="16" height="16">
          <path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
        </svg>
      </a>
    {/if}
  </div>
  
  {#if repo.description}
    <p class="repo-description">{repo.description}</p>
  {:else}
    <p class="repo-description no-desc">No description available</p>
  {/if}
  
  <div class="repo-footer">
    {#if repo.language}
      <div class="language-badge">
        <span 
          class="language-dot" 
          style="background-color: {getLanguageColor(repo.language)}"
        ></span>
        <span class="language-name">{repo.language}</span>
      </div>
    {/if}
    
    {#if onView}
      <button 
        class="view-button"
        onclick={handleView}
        title="View repository details"
      >
        View
      </button>
    {/if}
  </div>
</button>

<style>
  .repo-card {
    display: block;
    width: 100%;
    text-align: left;
    background: var(--surface-3, #1a1a2e);
    border: 1px solid var(--border, rgba(255, 255, 255, 0.1));
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .repo-card:hover {
    background: var(--surface-4, #16213e);
    border-color: var(--primary-alpha, rgba(59, 130, 246, 0.3));
    transform: translateY(-1px);
  }
  
  .repo-card.selected {
    background: var(--primary-alpha, rgba(59, 130, 246, 0.1));
    border-color: var(--primary, #3b82f6);
  }
  
  .repo-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }
  
  .repo-name {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary, white);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
  }
  
  .github-link {
    color: var(--text-secondary, rgba(255, 255, 255, 0.6));
    transition: color 0.2s;
    flex-shrink: 0;
    padding: 0.25rem;
    margin: -0.25rem;
  }
  
  .github-link:hover {
    color: var(--text-primary, white);
  }
  
  .repo-description {
    margin: 0 0 0.75rem 0;
    font-size: 0.875rem;
    color: var(--text-secondary, rgba(255, 255, 255, 0.7));
    line-height: 1.4;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  
  .repo-description.no-desc {
    font-style: italic;
    opacity: 0.6;
  }
  
  .repo-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }
  
  .language-badge {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.75rem;
  }
  
  .language-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  
  .language-name {
    color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  }
  
  .view-button {
    background: var(--primary, #3b82f6);
    border: none;
    border-radius: 4px;
    color: white;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.375rem 0.75rem;
    cursor: pointer;
    transition: all 0.2s;
    flex-shrink: 0;
  }
  
  .view-button:hover {
    background: var(--primary-hover, #2563eb);
    transform: translateY(-1px);
  }
</style>