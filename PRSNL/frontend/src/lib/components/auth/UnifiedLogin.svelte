<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { authActions, authError, isLoading } from '$lib/stores/unified-auth';
  import Icon from '$lib/components/Icon.svelte';
  
  const dispatch = createEventDispatcher();
  
  export let redirectUrl: string = '/timeline';
  export let showSocialLogin: boolean = true;
  export let showSignupLink: boolean = true;
  export let title: string = 'Welcome to PRSNL';
  export let subtitle: string = 'Your Personal Knowledge Management Platform';
  
  let activeTab: 'social' | 'email' = 'social';
  let email = '';
  let password = '';
  let formErrors: Record<string, string> = {};
  let isSubmitting = false;
  
  // Social login handlers
  async function handleSocialLogin(provider: 'google' | 'github' | 'microsoft') {
    try {
      isSubmitting = true;
      authActions.clearError();
      
      if (provider === 'google') {
        await authActions.loginWithGoogle();
      } else if (provider === 'github') {
        await authActions.loginWithGitHub();
      } else if (provider === 'microsoft') {
        await authActions.loginWithMicrosoft();
      }
      
      dispatch('login-success');
    } catch (error) {
      console.error(`${provider} login failed:`, error);
    } finally {
      isSubmitting = false;
    }
  }
  
  // Email/password login
  async function handleEmailLogin() {
    if (!validateForm()) return;
    
    try {
      isSubmitting = true;
      authActions.clearError();
      
      // Use PRSNL backend for email/password login
      await authActions.signupWithPRSNL({
        email,
        password,
        firstName: '',
        lastName: ''
      });
      
      dispatch('login-success');
    } catch (error) {
      console.error('Email login failed:', error);
      formErrors.general = error instanceof Error ? error.message : 'Login failed';
    } finally {
      isSubmitting = false;
    }
  }
  
  function validateForm(): boolean {
    formErrors = {};
    
    if (!email) {
      formErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      formErrors.email = 'Please enter a valid email address';
    }
    
    if (!password) {
      formErrors.password = 'Password is required';
    } else if (password.length < 6) {
      formErrors.password = 'Password must be at least 6 characters';
    }
    
    return Object.keys(formErrors).length === 0;
  }
  
  function handleSignupClick() {
    dispatch('show-signup');
  }
  
  // Clear field errors when user types
  $: if (email) delete formErrors.email;
  $: if (password) delete formErrors.password;
</script>

