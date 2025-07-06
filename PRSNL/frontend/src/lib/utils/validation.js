// Validation utilities for PRSNL

/**
 * Validates the format of an email address.
 * @param {string} email - The email string to validate.
 * @returns {boolean} True if the email format is valid, false otherwise.
 */
export function validateEmail(email) {
  if (!email) return false;
  const re = /^(([^<>()[\\]\\.,;:\s@\"]+(\\.[^<>()[\\]\\.,;:\s@\"]+)*)|(\".+\"))@((\\[[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\])|(([a-zA-Z\\-0-9]+\\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(email).toLowerCase());
}

/**
 * Validates the format of a tag (e.g., no spaces, special chars except hyphen).
 * @param {string} tag - The tag string to validate.
 * @returns {boolean} True if the tag format is valid, false otherwise.
 */
export function validateTag(tag) {
  if (!tag) return false;
  const re = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  return re.test(String(tag).toLowerCase());
}

/**
 * Sanitizes user input to prevent basic XSS attacks.
 * @param {string} input - The input string to sanitize.
 * @returns {string} The sanitized string.
 */
export function sanitizeInput(input) {
  if (typeof input !== 'string') return input;
  return input.replace(/</g, "&lt;").replace(/>/g, "&gt;");
}