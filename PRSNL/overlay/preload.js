const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
  'api', {
    // Send methods (from renderer to main)
    hideWindow: () => {
      ipcRenderer.send('hide-window');
    },
    quitApp: () => {
      ipcRenderer.send('quit-app');
    },
    
    // Search API
    search: async (query) => {
      try {
        const response = await fetch(`http://localhost:8000/api/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
      } catch (error) {
        console.error('Search API error:', error);
        return { results: [], error: error.message };
      }
    },
    
    // Listen for events from main process
    onFocusSearch: (callback) => {
      ipcRenderer.on('focus-search', () => callback());
    }
  }
);
