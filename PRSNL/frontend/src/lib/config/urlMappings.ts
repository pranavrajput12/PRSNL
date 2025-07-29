/**
 * CENTRALIZED URL MAPPINGS - Single Source of Truth
 * 
 * This file contains ALL URL type mappings and aliases used across
 * the entire PRSNL system. Both frontend and backend should reference
 * this for consistency.
 * 
 * CRITICAL: Maximum URL depth is 3 levels (/section/subsection/id)
 */

// Primary type mappings (singular -> plural for routes)
export const TYPE_TO_ROUTE_MAPPING: Record<string, string> = {
  // Core content types
  'article': 'articles',
  'video': 'videos',
  'recipe': 'recipes',
  'bookmark': 'bookmarks',
  'code': 'code',
  'document': 'documents',
  'conversation': 'conversations',
  'repository': 'repositories',
  'screenshot': 'screenshots',
  'item': 'items',
  
  // Common aliases and variations
  'link': 'bookmarks',
  'url': 'bookmarks',
  'repo': 'repositories',
  'doc': 'documents',
  'docs': 'documents',
  'convo': 'conversations',
  'chat': 'conversations',
  'screen': 'screenshots',
  'capture': 'screenshots',
  'snippet': 'code',
  'script': 'code',
  'vid': 'videos',
  'movie': 'videos',
  'clip': 'videos',
  
  // Plurals that map to themselves
  'articles': 'articles',
  'videos': 'videos',
  'recipes': 'recipes',
  'bookmarks': 'bookmarks',
  'documents': 'documents',
  'conversations': 'conversations',
  'repositories': 'repositories',
  'screenshots': 'screenshots',
  'items': 'items'
};

// Reverse mapping for validation (route -> canonical type)
export const ROUTE_TO_TYPE_MAPPING: Record<string, string> = {
  'articles': 'article',
  'videos': 'video',
  'recipes': 'recipe',
  'bookmarks': 'bookmark',
  'code': 'code',
  'documents': 'document',
  'conversations': 'conversation',
  'repositories': 'repository',
  'screenshots': 'screenshot',
  'items': 'item'
};

// Valid route paths (for validation)
export const VALID_CONTENT_ROUTES = new Set(Object.values(TYPE_TO_ROUTE_MAPPING));

// Legacy URL patterns that need redirects
export const LEGACY_PATTERNS = [
  // Deep nested routes (>3 levels) that need flattening
  { from: /^\/code-cortex\/codemirror\/analysis\/(.+)$/, to: '/tools/code-cortex?view=analysis&id=$1' },
  { from: /^\/code-cortex\/codemirror\/repo\/(.+)$/, to: '/repositories/$1' },
  { from: /^\/code-cortex\/docs\/(.+)$/, to: '/documents/$1' },
  { from: /^\/code-cortex\/links\/(.+)$/, to: '/bookmarks/$1' },
  { from: /^\/code-cortex\/projects\/(.+)$/, to: '/code/$1' },
  { from: /^\/code-cortex\/open-source\/(.+)$/, to: '/tools/code-cortex?view=opensource&id=$1' },
  
  // Legacy content patterns
  { from: /^\/c\/([^\/]+)\/([^\/]+)$/, to: '/articles/$2' }, // /c/category/slug
  { from: /^\/p\/([^\/]+)$/, to: '/tools/$1' }, // /p/tool
  { from: /^\/s\/([^\/]+)$/, to: '/info/$1' }, // /s/page (static pages)
  
  // Old item patterns
  { from: /^\/item\/(.+)$/, to: '/items/$1' },
  { from: /^\/recipe\/(.+)$/, to: '/recipes/$1' },
  { from: /^\/bookmark\/(.+)$/, to: '/bookmarks/$1' },
  { from: /^\/article\/(.+)$/, to: '/articles/$1' },
  { from: /^\/video\/(.+)$/, to: '/videos/$1' },
  
  // Library prefixed routes (redirect to cleaner URLs)
  { from: /^\/library\/([^\/]+)\/(.+)$/, to: '/$1/$2' }, // /library/videos/123 -> /videos/123
  { from: /^\/library\/([^\/]+)$/, to: '/$1' }, // /library/videos -> /videos
  
  // Timeline variations
  { from: /^\/discover\/timeline$/, to: '/timeline' },
  { from: /^\/v2\/timeline$/, to: '/timeline' },
  { from: /^\/v3\/timeline$/, to: '/timeline' },
  
  // Tool redirects
  { from: /^\/capture$/, to: '/tools/capture' },
  { from: /^\/import$/, to: '/tools/import' },
  { from: /^\/chat$/, to: '/tools/assistant' },
  { from: /^\/ai$/, to: '/tools/assistant' },
  { from: /^\/voice$/, to: '/tools/voice' },
  
  // Settings/account
  { from: /^\/profile$/, to: '/account/profile' },
  { from: /^\/settings$/, to: '/account/settings' },
  { from: /^\/settings\/voice$/, to: '/account/settings?tab=voice' }
];

/**
 * Get the route path for a given content type
 */
export function getRouteForType(type: string | undefined | null): string {
  if (!type) return 'items';
  
  const normalizedType = type.toLowerCase().trim();
  return TYPE_TO_ROUTE_MAPPING[normalizedType] || 'items';
}

/**
 * Get the canonical type for a route path
 */
export function getTypeForRoute(route: string): string {
  return ROUTE_TO_TYPE_MAPPING[route] || 'item';
}

/**
 * Generate a content URL with max 3 levels
 * Direct pattern: /[type]/[id] (e.g., /videos/123, /articles/abc)
 */
export function generateContentUrl(type: string | undefined, id: string): string {
  const route = getRouteForType(type);
  return `/${route}/${id}`;
}

/**
 * Check if a URL needs redirect and return new URL
 */
export function getRedirectUrl(pathname: string): string | null {
  for (const pattern of LEGACY_PATTERNS) {
    const match = pathname.match(pattern.from);
    if (match) {
      // Replace $1, $2 etc with captured groups
      let newUrl = pattern.to;
      match.forEach((group, index) => {
        if (index > 0) {
          newUrl = newUrl.replace(`$${index}`, group);
        }
      });
      return newUrl;
    }
  }
  return null;
}

/**
 * Validate URL depth (max 3 levels)
 */
export function validateUrlDepth(pathname: string): boolean {
  const segments = pathname.split('/').filter(Boolean);
  return segments.length <= 3;
}

/**
 * Export for backend Python compatibility
 * This can be used to generate a JSON file for Python to consume
 */
export const URL_MAPPINGS_JSON = {
  typeToRoute: TYPE_TO_ROUTE_MAPPING,
  routeToType: ROUTE_TO_TYPE_MAPPING,
  validRoutes: Array.from(VALID_CONTENT_ROUTES),
  legacyPatterns: LEGACY_PATTERNS.map(p => ({
    from: p.from.source,
    to: p.to
  }))
};