import { getApiConfig } from '../config/config';

/**
 * Get the API base URL for server-side requests
 * Now uses the centralized configuration service with Zod validation
 */
export function getServerApiUrl(): string {
  try {
    const apiConfig = getApiConfig();
    return apiConfig.baseUrl;
  } catch (error) {
    console.warn('⚠️ Failed to get API config, using fallback:', error);
    // Fallback to environment variable or default
    return import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';
  }
}

/**
 * Get WebSocket URL for real-time connections
 */
export function getWebSocketUrl(): string {
  try {
    const apiConfig = getApiConfig();
    return apiConfig.wsUrl;
  } catch (error) {
    console.warn('⚠️ Failed to get WebSocket config, using fallback:', error);
    // Fallback to environment variable or default
    return import.meta.env.PUBLIC_WS_URL || 'ws://localhost:8000';
  }
}

/**
 * Get API endpoint URL for server-side requests
 */
export function getApiEndpoint(path: string): string {
  const baseUrl = getServerApiUrl();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}/api${cleanPath}`;
}

/**
 * Get API configuration for timeout and retry settings
 */
export function getApiOptions() {
  try {
    const apiConfig = getApiConfig();
    return {
      timeout: apiConfig.timeout,
      retries: apiConfig.retries,
    };
  } catch (error) {
    console.warn('⚠️ Failed to get API options, using defaults:', error);
    return {
      timeout: 30000,
      retries: 3,
    };
  }
}