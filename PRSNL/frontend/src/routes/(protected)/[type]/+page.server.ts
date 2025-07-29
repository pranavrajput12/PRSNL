/**
 * Server-side loader for content type-specific library pages
 * 
 * Handles routes like:
 * - /library/articles
 * - /library/videos  
 * - /library/code
 * etc.
 */

import { error, redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { CONTENT_TYPE_ROUTES } from '$lib/config/routingSchema';

export const load: PageServerLoad = async ({ params, url, fetch }) => {
  const { type } = params;
  
  // Validate content type
  const contentTypeConfig = Object.values(CONTENT_TYPE_ROUTES).find(ct => ct.path === type);
  if (!contentTypeConfig) {
    throw error(404, {
      message: `Content type "${type}" not found`,
      hint: 'Available types: ' + Object.values(CONTENT_TYPE_ROUTES).map(ct => ct.path).join(', ')
    });
  }
  
  // Extract query parameters for filtering
  const category = url.searchParams.get('category');
  const tags = url.searchParams.get('tags')?.split(',').filter(Boolean) || [];
  const sortBy = url.searchParams.get('sort') || 'updated_date';
  const sortOrder = url.searchParams.get('order') || 'desc';
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = parseInt(url.searchParams.get('limit') || '24');
  const offset = (page - 1) * limit;
  
  try {
    // Build API URL for fetching content
    const apiUrl = new URL('/api/library/content', url.origin);
    apiUrl.searchParams.set('content_type', contentTypeConfig.type);
    apiUrl.searchParams.set('limit', limit.toString());
    apiUrl.searchParams.set('offset', offset.toString());
    apiUrl.searchParams.set('sort_by', sortBy);
    apiUrl.searchParams.set('sort_order', sortOrder);
    
    if (category) apiUrl.searchParams.set('category', category);
    if (tags.length > 0) apiUrl.searchParams.set('tags', tags.join(','));
    
    // Fetch content data
    const contentResponse = await fetch(apiUrl.toString());
    if (!contentResponse.ok) {
      throw new Error(`Failed to fetch content: ${contentResponse.status}`);
    }
    const contentData = await contentResponse.json();
    
    // Fetch category stats for this content type
    const categoryStatsUrl = new URL('/api/library/stats/categories', url.origin);
    categoryStatsUrl.searchParams.set('content_type', contentTypeConfig.type);
    
    const categoryResponse = await fetch(categoryStatsUrl.toString());
    const categoryStats = categoryResponse.ok ? await categoryResponse.json() : [];
    
    // Fetch tag stats for this content type
    const tagStatsUrl = new URL('/api/library/stats/tags', url.origin);
    tagStatsUrl.searchParams.set('content_type', contentTypeConfig.type);
    tagStatsUrl.searchParams.set('limit', '20');
    
    const tagResponse = await fetch(tagStatsUrl.toString());
    const tagStats = tagResponse.ok ? await tagResponse.json() : [];
    
    return {
      contentType: contentTypeConfig,
      content: {
        items: contentData.items || [],
        total: contentData.total || 0,
        hasMore: contentData.has_more || false
      },
      filters: {
        category,
        tags,
        sortBy,
        sortOrder,
        page,
        limit
      },
      stats: {
        categories: categoryStats,
        tags: tagStats
      }
    };
    
  } catch (err) {
    console.error(`Failed to load content for type ${type}:`, err);
    throw error(500, {
      message: 'Failed to load content',
      hint: 'Please try again or contact support if the problem persists'
    });
  }
};