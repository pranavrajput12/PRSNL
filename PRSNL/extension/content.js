// Enhanced content script with bundled modules + external library support
console.log('🔄 [CONTENT] Content script loading...');
console.log('🌐 [CONTENT] Page URL:', window.location.href);
console.log('📄 [CONTENT] Page title:', document.title);

// External library loader (optional enhancement)
async function loadExternalLibs() {
  const libsToLoad = [];
  
  if (!window.DOMPurify) {
    libsToLoad.push({
      name: 'DOMPurify',
      url: 'https://cdn.jsdelivr.net/npm/dompurify@3.0.5/dist/purify.min.js'
    });
  }
  
  if (!window.TurndownService) {
    libsToLoad.push({
      name: 'TurndownService', 
      url: 'https://cdn.jsdelivr.net/npm/turndown@7.1.2/dist/turndown.js'
    });
  }
  
  if (libsToLoad.length > 0) {
    console.log('📚 [CONTENT] Loading external libraries:', libsToLoad.map(lib => lib.name));
    
    for (const lib of libsToLoad) {
      try {
        await loadScript(lib.url);
        console.log(`✅ [CONTENT] Loaded ${lib.name}`);
      } catch (error) {
        console.warn(`⚠️ [CONTENT] Failed to load ${lib.name}:`, error);
      }
    }
  }
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// Base Platform Adapter class
class PlatformAdapter {
  detect() { throw new Error('Must implement detect()') }
  async extractConversation() { throw new Error('Must implement extractConversation()') }
  isConversationPage() { throw new Error('Must implement isConversationPage()') }
  getConversationTitle() { throw new Error('Must implement getConversationTitle()') }
  getConversationUrl() { 
    return window.location.href;
  }
}

// ChatGPT Adapter
class ChatGPTAdapter extends PlatformAdapter {
  detect() { 
    return window.location.hostname.includes('chatgpt.com') || window.location.hostname.includes('chat.openai.com');
  }
  
  isConversationPage() {
    return window.location.pathname.includes('/c/');
  }
  
  async extractConversation() {
    if (!this.isConversationPage()) {
      throw new Error('Not a ChatGPT conversation page');
    }

    try {
      // Get all message elements using the confirmed working selector
      const messageElements = document.querySelectorAll('[data-message-author-role]');
      const messages = [];
      
      console.log(`🔍 [CONTENT] Found ${messageElements.length} message elements`);
      
      // Extract messages with proper content selectors
      messageElements.forEach((element, index) => {
        const role = element.getAttribute('data-message-author-role');
        
        // Use different selectors based on role (from console analysis)
        let contentElement;
        let textContent = '';
        let htmlContent = '';
        
        if (role === 'user') {
          // User messages: content in .whitespace-pre-wrap
          contentElement = element.querySelector('.whitespace-pre-wrap');
          if (contentElement) {
            textContent = contentElement.textContent || '';
            htmlContent = contentElement.innerHTML || '';
          }
        } else {
          // Assistant messages: content in .markdown
          contentElement = element.querySelector('.markdown');
          if (contentElement) {
            textContent = contentElement.textContent || '';
            htmlContent = contentElement.innerHTML || '';
          }
        }
        
        // Skip if no content found
        if (!contentElement || !textContent.trim()) {
          console.log(`⚠️ [CONTENT] Skipping message ${index + 1} (${role}) - no content found`);
          return;
        }
        
        console.log(`✅ [CONTENT] Extracted message ${index + 1} (${role}): ${textContent.substring(0, 50)}...`);
        
        messages.push({
          id: `msg-${index}`,
          role: role === 'user' ? 'user' : 'assistant',
          content: {
            text: textContent,
            html: htmlContent
          },
          timestamp: new Date().toISOString()
        });
      });
      
      return {
        id: this._generateId(),
        platform: 'chatgpt',
        url: this.getConversationUrl(),
        title: this.getConversationTitle(),
        fetchedAt: new Date().toISOString(),
        messages
      };
    } catch (error) {
      console.error('Error extracting ChatGPT conversation:', error);
      throw new Error(`Failed to extract ChatGPT conversation: ${error.message}`);
    }
  }
  
  getConversationTitle() {
    // Based on console analysis, use document.title as primary source
    const documentTitle = document.title;
    if (documentTitle && documentTitle !== 'ChatGPT' && !documentTitle.includes('New chat')) {
      console.log(`🏷️ [CONTENT] Using document title: ${documentTitle}`);
      return documentTitle;
    }
    
    // Try alternative selectors as backup
    const selectors = [
      'nav .truncate',
      '[data-testid="conversation-title"]',
      '.conversation-title',
      'h1'
    ];
    
    for (const selector of selectors) {
      const titleElement = document.querySelector(selector);
      if (titleElement && titleElement.textContent.trim() && 
          titleElement.textContent.trim() !== 'New chat') {
        console.log(`🏷️ [CONTENT] Using selector ${selector}: ${titleElement.textContent.trim()}`);
        return titleElement.textContent.trim();
      }
    }
    
    // Fallback to generic name
    console.log(`🏷️ [CONTENT] Using fallback title`);
    return 'ChatGPT Conversation';
  }
  
  _generateId() {
    return 'chatgpt-' + Math.random().toString(36).substring(2, 15);
  }
}

// Claude Adapter
class ClaudeAdapter extends PlatformAdapter {
  detect() {
    return window.location.hostname.includes('claude.ai');
  }
  
  isConversationPage() {
    return window.location.pathname.includes('/chat/');
  }
  
  async extractConversation() {
    if (!this.isConversationPage()) {
      throw new Error('Not a Claude conversation page');
    }

    try {
      // Look for message elements with multiple possible selectors
      const messageSelectors = [
        '[data-is-streaming]',
        '.message',
        '.conversation-message',
        '.human-message-container',
        '.assistant-message-container'
      ];
      
      let messageElements = [];
      for (const selector of messageSelectors) {
        messageElements = document.querySelectorAll(selector);
        if (messageElements.length > 0) break;
      }
      
      const messages = [];
      
      messageElements.forEach((element, index) => {
        // Try to determine role from various indicators
        const isHuman = element.classList.contains('human-message-container') ||
                       element.querySelector('[data-is-human="true"]') ||
                       element.textContent.includes('Human:');
        const role = isHuman ? 'user' : 'assistant';
        
        const contentElement = element.querySelector('.message-content') || element;
        
        if (contentElement && contentElement.textContent.trim()) {
          messages.push({
            id: `msg-${index}`,
            role: role,
            content: {
              text: contentElement.textContent || '',
              html: contentElement.innerHTML || ''
            },
            timestamp: new Date().toISOString()
          });
        }
      });
      
      return {
        id: this._generateId(),
        platform: 'claude',
        url: this.getConversationUrl(),
        title: this.getConversationTitle(),
        fetchedAt: new Date().toISOString(),
        messages
      };
    } catch (error) {
      console.error('Error extracting Claude conversation:', error);
      throw new Error(`Failed to extract Claude conversation: ${error.message}`);
    }
  }
  
  getConversationTitle() {
    const titleElement = document.querySelector('.conversation-title') || 
                        document.querySelector('h1') ||
                        document.querySelector('[data-testid="conversation-title"]');
    if (titleElement) {
      return titleElement.textContent.trim();
    }
    
    return document.title || 'Claude Conversation';
  }
  
  _generateId() {
    return 'claude-' + Math.random().toString(36).substring(2, 15);
  }
}

// Perplexity Adapter
class PerplexityAdapter extends PlatformAdapter {
  detect() {
    return window.location.hostname.includes('perplexity.ai');
  }
  
  isConversationPage() {
    return window.location.pathname.includes('/search/') || 
           document.querySelector('.conversation') !== null;
  }
  
  async extractConversation() {
    if (!this.isConversationPage()) {
      throw new Error('Not a Perplexity conversation page');
    }

    try {
      const messageElements = document.querySelectorAll('.message, .query, .answer');
      const messages = [];
      
      messageElements.forEach((element, index) => {
        const isQuery = element.classList.contains('query') || 
                       element.querySelector('.query-text');
        const role = isQuery ? 'user' : 'assistant';
        
        if (element.textContent.trim()) {
          messages.push({
            id: `msg-${index}`,
            role: role,
            content: {
              text: element.textContent || '',
              html: element.innerHTML || ''
            },
            timestamp: new Date().toISOString()
          });
        }
      });
      
      return {
        id: this._generateId(),
        platform: 'perplexity',
        url: this.getConversationUrl(),
        title: this.getConversationTitle(),
        fetchedAt: new Date().toISOString(),
        messages
      };
    } catch (error) {
      console.error('Error extracting Perplexity conversation:', error);
      throw new Error(`Failed to extract Perplexity conversation: ${error.message}`);
    }
  }
  
  getConversationTitle() {
    return 'Perplexity Search';
  }
  
  _generateId() {
    return 'perplexity-' + Math.random().toString(36).substring(2, 15);
  }
}

// Adapter Factory
class AdapterFactory {
  static _adapters = [
    ChatGPTAdapter,
    ClaudeAdapter,
    PerplexityAdapter
  ];
  
  static getAdapter() {
    for (const AdapterClass of this._adapters) {
      const adapter = new AdapterClass();
      if (adapter.detect()) {
        console.log(`🎯 [CONTENT] Detected platform: ${AdapterClass.name}`);
        return adapter;
      }
    }
    console.log('❌ [CONTENT] No matching platform adapter found');
    return null;
  }
  
  static hasConversation() {
    const adapter = this.getAdapter();
    return adapter ? adapter.isConversationPage() : false;
  }
  
  static async extractConversation() {
    const adapter = this.getAdapter();
    
    if (!adapter) {
      throw new Error('No suitable adapter found for this platform');
    }
    
    if (!adapter.isConversationPage()) {
      throw new Error('Current page does not contain a conversation');
    }
    
    return adapter.extractConversation();
  }
  
  static getPlatformInfo() {
    const adapter = this.getAdapter();
    
    if (!adapter) {
      return { platform: null, isConversation: false };
    }
    
    const platform = adapter.constructor.name
      .replace('Adapter', '')
      .toLowerCase();
    
    return {
      platform,
      isConversation: adapter.isConversationPage()
    };
  }
}

// Enhanced HTML sanitizer (with external library support)
class SimpleSanitizer {
  static stripHtml(html) {
    if (!html) return '';
    
    const temp = document.createElement('div');
    temp.innerHTML = html;
    return temp.textContent
      .replace(/\s+/g, ' ')
      .trim();
  }
  
  static basicSanitize(html) {
    if (!html) return '';
    
    // Use DOMPurify if available, otherwise fallback to basic sanitization
    if (window.DOMPurify) {
      console.log('🧹 [CONTENT] Using DOMPurify for sanitization');
      return window.DOMPurify.sanitize(html, {
        ALLOWED_TAGS: [
          'a', 'b', 'br', 'code', 'div', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'i', 'li', 'ol', 'p', 'pre', 'span', 'strong', 'table', 'tbody', 'td',
          'th', 'thead', 'tr', 'ul'
        ],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'id']
      });
    }
    
    // Basic sanitization fallback
    console.log('🧹 [CONTENT] Using basic sanitization (no DOMPurify)');
    return html
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/on\w+="[^"]*"/gi, '')
      .replace(/javascript:/gi, '');
  }
}

