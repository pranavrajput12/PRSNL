# 📊 PRSNL Content Type System Map & API Filter Documentation

## 🎯 Overview

This document provides a comprehensive map of how content types flow through the entire PRSNL system - from initial capture to final display and filtering. This ensures consistency and helps prevent the content categorization issues we experienced.

## 🗂️ Content Type Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   USER INPUT    │ → │  PROCESSING     │ → │    STORAGE      │
│                 │    │                 │    │                 │
│ • Manual Type   │    │ • AI Analysis  │    │ • Database      │
│ • File Upload   │    │ • Type Mapping  │    │ • Type Column   │
│ • URL Capture   │    │ • Validation    │    │ • Metadata      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FILTERING     │ ← │   API LAYER     │ ← │   RETRIEVAL     │
│                 │    │                 │    │                 │
│ • Frontend UI   │    │ • Timeline API  │    │ • Database      │
│ • Type Buttons  │    │ • Search API    │    │ • Query Logic   │
│ • Search        │    │ • Filter Logic  │    │ • Type Mapping  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Master Content Types Registry

### Core Content Types
| Type | Description | File Extensions | URL Patterns | AI Detection |
|------|-------------|----------------|--------------|--------------|
| `document` | Text documents, PDFs, Office files | `.pdf`, `.doc`, `.docx`, `.txt`, `.csv` | N/A | Document analysis |
| `video` | Video content from platforms | N/A | YouTube, Vimeo, Twitter video | Platform detection |
| `article` | Web articles, blog posts | N/A | News sites, blogs | Content analysis |
| `link` | Simple web bookmarks | N/A | Any URL (fallback) | Minimal processing |
| `image` | Image files and visual content | `.jpg`, `.png`, `.gif`, `.svg` | Image URLs | Visual analysis |
| `tutorial` | Educational content | N/A | Tutorial sites, courses | AI classification |
| `note` | Personal notes and text | `.txt`, `.md` | N/A | User-generated |
| `auto` | System auto-detection | Any | Any | Full AI analysis |

## 🔄 Content Type Processing Pipeline

### 1. Input Stage (`/api/capture`)

#### File Upload Processing
```javascript
// File Extension → Type Mapping
const FILE_TYPE_MAP = {
  '.pdf': 'document',
  '.doc': 'document', 
  '.docx': 'document',
  '.txt': 'document',
  '.csv': 'document',
  '.jpg': 'image',
  '.png': 'image',
  '.gif': 'image',
  '.svg': 'image',
  '.md': 'note'
};
```

#### URL Processing
```python
# Platform Detection Logic (backend/app/services/media_detector.py)
PLATFORM_PATTERNS = {
    'youtube': ['youtube.com', 'youtu.be'] → 'video',
    'vimeo': ['vimeo.com'] → 'video', 
    'twitter': ['twitter.com', 'x.com'] → 'article/video',
    'github': ['github.com'] → 'link',
    'news_sites': [...] → 'article'
}
```

#### AI Auto-Detection
```python
# AI Analysis Pipeline (backend/app/services/unified_ai_service.py)
def detect_content_type(content, url, metadata):
    if is_video_platform(url):
        return 'video'
    elif is_document_like(content):
        return 'document'  
    elif is_tutorial_content(content):
        return 'tutorial'
    else:
        return 'article'  # Default fallback
```

### 2. Storage Stage (Database)

#### Items Table Schema
```sql
CREATE TABLE items (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT,
    type TEXT NOT NULL,  -- ← CRITICAL: This is the authoritative type
    content TEXT,
    summary TEXT,
    metadata JSONB,
    created_at TIMESTAMP,
    -- ... other fields
);
```

#### Type Validation
```python
# Allowed types in database
VALID_TYPES = [
    'auto', 'document', 'video', 'article', 
    'tutorial', 'image', 'note', 'link'
]
```

## 🔍 API Filtering System

### 1. Timeline API (`/api/timeline`)

#### Current Implementation (FIXED)
```python
# backend/app/api/timeline.py - CRITICAL FIX APPLIED
query = """
    SELECT 
        i.id,
        i.title,
        i.url,
        i.summary,
        i.processed_content as content,
        i.type as type,  -- ← USING ACTUAL DATABASE TYPE (FIXED!)
        i.created_at,
        -- ... other fields
    FROM items i
    WHERE ($1::text IS NULL OR i.type = $1)  -- Type filtering
    ORDER BY i.created_at DESC
"""
```

#### OLD BROKEN Implementation (FIXED)
```python
# THIS WAS WRONG - HARDCODED LOGIC IGNORING DATABASE
CASE 
    WHEN i.url LIKE '%youtube.com%' THEN 'video'
    WHEN i.url LIKE '%.pdf' THEN 'pdf'  
    ELSE 'article'
END as type,  -- ← IGNORED ACTUAL DATABASE TYPE!
```

### 2. Search API (`/api/search`)

#### Type-Based Search
```python
# backend/app/api/search.py
query = """
    SELECT i.id, i.title, i.url, i.type, i.summary
    FROM items i 
    WHERE ($3::text IS NULL OR i.type = $3)  -- Type filter
    AND (
        to_tsvector('english', i.title || ' ' || COALESCE(i.summary, '')) 
        @@ plainto_tsquery('english', $1)
    )
"""
```

### 3. Content Types API (`/api/content-types`)

