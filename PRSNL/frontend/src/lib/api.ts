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

// Get the API URL from environment variables or use default
// Use relative URL to leverage Vite's proxy configuration
const API_BASE_URL = import.meta.env.PUBLIC_API_URL || '/api';

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
  const params = new URLSearchParams();
  
  if (query) params.append('query', query);
  if (filters.date) params.append('date', filters.date);
  if (filters.type) params.append('type', filters.type);
  if (filters.tags) params.append('tags', filters.tags);
  if (filters.mode) params.append('mode', filters.mode);
  if (filters.limit) params.append('limit', filters.limit.toString());
  
  // Use semantic search endpoint if mode is semantic or hybrid
  const endpoint = (filters.mode === 'semantic' || filters.mode === 'hybrid') 
    ? '/search/semantic' 
    : '/search';
  
  return fetchWithErrorHandling<SearchResponse>(`${endpoint}?${params.toString()}`);
}

/**
 * Get similar items to a specific item
 */
export async function getSimilarItems(id: string, limit: number = 5): Promise<Item[]> {
  return fetchWithErrorHandling<Item[]>(`/items/${id}/similar?limit=${limit}`);
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
export async function getTimeline(page: number = 1): Promise<TimelineResponse> {
  const response = await fetchWithErrorHandling<TimelineResponse>(`/timeline?page=${page}`);
  
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
  return fetchWithErrorHandling('/ai/suggest', {
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
