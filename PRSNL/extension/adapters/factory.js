// Platform detection factory

import ChatGPTAdapter from './chatgpt.js';
import ClaudeAdapter from './claude.js';
import PerplexityAdapter from './perplexity.js';

/**
 * Factory class for creating platform adapters
 */
class AdapterFactory {
  /**
   * Available adapter classes
   * @private
   */
  static _adapters = [
    ChatGPTAdapter,
    ClaudeAdapter,
    PerplexityAdapter
  ];
  
  /**
   * Get the appropriate adapter for the current platform
   * @returns {PlatformAdapter|null} Platform adapter instance or null if no matching adapter
   */
  static getAdapter() {
    for (const AdapterClass of this._adapters) {
      const adapter = new AdapterClass();
      if (adapter.detect()) {
        console.log(`Detected platform: ${AdapterClass.name}`);
        return adapter;
      }
    }
    console.log('No matching platform adapter found');
    return null;
  }
  
  /**
   * Check if the current page has a conversation that can be extracted
   * @returns {boolean} True if a conversation is detected
   */
  static hasConversation() {
    const adapter = this.getAdapter();
    return adapter ? adapter.isConversationPage() : false;
  }
  
  /**
   * Extract the conversation from the current page
   * @returns {Promise<Object>} Extracted conversation data
   * @throws {Error} If no adapter is found or extraction fails
   */
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
  
  /**
   * Get information about the detected platform
   * @returns {Object} Platform information
   */
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

export default AdapterFactory;
