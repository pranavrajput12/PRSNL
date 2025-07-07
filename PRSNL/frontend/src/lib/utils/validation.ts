// Validation utilities for PRSNL

/**
 * Validates the format of an email address.
 * @param email - The email string to validate.
 * @returns True if the email format is valid, false otherwise.
 */
export function validateEmail(email: string | null | undefined): boolean {
  if (!email) return false;
  const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(String(email).toLowerCase());
}

/**
 * Validates the format of a tag (e.g., no spaces, special chars except hyphen).
 * @param tag - The tag string to validate.
 * @returns True if the tag format is valid, false otherwise.
 */
export function validateTag(tag: string | null | undefined): boolean {
  if (!tag) return false;
  const re = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  return re.test(String(tag).toLowerCase());
}

/**
 * Sanitizes user input to prevent basic XSS attacks.
 * @param input - The input to sanitize.
 * @returns The sanitized string.
 */
export function sanitizeInput<T>(input: T): T | string {
  if (typeof input !== 'string') return input;
  return input.replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/**
 * Validates URL format
 * @param url - The URL to validate
 * @returns True if valid URL, false otherwise
 */
export function validateUrl(url: string | null | undefined): boolean {
  if (!url) return false;
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validates that a string is within length bounds
 * @param str - The string to validate
 * @param minLength - Minimum length (inclusive)
 * @param maxLength - Maximum length (inclusive)
 * @returns True if within bounds, false otherwise
 */
export function validateLength(
  str: string | null | undefined,
  minLength: number = 0,
  maxLength: number = Infinity
): boolean {
  if (!str) return minLength === 0;
  return str.length >= minLength && str.length <= maxLength;
}