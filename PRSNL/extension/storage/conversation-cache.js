// Local conversation caching

/**
 * Service for locally caching extracted conversations
 */
class ConversationCache {
  /**
   * Storage key for the cache
   * @private
   */
  static _STORAGE_KEY = 'prsnl_conversation_cache';
  
  /**
   * Maximum number of conversations to keep in cache
   * @private
   */
  static _MAX_CACHE_SIZE = 20;
  
  /**
   * Add a conversation to the local cache
   * @param {Object} conversation Conversation object to cache
   * @returns {Promise<void>}
   */
  static async addToCache(conversation) {
    try {
      if (!conversation || !conversation.id) {
        throw new Error('Invalid conversation object');
      }
      
      const cache = await this._getCache();
      
      // Add conversation with timestamp
      cache[conversation.id] = {
        data: conversation,
        timestamp: new Date().toISOString()
      };
      
      // Remove oldest items if cache is too large
      const ids = Object.keys(cache);
      if (ids.length > this._MAX_CACHE_SIZE) {
        const sortedIds = ids.sort((a, b) => {
          return new Date(cache[a].timestamp) - new Date(cache[b].timestamp);
        });
        
        // Remove oldest items
        const itemsToRemove = sortedIds.slice(0, ids.length - this._MAX_CACHE_SIZE);
        itemsToRemove.forEach(id => delete cache[id]);
      }
      
      await this._saveCache(cache);
    } catch (error) {
      console.error('Error adding conversation to cache:', error);
    }
  }
  
  /**
   * Get a conversation from the cache by ID
   * @param {string} id Conversation ID
   * @returns {Promise<Object|null>} Cached conversation or null if not found
   */
  static async getFromCache(id) {
    try {
      const cache = await this._getCache();
      const item = cache[id];
      return item ? item.data : null;
    } catch (error) {
      console.error('Error getting conversation from cache:', error);
      return null;
    }
  }
  
  /**
   * Remove a conversation from the cache
   * @param {string} id Conversation ID to remove
   * @returns {Promise<void>}
   */
  static async removeFromCache(id) {
    try {
      const cache = await this._getCache();
      if (cache[id]) {
        delete cache[id];
        await this._saveCache(cache);
      }
    } catch (error) {
      console.error('Error removing conversation from cache:', error);
    }
  }
  
  /**
   * Get all conversations from the cache
   * @returns {Promise<Array<Object>>} Array of cached conversations
   */
  static async getAllConversations() {
    try {
      const cache = await this._getCache();
      return Object.values(cache).map(item => item.data);
    } catch (error) {
      console.error('Error getting all conversations from cache:', error);
      return [];
    }
  }
  
  /**
   * Clear all items from the cache
   * @returns {Promise<void>}
   */
  static async clearCache() {
    try {
      await this._saveCache({});
    } catch (error) {
      console.error('Error clearing cache:', error);
    }
  }
  
  /**
   * Get the current cache object
   * @returns {Promise<Object>} Cache object
   * @private
   */
  static async _getCache() {
    return new Promise((resolve) => {
      chrome.storage.local.get([this._STORAGE_KEY], (result) => {
        resolve(result[this._STORAGE_KEY] || {});
      });
    });
  }
  
  /**
   * Save the cache object to storage
   * @param {Object} cache Cache object to save
   * @returns {Promise<void>}
   * @private
   */
  static async _saveCache(cache) {
    return new Promise((resolve) => {
      const data = {};
      data[this._STORAGE_KEY] = cache;
      chrome.storage.local.set(data, resolve);
    });
  }
}

export default ConversationCache;
