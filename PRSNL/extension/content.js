// PRSNL Capture - Content Script

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getSelection') {
    // Get any selected text on the page
    const selectedText = window.getSelection().toString().trim();
    
    // Send the selected text back to the background script
    sendResponse({ selectedText });
    
    // Show a subtle visual feedback that content was captured
    if (selectedText) {
      showCaptureEffect();
    }
  }
  return true; // Required for async response
});

// Show a subtle visual feedback when content is captured
function showCaptureEffect() {
  // Create a visual effect element
  const effect = document.createElement('div');
  effect.className = 'prsnl-capture-effect';
  effect.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 8px 12px;
    border-radius: 4px;
    z-index: 999999;
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 14px;
    opacity: 0;
    transform: translateY(-10px);
    transition: opacity 0.3s, transform 0.3s;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  `;
  effect.textContent = 'Selection captured';
  
  // Add to page
  document.body.appendChild(effect);
  
  // Trigger animation
  setTimeout(() => {
    effect.style.opacity = '1';
    effect.style.transform = 'translateY(0)';
  }, 10);
  
  // Remove after animation
  setTimeout(() => {
    effect.style.opacity = '0';
    effect.style.transform = 'translateY(-10px)';
    setTimeout(() => {
      document.body.removeChild(effect);
    }, 300);
  }, 2000);
}
