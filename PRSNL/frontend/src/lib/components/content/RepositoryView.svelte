<!--
  Repository View Component
  Basic implementation for repository content display
-->

<script lang="ts">
  import Icon from '$lib/components/Icon.svelte';
  import GitHubRepoCard from '$lib/components/development/GitHubRepoCard.svelte';
  import GenericItemView from './GenericItemView.svelte';
  
  export let item: any;
  export let contentType: any;
  
  $: hasGitHubData = item.metadata?.rich_preview && item.metadata.rich_preview.type !== 'error';
  $: githubData = hasGitHubData ? item.metadata.rich_preview : null;
</script>

<div class="repository-view">
  {#if hasGitHubData && githubData}
    <section class="github-section">
      <GitHubRepoCard repoData={githubData} />
    </section>
  {/if}
  
  <!-- Use generic view for the rest -->
  <GenericItemView {item} {contentType} on:error />
</div>

<style>
  .repository-view {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  .github-section {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
  }
</style>