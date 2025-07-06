<script>
  import { onMount } from 'svelte';
  import Icon from '$lib/components/Icon.svelte';
  import { preferences, toggleDarkMode, setDefaultView } from '$lib/stores/app';
  
  let settings = {
    theme: 'dark',
    defaultView: 'timeline',
    keyboardShortcuts: true,
    notifications: true,
    autoCapture: false,
    syncEnabled: false
  };
  
  let activeSection = 'appearance';
  let isSaving = false;
  
  const sections = [
    { id: 'appearance', name: 'Appearance', icon: 'sparkles' },
    { id: 'shortcuts', name: 'Shortcuts', icon: 'info' },
    { id: 'capture', name: 'Capture', icon: 'capture' },
    { id: 'data', name: 'Data', icon: 'link' }
  ];
  
  onMount(() => {
    // Load settings from preferences store
    const unsubscribe = preferences.subscribe(prefs => {
      settings.theme = prefs.darkMode ? 'dark' : 'light';
      settings.defaultView = prefs.defaultView;
      settings.keyboardShortcuts = prefs.keyboardShortcutsEnabled;
    });
    
    return unsubscribe;
  });
  
  async function saveSettings() {
    isSaving = true;
    
    try {
      // Simulate save delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Update preferences store
      if (settings.theme === 'dark' !== $preferences.darkMode) {
        toggleDarkMode();
      }
      
      setDefaultView(settings.defaultView);
      
      // Show success feedback
      console.log('Settings saved');
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      isSaving = false;
    }
  }
  
  function exportData() {
    // Mock export functionality
    const data = {
      exported_at: new Date().toISOString(),
      items: [],
      tags: [],
      preferences: settings
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'prsnl-export.json';
    a.click();
    URL.revokeObjectURL(url);
  }
  
  function importData() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const data = JSON.parse(e.target.result);
            console.log('Imported data:', data);
            // Handle import logic here
          } catch (error) {
            console.error('Invalid JSON file:', error);
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  }
</script>

