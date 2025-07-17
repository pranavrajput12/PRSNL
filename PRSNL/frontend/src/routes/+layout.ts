import type { LayoutLoad } from './$types';
import { browser } from '$app/environment';
import { get } from 'svelte/store';
import { isAuthenticated } from '$lib/stores/unified-auth';

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

  return {
    isPublicRoute
  };
};