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
// Always use relative URL so it works with proxies (nginx in prod, vite in dev)
const API_BASE_URL = '/api';

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
  // Debug logging - remove in production
  if (import.meta.env.DEV) {
    console.log('🔵 API Request:', {
      url: fullUrl,
      method: options.method || 'GET',
      endpoint,
      API_BASE_URL
    });
  }

  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (import.meta.env.DEV) {
      console.log('🟡 API Response:', {
        url: fullUrl,
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      });
    }

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
    if (import.meta.env.DEV) {
      console.log('🟢 API Success:', {
        url: fullUrl,
        dataPreview: Array.isArray(data) ? `Array[${data.length}]` : typeof data
      });
    }
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
    
    const response = await fetchWithErrorHandling<{items: any[]}>('/search/semantic', {
      method: 'POST',
      body: JSON.stringify(semanticRequest),
    });
    
    // Transform to match SearchResponse format
    return {
      results: (response.items || []).map(item => ({
        id: item.id,
        title: item.title,
        url: item.url,
        snippet: item.summary || '',
        tags: item.tags || [],
        created_at: item.createdAt || item.created_at,
        type: item.type || item.item_type || 'article',
        similarity_score: item.similarity_score || item.similarity
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
  const response = await fetchWithErrorHandling<any>(`/timeline?limit=${limit}`);
  
  if (import.meta.env.DEV) {
    console.log('Raw timeline response before transform:', response);
  }
  
  // Transform backend response to match frontend expectations
  const transformedResponse: TimelineResponse = {
    items: [],
    hasMore: response.next_cursor !== null,
    // Include additional fields that might be used
    total: response.items?.length || 0,
    pageSize: limit
  } as any;
  
  // Transform items if they exist
  if (response && response.items && Array.isArray(response.items)) {
    transformedResponse.items = response.items.map((item: any) => ({
      ...transformItem(item),
      // Map summary to snippet for TimelineItem interface
      snippet: item.summary || item.snippet || '',
      // Ensure all required fields are present
      id: item.id,
      title: item.title || 'Untitled',
      url: item.url,
      tags: item.tags || [],
      created_at: item.createdAt || item.created_at,
      // Preserve summary for the timeline page
      summary: item.summary || '',
      // Include additional fields the timeline might use
      type: item.item_type || item.type || 'article',
      status: item.status,
      thumbnail_url: item.thumbnail_url,
      duration: item.duration,
      platform: item.platform,
      file_path: item.file_path,
      createdAt: item.createdAt || item.created_at,
      updatedAt: item.updatedAt || item.updated_at
    }));
  }
  
  if (import.meta.env.DEV) {
    console.log('Timeline response after transform:', transformedResponse);
  }
  
  return transformedResponse;
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
export async function getInsights(timeRange: string = '30d'): Promise<InsightsResponse> {
  return fetchWithErrorHandling<InsightsResponse>(`/insights?time_range=${timeRange}`);
}

/**
 * Get timeline trends data for Knowledge DNA visualization
 */
export async function getTimelineTrends(timeRange: string = '30d'): Promise<{
  timeline_data: Array<{
    date: string;
    articles: number;
    videos: number;
    notes: number;
    bookmarks: number;
  }>;
  time_range: string;
  total_days: number;
  generated_at: string;
}> {
  return fetchWithErrorHandling(`/insights/timeline-trends?time_range=${timeRange}`);
}

/**
 * Get top tags for Memory Palace visualization
 */
export async function getTopTags(timeRange: string = '30d', limit: number = 10): Promise<{
  tags: Array<{
    name: string;
    usage_count: number;
    latest_use: string;
    weight: number;
    recency_weight: number;
  }>;
  time_range: string;
  total_tags: number;
  max_usage: number;
  generated_at: string;
}> {
  return fetchWithErrorHandling(`/insights/top-tags?time_range=${timeRange}&limit=${limit}`);
}

/**
 * Get personality analysis for Cognitive Fingerprint visualization
 */
export async function getPersonalityAnalysis(timeRange: string = '30d'): Promise<{
  personality: {
    type: string;
    name: string;
    description: string;
    traits: string[];
    icon: string;
    confidence: number;
    scores: Record<string, number>;
    analysis_factors: {
      content_variety: number;
      tag_diversity: number;
      temporal_consistency: number;
      total_items: number;
    };
  };
  analysis_data: {
    content_distribution: Array<{ type: string; count: number }>;
    top_tags: Array<{ name: string; usage: number }>;
    temporal_pattern: Array<{ date: string; count: number }>;
  };
  time_range: string;
  generated_at: string;
}> {
  return fetchWithErrorHandling(`/insights/personality-analysis?time_range=${timeRange}`);
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
