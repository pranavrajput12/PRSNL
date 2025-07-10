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

export async function getDevelopmentDocs(filters?: DevelopmentDocsFilters): Promise<DevelopmentItem[]> {
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

export async function getProgrammingLanguages(): Promise<{ languages: Array<{ name: string; count: number }> }> {
  const response = await fetch(`${API_BASE_URL}/development/languages`);
  if (!response.ok) {
    throw new Error(`Failed to fetch programming languages: ${response.statusText}`);
  }
  return response.json();
}

export async function getLearningPaths(): Promise<{ learning_paths: Array<{ 
  name: string; 
  total_items: number; 
  completed_items: number;
  progress_percentage: number;
  avg_difficulty: number;
}> }> {
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
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(snippet)
  });
  
  if (!response.ok) {
    throw new Error(`Failed to save code snippet: ${response.statusText}`);
  }
  
  return response.json();
}

export async function autoCategorizeContent(itemId: string): Promise<{ 
  success: boolean; 
  message: string; 
  category: string 
}> {
  const response = await fetch(`${API_BASE_URL}/development/categorize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ item_id: itemId })
  });
  
  if (!response.ok) {
    throw new Error(`Failed to categorize content: ${response.statusText}`);
  }
  
  return response.json();
}