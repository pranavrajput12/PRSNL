/**
 * UNIFIED ROUTING SCHEMA - PRSNL v2.0
 * 
 * This is the single source of truth for the new hierarchical routing system.
 * All route generation, navigation, and content organization is based on this schema.
 * 
 * Created: January 2025
 * Purpose: Replace chaotic multi-pattern routing with unified, predictable structure
 */

// ===========================
// CORE ROUTE CONFIGURATION
// ===========================

export interface RouteSegment {
  id: string;
  path: string;
  label: string;
  icon: string;
  description: string;
  parent?: string;
  children?: string[];
  access: 'public' | 'protected' | 'admin';
  priority: number;
}

export interface ContentTypeRoute {
  type: string;
  path: string;
  label: string;
  icon: string;
  color: string;
  description: string;
  itemRoute: string;
  listRoute: string;
  searchable: boolean;
  categories: string[];
}

export interface NavigationHierarchy {
  primary: RouteSegment[];
  secondary: { [key: string]: RouteSegment[] };
}

// ===========================
// PRIMARY NAVIGATION STRUCTURE
// ===========================

export const PRIMARY_ROUTES: RouteSegment[] = [
  {
    id: 'dashboard',
    path: '/',
    label: 'Dashboard',
    icon: 'home',
    description: 'Overview of your knowledge base',
    access: 'protected',
    priority: 1,
    children: []
  },
  {
    id: 'library',
    path: '/library',
    label: 'Library',
    icon: 'library',
    description: 'Browse and organize your content',
    access: 'protected',
    priority: 2,
    children: ['library-all', 'library-types', 'library-categories', 'library-tags']
  },
  {
    id: 'discover',
    path: '/discover',
    label: 'Discover',
    icon: 'search',
    description: 'Find and explore content',
    access: 'protected',
    priority: 3,
    children: ['discover-search', 'discover-browse', 'discover-timeline', 'discover-insights']
  },
  {
    id: 'account',
    path: '/account',
    label: 'Account',
    icon: 'user',
    description: 'Profile and account settings',
    access: 'protected',
    priority: 5,
    children: ['account-profile', 'account-settings']
  }
];

// ===========================
// SECONDARY NAVIGATION (NESTED)
// ===========================

export const SECONDARY_ROUTES: { [key: string]: RouteSegment[] } = {
  'library': [
    {
      id: 'library-all',
      path: '/items',
      label: 'All Content',
      icon: 'grid',
      description: 'View all content items',
      parent: 'library',
      access: 'protected',
      priority: 1
    },
    {
      id: 'library-types',
      path: '/items',
      label: 'By Type',
      icon: 'layers',
      description: 'Browse content by type',
      parent: 'library',
      access: 'protected',
      priority: 2,
      children: ['articles', 'videos', 'code', 'recipes', 'documents', 'bookmarks']
    },
    {
      id: 'library-categories',
      path: '/categories',
      label: 'By Category',
      icon: 'folder',
      description: 'Browse content by category',
      parent: 'library',
      access: 'protected',
      priority: 3,
      children: ['development', 'learning', 'work', 'personal', 'reference']
    },
    {
      id: 'library-tags',
      path: '/tags',
      label: 'By Tags', 
      icon: 'tag',
      description: 'Browse content by tags',
      parent: 'library',
      access: 'protected',
      priority: 4
    }
  ],

  'discover': [
    {
      id: 'discover-search',
      path: '/discover/search',
      label: 'Search',
      icon: 'search',
      description: 'Search across all content',
      parent: 'discover',
      access: 'protected',
      priority: 1
    },
    {
      id: 'discover-browse',
      path: '/discover/browse',
      label: 'Browse',
      icon: 'compass',
      description: 'Explore content with filters',
      parent: 'discover',
      access: 'protected',
      priority: 2
    },
    {
      id: 'discover-timeline',
      path: '/discover/timeline',
      label: 'Timeline',
      icon: 'clock',
      description: 'Chronological view of content',
      parent: 'discover',
      access: 'protected',
      priority: 3
    },
    {
      id: 'discover-insights',
      path: '/discover/insights',
      label: 'Insights',
      icon: 'brain',
      description: 'AI-powered content insights',
      parent: 'discover',
      access: 'protected',
      priority: 4
    }
  ],


  'account': [
    {
      id: 'account-profile',
      path: '/account/profile',
      label: 'Profile',
      icon: 'user',
      description: 'View and edit your profile',
      parent: 'account',
      access: 'protected',
      priority: 1
    },
    {
      id: 'account-settings',
      path: '/account/settings',
      label: 'Settings',
      icon: 'settings',
      description: 'Application settings and preferences',
      parent: 'account',
      access: 'protected',
      priority: 2
    }
  ]
};

// ===========================
// CONTENT TYPE ROUTING
// ===========================

