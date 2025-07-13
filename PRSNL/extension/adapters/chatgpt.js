import PlatformAdapter from './base.js';

/**
 * Adapter for ChatGPT platform
 */
class ChatGPTAdapter extends PlatformAdapter {
  /**
   * Detect if the current page is ChatGPT
   * @returns {boolean} True if the current page is ChatGPT
   */
  detect() { 
    return window.location.hostname.includes('chat.openai.com');
  }
  
  /**
   * Check if the current page contains a conversation
   * @returns {boolean} True if the current page contains a conversation
   */
  isConversationPage() {
    return window.location.pathname.includes('/c/');
  }
  
  /**
   * Extract the conversation from the ChatGPT page
   * @returns {Promise<Object>} Conversation data in PRSNL schema format
   */
  async extractConversation() {
    if (!this.isConversationPage()) {
      throw new Error('Not a ChatGPT conversation page');
    }

    try {
      // Get all message elements
      const messageElements = document.querySelectorAll('[data-message-author-role]');
      const messages = [];
      
      // Extract messages
      messageElements.forEach((element, index) => {
        const role = element.getAttribute('data-message-author-role');
        const contentElement = element.querySelector('.markdown');
        
        if (!contentElement) return;
        
        // Deep clone to safely manipulate the content
        const contentClone = contentElement.cloneNode(true);
        
        // Process code blocks to preserve formatting
        const codeBlocks = contentClone.querySelectorAll('pre');
        codeBlocks.forEach(codeBlock => {
          const language = codeBlock.querySelector('code')?.className
            .replace('language-', '')
            .trim() || 'plaintext';
          
          codeBlock.dataset.language = language;
        });
        
        messages.push({
          id: `msg-${index}`,
          role: role === 'user' ? 'user' : 'assistant',
          content: {
            text: contentElement.textContent,
            html: contentElement.innerHTML
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
  
  /**
   * Get the title of the conversation
   * @returns {string} Conversation title
   */
  getConversationTitle() {
    // Try to find the conversation title in the navigation sidebar
    const titleElement = document.querySelector('nav .truncate');
    if (titleElement) {
      return titleElement.textContent.trim();
    }
    
    // Fallback to document title or generic name
    return document.title.replace(' - ChatGPT', '') || 'ChatGPT Conversation';
  }
  
  /**
   * Generate a random ID for the conversation
   * @private
   * @returns {string} Random ID
   */
  _generateId() {
    return 'chatgpt-' + Math.random().toString(36).substring(2, 15);
  }
}

export default ChatGPTAdapter;
