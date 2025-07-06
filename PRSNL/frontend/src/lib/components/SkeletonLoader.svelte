<script>
  export let type = 'card'; // card, timeline, search
  export let count = 3;
</script>

<div class="skeleton-container {type}">
  {#if type === 'card'}
    {#each Array(count) as _}
      <div class="skeleton-card">
        <div class="skeleton-header">
          <div class="skeleton-title"></div>
          <div class="skeleton-date"></div>
        </div>
        <div class="skeleton-content">
          <div class="skeleton-line"></div>
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
        </div>
        <div class="skeleton-tags">
          <div class="skeleton-tag"></div>
          <div class="skeleton-tag"></div>
        </div>
      </div>
    {/each}
  {:else if type === 'timeline'}
    <div class="skeleton-date-header"></div>
    {#each Array(count) as _}
      <div class="skeleton-timeline-item">
        <div class="skeleton-time"></div>
        <div class="skeleton-content">
          <div class="skeleton-title"></div>
          <div class="skeleton-url"></div>
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
          <div class="skeleton-tags">
            <div class="skeleton-tag"></div>
            <div class="skeleton-tag"></div>
          </div>
        </div>
      </div>
    {/each}
  {:else if type === 'search'}
    {#each Array(count) as _}
      <div class="skeleton-search-item">
        <div class="skeleton-title"></div>
        <div class="skeleton-url"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-tags">
          <div class="skeleton-tag"></div>
          <div class="skeleton-tag"></div>
        </div>
      </div>
    {/each}
  {/if}
</div>

<style>
  .skeleton-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    animation: pulse 1.5s ease-in-out infinite;
  }
  
  .skeleton-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .skeleton-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .skeleton-title {
    height: 1.25rem;
    width: 60%;
    background: var(--bg-tertiary);
    border-radius: 4px;
  }
  
  .skeleton-date {
    height: 0.875rem;
    width: 25%;
    background: var(--bg-tertiary);
    border-radius: 4px;
  }
  
  .skeleton-content {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .skeleton-line {
    height: 0.875rem;
    width: 100%;
    background: var(--bg-tertiary);
    border-radius: 4px;
  }
  
  .skeleton-line.short {
    width: 70%;
  }
  
  .skeleton-tags {
    display: flex;
    gap: 0.5rem;
  }
  
  .skeleton-tag {
    height: 0.75rem;
    width: 3rem;
    background: var(--bg-tertiary);
    border-radius: 4px;
  }
  
  .skeleton-timeline-item {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }
  
  .skeleton-time {
    height: 0.875rem;
    width: 3rem;
    background: var(--bg-tertiary);
    border-radius: 4px;
    flex-shrink: 0;
  }
  
  .skeleton-date-header {
    height: 1.125rem;
    width: 30%;
    background: var(--bg-tertiary);
    border-radius: 4px;
    margin-bottom: 1rem;
  }
  
  .skeleton-url {
    height: 0.75rem;
    width: 40%;
    background: var(--bg-tertiary);
    border-radius: 4px;
    margin-bottom: 0.5rem;
  }
  
  .skeleton-search-item {
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  @keyframes pulse {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.6;
    }
    100% {
      opacity: 1;
    }
  }
</style>
