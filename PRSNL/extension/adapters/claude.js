import PlatformAdapter from './base.js';

/**
 * Adapter for Claude.ai platform
 */
class ClaudeAdapter extends PlatformAdapter {
  /**
   * Detect if the current page is Claude
   * @returns {boolean} True if the current page is Claude
   */
  detect() {
    return window.location.hostname.includes('claude.ai');
  }
  
  /**
   * Check if the current page contains a conversation
   * @returns {boolean} True if the current page contains a conversation
   */
  isConversationPage() {
    return window.location.pathname.includes('/chat/');
  }
  
  /**
   * Extract the conversation from the Claude page
   * @returns {Promise<Object>} Conversation data in PRSNL schema format
   */
  async extractConversation() {
    if (!this.isConversationPage()) {
      throw new Error('Not a Claude conversation page');
    }

    try {
      // Claude conversation containers have these distinctive classes
      const humanMessages = document.querySelectorAll('.human-message-container');
      const assistantMessages = document.querySelectorAll('.assistant-message-container');
      
      // Combine and sort by position in DOM
      const allMessageElements = [...humanMessages, ...assistantMessages].sort((a, b) => {
        // Compare positions in the DOM to ensure messages are in the correct order
        return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
      });
      
      const messages = [];
      
      // Extract messages
      allMessageElements.forEach((element, index) => {
        // Determine role based on class name
        const isHuman = element.classList.contains('human-message-container');
        const role = isHuman ? 'user' : 'assistant';
        
        // Extract content - Claude has different content containers for human vs assistant
        const contentSelector = isHuman ? '.message-content' : '.message-content';
        const contentElement = element.querySelector(contentSelector);
        
        if (!contentElement) return;
        
        messages.push({
          id: `msg-${index}`,
          role: role,
          content: {
            text: contentElement.textContent,
            html: contentElement.innerHTML
          },
          timestamp: new Date().toISOString()
        });
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
  
  /**
   * Get the title of the conversation
   * @returns {string} Conversation title
   */
  getConversationTitle() {
    // Try to find the conversation title in the sidebar
    const titleElement = document.querySelector('.conversation-title');
    if (titleElement) {
      return titleElement.textContent.trim();
    }
    
    // Fallback to document title or generic name
    return document.title || 'Claude Conversation';
  }
  
  /**
   * Generate a random ID for the conversation
   * @private
   * @returns {string} Random ID
   */
  _generateId() {
    return 'claude-' + Math.random().toString(36).substring(2, 15);
  }
}

export default ClaudeAdapter;
