import PlatformAdapter from './base.js';

/**
 * Adapter for Perplexity.ai platform
 */
class PerplexityAdapter extends PlatformAdapter {
  /**
   * Detect if the current page is Perplexity
   * @returns {boolean} True if the current page is Perplexity
   */
  detect() { 
    return window.location.hostname.includes('perplexity.ai');
  }
  
  /**
   * Check if the current page contains a conversation
   * @returns {boolean} True if the current page contains a conversation
   */
  isConversationPage() {
    return window.location.pathname.includes('/search/');
  }
  
  /**
   * Extract the conversation from the Perplexity page
   * @returns {Promise<Object>} Conversation data in PRSNL schema format
   */
  async extractConversation() {
    if (!this.isConversationPage()) {
      throw new Error('Not a Perplexity conversation page');
    }

    try {
      // Perplexity marks user queries with this class
      const queryElements = document.querySelectorAll('.query-container');
      // Answer elements have this class
      const answerElements = document.querySelectorAll('.answer-container');
      
      // Combine and sort by position in the DOM
      const allElements = [...queryElements, ...answerElements].sort((a, b) => {
        // Compare positions in the DOM to ensure messages are in the correct order
        return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
      });
      
      const messages = [];
      
      // Extract messages
      allElements.forEach((element, index) => {
        // Determine role based on class
        const isQuery = element.classList.contains('query-container');
        const role = isQuery ? 'user' : 'assistant';
        
        // Get content elements
        const contentSelector = isQuery ? '.query-text' : '.answer-text';
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
  
  /**
   * Get the title of the conversation
   * @returns {string} Conversation title
   */
  getConversationTitle() {
    // Try to find the first query as title
    const firstQuery = document.querySelector('.query-text');
    if (firstQuery) {
      // Use first few words of query as title
      const query = firstQuery.textContent.trim();
      const shortQuery = query.length > 60 ? query.substring(0, 57) + '...' : query;
      return shortQuery;
    }
    
    // Fallback to document title or generic name
    return document.title || 'Perplexity Search';
  }
  
  /**
   * Generate a random ID for the conversation
   * @private
   * @returns {string} Random ID
   */
  _generateId() {
    return 'perplexity-' + Math.random().toString(36).substring(2, 15);
  }
}

export default PerplexityAdapter;
