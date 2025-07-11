// Svelte Query utilities for API calls
import { createQuery, createMutation, type CreateQueryOptions, type CreateMutationOptions } from '@tanstack/svelte-query';
import type { Readable } from 'svelte/store';

// Base API configuration
const API_BASE_URL = '/api';

// Default query options
export const defaultQueryOptions = {
  staleTime: 1000 * 60 * 5, // 5 minutes
  gcTime: 1000 * 60 * 10, // 10 minutes (formerly cacheTime)
  refetchOnWindowFocus: false,
  retry: 1,
} satisfies Partial<CreateQueryOptions<any, any, any, any>>;

// Generic fetch wrapper with error handling
export async function fetchApi<T = any>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

// Query key factory for consistent cache keys
export const queryKeys = {
  all: ['prsnl'] as const,
  captures: () => [...queryKeys.all, 'captures'] as const,
  capture: (id: string) => [...queryKeys.captures(), id] as const,
  captureSearch: (query: string) => [...queryKeys.captures(), 'search', query] as const,
  insights: () => [...queryKeys.all, 'insights'] as const,
  timeline: () => [...queryKeys.all, 'timeline'] as const,
  tags: () => [...queryKeys.all, 'tags'] as const,
  analytics: () => [...queryKeys.all, 'analytics'] as const,
  ai: {
    analyze: (content: string) => [...queryKeys.all, 'ai', 'analyze', content] as const,
    summary: (id: string) => [...queryKeys.all, 'ai', 'summary', id] as const,
    tags: (content: string) => [...queryKeys.all, 'ai', 'tags', content] as const,
  },
  rag: {
    search: (query: string) => [...queryKeys.all, 'rag', 'search', query] as const,
    documents: () => [...queryKeys.all, 'rag', 'documents'] as const,
  },
};

// Common query factories
export function createCapturesQuery(params?: Record<string, any>) {
  const searchParams = new URLSearchParams(params);
  const queryString = searchParams.toString();
  
  return createQuery({
    queryKey: queryString ? queryKeys.captureSearch(queryString) : queryKeys.captures(),
    queryFn: () => fetchApi(`/captures${queryString ? `?${queryString}` : ''}`),
    ...defaultQueryOptions,
  });
}

export function createCaptureQuery(id: string) {
  return createQuery({
    queryKey: queryKeys.capture(id),
    queryFn: () => fetchApi(`/captures/${id}`),
    enabled: !!id,
    ...defaultQueryOptions,
  });
}

export function createInsightsQuery() {
  return createQuery({
    queryKey: queryKeys.insights(),
    queryFn: () => fetchApi('/insights'),
    ...defaultQueryOptions,
  });
}

export function createTimelineQuery(params?: { start_date?: string; end_date?: string }) {
  return createQuery({
    queryKey: queryKeys.timeline(),
    queryFn: () => fetchApi('/timeline', {
      method: 'POST',
      body: JSON.stringify(params || {}),
    }),
    ...defaultQueryOptions,
  });
}

export function createTagsQuery() {
  return createQuery({
    queryKey: queryKeys.tags(),
    queryFn: () => fetchApi('/tags'),
    ...defaultQueryOptions,
  });
}

// AI-related queries
export function createAIAnalysisQuery(content: string, options?: { url?: string }) {
  return createQuery({
    queryKey: queryKeys.ai.analyze(content),
    queryFn: () => fetchApi('/ai/analyze', {
      method: 'POST',
      body: JSON.stringify({ content, ...options }),
    }),
    enabled: !!content,
    ...defaultQueryOptions,
  });
}

export function createAISummaryQuery(captureId: string) {
  return createQuery({
    queryKey: queryKeys.ai.summary(captureId),
    queryFn: () => fetchApi(`/ai/summary/${captureId}`),
    enabled: !!captureId,
    ...defaultQueryOptions,
  });
}

// Mutations
export function createCaptureMutation() {
  return createMutation({
    mutationFn: (capture: any) => fetchApi('/captures', {
      method: 'POST',
      body: JSON.stringify(capture),
    }),
  });
}

export function createUpdateCaptureMutation() {
  return createMutation({
    mutationFn: ({ id, ...data }: any) => fetchApi(`/captures/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  });
}

export function createDeleteCaptureMutation() {
  return createMutation({
    mutationFn: (id: string) => fetchApi(`/captures/${id}`, {
      method: 'DELETE',
    }),
  });
}

// RAG-related queries
export function createRAGSearchQuery(query: string, options?: { limit?: number }) {
  return createQuery({
    queryKey: queryKeys.rag.search(query),
    queryFn: () => fetchApi('/rag/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit: options?.limit || 10 }),
    }),
    enabled: !!query,
    ...defaultQueryOptions,
  });
}

// Utility to invalidate queries
export function getInvalidateQueries(queryClient: any) {
  return {
    captures: () => queryClient.invalidateQueries({ queryKey: queryKeys.captures() }),
    capture: (id: string) => queryClient.invalidateQueries({ queryKey: queryKeys.capture(id) }),
    insights: () => queryClient.invalidateQueries({ queryKey: queryKeys.insights() }),
    timeline: () => queryClient.invalidateQueries({ queryKey: queryKeys.timeline() }),
    tags: () => queryClient.invalidateQueries({ queryKey: queryKeys.tags() }),
    all: () => queryClient.invalidateQueries({ queryKey: queryKeys.all }),
  };
}