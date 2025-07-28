/**
 * Svelte Action for Automatic Element ID Assignment
 * 
 * This action automatically assigns unique IDs to DOM elements
 * for better design communication and debugging.
 * 
 * Usage:
 * <div use:autoId="container">...</div>
 * <button use:autoId={{type: "button", component: "VoiceChat"}}>Click</button>
 * <div use:autoId={{type: "header", suffix: "main"}}>...</div>
 */

import { generateId, getComponentId, autoGenerateId, ELEMENT_TYPES } from '$lib/utils/elementIds';
import { get } from 'svelte/store';
import { elementRegistry } from '$lib/stores/elementRegistry';

export interface AutoIdOptions {
  /** Element type (e.g., 'button', 'container') */
  type: string;
  /** Component name override (auto-detected if not provided) */
  component?: string;
  /** Additional suffix for specificity */
  suffix?: string;
  /** Whether to register in development overlay */
  register?: boolean;
  /** Custom prefix instead of component-based naming */
  prefix?: string;
}

/**
 * Svelte action to automatically assign unique IDs to elements
 * @param node - The DOM element
 * @param parameter - String (element type) or AutoIdOptions object
 */
export function autoId(node: HTMLElement, parameter: string | AutoIdOptions) {
  let assignedId: string;
  let isRegistered = false;

  function updateId(param: string | AutoIdOptions) {
    // Parse parameter
    const options: AutoIdOptions = typeof param === 'string' 
      ? { type: param, register: true }
      : { register: true, ...param };

    // Generate the ID
    if (options.prefix) {
      // Use custom prefix
      assignedId = options.suffix 
        ? `${options.prefix}-${options.type}-${options.suffix}`
        : `${options.prefix}-${options.type}`;
    } else if (options.component) {
      // Use specified component
      const componentId = getComponentId(options.component);
      assignedId = generateId(componentId, options.type, options.suffix);
    } else {
      // Auto-detect component (fallback to 'unknown')
      assignedId = autoGenerateId(options.type);
    }

    // Assign the ID to the element
    node.id = assignedId;
    
    // Add data attributes for debugging
    if (process.env.NODE_ENV === 'development') {
      node.setAttribute('data-auto-id', 'true');
      node.setAttribute('data-element-type', options.type);
      if (options.component) {
        node.setAttribute('data-component', options.component);
      }
      if (options.suffix) {
        node.setAttribute('data-suffix', options.suffix);
      }
    }

    // Register in the element registry for development overlay
    if (options.register && process.env.NODE_ENV === 'development') {
      elementRegistry.register({
        id: assignedId,
        element: node,
        type: options.type,
        component: options.component || 'auto-detected',
        suffix: options.suffix,
        timestamp: new Date()
      });
      isRegistered = true;
    }
  }

  // Initial setup
  updateId(parameter);

  // Return action object
  return {
    update(newParameter: string | AutoIdOptions) {
      // Unregister old ID if needed
      if (isRegistered) {
        elementRegistry.unregister(assignedId);
        isRegistered = false;
      }
      
      // Update with new parameter
      updateId(newParameter);
    },
    
    destroy() {
      // Clean up registration
      if (isRegistered) {
        elementRegistry.unregister(assignedId);
      }
      
      // Clean up development attributes
      if (process.env.NODE_ENV === 'development') {
        node.removeAttribute('data-auto-id');
        node.removeAttribute('data-element-type');
        node.removeAttribute('data-component');
        node.removeAttribute('data-suffix');
      }
    }
  };
}

/**
 * Specialized action for common element types
 */
