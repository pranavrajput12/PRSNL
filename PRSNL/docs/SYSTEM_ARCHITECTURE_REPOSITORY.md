# 🏗️ PRSNL System Architecture Repository

## 🎯 Purpose

This repository serves as the **single source of truth** for building new features without breaking existing functionality. Every new feature should follow these established patterns to maintain system consistency.

## 🚨 **CRITICAL RULE**
**Before adding ANY new feature, consult this repository to understand:**
1. How to extend APIs properly
2. How to modify database schema safely  
3. How to integrate frontend components
4. How to maintain data consistency

## 🆕 **Recent Major Upgrades**

### **Knowledge Graph Analytics v2.7 (2025-08-01)**
**Advanced AI-Powered Knowledge Graph System** - Complete semantic clustering, gap analysis, and intelligent insights:

#### **Knowledge Graph Analytics Architecture**
- **APIs**: Complete `/api/unified-knowledge-graph/*` - 8+ endpoints for graph visualization, analysis, clustering
- **Semantic Clustering**: 3 algorithms (semantic, structural, hybrid) for intelligent entity grouping  
- **Gap Analysis**: AI-powered knowledge domain analysis with completeness scoring
- **Learning Paths**: Graph traversal algorithms for knowledge connection discovery
- **Relationship Suggestions**: AI-powered recommendations for new entity relationships
- **Real-time Visualization**: D3.js-compatible graph data with advanced filtering
- **Statistics Dashboard**: Comprehensive analytics with 140+ entities, 176+ relationships
- **Performance**: Optimized with materialized views, composite indexes, and JSONB storage

#### **Knowledge Graph Integration Pattern**
```python
# Knowledge graph API integration pattern
from app.api.unified_knowledge_graph import router as kg_router

# Get full knowledge graph for visualization
graph_data = await fetch('/api/unified-knowledge-graph/visual/full?min_confidence=0.7&limit=200')

# Perform semantic clustering
clusters = await fetch('/api/unified-knowledge-graph/clustering/semantic', {
    method: 'POST',
    body: JSON.stringify({
        clustering_algorithm: 'hybrid',
        max_clusters: 8,
        min_cluster_size: 3
    })
})

# Analyze knowledge gaps
gap_analysis = await fetch('/api/unified-knowledge-graph/analysis/gaps', {
    method: 'POST', 
    body: JSON.stringify({
        analysis_depth: 'comprehensive',
        min_severity: 'medium',
        include_suggestions: true
    })
})
```

### **Auto-Processing System v1.0 (2025-08-02)**
**Complete AI Processing Pipeline** - Automatic content intelligence with knowledge graph integration:

#### **Auto-Processing Architecture**
- **Service**: `AutoProcessingService` - Centralized AI processing coordinator
- **Pipeline**: 5-step process (AI Analysis → Categorization → Summarization → **Entity Extraction** → Embeddings)
- **API**: `/api/auto-processing/*` - 6 REST endpoints for processing management
- **Queue**: Background processing with concurrency controls (up to 10 items)
- **Integration**: Automatic trigger on content capture with `enable_summarization=true`
- **Storage**: Processing metadata in `items.metadata.auto_processing` JSONB field
- **Knowledge Graph**: Automatic entity extraction and relationship creation for cross-feature integration

#### **Processing Pipeline Pattern**
```python
# Auto-processing integration pattern
background_tasks.add_task(
    auto_processing_service.process_captured_item,
    item_id, content, url, title, enable_ai_processing
)

# Processing results stored in items.metadata:
{
  "auto_processing": {
    "steps_completed": ["ai_analysis", "categorization", "summarization", "entity_extraction", "embeddings"],
    "success_rate": 1.0,
    "errors": [],
    "entity_extraction": {
      "entities_created": 3,
      "relationships_created": 2,
      "extraction_method": "ai_extracted"
    }
  }
}
```

### **Entity Extraction System v1.0 (2025-08-02)**
**Knowledge Graph Integration for Cross-Feature Intelligence**:

