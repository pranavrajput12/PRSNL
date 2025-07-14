<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	
	interface Props {
		selectedRepo: any;
		show: boolean;
	}
	
	let { selectedRepo, show = $bindable() }: Props = $props();
	
	const dispatch = createEventDispatcher();
	
	let selectedType = $state('web');
	let selectedDepth = $state('standard');
	
	function selectAnalysisType(type: string) {
		selectedType = type;
	}
	
	function startAnalysis() {
		dispatch('start', {
			type: selectedType,
			depth: selectedDepth,
			repo: selectedRepo
		});
		show = false;
	}
	
	function cancel() {
		show = false;
	}
</script>

{#if show}
	<div class="modal-overlay" onclick={cancel}>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<h2>Choose Analysis Method</h2>
				<button class="close-btn" onclick={cancel}>×</button>
			</div>
			
			<div class="analysis-types">
				<!-- Web-based Analysis -->
				<div 
					class="analysis-option {selectedType === 'web' ? 'selected' : ''}"
					onclick={() => selectAnalysisType('web')}
				>
					<div class="option-header">
						<div class="option-icon web">🌐</div>
						<div class="option-title">
							<h3>Web-Based Analysis</h3>
							<span class="badge recommended">Recommended</span>
						</div>
					</div>
					<div class="option-features">
						<div class="feature">✓ Direct GitHub integration</div>
						<div class="feature">✓ No local setup required</div>
						<div class="feature">✓ Real-time progress updates</div>
						<div class="feature">✓ Automatic pattern detection</div>
					</div>
					<div class="option-timing">
						<span class="timing-icon">⏱️</span>
						<span>2-10 minutes depending on repo size</span>
					</div>
				</div>
				
				<!-- CLI Analysis -->
				<div 
					class="analysis-option {selectedType === 'cli' ? 'selected' : ''}"
					onclick={() => selectAnalysisType('cli')}
				>
					<div class="option-header">
						<div class="option-icon cli">🖥️</div>
						<div class="option-title">
							<h3>CLI Analysis</h3>
							<span class="badge advanced">Advanced</span>
						</div>
					</div>
					<div class="option-features">
						<div class="feature">✓ Works with private/local repos</div>
						<div class="feature">✓ Offline analysis capability</div>
						<div class="feature">✓ More control over process</div>
						<div class="feature">✓ Custom pattern rules</div>
					</div>
					<div class="option-timing">
						<span class="timing-icon">⏱️</span>
						<span>1-5 minutes + manual upload</span>
					</div>
				</div>
			</div>
			
			<!-- Depth Selection -->
			<div class="depth-selection">
				<h3>Analysis Depth</h3>
				<div class="depth-options">
					<label class="depth-option">
						<input 
							type="radio" 
							name="depth" 
							value="quick"
							bind:group={selectedDepth}
						/>
						<div class="depth-content">
							<strong>⚡ Quick</strong>
							<span>Basic structure & README analysis</span>
						</div>
					</label>
					
					<label class="depth-option">
						<input 
							type="radio" 
							name="depth" 
							value="standard"
							bind:group={selectedDepth}
						/>
						<div class="depth-content">
							<strong>🔍 Standard</strong>
							<span>Patterns, dependencies & quality metrics</span>
						</div>
					</label>
					
					<label class="depth-option">
						<input 
							type="radio" 
							name="depth" 
							value="deep"
							bind:group={selectedDepth}
						/>
						<div class="depth-content">
							<strong>🧠 Deep</strong>
							<span>Full architecture & learning recommendations</span>
						</div>
					</label>
				</div>
			</div>
			
			<!-- CLI Instructions (shown when CLI is selected) -->
			{#if selectedType === 'cli'}
				<div class="cli-instructions">
					<h4>CLI Instructions:</h4>
					<ol>
						<li>Install the CLI tool (see CLI tab for details)</li>
						<li>Run: <code>prsnl-codemirror audit {selectedRepo?.full_name || '/path/to/repo'} --depth {selectedDepth} --upload</code></li>
						<li>The analysis will automatically sync to your dashboard</li>
					</ol>
				</div>
			{/if}
			
			<!-- Action Buttons -->
			<div class="modal-actions">
				<button class="btn-secondary" onclick={cancel}>Cancel</button>
				{#if selectedType === 'web'}
					<button class="btn-primary" onclick={startAnalysis}>
						Start Analysis
					</button>
				{:else}
					<button class="btn-primary" onclick={() => dispatch('showCLI')}>
						View CLI Instructions
					</button>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.7);
		backdrop-filter: blur(4px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		animation: fadeIn 0.2s ease-out;
	}
	
	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
	
	.modal-content {
		background: var(--surface-2);
		border: 1px solid var(--border);
		border-radius: 12px;
		max-width: 800px;
		width: 90%;
		max-height: 90vh;
		overflow-y: auto;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
		animation: slideUp 0.3s ease-out;
	}
	
	@keyframes slideUp {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		border-bottom: 1px solid var(--border);
	}
	
	.modal-header h2 {
		margin: 0;
		font-size: 1.5rem;
		color: var(--text-primary);
	}
	
	.close-btn {
		background: none;
		border: none;
		font-size: 1.5rem;
		color: var(--text-secondary);
		cursor: pointer;
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 4px;
		transition: all 0.2s;
	}
	
	.close-btn:hover {
		background: var(--surface-3);
		color: var(--text-primary);
	}
	
	.analysis-types {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		padding: 1.5rem;
	}
	
	.analysis-option {
		background: var(--surface-3);
		border: 2px solid var(--border);
		border-radius: 8px;
		padding: 1.5rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.analysis-option:hover {
		border-color: var(--primary);
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
	}
	
	.analysis-option.selected {
		border-color: var(--primary);
		background: rgba(59, 130, 246, 0.1);
	}
	
	.option-header {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		margin-bottom: 1rem;
	}
	
	.option-icon {
		font-size: 2.5rem;
		width: 60px;
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 12px;
	}
	
	.option-icon.web {
		background: rgba(59, 130, 246, 0.2);
	}
	
	.option-icon.cli {
		background: rgba(168, 85, 247, 0.2);
	}
	
	.option-title h3 {
		margin: 0 0 0.25rem 0;
		font-size: 1.125rem;
		color: var(--text-primary);
	}
	
	.badge {
		display: inline-block;
		padding: 0.25rem 0.75rem;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 600;
	}
	
	.badge.recommended {
		background: rgba(34, 197, 94, 0.2);
		color: #22c55e;
	}
	
	.badge.advanced {
		background: rgba(168, 85, 247, 0.2);
		color: #a855f7;
	}
	
	.option-features {
		margin-bottom: 1rem;
	}
	
	.feature {
		font-size: 0.875rem;
		color: var(--text-secondary);
		margin-bottom: 0.5rem;
	}
	
	.option-timing {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		color: var(--text-secondary);
		padding-top: 0.75rem;
		border-top: 1px solid var(--border);
	}
	
	.timing-icon {
		font-size: 1rem;
	}
	
	/* Depth Selection */
	.depth-selection {
		padding: 0 1.5rem 1.5rem;
	}
	
	.depth-selection h3 {
		margin: 0 0 1rem 0;
		font-size: 1.125rem;
		color: var(--text-primary);
	}
	
	.depth-options {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.75rem;
	}
	
	.depth-option {
		display: block;
		cursor: pointer;
	}
	
	.depth-option input {
		display: none;
	}
	
	.depth-content {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		padding: 1rem;
		background: var(--surface-3);
		border: 2px solid var(--border);
		border-radius: 8px;
		transition: all 0.2s;
		text-align: center;
	}
	
	.depth-option input:checked + .depth-content {
		border-color: var(--primary);
		background: rgba(59, 130, 246, 0.1);
	}
	
	.depth-content strong {
		color: var(--text-primary);
		font-size: 0.875rem;
	}
	
	.depth-content span {
		font-size: 0.75rem;
		color: var(--text-secondary);
	}
	
	/* CLI Instructions */
	.cli-instructions {
		margin: 0 1.5rem 1.5rem;
		padding: 1rem;
		background: rgba(168, 85, 247, 0.1);
		border: 1px solid rgba(168, 85, 247, 0.3);
		border-radius: 8px;
	}
	
	.cli-instructions h4 {
		margin: 0 0 0.75rem 0;
		color: #a855f7;
		font-size: 0.875rem;
	}
	
	.cli-instructions ol {
		margin: 0;
		padding-left: 1.5rem;
		color: var(--text-secondary);
		font-size: 0.875rem;
	}
	
	.cli-instructions li {
		margin-bottom: 0.5rem;
	}
	
	.cli-instructions code {
		background: var(--surface-4);
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
		font-size: 0.8rem;
		color: #60a5fa;
	}
	
	/* Modal Actions */
	.modal-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.75rem;
		padding: 1.5rem;
		border-top: 1px solid var(--border);
	}
	
	.btn-secondary,
	.btn-primary {
		padding: 0.75rem 1.5rem;
		border-radius: 6px;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		border: none;
		font-size: 0.875rem;
	}
	
	.btn-secondary {
		background: var(--surface-3);
		color: var(--text-primary);
		border: 1px solid var(--border);
	}
	
	.btn-secondary:hover {
		background: var(--surface-4);
	}
	
	.btn-primary {
		background: var(--primary);
		color: white;
	}
	
	.btn-primary:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}
	
	/* Responsive */
	@media (max-width: 768px) {
		.analysis-types {
			grid-template-columns: 1fr;
		}
		
		.depth-options {
			grid-template-columns: 1fr;
		}
		
		.modal-content {
			width: 95%;
			margin: 1rem;
		}
	}
</style>