export const CONTENT_TYPE_ROUTES: { [key: string]: ContentTypeRoute } = {
  'articles': {
    type: 'article',
    path: 'articles',
    label: 'Articles',
    icon: 'file-text',
    color: '#3B82F6',
    description: 'Written articles and blog posts',
    itemRoute: '/article/[id]',
    listRoute: '/articles',
    searchable: true,
    categories: ['development', 'learning', 'reference']
  },
  'videos': {
    type: 'video',
    path: 'videos',
    label: 'Videos',
    icon: 'play-circle',
    color: '#EF4444',
    description: 'Video content from various platforms',
    itemRoute: '/videos/[id]',
    listRoute: '/videos',
    searchable: true,
    categories: ['learning', 'development', 'personal']
  },
  'code': {
    type: 'code',
    path: 'code',
    label: 'Code',
    icon: 'code',
    color: '#84CC16',
    description: 'Code snippets, repositories, and development resources',
    itemRoute: '/code/[id]',
    listRoute: '/code',
    searchable: true,
    categories: ['development']
  },
  'recipes': {
    type: 'recipe',
    path: 'recipes',
    label: 'Recipes',
    icon: 'chef-hat',
    color: '#FF6B35',
    description: 'Cooking recipes with ingredients and instructions',
    itemRoute: '/recipe/[id]',
    listRoute: '/recipes',
    searchable: true,
    categories: ['personal']
  },
  'documents': {
    type: 'document',
    path: 'documents',
    label: 'Documents',
    icon: 'file',
    color: '#10B981',
    description: 'PDF files and other documents',
    itemRoute: '/documents/[id]',
    listRoute: '/documents',
    searchable: true,
    categories: ['work', 'reference']
  },
  'bookmarks': {
    type: 'bookmark',
    path: 'bookmarks',
    label: 'Bookmarks',
    icon: 'bookmark',
    color: '#6B7280',
    description: 'Saved links and bookmarks',
    itemRoute: '/bookmark/[id]',
    listRoute: '/bookmarks',
    searchable: true,
    categories: ['reference', 'development', 'personal']
  },
  'repositories': {
    type: 'repository',
    path: 'repositories',
    label: 'Repositories',
    icon: 'git-branch',
    color: '#8B5CF6',
    description: 'GitHub repositories and code projects',
    itemRoute: '/repositories/[id]',
    listRoute: '/repositories',
    searchable: true,
    categories: ['development']
  },
  'conversations': {
    type: 'conversation',
    path: 'conversations',
    label: 'Conversations',
    icon: 'message-circle',
    color: '#EC4899',
    description: 'Chat logs and conversations',
    itemRoute: '/conversations/[id]',
    listRoute: '/conversations',
    searchable: true,
    categories: ['personal', 'work']
  },
  'screenshots': {
    type: 'screenshot',
    path: 'screenshots',
    label: 'Screenshots',
    icon: 'image',
    color: '#06B6D4',
    description: 'Screenshots and visual captures',
    itemRoute: '/screenshots/[id]',
    listRoute: '/screenshots',
    searchable: true,
    categories: ['reference', 'work']
  },
  'items': {
    type: 'item',
    path: 'items',
    label: 'Items',
    icon: 'file',
    color: '#6B7280',
    description: 'Generic content items',
    itemRoute: '/items/[id]',
    listRoute: '/items',
    searchable: true,
    categories: ['all']
  }
};

// ===========================
// CATEGORY DEFINITIONS
// ===========================

export const CATEGORIES = {
  'development': {
    id: 'development',
    label: 'Development',
    icon: 'code',
    color: '#84CC16',
    description: 'Programming, tools, frameworks, and technical resources',
    contentTypes: ['code', 'articles', 'videos', 'bookmarks', 'repositories']
  },
  'learning': {
    id: 'learning',
    label: 'Learning',
    icon: 'book-open',
    color: '#06B6D4',
    description: 'Educational content, courses, tutorials, and research',
    contentTypes: ['articles', 'videos', 'documents', 'bookmarks']
  },
  'work': {
    id: 'work',
    label: 'Work',
    icon: 'briefcase',
    color: '#F59E0B',
    description: 'Professional projects, career resources, and productivity',
    contentTypes: ['documents', 'articles', 'conversations', 'bookmarks']
  },
  'personal': {
    id: 'personal',
    label: 'Personal',
    icon: 'heart',
    color: '#EC4899',
    description: 'Personal interests, hobbies, health, and lifestyle',
    contentTypes: ['recipes', 'videos', 'articles', 'bookmarks', 'conversations']
  },
  'reference': {
    id: 'reference',
    label: 'Reference',
    icon: 'library',
    color: '#6B7280',
    description: 'Documentation, guides, and reference materials',
    contentTypes: ['documents', 'articles', 'bookmarks']
  }
};

// ===========================
// ROUTE GENERATION UTILITIES
// ===========================

/**
 * Generate a content item route based on type and ID
 */
export function generateContentRoute(type: string, id: string): string {
  const contentType = CONTENT_TYPE_ROUTES[type];
  if (!contentType) {
    // Fallback to generic item route
    return `/items/${id}`;
  }
  return contentType.itemRoute.replace('[id]', id);
}