#### **Entity Extraction Architecture**
- **Service**: `EntityExtractionService` - AI-powered entity and relationship extraction
- **Database**: 6 specialized tables for unified entity storage and relationships
- **API**: `/api/entity-extraction/*` - 5 REST endpoints for entity management
- **Integration**: Seamlessly integrated with Auto-Processing pipeline (Step 4 of 5)
- **Content Types**: Supports conversation, video, code, articles, notes, and timeline events
- **AI Models**: Uses Azure OpenAI for intelligent entity recognition and relationship inference

#### **Entity Extraction Pattern**
```python
# Entity extraction service integration
from app.services.entity_extraction_service import entity_extraction_service

# Extract entities from content
entity_results = await entity_extraction_service.extract_entities_from_content(
    content_id=item_id,
    content_type='article',  # conversation, video, code, etc.
    content_text=content[:5000],
    metadata={"processing_context": "auto_processing"}
)

# Results include created entities and relationships
{
  "success": true,
  "entities_created": [
    {"entity_id": "uuid", "name": "React 18", "entity_type": "knowledge_concept"},
    {"entity_id": "uuid", "name": "useTransition", "entity_type": "code_function"}
  ],
  "relationships_created": [
    {"relationship_id": "uuid", "relationship_type": "implements", "confidence": 0.8}
  ]
}
```

#### **Database Schema for Knowledge Graph**
- **unified_entities**: Central entity table for all content types (140+ entities)
- **unified_relationships**: Cross-feature relationships with confidence scoring (176+ relationships)
- **conversation_turns**: Enhanced conversation analysis with entity linking
- **video_segments**: Time-based video segments with AI analysis
- **code_entities**: Code structure entities (functions, classes, modules)
- **timeline_events**: Timeline events with enhanced context and relationships
- **entity_statistics**: Materialized view for performance analytics
- **relationship_statistics**: Materialized view for relationship analytics

### **Advanced Integrations & Architecture v2.4 (2025-07-11)**
**Complete system enhancement:**

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

## 🏗️ **Infrastructure Configuration (Updated 2025-07-12)**

### Current Setup
- **Database**: Local PostgreSQL on port 5432 (user: `pronav`)
- **Backend**: Running locally with `uvicorn` on port 8000
- **Frontend**: Development server on port 3004
- **Redis**: Running in Docker container on port 6379
- **Container Runtime**: Rancher Desktop (NOT Docker Desktop)

### Services Status
- **Docker Containers**: Only Redis runs in Docker now
- **Backend**: Runs locally for better development experience
- **Database**: Migrated from Docker to local PostgreSQL
- **Frontend**: Always runs locally with `npm run dev`

### Important Changes
- Docker database has been **permanently disabled**
- All 23 items successfully migrated to local PostgreSQL
- Backend `.env` updated to use local database
- `docker-compose.yml` updated with database service commented out

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

