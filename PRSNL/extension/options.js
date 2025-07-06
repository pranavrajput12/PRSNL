// PRSNL Capture - Options Script

document.addEventListener('DOMContentLoaded', () => {
  // DOM elements
  const apiUrlInput = document.getElementById('api-url');
  const autoTagsToggle = document.getElementById('auto-tags');
  const showNotificationsToggle = document.getElementById('show-notifications');
  const contextMenuToggle = document.getElementById('context-menu');
  const saveBtn = document.getElementById('save-btn');
  const resetBtn = document.getElementById('reset-btn');
  const statusMessage = document.getElementById('status-message');
  
  // Default settings
  const defaultSettings = {
    apiUrl: 'http://localhost:8000',
    autoTags: true,
    showNotifications: true,
    contextMenu: true
  };
  
  // Load settings
  loadSettings();
  
  // Save button click
  saveBtn.addEventListener('click', saveSettings);
  
  // Reset button click
  resetBtn.addEventListener('click', () => {
    // Reset to defaults
    apiUrlInput.value = defaultSettings.apiUrl;
    autoTagsToggle.checked = defaultSettings.autoTags;
    showNotificationsToggle.checked = defaultSettings.showNotifications;
    contextMenuToggle.checked = defaultSettings.contextMenu;
    
    // Save the default settings
    saveSettings();
  });
  
  // Load settings from storage
  function loadSettings() {
    chrome.storage.sync.get(defaultSettings, (settings) => {
      apiUrlInput.value = settings.apiUrl;
      autoTagsToggle.checked = settings.autoTags;
      showNotificationsToggle.checked = settings.showNotifications;
      contextMenuToggle.checked = settings.contextMenu;
    });
  }
  
  // Save settings to storage
  function saveSettings() {
    const settings = {
      apiUrl: apiUrlInput.value.trim(),
      autoTags: autoTagsToggle.checked,
      showNotifications: showNotificationsToggle.checked,
      contextMenu: contextMenuToggle.checked
    };
    
    chrome.storage.sync.set(settings, () => {
      // Update context menu based on setting
      chrome.runtime.sendMessage({
        action: 'updateContextMenu',
        enabled: settings.contextMenu
      });
      
      // Show success message
      showStatus('Settings saved!', 'success');
    });
  }
  
  // Show status message
  function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status ${type}`;
    statusMessage.style.display = 'block';
    
    // Hide after 3 seconds
    setTimeout(() => {
      statusMessage.style.display = 'none';
    }, 3000);
  }
});