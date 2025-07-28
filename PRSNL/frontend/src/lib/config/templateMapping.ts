/**
 * Template Mapping Configuration
 * Maps content types to their respective single page templates
 */

export type TemplateType = 'generic' | 'video' | 'article' | 'document' | 'bookmark' | 'social' | 'code' | 'recipe';

export interface TemplateConfig {
  template: TemplateType;
  route: string;
  features: string[];
}

/**
 * Maps content types from the database to their optimal template
 */
export const CONTENT_TYPE_MAPPING: Record<string, TemplateConfig> = {
  // Video content
  'video': {
    template: 'video',
    route: '/videos/[id]',
    features: ['video-player', 'transcript', 'download', 'chapters']
  },
  'youtube': {
    template: 'video',
    route: '/videos/[id]',
    features: ['youtube-embed', 'transcript', 'download']
  },
  
  // Article/Text content
  'article': {
    template: 'article',
    route: '/article/[id]',
    features: ['markdown', 'toc', 'reading-time', 'typography']
  },
  'text': {
    template: 'article',
    route: '/article/[id]',
    features: ['markdown', 'toc', 'reading-time']
  },
  
  // Document content
  'document': {
    template: 'document',
    route: '/document/[id]',
    features: ['pdf-viewer', 'download', 'annotations']
  },
  'pdf': {
    template: 'document',
    route: '/document/[id]',
    features: ['pdf-viewer', 'download', 'fullscreen']
  },
  
  // Link/Bookmark content
  'bookmark': {
    template: 'bookmark',
    route: '/bookmark/[id]',
    features: ['preview', 'metadata', 'quick-save', 'original-link']
  },
  'link': {
    template: 'bookmark',
    route: '/bookmark/[id]',
    features: ['preview', 'metadata', 'original-link']
  },
  'website': {
    template: 'bookmark',
    route: '/bookmark/[id]',
    features: ['preview', 'screenshot', 'metadata', 'original-link']
  },
  
  // Development content (uses Code Cortex)
  'github_repo': {
    template: 'code',
    route: '/code-cortex/repo/[id]',
    features: ['readme', 'stats', 'file-tree', 'commits']
  },
  'github_document': {
    template: 'code',
    route: '/code-cortex/docs/[id]',
    features: ['syntax-highlight', 'markdown', 'toc']
  },
  'development': {
    template: 'code',
    route: '/code-cortex/links/[id]',
    features: ['syntax-highlight', 'metadata', 'related']
  },
  
  // Recipe content
  'recipe': {
    template: 'recipe',
    route: '/recipe/[id]',
    features: ['ingredients-list', 'step-tracker', 'timer', 'serving-calculator', 'voice-mode']
  },
  
  // Social media content (future)
  'twitter': {
    template: 'social',
    route: '/social/[id]',
    features: ['embed', 'thread-view', 'media-gallery']
  },
  
  // Default fallback
  'default': {
    template: 'generic',
    route: '/item/[id]',
    features: ['content', 'metadata', 'ai-analysis']
  }
};

/**
 * Get the appropriate template configuration for a content type
 */
export function getTemplateConfig(contentType: string): TemplateConfig {
  return CONTENT_TYPE_MAPPING[contentType] || CONTENT_TYPE_MAPPING['default'];
}

/**
 * Get the route for a specific item based on its type
 */
export function getItemRoute(itemId: string, contentType: string): string {
  const config = getTemplateConfig(contentType);
  return config.route.replace('[id]', itemId);
}

/**
 * Check if a template exists for the given content type
 */
export function hasSpecificTemplate(contentType: string): boolean {
  return contentType in CONTENT_TYPE_MAPPING && contentType !== 'default';
}

/**
 * Get all unique template types that need to be created
 */
export function getRequiredTemplates(): Set<TemplateType> {
  const templates = new Set<TemplateType>();
  Object.values(CONTENT_TYPE_MAPPING).forEach(config => {
    templates.add(config.template);
  });
  return templates;
}