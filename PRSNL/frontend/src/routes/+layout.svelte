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
  <div class="app-layout">
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

    <aside class="sidebar glass {sidebarCollapsed ? 'collapsed' : ''}">
      <div class="electrical-animations">
        <div class="electrical-spark spark-1"></div>
        <div class="electrical-spark spark-2"></div>
        <div class="electrical-spark spark-3"></div>
        <div class="electrical-spark spark-4"></div>

        <div class="electrical-circuit circuit-1"></div>
        <div class="electrical-circuit circuit-2"></div>
        <div class="electrical-circuit circuit-3"></div>

        <div class="data-pulse pulse-1"></div>
        <div class="data-pulse pulse-2"></div>
        <div class="data-pulse pulse-3"></div>
      </div>

      <div class="sidebar-header terminal-header">
        {#if !sidebarCollapsed}
          <div class="brain-logo-center">
            <div class="brain-circuit-container">
              <img src="/thug-brain-logo.png" alt="PRSNL Brain" class="brain-logo-main" />
              <div class="brain-circuits">
                <div class="brain-circuit brain-circuit-1"></div>
                <div class="brain-circuit brain-circuit-2"></div>
                <div class="brain-circuit brain-circuit-3"></div>
                <div class="brain-circuit brain-circuit-4"></div>
                <div class="brain-circuit brain-circuit-5"></div>
                <div class="brain-circuit brain-circuit-6"></div>
              </div>
            </div>
            <div class="dot-matrix-text">
              <div class="dot-matrix-letter letter-p">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
              </div>
              <div class="dot-matrix-letter letter-r">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
              </div>
              <div class="dot-matrix-letter letter-s">
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
              </div>
              <div class="dot-matrix-letter letter-n">
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
              </div>
              <div class="dot-matrix-letter letter-l">
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
              </div>
            </div>
          </div>
          <div class="system-info">NEURAL OS v3.0 - BRAIN COMPUTER INTERFACE</div>
          <div class="boot-sequence">
            <div class="boot-line">[ OK ] Neural pathways initialized</div>
            <div class="boot-line">[ OK ] Cognitive processes loaded</div>
            <div class="boot-line">[ OK ] Memory banks online</div>
            <div class="boot-line">[ OK ] Ready for neural interface</div>
          </div>
        {:else}
          <div class="brain-logo-center">
            <div class="brain-circuit-container">
              <img src="/thug-brain-logo.png" alt="PRSNL Brain" class="brain-logo-collapsed" />
              <div class="brain-circuits collapsed">
                <div class="brain-circuit brain-circuit-1"></div>
                <div class="brain-circuit brain-circuit-2"></div>
                <div class="brain-circuit brain-circuit-3"></div>
                <div class="brain-circuit brain-circuit-4"></div>
              </div>
            </div>
            <div class="dot-matrix-text collapsed">
              <div class="dot-matrix-letter letter-p">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
              </div>
              <div class="dot-matrix-letter letter-r">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
              </div>
              <div class="dot-matrix-letter letter-s">
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
              </div>
              <div class="dot-matrix-letter letter-n">
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
              </div>
              <div class="dot-matrix-letter letter-l">
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot empty"></div>
                <div class="dot empty"></div>
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
              </div>
            </div>
          </div>
        {/if}

        <button class="sidebar-toggle" on:click={toggleSidebar} aria-label="Toggle sidebar">
          <Icon name={sidebarCollapsed ? 'chevron-right' : 'chevron-left'} size="small" />
        </button>
      </div>

      <nav class="sidebar-nav terminal-nav">
        <a
          href="/"
          class="nav-link terminal-process {$page.url.pathname === '/' ? 'active' : ''}"
          title="Neural Nest"
        >
          <div class="process-header">
            <div class="process-name">Neural Nest</div>
            <div class="process-status">
              <div class="status-indicator {$page.url.pathname === '/' ? 'active' : ''}"></div>
              <span>{$page.url.pathname === '/' ? 'ACTIVE' : 'READY'}</span>
            </div>
          </div>
          {#if !sidebarCollapsed}
            <div class="process-info">MEM: 256MB | CPU: 12%</div>
          {/if}
        </a>

        <a
          href="/capture"
          class="nav-link terminal-process {$page.url.pathname === '/capture' ? 'active' : ''}"
          title="Ingest"
        >
          <div class="process-header">
            <div class="process-name">Ingest</div>
            <div class="process-status">
              <div
                class="status-indicator {$page.url.pathname === '/capture' ? 'active' : ''}"
              ></div>
              <span>{$page.url.pathname === '/capture' ? 'ACTIVE' : 'READY'}</span>
            </div>
          </div>
          {#if !sidebarCollapsed}
            <div class="process-info">MEM: 128MB | CPU: 5%</div>
          {/if}
        </a>

        <a
          href="/timeline"
          class="nav-link terminal-process {$page.url.pathname === '/timeline' ? 'active' : ''}"
          title="Thought Stream"
        >
          <div class="process-header">
            <div class="process-name">Thought Stream</div>
            <div class="process-status">
              <div
                class="status-indicator {$page.url.pathname === '/timeline' ? 'active' : ''}"
              ></div>
              <span>{$page.url.pathname === '/timeline' ? 'ACTIVE' : 'READY'}</span>
            </div>
          </div>
          {#if !sidebarCollapsed}
            <div class="process-info">MEM: 192MB | CPU: 8%</div>
          {/if}
        </a>

        <a
          href="/insights"
          class="nav-link terminal-process {$page.url.pathname === '/insights' ? 'active' : ''}"
          title="Cognitive Map"
        >
          <div class="process-header">
            <div class="process-name">Cognitive Map</div>
            <div class="process-status">
              <div
                class="status-indicator {$page.url.pathname === '/insights' ? 'active' : ''}"
              ></div>
              <span>{$page.url.pathname === '/insights' ? 'ACTIVE' : 'READY'}</span>
            </div>
          </div>
          {#if !sidebarCollapsed}
            <div class="process-info">MEM: 384MB | CPU: 15%</div>
          {/if}
        </a>

        <a
          href="/chat"
          class="nav-link terminal-process {$page.url.pathname === '/chat' ? 'active' : ''}"
          title="Mind Palace"
        >
          <div class="process-header">
            <div class="process-name">Mind Palace</div>
            <div class="process-status">
              <div class="status-indicator {$page.url.pathname === '/chat' ? 'active' : ''}"></div>
              <span>{$page.url.pathname === '/chat' ? 'ACTIVE' : 'READY'}</span>
            </div>
          </div>
          {#if !sidebarCollapsed}
            <div class="process-info">MEM: 512MB | CPU: 20%</div>
          {/if}
        </a>

        <a
          href="/videos"
          class="nav-link terminal-process {$page.url.pathname === '/videos' ? 'active' : ''}"
          title="Visual Cortex"
        >
          <div class="process-header">
            <div class="process-name">Visual Cortex</div>
            <div class="process-status">
              <div
                class="status-indicator {$page.url.pathname === '/videos' ? 'active' : ''}"
              ></div>
              <span>{$page.url.pathname === '/videos' ? 'ACTIVE' : 'READY'}</span>
            </div>
          </div>
          {#if !sidebarCollapsed}
            <div class="process-info">MEM: 256MB | CPU: 10%</div>
          {/if}
        </a>

        <a
          href="/code-cortex"
          class="nav-link terminal-process {$page.url.pathname.startsWith('/code-cortex')
            ? 'active'
            : ''}"
          title="Code Cortex"
        >
          <div class="process-header">
            <div class="process-name">Code Cortex</div>
            <div class="process-status">
              <div
                class="status-indicator {$page.url.pathname.startsWith('/code-cortex')
                  ? 'active'
                  : ''}"
              ></div>
              <span>{$page.url.pathname.startsWith('/code-cortex') ? 'ACTIVE' : 'READY'}</span>
            </div>
          </div>
          {#if !sidebarCollapsed}
            <div class="process-info">MEM: 320MB | CPU: 18%</div>
          {/if}
        </a>

        <a
          href="/import"
          class="nav-link terminal-process {$page.url.pathname === '/import' ? 'active' : ''}"
          title="Knowledge Sync"
        >
          <div class="process-header">
            <div class="process-name">Knowledge Sync</div>
            <div class="process-status">
              <div
                class="status-indicator {$page.url.pathname === '/import' ? 'active' : ''}"
              ></div>
              <span>{$page.url.pathname === '/import' ? 'ACTIVE' : 'READY'}</span>
            </div>
          </div>
          {#if !sidebarCollapsed}
            <div class="process-info">MEM: 164MB | CPU: 6%</div>
          {/if}
        </a>
      </nav>

      <div class="sidebar-footer terminal-footer">
        <a
          href="/docs"
          class="nav-link terminal-process {$page.url.pathname === '/docs' ? 'active' : ''}"
          title="Documentation"
        >
          <div class="process-header">
            <div class="process-name">Documentation</div>
            <div class="process-status">
              <div class="status-indicator {$page.url.pathname === '/docs' ? 'active' : ''}"></div>
              <span>{$page.url.pathname === '/docs' ? 'ACTIVE' : 'READY'}</span>
            </div>
          </div>
        </a>

        <a
          href="/settings"
          class="nav-link terminal-process {$page.url.pathname === '/settings' ? 'active' : ''}"
          title="Settings"
        >
          <div class="process-header">
            <div class="process-name">Settings</div>
            <div class="process-status">
              <div
                class="status-indicator {$page.url.pathname === '/settings' ? 'active' : ''}"
              ></div>
              <span>{$page.url.pathname === '/settings' ? 'ACTIVE' : 'READY'}</span>
            </div>
          </div>
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
</QueryClientProvider>

<style>
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
    background: linear-gradient(45deg, var(--brand-accent), var(--highlight), var(--error), var(--brand-hover));
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

  .prsnl-logo-text {
    background: linear-gradient(135deg, var(--brand-accent), var(--highlight), var(--error), var(--brand-hover));
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
      repeating-linear-gradient(0deg, transparent, transparent 40px, var(--success) 40px, var(--success) 42px),
      repeating-linear-gradient(90deg, transparent, transparent 40px, var(--success) 40px, var(--success) 42px);
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
</style>
