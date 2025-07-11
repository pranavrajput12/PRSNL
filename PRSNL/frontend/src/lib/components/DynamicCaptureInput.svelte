<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { contentTypes } from '$lib/stores/contentTypes';
  import Icon from '$lib/components/Icon.svelte';
  import TagAutocomplete from '$lib/components/TagAutocomplete.svelte';
  import FileUpload from '$lib/components/FileUpload.svelte';

  export let contentType = 'auto';
  export let isSubmitting = false;
  export let url = '';
  export let title = '';
  export let content = '';
  export let highlight = '';
  export let tags: string[] = [];
  export let programmingLanguage = '';
  export let projectCategory = '';
  export let difficultyLevel = 2;

  const dispatch = createEventDispatcher();

  let primaryInput: HTMLInputElement | HTMLTextAreaElement;
  let isTransitioning = false;

  // Reactive variable for primary field binding without circular dependency
  let primaryFieldValue = '';

  // Update primaryFieldValue when url or content changes, but only in one direction
  $: {
    if (config.primaryField === 'url') {
      primaryFieldValue = url;
    } else {
      primaryFieldValue = content;
    }
  }

  // Handle changes from the input back to the appropriate variable
  function handlePrimaryFieldChange() {
    if (config.primaryField === 'url') {
      url = primaryFieldValue;
    } else {
      content = primaryFieldValue;
    }
  }

  // Input configuration based on content type
  interface InputConfig {
    primaryField: 'url' | 'content' | 'file_upload';
    placeholder: string;
    visibleFields: string[];
    inputType: 'input' | 'textarea' | 'file';
    rows?: number;
  }

  const INPUT_CONFIGS: Record<string, InputConfig> = {
    auto: {
      primaryField: 'url',
      placeholder: 'Enter URL or paste content...',
      visibleFields: ['url', 'title', 'highlight', 'tags', 'ai_processing'],
      inputType: 'input',
    },
    note: {
      primaryField: 'content',
      placeholder: 'Write your note or thought...',
      visibleFields: ['content', 'title', 'highlight', 'tags', 'ai_processing'],
      inputType: 'textarea',
      rows: 6,
    },
    development: {
      primaryField: 'content',
      placeholder: 'Write documentation or paste code...',
      visibleFields: [
        'content',
        'title',
        'programming_language',
        'project_category',
        'difficulty_level',
        'highlight',
        'tags',
      ],
      inputType: 'textarea',
      rows: 8,
    },
    document: {
      primaryField: 'file_upload',
      placeholder: 'Upload document or enter URL...',
      visibleFields: ['file_upload', 'url', 'title', 'highlight', 'tags'],
      inputType: 'file',
    },
    video: {
      primaryField: 'url',
      placeholder: 'Enter video URL (YouTube, Vimeo, etc.)',
      visibleFields: ['url', 'title', 'highlight', 'tags', 'ai_processing'],
      inputType: 'input',
    },
    article: {
      primaryField: 'url',
      placeholder: 'Enter article URL',
      visibleFields: ['url', 'title', 'highlight', 'tags', 'ai_processing'],
      inputType: 'input',
    },
    image: {
      primaryField: 'file_upload',
      placeholder: 'Upload image or enter URL...',
      visibleFields: ['file_upload', 'url', 'title', 'highlight', 'tags'],
      inputType: 'file',
    },
  };

  $: config = INPUT_CONFIGS[contentType] || INPUT_CONFIGS['auto'];

  // Programming languages for development content
  const PROGRAMMING_LANGUAGES = [
    'JavaScript',
    'TypeScript',
    'Python',
    'Java',
    'Go',
    'Rust',
    'C++',
    'C#',
    'PHP',
    'Ruby',
    'Swift',
    'Kotlin',
    'Dart',
    'HTML',
    'CSS',
    'SQL',
    'Shell',
    'Other',
  ];

  // Project categories for development content
  const PROJECT_CATEGORIES = [
    'Documentation',
    'Frontend',
    'Backend',
    'DevOps',
    'Mobile',
    'Data Science',
    'AI/ML',
    'Tutorials',
    'Code Snippets',
    'Project Notes',
    'Learning Paths',
  ];

  // Watch for content type changes and trigger transition
  let previousContentType = contentType;
  $: if (contentType !== previousContentType) {
    transitionInterface(previousContentType, contentType);
    previousContentType = contentType;
  }

  async function transitionInterface(fromType: string, toType: string) {
    if (fromType === toType) return;

    isTransitioning = true;

    // Trigger electrical animation
    triggerElectricalAnimation();

    // Wait for animation
    await new Promise((resolve) => setTimeout(resolve, 300));

    // Focus on primary field after transition
    setTimeout(() => {
      primaryInput?.focus();
      isTransitioning = false;
    }, 100);
  }

  function triggerElectricalAnimation() {
    // Add electrical spark effect
    const spark = document.createElement('div');
    spark.className = 'electrical-transition-spark';
    spark.innerHTML = '⚡';
    document.body.appendChild(spark);

    setTimeout(() => {
      spark.remove();
    }, 600);
  }

  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement | HTMLTextAreaElement;
    if (config.primaryField === 'url') {
      url = target.value;
    } else if (config.primaryField === 'content') {
      content = target.value;
    }
    dispatch('input', { field: config.primaryField, value: target.value });
  }

  function handleTagsUpdate(event: CustomEvent) {
    tags = event.detail;
    dispatch('tagsUpdate', tags);
  }

  function handleFileUpload(event: CustomEvent) {
    dispatch('fileUpload', event.detail);
  }

  function shouldShowField(fieldName: string): boolean {
    return config.visibleFields.includes(fieldName);
  }
