<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { browser } from '$app/environment';
  import { 
    elementRegistry, 
    elementStats, 
    showIdOverlay, 
    overlaySettings,
    elementRegistryHelpers 
  } from '$lib/stores/elementRegistry';
  import type { RegisteredElement } from '$lib/stores/elementRegistry';

  // Only show in development
  $: isDevelopment = process.env.NODE_ENV === 'development';
  
  let hoveredElement: RegisteredElement | null = null;
  let selectedElement: RegisteredElement | null = null;
  let overlayContainer: HTMLDivElement;
  
  // Mouse position for tooltip
  let mouseX = 0;
  let mouseY = 0;
  
  // Element hover handlers
  let elementMouseEnterHandlers = new Map<string, (e: MouseEvent) => void>();
  let elementMouseLeaveHandlers = new Map<string, (e: MouseEvent) => void>();
  let elementClickHandlers = new Map<string, (e: MouseEvent) => void>();

  function setupElementListeners() {
    if (!browser || !isDevelopment) return;
    
    // Clear existing handlers
    cleanupElementListeners();
    
    $elementRegistry.forEach((element, id) => {
      const domElement = document.getElementById(id);
      if (!domElement) return;
      
      // Mouse enter handler
      const mouseEnterHandler = (e: MouseEvent) => {
        if ($overlaySettings.showOnHover) {
          hoveredElement = element;
          mouseX = e.clientX;
          mouseY = e.clientY;
        }
      };
      
      // Mouse leave handler  
      const mouseLeaveHandler = () => {
        if ($overlaySettings.showOnHover) {
          hoveredElement = null;
        }
      };
      
      // Click handler
      const clickHandler = (e: MouseEvent) => {
        if ($showIdOverlay && e.altKey) {
          e.preventDefault();
          e.stopPropagation();
          selectedElement = selectedElement?.id === element.id ? null : element;
          elementRegistryHelpers.highlightElement(element.id);
        }
      };
      
      // Add listeners
      domElement.addEventListener('mouseenter', mouseEnterHandler);
      domElement.addEventListener('mouseleave', mouseLeaveHandler);
      domElement.addEventListener('click', clickHandler);
      
      // Store handlers for cleanup
      elementMouseEnterHandlers.set(id, mouseEnterHandler);
      elementMouseLeaveHandlers.set(id, mouseLeaveHandler);
      elementClickHandlers.set(id, clickHandler);
    });
  }
  
  function cleanupElementListeners() {
    elementMouseEnterHandlers.forEach((handler, id) => {
      const element = document.getElementById(id);
      if (element) element.removeEventListener('mouseenter', handler);
    });
    
    elementMouseLeaveHandlers.forEach((handler, id) => {
      const element = document.getElementById(id);
      if (element) element.removeEventListener('mouseleave', handler);
    });
    
    elementClickHandlers.forEach((handler, id) => {
      const element = document.getElementById(id);
      if (element) element.removeEventListener('click', handler);
    });
    
    elementMouseEnterHandlers.clear();
    elementMouseLeaveHandlers.clear();
    elementClickHandlers.clear();
  }

  // Global mouse move handler for tooltip positioning
  function handleGlobalMouseMove(e: MouseEvent) {
    mouseX = e.clientX;
    mouseY = e.clientY;
  }

  // Keyboard handlers
  function handleKeydown(e: KeyboardEvent) {
    if (!$showIdOverlay) return;
    
    // Escape to close selection
    if (e.key === 'Escape') {
      selectedElement = null;
      hoveredElement = null;
    }
    
    // Copy ID with Ctrl+C
    if (e.key === 'c' && e.ctrlKey && selectedElement) {
      elementRegistryHelpers.copySelector(selectedElement.id);
    }
  }

  // Setup and cleanup
  onMount(() => {
    if (!browser || !isDevelopment) return;
    
    setupElementListeners();
    document.addEventListener('mousemove', handleGlobalMouseMove);
    document.addEventListener('keydown', handleKeydown);
    
    // Re-setup listeners when registry changes
    const unsubscribe = elementRegistry.subscribe(() => {
      setTimeout(setupElementListeners, 100);
    });
    
    return () => {
      unsubscribe();
    };
  });

  onDestroy(() => {
    if (browser) {
      cleanupElementListeners();
      document.removeEventListener('mousemove', handleGlobalMouseMove);
      document.removeEventListener('keydown', handleKeydown);
    }
  });

  function copyDesignRequest() {
    if (!selectedElement) return;
    
    const request = elementRegistryHelpers.generateDesignRequest(
      selectedElement.id,
      "/* Describe your changes here */"
    );
    
    navigator.clipboard?.writeText(request).then(() => {
      console.log('Design request template copied to clipboard!');
    });
  }

  function scrollToSelected() {
    if (selectedElement) {
      elementRegistryHelpers.scrollToElement(selectedElement.id);
    }
  }
