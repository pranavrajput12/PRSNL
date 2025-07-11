# 🏗️ PRSNL System Architecture Repository

## 🎯 Purpose

This repository serves as the **single source of truth** for building new features without breaking existing functionality. Every new feature should follow these established patterns to maintain system consistency.

## 🚨 **CRITICAL RULE**
**Before adding ANY new feature, consult this repository to understand:**
1. How to extend APIs properly
2. How to modify database schema safely  
3. How to integrate frontend components
4. How to maintain data consistency

## 🆕 **Recent Major Upgrade (2025-07-11)**
**Advanced Integrations & Architecture v2.4** - Complete system enhancement:

### **Frontend Modernization**
- **Svelte**: 4.2.20 → 5.35.6 (Runes system replaces stores for local state)
- **SvelteKit**: 2.22.2 → 2.22.5 
- **Vite**: 6.0.2 → 7.0.4
- **Node.js**: >=20.19 || >=22.12 || >=24
- **Frontend Port**: 3003 → 3004 (development server)
- **Security**: All vulnerabilities resolved, dependencies updated

### **New Architectural Components**
- **Content Fingerprinting**: SHA-256 based duplicate detection and change tracking
- **Normalized Embeddings**: Separate embeddings table with optimized vector storage
- **Enhanced Search**: Multi-modal search with semantic, keyword, and hybrid modes
- **Sentry Integration**: Complete error monitoring and performance tracking
- **Svelte-Query**: Advanced data fetching with caching and synchronization

**Migration Impact**: All frontend patterns now support both traditional stores (for shared state) and Svelte 5 runes (for component-local state). New backend patterns include fingerprint-based operations and normalized embedding workflows.

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

### **NEW: Enhanced Search API Pattern**
```python
# Multi-modal search endpoint with deduplication
@router.post("/search/")
async def enhanced_search(request: SearchRequest):
    """Semantic, keyword, or hybrid search with automatic deduplication."""
    
    # Choose search method
    if request.search_type == "semantic":
        results = await enhanced_search_service.semantic_search(
            query=request.query,
            limit=request.limit,
            threshold=request.threshold
        )
    elif request.search_type == "keyword":
        results = await enhanced_search_service.keyword_search(
            query=request.query,
            limit=request.limit
        )
    else:  # hybrid
        results = await enhanced_search_service.hybrid_search(
            query=request.query,
            limit=request.limit
        )
    
    # Apply deduplication based on content fingerprints
    if not request.include_duplicates:
        results = await enhanced_search_service.search_with_deduplication(
            query=request.query,
            search_type=request.search_type,
            limit=request.limit
        )
    
    return results

# Duplicate detection endpoint
@router.post("/search/duplicates")
async def find_duplicates(request: DuplicateSearchRequest):
    """Find exact duplicates using content fingerprint."""
    duplicates = await enhanced_search_service.find_duplicates_by_fingerprint(
        content=request.content,
        exclude_id=request.exclude_id
    )
    
    return {
        "duplicates": duplicates,
        "total": len(duplicates),
        "content_fingerprint": calculate_content_fingerprint(request.content)
    }
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

### **NEW: Content Fingerprinting Pattern**
```sql
-- Add content fingerprinting to any table with content
ALTER TABLE items ADD COLUMN content_fingerprint VARCHAR(64);
CREATE INDEX idx_items_content_fingerprint ON items(content_fingerprint);

-- Usage in application
from app.utils.fingerprint import calculate_content_fingerprint

# Generate fingerprint
fingerprint = calculate_content_fingerprint(content)

# Check for duplicates (O(1) lookup)
existing = await conn.fetchrow(
    "SELECT id FROM items WHERE content_fingerprint = $1", 
    fingerprint
)

# Detect content changes
if old_fingerprint != new_fingerprint:
    # Content has changed, reprocess
    await process_content(content)