</script>

<div class="dynamic-capture-input" class:transitioning={isTransitioning}>
  <!-- Primary Input Field -->
  <div class="primary-input-container" class:visible={shouldShowField(config.primaryField)}>
    {#if config.inputType === 'input'}
      <input
        bind:this={primaryInput}
        bind:value={primaryFieldValue}
        on:input={handlePrimaryFieldChange}
        type="text"
        class="terminal-input primary-input"
        placeholder={config.placeholder}
        disabled={isSubmitting}
      />
    {:else if config.inputType === 'textarea'}
      <textarea
        bind:this={primaryInput}
        bind:value={primaryFieldValue}
        on:input={handlePrimaryFieldChange}
        class="terminal-textarea primary-input"
        placeholder={config.placeholder}
        rows={config.rows || 6}
        disabled={isSubmitting}
      ></textarea>
    {:else if config.inputType === 'file'}
      <div class="file-upload-container">
        <FileUpload
          {contentType}
          multiple={false}
          disabled={isSubmitting}
          on:files={handleFileUpload}
        />
        {#if shouldShowField('url')}
          <input
            bind:value={url}
            type="text"
            class="terminal-input secondary-input"
            placeholder="Or enter URL..."
            disabled={isSubmitting}
            on:input={handleInput}
          />
        {/if}
      </div>
    {/if}
  </div>

  <!-- Development-specific fields -->
  {#if contentType === 'development'}
    <div class="development-fields" class:visible={shouldShowField('programming_language')}>
      <div class="field-row">
        <div class="field-group">
          <label for="programming-language">Programming Language</label>
          <select
            id="programming-language"
            bind:value={programmingLanguage}
            class="terminal-select"
            disabled={isSubmitting}
          >
            <option value="">Auto-detect</option>
            {#each PROGRAMMING_LANGUAGES as lang}
              <option value={lang.toLowerCase()}>{lang}</option>
            {/each}
          </select>
        </div>

        <div class="field-group">
          <label for="project-category">Category</label>
          <select
            id="project-category"
            bind:value={projectCategory}
            class="terminal-select"
            disabled={isSubmitting}
          >
            <option value="">Select category</option>
            {#each PROJECT_CATEGORIES as category}
              <option value={category}>{category}</option>
            {/each}
          </select>
        </div>

        <div class="field-group">
          <label for="difficulty-level">Difficulty</label>
          <select
            id="difficulty-level"
            bind:value={difficultyLevel}
            class="terminal-select"
            disabled={isSubmitting}
          >
            <option value={1}>1 - Beginner</option>
            <option value={2}>2 - Intermediate</option>
            <option value={3}>3 - Advanced</option>
            <option value={4}>4 - Expert</option>
            <option value={5}>5 - Master</option>
          </select>
        </div>
      </div>
    </div>
  {/if}

  <!-- Common metadata fields -->
  <div class="metadata-fields">
    {#if shouldShowField('title')}
      <input
        bind:value={title}
        type="text"
        class="terminal-input metadata-input"
        placeholder="Title (auto-generated if empty)"
        disabled={isSubmitting}
      />
    {/if}

    {#if shouldShowField('highlight')}
      <textarea
        bind:value={highlight}
        class="terminal-textarea metadata-input"
        placeholder="Highlight or notes"
        rows="3"
        disabled={isSubmitting}
      ></textarea>
    {/if}

    {#if shouldShowField('tags')}
      <TagAutocomplete
        value=""
        placeholder="Tags: #tech #ai #neural"
        disabled={isSubmitting}
        on:tags={handleTagsUpdate}
      />
    {/if}
  </div>
</div>

<style>
  .dynamic-capture-input {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .dynamic-capture-input.transitioning {
    opacity: 0.7;
    transform: scale(0.99);
  }

  .primary-input-container {
    opacity: 0;
    transform: translateY(-20px);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .primary-input-container.visible {
    opacity: 1;
    transform: translateY(0);
  }

  .terminal-input,
  .terminal-textarea,
  .terminal-select {
    width: 100%;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    border-radius: 8px;
    padding: 12px 16px;
    color: #00ff88;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.5;
    resize: vertical;
    transition: all 0.3s ease;
  }

  .terminal-input:focus,
  .terminal-textarea:focus,
  .terminal-select:focus {
    outline: none;
    border-color: #00ff88;
    box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
    background: rgba(0, 255, 136, 0.15);
  }

  .terminal-input::placeholder,
  .terminal-textarea::placeholder {
    color: rgba(0, 255, 136, 0.6);
  }

  .primary-input {
    font-size: 16px;
    min-height: 48px;
  }

  .terminal-textarea.primary-input {
    min-height: 120px;
    resize: vertical;
  }

  .file-upload-container {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .secondary-input {
    opacity: 0.8;
    font-size: 14px;
  }

  .development-fields {
    opacity: 0;
    transform: translateY(-10px);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .development-fields.visible {
    opacity: 1;
    transform: translateY(0);
  }

  .field-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
  }

  .field-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .field-group label {
    color: rgba(0, 255, 136, 0.8);
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .terminal-select {
    background: rgba(0, 255, 136, 0.1);
    cursor: pointer;
  }

  .terminal-select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .metadata-fields {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .metadata-input {
    opacity: 0.9;
  }

  /* Electrical transition animation */
  :global(.electrical-transition-spark) {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 2rem;
    z-index: 9999;
    animation: electricalSpark 0.6s ease-out;
    pointer-events: none;
  }

  @keyframes electricalSpark {
    0% {
      opacity: 0;
      transform: translate(-50%, -50%) scale(0.5);
    }
    50% {
      opacity: 1;
      transform: translate(-50%, -50%) scale(1.2);
      text-shadow:
        0 0 20px #00ff88,
        0 0 40px #00ff88;
    }
    100% {
      opacity: 0;
      transform: translate(-50%, -50%) scale(1);
    }
  }

  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .field-row {
      grid-template-columns: 1fr;
      gap: 0.75rem;
    }

    .primary-input {
      font-size: 16px; /* Prevent zoom on iOS */
    }
  }
</style>
