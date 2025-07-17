<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authActions } from '$lib/stores/unified-auth';
  import Icon from '$lib/components/Icon.svelte';
  import NeuralBackground from '$lib/components/NeuralBackground.svelte';

  let status: 'loading' | 'success' | 'error' = 'loading';
  let errorMessage = '';

  onMount(async () => {
    try {
      // Handle FusionAuth callback
      await authActions.handleCallback('fusionauth');
      status = 'success';
      
      // Small delay for UX, then redirect
      setTimeout(() => {
        goto('/');
      }, 2000);
    } catch (error) {
      console.error('FusionAuth callback handling failed:', error);
      status = 'error';
      errorMessage = error instanceof Error ? error.message : 'Authentication failed';
      
      // Redirect to login after error display
      setTimeout(() => {
        goto('/auth/login');
      }, 3000);
    }
  });
</script>

<svelte:head>
  <title>Authenticating - PRSNL</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4 relative overflow-hidden">
  <!-- Animated Neural Network Background -->
  <NeuralBackground 
    particleCount={80}
    connectionDistance={150}
    mouseInfluence={false}
    colorScheme={{
      particles: '#8b5cf6',
      connections: '#ec4899',
      mouseGlow: '#10b981'
    }}
  />
  
  <!-- Gradient Overlay for depth -->
  <div class="absolute inset-0 bg-gradient-to-t from-slate-900/50 via-transparent to-purple-900/30 pointer-events-none"></div>
  
  <div class="w-full max-w-md relative z-10">
    <div class="text-center">
      <!-- Status Icon -->
      <div class="inline-flex items-center justify-center w-24 h-24 mb-6">
        {#if status === 'loading'}
          <div class="w-20 h-20 border-4 border-orange-500/30 border-t-orange-500 rounded-full animate-spin"></div>
        {:else if status === 'success'}
          <div class="w-20 h-20 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center animate-bounce">
            <Icon name="check" class="w-10 h-10 text-white" />
          </div>
        {:else}
          <div class="w-20 h-20 bg-gradient-to-r from-red-500 to-red-600 rounded-full flex items-center justify-center">
            <Icon name="x" class="w-10 h-10 text-white" />
          </div>
        {/if}
      </div>

      <!-- Status Message -->
      {#if status === 'loading'}
        <h1 class="text-2xl font-bold text-white mb-4">Authenticating...</h1>
        <p class="text-slate-300 mb-6">Completing your FusionAuth sign-in</p>
        <div class="flex items-center justify-center space-x-2 text-orange-400">
          <Icon name="zap" class="w-4 h-4" />
          <span class="text-sm">Processing via FusionAuth</span>
        </div>
      {:else if status === 'success'}
        <h1 class="text-2xl font-bold text-white mb-4">Welcome to PRSNL!</h1>
        <p class="text-slate-300 mb-6">FusionAuth authentication successful. Redirecting to your dashboard...</p>
        <div class="flex items-center justify-center space-x-2 text-green-400">
          <Icon name="user-check" class="w-4 h-4" />
          <span class="text-sm">Signed in successfully</span>
        </div>
      {:else}
        <h1 class="text-2xl font-bold text-white mb-4">Authentication Failed</h1>
        <p class="text-slate-300 mb-6">{errorMessage}</p>
        <div class="flex items-center justify-center space-x-2 text-red-400">
          <Icon name="alert-circle" class="w-4 h-4" />
          <span class="text-sm">Redirecting to login...</span>
        </div>
      {/if}

      <!-- Loading Progress -->
      {#if status === 'loading'}
        <div class="mt-8">
          <div class="w-full bg-slate-700 rounded-full h-2">
            <div class="bg-gradient-to-r from-orange-500 to-yellow-500 h-2 rounded-full animate-pulse" style="width: 75%;"></div>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  @keyframes bounce {
    0%, 20%, 53%, 80%, 100% {
      transform: translate3d(0,0,0);
    }
    40%, 43% {
      transform: translate3d(0,-30px,0);
    }
    70% {
      transform: translate3d(0,-15px,0);
    }
    90% {
      transform: translate3d(0,-4px,0);
    }
  }

  .animate-bounce {
    animation: bounce 1.5s ease-in-out;
  }
</style>