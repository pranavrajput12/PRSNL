/**
 * PRSNL API Client
 * Handles all communication with the backend API
 */

// Get the API URL from environment variables or use default
const API_BASE_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000/api';

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
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.message || `API request failed with status ${response.status}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
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
  } = {}
) {
  const params = new URLSearchParams();
  
  if (query) params.append('q', query);
  if (filters.date) params.append('date', filters.date);
  if (filters.type) params.append('type', filters.type);
  if (filters.tags) params.append('tags', filters.tags);
  
  return fetchWithErrorHandling(`/search?${params.toString()}`);
}

/**
 * Get timeline items with pagination
 */
export async function getTimeline(page: number = 1) {
  return fetchWithErrorHandling(`/timeline?page=${page}`);
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
  return fetchWithErrorHandling('/tags/recent');
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
