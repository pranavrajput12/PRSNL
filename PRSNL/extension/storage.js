// Extension Storage Service using webext-storage
// This provides type-safe, schema-validated storage

import { StorageItem, StorageItemMap } from 'webext-storage';

// Schema definitions for type safety
const ExtensionSettings = new StorageItem('extension_settings', {
  defaultValue: {
    enableSummarization: true,
    defaultContentType: 'auto',
    autoDetectContentType: true,
    captureSelectedText: true
  }
});

const CaptureHistory = new StorageItem('capture_history', {
  defaultValue: []
});

const TagsCache = new StorageItem('tags_cache', {
  defaultValue: []
});

const LastCaptureData = new StorageItem('last_capture', {
  defaultValue: null
});

// Capture stats for analytics
const CaptureStats = new StorageItem('capture_stats', {
  defaultValue: {
    totalCaptures: 0,
    successfulCaptures: 0,
    failedCaptures: 0,
    lastCaptureDate: null,
    mostUsedContentTypes: {}
  }
});

// Export storage items for use across extension
export {
  ExtensionSettings,
  CaptureHistory,
  TagsCache,
  LastCaptureData,
  CaptureStats
};

// Helper functions for common operations
export class ExtensionStorage {
  
  // Settings management
  static async getSettings() {
    return await ExtensionSettings.get();
  }
  
  static async updateSettings(newSettings) {
    const current = await ExtensionSettings.get();
    return await ExtensionSettings.set({ ...current, ...newSettings });
  }
  
  // Capture history management
  static async addToHistory(captureData) {
    const history = await CaptureHistory.get();
    const newEntry = {
      ...captureData,
      timestamp: Date.now(),
      id: crypto.randomUUID()
    };
    
    // Keep only last 100 captures
    const updatedHistory = [newEntry, ...history].slice(0, 100);
    await CaptureHistory.set(updatedHistory);
    
    return newEntry;
  }
  
  static async getHistory(limit = 10) {
    const history = await CaptureHistory.get();
    return history.slice(0, limit);
  }
  
  static async clearHistory() {
    await CaptureHistory.set([]);
  }
  
  // Tags management
  static async addTag(tag) {
    const tags = await TagsCache.get();
    if (!tags.includes(tag)) {
      const updatedTags = [tag, ...tags].slice(0, 50); // Keep 50 most recent
      await TagsCache.set(updatedTags);
    }
  }
  
  static async getTags() {
    return await TagsCache.get();
  }
  
  static async getFrequentTags(limit = 10) {
    const tags = await TagsCache.get();
    return tags.slice(0, limit);
  }
  
  // Last capture data
  static async saveLastCapture(captureData) {
    await LastCaptureData.set({
      ...captureData,
      timestamp: Date.now()
    });
  }
  
  static async getLastCapture() {
    return await LastCaptureData.get();
  }
  
  // Statistics
  static async updateStats(success = true, contentType = 'auto') {
    const stats = await CaptureStats.get();
    
    const updatedStats = {
      ...stats,
      totalCaptures: stats.totalCaptures + 1,
      successfulCaptures: success ? stats.successfulCaptures + 1 : stats.successfulCaptures,
      failedCaptures: success ? stats.failedCaptures : stats.failedCaptures + 1,
      lastCaptureDate: Date.now(),
      mostUsedContentTypes: {
        ...stats.mostUsedContentTypes,
        [contentType]: (stats.mostUsedContentTypes[contentType] || 0) + 1
      }
    };
    
    await CaptureStats.set(updatedStats);
    return updatedStats;
  }
  
  static async getStats() {
    return await CaptureStats.get();
  }
  
  // Development utilities
  static async exportData() {
    return {
      settings: await ExtensionSettings.get(),
      history: await CaptureHistory.get(),
      tags: await TagsCache.get(),
      lastCapture: await LastCaptureData.get(),
      stats: await CaptureStats.get()
    };
  }
  
  static async importData(data) {
    if (data.settings) await ExtensionSettings.set(data.settings);
    if (data.history) await CaptureHistory.set(data.history);
    if (data.tags) await TagsCache.set(data.tags);
    if (data.lastCapture) await LastCaptureData.set(data.lastCapture);
    if (data.stats) await CaptureStats.set(data.stats);
  }
  
  static async clearAllData() {
    await ExtensionSettings.set(ExtensionSettings.defaultValue);
    await CaptureHistory.set([]);
    await TagsCache.set([]);
    await LastCaptureData.set(null);
    await CaptureStats.set(CaptureStats.defaultValue);
  }
}