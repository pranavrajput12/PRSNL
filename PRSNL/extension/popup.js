// Modern PRSNL Popup - Beautiful Carousel Design
let currentTab = null;
let selectedText = '';
let tags = [];
let isCapturing = false;
let isImporting = false;
let currentCard = 0;

// Helper function to ensure content script connection
async function ensureContentScriptConnection() {
  try {
    console.log('🔍 [POPUP] Testing content script connection...');
    
    const response = await new Promise((resolve, reject) => {
      chrome.tabs.sendMessage(currentTab.id, { action: 'ping' }, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
    
    if (response && response.status === 'pong') {
      console.log('✅ [POPUP] Content script is responsive');
      return true;
    }
    
    throw new Error('Content script did not respond correctly');
  } catch (error) {
    console.log('⚠️ [POPUP] Content script not responsive, requesting injection...');
    
    try {
      const injectResponse = await new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(
          { action: 'ensureContentScript', tabId: currentTab.id },
          (response) => {
            if (chrome.runtime.lastError) {
              reject(new Error(chrome.runtime.lastError.message));
            } else {
              resolve(response);
            }
          }
        );
      });
      
      if (injectResponse && injectResponse.success) {
        console.log('✅ [POPUP] Content script injection successful');
        return true;
      }
      
      throw new Error('Content script injection failed');
    } catch (injectError) {
      console.error('❌ [POPUP] Failed to inject content script:', injectError);
      return false;
    }
  }
}

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 [POPUP] Modern popup initializing...');
  console.log('🔍 [POPUP] DOM elements check:');
  console.log('- page-title:', !!document.getElementById('page-title'));
  console.log('- page-url:', !!document.getElementById('page-url'));
  console.log('- capture-btn:', !!document.getElementById('capture-btn'));
  console.log('- import-conversation-btn:', !!document.getElementById('import-conversation-btn'));
  console.log('- detection-icon:', !!document.getElementById('detection-icon'));
  console.log('- platform-text:', !!document.getElementById('platform-text'));
  
  try {
    // Get current tab info
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTab = tab;
    console.log('📋 [POPUP] Current tab:', tab.url);
    
    // Display tab info
    displayTabInfo(tab);
    
    // Check for selected text
    const connectionWorking = await ensureContentScriptConnection();
    if (connectionWorking) {
      chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, (response) => {
        if (chrome.runtime.lastError) {
          console.error('❌ [POPUP] Error getting selection:', chrome.runtime.lastError);
        } else if (response && response.selection) {
          selectedText = response.selection;
          console.log('📝 [POPUP] Selected text found');
        }
      });
    }
    
    // Set up event listeners
    setupEventListeners();
    
    // Auto-detect content type
    autoDetectContentType(tab.url);

    // Detect conversation platform
    detectConversationPlatform();
    
    console.log('✅ [POPUP] Popup initialization complete');
  } catch (error) {
    console.error('❌ [POPUP] Error during initialization:', error);
  }
});

// Display tab information
function displayTabInfo(tab) {
  const title = document.getElementById('page-title');
  const url = document.getElementById('page-url');
  const favicon = document.getElementById('favicon-container');
  
  if (title) {
    title.textContent = tab.title || 'Unknown Page';
  }
  if (url) {
    url.textContent = tab.url || 'Unknown URL';
  }
  if (favicon) {
    const faviconUrl = `https://www.google.com/s2/favicons?domain=${new URL(tab.url).hostname}&sz=32`;
    favicon.innerHTML = `<img src="${faviconUrl}" alt="Site favicon" style="width: 20px; height: 20px; border-radius: 4px;" />`;
  }
}

// Auto-detect content type based on URL
function autoDetectContentType(url) {
  const buttons = document.querySelectorAll('.type-button');
  const hiddenSelect = document.getElementById('content-type');
  
  let detectedType = 'auto';
  
  if (url.includes('github.com')) {
    detectedType = 'development';
  } else if (url.includes('youtube.com') || url.includes('youtu.be')) {
    detectedType = 'video';
  } else if (url.includes('medium.com') || url.includes('dev.to')) {
    detectedType = 'article';
  }
  
  // Update visual buttons
  buttons.forEach(btn => {
    btn.classList.remove('active');
    if (btn.dataset.type === detectedType) {
      btn.classList.add('active');
    }
  });
  
  // Update hidden select
  if (hiddenSelect) {
    hiddenSelect.value = detectedType;
  }
  
  console.log('🔍 [POPUP] Auto-detected content type:', detectedType);
}

