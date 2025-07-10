# 🏗️ PRSNL System Architecture Repository

## 🎯 Purpose

This repository serves as the **single source of truth** for building new features without breaking existing functionality. Every new feature should follow these established patterns to maintain system consistency.

## 🚨 **CRITICAL RULE**
**Before adding ANY new feature, consult this repository to understand:**
1. How to extend APIs properly
2. How to modify database schema safely  
3. How to integrate frontend components
4. How to maintain data consistency

---

## 📊 **API Design Patterns**

### Standard Endpoint Structure
```python
# Pattern: /api/{resource}[/{id}][/{action}]
GET    /api/items           # List items
GET    /api/items/{id}      # Get single item
POST   /api/items           # Create item
PUT    /api/items/{id}      # Update item
DELETE /api/items/{id}      # Delete item
POST   /api/items/{id}/process  # Custom action
```

### Response Format Standard
```python
# Success Response (200)
{
    "data": [...],           # Main payload
    "meta": {                # Metadata
        "total": 100,
        "page": 1,
        "limit": 20,
        "has_more": true
    },
    "status": "success"
}

# Error Response (400/500)
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {...}
    },
    "status": "error"
}
```

### Pagination Pattern
```python
# Query Parameters
?limit=20&offset=0&cursor=abc123

# Implementation Template
async def get_paginated_items(limit: int = 20, cursor: str = None):
    query = "SELECT * FROM items WHERE created_at > $1 ORDER BY created_at DESC LIMIT $2"
    items = await conn.fetch(query, cursor_date, limit + 1)
    
    has_more = len(items) > limit
    if has_more:
        items = items[:-1]
    
    return {
        "data": items,
        "meta": {
            "limit": limit,
            "has_more": has_more,
            "next_cursor": items[-1]["created_at"] if has_more else None
        }
    }
```

### Filtering Pattern
```python
# URL: /api/items?type=video&tags=ai,tech&created_after=2024-01-01

# Implementation Template
async def filter_items(
    type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    created_after: Optional[datetime] = None
):
    conditions = ["1=1"]  # Always true base condition
    params = []
    param_count = 1
    
    if type:
        conditions.append(f"type = ${param_count}")
        params.append(type)
        param_count += 1
    
    if tags:
        conditions.append(f"tags && ${param_count}")
        params.append(tags)
        param_count += 1
    
    if created_after:
        conditions.append(f"created_at > ${param_count}")
        params.append(created_after)
        param_count += 1
    
    query = f"SELECT * FROM items WHERE {' AND '.join(conditions)}"
    return await conn.fetch(query, *params)
```

---

## 🗄️ **Database Schema Patterns**

### Table Design Standards
```sql
-- Standard table template
CREATE TABLE new_feature_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core fields (REQUIRED)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Business fields
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL,
    
    -- Flexible data
    metadata JSONB DEFAULT '{}',
    
    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', title || ' ' || COALESCE(description, ''))
    ) STORED,
    
    -- Constraints
    CONSTRAINT valid_type CHECK (type IN ('type1', 'type2', 'type3'))
);

-- Standard indexes
CREATE INDEX idx_new_feature_created_at ON new_feature_items(created_at DESC);
CREATE INDEX idx_new_feature_type ON new_feature_items(type);
CREATE INDEX idx_new_feature_search ON new_feature_items USING gin(search_vector);
```

### Migration Pattern
```sql
-- migrations/add_new_feature.sql
BEGIN;

-- 1. Add new table
CREATE TABLE new_feature (...);

-- 2. Add new columns to existing tables (if needed)
ALTER TABLE items ADD COLUMN new_field TEXT;

-- 3. Update existing data (if needed)
UPDATE items SET new_field = 'default_value' WHERE new_field IS NULL;

-- 4. Add constraints (after data update)
ALTER TABLE items ALTER COLUMN new_field SET NOT NULL;

-- 5. Create indexes
CREATE INDEX idx_items_new_field ON items(new_field);

COMMIT;
```

### Relationship Patterns
```sql
-- One-to-Many (items → tags)
CREATE TABLE item_tags (
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (item_id, tag_id)
);

-- Many-to-Many with metadata
CREATE TABLE item_collections (
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    position INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (item_id, collection_id)
);
```

---

## 🎨 **Frontend Integration Patterns**

### API Client Pattern
```typescript
// lib/api/client.ts
class APIClient {
    async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
        const url = new URL(`${this.baseURL}${endpoint}`);
        if (params) {
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined) url.searchParams.set(key, value);
            });
        }
        
        const response = await fetch(url.toString());
        if (!response.ok) throw new APIError(response);
        return response.json();
    }
}

// Usage pattern for new features
export const newFeatureAPI = {
    list: (filters?: NewFeatureFilters) => 
        client.get<PaginatedResponse<NewFeature>>('/api/new-feature', filters),
    
    get: (id: string) => 
        client.get<NewFeature>(`/api/new-feature/${id}`),
    
    create: (data: CreateNewFeatureRequest) => 
        client.post<NewFeature>('/api/new-feature', data),
    
    update: (id: string, data: UpdateNewFeatureRequest) => 
        client.put<NewFeature>(`/api/new-feature/${id}`, data)
};
```

