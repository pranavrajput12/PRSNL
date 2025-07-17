<script lang="ts">
  import { onMount } from 'svelte';
  import { authStore, authActions } from '$lib/stores/auth';
  import { authDebugger } from '$lib/debug-auth';
  
  let authState: any = {};
  let debugLogs: any[] = [];
  let autoRefresh = true;
  
  onMount(() => {
    // Subscribe to auth changes
    const unsubscribe = authStore.subscribe(state => {
      authState = state;
    });
    
    // Auto-refresh logs
    const interval = setInterval(() => {
      if (autoRefresh) {
        refreshLogs();
      }
    }, 1000);
    
    refreshLogs();
    
    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  });
  
  function refreshLogs() {
    debugLogs = authDebugger.getLogs();
  }
  
  function clearLogs() {
    authDebugger.clearLogs();
    refreshLogs();
  }
  
  function exportLogs() {
    const data = authDebugger.exportLogs();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `auth-debug-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
  
  function testApiCall() {
    fetch('/api/tags')
      .then(response => response.json())
      .then(data => console.log('API test result:', data))
      .catch(err => console.error('API test error:', err));
  }
  
  function forceLogout() {
    authActions.logout();
  }
  
  function testRefresh() {
    authActions.refreshToken();
  }
  
  function getLogColor(event: string) {
    if (event.includes('ERROR') || event.includes('FAILED')) return 'text-red-600';
    if (event.includes('SUCCESS')) return 'text-green-600';
    if (event.includes('LOGOUT')) return 'text-orange-600';
    if (event.includes('API_')) return 'text-blue-600';
    return 'text-gray-600';
  }
</script>

<div class="container mx-auto p-4 max-w-6xl">
  <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
    <strong>🔍 Authentication Debug Dashboard</strong>
    <p>This page shows real-time authentication debugging information to help identify logout issues.</p>
  </div>
  
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Current Auth State -->
    <div class="bg-white rounded-lg shadow p-6">
      <h2 class="text-xl font-bold mb-4">Current Auth State</h2>
      <div class="space-y-2 text-sm">
        <div>
          <strong>Authenticated:</strong> 
          <span class={authState.isAuthenticated ? 'text-green-600' : 'text-red-600'}>
            {authState.isAuthenticated ? '✅ YES' : '❌ NO'}
          </span>
        </div>
        <div>
          <strong>User:</strong> 
          {authState.user?.email || 'None'}
        </div>
        <div>
          <strong>Access Token:</strong> 
          {authState.accessToken ? `${authState.accessToken.substring(0, 20)}...` : 'None'}
        </div>
        <div>
          <strong>Refresh Token:</strong> 
          {authState.refreshToken ? `${authState.refreshToken.substring(0, 20)}...` : 'None'}
        </div>
        <div>
          <strong>Loading:</strong> 
          {authState.isLoading ? 'Yes' : 'No'}
        </div>
        <div>
          <strong>Error:</strong> 
          {authState.error || 'None'}
        </div>
        <div>
          <strong>Current URL:</strong> 
          {typeof window !== 'undefined' ? window.location.href : 'N/A'}
        </div>
      </div>
      
      <div class="mt-4 space-x-2">
        <button 
          class="bg-blue-500 text-white px-3 py-1 rounded text-sm"
          on:click={testApiCall}
        >
          Test API Call
        </button>
        <button 
          class="bg-green-500 text-white px-3 py-1 rounded text-sm"
          on:click={testRefresh}
        >
          Test Refresh
        </button>
        <button 
          class="bg-red-500 text-white px-3 py-1 rounded text-sm"
          on:click={forceLogout}
        >
          Force Logout
        </button>
      </div>
    </div>
    
    <!-- Debug Logs -->
    <div class="bg-white rounded-lg shadow p-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-bold">Debug Logs ({debugLogs.length})</h2>
        <div class="space-x-2">
          <label class="text-sm">
            <input 
              type="checkbox" 
              bind:checked={autoRefresh}
              class="mr-1"
            />
            Auto-refresh
          </label>
          <button 
            class="bg-gray-500 text-white px-3 py-1 rounded text-sm"
            on:click={refreshLogs}
          >
            Refresh
          </button>
          <button 
            class="bg-orange-500 text-white px-3 py-1 rounded text-sm"
            on:click={clearLogs}
          >
            Clear
          </button>
          <button 
            class="bg-purple-500 text-white px-3 py-1 rounded text-sm"
            on:click={exportLogs}
          >
            Export
          </button>
        </div>
      </div>
      
      <div class="max-h-96 overflow-y-auto space-y-2">
        {#each debugLogs as log}
          <div class="border-l-4 border-blue-200 pl-3 py-2 bg-gray-50 text-xs">
            <div class="flex justify-between items-start">
              <span class={getLogColor(log.event) + ' font-mono font-bold'}>
                {log.event}
              </span>
              <span class="text-gray-500 text-xs">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div class="text-gray-700 mt-1">
              <pre class="whitespace-pre-wrap">{JSON.stringify(log.details, null, 2)}</pre>
            </div>
            {#if log.error}
              <div class="text-red-600 mt-1">
                <strong>Error:</strong> {log.error}
              </div>
            {/if}
            {#if log.url}
              <div class="text-blue-600 mt-1 text-xs">
                <strong>URL:</strong> {log.url}
              </div>
            {/if}
          </div>
        {/each}
        
        {#if debugLogs.length === 0}
          <div class="text-gray-500 text-center py-8">
            No debug logs yet. Navigate around the app to see authentication events.
          </div>
        {/if}
      </div>
    </div>
  </div>
  
  <div class="mt-6 bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
    <strong>💡 How to use:</strong>
    <ol class="list-decimal list-inside mt-2 space-y-1">
      <li>Keep this page open in a separate tab</li>
      <li>Navigate to other pages in your main tab</li>
      <li>Watch the logs to see exactly when and why logout happens</li>
      <li>Use the "Test API Call" button to trigger API requests</li>
      <li>Export logs to share with developers</li>
    </ol>
  </div>
</div>

<style>
  pre {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 11px;
    line-height: 1.4;
  }
</style>