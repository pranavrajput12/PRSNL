/**
 * Lazy Loading Infrastructure for PRSNL
 * 
 * This utility provides system-wide lazy loading for heavy components and libraries.
 * Benefits the entire application by reducing initial bundle size and improving performance.
 * 
 * Supported lazy loads:
 * - Syntax highlighters (highlight.js, Shiki)
 * - 3D libraries (Three.js components)
 * - Video players and media libraries
 * - Chart and visualization libraries
 * - Heavy UI components
 */

import { writable } from 'svelte/store';

// Global state for loaded modules
const loadedModules = new Map<string, any>();
const loadingPromises = new Map<string, Promise<any>>();

// Store for tracking loading states
export const loadingStates = writable<Record<string, boolean>>({});

/**
 * Generic lazy loader with caching and error handling
 */
export async function lazyLoad<T>(
  moduleKey: string,
  loader: () => Promise<T>,
  fallback?: T
): Promise<T> {
  // Return cached module if already loaded
  if (loadedModules.has(moduleKey)) {
    return loadedModules.get(moduleKey);
  }

  // Return existing promise if already loading
  if (loadingPromises.has(moduleKey)) {
    return loadingPromises.get(moduleKey);
  }

  // Update loading state
  loadingStates.update(states => ({ ...states, [moduleKey]: true }));

  // Create loading promise
  const loadingPromise = (async () => {
    try {
      console.log(`🔄 Lazy loading: ${moduleKey}`);
      const module = await loader();
      
      // Cache the loaded module
      loadedModules.set(moduleKey, module);
      console.log(`✅ Lazy loaded: ${moduleKey}`);
      
      return module;
    } catch (error) {
      console.error(`❌ Failed to lazy load ${moduleKey}:`, error);
      
      // Use fallback if provided
      if (fallback !== undefined) {
        console.log(`🔄 Using fallback for: ${moduleKey}`);
        loadedModules.set(moduleKey, fallback);
        return fallback;
      }
      
      throw error;
    } finally {
      // Clear loading state
      loadingStates.update(states => ({ ...states, [moduleKey]: false }));
      loadingPromises.delete(moduleKey);
    }
  })();

  // Cache the promise to prevent duplicate loads
  loadingPromises.set(moduleKey, loadingPromise);
  
  return loadingPromise;
}

/**
 * Lazy load syntax highlighter
 */
export async function lazyLoadHighlighter(language?: string) {
  const highlighter = await lazyLoad('highlight.js', async () => {
    const [hljs, ...languageModules] = await Promise.all([
      import('highlight.js/lib/core'),
      // Common languages - load on demand
      import('highlight.js/lib/languages/javascript'),
      import('highlight.js/lib/languages/typescript'),
      import('highlight.js/lib/languages/python'),
      import('highlight.js/lib/languages/json'),
      import('highlight.js/lib/languages/bash'),
      import('highlight.js/lib/languages/markdown')
    ]);

    const [javascript, typescript, python, json, bash, markdown] = languageModules;

    // Register core languages
    hljs.default.registerLanguage('javascript', javascript.default);
    hljs.default.registerLanguage('typescript', typescript.default);
    hljs.default.registerLanguage('python', python.default);
    hljs.default.registerLanguage('json', json.default);
    hljs.default.registerLanguage('bash', bash.default);
    hljs.default.registerLanguage('markdown', markdown.default);

    return hljs.default;
  });

  // Load additional language if specified
  if (language && !highlighter.getLanguage(language)) {
    await lazyLoadLanguage(language, highlighter);
  }

  return highlighter;
}

/**
 * Lazy load specific programming language for syntax highlighting
 */
export async function lazyLoadLanguage(language: string, hljs: any) {
  const languageKey = `highlight-lang-${language}`;
  
  // Skip if already loaded
  if (hljs.getLanguage(language)) {
    return;
  }

  await lazyLoad(languageKey, async () => {
    try {
      const languageModule = await import(`highlight.js/lib/languages/${language}`);
      hljs.registerLanguage(language, languageModule.default);
      return languageModule.default;
    } catch (error) {
      console.warn(`Language ${language} not available in highlight.js`);
      return null;
    }
  });
}

/**
 * Lazy load Three.js for 3D components
 */
export async function lazyLoadThreeJS() {
  return await lazyLoad('three.js', async () => {
    const THREE = await import('three');
    return THREE;
  });
}

