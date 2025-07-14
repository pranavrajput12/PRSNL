<script>
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import CodeMirrorBreadcrumbs from '$lib/components/codecortex/CodeMirrorBreadcrumbs.svelte';
	
	let analysisId = $page.params.id;
	let analysis = null;
	let insights = [];
	let knowledgeContent = null;
	let loading = true;
	let loadingKnowledge = false;
	let error = null;

	async function loadAnalysisData() {
		try {
			loading = true;
			
			// Load analysis details by ID
			const analysisResponse = await fetch(`/api/codemirror/analysis/${analysisId}`, {
				headers: {
					'X-PRSNL-Integration': 'frontend'
				}
			});
			
			if (!analysisResponse.ok) {
				throw new Error(`Failed to load analysis: ${analysisResponse.status}`);
			}
			
			analysis = await analysisResponse.json();
			
			// Load insights for this analysis
			const insightsResponse = await fetch(`/api/codemirror/insights/${analysisId}`, {
				headers: {
					'X-PRSNL-Integration': 'frontend'
				}
			});
			
			if (insightsResponse.ok) {
				insights = await insightsResponse.json();
			}
			
			// Load knowledge base content
			await loadKnowledgeContent();
			
		} catch (err) {
			console.error('Error loading analysis:', err);
			error = err.message;
		} finally {
			loading = false;
		}
	}

	async function loadKnowledgeContent() {
		try {
			loadingKnowledge = true;
			
			const knowledgeResponse = await fetch(`/api/codemirror/analysis/${analysisId}/knowledge`, {
				headers: {
					'X-PRSNL-Integration': 'frontend'
				}
			});
			
			if (knowledgeResponse.ok) {
				knowledgeContent = await knowledgeResponse.json();
			}
			
		} catch (err) {
			console.error('Error loading knowledge content:', err);
		} finally {
			loadingKnowledge = false;
		}
	}

	function goBack() {
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

	function getSeverityColor(severity) {
		switch (severity?.toLowerCase()) {
			case 'critical': return 'text-red-400';
			case 'high': return 'text-orange-400';
			case 'medium': return 'text-yellow-400';
			case 'low': return 'text-green-400';
			default: return 'text-gray-400';
		}
	}

	onMount(() => {
		loadAnalysisData();
	});
</script>

<svelte:head>
	<title>Analysis Details - CodeMirror</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white">
	<!-- Header -->
	<div class="border-b border-gray-700">
		<div class="container mx-auto px-6 py-4">
			<div class="flex items-center justify-between mb-2">
				<div class="flex items-center space-x-3">
					<div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
						</svg>
					</div>
					<div>
						<h1 class="text-xl font-bold">Analysis Details</h1>
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
				<span class="ml-3 text-gray-300">Loading analysis details...</span>
			</div>
		{:else if error}
			<div class="bg-red-900/50 border border-red-600 rounded-lg p-6 text-center">
				<svg class="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z" />
				</svg>
				<h3 class="text-lg font-semibold text-red-300 mb-2">Error Loading Analysis</h3>
				<p class="text-red-200">{error}</p>
				<button
					on:click={loadAnalysisData}
					class="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
				>
					Retry
				</button>
			</div>
		{:else if analysis}
			<!-- Analysis Header -->
			<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6 mb-6">
				<div class="flex items-start justify-between">
					<div>
						<h2 class="text-2xl font-bold text-white mb-2">
							{analysis.repository_name || 'Repository Analysis'}
						</h2>
						<div class="flex items-center space-x-4 text-sm text-gray-400">
							<span class="flex items-center space-x-1">
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
								</svg>
								<span>{formatDate(analysis.created_at)}</span>
							</span>
							<span class="flex items-center space-x-1">
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
								</svg>
								<span class="capitalize">{analysis.analysis_depth}</span>
							</span>
							<span class="flex items-center space-x-1">
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
								<span class="text-green-400">Completed</span>
							</span>
						</div>
					</div>
					<div class="text-right">
						<div class="text-sm text-gray-400 mb-1">Analysis ID</div>
						<div class="text-xs font-mono text-blue-400 bg-blue-900/30 px-2 py-1 rounded">
							{analysis.id}
						</div>
					</div>
				</div>
			</div>

			<!-- Analysis Results -->
			{#if analysis.results}
				{@const results = typeof analysis.results === 'string' ? JSON.parse(analysis.results) : analysis.results}
				<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
					<!-- File Count -->
					<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6">
						<div class="flex items-center justify-between">
							<div>
								<h3 class="text-lg font-semibold text-white mb-1">Files Analyzed</h3>
								<p class="text-3xl font-bold text-blue-400">{results.file_count || 0}</p>
							</div>
							<svg class="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
							</svg>
						</div>
					</div>

					<!-- Languages -->
					<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6">
						<h3 class="text-lg font-semibold text-white mb-3">Languages</h3>
						<div class="space-y-2">
							{#if results.languages_detected && results.languages_detected.length > 0}
								{#each results.languages_detected as language}
									<span class="inline-block px-3 py-1 text-xs font-medium bg-green-900/30 text-green-400 rounded-full border border-green-600/30">
										{language}
									</span>
								{/each}
							{:else}
								<span class="text-gray-400 text-sm">No languages detected</span>
							{/if}
						</div>
					</div>

					<!-- Frameworks -->
					<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6">
						<h3 class="text-lg font-semibold text-white mb-3">Frameworks</h3>
						<div class="space-y-2">
							{#if results.frameworks_detected && results.frameworks_detected.length > 0}
								{#each results.frameworks_detected as framework}
									<span class="inline-block px-3 py-1 text-xs font-medium bg-purple-900/30 text-purple-400 rounded-full border border-purple-600/30">
										{framework}
									</span>
								{/each}
							{:else}
								<span class="text-gray-400 text-sm">No frameworks detected</span>
							{/if}
						</div>
					</div>
				</div>
			{/if}

			<!-- Quality Scores -->
			{#if analysis.security_score || analysis.performance_score || analysis.quality_score}
				<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6 mb-6">
					<h3 class="text-lg font-semibold text-white mb-4">Quality Scores</h3>
					<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
						<!-- Security Score -->
						<div class="text-center">
							<div class="text-sm text-gray-400 mb-2">Security</div>
							<div class="text-2xl font-bold text-blue-400">
								{analysis.security_score || 'N/A'}
								{#if analysis.security_score}<span class="text-sm text-gray-400">/100</span>{/if}
							</div>
						</div>
						<!-- Performance Score -->
						<div class="text-center">
							<div class="text-sm text-gray-400 mb-2">Performance</div>
							<div class="text-2xl font-bold text-green-400">
								{analysis.performance_score || 'N/A'}
								{#if analysis.performance_score}<span class="text-sm text-gray-400">/100</span>{/if}
							</div>
						</div>
						<!-- Quality Score -->
						<div class="text-center">
							<div class="text-sm text-gray-400 mb-2">Code Quality</div>
							<div class="text-2xl font-bold text-purple-400">
								{analysis.quality_score || 'N/A'}
								{#if analysis.quality_score}<span class="text-sm text-gray-400">/100</span>{/if}
							</div>
						</div>
					</div>
				</div>
			{/if}

			<!-- Insights -->
			{#if insights.length > 0}
				<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6">
					<h3 class="text-lg font-semibold text-white mb-4">AI Insights</h3>
					<div class="space-y-4">
						{#each insights as insight}
							<div class="bg-gray-700/50 rounded-lg p-4 border border-gray-600">
								<div class="flex items-start justify-between mb-2">
									<h4 class="font-medium text-white">{insight.title}</h4>
									<div class="flex items-center space-x-2">
										<span class="text-xs px-2 py-1 rounded {getSeverityColor(insight.severity)} bg-gray-600/50">
											{insight.severity || 'medium'}
										</span>
										<span class="text-xs text-gray-400">
											{Math.round((insight.confidence_score || 0) * 100)}% confidence
										</span>
									</div>
								</div>
								<p class="text-gray-300 text-sm mb-2">{insight.description}</p>
								{#if insight.recommendation}
									<div class="bg-blue-900/30 border border-blue-600/30 rounded p-3 mt-3">
										<div class="text-xs text-blue-400 font-medium mb-1">Recommendation</div>
										<div class="text-sm text-blue-200">{insight.recommendation}</div>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{:else}
				<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6 text-center">
					<svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
					</svg>
					<h3 class="text-lg font-semibold text-gray-300 mb-2">No Insights Available</h3>
					<p class="text-gray-400">AI insights will appear here once the analysis is complete.</p>
				</div>
			{/if}

			<!-- Related Knowledge Base Content -->
			<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6 mt-6">
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-semibold text-white flex items-center space-x-2">
						<svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 00-2 2v2a2 2 0 002 2m0 0h14" />
						</svg>
						<span>Related Knowledge</span>
					</h3>
					{#if loadingKnowledge}
						<div class="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-400"></div>
					{/if}
				</div>

				{#if knowledgeContent && knowledgeContent.total_results > 0}
					<div class="space-y-6">
						<!-- Summary -->
						<div class="bg-purple-900/20 border border-purple-600/30 rounded-lg p-4">
							<div class="flex items-center justify-between text-sm">
								<span class="text-purple-300">
									Found {knowledgeContent.total_results} related items
								</span>
								<span class="text-gray-400">
									Search terms: {knowledgeContent.search_terms_used?.slice(0, 5).join(', ')}
									{#if knowledgeContent.search_terms_used?.length > 5}...{/if}
								</span>
							</div>
						</div>

						<!-- Videos -->
						{#if knowledgeContent.videos && knowledgeContent.videos.length > 0}
							<div>
								<h4 class="text-md font-semibold text-white mb-3 flex items-center space-x-2">
									<svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
									</svg>
									<span>Related Videos ({knowledgeContent.videos.length})</span>
								</h4>
								<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
									{#each knowledgeContent.videos as video}
										<div class="bg-gray-700/50 rounded-lg p-4 border border-gray-600 hover:bg-gray-700/70 transition-colors">
											<h5 class="font-medium text-white mb-2">{video.title}</h5>
											<p class="text-sm text-gray-300 mb-2 line-clamp-2">{video.description || 'No description available'}</p>
											<div class="flex items-center justify-between text-xs text-gray-400">
												<span>{video.duration || 'Unknown duration'}</span>
												<span class="bg-red-900/30 text-red-400 px-2 py-1 rounded">Score: {video.relevance_score}</span>
											</div>
											{#if video.video_url}
												<a href={video.video_url} target="_blank" class="text-blue-400 hover:text-blue-300 text-xs mt-2 inline-block">
													Watch Video →
												</a>
											{/if}
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Photos -->
						{#if knowledgeContent.photos && knowledgeContent.photos.length > 0}
							<div>
								<h4 class="text-md font-semibold text-white mb-3 flex items-center space-x-2">
									<svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
									</svg>
									<span>Related Images ({knowledgeContent.photos.length})</span>
								</h4>
								<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
									{#each knowledgeContent.photos as photo}
										<div class="bg-gray-700/50 rounded-lg p-3 border border-gray-600 hover:bg-gray-700/70 transition-colors">
											{#if photo.thumbnail_url}
												<img src={photo.thumbnail_url} alt={photo.filename} class="w-full h-20 object-cover rounded mb-2" />
											{:else}
												<div class="w-full h-20 bg-gray-600 rounded mb-2 flex items-center justify-center">
													<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
													</svg>
												</div>
											{/if}
											<h5 class="text-xs font-medium text-white mb-1 truncate">{photo.filename}</h5>
											<div class="flex items-center justify-between text-xs">
												<span class="text-gray-400 truncate">{photo.description || 'No description'}</span>
												<span class="bg-green-900/30 text-green-400 px-1 py-0.5 rounded text-xs">
													{photo.relevance_score}
												</span>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Documents -->
						{#if knowledgeContent.documents && knowledgeContent.documents.length > 0}
							<div>
								<h4 class="text-md font-semibold text-white mb-3 flex items-center space-x-2">
									<svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
									</svg>
									<span>Related Documents ({knowledgeContent.documents.length})</span>
								</h4>
								<div class="space-y-3">
									{#each knowledgeContent.documents as document}
										<div class="bg-gray-700/50 rounded-lg p-4 border border-gray-600 hover:bg-gray-700/70 transition-colors">
											<div class="flex items-start justify-between">
												<div class="flex-1">
													<h5 class="font-medium text-white mb-1">{document.title || document.filename}</h5>
													<p class="text-sm text-gray-300 mb-2 line-clamp-2">{document.content_preview || 'No preview available'}</p>
													<div class="flex items-center space-x-3 text-xs text-gray-400">
														<span class="bg-blue-900/30 text-blue-400 px-2 py-1 rounded">{document.document_type}</span>
														<span>Score: {document.relevance_score}</span>
													</div>
												</div>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Notes -->
						{#if knowledgeContent.notes && knowledgeContent.notes.length > 0}
							<div>
								<h4 class="text-md font-semibold text-white mb-3 flex items-center space-x-2">
									<svg class="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
									</svg>
									<span>Related Notes ({knowledgeContent.notes.length})</span>
								</h4>
								<div class="space-y-3">
									{#each knowledgeContent.notes as note}
										<div class="bg-gray-700/50 rounded-lg p-4 border border-gray-600 hover:bg-gray-700/70 transition-colors">
											<h5 class="font-medium text-white mb-2">{note.title}</h5>
											<p class="text-sm text-gray-300 mb-2 line-clamp-3">{note.content}</p>
											<div class="flex items-center justify-between text-xs text-gray-400">
												<div class="flex items-center space-x-2">
													<span class="bg-yellow-900/30 text-yellow-400 px-2 py-1 rounded">{note.category}</span>
													<span>Score: {note.relevance_score}</span>
												</div>
												<span>{new Date(note.updated_at).toLocaleDateString()}</span>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/if}
						
						<!-- Open Source Integrations -->
						{#if knowledgeContent.open_source_integrations && knowledgeContent.open_source_integrations.length > 0}
							<div>
								<h4 class="text-md font-semibold text-white mb-3 flex items-center space-x-2">
									<svg class="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
									</svg>
									<span>Relevant Open Source Tools ({knowledgeContent.open_source_integrations.length})</span>
								</h4>
								<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
									{#each knowledgeContent.open_source_integrations as integration}
										<div class="bg-gray-700/50 rounded-lg p-4 border border-gray-600 hover:bg-gray-700/70 transition-colors">
											<div class="flex items-start justify-between mb-2">
												<h5 class="font-medium text-white">{integration.name}</h5>
												<span class="text-xs bg-indigo-900/30 text-indigo-400 px-2 py-1 rounded">
													{integration.category}
												</span>
											</div>
											<p class="text-sm text-gray-300 mb-3">{integration.description}</p>
											
											{#if integration.matched_use_cases && integration.matched_use_cases.length > 0}
												<div class="mb-3">
													<span class="text-xs text-gray-400">Matching use cases:</span>
													<div class="flex flex-wrap gap-1 mt-1">
														{#each integration.matched_use_cases as useCase}
															<span class="text-xs bg-green-900/30 text-green-400 px-2 py-1 rounded">
																{useCase}
															</span>
														{/each}
													</div>
												</div>
											{/if}
											
											<div class="flex items-center justify-between text-xs">
												<div class="flex items-center space-x-2 text-gray-400">
													<span>⭐ {integration.popularity_score || 0}</span>
													<span>Score: {integration.relevance_score?.toFixed(2) || 'N/A'}</span>
												</div>
												{#if integration.repository_url}
													<a 
														href={integration.repository_url} 
														target="_blank" 
														class="text-indigo-400 hover:text-indigo-300"
													>
														View Repo →
													</a>
												{/if}
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/if}
						
						<!-- ChatGPT Conversations -->
						{#if knowledgeContent.chatgpt_conversations && knowledgeContent.chatgpt_conversations.length > 0}
							<div>
								<h4 class="text-md font-semibold text-white mb-3 flex items-center space-x-2">
									<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
									</svg>
									<span>Related ChatGPT Discussions ({knowledgeContent.chatgpt_conversations.length})</span>
								</h4>
								<div class="space-y-4">
									{#each knowledgeContent.chatgpt_conversations as conversation}
										<div class="bg-gray-700/50 rounded-lg p-4 border border-gray-600 hover:bg-gray-700/70 transition-colors">
											<h5 class="font-medium text-white mb-2">{conversation.title}</h5>
											<p class="text-sm text-gray-300 mb-3">{conversation.summary}</p>
											
											{#if conversation.relevant_snippets && conversation.relevant_snippets.length > 0}
												<div class="mb-3">
													<span class="text-xs text-gray-400">Code examples:</span>
													<div class="space-y-2 mt-2">
														{#each conversation.relevant_snippets as snippet}
															<div class="bg-gray-800 rounded p-2">
																<div class="flex items-center justify-between mb-1">
																	<span class="text-xs text-gray-400">{snippet.language}</span>
																	{#if snippet.description}
																		<span class="text-xs text-gray-500">{snippet.description}</span>
																	{/if}
																</div>
																<pre class="text-xs text-gray-300 overflow-x-auto"><code>{snippet.code}</code></pre>
															</div>
														{/each}
													</div>
												</div>
											{/if}
											
											<div class="flex items-center justify-between text-xs text-gray-400">
												<div class="flex items-center space-x-3">
													{#if conversation.key_topics && conversation.key_topics.length > 0}
														<div class="flex items-center space-x-1">
															<span>Topics:</span>
															{#each conversation.key_topics.slice(0, 3) as topic}
																<span class="bg-emerald-900/30 text-emerald-400 px-2 py-1 rounded">
																	{topic}
																</span>
															{/each}
														</div>
													{/if}
													<span>Score: {conversation.similarity_score?.toFixed(2) || 'N/A'}</span>
												</div>
												{#if conversation.url}
													<a 
														href={conversation.url} 
														target="_blank" 
														class="text-emerald-400 hover:text-emerald-300"
													>
														View Chat →
													</a>
												{/if}
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				{:else if loadingKnowledge}
					<div class="flex items-center justify-center py-8">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
						<span class="ml-3 text-gray-300">Searching knowledge base...</span>
					</div>
				{:else}
					<div class="text-center py-8">
						<svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
						<h4 class="text-lg font-semibold text-gray-300 mb-2">No Related Content Found</h4>
						<p class="text-gray-400">
							{#if knowledgeContent?.fallback_used}
								No content found matching the repository's technologies or patterns.
							{:else}
								Searching for related videos, photos, documents, and notes in your knowledge base...
							{/if}
						</p>
					</div>
				{/if}
			</div>
		{:else}
			<div class="bg-gray-800/50 rounded-lg border border-gray-700 p-6 text-center">
				<svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
				</svg>
				<h3 class="text-lg font-semibold text-gray-300 mb-2">Analysis Not Found</h3>
				<p class="text-gray-400">The requested analysis could not be found.</p>
			</div>
		{/if}
	</div>
</div>