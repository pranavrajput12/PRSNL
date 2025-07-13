/**
 * Convert text to URL-friendly slug
 */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove special characters
    .replace(/[\s_-]+/g, '-') // Replace spaces and underscores with hyphens
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
}

/**
 * Generate unique slug with fallback
 */
export function generateSlug(title: string, id?: string | number): string {
  const baseSlug = slugify(title);

  if (!baseSlug || baseSlug.length < 3) {
    return id ? `item-${id}` : `item-${Date.now()}`;
  }

  return baseSlug;
}

/**
 * Create slug from title with date prefix for uniqueness
 */
export function createDateSlug(title: string, date?: Date): string {
  const datePrefix = (date || new Date()).toISOString().split('T')[0];
  const titleSlug = slugify(title);

  if (!titleSlug || titleSlug.length < 3) {
    return `${datePrefix}-thought`;
  }

  return `${datePrefix}-${titleSlug}`;
}
