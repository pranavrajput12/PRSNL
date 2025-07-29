/**
 * UNIFIED CONTENT ROUTE SERVER
 * Route: /[type]/[id]
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

import { error, redirect } from '@sveltejs/kit';
import { getItem } from '$lib/api';
import { 
  CONTENT_TYPE_ROUTES, 
  generateContentRoute, 
  parseContentRoute 
} from '$lib/config/routingSchema';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, url, fetch }) => {
  const { type, id } = params;
  
  console.log(`[ROUTE] Loading content: type=${type}, id=${id}`);
  
  // Validate that the content type exists in our routing system
  const contentTypeConfig = Object.values(CONTENT_TYPE_ROUTES).find(ct => ct.path === type);
  if (!contentTypeConfig) {
    console.error(`[ROUTE] Invalid content type: ${type}`);
    throw error(404, {
      message: 'Content type not found',
      details: `The content type "${type}" is not supported. Available types: ${Object.keys(CONTENT_TYPE_ROUTES).join(', ')}`
    });
  }
  
  try {
    // Load the content item using server-side fetch
    const response = await fetch(`/api/items/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch item: ${response.status}`);
    }
    const item = await response.json();
    console.log(`[ROUTE] Loaded item: ${item.title} (type: ${item.type || item.item_type})`);
    
    // Validate that the item's actual type matches the requested route
    const actualItemType = item.type || item.item_type;
    const expectedType = contentTypeConfig.type;
    
    // Handle type mismatches by redirecting to the correct route
    if (actualItemType && actualItemType !== expectedType) {
      console.log(`[ROUTE] Type mismatch: expected ${expectedType}, got ${actualItemType}. Redirecting...`);
      
      // Find the correct content type configuration
      const correctTypeConfig = Object.values(CONTENT_TYPE_ROUTES).find(ct => ct.type === actualItemType);
      if (correctTypeConfig) {
        const correctRoute = generateContentRoute(correctTypeConfig.path, id);
        console.log(`[ROUTE] Redirecting to correct route: ${correctRoute}`);
        throw redirect(301, correctRoute);
      } else {
        // If we can't find a specific route but we're already on items route, continue
        if (type === 'items') {
          console.log(`[ROUTE] Generic items route being used for type ${actualItemType}`);
        } else {
          // Otherwise redirect to generic items route
          console.log(`[ROUTE] No specific route found for type ${actualItemType}, redirecting to generic route`);
          throw redirect(301, `/items/${id}`);
        }
      }
    }
    
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
    
  } catch (err: any) {
    console.error(`[ROUTE] Error loading item ${id}:`, err);
    
    // If it's already a redirect or error, re-throw it
    if (err?.status) {
      throw err;
    }
    
    // Handle API errors
    if (err?.message?.includes('404') || err?.message?.includes('not found')) {
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
function generateMetadata(item: any, contentType: any) {
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
function generateBreadcrumbs(contentType: any, item: any) {
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