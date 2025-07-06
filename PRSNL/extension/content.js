// PRSNL Capture - Content Script

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getSelection') {
    // Get any selected text on the page
    const selectedText = window.getSelection().toString().trim();
    
    // Send the selected text back to the background script
    sendResponse({ selectedText });
    
    return true; // Required for async response
  } else if (message.action === 'showCaptureEffect') {
    // Show visual feedback for successful capture
    showCaptureEffect(message.type || 'page');
    return true;
  }
});

// Show a visual feedback when content is captured
function showCaptureEffect(type = 'page') {
  // Highlight selected text briefly if it's a selection capture
  if (type === 'selection') {
    highlightSelection();
  }
  
  // Create notification element
  const effect = document.createElement('div');
  effect.className = 'prsnl-capture-effect';
  effect.innerHTML = `
    <span>${type === 'selection' ? 'Selection' : 'Page'} captured to PRSNL!</span>
  `;
  
  // Add to page
  document.body.appendChild(effect);
  
  // Trigger entrance animation
  setTimeout(() => {
    effect.style.opacity = '1';
    effect.style.transform = 'translateY(0)';
  }, 10);
  
  // Remove after delay
  setTimeout(() => {
    effect.style.opacity = '0';
    effect.style.transform = 'translateY(-10px)';
    setTimeout(() => {
      if (effect.parentNode) {
        document.body.removeChild(effect);
      }
    }, 300);
  }, 3000);
}

// Highlight selected text briefly
function highlightSelection() {
  const selection = window.getSelection();
  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    const selectedText = range.toString().trim();
    
    if (selectedText) {
      // Create highlight wrapper
      const highlight = document.createElement('span');
      highlight.className = 'prsnl-selection-highlight';
      
      try {
        // Wrap the selected content
        range.surroundContents(highlight);
        
        // Remove highlight after animation
        setTimeout(() => {
          if (highlight.parentNode) {
            const parent = highlight.parentNode;
            parent.insertBefore(document.createTextNode(selectedText), highlight);
            parent.removeChild(highlight);
          }
        }, 1000);
      } catch (e) {
        // If wrapping fails (complex selection), just clear selection
        console.log('Could not highlight complex selection');
      }
    }
  }
}

// Add capture effect styles if not already present
function addCaptureStyles() {
  if (!document.getElementById('prsnl-capture-styles')) {
    const style = document.createElement('style');
    style.id = 'prsnl-capture-styles';
    style.textContent = `
      .prsnl-capture-effect {
        position: fixed !important;
        top: 20px !important;
        right: 20px !important;
        background-color: rgba(18, 18, 18, 0.9) !important;
        color: white !important;
        padding: 10px 16px !important;
        border-radius: 8px !important;
        z-index: 999999 !important;
        font-family: 'Mulish', system-ui, -apple-system, sans-serif !important;
        font-size: 14px !important;
        opacity: 0 !important;
        transform: translateY(-10px) !important;
        transition: opacity 0.3s, transform 0.3s !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        border-left: 3px solid #dc143c !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        pointer-events: none !important;
      }
      
      .prsnl-capture-effect::before {
        content: '' !important;
        width: 14px !important;
        height: 14px !important;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="%23dc143c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>') !important;
        background-size: contain !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        flex-shrink: 0 !important;
      }
      
      .prsnl-selection-highlight {
        background-color: rgba(220, 20, 60, 0.2) !important;
        transition: background-color 0.3s !important;
        border-radius: 2px !important;
      }
    `;
    document.head.appendChild(style);
  }
}

// Add styles when content script loads
addCaptureStyles();