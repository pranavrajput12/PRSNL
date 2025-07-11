# PRSNL Chrome Extension - Code Examples & Integration Patterns

## 🎯 Complete popup.html Update Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PRSNL Capture</title>
  <link rel="stylesheet" href="styles.css">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap">
</head>
<body>
  <div class="container">
    <header>
      <h1 class="gradient-text">PRSNL Capture</h1>
      <div class="header-actions">
        <button id="settings-btn" class="icon-btn" title="Settings">
          <svg><!-- settings icon --></svg>
        </button>
      </div>
    </header>
    
    <div class="capture-form">
      <!-- URL Preview Section -->
      <div class="url-preview">
        <div id="favicon-container"></div>
        <div id="url-info">
          <div id="page-title" class="truncate"></div>
          <div id="page-url" class="truncate"></div>
        </div>
      </div>
      
      <!-- Content Type Selector -->
      <div class="form-group">
        <label for="content-type">Content Type</label>
        <select id="content-type" class="form-select">
          <option value="auto">Auto-detect</option>
          <option value="article">Article</option>
          <option value="tutorial">Tutorial</option>
          <option value="video">Video</option>
          <option value="development">Development</option>
          <option value="document">Document</option>
          <option value="note">Note</option>
          <option value="link">Link</option>
        </select>
      </div>
      
      <!-- Development-specific fields (hidden by default) -->
      <div id="development-fields" class="development-section" style="display: none;">
        <div class="form-group">
          <label for="programming-language">Programming Language</label>
          <input type="text" id="programming-language" placeholder="e.g., Python, JavaScript" />
        </div>
        
        <div class="form-group">
          <label for="project-category">Project Category</label>
          <input type="text" id="project-category" placeholder="e.g., Web Development, Machine Learning" />
        </div>
        
        <div class="form-group">
          <label for="difficulty-level">Difficulty Level</label>
          <div class="difficulty-selector">
            <input type="range" id="difficulty-level" min="1" max="5" value="3" />
            <div class="difficulty-labels">
              <span>Beginner</span>
              <span>Advanced</span>
            </div>
          </div>
        </div>
        
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" id="career-related" />
            <span>Career/Job Related</span>
          </label>
        </div>
      </div>
      
      <!-- AI Summarization Toggle -->
      <div class="form-group">
        <label class="toggle-label">
          <input type="checkbox" id="enable-summarization" checked />
          <span class="toggle-switch"></span>
          <span>Enable AI Summarization</span>
        </label>
      </div>
      
      <!-- Tags Section -->
      <div class="tag-input-container">
        <label for="tag-input">
          <svg><!-- tag icon --></svg>
          Add Tags
        </label>
        <div class="tag-input-wrapper">
          <input type="text" id="tag-input" placeholder="Type tags and press Enter" />
        </div>
        <div id="tags-container"></div>
      </div>
      
      <!-- Selection Preview -->
      <div class="selection-preview" id="selection-container" style="display: none;">
        <label>Selected Text</label>
        <div id="selection-text" class="selection-text"></div>
      </div>
      
      <!-- Action Buttons -->
      <div class="actions">
        <button id="capture-btn" class="primary-btn">
          <span class="btn-text">Capture</span>
          <span class="btn-loader" style="display: none;">
            <svg class="spinner"><!-- spinner svg --></svg>
          </span>
        </button>
        <button id="cancel-btn" class="secondary-btn">Cancel</button>
      </div>
      
      <div class="shortcut-hint">
        <span class="keyboard-hint">⌘/Ctrl</span> + <span class="keyboard-hint">Shift</span> + <span class="keyboard-hint">S</span> to capture
      </div>
    </div>
    
    <div id="status-message" class="status"></div>
  </div>
  
  <script src="popup.js"></script>
</body>
</html>
```

## 🎨 Enhanced styles.css

```css
:root {
  /* Neural/Electrical Theme Colors */
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --bg-dark: #0a0a0a;
  --surface-dark: #1a1a1a;
  --surface-hover: #252525;
  --border-color: #2a2a2a;
  --text-primary: #ffffff;
  --text-secondary: #a0a0a0;
  --text-muted: #666666;
  --success-color: #10b981;
  --error-color: #ef4444;
  --warning-color: #f59e0b;
  --info-color: #3b82f6;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-dark);
  color: var(--text-primary);
  width: 400px;
  min-height: 500px;
}

