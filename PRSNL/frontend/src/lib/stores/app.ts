/**
 * PRSNL App Stores
 * Manages application state using Svelte stores
 */

import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';

// Types
export interface UserPreferences {
  darkMode: boolean;
  sidebarCollapsed: boolean;
  defaultView: 'timeline' | 'grid' | 'list';
  tagsInSidebar: boolean;
  keyboardShortcutsEnabled: boolean;
}

export interface RecentSearch {
  query: string;
  timestamp: number;
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  timeout?: number;
}

// Default preferences
const DEFAULT_PREFERENCES: UserPreferences = {
  darkMode: true,
  sidebarCollapsed: false,
  defaultView: 'timeline',
  tagsInSidebar: true,
  keyboardShortcutsEnabled: true,
};

// Load preferences from localStorage if available
function loadPreferences(): UserPreferences {
  if (browser) {
    const saved = localStorage.getItem('prsnl-preferences');
    if (saved) {
      try {
        return { ...DEFAULT_PREFERENCES, ...JSON.parse(saved) };
      } catch (e) {
        console.error('Failed to parse preferences:', e);
      }
    }
  }
  return DEFAULT_PREFERENCES;
}

// Load recent searches from localStorage if available
function loadRecentSearches(): RecentSearch[] {
  if (browser) {
    const saved = localStorage.getItem('prsnl-recent-searches');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse recent searches:', e);
      }
    }
  }
  return [];
}

// Create stores
export const preferences = writable<UserPreferences>(loadPreferences());
export const recentSearches = writable<RecentSearch[]>(loadRecentSearches());
export const notifications = writable<Notification[]>([]);

// Save preferences to localStorage when they change
if (browser) {
  preferences.subscribe(value => {
    localStorage.setItem('prsnl-preferences', JSON.stringify(value));
  });
  
  recentSearches.subscribe(value => {
    localStorage.setItem('prsnl-recent-searches', JSON.stringify(value));
  });
}

// Derived store for dark mode
export const darkMode = derived(
  preferences,
  $preferences => $preferences.darkMode
);

// Helper functions for preferences
export function toggleDarkMode() {
  preferences.update(prefs => ({ ...prefs, darkMode: !prefs.darkMode }));
}

export function toggleSidebar() {
  preferences.update(prefs => ({ ...prefs, sidebarCollapsed: !prefs.sidebarCollapsed }));
}

export function setDefaultView(view: UserPreferences['defaultView']) {
  preferences.update(prefs => ({ ...prefs, defaultView: view }));
}

// Helper functions for recent searches
export function addRecentSearch(query: string) {
  recentSearches.update(searches => {
    // Remove duplicates
    const filtered = searches.filter(s => s.query !== query);
    
    // Add new search at the beginning
    const newSearches = [
      { query, timestamp: Date.now() },
      ...filtered
    ];
    
    // Keep only the 10 most recent searches
    return newSearches.slice(0, 10);
  });
}

export function clearRecentSearches() {
  recentSearches.set([]);
}

// Helper functions for notifications
export function addNotification(notification: Omit<Notification, 'id'>) {
  const id = Math.random().toString(36).substring(2, 9);
  const newNotification = { ...notification, id };
  
  notifications.update(items => [...items, newNotification]);
  
  // Auto-remove notification after timeout (default: 5000ms)
  if (notification.timeout !== 0) {
    setTimeout(() => {
      removeNotification(id);
    }, notification.timeout || 5000);
  }
  
  return id;
}

export function removeNotification(id: string) {
  notifications.update(items => items.filter(item => item.id !== id));
}

export function clearNotifications() {
  notifications.set([]);
}
