<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Notifications from '$lib/components/Notifications.svelte';
  import Icon from '$lib/components/Icon.svelte';
  import ErrorBoundary from '$lib/components/ErrorBoundary.svelte';
  import AnimatedToast from '$lib/components/AnimatedToast.svelte';
  import { preferences } from '$lib/stores/app';
  import { goto } from '$app/navigation';
  
  let toasts = [];
  let toastId = 0;
  let sidebarCollapsed = false;
  
  function showToast(type, message) {
    const id = toastId++;
    toasts = [...toasts, { id, type, message }];
  }
  
  function removeToast(id) {
    toasts = toasts.filter(t => t.id !== id);
  }
  
  function toggleSidebar() {
    sidebarCollapsed = !sidebarCollapsed;
    // Save preference to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebarCollapsed', sidebarCollapsed.toString());
    }
  }
  
  // Global keyboard navigation
  onMount(() => {
    // Load sidebar preference
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('sidebarCollapsed');
      if (saved !== null) {
        sidebarCollapsed = saved === 'true';
      }
    }
    const handleKeydown = (e) => {
      // CMD/CTRL + K for search (focus on dashboard search)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        window.location.href = '/';
        // Focus on search input after navigation
        setTimeout(() => {
          const searchInput = document.querySelector('.search-input');
          if (searchInput) searchInput.focus();
        }, 100);
      }
      // CMD/CTRL + N for new capture
      if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
        e.preventDefault();
        window.location.href = '/capture';
      }
      // CMD/CTRL + T for timeline
      if ((e.metaKey || e.ctrlKey) && e.key === 't') {
        e.preventDefault();
        window.location.href = '/timeline';
      }
      // CMD/CTRL + H for home
      if ((e.metaKey || e.ctrlKey) && e.key === 'h') {
        e.preventDefault();
        window.location.href = '/';
      }
      // CMD/CTRL + I for insights
      if ((e.metaKey || e.ctrlKey) && e.key === 'i') {
        e.preventDefault();
        window.location.href = '/insights';
      }
      // CMD/CTRL + B for toggle sidebar
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault();
        toggleSidebar();
      }
    };
    
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  });
</script>