export const autoIdPresets = {
  /**
   * Container elements
   */
  container: (node: HTMLElement, options?: Omit<AutoIdOptions, 'type'>) =>
    autoId(node, { type: ELEMENT_TYPES.CONTAINER, ...options }),

  /**
   * Button elements
   */
  button: (node: HTMLElement, options?: Omit<AutoIdOptions, 'type'>) =>
    autoId(node, { type: ELEMENT_TYPES.BUTTON, ...options }),

  /**
   * Header elements
   */
  header: (node: HTMLElement, options?: Omit<AutoIdOptions, 'type'>) =>
    autoId(node, { type: ELEMENT_TYPES.HEADER, ...options }),

  /**
   * Card elements
   */
  card: (node: HTMLElement, options?: Omit<AutoIdOptions, 'type'>) =>
    autoId(node, { type: ELEMENT_TYPES.CARD, ...options }),

  /**
   * Controls/toolbar elements
   */
  controls: (node: HTMLElement, options?: Omit<AutoIdOptions, 'type'>) =>
    autoId(node, { type: ELEMENT_TYPES.CONTROLS, ...options }),

  /**
   * Loading/spinner elements
   */
  loading: (node: HTMLElement, options?: Omit<AutoIdOptions, 'type'>) =>
    autoId(node, { type: ELEMENT_TYPES.LOADING, ...options })
};

/**
 * Helper to create component-specific auto-ID functions
 * @param componentName - Name of the component
 * @returns Object with preset functions for the component
 */
export function createAutoIdForComponent(componentName: string) {
  return {
    container: (node: HTMLElement, suffix?: string) =>
      autoId(node, { type: ELEMENT_TYPES.CONTAINER, component: componentName, suffix }),
    
    header: (node: HTMLElement, suffix?: string) =>
      autoId(node, { type: ELEMENT_TYPES.HEADER, component: componentName, suffix }),
    
    button: (node: HTMLElement, suffix?: string) =>
      autoId(node, { type: ELEMENT_TYPES.BUTTON, component: componentName, suffix }),
    
    content: (node: HTMLElement, suffix?: string) =>
      autoId(node, { type: ELEMENT_TYPES.CONTENT, component: componentName, suffix }),
    
    controls: (node: HTMLElement, suffix?: string) =>
      autoId(node, { type: ELEMENT_TYPES.CONTROLS, component: componentName, suffix }),
    
    custom: (node: HTMLElement, elementType: string, suffix?: string) =>
      autoId(node, { type: elementType, component: componentName, suffix })
  };
}

/**
 * Utility function to batch assign IDs to multiple elements
 * @param elements - Array of [element, options] tuples
 */
export function batchAutoId(elements: Array<[HTMLElement, string | AutoIdOptions]>) {
  const destroyFunctions: Array<() => void> = [];
  
  elements.forEach(([element, options]) => {
    const action = autoId(element, options);
    if (action.destroy) {
      destroyFunctions.push(action.destroy);
    }
  });
  
  return {
    destroy: () => {
      destroyFunctions.forEach(fn => fn());
    }
  };
}

/**
 * Development helper to assign IDs to all elements matching a selector
 * @param selector - CSS selector
 * @param elementType - Type to assign to all matching elements
 * @param component - Component name for all elements
 */
export function assignIdsToSelector(
  selector: string, 
  elementType: string, 
  component?: string
) {
  if (process.env.NODE_ENV !== 'development') {
    console.warn('assignIdsToSelector is only available in development mode');
    return;
  }
  
  const elements = document.querySelectorAll(selector);
  const actions: Array<() => void> = [];
  
  elements.forEach((element, index) => {
    if (element instanceof HTMLElement && !element.id) {
      const action = autoId(element, {
        type: elementType,
        component,
        suffix: `${index + 1}`
      });
      
      if (action.destroy) {
        actions.push(action.destroy);
      }
    }
  });
  
  console.log(`Assigned IDs to ${actions.length} elements matching "${selector}"`);
  
  return {
    destroy: () => actions.forEach(fn => fn())
  };
}

// Export types for TypeScript users
export type { AutoIdOptions };

// Development mode console helpers
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  (window as any).PRSNL_AUTO_ID = {
    autoId,
    autoIdPresets,
    createAutoIdForComponent,
    batchAutoId,
    assignIdsToSelector
  };
}