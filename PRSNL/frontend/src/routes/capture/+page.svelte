<script lang="ts" type="module">
  import { onMount } from 'svelte';
  import { captureItem, getRecentTags, getAISuggestions } from '$lib/api';
  import type { CaptureRequest, ContentTypeDefinition } from '$lib/types/api';
  import { addNotification } from '$lib/stores/app';
  import { isVideoUrl, getVideoPlatform, estimateDownloadTime, formatTime } from '$lib/utils/url';
  import Spinner from '$lib/components/Spinner.svelte';
  import ErrorMessage from '$lib/components/ErrorMessage.svelte';
  import UrlPreview from '$lib/components/UrlPreview.svelte';
  import TagAutocomplete from '$lib/components/TagAutocomplete.svelte';
  import VideoPlayer from '$lib/components/VideoPlayer.svelte';
  import Icon from '$lib/components/Icon.svelte';
  import AnimatedButton from '$lib/components/AnimatedButton.svelte';
  import PremiumInteractions from '$lib/components/PremiumInteractions.svelte';
  import FileUpload from '$lib/components/FileUpload.svelte';
  import DynamicCaptureInput from '$lib/components/DynamicCaptureInput.svelte';
  import { contentTypes, getTypeIcon } from '$lib/stores/contentTypes';

  // Form fields and state
  let url = '';
  let title = '';
  let content = '';
  let highlight = '';
  let tags: string[] = [];
  let isSubmitting = false;
  let message = '';
  let messageType = '';
  let error: Error | null = null;

  // Development-specific fields
  let programmingLanguage = '';
  let projectCategory = '';
  let difficultyLevel = 2;
  let recentTags: string[] = [];
  let isLoadingTags = false;
  let isDragging = false;
  let progress = 0;
  let progressInterval: number | null = null;

  // AI suggestions state
  let isLoadingSuggestions = false;
  let suggestionsError: string | null = null;

  // Video-specific variables
  let isVideoDetected = false;
  let videoPlatform: string | null = null;
  let estimatedDownloadTimeSeconds = 0;
  let videoQuality: 'standard' | 'high' = 'high';
  let thumbnailPreviewUrl: string | null = null;

  // Focus on URL input on mount
  let urlInput: HTMLInputElement;
  let dropZone: HTMLDivElement;

  // Debounced AI suggestions timeout
  let aiSuggestionsTimeout: number | undefined;

  // Summarization toggle
  let enableSummarization = false;

  // Content type selector
  let contentType = 'auto'; // auto or any dynamic type from backend
  let availableTypes: ContentTypeDefinition[] = [];

  // File upload state
  let uploadedFiles = [];

  // Terminal state
  let currentStep = 1;
  let stepStatus = {
    1: 'active', // active, completed, pending
    2: 'pending',
    3: 'pending',
    4: 'pending',
  };
  let terminalLines: string[] = [];
  let isAnalyzing = false;

  // Watch for URL changes to detect video URLs and get AI suggestions
  $: {
    if (url) {
      detectVideoUrl(url);
      // Debounce AI suggestions
      if (url.startsWith('http://') || url.startsWith('https://')) {
        if (aiSuggestionsTimeout) clearTimeout(aiSuggestionsTimeout);
        aiSuggestionsTimeout = setTimeout(() => loadAISuggestions(url), 500);
      }
    } else {
      resetVideoDetection();
      if (aiSuggestionsTimeout) clearTimeout(aiSuggestionsTimeout);
    }
  }

  onMount(() => {
    urlInput?.focus();
    loadRecentTags();
    window.addEventListener('paste', handlePaste);
    setupDragAndDrop();

    // Initialize content types
    contentTypes.init();
    contentTypes.subscribe((types) => {
      availableTypes = types;
    });

    // Initialize terminal
    addTerminalLine('> NEURAL PROCESSING TERMINAL v3.0 INITIALIZED');
    addTerminalLine('> MEMORY TRACE CAPTURE SYSTEM: ONLINE');
    addTerminalLine('> STATUS: READY FOR INPUT...');

    return () => {
      window.removeEventListener('paste', handlePaste);
      if (progressInterval) clearInterval(progressInterval);
    };
  });

  function addTerminalLine(line: string) {
    terminalLines = [...terminalLines, line];
    // Keep only last 10 lines
    if (terminalLines.length > 10) {
      terminalLines = terminalLines.slice(-10);
    }
  }

  function updateStepStatus(
    step: number,
    status: 'active' | 'completed' | 'pending' | 'processing'
  ) {
    stepStatus = { ...stepStatus, [step]: status };
    currentStep = step;
  }

  /**
   * Detects if the URL is a video URL and updates the UI accordingly
   */
  function detectVideoUrl(urlToCheck: string): void {
    isVideoDetected = isVideoUrl(urlToCheck);

    if (isVideoDetected) {
      videoPlatform = getVideoPlatform(urlToCheck);
      estimatedDownloadTimeSeconds = estimateDownloadTime(urlToCheck);
      contentType = 'video';
      addTerminalLine(`> VIDEO DETECTED: ${videoPlatform?.toUpperCase()}`);
      addTerminalLine(`> ESTIMATED_DOWNLOAD_TIME: ${formatTime(estimatedDownloadTimeSeconds)}`);
    }

    // Auto-detect GitHub URLs and set to development
    if (urlToCheck.includes('github.com')) {
      contentType = 'development';
      addTerminalLine(`> GITHUB DETECTED: AUTO_SET_TO_DEVELOPMENT`);
      addTerminalLine(`> CONTENT_TYPE: DEVELOPMENT_SELECTED`);

      // Extract repository name from URL
      const urlParts = urlToCheck.split('/');
      if (urlParts.length >= 5) {
        const owner = urlParts[3];
        const repoName = urlParts[4];
        if (owner && repoName) {
          addTerminalLine(`> REPOSITORY: ${owner}/${repoName}`);
        }
      }
    }

    if (urlToCheck) {
      updateStepStatus(1, 'processing');
      addTerminalLine(`> SCANNING_URL: ${urlToCheck.substring(0, 50)}...`);
      setTimeout(() => {
        updateStepStatus(1, 'completed');
        updateStepStatus(2, 'active');
        addTerminalLine('> URL_ANALYSIS: COMPLETE');
      }, 1000);
    }
  }

  function resetVideoDetection(): void {
    isVideoDetected = false;
    videoPlatform = null;
    estimatedDownloadTimeSeconds = 0;
    thumbnailPreviewUrl = null;
  }

  async function loadRecentTags(): Promise<void> {
    try {
      isLoadingTags = true;
      const response = await getRecentTags();
      recentTags = response.slice(0, 10);
    } catch (err) {
      console.error('Failed to load recent tags:', err);
    } finally {
      isLoadingTags = false;
    }
  }

  async function loadAISuggestions(urlToAnalyze: string): Promise<void> {
    try {
      isLoadingSuggestions = true;
      isAnalyzing = true;
      addTerminalLine('> AI_ANALYSIS: INITIATED');

      const suggestions = await getAISuggestions(urlToAnalyze);

      if (suggestions.title && !title) {
        title = suggestions.title;
        addTerminalLine(`> TITLE_EXTRACTED: ${suggestions.title.substring(0, 30)}...`);
      }

      if (suggestions.summary && !highlight) {
        highlight = suggestions.summary;
        addTerminalLine(`> SUMMARY_EXTRACTED: ${suggestions.summary.substring(0, 50)}...`);
      }

      if (suggestions.tags && suggestions.tags.length > 0 && tags.length === 0) {
        tags = suggestions.tags.slice(0, 5);
        addTerminalLine(`> TAGS_GENERATED: ${suggestions.tags.join(', ')}`);
      }

      addTerminalLine('> AI_ANALYSIS: COMPLETE');
    } catch (err) {
      console.error('AI suggestions failed:', err);
      suggestionsError = 'AI analysis failed';
      addTerminalLine('> AI_ANALYSIS: FAILED');
    } finally {
      isLoadingSuggestions = false;
      isAnalyzing = false;
    }
  }

  function handlePaste(e: ClipboardEvent): void {
    const pastedText = e.clipboardData?.getData('text');
    if (pastedText && (pastedText.startsWith('http://') || pastedText.startsWith('https://'))) {
      url = pastedText;
      addTerminalLine('> CLIPBOARD_URL_DETECTED');
    }
  }

  function setupDragAndDrop(): void {
    // Implementation for drag and drop
  }

  function handleTagsUpdate(event: CustomEvent): void {
    tags = event.detail;
    addTerminalLine(`> TAGS_UPDATED: ${tags.join(', ')}`);
  }

  function handleFileUpload(event: CustomEvent): void {
    uploadedFiles = event.detail;
    addTerminalLine(`> FILE_UPLOADED: ${uploadedFiles.length} files`);
  }

  function handleDynamicInput(event: CustomEvent): void {
    const { field, value } = event.detail;
    if (field === 'url') {
      url = value;
      detectVideoUrl(url);
      // Debounce AI suggestions
      if (url.startsWith('http://') || url.startsWith('https://')) {
        if (aiSuggestionsTimeout) clearTimeout(aiSuggestionsTimeout);
        aiSuggestionsTimeout = setTimeout(() => loadAISuggestions(url), 500);
      }
    } else if (field === 'content') {
      content = value;
      // Auto-detect development content
      if (contentType === 'development' || contentType === 'auto') {
        autoDetectDevelopmentMetadata(value);
      }
    }
    addTerminalLine(`> INPUT_UPDATED: ${field.toUpperCase()}`);
  }

  function autoDetectDevelopmentMetadata(content: string): void {
    if (!content) return;

    const lowerContent = content.toLowerCase();

    // Detect programming language
    if (!programmingLanguage) {
      if (content.includes('import ') && content.includes('from ')) {
        programmingLanguage = 'python';
      } else if (
        content.includes('function') ||
        content.includes('const ') ||
        content.includes('let ')
      ) {
        programmingLanguage = 'javascript';
      } else if (content.includes('interface ') || content.includes('type ')) {
        programmingLanguage = 'typescript';
      } else if (content.includes('public class') || content.includes('private ')) {
        programmingLanguage = 'java';
      } else if (content.includes('func ') || content.includes('package main')) {
        programmingLanguage = 'go';
      }
    }

    // Detect project category
    if (!projectCategory) {
      if (
        lowerContent.includes('react') ||
        lowerContent.includes('vue') ||
        lowerContent.includes('frontend')
      ) {
        projectCategory = 'Frontend';
      } else if (
        lowerContent.includes('api') ||
        lowerContent.includes('server') ||
        lowerContent.includes('backend')
      ) {
        projectCategory = 'Backend';
      } else if (
        lowerContent.includes('docker') ||
        lowerContent.includes('kubernetes') ||
        lowerContent.includes('deployment')
      ) {
        projectCategory = 'DevOps';
      } else if (
        lowerContent.includes('tutorial') ||
        lowerContent.includes('guide') ||
        lowerContent.includes('how to')
      ) {
        projectCategory = 'Tutorials';
      } else {
        projectCategory = 'Documentation';
      }
    }
  }

  function selectContentType(type: string): void {
    contentType = type;
    updateStepStatus(2, 'completed');
    updateStepStatus(3, 'active');
    addTerminalLine(`> CONTENT_TYPE_SELECTED: ${type.toUpperCase()}`);
  }

  function toggleAISummarization(): void {
    enableSummarization = !enableSummarization;
    updateStepStatus(3, 'completed');
    updateStepStatus(4, 'active');
    addTerminalLine(`> AI_SUMMARIZATION: ${enableSummarization ? 'ENABLED' : 'DISABLED'}`);
  }

  async function handleSubmit(): Promise<void> {
    if (!url && !highlight && uploadedFiles.length === 0) {
      error = new Error('Please provide a URL, content, or upload a file');
      addTerminalLine('> ERROR: NO_INPUT_PROVIDED');
      return;
    }

    try {
      isSubmitting = true;
      error = null;

      addTerminalLine('> INITIATING_MEMORY_TRACE_CAPTURE...');
      startProgressAnimation();

      const captureRequest: CaptureRequest = {
        url: url || undefined,
        content: content || undefined,
        title: title || undefined,
        highlight: highlight || undefined,
        content_type: contentType,
        enable_summarization: enableSummarization,
        tags: tags.length > 0 ? tags : undefined,
        // Include uploaded files only when they exist
        uploaded_files: uploadedFiles.length > 0 ? uploadedFiles : undefined,
        // Development-specific fields
        programming_language: programmingLanguage || undefined,
        project_category: projectCategory || undefined,
        difficulty_level: difficultyLevel || undefined,
        is_career_related:
          contentType === 'development' &&
          (title?.toLowerCase().includes('career') ||
            title?.toLowerCase().includes('job') ||
            content?.toLowerCase().includes('career') ||
            content?.toLowerCase().includes('professional')),
      };

      const result = await captureItem(captureRequest);

      addTerminalLine('> MEMORY_TRACE_CAPTURED_SUCCESSFULLY');
      addTerminalLine(`> TRACE_ID: ${result.item_id}`);
      addTerminalLine('> NEURAL_NETWORK_UPDATED');

      message = 'Memory trace captured successfully!';
      messageType = 'success';

      addNotification({
        type: 'success',
        message: 'Content captured successfully!',
      });

      // Reset form
      resetForm();
    } catch (err) {
      console.error('Capture failed:', err);
      error = err as Error;
      message = `Capture failed: ${err.message}`;
      messageType = 'error';
      addTerminalLine('> ERROR: MEMORY_TRACE_CAPTURE_FAILED');
      addTerminalLine(`> ERROR_CODE: ${err.message}`);
    } finally {
      isSubmitting = false;
      if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
      }
      progress = 0;
    }
  }

  function startProgressAnimation(): void {
    progress = 0;
    progressInterval = setInterval(() => {
      if (progress < 90) {
        progress += Math.random() * 10;
      }
    }, 200);
  }

  function resetForm(): void {
    url = '';
    title = '';
    content = '';
    highlight = '';
    tags = [];
    contentType = 'auto';
    enableSummarization = false;
    uploadedFiles = [];
    // Reset development fields
    programmingLanguage = '';
    projectCategory = '';
    difficultyLevel = 2;
    currentStep = 1;
    stepStatus = {
      1: 'active',
      2: 'pending',
      3: 'pending',
      4: 'pending',
    };
    // Focus on the dynamic input component instead
    // urlInput?.focus();
  }
