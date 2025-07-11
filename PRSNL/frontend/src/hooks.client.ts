import { handleErrorWithSentry, replayIntegration } from '@sentry/sveltekit';
import * as Sentry from '@sentry/sveltekit';

// Initialize Sentry for client-side error tracking
Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.VITE_ENVIRONMENT || 'development',

  // Performance Monitoring
  tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0.1'), // 10% of transactions

  // Session Replay
  replaysSessionSampleRate: 0.1, // 10% of sessions will be recorded
  replaysOnErrorSampleRate: 1.0, // 100% of sessions with errors will be recorded

  // Release tracking
  release: `prsnl-frontend@${import.meta.env.VITE_VERSION || '2.3.0'}`,

  // Integrations
  integrations: [
    replayIntegration({
      maskAllText: false,
      maskAllInputs: true,
      blockAllMedia: false,
    }),
  ],

  // Additional options
  beforeSend(event, hint) {
    // Don't send events in development unless explicitly enabled
    if (import.meta.env.DEV && !import.meta.env.VITE_SENTRY_ENABLE_IN_DEV) {
      return null;
    }

    // Filter out certain errors
    const error = hint.originalException;

    // Ignore network errors that are expected
    if (
      error &&
      error instanceof Error &&
      error.message &&
      error.message.includes('Failed to fetch')
    ) {
      return null;
    }

    // Ignore ResizeObserver errors (common and not actionable)
    if (
      error &&
      error instanceof Error &&
      error.message &&
      error.message.includes('ResizeObserver')
    ) {
      return null;
    }

    return event;
  },

  // Ignore certain errors
  ignoreErrors: [
    // Browser extensions
    'top.GLOBALS',
    // Random plugins/extensions
    'originalCreateNotification',
    'canvas.contentDocument',
    'MyApp_RemoveAllHighlights',
    // Facebook related errors
    'fb_xd_fragment',
    // Generic errors
    'Non-Error promise rejection captured',
    // Network errors
    'Network request failed',
    'NetworkError',
    'Failed to fetch',
  ],
});

// Use Sentry's handleError function
export const handleError = handleErrorWithSentry();
