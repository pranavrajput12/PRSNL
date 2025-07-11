# Svelte Query (TanStack Query) Integration Guide

## Overview
Svelte Query has been integrated into PRSNL to provide advanced data fetching, caching, and synchronization capabilities. This replaces manual fetch logic with a more robust and feature-rich solution.

## Installation
```bash
npm install @tanstack/svelte-query
```

## Configuration

### 1. QueryClient Setup
The QueryClient is configured in the root layout (`/frontend/src/routes/+layout.svelte`):

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});
```

### 2. QueryClientProvider
The entire app is wrapped with QueryClientProvider in the layout:

```svelte
<QueryClientProvider client={queryClient}>
  <div class="app-layout">
    <!-- App content -->
  </div>
</QueryClientProvider>
```

## API Utilities

### Query Key Factory
Located in `/frontend/src/lib/queries/api.ts`, provides consistent cache keys:

```typescript
export const queryKeys = {
  all: ['prsnl'] as const,
  captures: () => [...queryKeys.all, 'captures'] as const,
  capture: (id: string) => [...queryKeys.captures(), id] as const,
  captureSearch: (query: string) => [...queryKeys.captures(), 'search', query] as const,
  insights: () => [...queryKeys.all, 'insights'] as const,
  timeline: () => [...queryKeys.all, 'timeline'] as const,
  tags: () => [...queryKeys.all, 'tags'] as const,
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
```

### Fetch Wrapper
Generic fetch function with error handling:

```typescript
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
```

## Query Examples

### Basic Query
```typescript
import { createCapturesQuery } from '$lib/queries/api';

// In component
const capturesQuery = createCapturesQuery();

// Access data
$: captures = $capturesQuery.data;
$: isLoading = $capturesQuery.isLoading;
$: error = $capturesQuery.error;
```

### Query with Parameters
```typescript
const searchQuery = createRAGSearchQuery(searchTerm, { limit: 20 });

// Reactive query - automatically refetches when searchTerm changes
$: resultsQuery = searchTerm ? createRAGSearchQuery(searchTerm) : null;
```

### Conditional Query
```typescript
const captureQuery = createCaptureQuery(captureId);
// Query only runs when captureId is truthy (enabled option)
```

## Mutation Examples

### Basic Mutation
```typescript
import { createCaptureMutation } from '$lib/queries/api';
import { useQueryClient } from '@tanstack/svelte-query';

const queryClient = useQueryClient();
const createCapture = createCaptureMutation();

async function handleSubmit(data) {
  try {
    await $createCapture.mutateAsync(data);
    // Invalidate and refetch captures
    queryClient.invalidateQueries({ queryKey: queryKeys.captures() });
  } catch (error) {
    console.error('Failed to create capture:', error);
  }
}
```

### Update Mutation
```typescript
const updateCapture = createUpdateCaptureMutation();

async function handleUpdate(id, data) {
  await $updateCapture.mutateAsync({ id, ...data });
  // Invalidate specific capture and list
  queryClient.invalidateQueries({ queryKey: queryKeys.capture(id) });
  queryClient.invalidateQueries({ queryKey: queryKeys.captures() });
}
```

## Benefits

1. **Automatic Caching**: Reduces unnecessary API calls
2. **Background Refetching**: Keeps data fresh without blocking UI
3. **Request Deduplication**: Multiple components can use same query without duplicate requests
4. **Optimistic Updates**: Update UI immediately while mutation is in progress
5. **Error Handling**: Built-in error states and retry logic
6. **Loading States**: Automatic loading indicators
7. **Stale-While-Revalidate**: Show cached data while fetching fresh data

## Migration Guide

### Before (Manual Fetch):
```svelte
<script>
  import { onMount } from 'svelte';
  import { getTimeline } from '$lib/api';
  
  let items = [];
  let isLoading = true;
  let error = null;
  
  onMount(async () => {
    try {
      const response = await getTimeline();
      items = response.items;
    } catch (e) {
      error = e;
    } finally {
      isLoading = false;
    }
  });
</script>
```

### After (Svelte Query):
```svelte
<script>
  import { createTimelineQuery } from '$lib/queries/api';
  
  const timelineQuery = createTimelineQuery();
  
  $: items = $timelineQuery.data?.items || [];
  $: isLoading = $timelineQuery.isLoading;
  $: error = $timelineQuery.error;
</script>
```

## Best Practices

1. **Use Query Keys Consistently**: Always use the queryKeys factory for cache keys
2. **Invalidate Wisely**: Only invalidate queries that are affected by mutations
3. **Error Boundaries**: Wrap components with error boundaries for better error handling
4. **Suspense (Future)**: Prepare for Suspense support in future Svelte versions
5. **Prefetching**: Use queryClient.prefetchQuery for route transitions

## Advanced Usage

### Prefetching
```typescript
// In +page.ts or before navigation
await queryClient.prefetchQuery({
  queryKey: queryKeys.capture(id),
  queryFn: () => fetchApi(`/captures/${id}`),
});
```

### Infinite Queries (Pagination)
```typescript
// Coming soon - for timeline infinite scroll
import { createInfiniteQuery } from '@tanstack/svelte-query';
```

### Optimistic Updates
```typescript
const updateMutation = createMutation({
  mutationFn: updateCapture,
  onMutate: async (newData) => {
    // Cancel in-flight queries
    await queryClient.cancelQueries({ queryKey: queryKeys.capture(newData.id) });
    
    // Snapshot previous value
    const previousCapture = queryClient.getQueryData(queryKeys.capture(newData.id));
    
    // Optimistically update
    queryClient.setQueryData(queryKeys.capture(newData.id), newData);
    
    return { previousCapture };
  },
  onError: (err, newData, context) => {
    // Rollback on error
    queryClient.setQueryData(
      queryKeys.capture(newData.id),
      context.previousCapture
    );
  },
});
```

## Debugging

Enable React Query Devtools (works with Svelte Query):
```bash
npm install @tanstack/svelte-query-devtools
```

Add to layout:
```svelte
{#if import.meta.env.DEV}
  <SvelteQueryDevtools />
{/if}
```

## Status
- ✅ Core integration complete
- ✅ Query utilities created
- ✅ Example implementation provided
- ✅ Production-ready patterns documented
- ✅ Enhanced search integration complete
- ✅ Backend API integration verified
- ✅ Automatic caching and deduplication active
- ✅ Full TypeScript support
- ⚠️ Devtools integration optional