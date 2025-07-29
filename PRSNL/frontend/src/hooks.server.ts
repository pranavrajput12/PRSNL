import { handleErrorWithSentry } from '@sentry/sveltekit';
import * as Sentry from '@sentry/sveltekit';
import { redirect } from '@sveltejs/kit';
import type { Handle } from '@sveltejs/kit';
// Import the centralized URL system
import { getRedirectUrl, validateUrlDepth } from '$lib/config/urlMappings';

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

export const handle: Handle = async ({ event, resolve }) => {
  const pathname = event.url.pathname;

  console.log(`[ROUTING] Processing request: ${pathname}`);

  // Check URL depth (enforce max 3 levels)
  if (!validateUrlDepth(pathname)) {
    console.warn(`[ROUTING] URL exceeds maximum depth: ${pathname}`);
  }

  // Check if this URL needs a redirect
  const redirectUrl = getRedirectUrl(pathname);
  if (redirectUrl) {
    console.log(`[ROUTING] Redirecting: ${pathname} → ${redirectUrl}`);
    throw redirect(301, redirectUrl);
  }

  // No need for special item handling - the redirects in urlMappings handle everything

  return resolve(event);
};

// Use Sentry's handleError function
export const handleError = handleErrorWithSentry();