```

### **NEW: Normalized Embedding Pattern**
```sql
-- Create separate embeddings table for optimized vector storage
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-ada-002',
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1',
    vector vector(1536) NOT NULL,
    vector_norm FLOAT, -- Pre-calculated for faster similarity
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add foreign key to main table
ALTER TABLE items ADD COLUMN embed_vector_id UUID REFERENCES embeddings(id);
CREATE INDEX idx_items_embed_vector_id ON items(embed_vector_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (vector vector_cosine_ops);

-- Usage pattern
from app.services.embedding_manager import embedding_manager

# Create embedding
result = await embedding_manager.create_embedding(
    item_id=str(item.id),
    content=f"{item.title} {item.content}",
    update_item=True  # Updates item.embed_vector_id
)

# Search similar items (faster than direct vector search)
similar = await embedding_manager.search_similar(
    query_embedding=query_vector,
    limit=20,
    threshold=0.7
)
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

### Store Pattern (Svelte 5 with Runes)
```typescript
// stores/newFeature.svelte.ts
import { writable } from 'svelte/store';

interface NewFeatureStore {
    items: NewFeature[];
    loading: boolean;
    error: string | null;
    filters: NewFeatureFilters;
}

// Option 1: Traditional Store (for shared state)
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

// Option 2: Svelte 5 Runes (for component-local state)
export class NewFeatureState {
    items = $state<NewFeature[]>([]);
    loading = $state(false);
    error = $state<string | null>(null);
    filters = $state<NewFeatureFilters>({});

    async load(filters?: NewFeatureFilters) {
        this.loading = true;
        this.error = null;
        
        try {
            const response = await newFeatureAPI.list(filters);
            this.items = response.data;
            this.filters = filters || {};
        } catch (error) {
            this.error = error.message;
        } finally {
            this.loading = false;
        }
    }

    async create(data: CreateNewFeatureRequest) {
        const newItem = await newFeatureAPI.create(data);
        this.items = [newItem, ...this.items];
        return newItem;
    }
}
```

### Component Pattern (Svelte 5)
```svelte
<!-- components/NewFeatureList.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    import { NewFeatureState } from '$lib/stores/newFeature.svelte';
    import NewFeatureCard from './NewFeatureCard.svelte';
    
    interface Props {
        filters?: NewFeatureFilters;
    }
    
    let { filters = {} }: Props = $props();
    
    // Option 1: Using runes-based state class
    const state = new NewFeatureState();
    
    onMount(() => {
        state.load(filters);
    });
    
    // Svelte 5 effect for reactive filters
    $effect(() => {
        if (filters) {
            state.load(filters);
        }
    });

    // Alternative: Using traditional store
    // import { newFeatureStore } from '$lib/stores/newFeature';
    // onMount(() => newFeatureStore.load(filters));
    // $: if (filters) newFeatureStore.load(filters);
</script>

{#if state.loading}
    <div class="loading">Loading...</div>
{:else if state.error}
    <div class="error">{state.error}</div>
{:else}
    <div class="items-grid">
        {#each state.items as item (item.id)}
            <NewFeatureCard {item} />
        {/each}
    </div>
{/if}

<style>
    .items-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1rem;
    }
    
    .loading, .error {
        text-align: center;
        padding: 2rem;
    }
    
    .error {
        color: var(--color-error);
        background: var(--color-error-bg);
        border-radius: 4px;
    }
</style>
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
    
    # 4. AI processing (if enabled) - with automatic validation
    ai_analysis = None
    if validated_data.enable_ai:
        # Uses Guardrails-AI validated analysis
        ai_analysis = await unified_ai_service.analyze_content(extracted_content)
        
    # 4b. Transcription (if audio/video)
    transcription = None
    if content_type in ["audio", "video"]:
        # Uses whisper.cpp for all transcription
        from app.services.whisper_cpp_transcription import whisper_cpp_service
        transcription_result = await whisper_cpp_service.transcribe_audio(
            audio_path=validated_data.file_path,
            model_name="base"  # Or select based on requirements
        )
        transcription = transcription_result.get("text") if transcription_result else None
    
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

### AI Processing Standards
```python
# Standard AI integration flow with validation
async def ai_process_content(content: str, analysis_type: str) -> Dict[str, Any]:
    # 1. Prepare request
    request = {
        "content": content,
        "type": analysis_type,
        "enable_validation": True  # Always validate AI outputs
    }
    
    # 2. Get AI analysis
    raw_response = await unified_ai_service.analyze_content(content)
    
    # 3. Automatic validation via Guardrails-AI
    # (This happens inside unified_ai_service)
    
    # 4. Extract validated results
    return {
        "title": raw_response.get("title"),
        "summary": raw_response.get("summary"),
        "tags": raw_response.get("tags", []),
        "category": raw_response.get("category"),
        "sentiment": raw_response.get("sentiment"),
        "key_points": raw_response.get("key_points", []),
        "confidence": raw_response.get("confidence", 0.0)
    }
```

### Transcription Standards
```python
# Standard transcription flow (whisper.cpp only)
async def transcribe_content(audio_path: str, privacy_sensitive: bool = False) -> Dict[str, Any]:
    # Use whisper.cpp-based transcription service
    from app.services.whisper_cpp_transcription import whisper_cpp_service
    
    # Select model based on file size and requirements
    model = "base"  # Default for balance
    if privacy_sensitive:
        model = "small"  # Better accuracy for sensitive content
    
    result = await whisper_cpp_service.transcribe_audio(
        audio_path=audio_path,
        model_name=model,
        language="en",  # Auto-detect in future
        word_timestamps=True
    )
    
    return {
        "text": result.get("text", ""),
        "confidence": result.get("confidence", 0.0),
        "duration": result.get("duration", 0),
        "words": result.get("words", []),
        "service": "whisper.cpp"
    }
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