// Enhanced platform detection with beautiful UI updates
async function detectConversationPlatform() {
  console.log('🧠 [POPUP] Starting platform detection...');
  
  const detectionResult = document.getElementById('detection-result');
  const detectionIcon = document.getElementById('detection-icon');
  const platformText = document.getElementById('platform-text');
  const detectionStatus = document.getElementById('detection-status');
  const importButton = document.getElementById('import-conversation-btn');
  
  // Set scanning state
  if (detectionIcon) detectionIcon.textContent = '🔍';
  if (platformText) platformText.textContent = 'Scanning platform...';
  if (detectionStatus) detectionStatus.textContent = 'Analyzing page structure';
  
  // Ensure content script connection
  const isConnected = await ensureContentScriptConnection();
  if (!isConnected) {
    if (detectionIcon) detectionIcon.textContent = '❌';
    if (platformText) platformText.textContent = 'Connection Error';
    if (detectionStatus) detectionStatus.textContent = 'Try refreshing the page';
    return;
  }
  
  // Detect platform
  chrome.tabs.sendMessage(currentTab.id, { action: 'detectPlatform' }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('❌ [POPUP] Platform detection error:', chrome.runtime.lastError);
      if (detectionIcon) detectionIcon.textContent = '❌';
      if (platformText) platformText.textContent = 'Detection Failed';
      if (detectionStatus) detectionStatus.textContent = 'Content script error';
      return;
    }
    
    if (response && response.platform) {
      console.log('🎯 [POPUP] Platform detected:', response.platform);
      
      // Update detection result
      if (detectionResult) detectionResult.classList.add('detected');
      if (detectionIcon) detectionIcon.textContent = '🎯';
      if (platformText) platformText.textContent = `${response.platform.charAt(0).toUpperCase() + response.platform.slice(1)} Detected`;
      
      if (response.isConversation) {
        if (detectionStatus) detectionStatus.textContent = 'Conversation ready to import';
        if (importButton) importButton.disabled = false;
        
        // Highlight platform in grid
        const platformItems = document.querySelectorAll('.platform-item');
        platformItems.forEach(item => {
          if (item.dataset.platform === response.platform) {
            item.classList.add('detected');
          }
        });
      } else {
        if (detectionStatus) detectionStatus.textContent = 'No active conversation found';
        if (importButton) importButton.disabled = true;
      }
    } else {
      console.log('❌ [POPUP] No platform detected');
      if (detectionIcon) detectionIcon.textContent = '🌐';
      if (platformText) platformText.textContent = 'No AI Platform';
      if (detectionStatus) detectionStatus.textContent = 'Visit ChatGPT, Claude, or Perplexity';
    }
  });
}

// Set up all event listeners
function setupEventListeners() {
  // Carousel navigation
  const navDots = document.querySelectorAll('.nav-dot');
  navDots.forEach((dot, index) => {
    dot.addEventListener('click', () => switchCard(index));
  });
  
  // Content type buttons
  const typeButtons = document.querySelectorAll('.type-button');
  const hiddenSelect = document.getElementById('content-type');
  
  typeButtons.forEach(button => {
    button.addEventListener('click', () => {
      typeButtons.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      
      const type = button.dataset.type;
      if (hiddenSelect) hiddenSelect.value = type;
      
      console.log('🎯 [POPUP] Content type selected:', type);
    });
  });
  
  // Capture button
  const captureBtn = document.getElementById('capture-btn');
  if (captureBtn) {
    captureBtn.addEventListener('click', handleCapture);
  }
  
  // Import button
  const importBtn = document.getElementById('import-conversation-btn');
  if (importBtn) {
    importBtn.addEventListener('click', handleConversationImport);
  }
  
  // Quick options sync
  const aiSummaryCheckbox = document.getElementById('ai-summary');
  const hiddenSummaryCheckbox = document.getElementById('enable-summarization');
  
  if (aiSummaryCheckbox && hiddenSummaryCheckbox) {
    aiSummaryCheckbox.addEventListener('change', () => {
      hiddenSummaryCheckbox.checked = aiSummaryCheckbox.checked;
    });
  }
  
  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      const direction = e.key === 'ArrowLeft' ? -1 : 1;
      const newCard = Math.max(0, Math.min(1, currentCard + direction));
      switchCard(newCard);
    }
    
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      if (currentCard === 0) {
        handleCapture();
      } else {
        handleConversationImport();
      }
    }
    
    if (e.key === 'Escape') {
      window.close();
    }
  });
}

// Switch between cards (carousel functionality)
function switchCard(cardIndex) {
  if (cardIndex === currentCard) return;
  
  const cards = document.querySelectorAll('.capture-card');
  const navDots = document.querySelectorAll('.nav-dot');
  
  // Update active states
  cards.forEach((card, index) => {
    card.classList.toggle('active', index === cardIndex);
  });
  
  navDots.forEach((dot, index) => {
    dot.classList.toggle('active', index === cardIndex);
  });
  
  currentCard = cardIndex;
  console.log('🎠 [POPUP] Switched to card:', cardIndex);
}

