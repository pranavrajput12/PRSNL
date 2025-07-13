/**
 * Base class for platform adapters.
 * 
 * Platform adapters are responsible for detecting if the current page belongs to a specific platform,
 * extracting conversation data from the page, and checking if the page contains a conversation.
 * 
 * This class provides a basic implementation of these methods, which must be overridden by subclasses.
 */
class PlatformAdapter {
  /**
   * Detect if the current page belongs to this platform
   * @returns {boolean} True if the current page belongs to this platform
   */
  detect() { throw new Error('Must implement detect()') }

  /**
   * Extract the conversation from the current page
   * @returns {Promise<Object>} Conversation data in PRSNL schema format
   */
  async extractConversation() { throw new Error('Must implement extractConversation()') }

  /**
   * Check if the current page contains a conversation
   * @returns {boolean} True if the current page contains a conversation
   */
  isConversationPage() { throw new Error('Must implement isConversationPage()') }
  
  /**
   * Get the title of the conversation
   * @returns {string} Conversation title or null if not found
   */
  getConversationTitle() { throw new Error('Must implement getConversationTitle()') }
  
  /**
   * Get the URL of the conversation
   * @returns {string} Conversation URL
   */
  getConversationUrl() { 
    return window.location.href;
  }
}

// Export the class for use in other modules
export default PlatformAdapter;
