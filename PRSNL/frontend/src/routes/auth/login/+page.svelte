<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { authActions, isAuthenticated, isLoading, authError } from '$lib/stores/unified-auth';
  import Icon from '$lib/components/Icon.svelte';
  import NeuralBackground from '$lib/components/NeuralBackground.svelte';
  import InspirationMessage from '$lib/components/InspirationMessage.svelte';
  import MagneticButton from '$lib/components/MagneticButton.svelte';
  import BreathingCard from '$lib/components/BreathingCard.svelte';

  // Form state
  let formData = {
    email: '',
    password: ''
  };

  let showPassword = false;
  let loginMode: 'password' | 'magic-link' = 'password';
  let magicLinkSent = false;
  let formErrors: Record<string, string> = {};
  let isFormActive = false;

  // Inspirational messages
  const loginMessages = [
    "Welcome back to your second brain",
    "Your neural pathways await",
    "Ready to amplify your intelligence?",
    "Let's unlock your digital consciousness",
    "Your knowledge graph misses you"
  ];

  const successMessages = [
    "Synapses firing... Intelligence loading...",
    "Neural connection established",
    "Preparing your cognitive enhancement..."
  ];

  // Redirect if already authenticated
  $: if ($isAuthenticated) {
    // Check for redirect parameter in URL
    const redirectTo = $page.url.searchParams.get('redirect');
    const destination = redirectTo || '/';
    goto(destination);
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
      try {
        // Use auth service for proper state management
        await authActions.loginWithPRSNL({
          email: formData.email,
          password: formData.password
        });
        
        // Redirect to intended destination or homepage
        const redirectTo = $page.url.searchParams.get('redirect');
        const destination = redirectTo || '/';
        goto(destination);
      } catch (error) {
        console.error('Login failed:', error);
      }
    } else {
      // Magic link not implemented in unified auth yet
      // Fall back to Google SSO for passwordless experience
      try {
        await authActions.loginWithGoogle();
      } catch (error) {
        console.error('Google login failed:', error);
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

<div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4 relative overflow-hidden">
  <!-- Animated Neural Network Background -->
  <NeuralBackground 
    particleCount={100}
    connectionDistance={150}
    mouseInfluence={true}
    colorScheme={{
      particles: '#8b5cf6',
      connections: '#ec4899',
      mouseGlow: '#10b981'
    }}
  />
  
  <!-- Gradient Overlay for depth -->
  <div class="absolute inset-0 bg-gradient-to-t from-slate-900/50 via-transparent to-purple-900/30 pointer-events-none"></div>
  
  <!-- Inspirational Messages -->
  {#if !$isLoading}
    <InspirationMessage 
      messages={loginMessages}
      position="top"
      size="medium"
      interval={6000}
    />
  {:else}
    <InspirationMessage 
      messages={successMessages}
      position="top"
      size="medium"
      interval={3000}
    />
  {/if}

  <div class="w-full max-w-md relative z-10">
    <!-- Header with enhanced animation -->
    <div class="text-center mb-8 animate-fade-in">
      <div class="inline-flex items-center space-x-2 mb-4 group">
        <div class="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center transform transition-all duration-300 group-hover:scale-110 group-hover:rotate-12">
          <Icon name="brain" class="w-6 h-6 text-white" />
        </div>
        <span class="text-2xl font-bold text-white bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">PRSNL</span>
      </div>
      <h1 class="text-3xl font-bold text-white mb-2 animate-slide-up">Welcome back</h1>
      <p class="text-slate-300 animate-slide-up-delayed">Your digital consciousness awaits</p>
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

    <!-- Form Card with breathing effect -->
    <BreathingCard 
      glowColor={isFormActive ? '#10b981' : '#8b5cf6'} 
      breathingScale={0.015} 
      breathingDuration={4}
      interactive={true}
    >
      <div on:focusin={() => isFormActive = true} on:focusout={() => isFormActive = false}>
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

          <!-- Submit Button with Magnetic Effect -->
          <MagneticButton
            type="submit"
            variant="primary"
            disabled={$isLoading}
            loading={$isLoading}
            fullWidth={true}
            size="medium"
            icon={loginMode === 'password' ? 'log-in' : 'mail'}
          >
            {#if $isLoading}
              {loginMode === 'password' ? 'Signing in...' : 'Sending magic link...'}
            {:else}
              {loginMode === 'password' ? 'Sign In' : 'Send Magic Link'}
            {/if}
          </MagneticButton>
        </form>
      {/if}
      </div>
    </BreathingCard>

    <!-- Sign Up Link -->
    <div class="text-center mt-6">
      <p class="text-slate-300">
        Don't have an account? 
        <a href="/auth/signup" class="text-purple-400 hover:text-purple-300 font-medium transition-colors duration-200">
          Create one now
        </a>
      </p>
    </div>

    <!-- Social Login with Enterprise SSO -->
    <div class="mt-8">
      <div class="relative">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-white/20"></div>
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-slate-900 text-slate-400">Or continue with</span>
        </div>
      </div>
      
      <div class="mt-6 space-y-3">
        <button 
          on:click={() => authActions.loginWithGoogle()}
          disabled={$isLoading}
          class="w-full inline-flex justify-center py-3 px-4 border border-white/20 rounded-lg bg-white/10 text-sm font-medium text-white hover:bg-white/20 transition-colors disabled:opacity-50"
        >
          <Icon name="chrome" class="w-5 h-5" />
          <span class="ml-2">Continue with Google</span>
        </button>
        
        <button 
          on:click={() => authActions.loginWithGitHub()}
          disabled={$isLoading}
          class="w-full inline-flex justify-center py-3 px-4 border border-white/20 rounded-lg bg-white/10 text-sm font-medium text-white hover:bg-white/20 transition-colors disabled:opacity-50"
        >
          <Icon name="github" class="w-5 h-5" />
          <span class="ml-2">Continue with GitHub</span>
        </button>
        
        <button 
          on:click={() => authActions.loginWithMicrosoft()}
          disabled={$isLoading}
          class="w-full inline-flex justify-center py-3 px-4 border border-white/20 rounded-lg bg-white/10 text-sm font-medium text-white hover:bg-white/20 transition-colors disabled:opacity-50"
        >
          <Icon name="windows" class="w-5 h-5" />
          <span class="ml-2">Continue with Microsoft</span>
        </button>
      </div>
      
      <div class="mt-4 text-center">
        <p class="text-xs text-slate-400">
          <Icon name="shield-check" class="w-3 h-3 inline mr-1" />
          Secure enterprise SSO via Keycloak
        </p>
      </div>
    </div>
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

  /* Animations */
  :global(.animate-fade-in) {
    animation: fadeIn 0.8s ease-out;
  }

  :global(.animate-slide-up) {
    animation: slideUp 0.6s ease-out;
  }

  :global(.animate-slide-up-delayed) {
    animation: slideUp 0.6s ease-out 0.2s both;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Input focus effects */
  :global(input:focus) {
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  }

  /* Reduce motion for accessibility */
  @media (prefers-reduced-motion: reduce) {
    :global(.animate-fade-in),
    :global(.animate-slide-up),
    :global(.animate-slide-up-delayed) {
      animation: none;
    }
  }
</style>