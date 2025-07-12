# 🛣️ SvelteKit Routing Structure for PRSNL Permalink System

## 📋 Overview

This document outlines the technical implementation of the new permalink architecture using SvelteKit's file-based routing system. The design implements the hybrid semantic hierarchy with neural-themed URLs while maintaining backward compatibility.

## 🏗️ Directory Structure

### Complete Route Structure:

```
src/routes/
├── (app)/                              # Main application group
│   ├── neural/                         # Content archive hub
│   │   ├── [category]/                 # Dynamic category routes
│   │   │   ├── [subcategory]/          # Dynamic subcategory routes
│   │   │   │   ├── [slug]/             # Individual content items
│   │   │   │   │   ├── +page.svelte    # Content detail page
│   │   │   │   │   ├── +page.server.ts # Server-side data loading
│   │   │   │   │   └── +layout.svelte  # Content item layout
│   │   │   │   ├── +page.svelte        # Subcategory index (list view)
│   │   │   │   ├── +page.server.ts     # Subcategory data loading
│   │   │   │   └── +layout.svelte      # Subcategory layout
│   │   │   ├── +page.svelte            # Category index page
│   │   │   ├── +page.server.ts         # Category data loading
│   │   │   └── +layout.svelte          # Category layout with nav
│   │   ├── +page.svelte                # Neural hub main page
│   │   ├── +page.server.ts             # Neural hub data
│   │   └── +layout.svelte              # Neural section layout
│   ├── processing/                     # Analysis centers
│   │   ├── timeline/
│   │   │   ├── +page.svelte            # Timeline interface
│   │   │   └── +page.server.ts         # Timeline data
│   │   ├── insights/
│   │   │   ├── +page.svelte            # AI insights dashboard
│   │   │   └── +page.server.ts         # Analytics data
│   │   ├── chat/
│   │   │   ├── +page.svelte            # Mind Palace chat
│   │   │   └── +page.server.ts         # Chat state management
│   │   ├── visual/
│   │   │   ├── +page.svelte            # Visual cortex (videos)
│   │   │   ├── +page.server.ts         # Video data
│   │   │   └── [slug]/
│   │   │       ├── +page.svelte        # Individual video player
│   │   │       └── +page.server.ts     # Video metadata
│   │   └── code/
│   │       ├── +page.svelte            # Code cortex dashboard
│   │       ├── +page.server.ts         # Development data
│   │       └── [section]/
│   │           ├── +page.svelte        # Code section view
│   │           └── +page.server.ts     # Section data
│   ├── system/                         # System management
│   │   ├── import/
│   │   │   ├── +page.svelte            # Import interface
│   │   │   ├── v1/+page.svelte         # Import v1
│   │   │   └── v2/+page.svelte         # Import v2
│   │   ├── settings/
│   │   │   ├── +page.svelte            # Settings page
│   │   │   └── +page.server.ts         # Settings data
│   │   ├── docs/
│   │   │   ├── +page.svelte            # Documentation hub
│   │   │   └── [topic]/+page.svelte    # Documentation topics
│   │   └── health/
│   │       ├── +page.svelte            # System health
│   │       └── +page.server.ts         # Health checks
│   └── +layout.svelte                  # Main app layout
├── capture/                            # Content creation (remains unchanged)
│   ├── +page.svelte
│   └── +page.server.ts
├── +page.svelte                        # Homepage (Neural Nest)
├── +page.server.ts                     # Homepage data
├── +layout.svelte                      # Root layout
├── +error.svelte                       # Error page
└── +hooks.server.ts                    # Server hooks for redirects
```

## 🔧 Dynamic Route Parameters

### Category/Subcategory/Slug Pattern:

```typescript
// /neural/[category]/[subcategory]/[slug]/+page.server.ts
export async function load({ params, url }) {
  const { category, subcategory, slug } = params;
  
  // Validate category and subcategory
  if (!VALID_CATEGORIES.includes(category)) {
    throw error(404, 'Category not found');
  }
  
  if (!VALID_SUBCATEGORIES[category].includes(subcategory)) {
    throw error(404, 'Subcategory not found');
  }
  
  // Fetch content by slug
  const content = await getContentBySlug(slug, category, subcategory);
  
  if (!content) {
    throw error(404, 'Content not found');
  }
  
  return {
    content,
    breadcrumbs: generateBreadcrumbs(category, subcategory, content.title),
    relatedContent: await getRelatedContent(content.id, category),
    seo: generateSEOData(content)
  };
}
```

### Valid Route Configurations:

