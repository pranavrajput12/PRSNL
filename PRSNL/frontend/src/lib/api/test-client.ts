/**
 * Test file to verify the generated OpenAPI client works
 */

import {
  getHealthCheckApiHealthGetQueryKey,
  getSearchItemsApiSearchGetQueryKey,
  createHealthCheckApiHealthGet,
  createSearchItemsApiSearchGet,
  createCaptureItemApiCapturePost,
} from './generated';
import type { CaptureItemApiCapturePostMutationBody } from './generated';

// Example usage demonstrating the generated API client
export function testApiClient() {
  // These are just query key generators, not hooks
  const healthQueryKey = getHealthCheckApiHealthGetQueryKey();
  const searchQueryKey = getSearchItemsApiSearchGetQueryKey({ 
    query: 'test search',
    limit: 10,
    offset: 0,
  });

  // The actual API functions are create* functions
  const healthApiFunction = createHealthCheckApiHealthGet;
  const searchApiFunction = createSearchItemsApiSearchGet;
  const captureApiFunction = createCaptureItemApiCapturePost;

  console.log('Generated API client is working!', {
    healthQueryKey,
    searchQueryKey,
    healthApiFunction,
    searchApiFunction,
    captureApiFunction,
  });
}

// Export generated types for use elsewhere
export type { CaptureRequest, Item, SearchRequest, TimelineResponse } from '../types/generated';
