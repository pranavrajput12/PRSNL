import { writable, derived } from 'svelte/store';
import type { ContentTypeDefinition, ContentTypesResponse } from '$lib/types/api';
import { api } from '$lib/api';

// Store for content types
function createContentTypesStore() {
  const { subscribe, set, update } = writable<ContentTypeDefinition[]>([]);
  
  let initialized = false;
  
  return {
    subscribe,
    
    // Initialize content types from backend
    async init() {
      if (initialized) return;
      
      try {
        const response = await api.get<ContentTypesResponse>('/content-types');
        set(response.content_types);
        initialized = true;
      } catch (error) {
        console.error('Failed to load content types:', error);
        // Fallback to default types if API fails
        set(getDefaultTypes());
      }
    },
    
    // Get a specific content type definition
    getType(typeName: string): ContentTypeDefinition | undefined {
      let types: ContentTypeDefinition[] = [];
      const unsubscribe = subscribe(t => types = t);
      unsubscribe();
      
      return types.find(t => t.name === typeName) || {
        name: typeName,
        display_name: typeName.charAt(0).toUpperCase() + typeName.slice(1),
        icon: 'file',
        description: `${typeName} content`,
        color: '#6B7280'
      };
    },
    
    // Refresh content types from backend
    async refresh() {
      try {
        const response = await api.get<ContentTypesResponse>('/content-types');
        set(response.content_types);
      } catch (error) {
        console.error('Failed to refresh content types:', error);
      }
    }
  };
}

// Default content types (fallback)
function getDefaultTypes(): ContentTypeDefinition[] {
  return [
    {
      name: 'article',
      display_name: 'Article',
      icon: 'file-text',
      description: 'Written articles and blog posts',
      color: '#3B82F6'
    },
    {
      name: 'video',
      display_name: 'Video',
      icon: 'play-circle',
      description: 'Video content from various platforms',
      color: '#EF4444'
    },
    {
      name: 'document',
      display_name: 'Document',
      icon: 'file',
      description: 'PDF files and other documents',
      color: '#10B981'
    },
    {
      name: 'image',
      display_name: 'Image',
      icon: 'image',
      description: 'Images and visual content',
      color: '#8B5CF6'
    },
    {
      name: 'note',
      display_name: 'Note',
      icon: 'edit',
      description: 'Personal notes and highlights',
      color: '#F59E0B'
    },
    {
      name: 'link',
      display_name: 'Link',
      icon: 'link',
      description: 'Simple bookmarked links',
      color: '#6B7280'
    }
  ];
}

// Create the store
export const contentTypes = createContentTypesStore();

// Derived store for type map (for quick lookups)
export const contentTypeMap = derived(
  contentTypes,
  $types => {
    const map = new Map<string, ContentTypeDefinition>();
    $types.forEach(type => map.set(type.name, type));
    return map;
  }
);

// Helper function to get icon for a type
export function getTypeIcon(typeName: string): string {
  const typeMap = new Map<string, string>([
    ['article', 'file-text'],
    ['video', 'play-circle'],
    ['document', 'file'],
    ['image', 'image'],
    ['note', 'edit'],
    ['link', 'link'],
    ['tutorial', 'book-open'],
    ['audio', 'headphones'],
    ['code', 'code']
  ]);
  
  return typeMap.get(typeName) || 'file';
}

// Helper function to get color for a type
export function getTypeColor(typeName: string): string {
  const colorMap = new Map<string, string>([
    ['article', '#3B82F6'],
    ['video', '#EF4444'],
    ['document', '#10B981'],
    ['image', '#8B5CF6'],
    ['note', '#F59E0B'],
    ['link', '#6B7280'],
    ['tutorial', '#06B6D4'],
    ['audio', '#EC4899'],
    ['code', '#84CC16']
  ]);
  
  return colorMap.get(typeName) || '#6B7280';
}