<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { authActions } from '$lib/stores/unified-auth';
  import Icon from '$lib/components/Icon.svelte';

  let password = '';
  let confirmPassword = '';
  let loading = false;
  let error = '';
  let success = false;
  let token = '';

  onMount(() => {
    // Get token from URL query params
    token = $page.url.searchParams.get('token') || '';
    if (!token) {
      error = 'Invalid or missing reset token';
    }
  });

  async function handleSubmit(e: Event) {
    e.preventDefault();
    error = '';

    if (!password) {
      error = 'Password is required';
      return;
    }

    if (password !== confirmPassword) {
      error = 'Passwords do not match';
      return;
    }

    if (password.length < 8) {
      error = 'Password must be at least 8 characters';
      return;
    }

    loading = true;

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token,
          new_password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to reset password');
      }

      success = true;
      setTimeout(() => {
        goto('/auth/login');
      }, 3000);
    } catch (err) {
      console.error('Password reset failed:', err);
      error = err instanceof Error ? err.message : 'Failed to reset password';
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-black via-gray-900 to-black p-4">
  <div class="w-full max-w-md">
    <!-- Logo/Title -->
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold text-white mb-2">
        Reset Password
      </h1>
      <p class="text-gray-400">
        Enter your new password below
      </p>
    </div>

    <!-- Reset Form -->
    <div class="glass-card p-8">
      {#if success}
        <div class="text-center">
          <div class="mb-4">
            <Icon name="check-circle" class="w-16 h-16 text-green-500 mx-auto" />
          </div>
          <h2 class="text-xl font-semibold text-white mb-2">
            Password Reset Successful!
          </h2>
          <p class="text-gray-400 mb-4">
            Your password has been reset. Redirecting to login...
          </p>
        </div>
      {:else if !token}
        <div class="text-center">
          <div class="mb-4">
            <Icon name="x-circle" class="w-16 h-16 text-red-500 mx-auto" />
          </div>
          <h2 class="text-xl font-semibold text-white mb-2">
            Invalid Reset Link
          </h2>
          <p class="text-gray-400 mb-4">
            This password reset link is invalid or has expired.
          </p>
          <a
            href="/auth/login"
            class="inline-block px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Back to Login
          </a>
        </div>
      {:else}
        <form on:submit={handleSubmit} class="space-y-6">
          {#if error}
            <div class="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500">
              {error}
            </div>
          {/if}

          <div>
            <label for="password" class="block text-sm font-medium text-gray-300 mb-2">
              New Password
            </label>
            <input
              id="password"
              type="password"
              bind:value={password}
              class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-transparent"
              placeholder="Enter new password"
              disabled={loading}
              required
              minlength="8"
            />
          </div>

          <div>
            <label for="confirmPassword" class="block text-sm font-medium text-gray-300 mb-2">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              bind:value={confirmPassword}
              class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-transparent"
              placeholder="Confirm new password"
              disabled={loading}
              required
              minlength="8"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            class="w-full py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>

          <div class="text-center">
            <a
              href="/auth/login"
              class="text-gray-400 hover:text-white transition-colors"
            >
              Back to Login
            </a>
          </div>
        </form>
      {/if}
    </div>
  </div>
</div>

<style>
  .glass-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  }
</style>