// PRSNL Capture - Background Service Worker v2

// Configuration
const API_BASE_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/ws';

// WebSocket connection
let ws = null;

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  // setupContextMenu(true);
  connectWebSocket();
});

// Connect to WebSocket for real-time updates
function connectWebSocket() {
  try {
    ws = new WebSocket(WS_URL);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected. Reconnecting in 5s...');
      setTimeout(connectWebSocket, 5000);
    };
  } catch (error) {
    console.error('Failed to connect WebSocket:', error);
  }
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
  if (data.type === 'capture_complete') {
    // Show notification for successful capture
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon128.png',
      title: 'PRSNL Capture Complete',
      message: data.message || 'Your content has been processed successfully!'
    });
  } else if (data.type === 'capture_error') {
    // Show error notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon128.png',
      title: 'PRSNL Capture Error',
      message: data.message || 'Failed to process content'
    });
  }
}

// Enhanced capture function with retry logic
async function captureCurrentPage(tags = []) {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Smart content type detection
    const contentType = detectContentType(tab.url);
    
    const captureData = {
      url: tab.url,
      title: tab.title,
      tags: tags,
      enable_summarization: true,
      content_type: contentType
    };
    
    // Add development metadata for GitHub
    if (contentType === 'development' && tab.url.includes('github.com')) {
      const githubInfo = parseGitHubUrl(tab.url);
      if (githubInfo) {
        captureData.programming_language = githubInfo.language;
        captureData.project_category = 'Open Source';
      }
    }
    
    // Send capture request with retry
    const result = await sendCaptureRequest(captureData);
    
    if (result.success) {
      // Store in local cache for offline access
      await chrome.storage.local.set({
        lastCapture: {
          ...captureData,
          timestamp: Date.now(),
          id: result.id
        }
      });
    }
    
    return result;
  } catch (error) {
    console.error('Capture error:', error);
    throw error;
  }
}

// Send capture request with retry logic
async function sendCaptureRequest(data, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(`${API_BASE_URL}/capture`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });
      
      if (response.ok) {
        const result = await response.json();
        return { success: true, ...result };
      }
      
      // Handle specific error codes
      if (response.status === 429) {
        // Rate limited - wait and retry
        await new Promise(resolve => setTimeout(resolve, 2000 * (i + 1)));
        continue;
      }
      
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    } catch (error) {
      if (i === retries - 1) throw error;
      
      // Exponential backoff
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
}

// Detect content type from URL
function detectContentType(url) {
  if (url.includes('github.com')) return 'development';
  if (url.includes('youtube.com') || url.includes('youtu.be')) return 'video';
  if (url.includes('.pdf')) return 'document';
  if (url.includes('medium.com') || url.includes('dev.to')) return 'article';
  if (url.includes('stackoverflow.com')) return 'development';
  return 'auto';
}

// Parse GitHub URL for metadata
function parseGitHubUrl(url) {
  const match = url.match(/github\.com\/([^\/]+)\/([^\/]+)/);
  if (match) {
    return {
      owner: match[1],
      repo: match[2],
      language: 'Unknown' // Would need API call to detect
    };
  }
  return null;
}

// Listen for keyboard commands
chrome.commands.onCommand.addListener(async (command) => {
  if (command === 'capture-page') {
    await captureCurrentPage();
  } else if (command === 'capture-selection') {
    // await captureSelection();
  }
});

// Message handler
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'capture') {
    captureCurrentPage(message.tags)
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ error: error.message }));
    return true; // Keep channel open for async response
  }
});