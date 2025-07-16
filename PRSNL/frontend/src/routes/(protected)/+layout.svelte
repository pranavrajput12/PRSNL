<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { authGuard, redirectIfAuthenticated } from '$lib/auth/auth-guard';
  import { isAuthenticated, isLoading } from '$lib/stores/auth';
  
  let authCheckComplete = false;

  // Check authentication on mount and route changes
  $: if ($page.url.pathname && !$isLoading) {
    checkAuth($page.url.pathname);
  }

  async function checkAuth(pathname: string) {
    authCheckComplete = false;

    // Redirect authenticated users away from auth pages
    if (redirectIfAuthenticated(pathname)) {
      return;
    }

    // Run auth guard for protected routes
    const canAccess = await authGuard(pathname);
    
    if (canAccess) {
      authCheckComplete = true;
    }
    // If can't access, authGuard will handle the redirect
  }

  onMount(() => {
    checkAuth($page.url.pathname);
  });
</script>

<!-- Only render content if auth check is complete and user is authenticated -->
{#if authCheckComplete && $isAuthenticated}
  <slot />
{:else if $isLoading}
  <!-- Loading state -->
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
    <div class="text-center space-y-4">
      <div class="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto animate-pulse">
        <div class="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
      </div>
      <p class="text-white text-lg">Checking authentication...</p>
    </div>
  </div>
{:else}
  <!-- Fallback loading or error state -->
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
    <div class="text-center space-y-4">
      <div class="w-16 h-16 bg-gradient-to-r from-red-500 to-rose-500 rounded-full flex items-center justify-center mx-auto">
        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <p class="text-white text-lg">Authentication required</p>
      <p class="text-slate-300">Redirecting to login...</p>
    </div>
  </div>
{/if}