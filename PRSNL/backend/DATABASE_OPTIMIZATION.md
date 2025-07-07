# Database Optimization Guide

This document describes the database indexes and optimizations implemented in PRSNL.

## Index Strategy

### 1. Primary Indexes (from schema.sql)
- `idx_items_search` - GIN index for full-text search
- `idx_items_created` - B-tree index on created_at (DESC)
- `idx_items_accessed` - B-tree index on accessed_at (DESC)
- `idx_items_status` - B-tree index on status
- `idx_items_url` - B-tree index on URL
- `idx_tags_name` - B-tree index on tag names

### 2. Performance Indexes (from 002_add_performance_indexes.sql)

#### Composite Indexes
- `idx_items_status_created` - Composite index on (status, created_at DESC)
  - Optimizes queries filtering by status and ordering by date
  - Partial index only for common statuses

#### JSON Indexes
- `idx_items_item_type` - Index on metadata->>'item_type'
  - Speeds up filtering by item type (article, video, note)
- `idx_items_platform` - Index on metadata->>'platform'
  - Optimizes video platform filtering

#### Tag Query Optimization
- `idx_item_tags_tag_item` - Composite on (tag_id, item_id)
  - Speeds up tag-based lookups
- `idx_item_tags_confidence` - Partial index for high-confidence tags
  - Only indexes tags with confidence > 0.8

#### Search Optimization
- `idx_items_url_prefix` - Text pattern ops for URL prefix searches
- `idx_items_title_trgm` - Trigram index for fuzzy title searches
- `idx_items_search_english` - Language-specific full-text search

#### Specialized Indexes
- `idx_items_bookmarks` - Partial index for bookmark items
- `idx_items_popular` - Index for frequently accessed items
- `idx_items_videos` - Partial index for video items
- `idx_items_recent_tagged` - Optimizes recent items with tags

#### Vector Search
- `idx_items_embedding` - IVFFlat index for similarity searches
  - Uses 100 lists for efficient nearest neighbor queries

## Query Patterns Optimized

### 1. Timeline Queries
```sql
SELECT * FROM items 
WHERE status = 'completed' 
ORDER BY created_at DESC 
LIMIT 20;
```
Optimized by: `idx_items_status_created`

### 2. Tag-based Searches
```sql
SELECT i.* FROM items i
JOIN item_tags it ON i.id = it.item_id
JOIN tags t ON it.tag_id = t.id
WHERE t.name = 'tutorial'
ORDER BY i.created_at DESC;
```
Optimized by: `idx_tags_name`, `idx_item_tags_tag_item`

### 3. Video Platform Filtering
```sql
SELECT * FROM items
WHERE metadata->>'item_type' = 'video'
AND metadata->>'platform' = 'youtube'
ORDER BY created_at DESC;
```
Optimized by: `idx_items_videos`, `idx_items_platform`

### 4. Semantic Search
```sql
SELECT * FROM items
ORDER BY embedding <=> $1
LIMIT 10;
```
Optimized by: `idx_items_embedding`

### 5. Full-text Search
```sql
SELECT * FROM items
WHERE search_vector @@ plainto_tsquery('english', $1)
ORDER BY ts_rank(search_vector, plainto_tsquery('english', $1)) DESC;
```
Optimized by: `idx_items_search`, `idx_items_search_english`

## Applying Indexes

### Automatic Application
Indexes are automatically created when the database schema is initialized.

### Manual Application
To manually apply performance indexes:
```bash
cd PRSNL/backend
python scripts/apply_indexes.py
```

### Docker Environment
```bash
docker-compose exec backend python scripts/apply_indexes.py
```

## Monitoring Index Usage

### Check Index Sizes
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::regclass) DESC;
```

### Check Index Usage
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Find Missing Indexes
```sql
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch
FROM pg_stat_user_tables
WHERE seq_scan > idx_scan
ORDER BY seq_scan DESC;
```

## Maintenance

### Regular Tasks
1. **VACUUM**: Run weekly to reclaim space
   ```sql
   VACUUM ANALYZE items;
   ```

2. **REINDEX**: Run monthly for heavily updated indexes
   ```sql
   REINDEX INDEX idx_items_search;
   ```

3. **Statistics Update**: Run after bulk operations
   ```sql
   ANALYZE items;
   ```

### Performance Tips
1. Monitor slow queries using `pg_stat_statements`
2. Use `EXPLAIN ANALYZE` to verify index usage
3. Consider partitioning for very large tables (>10M rows)
4. Adjust `work_mem` and `shared_buffers` PostgreSQL settings
5. Use connection pooling (already implemented via asyncpg)

## Future Optimizations
1. Table partitioning by date for items table
2. Materialized views for complex aggregations
3. Redis caching layer for hot queries
4. Read replicas for scaling read operations