/**
 * CONTENT CATEGORIZATION SERVICE
 * 
 * Provides three-tier content organization:
 * 1. Content Types → 2. Categories → 3. Tags
 * 
 * Supports filtering, counting, and hierarchical browsing
 */

import type { ContentTypeRoute } from '$lib/config/routingSchema';
import { CONTENT_TYPE_ROUTES, CATEGORIES } from '$lib/config/routingSchema';

// ===========================
// TYPE DEFINITIONS
// ===========================

export interface ContentItem {
  id: string;
  title: string;
  type: string;
  category?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  url?: string;
  description?: string;
  thumbnail?: string;
  author?: string;
  status?: 'active' | 'archived' | 'draft';
}

export interface CategoryStats {
  id: string;
  label: string;
  icon: string;
  color: string;
  count: number;
  contentTypes: string[];
}

export interface TagStats {
  tag: string;
  count: number;
  contentTypes: string[];
  categories: string[];
}

export interface ContentTypeStats {
  type: string;
  path: string;
  label: string;
  icon: string;
  color: string;
  count: number;
  categories: CategoryStats[];
  recentTags: string[];
}

export interface CategoryFilter {
  contentType?: string;
  category?: string;
  tags?: string[];
  status?: 'active' | 'archived' | 'draft' | 'all';
  dateRange?: {
    start: string;
    end: string;
  };
  limit?: number;
  offset?: number;
  sortBy?: 'created_date' | 'updated_date' | 'title' | 'type';
  sortOrder?: 'asc' | 'desc';
}

// ===========================
// CATEGORIZATION SERVICE
// ===========================

class CategorizationService {
  private baseUrl = '/api';

  /**
   * Get all content types with statistics
   */
  async getContentTypeStats(): Promise<ContentTypeStats[]> {
    try {
      const response = await fetch(`${this.baseUrl}/library/stats/content-types`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      
      // Enhance with routing schema data
      return data.map((stats: any) => {
        const routeConfig = Object.values(CONTENT_TYPE_ROUTES).find(ct => ct.type === stats.type);
        return {
          ...stats,
          path: routeConfig?.path || stats.type,
          label: routeConfig?.label || stats.type,
          icon: routeConfig?.icon || 'file',
          color: routeConfig?.color || '#6B7280'
        };
      });
    } catch (error) {
      console.error('Failed to fetch content type stats:', error);
      return this.getDefaultContentTypeStats();
    }
  }

  /**
   * Get category statistics across all content types
   */
  async getCategoryStats(contentType?: string): Promise<CategoryStats[]> {
    try {
      const url = contentType 
        ? `${this.baseUrl}/library/stats/categories?content_type=${contentType}`
        : `${this.baseUrl}/library/stats/categories`;
      
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      
      // Enhance with category definitions
      return data.map((stats: any) => {
        const categoryDef = CATEGORIES[stats.id as keyof typeof CATEGORIES];
        return {
          ...stats,
          label: categoryDef?.label || stats.id,
          icon: categoryDef?.icon || 'folder',
          color: categoryDef?.color || '#6B7280',
          contentTypes: categoryDef?.contentTypes || []
        };
      });
    } catch (error) {
      console.error('Failed to fetch category stats:', error);
      return this.getDefaultCategoryStats();
    }
  }

  /**
   * Get tag statistics with usage counts
   */
  async getTagStats(filters?: { contentType?: string; category?: string; limit?: number }): Promise<TagStats[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.contentType) params.set('content_type', filters.contentType);
      if (filters?.category) params.set('category', filters.category);
      if (filters?.limit) params.set('limit', filters.limit.toString());
      
      const response = await fetch(`${this.baseUrl}/library/stats/tags?${params}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch tag stats:', error);
      return [];
    }
  }

  /**
   * Get filtered content items
   */
  async getContentItems(filters: CategoryFilter = {}): Promise<{
    items: ContentItem[];
    total: number;
    hasMore: boolean;
  }> {
    try {
      const params = new URLSearchParams();
      
      if (filters.contentType) params.set('content_type', filters.contentType);
      if (filters.category) params.set('category', filters.category);
      if (filters.tags?.length) params.set('tags', filters.tags.join(','));
      if (filters.status && filters.status !== 'all') params.set('status', filters.status);
      if (filters.dateRange) {
        params.set('date_start', filters.dateRange.start);
        params.set('date_end', filters.dateRange.end);
      }
      if (filters.limit) params.set('limit', filters.limit.toString());
      if (filters.offset) params.set('offset', filters.offset.toString());
      if (filters.sortBy) params.set('sort_by', filters.sortBy);
      if (filters.sortOrder) params.set('sort_order', filters.sortOrder);
      
      const response = await fetch(`${this.baseUrl}/library/content?${params}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      
      return {
        items: data.items || [],
        total: data.total || 0,
        hasMore: data.has_more || false
      };
    } catch (error) {
      console.error('Failed to fetch content items:', error);
      return { items: [], total: 0, hasMore: false };
    }
  }

