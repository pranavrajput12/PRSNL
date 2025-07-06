// PRSNL Capture - Background Service Worker

// Initialize context menu
chrome.runtime.onInstalled.addListener(() => {
  setupContextMenu(true);
});

// Load settings and update context menu
chrome.storage.sync.get({ contextMenu: true }, (settings) => {
  setupContextMenu(settings.contextMenu);
});

// Listen for keyboard command
chrome.commands.onCommand.addListener(async (command) => {
  if (command === 'capture-page') {
    await captureCurrentPage();
  } else if (command === 'capture-selection') {
    await captureSelection();
  }
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'capture') {
    captureCurrentPage(message.tags);
    return true;
  } else if (message.action === 'updateContextMenu') {
    setupContextMenu(message.enabled);
    return true;
  } else if (message.action === 'captureSelection') {
    captureSelection(message.tags);
    return true;
  }
});

// Context menu click handler
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'capture-page') {
    captureCurrentPage();
  } else if (info.menuItemId === 'capture-selection') {
    captureSelection();
  }
});

// Setup context menu
function setupContextMenu(enabled) {
  chrome.contextMenus.removeAll(() => {
    if (enabled) {
      chrome.contextMenus.create({
        id: 'capture-page',
        title: 'Capture page to PRSNL',
        contexts: ['page']
      });
      
      chrome.contextMenus.create({
        id: 'capture-selection',
        title: 'Capture selection to PRSNL',
        contexts: ['selection']
      });
    }
  });
}

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

// Capture selection function
async function captureSelection(tags = []) {
  try {
    // Get current active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) {
      showNotification('Error', 'No active tab found');
      return;
    }
    
    // Get selected text from content script
    await chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, async (response) => {
      if (chrome.runtime.lastError) {
        // Inject content script and try again
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        });
        
        chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, (secondResponse) => {
          const selectedText = secondResponse?.selectedText || '';
          if (selectedText) {
            sendToApi(tab.url, tab.title, selectedText, tags, 'selection');
          } else {
            showNotification('Error', 'No text selected');
          }
        });
      } else {
        const selectedText = response?.selectedText || '';
        if (selectedText) {
          sendToApi(tab.url, tab.title, selectedText, tags, 'selection');
        } else {
          showNotification('Error', 'No text selected');
        }
      }
    });
  } catch (error) {
    console.error('Selection capture failed:', error);
    showNotification('Error', 'Failed to capture selection');
  }
}

// Send data to API
async function sendToApi(url, title, highlight, tags, type = 'page') {
  try {
    // Get API URL from settings
    const settings = await chrome.storage.sync.get({ apiUrl: 'http://localhost:8000' });
    
    const response = await fetch(`${settings.apiUrl}/api/capture`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url,
        title,
        content: highlight,
        tags,
        type
      })
    });
    
    if (response.ok) {
      showNotification('Success', `${type === 'selection' ? 'Selection' : 'Page'} captured to PRSNL`);
      
      // Show visual feedback on page
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, { 
            action: 'showCaptureEffect',
            type: type === 'selection' ? 'selection' : 'page'
          });
        }
      });
    } else {
      showNotification('Error', `Failed to save: ${response.statusText}`);
    }
  } catch (error) {
    console.error('API error:', error);
    showNotification('Error', 'Failed to connect to PRSNL');
  }
}

// Show notification
async function showNotification(title, message) {
  // Check if notifications are enabled
  const settings = await chrome.storage.sync.get({ showNotifications: true });
  
  if (settings.showNotifications) {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon128.png',
      title,
      message,
      priority: 2
    });
  }
}