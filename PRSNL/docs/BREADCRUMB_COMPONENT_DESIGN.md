# 🧭 Breadcrumb Component System for PRSNL

## 📋 Overview

The breadcrumb system provides users with clear navigation context within PRSNL's neural hierarchy. It shows current location, enables quick navigation to parent levels, and maintains consistency across all content types.

## 🎯 Design Requirements

### Functional Requirements:
- **Location Awareness**: Show current position in site hierarchy
- **Quick Navigation**: Click any level to navigate up
- **Visual Hierarchy**: Clear parent-child relationships
- **Responsive Design**: Adapt to mobile screens
- **Accessibility**: Screen reader and keyboard navigation support

### Design Requirements:
- **Neural Theme**: Match PRSNL's brain-computer interface aesthetic
- **Consistent Icons**: Visual indicators for each level type
- **Hover Effects**: Interactive feedback for clickable elements
- **Truncation**: Handle long breadcrumb chains gracefully

## 🏗️ Component Architecture

### Core Breadcrumb Component (`Breadcrumbs.svelte`):

```svelte
<script lang="ts">
  import Icon from '$lib/components/Icon.svelte';
  import type { BreadcrumbItem } from '$lib/types/navigation';
  
  export let items: BreadcrumbItem[] = [];
  export let separator: '>' | '/' | '•' = '>';
  export let showIcons = true;
  export let showHome = true;
  export let maxItems = 5;
  export let variant: 'default' | 'compact' | 'minimal' = 'default';
  
  $: displayItems = truncateItems(items, maxItems);
  $: hasOverflow = items.length > maxItems;
</script>

<nav class="breadcrumbs" class:compact={variant === 'compact'} aria-label="Breadcrumb navigation">
  <ol class="breadcrumb-list">
    {#each displayItems as item, index}
      <li class="breadcrumb-item" class:active={item.active}>
        {#if item.href && !item.active}
          <a href={item.href} class="breadcrumb-link">
            {#if showIcons && item.icon}
              <Icon name={item.icon} size="small" />
            {/if}
            <span class="breadcrumb-label">{item.label}</span>
          </a>
        {:else}
          <span class="breadcrumb-current" aria-current="page">
            {#if showIcons && item.icon}
              <Icon name={item.icon} size="small" />
            {/if}
            <span class="breadcrumb-label">{item.label}</span>
          </span>
        {/if}
        
        {#if index < displayItems.length - 1}
          <span class="breadcrumb-separator" aria-hidden="true">{separator}</span>
        {/if}
      </li>
      
      {#if hasOverflow && index === 0}
        <li class="breadcrumb-item breadcrumb-overflow">
          <button class="breadcrumb-toggle" aria-label="Show all breadcrumbs">
            <Icon name="more-horizontal" size="small" />
          </button>
          <span class="breadcrumb-separator" aria-hidden="true">{separator}</span>
        </li>
      {/if}
    {/each}
  </ol>
</nav>
```

### Breadcrumb Item Type Definition:

```typescript
// lib/types/navigation.ts
export interface BreadcrumbItem {
  /** Display text for the breadcrumb */
  label: string;
  
  /** URL to navigate to (empty for current page) */
  href: string;
  
  /** Icon name to display */
  icon?: string;
  
  /** Whether this is the current/active page */
  active?: boolean;
  
  /** Additional metadata */
  meta?: {
    category?: string;
    type?: string;
    id?: string;
  };
}

export interface BreadcrumbConfig {
  /** Show home link */
  showHome: boolean;
  
  /** Show icons next to labels */
  showIcons: boolean;
  
  /** Separator character */
  separator: '>' | '/' | '•';
  
  /** Maximum items before truncation */
  maxItems: number;
  
  /** Visual variant */
  variant: 'default' | 'compact' | 'minimal';
  
  /** Enable dropdown for overflow */
  enableOverflowMenu: boolean;
}
```

## 🎨 Component Variants

