# ⚙️ Permalink Configuration System for PRSNL

## 📋 Overview

The permalink configuration system provides WordPress-style URL management for PRSNL, allowing administrators to customize URL patterns, manage redirects, and optimize SEO settings. This system enables flexible URL structures while maintaining backward compatibility.

## 🎯 System Architecture

### Core Components:
1. **Permalink Manager**: Central configuration and generation service
2. **URL Builder**: Dynamic URL generation based on patterns
3. **Redirect Engine**: Legacy URL redirect management
4. **SEO Optimizer**: Automatic slug generation and optimization
5. **Admin Interface**: User-friendly configuration dashboard

## 🔧 Permalink Manager Service

### Core Configuration (`PermalinkManager.ts`):

```typescript
// lib/services/PermalinkManager.ts
export interface PermalinkPattern {
  id: string;
  name: string;
  pattern: string;
  description: string;
  example: string;
  contentTypes: string[];
  variables: string[];
  active: boolean;
}

export interface PermalinkConfig {
  patterns: Record<string, PermalinkPattern>;
  defaultPattern: string;
  slugConfig: SlugConfig;
  redirectConfig: RedirectConfig;
  seoConfig: SEOConfig;
}

export interface SlugConfig {
  maxLength: number;
  separator: '-' | '_';
  lowercase: boolean;
  removeStopWords: boolean;
  allowNumbers: boolean;
  allowUnicode: boolean;
  customReplacements: Record<string, string>;
}

export interface RedirectConfig {
  enabled: boolean;
  permanentRedirects: boolean; // 301 vs 302
  preserveQuery: boolean;
  legacyPatterns: LegacyPattern[];
}

export interface SEOConfig {
  generateMetaTitles: boolean;
  generateDescriptions: boolean;
  titleTemplate: string;
  descriptionTemplate: string;
  maxTitleLength: number;
  maxDescriptionLength: number;
}

export class PermalinkManager {
  private config: PermalinkConfig;
  
  constructor(config: PermalinkConfig) {
    this.config = config;
  }
  
  // Generate URL for content
  generateUrl(
    content: ContentItem,
    pattern?: string
  ): string {
    const activePattern = pattern || this.config.defaultPattern;
    const patternConfig = this.config.patterns[activePattern];
    
    if (!patternConfig) {
      throw new Error(`Pattern ${activePattern} not found`);
    }
    
    return this.buildUrl(patternConfig.pattern, content);
  }
  
  // Build URL from pattern and content
  private buildUrl(pattern: string, content: ContentItem): string {
    let url = pattern;
    
    // Replace variables in pattern
    const variables = this.extractVariables(pattern);
    
    for (const variable of variables) {
      const value = this.getVariableValue(variable, content);
      url = url.replace(`{${variable}}`, value);
    }
    
    // Clean up URL
    return this.cleanUrl(url);
  }
  
  // Extract variables from pattern
  private extractVariables(pattern: string): string[] {
    const matches = pattern.match(/\{([^}]+)\}/g);
    return matches ? matches.map(m => m.slice(1, -1)) : [];
  }
  
  // Get value for variable
  private getVariableValue(variable: string, content: ContentItem): string {
    switch (variable) {
      case 'category':
        return content.category || 'uncategorized';
      case 'subcategory':
        return content.subcategory || 'general';
      case 'slug':
        return this.generateSlug(content.title);
      case 'year':
        return new Date(content.created_at).getFullYear().toString();
      case 'month':
        return (new Date(content.created_at).getMonth() + 1).toString().padStart(2, '0');
      case 'day':
        return new Date(content.created_at).getDate().toString().padStart(2, '0');
      case 'id':
        return content.id;
      case 'type':
        return content.type || 'post';
      case 'author':
        return content.author || 'admin';
      default:
        return content[variable] || '';
    }
  }
  
  // Generate SEO-friendly slug
  generateSlug(title: string): string {
    const { slugConfig } = this.config;
    let slug = title;
    
    // Convert to lowercase
    if (slugConfig.lowercase) {
      slug = slug.toLowerCase();
    }
    
    // Remove stop words
    if (slugConfig.removeStopWords) {
      slug = this.removeStopWords(slug);
    }
    
    // Apply custom replacements
    for (const [search, replace] of Object.entries(slugConfig.customReplacements)) {
      slug = slug.replace(new RegExp(search, 'g'), replace);
    }
    
    // Remove special characters
    slug = slug.replace(/[^\w\s-]/g, '');
    
    // Replace spaces with separator
    slug = slug.replace(/\s+/g, slugConfig.separator);
    
    // Remove multiple separators
    slug = slug.replace(new RegExp(`${slugConfig.separator}+`, 'g'), slugConfig.separator);
    
    // Trim separators from ends
    slug = slug.replace(new RegExp(`^${slugConfig.separator}+|${slugConfig.separator}+$`, 'g'), '');
    
    // Limit length
    if (slug.length > slugConfig.maxLength) {
      slug = slug.substring(0, slugConfig.maxLength);
      // Break at word boundary
      const lastSeparator = slug.lastIndexOf(slugConfig.separator);
      if (lastSeparator > 0) {
        slug = slug.substring(0, lastSeparator);
      }
    }
    
    return slug || 'untitled';
  }
  
  // Remove stop words
  private removeStopWords(text: string): string {
    const stopWords = [
      'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
      'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
      'to', 'was', 'will', 'with', 'how', 'what', 'when', 'where', 'why'
    ];
    
    return text
      .split(/\s+/)
      .filter(word => !stopWords.includes(word.toLowerCase()))
      .join(' ');
  }
  
  // Clean URL
  private cleanUrl(url: string): string {
    return url
      .replace(/\/+/g, '/') // Remove multiple slashes
      .replace(/\/$/, '') // Remove trailing slash
      .replace(/^\//, ''); // Remove leading slash (will be added by router)
  }
}
```

