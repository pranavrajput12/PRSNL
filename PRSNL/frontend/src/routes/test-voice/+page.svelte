<script>
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  
  // Set a dummy token to avoid auth errors on test page
  onMount(() => {
    if (browser && !localStorage.getItem('token')) {
      localStorage.setItem('token', 'test-token-for-voice-debug');
    }
  });
  
  let log = [];
  let status = 'Ready';
  let statusColor = '#4a9eff';
  let ws = null;
  let mediaRecorder = null;
  let audioChunks = [];
  let recordButton;
  let isRecording = false;
  let currentTranscription = '';
  let finalTranscription = '';
  
  function addLog(message, type = 'info') {
    log = [...log, {
      time: new Date().toLocaleTimeString(),
      message,
      type
    }];
  }
  
  function updateStatus(message, color = '#4a9eff') {
    status = message;
    statusColor = color;
  }
  
  async function testVoice() {
    addLog('Testing voice endpoint...');
    try {
      const response = await fetch('http://localhost:8000/api/voice/test', {
        method: 'POST'
      });
      const data = await response.json();
      addLog(`Voice test successful! Audio size: ${data.audio_size} bytes`, 'success');
      addLog(`Mood: ${data.mood}, Text: "${data.personalized_text}"`, 'success');
    } catch (error) {
      addLog(`Voice test failed: ${error.message}`, 'error');
    }
  }
  
  function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      addLog('WebSocket already connected');
      return;
    }
    
    addLog('Connecting to WebSocket...');
    ws = new WebSocket('ws://localhost:8000/api/voice/ws');
    
    ws.onopen = () => {
      addLog('WebSocket connected!', 'success');
      updateStatus('Connected', '#44ff44');
    };
    
    ws.onmessage = (event) => {
      addLog(`WebSocket message: ${event.data}`);
      if (typeof event.data === 'string') {
        const data = JSON.parse(event.data);
        addLog(`Message type: ${data.type}`);
        
        if (data.type === 'transcription') {
          // Show what was transcribed
          finalTranscription = data.data.user_text;
          addLog(`Transcribed: "${data.data.user_text}"`, 'info');
          addLog(`AI Response: "${data.data.ai_text}"`, 'info');
          addLog(`Personalized: "${data.data.personalized_text}"`, 'info');
          addLog(`Mood: ${data.data.mood}`, 'info');
        }
        
        if (data.type === 'audio_response' && data.data) {
          addLog('Received audio response, playing...', 'success');
          playAudio(data.data);
        }
      }
    };
    
    ws.onerror = (error) => {
      addLog(`WebSocket error: ${error}`, 'error');
      updateStatus('Error', '#ff4444');
    };
    
    ws.onclose = () => {
      addLog('WebSocket disconnected');
      updateStatus('Disconnected', '#666666');
      ws = null;
    };
  }
  
  async function startRecording() {
    try {
      addLog('Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
          addLog(`Audio chunk received: ${event.data.size} bytes`);
        }
      };
      
      mediaRecorder.onstop = async () => {
        addLog('Recording stopped, processing audio...');
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        addLog(`Total audio size: ${audioBlob.size} bytes`);
        
        if (ws && ws.readyState === WebSocket.OPEN) {
          const reader = new FileReader();
          reader.onload = () => {
            const arrayBuffer = reader.result;
            ws.send(arrayBuffer);
            addLog('Audio sent to server', 'success');
            ws.send(JSON.stringify({ type: 'end_recording' }));
            addLog('End recording signal sent', 'success');
          };
          reader.readAsArrayBuffer(audioBlob);
        } else {
          addLog('WebSocket not connected!', 'error');
        }
        
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start(100);
      isRecording = true;
      currentTranscription = 'Recording...';
      addLog('Recording started...', 'success');
      updateStatus('Recording...', '#ff4444');
      
    } catch (error) {
      addLog(`Failed to start recording: ${error.message}`, 'error');
    }
  }
  
  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      isRecording = false;
      currentTranscription = 'Processing audio...';
      updateStatus('Processing...', '#ffaa44');
    }
  }
  
  async function playAudio(base64Data) {
    try {
      const audioContext = new AudioContext();
      const binaryString = atob(base64Data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start();
      
      addLog('Audio playback started', 'success');
      updateStatus('Playing response...', '#44ff44');
      
      source.onended = () => {
        addLog('Audio playback finished');
        updateStatus('Connected', '#44ff44');
      };
      
    } catch (error) {
      addLog(`Failed to play audio: ${error.message}`, 'error');
    }
  }
</script>

<div class="container">
  <h1>Voice Chat Debug Tool</h1>
  <div class="status" style="background-color: {statusColor}">Status: {status}</div>
  
  <div class="buttons">
    <button on:click={testVoice}>Test Voice Endpoint</button>
    <button 
      bind:this={recordButton}
      on:mousedown={startRecording}
      on:mouseup={stopRecording}
      on:mouseleave={stopRecording}
      disabled={!ws || ws.readyState !== WebSocket.OPEN}
    >
      {isRecording ? 'Recording...' : 'Hold to Record'}
    </button>
    <button on:click={connectWebSocket}>
      {ws && ws.readyState === WebSocket.OPEN ? 'Disconnect' : 'Connect WebSocket'}
    </button>
  </div>
  
  {#if currentTranscription || finalTranscription}
    <div class="transcription-box">
      <h3>Transcription:</h3>
      <div class="current-transcription">{currentTranscription}</div>
      {#if finalTranscription}
        <div class="final-transcription">Last: "{finalTranscription}"</div>
      {/if}
    </div>
  {/if}
  
  <h3>Log:</h3>
  <div class="log">
    {#each log as entry}
      <div class="log-entry {entry.type}">
        [{entry.time}] {entry.message}
      </div>
    {/each}
  </div>
</div>

<style>
  .container {
    font-family: Arial, sans-serif;
    max-width: 800px;
    margin: 50px auto;
    padding: 20px;
    background: #1a1a1a;
    color: white;
  }
  
  .buttons {
    display: flex;
    gap: 10px;
    margin: 20px 0;
  }
  
  button {
    padding: 15px 30px;
    font-size: 18px;
    cursor: pointer;
    background: #4a9eff;
    color: white;
    border: none;
    border-radius: 5px;
    transition: background 0.3s;
  }
  
  button:hover {
    background: #357abd;
  }
  
  button:disabled {
    background: #666;
    cursor: not-allowed;
  }
  
  .status {
    padding: 10px;
    margin: 10px 0;
    border-radius: 5px;
    font-weight: bold;
    text-align: center;
  }
  
  .log {
    background: #2a2a2a;
    padding: 20px;
    border-radius: 5px;
    margin-top: 20px;
    max-height: 400px;
    overflow-y: auto;
    font-family: monospace;
    font-size: 14px;
  }
  
  .log-entry {
    margin: 5px 0;
    padding: 5px;
    border-left: 3px solid #4a9eff;
    padding-left: 10px;
  }
  
  .log-entry.error {
    border-left-color: #ff4444;
    color: #ff6666;
  }
  
  .log-entry.success {
    border-left-color: #44ff44;
    color: #66ff66;
  }
  
  .transcription-box {
    background: #2a2a2a;
    padding: 20px;
    border-radius: 5px;
    margin: 20px 0;
    border: 2px solid #4a9eff;
  }
  
  .transcription-box h3 {
    margin-top: 0;
    color: #4a9eff;
  }
  
  .current-transcription {
    font-size: 20px;
    color: #ffffff;
    margin: 10px 0;
    min-height: 30px;
  }
  
  .final-transcription {
    font-size: 16px;
    color: #aaaaaa;
    margin-top: 10px;
    font-style: italic;
  }
</style>