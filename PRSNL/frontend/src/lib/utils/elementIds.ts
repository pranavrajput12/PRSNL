/**
 * Element ID Generation Utility for PRSNL Frontend
 * 
 * Provides consistent, human-readable unique IDs for UI elements
 * to improve design communication and debugging.
 * 
 * Usage:
 * - generateId('voice-chat', 'button') → 'voice-chat-button-1'
 * - getComponentId('VoiceChat') → 'voice-chat'
 * - resetCounters() → resets all counters (for testing)
 */

// Global counters for each component-element combination
const idCounters = new Map<string, number>();

// Registry to track all generated IDs for debugging
const idRegistry = new Map<string, {
  component: string;
  element: string;
  count: number;
  timestamp: Date;
}>();

/**
 * Generate a unique ID for an element
 * @param componentName - Name of the component (e.g., 'voice-chat', 'glass-card')
 * @param elementType - Type of element (e.g., 'button', 'container', 'header')
 * @param suffix - Optional suffix for more specificity
 * @returns Unique ID string
 */
export function generateId(componentName: string, elementType: string, suffix?: string): string {
  const key = `${componentName}-${elementType}`;
  const currentCount = idCounters.get(key) || 0;
  const newCount = currentCount + 1;
  idCounters.set(key, newCount);
  
  const baseId = `${key}-${newCount}`;
  const finalId = suffix ? `${baseId}-${suffix}` : baseId;
  
  // Register the ID for debugging
  idRegistry.set(finalId, {
    component: componentName,
    element: elementType,
    count: newCount,
    timestamp: new Date()
  });
  
  return finalId;
}

/**
 * Convert component name to kebab-case ID format
 * @param componentName - Component name (e.g., 'VoiceChat', 'GlassCard')
 * @returns kebab-case string (e.g., 'voice-chat', 'glass-card')
 */
export function getComponentId(componentName: string): string {
  return componentName
    .replace(/([A-Z])/g, '-$1')
    .toLowerCase()
    .replace(/^-/, '');
}

/**
 * Generate ID using automatic component name detection
 * @param elementType - Type of element
 * @param componentName - Optional component name override
 * @returns Unique ID string
 */
export function autoGenerateId(elementType: string, componentName?: string): string {
  // If no component name provided, try to detect from call stack
  const detectedComponent = componentName || detectComponentName();
  const componentId = getComponentId(detectedComponent);
  return generateId(componentId, elementType);
}

/**
 * Attempt to detect component name from call stack (fallback)
 * @returns Detected component name or 'unknown'
 */
function detectComponentName(): string {
  try {
    const stack = new Error().stack;
    if (!stack) return 'unknown';
    
    // Look for .svelte files in the stack
    const svelteMatch = stack.match(/([^/\\]+)\.svelte/);
    if (svelteMatch) {
      return svelteMatch[1];
    }
    
    return 'unknown';
  } catch {
    return 'unknown';
  }
}

/**
 * Get all registered IDs for debugging
 * @returns Map of all registered IDs with metadata
 */
export function getIdRegistry(): Map<string, any> {
  return new Map(idRegistry);
}

/**
 * Get IDs for a specific component
 * @param componentName - Component name to filter by
 * @returns Array of IDs for the component
 */
export function getComponentIds(componentName: string): string[] {
  const componentId = getComponentId(componentName);
  return Array.from(idRegistry.keys()).filter(id => 
    id.startsWith(componentId)
  );
}

/**
 * Reset all counters (useful for testing)
 */
export function resetCounters(): void {
  idCounters.clear();
  idRegistry.clear();
}

/**
 * Check if an ID exists in the registry
 * @param id - ID to check
 * @returns boolean indicating if ID exists
 */
export function idExists(id: string): boolean {
  return idRegistry.has(id);
}

/**
 * Get statistics about ID usage
 * @returns Object with usage statistics
 */
