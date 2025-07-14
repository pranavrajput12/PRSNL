<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	
	interface Breadcrumb {
		label: string;
		href: string;
	}
	
	let breadcrumbs = $state<Breadcrumb[]>([]);
	
	$effect(() => {
		// Build breadcrumbs based on current path
		const path = $page.url.pathname;
		const parts = path.split('/').filter(Boolean);
		
		breadcrumbs = [
			{ label: 'Code Cortex', href: '/code-cortex' },
			{ label: 'CodeMirror', href: '/code-cortex/codemirror' }
		];
		
		// Add dynamic breadcrumbs based on path
		if (parts.includes('repo') && parts.length > 3) {
			const repoId = parts[parts.indexOf('repo') + 1];
			breadcrumbs.push({
				label: 'Repository Analysis',
				href: `/code-cortex/codemirror/repo/${repoId}`
			});
		}
		
		if (parts.includes('analysis') && parts.length > 3) {
			const analysisId = parts[parts.indexOf('analysis') + 1];
			// Only add repo breadcrumb if we're not already on repo page
			if (!parts.includes('repo')) {
				breadcrumbs.push({
					label: 'Analysis',
					href: `/code-cortex/codemirror/analysis/${analysisId}`
				});
			} else {
				breadcrumbs.push({
					label: 'Analysis Details',
					href: `/code-cortex/codemirror/analysis/${analysisId}`
				});
			}
		}
	});
	
	function navigate(href: string) {
		goto(href);
	}
</script>

<nav class="breadcrumbs" aria-label="Breadcrumb">
	<ol>
		{#each breadcrumbs as crumb, i}
			<li>
				{#if i < breadcrumbs.length - 1}
					<button
						class="breadcrumb-link"
						onclick={() => navigate(crumb.href)}
					>
						{crumb.label}
					</button>
					<span class="separator" aria-hidden="true">/</span>
				{:else}
					<span class="current" aria-current="page">{crumb.label}</span>
				{/if}
			</li>
		{/each}
	</ol>
</nav>

<style>
	.breadcrumbs {
		padding: 0.75rem 0;
		font-size: 0.875rem;
	}
	
	ol {
		display: flex;
		align-items: center;
		list-style: none;
		margin: 0;
		padding: 0;
	}
	
	li {
		display: flex;
		align-items: center;
	}
	
	.breadcrumb-link {
		background: none;
		border: none;
		color: #60a5fa;
		cursor: pointer;
		font-size: inherit;
		padding: 0.25rem 0.5rem;
		margin: 0 -0.5rem;
		border-radius: 0.25rem;
		transition: all 0.2s;
		text-decoration: none;
	}
	
	.breadcrumb-link:hover {
		background: rgba(96, 165, 250, 0.1);
		color: #93bbfc;
	}
	
	.separator {
		margin: 0 0.5rem;
		color: rgba(255, 255, 255, 0.3);
	}
	
	.current {
		color: rgba(255, 255, 255, 0.9);
		padding: 0.25rem 0;
	}
</style>