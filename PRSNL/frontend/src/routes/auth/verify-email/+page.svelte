<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { authActions, isAuthenticated, isLoading } from '$lib/stores/auth';
  import Icon from '$lib/components/Icon.svelte';

  let verificationStatus: 'loading' | 'success' | 'error' | 'expired' = 'loading';
  let errorMessage = '';

  // Redirect if already authenticated
  $: if ($isAuthenticated) {
    goto('/');
  }

  onMount(async () => {
    const token = $page.url.searchParams.get('token');
    
    if (!token) {
      verificationStatus = 'error';
      errorMessage = 'No verification token provided';
      return;
    }

    try {
      const success = await authActions.verifyEmail(token);
      
      if (success) {
        verificationStatus = 'success';
        // Redirect to dashboard after a brief success message
        setTimeout(() => {
          goto('/');
        }, 3000);
      } else {
        verificationStatus = 'error';
        errorMessage = 'Invalid or expired verification token';
      }
    } catch (error) {
      verificationStatus = 'error';
      errorMessage = error instanceof Error ? error.message : 'Verification failed';
    }
  });

  async function resendVerification() {
    const success = await authActions.resendVerification();
    if (success) {
      goto('/auth/login');
    }
  }
</script>

<svelte:head>
  <title>Verify Email - PRSNL</title>
  <meta name="description" content="Verify your email address to complete your PRSNL account setup" />
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
  <!-- Background Pattern -->
  <div class="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.03%22%3E%3Cpath%20d%3D%22M36%2034v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6%2034v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6%204V0H4v4H0v2h4v4h2V6h4V4H6z%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-20"></div>

  <div class="w-full max-w-md relative">
    <!-- Header -->
    <div class="text-center mb-8">
      <div class="inline-flex items-center space-x-2 mb-4">
        <div class="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
          <Icon name="brain" class="w-6 h-6 text-white" />
        </div>
        <span class="text-2xl font-bold text-white">PRSNL</span>
      </div>
    </div>

    <!-- Verification Card -->
    <div class="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 shadow-2xl">
      <div class="text-center space-y-6">
        {#if verificationStatus === 'loading'}
          <!-- Loading State -->
          <div class="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto">
            <Icon name="loader-2" class="w-8 h-8 text-white animate-spin" />
          </div>
          <div>
            <h1 class="text-2xl font-bold text-white mb-2">Verifying your email</h1>
            <p class="text-slate-300">Please wait while we verify your email address...</p>
          </div>
        
        {:else if verificationStatus === 'success'}
          <!-- Success State -->
          <div class="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto">
            <Icon name="check-circle" class="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 class="text-2xl font-bold text-white mb-2">Email verified!</h1>
            <p class="text-slate-300 mb-4">
              Your email address has been successfully verified. Welcome to PRSNL!
            </p>
            <p class="text-sm text-slate-400">
              Redirecting you to your dashboard in a few seconds...
            </p>
          </div>
          <div class="flex items-center justify-center space-x-2 text-purple-400">
            <Icon name="loader-2" class="w-4 h-4 animate-spin" />
            <span class="text-sm">Taking you to your dashboard...</span>
          </div>
        
        {:else if verificationStatus === 'error'}
          <!-- Error State -->
          <div class="w-16 h-16 bg-gradient-to-r from-red-500 to-rose-500 rounded-full flex items-center justify-center mx-auto">
            <Icon name="x-circle" class="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 class="text-2xl font-bold text-white mb-2">Verification failed</h1>
            <p class="text-slate-300 mb-4">{errorMessage}</p>
            <p class="text-sm text-slate-400 mb-6">
              This could happen if the verification link has expired or has already been used.
            </p>
          </div>
          
          <div class="space-y-3">
            <button
              on:click={resendVerification}
              disabled={$isLoading}
              class="w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {#if $isLoading}
                <Icon name="loader-2" class="w-4 h-4 animate-spin" />
                <span>Sending...</span>
              {:else}
                <Icon name="mail" class="w-4 h-4" />
                <span>Resend verification email</span>
              {/if}
            </button>
            
            <a
              href="/auth/login"
              class="block w-full px-6 py-3 bg-white/10 border border-white/20 text-white rounded-lg hover:bg-white/20 transition-all duration-200 text-center"
            >
              Back to sign in
            </a>
          </div>
        {/if}
      </div>
    </div>

    <!-- Help Text -->
    <div class="text-center mt-6">
      <p class="text-slate-400 text-sm">
        Need help? 
        <a href="/support" class="text-purple-400 hover:text-purple-300 transition-colors">
          Contact support
        </a>
      </p>
    </div>
  </div>
</div>