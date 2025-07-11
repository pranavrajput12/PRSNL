// Search utilities for PRSNL

import type { SearchResult, Item } from '$lib/types/api';

/**
 * Escapes HTML entities in a string to prevent XSS attacks.
 * @param str - The string to escape.
 * @returns The escaped string.
 */
function escapeHtml(str: string): string {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

/**
 * Highlights search terms in text by wrapping them in <mark> tags.
 * Prevents XSS by escaping the input text.
 * @param text - The original text.
 * @param query - The search query to highlight.
 * @returns The text with search terms highlighted.
 */
export function highlightText(
  text: string | null | undefined,
  query: string | null | undefined
): string {
  if (!text || !query) return text || '';
  const escapedText = escapeHtml(text);
  const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // Escape regex special chars
  const regex = new RegExp(`(${escapedQuery})`, 'gi');
  return escapedText.replace(regex, '<mark>$1</mark>');
}

/**
 * Filters a list of items by checking if they contain all specified tags.
 * @param items - The list of items to filter.
 * @param tags - The tags to filter by.
 * @returns The filtered list of items.
 */
export function filterByTags<T extends { tags?: string[] }>(
  items: T[] | null | undefined,
  tags: string[] | null | undefined
): T[] {
  if (!items || !tags || tags.length === 0) return items || [];
  return items.filter((item) => tags.every((tag) => item.tags && item.tags.includes(tag)));
}

/**
 * Sorts search results by relevance based on the query.
 * Items with query in title are more relevant, then content.
 * @param results - The search results to sort.
 * @param query - The search query.
 * @returns The sorted list of search results.
 */
export function sortByRelevance<T extends { title?: string; content?: string; snippet?: string }>(
  results: T[] | null | undefined,
  query: string | null | undefined
): T[] {
  if (!results || !query) return results || [];
  const lowerQuery = query.toLowerCase();

  return [...results].sort((a, b) => {
    const aRelevance =
      (a.title && a.title.toLowerCase().includes(lowerQuery) ? 2 : 0) +
      ((a.content && a.content.toLowerCase().includes(lowerQuery)) ||
      (a.snippet && a.snippet.toLowerCase().includes(lowerQuery))
        ? 1
        : 0);

    const bRelevance =
      (b.title && b.title.toLowerCase().includes(lowerQuery) ? 2 : 0) +
      ((b.content && b.content.toLowerCase().includes(lowerQuery)) ||
      (b.snippet && b.snippet.toLowerCase().includes(lowerQuery))
        ? 1
        : 0);

    return bRelevance - aRelevance;
  });
}

/**
 * Debounces a function call
 * @param func - The function to debounce
 * @param wait - The delay in milliseconds
 * @returns The debounced function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;

  return function (...args: Parameters<T>) {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
