<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import Icon from '$lib/components/Icon.svelte';
  import StreamingMessage from '$lib/components/StreamingMessage.svelte';
  import { formatDate } from '$lib/utils/date';
  import { createStreamingConnection, type StreamingWebSocket } from '$lib/utils/websocket';
  import { api } from '$lib/api';

  interface ChatMessage {
    id: string;
    type: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    citations?: Citation[];
    suggestedItems?: SuggestedItem[];
    insights?: ChatInsights;
    isStreaming?: boolean;
  }

  interface Citation {
    text?: string;
    item_id?: string;  // Optional since conversations may not have item_id
    title: string;
    url: string;
    permalink?: string;
    type?: string;
    format_label?: string;
  }

  interface SuggestedItem {
    id: string;
    title: string;
    reason: string;
    permalink?: string;
  }

  interface ChatInsights {
    topics_discussed: string[];
    knowledge_gaps: { topic: string; suggestion: string }[];
    exploration_suggestions: { action: string; topic: string; reason: string }[];
  }

  let messages: ChatMessage[] = [];
  let inputMessage = '';
  let isLoading = false;
  let suggestedQuestions: string[] = [];
  let showSuggestions = true;
  let conversationId: string | null = null;
  let ws: StreamingWebSocket | null = null;
  let messagesContainer: HTMLElement;
  let contextItems: string[] = [];
  let currentStreamingMessage: ChatMessage | null = null;
  
  // Multi-modal states
  let isRecording = false;
  let recordingTime = 0;
  let mediaRecorder: MediaRecorder | null = null;
  let audioChunks: Blob[] = [];
  let recordingInterval: NodeJS.Timeout | null = null;
  let voiceWs: WebSocket | null = null;

  // Load suggested questions
  async function loadSuggestedQuestions() {
    try {
      const params = new URLSearchParams();
      if (contextItems.length > 0) {
        params.append('context_items', contextItems.join(','));
      }

      const data = await api.get(`/suggest-questions?${params}`);
      suggestedQuestions = data.questions;
    } catch (error) {
      console.error('Error loading suggested questions:', error);
    }
  }

  // Connect to WebSocket
  function connectWebSocket() {
    // Use the chat endpoint with a unique client ID
    const clientId = Math.random().toString(36).substring(7);

    // Debug logging
    console.debug('[Chat] Connecting to WebSocket with clientId:', clientId);

    ws = createStreamingConnection(`/ws/chat/${clientId}`, {
      onConnect: () => {
        console.debug('[Chat] WebSocket connected successfully');
      },
      onTyping: () => {
        console.debug('[Chat] Typing indicator received');
        isLoading = true;
      },
      onContext: (data) => {
        console.debug('[Chat] Context received:', data);
        // Show context being considered
      },
      onChunk: (text) => {
        console.debug('[Chat] Chunk received:', text);
        if (currentStreamingMessage) {
          currentStreamingMessage.content += text;
          messages = messages;
          scrollToBottom();
        }
      },
      onComplete: (data) => {
        console.debug('[Chat] Message complete:', data);
        if (currentStreamingMessage) {
          currentStreamingMessage.isStreaming = false;
          // Don't append the message content again - we already have it from chunks
          // Only add the metadata
          currentStreamingMessage.citations = data.citations;
          currentStreamingMessage.suggestedItems = data.suggested_items;
          currentStreamingMessage.insights = data.insights;
          currentStreamingMessage = null;
          messages = messages;

          if (!conversationId && data.conversation_id) {
            conversationId = data.conversation_id;
          }

          loadSuggestedQuestions();
        }
        isLoading = false;
      },
      onError: (error) => {
        console.error('[Chat] Error:', error);
        isLoading = false;
        // Show error message to user
        if (currentStreamingMessage) {
          currentStreamingMessage.content = `Error: ${error.message || 'Failed to get response'}`;
          currentStreamingMessage.isStreaming = false;
          messages = messages;
        }
      },
    });

    ws.connect();
  }

  // Send message
  async function sendMessage(message: string = inputMessage) {
    if (!message.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: message,
      timestamp: new Date(),
    };

    messages = [...messages, userMessage];
    inputMessage = '';
    isLoading = true;
    showSuggestions = false;

    // Create assistant message placeholder
    currentStreamingMessage = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    messages = [...messages, currentStreamingMessage];
    scrollToBottom();

    // Send via WebSocket
    if (ws?.isConnected) {
      console.debug('[Chat] Sending message:', message);

      // Build conversation history
      const history = messages.slice(0, -2).map((msg) => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
      }));

      ws.send({
        message: message,
        history: history,
        conversation_id: conversationId,
        context_items: contextItems.length > 0 ? contextItems : null,
      });
    } else {
      console.error('[Chat] WebSocket not connected');
      isLoading = false;
      // Remove the placeholder message
      messages = messages.slice(0, -1);
      // Show error to user
      alert('Chat connection lost. Please refresh the page.');
    }
  }

  // Navigate to item
  function navigateToItem(itemId?: string, permalink?: string) {
    // Use permalink if available, otherwise fall back to item ID
    if (permalink) {
      window.location.href = permalink;
    } else if (itemId) {
      window.location.href = `/items/${itemId}`;
    } else {
      console.error('No navigation target available');
    }
  }

  // Scroll to bottom
  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  // Handle key press
  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  // Audio recording functions
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        
        // Connect to voice WebSocket if not connected
        if (!voiceWs || voiceWs.readyState !== WebSocket.OPEN) {
          await connectVoiceWebSocket();
        }
        
        // Send audio to voice WebSocket
        if (voiceWs && voiceWs.readyState === WebSocket.OPEN) {
          const reader = new FileReader();
          reader.onload = () => {
            voiceWs!.send(reader.result as ArrayBuffer);
            voiceWs!.send(JSON.stringify({ type: 'end_recording' }));
          };
          reader.readAsArrayBuffer(audioBlob);
        }
      };
      
      mediaRecorder.start();
      isRecording = true;
      recordingTime = 0;
      
      recordingInterval = setInterval(() => {
        recordingTime++;
      }, 1000);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      if (error.name === 'NotAllowedError') {
        // User denied permission or it was blocked
        alert('Microphone permission is required for voice recording. Please click "Allow" when prompted by your browser.');
      } else if (error.name === 'NotFoundError') {
        alert('No microphone found. Please connect a microphone and try again.');
      } else {
        alert('Unable to access microphone. Please check your permissions.');
      }
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      isRecording = false;
      
      if (recordingInterval) {
        clearInterval(recordingInterval);
        recordingInterval = null;
      }
      
      // Stop all tracks
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
  }

  // File handling
  function handleImageUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      console.log('Image selected:', file);
      // TODO: Process and send image
    }
  }

  function handleFileUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      console.log('File selected:', file);
      // TODO: Process and send file
    }
  }

  // Voice WebSocket connection
  function connectVoiceWebSocket(): Promise<void> {
    return new Promise((resolve) => {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/voice/ws`;
      voiceWs = new WebSocket(wsUrl);
      
      voiceWs.onopen = () => {
        console.log('[Chat] Voice WebSocket connected');
        resolve();
      };
      
      voiceWs.onmessage = async (event) => {
        if (typeof event.data === 'string') {
          const data = JSON.parse(event.data);
          console.log('[Voice] Received message:', data.type, data);
          
          switch (data.type) {
            case 'chunk_received':
              // Audio chunk acknowledgment - could add visual feedback here
              console.log('[Voice] Audio chunk received:', data.size, 'bytes');
              break;
              
            case 'processing':
              // Show processing indicator
              console.log('[Voice] Processing audio:', data.status);
              // Add a temporary processing message
              messages = [...messages, {
                id: `processing-${Date.now()}`,
                type: 'assistant',
                content: '🤔 Cortex is thinking...',
                timestamp: new Date(),
                isStreaming: true
              }];
              scrollToBottom();
              break;
              
            case 'transcription':
              // Remove any processing messages
              messages = messages.filter(m => !m.isStreaming);
              
              // Add user message with transcription
              messages = [...messages, {
                id: `user-${Date.now()}`,
                type: 'user',
                content: data.data.user_text,
                timestamp: new Date()
              }];
              
              // Add AI response with knowledge context indicator
              const aiContent = data.data.personalized_text;
              const hasKnowledge = data.data.ai_text !== data.data.user_text; // Simple check for knowledge usage
              const contextIndicator = hasKnowledge ? '🧠 ' : '';
              
              messages = [...messages, {
                id: `assistant-${Date.now()}`,
                type: 'assistant',
                content: contextIndicator + aiContent,
                timestamp: new Date()
              }];
              
              scrollToBottom();
              break;
              
            case 'audio_response':
              if (data.data) {
                console.log('[Voice] Playing audio response');
                await playAudioResponse(data.data);
              }
              break;
              
            case 'error':
              console.error('[Voice] Error:', data.message);
              // Remove any processing messages
              messages = messages.filter(m => !m.isStreaming);
              // Could add error message to chat
              break;
              
            case 'pong':
              console.log('[Voice] WebSocket keepalive');
              break;
              
            default:
              console.log('[Voice] Unknown message type:', data.type);
          }
        }
      };
      
      voiceWs.onerror = (error) => {
        console.error('[Chat] Voice WebSocket error:', error);
      };
    });
  }
  
  async function playAudioResponse(base64Data: string) {
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
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  }

  onMount(() => {
    loadSuggestedQuestions();
    connectWebSocket();

    // Check for context items from URL
    const urlContextItems = $page.url.searchParams.get('context');
    if (urlContextItems) {
      contextItems = urlContextItems.split(',');
    }
  });

  onDestroy(() => {
    if (ws) {
      ws.close();
    }
    if (voiceWs) {
      voiceWs.close();
    }
    stopRecording();
  });
</script>

<div class="chat-page">
  <div class="chat-header">
    <div class="header-content">
      <h1 class="page-title">
        <div class="brain-icon">
          <Icon name="brain" size={32} />
          <div class="pulse-ring"></div>
        </div>
        Second Brain Chat
      </h1>
    </div>
  </div>

  <div class="chat-container">
    <div class="messages-area" bind:this={messagesContainer}>
      {#if messages.length === 0 && showSuggestions}
        <div class="welcome-message">
          <div class="welcome-animation">
            <div class="brain-visualization">
              <Icon name="brain" size={60} />
            </div>
          </div>

          <h2>Welcome to your Second Brain</h2>
          <p class="welcome-subtitle">
            I'm here to help you explore, understand, and connect your knowledge.
          </p>

          {#if suggestedQuestions.length > 0}
            <div class="suggested-questions">
              <h3>Let's get started with:</h3>
              <div class="questions-grid">
                {#each suggestedQuestions as question, i}
                  <button
                    class="suggestion-card"
                    on:click={() => sendMessage(question)}
                    style="animation-delay: {i * 0.1}s"
                  >
                    <div class="suggestion-icon">
                      <Icon name="sparkles" size={16} />
                    </div>
                    <span>{question}</span>
                  </button>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      {/if}

      {#each messages as message}
        <div class="message-wrapper {message.type}">
          {#if message.isStreaming}
            <!-- For streaming messages, show content directly without character animation -->
            <div class="message-container {message.type}">
              <div class="avatar">
                <Icon name={message.type === 'user' ? 'user' : 'brain'} />
              </div>
              <div class="message-content">
                <div class="message-bubble">
                  <span class="text">{message.content}</span>
                  <span class="cursor">|</span>
                </div>
              </div>
            </div>
          {:else}
            <!-- For completed messages, use the StreamingMessage component without streaming -->
            <StreamingMessage
              message={message.content}
              isStreaming={false}
              role={message.type}
              onComplete={() => {}}
            />
          {/if}

          {#if message.citations && message.citations.length > 0}
            <div class="message-metadata citations">
              <h4><Icon name="link" size={14} /> Sources</h4>
              <div class="citations-list">
                {#each message.citations as citation}
                  <button
                    class="citation-chip"
                    on:click={() => navigateToItem(citation.item_id, citation.permalink)}
                    title="{citation.format_label || 'Link'}: {citation.title}"
                  >
                    <span class="format-label">{citation.format_label || '📎 Link'}</span>
                    <span class="citation-title">{citation.title}</span>
                  </button>
                {/each}
              </div>
            </div>
          {/if}

          {#if message.insights && message.insights.topics_discussed.length > 0}
            <div class="message-metadata insights">
              <div class="insight-chips">
                {#each message.insights.topics_discussed as topic}
                  <span class="topic-chip">{topic}</span>
                {/each}
              </div>
            </div>
          {/if}

          {#if message.suggestedItems && message.suggestedItems.length > 0}
            <div class="message-metadata suggestions">
              <h4><Icon name="compass" size={14} /> Explore Further</h4>
              <div class="suggestions-list">
                {#each message.suggestedItems as item}
                  <button
                    class="suggestion-item"
                    on:click={() => navigateToItem(item.id, item.permalink)}
                  >
                    <Icon name="arrow-right" size={14} />
                    <div>
                      <div class="item-title">{item.title}</div>
                      <div class="item-reason">{item.reason}</div>
                    </div>
                  </button>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <div class="input-area">
      <div class="input-container">
        <div class="input-wrapper">
          <div class="input-actions-left">
            <button 
              class="input-action-button voice-button" 
              class:recording={isRecording}
              title={isRecording ? "Release to send" : "Hold to speak"} 
              aria-label={isRecording ? "Recording voice message" : "Hold to record voice message"}
              on:mousedown={startRecording}
              on:mouseup={stopRecording}
              on:mouseleave={stopRecording}
              on:touchstart|preventDefault={startRecording}
              on:touchend|preventDefault={stopRecording}
            >
              <Icon name="mic" size={20} />
              {#if isRecording}
                <span class="recording-indicator"></span>
              {/if}
            </button>
            
            <label class="input-action-button" title="Upload image" aria-label="Upload image">
              <Icon name="image" size={20} />
              <input type="file" accept="image/*" on:change={handleImageUpload} class="hidden-input" aria-label="Choose image file" />
            </label>
            
            <label class="input-action-button" title="Attach file" aria-label="Upload document">
              <Icon name="file-text" size={20} />
              <input type="file" accept=".pdf,.doc,.docx,.txt,.md,.js,.ts,.py,.json" on:change={handleFileUpload} class="hidden-input" aria-label="Choose document file" />
            </label>
          </div>

          <textarea
            class="message-input"
            placeholder="Ask your Second Brain anything..."
            bind:value={inputMessage}
            on:keypress={handleKeyPress}
            rows="1"
          ></textarea>

          <div class="input-actions-right">
            {#if contextItems.length > 0}
              <button class="context-indicator" title="{contextItems.length} items in context">
                <Icon name="layers" size={16} />
                <span>{contextItems.length}</span>
              </button>
            {/if}

            <button
              class="send-button"
              on:click={() => sendMessage()}
              disabled={!inputMessage.trim() || isLoading}
              class:pulse={inputMessage.trim() && !isLoading}
              aria-label="Send message"
              title="Send message"
            >
              <Icon name="send" size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .chat-page {
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    position: relative;
  }

  /* Header */
  .chat-header {
    background: rgba(26, 26, 26, 0.8);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    position: relative;
    z-index: 10;
  }

  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1.5rem 2rem;
  }

  .page-title {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 1.75rem;
    font-weight: 600;
    color: white;
    margin: 0;
  }

  .brain-icon {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6366f1;
  }

  .pulse-ring {
    position: absolute;
    inset: -8px;
    border: 2px solid #6366f1;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
      opacity: 1;
    }
    100% {
      transform: scale(1.3);
      opacity: 0;
    }
  }

  /* Chat Container */
  .chat-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    width: 100%;
    position: relative;
    z-index: 1;
  }

  .messages-area {
    flex: 1;
    overflow-y: auto;
    padding: 2rem;
    scroll-behavior: smooth;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
  }

  /* Welcome Message */
  .welcome-message {
    text-align: center;
    padding: 3rem 1rem;
    animation: fadeIn 0.6s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .welcome-animation {
    margin-bottom: 2rem;
  }

  .brain-visualization {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: #6366f1;
    animation: float 3s ease-in-out infinite;
  }

  @keyframes float {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-10px);
    }
  }

  .welcome-message h2 {
    font-size: 2rem;
    margin: 1rem 0;
    color: white;
  }

  .welcome-subtitle {
    font-size: 1.125rem;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 2rem;
  }

  /* Suggested Questions */
  .suggested-questions {
    max-width: 600px;
    margin: 0 auto;
  }

  .suggested-questions h3 {
    font-size: 1rem;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 1rem;
  }

  .questions-grid {
    display: grid;
    gap: 0.75rem;
  }

  .suggestion-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1.25rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    text-align: left;
    color: white;
    cursor: pointer;
    transition: all 0.3s;
    animation: slideIn 0.5s ease-out backwards;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .suggestion-card:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: #6366f1;
    transform: translateX(8px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  }

  .suggestion-icon {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(99, 102, 241, 0.2);
    border-radius: 50%;
    flex-shrink: 0;
    color: #6366f1;
  }

  /* Messages */
  .message-wrapper {
    margin-bottom: 2rem;
    animation: messageSlide 0.4s ease-out;
  }

  /* Inline message styles for streaming */
  .message-container {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .message-container.user {
    flex-direction: row-reverse;
  }

  .avatar {
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    flex-shrink: 0;
  }

  .user .avatar {
    background: #6366f1;
    color: white;
  }

  .message-content {
    flex: 1;
    max-width: 70%;
  }

  .user .message-content {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }

  .message-bubble {
    position: relative;
    padding: 1rem 1.25rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1.25rem;
    display: inline-block;
  }

  .user .message-bubble {
    background: #6366f1;
    color: white;
    border: none;
  }

  .text {
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .cursor {
    display: inline-block;
    width: 2px;
    height: 1.2em;
    background: #6366f1;
    margin-left: 2px;
    vertical-align: text-bottom;
    animation: blink 1s infinite;
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

  @keyframes messageSlide {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Message Metadata */
  .message-metadata {
    margin-top: 1rem;
    margin-left: 3.5rem;
  }

  .message-metadata h4 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.6);
    margin: 0 0 0.75rem;
  }

  .citations-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .citation-chip {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 2rem;
    color: #a5b4fc;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    max-width: 100%;
    overflow: hidden;
  }
  
  .format-label {
    font-size: 1rem;
    flex-shrink: 0;
  }
  
  .citation-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .citation-chip:hover {
    background: rgba(99, 102, 241, 0.2);
    border-color: #6366f1;
    transform: translateY(-2px);
  }

  .insight-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .topic-chip {
    padding: 0.25rem 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 2rem;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.75rem;
  }

  .suggestions-list {
    display: grid;
    gap: 0.75rem;
  }

  .suggestion-item {
    display: flex;
    gap: 0.75rem;
    padding: 1rem;
    background: rgba(16, 185, 129, 0.05);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 0.75rem;
    text-align: left;
    cursor: pointer;
    transition: all 0.2s;
  }

  .suggestion-item:hover {
    background: rgba(16, 185, 129, 0.1);
    border-color: #10b981;
    transform: translateX(4px);
  }

  .item-title {
    font-weight: 500;
    color: white;
    margin-bottom: 0.25rem;
  }

  .item-reason {
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.6);
  }

  /* Input Area */
  .input-area {
    padding: 1.5rem 2rem 2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(10, 10, 10, 0.95);
    backdrop-filter: blur(20px);
    position: relative;
    z-index: 10;
  }

  .input-container {
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
  }

  .input-wrapper {
    display: flex;
    align-items: flex-end;
    gap: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1.5rem;
    padding: 0.75rem;
    transition: all 0.3s;
  }

  .input-wrapper:focus-within {
    border-color: #6366f1;
    box-shadow: 0 0 30px rgba(99, 102, 241, 0.2);
  }

  .input-actions-left {
    display: flex;
    gap: 0.5rem;
    flex-shrink: 0;
  }

  .input-action-button {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.75rem;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    transition: all 0.2s;
  }

  .input-action-button:hover {
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border-color: rgba(255, 255, 255, 0.2);
  }

  .input-action-button.voice-button {
    position: relative;
    background: rgba(99, 102, 241, 0.1);
    border-color: rgba(99, 102, 241, 0.3);
    color: #6366f1;
  }

  .input-action-button.voice-button:hover {
    background: rgba(99, 102, 241, 0.2);
    border-color: rgba(99, 102, 241, 0.5);
  }

  .input-action-button.voice-button:active {
    transform: scale(0.95);
  }

  .input-action-button.voice-button.recording {
    background: rgba(239, 68, 68, 0.3);
    border-color: #ef4444;
    color: white;
    animation: pulse 1s ease-in-out infinite;
  }

  .recording-indicator {
    position: absolute;
    top: 4px;
    right: 4px;
    width: 6px;
    height: 6px;
    background: #ef4444;
    border-radius: 50%;
    animation: blink 1s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% {
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
    }
    50% {
      box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
    }
  }

  @keyframes blink {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.3;
    }
  }

  .hidden-input {
    display: none;
  }

  label.input-action-button {
    cursor: pointer;
  }

  .message-input {
    flex: 1;
    background: none;
    border: none;
    color: white;
    resize: none;
    min-height: 1.5rem;
    max-height: 8rem;
    line-height: 1.5;
    font-size: 1rem;
    padding: 0.5rem 0;
  }

  .message-input:focus {
    outline: none;
  }

  .message-input::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }

  .input-actions-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
  }

  .context-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 2rem;
    color: white;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .context-indicator:hover {
    background: rgba(255, 255, 255, 0.15);
  }

  .send-button {
    position: relative;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #6366f1;
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.3s;
  }

  .send-button:hover:not(:disabled) {
    transform: scale(1.1);
    box-shadow: 0 0 30px rgba(99, 102, 241, 0.5);
  }

  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .send-button.pulse {
    animation: pulse 2s infinite;
  }

  /* Scrollbar */
  .messages-area::-webkit-scrollbar {
    width: 8px;
  }

  .messages-area::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
  }

  .messages-area::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
  }

  .messages-area::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .header-content {
      padding: 1rem;
    }

    .page-title {
      font-size: 1.5rem;
    }

    .messages-area {
      padding: 1rem;
    }

    .message-metadata {
      margin-left: 0;
    }

    .input-area {
      padding: 1rem;
    }

    .input-actions-left {
      display: none; /* Hide on mobile for now */
    }

    .message-content {
      max-width: 85%;
    }
  }
</style>