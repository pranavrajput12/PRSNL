<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { mediaSettings } from '$lib/stores/media';
  import Icon from './Icon.svelte';
  
  // Create a local performance metrics store
  const videoPerformanceMetrics = {
    loadTimes: [] as {videoId: string, value: number}[],
    bufferingEvents: [] as {videoId: string, value: number}[],
    memoryUsage: [] as {timestamp: number, value: number}[],
    activeVideoCount: 0
  };

  export let position: 'top-right' | 'bottom-right' | 'bottom-left' | 'top-left' = 'bottom-right';
  
  let visible = false;
  let updateInterval: number | null = null;
  let memoryUsage: number = 0;
  let cpuUsage: number = 0;
  
  onMount(() => {
    if ($mediaSettings.logPerformanceMetrics) {
      visible = true;
      updateInterval = window.setInterval(() => {
        updateMetrics();
      }, 2000);
    }
  });
  
  onDestroy(() => {
    if (updateInterval) {
      window.clearInterval(updateInterval);
    }
  });
  
  function updateMetrics() {
    // Get latest memory usage from performance metrics
    if (videoPerformanceMetrics.memoryUsage.length > 0) {
      memoryUsage = videoPerformanceMetrics.memoryUsage[videoPerformanceMetrics.memoryUsage.length - 1].value;
    }
    
    // Update active video count
    const activeVideos = document.querySelectorAll('video');
    videoPerformanceMetrics.activeVideoCount = activeVideos.length;
    
    // Record memory usage
    if (window.performance && 'memory' in window.performance) {
      const memory = (window.performance as any).memory;
      if (memory) {
        const currentMemory = memory.usedJSHeapSize;
        videoPerformanceMetrics.memoryUsage.push({
          timestamp: Date.now(),
          value: currentMemory
        });
        
        // Keep only the last 20 memory measurements
        if (videoPerformanceMetrics.memoryUsage.length > 20) {
          videoPerformanceMetrics.memoryUsage.shift();
        }
      }
    }
    
    // Get CPU usage if available
    if (window.performance && 'memory' in window.performance) {
      const memory = (window.performance as any).memory;
      if (memory) {
        cpuUsage = Math.round((memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100);
      }
    }
  }
  
  function toggleVisibility() {
    visible = !visible;
  }
  
  function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  function formatTime(ms: number): string {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  }
</script>

<div class="performance-monitor {position}" class:visible>
  <button class="toggle-button" on:click={toggleVisibility}>
    <Icon name={visible ? "chart-bar" : "gauge"} size="small" />
  </button>
  
  {#if visible}
    <div class="metrics-panel">
      <div class="panel-header">
        <h3>Video Performance</h3>
        <div class="network-mode">
          {#if $mediaSettings.networkSavingMode}
            <span class="network-saving">
              <Icon name="wifi-off" size="small" />
              Network Saving
            </span>
          {:else}
            <span class="network-normal">
              <Icon name="wifi" size="small" />
              Normal
            </span>
          {/if}
        </div>
      </div>
      
      <div class="metrics-grid">
        <div class="metric-item">
          <div class="metric-label">Active Videos</div>
          <div class="metric-value">{videoPerformanceMetrics.activeVideoCount}</div>
        </div>
        
        <div class="metric-item">
          <div class="metric-label">Memory</div>
          <div class="metric-value">{formatBytes(memoryUsage)}</div>
        </div>
        
        <div class="metric-item">
          <div class="metric-label">CPU</div>
          <div class="metric-value">{cpuUsage}%</div>
        </div>
        
        <div class="metric-item">
          <div class="metric-label">Avg Load Time</div>
          <div class="metric-value">
            {#if videoPerformanceMetrics.loadTimes.length > 0}
              {formatTime(videoPerformanceMetrics.loadTimes.reduce((sum, item) => sum + item.value, 0) / videoPerformanceMetrics.loadTimes.length)}
            {:else}
              N/A
            {/if}
          </div>
        </div>
        
        <div class="metric-item">
          <div class="metric-label">Buffer Events</div>
          <div class="metric-value">{videoPerformanceMetrics.bufferingEvents.length}</div>
        </div>
        
        <div class="metric-item">
          <div class="metric-label">Preload</div>
          <div class="metric-value">{$mediaSettings.preloadStrategy}</div>
        </div>
      </div>
      
      <div class="settings-section">
        <label class="setting-toggle">
          <input 
            type="checkbox" 
            checked={$mediaSettings.networkSavingMode}
            on:change={() => $mediaSettings.networkSavingMode = !$mediaSettings.networkSavingMode}
          />
          Network Saving Mode
        </label>
        
        <label class="setting-toggle">
          <input 
            type="checkbox" 
            checked={$mediaSettings.enableProgressiveLoading}
            on:change={() => $mediaSettings.enableProgressiveLoading = !$mediaSettings.enableProgressiveLoading}
          />
          Progressive Loading
        </label>
      </div>
    </div>
  {/if}
</div>

<style>
  .performance-monitor {
    position: fixed;
    z-index: 1000;
  }
  
  .top-right {
    top: 20px;
    right: 20px;
  }
  
  .bottom-right {
    bottom: 20px;
    right: 20px;
  }
  
  .bottom-left {
    bottom: 20px;
    left: 20px;
  }
  
  .top-left {
    top: 20px;
    left: 20px;
  }
  
  .toggle-button {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
  }
  
  .toggle-button:hover {
    background: var(--bg-tertiary);
    transform: scale(1.05);
  }
  
  .metrics-panel {
    position: absolute;
    bottom: 50px;
    right: 0;
    width: 280px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    box-shadow: var(--shadow-lg);
    padding: 1rem;
    animation: fadeIn 0.2s ease-out;
  }
  
  .bottom-left .metrics-panel {
    right: auto;
    left: 0;
  }
  
  .top-right .metrics-panel,
  .top-left .metrics-panel {
    bottom: auto;
    top: 50px;
  }
  
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .panel-header h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
  }
  
  .network-mode {
    font-size: 0.75rem;
    font-weight: 500;
  }
  
  .network-saving {
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--warning);
  }
  
  .network-normal {
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--success);
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
  
  .metric-item {
    background: var(--bg-tertiary);
    padding: 0.5rem;
    border-radius: var(--radius-sm);
  }
  
  .metric-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
  }
  
  .metric-value {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  .settings-section {
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border-color);
  }
  
  .setting-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    margin-bottom: 0.5rem;
    cursor: pointer;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
