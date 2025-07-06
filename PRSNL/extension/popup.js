// PRSNL Capture - Popup Script

document.addEventListener('DOMContentLoaded', async () => {
  // DOM elements
  const tagInput = document.getElementById('tag-input');
  const tagsContainer = document.getElementById('tags-container');
  const captureBtn = document.getElementById('capture-btn');
  const cancelBtn = document.getElementById('cancel-btn');
  const pageTitle = document.getElementById('page-title');
  const pageUrl = document.getElementById('page-url');
  const selectionContainer = document.getElementById('selection-container');
  const selectionText = document.getElementById('selection-text');
  const faviconContainer = document.getElementById('favicon-container');
  const statusMessage = document.getElementById('status-message');
  
  // State
  let tags = [];
  let currentTab = null;
  let selectedText = '';
  
  // Initialize popup
  async function initPopup() {
    try {
      // Get current tab info
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      currentTab = tab;
      
      if (tab) {
        // Display tab info
        pageTitle.textContent = tab.title;
        pageUrl.textContent = tab.url;
        
        // Add favicon
        const faviconUrl = tab.favIconUrl || 'icons/icon16.png';
        const favicon = document.createElement('img');
        favicon.src = faviconUrl;
        favicon.alt = 'Favicon';
        favicon.className = 'favicon';
        faviconContainer.appendChild(favicon);
        
        // Get selected text from content script
        chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, (response) => {
          if (chrome.runtime.lastError) {
            // Content script might not be loaded, hide selection container
            selectionContainer.style.display = 'none';
          } else if (response && response.selectedText) {
            selectedText = response.selectedText;
            selectionText.textContent = selectedText.length > 280 
              ? selectedText.substring(0, 280) + '...' 
              : selectedText;
          } else {
            selectionContainer.style.display = 'none';
          }
        });
      }
    } catch (error) {
      console.error('Error initializing popup:', error);
    }
  }
  
  // Handle tag input
  tagInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && tagInput.value.trim()) {
      addTag(tagInput.value.trim());
      tagInput.value = '';
    }
  });
  
  // Add a tag
  function addTag(tagText) {
    // Don't add duplicate tags
    if (tags.includes(tagText)) return;
    
    // Add to state
    tags.push(tagText);
    
    // Create tag element
    const tag = document.createElement('div');
    tag.className = 'tag';
    
    const tagContent = document.createElement('span');
    tagContent.textContent = tagText;
    
    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-tag';
    removeBtn.innerHTML = '&times;';
    removeBtn.addEventListener('click', () => removeTag(tagText, tag));
    
    tag.appendChild(tagContent);
    tag.appendChild(removeBtn);
    tagsContainer.appendChild(tag);
  }
  
  // Remove a tag
  function removeTag(tagText, element) {
    tags = tags.filter(tag => tag !== tagText);
    tagsContainer.removeChild(element);
  }
  
  // Capture button click
  captureBtn.addEventListener('click', async () => {
    if (!currentTab) return;
    
    try {
      // Show loading state
      captureBtn.disabled = true;
      captureBtn.textContent = 'Saving...';
      
      // Send capture message to background script
      chrome.runtime.sendMessage({
        action: 'capture',
        tags: tags
      });
      
      // Show success and close popup
      showStatus('Captured!', 'success');
      setTimeout(() => window.close(), 1000);
    } catch (error) {
      console.error('Error capturing:', error);
      showStatus('Failed to capture', 'error');
      captureBtn.disabled = false;
      captureBtn.textContent = 'Capture';
    }
  });
  
  // Cancel button click
  cancelBtn.addEventListener('click', () => {
    window.close();
  });
  
  // Show status message
  function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status ${type}`;
    statusMessage.style.display = 'block';
  }
  
  // Initialize
  initPopup();
});
