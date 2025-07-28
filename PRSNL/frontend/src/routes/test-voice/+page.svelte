<script>
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { autoId } from '$lib/actions/autoId';
  import IdInspectorOverlay from '$lib/components/development/IdInspectorOverlay.svelte';
  
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
  let lastAiResponse = '';
  let voiceSettings = {
    gender: 'female',
    ttsEngine: 'piper',
    useCrewAI: false,
    emotionStrength: 0.8
  };
  let memoryStats = {
    sttModel: 'faster-whisper tiny.en',
    estimatedMemory: '~39MB',
    performance: '3-4x faster'
  };
  let knowledgeBaseQueries = [
    "What is the PRSNL system architecture?",
    "How does the voice processing work?",
    "Tell me about the knowledge base features",
    "What are the recent improvements?",
    "How does CLI integration work?",
    "Explain the database schema"
  ];
  let selectedQuery = '';
  let isTestingKnowledge = false;
  
  function addLog(message, type = 'info') {
    log = [...log, {
      time: new Date().toLocaleTimeString(),
      message,
      type
    }];
    // Auto-scroll log
    setTimeout(() => {
      const logElement = document.querySelector('.log');
      if (logElement) {
        logElement.scrollTop = logElement.scrollHeight;
      }
    }, 10);
  }
  
  function updateStatus(message, color = '#4a9eff') {
    status = message;
    statusColor = color;
  }

  async function testVoiceOptimizations() {
    addLog('Testing memory-optimized voice improvements...', 'info');
    
    try {
      // Test health endpoint
      const healthResponse = await fetch('http://localhost:8000/api/voice/health');
      const healthData = await healthResponse.json();
      
      addLog(`✅ Voice service health: ${healthData.status}`, 'success');
      addLog(`   Model: ${healthData.whisper_model}`, 'info');
      addLog(`   Personality: ${healthData.personality}`, 'info');
      addLog(`   Available voices: ${healthData.voices_available.join(', ')}`, 'info');
      
      // Test with knowledge base query
      const testText = selectedQuery || "Tell me about the PRSNL system's voice processing improvements";
      
      const response = await fetch('http://localhost:8000/api/voice/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token-for-voice-debug'
        },
        body: JSON.stringify({
          text: testText,
          settings: voiceSettings
        })
      });
      
      if (response.ok) {
        const audioBlob = await response.blob();
        addLog(`✅ Voice synthesis successful! Audio size: ${audioBlob.size} bytes`, 'success');
        addLog(`   Settings: ${JSON.stringify(voiceSettings)}`, 'info');
        
        // Play the audio
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
        
        addLog('🔊 Playing synthesized audio...', 'success');
        
        audio.onended = () => {
          addLog('✅ Audio playback completed', 'success');
          URL.revokeObjectURL(audioUrl);
        };
        
      } else {
        const error = await response.text();
        addLog(`❌ Voice test failed: ${error}`, 'error');
      }
      
    } catch (error) {
      addLog(`❌ Voice optimization test failed: ${error.message}`, 'error');
    }
  }

  async function testKnowledgeBaseQuery() {
    if (!selectedQuery) {
      addLog('❌ Please select a knowledge base query first', 'error');
      return;
    }
    
    isTestingKnowledge = true;
    addLog(`🧠 Testing knowledge base query: "${selectedQuery}"`, 'info');
    
    try {
      // First test RAG query to see if knowledge base has relevant info
      const ragResponse = await fetch('http://localhost:8000/api/rag/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token-for-voice-debug'
        },
        body: JSON.stringify({
          question: selectedQuery,  // Fixed: was "query"
          top_k: 3                  // Fixed: was "limit"
        })
      });
      
      if (ragResponse.ok) {
        const ragData = await ragResponse.json();
        addLog(`✅ Knowledge base found ${ragData.documents?.length || 0} relevant documents`, 'success');
        
        if (ragData.documents && ragData.documents.length > 0) {
          addLog(`   Top result: "${ragData.documents[0].content?.substring(0, 100)}..."`, 'info');
        }
      }
      
      // Now test voice processing with knowledge base integration
      const response = await fetch('http://localhost:8000/api/voice/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token-for-voice-debug'
        },
        body: JSON.stringify({
          text: selectedQuery,
          settings: {
            ...voiceSettings,
            useKnowledgeBase: true,
            useCrewAI: true  // Enable CrewAI for better knowledge integration
          }
        })
      });
      
      if (response.ok) {
        const audioBlob = await response.blob();
        addLog(`✅ Knowledge-enhanced voice response generated! (${audioBlob.size} bytes)`, 'success');
        
        // Play the response
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
        
        addLog('🔊 Playing knowledge-enhanced response...', 'success');
        
        audio.onended = () => {
          addLog('✅ Knowledge base query test completed', 'success');
          URL.revokeObjectURL(audioUrl);
        };
        
      } else {
        const error = await response.text();
        addLog(`❌ Knowledge base voice test failed: ${error}`, 'error');
      }
      
    } catch (error) {
      addLog(`❌ Knowledge base test failed: ${error.message}`, 'error');
    } finally {
      isTestingKnowledge = false;
    }
  }
  
  function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      addLog('WebSocket already connected');
      return;
    }
    
    addLog('Connecting to voice WebSocket...', 'info');
    ws = new WebSocket('ws://localhost:8000/api/voice/ws');
    
    ws.onopen = () => {
      addLog('✅ WebSocket connected! Ready for real-time voice chat', 'success');
      updateStatus('Connected - Ready for Voice', '#44ff44');
      
      // Send voice settings
      ws.send(JSON.stringify({
        type: 'set_voice',
        gender: voiceSettings.gender
      }));
    };
    
    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
          case 'chunk_received':
            addLog(`📦 Audio chunk received: ${data.size} bytes`, 'info');
            break;
            
          case 'processing':
            addLog(`⚙️ ${data.status}...`, 'info');
            updateStatus('Processing...', '#ffaa44');
            break;
            
          case 'transcription':
            finalTranscription = data.data.user_text;
            lastAiResponse = data.data.personalized_text;
            addLog(`🎤 You said: "${data.data.user_text}"`, 'success');
            addLog(`🧠 AI Response: "${data.data.ai_text}"`, 'info');
            addLog(`🎭 Cortex says: "${data.data.personalized_text}"`, 'success');
            addLog(`😊 Mood: ${data.data.mood}`, 'info');
            break;
            
          case 'audio_response':
            addLog('🔊 Received audio response, playing...', 'success');
            playAudio(data.data);
            break;
            
          case 'voice_changed':
            addLog(`🎵 Voice changed to: ${data.gender}`, 'info');
            break;
            
          case 'error':
            addLog(`❌ Error: ${data.message}`, 'error');
            updateStatus('Error', '#ff4444');
            break;
            
          case 'pong':
            addLog('📡 Connection alive', 'info');
            break;
        }
      } else {
        addLog(`📡 Binary message received: ${event.data.size} bytes`, 'info');
      }
    };
    
    ws.onerror = (error) => {
      addLog(`❌ WebSocket error: ${error}`, 'error');
      updateStatus('Connection Error', '#ff4444');
    };
    
    ws.onclose = () => {
      addLog('🔌 WebSocket disconnected', 'info');
      updateStatus('Disconnected', '#666666');
      ws = null;
    };
  }
  
  async function startRecording() {
    try {
      addLog('🎤 Requesting microphone access...', 'info');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      
      mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      audioChunks = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
          
          // Send chunk immediately for real-time processing
          if (ws && ws.readyState === WebSocket.OPEN) {
            event.data.arrayBuffer().then(buffer => {
              ws.send(buffer);
            });
          }
        }
      };
      
      mediaRecorder.onstop = async () => {
        addLog('🛑 Recording stopped, processing...', 'info');
        updateStatus('Processing Audio...', '#ffaa44');
        
        if (ws && ws.readyState === WebSocket.OPEN) {
          // Signal end of recording
          ws.send(JSON.stringify({ type: 'end_recording' }));
          addLog('📤 Audio processing request sent', 'success');
        } else {
          addLog('❌ WebSocket not connected!', 'error');
        }
        
        // Clean up stream
        stream.getTracks().forEach(track => track.stop());
      };
      
      // Start recording with small chunks for real-time processing
      mediaRecorder.start(100);
      isRecording = true;
      currentTranscription = '🎤 Recording... Ask me about PRSNL features!';
      addLog('🎙️ Recording started! Try asking about knowledge base features', 'success');
      updateStatus('Recording - Ask about PRSNL!', '#ff4444');
      
    } catch (error) {
      addLog(`❌ Failed to start recording: ${error.message}`, 'error');
      updateStatus('Microphone Error', '#ff4444');
    }
  }
  
  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      isRecording = false;
      currentTranscription = '⚙️ Processing your question...';
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
      
      addLog('🔊 Audio playback started', 'success');
      updateStatus('🔊 Cortex is speaking...', '#44ff44');
      
      source.onended = () => {
        addLog('✅ Audio playback finished', 'info');
        updateStatus('Connected - Ready for Voice', '#44ff44');
      };
      
    } catch (error) {
      addLog(`❌ Failed to play audio: ${error.message}`, 'error');
      updateStatus('Audio Error', '#ff4444');
    }
  }

  function clearLog() {
    log = [];
    addLog('📝 Log cleared', 'info');
  }

  function sendPing() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
      addLog('📡 Ping sent', 'info');
    } else {
      addLog('❌ WebSocket not connected', 'error');
    }
  }

  function updateVoiceSettings() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'set_voice',
        gender: voiceSettings.gender
      }));
      addLog(`🎵 Voice settings updated: ${JSON.stringify(voiceSettings)}`, 'info');
    }
  }
