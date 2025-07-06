// PRSNL Capture - Background Service Worker

// Listen for keyboard command
chrome.commands.onCommand.addListener(async (command) => {
  if (command === 'capture-page') {
    await captureCurrentPage();
  }
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'capture') {
    captureCurrentPage(message.tags);
    return true;
  }
});

// Main capture function
async function captureCurrentPage(tags = []) {
  try {
    // Get current active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) {
      showNotification('Error', 'No active tab found');
      return;
    }
    
    // Get selected text from content script
    await chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, async (response) => {
      // If there's an error in the response, it might be because the content script isn't loaded
      if (chrome.runtime.lastError) {
        // Inject content script and try again
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        });
        
        // Try again after injecting
        chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, (secondResponse) => {
          const highlight = secondResponse?.selectedText || '';
          sendToApi(tab.url, tab.title, highlight, tags);
        });
      } else {
        // Content script responded normally
        const highlight = response?.selectedText || '';
        sendToApi(tab.url, tab.title, highlight, tags);
      }
    });
  } catch (error) {
    console.error('Capture failed:', error);
    showNotification('Error', 'Failed to capture page');
  }
}

// Send data to API
async function sendToApi(url, title, highlight, tags) {
  try {
    const response = await fetch('http://localhost:8000/api/capture', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url,
        title,
        highlight,
        tags
      })
    });
    
    if (response.ok) {
      showNotification('Success', 'Page captured to PRSNL');
    } else {
      showNotification('Error', `Failed to save: ${response.statusText}`);
    }
  } catch (error) {
    console.error('API error:', error);
    showNotification('Error', 'Failed to connect to PRSNL');
  }
}

// Show notification
function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title,
    message,
    priority: 2
  });
}