  /**
   * Get content items by specific content type
   */
  async getContentByType(type: string, filters: Omit<CategoryFilter, 'contentType'> = {}): Promise<{
    items: ContentItem[];
    total: number;
    hasMore: boolean;
  }> {
    return this.getContentItems({ ...filters, contentType: type });
  }

  /**
   * Get content items by category
   */
  async getContentByCategory(category: string, contentType?: string, filters: Omit<CategoryFilter, 'category' | 'contentType'> = {}): Promise<{
    items: ContentItem[];
    total: number;
    hasMore: boolean;
  }> {
    return this.getContentItems({ 
      ...filters, 
      category, 
      contentType 
    });
  }

  /**
   * Get content items by tags
   */
  async getContentByTags(tags: string[], filters: Omit<CategoryFilter, 'tags'> = {}): Promise<{
    items: ContentItem[];
    total: number;
    hasMore: boolean;
  }> {
    return this.getContentItems({ ...filters, tags });
  }

  /**
   * Search content items with categorization context
   */
  async searchContent(query: string, filters: CategoryFilter = {}): Promise<{
    items: ContentItem[];
    total: number;
    hasMore: boolean;
    facets?: {
      contentTypes: { [key: string]: number };
      categories: { [key: string]: number };
      tags: { [key: string]: number };
    };
  }> {
    try {
      const params = new URLSearchParams();
      params.set('q', query);
      
      if (filters.contentType) params.set('content_type', filters.contentType);
      if (filters.category) params.set('category', filters.category);
      if (filters.tags?.length) params.set('tags', filters.tags.join(','));
      if (filters.limit) params.set('limit', filters.limit.toString());
      if (filters.offset) params.set('offset', filters.offset.toString());
      
      const response = await fetch(`${this.baseUrl}/library/search?${params}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      return await response.json();
    } catch (error) {
      console.error('Failed to search content:', error);
      return { items: [], total: 0, hasMore: false };
    }
  }

  /**
   * Get related content based on categories and tags
   */
  async getRelatedContent(itemId: string, limit = 5): Promise<ContentItem[]> {
    try {
      const response = await fetch(`${this.baseUrl}/library/content/${itemId}/related?limit=${limit}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch related content:', error);
      return [];
    }
  }

  // ===========================
  // UTILITY METHODS
  // ===========================

  /**
   * Get content type configuration
   */
  getContentTypeConfig(type: string): ContentTypeRoute | null {
    return Object.values(CONTENT_TYPE_ROUTES).find(ct => ct.type === type) || null;
  }

  /**
   * Get category configuration
   */
  getCategoryConfig(categoryId: string) {
    return CATEGORIES[categoryId as keyof typeof CATEGORIES] || null;
  }

  /**
   * Validate content type
   */
  isValidContentType(type: string): boolean {
    return Object.values(CONTENT_TYPE_ROUTES).some(ct => ct.type === type);
  }

  /**
   * Validate category
   */
  isValidCategory(category: string): boolean {
    return category in CATEGORIES;
  }

  /**
   * Get categories for content type
   */
  getCategoriesForContentType(type: string): string[] {
    const contentType = this.getContentTypeConfig(type);
    return contentType?.categories || [];
  }

  /**
   * Get content types for category
   */
  getContentTypesForCategory(category: string): string[] {
    const categoryConfig = this.getCategoryConfig(category);
    return categoryConfig?.contentTypes || [];
  }

  // ===========================
  // FALLBACK DATA
  // ===========================

  private getDefaultContentTypeStats(): ContentTypeStats[] {
    return Object.values(CONTENT_TYPE_ROUTES).map(route => ({
      type: route.type,
      path: route.path,
      label: route.label,
      icon: route.icon,
      color: route.color,
      count: 0,
      categories: [],
      recentTags: []
    }));
  }

  private getDefaultCategoryStats(): CategoryStats[] {
    return Object.values(CATEGORIES).map(category => ({
      id: category.id,
      label: category.label,
      icon: category.icon,
      color: category.color,
      count: 0,
      contentTypes: category.contentTypes
    }));
  }
}

// ===========================
// SINGLETON EXPORT
// ===========================

export const categorizationService = new CategorizationService();
export default categorizationService;