.container {
  padding: 20px;
}

/* Header Styles */
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.gradient-text {
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 24px;
  font-weight: 700;
}

/* Form Styles */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-select,
input[type="text"] {
  width: 100%;
  padding: 10px 12px;
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
}

.form-select:hover,
input[type="text"]:hover {
  background: var(--surface-hover);
  border-color: #3a3a3a;
}

.form-select:focus,
input[type="text"]:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Development Section */
.development-section {
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Toggle Switch */
.toggle-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  background: var(--surface-dark);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  margin-right: 12px;
  transition: all 0.3s ease;
}

.toggle-switch::after {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  background: var(--text-secondary);
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: all 0.3s ease;
}

input[type="checkbox"]:checked + .toggle-switch {
  background: var(--primary-gradient);
  border-color: transparent;
}

input[type="checkbox"]:checked + .toggle-switch::after {
  transform: translateX(20px);
  background: white;
}

input[type="checkbox"] {
  display: none;
}

/* Buttons */
.primary-btn {
  width: 100%;
  padding: 12px 24px;
  background: var(--primary-gradient);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.primary-btn:active {
  transform: translateY(0);
}

.primary-btn[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Loading Spinner */
.spinner {
  animation: rotate 1s linear infinite;
  width: 16px;
  height: 16px;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Status Messages */
.status {
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  display: none;
  animation: fadeIn 0.3s ease;
}

.status.success {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: var(--success-color);
}

.status.error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: var(--error-color);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

## 📱 Complete popup.js Implementation

```javascript
// State management
let currentTab = null;
let selectedText = '';
let tags = [];
let isCapturing = false;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  // Get current tab info
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTab = tab;
  
  // Display tab info
  displayTabInfo(tab);
  
  // Check for selected text
  chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, (response) => {
    if (response && response.selection) {
      selectedText = response.selection;
      displaySelection(selectedText);
    }
  });
  
  // Set up event listeners
  setupEventListeners();
  
  // Auto-detect content type
  autoDetectContentType(tab.url);
});

// Display tab information
function displayTabInfo(tab) {
  const favicon = document.getElementById('favicon-container');
  const title = document.getElementById('page-title');
  const url = document.getElementById('page-url');
  
  // Set favicon
  const faviconUrl = `https://www.google.com/s2/favicons?domain=${new URL(tab.url).hostname}&sz=32`;
  favicon.innerHTML = `<img src="${faviconUrl}" alt="Site favicon" />`;
  
  // Set title and URL
  title.textContent = tab.title;
  url.textContent = tab.url;
}

// Display selected text
function displaySelection(text) {
  const container = document.getElementById('selection-container');
  const textElement = document.getElementById('selection-text');
  
  if (text && text.trim()) {
    container.style.display = 'block';
    textElement.textContent = text.substring(0, 200) + (text.length > 200 ? '...' : '');
  }
}

// Auto-detect content type based on URL
function autoDetectContentType(url) {
  const contentTypeSelect = document.getElementById('content-type');
  
  if (url.includes('github.com')) {
    contentTypeSelect.value = 'development';
    toggleDevelopmentFields(true);
  } else if (url.includes('youtube.com') || url.includes('youtu.be')) {
    contentTypeSelect.value = 'video';
  } else if (url.includes('medium.com') || url.includes('dev.to')) {
    contentTypeSelect.value = 'article';
  }
}

// Toggle development fields visibility
function toggleDevelopmentFields(show) {
  const devFields = document.getElementById('development-fields');
  devFields.style.display = show ? 'block' : 'none';
}

// Set up all event listeners
function setupEventListeners() {
  // Content type change
  document.getElementById('content-type').addEventListener('change', (e) => {
    toggleDevelopmentFields(e.target.value === 'development');
  });
  
  // Tag input
  const tagInput = document.getElementById('tag-input');
  tagInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      e.preventDefault();
      addTag(e.target.value.trim());
      e.target.value = '';
    }
  });
  
  // Capture button
  document.getElementById('capture-btn').addEventListener('click', handleCapture);
  
  // Cancel button
  document.getElementById('cancel-btn').addEventListener('click', () => {
    window.close();
  });
  
  // Settings button
  document.getElementById('settings-btn').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
  
  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleCapture();
    }
    if (e.key === 'Escape') {
      window.close();
    }
  });
}

