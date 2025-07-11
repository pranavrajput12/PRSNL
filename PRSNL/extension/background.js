// PRSNL Capture - Background Service Worker v2

// Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('PRSNL Extension installed');
});

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
  console.log('🚀 [BACKGROUND] Starting capture request:', data);
  
  for (let i = 0; i < retries; i++) {
    try {
      console.log(`🔄 [BACKGROUND] Attempt ${i + 1}/${retries}`);
      console.log('📤 [BACKGROUND] Sending to:', `${API_BASE_URL}/capture`);
      console.log('📦 [BACKGROUND] Request body:', JSON.stringify(data, null, 2));
      
      const response = await fetch(`${API_BASE_URL}/capture`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });
      
      console.log('📥 [BACKGROUND] Response status:', response.status);
      console.log('📥 [BACKGROUND] Response headers:', [...response.headers.entries()]);
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ [BACKGROUND] Success response:', result);
        return { success: true, ...result };
      }
      
      // Handle error responses
      const errorText = await response.text();
      console.error('❌ [BACKGROUND] Error response:', errorText);
      console.error('❌ [BACKGROUND] Response status:', response.status);
      
      // Handle specific error codes
      if (response.status === 429) {
        console.log('⏳ [BACKGROUND] Rate limited, retrying...');
        // Rate limited - wait and retry
        await new Promise(resolve => setTimeout(resolve, 2000 * (i + 1)));
        continue;
      }
      
      // Don't retry business logic errors (400 range except 429)
      if (response.status >= 400 && response.status < 500 && response.status !== 429) {
        console.log('🚫 [BACKGROUND] Business logic error, not retrying');
        // Break out of retry loop for client errors
        break;
      }
      
      // Try to parse error JSON
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorJson.message || errorMessage;
        console.error('❌ [BACKGROUND] Parsed error:', errorJson);
      } catch (e) {
        console.error('❌ [BACKGROUND] Could not parse error JSON');
      }
      
      throw new Error(errorMessage);
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
  console.log('📨 [BACKGROUND] Received message:', message);
  
  if (message.action === 'capture') {
    console.log('🎯 [BACKGROUND] Processing capture action');
    console.log('📄 [BACKGROUND] Capture data received:', message.data);
    
    // Send the capture data directly
    sendCaptureRequest(message.data)
      .then(result => {
        console.log('✅ [BACKGROUND] Capture successful, sending response:', result);
        sendResponse({ success: true, ...result });
      })
      .catch(error => {
        console.error('❌ [BACKGROUND] Capture failed:', error);
        sendResponse({ success: false, error: error.message });
      });
    return true; // Keep channel open for async response
  }
});