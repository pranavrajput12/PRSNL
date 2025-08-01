/**
 * PRSNL API Client
 * Handles all communication with the backend API
 */

import type {
  CaptureRequest,
  CaptureResponse,
  SearchResponse,
  TimelineResponse,
  Item,
  Tag,
  UpdateItemRequest,
  TimelineItem,
  InsightsResponse,
  ContentTypesResponse,
} from './types/api';
import { get } from 'svelte/store';
import { authStore } from './stores/unified-auth';

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
async function fetchWithErrorHandling<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  // Debug logging - remove in production
  if (import.meta.env.DEV) {
    console.log('🔵 API Request:', {
      url: fullUrl,
      method: options.method || 'GET',
      endpoint,
      API_BASE_URL,
    });
  }

  // Get auth token from store
  const auth = get(authStore);
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  // Add authorization header if user is authenticated
  if (auth.token) {
    headers['Authorization'] = `Bearer ${auth.token}`;
  }
  
  // Debug logging
  if (import.meta.env.DEV) {
    console.log('🔐 AUTH DEBUG [API_REQUEST]:', {
      endpoint,
      method: options.method || 'GET',
      hasAuth: !!auth.token,
      isAuthenticated: auth.isAuthenticated,
      tokenLength: auth.token?.length || 0,
      userId: auth.user?.id || null
    });
  }

  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers,
      credentials: 'include', // Include cookies for cross-origin requests
    });

    if (import.meta.env.DEV) {
      console.log('🟡 API Response:', {
        url: fullUrl,
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
      });
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('🔴 API Error:', {
        url: fullUrl,
        status: response.status,
        errorData,
      });
      
      // Handle 401 Unauthorized - try to refresh token first
      if (response.status === 401 && !endpoint.includes('/auth/')) {
        if (import.meta.env.DEV) {
          console.log('🔐 AUTH DEBUG [API_401_UNAUTHORIZED]:', {
            endpoint,
            currentAuth: {
              hasToken: !!auth.token,
              hasRefreshToken: !!auth.refreshToken,
              isAuthenticated: auth.isAuthenticated,
              userId: auth.user?.id
            }
          });
        }
        
        // Try to refresh the token once
        const { authActions } = await import('./stores/unified-auth');
        if (import.meta.env.DEV) {
          console.log('🔐 AUTH DEBUG [API_REFRESH_ATTEMPT]:', { endpoint });
        }
        
        const refreshed = await authActions.refreshToken();
        
        if (refreshed) {
          if (import.meta.env.DEV) {
            console.log('🔐 AUTH DEBUG [API_REFRESH_SUCCESS]:', { endpoint });
          }
          // Retry the original request with new token
          const newAuth = get(authStore);
          if (newAuth.token) {
            headers['Authorization'] = `Bearer ${newAuth.token}`;
            const retryResponse = await fetch(fullUrl, {
              ...options,
              headers,
              credentials: 'include', // Include cookies for cross-origin requests
            });
            
            if (retryResponse.ok) {
              if (import.meta.env.DEV) {
                console.log('🔐 AUTH DEBUG [API_RETRY_SUCCESS]:', { endpoint, status: retryResponse.status });
              }
              return await retryResponse.json();
            } else {
              if (import.meta.env.DEV) {
                console.log('🔐 AUTH DEBUG [API_RETRY_FAILED]:', { endpoint, status: retryResponse.status });
              }
            }
          }
        } else {
          if (import.meta.env.DEV) {
            console.log('🔐 AUTH DEBUG [API_REFRESH_FAILED]:', { endpoint });
          }
        }
        
        // If refresh failed or retry failed, logout
        if (import.meta.env.DEV) {
          console.log('🔐 AUTH DEBUG [API_FORCING_LOGOUT]:', { endpoint, reason: 'auth failed' });
        }
        await authActions.logout();
        
        // Redirect to login
        if (typeof window !== 'undefined') {
          window.location.href = '/auth/login';
        }
      }
      
      throw new ApiError(
        errorData.message || `API request failed with status ${response.status}`,
        response.status
      );
    }

    const data = await response.json();
    if (import.meta.env.DEV) {
      console.log('🟢 API Success:', {
        url: fullUrl,
        dataPreview: Array.isArray(data) ? `Array[${data.length}]` : typeof data,
      });
    }
    return data;
  } catch (error) {
    console.error('🔴 API Catch Error:', {
      url: fullUrl,
      error: error instanceof Error ? error.message : error,
    });
    if (error instanceof ApiError) {
      throw error;
    }

    // Network errors or other issues
    throw new ApiError(error instanceof Error ? error.message : 'Unknown API error', 0);
  }
}

/**
 * Capture a new item in the knowledge vault
 */
