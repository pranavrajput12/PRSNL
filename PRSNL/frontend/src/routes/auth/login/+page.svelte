<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authActions, isAuthenticated, isLoading, authError } from '$lib/stores/auth';
  import Icon from '$lib/components/Icon.svelte';

  // Form state
  let formData = {
    email: '',
    password: ''
  };

  let showPassword = false;
  let loginMode: 'password' | 'magic-link' = 'password';
  let magicLinkSent = false;
  let formErrors: Record<string, string> = {};

  // Redirect if already authenticated
  $: if ($isAuthenticated) {
    goto('/');
  }

  // Validation
  function validateEmail(email: string): string | null {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) return 'Email is required';
    if (!emailRegex.test(email)) return 'Please enter a valid email address';
    return null;
  }

  function validatePassword(password: string): string | null {
    if (!password) return 'Password is required';
    return null;
  }

  function validateForm(): boolean {
    formErrors = {};
    
    const emailError = validateEmail(formData.email);
    if (emailError) formErrors.email = emailError;
    
    if (loginMode === 'password') {
      const passwordError = validatePassword(formData.password);
      if (passwordError) formErrors.password = passwordError;
    }
    
    return Object.keys(formErrors).length === 0;
  }

  async function handleSubmit() {
    if (!validateForm()) return;

    if (loginMode === 'password') {
      const success = await authActions.login({
        email: formData.email,
        password: formData.password
      });

      if (success) {
        goto('/');
      }
    } else {
      const success = await authActions.sendMagicLink(formData.email);
      if (success) {
        magicLinkSent = true;
      }
    }
  }

  function switchMode() {
    loginMode = loginMode === 'password' ? 'magic-link' : 'password';
    formErrors = {};
    authActions.clearError();
    magicLinkSent = false;
  }

  // Clear errors when inputs change
  $: if (formData.email) delete formErrors.email;
  $: if (formData.password) delete formErrors.password;

  onMount(() => {
    // Clear any previous errors
    authActions.clearError();
  });
</script>