/**
 * Lazy load D3.js for data visualizations
 */
export async function lazyLoadD3() {
  return await lazyLoad('d3', async () => {
    const d3 = await import('d3');
    return d3;
  });
}

/**
 * Lazy load video player components
 */
export async function lazyLoadVideoPlayer() {
  return await lazyLoad('video-player', async () => {
    // Placeholder for heavy video player library
    // Could be video.js, plyr, or custom player
    console.log('Loading video player...');
    return { videoPlayer: 'loaded' };
  });
}

/**
 * Lazy load markdown processor with better performance
 */
export async function lazyLoadMarkdownProcessor() {
  return await lazyLoad('markdown-processor', async () => {
    const [marked, highlighter] = await Promise.all([
      import('marked'),
      lazyLoadHighlighter()
    ]);

    // Configure marked with highlighter
    marked.marked.setOptions({
      highlight: (code: string, lang: string) => {
        if (highlighter.getLanguage(lang)) {
          return highlighter.highlight(code, { language: lang }).value;
        }
        return code;
      },
      gfm: true,
      breaks: true
    });

    return {
      marked: marked.marked,
      highlighter
    };
  });
}

/**
 * Preload modules in background for better UX
 */
export function preloadModules(modules: string[]) {
  // Use requestIdleCallback if available, otherwise setTimeout with shorter delay
  const schedulePreload = (callback: () => void) => {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(callback, { timeout: 500 }); // Reduced timeout
    } else {
      setTimeout(callback, 50); // Significantly reduced delay
    }
  };

  modules.forEach(moduleKey => {
    schedulePreload(() => {
      switch (moduleKey) {
        case 'highlighter':
          lazyLoadHighlighter().catch(() => {/* Silent fail */});
          break;
        case 'three':
          lazyLoadThreeJS().catch(() => {/* Silent fail */});
          break;
        case 'd3':
          lazyLoadD3().catch(() => {/* Silent fail */});
          break;
        case 'markdown':
          lazyLoadMarkdownProcessor().catch(() => {/* Silent fail */});
          break;
      }
    });
  });
}

/**
 * Get loading state for a specific module
 */
export function isModuleLoading(moduleKey: string): boolean {
  return loadingPromises.has(moduleKey);
}

/**
 * Check if module is already loaded
 */
export function isModuleLoaded(moduleKey: string): boolean {
  return loadedModules.has(moduleKey);
}

/**
 * Clear all cached modules (useful for development/testing)
 */
export function clearModuleCache() {
  loadedModules.clear();
  loadingPromises.clear();
  loadingStates.set({});
}

/**
 * Svelte action for lazy loading components
 */
export function lazyLoadAction(node: HTMLElement, moduleKey: string) {
  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        // Small delay to ensure smooth rendering, but fast enough to avoid loading issues
        setTimeout(() => {
          node.dispatchEvent(new CustomEvent('lazyload', { detail: { moduleKey } }));
        }, 50); // Reduced from potential longer delays
        observer.disconnect();
      }
    },
    { 
      threshold: 0.2, // Increased threshold for earlier loading
      rootMargin: '100px' // Increased margin for more aggressive preloading
    }
  );

  observer.observe(node);

  return {
    destroy() {
      observer.disconnect();
    }
  };
}

/**
 * Performance utilities
 */
export const perfUtils = {
  // Measure loading time
  measureLoadTime: (moduleKey: string) => {
    const startTime = performance.now();
    return () => {
      const endTime = performance.now();
      console.log(`⚡ ${moduleKey} loaded in ${(endTime - startTime).toFixed(2)}ms`);
    };
  },

  // Get memory usage if available
  getMemoryUsage: () => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: Math.round(memory.usedJSHeapSize / 1024 / 1024),
        total: Math.round(memory.totalJSHeapSize / 1024 / 1024),
        limit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024)
      };
    }
    return null;
  }
};

export default {
  lazyLoad,
  lazyLoadHighlighter,
  lazyLoadLanguage,
  lazyLoadThreeJS,
  lazyLoadD3,
  lazyLoadVideoPlayer,
  lazyLoadMarkdownProcessor,
  preloadModules,
  isModuleLoading,
  isModuleLoaded,
  clearModuleCache,
  lazyLoadAction,
  loadingStates,
  perfUtils
};