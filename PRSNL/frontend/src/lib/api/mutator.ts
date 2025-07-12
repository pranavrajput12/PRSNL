// Use built-in fetch types instead of node-fetch

// Base API configuration - handle both browser and build environments
const API_BASE_URL =
  typeof window !== 'undefined' && import.meta.env?.VITE_API_URL
    ? import.meta.env.VITE_API_URL
    : 'http://localhost:8000';

/**
 * Extended config interface for Orval-generated API clients
 * Includes Orval-specific properties like data and params
 */
interface OrvalRequestConfig extends RequestInit {
  url: string;
  data?: any;
  params?: Record<string, any>;
}

/**
 * Custom instance for Orval-generated API clients
 * Provides authentication, error handling, and request/response transformation
 */
export const customInstance = async <T>(config: OrvalRequestConfig): Promise<T> => {
  const { url, data, params, ...requestConfig } = config;

  // Build full URL with query parameters
  let fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      fullUrl += fullUrl.includes('?') ? '&' + queryString : '?' + queryString;
    }
  }

  // Handle request body
  let body = requestConfig.body;
  if (data && !body) {
    body = typeof data === 'string' ? data : JSON.stringify(data);
  }

  // Add default headers
  const headers = new Headers(requestConfig.headers);
  if (!headers.has('Content-Type') && body && typeof body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  // Get auth token from localStorage if available
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  const response = await fetch(fullUrl, {
    ...requestConfig,
    headers,
    body,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorData;
    try {
      errorData = JSON.parse(errorText);
    } catch {
      errorData = { message: errorText };
    }

    throw new Error(
      `API Error ${response.status}: ${errorData.message || errorData.detail || 'Unknown error'}`
    );
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }

  return response.text() as unknown as T;
};

export default customInstance;
