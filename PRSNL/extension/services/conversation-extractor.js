// Main extraction service

import AdapterFactory from '../adapters/factory.js';
import Sanitizer from '../utils/sanitizer.js';

/**
 * Service for extracting conversations from AI chat platforms
 */
class ConversationExtractor {
  /**
   * Extract conversation data from the current page
   * @returns {Promise<Object>} Extracted conversation data
   * @throws {Error} If extraction fails or no suitable adapter is found
   */
  static async extractConversation() {
    try {
      // Use adapter factory to get the right adapter for the current platform
      const conversation = await AdapterFactory.extractConversation();
      
      if (!conversation) {
        throw new Error('Failed to extract conversation data');
      }
      
      // Process and sanitize the messages
      const sanitizedMessages = conversation.messages.map(message => {
        return {
          ...message,
          content: {
            text: Sanitizer.stripHtml(message.content.text),
            html: Sanitizer.sanitize(message.content.html)
          }
        };
      });
      
      return {
        ...conversation,
        messages: sanitizedMessages
      };
    } catch (error) {
      console.error('Error in ConversationExtractor:', error);
      throw new Error(`Conversation extraction failed: ${error.message}`);
    }
  }
  
  /**
   * Check if the current page has an extractable conversation
   * @returns {boolean} True if a conversation can be extracted
   */
  static canExtractConversation() {
    return AdapterFactory.hasConversation();
  }
  
  /**
   * Get information about the detected platform
   * @returns {Object} Platform information including name and conversation availability
   */
  static getPlatformInfo() {
    return AdapterFactory.getPlatformInfo();
  }
}

export default ConversationExtractor;
