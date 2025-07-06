<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import Notifications from '$lib/components/Notifications.svelte';
  import { preferences } from '$lib/stores/app';
  
  // Global keyboard navigation
  onMount(() => {
    const handleKeydown = (e: KeyboardEvent) => {
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
    };
    
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  });
</script>

<nav>
  <div class="nav-container">
    <a href="/" class="logo">PRSNL</a>
    <div class="nav-links">
      <a href="/capture">
        Capture <span class="keyboard-hint">⌘N</span>
      </a>
      <a href="/search">
        Search <span class="keyboard-hint">⌘K</span>
      </a>
      <a href="/timeline">Timeline</a>
    </div>
  </div>
</nav>

<main>
  <slot />
</main>

<Notifications />

<style>
  nav {
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
  }
  
  .nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .logo {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
  }
  
  .nav-links {
    display: flex;
    gap: 2rem;
    align-items: center;
  }
  
  .nav-links a {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
    transition: color 0.2s;
  }
  
  .nav-links a:hover {
    color: var(--text-primary);
  }
  
  main {
    min-height: calc(100vh - 60px);
  }
</style>