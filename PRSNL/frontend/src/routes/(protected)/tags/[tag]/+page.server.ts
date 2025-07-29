/**
 * Server-side loader for tag-specific library pages
 * 
 * Handles routes like:
 * - /tags/javascript
 * - /tags/react
 * - /tags/cooking
 * etc.
 */

import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, url, fetch }) => {
  const { tag } = params;
  
  // Decode the tag parameter (it might be URL encoded)
  const decodedTag = decodeURIComponent(tag);
  
  // Extract query parameters for filtering
  const contentType = url.searchParams.get('type');
  const category = url.searchParams.get('category');
  const sortBy = url.searchParams.get('sort') || 'updated_date';
  const sortOrder = url.searchParams.get('order') || 'desc';
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = parseInt(url.searchParams.get('limit') || '24');
  const offset = (page - 1) * limit;
  
  try {
    // First, verify the tag exists and get its stats
    const tagStatsUrl = new URL('/api/library/stats/tags', url.origin);
    tagStatsUrl.searchParams.set('tag', decodedTag);
    
    const tagStatsResponse = await fetch(tagStatsUrl.toString());
    if (!tagStatsResponse.ok) {
      throw error(404, {
        message: `Tag "${decodedTag}" not found`,
        hint: 'The tag may not exist or may have been removed.'
      });
    }
    
    const tagStats = await tagStatsResponse.json();
    const tagInfo = tagStats.find((t: any) => t.tag === decodedTag);
    
    if (!tagInfo) {
      throw error(404, {
        message: `Tag "${decodedTag}" not found`,
        hint: 'The tag may not exist in your content library.'
      });
    }
    
    // Build API URL for fetching content
    const apiUrl = new URL('/api/library/content', url.origin);
    apiUrl.searchParams.set('tags', decodedTag);
    apiUrl.searchParams.set('limit', limit.toString());
    apiUrl.searchParams.set('offset', offset.toString());
    apiUrl.searchParams.set('sort_by', sortBy);
    apiUrl.searchParams.set('sort_order', sortOrder);
    
    if (contentType) apiUrl.searchParams.set('content_type', contentType);
    if (category) apiUrl.searchParams.set('category', category);
    
    // Fetch content data
    const contentResponse = await fetch(apiUrl.toString());
    if (!contentResponse.ok) {
      throw new Error(`Failed to fetch content: ${contentResponse.status}`);
    }
    const contentData = await contentResponse.json();
    
    // Fetch content type stats for this tag
    const contentTypeStatsUrl = new URL('/api/library/stats/content-types', url.origin);
    contentTypeStatsUrl.searchParams.set('tags', decodedTag);
    
    const contentTypeResponse = await fetch(contentTypeStatsUrl.toString());
    const contentTypeStats = contentTypeResponse.ok ? await contentTypeResponse.json() : [];
    
    // Fetch category stats for this tag
    const categoryStatsUrl = new URL('/api/library/stats/categories', url.origin);
    categoryStatsUrl.searchParams.set('tags', decodedTag);
    
    const categoryResponse = await fetch(categoryStatsUrl.toString());
    const categoryStats = categoryResponse.ok ? await categoryResponse.json() : [];
    
    // Fetch related tags
    const relatedTagsUrl = new URL('/api/library/stats/tags', url.origin);
    relatedTagsUrl.searchParams.set('related_to', decodedTag);
    relatedTagsUrl.searchParams.set('limit', '10');
    
    const relatedTagsResponse = await fetch(relatedTagsUrl.toString());
    const relatedTags = relatedTagsResponse.ok ? await relatedTagsResponse.json() : [];
    
    return {
      tag: {
        name: decodedTag,
        count: tagInfo.count,
        contentTypes: tagInfo.contentTypes || [],
        categories: tagInfo.categories || []
      },
      content: {
        items: contentData.items || [],
        total: contentData.total || 0,
        hasMore: contentData.has_more || false
      },
      filters: {
        contentType,
        category,
        sortBy,
        sortOrder,
        page,
        limit
      },
      stats: {
        contentTypes: contentTypeStats,
        categories: categoryStats,
        relatedTags: relatedTags.filter((t: any) => t.tag !== decodedTag)
      }
    };
    
  } catch (err) {
    console.error(`Failed to load content for tag ${decodedTag}:`, err);
    
    if (err instanceof Error && err.message.includes('404')) {
      throw error(404, {
        message: `Tag "${decodedTag}" not found`,
        hint: 'The tag may not exist in your content library.'
      });
    }
    
    throw error(500, {
      message: 'Failed to load tag content',
      hint: 'Please try again or contact support if the problem persists'
    });
  }
};