// Conversation Extractor Service
class ConversationExtractor {
  static async extractConversation() {
    try {
      console.log('🔍 [CONTENT] Starting conversation extraction...');
      
      const conversation = await AdapterFactory.extractConversation();
      
      if (!conversation) {
        throw new Error('Failed to extract conversation data');
      }
      
      console.log('✅ [CONTENT] Raw conversation extracted:', {
        platform: conversation.platform,
        messageCount: conversation.messages.length,
        title: conversation.title
      });
      
      // Process and sanitize the messages
      const sanitizedMessages = conversation.messages.map(message => {
        return {
          ...message,
          content: {
            text: SimpleSanitizer.stripHtml(message.content.text),
            html: SimpleSanitizer.basicSanitize(message.content.html)
          }
        };
      });
      
      return {
        ...conversation,
        messages: sanitizedMessages
      };
    } catch (error) {
      console.error('❌ [CONTENT] Error in ConversationExtractor:', error);
      throw new Error(`Conversation extraction failed: ${error.message}`);
    }
  }
  
  static canExtractConversation() {
    return AdapterFactory.hasConversation();
  }
  
  static getPlatformInfo() {
    return AdapterFactory.getPlatformInfo();
  }
}

// Simple conversation processor
class ConversationProcessor {
  static processConversation(conversation) {
    if (!conversation) {
      throw new Error('No conversation data provided');
    }

    this._validateConversation(conversation);

    const conversationId = conversation.id || this._generateId();

    const processedMessages = conversation.messages.map(message => {
      const content = message.content || {};
      
      const sanitizedText = SimpleSanitizer.stripHtml(content.text || '');
      const sanitizedHtml = SimpleSanitizer.basicSanitize(content.html || '');
      
      return {
        id: message.id || this._generateId(),
        role: message.role,
        timestamp: message.timestamp || new Date().toISOString(),
        content: {
          text: sanitizedText,
          html: sanitizedHtml,
          markdown: sanitizedText // Simple fallback to text
        }
      };
    });

    const filteredMessages = processedMessages.filter(msg => 
      msg.content && msg.content.text.trim()
    );

    return {
      id: conversationId,
      title: SimpleSanitizer.stripHtml(conversation.title || 'Untitled Conversation'),
      platform: conversation.platform,
      source_url: conversation.url || window.location.href,
      timestamp: conversation.fetchedAt || new Date().toISOString(),
      messages: filteredMessages
    };
  }

