<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Notifications from '$lib/components/Notifications.svelte';
  import Icon from '$lib/components/Icon.svelte';
  import { preferences } from '$lib/stores/app';
  
  // Global keyboard navigation
  onMount(() => {
    const handleKeydown = (e) => {
      // CMD/CTRL + K for search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        window.location.href = '/search';
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
    };
    
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  });
</script>

<nav class="glass">
  <div class="nav-container">
    <a href="/" class="logo animate-slide">
      <div class="logo-icon">
        <Icon name="sparkles" size="medium" color="var(--accent)" />
      </div>
      <span class="red-gradient-text">PRSNL</span>
    </a>
    
    <div class="nav-links">
      <a href="/capture" class="nav-link {$page.url.pathname === '/capture' ? 'active' : ''}">
        <Icon name="capture" size="small" />
        <span>Capture</span>
        <span class="keyboard-hint">⌘N</span>
      </a>
      
      <a href="/search" class="nav-link {$page.url.pathname === '/search' ? 'active' : ''}">
        <Icon name="search" size="small" />
        <span>Search</span>
        <span class="keyboard-hint">⌘K</span>
      </a>
      
      <a href="/timeline" class="nav-link {$page.url.pathname === '/timeline' ? 'active' : ''}">
        <Icon name="timeline" size="small" />
        <span>Timeline</span>
      </a>
    </div>
  </div>
</nav>

<main class="main-content">
  <slot />
</main>

<Notifications />

<style>
  nav {
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
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
  }
  
  .logo:hover {
    transform: scale(1.05);
  }
  
  .logo-icon {
    width: 32px;
    height: 32px;
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
  
  .nav-links {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  
  .nav-link {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    color: var(--text-secondary);
    font-weight: 500;
    border-radius: var(--radius);
    transition: all var(--transition-base);
    position: relative;
    overflow: hidden;
  }
  
  .nav-link::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 0;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(74, 158, 255, 0.1), transparent);
    transition: width var(--transition-slow);
  }
  
  .nav-link:hover::before {
    width: 100%;
  }
  
  .nav-link:hover {
    color: var(--text-primary);
    background: rgba(74, 158, 255, 0.05);
    transform: translateY(-1px);
  }
  
  .nav-link.active {
    color: var(--accent);
    background: rgba(74, 158, 255, 0.1);
    font-weight: 600;
  }
  
  .nav-link .keyboard-hint {
    margin-left: 0.5rem;
    opacity: 0;
    transform: translateX(-10px);
    transition: all var(--transition-base);
  }
  
  .nav-link:hover .keyboard-hint {
    opacity: 1;
    transform: translateX(0);
  }
  
  .main-content {
    min-height: calc(100vh - 80px);
    animation: fadeIn var(--transition-base) ease-out;
  }
  
  .red-gradient-text {
    background: linear-gradient(135deg, var(--man-united-red), #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  @media (max-width: 768px) {
    .nav-container {
      padding: 1rem;
    }
    
    .nav-links {
      gap: 0.25rem;
    }
    
    .nav-link {
      padding: 0.5rem 0.75rem;
    }
    
    .nav-link span:not(.keyboard-hint) {
      display: none;
    }
    
    .nav-link .keyboard-hint {
      display: none;
    }
  }
</style>