/**
 * PRSNL API Client
 * Handles all communication with the backend API
 */

import type {
  CaptureRequest,
  CaptureResponse,
  SearchRequest,
  SearchResponse,
  TimelineResponse,
  Item,
  Tag,
  UpdateItemRequest,
  APIError,
  TimelineItem,
  InsightsResponse
} from './types/api';

// Add RequestInit type for fetch API
type RequestInit = {
  method?: string;
  headers?: Record<string, string>;
  body?: string;
  credentials?: 'include' | 'omit' | 'same-origin';
  mode?: 'cors' | 'navigate' | 'no-cors' | 'same-origin';
  cache?: 'default' | 'force-cache' | 'no-cache' | 'no-store' | 'only-if-cached' | 'reload';
};

// Get the API URL from environment variables or use default
// In production (Docker), use the full URL; in dev, use relative URL for Vite proxy
const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 
  (import.meta.env.MODE === 'production' ? 'http://localhost:8001/api' : '/api');

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  status: number;
  
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/**
 * Base fetch function with error handling
 */
async function fetchWithErrorHandling<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  console.log('🔵 API Request:', {
    url: fullUrl,
    method: options.method || 'GET',
    endpoint,
    API_BASE_URL
  });

  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    console.log('🟡 API Response:', {
      url: fullUrl,
      status: response.status,
      statusText: response.statusText,
      ok: response.ok
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('🔴 API Error:', {
        url: fullUrl,
        status: response.status,
        errorData
      });
      throw new ApiError(
        errorData.message || `API request failed with status ${response.status}`,
        response.status
      );
    }

    const data = await response.json();
    console.log('🟢 API Success:', {
      url: fullUrl,
      dataPreview: Array.isArray(data) ? `Array[${data.length}]` : typeof data
    });
    return data;
  } catch (error) {
    console.error('🔴 API Catch Error:', {
      url: fullUrl,
      error: error instanceof Error ? error.message : error
    });
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Network errors or other issues
    throw new ApiError(
      error instanceof Error ? error.message : 'Unknown API error',
      0
    );
  }
}

/**
 * Capture a new item in the knowledge vault
 */
