/**
 * Get the API base URL for server-side requests
 */
export function getServerApiUrl(): string {
  // Use environment variable if available
  if (process.env.VITE_API_URL) {
    return process.env.VITE_API_URL;
  }
  
  // Default to backend service URL
  return 'http://localhost:8000';
}

/**
 * Get API endpoint URL for server-side requests
 */
export function getApiEndpoint(path: string): string {
  const baseUrl = getServerApiUrl();
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}/api${cleanPath}`;
}