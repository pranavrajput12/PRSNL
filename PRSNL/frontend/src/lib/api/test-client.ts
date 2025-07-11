/**
 * Test file to verify the generated OpenAPI client works
 */

import { 
  useHealthCheckApiHealthGetQuery,
  useSearchItemsApiSearchGetQuery,
  useCaptureItemApiCapturePostMutation
} from './generated';

// Example usage demonstrating the generated API client
export function testApiClient() {
  // Health check query
  const healthQuery = useHealthCheckApiHealthGetQuery();
  
  // Search query with parameters
  const searchQuery = useSearchItemsApiSearchGetQuery({
    query: 'test search',
    limit: 10,
    offset: 0
  });
  
  // Capture mutation
  const captureMutation = useCaptureItemApiCapturePostMutation();
  
  console.log('Generated API client is working!', {
    healthQuery,
    searchQuery,
    captureMutation
  });
}

// Export generated types for use elsewhere
export type {
  CaptureRequest,
  Item,
  SearchRequest,
  TimelineResponse
} from '../types/generated';