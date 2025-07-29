<!--
  Recipe View Component
  
  Specialized component for displaying recipe content with ingredients,
  steps, cooking times, and other recipe-specific features.
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import { formatDate } from '$lib/utils/date';
  
  export let item: any;
  export let contentType: any;
  
  const dispatch = createEventDispatcher();
  
  // Extract recipe data - could be in metadata or as separate fields
  $: recipeData = item.metadata?.recipe_data || item.recipe_data || {};
  $: ingredients = recipeData.ingredients || [];
  $: steps = recipeData.steps || [];
  $: hasNutrition = recipeData.nutritional_info && Object.keys(recipeData.nutritional_info).length > 0;
  $: hasDietaryInfo = recipeData.dietary_info && recipeData.dietary_info.length > 0;
  $: hasTips = recipeData.tips_and_notes && recipeData.tips_and_notes.length > 0;
  
  // Step tracking for cooking mode
  let currentStep = 1;
  let completedSteps = new Set();
  let cookingMode = false;
  
  function toggleStep(stepNumber: number) {
    if (completedSteps.has(stepNumber)) {
      completedSteps.delete(stepNumber);
    } else {
      completedSteps.add(stepNumber);
    }
    completedSteps = completedSteps; // Trigger reactivity
  }
  
  function toggleCookingMode() {
    cookingMode = !cookingMode;
    if (cookingMode) {
      currentStep = 1;
      completedSteps.clear();
    }
  }
  
  function nextStep() {
    if (currentStep < steps.length) {
      completedSteps.add(currentStep);
      currentStep++;
      completedSteps = completedSteps;
    }
  }
  
  function previousStep() {
    if (currentStep > 1) {
      currentStep--;
    }
  }
  
  function handleError(error: any) {
    dispatch('error', error);
  }
</script>