<div class="app-layout">
  <aside class="sidebar glass {sidebarCollapsed ? 'collapsed' : ''}">
    <div class="sidebar-header">
      <a href="/" class="logo">
        <div class="logo-icon">
          <Icon name="sparkles" size="medium" color="var(--accent)" />
        </div>
        {#if !sidebarCollapsed}
          <span class="red-gradient-text">PRSNL</span>
        {/if}
      </a>
      
      <button class="sidebar-toggle" on:click={toggleSidebar} aria-label="Toggle sidebar">
        <Icon name={sidebarCollapsed ? 'chevron-right' : 'chevron-left'} size="small" />
      </button>
    </div>
    
    <nav class="sidebar-nav">
      <a href="/" class="nav-link {$page.url.pathname === '/' ? 'active' : ''}" title="Home">
        <Icon name="home" size="small" />
        {#if !sidebarCollapsed}
          <span>Home</span>
          <span class="keyboard-hint">⌘H</span>
        {/if}
      </a>
      
      <a href="/capture" class="nav-link {$page.url.pathname === '/capture' ? 'active' : ''}" title="Capture">
        <Icon name="plus" size="small" />
        {#if !sidebarCollapsed}
          <span>Capture</span>
          <span class="keyboard-hint">⌘N</span>
        {/if}
      </a>
      
      <a href="/timeline" class="nav-link {$page.url.pathname === '/timeline' ? 'active' : ''}" title="Timeline">
        <Icon name="clock" size="small" />
        {#if !sidebarCollapsed}
          <span>Timeline</span>
          <span class="keyboard-hint">⌘T</span>
        {/if}
      </a>
      
      <a href="/insights" class="nav-link {$page.url.pathname === '/insights' ? 'active' : ''}" title="Insights">
        <Icon name="sparkles" size="small" />
        {#if !sidebarCollapsed}
          <span>Insights</span>
          <span class="keyboard-hint">⌘I</span>
        {/if}
      </a>
      
      <a href="/chat" class="nav-link {$page.url.pathname === '/chat' ? 'active' : ''}" title="Chat">
        <Icon name="message-circle" size="small" />
        {#if !sidebarCollapsed}
          <span>Chat</span>
        {/if}
      </a>
      
      <a href="/videos" class="nav-link {$page.url.pathname === '/videos' ? 'active' : ''}" title="Videos">
        <Icon name="video" size="small" />
        {#if !sidebarCollapsed}
          <span>Videos</span>
        {/if}
      </a>
    </nav>
    
    <div class="sidebar-footer">
      <a href="/settings" class="nav-link {$page.url.pathname === '/settings' ? 'active' : ''}" title="Settings">
        <Icon name="settings" size="small" />
        {#if !sidebarCollapsed}
          <span>Settings</span>
        {/if}
      </a>
    </div>
  </aside>

  <ErrorBoundary fallback="full">
    <main class="main-content {sidebarCollapsed ? 'sidebar-collapsed' : ''}">
      <slot />
    </main>

    <Notifications />
    
    <!-- Toast notifications -->
    {#each toasts as toast (toast.id)}
      <AnimatedToast
        type={toast.type}
        message={toast.message}
        onClose={() => removeToast(toast.id)}
      />
    {/each}
  </ErrorBoundary>
</div>

<style>
  .app-layout {
    display: flex;
    height: 100vh;
    width: 100%;
    overflow: hidden;
  }
  
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    width: 240px;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    transition: all var(--transition-base) cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 100;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  .sidebar.collapsed {
    width: 70px;
  }
  
  .sidebar-header {
    padding: 1.5rem 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }
  
  .logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-weight: 800;
    text-decoration: none;
    transition: all var(--transition-base);
    white-space: nowrap;
    overflow: hidden;
  }
  
  .logo:hover {
    transform: scale(1.05);
  }
  
  .logo-icon {
    width: 36px;
    height: 36px;
    min-width: 36px;
    background: rgba(74, 158, 255, 0.1);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-base);
  }
  
  .logo:hover .logo-icon {
    background: rgba(74, 158, 255, 0.2);
    transform: rotate(5deg);
  }
  
  .sidebar-toggle {
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-base);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .sidebar-toggle:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    transform: scale(1.1);
  }
  
  .sidebar-nav {
    flex: 1;
    padding: 1.5rem 0.75rem;
    overflow-y: auto;
    overflow-x: hidden;
  }
  
  .sidebar-footer {
    padding: 1rem 0.75rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .nav-link {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    margin-bottom: 0.25rem;
    color: var(--text-secondary);
    font-weight: 500;
    border-radius: var(--radius);
    transition: all var(--transition-base);
    position: relative;
    overflow: hidden;
    white-space: nowrap;
  }
  
  .sidebar.collapsed .nav-link {
    justify-content: center;
    padding: 0.75rem;
  }
  
  .nav-link::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(74, 158, 255, 0.2), transparent);
    transition: left var(--transition-slow);
  }
  
  .nav-link:hover::before {
    left: 0;
  }
  
  .nav-link:hover {
    color: var(--text-primary);
    background: rgba(74, 158, 255, 0.05);
    transform: translateX(2px);
  }
  
  .sidebar.collapsed .nav-link:hover {
    transform: none;
  }
  
  .nav-link.active {
    color: var(--accent);
    background: rgba(74, 158, 255, 0.1);
    font-weight: 600;
    box-shadow: inset 3px 0 0 var(--accent);
  }
  
  .nav-link .keyboard-hint {
    margin-left: auto;
    font-size: 0.75rem;
    opacity: 0.5;
    transition: all var(--transition-base);
  }
  
  .nav-link:hover .keyboard-hint {
    opacity: 0.8;
  }
  
  .main-content {
    flex: 1;
    margin-left: 240px;
    min-height: 100vh;
    overflow-y: auto;
    transition: margin-left var(--transition-base) cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeIn var(--transition-base) ease-out;
  }
  
  .main-content.sidebar-collapsed {
    margin-left: 70px;
  }
  
  .red-gradient-text {
    background: linear-gradient(135deg, var(--man-united-red), #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  /* Scrollbar styling for sidebar */
  .sidebar-nav::-webkit-scrollbar {
    width: 4px;
  }
  
  .sidebar-nav::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .sidebar-nav::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
  }
  
  .sidebar-nav::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
  }
  
  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .sidebar {
      transform: translateX(-100%);
    }
    
    .sidebar:not(.collapsed) {
      transform: translateX(0);
    }
    
    .main-content {
      margin-left: 0;
    }
    
    .main-content.sidebar-collapsed {
      margin-left: 0;
    }
    
    /* Add mobile menu button when needed */
  }
  
  /* Animations */
  @keyframes slideInFromLeft {
    from {
      transform: translateX(-20px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  .nav-link {
    animation: slideInFromLeft var(--transition-base) ease-out;
    animation-fill-mode: both;
  }
  
  .nav-link:nth-child(1) { animation-delay: 0.05s; }
  .nav-link:nth-child(2) { animation-delay: 0.1s; }
  .nav-link:nth-child(3) { animation-delay: 0.15s; }
  .nav-link:nth-child(4) { animation-delay: 0.2s; }
  .nav-link:nth-child(5) { animation-delay: 0.25s; }
  .nav-link:nth-child(6) { animation-delay: 0.3s; }
</style>