// Add a tag
function addTag(tagText) {
  if (tags.includes(tagText.toLowerCase())) return;
  
  tags.push(tagText.toLowerCase());
  renderTags();
}

// Remove a tag
function removeTag(tagText) {
  tags = tags.filter(t => t !== tagText);
  renderTags();
}

// Render tags
function renderTags() {
  const container = document.getElementById('tags-container');
  container.innerHTML = tags.map(tag => `
    <span class="tag">
      ${tag}
      <button class="tag-remove" data-tag="${tag}">×</button>
    </span>
  `).join('');
  
  // Add remove listeners
  container.querySelectorAll('.tag-remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
      removeTag(e.target.dataset.tag);
    });
  });
}

// Handle capture
async function handleCapture() {
  if (isCapturing) return;
  
  isCapturing = true;
  const captureBtn = document.getElementById('capture-btn');
  const btnText = captureBtn.querySelector('.btn-text');
  const btnLoader = captureBtn.querySelector('.btn-loader');
  
  // Show loading state
  btnText.style.display = 'none';
  btnLoader.style.display = 'inline-block';
  captureBtn.disabled = true;
  
  try {
    // Gather form data
    const captureData = {
      url: currentTab.url,
      title: currentTab.title,
      content: selectedText || null,
      highlight: selectedText || null,
      tags: tags,
      enable_summarization: document.getElementById('enable-summarization').checked,
      content_type: document.getElementById('content-type').value
    };
    
    // Add development fields if applicable
    if (captureData.content_type === 'development') {
      const progLang = document.getElementById('programming-language').value;
      const projCat = document.getElementById('project-category').value;
      const diffLevel = document.getElementById('difficulty-level').value;
      const careerRelated = document.getElementById('career-related').checked;
      
      if (progLang) captureData.programming_language = progLang;
      if (projCat) captureData.project_category = projCat;
      if (diffLevel) captureData.difficulty_level = parseInt(diffLevel);
      captureData.is_career_related = careerRelated;
    }
    
    // Send to backend
    const response = await fetch('http://localhost:8000/api/capture', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(captureData)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showStatus('Content captured successfully!', 'success');
      
      // Show notification
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon128.png',
        title: 'PRSNL Capture',
        message: 'Content captured successfully!'
      });
      
      // Close popup after delay
      setTimeout(() => {
        window.close();
      }, 1500);
    } else {
      throw new Error(result.detail || 'Capture failed');
    }
  } catch (error) {
    console.error('Capture error:', error);
    showStatus(error.message || 'Failed to capture content', 'error');
  } finally {
    // Reset button state
    btnText.style.display = 'inline-block';
    btnLoader.style.display = 'none';
    captureBtn.disabled = false;
    isCapturing = false;
  }
}

// Show status message
function showStatus(message, type) {
  const statusEl = document.getElementById('status-message');
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  statusEl.style.display = 'block';
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    statusEl.style.display = 'none';
  }, 5000);
}
```

## 🔧 Updated background.js

```javascript
// PRSNL Capture - Background Service Worker v2

// Configuration
const API_BASE_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/ws';

// WebSocket connection
let ws = null;

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  setupContextMenu(true);
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
    await captureSelection();
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
```

## 🔍 Content Script Enhancement (content.js)

```javascript
// Enhanced content script with selection tracking and smart detection

let selectedText = '';

// Track text selection
document.addEventListener('selectionchange', () => {
  const selection = window.getSelection();
  selectedText = selection.toString().trim();
});

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getSelection') {
    sendResponse({ selection: selectedText });
  } else if (request.action === 'getPageMetadata') {
    sendResponse({
      selection: selectedText,
      metadata: extractPageMetadata()
    });
  }
});

