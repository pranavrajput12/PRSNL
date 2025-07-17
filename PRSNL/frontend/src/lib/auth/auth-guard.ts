/**
 * Authentication Guard for PRSNL
 * Handles route protection and redirection logic
 */

import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { get } from 'svelte/store';
import { authStore, authActions } from '$lib/stores/unified-auth';

export interface AuthGuardOptions {
  redirectTo?: string;
  requireVerification?: boolean;
  allowedUserTypes?: Array<'individual' | 'team' | 'enterprise'>;
}

/**
 * Routes that don't require authentication
 */
export const PUBLIC_ROUTES = new Set([
  '/',
  '/auth/login',
  '/auth/signup',
  '/auth/verify-email',
  '/auth/magic-link',
  '/auth/forgot-password',
  '/demo-github-cards',
  '/demo-repository-preview',
  '/preview-avatar',
  '/preview-dna',
  '/preview-galaxy',
  '/preview-racing',
  '/preview-terrarium',
  '/vertical-nav-a-modern.html',
  '/vertical-nav-b-innovative.html',
  '/vertical-nav-c-unique.html',
  '/menu-preview-1.html',
  '/menu-preview-2.html',
  '/menu-preview-3.html',
  '/menu-preview-4.html',
  '/menu-preview-5.html',
  '/nav-preview-a-floating-bubbles.html',
  '/nav-preview-b-arc-curved.html',
  '/nav-preview-c-layered-cards.html'
]);

/**
 * Check if a route is public (doesn't require authentication)
 */
export function isPublicRoute(pathname: string): boolean {
  // Check exact matches first
  if (PUBLIC_ROUTES.has(pathname)) {
    return true;
  }

  // Check for dynamic auth routes
  if (pathname.startsWith('/auth/')) {
    return true;
  }

  // Check for other public patterns
  if (pathname.startsWith('/s/') || pathname.startsWith('/p/') || pathname.startsWith('/c/')) {
    return true; // These might be public content pages
  }

  return false;
}

/**
 * Main authentication guard function
 */
export async function authGuard(pathname: string, options: AuthGuardOptions = {}): Promise<boolean> {
  const {
    redirectTo = '/auth/login',
    requireVerification = false,
    allowedUserTypes = []
  } = options;

  // Skip guard on server-side
  if (!browser) {
    return true;
  }

  // Allow public routes
  if (isPublicRoute(pathname)) {
    return true;
  }

  const auth = get(authStore);

  // Check if user is authenticated
  if (!auth.isAuthenticated || !auth.user || !auth.token) {
    console.log('Auth guard: User not authenticated, redirecting to', redirectTo, {
      isAuthenticated: auth.isAuthenticated,
      hasUser: !!auth.user,
      hasToken: !!auth.token,
      authSource: auth.authSource
    });
    goto(redirectTo);
    return false;
  }

  // Check email verification if required
  if (requireVerification && !auth.user.isEmailVerified) {
    console.log('Auth guard: Email verification required');
    goto('/auth/verify-email?required=true');
    return false;
  }

  // Check user type restrictions
  if (allowedUserTypes.length > 0) {
    console.log('Auth guard: User type not allowed for this route');
    goto('/'); // Redirect to dashboard
    return false;
  }

  // Don't try to refresh on every route change - the service handles this
  // Only the initial auth check in the service will handle token refresh

  return true;
}

/**
 * Auth guard for enterprise features
 */
export async function enterpriseGuard(pathname: string): Promise<boolean> {
  return authGuard(pathname, {
    requireVerification: true,
    allowedUserTypes: ['enterprise']
  });
}

/**
 * Auth guard for team features
 */
export async function teamGuard(pathname: string): Promise<boolean> {
  return authGuard(pathname, {
    requireVerification: true,
    allowedUserTypes: ['team', 'enterprise']
  });
}

/**
 * Auth guard for verified users only
 */
export async function verifiedGuard(pathname: string): Promise<boolean> {
  return authGuard(pathname, {
    requireVerification: true
  });
}

/**
 * Redirect authenticated users away from auth pages
 */
export function redirectIfAuthenticated(pathname: string): boolean {
  if (!browser) {
    return false;
  }

  const auth = get(authStore);
  
  if (auth.isAuthenticated && pathname.startsWith('/auth/')) {
    console.log('Auth guard: Authenticated user accessing auth page, redirecting to dashboard');
    goto('/');
    return true;
  }

  return false;
}

/**
 * Get user permissions for route access
 */
export function getUserPermissions() {
  const auth = get(authStore);
  
  if (!auth.user) {
    return {
      canAccessTeamFeatures: false,
      canAccessEnterpriseFeatures: false,
      isVerified: false,
      userType: null
    };
  }

  return {
    canAccessTeamFeatures: false, // TODO: implement user type checking
    canAccessEnterpriseFeatures: false, // TODO: implement user type checking
    isVerified: auth.user.isEmailVerified,
    userType: 'individual' // TODO: implement user type
  };
}