// App constants for PRSNL

/**
 * The name of the application.
 */
export const APP_NAME = 'PRSNL' as const;

/**
 * The maximum number of tags allowed per item.
 */
export const MAX_TAGS_PER_ITEM = 20 as const;

/**
 * The maximum length for an item's title.
 */
export const MAX_TITLE_LENGTH = 500 as const;

/**
 * The maximum length for an item's summary.
 */
export const MAX_SUMMARY_LENGTH = 5000 as const;

/**
 * The maximum length for item content.
 */
export const MAX_CONTENT_LENGTH = 50000 as const;

/**
 * The maximum length for a single tag.
 */
export const MAX_TAG_LENGTH = 50 as const;

/**
 * The maximum length for search queries.
 */
export const MAX_QUERY_LENGTH = 1000 as const;

/**
 * Supported file types for capture.
 */
export const SUPPORTED_FILE_TYPES = ['.txt', '.md', '.pdf', '.docx'] as const;

/**
 * Keyboard shortcuts used throughout the application.
 */
export const KEYBOARD_SHORTCUTS = {
  CAPTURE: 'Cmd+N',
  SEARCH: 'Cmd+K',
  TIMELINE: 'Cmd+T',
  HOME: 'Cmd+H'
} as const;

/**
 * Options for filtering data.
 */
export const FILTER_OPTIONS = {
  DATE: ['today', 'week', 'month', 'year'] as const,
  TYPE: ['article', 'video', 'note', 'bookmark'] as const,
  SORT: ['recent', 'relevant', 'alphabetical'] as const
} as const;

/**
 * API endpoints
 */
export const API_ENDPOINTS = {
  CAPTURE: '/capture',
  SEARCH: '/search',
  SEARCH_SEMANTIC: '/search/semantic',
  TIMELINE: '/timeline',
  ITEMS: '/items',
  TAGS: '/tags'
} as const;

/**
 * WebSocket message types
 */
export const WS_MESSAGE_TYPES = {
  PROGRESS: 'progress',
  UPDATE: 'update',
  NOTIFICATION: 'notification',
  ERROR: 'error'
} as const;

// Type exports for the constants
export type SupportedFileType = typeof SUPPORTED_FILE_TYPES[number];
export type DateFilter = typeof FILTER_OPTIONS.DATE[number];
export type TypeFilter = typeof FILTER_OPTIONS.TYPE[number];
export type SortOption = typeof FILTER_OPTIONS.SORT[number];
export type WSMessageType = typeof WS_MESSAGE_TYPES[keyof typeof WS_MESSAGE_TYPES];