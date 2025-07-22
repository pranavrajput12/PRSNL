<script lang="ts">
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import { addNotification } from '$lib/stores/app';
  
  // Voice settings state
  let settings = {
    ttsEngine: 'edge-tts',
    sttModel: 'small',
    useCrewAI: true,
    enableStreaming: false,
    defaultGender: 'female',
    emotionStrength: 1.2
  };
  
  let loading = false;
  let saving = false;
  
  // TTS Engine options
  const ttsEngines = [
    { value: 'edge-tts', label: 'Edge TTS', description: 'Microsoft Edge voices (reliable, good quality)' },
    { value: 'chatterbox', label: 'Chatterbox TTS', description: 'Modern emotion-aware voices (experimental)' }
  ];
  
  // STT Model options
  const sttModels = [
    { value: 'tiny', label: 'Tiny', description: 'Fastest, least accurate (39M params)' },
    { value: 'base', label: 'Base', description: 'Fast, good accuracy (74M params)' },
    { value: 'small', label: 'Small', description: 'Balanced speed/accuracy (244M params)' },
    { value: 'medium', label: 'Medium', description: 'Better accuracy, slower (769M params)' },
    { value: 'large', label: 'Large', description: 'Best accuracy, slowest (1550M params)' }
  ];
  
  // Voice gender options
  const genderOptions = [
    { value: 'female', label: 'Female', icon: '👩' },
    { value: 'male', label: 'Male', icon: '👨' }
  ];
  
  // Load current settings
  async function loadSettings() {
    loading = true;
    try {
      const response = await fetch('/api/settings/voice', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        settings = { ...settings, ...data };
      }
    } catch (error) {
      console.error('Failed to load voice settings:', error);
    } finally {
      loading = false;
    }
  }
  
  // Save settings
  async function saveSettings() {
    saving = true;
    try {
      const response = await fetch('/api/settings/voice', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(settings)
      });
      
      if (response.ok) {
        addNotification({
          type: 'success',
          message: 'Voice settings saved successfully'
        });
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      console.error('Failed to save voice settings:', error);
      addNotification({
        type: 'error',
        message: 'Failed to save voice settings'
      });
    } finally {
      saving = false;
    }
  }
  
  // Test voice with current settings
  async function testVoice() {
    try {
      const response = await fetch('/api/voice/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          text: 'Hello! This is a test of the voice settings.',
          settings
        })
      });
      
      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        await audio.play();
      }
    } catch (error) {
      console.error('Voice test failed:', error);
      addNotification({
        type: 'error',
        message: 'Voice test failed'
      });
    }
  }
  
  onMount(() => {
    loadSettings();
  });
</script>

