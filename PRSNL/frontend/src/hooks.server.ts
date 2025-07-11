import { handleErrorWithSentry } from '@sentry/sveltekit';
import * as Sentry from '@sentry/sveltekit';

// Initialize Sentry for server-side error tracking
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.ENVIRONMENT || 'development',

  // Performance Monitoring
  tracesSampleRate: parseFloat(process.env.SENTRY_TRACES_SAMPLE_RATE || '0.1'), // 10% of transactions

  // Release tracking
  release: `prsnl-frontend@${process.env.VERSION || '2.3.0'}`,

  // Additional options
  beforeSend(event, hint) {
    // Don't send events in development unless explicitly enabled
    if (process.env.NODE_ENV === 'development' && process.env.SENTRY_ENABLE_IN_DEV !== 'true') {
      return null;
    }

    return event;
  },
});

// Use Sentry's handleError function
export const handleError = handleErrorWithSentry();