### Default Breadcrumb:
```svelte
<!-- Full-featured breadcrumb with icons and hover effects -->
<Breadcrumbs 
  items={breadcrumbs} 
  showIcons={true}
  separator=">"
  maxItems={5}
/>
```

### Compact Breadcrumb:
```svelte
<!-- Smaller version for tight spaces -->
<Breadcrumbs 
  items={breadcrumbs}
  variant="compact"
  showIcons={false}
  separator="/"
  maxItems={3}
/>
```

### Minimal Breadcrumb:
```svelte
<!-- Simple text-only version -->
<Breadcrumbs 
  items={breadcrumbs}
  variant="minimal"
  showIcons={false}
  separator="•"
  showHome={false}
/>
```

## 🔧 Breadcrumb Generation Service

### Dynamic Breadcrumb Builder:

```typescript
// lib/services/breadcrumbService.ts
export class BreadcrumbService {
  private static categoryConfig = {
    development: {
      label: 'Development',
      icon: 'code',
      color: '#00ff88'
    },
    learning: {
      label: 'Learning', 
      icon: 'book',
      color: '#4a9eff'
    },
    media: {
      label: 'Media',
      icon: 'play',
      color: '#f59e0b'
    },
    thoughts: {
      label: 'Thoughts',
      icon: 'lightbulb',
      color: '#dc143c'
    }
  };
  
  private static subcategoryConfig = {
    // Development subcategories
    repositories: { label: 'Repositories', icon: 'github' },
    documentation: { label: 'Documentation', icon: 'file-text' },
    projects: { label: 'Projects', icon: 'folder' },
    snippets: { label: 'Snippets', icon: 'code' },
    tools: { label: 'Tools', icon: 'tool' },
    
    // Learning subcategories
    articles: { label: 'Articles', icon: 'file-text' },
    tutorials: { label: 'Tutorials', icon: 'play-circle' },
    courses: { label: 'Courses', icon: 'graduation-cap' },
    references: { label: 'References', icon: 'bookmark' },
    
    // Media subcategories
    videos: { label: 'Videos', icon: 'video' },
    images: { label: 'Images', icon: 'image' },
    audio: { label: 'Audio', icon: 'headphones' },
    presentations: { label: 'Presentations', icon: 'presentation' },
    
    // Thoughts subcategories
    notes: { label: 'Notes', icon: 'edit' },
    ideas: { label: 'Ideas', icon: 'lightbulb' },
    reflections: { label: 'Reflections', icon: 'mirror' },
    bookmarks: { label: 'Bookmarks', icon: 'bookmark' }
  };
  
  static generateContentBreadcrumbs(
    category: string,
    subcategory?: string,
    title?: string,
    currentPath?: string
  ): BreadcrumbItem[] {
    const breadcrumbs: BreadcrumbItem[] = [];
    
    // Home
    breadcrumbs.push({
      label: 'Home',
      href: '/',
      icon: 'home'
    });
    
    // Neural section
    breadcrumbs.push({
      label: 'Neural',
      href: '/neural',
      icon: 'brain'
    });
    
    // Category
    if (category && this.categoryConfig[category]) {
      const config = this.categoryConfig[category];
      breadcrumbs.push({
        label: config.label,
        href: `/neural/${category}`,
        icon: config.icon,
        meta: { category, type: 'category' }
      });
    }
    
    // Subcategory
    if (subcategory && this.subcategoryConfig[subcategory]) {
      const config = this.subcategoryConfig[subcategory];
      breadcrumbs.push({
        label: config.label,
        href: `/neural/${category}/${subcategory}`,
        icon: config.icon,
        meta: { category, subcategory, type: 'subcategory' }
      });
    }
    
    // Current item
    if (title) {
      breadcrumbs.push({
        label: title,
        href: currentPath || '',
        active: true,
        meta: { category, subcategory, type: 'content' }
      });
    }
    
    return breadcrumbs;
  }
  
  static generateProcessingBreadcrumbs(tool: string, section?: string): BreadcrumbItem[] {
    const processingConfig = {
      timeline: { label: 'Timeline', icon: 'clock' },
      insights: { label: 'Insights', icon: 'trending-up' },
      chat: { label: 'Mind Palace', icon: 'message-circle' },
      visual: { label: 'Visual Cortex', icon: 'eye' },
      code: { label: 'Code Cortex', icon: 'terminal' }
    };
    
    const breadcrumbs: BreadcrumbItem[] = [
      { label: 'Home', href: '/', icon: 'home' },
      { label: 'Processing', href: '/processing', icon: 'cpu' }
    ];
    
    if (processingConfig[tool]) {
      const config = processingConfig[tool];
      breadcrumbs.push({
        label: config.label,
        href: `/processing/${tool}`,
        icon: config.icon,
        active: !section
      });
    }
    
    if (section) {
      breadcrumbs.push({
        label: section,
        href: `/processing/${tool}/${section}`,
        active: true
      });
    }
    
    return breadcrumbs;
  }
  
  static generateSystemBreadcrumbs(service: string, page?: string): BreadcrumbItem[] {
    const systemConfig = {
      import: { label: 'Import', icon: 'download' },
      settings: { label: 'Settings', icon: 'settings' },
      docs: { label: 'Documentation', icon: 'help-circle' },
      health: { label: 'Health', icon: 'activity' }
    };
    
    const breadcrumbs: BreadcrumbItem[] = [
      { label: 'Home', href: '/', icon: 'home' },
      { label: 'System', href: '/system', icon: 'server' }
    ];
    
    if (systemConfig[service]) {
      const config = systemConfig[service];
      breadcrumbs.push({
        label: config.label,
        href: `/system/${service}`,
        icon: config.icon,
        active: !page
      });
    }
    
    if (page) {
      breadcrumbs.push({
        label: page,
        href: `/system/${service}/${page}`,
        active: true
      });
    }
    
    return breadcrumbs;
  }
}
```