#### Dynamic Type Registry
```python
# backend/app/api/content_types.py
@router.get("/content-types")
async def get_content_types():
    # Get actual types from database
    types_query = "SELECT DISTINCT type FROM items WHERE type IS NOT NULL"
    db_types = await conn.fetch(types_query)
    
    # Merge with predefined metadata
    return {
        "types": [
            {
                "name": type_name,
                "icon": TYPE_ICONS.get(type_name, "📄"),
                "color": TYPE_COLORS.get(type_name, "#666"),
                "description": TYPE_DESCRIPTIONS.get(type_name, ""),
                "count": get_type_count(type_name)
            }
            for type_name in all_types
        ]
    }
```

## 🎨 Frontend Type Display & Filtering

### 1. Dynamic Content Types Store

#### Frontend Store (`frontend/src/lib/stores/contentTypes.ts`)
```typescript
interface ContentType {
  name: string;
  icon: string; 
  color: string;
  description: string;
  count: number;
}

export const contentTypes = createContentTypesStore();
```

### 2. Timeline Page Filtering

#### Implementation (`frontend/src/routes/timeline/+page.svelte`)
```svelte
<!-- Dynamic filter buttons -->
{#each $contentTypes as type}
  <button 
    class="filter-btn {selectedType === type.name ? 'active' : ''}"
    style="--type-color: {type.color}"
    on:click={() => filterByType(type.name)}
  >
    {type.icon} {type.name} ({type.count})
  </button>
{/each}

<!-- Filter logic -->
<script>
  async function filterByType(typeName) {
    selectedType = typeName;
    const response = await fetch(`/api/timeline?type=${typeName}&limit=20`);
    items = await response.json();
  }
</script>
```

### 3. Search Page Type Filters

#### Search Implementation (`frontend/src/routes/search/+page.svelte`)
```svelte
<!-- Type filter dropdown -->
<select bind:value={selectedType} on:change={performSearch}>
  <option value="">All Types</option>
  {#each $contentTypes as type}
    <option value={type.name}>{type.icon} {type.name}</option>
  {/each}
</select>
```

### 4. Capture Page Type Selection

#### Capture Implementation (`frontend/src/routes/capture/+page.svelte`)
```svelte
<!-- Content type selector -->
<div class="type-selector">
  {#each $contentTypes as type}
    <button 
      class="type-option {selectedType === type.name ? 'selected' : ''}"
      on:click={() => selectedType = type.name}
    >
      <div class="type-icon">{type.icon}</div>
      <div class="type-name">{type.name}</div>
    </button>
  {/each}
</div>
```

## 🔧 Type Icons & Colors Registry

### Icon Mapping
```javascript
const TYPE_ICONS = {
  'document': '📄',
  'video': '🎥', 
  'article': '📰',
  'link': '🔗',
  'image': '🖼️',
  'tutorial': '🎓',
  'note': '📝',
  'auto': '🤖'
};
```

### Color Mapping  
```javascript
const TYPE_COLORS = {
  'document': '#3b82f6',  // Blue
  'video': '#ef4444',     // Red
  'article': '#10b981',   // Green  
  'link': '#6366f1',      // Indigo
  'image': '#f59e0b',     // Amber
  'tutorial': '#8b5cf6',  // Purple
  'note': '#06b6d4',      // Cyan
  'auto': '#6b7280'       // Gray
};
```

## 🐛 Common Issues & Solutions

### Issue 1: Type Mismatch Between Capture and Display
**Problem**: User selects 'video' but content appears as 'article'
**Root Cause**: AI override or URL-based hardcoded logic
**Solution**: Always respect user's explicit type selection

### Issue 2: Content Not Appearing in Type Filters  
**Problem**: Videos don't show in "Videos" filter
**Root Cause**: Hardcoded CASE statements in SQL ignoring database type column
**Solution**: Use `i.type as type` in all queries ✅ **FIXED**

### Issue 3: New Types Not Appearing in Frontend
**Problem**: Database has new types but frontend doesn't show them
**Root Cause**: Frontend using hardcoded type list instead of dynamic API
**Solution**: Always fetch types from `/api/content-types` ✅ **IMPLEMENTED**

## 🧪 Testing Content Type Flow

### Test Scenarios
1. **Manual Type Selection**: User picks 'video', content should be 'video'
2. **File Upload Type**: .pdf upload should become 'document'  
3. **AI Auto-Detection**: URL analysis should pick appropriate type
4. **Filter Consistency**: Timeline filter should show same types as database
5. **Search Integration**: Type filter in search should work correctly

### Validation Queries
```sql
-- Check type distribution
SELECT type, COUNT(*) FROM items GROUP BY type;

-- Find type mismatches  
SELECT id, title, type, url FROM items WHERE type != expected_type_from_url(url);

-- Verify filter consistency
SELECT DISTINCT type FROM items ORDER BY type;
```

## 🔄 Future Enhancements

### Planned Improvements
1. **Sub-type Support**: `video.youtube`, `document.pdf`, etc.
2. **Type History**: Track type changes and user corrections
3. **Smart Suggestions**: Learn from user type corrections
4. **Bulk Type Updates**: Change types for multiple items
5. **Type Analytics**: Usage patterns and type distribution metrics

### API Extensions
```python
# Future endpoint ideas
GET /api/content-types/hierarchy     # Nested type structure
POST /api/items/bulk-update-types    # Bulk type changes  
GET /api/analytics/type-distribution # Type usage analytics
```

---

**This map ensures that every content type decision is traceable and consistent across the entire PRSNL system.**