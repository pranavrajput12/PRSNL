<script lang="ts">
  import { notifications, removeNotification } from '$lib/stores/app';
  import { fly } from 'svelte/transition';
  import { flip } from 'svelte/animate';
</script>

<div class="notifications-container">
  {#each $notifications as notification (notification.id)}
    <div 
      class="notification {notification.type}" 
      transition:fly={{ y: -30, duration: 300 }}
      animate:flip={{ duration: 300 }}
    >
      <div class="notification-content">
        <div class="notification-icon">
          {#if notification.type === 'success'}
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          {:else if notification.type === 'error'}
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
          {:else if notification.type === 'warning'}
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          {:else}
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          {/if}
        </div>
        <div class="notification-message">{notification.message}</div>
      </div>
      <button 
        class="notification-close" 
        on:click={() => removeNotification(notification.id)}
        aria-label="Close notification"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
  {/each}
</div>

<style>
  .notifications-container {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: 400px;
    pointer-events: none;
  }
  
  .notification {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    border-radius: var(--radius);
    background: var(--bg-secondary);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    pointer-events: auto;
    border-left: 4px solid;
  }
  
  .notification.success {
    border-color: var(--success);
  }
  
  .notification.error {
    border-color: var(--error);
  }
  
  .notification.warning {
    border-color: var(--warning);
  }
  
  .notification.info {
    border-color: var(--info);
  }
  
  .notification-content {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .notification-icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .notification.success .notification-icon {
    color: var(--success);
  }
  
  .notification.error .notification-icon {
    color: var(--error);
  }
  
  .notification.warning .notification-icon {
    color: var(--warning);
  }
  
  .notification.info .notification-icon {
    color: var(--info);
  }
  
  .notification-message {
    font-size: 0.875rem;
    color: var(--text-primary);
  }
  
  .notification-close {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-left: 0.5rem;
    border-radius: 50%;
    transition: background-color 0.2s;
  }
  
  .notification-close:hover {
    background-color: var(--bg-tertiary);
  }
</style>