/**
 * Generate a content list route based on type
 */
export function generateListRoute(type: string): string {
  const contentType = CONTENT_TYPE_ROUTES[type];
  if (!contentType) {
    return '/items';
  }
  return contentType.listRoute;
}

/**
 * Generate a category route
 */
export function generateCategoryRoute(categoryId: string): string {
  return `/categories/${categoryId}`;
}

/**
 * Generate a tag route
 */
export function generateTagRoute(tag: string): string {
  return `/tags/${encodeURIComponent(tag)}`;
}

/**
 * Parse a route to extract type and ID
 */
export function parseContentRoute(path: string): { type: string | null, id: string | null } {
  // Match pattern: /{type}/{id}
  const match = path.match(/^\/([^\/]+)\/([^\/]+)$/);
  if (!match) {
    return { type: null, id: null };
  }
  
  const [, pathType, id] = match;
  
  // Find content type by path
  const contentType = Object.values(CONTENT_TYPE_ROUTES).find(ct => ct.path === pathType);
  
  return {
    type: contentType?.type || null,
    id: id
  };
}

/**
 * Get breadcrumb trail for a given route
 */
export function getBreadcrumbs(path: string): { label: string; path: string; }[] {
  const breadcrumbs: { label: string; path: string; }[] = [];
  
  // Always start with Dashboard
  breadcrumbs.push({ label: 'Dashboard', path: '/' });
  
  // Parse path segments
  const segments = path.split('/').filter(Boolean);
  let currentPath = '';
  
  for (let i = 0; i < segments.length; i++) {
    currentPath += `/${segments[i]}`;
    
    // Find matching route
    const primaryRoute = PRIMARY_ROUTES.find(r => r.path === currentPath);
    if (primaryRoute) {
      breadcrumbs.push({ label: primaryRoute.label, path: currentPath });
      continue;
    }
    
    // Check secondary routes
    for (const [parent, routes] of Object.entries(SECONDARY_ROUTES)) {
      const route = routes.find(r => r.path === currentPath);
      if (route) {
        breadcrumbs.push({ label: route.label, path: currentPath });
        break;
      }
    }
    
    // Check content type routes
    const contentRoute = parseContentRoute(currentPath);
    if (contentRoute.type && contentRoute.id) {
      const contentType = CONTENT_TYPE_ROUTES[Object.keys(CONTENT_TYPE_ROUTES).find(key => 
        CONTENT_TYPE_ROUTES[key].type === contentRoute.type
      ) || ''];
      
      if (contentType) {
        breadcrumbs.push({ 
          label: contentType.label, 
          path: contentType.listRoute 
        });
        // Item title will be added by the component when item data is loaded
      }
    }
  }
  
  return breadcrumbs;
}

/**
 * Check if a route is currently active
 */
export function isRouteActive(currentPath: string, routePath: string): boolean {
  if (routePath === '/' && currentPath === '/') {
    return true;
  }
  
  if (routePath !== '/' && currentPath.startsWith(routePath)) {
    return true;
  }
  
  return false;
}

/**
 * Get navigation hierarchy for sidebar
 */
export function getNavigationHierarchy(): NavigationHierarchy {
  return {
    primary: PRIMARY_ROUTES,
    secondary: SECONDARY_ROUTES
  };
}

/**
 * Get content type configuration by route path
 */
export function getContentTypeConfig(routePath: string): ContentTypeRoute | null {
  return Object.values(CONTENT_TYPE_ROUTES).find(ct => ct.path === routePath) || null;
}

// ===========================
// MIGRATION HELPERS
// ===========================

/**
 * Legacy route mapping for redirects
 */
export const LEGACY_ROUTE_MAPPINGS: { [key: string]: string } = {
  // Content item routes
  '/item/': '/items/',
  '/recipe/': '/recipes/',
  '/bookmark/': '/bookmarks/',
  '/article/': '/articles/',
  '/video/': '/videos/',
  
  // List routes (already handled by new system)
  
  
  // Account routes
  '/profile': '/account/profile',
  '/settings': '/account/settings'
};

/**
 * Get new route for legacy route
 */
export function getLegacyRouteMapping(legacyPath: string): string | null {
  for (const [oldPattern, newPattern] of Object.entries(LEGACY_ROUTE_MAPPINGS)) {
    if (legacyPath.startsWith(oldPattern)) {
      return legacyPath.replace(oldPattern, newPattern);
    }
  }
  return null;
}

export default {
  PRIMARY_ROUTES,
  SECONDARY_ROUTES,
  CONTENT_TYPE_ROUTES,
  CATEGORIES,
  generateContentRoute,
  generateListRoute,
  generateCategoryRoute,
  generateTagRoute,
  parseContentRoute,
  getBreadcrumbs,
  isRouteActive,
  getNavigationHierarchy,
  LEGACY_ROUTE_MAPPINGS,
  getLegacyRouteMapping
};