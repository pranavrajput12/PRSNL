<script>
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import CodeMirrorBreadcrumbs from '$lib/components/codecortex/CodeMirrorBreadcrumbs.svelte';
	
	let repoId = $page.params.id;
	let repository = null;
	let analyses = [];
	let loading = true;
	let error = null;

	async function loadRepositoryData() {
		try {
			loading = true;
			
			// Load analyses for this repository
			const analysesResponse = await fetch(`/api/codemirror/analyses/${repoId}`, {
				headers: {
					'X-PRSNL-Integration': 'frontend'
				}
			});
			
			if (!analysesResponse.ok) {
				throw new Error(`Failed to load analyses: ${analysesResponse.status}`);
			}
			
			analyses = await analysesResponse.json();
			
			// Get repository name from first analysis
			if (analyses.length > 0 && analyses[0].repository_name) {
				repository = {
					name: analyses[0].repository_name,
					id: repoId
				};
			}
			
		} catch (err) {
			console.error('Error loading repository data:', err);
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function goBack() {
		goto('/code-cortex/codemirror');
	}

	function viewAnalysis(analysisId) {
		goto(`/code-cortex/codemirror/analysis/${analysisId}`);
	}

	function startNewAnalysis() {
		// Navigate to analysis start or trigger analysis
		goto('/code-cortex/codemirror');
	}

	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getStatusColor(analysis) {
		if (analysis.analysis_completed_at) {
			return 'text-green-400 bg-green-900/30 border-green-600/30';
		} else if (analysis.job_status === 'failed') {
			return 'text-red-400 bg-red-900/30 border-red-600/30';
		} else {
			return 'text-yellow-400 bg-yellow-900/30 border-yellow-600/30';
		}
	}

	function getStatusText(analysis) {
		if (analysis.analysis_completed_at) {
			return 'Completed';
		} else if (analysis.job_status === 'failed') {
			return 'Failed';
		} else {
			return 'Processing';
		}
	}

	onMount(() => {
		loadRepositoryData();
	});
</script>

<svelte:head>
	<title>Repository Analysis - CodeMirror</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white">
	<!-- Header -->
	<div class="border-b border-gray-700">
		<div class="container mx-auto px-6 py-4">
			<div class="flex items-center justify-between mb-2">
				<div class="flex items-center space-x-3">
					<div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 00-2 2v2a2 2 0 002 2m0 0h14" />
						</svg>
					</div>
					<div>
						<h1 class="text-xl font-bold">Repository Analysis</h1>
						<p class="text-sm text-gray-400">AI-powered repository intelligence</p>
					</div>
				</div>
			</div>
			<CodeMirrorBreadcrumbs />
		</div>
	</div>

	<!-- Main Content -->
	<div class="container mx-auto px-6 py-8">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
				<span class="ml-3 text-gray-300">Loading repository analysis...</span>
			</div>
		{:else if error}
			<div class="bg-red-900/50 border border-red-600 rounded-lg p-6 text-center">
				<svg class="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z" />
				</svg>
				<h3 class="text-lg font-semibold text-red-300 mb-2">Error Loading Repository</h3>
				<p class="text-red-200">{error}</p>
				<button
					on:click={loadRepositoryData}
					class="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
				>
					Retry
				</button>
			</div>
		{:else}
			<!-- Repository Header -->
			<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6 mb-6">
				<div class="flex items-start justify-between">
					<div>
						<h2 class="text-2xl font-bold text-white mb-2">
							{repository?.name || 'Repository'}
						</h2>
						<div class="flex items-center space-x-4 text-sm text-gray-400">
							<span class="flex items-center space-x-1">
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
								</svg>
								<span>{analyses.length} analyses</span>
							</span>
							<span class="flex items-center space-x-1">
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
								</svg>
								<span>Repository ID: {repoId.slice(0, 8)}...</span>
							</span>
						</div>
					</div>
					<button
						on:click={startNewAnalysis}
						class="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
						</svg>
						<span>New Analysis</span>
					</button>
				</div>
			</div>

			<!-- Analyses List -->
			{#if analyses.length > 0}
				<div class="space-y-4">
					<h3 class="text-lg font-semibold text-white mb-4">Analysis History</h3>
					{#each analyses as analysis}
						<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6 hover:bg-gray-800/70 transition-colors cursor-pointer"
							 on:click={() => viewAnalysis(analysis.id)}>
							<div class="flex items-start justify-between">
								<div class="flex-1">
									<div class="flex items-center space-x-3 mb-2">
										<h4 class="font-medium text-white">
											{analysis.analysis_type.toUpperCase()} Analysis
										</h4>
										<span class="text-xs px-2 py-1 rounded border {getStatusColor(analysis)}">
											{getStatusText(analysis)}
										</span>
										<span class="text-xs px-2 py-1 bg-purple-900/30 text-purple-400 rounded border border-purple-600/30">
											{analysis.analysis_depth}
										</span>
									</div>
									<div class="flex items-center space-x-4 text-sm text-gray-400 mb-3">
										<span class="flex items-center space-x-1">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
											</svg>
											<span>{formatDate(analysis.created_at)}</span>
										</span>
										{#if analysis.file_count}
											<span class="flex items-center space-x-1">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
												</svg>
												<span>{analysis.file_count} files</span>
											</span>
										{/if}
										{#if analysis.progress}
											<span class="flex items-center space-x-1">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
												</svg>
												<span>{analysis.progress}% complete</span>
											</span>
										{/if}
									</div>
									
									<!-- Languages and Frameworks -->
									{#if analysis.languages_detected || analysis.frameworks_detected}
										<div class="flex items-center space-x-4">
											{#if analysis.languages_detected}
												<div class="flex items-center space-x-2">
													<span class="text-xs text-gray-400">Languages:</span>
													<div class="flex space-x-1">
														{#each JSON.parse(analysis.languages_detected || '[]') as language}
															<span class="text-xs px-2 py-1 bg-green-900/30 text-green-400 rounded border border-green-600/30">
																{language}
															</span>
														{/each}
													</div>
												</div>
											{/if}
											{#if analysis.frameworks_detected}
												<div class="flex items-center space-x-2">
													<span class="text-xs text-gray-400">Frameworks:</span>
													<div class="flex space-x-1">
														{#each JSON.parse(analysis.frameworks_detected || '[]') as framework}
															<span class="text-xs px-2 py-1 bg-blue-900/30 text-blue-400 rounded border border-blue-600/30">
																{framework}
															</span>
														{/each}
													</div>
												</div>
											{/if}
										</div>
									{/if}
								</div>
								
								<!-- Action Button -->
								<div class="ml-4">
									<div class="flex items-center space-x-2 text-blue-400">
										<span class="text-sm">View Details</span>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
										</svg>
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-8 text-center">
					<svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
					</svg>
					<h3 class="text-xl font-semibold text-gray-300 mb-2">No Analyses Found</h3>
					<p class="text-gray-400 mb-6">Start your first analysis to see intelligent insights about this repository.</p>
					<button
						on:click={startNewAnalysis}
						class="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium"
					>
						Start Analysis
					</button>
				</div>
			{/if}
		{/if}
	</div>
</div>