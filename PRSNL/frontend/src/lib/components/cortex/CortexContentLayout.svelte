<script lang="ts">
  import Icon from '../Icon.svelte';

  export let showSidebar: boolean = true;
  export let sidebarCollapsed: boolean = false;
  export let sidebarWidth: string = '280px';
  export let sidebarTitle: string = '';
  export let collapsible: boolean = true;
</script>

<div class="cortex-content-layout">
  {#if showSidebar}
    <aside
      class="sidebar"
      class:collapsed={sidebarCollapsed}
      style="width: {sidebarCollapsed ? '0' : sidebarWidth}"
    >
      <div class="sidebar-content">
        {#if sidebarTitle}
          <div class="sidebar-header">
            <h3>{sidebarTitle}</h3>
            {#if collapsible}
              <button
                class="collapse-btn"
                on:click={() => (sidebarCollapsed = !sidebarCollapsed)}
                aria-label="Toggle sidebar"
              >
                <Icon name={sidebarCollapsed ? 'chevron-right' : 'chevron-left'} size="16" />
              </button>
            {/if}
          </div>
        {/if}

        <div class="sidebar-body">
          <slot name="sidebar" />
        </div>
      </div>
    </aside>
  {/if}

  <main class="main-content">
    {#if collapsible && showSidebar}
      <button
        class="mobile-sidebar-toggle"
        on:click={() => (sidebarCollapsed = !sidebarCollapsed)}
        aria-label="Toggle sidebar"
      >
        <Icon name="menu" size="20" />
      </button>
    {/if}

    <div class="content-area">
      <slot name="content" />
    </div>
  </main>
</div>

<style>
  .cortex-content-layout {
    display: flex;
    gap: 1.5rem;
    min-height: 60vh;
  }

  .sidebar {
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(0, 255, 136, 0.2);
    border-radius: 8px;
    transition: all 0.3s ease;
    overflow: hidden;
    flex-shrink: 0;
  }

  .sidebar.collapsed {
    width: 0 !important;
    border: none;
    margin: 0;
  }

  .sidebar-content {
    padding: 1rem;
    height: 100%;
    min-width: 260px;
  }

  .sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(0, 255, 136, 0.2);
  }

  .sidebar-header h3 {
    margin: 0;
    font-size: 1rem;
    color: #00ff88;
    font-weight: 600;
  }

  .collapse-btn {
    background: transparent;
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.25rem;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .collapse-btn:hover {
    background: rgba(0, 255, 136, 0.1);
    border-color: #00ff88;
  }

  .sidebar-body {
    height: calc(100% - 3rem);
    overflow-y: auto;
  }

  .main-content {
    flex: 1;
    min-width: 0;
    position: relative;
  }

  .mobile-sidebar-toggle {
    display: none;
    position: absolute;
    top: 0;
    left: 0;
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid rgba(0, 255, 136, 0.3);
    color: #00ff88;
    padding: 0.5rem;
    border-radius: 6px;
    cursor: pointer;
    z-index: 10;
    transition: all 0.2s ease;
  }

  .mobile-sidebar-toggle:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
  }

  .content-area {
    height: 100%;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .cortex-content-layout {
      flex-direction: column;
      gap: 1rem;
    }

    .sidebar {
      position: fixed;
      top: 0;
      left: 0;
      bottom: 0;
      z-index: 100;
      width: 280px !important;
      transform: translateX(0);
      background: rgba(0, 0, 0, 0.95);
      backdrop-filter: blur(10px);
    }

    .sidebar.collapsed {
      transform: translateX(-100%);
      width: 280px !important;
    }

    .mobile-sidebar-toggle {
      display: block;
      position: relative;
      margin-bottom: 1rem;
    }

    .main-content {
      width: 100%;
    }
  }

  /* Custom scrollbar for sidebar */
  .sidebar-body::-webkit-scrollbar {
    width: 4px;
  }

  .sidebar-body::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.1);
  }

  .sidebar-body::-webkit-scrollbar-thumb {
    background: rgba(0, 255, 136, 0.3);
    border-radius: 2px;
  }

  .sidebar-body::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 255, 136, 0.5);
  }
</style>
