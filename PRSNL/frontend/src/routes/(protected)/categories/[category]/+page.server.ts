/**
 * Server-side loader for category-specific library pages
 * 
 * Handles routes like:
 * - /categories/development
 * - /categories/learning
 * - /categories/work
 * etc.
 */

import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { CATEGORIES } from '$lib/config/routingSchema';

export const load: PageServerLoad = async ({ params, url, fetch }) => {
  const { category } = params;
  
  // Validate category
  const categoryConfig = CATEGORIES[category as keyof typeof CATEGORIES];
  if (!categoryConfig) {
    throw error(404, {
      message: `Category "${category}" not found`,
      hint: 'Available categories: ' + Object.keys(CATEGORIES).join(', ')
    });
  }
  
  // Extract query parameters for filtering
  const contentType = url.searchParams.get('type');
  const tags = url.searchParams.get('tags')?.split(',').filter(Boolean) || [];
  const sortBy = url.searchParams.get('sort') || 'updated_date';
  const sortOrder = url.searchParams.get('order') || 'desc';
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = parseInt(url.searchParams.get('limit') || '24');
  const offset = (page - 1) * limit;
  
  try {
    // Build API URL for fetching content
    const apiUrl = new URL('/api/library/content', url.origin);
    apiUrl.searchParams.set('category', category);
    apiUrl.searchParams.set('limit', limit.toString());
    apiUrl.searchParams.set('offset', offset.toString());
    apiUrl.searchParams.set('sort_by', sortBy);
    apiUrl.searchParams.set('sort_order', sortOrder);
    
    if (contentType) apiUrl.searchParams.set('content_type', contentType);
    if (tags.length > 0) apiUrl.searchParams.set('tags', tags.join(','));
    
    // Fetch content data
    const contentResponse = await fetch(apiUrl.toString());
    if (!contentResponse.ok) {
      throw new Error(`Failed to fetch content: ${contentResponse.status}`);
    }
    const contentData = await contentResponse.json();
    
    // Fetch content type stats for this category
    const contentTypeStatsUrl = new URL('/api/library/stats/content-types', url.origin);
    contentTypeStatsUrl.searchParams.set('category', category);
    
    const contentTypeResponse = await fetch(contentTypeStatsUrl.toString());
    const contentTypeStats = contentTypeResponse.ok ? await contentTypeResponse.json() : [];
    
    // Fetch tag stats for this category
    const tagStatsUrl = new URL('/api/library/stats/tags', url.origin);
    tagStatsUrl.searchParams.set('category', category);
    tagStatsUrl.searchParams.set('limit', '20');
    
    const tagResponse = await fetch(tagStatsUrl.toString());
    const tagStats = tagResponse.ok ? await tagResponse.json() : [];
    
    return {
      category: categoryConfig,
      content: {
        items: contentData.items || [],
        total: contentData.total || 0,
        hasMore: contentData.has_more || false
      },
      filters: {
        contentType,
        tags,
        sortBy,
        sortOrder,
        page,
        limit
      },
      stats: {
        contentTypes: contentTypeStats,
        tags: tagStats
      }
    };
    
  } catch (err) {
    console.error(`Failed to load content for category ${category}:`, err);
    throw error(500, {
      message: 'Failed to load category content',
      hint: 'Please try again or contact support if the problem persists'
    });
  }
};