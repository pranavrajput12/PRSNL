<script lang="ts">
  import { onMount } from 'svelte';
  import { authActions, isAuthenticated, currentUser, authError, authSource } from '$lib/stores/unified-auth';
  import Icon from '$lib/components/Icon.svelte';

  let debugInfo = {
    keycloakConfig: null,
    fusionAuthConfig: null,
    currentState: null,
    browserInfo: null,
    testResults: {}
  };

  let isRunningTests = false;

  onMount(async () => {
    // Get debug information
    debugInfo.currentState = authActions.getState();
    debugInfo.browserInfo = {
      userAgent: navigator.userAgent,
      location: window.location.href,
      localStorage: {
        authToken: localStorage.getItem('prsnl_auth_token') ? 'present' : 'not found',
        authSource: localStorage.getItem('prsnl_auth_source') || 'not set'
      }
    };
  });

  async function testKeycloakConnection() {
    isRunningTests = true;
    try {
      const response = await fetch('http://localhost:8080/realms/prsnl');
      const data = await response.json();
      debugInfo.testResults.keycloak = {
        status: response.ok ? 'connected' : 'failed',
        data: data
      };
    } catch (error) {
      debugInfo.testResults.keycloak = {
        status: 'error',
        error: error.message
      };
    }
    isRunningTests = false;
  }

  async function testFusionAuthConnection() {
    isRunningTests = true;
    try {
      const response = await fetch('http://localhost:9011/api/status');
      debugInfo.testResults.fusionauth = {
        status: response.ok ? 'connected' : 'failed',
        statusCode: response.status
      };
    } catch (error) {
      debugInfo.testResults.fusionauth = {
        status: 'error',
        error: error.message
      };
    }
    isRunningTests = false;
  }

  async function testPRSNLBackend() {
    isRunningTests = true;
    try {
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      debugInfo.testResults.backend = {
        status: response.ok ? 'connected' : 'failed',
        data: data
      };
    } catch (error) {
      debugInfo.testResults.backend = {
        status: 'error',
        error: error.message
      };
    }
    isRunningTests = false;
  }

  async function testGoogleLogin() {
    try {
      await authActions.loginWithGoogle();
    } catch (error) {
      console.error('Google login test failed:', error);
    }
  }

  async function clearAuthState() {
    localStorage.removeItem('prsnl_auth_token');
    localStorage.removeItem('prsnl_auth_source');
    localStorage.removeItem('prsnl_refresh_token');
    authActions.clearError();
    location.reload();
  }
</script>

<svelte:head>
  <title>Auth Debug - PRSNL</title>
</svelte:head>

<div class="min-h-screen bg-slate-900 p-8">
  <div class="max-w-4xl mx-auto">
    <div class="flex items-center space-x-4 mb-8">
      <Icon name="bug" class="w-8 h-8 text-purple-500" />
      <h1 class="text-3xl font-bold text-white">Authentication Debug</h1>
    </div>

    <!-- Current Auth State -->
    <div class="bg-slate-800 rounded-lg p-6 mb-6">
      <h2 class="text-xl font-semibold text-white mb-4">Current Authentication State</h2>
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span class="text-slate-400">Authenticated:</span>
          <span class="text-white ml-2">{$isAuthenticated ? '✅ Yes' : '❌ No'}</span>
        </div>
        <div>
          <span class="text-slate-400">Auth Source:</span>
          <span class="text-white ml-2">{$authSource || 'None'}</span>
        </div>
        <div>
          <span class="text-slate-400">User:</span>
          <span class="text-white ml-2">{$currentUser?.email || 'No user'}</span>
        </div>
        <div>
          <span class="text-slate-400">Error:</span>
          <span class="text-red-400 ml-2">{$authError || 'None'}</span>
        </div>
      </div>
    </div>

    <!-- Service Tests -->
    <div class="bg-slate-800 rounded-lg p-6 mb-6">
      <h2 class="text-xl font-semibold text-white mb-4">Service Connection Tests</h2>
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <span class="text-white">Keycloak (localhost:8080)</span>
          <div class="flex items-center space-x-2">
            {#if debugInfo.testResults.keycloak}
              <span class="text-sm {debugInfo.testResults.keycloak.status === 'connected' ? 'text-green-400' : 'text-red-400'}">
                {debugInfo.testResults.keycloak.status}
              </span>
            {/if}
            <button 
              on:click={testKeycloakConnection}
              disabled={isRunningTests}
              class="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 disabled:opacity-50"
            >
              Test
            </button>
          </div>
        </div>

        <div class="flex items-center justify-between">
          <span class="text-white">FusionAuth (localhost:9011)</span>
          <div class="flex items-center space-x-2">
            {#if debugInfo.testResults.fusionauth}
              <span class="text-sm {debugInfo.testResults.fusionauth.status === 'connected' ? 'text-green-400' : 'text-red-400'}">
                {debugInfo.testResults.fusionauth.status}
              </span>
            {/if}
            <button 
              on:click={testFusionAuthConnection}
              disabled={isRunningTests}
              class="px-3 py-1 bg-orange-600 text-white rounded text-sm hover:bg-orange-700 disabled:opacity-50"
            >
              Test
            </button>
          </div>
        </div>

        <div class="flex items-center justify-between">
          <span class="text-white">PRSNL Backend (localhost:8000)</span>
          <div class="flex items-center space-x-2">
            {#if debugInfo.testResults.backend}
              <span class="text-sm {debugInfo.testResults.backend.status === 'connected' ? 'text-green-400' : 'text-red-400'}">
                {debugInfo.testResults.backend.status}
              </span>
            {/if}
            <button 
              on:click={testPRSNLBackend}
              disabled={isRunningTests}
              class="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              Test
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Test Actions -->
    <div class="bg-slate-800 rounded-lg p-6 mb-6">
      <h2 class="text-xl font-semibold text-white mb-4">Test Authentication</h2>
      <div class="flex flex-wrap gap-4">
        <button 
          on:click={testGoogleLogin}
          class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Test Google Login
        </button>
        
        <button 
          on:click={() => authActions.loginWithGitHub()}
          class="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-900"
        >
          Test GitHub Login
        </button>
        
        <button 
          on:click={() => authActions.loginWithMicrosoft()}
          class="px-4 py-2 bg-blue-700 text-white rounded hover:bg-blue-800"
        >
          Test Microsoft Login
        </button>
        
        <button 
          on:click={clearAuthState}
          class="px-4 py-2 bg-red-800 text-white rounded hover:bg-red-900"
        >
          Clear Auth State
        </button>
      </div>
    </div>

    <!-- Debug Information -->
    <div class="bg-slate-800 rounded-lg p-6">
      <h2 class="text-xl font-semibold text-white mb-4">Debug Information</h2>
      <pre class="text-xs text-slate-300 bg-slate-900 p-4 rounded overflow-auto max-h-96">
{JSON.stringify(debugInfo, null, 2)}
      </pre>
    </div>

    <!-- Navigation -->
    <div class="mt-8 flex justify-center">
      <a href="/auth/login" class="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
        Back to Login
      </a>
    </div>
  </div>
</div>