// Extract additional page metadata
function extractPageMetadata() {
  const metadata = {
    readTime: estimateReadTime(),
    mainContent: extractMainContent(),
    codeBlocks: findCodeBlocks(),
    images: findImages()
  };
  
  // GitHub-specific metadata
  if (window.location.hostname === 'github.com') {
    metadata.github = extractGitHubMetadata();
  }
  
  return metadata;
}

// Estimate reading time
function estimateReadTime() {
  const text = document.body.innerText;
  const wordsPerMinute = 200;
  const wordCount = text.trim().split(/\s+/).length;
  return Math.ceil(wordCount / wordsPerMinute);
}

// Extract main content using readability heuristics
function extractMainContent() {
  // Look for article, main, or content containers
  const contentSelectors = ['article', 'main', '[role="main"]', '.content', '#content'];
  
  for (const selector of contentSelectors) {
    const element = document.querySelector(selector);
    if (element) {
      return element.innerText.substring(0, 1000);
    }
  }
  
  return document.body.innerText.substring(0, 1000);
}

// Find code blocks
function findCodeBlocks() {
  const codeBlocks = [];
  const blocks = document.querySelectorAll('pre code, .highlight, .code-block');
  
  blocks.forEach(block => {
    const language = block.className.match(/language-(\w+)/)?.[1] || 'unknown';
    codeBlocks.push({
      language,
      content: block.textContent.substring(0, 500)
    });
  });
  
  return codeBlocks;
}

// Find images
function findImages() {
  const images = [];
  const imgs = document.querySelectorAll('img');
  
  imgs.forEach(img => {
    if (img.width > 100 && img.height > 100) {
      images.push({
        src: img.src,
        alt: img.alt,
        width: img.width,
        height: img.height
      });
    }
  });
  
  return images.slice(0, 5); // Limit to 5 images
}

// Extract GitHub-specific metadata
function extractGitHubMetadata() {
  const metadata = {};
  
  // Repository info
  const repoLink = document.querySelector('[itemprop="name"] a');
  if (repoLink) {
    metadata.repository = repoLink.textContent.trim();
  }
  
  // Language
  const langElement = document.querySelector('[itemprop="programmingLanguage"]');
  if (langElement) {
    metadata.language = langElement.textContent.trim();
  }
  
  // Stars
  const starsElement = document.querySelector('[aria-label*="star"]');
  if (starsElement) {
    metadata.stars = starsElement.textContent.trim();
  }
  
  // README content
  const readme = document.querySelector('.markdown-body');
  if (readme) {
    metadata.hasReadme = true;
    metadata.readmePreview = readme.textContent.substring(0, 500);
  }
  
  return metadata;
}
```

## 📋 Testing Examples

```javascript
// Test capture request
const testCapture = async () => {
  const testData = {
    url: "https://github.com/user/repo",
    title: "Test Repository",
    content_type: "development",
    programming_language: "Python",
    project_category: "Machine Learning",
    difficulty_level: 3,
    is_career_related: false,
    tags: ["python", "ml", "tutorial"],
    enable_summarization: true
  };
  
  try {
    const response = await fetch('http://localhost:8000/api/capture', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(testData)
    });
    
    console.log('Response:', await response.json());
  } catch (error) {
    console.error('Test failed:', error);
  }
};
```

## 🔒 Security Enhancements

```javascript
// Sanitize user input
function sanitizeInput(input) {
  // Remove HTML tags
  const div = document.createElement('div');
  div.textContent = input;
  return div.innerHTML;
}

// Validate URL
function isValidUrl(url) {
  try {
    const u = new URL(url);
    return ['http:', 'https:'].includes(u.protocol);
  } catch {
    return false;
  }
}

// Secure storage
async function secureStore(key, data) {
  // Encrypt sensitive data before storing
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: new Uint8Array(12) },
    await getStorageKey(),
    new TextEncoder().encode(JSON.stringify(data))
  );
  
  await chrome.storage.local.set({
    [key]: Array.from(new Uint8Array(encrypted))
  });
}
```

---

This document provides comprehensive code examples for updating the PRSNL Chrome Extension to work with the latest backend changes.