  static _validateConversation(conversation) {
    if (!conversation.platform) {
      throw new Error('Missing platform information');
    }

    if (!Array.isArray(conversation.messages) || conversation.messages.length === 0) {
      throw new Error('Conversation must contain at least one message');
    }

    conversation.messages.forEach((message, index) => {
      if (!message.role) {
        throw new Error(`Message at index ${index} is missing role`);
      }
      
      if (!message.content) {
        throw new Error(`Message at index ${index} is missing content`);
      }
    });
  }
  
  static _generateId() {
    return 'id-' + Math.random().toString(36).substring(2, 15) + '-' + Date.now().toString(36);
  }
}

// Simple conversation cache
class ConversationCache {
  static _STORAGE_KEY = 'prsnl_conversation_cache';
  static _MAX_CACHE_SIZE = 20;
  
  static async addToCache(conversation) {
    try {
      if (!conversation || !conversation.id) {
        throw new Error('Invalid conversation object');
      }
      
      const cache = await this._getCache();
      
      cache[conversation.id] = {
        data: conversation,
        timestamp: new Date().toISOString()
      };
      
      const ids = Object.keys(cache);
      if (ids.length > this._MAX_CACHE_SIZE) {
        const sortedIds = ids.sort((a, b) => {
          return new Date(cache[a].timestamp) - new Date(cache[b].timestamp);
        });
        
        const itemsToRemove = sortedIds.slice(0, ids.length - this._MAX_CACHE_SIZE);
        itemsToRemove.forEach(id => delete cache[id]);
      }
      
      await this._saveCache(cache);
    } catch (error) {
      console.error('❌ [CONTENT] Error adding conversation to cache:', error);
    }
  }
  
