/**
 * UNIFIED CONTENT ROUTE SERVER
 * Route: /items/[id]
 * 
 * This is the main server-side handler for all individual content items
 * in the new unified routing system. It replaces the multiple scattered
 * routes like /item/[id], /recipe/[id], /bookmark/[id], etc.
 * 
 * Features:
 * - Content type validation
 * - Automatic route correction (redirects to correct type if wrong)
 * - Unified data loading for all content types
 * - SEO optimization with proper metadata
 */

import { error } from '@sveltejs/kit';
import { 
  CONTENT_TYPE_ROUTES, 
  generateContentRoute
} from '$lib/config/routingSchema';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, fetch }) => {
  const { id } = params;
  
  console.log(`[ROUTE] Loading content: id=${id}`);
  
  // For items route, use generic content type configuration
  const contentTypeConfig = CONTENT_TYPE_ROUTES.items || {
    type: 'item',
    path: 'items',
    label: 'Item',
    listRoute: '/items'
  };
  
  try {
    // Load the content item using server-side fetch
    const response = await fetch(`/api/items/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch item: ${response.status}`);
    }
    const item = await response.json();
    console.log(`[ROUTE] Loaded item: ${item.title} (type: ${item.type || item.item_type})`);
    
    // For items route, we accept any type - no redirection needed
    const actualItemType = item.type || item.item_type;
    console.log(`[ROUTE] Item type: ${actualItemType}, serving via generic items route`);
    
    // Enhance item with content type configuration
    const enhancedItem = {
      ...item,
      contentTypeConfig
    };
    
    // Generate metadata for SEO
    const metadata = generateMetadata(enhancedItem, contentTypeConfig);
    
    console.log(`[ROUTE] Successfully loaded ${contentTypeConfig.label.toLowerCase()}: ${item.title}`);
    
    return {
      item: enhancedItem,
      contentType: contentTypeConfig,
      metadata,
      breadcrumbs: generateBreadcrumbs(contentTypeConfig, item)
    };
    
  } catch (err: unknown) {
    console.error(`[ROUTE] Error loading item ${id}:`, err);
    
    // If it's already a redirect or error, re-throw it
    if (err && typeof err === 'object' && 'status' in err) {
      throw err;
    }
    
    // Handle API errors
    const errorMessage = err instanceof Error ? err.message : String(err);
    if (errorMessage.includes('404') || errorMessage.includes('not found')) {
      throw error(404, {
        message: 'Content not found',
        details: `The ${contentTypeConfig.label.toLowerCase()} with ID "${id}" could not be found.`
      });
    }
    
    // Handle other errors
    throw error(500, {
      message: 'Failed to load content',
      details: 'An unexpected error occurred while loading the content. Please try again.'
    });
  }
};

/**
 * Generate SEO metadata for the content item
 */
function generateMetadata(item: Record<string, unknown>, contentType: Record<string, unknown>) {
  const title = item.title || 'Untitled';
  const description = item.summary || item.description || `${contentType.label} from your personal knowledge base`;
  const type = contentType.label;
  
  return {
    title: `${title} | ${type} | PRSNL`,
    description: description.slice(0, 160), // SEO description limit
    openGraph: {
      title,
      description,
      type: 'article',
      url: generateContentRoute(contentType.path, item.id),
      image: item.thumbnail_url || item.image_url,
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      image: item.thumbnail_url || item.image_url,
    },
    jsonLd: {
      '@context': 'https://schema.org',
      '@type': getSchemaType(contentType.type),
      name: title,
      description,
      dateCreated: item.created_at || item.createdAt,
      url: generateContentRoute(contentType.path, item.id),
      keywords: item.tags?.join(', '),
    }
  };
}

/**
 * Generate breadcrumb navigation for the content item
 */
function generateBreadcrumbs(contentType: Record<string, unknown>, item: Record<string, unknown>) {
  return [
    { label: 'Dashboard', path: '/' },
    { label: 'Library', path: '/library' },
    { label: contentType.label, path: contentType.listRoute },
    { label: item.title || 'Untitled', path: '', active: true }
  ];
}

/**
 * Map content types to Schema.org types for structured data
 */
function getSchemaType(contentType: string): string {
  const schemaMapping = {
    'article': 'Article',
    'video': 'VideoObject', 
    'code': 'SoftwareSourceCode',
    'recipe': 'Recipe',
    'document': 'DigitalDocument',
    'bookmark': 'WebPage',
    'repository': 'SoftwareSourceCode',
    'conversation': 'Conversation'
  };
  
  return schemaMapping[contentType as keyof typeof schemaMapping] || 'CreativeWork';
}