<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { fly } from 'svelte/transition';
  import RecordRTC from 'recordrtc';
  import Icon from './Icon.svelte';
  import { websocketStore } from '$lib/stores/websocket';
  import { addNotification } from '$lib/stores/app';
  
  // Props
  export let position: 'bottom-right' | 'bottom-left' | 'floating' = 'bottom-right';
  export let size: 'small' | 'medium' | 'large' = 'medium';
  
  // State
  let isRecording = false;
  let isProcessing = false;
  let isExpanded = false;
  let cortexMood = 'idle';
  let showTranscript = false;
  let voicePermissionGranted = false;
  
  // WebSocket and recording
  let ws: WebSocket | null = null;
  let recorder: RecordRTC | null = null;
  let audioContext: AudioContext | null = null;
  let stream: MediaStream | null = null;
  let audioQueue: Blob[] = [];
  
  // Transcript history
  let transcriptHistory: Array<{
    type: 'user' | 'cortex';
    text: string;
    mood?: string;
    timestamp: Date;
  }> = [];
  
  // Visual states
  const brainStates = {
    idle: '🧠',
    listening: '👂',
    thinking: '🤔',
    speaking: '🗣️',
    excited: '✨',
    error: '❌'
  };
  
  // Size configurations
  const sizeConfig = {
    small: { button: 'w-12 h-12', icon: 20 },
    medium: { button: 'w-16 h-16', icon: 24 },
    large: { button: 'w-20 h-20', icon: 28 }
  };
  
  onMount(async () => {
    // Initialize Web Audio API
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    
    // Don't check permissions on mount - wait for user interaction
    // This avoids permission errors and allows proper permission prompt
    voicePermissionGranted = true; // Assume granted until proven otherwise
  });
  
  onDestroy(() => {
    if (ws) {
      ws.close();
    }
    if (recorder) {
      recorder.destroy();
    }
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    if (audioContext) {
      audioContext.close();
    }
  });
  
  function connectToVoiceWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) return;
    
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//localhost:8000/api/voice/ws`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('[VoiceChat] Voice WebSocket connected to:', wsUrl);
    };
    
    ws.onmessage = async (event) => {
      console.log('[VoiceChat] WebSocket message received:', event.data);
      if (typeof event.data === 'string') {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      }
    };
    
    ws.onerror = (error) => {
      console.error('[VoiceChat] Voice WebSocket error:', error);
      cortexMood = 'error';
      addNotification({ type: 'error', message: 'Voice connection error. Please refresh and try again.' });
    };
    
    ws.onclose = () => {
      console.log('Voice WebSocket closed');
      ws = null;
    };
  }
  
  async function handleWebSocketMessage(data: any) {
    switch (data.type) {
      case 'chunk_received':
        // Audio chunk acknowledgment
        break;
        
      case 'processing':
        cortexMood = 'thinking';
        break;
        
      case 'transcription':
        // Add user message to transcript
        transcriptHistory = [...transcriptHistory, {
          type: 'user',
          text: data.text,
          timestamp: new Date()
        }];
        showTranscript = true;
        break;
        
      case 'ai_response':
        // Add Cortex response to transcript
        transcriptHistory = [...transcriptHistory, {
          type: 'cortex',
          text: data.personalized_text || data.text,
          mood: data.mood,
          timestamp: new Date()
        }];
        
        // Update mood
        if (data.mood === 'discovering' || data.mood === 'encouraging') {
          cortexMood = 'excited';
        } else {
          cortexMood = 'speaking';
        }
        break;
        
      case 'audio_response':
        // Play audio response
        if (data.data && audioContext) {
          const audioData = base64ToArrayBuffer(data.data);
          await playAudioResponse(audioData);
        }
        break;
        
      case 'error':
        cortexMood = 'error';
        addNotification({ type: 'error', message: data.message || 'Voice processing error' });
        isProcessing = false;
        break;
    }
  }
  
  async function startRecording() {
    try {
      // Request microphone permission when user clicks
      // This will show the browser's permission prompt
      // Connect to WebSocket if not connected
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        connectToVoiceWebSocket();
        // Wait for connection
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      // Get microphone stream - this will trigger permission prompt if needed
      stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      // If we get here, permission was granted
      voicePermissionGranted = true;
      
      // Create recorder
      recorder = new RecordRTC(stream, {
        type: 'audio',
        mimeType: 'audio/webm',
        recorderType: RecordRTC.StereoAudioRecorder,
        timeSlice: 100, // Send chunks every 100ms
        ondataavailable: (blob: Blob) => {
          // Send audio chunks to server
          if (ws && ws.readyState === WebSocket.OPEN) {
            console.log('[VoiceChat] Sending audio chunk, size:', blob.size);
            blob.arrayBuffer().then(buffer => {
              ws!.send(buffer);
            });
          } else {
            console.error('[VoiceChat] WebSocket not ready for audio chunk');
          }
        }
      });
      
      recorder.startRecording();
      isRecording = true;
      cortexMood = 'listening';
      console.log('[VoiceChat] Recording started');
      
      // Haptic feedback on mobile
      if ('vibrate' in navigator) {
        navigator.vibrate(50);
      }
      
    } catch (err) {
      console.error('Failed to start recording:', err);
      if (err.name === 'NotAllowedError') {
        addNotification({ 
          type: 'error', 
          message: 'Microphone blocked. Go to chrome://settings/content/microphone and allow localhost:3004' 
        });
      } else {
        addNotification({ type: 'error', message: 'Failed to start recording: ' + err.message });
      }
      cortexMood = 'error';
    }
  }
  
  function stopRecording() {
    if (!recorder || !isRecording) return;
    
    recorder.stopRecording(() => {
      console.log('[VoiceChat] Recording stopped, WebSocket state:', ws?.readyState);
      // Signal end of audio
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'end_recording' }));
        console.log('[VoiceChat] Sent end_recording signal');
      } else {
        console.error('[VoiceChat] WebSocket not open, cannot send audio');
        addNotification({ type: 'error', message: 'Voice connection lost. Please try again.' });
      }
      
      isRecording = false;
      isProcessing = true;
      cortexMood = 'thinking';
      
      // Clean up
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
      }
      
      // Haptic feedback
      if ('vibrate' in navigator) {
        navigator.vibrate([50, 50]);
      }
    });
  }
  
  async function playAudioResponse(audioData: ArrayBuffer) {
    if (!audioContext) return;
    
    try {
      const audioBuffer = await audioContext.decodeAudioData(audioData);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      
      source.onended = () => {
        isProcessing = false;
        cortexMood = 'idle';
      };
      
      source.start();
      cortexMood = 'speaking';
      
    } catch (err) {
      console.error('Failed to play audio:', err);
      isProcessing = false;
      cortexMood = 'idle';
    }
  }
  
  function base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }
  
  function toggleExpanded() {
    isExpanded = !isExpanded;
  }
  
  function clearTranscript() {
    transcriptHistory = [];
    showTranscript = false;
  }
  
  // Touch event handlers for mobile
  function handleTouchStart(e: TouchEvent) {
    e.preventDefault();
    startRecording();
  }
  
  function handleTouchEnd(e: TouchEvent) {
    e.preventDefault();
    stopRecording();
  }
