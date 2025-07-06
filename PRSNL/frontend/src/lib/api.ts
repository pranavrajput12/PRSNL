/**
 * PRSNL API Client
 * Handles all communication with the backend API
 */

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
async function fetchWithErrorHandling(
  endpoint: string, 
  options: RequestInit = {}
): Promise<any> {
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
  data: {
    url?: string;
    title?: string;
    highlight?: string;
    tags?: string[];
  }
) {
  return fetchWithErrorHandling('/capture', {
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
) {
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
  
  return fetchWithErrorHandling(`${endpoint}?${params.toString()}`);
}

/**
 * Get similar items to a specific item
 */
export async function getSimilarItems(id: string, limit: number = 5) {
  return fetchWithErrorHandling(`/items/${id}/similar?limit=${limit}`);
}

/**
 * Transform snake_case to camelCase for a single item
 */
function transformItem(item: any) {
  // If already has camelCase fields, return as is
  if (item.createdAt) {
    return item;
  }
  
  return {
    ...item,
    createdAt: item.createdAt || item.created_at,
    updatedAt: item.updatedAt || item.updated_at,
    itemType: item.itemType || item.item_type,
    thumbnailUrl: item.thumbnailUrl || item.thumbnail_url,
    filePath: item.filePath || item.file_path
  };
}

/**
 * Get timeline items with pagination
 */
export async function getTimeline(page: number = 1) {
  const response = await fetchWithErrorHandling(`/timeline?page=${page}`);
  
  console.log('Raw timeline response before transform:', response);
  
  // Transform snake_case to camelCase for frontend compatibility
  if (response && response.items) {
    response.items = response.items.map(transformItem);
  }
  
  console.log('Timeline response after transform:', response);
  
  return response;
}

/**
 * Get a single item by ID
 */
export async function getItem(id: string) {
  return fetchWithErrorHandling(`/items/${id}`);
}

/**
 * Get recent tags for autocomplete
 */
export async function getRecentTags() {
  return fetchWithErrorHandling('/tags');
}

/**
 * Get all tags
 */
export async function getTags() {
  const tags = await fetchWithErrorHandling('/tags');
  
  // Backend returns array directly, frontend expects object with tags array
  return { tags: Array.isArray(tags) ? tags : [] };
}

/**
 * Delete an item by ID
 */
export async function deleteItem(id: string) {
  return fetchWithErrorHandling(`/items/${id}`, {
    method: 'DELETE',
  });
}

/**
 * Update an item by ID
 */
export async function updateItem(
  id: string,
  data: {
    title?: string;
    tags?: string[];
    notes?: string;
  }
) {
  return fetchWithErrorHandling(`/items/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}
