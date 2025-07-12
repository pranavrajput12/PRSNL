# PRSNL Permalink Modernization Plan

## Current Issues
- Inconsistent naming: `/item/[id]` vs `/items/[id]`
- Only numeric IDs, no SEO-friendly slugs
- Static routes where dynamic would be better
- Cryptic abbreviated route names

## Proposed Modern Structure

### Before → After

```
/item/[id]           → /thoughts/[slug]         (consolidate item routes)
/items/[id]          → /thoughts/[slug]         (remove duplicate)
/videos/[id]         → /videos/[slug]          (add slug support)
/code-cortex/docs    → /code/docs/[slug]       (make dynamic)
/code-cortex/links   → /code/links/[slug]      (make dynamic)  
/code-cortex/projects → /code/projects/[slug]   (make dynamic)
/code-cortex/synapses → /code/insights/[slug]   (rename + dynamic)
/c/[category]/[slug] → /topics/[category]/[slug] (more descriptive)
/p/[tool]           → /tools/[tool]            (more descriptive)
/s/[page]           → /search/[query]          (more descriptive)
```

### New URL Examples

```
Current: /item/123
Modern:  /thoughts/fixing-frontend-routing-issues

Current: /videos/456  
Modern:  /videos/building-knowledge-graphs

Current: /code-cortex/docs
Modern:  /code/docs/api-documentation-guide

Current: /c/ai/machine-learning
Modern:  /topics/ai/machine-learning

Current: /p/calculator
Modern:  /tools/calculator
```

## Implementation Plan

### Phase 1: Core Route Restructuring
1. Create new route directories with modern names
2. Consolidate `/item/` and `/items/` into `/thoughts/`
3. Convert static code-cortex routes to dynamic `/code/[category]/[slug]`
4. Rename cryptic routes (`/c/` → `/topics/`, `/p/` → `/tools/`)

### Phase 2: Slug Support
1. Add slug generation utility functions
2. Update API to support slug-based lookups
3. Generate slugs from existing content titles
4. Add slug validation and uniqueness checks

### Phase 3: Migration & Redirects  
1. Implement redirect middleware for old URLs
2. Update all internal links to use new structure
3. Update test suite with new URLs
4. Update sitemap and SEO meta tags

### Phase 4: Backend Integration
1. Add slug columns to database schema
2. Update API endpoints to handle slugs
3. Implement slug-based content resolution
4. Add slug regeneration for title changes

## Benefits

- **SEO-Friendly**: Descriptive URLs improve search ranking
- **User-Friendly**: URLs convey meaning and context  
- **Consistent**: Single naming convention across all routes
- **Maintainable**: Clear structure is easier to understand
- **Future-Proof**: Extensible pattern for new content types

## Backward Compatibility

- Old numeric ID URLs will redirect to new slug URLs
- API will support both ID and slug lookups during transition
- Gradual migration to avoid breaking existing bookmarks