<div class="recipe-view">
  <!-- Recipe Header -->
  <section class="recipe-header">
    <div class="recipe-meta">
      {#if recipeData.prep_time_minutes}
        <div class="meta-item">
          <Icon name="clock" size="small" />
          <span class="meta-label">Prep Time</span>
          <span class="meta-value">{recipeData.prep_time_minutes} min</span>
        </div>
      {/if}
      
      {#if recipeData.cook_time_minutes}
        <div class="meta-item">
          <Icon name="flame" size="small" />
          <span class="meta-label">Cook Time</span>
          <span class="meta-value">{recipeData.cook_time_minutes} min</span>
        </div>
      {/if}
      
      {#if recipeData.servings}
        <div class="meta-item">
          <Icon name="users" size="small" />
          <span class="meta-label">Servings</span>
          <span class="meta-value">{recipeData.servings}</span>
        </div>
      {/if}
      
      {#if recipeData.difficulty}
        <div class="meta-item">
          <Icon name="bar-chart" size="small" />
          <span class="meta-label">Difficulty</span>
          <span class="meta-value difficulty-{recipeData.difficulty.toLowerCase()}">{recipeData.difficulty}</span>
        </div>
      {/if}
    </div>
    
    <!-- Dietary Information -->
    {#if hasDietaryInfo}
      <div class="dietary-info">
        {#each recipeData.dietary_info as diet}
          <span class="dietary-badge">{diet}</span>
        {/each}
      </div>
    {/if}
    
    <!-- Cooking Mode Toggle -->
    <div class="cooking-mode-toggle">
      <button 
        class="cooking-mode-btn {cookingMode ? 'active' : ''}"
        on:click={toggleCookingMode}
      >
        <Icon name="play-circle" size="small" />
        {cookingMode ? 'Exit Cooking Mode' : 'Enter Cooking Mode'}
      </button>
    </div>
  </section>
  
  <!-- Recipe Description -->
  {#if recipeData.description || item.summary}
    <section class="recipe-description">
      <h2>Description</h2>
      <p>{recipeData.description || item.summary}</p>
    </section>
  {/if}
  
  <div class="recipe-content" class:cooking-mode>
    <!-- Ingredients Section -->
    {#if ingredients.length > 0}
      <section class="ingredients-section">
        <h2>🥘 Ingredients</h2>
        <ul class="ingredients-list">
          {#each ingredients as ingredient, index}
            <li class="ingredient-item">
              <div class="ingredient-checkbox">
                <input 
                  type="checkbox" 
                  id="ingredient-{index}"
                  bind:checked={ingredient.checked}
                />
                <label for="ingredient-{index}"></label>
              </div>
              <div class="ingredient-content">
                {#if ingredient.quantity}
                  <span class="ingredient-quantity">{ingredient.quantity} {ingredient.unit || ''}</span>
                {/if}
                <span class="ingredient-name">{ingredient.name}</span>
                {#if ingredient.notes}
                  <span class="ingredient-notes">({ingredient.notes})</span>
                {/if}
              </div>
            </li>
          {/each}
        </ul>
      </section>
    {/if}
    
    <!-- Instructions Section -->
    {#if steps.length > 0}
      <section class="instructions-section">
        <div class="instructions-header">
          <h2>👨‍🍳 Instructions</h2>
          {#if cookingMode}
            <div class="step-counter">
              Step {currentStep} of {steps.length}
            </div>
          {/if}
        </div>
        
        {#if cookingMode}
          <!-- Cooking Mode View - Focus on current step -->
          <div class="cooking-mode-steps">
            {#if currentStep <= steps.length}
              {@const step = steps[currentStep - 1]}
              <div class="current-step">
                <div class="step-number">{currentStep}</div>
                <div class="step-content">
                  <div class="step-instruction">{step.instruction}</div>
                  
                  {#if step.time_minutes || step.temperature || step.equipment}
                    <div class="step-meta">
                      {#if step.time_minutes}
                        <span class="step-time">⏱️ {step.time_minutes} min</span>
                      {/if}
                      {#if step.temperature}
                        <span class="step-temp">🌡️ {step.temperature}</span>
                      {/if}
                      {#if step.equipment}
                        <span class="step-equipment">🔧 {step.equipment}</span>
                      {/if}
                    </div>
                  {/if}
                  
                  {#if step.tips}
                    <div class="step-tip">
                      💡 <strong>Tip:</strong> {step.tips}
                    </div>
                  {/if}
                </div>
              </div>
              
              <div class="cooking-controls">
                <button 
                  class="control-btn secondary" 
                  on:click={previousStep}
                  disabled={currentStep === 1}
                >
                  <Icon name="chevron-left" size="small" />
                  Previous
                </button>
                
                <button 
                  class="control-btn primary" 
                  on:click={nextStep}
                  disabled={currentStep === steps.length}
                >
                  Next
                  <Icon name="chevron-right" size="small" />
                </button>
              </div>
            {:else}
              <div class="recipe-complete">
                <Icon name="check-circle" size="large" />
                <h3>Recipe Complete!</h3>
                <p>Great job! You've finished all the steps.</p>
                <button class="control-btn primary" on:click={() => currentStep = 1}>
                  Start Over
                </button>
              </div>
            {/if}
          </div>
        {:else}
          <!-- Normal View - All steps -->
          <ol class="steps-list">
            {#each steps as step, index}
              <li class="step-item">
                <div class="step-checkbox">
                  <input 
                    type="checkbox" 
                    id="step-{index + 1}"
                    checked={completedSteps.has(index + 1)}
                    on:change={() => toggleStep(index + 1)}
                  />
                  <label for="step-{index + 1}"></label>
                </div>
                
                <div class="step-content">
                  <div class="step-instruction">{step.instruction}</div>
                  
                  {#if step.time_minutes || step.temperature || step.equipment}
                    <div class="step-meta">
                      {#if step.time_minutes}
                        <span class="step-time">⏱️ {step.time_minutes} min</span>
                      {/if}
                      {#if step.temperature}
                        <span class="step-temp">🌡️ {step.temperature}</span>
                      {/if}
                      {#if step.equipment}
                        <span class="step-equipment">🔧 {step.equipment}</span>
                      {/if}
                    </div>
                  {/if}
                  
                  {#if step.tips}
                    <div class="step-tip">
                      💡 <strong>Tip:</strong> {step.tips}
                    </div>
                  {/if}
                </div>
              </li>
            {/each}
          </ol>
        {/if}
      </section>
    {/if}
  </div>
  
  <!-- Tips & Notes -->
  {#if hasTips}
    <section class="tips-section">
      <h2>💡 Tips & Notes</h2>
      <ul class="tips-list">
        {#each recipeData.tips_and_notes as tip}
          <li>{tip}</li>
        {/each}
      </ul>
    </section>
  {/if}
  
  <!-- Nutritional Information -->
  {#if hasNutrition}
    <section class="nutrition-section">
      <h2>📊 Nutritional Information</h2>
      <div class="nutrition-grid">
        {#each Object.entries(recipeData.nutritional_info) as [key, value]}
          <div class="nutrition-item">
            <span class="nutrition-label">{key}:</span>
            <span class="nutrition-value">{value}</span>
          </div>
        {/each}
      </div>
    </section>
  {/if}
</div>

<style>
  .recipe-view {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  section {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
  }
  
  h2 {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    color: var(--neural-green);
    font-weight: 600;
  }
  
  /* Recipe Header */
  .recipe-meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .meta-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    background: rgba(0, 255, 100, 0.05);
    border: 1px solid rgba(0, 255, 100, 0.2);
    border-radius: 8px;
    text-align: center;
  }
  
  .meta-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin: 0.25rem 0;
  }
  
  .meta-value {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--neural-green);
  }
  
  .difficulty-easy { color: #10b981; }
  .difficulty-medium { color: #f59e0b; }
  .difficulty-hard { color: #ef4444; }
  
  .dietary-info {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }
  
  .dietary-badge {
    padding: 0.375rem 0.75rem;
    background: rgba(0, 255, 100, 0.2);
    color: var(--neural-green);
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
  }
  
  /* Cooking Mode */
  .cooking-mode-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: linear-gradient(135deg, #dc143c, #b91c3c);
    color: white;
    border: none;
    border-radius: 25px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .cooking-mode-btn:hover {
    background: linear-gradient(135deg, #b91c3c, #991b1b);
    transform: translateY(-2px);
  }
  
  .cooking-mode-btn.active {
    background: linear-gradient(135deg, #10b981, #059669);
  }
  
  /* Recipe Content */
  .recipe-content {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 2rem;
  }
  
  .recipe-content.cooking-mode {
    grid-template-columns: 1fr;
  }
  
  /* Ingredients */
  .ingredients-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .ingredient-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .ingredient-item:last-child {
    border-bottom: none;
  }
  
  .ingredient-checkbox input[type="checkbox"] {
    appearance: none;
    width: 18px;
    height: 18px;
    border: 2px solid var(--neural-green);
    border-radius: 4px;
    position: relative;
    cursor: pointer;
  }
  
  .ingredient-checkbox input[type="checkbox"]:checked {
    background: var(--neural-green);
  }
  
  .ingredient-checkbox input[type="checkbox"]:checked::after {
    content: '✓';
    position: absolute;
    top: -1px;
    left: 2px;
    color: #000;
    font-weight: bold;
    font-size: 12px;
  }
  
  .ingredient-content {
    flex: 1;
    display: flex;
    gap: 0.5rem;
    align-items: baseline;
  }
  
  .ingredient-quantity {
    color: #dc143c;
    font-weight: 600;
    min-width: 80px;
  }
  
  .ingredient-name {
    color: var(--text-primary);
    flex: 1;
  }
  
  .ingredient-notes {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
  
  /* Instructions */
  .instructions-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .step-counter {
    background: rgba(220, 20, 60, 0.2);
    color: #dc143c;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: 600;
  }
  
  /* Normal Steps View */
  .steps-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .step-item {
    display: flex;
    gap: 1rem;
    padding: 1.5rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .step-item:last-child {
    border-bottom: none;
  }
  
  .step-checkbox input[type="checkbox"] {
    appearance: none;
    width: 20px;
    height: 20px;
    border: 2px solid var(--neural-green);
    border-radius: 50%;
    position: relative;
    cursor: pointer;
    margin-top: 0.25rem;
  }
  
  .step-checkbox input[type="checkbox"]:checked {
    background: var(--neural-green);
  }
  
  .step-checkbox input[type="checkbox"]:checked::after {
    content: '✓';
    position: absolute;
    top: -2px;
    left: 3px;
    color: #000;
    font-weight: bold;
    font-size: 12px;
  }
  
  /* Cooking Mode Steps */
  .current-step {
    display: flex;
    gap: 1.5rem;
    padding: 2rem;
    background: rgba(220, 20, 60, 0.1);
    border: 2px solid rgba(220, 20, 60, 0.3);
    border-radius: 16px;
    margin-bottom: 2rem;
  }
  
  .step-number {
    width: 3rem;
    height: 3rem;
    background: linear-gradient(135deg, #dc143c, #b91c3c);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: bold;
    flex-shrink: 0;
  }
  
  .step-content {
    flex: 1;
  }
  
  .step-instruction {
    color: var(--text-primary);
    font-size: 1.1rem;
    line-height: 1.6;
    margin-bottom: 1rem;
  }
  
  .step-meta {
    display: flex;
    gap: 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    flex-wrap: wrap;
  }
  
  .step-time,
  .step-temp,
  .step-equipment {
    color: var(--neural-green);
    background: rgba(0, 255, 100, 0.1);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
  }
  
  .step-tip {
    background: rgba(74, 158, 255, 0.1);
    border: 1px solid rgba(74, 158, 255, 0.3);
    border-radius: 8px;
    padding: 0.75rem;
    color: #4a9eff;
    font-size: 0.875rem;
    margin-top: 0.5rem;
  }
  
  /* Cooking Controls */
  .cooking-controls {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
  }
  
  .control-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 25px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .control-btn.primary {
    background: linear-gradient(135deg, #dc143c, #b91c3c);
    color: white;
  }
  
  .control-btn.secondary {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .control-btn:hover:not(:disabled) {
    transform: translateY(-2px);
  }
  
  .control-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  /* Recipe Complete */
  .recipe-complete {
    text-align: center;
    padding: 3rem 2rem;
  }
  
  .recipe-complete h3 {
    color: var(--neural-green);
    margin: 1rem 0 0.5rem 0;
    font-size: 1.5rem;
  }
  
  /* Additional Sections */
  .tips-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .tips-list li {
    padding: 0.75rem 0 0.75rem 1.5rem;
    position: relative;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
  }
  
  .tips-list li:last-child {
    border-bottom: none;
  }
  
  .tips-list li::before {
    content: '•';
    position: absolute;
    left: 0;
    color: var(--neural-green);
  }
  
  .nutrition-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
  }
  
  .nutrition-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .nutrition-label {
    color: var(--text-secondary);
    text-transform: capitalize;
  }
  
  .nutrition-value {
    color: var(--text-primary);
    font-weight: 500;
  }
  
  /* Responsive */
  @media (max-width: 768px) {
    .recipe-content {
      grid-template-columns: 1fr;
    }
    
    .recipe-meta {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .current-step {
      flex-direction: column;
      gap: 1rem;
    }
    
    .cooking-controls {
      flex-direction: column;
    }
  }
</style>