<svelte:head>
  <title>Sign In - PRSNL</title>
  <meta name="description" content="Sign in to your PRSNL account and access your AI-powered knowledge base" />
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
      <h1 class="text-3xl font-bold text-white mb-2">Welcome back</h1>
      <p class="text-slate-300">Sign in to continue your AI-powered journey</p>
    </div>

    <!-- Login Mode Toggle -->
    <div class="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-2 mb-6 shadow-xl">
      <div class="grid grid-cols-2 gap-2">
        <button
          type="button"
          on:click={() => loginMode = 'password'}
          class="relative px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 {
            loginMode === 'password'
              ? 'bg-white/20 text-white shadow-lg'
              : 'text-slate-300 hover:text-white'
          }"
        >
          <Icon name="lock" class="w-4 h-4 inline mr-2" />
          Password
        </button>
        <button
          type="button"
          on:click={() => loginMode = 'magic-link'}
          class="relative px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 {
            loginMode === 'magic-link'
              ? 'bg-white/20 text-white shadow-lg'
              : 'text-slate-300 hover:text-white'
          }"
        >
          <Icon name="mail" class="w-4 h-4 inline mr-2" />
          Magic Link
        </button>
      </div>
    </div>

    <!-- Form Card -->
    <div class="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 shadow-2xl">
      {#if magicLinkSent}
        <!-- Magic Link Sent State -->
        <div class="text-center space-y-6">
          <div class="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto">
            <Icon name="mail-check" class="w-8 h-8 text-white" />
          </div>
          <div>
            <h2 class="text-xl font-semibold text-white mb-2">Check your email</h2>
            <p class="text-slate-300 mb-4">
              We've sent a magic link to <strong class="text-white">{formData.email}</strong>
            </p>
            <p class="text-sm text-slate-400">
              Click the link in your email to sign in. The link will expire in 15 minutes.
            </p>
          </div>
          <div class="flex flex-col space-y-3">
            <button
              type="button"
              on:click={() => handleSubmit()}
              disabled={$isLoading}
              class="w-full px-6 py-3 bg-white/10 border border-white/20 text-white rounded-lg hover:bg-white/20 transition-all duration-200 disabled:opacity-50"
            >
              {#if $isLoading}
                <Icon name="loader-2" class="w-4 h-4 animate-spin inline mr-2" />
                Resending...
              {:else}
                <Icon name="refresh-cw" class="w-4 h-4 inline mr-2" />
                Resend magic link
              {/if}
            </button>
            <button
              type="button"
              on:click={() => { magicLinkSent = false; loginMode = 'password'; }}
              class="text-purple-400 hover:text-purple-300 text-sm transition-colors"
            >
              Use password instead
            </button>
          </div>
        </div>
      {:else}
        <!-- Login Form -->
        <form on:submit|preventDefault={handleSubmit} class="space-y-6">
          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-medium text-slate-200 mb-2">Email Address</label>
            <div class="relative">
              <input
                type="email"
                id="email"
                bind:value={formData.email}
                class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
                placeholder="you@example.com"
                autocomplete="email"
                required
              />
              <Icon name="mail" class="absolute right-3 top-3.5 w-5 h-5 text-slate-400" />
            </div>
            {#if formErrors.email}
              <p class="text-red-400 text-sm mt-1">{formErrors.email}</p>
            {/if}
          </div>

          <!-- Password (only shown in password mode) -->
          {#if loginMode === 'password'}
            <div>
              <div class="flex items-center justify-between mb-2">
                <label for="password" class="block text-sm font-medium text-slate-200">Password</label>
                <a href="/auth/forgot-password" class="text-sm text-purple-400 hover:text-purple-300 transition-colors">
                  Forgot password?
                </a>
              </div>
              <div class="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  bind:value={formData.password}
                  class="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 pr-12"
                  placeholder="Enter your password"
                  autocomplete="current-password"
                  required
                />
                <button
                  type="button"
                  on:click={() => showPassword = !showPassword}
                  class="absolute right-3 top-3.5 text-slate-400 hover:text-white transition-colors"
                >
                  <Icon name={showPassword ? 'eye-off' : 'eye'} class="w-5 h-5" />
                </button>
              </div>
              {#if formErrors.password}
                <p class="text-red-400 text-sm mt-1">{formErrors.password}</p>
              {/if}
            </div>
          {/if}

          <!-- Magic Link Description -->
          {#if loginMode === 'magic-link'}
            <div class="bg-purple-500/20 border border-purple-500/30 rounded-lg p-4">
              <div class="flex items-start space-x-3">
                <Icon name="zap" class="w-5 h-5 text-purple-400 mt-0.5" />
                <div>
                  <h3 class="text-sm font-medium text-white mb-1">Passwordless Sign In</h3>
                  <p class="text-xs text-slate-300">
                    We'll send you a secure link that will automatically sign you in. No password needed!
                  </p>
                </div>
              </div>
            </div>
          {/if}

          <!-- Error Display -->
          {#if $authError}
            <div class="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
              <div class="flex items-center space-x-2">
                <Icon name="alert-circle" class="w-5 h-5 text-red-400" />
                <p class="text-red-400 text-sm">{$authError}</p>
              </div>
            </div>
          {/if}

          <!-- Submit Button -->
          <button
            type="submit"
            disabled={$isLoading}
            class="w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium rounded-lg transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center space-x-2"
          >
            {#if $isLoading}
              <Icon name="loader-2" class="w-4 h-4 animate-spin" />
              <span>{loginMode === 'password' ? 'Signing in...' : 'Sending magic link...'}</span>
            {:else}
              {#if loginMode === 'password'}
                <Icon name="log-in" class="w-4 h-4" />
                <span>Sign In</span>
              {:else}
                <Icon name="mail" class="w-4 h-4" />
                <span>Send Magic Link</span>
              {/if}
            {/if}
          </button>
        </form>
      {/if}
    </div>

    <!-- Sign Up Link -->
    <div class="text-center mt-6">
      <p class="text-slate-300">
        Don't have an account? 
        <a href="/auth/signup" class="text-purple-400 hover:text-purple-300 font-medium transition-colors duration-200">
          Create one now
        </a>
      </p>
    </div>

    <!-- Social Login (Future) -->
    <!-- 
    <div class="mt-8">
      <div class="relative">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-white/20"></div>
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-slate-900 text-slate-400">Or continue with</span>
        </div>
      </div>
      
      <div class="mt-6 grid grid-cols-2 gap-3">
        <button class="w-full inline-flex justify-center py-3 px-4 border border-white/20 rounded-lg bg-white/10 text-sm font-medium text-white hover:bg-white/20 transition-colors">
          <Icon name="github" class="w-5 h-5" />
          <span class="ml-2">GitHub</span>
        </button>
        
        <button class="w-full inline-flex justify-center py-3 px-4 border border-white/20 rounded-lg bg-white/10 text-sm font-medium text-white hover:bg-white/20 transition-colors">
          <Icon name="chrome" class="w-5 h-5" />
          <span class="ml-2">Google</span>
        </button>
      </div>
    </div>
    -->
  </div>
</div>

<style>
  /* Custom scrollbar for the page */
  :global(html) {
    scrollbar-width: thin;
    scrollbar-color: rgba(139, 92, 246, 0.5) transparent;
  }

  :global(html::-webkit-scrollbar) {
    width: 6px;
  }

  :global(html::-webkit-scrollbar-track) {
    background: transparent;
  }

  :global(html::-webkit-scrollbar-thumb) {
    background: rgba(139, 92, 246, 0.5);
    border-radius: 3px;
  }

  :global(html::-webkit-scrollbar-thumb:hover) {
    background: rgba(139, 92, 246, 0.7);
  }
</style>