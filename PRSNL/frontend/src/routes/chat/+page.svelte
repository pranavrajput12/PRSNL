<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { spring, tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import Icon from '$lib/components/Icon.svelte';
  import StreamingMessage from '$lib/components/StreamingMessage.svelte';
  import { formatDate } from '$lib/utils/date';
  import { createStreamingConnection, type StreamingWebSocket } from '$lib/utils/websocket';
  
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
    text: string;
    item_id: string;
    title: string;
    url: string;
  }
  
  interface SuggestedItem {
    id: string;
    title: string;
    reason: string;
  }
  
  interface ChatInsights {
    topics_discussed: string[];
    knowledge_gaps: { topic: string; suggestion: string }[];
    exploration_suggestions: { action: string; topic: string; reason: string }[];
  }
  
  interface ChatMode {
    id: string;
    name: string;
    description: string;
    icon: string;
    color: string;
    bgGradient: string;
  }
  
  let messages: ChatMessage[] = [];
  let inputMessage = '';
  let isLoading = false;
  let selectedMode = 'general';
  let suggestedQuestions: string[] = [];
  let showSuggestions = true;
  let conversationId: string | null = null;
  let ws: StreamingWebSocket | null = null;
  let messagesContainer: HTMLElement;
  let contextItems: string[] = [];
  let showModeSelector = false;
  let currentStreamingMessage: ChatMessage | null = null;
  
  // Visual effects
  const orbPositions = Array(5).fill(null).map(() => ({
    x: Math.random() * 100,
    y: Math.random() * 100,
    scale: 0.8 + Math.random() * 0.4,
    rotation: 0
  }));
  
  // Create springs for orbs at top level
  const orbX1 = spring(orbPositions[0].x);
  const orbY1 = spring(orbPositions[0].y);
  const orbScale1 = spring(orbPositions[0].scale);
  const orbRotation1 = tweened(0, { duration: 20000 });
  
  const orbX2 = spring(orbPositions[1].x);
  const orbY2 = spring(orbPositions[1].y);
  const orbScale2 = spring(orbPositions[1].scale);
  const orbRotation2 = tweened(0, { duration: 20000 });
  
  const orbX3 = spring(orbPositions[2].x);
  const orbY3 = spring(orbPositions[2].y);
  const orbScale3 = spring(orbPositions[2].scale);
  const orbRotation3 = tweened(0, { duration: 20000 });
  
  const orbX4 = spring(orbPositions[3].x);
  const orbY4 = spring(orbPositions[3].y);
  const orbScale4 = spring(orbPositions[3].scale);
  const orbRotation4 = tweened(0, { duration: 20000 });
  
  const orbX5 = spring(orbPositions[4].x);
  const orbY5 = spring(orbPositions[4].y);
  const orbScale5 = spring(orbPositions[4].scale);
  const orbRotation5 = tweened(0, { duration: 20000 });
  
  // Enhanced chat modes with visual styling
  const chatModes: ChatMode[] = [
    {
      id: 'general',
      name: 'General',
      description: 'General conversation about your knowledge base',
      icon: 'message-circle',
      color: '#6366f1',
      bgGradient: 'from-indigo-500/20 to-purple-500/20'
    },
    {
      id: 'research',
      name: 'Research',
      description: 'Deep dive into topics and find connections',
      icon: 'search',
      color: '#10b981',
      bgGradient: 'from-emerald-500/20 to-teal-500/20'
    },
    {
      id: 'learning',
      name: 'Learning',
      description: 'Understand and retain information better',
      icon: 'book-open',
      color: '#f59e0b',
      bgGradient: 'from-amber-500/20 to-orange-500/20'
    },
    {
      id: 'creative',
      name: 'Creative',
      description: 'Generate new ideas and unexpected connections',
      icon: 'lightbulb',
      color: '#ec4899',
      bgGradient: 'from-pink-500/20 to-rose-500/20'
    }
  ];
  
  $: currentMode = chatModes.find(mode => mode.id === selectedMode) || chatModes[0];
  
  // Animate background orbs
  function animateOrbs() {
    // Animate orb 1
    setInterval(() => {
      orbX1.set(Math.random() * 100);
      orbY1.set(Math.random() * 100);
      orbScale1.set(0.8 + Math.random() * 0.4);
    }, 5000);
    
    // Animate orb 2
    setInterval(() => {
      orbX2.set(Math.random() * 100);
      orbY2.set(Math.random() * 100);
      orbScale2.set(0.8 + Math.random() * 0.4);
    }, 6000);
    
    // Animate orb 3
    setInterval(() => {
      orbX3.set(Math.random() * 100);
      orbY3.set(Math.random() * 100);
      orbScale3.set(0.8 + Math.random() * 0.4);
    }, 7000);
    
    // Animate orb 4
    setInterval(() => {
      orbX4.set(Math.random() * 100);
      orbY4.set(Math.random() * 100);
      orbScale4.set(0.8 + Math.random() * 0.4);
    }, 8000);
    
    // Animate orb 5
    setInterval(() => {
      orbX5.set(Math.random() * 100);
      orbY5.set(Math.random() * 100);
      orbScale5.set(0.8 + Math.random() * 0.4);
    }, 9000);
    
    // Rotation animations
    orbRotation1.set(360);
    orbRotation2.set(360);
    orbRotation3.set(360);
    orbRotation4.set(360);
    orbRotation5.set(360);
    
    setInterval(() => {
      orbRotation1.update(r => r + 360);
      orbRotation2.update(r => r + 360);
      orbRotation3.update(r => r + 360);
      orbRotation4.update(r => r + 360);
      orbRotation5.update(r => r + 360);
    }, 20000);
  }
  
  // Load chat modes
  async function loadChatModes() {
    // Modes are now hardcoded with enhanced styling
  }
  
  // Load suggested questions
  async function loadSuggestedQuestions() {
    try {
      const params = new URLSearchParams();
      if (contextItems.length > 0) {
        params.append('context_items', contextItems.join(','));
      }
      
      const response = await fetch(`/api/suggest-questions?${params}`);
      if (response.ok) {
        const data = await response.json();
        suggestedQuestions = data.questions;
      }
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
      }
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
      timestamp: new Date()
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
      isStreaming: true
    };
    
    messages = [...messages, currentStreamingMessage];
    scrollToBottom();
    
    // Send via WebSocket
    if (ws?.isConnected) {
      console.debug('[Chat] Sending message:', message);
      
      // Build conversation history
      const history = messages.slice(0, -2).map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));
      
      ws.send({
        message: message,
        history: history,
        chat_mode: selectedMode,
        conversation_id: conversationId,
        context_items: contextItems.length > 0 ? contextItems : null
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
  function navigateToItem(itemId: string) {
    window.location.href = `/items/${itemId}`;
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
  
  onMount(() => {
    loadChatModes();
    loadSuggestedQuestions();
    connectWebSocket();
    animateOrbs();
    
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
  });
</script>

<div class="chat-page" style="--mode-color: {currentMode.color}">
  <!-- Animated background -->
  <div class="background-animation">
    <div 
      class="orb"
      style="
        left: {$orbX1}%;
        top: {$orbY1}%;
        transform: scale({$orbScale1}) rotate({$orbRotation1}deg);
        background: radial-gradient(circle, {currentMode.color}40, transparent);
      "
    ></div>
    <div 
      class="orb"
      style="
        left: {$orbX2}%;
        top: {$orbY2}%;
        transform: scale({$orbScale2}) rotate({$orbRotation2}deg);
        background: radial-gradient(circle, {currentMode.color}40, transparent);
      "
    ></div>
    <div 
      class="orb"
      style="
        left: {$orbX3}%;
        top: {$orbY3}%;
        transform: scale({$orbScale3}) rotate({$orbRotation3}deg);
        background: radial-gradient(circle, {currentMode.color}40, transparent);
      "
    ></div>
    <div 
      class="orb"
      style="
        left: {$orbX4}%;
        top: {$orbY4}%;
        transform: scale({$orbScale4}) rotate({$orbRotation4}deg);
        background: radial-gradient(circle, {currentMode.color}40, transparent);
      "
    ></div>
    <div 
      class="orb"
      style="
        left: {$orbX5}%;
        top: {$orbY5}%;
        transform: scale({$orbScale5}) rotate({$orbRotation5}deg);
        background: radial-gradient(circle, {currentMode.color}40, transparent);
      "
    ></div>
  </div>
  
  <div class="chat-header">
    <div class="header-content">
      <div class="title-section">
        <h1 class="page-title">
          <div class="brain-icon">
            <Icon name="brain" size={32} />
            <div class="pulse-ring"></div>
          </div>
          Second Brain
        </h1>
        
        <button 
          class="mode-indicator"
          on:click={() => showModeSelector = !showModeSelector}
        >
          <Icon name={currentMode.icon} size={20} />
          <span>{currentMode.name} Mode</span>
          <Icon name="chevron-down" size={16} />
        </button>
      </div>
      
      {#if showModeSelector}
        <div class="mode-selector-overlay" on:click={() => showModeSelector = false}>
          <div class="mode-selector" on:click|stopPropagation>
            <h3>Choose your thinking mode</h3>
            <div class="modes-grid">
              {#each chatModes as mode}
                <button
                  class="mode-card"
                  class:active={selectedMode === mode.id}
                  on:click={() => {
                    selectedMode = mode.id;
                    showModeSelector = false;
                  }}
                  style="--mode-color: {mode.color}"
                >
                  <div class="mode-icon">
                    <Icon name={mode.icon} size={24} />
                  </div>
                  <h4>{mode.name}</h4>
                  <p>{mode.description}</p>
                  <div class="mode-bg-gradient {mode.bgGradient}"></div>
                </button>
              {/each}
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
  
  <div class="chat-container">
    <div class="messages-area" bind:this={messagesContainer}>
      {#if messages.length === 0 && showSuggestions}
        <div class="welcome-message">
          <div class="welcome-animation">
            <div class="brain-visualization">
              <svg viewBox="0 0 200 200" class="brain-svg">
                <defs>
                  <linearGradient id="brain-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:{currentMode.color};stop-opacity:0.6" />
                    <stop offset="100%" style="stop-color:{currentMode.color};stop-opacity:0.2" />
                  </linearGradient>
                </defs>
                <path d="M 100 50 Q 60 50 40 80 T 50 140 Q 80 170 100 170 Q 120 170 150 140 T 160 80 Q 140 50 100 50" 
                      fill="url(#brain-gradient)" 
                      stroke="{currentMode.color}" 
                      stroke-width="2"
                      opacity="0.8"
                >
                  <animate attributeName="d" 
                    values="M 100 50 Q 60 50 40 80 T 50 140 Q 80 170 100 170 Q 120 170 150 140 T 160 80 Q 140 50 100 50;
                            M 100 50 Q 65 45 45 75 T 55 135 Q 85 165 100 165 Q 115 165 145 135 T 155 75 Q 135 45 100 50;
                            M 100 50 Q 60 50 40 80 T 50 140 Q 80 170 100 170 Q 120 170 150 140 T 160 80 Q 140 50 100 50"
                    dur="4s"
                    repeatCount="indefinite"
                  />
                </path>
                
                <!-- Neural connections -->
                {#each Array(6) as _, i}
                  <circle r="3" fill="{currentMode.color}">
                    <animateMotion
                      dur="{3 + i}s"
                      repeatCount="indefinite"
                      path="M {50 + i * 20} 100 Q 100 {50 + i * 10} {150 - i * 20} 100"
                    />
                    <animate attributeName="opacity" values="0;1;0" dur="{3 + i}s" repeatCount="indefinite" />
                  </circle>
                {/each}
              </svg>
            </div>
          </div>
          
          <h2>Welcome to your Second Brain</h2>
          <p class="welcome-subtitle">I'm here to help you explore, understand, and connect your knowledge in {currentMode.name.toLowerCase()} mode.</p>
          
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
                    on:click={() => navigateToItem(citation.item_id)}
                  >
                    <Icon name="file-text" size={12} />
                    {citation.title}
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
                    on:click={() => navigateToItem(item.id)}
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
          <textarea
            class="message-input"
            placeholder="Ask your Second Brain anything..."
            bind:value={inputMessage}
            on:keypress={handleKeyPress}
            rows="1"
          ></textarea>
          
          <div class="input-actions">
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
            >
              <Icon name="send" size={20} />
              <div class="send-ripple"></div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .chat-page {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    position: relative;
    overflow: hidden;
  }
  
  /* Animated background */
  .background-animation {
    position: absolute;
    inset: 0;
    pointer-events: none;
    opacity: 0.5;
  }
  
  .orb {
    position: absolute;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    filter: blur(80px);
    animation: float 20s infinite ease-in-out;
  }
  
  @keyframes float {
    0%, 100% {
      transform: translateY(0) rotate(0deg);
    }
    50% {
      transform: translateY(-20px) rotate(180deg);
    }
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
  
  .title-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
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
  }
  
  .pulse-ring {
    position: absolute;
    inset: -8px;
    border: 2px solid var(--mode-color);
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
  
  .mode-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 2rem;
    color: white;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .mode-indicator:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: var(--mode-color);
    box-shadow: 0 0 20px rgba(var(--mode-color), 0.3);
  }
  
  /* Mode Selector */
  .mode-selector-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
    backdrop-filter: blur(10px);
  }
  
  .mode-selector {
    background: #1a1a1a;
    border-radius: 1.5rem;
    padding: 2rem;
    max-width: 600px;
    width: 90%;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .mode-selector h3 {
    text-align: center;
    margin-bottom: 2rem;
    color: white;
    font-size: 1.5rem;
  }
  
  .modes-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .mode-card {
    position: relative;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    cursor: pointer;
    transition: all 0.3s;
    overflow: hidden;
    text-align: center;
  }
  
  .mode-card:hover {
    transform: translateY(-4px);
    border-color: var(--mode-color);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  }
  
  .mode-card.active {
    border-color: var(--mode-color);
    background: rgba(255, 255, 255, 0.1);
  }
  
  .mode-icon {
    width: 48px;
    height: 48px;
    margin: 0 auto 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--mode-color);
    border-radius: 50%;
    color: white;
  }
  
  .mode-card h4 {
    margin: 0 0 0.5rem;
    color: white;
    font-size: 1.125rem;
  }
  
  .mode-card p {
    margin: 0;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.875rem;
  }
  
  .mode-bg-gradient {
    position: absolute;
    inset: 0;
    opacity: 0.1;
    z-index: -1;
  }
  
  /* Chat Container */
  .chat-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
    padding: 0 2rem;
    overflow: hidden;
    position: relative;
    z-index: 1;
  }
  
  .messages-area {
    flex: 1;
    overflow-y: auto;
    padding: 2rem 0;
    scroll-behavior: smooth;
  }
  
  /* Welcome Message */
  .welcome-message {
    text-align: center;
    padding: 4rem 2rem;
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
    width: 200px;
    height: 200px;
    margin: 0 auto;
  }
  
  .brain-svg {
    width: 100%;
    height: 100%;
  }
  
  .welcome-message h2 {
    font-size: 2rem;
    margin: 1rem 0;
    color: white;
  }
  
  .welcome-subtitle {
    font-size: 1.125rem;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 3rem;
  }
  
  /* Suggested Questions */
  .suggested-questions {
    max-width: 600px;
    margin: 0 auto;
  }
  
  .suggested-questions h3 {
    font-size: 1rem;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 1.5rem;
  }
  
  .questions-grid {
    display: grid;
    gap: 1rem;
  }
  
  .suggestion-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
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
    border-color: var(--mode-color);
    transform: translateX(8px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  }
  
  .suggestion-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    flex-shrink: 0;
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
    background: var(--mode-color);
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
    background: var(--mode-color);
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
    background: var(--mode-color);
    margin-left: 2px;
    vertical-align: text-bottom;
    animation: blink 1s infinite;
  }
  
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
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
    padding: 1.5rem 0 2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(10, 10, 10, 0.8);
    backdrop-filter: blur(20px);
  }
  
  .input-container {
    max-width: 100%;
  }
  
  .input-wrapper {
    display: flex;
    align-items: flex-end;
    gap: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1.5rem;
    padding: 0.75rem 1rem;
    transition: all 0.3s;
  }
  
  .input-wrapper:focus-within {
    border-color: var(--mode-color);
    box-shadow: 0 0 30px rgba(var(--mode-color), 0.2);
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
  }
  
  .message-input:focus {
    outline: none;
  }
  
  .message-input::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }
  
  .input-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
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
    background: var(--mode-color);
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.3s;
  }
  
  .send-button:hover:not(:disabled) {
    transform: scale(1.1);
    box-shadow: 0 0 30px rgba(var(--mode-color), 0.5);
  }
  
  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .send-button.pulse {
    animation: pulse 2s infinite;
  }
  
  .send-ripple {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: var(--mode-color);
    opacity: 0;
    transform: scale(0);
  }
  
  .send-button:active .send-ripple {
    animation: ripple 0.6s ease-out;
  }
  
  @keyframes ripple {
    to {
      opacity: 0;
      transform: scale(2);
    }
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
  
  /* Gradient backgrounds for modes */
  .from-indigo-500\/20 {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  }
  
  .from-emerald-500\/20 {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(20, 184, 166, 0.2));
  }
  
  .from-amber-500\/20 {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(251, 146, 60, 0.2));
  }
  
  .from-pink-500\/20 {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(244, 63, 94, 0.2));
  }
  
  /* Responsive */
  @media (max-width: 768px) {
    .chat-container {
      padding: 0 1rem;
    }
    
    .modes-grid {
      grid-template-columns: 1fr;
    }
    
    .message-metadata {
      margin-left: 0;
    }
  }
</style>