// Search utilities for PRSNL

/**
 * Escapes HTML entities in a string to prevent XSS attacks.
 * @param {string} str - The string to escape.
 * @returns {string} The escaped string.
 */
function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

/**
 * Highlights search terms in text by wrapping them in <mark> tags.
 * Prevents XSS by escaping the input text.
 * @param {string} text - The original text.
 * @param {string} query - The search query to highlight.
 * @returns {string} The text with search terms highlighted.
 */
export function highlightText(text, query) {
  if (!text || !query) return text;
  const escapedText = escapeHtml(text);
  const regex = new RegExp(`(${query})`, 'gi');
  return escapedText.replace(regex, '<mark>$1</mark>');
}

/**
 * Filters a list of items by checking if they contain all specified tags.
 * @param {Array<Object>} items - The list of items to filter.
 * @param {Array<string>} tags - The tags to filter by.
 * @returns {Array<Object>} The filtered list of items.
 */
export function filterByTags(items, tags) {
  if (!items || !tags || tags.length === 0) return items;
  return items.filter(item => tags.every(tag => item.tags && item.tags.includes(tag)));
}

/**
 * Sorts search results by relevance based on the query.
 * Items with query in title are more relevant, then content.
 * @param {Array<Object>} results - The search results to sort.
 * @param {string} query - The search query.
 * @returns {Array<Object>} The sorted list of search results.
 */
export function sortByRelevance(results, query) {
  if (!results || !query) return results;
  const lowerQuery = query.toLowerCase();
  return [...results].sort((a, b) => {
    const aRelevance = (a.title && a.title.toLowerCase().includes(lowerQuery) ? 2 : 0) +
                       (a.content && a.content.toLowerCase().includes(lowerQuery) ? 1 : 0);
    const bRelevance = (b.title && b.title.toLowerCase().includes(lowerQuery) ? 2 : 0) +
                       (b.content && b.content.toLowerCase().includes(lowerQuery) ? 1 : 0);
    return bRelevance - aRelevance;
  });
}
