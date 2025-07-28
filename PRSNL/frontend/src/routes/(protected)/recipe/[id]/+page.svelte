<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import Button from '$lib/components/ui/Button.svelte';
	import { autoId } from '$lib/actions/autoId';

	const itemId = $page.params.id;

	interface Ingredient {
		name: string;
		quantity?: string;
		unit?: string;
		notes?: string;
		category?: string;
	}

	interface CookingStep {
		step_number: number;
		instruction: string;
		time_minutes?: number;
		temperature?: string;
		equipment?: string;
		tips?: string;
	}

	interface RecipeData {
		title: string;
		description?: string;
		ingredients: Ingredient[];
		steps: CookingStep[];
		prep_time_minutes?: number;
		cook_time_minutes?: number;
		total_time_minutes?: number;
		servings?: number;
		difficulty?: string;
		cuisine_type?: string;
		dietary_info: string[];
		nutritional_info: Record<string, string>;
		voice_friendly_summary?: string;
		tips_and_notes: string[];
	}

	let item: any = null;
	let recipeData: RecipeData | null = null;
	let loading = true;
	let error: string | null = null;
	let currentStep = 1;
	let completedSteps: Set<number> = new Set();
	let timers: Map<number, { remaining: number; active: boolean; interval?: number }> = new Map();
	let servingMultiplier = 1;
	let voiceMode = false;

	onMount(async () => {
		try {
			const response = await api.get(`/api/items/${itemId}`);
			item = response;
			
			// Extract recipe data from metadata
			if (item.metadata?.recipe_data) {
				recipeData = item.metadata.recipe_data;
				servingMultiplier = 1;
			} else {
				error = 'No recipe data found for this item.';
			}
		} catch (e) {
			console.error('Error loading recipe:', e);
			error = 'Failed to load recipe. Please try again.';
		} finally {
			loading = false;
		}
	});

	function adjustQuantity(quantity?: string): string {
		if (!quantity) return '';
		
		// Try to parse numeric quantities and adjust
		const numMatch = quantity.match(/^(\d+(?:\.\d+)?(?:\/\d+)?)/);
		if (numMatch) {
			const num = parseFloat(numMatch[1]);
			const adjusted = num * servingMultiplier;
			return quantity.replace(numMatch[1], adjusted.toString());
		}
		
		return quantity;
	}

	function toggleStepComplete(stepNumber: number) {
		if (completedSteps.has(stepNumber)) {
			completedSteps.delete(stepNumber);
		} else {
			completedSteps.add(stepNumber);
		}
		completedSteps = completedSteps; // Trigger reactivity
	}

	function startTimer(stepNumber: number, minutes: number) {
		if (timers.has(stepNumber)) {
			stopTimer(stepNumber);
		}

		const timer = {
			remaining: minutes * 60, // Convert to seconds
			active: true
		};

		timer.interval = setInterval(() => {
			timer.remaining--;
			if (timer.remaining <= 0) {
				timer.active = false;
				clearInterval(timer.interval);
				// Could add notification here
				alert(`Timer for step ${stepNumber} finished!`);
			}
			timers = timers; // Trigger reactivity
		}, 1000);

		timers.set(stepNumber, timer);
		timers = timers;
	}

	function stopTimer(stepNumber: number) {
		const timer = timers.get(stepNumber);
		if (timer?.interval) {
			clearInterval(timer.interval);
		}
		timers.delete(stepNumber);
		timers = timers;
	}

	function formatTime(seconds: number): string {
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}

	function getDifficultyColor(difficulty?: string): string {
		switch (difficulty?.toLowerCase()) {
			case 'easy':
				return 'text-green-400';
			case 'medium':
				return 'text-yellow-400';
			case 'hard':
				return 'text-red-400';
			default:
				return 'text-gray-400';
		}
	}

	function speakText(text: string) {
		if ('speechSynthesis' in window) {
			const utterance = new SpeechSynthesisUtterance(text);
			utterance.rate = 0.8;
			speechSynthesis.speak(utterance);
		}
	}
</script>