### Store Pattern (Svelte)
```typescript
// stores/newFeature.ts
interface NewFeatureStore {
    items: NewFeature[];
    loading: boolean;
    error: string | null;
    filters: NewFeatureFilters;
}

function createNewFeatureStore() {
    const { subscribe, set, update } = writable<NewFeatureStore>({
        items: [],
        loading: false,
        error: null,
        filters: {}
    });

    return {
        subscribe,
        
        async load(filters?: NewFeatureFilters) {
            update(s => ({ ...s, loading: true, error: null }));
            
            try {
                const response = await newFeatureAPI.list(filters);
                update(s => ({ 
                    ...s, 
                    items: response.data, 
                    loading: false,
                    filters: filters || {}
                }));
            } catch (error) {
                update(s => ({ ...s, error: error.message, loading: false }));
            }
        },
        
        async create(data: CreateNewFeatureRequest) {
            const newItem = await newFeatureAPI.create(data);
            update(s => ({ ...s, items: [newItem, ...s.items] }));
            return newItem;
        }
    };
}

export const newFeatureStore = createNewFeatureStore();
```

### Component Pattern
```svelte
<!-- components/NewFeatureList.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    import { newFeatureStore } from '$lib/stores/newFeature';
    
    export let filters: NewFeatureFilters = {};
    
    onMount(() => {
        newFeatureStore.load(filters);
    });
    
    $: if (filters) {
        newFeatureStore.load(filters);
    }
</script>

{#if $newFeatureStore.loading}
    <div class="loading">Loading...</div>
{:else if $newFeatureStore.error}
    <div class="error">{$newFeatureStore.error}</div>
{:else}
    <div class="items-grid">
        {#each $newFeatureStore.items as item}
            <NewFeatureCard {item} />
        {/each}
    </div>
{/if}
```

---

## 🔄 **Data Flow Standards**

### Content Processing Pipeline
```python
# Standard processing flow for new content types
async def process_new_content(data: NewContentInput) -> ProcessedContent:
    # 1. Validation
    validated_data = validate_input(data)
    
    # 2. Type detection/classification
    content_type = detect_content_type(validated_data)
    
    # 3. Content extraction
    extracted_content = extract_content(validated_data, content_type)
    
    # 4. AI processing (if enabled)
    ai_analysis = None
    if validated_data.enable_ai:
        ai_analysis = await ai_service.analyze(extracted_content)
    
    # 5. Storage
    stored_item = await store_content({
        **extracted_content,
        "type": content_type,
        "ai_analysis": ai_analysis,
        "metadata": build_metadata(validated_data, ai_analysis)
    })
    
    # 6. Indexing
    await search_service.index_item(stored_item)
    
    # 7. Notifications
    await notification_service.notify_content_processed(stored_item)
    
    return stored_item
```

### Event System Pattern
```python
# Event-driven updates
@event_handler("content.created")
async def on_content_created(event: ContentCreatedEvent):
    await search_service.index_item(event.item)
    await analytics_service.track_creation(event.item)

@event_handler("content.updated") 
async def on_content_updated(event: ContentUpdatedEvent):
    await search_service.reindex_item(event.item)
    await cache_service.invalidate_item(event.item.id)
```

---

## 🧪 **Testing Patterns**

### API Testing Template
```python
# tests/test_new_feature_api.py
class TestNewFeatureAPI:
    async def test_create_new_feature(self, client, db):
        # Arrange
        data = {"title": "Test", "type": "test_type"}
        
        # Act
        response = await client.post("/api/new-feature", json=data)
        
        # Assert
        assert response.status_code == 201
        assert response.json()["title"] == "Test"
        
        # Verify database
        db_item = await db.fetchrow("SELECT * FROM new_feature WHERE title = $1", "Test")
        assert db_item is not None
    
    async def test_list_with_filters(self, client, db):
        # Setup test data
        await create_test_items(db, count=5, type="test_type")
        
        # Test filtering
        response = await client.get("/api/new-feature?type=test_type")
        
        assert response.status_code == 200
        assert len(response.json()["data"]) == 5
```

### Frontend Testing Template
```typescript
// tests/NewFeature.test.ts
import { render, screen, fireEvent } from '@testing-library/svelte';
import NewFeatureList from '$lib/components/NewFeatureList.svelte';

describe('NewFeatureList', () => {
    it('loads and displays items', async () => {
        // Mock API
        vi.mocked(newFeatureAPI.list).mockResolvedValue({
            data: [{ id: '1', title: 'Test Item' }],
            meta: { total: 1 }
        });
        
        render(NewFeatureList);
        
        // Wait for loading to complete
        await waitFor(() => {
            expect(screen.getByText('Test Item')).toBeInTheDocument();
        });
    });
});
```

---

## 📋 **Feature Addition Checklist**

### Before Starting New Feature:
- [ ] Review existing similar features in this repository
- [ ] Check database schema for extension points
- [ ] Identify API endpoints that need modification
- [ ] Plan frontend integration points

### During Development:
- [ ] Follow API response format standards
- [ ] Use standard database patterns (UUID, timestamps, constraints)
- [ ] Implement consistent error handling
- [ ] Add proper validation and type checking
- [ ] Follow frontend store and component patterns

### Before Deployment:
- [ ] Add database migration scripts
- [ ] Update API documentation
- [ ] Add comprehensive tests
- [ ] Verify no breaking changes to existing features
- [ ] Update this repository with new patterns (if any)

---

## 🚀 **Common Feature Extensions**

### Adding New Content Type
1. **Database**: Add to `type` enum constraint
2. **Backend**: Update type validation and processing logic
3. **Frontend**: Add to content type store and UI components
4. **Testing**: Add test cases for new type flow

### Adding New API Endpoint
1. **Backend**: Follow standard endpoint pattern
2. **Frontend**: Add to API client
3. **Types**: Update TypeScript interfaces
4. **Documentation**: Update API contracts

### Adding New Filter
1. **Database**: Ensure proper indexing
2. **Backend**: Add to filter parameters
3. **Frontend**: Add to filter UI components
4. **Testing**: Test filter combinations

---

**This repository ensures every new feature builds ON the system instead of breaking it.**