```typescript
export const VALID_CATEGORIES = [
  'development',
  'learning', 
  'media',
  'thoughts'
] as const;

export const VALID_SUBCATEGORIES = {
  development: ['repositories', 'documentation', 'projects', 'snippets', 'tools'],
  learning: ['articles', 'tutorials', 'courses', 'references'],
  media: ['videos', 'images', 'audio', 'presentations'],
  thoughts: ['notes', 'ideas', 'reflections', 'bookmarks']
} as const;

export const ROUTE_PATTERNS = {
  content: '/neural/[category]/[subcategory]/[slug]',
  category: '/neural/[category]',
  subcategory: '/neural/[category]/[subcategory]',
  processing: '/processing/[tool]',
  system: '/system/[service]'
} as const;
```

## 📄 Page Component Structure

### Content Detail Page (`/neural/[category]/[subcategory]/[slug]/+page.svelte`):

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import Breadcrumbs from '$lib/components/navigation/Breadcrumbs.svelte';
  import ContentViewer from '$lib/components/content/ContentViewer.svelte';
  import RelatedContent from '$lib/components/content/RelatedContent.svelte';
  import ShareButton from '$lib/components/ui/ShareButton.svelte';
  import type { PageData } from './$types';
  
  export let data: PageData;
  
  $: ({ content, breadcrumbs, relatedContent, seo } = data);
  $: canonical = `${$page.url.origin}${$page.url.pathname}`;
</script>

<svelte:head>
  <title>{seo.title} | PRSNL</title>
  <meta name="description" content={seo.description} />
  <meta property="og:title" content={seo.title} />
  <meta property="og:description" content={seo.description} />
  <meta property="og:url" content={canonical} />
  <link rel="canonical" href={canonical} />
</svelte:head>

<div class="content-page">
  <Breadcrumbs items={breadcrumbs} />
  
  <header class="content-header">
    <h1>{content.title}</h1>
    <div class="content-meta">
      <span class="category">{content.category}</span>
      <span class="date">{content.created_at}</span>
      <ShareButton url={canonical} title={content.title} />
    </div>
  </header>
  
  <main class="content-main">
    <ContentViewer {content} />
  </main>
  
  <aside class="content-sidebar">
    <RelatedContent items={relatedContent} />
  </aside>
</div>
```

### Category Index Page (`/neural/[category]/+page.svelte`):

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import Breadcrumbs from '$lib/components/navigation/Breadcrumbs.svelte';
  import CategoryGrid from '$lib/components/content/CategoryGrid.svelte';
  import FilterBar from '$lib/components/ui/FilterBar.svelte';
  import type { PageData } from './$types';
  
  export let data: PageData;
  
  $: ({ category, subcategories, items, filters, breadcrumbs } = data);
</script>

<div class="category-page">
  <Breadcrumbs items={breadcrumbs} />
  
  <header class="category-header">
    <h1>{category.title}</h1>
    <p>{category.description}</p>
  </header>
  
  <FilterBar {filters} />
  
  <CategoryGrid {subcategories} {items} />
</div>
```

## 🔄 URL Redirect System

### Server Hooks for Legacy URL Redirects (`+hooks.server.ts`):

```typescript
import type { Handle } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';

const LEGACY_REDIRECTS = new Map([
  // Old item URLs to new neural structure
  ['/items/', '/neural/'],
  ['/videos/', '/processing/visual/'],
  ['/timeline', '/processing/timeline'],
  ['/insights', '/processing/insights'],
  ['/chat', '/processing/chat'],
  ['/code-cortex', '/processing/code'],
  ['/import', '/system/import'],
  ['/settings', '/system/settings'],
  ['/docs', '/system/docs']
]);

const ITEM_ID_PATTERN = /^\/items\/([a-f0-9-]+)$/;
const VIDEO_ID_PATTERN = /^\/videos\/([a-f0-9-]+)$/;

export const handle: Handle = async ({ event, resolve }) => {
  const pathname = event.url.pathname;
  
  // Handle legacy static redirects
  for (const [oldPath, newPath] of LEGACY_REDIRECTS) {
    if (pathname.startsWith(oldPath)) {
      throw redirect(301, pathname.replace(oldPath, newPath));
    }
  }
  
  // Handle dynamic item ID redirects
  const itemMatch = pathname.match(ITEM_ID_PATTERN);
  if (itemMatch) {
    const itemId = itemMatch[1];
    const newUrl = await getNewUrlFromItemId(itemId);
    if (newUrl) {
      throw redirect(301, newUrl);
    }
  }
  
  // Handle video ID redirects  
  const videoMatch = pathname.match(VIDEO_ID_PATTERN);
  if (videoMatch) {
    const videoId = videoMatch[1];
    const newUrl = await getNewUrlFromVideoId(videoId);
    if (newUrl) {
      throw redirect(301, newUrl);
    }
  }
  
  return resolve(event);
};

async function getNewUrlFromItemId(itemId: string): Promise<string | null> {
  // Query database to get item category, subcategory, and slug
  const item = await getItemById(itemId);
  if (!item) return null;
  
  return `/neural/${item.category}/${item.subcategory}/${item.slug}`;
}
```

