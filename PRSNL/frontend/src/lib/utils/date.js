// Date formatting utilities for PRSNL

/**
 * Formats a date for display (e.g., "Mar 15, 2024").
 * @param {Date | string} date - The date to format.
 * @returns {string} The formatted date string.
 */
export function formatDate(date) {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * Gets the relative time string (e.g., "2 hours ago", "3 days ago").
 * @param {Date | string} date - The date to compare.
 * @returns {string} The relative time string.
 */
export function getRelativeTime(date) {
  if (!date) return '';
  const d = new Date(date);
  const now = new Date();
  const diffSeconds = Math.round((now.getTime() - d.getTime()) / 1000);

  if (diffSeconds < 60) return `${diffSeconds} seconds ago`;
  const diffMinutes = Math.round(diffSeconds / 60);
  if (diffMinutes < 60) return `${diffMinutes} minutes ago`;
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours} hours ago`;
  const diffDays = Math.round(diffHours / 24);
  if (diffDays < 30) return `${diffDays} days ago`;
  const diffMonths = Math.round(diffDays / 30);
  if (diffMonths < 12) return `${diffMonths} months ago`;
  const diffYears = Math.round(diffMonths / 12);
  return `${diffYears} years ago`;
}

/**
 * Checks if a given date is today.
 * @param {Date | string} date - The date to check.
 * @returns {boolean} True if the date is today, false otherwise.
 */
export function isToday(date) {
  if (!date) return false;
  const d = new Date(date);
  const today = new Date();
  return d.getDate() === today.getDate() &&
         d.getMonth() === today.getMonth() &&
         d.getFullYear() === today.getFullYear();
}

/**
 * Checks if a given date is within the current week.
 * @param {Date | string} date - The date to check.
 * @returns {boolean} True if the date is in the current week, false otherwise.
 */
export function isThisWeek(date) {
  if (!date) return false;
  const d = new Date(date);
  const today = new Date(); // Create a new Date object to avoid mutation
  const firstDayOfWeek = new Date(today.setDate(today.getDate() - today.getDay()));
  const lastDayOfWeek = new Date(today.setDate(today.getDate() - today.getDay() + 6));
  return d >= firstDayOfWeek && d <= lastDayOfWeek;
}

/**
 * Checks if a given date is within the current month.
 * @param {Date | string} date - The date to check.
 * @returns {boolean} True if the date is in the current month, false otherwise.
 */
export function isThisMonth(date) {
  if (!date) return false;
  const d = new Date(date);
  const today = new Date();
  return d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear();
}
