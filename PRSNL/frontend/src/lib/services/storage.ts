// Simple localStorage wrapper for PRSNL

const STORAGE_PREFIX = 'prsnl-' as const;

/**
 * Save an item to localStorage
 * @param key - The storage key
 * @param value - The value to store
 * @returns True if successful, false otherwise
 */
export function saveItem<T>(key: string, value: T): boolean {
  try {
    localStorage.setItem(`${STORAGE_PREFIX}${key}`, JSON.stringify(value));
    return true;
  } catch (error) {
    console.error('Failed to save to localStorage:', error);
    return false;
  }
}

/**
 * Get an item from localStorage
 * @param key - The storage key
 * @param defaultValue - Default value if key doesn't exist
 * @returns The stored value or default value
 */
export function getItem<T>(key: string, defaultValue: T | null = null): T | null {
  try {
    const item = localStorage.getItem(`${STORAGE_PREFIX}${key}`);
    return item ? JSON.parse(item) as T : defaultValue;
  } catch (error) {
    console.error('Failed to get from localStorage:', error);
    return defaultValue;
  }
}

/**
 * Remove an item from localStorage
 * @param key - The storage key to remove
 * @returns True if successful, false otherwise
 */
export function removeItem(key: string): boolean {
  try {
    localStorage.removeItem(`${STORAGE_PREFIX}${key}`);
    return true;
  } catch (error) {
    console.error('Failed to remove from localStorage:', error);
    return false;
  }
}

/**
 * Clear all PRSNL data from localStorage
 * @returns True if successful, false otherwise
 */
export function clearAll(): boolean {
  try {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith(STORAGE_PREFIX)) {
        localStorage.removeItem(key);
      }
    });
    return true;
  } catch (error) {
    console.error('Failed to clear localStorage:', error);
    return false;
  }
}

/**
 * Check if localStorage is available
 * @returns True if localStorage is available, false otherwise
 */
export function isAvailable(): boolean {
  try {
    const test = '__prsnl_test__';
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch {
    return false;
  }
}

/**
 * Storage keys enum for type safety
 */
export enum StorageKeys {
  RECENT_SEARCHES = 'recent-searches',
  USER_PREFERENCES = 'user-preferences',
  MEDIA_SETTINGS = 'media-settings',
  FILTER_PREFERENCES = 'filter-preferences',
  SEARCH_MODE = 'search-mode'
}

/**
 * Get all PRSNL keys from localStorage
 * @returns Array of storage keys (without prefix)
 */
export function getAllKeys(): string[] {
  try {
    return Object.keys(localStorage)
      .filter(key => key.startsWith(STORAGE_PREFIX))
      .map(key => key.substring(STORAGE_PREFIX.length));
  } catch (error) {
    console.error('Failed to get localStorage keys:', error);
    return [];
  }
}