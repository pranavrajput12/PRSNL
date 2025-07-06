// URL utilities for PRSNL

/**
 * Checks if a given string is a valid URL.
 * @param {string} string - The string to validate.
 * @returns {boolean} True if the string is a valid URL, false otherwise.
 */
export function isValidUrl(string) {
  try {
    new URL(string);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Extracts the domain from a given URL.
 * @param {string} url - The URL to extract the domain from.
 * @returns {string | null} The domain name, or null if the URL is invalid.
 */
export function getDomain(url) {
  try {
    const parsedUrl = new URL(url);
    return parsedUrl.hostname;
  } catch (e) {
    return null;
  }
}

/**
 * Generates a favicon URL for a given domain.
 * @param {string} domain - The domain to get the favicon for.
 * @returns {string | null} The favicon URL, or null if no domain is provided.
 */
export function getFavicon(domain) {
  if (!domain) return null;
  return `https://www.google.com/s2/favicons?domain=${domain}`;
}

/**
 * Cleans and normalizes a URL by removing hash and query parameters.
 * @param {string} url - The URL to clean.
 * @returns {string} The cleaned URL.
 */
export function cleanUrl(url) {
  try {
    const parsedUrl = new URL(url);
    parsedUrl.hash = ''; // Remove hash
    parsedUrl.search = ''; // Remove query parameters
    return parsedUrl.toString();
  } catch (e) {
    return url; // Return original if invalid
  }
}
