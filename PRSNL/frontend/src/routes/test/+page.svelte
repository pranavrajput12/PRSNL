<script>
  import { onMount } from 'svelte';

  let apiResults = {
    timeline: null,
    tags: null,
    errors: [],
  };

  onMount(async () => {
    // Test timeline endpoint
    try {
      const timelineRes = await fetch('/api/timeline?page=1');
      const timelineData = await timelineRes.json();
      apiResults.timeline = {
        status: timelineRes.status,
        ok: timelineRes.ok,
        data: timelineData,
      };
    } catch (e) {
      apiResults.errors.push(`Timeline error: ${e.message}`);
    }

    // Test tags endpoint
    try {
      const tagsRes = await fetch('/api/tags');
      const tagsData = await tagsRes.json();
      apiResults.tags = {
        status: tagsRes.status,
        ok: tagsRes.ok,
        data: tagsData,
      };
    } catch (e) {
      apiResults.errors.push(`Tags error: ${e.message}`);
    }
  });
</script>

<div class="container">
  <h1>API Test Page</h1>

  <h2>Timeline API</h2>
  {#if apiResults.timeline}
    <pre>{JSON.stringify(apiResults.timeline, null, 2)}</pre>
  {:else}
    <p>Loading...</p>
  {/if}

  <h2>Tags API</h2>
  {#if apiResults.tags}
    <pre>{JSON.stringify(apiResults.tags, null, 2)}</pre>
  {:else}
    <p>Loading...</p>
  {/if}

  {#if apiResults.errors.length > 0}
    <h2>Errors</h2>
    <ul>
      {#each apiResults.errors as error}
        <li>{error}</li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .container {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  pre {
    background: var(--bg-secondary);
    padding: 1rem;
    border-radius: var(--radius);
    overflow: auto;
    max-height: 400px;
  }

  h1,
  h2 {
    color: var(--text-primary);
  }
</style>