</script>

<!-- Global mouse tracking -->
<svelte:window on:mousemove={handleGlobalMouseMove} on:keydown={handleKeydown} />

{#if isDevelopment && $showIdOverlay}
  <!-- Main Overlay Container -->
  <div 
    bind:this={overlayContainer}
    class="id-inspector-overlay"
    style="--overlay-opacity: {$overlaySettings.opacity}; --font-size: {$overlaySettings.fontSize}px"
  >
    
    <!-- Control Panel -->
    <div class="control-panel {$overlaySettings.position}">
      <div class="panel-header">
        <h3>🆔 ID Inspector</h3>
        <button 
          class="close-btn"
          on:click={() => showIdOverlay.set(false)}
          title="Close (Ctrl+Shift+I)"
        >
          ✕
        </button>
      </div>
      
      <div class="panel-content">
        <!-- Stats -->
        <div class="stats">
          <div class="stat">
            <span class="label">Total Elements:</span>
            <span class="value">{$elementStats.totalElements}</span>
          </div>
          <div class="stat">
            <span class="label">Components:</span>
            <span class="value">{Object.keys($elementStats.byComponent).length}</span>
          </div>
        </div>
        
        <!-- Settings -->
        <div class="settings">
          <label class="setting">
            <input 
              type="checkbox" 
              bind:checked={$overlaySettings.showOnHover}
            />
            Show on hover
          </label>
          
          <label class="setting">
            <input 
              type="checkbox" 
              bind:checked={$overlaySettings.showAllIds}
            />
            Show all IDs
          </label>
          
          <label class="setting">
            <span>Opacity:</span>
            <input 
              type="range" 
              min="0.1" 
              max="1" 
              step="0.1"
              bind:value={$overlaySettings.opacity}
            />
          </label>
        </div>
        
        <!-- Actions -->
        <div class="actions">
          <button 
            class="action-btn"
            on:click={elementRegistryHelpers.exportData}
            title="Export all element data"
          >
            📤 Export
          </button>
          
          <button 
            class="action-btn"
            on:click={() => console.table($elementStats.byComponent)}
            title="Log stats to console"
          >
            📊 Stats
          </button>
        </div>
      </div>
    </div>

    <!-- Hover Tooltip -->
    {#if hoveredElement && $overlaySettings.showOnHover}
      <div 
        class="hover-tooltip"
        style="left: {mouseX + 10}px; top: {mouseY - 10}px"
      >
        <div class="tooltip-id">#{hoveredElement.id}</div>
        <div class="tooltip-info">
          <span class="component">{hoveredElement.component}</span>
          <span class="type">{hoveredElement.type}</span>
        </div>
      </div>
    {/if}

    <!-- Selection Details Panel -->
    {#if selectedElement}
      <div class="selection-panel">
        <div class="selection-header">
          <h4>Selected Element</h4>
          <button 
            class="close-btn"
            on:click={() => selectedElement = null}
          >
            ✕
          </button>
        </div>
        
        <div class="selection-content">
          <div class="detail-row">
            <strong>ID:</strong> 
            <code>#{selectedElement.id}</code>
            <button 
              class="copy-btn"
              on:click={() => elementRegistryHelpers.copySelector(selectedElement.id)}
              title="Copy selector"
            >
              📋
            </button>
          </div>
          
          <div class="detail-row">
            <strong>Component:</strong> 
            <span>{selectedElement.component}</span>
          </div>
          
          <div class="detail-row">
            <strong>Type:</strong> 
            <span>{selectedElement.type}</span>
          </div>
          
          {#if selectedElement.suffix}
            <div class="detail-row">
              <strong>Suffix:</strong> 
              <span>{selectedElement.suffix}</span>
            </div>
          {/if}
          
          <div class="detail-row">
            <strong>Created:</strong> 
            <span>{selectedElement.timestamp.toLocaleTimeString()}</span>
          </div>
          
          <div class="selection-actions">
            <button 
              class="action-btn"
              on:click={scrollToSelected}
              title="Scroll to element"
            >
              🎯 Locate
            </button>
            
            <button 
              class="action-btn"
              on:click={() => elementRegistryHelpers.highlightElement(selectedElement.id)}
              title="Highlight element"
            >
              ✨ Highlight
            </button>
            
            <button 
              class="action-btn"
              on:click={copyDesignRequest}
              title="Copy design request template"
            >
              📝 Template
            </button>
          </div>
        </div>
      </div>
    {/if}

    <!-- All IDs Overlay (when showAllIds is enabled) -->
    {#if $overlaySettings.showAllIds}
      {#each Array.from($elementRegistry.values()) as element (element.id)}
        {#if element.position}
          <div 
            class="id-badge"
            style="
              left: {element.position.left}px; 
              top: {element.position.top - 25}px;
              z-index: 999999;
            "
            on:click={() => selectedElement = element}
          >
            #{element.id}
          </div>
        {/if}
      {/each}
    {/if}

  </div>
{/if}

<style>
  .id-inspector-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    pointer-events: none;
    z-index: 999999;
    font-family: 'JetBrains Mono', 'Monaco', 'Consolas', monospace;
    font-size: var(--font-size, 12px);
  }

  /* Control Panel */
  .control-panel {
    position: fixed;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    color: white;
    min-width: 250px;
    max-width: 300px;
    pointer-events: all;
    opacity: var(--overlay-opacity, 0.9);
  }

  .control-panel.top-right {
    top: 20px;
    right: 20px;
  }

  .control-panel.top-left {
    top: 20px;
    left: 20px;
  }

  .control-panel.bottom-right {
    bottom: 20px;
    right: 20px;
  }

  .control-panel.bottom-left {
    bottom: 20px;
    left: 20px;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.1);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .panel-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
  }

  .close-btn {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    font-size: 16px;
    padding: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: background-color 0.2s;
  }

  .close-btn:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  .panel-content {
    padding: 16px;
  }

  /* Stats */
  .stats {
    margin-bottom: 16px;
  }

  .stat {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 12px;
  }

  .label {
    color: rgba(255, 255, 255, 0.7);
  }

  .value {
    font-weight: 600;
  }

  /* Settings */
  .settings {
    margin-bottom: 16px;
  }

  .setting {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 12px;
    cursor: pointer;
  }

  .setting input[type="checkbox"] {
    margin-left: 8px;
  }

  .setting input[type="range"] {
    width: 80px;
    margin-left: 8px;
  }

  /* Actions */
  .actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .action-btn {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 11px;
    transition: all 0.2s;
  }

  .action-btn:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  /* Hover Tooltip */
  .hover-tooltip {
    position: fixed;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    pointer-events: none;
    z-index: 1000000;
    backdrop-filter: blur(4px);
  }

  .tooltip-id {
    font-weight: 600;
    font-size: 12px;
    color: #4a9eff;
  }

  .tooltip-info {
    display: flex;
    gap: 8px;
    font-size: 10px;
    color: rgba(255, 255, 255, 0.8);
    margin-top: 4px;
  }

  .component {
    color: #10b981;
  }

  .type {
    color: #f59e0b;
  }

  /* Selection Panel */
  .selection-panel {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.95);
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    color: white;
    min-width: 350px;
    pointer-events: all;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  }

  .selection-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: rgba(255, 255, 255, 0.1);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px 12px 0 0;
  }

  .selection-header h4 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }

  .selection-content {
    padding: 20px;
  }

  .detail-row {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    font-size: 13px;
  }

  .detail-row strong {
    min-width: 80px;
    color: rgba(255, 255, 255, 0.8);
  }

  .detail-row code {
    background: rgba(255, 255, 255, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: inherit;
    color: #4a9eff;
    margin-right: 8px;
  }

  .copy-btn {
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    padding: 2px;
    border-radius: 3px;
    transition: color 0.2s;
  }

  .copy-btn:hover {
    color: white;
  }

  .selection-actions {
    display: flex;
    gap: 10px;
    margin-top: 20px;
    justify-content: center;
  }

  /* ID Badges (Show All Mode) */
  .id-badge {
    position: fixed;
    background: rgba(74, 158, 255, 0.9);
    color: white;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    cursor: pointer;
    pointer-events: all;
    border: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(4px);
    transition: all 0.2s;
  }

  .id-badge:hover {
    background: rgba(74, 158, 255, 1);
    transform: scale(1.1);
  }

  /* Development mode indicator */
  .id-inspector-overlay::before {
    content: 'DEV MODE';
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    background: #ef4444;
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 600;
    pointer-events: none;
    z-index: 1000001;
  }
</style>