<div class="settings-page">
  <div class="settings-header">
    <h1>
      <Icon name="mic" size={32} />
      Voice Settings
    </h1>
    <p class="subtitle">Configure speech recognition and synthesis options</p>
  </div>
  
  {#if loading}
    <div class="loading">
      <Icon name="loader" size={24} class="animate-spin" />
      <span>Loading settings...</span>
    </div>
  {:else}
    <div class="settings-content">
      <!-- TTS Engine -->
      <div class="setting-group">
        <h2>Text-to-Speech Engine</h2>
        <p class="description">Choose the voice synthesis engine</p>
        
        <div class="radio-group">
          {#each ttsEngines as engine}
            <label class="radio-option">
              <input
                type="radio"
                name="ttsEngine"
                value={engine.value}
                bind:group={settings.ttsEngine}
              />
              <div class="radio-content">
                <strong>{engine.label}</strong>
                <span>{engine.description}</span>
              </div>
            </label>
          {/each}
        </div>
      </div>
      
      <!-- STT Model -->
      <div class="setting-group">
        <h2>Speech Recognition Model</h2>
        <p class="description">Balance between speed and accuracy</p>
        
        <select bind:value={settings.sttModel} class="select-input">
          {#each sttModels as model}
            <option value={model.value}>
              {model.label} - {model.description}
            </option>
          {/each}
        </select>
      </div>
      
      <!-- Voice Gender -->
      <div class="setting-group">
        <h2>Default Voice Gender</h2>
        <p class="description">Choose the default voice for responses</p>
        
        <div class="gender-options">
          {#each genderOptions as gender}
            <button
              class="gender-button"
              class:active={settings.defaultGender === gender.value}
              on:click={() => settings.defaultGender = gender.value}
            >
              <span class="gender-icon">{gender.icon}</span>
              <span>{gender.label}</span>
            </button>
          {/each}
        </div>
      </div>
      
      <!-- Advanced Options -->
      <div class="setting-group">
        <h2>Advanced Options</h2>
        
        <label class="toggle-option">
          <input
            type="checkbox"
            bind:checked={settings.useCrewAI}
          />
          <div class="toggle-content">
            <strong>Use CrewAI Intelligence</strong>
            <span>Enable multi-agent system for smarter responses</span>
          </div>
        </label>
        
        <label class="toggle-option">
          <input
            type="checkbox"
            bind:checked={settings.enableStreaming}
            disabled
          />
          <div class="toggle-content">
            <strong>Enable Streaming (Coming Soon)</strong>
            <span>Real-time transcription and response generation</span>
          </div>
        </label>
        
        <div class="slider-option">
          <label for="emotion-strength">
            <strong>Emotion Intensity</strong>
            <span>{settings.emotionStrength.toFixed(1)}x</span>
          </label>
          <input
            id="emotion-strength"
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            bind:value={settings.emotionStrength}
            class="slider"
          />
          <div class="slider-labels">
            <span>Subtle</span>
            <span>Natural</span>
            <span>Expressive</span>
          </div>
        </div>
      </div>
      
      <!-- Actions -->
      <div class="actions">
        <button
          class="test-button"
          on:click={testVoice}
        >
          <Icon name="play" size={16} />
          Test Voice
        </button>
        
        <div class="save-actions">
          <button
            class="cancel-button"
            on:click={loadSettings}
            disabled={saving}
          >
            Reset
          </button>
          
          <button
            class="save-button"
            on:click={saveSettings}
            disabled={saving}
          >
            {#if saving}
              <Icon name="loader" size={16} class="animate-spin" />
              Saving...
            {:else}
              <Icon name="save" size={16} />
              Save Changes
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .settings-page {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .settings-header {
    margin-bottom: 3rem;
  }
  
  .settings-header h1 {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
  }
  
  .subtitle {
    color: #64748b;
    font-size: 1.1rem;
  }
  
  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 4rem;
    color: #64748b;
  }
  
  .settings-content {
    display: flex;
    flex-direction: column;
    gap: 3rem;
  }
  
  .setting-group {
    background: #0f172a;
    padding: 2rem;
    border-radius: 16px;
    border: 1px solid #1e293b;
  }
  
  .setting-group h2 {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }
  
  .description {
    color: #94a3b8;
    margin-bottom: 1.5rem;
  }
  
  .radio-group {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .radio-option {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem;
    background: #1e293b;
    border: 2px solid transparent;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .radio-option:hover {
    border-color: #475569;
  }
  
  .radio-option:has(input:checked) {
    border-color: #6366f1;
    background: rgba(99, 102, 241, 0.1);
  }
  
  .radio-option input {
    margin-top: 0.125rem;
  }
  
  .radio-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .radio-content strong {
    color: #f1f5f9;
  }
  
  .radio-content span {
    color: #94a3b8;
    font-size: 0.875rem;
  }
  
  .select-input {
    width: 100%;
    padding: 0.75rem 1rem;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #f1f5f9;
    font-size: 1rem;
  }
  
  .select-input:focus {
    outline: none;
    border-color: #6366f1;
  }
  
  .gender-options {
    display: flex;
    gap: 1rem;
  }
  
  .gender-button {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1.5rem;
    background: #1e293b;
    border: 2px solid transparent;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .gender-button:hover {
    border-color: #475569;
    transform: translateY(-2px);
  }
  
  .gender-button.active {
    border-color: #6366f1;
    background: rgba(99, 102, 241, 0.1);
  }
  
  .gender-icon {
    font-size: 2rem;
  }
  
  .toggle-option {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem 0;
    cursor: pointer;
  }
  
  .toggle-option input[type="checkbox"] {
    margin-top: 0.125rem;
    width: 1.25rem;
    height: 1.25rem;
    cursor: pointer;
  }
  
  .toggle-option input[type="checkbox"]:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .toggle-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .toggle-content strong {
    color: #f1f5f9;
  }
  
  .toggle-content span {
    color: #94a3b8;
    font-size: 0.875rem;
  }
  
  .slider-option {
    margin-top: 1.5rem;
  }
  
  .slider-option label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .slider {
    width: 100%;
    height: 6px;
    background: #334155;
    border-radius: 3px;
    outline: none;
    -webkit-appearance: none;
  }
  
  .slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    background: #6366f1;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .slider::-webkit-slider-thumb:hover {
    transform: scale(1.2);
  }
  
  .slider-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #64748b;
  }
  
  .actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 2rem;
  }
  
  .save-actions {
    display: flex;
    gap: 1rem;
  }
  
  .test-button,
  .cancel-button,
  .save-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .test-button {
    background: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
  }
  
  .test-button:hover {
    background: #334155;
  }
  
  .cancel-button {
    background: transparent;
    color: #94a3b8;
    border: 1px solid #334155;
  }
  
  .cancel-button:hover {
    background: #1e293b;
    color: #f1f5f9;
  }
  
  .save-button {
    background: #6366f1;
    color: white;
  }
  
  .save-button:hover:not(:disabled) {
    background: #5558e3;
    transform: translateY(-2px);
  }
  
  .save-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>