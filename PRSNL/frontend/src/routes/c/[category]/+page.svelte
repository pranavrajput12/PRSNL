<script lang="ts">
	import type { PageData } from './$types';

	export let data: PageData;

	$: ({ category, categoryInfo, content, pagination, filters } = data);
</script>

<svelte:head>
	<title>{categoryInfo.title} | PRSNL</title>
	<meta name="description" content={categoryInfo.description} />
	<meta property="og:title" content="{categoryInfo.title} | PRSNL" />
	<meta property="og:description" content={categoryInfo.description} />
</svelte:head>

<div class="category-page">
	<h1>Category: {category}</h1>
	<h2>{categoryInfo.title}</h2>
	<p>{categoryInfo.description}</p>
	<p>Content items: {content.length}</p>
	{#each content as item}
		<div style="border: 1px solid #ccc; margin: 1rem; padding: 1rem;">
			<h3>{item.title}</h3>
			<p>{item.summary || 'No summary'}</p>
			<p><strong>URL:</strong> <a href={item.url}>{item.url}</a></p>
			<p><strong>Source:</strong> {item.source_url || 'No source'}</p>
			<p><strong>Type:</strong> {item.type}</p>
			<p><strong>Created:</strong> {item.created_at}</p>
		</div>
	{/each}
</div>

<style>
	.category-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: 1rem;
		color: white;
	}
</style>