export function getIdStats() {
  const componentStats = new Map<string, number>();
  const elementStats = new Map<string, number>();
  
  for (const [id, info] of idRegistry) {
    // Component stats
    const currentComponentCount = componentStats.get(info.component) || 0;
    componentStats.set(info.component, currentComponentCount + 1);
    
    // Element stats
    const currentElementCount = elementStats.get(info.element) || 0;
    elementStats.set(info.element, currentElementCount + 1);
  }
  
  return {
    totalIds: idRegistry.size,
    uniqueComponents: componentStats.size,
    uniqueElements: elementStats.size,
    componentBreakdown: Object.fromEntries(componentStats),
    elementBreakdown: Object.fromEntries(elementStats),
    mostUsedComponent: [...componentStats.entries()].sort((a, b) => b[1] - a[1])[0]?.[0],
    mostUsedElement: [...elementStats.entries()].sort((a, b) => b[1] - a[1])[0]?.[0]
  };
}

/**
 * Common element types for consistent naming
 */
export const ELEMENT_TYPES = {
  // Containers
  CONTAINER: 'container',
  WRAPPER: 'wrapper',
  SECTION: 'section',
  CARD: 'card',
  PANEL: 'panel',
  
  // Headers & Content
  HEADER: 'header',
  TITLE: 'title',
  SUBTITLE: 'subtitle',
  CONTENT: 'content',
  BODY: 'body',
  FOOTER: 'footer',
  
  // Interactive Elements
  BUTTON: 'button',
  LINK: 'link',
  INPUT: 'input',
  FORM: 'form',
  FIELD: 'field',
  
  // Navigation
  NAV: 'nav',
  MENU: 'menu',
  TAB: 'tab',
  BREADCRUMB: 'breadcrumb',
  
  // Display Elements
  LIST: 'list',
  ITEM: 'item',
  GRID: 'grid',
  TABLE: 'table',
  ROW: 'row',
  CELL: 'cell',
  
  // Media
  IMAGE: 'image',
  VIDEO: 'video',
  AUDIO: 'audio',
  ICON: 'icon',
  
  // Status & Feedback
  LOADING: 'loading',
  ERROR: 'error',
  SUCCESS: 'success',
  WARNING: 'warning',
  SPINNER: 'spinner',
  
  // Controls
  CONTROLS: 'controls',
  TOOLBAR: 'toolbar',
  ACTIONS: 'actions',
  
  // Layout
  SIDEBAR: 'sidebar',
  MAIN: 'main',
  ASIDE: 'aside',
  OVERLAY: 'overlay',
  MODAL: 'modal'
} as const;

/**
 * Helper function to create element-specific ID generators
 */
export function createElementIdGenerator(componentName: string) {
  const componentId = getComponentId(componentName);
  
  return {
    container: () => generateId(componentId, ELEMENT_TYPES.CONTAINER),
    header: () => generateId(componentId, ELEMENT_TYPES.HEADER),
    button: (type?: string) => generateId(componentId, ELEMENT_TYPES.BUTTON, type),
    controls: () => generateId(componentId, ELEMENT_TYPES.CONTROLS),
    content: () => generateId(componentId, ELEMENT_TYPES.CONTENT),
    card: () => generateId(componentId, ELEMENT_TYPES.CARD),
    list: () => generateId(componentId, ELEMENT_TYPES.LIST),
    item: () => generateId(componentId, ELEMENT_TYPES.ITEM),
    loading: () => generateId(componentId, ELEMENT_TYPES.LOADING),
    error: () => generateId(componentId, ELEMENT_TYPES.ERROR),
    custom: (elementType: string, suffix?: string) => generateId(componentId, elementType, suffix)
  };
}

// Development mode helpers
export const DEV_HELPERS = {
  /**
   * Log all registered IDs to console
   */
  logAllIds: () => {
    console.group('🆔 Element ID Registry');
    for (const [id, info] of idRegistry) {
      console.log(`${id}:`, info);
    }
    console.groupEnd();
  },
  
  /**
   * Find elements by component name
   */
  findByComponent: (componentName: string) => {
    const componentId = getComponentId(componentName);
    const matches = Array.from(idRegistry.entries()).filter(([id]) => 
      id.startsWith(componentId)
    );
    console.table(matches);
    return matches;
  },
  
  /**
   * Get ID usage statistics
   */
  getStats: () => {
    const stats = getIdStats();
    console.table(stats);
    return stats;
  }
};

// Export for browser console access in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  (window as any).PRSNL_ID_UTILS = {
    generateId,
    getComponentId,
    getIdRegistry,
    getIdStats,
    resetCounters,
    ELEMENT_TYPES,
    DEV_HELPERS
  };
}