## 🧭 Breadcrumb Generation

### Dynamic Breadcrumb Service:

```typescript
// lib/services/breadcrumbService.ts
export interface BreadcrumbItem {
  label: string;
  href: string;
  icon?: string;
  active?: boolean;
}

export function generateBreadcrumbs(
  category: string,
  subcategory?: string,
  title?: string
): BreadcrumbItem[] {
  const breadcrumbs: BreadcrumbItem[] = [
    { label: 'Home', href: '/', icon: 'home' },
    { label: 'Neural', href: '/neural', icon: 'brain' }
  ];
  
  // Add category
  if (category) {
    breadcrumbs.push({
      label: categoryLabels[category] || category,
      href: `/neural/${category}`,
      icon: categoryIcons[category]
    });
  }
  
  // Add subcategory  
  if (subcategory) {
    breadcrumbs.push({
      label: subcategoryLabels[subcategory] || subcategory,
      href: `/neural/${category}/${subcategory}`,
      icon: subcategoryIcons[subcategory]
    });
  }
  
  // Add current page
  if (title) {
    breadcrumbs.push({
      label: title,
      href: '',
      active: true
    });
  }
  
  return breadcrumbs;
}

const categoryLabels = {
  development: 'Development',
  learning: 'Learning',
  media: 'Media',
  thoughts: 'Thoughts'
};

const categoryIcons = {
  development: 'code',
  learning: 'book',
  media: 'play',
  thoughts: 'lightbulb'
};
```

## 🔍 SEO & Meta Data

### SEO Data Generation:

```typescript
// lib/services/seoService.ts
export interface SEOData {
  title: string;
  description: string;
  keywords: string[];
  type: string;
  image?: string;
}

export function generateSEOData(content: any, category: string, subcategory: string): SEOData {
  return {
    title: `${content.title} | ${categoryLabels[category]} | PRSNL`,
    description: content.summary || content.description || `${content.title} in ${category}`,
    keywords: [
      content.title,
      category,
      subcategory,
      ...(content.tags || []),
      'PRSNL',
      'neural',
      'knowledge'
    ],
    type: getOpenGraphType(category, subcategory),
    image: content.thumbnail || content.preview_image
  };
}

function getOpenGraphType(category: string, subcategory: string): string {
  if (category === 'media' && subcategory === 'videos') return 'video.other';
  if (category === 'media' && subcategory === 'images') return 'image';
  if (category === 'learning') return 'article';
  return 'website';
}
```

## 📱 Layout Components

### Neural Section Layout (`/neural/+layout.svelte`):

```svelte
<script lang="ts">
  import { page } from '$app/stores';
  import CategoryNav from '$lib/components/navigation/CategoryNav.svelte';
  import SearchBox from '$lib/components/ui/SearchBox.svelte';
  
  $: currentCategory = $page.params.category;
  $: currentSubcategory = $page.params.subcategory;
</script>

<div class="neural-layout">
  <header class="neural-header">
    <div class="neural-title">
      <h1>Neural Archive</h1>
      <p>Your personal knowledge repository</p>
    </div>
    <SearchBox placeholder="Search neural archive..." />
  </header>
  
  <nav class="neural-nav">
    <CategoryNav {currentCategory} {currentSubcategory} />
  </nav>
  
  <main class="neural-content">
    <slot />
  </main>
</div>
```

## 🎯 Implementation Checklist

### Phase 1: Route Structure
- [ ] Create new route directory structure
- [ ] Implement dynamic route parameters
- [ ] Add route validation logic
- [ ] Create layout components

### Phase 2: Data Layer
- [ ] Add slug generation to backend
- [ ] Update database schema for categories
- [ ] Implement content fetching by slug
- [ ] Create category/subcategory APIs

### Phase 3: Navigation
- [ ] Build breadcrumb component
- [ ] Create category navigation
- [ ] Implement search integration
- [ ] Add pagination for category views

### Phase 4: Redirects & SEO
- [ ] Implement legacy URL redirects
- [ ] Add SEO meta data generation
- [ ] Create sitemap generation
- [ ] Add structured data markup

### Phase 5: Testing & Polish
- [ ] Test all route patterns
- [ ] Validate redirect functionality
- [ ] Check mobile navigation
- [ ] Performance optimization

---

## 🔧 Development Commands

```bash
# Generate route structure
npm run generate:routes

# Test route patterns
npm run test:routes

# Build sitemap
npm run build:sitemap

# Validate redirects
npm run test:redirects
```

*This routing structure provides a scalable, maintainable foundation for the PRSNL permalink system while preserving existing functionality and improving user experience.*