### **NEW: Knowledge Graph API Pattern**
```python
# Knowledge graph visualization endpoints
@router.get("/unified-knowledge-graph/visual/full", response_model=UnifiedGraphResponse)
async def get_unified_visual_graph(
    entity_type: Optional[str] = Query(None),
    relationship_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=10, le=500),
    min_confidence: float = Query(0.5, ge=0.0, le=1.0)
):
    """Get complete knowledge graph for D3.js visualization with filtering."""
    
    # Build dynamic query with filters
    entity_query = """
        SELECT ue.id, ue.name as title, ue.entity_type as type,
               ue.description as summary, ue.confidence_score as confidence,
               i.content_type, i.title as source_title
        FROM unified_entities ue
        LEFT JOIN items i ON ue.source_content_id = i.id
        WHERE ue.confidence_score >= $1
    """
    
    params = [min_confidence]
    if entity_type:
        entity_query += f" AND ue.entity_type = ${len(params) + 1}"
        params.append(entity_type)
    
    # Get entities and relationships
    entities = await conn.fetch(entity_query + " LIMIT $" + str(len(params) + 1), *params, limit)
    relationships = await get_relationships_for_entities([e['id'] for e in entities])
    
    return UnifiedGraphResponse(
        nodes=[UnifiedGraphNode(**entity) for entity in entities],
        edges=[UnifiedGraphEdge(**rel) for rel in relationships],
        metadata={"total_nodes": len(entities), "total_edges": len(relationships)}
    )

# Semantic clustering endpoint
@router.post("/unified-knowledge-graph/clustering/semantic")
async def perform_semantic_clustering(request: SemanticClusteringRequest):
    """Perform semantic clustering using multiple algorithms."""
    
    # Select algorithm
    if request.clustering_algorithm == "semantic":
        clusters = await _semantic_clustering(entities, relationships, request)
    elif request.clustering_algorithm == "structural":
        clusters = await _structural_clustering(entities, relationships, request)
    else:  # hybrid
        clusters = await _hybrid_clustering(entities, relationships, request)
    
    return SemanticClusteringResponse(
        clusters=clusters,
        total_entities_clustered=sum(len(c.entities) for c in clusters),
        clustering_metadata={
            "algorithm": request.clustering_algorithm,
            "total_entities_processed": len(entities)
        }
    )

# Knowledge gap analysis endpoint
@router.post("/unified-knowledge-graph/analysis/gaps")
async def analyze_knowledge_gaps(request: KnowledgeGapAnalysisRequest):
    """Comprehensive knowledge gap analysis with domain scoring."""
    
    gaps, domains, completeness = await _analyze_knowledge_gaps(
        entities, relationships, request
    )
    
    return KnowledgeGapAnalysisResponse(
        gaps=gaps,
        domains=domains,
        overall_completeness=completeness,
        recommendations=_generate_gap_recommendations(gaps, domains, completeness)
    )

# Learning path discovery endpoint
@router.post("/unified-knowledge-graph/paths/discover")
async def discover_knowledge_paths(request: KnowledgePathRequest):
    """Find learning paths using graph traversal algorithms."""
    
    # Build adjacency graph for pathfinding
    graph = await build_graph_for_pathfinding(relationships, request.min_confidence)
    
    # Find paths using BFS with confidence weighting
    paths = await _find_knowledge_paths(
        graph, request.start_entity_id, request.end_entity_id, request.max_depth
    )
    
    return KnowledgePathResponse(
        paths=sorted(paths, key=lambda p: p.total_confidence, reverse=True)[:5],
        total_paths=len(paths),
        search_metadata={"algorithm": "bfs_confidence_weighted"}
    )
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

### 🚨 **Database Configuration (Updated 2025-07-12)**
- **Database**: Local PostgreSQL (NOT Docker)
- **Connection**: `postgresql://pronav@localhost:5432/prsnl`
- **User**: `pronav` (local system user)
- **Port**: 5432
- **Important**: Docker database has been deprecated and all data migrated to local PostgreSQL

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