<div class="login-container">
  <!-- Header -->
  <div class="login-header">
    <div class="logo">
      <div class="logo-icon">
        <Icon name="brain" class="w-8 h-8 text-purple-500" />
      </div>
      <h1>{title}</h1>
    </div>
    <p class="subtitle">{subtitle}</p>
  </div>

  <!-- Login Form -->
  <div class="login-form">
    <!-- Tab Navigation -->
    <div class="tab-nav">
      <button 
        type="button"
        class="tab-btn {activeTab === 'social' ? 'active' : ''}"
        on:click={() => activeTab = 'social'}
      >
        <Icon name="users" class="w-4 h-4" />
        Quick Login
      </button>
      <button 
        type="button"
        class="tab-btn {activeTab === 'email' ? 'active' : ''}"
        on:click={() => activeTab = 'email'}
      >
        <Icon name="mail" class="w-4 h-4" />
        Email
      </button>
    </div>

    <!-- Error Display -->
    {#if $authError || formErrors.general}
      <div class="error-alert">
        <Icon name="alert-circle" class="w-4 h-4" />
        <span>{$authError || formErrors.general}</span>
      </div>
    {/if}

    <!-- Social Login Tab -->
    {#if activeTab === 'social' && showSocialLogin}
      <div class="social-login">
        <div class="social-buttons">
          <button 
            type="button"
            class="social-btn google"
            on:click={() => handleSocialLogin('google')}
            disabled={isSubmitting || $isLoading}
          >
            <Icon name="chrome" class="w-5 h-5" />
            <span>Continue with Google</span>
          </button>
          
          <button 
            type="button"
            class="social-btn github"
            on:click={() => handleSocialLogin('github')}
            disabled={isSubmitting || $isLoading}
          >
            <Icon name="github" class="w-5 h-5" />
            <span>Continue with GitHub</span>
          </button>
          
          <button 
            type="button"
            class="social-btn microsoft"
            on:click={() => handleSocialLogin('microsoft')}
            disabled={isSubmitting || $isLoading}
          >
            <Icon name="windows" class="w-5 h-5" />
            <span>Continue with Microsoft</span>
          </button>
        </div>
        
        <div class="social-note">
          <Icon name="shield-check" class="w-4 h-4 text-green-500" />
          <span>Secure authentication via enterprise SSO</span>
        </div>
      </div>
    {/if}

    <!-- Email Login Tab -->
    {#if activeTab === 'email'}
      <form on:submit|preventDefault={handleEmailLogin} class="email-form">
        <div class="form-group">
          <label for="email">Email Address</label>
          <div class="input-wrapper">
            <input
              type="email"
              id="email"
              bind:value={email}
              placeholder="you@example.com"
              class="form-input {formErrors.email ? 'error' : ''}"
              disabled={isSubmitting || $isLoading}
            />
            <Icon name="mail" class="input-icon" />
          </div>
          {#if formErrors.email}
            <span class="field-error">{formErrors.email}</span>
          {/if}
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <div class="input-wrapper">
            <input
              type="password"
              id="password"
              bind:value={password}
              placeholder="Enter your password"
              class="form-input {formErrors.password ? 'error' : ''}"
              disabled={isSubmitting || $isLoading}
            />
            <Icon name="lock" class="input-icon" />
          </div>
          {#if formErrors.password}
            <span class="field-error">{formErrors.password}</span>
          {/if}
        </div>

        <button 
          type="submit" 
          class="login-btn"
          disabled={isSubmitting || $isLoading}
        >
          {#if isSubmitting || $isLoading}
            <Icon name="loader-2" class="w-4 h-4 animate-spin" />
            <span>Signing in...</span>
          {:else}
            <Icon name="log-in" class="w-4 h-4" />
            <span>Sign In</span>
          {/if}
        </button>
      </form>
    {/if}

    <!-- Signup Link -->
    {#if showSignupLink}
      <div class="signup-link">
        <span>Don't have an account?</span>
        <button type="button" on:click={handleSignupClick} class="link-btn">
          Sign up for free
        </button>
      </div>
    {/if}

    <!-- Security Notice -->
    <div class="security-notice">
      <Icon name="shield" class="w-4 h-4 text-blue-500" />
      <span>Your data is encrypted and secure</span>
    </div>
  </div>
</div>

<style>
  .login-container {
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
    padding: 2rem;
  }

  .login-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .logo-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 3rem;
    height: 3rem;
    background: linear-gradient(135deg, #8B5CF6, #EC4899);
    border-radius: 1rem;
  }

  .logo h1 {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #8B5CF6, #EC4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
  }

  .subtitle {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.875rem;
    margin: 0;
  }

  .login-form {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 1rem;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
  }

  .tab-nav {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    background: rgba(30, 41, 59, 0.5);
    border-radius: 0.5rem;
    padding: 0.25rem;
  }

  .tab-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: transparent;
    border: none;
    border-radius: 0.375rem;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s ease;
    cursor: pointer;
  }

  .tab-btn:hover {
    color: rgba(255, 255, 255, 0.8);
  }

  .tab-btn.active {
    background: rgba(139, 92, 246, 0.2);
    color: white;
  }

  .error-alert {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 0.5rem;
    color: #FCA5A5;
    font-size: 0.875rem;
    margin-bottom: 1rem;
  }

  .social-login {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .social-buttons {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .social-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 0.875rem 1rem;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 0.5rem;
    color: white;
    font-weight: 500;
    transition: all 0.2s ease;
    cursor: pointer;
  }

  .social-btn:hover:not(:disabled) {
    background: rgba(30, 41, 59, 0.9);
    border-color: #8B5CF6;
    transform: translateY(-1px);
  }

  .social-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  .social-btn.google:hover:not(:disabled) {
    border-color: #DB4437;
  }

  .social-btn.github:hover:not(:disabled) {
    border-color: #333;
  }

  .social-btn.microsoft:hover:not(:disabled) {
    border-color: #0078D4;
  }

  .social-note {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.6);
  }

  .email-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-group label {
    font-size: 0.875rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.9);
  }

  .input-wrapper {
    position: relative;
  }

  .form-input {
    width: 100%;
    padding: 0.875rem 2.5rem 0.875rem 1rem;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 0.5rem;
    color: white;
    font-size: 0.875rem;
    transition: all 0.2s ease;
  }

  .form-input:focus {
    outline: none;
    border-color: #8B5CF6;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  }

  .form-input.error {
    border-color: #EF4444;
  }

  .form-input::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }

  .input-icon {
    position: absolute;
    right: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    color: rgba(255, 255, 255, 0.4);
    width: 1rem;
    height: 1rem;
  }

  .field-error {
    font-size: 0.75rem;
    color: #FCA5A5;
  }

  .login-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.875rem 1rem;
    background: linear-gradient(135deg, #8B5CF6, #EC4899);
    border: none;
    border-radius: 0.5rem;
    color: white;
    font-weight: 600;
    transition: all 0.2s ease;
    cursor: pointer;
    margin-top: 0.5rem;
  }

  .login-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 10px 25px -5px rgba(139, 92, 246, 0.4);
  }

  .login-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .signup-link {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 1rem;
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.6);
  }

  .link-btn {
    background: none;
    border: none;
    color: #8B5CF6;
    font-weight: 500;
    cursor: pointer;
    transition: color 0.2s ease;
  }

  .link-btn:hover {
    color: #EC4899;
    text-decoration: underline;
  }

  .security-notice {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(139, 92, 246, 0.2);
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.5);
  }
</style>