export async function captureItem(data: CaptureRequest): Promise<CaptureResponse> {
  // Check if files are uploaded
  const hasFiles = data.uploaded_files && data.uploaded_files.length > 0;

  if (hasFiles) {
    // Use FormData for file uploads
    const formData = new FormData();

    // Add form fields
    if (data.url) formData.append('url', data.url);
    if (data.title) formData.append('title', data.title);
    if (data.highlight) formData.append('highlight', data.highlight);
    if (data.content_type) formData.append('content_type', data.content_type);
    if (data.enable_summarization)
      formData.append('enable_summarization', data.enable_summarization.toString());
    if (data.tags) formData.append('tags', JSON.stringify(data.tags));

    // Add files if they exist
    if (data.uploaded_files) {
      data.uploaded_files.forEach((file) => {
        formData.append('files', file);
      });
    }

    // Use fetch directly for file uploads (no JSON content-type)
    const response = await fetch(`${API_BASE_URL}/file/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || 'File upload failed');
    }

    return await response.json();
  } else {
    // Use regular JSON API for non-file uploads
    return fetchWithErrorHandling<CaptureResponse>('/capture', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
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
    threshold?: number;
    include_duplicates?: boolean;
  } = {}
): Promise<SearchResponse> {
  // Use semantic search endpoint if mode is semantic or hybrid
  if (filters.mode === 'semantic' || filters.mode === 'hybrid') {
    const semanticRequest = {
      query: query,
      full_text_query: filters.mode === 'hybrid' ? query : undefined,
      limit: filters.limit || 10,
      offset: 0,
    };

    const response = await fetchWithErrorHandling<{ items: any[] }>('/search/semantic', {
      method: 'POST',
      body: JSON.stringify(semanticRequest),
    });

    // Transform to match SearchResponse format
    return {
      results: (response.items || []).map((item) => ({
        id: item.id,
        title: item.title,
        url: item.url,
        snippet: item.summary || '',
        tags: item.tags || [],
        created_at: item.createdAt || item.created_at,
        type: item.type || item.item_type,
        similarity_score: item.similarity_score || item.similarity,
      })),
      total: response.items?.length || 0,
      query: query,
      search_type: filters.mode || 'semantic',
      timestamp: new Date().toISOString(),
      user_id: 'current',
      request_params: {
        search_type: filters.mode || 'semantic',
        limit: filters.limit || 10,
        threshold: filters.threshold || 0.3,
        include_duplicates: filters.include_duplicates || false,
      },
    };
  }

  // Fallback: Use enhanced search API for keyword search too
  const keywordSearchRequest = {
    query: query,
    search_type: 'keyword' as const,
    limit: filters.limit || 20,
    threshold: filters.threshold || 0.3,
    include_duplicates: filters.include_duplicates || false,
    filters: {
      ...(filters.type && { type: filters.type }),
      ...(filters.date && {
        date_range: {
          start: filters.date,
          end: filters.date,
        },
      }),
    },
  };

  const response = await fetchWithErrorHandling<SearchResponse>('/search/', {
    method: 'POST',
    body: JSON.stringify(keywordSearchRequest),
  });

  // Transform results to ensure compatibility
  return {
    ...response,
    results: response.results.map((result) => ({
      ...result,
      snippet: result.snippet || '',
      tags: result.tags || [],
      score: result.similarity || result.score || 0,
    })),
  };
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
    filePath: item.file_path || item.filePath,
  };
}

/**
 * Get timeline items with pagination (legacy page-based)
 */
export async function getTimeline(
  _page: number = 1,
  limit: number = 20
): Promise<TimelineResponse> {
  // Legacy page-based pagination - ignores page parameter since backend uses cursor pagination
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
    pageSize: limit,
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
      type: item.type || item.item_type,
      status: item.status,
      thumbnail_url: item.thumbnail_url,
      duration: item.duration,
      platform: item.platform,
      file_path: item.file_path,
      createdAt: item.createdAt || item.created_at,
      updatedAt: item.updatedAt || item.updated_at,
    }));
  }

  if (import.meta.env.DEV) {
    console.log('Timeline response after transform:', transformedResponse);
  }

  return transformedResponse;
}

/**
 * Get timeline items with cursor-based pagination (modern)
 */
export async function getTimelineCursor(
  cursor: string | null = null,
  limit: number = 20
): Promise<TimelineResponse> {
  // Modern cursor-based pagination as supported by backend
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  if (cursor) {
    params.append('cursor', cursor);
  }

  const response = await fetchWithErrorHandling<any>(`/timeline?${params.toString()}`);

  if (import.meta.env.DEV) {
    console.log('Raw timeline response before transform:', response);
  }

  // Transform backend response to match frontend expectations
  const transformedResponse: TimelineResponse = {
    items: [],
    hasMore: response.next_cursor !== null,
    total: response.items?.length || 0,
    pageSize: limit,
    nextCursor: response.next_cursor || null,
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
      type: item.type || item.item_type,
      status: item.status,
      thumbnail_url: item.thumbnail_url,
      duration: item.duration,
      platform: item.platform,
      file_path: item.file_path,
      createdAt: item.createdAt || item.created_at,
      updatedAt: item.updatedAt || item.updated_at,
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

// Simple cache for tags to prevent redundant API calls
let tagsCache: { data: Tag[] | null; timestamp: number } = { data: null, timestamp: 0 };
const TAGS_CACHE_TTL = 30000; // 30 seconds cache

/**
 * Internal function to fetch tags with caching
 */
async function fetchTagsWithCache(): Promise<Tag[]> {
  const now = Date.now();
  
  // Return cached data if it exists and is not expired
  if (tagsCache.data && (now - tagsCache.timestamp) < TAGS_CACHE_TTL) {
    return tagsCache.data;
  }
  
  try {
    const tags = await fetchWithErrorHandling<Tag[]>('/tags');
    tagsCache = { data: tags, timestamp: now };
    return tags;
  } catch (error) {
    console.error('Failed to fetch tags, returning empty array:', error);
    return [];
  }
}

/**
 * Get recent tags for autocomplete
 */
export async function getRecentTags(): Promise<Tag[]> {
  return fetchTagsWithCache();
}

/**
 * Get all tags
 */
export async function getTags(): Promise<{ tags: Tag[] }> {
  const tags = await fetchTagsWithCache();
  
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
export async function updateItem(id: string, data: UpdateItemRequest): Promise<Item> {
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
    body: JSON.stringify({
      url,
      include_title: true,
      include_summary: true,
      include_tags: true,
      include_category: true,
      max_tags: 5,
    }),
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
export async function getTopTags(
  timeRange: string = '30d',
  limit: number = 10
): Promise<{
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
 * Content Types API
 */
export async function getContentTypes(): Promise<ContentTypesResponse> {
  return fetchWithErrorHandling<ContentTypesResponse>('/content-types');
}

/**
 * User Profile API
 */
export const profileApi = {
  getProfile: async () => 
    fetchWithErrorHandling('/profile'),
  
  updateProfile: async (data: {
    name?: string;
    first_name?: string;
    last_name?: string;
  }) =>
    fetchWithErrorHandling('/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  changePassword: async (data: {
    current_password: string;
    new_password: string;
  }) =>
    fetchWithErrorHandling('/profile/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  getStats: async () =>
    fetchWithErrorHandling('/profile/stats'),
  
  deleteAccount: async () =>
    fetchWithErrorHandling('/profile', {
      method: 'DELETE',
    }),
  
  completeOnboarding: async () =>
    fetchWithErrorHandling('/profile/complete-onboarding', {
      method: 'POST',
    }),
};

export const api = {
  get: fetchWithErrorHandling,
  post: <T>(endpoint: string, data: any) =>
    fetchWithErrorHandling<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  delete: <T>(endpoint: string) =>
    fetchWithErrorHandling<T>(endpoint, {
      method: 'DELETE',
    }),
  patch: <T>(endpoint: string, data: any) =>
    fetchWithErrorHandling<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
};

/**
 * AI Features API
 */
export const aiApi = {
  categorize: {
    single: async (itemId: string) =>
      fetchWithErrorHandling('/categorize', {
        method: 'POST',
        body: JSON.stringify({ item_id: itemId }),
      }),
    bulk: async (limit = 100) =>
      fetchWithErrorHandling('/categorize/bulk', {
        method: 'POST',
        body: JSON.stringify({ limit }),
      }),
    stats: async () => fetchWithErrorHandling('/categories/stats'),
  },

  duplicates: {
    check: async (url: string, title: string, content?: string) =>
      fetchWithErrorHandling('/duplicates/check', {
        method: 'POST',
        body: JSON.stringify({ url, title, content }),
      }),
    findAll: async (_minSimilarity = 0.85) =>
      fetchWithErrorHandling('/duplicates/find-all', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      }),
    merge: async (keepId: string, duplicateIds: string[]) =>
      fetchWithErrorHandling('/duplicates/merge', {
        method: 'POST',
        body: JSON.stringify({ keep_id: keepId, duplicate_ids: duplicateIds }),
      }),
  },

  summarization: {
    item: async (itemId: string, type: 'brief' | 'detailed' | 'key_points' = 'brief') =>
      fetchWithErrorHandling('/summarization/item', {
        method: 'POST',
        body: JSON.stringify({ item_id: itemId, summary_type: type }),
      }),
    digest: async (
      type: 'brief' | 'detailed' | 'key_points' = 'brief',
      period: 'daily' | 'weekly' | 'monthly' = 'daily'
    ) =>
      fetchWithErrorHandling('/summarization/digest', {
        method: 'POST',
        body: JSON.stringify({ summary_type: type, period }),
      }),
    topic: async (topic: string, limit = 20) =>
      fetchWithErrorHandling('/summarization/topic', {
        method: 'POST',
        body: JSON.stringify({ topic, limit }),
      }),
  },

  insights: {
    dashboard: async () => fetchWithErrorHandling('/insights/dashboard'),
    topicClusters: async (_minItems = 3) =>
      fetchWithErrorHandling('/insights/topics', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      }),
    contentTrends: async (period = 'month') =>
      fetchWithErrorHandling(`/insights/trends?period=${period}`),
    semanticMap: async (dimensions = '2d') =>
      fetchWithErrorHandling(`/insights/semantic-map?dimensions=${dimensions}`),
  },
};
