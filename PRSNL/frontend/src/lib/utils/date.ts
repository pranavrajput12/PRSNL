// Date formatting utilities for PRSNL

/**
 * Formats a date for display (e.g., "Mar 15, 2024").
 * @param date - The date to format.
 * @returns The formatted date string.
 */
export function formatDate(date: Date | string | null | undefined): string {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * Gets the relative time string (e.g., "2 hours ago", "3 days ago").
 * @param date - The date to compare.
 * @returns The relative time string.
 */
export function getRelativeTime(date: Date | string | null | undefined): string {
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
 * @param date - The date to check.
 * @returns True if the date is today, false otherwise.
 */
export function isToday(date: Date | string | null | undefined): boolean {
  if (!date) return false;
  const d = new Date(date);
  const today = new Date();
  return (
    d.getDate() === today.getDate() &&
    d.getMonth() === today.getMonth() &&
    d.getFullYear() === today.getFullYear()
  );
}

/**
 * Checks if a given date is within the current week.
 * @param date - The date to check.
 * @returns True if the date is in the current week, false otherwise.
 */
export function isThisWeek(date: Date | string | null | undefined): boolean {
  if (!date) return false;
  const d = new Date(date);
  const today = new Date();
  const dayOfWeek = today.getDay();
  const firstDayOfWeek = new Date(today);
  firstDayOfWeek.setDate(today.getDate() - dayOfWeek);
  const lastDayOfWeek = new Date(today);
  lastDayOfWeek.setDate(today.getDate() - dayOfWeek + 6);
  return d >= firstDayOfWeek && d <= lastDayOfWeek;
}

/**
 * Checks if a given date is within the current month.
 * @param date - The date to check.
 * @returns True if the date is in the current month, false otherwise.
 */
export function isThisMonth(date: Date | string | null | undefined): boolean {
  if (!date) return false;
  const d = new Date(date);
  const today = new Date();
  return d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear();
}