</script>

<div class="voice-chat-container {position}" class:expanded={isExpanded}>
  {#if isExpanded}
    <div class="voice-chat-expanded" transition:fly={{ y: 20, duration: 300 }}>
      <div class="expanded-header">
        <div class="cortex-info">
          <span class="brain-icon">{brainStates[cortexMood]}</span>
          <div>
            <h3>Cortex</h3>
            <p>Your Prefrontal Assistant</p>
          </div>
        </div>
        <button on:click={toggleExpanded} class="close-button">
          <Icon name="x" size={20} />
        </button>
      </div>
      
      {#if showTranscript && transcriptHistory.length > 0}
        <div class="transcript-container">
          {#each transcriptHistory as message}
            <div class="message {message.type}">
              <span class="message-type">{message.type === 'user' ? 'You' : 'Cortex'}</span>
              <p>{message.text}</p>
              <span class="timestamp">{message.timestamp.toLocaleTimeString()}</span>
            </div>
          {/each}
        </div>
        <button on:click={clearTranscript} class="clear-button">
          Clear transcript
        </button>
      {/if}
    </div>
  {/if}
  
  <button
    class="voice-button {sizeConfig[size].button}"
    class:recording={isRecording}
    class:processing={isProcessing}
    on:mousedown={startRecording}
    on:mouseup={stopRecording}
    on:mouseleave={stopRecording}
    on:touchstart={handleTouchStart}
    on:touchend={handleTouchEnd}
    on:click={!isRecording && !isProcessing ? toggleExpanded : null}
    disabled={false}
    aria-label={isRecording ? 'Recording...' : 'Hold to speak'}
  >
    <div class="button-content">
      {#if isRecording}
        <div class="recording-indicator">
          <span class="pulse"></span>
          <Icon name="mic" size={sizeConfig[size].icon} />
        </div>
      {:else if isProcessing}
        <div class="processing-indicator">
          <span class="brain-state">{brainStates[cortexMood]}</span>
        </div>
      {:else}
        <Icon name="mic" size={sizeConfig[size].icon} />
      {/if}
    </div>
    
    {#if !voicePermissionGranted}
      <div class="permission-warning" title="Microphone permission required">
        <Icon name="alert-circle" size={16} />
      </div>
    {/if}
  </button>
</div>

<style>
  .voice-chat-container {
    position: fixed;
    z-index: 1000;
    transition: all 0.3s ease;
  }
  
  .voice-chat-container.bottom-right {
    bottom: 2rem;
    right: 2rem;
  }
  
  .voice-chat-container.bottom-left {
    bottom: 2rem;
    left: 2rem;
  }
  
  .voice-chat-container.floating {
    bottom: 50%;
    right: 2rem;
    transform: translateY(50%);
  }
  
  .voice-button {
    background: linear-gradient(135deg, var(--accent), var(--accent-hover));
    border: none;
    border-radius: 50%;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: all 0.3s ease;
    position: relative;
    user-select: none;
    -webkit-user-select: none;
    -webkit-touch-callout: none;
  }
  
  .voice-button:hover:not(:disabled) {
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  }
  
  .voice-button:active:not(:disabled) {
    transform: scale(0.95);
  }
  
  .voice-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .voice-button.recording {
    background: linear-gradient(135deg, #dc143c, #8b0000);
    animation: recording-glow 1.5s ease-in-out infinite;
  }
  
  .voice-button.processing {
    background: linear-gradient(135deg, #6a5acd, #483d8b);
  }
  
  @keyframes recording-glow {
    0%, 100% {
      box-shadow: 0 0 20px rgba(220, 20, 60, 0.6);
    }
    50% {
      box-shadow: 0 0 30px rgba(220, 20, 60, 0.8);
    }
  }
  
  .button-content {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
  }
  
  .recording-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
  }
  
  .pulse {
    position: absolute;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    animation: pulse 1s infinite;
  }
  
  @keyframes pulse {
    0% {
      transform: scale(1);
      opacity: 1;
    }
    100% {
      transform: scale(1.5);
      opacity: 0;
    }
  }
  
  .processing-indicator {
    animation: rotate 2s linear infinite;
  }
  
  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
  
  .brain-state {
    font-size: 1.5rem;
  }
  
  .permission-warning {
    position: absolute;
    top: -5px;
    right: -5px;
    background: var(--error);
    color: white;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .voice-chat-expanded {
    position: absolute;
    bottom: calc(100% + 1rem);
    right: 0;
    width: 350px;
    max-height: 500px;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 1rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  .expanded-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--border);
    background: var(--bg-secondary);
  }
  
  .cortex-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .cortex-info h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
  }
  
  .cortex-info p {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
  
  .brain-icon {
    font-size: 2rem;
  }
  
  .close-button {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 0.5rem;
    transition: all 0.2s ease;
  }
  
  .close-button:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  .transcript-container {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .message {
    padding: 0.75rem;
    border-radius: 0.75rem;
    animation: fadeIn 0.3s ease;
  }
  
  .message.user {
    background: var(--bg-secondary);
    margin-left: 2rem;
  }
  
  .message.cortex {
    background: linear-gradient(135deg, rgba(106, 90, 205, 0.1), rgba(72, 61, 139, 0.1));
    margin-right: 2rem;
  }
  
  .message-type {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
  }
  
  .message p {
    margin: 0.25rem 0 0.5rem;
    line-height: 1.5;
  }
  
  .timestamp {
    font-size: 0.75rem;
    color: var(--text-tertiary);
  }
  
  .clear-button {
    padding: 0.75rem;
    background: var(--bg-secondary);
    border: none;
    border-top: 1px solid var(--border);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .clear-button:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @media (max-width: 768px) {
    .voice-chat-container.bottom-right,
    .voice-chat-container.bottom-left {
      bottom: 1rem;
      right: 1rem;
      left: auto;
    }
    
    .voice-chat-expanded {
      width: calc(100vw - 2rem);
      right: -1rem;
    }
  }
</style>