export async function captureItem(
  data: CaptureRequest
): Promise<CaptureResponse> {
  return fetchWithErrorHandling<CaptureResponse>('/capture', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Search items in the knowledge vault
 */
export async function searchItems(
  query: string,
  filters: {
    date?: string;
    type?: string;
    tags?: string;
    mode?: 'keyword' | 'semantic' | 'hybrid';
    limit?: number;
  } = {}
): Promise<SearchResponse> {
  // Use semantic search endpoint if mode is semantic or hybrid
  if (filters.mode === 'semantic' || filters.mode === 'hybrid') {
    const semanticRequest = {
      query: query,
      full_text_query: filters.mode === 'hybrid' ? query : undefined,
      limit: filters.limit || 10,
      offset: 0
    };
    
    const results = await fetchWithErrorHandling<any[]>('/search/semantic', {
      method: 'POST',
      body: JSON.stringify(semanticRequest),
    });
    
    // Transform to match SearchResponse format
    return {
      results: results.map(item => ({
        id: item.id,
        title: item.title,
        url: item.url,
        snippet: item.summary || '',
        tags: item.tags || [],
        created_at: item.created_at,
        type: item.item_type || 'article',
        similarity_score: item.similarity
      }))
    };
  }
  
  // Regular keyword search
  const params = new URLSearchParams();
  
  if (query) params.append('query', query);
  if (filters.date) params.append('date', filters.date);
  if (filters.type) params.append('type', filters.type);
  if (filters.tags) params.append('tags', filters.tags);
  if (filters.limit) params.append('limit', filters.limit.toString());
  
  return fetchWithErrorHandling<SearchResponse>(`/search?${params.toString()}`);
}

/**
 * Get similar items to a specific item
 */
export async function getSimilarItems(id: string, limit: number = 5): Promise<Item[]> {
  return fetchWithErrorHandling<Item[]>(`/search/similar/${id}?limit=${limit}`);
}

/**
 * Transform snake_case to camelCase for a single item
 */
function transformItem(item: any): Item | TimelineItem {
  // If already has camelCase fields, return as is
  if ('createdAt' in item && item.createdAt) {
    return item;
  }
  
  return {
    ...item,
    createdAt: item.created_at || item.createdAt,
    updatedAt: item.updated_at || item.updatedAt,
    itemType: item.item_type || item.itemType,
    thumbnailUrl: item.thumbnail_url || item.thumbnailUrl,
    filePath: item.file_path || item.filePath
  };
}

/**
 * Get timeline items with pagination
 */
export async function getTimeline(page: number = 1, limit: number = 20): Promise<TimelineResponse> {
  // For now, we'll ignore the page parameter since backend uses cursor pagination
  // TODO: Update frontend to use cursor pagination
  const response = await fetchWithErrorHandling<TimelineResponse>(`/timeline?limit=${limit}`);
  
  console.log('Raw timeline response before transform:', response);
  
  // Transform snake_case to camelCase for frontend compatibility
  if (response && response.items) {
    response.items = response.items.map(item => transformItem(item) as TimelineItem);
  }
  
  console.log('Timeline response after transform:', response);
  
  return response;
}

/**
 * Get a single item by ID
 */
export async function getItem(id: string): Promise<Item> {
  return fetchWithErrorHandling<Item>(`/items/${id}`);
}

/**
 * Get recent tags for autocomplete
 */
export async function getRecentTags(): Promise<Tag[]> {
  try {
    return await fetchWithErrorHandling<Tag[]>('/tags');
  } catch (error) {
    console.error('Failed to fetch tags, returning empty array:', error);
    return [];
  }
}

/**
 * Get all tags
 */
export async function getTags(): Promise<{ tags: Tag[] }> {
  const tags = await fetchWithErrorHandling<Tag[]>('/tags');
  
  // Backend returns array directly, frontend expects object with tags array
  return { tags: Array.isArray(tags) ? tags : [] };
}

/**
 * Delete an item by ID
 */
export async function deleteItem(id: string): Promise<void> {
  return fetchWithErrorHandling<void>(`/items/${id}`, {
    method: 'DELETE',
  });
}

/**
 * Update an item by ID
 */
export async function updateItem(
  id: string,
  data: UpdateItemRequest
): Promise<Item> {
  return fetchWithErrorHandling<Item>(`/items/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Get AI suggestions for URL metadata
 */
export async function getAISuggestions(url: string): Promise<{
  title: string;
  summary: string;
  tags: string[];
  category?: string;
}> {
  return fetchWithErrorHandling('/suggest', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

/**
 * Get AI insights data for the dashboard
 */
export async function getInsights(timeRange: string = 'week'): Promise<InsightsResponse> {
  return fetchWithErrorHandling<InsightsResponse>(`/insights?timeRange=${timeRange}`);
}

/**
 * AI Features API
 */
export const aiApi = {
  categorize: {
    single: async (itemId: string) => 
      fetchWithErrorHandling('/categorize', { method: 'POST', body: JSON.stringify({ item_id: itemId }) }),
    bulk: async (limit = 100) => 
      fetchWithErrorHandling('/categorize/bulk', { method: 'POST', body: JSON.stringify({ limit }) }),
    stats: async () => 
      fetchWithErrorHandling('/categories/stats')
  },
  
  duplicates: {
    check: async (url: string, title: string, content?: string) =>
      fetchWithErrorHandling('/duplicates/check', { 
        method: 'POST', 
        body: JSON.stringify({ url, title, content }) 
      }),
    findAll: async (minSimilarity = 0.85) =>
      fetchWithErrorHandling('/duplicates/find-all', { 
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      }),
    merge: async (keepId: string, duplicateIds: string[]) =>
      fetchWithErrorHandling('/duplicates/merge', { 
        method: 'POST', 
        body: JSON.stringify({ keep_id: keepId, duplicate_ids: duplicateIds }) 
      })
  },
  
  summarization: {
    item: async (itemId: string, type: 'brief' | 'detailed' | 'key_points' = 'brief') =>
      fetchWithErrorHandling('/summarization/item', { 
        method: 'POST', 
        body: JSON.stringify({ item_id: itemId, summary_type: type }) 
      }),
    digest: async (type: 'brief' | 'detailed' | 'key_points' = 'brief', period: 'daily' | 'weekly' | 'monthly' = 'daily') =>
      fetchWithErrorHandling('/summarization/digest', { 
        method: 'POST', 
        body: JSON.stringify({ summary_type: type, period }) 
      }),
    topic: async (topic: string, limit = 20) =>
      fetchWithErrorHandling('/summarization/topic', { 
        method: 'POST', 
        body: JSON.stringify({ topic, limit }) 
      })
  },
  
  insights: {
    dashboard: async () =>
      fetchWithErrorHandling('/insights/dashboard'),
    topicClusters: async (minItems = 3) =>
      fetchWithErrorHandling('/insights/topics', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      }),
    contentTrends: async (period = 'month') =>
      fetchWithErrorHandling(`/insights/trends?period=${period}`),
    semanticMap: async (dimensions = '2d') =>
      fetchWithErrorHandling(`/insights/semantic-map?dimensions=${dimensions}`)
  }
};
