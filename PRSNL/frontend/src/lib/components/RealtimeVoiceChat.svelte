<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { RealtimeSTTClient, type AIResponseData } from '$lib/services/realtime-stt';
  import { Mic, MicOff, Loader2, Volume2 } from 'lucide-svelte';

  export let className = '';

  let client: RealtimeSTTClient | null = null;
  let isConnected = false;
  let isStreaming = false;
  let isProcessing = false;
  let partialText = '';
  let finalText = '';
  let aiResponse = '';
  let error = '';
  let selectedLanguage = 'en';

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'ja', name: 'Japanese' },
    { code: 'zh', name: 'Chinese' }
  ];

  onMount(async () => {
    client = new RealtimeSTTClient();

    // Set up event handlers
    client.onConnectionChange = (connected) => {
      isConnected = connected;
      if (!connected) {
        isStreaming = false;
      }
    };

    client.onStreamingStatusChange = (active) => {
      isStreaming = active;
      if (active) {
        partialText = '';
        finalText = '';
        error = '';
      }
    };

    client.onPartialTranscription = (text) => {
      partialText = text;
    };

    client.onFinalTranscription = (text) => {
      finalText += (finalText ? ' ' : '') + text;
      partialText = '';
    };

    client.onAIResponse = (response: AIResponseData) => {
      aiResponse = response.personalized_text;
      isProcessing = false;
    };

    client.onAudioResponse = (audioData, format) => {
      playAudioResponse(audioData, format);
    };

    client.onError = (errorMessage) => {
      error = errorMessage;
      isProcessing = false;
    };

    // Connect to WebSocket
    try {
      await client.connect();
    } catch (err) {
      console.error('Failed to connect:', err);
      error = 'Failed to connect to voice service';
    }
  });

  onDestroy(() => {
    if (client) {
      client.disconnect();
    }
  });

  function toggleStreaming() {
    if (!client || !isConnected) return;

    if (isStreaming) {
      client.stopStreaming();
    } else {
      client.startStreaming();
      aiResponse = '';
    }
  }

  function processText() {
    if (!client || !isConnected || isProcessing) return;

    const textToProcess = finalText || partialText;
    if (!textToProcess.trim()) {
      error = 'No text to process';
      return;
    }

    isProcessing = true;
    client.processWithAI(textToProcess);
  }

  function playAudioResponse(audioData: string, format: string) {
    try {
      const audio = new Audio(`data:audio/${format};base64,${audioData}`);
      audio.play().catch(err => {
        console.error('Failed to play audio:', err);
      });
    } catch (err) {
      console.error('Failed to create audio:', err);
    }
  }

  function changeLanguage() {
    if (!client || !isConnected) return;
    client.setLanguage(selectedLanguage);
  }

  function clearTranscription() {
    partialText = '';
    finalText = '';
    aiResponse = '';
    error = '';
    if (client) {
      client.clearAccumulatedText();
    }
  }
</script>

<div class="realtime-voice-chat {className}">
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">Real-time Voice Chat</h2>
      
      <!-- Connection Status -->
      <div class="flex items-center gap-2 mb-4">
        <div class="badge {isConnected ? 'badge-success' : 'badge-error'}">
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
        
        <!-- Language Selector -->
        <select 
          class="select select-sm select-bordered"
          bind:value={selectedLanguage}
          on:change={changeLanguage}
          disabled={!isConnected || isStreaming}
        >
          {#each languages as lang}
            <option value={lang.code}>{lang.name}</option>
          {/each}
        </select>
      </div>

      <!-- Transcription Display -->
      <div class="transcription-area">
        <div class="form-control">
          <label class="label">
            <span class="label-text">Transcription</span>
            {#if isStreaming}
              <span class="label-text-alt text-primary">Listening...</span>
            {/if}
          </label>
          <textarea 
            class="textarea textarea-bordered h-24" 
            readonly
            value={finalText + (partialText ? ` ${partialText}` : '')}
            placeholder="Your speech will appear here..."
          />
        </div>
      </div>

      <!-- AI Response -->
      {#if aiResponse}
        <div class="ai-response mt-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">AI Response</span>
              <Volume2 class="w-4 h-4" />
            </label>
            <textarea 
              class="textarea textarea-bordered textarea-primary h-24" 
              readonly
              value={aiResponse}
            />
          </div>
        </div>
      {/if}

      <!-- Error Display -->
      {#if error}
        <div class="alert alert-error mt-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      {/if}

      <!-- Controls -->
      <div class="card-actions justify-between mt-4">
        <div class="flex gap-2">
          <!-- Start/Stop Button -->
          <button 
            class="btn {isStreaming ? 'btn-error' : 'btn-primary'}"
            on:click={toggleStreaming}
            disabled={!isConnected}
          >
            {#if isStreaming}
              <MicOff class="w-4 h-4 mr-2" />
              Stop Recording
            {:else}
              <Mic class="w-4 h-4 mr-2" />
              Start Recording
            {/if}
          </button>

          <!-- Process Button -->
          <button 
            class="btn btn-secondary"
            on:click={processText}
            disabled={!isConnected || isProcessing || (!finalText && !partialText)}
          >
            {#if isProcessing}
              <Loader2 class="w-4 h-4 mr-2 animate-spin" />
              Processing...
            {:else}
              Process with AI
            {/if}
          </button>
        </div>

        <!-- Clear Button -->
        <button 
          class="btn btn-ghost"
          on:click={clearTranscription}
          disabled={isStreaming || isProcessing}
        >
          Clear
        </button>
      </div>

      <!-- Instructions -->
      <div class="text-sm text-base-content/70 mt-4">
        <p>1. Click "Start Recording" to begin real-time transcription</p>
        <p>2. Speak clearly into your microphone</p>
        <p>3. Click "Stop Recording" when finished</p>
        <p>4. Click "Process with AI" to get Cortex's response</p>
      </div>
    </div>
  </div>
</div>

<style>
  .realtime-voice-chat {
    max-width: 600px;
    margin: 0 auto;
  }

  .transcription-area textarea {
    font-family: monospace;
  }

  .ai-response textarea {
    background-color: rgba(var(--p), 0.1);
  }
</style>