<script>
  import { createEventDispatcher } from 'svelte';
  import Icon from './Icon.svelte';

  export let disabled = false;
  export let accept = '*/*';
  export let multiple = false;
  export let maxSize = 10 * 1024 * 1024; // 10MB default
  export let contentType = 'auto';

  const dispatch = createEventDispatcher();

  let isDragging = false;
  let fileInput;
  let uploadedFiles = [];
  let uploadError = null;

  // File type validation based on content type
  const getAcceptedTypes = (type) => {
    switch (type) {
      case 'document':
        return '.pdf,.doc,.docx,.txt,.rtf,.odt';
      case 'image':
        return '.jpg,.jpeg,.png,.gif,.bmp,.svg,.webp';
      case 'video':
        return '.mp4,.avi,.mov,.mkv,.webm,.flv,.wmv,.m4v';
      case 'audio':
        return '.mp3,.wav,.flac,.aac,.ogg,.wma,.m4a';
      default:
        return '*/*';
    }
  };

  $: actualAccept = accept === '*/*' ? getAcceptedTypes(contentType) : accept;

  function handleDragOver(e) {
    e.preventDefault();
    if (!disabled) {
      isDragging = true;
    }
  }

  function handleDragLeave(e) {
    e.preventDefault();
    isDragging = false;
  }

  function handleDrop(e) {
    e.preventDefault();
    isDragging = false;

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    processFiles(files);
  }

  function handleFileSelect(e) {
    if (disabled) return;

    const files = Array.from(e.target.files);
    processFiles(files);
  }

  function processFiles(files) {
    uploadError = null;
    const validFiles = [];

    for (const file of files) {
      // Check file size
      if (file.size > maxSize) {
        uploadError = `File "${file.name}" exceeds maximum size of ${formatFileSize(maxSize)}`;
        continue;
      }

      // Check file type
      if (!isValidFileType(file)) {
        uploadError = `File "${file.name}" is not a supported file type`;
        continue;
      }

      validFiles.push(file);
    }

    if (validFiles.length > 0) {
      uploadedFiles = multiple ? [...uploadedFiles, ...validFiles] : validFiles;
      dispatch('files', { files: uploadedFiles });
    }
  }

  function isValidFileType(file) {
    if (actualAccept === '*/*') return true;

    const allowedTypes = actualAccept.split(',').map((type) => type.trim());
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    const fileMimeType = file.type.toLowerCase();

    return allowedTypes.some((type) => {
      if (type.startsWith('.')) {
        return type === fileExtension;
      }
      return fileMimeType.includes(type.replace('*', ''));
    });
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function removeFile(index) {
    uploadedFiles = uploadedFiles.filter((_, i) => i !== index);
    dispatch('files', { files: uploadedFiles });
  }

  function clearFiles() {
    uploadedFiles = [];
    uploadError = null;
    if (fileInput) fileInput.value = '';
    dispatch('files', { files: [] });
  }

  function openFileDialog() {
    if (!disabled && fileInput) {
      fileInput.click();
    }
  }
</script>

<div class="file-upload-container">
  <div
    class="file-upload-area"
    class:dragging={isDragging}
    class:disabled
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
    on:drop={handleDrop}
    on:click={openFileDialog}
  >
    <div class="upload-content">
      <div class="upload-icon">
        <Icon name="upload" size="large" />
      </div>

      <div class="upload-text">
        <h3>Drop files here or click to upload</h3>
        <p>
          {#if contentType === 'document'}
            Supported: PDF, DOC, DOCX, TXT, RTF, ODT
          {:else if contentType === 'image'}
            Supported: JPG, PNG, GIF, BMP, SVG, WEBP
          {:else if contentType === 'video'}
            Supported: MP4, AVI, MOV, MKV, WEBM, FLV, WMV, M4V
          {:else if contentType === 'audio'}
            Supported: MP3, WAV, FLAC, AAC, OGG, WMA, M4A
          {:else}
            Any file type supported
          {/if}
        </p>
        <p class="file-size-limit">Maximum file size: {formatFileSize(maxSize)}</p>
      </div>
    </div>

    <input
      bind:this={fileInput}
      type="file"
      accept={actualAccept}
      {multiple}
      on:change={handleFileSelect}
      {disabled}
      style="display: none;"
    />
  </div>

  {#if uploadError}
    <div class="upload-error">
      <Icon name="alert-triangle" size="small" />
      {uploadError}
    </div>
  {/if}

  {#if uploadedFiles.length > 0}
    <div class="uploaded-files">
      <div class="files-header">
        <h4>Uploaded Files ({uploadedFiles.length})</h4>
        <button type="button" class="clear-files" on:click={clearFiles}>
          <Icon name="x" size="small" />
          Clear All
        </button>
      </div>

      <div class="files-list">
        {#each uploadedFiles as file, index}
          <div class="file-item">
            <div class="file-info">
              <div class="file-icon">
                {#if file.type.startsWith('image/')}
                  <Icon name="image" size="small" />
                {:else if file.type.includes('pdf')}
                  <Icon name="file-text" size="small" />
                {:else}
                  <Icon name="file" size="small" />
                {/if}
              </div>

              <div class="file-details">
                <div class="file-name">{file.name}</div>
                <div class="file-size">{formatFileSize(file.size)}</div>
              </div>
            </div>

            <button type="button" class="remove-file" on:click={() => removeFile(index)}>
              <Icon name="x" size="small" />
            </button>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .file-upload-container {
    margin-bottom: 1.5rem;
  }

  .file-upload-area {
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    background: var(--bg-secondary);
  }

  .file-upload-area:hover:not(.disabled) {
    border-color: var(--accent);
    background: var(--bg-tertiary);
  }

  .file-upload-area.dragging {
    border-color: var(--accent);
    background: var(--bg-tertiary);
    transform: scale(1.02);
  }

  .file-upload-area.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .upload-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .upload-icon {
    color: var(--text-secondary);
    opacity: 0.7;
  }

  .upload-text h3 {
    margin: 0 0 0.5rem 0;
    color: var(--text-primary);
    font-size: 1.1rem;
    font-weight: 600;
  }

  .upload-text p {
    margin: 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .file-size-limit {
    color: var(--text-muted);
    font-size: 0.8rem;
  }

  .upload-error {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: var(--error-bg);
    color: var(--error);
    border-radius: var(--radius-sm);
    font-size: 0.9rem;
  }

  .uploaded-files {
    margin-top: 1rem;
    padding: 1rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius);
    border: 1px solid var(--border);
  }

  .files-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
  }

  .files-header h4 {
    margin: 0;
    color: var(--text-primary);
    font-size: 1rem;
    font-weight: 600;
  }

  .clear-files {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: rgba(220, 20, 60, 0.1);
    border: 1px solid rgba(220, 20, 60, 0.2);
    border-radius: var(--radius-sm);
    color: var(--error);
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .clear-files:hover {
    background: rgba(220, 20, 60, 0.2);
    border-color: rgba(220, 20, 60, 0.3);
  }

  .files-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .file-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
  }

  .file-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .file-icon {
    color: var(--text-secondary);
  }

  .file-details {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .file-name {
    color: var(--text-primary);
    font-weight: 500;
    font-size: 0.9rem;
  }

  .file-size {
    color: var(--text-muted);
    font-size: 0.8rem;
  }

  .remove-file {
    padding: 0.25rem;
    background: rgba(220, 20, 60, 0.1);
    border: 1px solid rgba(220, 20, 60, 0.2);
    border-radius: var(--radius-sm);
    color: var(--error);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .remove-file:hover {
    background: rgba(220, 20, 60, 0.2);
    border-color: rgba(220, 20, 60, 0.3);
  }

  @media (max-width: 768px) {
    .file-upload-area {
      padding: 1.5rem;
    }

    .upload-text h3 {
      font-size: 1rem;
    }

    .files-header {
      flex-direction: column;
      gap: 0.5rem;
      align-items: flex-start;
    }

    .file-item {
      padding: 0.5rem;
    }
  }
</style>