// Handle capture with modern UI
async function handleCapture() {
  if (isCapturing) return;
  
  isCapturing = true;
  const captureBtn = document.getElementById('capture-btn');
  const btnText = captureBtn.querySelector('.btn-text');
  const btnLoader = captureBtn.querySelector('.btn-loader');
  
  // Show loading state
  btnText.style.display = 'none';
  btnLoader.style.display = 'flex';
  captureBtn.disabled = true;
  
  try {
    // Gather form data
    const contentType = document.getElementById('content-type').value || 'auto';
    const enableSummarization = document.getElementById('enable-summarization').checked;
    
    const captureData = {
      url: currentTab.url,
      title: currentTab.title,
      content: selectedText || null,
      highlight: selectedText || null,
      tags: tags,
      enable_summarization: enableSummarization,
      content_type: contentType
    };
    
    console.log('📤 [POPUP] Capturing:', captureData);
    
    // Send to backend
    chrome.runtime.sendMessage({ action: 'capture', data: captureData }, (response) => {
      if (response && response.success) {
        console.log('✅ [POPUP] Capture successful');
        showGlobalStatus('Content captured successfully!', 'success');
        setTimeout(() => window.close(), 1500);
      } else {
        console.error('❌ [POPUP] Capture failed:', response);
        showGlobalStatus(response?.error || 'Failed to capture content', 'error');
      }
    });
    
  } catch (error) {
    console.error('❌ [POPUP] Capture error:', error);
    showGlobalStatus(error.message || 'Failed to capture content', 'error');
  } finally {
    // Reset button state
    btnText.style.display = 'inline';
    btnLoader.style.display = 'none';
    captureBtn.disabled = false;
    isCapturing = false;
  }
}

// Handle conversation import with modern UI
async function handleConversationImport() {
  if (isImporting) return;
  
  isImporting = true;
  const importBtn = document.getElementById('import-conversation-btn');
  const btnText = importBtn.querySelector('.btn-text');
  const btnLoader = importBtn.querySelector('.btn-loader');
  const importStatus = document.getElementById('import-status');
  
  // Show loading state
  btnText.style.display = 'none';
  btnLoader.style.display = 'flex';
  importBtn.disabled = true;
  
  if (importStatus) {
    importStatus.style.display = 'block';
    importStatus.className = 'import-status loading';
    const statusMessageEl = importStatus.querySelector('.status-message');
    if (statusMessageEl) {
      statusMessageEl.textContent = 'Extracting conversation...';
    }
  }
  
  try {
    // Ensure content script connection
    const isConnected = await ensureContentScriptConnection();
    if (!isConnected) {
      throw new Error('Unable to connect to page. Please refresh and try again.');
    }
    
    // Extract conversation
    chrome.tabs.sendMessage(currentTab.id, { action: 'extractConversation' }, async (extractResponse) => {
      if (chrome.runtime.lastError) {
        console.error('❌ [POPUP] Extract error:', chrome.runtime.lastError);
        throw new Error('Communication error with page');
      }
      
      if (!extractResponse || !extractResponse.success) {
        throw new Error(extractResponse?.error || 'Failed to extract conversation');
      }
      
      console.log('✅ [POPUP] Conversation extracted successfully');
      
      if (importStatus) {
        const statusMessageEl = importStatus.querySelector('.status-message');
        if (statusMessageEl) {
          statusMessageEl.textContent = 'Processing conversation...';
        }
      }
      
      // Import conversation
      chrome.runtime.sendMessage({ 
        action: 'importConversation', 
        data: extractResponse.data 
      }, (importResponse) => {
        if (chrome.runtime.lastError) {
          console.error('❌ [POPUP] Import error:', chrome.runtime.lastError);
          showImportError('Background communication error');
          return;
        }
        
        if (importResponse && importResponse.success) {
          console.log('✅ [POPUP] Import successful');
          if (importStatus) {
            importStatus.className = 'import-status success';
            const statusMessageEl = importStatus.querySelector('.status-message');
            if (statusMessageEl) {
              statusMessageEl.textContent = 'Conversation imported successfully!';
            }
          }
          showGlobalStatus('Conversation imported successfully!', 'success');
          setTimeout(() => window.close(), 2000);
        } else {
          showImportError(importResponse?.error || 'Import failed');
        }
      });
    });
    
  } catch (error) {
    console.error('❌ [POPUP] Import error:', error);
    showImportError(error.message);
  }
}

// Show import error
function showImportError(message) {
  const importStatus = document.getElementById('import-status');
  const importBtn = document.getElementById('import-conversation-btn');
  const btnText = importBtn.querySelector('.btn-text');
  const btnLoader = importBtn.querySelector('.btn-loader');
  
  if (importStatus) {
    importStatus.className = 'import-status error';
    const statusMessageEl = importStatus.querySelector('.status-message');
    if (statusMessageEl) {
      statusMessageEl.textContent = message;
    }
  }
  
  showGlobalStatus(message, 'error');
  
  // Reset button
  btnText.style.display = 'inline';
  btnLoader.style.display = 'none';
  importBtn.disabled = false;
  isImporting = false;
}

// Show global status message
function showGlobalStatus(message, type) {
  const statusEl = document.getElementById('status-message');
  if (!statusEl) {
    console.log('⚠️ [POPUP] Status element not found, logging status:', message);
    return;
  }
  
  statusEl.textContent = message;
  statusEl.className = `global-status ${type}`;
  statusEl.style.display = 'block';
  
  // Auto-hide after delay
  setTimeout(() => {
    statusEl.style.display = 'none';
  }, type === 'success' ? 3000 : 5000);
}

console.log('🎨 [POPUP] Modern popup script loaded');