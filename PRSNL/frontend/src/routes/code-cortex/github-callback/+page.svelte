<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  
  let status = $state('processing');
  let error = $state('');
  
  onMount(async () => {
    const code = $page.url.searchParams.get('code');
    const state = $page.url.searchParams.get('state');
    
    if (!code || !state) {
      error = 'Invalid OAuth callback parameters';
      status = 'error';
      return;
    }
    
    try {
      // Call the backend OAuth callback endpoint
      const response = await fetch(`/api/github/auth/callback?code=${code}&state=${state}`, {
        method: 'GET',
        credentials: 'include',
        redirect: 'manual' // Don't follow redirects automatically
      });
      
      if (!response.ok && response.status !== 0) {
        const text = await response.text();
        throw new Error(text || 'OAuth authentication failed');
      }
      
      // Success - redirect to CodeMirror page
      status = 'success';
      setTimeout(() => {
        goto('/code-cortex/codemirror');
      }, 1500);
      
    } catch (err) {
      console.error('OAuth callback error:', err);
      error = err.message || 'Authentication failed';
      status = 'error';
    }
  });
</script>

<div class="callback-page">
  <div class="callback-content">
    {#if status === 'processing'}
      <div class="processing">
        <div class="spinner"></div>
        <h2>Connecting to GitHub...</h2>
        <p>Please wait while we complete the authentication process.</p>
      </div>
    {:else if status === 'success'}
      <div class="success">
        <div class="success-icon">✅</div>
        <h2>Successfully Connected!</h2>
        <p>Redirecting you back to CodeMirror...</p>
      </div>
    {:else if status === 'error'}
      <div class="error">
        <div class="error-icon">❌</div>
        <h2>Connection Failed</h2>
        <p>{error}</p>
        <a href="/code-cortex/codemirror" class="back-link">
          Return to CodeMirror
        </a>
      </div>
    {/if}
  </div>
</div>

<style>
  .callback-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }
  
  .callback-content {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 3rem;
    max-width: 500px;
    width: 90%;
    text-align: center;
  }
  
  /* Processing State */
  .processing h2 {
    margin: 1.5rem 0 0.5rem 0;
    color: #60a5fa;
  }
  
  .processing p {
    color: rgba(255, 255, 255, 0.7);
    margin: 0;
  }
  
  .spinner {
    width: 50px;
    height: 50px;
    margin: 0 auto;
    border: 3px solid rgba(255, 255, 255, 0.1);
    border-top-color: #60a5fa;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  
  /* Success State */
  .success-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }
  
  .success h2 {
    margin: 0 0 0.5rem 0;
    color: #22c55e;
  }
  
  .success p {
    color: rgba(255, 255, 255, 0.7);
    margin: 0;
  }
  
  /* Error State */
  .error-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }
  
  .error h2 {
    margin: 0 0 0.5rem 0;
    color: #ef4444;
  }
  
  .error p {
    color: rgba(255, 255, 255, 0.7);
    margin: 0 0 2rem 0;
  }
  
  .back-link {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    background: rgba(96, 165, 250, 0.2);
    border: 1px solid rgba(96, 165, 250, 0.3);
    color: #60a5fa;
    text-decoration: none;
    border-radius: 0.5rem;
    transition: all 0.2s;
  }
  
  .back-link:hover {
    background: rgba(96, 165, 250, 0.3);
    transform: translateY(-1px);
  }
</style>