### **NEW: Knowledge Graph Schema Pattern**
```sql
-- Central entity table for cross-feature integration
CREATE TABLE unified_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL CHECK (entity_type IN (
        'conversation_turn', 'video_segment', 'code_function', 'code_class', 
        'code_module', 'timeline_event', 'file_attachment', 'image_entity', 
        'audio_entity', 'text_entity', 'knowledge_concept'
    )),
    source_content_id UUID REFERENCES items(id) ON DELETE CASCADE,
    parent_entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    start_position INTEGER, -- For segments (video time, text position, line numbers)
    end_position INTEGER,
    confidence_score FLOAT DEFAULT 1.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    extraction_method TEXT DEFAULT 'manual', -- manual, ai_extracted, user_defined
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Cross-feature relationships with semantic types
CREATE TABLE unified_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES unified_entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN (
        -- Temporal relationships
        'precedes', 'follows', 'concurrent', 'enables', 'depends_on',
        -- Content relationships  
        'discusses', 'implements', 'references', 'explains', 'demonstrates',
        -- Structural relationships
        'contains', 'part_of', 'similar_to', 'related_to', 'opposite_of',
        -- Cross-modal relationships
        'visualizes', 'describes', 'transcribes', 'summarizes', 'extends',
        -- Learning relationships
        'prerequisite', 'builds_on', 'reinforces', 'applies', 'teaches'
    )),
    confidence_score FLOAT DEFAULT 1.0 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    strength FLOAT DEFAULT 1.0,
    bidirectional BOOLEAN DEFAULT false,
    context TEXT, -- Why this relationship exists
    extraction_method TEXT DEFAULT 'manual',
    evidence JSONB DEFAULT '{}', -- Supporting evidence
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (source_entity_id, target_entity_id, relationship_type)
);

-- Performance optimization with materialized views
CREATE MATERIALIZED VIEW entity_statistics AS
SELECT 
    entity_type,
    COUNT(*) as total_entities,
    AVG(confidence_score) as avg_confidence,
    COUNT(DISTINCT source_content_id) as unique_sources,
    MIN(created_at) as first_created,
    MAX(created_at) as last_created
FROM unified_entities 
GROUP BY entity_type;

CREATE MATERIALIZED VIEW relationship_statistics AS
SELECT 
    relationship_type,
    COUNT(*) as total_relationships,
    AVG(confidence_score) as avg_confidence,
    AVG(strength) as avg_strength,
    COUNT(DISTINCT source_entity_id) as unique_sources,
    COUNT(DISTINCT target_entity_id) as unique_targets
FROM unified_relationships 
GROUP BY relationship_type;

-- Composite indexes for complex graph queries
CREATE INDEX idx_unified_entities_composite ON unified_entities(entity_type, source_content_id, created_at);
CREATE INDEX idx_unified_relationships_composite ON unified_relationships(relationship_type, confidence_score, created_at);

-- Full-text search indexes for semantic operations
CREATE INDEX idx_unified_entities_name_fts ON unified_entities USING gin(to_tsvector('english', name));
CREATE INDEX idx_unified_entities_description_fts ON unified_entities USING gin(to_tsvector('english', description));

-- PostgreSQL functions for graph operations
CREATE OR REPLACE FUNCTION create_entity_from_content(
    p_entity_type text,
    p_source_content_id uuid,
    p_name text,
    p_description text DEFAULT NULL,
    p_metadata jsonb DEFAULT '{}'
) RETURNS uuid AS $$
DECLARE
    new_entity_id uuid;
BEGIN
    INSERT INTO unified_entities (entity_type, source_content_id, name, description, metadata, extraction_method)
    VALUES (p_entity_type, p_source_content_id, p_name, p_description, p_metadata, 'ai_extracted')
    RETURNING id INTO new_entity_id;
    
    RETURN new_entity_id;
END;
$$ LANGUAGE plpgsql;

-- Automatic relationship validation and creation
CREATE OR REPLACE FUNCTION create_relationship(
    p_source_entity_id uuid,
    p_target_entity_id uuid,
    p_relationship_type text,
    p_confidence_score float DEFAULT 1.0,
    p_context text DEFAULT NULL,
    p_bidirectional boolean DEFAULT false
) RETURNS uuid AS $$
DECLARE
    new_relationship_id uuid;
BEGIN
    -- Prevent self-relationships
    IF p_source_entity_id = p_target_entity_id THEN
        RAISE EXCEPTION 'Cannot create relationship between entity and itself';
    END IF;
    
    INSERT INTO unified_relationships (
        source_entity_id, target_entity_id, relationship_type, 
        confidence_score, context, bidirectional, extraction_method
    )
    VALUES (
        p_source_entity_id, p_target_entity_id, p_relationship_type,
        p_confidence_score, p_context, p_bidirectional, 'ai_inferred'
    )
    RETURNING id INTO new_relationship_id;
    
    -- Create reverse relationship if bidirectional
    IF p_bidirectional THEN
        INSERT INTO unified_relationships (
            source_entity_id, target_entity_id, relationship_type,
            confidence_score, context, bidirectional, extraction_method
        )
        VALUES (
            p_target_entity_id, p_source_entity_id, p_relationship_type,
            p_confidence_score, p_context, false, 'ai_inferred'
        );
    END IF;
    
    RETURN new_relationship_id;
END;
$$ LANGUAGE plpgsql;
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

### **NEW: Knowledge Graph Component Pattern (Svelte 5)**
```svelte
<!-- components/KnowledgeGraphVisualization.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    import { KnowledgeGraphState } from '$lib/stores/knowledgeGraph.svelte';
    import { knowledgeGraphAPI } from '$lib/api/knowledgeGraph';
    import * as d3 from 'd3';
    
    interface Props {
        itemId?: string;
        entityType?: string;
        showClustering?: boolean;
        analyticsMode?: boolean;
    }
    
    let { itemId, entityType, showClustering = false, analyticsMode = false }: Props = $props();
    
    // Knowledge graph state management
    const graphState = new KnowledgeGraphState();
    
    let svgElement: SVGElement;
    let simulation: d3.Simulation<any, any>;
    
    onMount(async () => {
        await loadGraphData();
        initializeVisualization();
    });
    
    // Reactive graph loading based on props
    $effect(async () => {
        if (itemId || entityType) {
            await loadGraphData();
            updateVisualization();
        }
    });

    // Load graph data based on context
    async function loadGraphData() {
        try {
            if (analyticsMode) {
                // Load analytics dashboard data
                const [graphData, stats, clusters, gaps] = await Promise.all([
                    knowledgeGraphAPI.getFullGraph({ entityType, minConfidence: 0.6 }),
                    knowledgeGraphAPI.getStats(),
                    showClustering ? knowledgeGraphAPI.performClustering({ 
                        algorithm: 'hybrid', maxClusters: 8 
                    }) : null,
                    knowledgeGraphAPI.analyzeGaps({ analysisDepth: 'standard' })
                ]);
                
                graphState.setAnalyticsData(graphData, stats, clusters, gaps);
            } else if (itemId) {
                // Load item-centered graph
                const graphData = await knowledgeGraphAPI.getItemGraph(itemId, { depth: 2 });
                graphState.setGraphData(graphData);
            } else {
                // Load filtered full graph
                const graphData = await knowledgeGraphAPI.getFullGraph({ 
                    entityType, 
                    limit: 150,
                    minConfidence: 0.5 
                });
                graphState.setGraphData(graphData);
            }
        } catch (error) {
            graphState.setError(error.message);
        }
    }

    // D3.js visualization setup
    function initializeVisualization() {
        if (!svgElement || !graphState.nodes.length) return;
        
        const svg = d3.select(svgElement);
        const width = 800;
        const height = 600;
        
        // Create force simulation
        simulation = d3.forceSimulation(graphState.nodes)
            .force('link', d3.forceLink(graphState.edges).id(d => d.id).strength(0.5))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collide', d3.forceCollide().radius(30));
        
        // Create links
        const link = svg.append('g')
            .selectAll('line')
            .data(graphState.edges)
            .enter().append('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => Math.sqrt(d.strength * 3));
        
        // Create nodes
        const node = svg.append('g')
            .selectAll('circle')
            .data(graphState.nodes)
            .enter().append('circle')
            .attr('r', d => 5 + d.confidence * 10)
            .attr('fill', d => getNodeColor(d.type))
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));
        
        // Add labels
        const label = svg.append('g')
            .selectAll('text')
            .data(graphState.nodes)
            .enter().append('text')
            .text(d => d.title)
            .attr('font-size', 10)
            .attr('dx', 15)
            .attr('dy', 4);
        
        // Update positions on simulation tick
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });
        
        // Handle clustering visualization
        if (showClustering && graphState.clusters.length) {
            highlightClusters();
        }
    }
    
    // Clustering visualization
    function highlightClusters() {
        const svg = d3.select(svgElement);
        
        graphState.clusters.forEach((cluster, i) => {
            const clusterNodes = cluster.entities.map(e => e.id);
            
            svg.selectAll('circle')
                .filter(d => clusterNodes.includes(d.id))
                .attr('stroke', d3.schemeCategory10[i % 10])
                .attr('stroke-width', 3);
        });
    }
    
    // Node color mapping
    function getNodeColor(entityType: string): string {
        const colorMap = {
            'knowledge_concept': '#ff6b6b',
            'text_entity': '#4ecdc4',
            'code_function': '#45b7d1',
            'video_segment': '#96ceb4',
            'conversation_turn': '#ffeaa7'
        };
        return colorMap[entityType] || '#74b9ff';
    }
    
    // D3 drag handlers
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    
    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
