/**
 * Client-side auth guard that redirects unauthenticated users
 * Only runs once per session to avoid repeated checks
 */

import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { get } from 'svelte/store';
import { isAuthenticated } from './stores/unified-auth';

let authCheckPerformed = false;

export function setupAuthGuard() {
  if (!browser || authCheckPerformed) return;
  
  // Only perform auth check once per session
  authCheckPerformed = true;
  
  // Check if user is authenticated
  const authenticated = get(isAuthenticated);
  
  // If not authenticated and not on auth page, redirect to login
  if (!authenticated && !window.location.pathname.startsWith('/auth')) {
    goto('/auth/login');
  }
}