<div class="container animate-in">
  <div class="settings-container">
    <div class="settings-header">
      <h1 class="red-gradient-text">Settings</h1>
      <p class="subtitle">Customize your PRSNL experience</p>
    </div>
    
    <div class="settings-content">
      <div class="settings-sidebar">
        <nav class="settings-nav">
          {#each sections as section}
            <button 
              class="nav-item {activeSection === section.id ? 'active' : ''}"
              on:click={() => activeSection = section.id}
            >
              <Icon name={section.icon} size="small" />
              {section.name}
            </button>
          {/each}
        </nav>
      </div>
      
      <div class="settings-main">
        {#if activeSection === 'appearance'}
          <div class="settings-section">
            <h2>Appearance</h2>
            <p class="section-description">Customize the look and feel of PRSNL</p>
            
            <div class="setting-group">
              <label class="setting-label">
                <Icon name="sparkles" size="small" />
                Theme
              </label>
              <div class="radio-group">
                <label class="radio-option">
                  <input 
                    type="radio" 
                    bind:group={settings.theme} 
                    value="dark"
                    on:change={saveSettings}
                  />
                  <span>Dark</span>
                </label>
                <label class="radio-option">
                  <input 
                    type="radio" 
                    bind:group={settings.theme} 
                    value="light"
                    on:change={saveSettings}
                  />
                  <span>Light</span>
                </label>
              </div>
            </div>
            
            <div class="setting-group">
              <label class="setting-label">
                <Icon name="search" size="small" />
                Default View
              </label>
              <select bind:value={settings.defaultView} on:change={saveSettings}>
                <option value="timeline">Timeline</option>
                <option value="grid">Grid</option>
                <option value="list">List</option>
              </select>
            </div>
          </div>
        {:else if activeSection === 'shortcuts'}
          <div class="settings-section">
            <h2>Keyboard Shortcuts</h2>
            <p class="section-description">Customize keyboard shortcuts for faster navigation</p>
            
            <div class="setting-group">
              <label class="setting-toggle">
                <input 
                  type="checkbox" 
                  bind:checked={settings.keyboardShortcuts}
                  on:change={saveSettings}
                />
                <span class="toggle-slider"></span>
                Enable keyboard shortcuts
              </label>
            </div>
            
            <div class="shortcuts-list">
              <div class="shortcut-item">
                <span class="shortcut-action">Quick Capture</span>
                <span class="keyboard-hint">⌘N</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Search</span>
                <span class="keyboard-hint">⌘K</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Timeline</span>
                <span class="keyboard-hint">⌘T</span>
              </div>
              <div class="shortcut-item">
                <span class="shortcut-action">Home</span>
                <span class="keyboard-hint">⌘H</span>
              </div>
            </div>
          </div>
        {:else if activeSection === 'capture'}
          <div class="settings-section">
            <h2>Capture Settings</h2>
            <p class="section-description">Configure how content is captured and processed</p>
            
            <div class="setting-group">
              <label class="setting-toggle">
                <input 
                  type="checkbox" 
                  bind:checked={settings.notifications}
                  on:change={saveSettings}
                />
                <span class="toggle-slider"></span>
                Show capture notifications
              </label>
            </div>
            
            <div class="setting-group">
              <label class="setting-toggle">
                <input 
                  type="checkbox" 
                  bind:checked={settings.autoCapture}
                  on:change={saveSettings}
                />
                <span class="toggle-slider"></span>
                Auto-capture from browser extension
              </label>
            </div>
          </div>
        {:else if activeSection === 'data'}
          <div class="settings-section">
            <h2>Data Management</h2>
            <p class="section-description">Import, export, and manage your captured data</p>
            
            <div class="setting-group">
              <label class="setting-label">
                <Icon name="link" size="small" />
                Export Data
              </label>
              <button class="btn-secondary" on:click={exportData}>
                <Icon name="capture" size="small" />
                Export to JSON
              </button>
            </div>
            
            <div class="setting-group">
              <label class="setting-label">
                <Icon name="plus" size="small" />
                Import Data
              </label>
              <button class="btn-secondary" on:click={importData}>
                <Icon name="plus" size="small" />
                Import from JSON
              </button>
            </div>
            
            <div class="setting-group">
              <label class="setting-toggle">
                <input 
                  type="checkbox" 
                  bind:checked={settings.syncEnabled}
                  on:change={saveSettings}
                />
                <span class="toggle-slider"></span>
                Enable cloud sync (coming soon)
              </label>
            </div>
          </div>
        {/if}
        
        <div class="settings-footer">
          <button 
            class="btn-red" 
            on:click={saveSettings}
            disabled={isSaving}
          >
            {#if isSaving}
              <Icon name="info" size="small" />
              Saving...
            {:else}
              <Icon name="check" size="small" />
              Save Changes
            {/if}
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .settings-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }
  
  .settings-header {
    text-align: center;
    margin-bottom: 3rem;
  }
  
  .settings-header h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
    font-weight: 800;
  }
  
  .subtitle {
    color: var(--text-secondary);
    font-size: 1.25rem;
    font-weight: 500;
    margin: 0;
  }
  
  .red-gradient-text {
    background: linear-gradient(135deg, var(--man-united-red), #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .settings-content {
    display: grid;
    grid-template-columns: 250px 1fr;
    gap: 3rem;
    background: var(--bg-secondary);
    border-radius: var(--radius-lg);
    overflow: hidden;
    min-height: 600px;
  }
  
  .settings-sidebar {
    background: var(--bg-tertiary);
    padding: 2rem 0;
  }
  
  .settings-nav {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 2rem;
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-weight: 500;
    text-align: left;
    transition: all var(--transition-base);
    border-left: 3px solid transparent;
  }
  
  .nav-item:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }
  
  .nav-item.active {
    background: var(--bg-secondary);
    color: var(--accent);
    border-left-color: var(--accent);
  }
  
  .settings-main {
    padding: 2rem;
    display: flex;
    flex-direction: column;
  }
  
  .settings-section {
    flex: 1;
  }
  
  .settings-section h2 {
    margin: 0 0 0.5rem;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary);
  }
  
  .section-description {
    color: var(--text-secondary);
    margin-bottom: 2rem;
    font-size: 1rem;
  }
  
  .setting-group {
    margin-bottom: 2rem;
  }
  
  .setting-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.75rem;
  }
  
  .radio-group {
    display: flex;
    gap: 1rem;
  }
  
  .radio-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }
  
  .radio-option input[type="radio"] {
    margin: 0;
  }
  
  .setting-toggle {
    display: flex;
    align-items: center;
    gap: 1rem;
    cursor: pointer;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .setting-toggle input[type="checkbox"] {
    display: none;
  }
  
  .toggle-slider {
    position: relative;
    width: 44px;
    height: 24px;
    background: var(--bg-tertiary);
    border-radius: 24px;
    transition: all var(--transition-base);
  }
  
  .toggle-slider::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    transition: all var(--transition-base);
  }
  
  .setting-toggle input:checked + .toggle-slider {
    background: var(--accent);
  }
  
  .setting-toggle input:checked + .toggle-slider::before {
    transform: translateX(20px);
  }
  
  select {
    padding: 0.75rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-primary);
    font-size: 0.9375rem;
    min-width: 200px;
  }
  
  .shortcuts-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-top: 1rem;
  }
  
  .shortcut-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius);
  }
  
  .shortcut-action {
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .btn-secondary {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-primary);
    font-weight: 500;
    transition: all var(--transition-base);
  }
  
  .btn-secondary:hover {
    background: var(--bg-primary);
    border-color: var(--accent);
    transform: translateY(-1px);
  }
  
  .btn-red {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 2rem;
    background: var(--man-united-red);
    border: none;
    border-radius: var(--radius);
    color: white;
    font-weight: 600;
    transition: all var(--transition-base);
  }
  
  .btn-red:hover:not(:disabled) {
    background: var(--accent-red-hover);
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.3);
    transform: translateY(-2px);
  }
  
  .btn-red:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
  
  .settings-footer {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border);
  }
  
  @media (max-width: 768px) {
    .settings-content {
      grid-template-columns: 1fr;
      gap: 0;
    }
    
    .settings-sidebar {
      padding: 1rem 0;
    }
    
    .settings-nav {
      flex-direction: row;
      overflow-x: auto;
      padding: 0 1rem;
    }
    
    .nav-item {
      flex-shrink: 0;
      border-left: none;
      border-bottom: 3px solid transparent;
    }
    
    .nav-item.active {
      border-left: none;
      border-bottom-color: var(--accent);
    }
  }
</style>