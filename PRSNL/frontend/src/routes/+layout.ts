import type { LayoutLoad } from './$types';
import { browser } from '$app/environment';
import { get } from 'svelte/store';
import { isAuthenticated } from '$lib/stores/auth';

export const ssr = false; // Disable SSR for authentication

export const load: LayoutLoad = async ({ url }) => {
  // List of public routes that don't require authentication
  const publicRoutes = [
    '/auth/login',
    '/auth/signup',
    '/auth/verify-email',
    '/auth/magic-link',
    '/auth/forgot-password',
    '/auth/reset-password',
    '/test-auth' // Add test route
  ];

  // Check if current route is public
  const isPublicRoute = publicRoutes.some(route => url.pathname.startsWith(route));

  // Only check authentication in browser
  if (browser && !isPublicRoute) {
    // Wait for auth to be initialized
    const { authInitialized } = await import('$lib/stores/auth');
    await authInitialized;
    
    const authenticated = get(isAuthenticated);
    
    // If not authenticated and trying to access protected route, redirect to login
    if (!authenticated) {
      // Import goto dynamically to avoid SSR issues
      const { goto } = await import('$app/navigation');
      await goto('/auth/login');
      return {
        isPublicRoute,
        authenticated: false
      };
    }
  }

  return {
    isPublicRoute,
    authenticated: browser ? get(isAuthenticated) : false
  };
};