// Content sanitization utilities

import DOMPurify from 'dompurify';

/**
 * Utility class for sanitizing HTML content
 */
class Sanitizer {
  /**
   * Default configuration for DOMPurify
   * @type {Object}
   * @private
   */
  static _defaultConfig = {
    ALLOWED_TAGS: [
      'a', 'b', 'br', 'code', 'div', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'i', 'li', 'ol', 'p', 'pre', 'span', 'strong', 'table', 'tbody', 'td',
      'th', 'thead', 'tr', 'ul', 'img'
    ],
    ALLOWED_ATTR: [
      'href', 'target', 'rel', 'class', 'id', 'style', 'src', 'alt', 'width', 'height'
    ],
    RETURN_DOM: false,
    RETURN_DOM_FRAGMENT: false,
    RETURN_DOM_IMPORT: false
  };

  /**
   * Sanitize HTML string to prevent XSS
   * @param {string} html HTML string to sanitize
   * @param {Object} [options] Configuration options for DOMPurify
   * @returns {string} Sanitized HTML
   */
  static sanitize(html, options = {}) {
    if (!html) return '';
    
    const config = {
      ...this._defaultConfig,
      ...options
    };
    
    return DOMPurify.sanitize(html, config);
  }
  
  /**
   * Sanitize HTML specifically for code blocks
   * @param {string} html HTML string to sanitize
   * @returns {string} Sanitized HTML with code formatting preserved
   */
  static sanitizeCode(html) {
    if (!html) return '';
    
    const config = {
      ...this._defaultConfig,
      ALLOWED_TAGS: [
        ...this._defaultConfig.ALLOWED_TAGS,
        'code', 'pre'
      ],
      ALLOWED_ATTR: [
        ...this._defaultConfig.ALLOWED_ATTR,
        'data-language', 'language'
      ]
    };
    
    return DOMPurify.sanitize(html, config);
  }
  
  /**
   * Remove all HTML tags and return text only
   * @param {string} html HTML string to clean
   * @returns {string} Plain text without any HTML
   */
  static stripHtml(html) {
    if (!html) return '';
    
    // First sanitize to remove potentially harmful elements
    const sanitized = this.sanitize(html);
    
    // Create a temporary DOM element
    const temp = document.createElement('div');
    temp.innerHTML = sanitized;
    
    // Get text content and normalize whitespace
    return temp.textContent
      .replace(/\s+/g, ' ')
      .trim();
  }
}

export default Sanitizer;
