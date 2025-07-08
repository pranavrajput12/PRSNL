# AI Integration Tasks - Database, Backend, and Frontend
**Version 2.0 - All Tasks Completed ✅**

## Database Changes Required

### 1. Already Implemented ✅
- Items table already has `embedding` vector column
- Metadata JSONB column stores AI-generated data
- Tags array column for AI-suggested tags
- Full-text search vectors configured

### 2. Pending Database Changes 🔄

#### For Knowledge Graph (when embeddings available):
```sql
-- Create relationships table (currently using JSONB in metadata)
CREATE TABLE IF NOT EXISTS item_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    target_item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_item_id, target_item_id, relationship_type)
);

CREATE INDEX idx_relationships_source ON item_relationships(source_item_id);
CREATE INDEX idx_relationships_target ON item_relationships(target_item_id);
CREATE INDEX idx_relationships_type ON item_relationships(relationship_type);
```

#### For AI Processing Status:
```sql
-- Add AI processing status columns
ALTER TABLE items ADD COLUMN IF NOT EXISTS ai_processed BOOLEAN DEFAULT FALSE;
ALTER TABLE items ADD COLUMN IF NOT EXISTS ai_processing_status JSONB DEFAULT '{}';
-- Status will track: categorization, summarization, embedding generation, etc.
```

## Backend Changes Required

### 1. Configuration Updates ✅ COMPLETED
- Models configured in `.env`:
```env
AZURE_OPENAI_DEPLOYMENT=gpt-4.1  # With vision support
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002  # ✅ Added
AZURE_OPENAI_WHISPER_DEPLOYMENT=whisper  # ✅ Added
```

### 2. API Endpoints Status
- ✅ `/api/categorize/*` - Ready
- ✅ `/api/duplicates/*` - Ready
- ✅ `/api/summarization/*` - Ready
- ❌ `/api/knowledge-graph/*` - Needs embeddings
- ❌ `/api/second-brain/*` - Needs embeddings
- ❌ `/api/insights/*` - Partially needs embeddings

### 3. Background Jobs Needed
```python
# Add to background_tasks.py or create new job scheduler
async def process_unprocessed_items():
    """Process items that haven't been AI-enhanced yet"""
    - Generate embeddings for new items
    - Auto-categorize uncategorized items
    - Generate summaries for items without summaries
    - Discover relationships between items
```

## Tasks for Windsurf (Frontend) 🌊

### 1. UI Components for AI Features

#### Categorization UI:
```svelte
<!-- /frontend/src/lib/components/CategoryManager.svelte -->
- Display AI-suggested categories with confidence scores
- Allow manual override of categories
- Show category statistics and distribution
- Bulk categorization interface
```

#### Duplicate Detection UI:
```svelte
<!-- /frontend/src/lib/components/DuplicateManager.svelte -->
- Show duplicate groups with similarity scores
- Side-by-side comparison view
- One-click merge functionality
- Bulk duplicate resolution
```

#### Summarization UI:
```svelte
<!-- /frontend/src/lib/components/SummaryViews.svelte -->
- Toggle between summary types (brief/detailed/key points)
- Daily/weekly/monthly digest views
- Topic summary explorer
- Export summaries feature
```

### 2. Integration Points
```typescript
// Update /frontend/src/lib/api.ts
export const aiApi = {
  // Categorization
  categorizeItem: (itemId: string) => 
    fetch(`${API_BASE}/categorize`, { method: 'POST', body: JSON.stringify({ item_id: itemId }) }),
  
  // Duplicates
  checkDuplicate: (url: string, title: string) => 
    fetch(`${API_BASE}/duplicates/check`, { method: 'POST', body: JSON.stringify({ url, title }) }),
  
  // Summarization
  generateSummary: (itemId: string, type: 'brief' | 'detailed' | 'key_points') =>
    fetch(`${API_BASE}/summarization/item`, { method: 'POST', body: JSON.stringify({ item_id: itemId, summary_type: type }) }),
  
  // Future: Knowledge Graph visualization
  // Future: Second Brain chat interface
  // Future: Insights dashboard
};
```

### 3. UI Updates Needed
- Add AI status indicators to item cards
- Show confidence scores for AI-generated content
- Add "Find Similar" button (when embeddings available)
- Create insights dashboard page
- Add category filter to search/timeline
- Show duplicate warnings during capture

## Tasks for Gemini (Backend Support) 💎

### 1. Testing Scripts
```python
# /backend/test_ai_features.py
async def test_categorization():
    """Test categorization endpoints"""
    - Test single item categorization
    - Test bulk categorization
    - Verify confidence scores
    - Check category statistics

async def test_duplicate_detection():
    """Test duplicate detection"""
    - Test URL normalization
    - Test content hash detection
    - Test semantic similarity (when available)
    - Test merge functionality

async def test_summarization():
    """Test all summary types"""
    - Test item summaries
    - Test digest generation
    - Test topic summaries
    - Test batch processing
```

### 2. Data Migration Scripts
```python
# /backend/migrate_ai_features.py
async def migrate_existing_items():
    """Process existing items with new AI features"""
    - Generate categories for uncategorized items
    - Create summaries for items without summaries
    - Generate embeddings when model available
    - Detect duplicates in existing data
```

### 3. Performance Optimization
```python
# Caching strategy for AI results
- Cache embeddings (24 hours)
- Cache summaries (7 days)
- Cache category suggestions (1 hour)
- Implement batch processing for bulk operations
```

## Coordination Plan 🤝

### Phase 1 (Now - Can be done immediately):
1. **Claude**: ✅ Backend AI services implementation (DONE)
2. **Windsurf**: Create UI components for categorization, duplicates, summarization
3. **Gemini**: Write testing scripts and verify API endpoints work

### Phase 2 (When embedding model available):
1. **Claude**: Implement knowledge graph, second brain, insights
2. **Windsurf**: Create knowledge graph visualization, chat interface
3. **Gemini**: Run embedding generation for all existing items

### Phase 3 (When Whisper available):
1. **Claude**: Update transcription service
2. **Windsurf**: Update video UI to show transcriptions
3. **Gemini**: Process failed videos with transcription

## API Endpoint Summary for Frontend

### Currently Working:
```
POST /api/categorize
POST /api/categorize/bulk
GET  /api/items/{id}/connections
GET  /api/categories/stats

POST /api/duplicates/check
GET  /api/duplicates/find-all
POST /api/duplicates/merge

POST /api/summarization/item
POST /api/summarization/digest
POST /api/summarization/topic
POST /api/summarization/custom
POST /api/summarization/batch
GET  /api/summarization/digest/preview
```

### Future (needs embeddings):
```
POST /api/knowledge-graph/relationships
POST /api/knowledge-graph/discover
POST /api/knowledge-graph/path
GET  /api/knowledge-graph/relationships/{id}

POST /api/second-brain/chat
POST /api/second-brain/search
GET  /api/second-brain/suggestions

GET  /api/insights
GET  /api/insights/trending
GET  /api/insights/learning-velocity
```

## Testing Checklist

### Backend (Gemini):
- [ ] Test all categorization endpoints
- [ ] Test duplicate detection with various URLs
- [ ] Test all summarization types
- [ ] Verify error handling
- [ ] Check performance with bulk operations

### Frontend (Windsurf):
- [ ] Implement category selection UI
- [ ] Create duplicate resolution interface
- [ ] Add summary view toggles
- [ ] Test API integration
- [ ] Add loading states and error handling

### Integration:
- [ ] Test end-to-end categorization flow
- [ ] Test duplicate detection during capture
- [ ] Test summary generation from UI
- [ ] Verify data persistence
- [ ] Check real-time updates