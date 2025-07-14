<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	
	interface Props {
		repoId?: string;
		userId?: string;
	}
	
	let { repoId = null, userId = null }: Props = $props();
	
	// State
	let stats = $state({
		totalAnalyses: 0,
		completedAnalyses: 0,
		totalPatterns: 0,
		totalInsights: 0,
		averageQualityScore: 0,
		averageSecurityScore: 0,
		averagePerformanceScore: 0,
		languagesAnalyzed: [],
		frameworksDetected: []
	});
	
	let recentAnalyses = $state([]);
	let topPatterns = $state([]);
	let loading = $state(true);
	
	onMount(async () => {
		await loadOverviewData();
	});
	
	async function loadOverviewData() {
		loading = true;
		try {
			// Load analyses
			let analysesUrl = '/api/codemirror/analyses';
			if (repoId) {
				analysesUrl = `/api/codemirror/analyses/${repoId}`;
			}
			
			const analyses = await api.get(analysesUrl);
			
			// Calculate statistics
			if (analyses && analyses.length > 0) {
				stats.totalAnalyses = analyses.length;
				stats.completedAnalyses = analyses.filter(a => a.analysis_completed_at).length;
				
				// Calculate average scores
				const scores = {
					quality: [],
					security: [],
					performance: []
				};
				
				const languages = new Set();
				const frameworks = new Set();
				
				analyses.forEach(analysis => {
					if (analysis.quality_score) scores.quality.push(analysis.quality_score);
					if (analysis.security_score) scores.security.push(analysis.security_score);
					if (analysis.performance_score) scores.performance.push(analysis.performance_score);
					
					// Collect languages and frameworks
					if (analysis.languages_detected) {
						const langs = JSON.parse(analysis.languages_detected || '[]');
						langs.forEach(lang => languages.add(lang));
					}
					if (analysis.frameworks_detected) {
						const fws = JSON.parse(analysis.frameworks_detected || '[]');
						fws.forEach(fw => frameworks.add(fw));
					}
				});
				
				stats.averageQualityScore = calculateAverage(scores.quality);
				stats.averageSecurityScore = calculateAverage(scores.security);
				stats.averagePerformanceScore = calculateAverage(scores.performance);
				stats.languagesAnalyzed = Array.from(languages);
				stats.frameworksDetected = Array.from(frameworks);
				
				// Get recent analyses
				recentAnalyses = analyses.slice(0, 5);
			}
			
			// Load patterns
			try {
				const patterns = await api.get('/api/codemirror/patterns?limit=5');
				topPatterns = patterns || [];
				stats.totalPatterns = patterns.length;
			} catch (e) {
				console.error('Failed to load patterns:', e);
			}
			
			// Count total insights from analyses
			let insightCount = 0;
			for (const analysis of analyses) {
				if (analysis.id) {
					try {
						const insights = await api.get(`/api/codemirror/insights/${analysis.id}`);
						insightCount += insights.length;
					} catch (e) {
						// Ignore individual insight loading errors
					}
				}
			}
			stats.totalInsights = insightCount;
			
		} catch (error) {
			console.error('Failed to load overview data:', error);
		} finally {
			loading = false;
		}
	}
	
	function calculateAverage(numbers: number[]): number {
		if (numbers.length === 0) return 0;
		return Math.round(numbers.reduce((a, b) => a + b, 0) / numbers.length);
	}
	
	function getScoreColor(score: number): string {
		if (score >= 80) return 'text-green-400';
		if (score >= 60) return 'text-yellow-400';
		if (score >= 40) return 'text-orange-400';
		return 'text-red-400';
	}
	
	function getScoreBackground(score: number): string {
		if (score >= 80) return 'bg-green-900/30 border-green-600/30';
		if (score >= 60) return 'bg-yellow-900/30 border-yellow-600/30';
		if (score >= 40) return 'bg-orange-900/30 border-orange-600/30';
		return 'bg-red-900/30 border-red-600/30';
	}
</script>

