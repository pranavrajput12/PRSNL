// Use built-in fetch types instead of node-fetch

// Base API configuration - handle both browser and build environments
const API_BASE_URL =
  typeof window !== 'undefined' && import.meta.env?.VITE_API_URL
    ? import.meta.env.VITE_API_URL
    : 'http://localhost:8000';

/**
 * Custom instance for Orval-generated API clients
 * Provides authentication, error handling, and request/response transformation
 */
export const customInstance = async <T>(config: RequestInit & { url: string }): Promise<T> => {
  const { url, ...requestConfig } = config;

  // Build full URL
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

  // Add default headers
  const headers = new Headers(requestConfig.headers);
  if (!headers.has('Content-Type') && requestConfig.body) {
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