</script>

<div class="knowledge-graph-container">
    {#if graphState.loading}
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading knowledge graph...</p>
        </div>
    {:else if graphState.error}
        <div class="error">
            <p>Error loading graph: {graphState.error}</p>
            <button onclick={() => loadGraphData()}>Retry</button>
        </div>
    {:else}
        <div class="graph-controls">
            <div class="stats">
                <span>{graphState.nodes.length} entities</span>
                <span>{graphState.edges.length} relationships</span>
                {#if graphState.clusters.length}
                    <span>{graphState.clusters.length} clusters</span>
                {/if}
            </div>
            
            {#if analyticsMode}
                <div class="analytics-panel">
                    <h3>Knowledge Analytics</h3>
                    <div class="metric">
                        <label>Completeness Score:</label>
                        <span class="score">{(graphState.analytics?.overallCompleteness * 100).toFixed(1)}%</span>
                    </div>
                    <div class="gaps-summary">
                        <label>Knowledge Gaps:</label>
                        <span>{graphState.analytics?.gaps?.length || 0} identified</span>
                    </div>
                </div>
            {/if}
        </div>
        
        <svg 
            bind:this={svgElement}
            width="800" 
            height="600"
            class="knowledge-graph-svg"
        ></svg>
        
        {#if showClustering && graphState.clusters.length}
            <div class="clusters-panel">
                <h4>Semantic Clusters</h4>
                {#each graphState.clusters as cluster, i}
                    <div class="cluster-item" style="border-left-color: {d3.schemeCategory10[i % 10]}">
                        <strong>{cluster.clusterName}</strong>
                        <p>{cluster.description}</p>
                        <small>{cluster.entities.length} entities | Cohesion: {cluster.cohesionScore.toFixed(2)}</small>
                    </div>
                {/each}
            </div>
        {/if}
    {/if}
</div>

<style>
    .knowledge-graph-container {
        display: flex;
        flex-direction: column;
        height: 100%;
        background: var(--color-bg-secondary);
        border-radius: 8px;
        overflow: hidden;
    }
    
    .graph-controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        background: var(--color-bg-primary);
        border-bottom: 1px solid var(--color-border);
    }
    
    .stats {
        display: flex;
        gap: 1rem;
    }
    
    .stats span {
        padding: 0.25rem 0.5rem;
        background: var(--color-bg-tertiary);
        border-radius: 4px;
        font-size: 0.875rem;
    }
    
    .analytics-panel {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .metric, .gaps-summary {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    
    .score {
        font-weight: bold;
        color: var(--color-success);
    }
    
    .knowledge-graph-svg {
        flex: 1;
        background: white;
    }
    
    .clusters-panel {
        max-height: 300px;
        overflow-y: auto;
        padding: 1rem;
        background: var(--color-bg-primary);
        border-top: 1px solid var(--color-border);
    }
    
    .cluster-item {
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        background: var(--color-bg-secondary);
        border-left: 4px solid;
        border-radius: 4px;
    }
    
    .loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 400px;
        gap: 1rem;
    }
    
    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid var(--color-border);
        border-top: 4px solid var(--color-primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .error {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 400px;
        gap: 1rem;
        color: var(--color-error);
    }

    .error button {
        padding: 0.5rem 1rem;
        background: var(--color-primary);
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
</style>
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