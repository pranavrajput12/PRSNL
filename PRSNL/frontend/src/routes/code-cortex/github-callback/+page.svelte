<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  
  let status = 'Processing...';
  let error = '';
  
  onMount(async () => {
    const code = $page.url.searchParams.get('code');
    const state = $page.url.searchParams.get('state');
    
    if (!code || !state) {
      error = 'Invalid callback parameters';
      return;
    }
    
    try {
      // The backend will handle the callback
      const response = await fetch(`/api/github/auth/callback?code=${code}&state=${state}`);
      
      if (response.redirected) {
        // Follow the redirect
        window.location.href = response.url;
      } else if (!response.ok) {
        const data = await response.json();
        error = data.detail || 'Authentication failed';
      } else {
        // If no redirect, go to Code Cortex
        goto('/code-cortex');
      }
    } catch (err) {
      error = 'Failed to complete authentication';
      console.error('GitHub callback error:', err);
    }
  });
</script>

<div class="callback-container">
  <div class="callback-card">
    <h2>GitHub Authentication</h2>
    
    {#if error}
      <div class="error">
        <p>{error}</p>
        <a href="/code-cortex" class="button">Return to Code Cortex</a>
      </div>
    {:else}
      <div class="processing">
        <div class="spinner"></div>
        <p>{status}</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .callback-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--surface-1);
  }
  
  .callback-card {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 3rem;
    text-align: center;
    max-width: 400px;
    width: 90%;
  }
  
  h2 {
    color: var(--text-primary);
    margin-bottom: 2rem;
  }
  
  .processing {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
  
  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .error {
    color: var(--error);
  }
  
  .error p {
    margin-bottom: 1.5rem;
  }
  
  .button {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    background: var(--primary);
    color: white;
    text-decoration: none;
    border-radius: 6px;
    font-weight: 500;
    transition: opacity 0.2s;
  }
  
  .button:hover {
    opacity: 0.9;
  }
</style>