<svelte:head>
	<title>{recipeData?.title || 'Recipe'} - PRSNL</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900" use:autoId>
	<div class="container mx-auto px-4 py-8">
		{#if loading}
			<div class="flex items-center justify-center min-h-96">
				<div class="animate-spin rounded-full h-32 w-32 border-b-2 border-red-500"></div>
			</div>
		{:else if error}
			<div class="glass-card p-8 text-center">
				<h1 class="text-2xl font-bold text-red-400 mb-4">Error</h1>
				<p class="text-gray-300">{error}</p>
				<Button href="/capture" class="mt-4">Go Back</Button>
			</div>
		{:else if recipeData}
			<!-- Recipe Header -->
			<div class="glass-card p-6 mb-6">
				<div class="flex justify-between items-start mb-4">
					<div>
						<h1 class="text-3xl font-bold text-white mb-2">{recipeData.title}</h1>
						{#if recipeData.description}
							<p class="text-gray-300 text-lg">{recipeData.description}</p>
						{/if}
					</div>
					<Button
						variant="outline"
						on:click={() => voiceMode = !voiceMode}
						class="ml-4"
					>
						{voiceMode ? '🔇' : '🔊'} Voice Mode
					</Button>
				</div>

				<!-- Recipe Meta Info -->
				<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
					{#if recipeData.prep_time_minutes}
						<div class="text-center">
							<div class="text-2xl font-bold text-green-400">{recipeData.prep_time_minutes}min</div>
							<div class="text-sm text-gray-400">Prep Time</div>
						</div>
					{/if}
					{#if recipeData.cook_time_minutes}
						<div class="text-center">
							<div class="text-2xl font-bold text-orange-400">{recipeData.cook_time_minutes}min</div>
							<div class="text-sm text-gray-400">Cook Time</div>
						</div>
					{/if}
					{#if recipeData.servings}
						<div class="text-center">
							<div class="text-2xl font-bold text-blue-400">{recipeData.servings}</div>
							<div class="text-sm text-gray-400">Servings</div>
						</div>
					{/if}
					{#if recipeData.difficulty}
						<div class="text-center">
							<div class="text-2xl font-bold {getDifficultyColor(recipeData.difficulty)}">{recipeData.difficulty}</div>
							<div class="text-sm text-gray-400">Difficulty</div>
						</div>
					{/if}
				</div>

				<!-- Dietary Info -->
				{#if recipeData.dietary_info.length > 0}
					<div class="flex flex-wrap gap-2 mb-4">
						{#each recipeData.dietary_info as diet}
							<span class="px-3 py-1 bg-green-600/20 text-green-400 rounded-full text-sm border border-green-600/30">
								{diet}
							</span>
						{/each}
					</div>
				{/if}

				<!-- Serving Size Adjuster -->
				{#if recipeData.servings}
					<div class="flex items-center gap-4 mt-4">
						<span class="text-gray-300">Adjust servings:</span>
						<div class="flex items-center gap-2">
							<Button
								variant="outline"
								size="sm"
								on:click={() => servingMultiplier = Math.max(0.5, servingMultiplier - 0.5)}
							>
								-
							</Button>
							<span class="text-white font-bold min-w-12 text-center">
								{recipeData.servings * servingMultiplier}
							</span>
							<Button
								variant="outline"
								size="sm"
								on:click={() => servingMultiplier += 0.5}
							>
								+
							</Button>
						</div>
					</div>
				{/if}
			</div>

			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<!-- Ingredients Panel -->
				<div class="lg:col-span-1">
					<div class="glass-card p-6 sticky top-4">
						<h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
							🥘 Ingredients
							{#if voiceMode}
								<Button
									variant="ghost"
									size="sm"
									on:click={() => speakText(recipeData.ingredients.map(ing => `${adjustQuantity(ing.quantity)} ${ing.unit || ''} ${ing.name}`).join(', '))}
								>
									🔊
								</Button>
							{/if}
						</h2>
						
						<div class="space-y-3">
							{#each recipeData.ingredients as ingredient, i}
								<label class="flex items-start gap-3 cursor-pointer group">
									<input
										type="checkbox"
										class="mt-1 h-4 w-4 rounded border-gray-600 bg-gray-800 text-red-500 focus:ring-red-500"
									/>
									<div class="flex-1">
										<div class="text-white group-hover:text-red-300 transition-colors">
											{#if ingredient.quantity}
												<span class="font-semibold text-red-400">
													{adjustQuantity(ingredient.quantity)}
													{ingredient.unit || ''}
												</span>
											{/if}
											{ingredient.name}
										</div>
										{#if ingredient.notes}
											<div class="text-sm text-gray-400 mt-1">
												{ingredient.notes}
											</div>
										{/if}
									</div>
								</label>
							{/each}
						</div>

						{#if recipeData.nutritional_info && Object.keys(recipeData.nutritional_info).length > 0}
							<div class="mt-6 pt-4 border-t border-gray-700">
								<h3 class="text-lg font-semibold text-white mb-2">Nutrition</h3>
								<div class="grid grid-cols-2 gap-2 text-sm">
									{#each Object.entries(recipeData.nutritional_info) as [key, value]}
										<div class="flex justify-between">
											<span class="text-gray-400 capitalize">{key}:</span>
											<span class="text-white">{value}</span>
										</div>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				</div>

				<!-- Cooking Instructions -->
				<div class="lg:col-span-2">
					<div class="glass-card p-6">
						<h2 class="text-xl font-bold text-white mb-6 flex items-center gap-2">
							👨‍🍳 Instructions
							{#if voiceMode && recipeData.voice_friendly_summary}
								<Button
									variant="ghost"
									size="sm"
									on:click={() => speakText(recipeData.voice_friendly_summary)}
								>
									🔊 Summary
								</Button>
							{/if}
						</h2>

						<div class="space-y-6">
							{#each recipeData.steps as step}
								<div class="flex gap-4 group">
									<!-- Step Number -->
									<div class="flex-shrink-0">
										<button
											class="w-10 h-10 rounded-full border-2 flex items-center justify-center font-bold transition-all
												{completedSteps.has(step.step_number) 
													? 'bg-green-500 border-green-500 text-white' 
													: 'border-red-500 text-red-400 hover:bg-red-500/10'
												}"
											on:click={() => toggleStepComplete(step.step_number)}
										>
											{completedSteps.has(step.step_number) ? '✓' : step.step_number}
										</button>
									</div>

									<!-- Step Content -->
									<div class="flex-1">
										<div class="text-white text-lg leading-relaxed mb-2 
											{completedSteps.has(step.step_number) ? 'line-through opacity-60' : ''}">
											{step.instruction}
										</div>

										<!-- Step Meta Info -->
										<div class="flex flex-wrap gap-4 text-sm text-gray-400 mb-2">
											{#if step.time_minutes}
												<div class="flex items-center gap-1">
													⏱️ {step.time_minutes} min
													{#if !timers.has(step.step_number)}
														<Button
															variant="ghost"
															size="sm"
															on:click={() => startTimer(step.step_number, step.time_minutes)}
															class="ml-2 text-xs"
														>
															Start Timer
														</Button>
													{/if}
												</div>
											{/if}
											{#if step.temperature}
												<div class="flex items-center gap-1">
													🌡️ {step.temperature}
												</div>
											{/if}
											{#if step.equipment}
												<div class="flex items-center gap-1">
													🔧 {step.equipment}
												</div>
											{/if}
										</div>

										<!-- Timer Display -->
										{#if timers.has(step.step_number)}
											{@const timer = timers.get(step.step_number)}
											<div class="bg-red-600/20 border border-red-600/30 rounded-lg p-3 mb-2">
												<div class="flex items-center justify-between">
													<span class="text-red-400 font-bold">
														Timer: {formatTime(timer.remaining)}
													</span>
													<Button
														variant="ghost"
														size="sm"
														on:click={() => stopTimer(step.step_number)}
													>
														Stop
													</Button>
												</div>
											</div>
										{/if}

										<!-- Step Tips -->
										{#if step.tips}
											<div class="bg-blue-600/10 border border-blue-600/20 rounded-lg p-3 mb-2">
												<div class="text-blue-300 text-sm">
													💡 <strong>Tip:</strong> {step.tips}
												</div>
											</div>
										{/if}

										<!-- Voice Controls -->
										{#if voiceMode}
											<Button
												variant="ghost"
												size="sm"
												on:click={() => speakText(step.instruction)}
												class="text-xs"
											>
												🔊 Read Step
											</Button>
										{/if}
									</div>
								</div>
							{/each}
						</div>

						<!-- Progress Indicator -->
						<div class="mt-8 pt-6 border-t border-gray-700">
							<div class="flex justify-between items-center mb-2">
								<span class="text-gray-400">Progress</span>
								<span class="text-white">
									{completedSteps.size} / {recipeData.steps.length} steps
								</span>
							</div>
							<div class="w-full bg-gray-700 rounded-full h-2">
								<div
									class="bg-red-500 h-2 rounded-full transition-all duration-300"
									style="width: {(completedSteps.size / recipeData.steps.length) * 100}%"
								></div>
							</div>
						</div>
					</div>

					<!-- Tips and Notes -->
					{#if recipeData.tips_and_notes.length > 0}
						<div class="glass-card p-6 mt-6">
							<h3 class="text-lg font-bold text-white mb-4">💡 Tips & Notes</h3>
							<div class="space-y-2">
								{#each recipeData.tips_and_notes as tip}
									<div class="text-gray-300 leading-relaxed">
										• {tip}
									</div>
								{/each}
							</div>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	.glass-card {
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 1rem;
		backdrop-filter: blur(10px);
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
	}
</style>