  static async _getCache() {
    return new Promise((resolve) => {
      chrome.storage.local.get([this._STORAGE_KEY], (result) => {
        resolve(result[this._STORAGE_KEY] || {});
      });
    });
  }
  
  static async _saveCache(cache) {
    return new Promise((resolve) => {
      const data = {};
      data[this._STORAGE_KEY] = cache;
      chrome.storage.local.set(data, resolve);
    });
  }
}

// Track text selection
let selectedText = '';

document.addEventListener('selectionchange', () => {
  const selection = window.getSelection();
  selectedText = selection.toString().trim();
});

console.log('📦 [CONTENT] All modules bundled successfully');

// Initialize external libraries (optional enhancement)
loadExternalLibs().then(() => {
  console.log('📚 [CONTENT] External library initialization complete');
}).catch(error => {
  console.warn('⚠️ [CONTENT] External library loading failed:', error);
});

console.log('✅ [CONTENT] Content script initialization complete');

// Extract and process conversation function
async function extractAndProcessConversation() {
  console.log('🔄 [CONTENT] Starting conversation extraction pipeline...');
  
  try {
    console.log('🔍 [CONTENT] Step 1: Getting platform information...');
    const platformInfo = ConversationExtractor.getPlatformInfo();
    console.log('🔍 [CONTENT] Platform info:', platformInfo);
    
    if (!platformInfo.isConversation) {
      throw new Error(`No active conversation detected on ${platformInfo.platform || 'this page'}`);
    }
    
    console.log('📤 [CONTENT] Step 2: Extracting raw conversation data...');
    const rawConversation = await ConversationExtractor.extractConversation();
    console.log('📤 [CONTENT] Raw conversation extracted:', {
      platform: rawConversation?.platform,
      title: rawConversation?.title,
      messagesFound: rawConversation?.messages?.length,
      timestamp: rawConversation?.timestamp
    });
    
    if (!rawConversation) {
      throw new Error('No conversation data could be extracted from the page');
    }
    
    if (!rawConversation.messages || rawConversation.messages.length === 0) {
      throw new Error('No messages found in the conversation');
    }
    
    console.log('⚙️ [CONTENT] Step 3: Processing conversation data...');
    const processedConversation = ConversationProcessor.processConversation(rawConversation);
    console.log('⚙️ [CONTENT] Conversation processed:', {
      platform: processedConversation?.platform,
      title: processedConversation?.title,
      processedMessages: processedConversation?.messages?.length,
      hasId: !!processedConversation?.id
    });
    
    console.log('💾 [CONTENT] Step 4: Caching processed conversation...');
    await ConversationCache.addToCache(processedConversation);
    console.log('💾 [CONTENT] Conversation cached successfully');
    
    console.log('✅ [CONTENT] Extraction pipeline completed successfully');
    return processedConversation;
  } catch (error) {
    console.error('❌ [CONTENT] Extraction pipeline failed:', error);
    console.error('❌ [CONTENT] Error details:', {
      message: error.message,
      stack: error.stack,
      url: window.location.href,
      platform: document.title
    });
    throw new Error(`Failed to extract conversation: ${error.message}`);
  }
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📨 [CONTENT] Received message:', request);
  console.log('📍 [CONTENT] Current URL:', window.location.href);
  console.log('📍 [CONTENT] Page title:', document.title);
  
  if (request.action === 'ping') {
    console.log('🏓 [CONTENT] Ping received, responding with pong');
    sendResponse({ status: 'pong' });
  } else if (request.action === 'getSelection') {
    console.log('📝 [CONTENT] Getting selection...');
    console.log('📝 [CONTENT] Selected text:', selectedText);
    sendResponse({ selection: selectedText });
  } else if (request.action === 'getPageMetadata') {
    console.log('📊 [CONTENT] Getting page metadata...');
    const metadata = extractPageMetadata();
    console.log('📊 [CONTENT] Extracted metadata:', metadata);
    sendResponse({
      selection: selectedText,
      metadata: metadata
    });
  } else if (request.action === 'detectPlatform') {
    console.log('🧠 [CONTENT] Detecting platform...');
    console.log('🧠 [CONTENT] URL analysis:', {
      hostname: window.location.hostname,
      pathname: window.location.pathname,
      search: window.location.search
    });
    
    try {
      const platformInfo = ConversationExtractor.getPlatformInfo();
      console.log('🧠 [CONTENT] Platform info result:', platformInfo);
      sendResponse(platformInfo);
    } catch (error) {
      console.error('❌ [CONTENT] Error detecting platform:', error);
      sendResponse({ 
        platform: null, 
        isConversation: false, 
        error: error.message 
      });
    }
  } else if (request.action === 'extractConversation') {
    console.log('🚀 [CONTENT] Conversation extraction triggered');
    console.log('🔍 [CONTENT] Starting extraction process...');
    
    extractAndProcessConversation()
      .then(data => {
        console.log('✅ [CONTENT] Extraction successful');
        console.log('📊 [CONTENT] Extracted data summary:', {
          platform: data?.platform,
          title: data?.title,
          messageCount: data?.messages?.length,
          timestamp: data?.timestamp
        });
        sendResponse({ success: true, data });
      })
      .catch(error => {
        console.error('❌ [CONTENT] Error extracting conversation:', error);
        console.error('❌ [CONTENT] Error stack:', error.stack);
        sendResponse({ 
          success: false, 
          error: error.message || 'Failed to extract conversation' 
        });
      });
  } else {
    console.log('❓ [CONTENT] Unknown action:', request.action);
    sendResponse({ error: 'Unknown action' });
  }
  return true; // Keep channel open for async response
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
  
  const repoLink = document.querySelector('[itemprop="name"] a');
  if (repoLink) {
    metadata.repository = repoLink.textContent.trim();
  }
  
  const langElement = document.querySelector('[itemprop="programmingLanguage"]');
  if (langElement) {
    metadata.language = langElement.textContent.trim();
  }
  
  const starsElement = document.querySelector('[aria-label*="star"]');
  if (starsElement) {
    metadata.stars = starsElement.textContent.trim();
  }
  
  const readme = document.querySelector('.markdown-body');
  if (readme) {
    metadata.hasReadme = true;
    metadata.readmePreview = readme.textContent.substring(0, 500);
  }
  
  return metadata;
}