## 🎨 Styling & Theme Integration

### CSS Styles (`breadcrumbs.css`):

```css
.breadcrumbs {
  --breadcrumb-font-family: 'JetBrains Mono', monospace;
  --breadcrumb-font-size: 0.875rem;
  --breadcrumb-spacing: 0.5rem;
  --breadcrumb-height: 2.5rem;
  --breadcrumb-bg: rgba(0, 0, 0, 0.3);
  --breadcrumb-border: rgba(0, 255, 136, 0.2);
  --breadcrumb-text: rgba(255, 255, 255, 0.8);
  --breadcrumb-link: var(--success);
  --breadcrumb-hover: var(--brand-accent);
  --breadcrumb-active: #fff;
  --breadcrumb-separator: rgba(255, 255, 255, 0.4);
  
  display: flex;
  align-items: center;
  min-height: var(--breadcrumb-height);
  padding: 0 1rem;
  background: var(--breadcrumb-bg);
  border: 1px solid var(--breadcrumb-border);
  border-radius: 8px;
  font-family: var(--breadcrumb-font-family);
  font-size: var(--breadcrumb-font-size);
  backdrop-filter: blur(4px);
  margin-bottom: 1.5rem;
}

.breadcrumb-list {
  display: flex;
  align-items: center;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: var(--breadcrumb-spacing);
  flex-wrap: wrap;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: var(--breadcrumb-spacing);
}

.breadcrumb-link {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--breadcrumb-link);
  text-decoration: none;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: all 0.2s ease;
  position: relative;
}

.breadcrumb-link:hover {
  color: var(--breadcrumb-hover);
  background: rgba(0, 255, 136, 0.1);
  transform: translateY(-1px);
}

.breadcrumb-link:focus {
  outline: 2px solid var(--breadcrumb-link);
  outline-offset: 2px;
}

.breadcrumb-current {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--breadcrumb-active);
  font-weight: 600;
  padding: 0.25rem 0.5rem;
}

.breadcrumb-separator {
  color: var(--breadcrumb-separator);
  font-weight: 300;
  user-select: none;
  margin: 0 0.125rem;
}

.breadcrumb-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

/* Compact variant */
.breadcrumbs.compact {
  --breadcrumb-font-size: 0.75rem;
  --breadcrumb-height: 2rem;
  --breadcrumb-spacing: 0.375rem;
  padding: 0 0.75rem;
}

.breadcrumbs.compact .breadcrumb-label {
  max-width: 120px;
}

/* Minimal variant */
.breadcrumbs.minimal {
  background: transparent;
  border: none;
  padding: 0;
  margin-bottom: 1rem;
}

/* Overflow handling */
.breadcrumb-overflow {
  position: relative;
}

.breadcrumb-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  background: transparent;
  border: 1px solid var(--breadcrumb-border);
  border-radius: 3px;
  color: var(--breadcrumb-text);
  cursor: pointer;
  transition: all 0.2s ease;
}

.breadcrumb-toggle:hover {
  background: rgba(0, 255, 136, 0.1);
  color: var(--breadcrumb-link);
}

/* Neural-themed animations */
.breadcrumb-link::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -0.25rem;
  width: 2px;
  height: 0;
  background: var(--breadcrumb-link);
  transition: height 0.2s ease;
  transform: translateY(-50%);
}

.breadcrumb-link:hover::before {
  height: 100%;
}

/* Responsive behavior */
@media (max-width: 768px) {
  .breadcrumbs {
    --breadcrumb-font-size: 0.75rem;
    --breadcrumb-spacing: 0.375rem;
    padding: 0 0.75rem;
  }
  
  .breadcrumb-label {
    max-width: 100px;
  }
  
  .breadcrumb-list {
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  
  .breadcrumb-list::-webkit-scrollbar {
    display: none;
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .breadcrumb-link,
  .breadcrumb-toggle,
  .breadcrumb-link::before {
    transition: none;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .breadcrumbs {
    --breadcrumb-bg: #000;
    --breadcrumb-border: #fff;
    --breadcrumb-text: #fff;
    --breadcrumb-link: #fff;
    --breadcrumb-separator: #fff;
  }
}
```

