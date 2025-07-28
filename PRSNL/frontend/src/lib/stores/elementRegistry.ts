/**
 * Element Registry Store for PRSNL Frontend
 * 
 * Tracks all registered elements with auto-IDs for development
 * and design communication purposes.
 */

import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';

export interface RegisteredElement {
  id: string;
  element: HTMLElement;
  type: string;
  component: string;
  suffix?: string;
  timestamp: Date;
  position?: DOMRect;
}

export interface ElementStats {
  totalElements: number;
  byComponent: Record<string, number>;
  byType: Record<string, number>;
  recentlyAdded: RegisteredElement[];
}

// Core registry store
function createElementRegistry() {
  const { subscribe, set, update } = writable<Map<string, RegisteredElement>>(new Map());

  return {
    subscribe,
    
    /**
     * Register a new element
     */
    register: (element: RegisteredElement) => {
      update(registry => {
        const newRegistry = new Map(registry);
        
        // Store position for overlay
        if (browser && element.element.getBoundingClientRect) {
          element.position = element.element.getBoundingClientRect();
        }
        
        newRegistry.set(element.id, element);
        return newRegistry;
      });
      
      // Log in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`📝 Registered element: ${element.id}`, element);
      }
    },
    
    /**
     * Unregister an element
     */
    unregister: (id: string) => {
      update(registry => {
        const newRegistry = new Map(registry);
        newRegistry.delete(id);
        return newRegistry;
      });
      
      if (process.env.NODE_ENV === 'development') {
        console.log(`🗑️ Unregistered element: ${id}`);
      }
    },
    
    /**
     * Get element by ID
     */
    getElement: (id: string): RegisteredElement | undefined => {
      const registry = get({ subscribe });
      return registry.get(id);
    },
    
    /**
     * Update element position (for overlay)
     */
    updatePosition: (id: string) => {
      update(registry => {
        const element = registry.get(id);
        if (element && browser && element.element.getBoundingClientRect) {
          element.position = element.element.getBoundingClientRect();
          const newRegistry = new Map(registry);
          newRegistry.set(id, element);
          return newRegistry;
        }
        return registry;
      });
    },
    
    /**
     * Clear all registered elements
     */
    clear: () => {
      set(new Map());
    },
    
    /**
     * Get all elements as array
     */
    getAll: (): RegisteredElement[] => {
      const registry = get({ subscribe });
      return Array.from(registry.values());
    },
    
    /**
     * Get elements by component
     */
    getByComponent: (componentName: string): RegisteredElement[] => {
      const registry = get({ subscribe });
      return Array.from(registry.values()).filter(
        element => element.component === componentName
      );
    },
    
    /**
     * Get elements by type
     */
    getByType: (type: string): RegisteredElement[] => {
      const registry = get({ subscribe });
      return Array.from(registry.values()).filter(
        element => element.type === type
      );
    }
  };
}

export const elementRegistry = createElementRegistry();

// Derived store for statistics
export const elementStats = derived(
  elementRegistry,
  ($registry): ElementStats => {
    const elements = Array.from($registry.values());
    
    // Group by component
    const byComponent: Record<string, number> = {};
    elements.forEach(element => {
      byComponent[element.component] = (byComponent[element.component] || 0) + 1;
    });
    
    // Group by type
    const byType: Record<string, number> = {};
    elements.forEach(element => {
      byType[element.type] = (byType[element.type] || 0) + 1;
    });
    
    // Get recently added (last 10)
    const recentlyAdded = elements
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, 10);
    
    return {
      totalElements: elements.length,
      byComponent,
      byType,
      recentlyAdded
    };
  }
);

// Store for overlay visibility
export const showIdOverlay = writable(false);

// Store for overlay settings
export const overlaySettings = writable({
  showOnHover: true,
  showAllIds: false,
  highlightComponent: '',
  opacity: 0.9,
  fontSize: 12,
  position: 'top-right' as 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
});

// Development helpers
export const elementRegistryHelpers = {
  /**
   * Toggle overlay visibility
   */
  toggleOverlay: () => {
    showIdOverlay.update(show => !show);
  },
  
  /**
   * Find element in DOM by ID
   */
  findElement: (id: string): HTMLElement | null => {
    return document.getElementById(id);
  },
  
  /**
   * Highlight element temporarily
   */
  highlightElement: (id: string, duration = 2000) => {
    const element = document.getElementById(id);
    if (!element) return;
    
    const originalStyle = element.style.cssText;
    element.style.outline = '3px solid #ff6b6b';
    element.style.outlineOffset = '2px';
    element.style.backgroundColor = 'rgba(255, 107, 107, 0.1)';
    
    setTimeout(() => {
      element.style.cssText = originalStyle;
    }, duration);
  },
  
  /**
   * Scroll to element
   */
  scrollToElement: (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
      });
      // Highlight after scroll
      setTimeout(() => {
        elementRegistryHelpers.highlightElement(id);
      }, 500);
    }
  },
  
  /**
   * Copy element selector to clipboard
   */
  copySelector: async (id: string) => {
    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(`#${id}`);
        console.log(`Copied selector: #${id}`);
      } catch (err) {
        console.error('Failed to copy selector:', err);
      }
    }
  },
  
  /**
   * Generate design communication template
   */
  generateDesignRequest: (id: string, changes: string): string => {
    const element = elementRegistry.getElement(id);
    if (!element) return `Element ${id} not found`;
    
    return `## Design Change Request

**Element ID**: \`${id}\`
**Component**: ${element.component}
**Element Type**: ${element.type}
**Timestamp**: ${element.timestamp.toISOString()}

### Requested Changes:
${changes}

### Element Info:
- Location: Can be found with ID \`${id}\`
- Component: ${element.component}
- Type: ${element.type}
${element.suffix ? `- Suffix: ${element.suffix}` : ''}

### CSS Selector:
\`\`\`css
#${id} {
  /* Your changes here */
}
\`\`\`
`;
  },
  
  /**
   * Export all element data for analysis
   */
  exportData: () => {
    const data = {
      elements: elementRegistry.getAll().map(el => ({
        id: el.id,
        type: el.type,
        component: el.component,
        suffix: el.suffix,
        timestamp: el.timestamp,
        position: el.position
      })),
      stats: get(elementStats),
      exportTimestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `prsnl-element-registry-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
};

// Keyboard shortcuts for development
if (browser && process.env.NODE_ENV === 'development') {
  document.addEventListener('keydown', (e) => {
    // Ctrl+Shift+I to toggle overlay
    if (e.ctrlKey && e.shiftKey && e.key === 'I') {
      e.preventDefault();
      elementRegistryHelpers.toggleOverlay();
    }
    
    // Ctrl+Shift+E to export data
    if (e.ctrlKey && e.shiftKey && e.key === 'E') {
      e.preventDefault();
      elementRegistryHelpers.exportData();
    }
  });
}

// Window object for console access
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  (window as any).PRSNL_ELEMENT_REGISTRY = {
    registry: elementRegistry,
    stats: elementStats,
    helpers: elementRegistryHelpers,
    showOverlay: showIdOverlay,
    settings: overlaySettings
  };
}

// Auto-update positions on resize/scroll for overlay
if (browser && process.env.NODE_ENV === 'development') {
  let resizeTimeout: number;
  
  const updatePositions = () => {
    const elements = elementRegistry.getAll();
    elements.forEach(element => {
      elementRegistry.updatePosition(element.id);
    });
  };
  
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = window.setTimeout(updatePositions, 100);
  });
  
  window.addEventListener('scroll', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = window.setTimeout(updatePositions, 50);
  }, { passive: true });
}