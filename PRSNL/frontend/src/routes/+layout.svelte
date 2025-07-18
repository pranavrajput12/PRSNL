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
  import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
  import { currentUser, isAuthenticated, authActions } from '$lib/stores/unified-auth';
  import FloatingChat from '$lib/components/FloatingChat.svelte';
  
  export let data;

  // Create QueryClient instance
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5, // 5 minutes
        gcTime: 1000 * 60 * 10, // 10 minutes
        refetchOnWindowFocus: true,
        retry: 1,
      },
    },
  });

  let toasts = [];
  let toastId = 0;
  let sidebarCollapsed = false;
  let sidebarMorphed = false;
  let mobileMenuOpen = false;

  function showToast(type, message) {
    const id = toastId++;
    toasts = [...toasts, { id, type, message }];
  }

  function removeToast(id) {
    toasts = toasts.filter((t) => t.id !== id);
  }

  function toggleSidebar() {
    sidebarCollapsed = !sidebarCollapsed;
    // Save preference to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebarCollapsed', sidebarCollapsed.toString());
    }
  }

  function toggleMorph() {
    sidebarMorphed = !sidebarMorphed;
    // Save preference to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebarMorphed', sidebarMorphed.toString());
    }
  }

  function toggleMobileMenu() {
    mobileMenuOpen = !mobileMenuOpen;
  }

  // Global keyboard navigation
  onMount(() => {
    // Load sidebar preferences
    if (typeof window !== 'undefined') {
      const savedCollapsed = localStorage.getItem('sidebarCollapsed');
      const savedMorphed = localStorage.getItem('sidebarMorphed');
      if (savedCollapsed !== null) {
        sidebarCollapsed = savedCollapsed === 'true';
      }
      if (savedMorphed !== null) {
        sidebarMorphed = savedMorphed === 'true';
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
      // CMD/CTRL + T for thought stream
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
      // CMD/CTRL + D for code cortex
      if ((e.metaKey || e.ctrlKey) && e.key === 'd') {
        e.preventDefault();
        window.location.href = '/code-cortex';
      }
      // CMD/CTRL + E for conversations
      if ((e.metaKey || e.ctrlKey) && e.key === 'e') {
        e.preventDefault();
        window.location.href = '/conversations';
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

<QueryClientProvider client={queryClient}>
  <div class="app-layout {data?.isPublicRoute ? 'auth-layout' : ''}">
    <!-- Universal neural motherboard background for all pages except homepage -->
      <div class="neural-motherboard-bg {$page.url.pathname === '/' ? 'hide-bg' : ''}">
        <div class="pcb-traces"></div>
        <div class="circuit-nodes">
          <div class="node node-1"></div>
          <div class="node node-2"></div>
          <div class="node node-3"></div>
          <div class="node node-4"></div>
        </div>
      </div>

      {#if !data?.isPublicRoute}
    <!-- Mobile Toggle -->
    <button class="mobile-toggle {mobileMenuOpen ? 'active' : ''}" on:click={toggleMobileMenu}>
      <span class="toggle-icon">≡</span>
    </button>

    <!-- Mobile Backdrop -->
    <button 
        class="mobile-backdrop {mobileMenuOpen ? 'show' : ''}" 
        on:click={toggleMobileMenu}
        on:keydown={(e) => e.key === 'Enter' || e.key === ' ' ? toggleMobileMenu() : null}
        aria-label="Close mobile menu"
        tabindex={mobileMenuOpen ? 0 : -1}
    ></button>

    <!-- Innovative Morphing Sidebar -->
    <aside
      class="innovative-sidebar {sidebarMorphed ? 'morphed' : ''} {mobileMenuOpen
        ? 'mobile-open'
        : ''}"
    >
      <div class="sidebar-glow"></div>

      <div class="sidebar-header">
        <div class="header-bg"></div>
        <div class="logo-container">
          <div class="logo-orb">P</div>
          <div class="logo-text">PRSNL</div>
        </div>
      </div>

      <div class="morph-button-container">
        <button class="morph-toggle" on:click={toggleMorph}>
          {sidebarMorphed ? '▶' : '◀'}
        </button>
      </div>

      <nav class="nav-container">
        <!-- Navigation Items -->
        <a href="/" class="nav-item {$page.url.pathname === '/' ? 'active' : ''}">
          <div class="nav-icon"></div>
          <span class="nav-text">Dashboard</span>
          <div class="nav-tooltip">Dashboard</div>
        </a>

        <a href="/capture" class="nav-item {$page.url.pathname === '/capture' ? 'active' : ''}">
          <div class="nav-icon"></div>
          <span class="nav-text">Capture</span>
          <div class="nav-tooltip">Capture</div>
        </a>

        <a href="/timeline" class="nav-item {$page.url.pathname === '/timeline' ? 'active' : ''}">
          <div class="nav-icon"></div>
          <span class="nav-text">Timeline</span>
          <div class="nav-tooltip">Timeline</div>
        </a>

        <!-- TEMPORARILY DISABLED: AI Insights page
        <a href="/insights" class="nav-item {$page.url.pathname === '/insights' ? 'active' : ''}">
          <div class="nav-icon"></div>
          <span class="nav-text">Insights</span>
          <div class="nav-tooltip">Insights</div>
        </a>
        -->

        <a href="/chat" class="nav-item {$page.url.pathname === '/chat' ? 'active' : ''}">
          <div class="nav-icon"></div>
          <span class="nav-text">Assistant</span>
          <div class="nav-tooltip">Assistant</div>
        </a>

        <a href="/videos" class="nav-item {$page.url.pathname === '/videos' ? 'active' : ''}">
          <div class="nav-icon"></div>
          <span class="nav-text">Visual Cortex</span>
          <div class="nav-tooltip">Visual Cortex</div>
        </a>

        <a
          href="/conversations"
          class="nav-item {$page.url.pathname.startsWith('/conversations') ? 'active' : ''}"
        >
          <div class="nav-icon"></div>
          <span class="nav-text">Conversations</span>
          <div class="nav-tooltip">Conversations</div>
        </a>

        <a
          href="/code-cortex"
          class="nav-item {$page.url.pathname.startsWith('/code-cortex') ? 'active' : ''}"
        >
          <div class="nav-icon"></div>
          <span class="nav-text">Code Cortex</span>
          <div class="nav-tooltip">Code Cortex</div>
        </a>

        <a href="/import" class="nav-item {$page.url.pathname === '/import' ? 'active' : ''}">
          <div class="nav-icon"></div>
          <span class="nav-text">Knowledge Sync</span>
          <div class="nav-tooltip">Knowledge Sync</div>
        </a>
      </nav>

      <!-- User Authentication Section -->
      <div class="user-auth-section">
        {#if $isAuthenticated && $currentUser}
          <div class="user-profile">
            <div class="user-avatar">
              {$currentUser.firstName ? $currentUser.firstName.charAt(0).toUpperCase() : $currentUser.email.charAt(0).toUpperCase()}
            </div>
            <div class="user-info">
              <div class="user-name">
                {$currentUser.firstName && $currentUser.lastName 
                  ? `${$currentUser.firstName} ${$currentUser.lastName}` 
                  : $currentUser.firstName || $currentUser.email}
              </div>
              <div class="user-type">{$currentUser.source}</div>
              {#if !$currentUser.isEmailVerified}
                <div class="verification-status">Email not verified</div>
              {/if}
            </div>
          </div>
          <div class="auth-actions">
            <a href="/profile" class="auth-link">
              <Icon name="user" class="w-4 h-4" />
              <span>Profile</span>
            </a>
            <a href="/settings" class="auth-link">
              <Icon name="settings" class="w-4 h-4" />
              <span>Settings</span>
            </a>
            <button on:click={() => authActions.logout()} class="auth-link logout-btn">
              <Icon name="log-out" class="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        {:else}
          <div class="auth-prompt">
            <a href="/auth/login" class="auth-link primary">
              <Icon name="log-in" class="w-4 h-4" />
              <span>Sign In</span>
            </a>
            <a href="/auth/signup" class="auth-link">
              <Icon name="user-plus" class="w-4 h-4" />
              <span>Sign Up</span>
            </a>
          </div>
        {/if}
      </div>
    </aside>
    {/if}

    <ErrorBoundary fallback="full">
      <main class="main-content {sidebarCollapsed ? 'sidebar-collapsed' : ''} {data?.isPublicRoute ? 'auth-page' : ''}">
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
</QueryClientProvider>

<style>
  /* Design Language Bible CSS Variables */
  :root {
    /* Core Brand Colors */
    --man-united-red: #dc143c;
    --accent-red: #dc143c;
    --accent-red-hover: #b91c3c;
    --accent-red-dim: #991b1b;

    /* Background Colors */
    --bg-primary: #0a0a0a;
    --bg-secondary: #1a1a1a;
    --bg-tertiary: #2a2a2a;

    /* Text Colors */
    --text-primary: #e0e0e0;
    --text-secondary: #a0a0a0;
    --text-muted: #666;

    /* Glass/Transparency Effects */
    --glass-light: rgba(255, 255, 255, 0.1);
    --glass-medium: rgba(255, 255, 255, 0.05);
    --glass-dark: rgba(0, 0, 0, 0.3);

    /* Neural Circuit Colors */
    --neural-green: #00ff64;

    /* Typography */
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-display: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;

    /* Transitions */
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);

    /* Border Radius */
    --radius-sm: 8px;
    --radius: 12px;
    --radius-lg: 16px;
  }

  .app-layout {
    display: flex;
    height: 100vh;
    width: 100%;
    overflow: hidden;
    background: transparent;
  }

  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    width: 420px;
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.95), rgba(42, 42, 42, 0.95));
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    border-right: 2px solid rgba(0, 255, 100, 0.3);
    transition: all var(--transition-base) cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 10;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    overflow: hidden;
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
    width: 44px;
    height: 44px;
    min-width: 44px;
    background: radial-gradient(circle, rgba(220, 20, 60, 0.1), rgba(220, 20, 60, 0.05));
    border: 2px solid rgba(220, 20, 60, 0.2);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-base);
    position: relative;
    overflow: hidden;
  }

  .logo-icon::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(
      45deg,
      var(--brand-accent),
      var(--highlight),
      var(--error),
      var(--brand-hover)
    );
    border-radius: 12px;
    z-index: -1;
    opacity: 0;
    transition: opacity var(--transition-base);
  }

  .logo:hover .logo-icon {
    background: rgba(220, 20, 60, 0.15);
    transform: rotate(3deg) scale(1.05);
    box-shadow: 0 8px 24px rgba(220, 20, 60, 0.3);
  }

  .logo:hover .logo-icon::before {
    opacity: 0.3;
  }

  /* Brain Logo Styling */
  .brain-logo-center {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    padding: 1rem 0 0.5rem 0;
  }

  .brain-circuit-container {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
    transition: all 0.3s ease;
  }

  .brain-circuits {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 280px;
    height: 280px;
    pointer-events: none;
    z-index: 0;
    will-change: transform, opacity;
  }

  .brain-circuits.collapsed {
    width: 200px;
    height: 200px;
  }

  .brain-circuit {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 120px;
    height: 2px;
    background: linear-gradient(90deg, rgba(0, 255, 136, 0.8), rgba(0, 255, 136, 0.1), transparent);
    transform-origin: 0% 50%;
    opacity: 0.6;
    animation: circuit-pulse 3s ease-in-out infinite;
    will-change: transform, opacity, background;
    backface-visibility: hidden;
    perspective: 1000px;
  }

  .brain-circuit-1 {
    transform: translate(-50%, -50%) rotate(0deg);
    animation-delay: 0s;
  }

  .brain-circuit-2 {
    transform: translate(-50%, -50%) rotate(60deg);
    animation-delay: 0.5s;
  }

  .brain-circuit-3 {
    transform: translate(-50%, -50%) rotate(120deg);
    animation-delay: 1s;
  }

  .brain-circuit-4 {
    transform: translate(-50%, -50%) rotate(180deg);
    animation-delay: 1.5s;
  }

  .brain-circuit-5 {
    transform: translate(-50%, -50%) rotate(240deg);
    animation-delay: 2s;
  }

  .brain-circuit-6 {
    transform: translate(-50%, -50%) rotate(300deg);
    animation-delay: 2.5s;
  }

  /* Hover state with specific rotations for fast animation */
  .brain-circuit-container:hover .brain-circuit-1 {
    animation: circuit-pulse-fast-0 1.5s ease-in-out infinite;
  }

  .brain-circuit-container:hover .brain-circuit-2 {
    animation: circuit-pulse-fast-60 1.5s ease-in-out infinite;
  }

  .brain-circuit-container:hover .brain-circuit-3 {
    animation: circuit-pulse-fast-120 1.5s ease-in-out infinite;
  }

  .brain-circuit-container:hover .brain-circuit-4 {
    animation: circuit-pulse-fast-180 1.5s ease-in-out infinite;
  }

  .brain-circuit-container:hover .brain-circuit-5 {
    animation: circuit-pulse-fast-240 1.5s ease-in-out infinite;
  }

  .brain-circuit-container:hover .brain-circuit-6 {
    animation: circuit-pulse-fast-300 1.5s ease-in-out infinite;
  }

  /* Collapsed state circuits */
  .brain-circuits.collapsed .brain-circuit {
    width: 80px;
  }

  /* Dot Matrix Text Styling */
  .dot-matrix-text {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin-top: 20px;
    z-index: 2;
    position: relative;
  }

  .dot-matrix-text.collapsed {
    gap: 4px;
    margin-top: 12px;
  }

  .dot-matrix-letter {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    grid-template-rows: repeat(7, 1fr);
    gap: 2px;
    width: 30px;
    height: 42px;
  }

  .dot-matrix-text.collapsed .dot-matrix-letter {
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(5, 1fr);
    gap: 1px;
    width: 20px;
    height: 25px;
  }

  .dot {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--success);
    animation: dot-wave 3s ease-in-out infinite;
    will-change: background-color;
  }

  .dot-matrix-text.collapsed .dot {
    width: 3px;
    height: 3px;
  }

  .dot.empty {
    background: transparent;
    animation: none;
  }

  /* Wave animation delays - color sweeps P→R→S→N→L */
  .letter-p .dot {
    animation-delay: 0s;
  }
  .letter-r .dot {
    animation-delay: 0.6s;
  }
  .letter-s .dot {
    animation-delay: 1.2s;
  }
  .letter-n .dot {
    animation-delay: 1.8s;
  }
  .letter-l .dot {
    animation-delay: 2.4s;
  }

  .brain-logo-main {
    width: 180px;
    height: 180px;
    object-fit: contain;
    background: transparent;
    filter: drop-shadow(0 0 15px rgba(0, 255, 136, 0.4))
      drop-shadow(0 0 25px rgba(220, 20, 60, 0.3));
    transition: all 0.3s ease;
    animation: brain-breathing 4s ease-in-out infinite;
    will-change: transform;
    position: relative;
    z-index: 1;
  }

  .brain-logo-main:hover {
    animation: brain-breathing-fast 2s ease-in-out infinite;
    filter: drop-shadow(0 0 20px rgba(0, 255, 136, 0.6))
      drop-shadow(0 0 30px rgba(220, 20, 60, 0.5));
  }

  .brain-logo-collapsed {
    width: 120px;
    height: 120px;
    object-fit: contain;
    background: transparent;
    filter: drop-shadow(0 0 12px rgba(0, 255, 136, 0.4))
      drop-shadow(0 0 20px rgba(220, 20, 60, 0.3));
    transition: all 0.3s ease;
    animation: brain-breathing 4s ease-in-out infinite;
    will-change: transform;
    position: relative;
    z-index: 1;
  }

  .brain-logo-collapsed:hover {
    animation: brain-breathing-fast 2s ease-in-out infinite;
    filter: drop-shadow(0 0 18px rgba(0, 255, 136, 0.6))
      drop-shadow(0 0 25px rgba(220, 20, 60, 0.5));
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
    gap: 1rem;
    padding: 1rem 1.25rem;
    margin-bottom: 0.25rem;
    color: var(--text-secondary);
    font-family: var(--font-display);
    font-weight: 500;
    font-size: 1.1rem;
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

  /* Override default nav-link styles for terminal design */
  .nav-link:not(.terminal-process) {
    position: relative;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: var(--radius-sm);
    transition: all var(--transition-base);
    font-weight: 500;
    font-size: 0.875rem;
  }

  .nav-link:not(.terminal-process)::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(74, 158, 255, 0.2), transparent);
    transition: left var(--transition-slow);
  }

  .nav-link:not(.terminal-process):hover::before {
    left: 0;
  }

  .nav-link:not(.terminal-process):hover {
    color: var(--text-primary);
    background: rgba(74, 158, 255, 0.05);
    transform: translateX(2px);
  }

  .sidebar.collapsed .nav-link:not(.terminal-process):hover {
    transform: none;
  }

  .nav-link:not(.terminal-process).active {
    color: var(--accent);
    background: rgba(74, 158, 255, 0.1);
    font-weight: 600;
    box-shadow: inset 3px 0 0 var(--accent);
  }

  .main-content {
    flex: 1;
    margin-left: 420px;
    min-height: 100vh;
    overflow-y: auto;
    transition: margin-left var(--transition-base) cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeIn var(--transition-base) ease-out;
    background: transparent;
    position: relative;
    z-index: 1;
  }

  .main-content.sidebar-collapsed {
    margin-left: 70px;
  }

  /* Auth page specific styles */
  .app-layout.auth-layout {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .main-content.auth-page {
    margin-left: 0;
    width: 100%;
    max-width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
  }

  .prsnl-logo-text {
    background: linear-gradient(
      135deg,
      var(--brand-accent),
      var(--highlight),
      var(--error),
      var(--brand-hover)
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-family:
      'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'SF Mono', 'Courier New', monospace !important;
    font-weight: 800;
    animation: glow-pulse 2s ease-in-out infinite;
  }

  /* Electrical Animations */
  .electrical-animations {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    z-index: 1;
  }

  .electrical-spark {
    position: absolute;
    width: 3px;
    height: 3px;
    background: var(--synapse-teal);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--synapse-teal-40);
    animation: spark-travel 4s ease-in-out infinite;
  }

  .spark-1 {
    top: 20%;
    left: 5%;
    animation-delay: 0s;
  }

  .spark-2 {
    top: 40%;
    left: 95%;
    animation-delay: 1s;
  }

  .spark-3 {
    top: 60%;
    left: 10%;
    animation-delay: 2s;
  }

  .spark-4 {
    top: 80%;
    left: 90%;
    animation-delay: 3s;
  }

  .electrical-circuit {
    position: absolute;
    background: linear-gradient(90deg, transparent, var(--synapse-teal), transparent);
    height: 1px;
    opacity: 0.6;
    animation: circuit-flow 3s ease-in-out infinite;
  }

  .circuit-1 {
    top: 25%;
    left: 0;
    width: 100%;
    animation-delay: 0s;
  }

  .circuit-2 {
    top: 50%;
    left: 0;
    width: 100%;
    animation-delay: 1s;
  }

  .circuit-3 {
    top: 75%;
    left: 0;
    width: 100%;
    animation-delay: 2s;
  }

  .data-pulse {
    position: absolute;
    width: 20px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--brand-accent), transparent);
    animation: data-flow 2s ease-in-out infinite;
  }

  .pulse-1 {
    top: 30%;
    left: 0;
    animation-delay: 0s;
  }

  .pulse-2 {
    top: 55%;
    left: 0;
    animation-delay: 0.5s;
  }

  .pulse-3 {
    top: 70%;
    left: 0;
    animation-delay: 1s;
  }

  /* Terminal Process Styling */
  .terminal-process {
    position: relative;
    margin-bottom: 1rem;
    padding: 0.8rem;
    background: rgba(0, 255, 0, 0.05);
    border-left: 4px solid var(--synapse-teal);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
    color: var(--synapse-teal);
  }

  .terminal-process:hover {
    background: rgba(0, 255, 0, 0.1);
    border-left-color: var(--brand-accent);
    transform: translateX(4px);
  }

  .terminal-process.active {
    background: rgba(220, 20, 60, 0.1);
    border-left-color: var(--brand-accent);
    box-shadow: 0 0 15px rgba(220, 20, 60, 0.3);
  }

  .process-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .process-name {
    color: var(--synapse-teal);
    font-weight: 600;
    font-size: 1rem;
  }

  .terminal-process.active .process-name {
    color: var(--brand-accent);
  }

  .process-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
  }

  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--synapse-teal);
    animation: status-blink 1.5s ease-in-out infinite;
  }

  .status-indicator.active {
    background: var(--brand-accent);
    animation: status-pulse 1s ease-in-out infinite;
  }

  .process-info {
    color: rgba(0, 255, 0, 0.9);
    font-size: 0.85rem;
    margin-bottom: 0.3rem;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .sidebar.collapsed .process-info {
    display: none;
  }

  .sidebar.collapsed .process-header {
    justify-content: center;
  }

  .sidebar.collapsed .process-name {
    font-size: 0.8rem;
  }

  .sidebar.collapsed .process-status {
    display: none;
  }

  /* Scan lines effect */
  .sidebar::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0, 255, 100, 0.1) 2px,
      rgba(0, 255, 100, 0.1) 4px
    );
    animation: scan-lines 2s linear infinite;
    pointer-events: none;
    z-index: 2;
  }

  @keyframes spark-travel {
    0% {
      transform: translateX(0) scale(1);
      opacity: 1;
    }
    25% {
      transform: translateX(105px) scale(1.2);
      opacity: 0.8;
    }
    50% {
      transform: translateX(210px) scale(1);
      opacity: 0.6;
    }
    75% {
      transform: translateX(315px) scale(1.2);
      opacity: 0.8;
    }
    100% {
      transform: translateX(420px) scale(1);
      opacity: 0;
    }
  }

  @keyframes circuit-flow {
    0% {
      opacity: 0.3;
      transform: scaleX(0.8);
    }
    50% {
      opacity: 0.8;
      transform: scaleX(1.2);
    }
    100% {
      opacity: 0.3;
      transform: scaleX(0.8);
    }
  }

  @keyframes data-flow {
    0% {
      transform: translateX(0);
      opacity: 0;
    }
    20% {
      opacity: 1;
    }
    80% {
      opacity: 1;
    }
    100% {
      transform: translateX(420px);
      opacity: 0;
    }
  }

  @keyframes glow-pulse {
    0%,
    100% {
      text-shadow: 0 0 20px rgba(220, 20, 60, 0.5);
    }
    50% {
      text-shadow: 0 0 30px rgba(220, 20, 60, 0.8);
    }
  }

  @keyframes scan-lines {
    0% {
      transform: translateY(0);
    }
    100% {
      transform: translateY(4px);
    }
  }

  @keyframes status-blink {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.3;
    }
  }

  @keyframes status-pulse {
    0%,
    100% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.2);
      opacity: 0.8;
    }
  }

  /* Brain Logo Animations */
  @keyframes brain-breathing {
    0%,
    100% {
      transform: scale(1);
      filter: drop-shadow(0 0 15px rgba(0, 255, 136, 0.4))
        drop-shadow(0 0 25px rgba(220, 20, 60, 0.3));
    }
    50% {
      transform: scale(1.05);
      filter: drop-shadow(0 0 18px rgba(0, 255, 136, 0.5))
        drop-shadow(0 0 28px rgba(220, 20, 60, 0.4));
    }
  }

  @keyframes brain-breathing-fast {
    0%,
    100% {
      transform: scale(1.05);
      filter: drop-shadow(0 0 20px rgba(0, 255, 136, 0.6))
        drop-shadow(0 0 30px rgba(220, 20, 60, 0.5));
    }
    50% {
      transform: scale(1.15);
      filter: drop-shadow(0 0 25px rgba(0, 255, 136, 0.8))
        drop-shadow(0 0 35px rgba(220, 20, 60, 0.7));
    }
  }

  @keyframes circuit-pulse {
    0%,
    100% {
      opacity: 0.3;
      background: linear-gradient(
        90deg,
        rgba(0, 255, 136, 0.4),
        rgba(0, 255, 136, 0.1),
        transparent
      );
    }
    50% {
      opacity: 0.8;
      background: linear-gradient(
        90deg,
        rgba(0, 255, 136, 0.9),
        rgba(0, 255, 136, 0.3),
        transparent
      );
    }
  }

  /* Fast pulse animations for each circuit rotation */
  @keyframes circuit-pulse-fast-0 {
    0%,
    100% {
      opacity: 0.6;
      background: linear-gradient(
        90deg,
        rgba(0, 255, 136, 0.9),
        rgba(220, 20, 60, 0.3),
        transparent
      );
      transform: translate(-50%, -50%) rotate(0deg) scaleX(1);
    }
    50% {
      opacity: 1;
      background: linear-gradient(90deg, rgba(0, 255, 136, 1), rgba(220, 20, 60, 0.6), transparent);
      transform: translate(-50%, -50%) rotate(0deg) scaleX(1.3);
    }
  }

  @keyframes circuit-pulse-fast-60 {
    0%,
    100% {
      opacity: 0.6;
      background: linear-gradient(
        90deg,
        rgba(0, 255, 136, 0.9),
        rgba(220, 20, 60, 0.3),
        transparent
      );
      transform: translate(-50%, -50%) rotate(60deg) scaleX(1);
    }
    50% {
      opacity: 1;
      background: linear-gradient(90deg, rgba(0, 255, 136, 1), rgba(220, 20, 60, 0.6), transparent);
      transform: translate(-50%, -50%) rotate(60deg) scaleX(1.3);
    }
  }

  @keyframes circuit-pulse-fast-120 {
    0%,
    100% {
      opacity: 0.6;
      background: linear-gradient(
        90deg,
        rgba(0, 255, 136, 0.9),
        rgba(220, 20, 60, 0.3),
        transparent
      );
      transform: translate(-50%, -50%) rotate(120deg) scaleX(1);
    }
    50% {
      opacity: 1;
      background: linear-gradient(90deg, rgba(0, 255, 136, 1), rgba(220, 20, 60, 0.6), transparent);
      transform: translate(-50%, -50%) rotate(120deg) scaleX(1.3);
    }
  }

  @keyframes circuit-pulse-fast-180 {
    0%,
    100% {
      opacity: 0.6;
      background: linear-gradient(
        90deg,
        rgba(0, 255, 136, 0.9),
        rgba(220, 20, 60, 0.3),
        transparent
      );
      transform: translate(-50%, -50%) rotate(180deg) scaleX(1);
    }
    50% {
      opacity: 1;
      background: linear-gradient(90deg, rgba(0, 255, 136, 1), rgba(220, 20, 60, 0.6), transparent);
      transform: translate(-50%, -50%) rotate(180deg) scaleX(1.3);
    }
  }

  @keyframes circuit-pulse-fast-240 {
    0%,
    100% {
      opacity: 0.6;
      background: linear-gradient(
        90deg,
        rgba(0, 255, 136, 0.9),
        rgba(220, 20, 60, 0.3),
        transparent
      );
      transform: translate(-50%, -50%) rotate(240deg) scaleX(1);
    }
    50% {
      opacity: 1;
      background: linear-gradient(90deg, rgba(0, 255, 136, 1), rgba(220, 20, 60, 0.6), transparent);
      transform: translate(-50%, -50%) rotate(240deg) scaleX(1.3);
    }
  }

  @keyframes circuit-pulse-fast-300 {
    0%,
    100% {
      opacity: 0.6;
      background: linear-gradient(
        90deg,
        rgba(0, 255, 136, 0.9),
        rgba(220, 20, 60, 0.3),
        transparent
      );
      transform: translate(-50%, -50%) rotate(300deg) scaleX(1);
    }
    50% {
      opacity: 1;
      background: linear-gradient(90deg, rgba(0, 255, 136, 1), rgba(220, 20, 60, 0.6), transparent);
      transform: translate(-50%, -50%) rotate(300deg) scaleX(1.3);
    }
  }

  /* Dot Matrix Wave Animation */
  @keyframes dot-wave {
    0% {
      background: var(--success);
      box-shadow: 0 0 4px rgba(0, 255, 136, 0.8);
    }
    50% {
      background: var(--brand-accent);
      box-shadow: 0 0 8px rgba(220, 20, 60, 1);
    }
    100% {
      background: var(--success);
      box-shadow: 0 0 4px rgba(0, 255, 136, 0.8);
    }
  }

  /* Terminal Header Styles */
  .terminal-header {
    border-bottom: 2px solid var(--synapse-teal);
    padding-bottom: 1rem;
    margin-bottom: 1rem;
    flex-direction: column;
    align-items: flex-start;
  }

  .terminal-header .logo {
    text-align: center;
    margin-bottom: 1rem;
    width: 100%;
  }

  .system-info {
    font-size: 0.8rem;
    color: var(--synapse-teal);
    margin-bottom: 0.5rem;
    text-align: center;
    width: 100%;
  }

  .boot-sequence {
    margin-bottom: 1rem;
    width: 100%;
  }

  .boot-line {
    margin-bottom: 0.3rem;
    font-size: 0.75rem;
    color: var(--synapse-teal);
    opacity: 0.8;
  }

  .terminal-header .sidebar-toggle {
    position: absolute;
    top: 1rem;
    right: 1rem;
    font-size: 1.8rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    position: relative;
    text-shadow: 0 0 20px rgba(220, 20, 60, 0.3);
    animation: pulse-glow 3s ease-in-out infinite;
  }

  @keyframes pulse-glow {
    0%,
    100% {
      filter: drop-shadow(0 0 8px rgba(220, 20, 60, 0.4));
      transform: scale(1);
    }
    50% {
      filter: drop-shadow(0 0 16px rgba(220, 20, 60, 0.6));
      transform: scale(1.02);
    }
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

  .nav-link:nth-child(1) {
    animation-delay: 0.05s;
  }
  .nav-link:nth-child(2) {
    animation-delay: 0.1s;
  }
  .nav-link:nth-child(3) {
    animation-delay: 0.15s;
  }
  .nav-link:nth-child(4) {
    animation-delay: 0.2s;
  }
  .nav-link:nth-child(5) {
    animation-delay: 0.25s;
  }
  .nav-link:nth-child(6) {
    animation-delay: 0.3s;
  }

  /* Neural motherboard background for all pages except homepage */
  .neural-motherboard-bg {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    opacity: 0.1;
    pointer-events: none;
    z-index: 0;
  }

  .neural-motherboard-bg.hide-bg {
    display: none;
  }

  .pcb-traces {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 40px,
        var(--success) 40px,
        var(--success) 42px
      ),
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 40px,
        var(--success) 40px,
        var(--success) 42px
      );
  }

  .circuit-nodes {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .node {
    position: absolute;
    width: 20px;
    height: 20px;
    background: radial-gradient(circle, var(--brand-accent), var(--brand-hover));
    border-radius: 50%;
    border: 2px solid var(--brand-accent);
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.5);
    animation: node-pulse 3s ease-in-out infinite;
  }

  .node-1 {
    top: 20%;
    left: 15%;
    animation-delay: 0s;
  }
  .node-2 {
    top: 60%;
    left: 80%;
    animation-delay: 1s;
  }
  .node-3 {
    top: 30%;
    left: 70%;
    animation-delay: 2s;
  }
  .node-4 {
    top: 80%;
    left: 25%;
    animation-delay: 1.5s;
  }

  @keyframes node-pulse {
    0%,
    100% {
      transform: scale(1);
      opacity: 0.6;
    }
    50% {
      transform: scale(1.3);
      opacity: 0.9;
    }
  }

  /* ========== VERSION B INNOVATIVE NAVIGATION ========== */

  /* Mobile Toggle */
  .mobile-toggle {
    position: fixed;
    top: 20px;
    left: 20px;
    z-index: 1001;
    width: 55px;
    height: 55px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    border-radius: 50%;
    color: white;
    cursor: pointer;
    display: none;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
  }

  .mobile-toggle:hover {
    transform: scale(1.1) rotate(90deg);
  }

  @media (max-width: 768px) {
    .mobile-toggle {
      display: flex;
    }
  }

  .toggle-icon {
    font-size: 20px;
    transition: transform 0.3s ease;
  }

  .mobile-toggle.active .toggle-icon {
    transform: rotate(45deg);
  }

  /* Mobile Backdrop */
  .mobile-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    z-index: 999;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
    backdrop-filter: blur(5px);
  }

  .mobile-backdrop.show {
    opacity: 1;
    visibility: visible;
  }

  /* Innovative Morphing Sidebar */
  .innovative-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    width: 300px;
    background: linear-gradient(180deg, rgba(0, 0, 0, 0.9) 0%, rgba(16, 16, 32, 0.9) 100%);
    backdrop-filter: blur(25px);
    border-right: 1px solid rgba(255, 255, 255, 0.12);
    transition: all 0.5s cubic-bezier(0.68, 0, 0.32, 1);
    z-index: 1000;
    overflow: hidden;
    transform-origin: left center;
  }

  .innovative-sidebar.morphed {
    width: 80px;
    border-radius: 0 25px 25px 0;
  }

  /* Floating sidebar on mobile */
  @media (max-width: 768px) {
    .innovative-sidebar {
      width: 280px;
      border-radius: 0 25px 25px 0;
      transform: translateX(-100%) scale(0.9);
      opacity: 0;
      background: rgba(0, 0, 0, 0.95);
    }

    .innovative-sidebar.mobile-open {
      transform: translateX(0) scale(1);
      opacity: 1;
    }

    .innovative-sidebar.morphed {
      transform: translateX(-100%) scale(0.9);
      opacity: 0;
    }
  }

  .sidebar-glow {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .innovative-sidebar:hover .sidebar-glow {
    opacity: 1;
  }

  .header-bg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }

  .innovative-sidebar:hover .header-bg {
    transform: translateX(0);
  }

  .logo-orb {
    width: 50px;
    height: 50px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
  }

  .logo-orb::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: conic-gradient(transparent, rgba(255, 255, 255, 0.3), transparent);
    animation: spin 4s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .morph-toggle {
    position: absolute;
    top: 80%;
    right: -15px;
    transform: translateY(-50%);
    width: 30px;
    height: 60px;
    background: rgba(102, 126, 234, 0.8);
    border: none;
    border-radius: 0 15px 15px 0;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
    font-size: 12px;
  }

  .morph-toggle:hover {
    background: rgba(102, 126, 234, 1);
    transform: translateY(-50%) translateX(5px);
  }

  @media (max-width: 768px) {
    .morph-toggle {
      display: none;
    }
  }

  /* Navigation Items with Rotating Icons */
  .nav-item {
    display: flex;
    align-items: center;
    padding: 15px 20px;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all var(--transition-base);
    position: relative;
    margin: 3px 10px;
    border-radius: var(--radius-lg);
    overflow: hidden;
    border: 1px solid transparent;
    font-family: var(--font-display);
  }

  .nav-item::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 5px;
    height: 100%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    transform: scaleY(0);
    transition: transform var(--transition-base);
    border-radius: 0 3px 3px 0;
  }

  .nav-item::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, rgba(102, 126, 234, 0.1), transparent);
    transform: translateX(-100%);
    transition: transform var(--transition-base);
  }

  .nav-item:hover::before,
  .nav-item.active::before {
    transform: scaleY(1);
  }

  .nav-item:hover::after {
    transform: translateX(0);
  }

  .nav-item:hover {
    background: var(--glass-light);
    color: var(--text-primary);
    transform: translateX(10px);
    border-color: rgba(102, 126, 234, 0.3);
  }

  .nav-item.active {
    background: rgba(102, 126, 234, 0.2);
    color: var(--text-primary);
    border-color: #667eea;
    box-shadow: 0 5px 20px rgba(102, 126, 234, 0.2);
  }

  .nav-icon {
    width: 24px;
    height: 24px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    margin-right: 15px;
    flex-shrink: 0;
    position: relative;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .nav-icon::before {
    content: '';
    width: 12px;
    height: 12px;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 2px;
    transition: all 0.3s ease;
  }

  .nav-item:hover .nav-icon,
  .nav-item.active .nav-icon {
    background: linear-gradient(135deg, #667eea, #764ba2);
    transform: rotate(180deg);
  }

  .nav-item:hover .nav-icon::before,
  .nav-item.active .nav-icon::before {
    background: white;
    transform: scale(1.2);
  }

  .nav-text {
    font-size: 15px;
    font-weight: 500;
    opacity: 1;
    transition: all 0.5s ease;
    white-space: nowrap;
  }

  .innovative-sidebar.morphed .nav-text {
    display: none;
  }

  .innovative-sidebar.morphed .nav-item {
    justify-content: center;
    padding: 15px 10px;
    margin: 5px 8px;
  }

  .innovative-sidebar.morphed .nav-icon {
    margin-right: 0;
  }

  /* Tooltip for morphed state */
  .nav-tooltip {
    position: absolute;
    left: 90px;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 10px 15px;
    border-radius: 10px;
    font-size: 13px;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: all 0.3s ease;
    z-index: 1001;
    border: 1px solid rgba(102, 126, 234, 0.3);
    backdrop-filter: blur(10px);
    transform: translateY(-50%) translateX(-10px);
  }

  .nav-tooltip::before {
    content: '';
    position: absolute;
    left: -6px;
    top: 50%;
    transform: translateY(-50%);
    border: 6px solid transparent;
    border-right-color: rgba(0, 0, 0, 0.9);
  }

  .innovative-sidebar.morphed .nav-item:hover .nav-tooltip {
    opacity: 1;
    transform: translateY(-50%) translateX(0);
  }

  /* Logo Container Styling */
  .logo-container {
    display: flex;
    align-items: center;
    gap: 15px;
    position: relative;
    z-index: 2;
  }

  .logo-text {
    font-size: 24px;
    font-weight: 800;
    opacity: 1;
    transition: all 0.6s ease;
    background: linear-gradient(135deg, #667eea, #764ba2);
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-size: 200% 200%;
    animation: gradient-shift 4s ease-in-out infinite;
  }

  @keyframes gradient-shift {
    0%,
    100% {
      background-position: 0% 50%;
    }
    50% {
      background-position: 100% 50%;
    }
  }

  .innovative-sidebar.morphed .logo-text {
    display: none;
  }

  /* Update main content margin */
  .main-content {
    margin-left: 300px;
    transition: margin-left 0.5s cubic-bezier(0.68, 0, 0.32, 1);
  }

  .innovative-sidebar.morphed + .main-content {
    margin-left: 80px;
  }

  @media (max-width: 768px) {
    .main-content {
      margin-left: 0;
    }
  }

  /* User Authentication Section Styles */
  .user-auth-section {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
  }

  .user-profile {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: var(--radius);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .user-avatar {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 16px;
    color: white;
    flex-shrink: 0;
  }

  .user-info {
    flex: 1;
    min-width: 0;
  }

  .user-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .user-type {
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: capitalize;
    margin-bottom: 0.25rem;
  }

  .verification-status {
    font-size: 0.7rem;
    color: #f59e0b;
    background: rgba(245, 158, 11, 0.1);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    border: 1px solid rgba(245, 158, 11, 0.2);
  }

  .auth-actions {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .auth-prompt {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .auth-link {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all var(--transition-base);
    cursor: pointer;
  }

  .auth-link:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    transform: translateY(-1px);
  }

  .auth-link.primary {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-color: #667eea;
    color: white;
  }

  .auth-link.primary:hover {
    background: linear-gradient(135deg, #5a67d8, #6b46c1);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }

  .logout-btn {
    border: none;
    width: 100%;
    justify-content: flex-start;
    text-align: left;
  }

  .logout-btn:hover {
    background: rgba(239, 68, 68, 0.1);
    border-color: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }

  /* Morphed sidebar adjustments */
  .innovative-sidebar.morphed .user-auth-section {
    padding: 0.5rem;
  }

  .innovative-sidebar.morphed .user-profile {
    flex-direction: column;
    text-align: center;
    gap: 0.5rem;
  }

  .innovative-sidebar.morphed .user-info {
    display: none;
  }

  .innovative-sidebar.morphed .auth-actions {
    gap: 0.25rem;
  }

  .innovative-sidebar.morphed .auth-link {
    padding: 0.5rem;
    justify-content: center;
    font-size: 0.75rem;
  }

  .innovative-sidebar.morphed .auth-link span {
    display: none;
  }

</style>

<!-- Floating Chat - Available on all pages -->
<FloatingChat />