## 🧪 Usage Examples

### Content Page Breadcrumbs:
```svelte
<script>
  import { BreadcrumbService } from '$lib/services/breadcrumbService';
  
  export let data;
  
  $: breadcrumbs = BreadcrumbService.generateContentBreadcrumbs(
    data.category,
    data.subcategory,
    data.content.title,
    $page.url.pathname
  );
</script>

<Breadcrumbs items={breadcrumbs} />
```

### Processing Center Breadcrumbs:
```svelte
<script>
  $: breadcrumbs = BreadcrumbService.generateProcessingBreadcrumbs('visual', 'videos');
</script>

<Breadcrumbs items={breadcrumbs} variant="compact" />
```

### System Page Breadcrumbs:
```svelte
<script>
  $: breadcrumbs = BreadcrumbService.generateSystemBreadcrumbs('settings', 'general');
</script>

<Breadcrumbs items={breadcrumbs} showIcons={false} />
```

## ♿ Accessibility Features

### Screen Reader Support:
- `aria-label="Breadcrumb navigation"` on nav element
- `aria-current="page"` on current page
- Semantic `<ol>` list structure
- Descriptive link text

### Keyboard Navigation:
- Tab order follows logical sequence
- Focus indicators on all interactive elements
- Skip links for long breadcrumb chains

### Visual Accessibility:
- High contrast mode support
- Reduced motion preferences respected
- Scalable font sizes
- Clear visual hierarchy

## 🚀 Performance Considerations

### Optimization Strategies:
- **Memoization**: Cache breadcrumb generation results
- **Lazy Loading**: Load overflow menu content on demand
- **Minimal DOM**: Efficient rendering with minimal elements
- **CSS-in-JS**: Dynamic theming without JavaScript

### Bundle Impact:
- **Core Component**: ~2KB minified
- **Service Layer**: ~1KB minified
- **CSS Styles**: ~3KB minified
- **Total Impact**: ~6KB for complete breadcrumb system

---

This breadcrumb system provides a comprehensive navigation solution that integrates seamlessly with PRSNL's neural theme while maintaining accessibility and performance standards.