<div class="analysis-overview">
	{#if loading}
		<div class="loading-state">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
			<span class="ml-3">Loading analysis overview...</span>
		</div>
	{:else}
		<!-- Statistics Grid -->
		<div class="stats-grid">
			<!-- Total Analyses -->
			<div class="stat-card">
				<div class="stat-icon">
					<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
					</svg>
				</div>
				<div class="stat-content">
					<div class="stat-value">{stats.totalAnalyses}</div>
					<div class="stat-label">Total Analyses</div>
					<div class="stat-sublabel">{stats.completedAnalyses} completed</div>
				</div>
			</div>
			
			<!-- Patterns Detected -->
			<div class="stat-card">
				<div class="stat-icon patterns">
					<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
					</svg>
				</div>
				<div class="stat-content">
					<div class="stat-value">{stats.totalPatterns}</div>
					<div class="stat-label">Patterns Found</div>
					<div class="stat-sublabel">Across all repos</div>
				</div>
			</div>
			
			<!-- Insights Generated -->
			<div class="stat-card">
				<div class="stat-icon insights">
					<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
					</svg>
				</div>
				<div class="stat-content">
					<div class="stat-value">{stats.totalInsights}</div>
					<div class="stat-label">AI Insights</div>
					<div class="stat-sublabel">Actionable items</div>
				</div>
			</div>
		</div>
		
		<!-- Score Overview -->
		<div class="scores-section">
			<h3 class="section-title">Average Scores</h3>
			<div class="scores-grid">
				<!-- Security Score -->
				<div class="score-card {getScoreBackground(stats.averageSecurityScore)}">
					<div class="score-header">
						<svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
						</svg>
						<span>Security</span>
					</div>
					<div class="score-value {getScoreColor(stats.averageSecurityScore)}">
						{stats.averageSecurityScore || 'N/A'}
						{#if stats.averageSecurityScore}<span class="score-suffix">/100</span>{/if}
					</div>
					<div class="score-bar">
						<div 
							class="score-bar-fill security"
							style="width: {stats.averageSecurityScore}%"
						></div>
					</div>
				</div>
				
				<!-- Performance Score -->
				<div class="score-card {getScoreBackground(stats.averagePerformanceScore)}">
					<div class="score-header">
						<svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
						</svg>
						<span>Performance</span>
					</div>
					<div class="score-value {getScoreColor(stats.averagePerformanceScore)}">
						{stats.averagePerformanceScore || 'N/A'}
						{#if stats.averagePerformanceScore}<span class="score-suffix">/100</span>{/if}
					</div>
					<div class="score-bar">
						<div 
							class="score-bar-fill performance"
							style="width: {stats.averagePerformanceScore}%"
						></div>
					</div>
				</div>
				
				<!-- Quality Score -->
				<div class="score-card {getScoreBackground(stats.averageQualityScore)}">
					<div class="score-header">
						<svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
						</svg>
						<span>Code Quality</span>
					</div>
					<div class="score-value {getScoreColor(stats.averageQualityScore)}">
						{stats.averageQualityScore || 'N/A'}
						{#if stats.averageQualityScore}<span class="score-suffix">/100</span>{/if}
					</div>
					<div class="score-bar">
						<div 
							class="score-bar-fill quality"
							style="width: {stats.averageQualityScore}%"
						></div>
					</div>
				</div>
			</div>
		</div>
		
		<!-- Technologies Overview -->
		{#if stats.languagesAnalyzed.length > 0 || stats.frameworksDetected.length > 0}
			<div class="technologies-section">
				<h3 class="section-title">Technologies Analyzed</h3>
				<div class="tech-grid">
					{#if stats.languagesAnalyzed.length > 0}
						<div class="tech-category">
							<h4>Languages</h4>
							<div class="tech-tags">
								{#each stats.languagesAnalyzed as language}
									<span class="tech-tag language">{language}</span>
								{/each}
							</div>
						</div>
					{/if}
					
					{#if stats.frameworksDetected.length > 0}
						<div class="tech-category">
							<h4>Frameworks</h4>
							<div class="tech-tags">
								{#each stats.frameworksDetected as framework}
									<span class="tech-tag framework">{framework}</span>
								{/each}
							</div>
						</div>
					{/if}
				</div>
			</div>
		{/if}
		
		<!-- Top Patterns -->
		{#if topPatterns.length > 0}
			<div class="patterns-section">
				<h3 class="section-title">Top Patterns</h3>
				<div class="patterns-list">
					{#each topPatterns as pattern}
						<div class="pattern-item">
							<div class="pattern-info">
								<h4>{pattern.pattern_signature}</h4>
								<p>{pattern.description || `${pattern.pattern_type} pattern`}</p>
							</div>
							<div class="pattern-meta">
								<span class="occurrence-count">{pattern.occurrence_count}x</span>
								<span class="confidence">{Math.round(pattern.confidence * 100)}%</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div>

<style>
	.analysis-overview {
		padding: 1.5rem;
	}
	
	.loading-state {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 3rem;
		color: var(--text-secondary);
	}
	
	/* Statistics Grid */
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		background: var(--surface-3);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 1.5rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		transition: all 0.2s;
	}
	
	.stat-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
	}
	
	.stat-icon {
		width: 48px;
		height: 48px;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(59, 130, 246, 0.1);
		color: #3b82f6;
	}
	
	.stat-icon.patterns {
		background: rgba(168, 85, 247, 0.1);
		color: #a855f7;
	}
	
	.stat-icon.insights {
		background: rgba(236, 72, 153, 0.1);
		color: #ec4899;
	}
	
	.stat-content {
		flex: 1;
	}
	
	.stat-value {
		font-size: 2rem;
		font-weight: 700;
		color: var(--text-primary);
		line-height: 1;
	}
	
	.stat-label {
		font-size: 0.875rem;
		color: var(--text-primary);
		margin-top: 0.25rem;
	}
	
	.stat-sublabel {
		font-size: 0.75rem;
		color: var(--text-secondary);
		margin-top: 0.125rem;
	}
	
	/* Score Section */
	.scores-section {
		margin-bottom: 2rem;
	}
	
	.section-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 1rem;
	}
	
	.scores-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}
	
	.score-card {
		padding: 1rem;
		border-radius: 8px;
		border: 1px solid;
	}
	
	.score-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		color: var(--text-secondary);
		margin-bottom: 0.5rem;
	}
	
	.score-value {
		font-size: 2rem;
		font-weight: 700;
		margin-bottom: 0.5rem;
	}
	
	.score-suffix {
		font-size: 0.875rem;
		font-weight: 400;
		opacity: 0.7;
	}
	
	.score-bar {
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
		overflow: hidden;
	}
	
	.score-bar-fill {
		height: 100%;
		border-radius: 2px;
		transition: width 0.3s ease;
	}
	
	.score-bar-fill.security {
		background: #3b82f6;
	}
	
	.score-bar-fill.performance {
		background: #10b981;
	}
	
	.score-bar-fill.quality {
		background: #a855f7;
	}
	
	/* Technologies Section */
	.technologies-section {
		margin-bottom: 2rem;
	}
	
	.tech-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
	}
	
	.tech-category h4 {
		font-size: 0.875rem;
		color: var(--text-secondary);
		margin-bottom: 0.75rem;
	}
	
	.tech-tags {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
	
	.tech-tag {
		padding: 0.25rem 0.75rem;
		border-radius: 16px;
		font-size: 0.75rem;
		font-weight: 500;
	}
	
	.tech-tag.language {
		background: rgba(34, 197, 94, 0.1);
		color: #22c55e;
		border: 1px solid rgba(34, 197, 94, 0.3);
	}
	
	.tech-tag.framework {
		background: rgba(59, 130, 246, 0.1);
		color: #3b82f6;
		border: 1px solid rgba(59, 130, 246, 0.3);
	}
	
	/* Patterns Section */
	.patterns-section {
		margin-bottom: 2rem;
	}
	
	.patterns-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.pattern-item {
		background: var(--surface-3);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 1rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		transition: all 0.2s;
	}
	
	.pattern-item:hover {
		background: var(--surface-4);
		border-color: var(--primary);
	}
	
	.pattern-info h4 {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 0.25rem;
	}
	
	.pattern-info p {
		font-size: 0.75rem;
		color: var(--text-secondary);
	}
	
	.pattern-meta {
		display: flex;
		align-items: center;
		gap: 1rem;
		font-size: 0.75rem;
	}
	
	.occurrence-count {
		padding: 0.25rem 0.5rem;
		background: rgba(168, 85, 247, 0.1);
		color: #a855f7;
		border-radius: 4px;
		font-weight: 600;
	}
	
	.confidence {
		color: var(--text-secondary);
	}
</style>