## 📝 Predefined URL Patterns

### Pattern Definitions:

```typescript
export const DEFAULT_PATTERNS: Record<string, PermalinkPattern> = {
  neural_semantic: {
    id: 'neural_semantic',
    name: 'Neural Semantic (Recommended)',
    pattern: '/neural/{category}/{subcategory}/{slug}',
    description: 'Hierarchical structure matching PRSNL neural theme',
    example: '/neural/development/repositories/tensorflow-machine-learning',
    contentTypes: ['all'],
    variables: ['category', 'subcategory', 'slug'],
    active: true
  },
  
  date_based: {
    id: 'date_based',
    name: 'Date-Based Structure',
    pattern: '/{year}/{month}/{category}/{slug}',
    description: 'WordPress-style date-based URLs',
    example: '/2025/07/development/tensorflow-machine-learning',
    contentTypes: ['all'],
    variables: ['year', 'month', 'category', 'slug'],
    active: false
  },
  
  flat_category: {
    id: 'flat_category',
    name: 'Flat Category Structure',
    pattern: '/{category}/{slug}',
    description: 'Simple category-based structure',
    example: '/development/tensorflow-machine-learning',
    contentTypes: ['all'],
    variables: ['category', 'slug'],
    active: false
  },
  
  type_based: {
    id: 'type_based',
    name: 'Content Type Structure',
    pattern: '/{type}/{category}/{slug}',
    description: 'Organized by content type first',
    example: '/repository/development/tensorflow-machine-learning',
    contentTypes: ['all'],
    variables: ['type', 'category', 'slug'],
    active: false
  },
  
  simple_slug: {
    id: 'simple_slug',
    name: 'Simple Slug Only',
    pattern: '/{slug}',
    description: 'Flat structure with just slugs',
    example: '/tensorflow-machine-learning-framework',
    contentTypes: ['all'],
    variables: ['slug'],
    active: false
  },
  
  custom: {
    id: 'custom',
    name: 'Custom Pattern',
    pattern: '/content/{category}/{year}/{slug}',
    description: 'User-defined custom pattern',
    example: '/content/development/2025/tensorflow-machine-learning',
    contentTypes: ['all'],
    variables: ['category', 'year', 'slug'],
    active: false
  }
};
```

## 🔄 Redirect Engine

### Legacy URL Management:

```typescript
// lib/services/RedirectEngine.ts
export interface LegacyPattern {
  id: string;
  oldPattern: string;
  newPattern: string;
  redirectType: 301 | 302;
  active: boolean;
  description: string;
}

export interface RedirectRule {
  from: string | RegExp;
  to: string;
  type: 301 | 302;
  conditions?: RedirectCondition[];
}

export interface RedirectCondition {
  type: 'query' | 'header' | 'host';
  key: string;
  value: string | RegExp;
  operator: 'equals' | 'contains' | 'matches';
}

export class RedirectEngine {
  private rules: RedirectRule[] = [];
  private legacyMappings: Map<string, string> = new Map();
  
  constructor(private config: RedirectConfig) {
    this.buildRedirectRules();
  }
  
  // Build redirect rules from configuration
  private buildRedirectRules(): void {
    // Add legacy pattern redirects
    for (const pattern of this.config.legacyPatterns) {
      if (pattern.active) {
        this.rules.push({
          from: this.patternToRegex(pattern.oldPattern),
          to: pattern.newPattern,
          type: pattern.redirectType
        });
      }
    }
    
    // Add hardcoded legacy redirects
    this.addLegacyRedirects();
  }
  
  // Add specific legacy redirects
  private addLegacyRedirects(): void {
    const legacyRedirects = [
      { from: '/items/{id}', to: '/neural/{category}/{subcategory}/{slug}' },
      { from: '/videos/{id}', to: '/neural/media/videos/{slug}' },
      { from: '/timeline', to: '/processing/timeline' },
      { from: '/insights', to: '/processing/insights' },
      { from: '/chat', to: '/processing/chat' },
      { from: '/code-cortex', to: '/processing/code' },
      { from: '/import', to: '/system/import' },
      { from: '/settings', to: '/system/settings' },
      { from: '/docs', to: '/system/docs' }
    ];
    
    for (const redirect of legacyRedirects) {
      this.rules.push({
        from: this.patternToRegex(redirect.from),
        to: redirect.to,
        type: this.config.permanentRedirects ? 301 : 302
      });
    }
  }
  
  // Convert pattern to regex
  private patternToRegex(pattern: string): RegExp {
    const escaped = pattern
      .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      .replace(/\\\{(\w+)\\\}/g, '([^/]+)');
    return new RegExp(`^${escaped}$`);
  }
  
  // Find redirect for URL
  findRedirect(url: string): { to: string; type: number } | null {
    for (const rule of this.rules) {
      const match = url.match(rule.from);
      if (match) {
        let redirectTo = rule.to;
        
        // Replace captured groups
        for (let i = 1; i < match.length; i++) {
          redirectTo = redirectTo.replace(`$${i}`, match[i]);
        }
        
        return { to: redirectTo, type: rule.type };
      }
    }
    
    return null;
  }
  
  // Add dynamic redirect
  addRedirect(from: string, to: string, type: 301 | 302 = 301): void {
    this.rules.unshift({
      from: this.patternToRegex(from),
      to,
      type
    });
  }
}
```

## 🎨 Admin Interface Components

### Permalink Settings Page:

```svelte
<!-- routes/system/settings/permalinks/+page.svelte -->
<script lang="ts">
  import { PermalinkManager, DEFAULT_PATTERNS } from '$lib/services/PermalinkManager';
  import PatternSelector from '$lib/components/admin/PatternSelector.svelte';
  import SlugSettings from '$lib/components/admin/SlugSettings.svelte';
  import RedirectManager from '$lib/components/admin/RedirectManager.svelte';
  import PermalinkPreview from '$lib/components/admin/PermalinkPreview.svelte';
  import type { PageData } from './$types';
  
  export let data: PageData;
  
  let selectedPattern = data.config.defaultPattern;
  let config = data.config;
  let previewContent = {
    title: 'Complete Guide to React Hooks',
    category: 'learning',
    subcategory: 'tutorials',
    created_at: '2025-07-12',
    type: 'tutorial'
  };
  
  $: manager = new PermalinkManager(config);
  $: previewUrl = manager.generateUrl(previewContent, selectedPattern);
  
  async function saveConfig() {
    try {
      const response = await fetch('/api/admin/permalinks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        // Show success message
        showNotification('Permalink settings saved successfully', 'success');
      }
    } catch (error) {
      showNotification('Failed to save settings', 'error');
    }
  }
</script>

<div class="permalink-settings">
  <header class="settings-header">
    <h1>Permalink Settings</h1>
    <p>Configure URL structure and redirects for your content</p>
  </header>
  
  <div class="settings-grid">
    <!-- Pattern Selection -->
    <section class="settings-section">
      <h2>URL Structure</h2>
      <PatternSelector 
        patterns={DEFAULT_PATTERNS}
        bind:selected={selectedPattern}
        bind:config={config.patterns}
      />
      
      <PermalinkPreview 
        url={previewUrl}
        content={previewContent}
      />
    </section>
    
    <!-- Slug Configuration -->
    <section class="settings-section">
      <h2>Slug Generation</h2>
      <SlugSettings bind:config={config.slugConfig} />
    </section>
    
    <!-- Redirect Management -->
    <section class="settings-section">
      <h2>Redirects</h2>
      <RedirectManager bind:config={config.redirectConfig} />
    </section>
    
    <!-- SEO Settings -->
    <section class="settings-section">
      <h2>SEO Configuration</h2>
      <SEOSettings bind:config={config.seoConfig} />
    </section>
  </div>
  
  <div class="settings-actions">
    <button class="btn-save" on:click={saveConfig}>
      Save Changes
    </button>
    <button class="btn-reset" on:click={() => config = data.config}>
      Reset
    </button>
  </div>
</div>
```

