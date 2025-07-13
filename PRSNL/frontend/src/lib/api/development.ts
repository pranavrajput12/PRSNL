/**
 * Development API functions for Code Cortex
 */

// Use the same API base URL as the main API
const API_BASE_URL = '/api';

export interface DevelopmentStats {
  total_items: number;
  by_language: Record<string, number>;
  by_category: Record<string, number>;
  by_difficulty: Record<string, number>;
  career_related_count: number;
  repository_count: number;
  recent_activity: Array<{
    id: string;
    title: string;
    programming_language?: string;
    project_category?: string;
    created_at: string;
  }>;
}

export interface DevelopmentCategory {
  id: string;
  name: string;
  description?: string;
  icon: string;
  color: string;
  created_at: string;
  item_count: number;
}

export interface DevelopmentItem {
  id: string;
  title: string;
  url?: string;
  summary?: string;
  type: string;
  programming_language?: string;
  project_category?: string;
  difficulty_level?: number;
  is_career_related: boolean;
  learning_path?: string;
  code_snippets: Array<any>;
  created_at: string;
  updated_at?: string;
  tags: string[];
  // Enhanced search metadata (optional)
  similarity_score?: number;
  search_metadata?: {
    has_embedding: boolean;
    search_timestamp: string;
  };
  component_scores?: {
    semantic?: number;
    keyword?: number;
  };
}

export interface DevelopmentDocsFilters {
  limit?: number;
  offset?: number;
  category?: string;
  language?: string;
  difficulty?: number;
  career_related?: boolean;
  learning_path?: string;
  search?: string;
  content_type?: 'knowledge' | 'tools' | 'repositories' | 'progress';
}

// API Functions

export async function getDevelopmentStats(): Promise<DevelopmentStats> {
  const response = await fetch(`${API_BASE_URL}/development/stats`);
  if (!response.ok) {
    throw new Error(`Failed to fetch development stats: ${response.statusText}`);
  }
  return response.json();
}

export async function getDevelopmentCategories(): Promise<DevelopmentCategory[]> {
  const response = await fetch(`${API_BASE_URL}/development/categories`);
  if (!response.ok) {
    throw new Error(`Failed to fetch development categories: ${response.statusText}`);
  }
  return response.json();
}

export async function getDevelopmentDocs(
  filters?: DevelopmentDocsFilters
): Promise<DevelopmentItem[]> {
  const params = new URLSearchParams();

  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });
  }

  const url = `${API_BASE_URL}/development/docs${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch development docs: ${response.statusText}`);
  }

  return response.json();
}

export async function getProgrammingLanguages(): Promise<{
  languages: Array<{ name: string; count: number }>;
}> {
  const response = await fetch(`${API_BASE_URL}/development/languages`);
  if (!response.ok) {
    throw new Error(`Failed to fetch programming languages: ${response.statusText}`);
  }
  return response.json();
}

export async function getLearningPaths(): Promise<{
  learning_paths: Array<{
    name: string;
    total_items: number;
    completed_items: number;
    progress_percentage: number;
    avg_difficulty: number;
  }>;
}> {
  const response = await fetch(`${API_BASE_URL}/development/learning-paths`);
  if (!response.ok) {
    throw new Error(`Failed to fetch learning paths: ${response.statusText}`);
  }
  return response.json();
}

export async function saveCodeSnippet(snippet: {
  title: string;
  language: string;
  code: string;
  description?: string;
  tags?: string[];
}): Promise<{ success: boolean; message: string; item_id: string }> {
  const response = await fetch(`${API_BASE_URL}/development/snippet`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(snippet),
  });

  if (!response.ok) {
    throw new Error(`Failed to save code snippet: ${response.statusText}`);
  }

  return response.json();
}

export async function autoCategorizeContent(itemId: string): Promise<{
  success: boolean;
  message: string;
  category: string;
}> {
  const response = await fetch(`${API_BASE_URL}/development/categorize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ item_id: itemId }),
  });

  if (!response.ok) {
    throw new Error(`Failed to categorize content: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Enhanced search for development content using semantic search API
 */
export async function searchDevelopmentContent(
  query: string,
  options: {
    searchMode?: 'semantic' | 'keyword' | 'hybrid';
    limit?: number;
    filters?: {
      category?: string;
      language?: string;
      difficulty?: number;
      career_related?: boolean;
    };
  } = {}
): Promise<{
  results: DevelopmentItem[];
  total: number;
  searchStats: any;
}> {
  const { searchMode = 'semantic', limit = 20, filters = {} } = options;

  // Build enhanced search request
  const searchRequest = {
    query: query,
    search_type: searchMode,
    limit: limit,
    threshold: 0.3,
    include_duplicates: false,
    filters: {
      // Add content type filter to focus on development content
      type: filters.category,
      // Add custom filters for development content
      programming_language: filters.language,
      difficulty_level: filters.difficulty,
      is_career_related: filters.career_related,
    },
  };

  try {
    const response = await fetch(`${API_BASE_URL}/search/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(searchRequest),
    });

    if (!response.ok) {
      throw new Error(`Enhanced search failed: ${response.statusText}`);
    }

    const searchResponse = await response.json();

    // Transform search results to DevelopmentItem format
    const results: DevelopmentItem[] = searchResponse.results.map((result: any) => ({
      id: result.id,
      title: result.title,
      url: result.url,
      summary: result.snippet || result.summary,
      type: result.type || 'article',
      programming_language: result.programming_language,
      project_category: result.project_category,
      difficulty_level: result.difficulty_level,
      is_career_related: result.is_career_related || false,
      learning_path: result.learning_path,
      code_snippets: result.code_snippets || [],
      created_at: result.created_at,
      updated_at: result.updated_at,
      tags: result.tags || [],
      // Add search-specific metadata
      similarity_score: result.similarity,
      search_metadata: result.search_metadata,
      component_scores: result.component_scores,
    }));

    return {
      results: results,
      total: searchResponse.total,
      searchStats: {
        searchType: searchResponse.search_type,
        deduplication: searchResponse.deduplication,
        weights: searchResponse.weights,
        timestamp: searchResponse.timestamp,
      },
    };
  } catch (error) {
    console.error('Enhanced development search failed:', error);
    // Fallback to regular development docs API
    const fallbackFilters: DevelopmentDocsFilters = {
      search: query,
      limit: limit,
      category: filters.category,
      language: filters.language,
      difficulty: filters.difficulty,
      career_related: filters.career_related,
    };

    const fallbackResults = await getDevelopmentDocs(fallbackFilters);
    return {
      results: fallbackResults,
      total: fallbackResults.length,
      searchStats: {
        searchType: 'fallback',
        deduplication: null,
        weights: null,
        timestamp: new Date().toISOString(),
      },
    };
  }
}
