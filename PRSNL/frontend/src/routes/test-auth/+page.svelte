<script lang="ts">
  import { authStore, isAuthenticated } from '$lib/stores/auth';
  import { onMount } from 'svelte';
  
  let authState: any = {};
  let localStorageData: any = {};
  let apiTestResult: string = '';
  
  onMount(() => {
    // Subscribe to auth store
    const unsubscribe = authStore.subscribe(state => {
      authState = state;
    });
    
    // Check localStorage
    localStorageData = {
      accessToken: localStorage.getItem('prsnl-access-token')?.substring(0, 20) + '...',
      refreshToken: localStorage.getItem('prsnl-refresh-token')?.substring(0, 20) + '...',
      user: localStorage.getItem('prsnl-user')
    };
    
    return unsubscribe;
  });
  
  async function testApiCall() {
    try {
      apiTestResult = 'Testing API call...';
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${authState.accessToken}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        apiTestResult = `✅ API call successful! User: ${data.email}`;
      } else {
        apiTestResult = `❌ API call failed: ${response.status} ${response.statusText}`;
      }
    } catch (error) {
      apiTestResult = `❌ Error: ${error}`;
    }
  }
  
  async function testRefresh() {
    try {
      apiTestResult = 'Testing token refresh...';
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: authState.refreshToken
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        apiTestResult = `✅ Refresh successful! New token: ${data.access_token.substring(0, 20)}...`;
      } else {
        const error = await response.json();
        apiTestResult = `❌ Refresh failed: ${response.status} - ${error.detail}`;
      }
    } catch (error) {
      apiTestResult = `❌ Error: ${error}`;
    }
  }
</script>

<div class="container mx-auto p-8">
  <h1 class="text-2xl font-bold mb-4">Auth Debug Page</h1>
  
  <div class="space-y-4">
    <div class="p-4 bg-gray-100 rounded">
      <h2 class="font-bold mb-2">Auth Store State</h2>
      <pre class="text-sm">{JSON.stringify(authState, null, 2)}</pre>
    </div>
    
    <div class="p-4 bg-gray-100 rounded">
      <h2 class="font-bold mb-2">LocalStorage</h2>
      <pre class="text-sm">{JSON.stringify(localStorageData, null, 2)}</pre>
    </div>
    
    <div class="p-4 bg-gray-100 rounded">
      <h2 class="font-bold mb-2">API Test</h2>
      <div class="space-x-2 mb-2">
        <button 
          class="px-4 py-2 bg-blue-500 text-white rounded"
          on:click={testApiCall}
        >
          Test /api/auth/me
        </button>
        <button 
          class="px-4 py-2 bg-green-500 text-white rounded"
          on:click={testRefresh}
        >
          Test Token Refresh
        </button>
      </div>
      {#if apiTestResult}
        <pre class="text-sm mt-2">{apiTestResult}</pre>
      {/if}
    </div>
  </div>
</div>