### Pattern Selector Component:

```svelte
<!-- lib/components/admin/PatternSelector.svelte -->
<script lang="ts">
  import type { PermalinkPattern } from '$lib/services/PermalinkManager';
  
  export let patterns: Record<string, PermalinkPattern>;
  export let selected: string;
  export let config: Record<string, PermalinkPattern>;
  
  $: patternList = Object.values(patterns);
  $: selectedPattern = patterns[selected];
</script>

<div class="pattern-selector">
  <div class="pattern-options">
    {#each patternList as pattern (pattern.id)}
      <label class="pattern-option" class:selected={selected === pattern.id}>
        <input 
          type="radio" 
          bind:group={selected} 
          value={pattern.id}
          name="permalink-pattern"
        />
        <div class="pattern-content">
          <h3>{pattern.name}</h3>
          <p class="pattern-description">{pattern.description}</p>
          <code class="pattern-example">{pattern.example}</code>
          <div class="pattern-variables">
            Variables: {pattern.variables.join(', ')}
          </div>
        </div>
      </label>
    {/each}
  </div>
  
  {#if selected === 'custom'}
    <div class="custom-pattern-editor">
      <label for="custom-pattern">Custom Pattern:</label>
      <input 
        id="custom-pattern"
        type="text" 
        bind:value={config.custom.pattern}
        placeholder="/custom/{category}/{slug}"
      />
      <p class="pattern-help">
        Available variables: {'{category}'}, {'{subcategory}'}, {'{slug}'}, {'{year}'}, {'{month}'}, {'{day}'}, {'{type}'}, {'{id}'}
      </p>
    </div>
  {/if}
</div>
```

## 🔧 Configuration Storage

### Database Schema:

```sql
-- Permalink configurations table
CREATE TABLE permalink_configs (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  config JSONB NOT NULL,
  active BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content slugs table
CREATE TABLE content_slugs (
  id SERIAL PRIMARY KEY,
  content_id UUID REFERENCES items(id),
  slug VARCHAR(255) NOT NULL,
  pattern_id VARCHAR(50) NOT NULL,
  url_path TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(slug, pattern_id),
  INDEX(slug),
  INDEX(url_path)
);

-- URL redirects table
CREATE TABLE url_redirects (
  id SERIAL PRIMARY KEY,
  from_url TEXT NOT NULL,
  to_url TEXT NOT NULL,
  redirect_type INTEGER DEFAULT 301,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX(from_url)
);
```

### Configuration API:

```typescript
// routes/api/admin/permalinks/+server.ts
export async function GET() {
  const config = await getPermalinkConfig();
  return json(config);
}

export async function POST({ request }) {
  const newConfig = await request.json();
  
  // Validate configuration
  const validationResult = validatePermalinkConfig(newConfig);
  if (!validationResult.valid) {
    return json({ error: validationResult.errors }, { status: 400 });
  }
  
  // Save configuration
  await savePermalinkConfig(newConfig);
  
  // Regenerate all URLs if pattern changed
  if (newConfig.regenerateUrls) {
    await regenerateAllUrls(newConfig);
  }
  
  return json({ success: true });
}
```

## 🚀 Implementation Roadmap

### Phase 1: Core System (Week 1)
- [ ] Implement PermalinkManager class
- [ ] Create URL pattern definitions
- [ ] Build slug generation service
- [ ] Add database schema

### Phase 2: Redirect Engine (Week 2)
- [ ] Implement RedirectEngine class
- [ ] Create legacy URL mappings
- [ ] Add redirect middleware
- [ ] Test redirect functionality

### Phase 3: Admin Interface (Week 3)
- [ ] Build permalink settings page
- [ ] Create pattern selector component
- [ ] Add slug configuration UI
- [ ] Implement redirect management

### Phase 4: Integration (Week 4)
- [ ] Integrate with existing routing
- [ ] Update content creation flow
- [ ] Add URL regeneration tools
- [ ] Performance optimization

## 📊 Performance Considerations

### Optimization Strategies:
- **Caching**: Cache generated URLs in memory and database
- **Batch Processing**: Generate URLs in batches during migration
- **Lazy Loading**: Load redirect rules on demand
- **Indexing**: Database indexes on slug and URL columns

### Monitoring:
- **URL Generation Time**: Track performance of slug generation
- **Redirect Performance**: Monitor redirect lookup speed
- **Cache Hit Rate**: Track URL cache effectiveness
- **Error Rates**: Monitor 404 and redirect errors

---

This permalink configuration system provides WordPress-level URL management flexibility while maintaining the neural theme and ensuring optimal performance for PRSNL.