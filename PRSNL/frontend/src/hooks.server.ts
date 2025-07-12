import { handleErrorWithSentry } from '@sentry/sveltekit';
import * as Sentry from '@sentry/sveltekit';
import { redirect } from '@sveltejs/kit';
import type { Handle } from '@sveltejs/kit';

// Initialize Sentry for server-side error tracking
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.ENVIRONMENT || 'development',

  // Performance Monitoring
  tracesSampleRate: parseFloat(process.env.SENTRY_TRACES_SAMPLE_RATE || '0.1'), // 10% of transactions

  // Release tracking
  release: `prsnl-frontend@${process.env.VERSION || '2.3.0'}`,

  // Additional options
  beforeSend(event, _hint) {
    // Don't send events in development unless explicitly enabled
    if (process.env.NODE_ENV === 'development' && process.env.SENTRY_ENABLE_IN_DEV !== 'true') {
      return null;
    }

    return event;
  },
});

// Legacy URL redirect mappings
// TEMPORARILY DISABLED: These redirects point to non-existent /p/ and /s/ directories
// Will be re-enabled in Phase 3 when new routes are properly implemented
const LEGACY_REDIRECTS = new Map([
	// Processing tools
	// ['/timeline', '/p/timeline'],
	// ['/insights', '/p/insights'],
	// ['/chat', '/p/chat'],
	// ['/videos', '/p/visual'],
	// ['/code-cortex', '/p/code'],
	
	// System pages - keeping import redirects as they might be used
	['/import/v1', '/import?v=v1'],
	['/import/v2', '/import?v=v2'],
	// ['/import', '/s/import'],
	// ['/settings', '/s/settings'],
	// ['/docs', '/s/docs'],
]);

// Modern permalink redirects - redirect old routes to new structure
const MODERN_REDIRECTS = new Map([
	// Consolidate item routes to thoughts
	['/item', '/thoughts'],
	['/items', '/thoughts'],
]);

// Dynamic item ID patterns - redirect to slug-based URLs
const ITEM_ID_PATTERN = /^\/items?\/([a-f0-9-]+|\d+)$/;
const VIDEO_ID_PATTERN = /^\/videos\/([a-f0-9-]+|\d+)$/;

export const handle: Handle = async ({ event, resolve }) => {
	const pathname = event.url.pathname;
	
	// Handle modern permalink redirects
	if (MODERN_REDIRECTS.has(pathname)) {
		const newPath = MODERN_REDIRECTS.get(pathname)!;
		throw redirect(301, newPath);
	}
	
	// Handle static legacy redirects
	if (LEGACY_REDIRECTS.has(pathname)) {
		const newPath = LEGACY_REDIRECTS.get(pathname)!;
		throw redirect(301, newPath);
	}
	
	// Handle dynamic item ID redirects
	const itemMatch = pathname.match(ITEM_ID_PATTERN);
	if (itemMatch) {
		const itemId = itemMatch[1];
		
		try {
			// Try to fetch slug for the item from backend
			const response = await fetch(`${event.url.origin}/api/items/${itemId}`);
			if (response.ok) {
				const data = await response.json();
				if (data.slug) {
					// Redirect to new slug-based URL
					throw redirect(301, `/thoughts/${data.slug}`);
				} else if (data.title) {
					// Generate slug from title if no slug exists
					const { generateSlug } = await import('$lib/utils/slugify');
					const slug = generateSlug(data.title, itemId);
					throw redirect(301, `/thoughts/${slug}`);
				}
			}
		} catch (error) {
			// If redirect lookup fails, fall through to 404
			console.warn(`Failed to resolve legacy item redirect for ${itemId}:`, error);
		}
	}
	
	// Handle video ID redirects
	const videoMatch = pathname.match(VIDEO_ID_PATTERN);
	if (videoMatch) {
		const videoId = videoMatch[1];
		
		try {
			// Fetch new URL from backend
			const response = await fetch(`${event.url.origin}/api/legacy-redirect/videos/${videoId}`);
			if (response.ok) {
				const data = await response.json();
				if (data.newUrl) {
					throw redirect(301, data.newUrl);
				}
			}
		} catch (error) {
			// If redirect lookup fails, fall through to 404
			console.warn(`Failed to resolve legacy video redirect for ${videoId}:`, error);
		}
	}
	
	return resolve(event);
};

// Use Sentry's handleError function
export const handleError = handleErrorWithSentry();