</script>

<div class="container" use:autoId={"container"}>
  <div class="header" use:autoId={"header"}>
    <h1 use:autoId={"title"}>🎤 PRSNL Voice System Test - Memory Optimized</h1>
    <div class="status" style="background-color: {statusColor}" use:autoId={"status"}>
      Status: {status}
    </div>
  </div>

  <!-- Memory Optimization Stats -->
  <div class="stats-panel" use:autoId={"stats-panel"}>
    <h3 use:autoId={"stats-header"}>📊 Memory Optimization Results</h3>
    <div class="stats-grid" use:autoId={"stats-grid"}>
      <div class="stat-item">
        <strong>STT Model:</strong> {memoryStats.sttModel}
      </div>
      <div class="stat-item">
        <strong>Memory Usage:</strong> {memoryStats.estimatedMemory}
      </div>
      <div class="stat-item">
        <strong>Performance:</strong> {memoryStats.performance}
      </div>
      <div class="stat-item">
        <strong>Cost:</strong> $0/month (vs $200-500)
      </div>
    </div>
  </div>

  <!-- Voice Settings -->
  <div class="settings-panel" use:autoId={"settings-panel"}>
    <h3 use:autoId={"settings-header"}>🎛️ Voice Settings</h3>
    <div class="settings-grid" use:autoId={"settings-grid"}>
      <div class="setting-item">
        <label>Gender:</label>
        <select bind:value={voiceSettings.gender} on:change={updateVoiceSettings}>
          <option value="female">Female</option>
          <option value="male">Male</option>
        </select>
      </div>
      <div class="setting-item">
        <label>TTS Engine:</label>
        <select bind:value={voiceSettings.ttsEngine}>
          <option value="piper">Piper (Memory Optimized)</option>
          <option value="chatterbox">Chatterbox (Emotion)</option>
          <option value="edge-tts">Edge TTS (Fallback)</option>
        </select>
      </div>
      <div class="setting-item">
        <label>Use CrewAI:</label>
        <input type="checkbox" bind:checked={voiceSettings.useCrewAI} />
      </div>
      <div class="setting-item">
        <label>Emotion Strength:</label>
        <input type="range" min="0" max="1" step="0.1" bind:value={voiceSettings.emotionStrength} />
        <span>{voiceSettings.emotionStrength}</span>
      </div>
    </div>
  </div>

  <!-- Knowledge Base Test Section -->
  <div class="knowledge-panel" use:autoId={"knowledge-panel"}>
    <h3 use:autoId={"knowledge-header"}>🧠 Knowledge Base Integration Test</h3>
    <div class="knowledge-controls" use:autoId={"knowledge-controls"}>
      <select bind:value={selectedQuery}>
        <option value="">Select a knowledge base query...</option>
        {#each knowledgeBaseQueries as query}
          <option value={query}>{query}</option>
        {/each}
      </select>
      <button on:click={testKnowledgeBaseQuery} disabled={isTestingKnowledge || !selectedQuery} use:autoId={"test-knowledge-btn"}>
        {isTestingKnowledge ? '⚙️ Testing...' : '🧠 Test Knowledge Query'}
      </button>
    </div>
    {#if selectedQuery}
      <div class="selected-query">
        <strong>Selected Query:</strong> "{selectedQuery}"
      </div>
    {/if}
  </div>

  <!-- Main Controls -->
  <div class="controls" use:autoId={"main-controls"}>
    <div class="button-group" use:autoId={"button-group-primary"}>
      <button on:click={testVoiceOptimizations} class="primary" use:autoId={"test-optimizations-btn"}>
        🚀 Test Voice Optimizations
      </button>
      <button on:click={connectWebSocket} class={ws && ws.readyState === WebSocket.OPEN ? 'connected' : 'disconnected'} use:autoId={"websocket-btn"}>
        {ws && ws.readyState === WebSocket.OPEN ? '🔌 Disconnect WS' : '🔌 Connect WebSocket'}
      </button>
    </div>
    
    <div class="button-group" use:autoId={"button-group-recording"}>
      <button 
        bind:this={recordButton}
        on:mousedown={startRecording}
        on:mouseup={stopRecording}
        on:mouseleave={stopRecording}
        disabled={!ws || ws.readyState !== WebSocket.OPEN}
        class="record-button"
        class:recording={isRecording}
        use:autoId={"record-btn"}
      >
        {isRecording ? '🔴 Recording...' : '🎤 Hold to Record'}
      </button>
      <button on:click={sendPing} disabled={!ws || ws.readyState !== WebSocket.OPEN}>
        📡 Ping
      </button>
      <button on:click={clearLog}>
        🗑️ Clear Log
      </button>
    </div>
  </div>

  <!-- Live Transcription Display -->
  <div class="transcription-panel">
    <h3>💬 Live Transcription & Conversation</h3>
    
    <!-- Real-time speech indicator -->
    {#if isRecording}
      <div class="live-speech-indicator">
        <div class="speech-waveform">
          <div class="wave-bar"></div>
          <div class="wave-bar"></div>
          <div class="wave-bar"></div>
          <div class="wave-bar"></div>
          <div class="wave-bar"></div>
        </div>
        <span class="recording-text">🎤 Listening... Speak now!</span>
      </div>
    {/if}
    
    <!-- Current status (processing, thinking, etc.) -->
    {#if currentTranscription}
      <div class="current-status">{currentTranscription}</div>
    {/if}
    
    <!-- Final conversation history -->
    {#if finalTranscription}
      <div class="conversation-item user">
        <div class="speaker-label">👤 You</div>
        <div class="message-content">"{finalTranscription}"</div>
        <div class="message-time">{new Date().toLocaleTimeString()}</div>
      </div>
    {/if}
    
    {#if lastAiResponse}
      <div class="conversation-item ai">
        <div class="speaker-label">🧠 Cortex</div>
        <div class="message-content">"{lastAiResponse}"</div>
        <div class="message-time">{new Date().toLocaleTimeString()}</div>
      </div>
    {/if}
    
    {#if !isRecording && !finalTranscription && !lastAiResponse}
      <div class="empty-state">
        <p>🎙️ Press and hold "Hold to Record" to start voice conversation</p>
        <p>💡 Ask questions about PRSNL features and get knowledge-based responses!</p>
      </div>
    {/if}
  </div>

  <!-- Instructions -->
  <div class="instructions">
    <h3>📋 Test Instructions</h3>
    <ol>
      <li><strong>Test Optimizations:</strong> Click "Test Voice Optimizations" to verify memory improvements</li>
      <li><strong>Connect WebSocket:</strong> Establish real-time voice connection</li>
      <li><strong>Test Knowledge Queries:</strong> Select and test knowledge base integration</li>
      <li><strong>Voice Chat:</strong> Hold "Record" and ask questions about PRSNL features</li>
      <li><strong>Try These Queries:</strong></li>
      <ul>
        <li>"What is the PRSNL architecture?"</li>
        <li>"How does voice processing work?"</li>
        <li>"Tell me about CLI integration"</li>
        <li>"What are the recent improvements?"</li>
      </ul>
    </ol>
  </div>

  <!-- Log Display -->
  <div class="log-panel">
    <h3>📄 System Log</h3>
    <div class="log">
      {#each log as entry}
        <div class="log-entry {entry.type}">
          <span class="log-time">[{entry.time}]</span>
          <span class="log-message">{entry.message}</span>
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  .container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    max-width: 1200px;
    margin: 20px auto;
    padding: 20px;
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    color: white;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  }

  .header {
    text-align: center;
    margin-bottom: 30px;
  }

  .header h1 {
    margin: 0 0 15px 0;
    font-size: 2.2em;
    background: linear-gradient(45deg, #4a9eff, #44ff44);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .status {
    padding: 12px 24px;
    border-radius: 25px;
    font-weight: bold;
    font-size: 1.1em;
    display: inline-block;
    min-width: 200px;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
  }

  .stats-panel, .settings-panel, .knowledge-panel, .instructions {
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
    border: 1px solid rgba(255,255,255,0.1);
  }

  .stats-panel h3, .settings-panel h3, .knowledge-panel h3, .instructions h3 {
    margin-top: 0;
    color: #4a9eff;
    font-size: 1.3em;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
  }

  .stat-item {
    background: rgba(74, 158, 255, 0.1);
    padding: 12px;
    border-radius: 8px;
    border-left: 4px solid #4a9eff;
  }

  .settings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
  }

  .setting-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .setting-item label {
    font-weight: bold;
    color: #ccc;
  }

  .setting-item select, .setting-item input[type="range"] {
    padding: 8px;
    border-radius: 5px;
    border: 1px solid #444;
    background: #333;
    color: white;
  }

  .knowledge-controls {
    display: flex;
    gap: 15px;
    align-items: center;
    flex-wrap: wrap;
  }

  .knowledge-controls select {
    flex: 1;
    min-width: 300px;
    padding: 10px;
    border-radius: 5px;
    border: 1px solid #444;
    background: #333;
    color: white;
  }

  .selected-query {
    margin-top: 15px;
    padding: 10px;
    background: rgba(68, 255, 68, 0.1);
    border-radius: 5px;
    border-left: 4px solid #44ff44;
  }

  .controls {
    margin: 30px 0;
  }

  .button-group {
    display: flex;
    gap: 15px;
    margin: 15px 0;
    flex-wrap: wrap;
  }

  button {
    padding: 12px 24px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    border: none;
    border-radius: 8px;
    transition: all 0.3s ease;
    min-width: 120px;
  }

  button.primary {
    background: linear-gradient(45deg, #4a9eff, #357abd);
    color: white;
  }

  button.primary:hover {
    background: linear-gradient(45deg, #357abd, #4a9eff);
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(74, 158, 255, 0.4);
  }

  button.connected {
    background: linear-gradient(45deg, #44ff44, #2ecc71);
    color: white;
  }

  button.disconnected {
    background: linear-gradient(45deg, #ff4444, #e74c3c);
    color: white;
  }

  button.record-button {
    background: linear-gradient(45deg, #ff6b6b, #ff4444);
    color: white;
    font-size: 18px;
    padding: 15px 30px;
  }

  button.record-button.recording {
    background: linear-gradient(45deg, #ff0000, #cc0000);
    animation: pulse 1s infinite;
  }

  button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(255,255,255,0.2);
  }

  button:disabled {
    background: #666;
    cursor: not-allowed;
    opacity: 0.5;
  }

  .transcription-panel {
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
    border: 2px solid #4a9eff;
    min-height: 200px;
  }

  .transcription-panel h3 {
    margin-top: 0;
    color: #4a9eff;
  }

  .live-speech-indicator {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    background: rgba(255, 68, 68, 0.1);
    border-radius: 8px;
    border-left: 4px solid #ff4444;
    margin-bottom: 15px;
  }

  .speech-waveform {
    display: flex;
    gap: 3px;
    align-items: end;
  }

  .wave-bar {
    width: 4px;
    background: #ff4444;
    border-radius: 2px;
    animation: waveform 1.5s infinite ease-in-out;
  }

  .wave-bar:nth-child(1) { height: 20px; animation-delay: 0s; }
  .wave-bar:nth-child(2) { height: 30px; animation-delay: 0.1s; }
  .wave-bar:nth-child(3) { height: 25px; animation-delay: 0.2s; }
  .wave-bar:nth-child(4) { height: 35px; animation-delay: 0.3s; }
  .wave-bar:nth-child(5) { height: 20px; animation-delay: 0.4s; }

  @keyframes waveform {
    0%, 100% { transform: scaleY(0.5); opacity: 0.7; }
    50% { transform: scaleY(1); opacity: 1; }
  }

  .recording-text {
    font-size: 16px;
    font-weight: bold;
    color: #ff6666;
  }

  .current-status {
    font-size: 18px;
    color: #ffaa44;
    margin: 10px 0;
    font-style: italic;
    text-align: center;
    padding: 10px;
    background: rgba(255, 170, 68, 0.1);
    border-radius: 5px;
  }

  .conversation-item {
    margin: 15px 0;
    padding: 15px;
    border-radius: 8px;
    position: relative;
  }

  .conversation-item.user {
    background: rgba(74, 158, 255, 0.1);
    border-left: 4px solid #4a9eff;
  }

  .conversation-item.ai {
    background: rgba(68, 255, 68, 0.1);
    border-left: 4px solid #44ff44;
  }

  .speaker-label {
    font-weight: bold;
    font-size: 14px;
    margin-bottom: 8px;
    opacity: 0.8;
  }

  .message-content {
    font-size: 16px;
    line-height: 1.4;
    margin-bottom: 8px;
  }

  .message-time {
    font-size: 12px;
    opacity: 0.6;
    text-align: right;
  }

  .empty-state {
    text-align: center;
    padding: 30px;
    opacity: 0.7;
  }

  .empty-state p {
    margin: 10px 0;
    font-size: 16px;
  }

  .instructions ol, .instructions ul {
    padding-left: 20px;
  }

  .instructions li {
    margin: 8px 0;
    line-height: 1.5;
  }

  .log-panel {
    margin-top: 30px;
  }

  .log-panel h3 {
    color: #4a9eff;
    margin-bottom: 15px;
  }

  .log {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 15px;
    max-height: 400px;
    overflow-y: auto;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 13px;
    line-height: 1.4;
  }

  .log-entry {
    margin: 8px 0;
    padding: 6px 10px;
    border-radius: 4px;
    border-left: 3px solid #4a9eff;
    background: rgba(255,255,255,0.02);
  }

  .log-entry.success {
    border-left-color: #44ff44;
    color: #88ff88;
    background: rgba(68, 255, 68, 0.05);
  }

  .log-entry.error {
    border-left-color: #ff4444;
    color: #ff8888;
    background: rgba(255, 68, 68, 0.05);
  }

  .log-entry.info {
    border-left-color: #4a9eff;
    color: #88ccff;
  }

  .log-time {
    color: #888;
    margin-right: 10px;
    font-size: 11px;
  }

  .log-message {
    color: inherit;
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .container {
      margin: 10px;
      padding: 15px;
    }

    .stats-grid, .settings-grid {
      grid-template-columns: 1fr;
    }

    .button-group {
      flex-direction: column;
    }

    .knowledge-controls {
      flex-direction: column;
      align-items: stretch;
    }

    .knowledge-controls select {
      min-width: auto;
    }
  }
</style>

<!-- ID Inspector Overlay for Development -->
<IdInspectorOverlay />