</script>

<svelte:head>
  <title>Ingest - Neural Processing Terminal</title>
  <meta
    name="description"
    content="Neural interface for capturing and processing memory traces into your knowledge network"
  />
</svelte:head>

<div class="neural-terminal-page">
  <!-- Neural motherboard background -->
  <div class="neural-motherboard-bg">
    <div class="pcb-traces"></div>
    <div class="circuit-nodes">
      <div class="node node-1"></div>
      <div class="node node-2"></div>
      <div class="node node-3"></div>
      <div class="node node-4"></div>
    </div>
  </div>

  <div class="terminal-container">
    <div class="terminal-header">
      <div class="terminal-title">
        <Icon name="brain" size="small" color="#00ff64" />
        NEURAL PROCESSING TERMINAL v3.0
      </div>
      <div class="terminal-controls">
        <div class="control-dot minimize"></div>
        <div class="control-dot maximize"></div>
        <div class="control-dot close"></div>
      </div>
    </div>

    <div class="terminal-body">
      <!-- System Status -->
      <div class="system-status">
        <div class="status-line">
          > NEURAL PATHWAYS: <span class="status-online">ONLINE</span>
        </div>
        <div class="status-line">
          > MEMORY BANKS: <span class="status-online">READY</span>
        </div>
        <div class="status-line">
          > AI ENHANCEMENT: <span class="status-standby">STANDBY</span>
        </div>
      </div>

      <!-- Terminal Output -->
      <div class="terminal-output">
        {#each terminalLines as line}
          <div class="terminal-line">{line}</div>
        {/each}
        <div class="terminal-line current">
          > Ready for neural interface command...<span class="cursor">_</span>
        </div>
      </div>

      <!-- Processing Steps -->
      <form on:submit|preventDefault={handleSubmit} class="processing-steps">
        <!-- Step 1: Input Source Detection -->
        <div
          class="step-section"
          class:active={currentStep === 1}
          class:completed={stepStatus[1] === 'completed'}
        >
          <div class="step-header">
            <div class="step-indicator">
              {#if stepStatus[1] === 'completed'}
                <Icon name="check" size="small" color="#00ff64" />
              {:else if stepStatus[1] === 'processing'}
                <Spinner size="small" />
              {:else}
                <span class="step-number">1</span>
              {/if}
            </div>
            <span class="step-title">[STEP 1] INPUT SOURCE DETECTION</span>
          </div>

          <div class="step-content">
            <DynamicCaptureInput
              {contentType}
              {isSubmitting}
              bind:url
              bind:title
              bind:content
              bind:highlight
              bind:tags
              bind:programmingLanguage
              bind:projectCategory
              bind:difficultyLevel
              on:input={handleDynamicInput}
              on:tagsUpdate={handleTagsUpdate}
              on:fileUpload={handleFileUpload}
            />

            {#if isLoadingSuggestions}
              <div class="input-status">
                <Spinner size="small" />
                <span>AI analyzing...</span>
              </div>
            {:else if isVideoDetected}
              <div class="input-status video">
                <Icon name="video" size="small" color="#DC143C" />
                <span>{videoPlatform} Video Detected</span>
              </div>
            {/if}

            {#if url && stepStatus[1] === 'processing'}
              <div class="progress-bar">
                <div class="progress-fill"></div>
              </div>
              <div class="status-text">
                Status: <span class="status-processing">SCANNING...</span>
              </div>
            {/if}
          </div>
        </div>

        <!-- Step 2: Cognitive Classification -->
        <div
          class="step-section"
          class:active={currentStep === 2}
          class:completed={stepStatus[2] === 'completed'}
        >
          <div class="step-header">
            <div class="step-indicator">
              {#if stepStatus[2] === 'completed'}
                <Icon name="check" size="small" color="#00ff64" />
              {:else}
                <span class="step-number">2</span>
              {/if}
            </div>
            <span class="step-title">[STEP 2] COGNITIVE CLASSIFICATION</span>
          </div>

          <div class="step-content">
            <div class="content-type-grid">
              <!-- Auto option always available -->
              <button
                type="button"
                class="content-type-option"
                class:active={contentType === 'auto'}
                on:click={() => selectContentType('auto')}
                disabled={isSubmitting}
              >
                <span class="option-icon">🤖</span>
                <span class="option-label">AUTO</span>
              </button>

              <!-- Dynamic content types from backend -->
              {#each availableTypes as type}
                <button
                  type="button"
                  class="content-type-option"
                  class:active={contentType === type.name}
                  on:click={() => selectContentType(type.name)}
                  disabled={isSubmitting}
                >
                  <span class="option-icon">
                    {#if type.name === 'document'}📄
                    {:else if type.name === 'video'}🎥
                    {:else if type.name === 'article'}📰
                    {:else if type.name === 'tutorial'}🎓
                    {:else if type.name === 'image'}🖼️
                    {:else if type.name === 'note'}📝
                    {:else if type.name === 'link'}🔗
                    {:else if type.name === 'audio'}🎵
                    {:else if type.name === 'code'}💻
                    {:else if type.name === 'development'}⚡
                    {:else}📋{/if}
                  </span>
                  <span class="option-label">{type.display_name.substring(0, 4).toUpperCase()}</span
                  >
                </button>
              {/each}
            </div>

            {#if stepStatus[2] === 'completed'}
              <div class="status-text">
                Classification: <span class="status-complete"
                  >{contentType.toUpperCase()}_SELECTED</span
                >
              </div>
            {/if}
          </div>
        </div>

        <!-- Step 3: Neural Enhancement Protocols -->
        <div
          class="step-section"
          class:active={currentStep === 3}
          class:completed={stepStatus[3] === 'completed'}
        >
          <div class="step-header">
            <div class="step-indicator">
              {#if stepStatus[3] === 'completed'}
                <Icon name="check" size="small" color="#00ff64" />
              {:else}
                <span class="step-number">3</span>
              {/if}
            </div>
            <span class="step-title">[STEP 3] NEURAL ENHANCEMENT PROTOCOLS</span>
          </div>

          <div class="step-content">
            <div class="enhancement-toggles">
              <div class="enhancement-option">
                <button
                  type="button"
                  class="toggle-switch"
                  class:active={enableSummarization}
                  on:click={toggleAISummarization}
                  disabled={isSubmitting}
                >
                  <div class="switch-slider"></div>
                </button>
                <span class="option-text">
                  AI Summarization Engine:
                  <span class="status-indicator" class:active={enableSummarization}>
                    {enableSummarization ? 'ENABLED' : 'DISABLED'}
                  </span>
                </span>
              </div>

              <div class="enhancement-option">
                <button type="button" class="toggle-switch active" disabled>
                  <div class="switch-slider"></div>
                </button>
                <span class="option-text">
                  Pattern Recognition: <span class="status-indicator active">ACTIVE</span>
                </span>
              </div>

              <div class="enhancement-option">
                <button type="button" class="toggle-switch" disabled>
                  <div class="switch-slider"></div>
                </button>
                <span class="option-text">
                  Knowledge Graph Link: <span class="status-indicator">STANDBY</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 4: Memory Trace Metadata -->
        <div class="step-section" class:active={currentStep === 4}>
          <div class="step-header">
            <div class="step-indicator">
              <span class="step-number">4</span>
            </div>
            <span class="step-title">[STEP 4] MEMORY TRACE METADATA</span>
          </div>

          <div class="step-content">
            <div class="metadata-inputs">
              <input
                bind:value={title}
                type="text"
                class="terminal-input"
                placeholder="Title (auto-generated if empty)"
                disabled={isSubmitting}
              />

              <textarea
                bind:value={highlight}
                class="terminal-textarea"
                placeholder="Highlight or notes"
                rows="3"
                disabled={isSubmitting}
              ></textarea>

              <TagAutocomplete
                value=""
                placeholder="Tags: #tech #ai #neural"
                disabled={isSubmitting}
                on:tags={handleTagsUpdate}
              />
            </div>
          </div>
        </div>

        <!-- File Upload for document/image types -->
        {#if (contentType === 'document' || contentType === 'image') && currentStep >= 2}
          <div class="step-section file-upload-section">
            <div class="step-header">
              <Icon name="upload" size="small" color="#DC143C" />
              <span class="step-title">[OPTIONAL] FILE UPLOAD</span>
            </div>
            <div class="step-content">
              <FileUpload
                {contentType}
                multiple={false}
                disabled={isSubmitting}
                on:files={handleFileUpload}
              />
            </div>
          </div>
        {/if}

        <!-- Error Display -->
        {#if error}
          <div class="error-section">
            <div class="error-header">
              <Icon name="alert-triangle" size="small" color="#DC143C" />
              <span>NEURAL PATHWAY DISRUPTED</span>
            </div>
            <div class="error-message">{error.message}</div>
          </div>
        {/if}

        <!-- Progress Bar -->
        {#if isSubmitting}
          <div class="processing-section">
            <div class="processing-header">
              <Spinner size="small" />
              <span>PROCESSING MEMORY TRACE...</span>
            </div>
            <div class="progress-bar active">
              <div class="progress-fill" style="width: {progress}%"></div>
            </div>
            <div class="processing-status">
              Neural network synchronization: {Math.round(progress)}%
            </div>
          </div>
        {/if}

        <!-- Execute Button -->
        <div class="execute-section">
          <button
            type="submit"
            class="execute-button"
            disabled={isSubmitting || (!url && !highlight && uploadedFiles.length === 0)}
          >
            {#if isSubmitting}
              <Spinner size="small" />
              PROCESSING...
            {:else}
              > EXECUTE_MEMORY_CAPTURE()
            {/if}
          </button>

          <div class="command-hint">
            <Icon name="keyboard" size="small" color="#666" />
            <span>Cmd+Enter to execute</span>
          </div>
        </div>
      </form>
    </div>
  </div>
</div>

<style>
  .neural-terminal-page {
    min-height: 100vh;
    background: #0a0a0a;
    position: relative;
    padding: 2rem;
    font-family: var(--font-mono);
  }

  .neural-motherboard-bg {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    opacity: 0.03;
    pointer-events: none;
    z-index: 0;
  }

  .pcb-traces {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      repeating-linear-gradient(0deg, transparent, transparent 40px, #00ff64 40px, #00ff64 42px),
      repeating-linear-gradient(90deg, transparent, transparent 40px, #00ff64 40px, #00ff64 42px);
  }

  .circuit-nodes {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .node {
    position: absolute;
    width: 20px;
    height: 20px;
    background: radial-gradient(circle, #dc143c, #b91c3c);
    border-radius: 50%;
    border: 2px solid #dc143c;
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.5);
    animation: node-pulse 3s ease-in-out infinite;
  }

  .node-1 {
    top: 20%;
    left: 15%;
    animation-delay: 0s;
  }
  .node-2 {
    top: 60%;
    left: 80%;
    animation-delay: 1s;
  }
  .node-3 {
    top: 30%;
    left: 70%;
    animation-delay: 2s;
  }
  .node-4 {
    top: 80%;
    left: 25%;
    animation-delay: 1.5s;
  }

  @keyframes node-pulse {
    0%,
    100% {
      transform: scale(1);
      opacity: 0.6;
    }
    50% {
      transform: scale(1.3);
      opacity: 0.9;
    }
  }

  .terminal-container {
    max-width: 900px;
    margin: 0 auto;
    background: rgba(26, 26, 26, 0.95);
    border: 2px solid #00ff64;
    border-radius: var(--radius-lg);
    backdrop-filter: blur(15px);
    box-shadow:
      0 0 30px rgba(0, 255, 100, 0.2),
      inset 0 0 100px rgba(0, 0, 0, 0.5);
    overflow: hidden;
    position: relative;
    z-index: 1;
  }

  .terminal-header {
    background: linear-gradient(90deg, #00ff64, #00dd55);
    color: #000;
    padding: 1rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    position: relative;
    overflow: hidden;
  }

  .terminal-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    animation: scan 4s ease-in-out infinite;
  }

  @keyframes scan {
    0% {
      left: -100%;
    }
    100% {
      left: 100%;
    }
  }

  .terminal-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.1rem;
    letter-spacing: 1px;
  }

  .terminal-controls {
    display: flex;
    gap: 0.5rem;
  }

  .control-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #000;
    opacity: 0.7;
  }

  .terminal-body {
    padding: 2rem;
    font-size: 14px;
    line-height: 1.4;
    color: var(--text-primary);
  }

  .system-status {
    margin-bottom: 2rem;
    padding: 1rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(0, 255, 100, 0.2);
    border-radius: var(--radius-sm);
  }

  .status-line {
    color: #666;
    margin-bottom: 0.5rem;
  }

  .status-line:last-child {
    margin-bottom: 0;
  }

  .status-online {
    color: #00ff64;
    font-weight: 600;
  }

  .status-standby {
    color: #fbbf24;
    font-weight: 600;
  }

  .terminal-output {
    margin-bottom: 2rem;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(0, 255, 100, 0.1);
    border-radius: var(--radius-sm);
    padding: 1rem;
    max-height: 150px;
    overflow-y: auto;
  }

  .terminal-line {
    color: #00ff64;
    margin-bottom: 0.25rem;
    font-size: 13px;
  }

  .terminal-line.current {
    color: var(--text-primary);
  }

  .cursor {
    animation: blink 1s infinite;
    color: #00ff64;
  }

  @keyframes blink {
    0%,
    50% {
      opacity: 1;
    }
    51%,
    100% {
      opacity: 0;
    }
  }

  .processing-steps {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .step-section {
    border: 1px solid rgba(0, 255, 100, 0.2);
    border-radius: var(--radius);
    padding: 1.5rem;
    background: rgba(0, 255, 100, 0.02);
    transition: all var(--transition-base);
  }

  .step-section.active {
    border-color: rgba(0, 255, 100, 0.5);
    background: rgba(0, 255, 100, 0.05);
    box-shadow: 0 0 15px rgba(0, 255, 100, 0.1);
  }

  .step-section.completed {
    border-color: rgba(0, 255, 100, 0.3);
    background: rgba(0, 255, 100, 0.02);
    opacity: 0.8;
  }

  .step-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    color: #00ff64;
    font-weight: 600;
  }

  .step-indicator {
    width: 32px;
    height: 32px;
    border: 2px solid #00ff64;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    background: rgba(0, 255, 100, 0.1);
  }

  .step-section.completed .step-indicator {
    background: #00ff64;
    color: #000;
  }

  .step-number {
    font-size: 14px;
  }

  .step-title {
    font-size: 16px;
    letter-spacing: 0.5px;
  }

  .step-content {
    margin-left: 3rem;
  }

  .input-group {
    position: relative;
  }

  .terminal-input,
  .terminal-textarea {
    width: 100%;
    background: rgba(0, 0, 0, 0.5);
    border: 2px solid #333;
    color: var(--text-primary);
    padding: 0.75rem;
    border-radius: var(--radius-sm);
    font-family: var(--font-mono);
    font-size: 14px;
    transition: all var(--transition-base);
  }

  .terminal-input:focus,
  .terminal-textarea:focus {
    outline: none;
    border-color: #00ff64;
    box-shadow: 0 0 15px rgba(0, 255, 100, 0.3);
    background: rgba(0, 0, 0, 0.7);
  }

  .terminal-textarea {
    resize: vertical;
    min-height: 80px;
  }

  .input-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
    font-size: 13px;
    color: #00ff64;
  }

  .input-status.video {
    color: #dc143c;
  }

  .progress-bar {
    background: rgba(0, 0, 0, 0.5);
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin: 0.75rem 0;
  }

  .progress-fill {
    background: linear-gradient(90deg, #00ff64, #dc143c);
    height: 100%;
    width: 70%;
    animation: progress-pulse 2s ease-in-out infinite;
  }

  .progress-bar.active .progress-fill {
    transition: width var(--transition-base);
  }

  @keyframes progress-pulse {
    0%,
    100% {
      opacity: 0.8;
    }
    50% {
      opacity: 1;
    }
  }

  .status-text {
    font-size: 13px;
    color: #666;
  }

  .status-processing {
    color: #fbbf24;
    font-weight: 600;
  }

  .status-complete {
    color: #00ff64;
    font-weight: 600;
  }

  .content-type-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .content-type-option {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid #333;
    color: var(--text-secondary);
    padding: 0.75rem;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all var(--transition-base);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    font-family: var(--font-mono);
    font-size: 12px;
  }

  .content-type-option:hover {
    border-color: #00ff64;
    background: rgba(0, 255, 100, 0.1);
  }

  .content-type-option.active {
    border-color: #dc143c;
    background: rgba(220, 20, 60, 0.2);
    color: #dc143c;
  }

  .option-icon {
    font-size: 16px;
  }

  .option-label {
    font-weight: 600;
  }

  .enhancement-toggles {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .enhancement-option {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .toggle-switch {
    width: 50px;
    height: 25px;
    background: #333;
    border: none;
    border-radius: 25px;
    position: relative;
    cursor: pointer;
    transition: all var(--transition-base);
  }

  .toggle-switch.active {
    background: #dc143c;
  }

  .toggle-switch:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  .switch-slider {
    position: absolute;
    width: 21px;
    height: 21px;
    border-radius: 50%;
    background: var(--text-primary);
    top: 2px;
    left: 2px;
    transition: all var(--transition-base);
  }

  .toggle-switch.active .switch-slider {
    left: 27px;
  }

  .option-text {
    font-size: 14px;
    color: var(--text-secondary);
  }

  .status-indicator {
    font-weight: 600;
    color: #666;
  }

  .status-indicator.active {
    color: #00ff64;
  }

  .metadata-inputs {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .file-upload-section {
    border-color: rgba(220, 20, 60, 0.2);
    background: rgba(220, 20, 60, 0.02);
  }

  .error-section {
    background: rgba(220, 20, 60, 0.1);
    border: 1px solid rgba(220, 20, 60, 0.3);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .error-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #dc143c;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .error-message {
    color: var(--text-secondary);
    font-size: 14px;
  }

  .processing-section {
    background: rgba(0, 255, 100, 0.05);
    border: 1px solid rgba(0, 255, 100, 0.2);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .processing-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #00ff64;
    font-weight: 600;
    margin-bottom: 0.75rem;
  }

  .processing-status {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 0.5rem;
  }

  .execute-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    margin-top: 2rem;
  }

  .execute-button {
    background: linear-gradient(135deg, #dc143c, #b91c3c);
    color: white;
    border: none;
    padding: 1rem 3rem;
    font-family: var(--font-mono);
    font-weight: 600;
    font-size: 16px;
    border-radius: var(--radius);
    cursor: pointer;
    transition: all var(--transition-base);
    text-transform: uppercase;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .execute-button:hover:not(:disabled) {
    background: linear-gradient(135deg, #b91c3c, #991b1b);
    box-shadow: 0 0 25px rgba(220, 20, 60, 0.4);
    transform: translateY(-2px);
  }

  .execute-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .command-hint {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #666;
    font-size: 12px;
  }

  @media (max-width: 768px) {
    .neural-terminal-page {
      padding: 1rem;
    }

    .terminal-body {
      padding: 1rem;
    }

    .step-content {
      margin-left: 0;
    }

    .content-type-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .terminal-container {
      border-radius: var(--radius);
    }
  }
</style>
