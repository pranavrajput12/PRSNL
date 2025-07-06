// App constants for PRSNL

/**
 * The name of the application.
 * @type {string}
 */
export const APP_NAME = 'PRSNL';

/**
 * The maximum number of tags allowed per item.
 * @type {number}
 */
export const MAX_TAGS_PER_ITEM = 10;

/**
 * The maximum length for an item's title.
 * @type {number}
 */
export const MAX_TITLE_LENGTH = 200;

/**
 * Supported file types for capture.
 * @type {string[]}
 */
export const SUPPORTED_FILE_TYPES = ['.txt', '.md', '.pdf', '.docx'];

/**
 * Keyboard shortcuts used throughout the application.
 * @type {Object}
 * @property {string} CAPTURE - Shortcut for capturing a new item.
 * @property {string} SEARCH - Shortcut for initiating a search.
 * @property {string} TIMELINE - Shortcut for navigating to the timeline.
 * @property {string} HOME - Shortcut for navigating to the home page.
 */
export const KEYBOARD_SHORTCUTS = {
  CAPTURE: 'Cmd+N',
  SEARCH: 'Cmd+K',
  TIMELINE: 'Cmd+T',
  HOME: 'Cmd+H'
};

/**
 * Options for filtering data.
 * @type {Object}
 * @property {string[]} DATE - Date filter options.
 * @property {string[]} TYPE - Item type filter options.
 * @property {string[]} SORT - Sorting options.
 */
export const FILTER_OPTIONS = {
  DATE: ['today', 'week', 'month', 'year'],
  TYPE: ['url', 'text', 'file'],
  SORT: ['recent', 'relevant', 'alphabetical']
};
