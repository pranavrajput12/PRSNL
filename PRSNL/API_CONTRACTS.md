# API Contracts Documentation - PRSNL Project

*Generated: 2025-01-08*

## 📑 Overview

This document details all API endpoints, their contracts, headers, and authentication requirements in the PRSNL backend.

## 🔐 Authentication Status

**CRITICAL GAP**: Most endpoints lack authentication. Only Knowledge Graph API has consistent auth requirements.

## 📡 API Endpoints by Category

### 1. Admin API (`/api/admin`)

#### Storage Statistics
- **Endpoint**: `GET /api/admin/storage/stats`
- **Headers**: Standard (Accept, Content-Type)
- **Auth**: ❌ None
- **Response**: 
  ```json
  {
    "total_size": integer,
    "file_count": integer,
    "size_by_type": object
  }
  ```

#### Cleanup Orphaned Files
- **Endpoint**: `POST /api/admin/cleanup/orphaned`
- **Headers**: Standard
- **Auth**: ❌ None
- **Response**: 
  ```json
  {
    "message": string,
    "status": string
  }
  ```

#### Cleanup Temporary Files
- **Endpoint**: `POST /api/admin/cleanup/temp?older_than_hours=24`
- **Headers**: Standard
- **Auth**: ❌ None
- **Query Params**: `older_than_hours` (default: 24)
- **Response**: Same as cleanup orphaned

#### Debug Items
- **Endpoint**: `GET /api/admin/debug/items`
- **Headers**: Standard
- **Auth**: ❌ None
- **Response**: 
  ```json
  {
    "total_items": integer,
    "status_counts": array,
    "recent_items": array
  }
  ```

### 2. AI Suggestions API (`/api`)

#### Get AI Suggestions
- **Endpoint**: `POST /api/suggest`
- **Headers**: 
  - `Content-Type: application/json`
- **Auth**: ❌ None
- **Request Body**:
  ```json
  {
    "url": "https://example.com"
  }
  ```
- **Response**:
  ```json
  {
    "title": string,
    "summary": string,
    "tags": [string],
    "category": string | null
  }
  ```

### 3. Analytics API (`/api/analytics`)

#### Content Trends
- **Endpoint**: `GET /api/analytics/trends?timeframe=7d`
- **Headers**: Standard
- **Auth**: ❌ None
- **Query Params**: `timeframe` (7d|30d|90d|1y)
- **Cache**: 1 hour
- **Response**:
  ```json
  {
    "trends": [
      {
        "date": "YYYY-MM-DD",
        "count": integer
      }
    ]
  }
  ```

#### Top Topics
- **Endpoint**: `GET /api/analytics/topics?limit=10`
- **Headers**: Standard
- **Auth**: ❌ None
- **Query Params**: `limit` (default: 10)
- **Cache**: 1 hour
- **Response**:
  ```json
  {
    "topics": [
      {
        "tag": string,
        "count": integer,
        "percentage": float
      }
    ]
  }
  ```

#### Usage Patterns
- **Endpoint**: `GET /api/analytics/usage_patterns`
- **Headers**: Standard
- **Auth**: ❌ None
- **Cache**: 1 hour
- **Response**:
  ```json
  {
    "total_items": integer,
    "content_type_distribution": object,
    "average_items_per_day": float,
    "recent_daily_counts": array
  }
  ```

#### AI Insights
- **Endpoint**: `GET /api/analytics/ai_insights`
- **Headers**: Standard
- **Auth**: ❌ None
- **Cache**: 6 hours
- **Response**:
  ```json
  {
    "insights": [
      {
        "id": string,
        "insight": string
      }
    ]
  }
  ```

### 4. Capture API (`/api`)

#### Capture Content
- **Endpoint**: `POST /api/capture`
- **Headers**: 
  - `Content-Type: application/json`
- **Auth**: ❌ None
- **Rate Limit**: ✅ Applied
- **Request Body**:
  ```json
  {
    "url": "https://example.com" | null,
    "content": string | null,
    "title": string | null,
    "highlight": string | null,
    "tags": [string] | null
  }
  ```
- **Response** (201):
  ```json
  {
    "id": "uuid",
    "status": "pending|completed|failed",
    "message": string,
    "duplicate_info": object | null
  }
  ```
- **Validation**: Either `url` or `content` required

#### Check Duplicate
- **Endpoint**: `POST /api/capture/check-duplicate`
- **Headers**: 
  - `Content-Type: application/json`
- **Auth**: ❌ None
- **Request Body**:
  ```json
  {
    "url": "https://example.com"
  }
  ```
- **Response**:
  ```json
  {
    "is_duplicate": boolean,
    "existing_item": object | null
  }
  ```

### 5. Items API (`/api/items`)

#### Get Item
- **Endpoint**: `GET /api/items/{item_id}`
- **Headers**: Standard
- **Auth**: ❌ None
- **Path Params**: `item_id` (UUID)
- **Cache**: Item-specific caching
- **Response**:
  ```json
  {
    "id": "uuid",
    "url": string | null,
    "title": string,
    "summary": string | null,
    "content": string | null,
    "tags": [string],
    "created_at": "ISO8601",
    "updated_at": "ISO8601",
    "accessed_at": "ISO8601",
    "access_count": integer,
    "status": string,
    "item_type": string | null,
    "platform": string | null,
    "duration": integer | null,
    "file_path": string | null,
    "thumbnail_url": string | null,
    "metadata": object | null
  }
  ```

#### Update Item
- **Endpoint**: `PATCH /api/items/{item_id}`
- **Headers**: 
  - `Content-Type: application/json`
- **Auth**: ❌ None
- **Path Params**: `item_id` (UUID)
- **Request Body**:
  ```json
  {
    "title": string | null,
    "summary": string | null,
    "tags": [string] | null
  }
  ```
- **Response**: Updated item object
- **Cache**: Invalidates item, search, timeline caches

#### Delete Item
- **Endpoint**: `DELETE /api/items/{item_id}`
- **Headers**: Standard
- **Auth**: ❌ None
- **Path Params**: `item_id` (string)
- **Response**:
  ```json
  {
    "message": string,
    "id": string
  }
  ```

### 6. Enhanced Search API (`/api/search`)

#### Enhanced Multi-Modal Search
- **Endpoint**: `POST /api/search/`
- **Headers**: 
  - `Content-Type: application/json`
- **Auth**: ❌ None (Optional user context supported)
- **Request Body**:
  ```json
  {
    "query": "string (required, max 1000 chars)",
    "search_type": "semantic|keyword|hybrid (default: hybrid)",
    "limit": "integer (default: 20, max: 100)",
    "threshold": "float (default: 0.3, range: 0.0-1.0)",
    "include_duplicates": "boolean (default: false)"
  }
  ```
- **Cache**: 5 minutes  
- **Response**:
  ```json
  {
    "results": [
      {
        "id": "uuid",
        "title": "string",
        "snippet": "string",
        "url": "string | null",
        "tags": ["string"],
        "created_at": "ISO8601",
        "similarity": 0.89,
        "search_type": "hybrid",
        "component_scores": {
          "semantic": 0.85,
          "keyword": 0.92
        }
      }
    ],
    "total": 15,
    "query": "search query",
    "search_type": "hybrid",
    "deduplication": {
      "original_count": 18,
      "deduplicated_count": 15,
      "removed_duplicates": 3
    }
  }
  ```

#### Find Similar Items
- **Endpoint**: `GET /api/search/similar/{item_id}?limit=10`
- **Headers**: Standard
- **Auth**: ❌ None
- **Path Params**: `item_id` (string)
- **Query Params**: `limit` (default: 10)
- **Cache**: 1 day
- **Response**:
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "title": string,
        "summary": string,
        "similarity": float,
        "tags": [string]
      }
    ]
  }
  ```

#### Semantic Search
- **Endpoint**: `POST /api/search/semantic?limit=20`
- **Headers**: 
  - `Content-Type: application/json`
- **Auth**: ❌ None
- **Query Params**: `limit` (default: 20)
- **Request Body**:
  ```json
  {
    "query": string
  }
  ```
- **Cache**: 1 day
- **Response**: Similar to find similar items

### 7. Timeline API (`/api`)

#### Get Timeline
- **Endpoint**: `GET /api/timeline?limit=20&cursor=xyz`
- **Headers**: Standard
- **Auth**: ❌ None
- **Query Params**:
  - `limit` (default: 20, max: 100)
  - `cursor` (optional, for pagination)
  - `page` (deprecated)
- **Response**:
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "title": string,
        "url": string | null,
        "snippet": string,
        "tags": [string],
        "created_at": "ISO8601"
      }
    ],
    "next_cursor": string | null
  }
  ```

### 8. Vision API (`/api/vision`)

#### Analyze Image
- **Endpoint**: `POST /api/vision/analyze?save_to_db=true`
- **Headers**: 
  - `Content-Type: multipart/form-data`
- **Auth**: ❌ None
- **Query Params**: `save_to_db` (default: true)
- **Request Body**: File upload
- **Response**:
  ```json
  {
    "success": boolean,
    "data": {
      "text": string,
      "description": string,
      "objects": [string],
      "tags": [string],
      "colors": [string],
      "confidence": float
    }
  }
  ```

#### Process Screenshot
- **Endpoint**: `POST /api/vision/screenshot?url=&title=`
- **Headers**: 
  - `Content-Type: multipart/form-data`
- **Auth**: ❌ None
- **Query Params**:
  - `url` (optional)
  - `title` (optional)
- **Request Body**: File upload
- **Response**:
  ```json
  {
    "success": boolean,
    "item_id": string,
    "analysis": object
  }
  ```

#### Vision Status
- **Endpoint**: `GET /api/vision/status`
- **Headers**: Standard
- **Auth**: ❌ None
- **Response**:
  ```json
  {
    "providers": object,
    "usage": object
  }
  ```

### 9. WebSocket API (`/ws`)

#### AI Stream
- **Endpoint**: `ws://localhost:8000/ws/ai/stream/{client_id}`
- **Protocol**: WebSocket
- **Auth**: ❌ None
- **Path Params**: `client_id` (string)
- **Message Format**:
  ```json
  {
    "content": string
  }
  ```
- **Response Stream**:
  ```json
  {
    "chunk": string
  }
  ```
  or
  ```json
  {
    "error": string
  }
  ```

#### AI Tags Stream
- **Endpoint**: `ws://localhost:8000/ws/ai/tags/{client_id}`
- **Protocol**: WebSocket
- **Auth**: ❌ None
- **Path Params**: `client_id` (string)
- **Message/Response**: Same as AI Stream

#### Chat WebSocket
- **Endpoint**: `ws://localhost:8000/ws/chat/{client_id}`
- **Protocol**: WebSocket
- **Auth**: ❌ None
- **Path Params**: `client_id` (string)
- **Message Format**:
  ```json
  {
    "message": string,
    "history": array
  }
  ```
- **Response Types**:
  ```json
  {
    "type": "connection",
    "status": string,
    "message": string
  }
  ```
  ```json
  {
    "type": "status",
    "message": string
  }
  ```
  ```json
  {
    "type": "chunk",
    "content": string
  }
  ```
  ```json
  {
    "type": "complete",
    "message": string,
    "citations": array,
    "context_count": integer
  }
  ```
  ```json
  {
    "type": "error",
    "message": string
  }
  ```

### 10. Categorization API (`/api`)

#### Categorize Content
- **Endpoint**: `POST /api/categorize`
- **Headers**: 
  - `Content-Type: application/json`
- **Auth**: ❌ None
- **Request Body**:
  ```json
  {
    "title": string,
    "content": string,
    "tags": [string] | null
  }
  ```
- **Response**:
  ```json
  {
    "category": string,
    "subcategory": string,
    "confidence": float,
    "suggested_tags": [string],
    "content_type": string,
    "reasoning": string
  }
  ```

#### Bulk Categorize
- **Endpoint**: `POST /api/categorize/bulk?limit=100`
- **Headers**: Standard
- **Auth**: ❌ None
- **Query Params**: `limit` (default: 100)
- **Response**:
  ```json
  {
    "processed": integer,
    "total": integer,
    "stats": object,
    "message": string
  }
  ```

#### Get Item Connections
- **Endpoint**: `GET /api/items/{item_id}/connections?limit=5`
- **Headers**: Standard
- **Auth**: ❌ None
- **Path Params**: `item_id` (string)
- **Query Params**: `limit` (default: 5)
- **Response**: List of connection objects

#### Reorganize Clusters
- **Endpoint**: `POST /api/reorganize/clusters`
- **Headers**: Standard
- **Auth**: ❌ None
- **Response**: Clustering results

#### Category Statistics
- **Endpoint**: `GET /api/categories/stats`
- **Headers**: Standard
- **Auth**: ❌ None
- **Response**: Category statistics

### 11. Duplicate Detection API (`/api`)

#### Check Duplicate
- **Endpoint**: `POST /api/duplicates/check`
- **Headers**: 
  - `Content-Type: application/json`
- **Auth**: ❌ None
- **Request Body**:
  ```json
  {
    "url": string | null,
    "title": string,
    "content": string | null
  }
  ```
- **Response**:
  ```json
  {
    "is_duplicate": boolean,
    "duplicates": array,
    "recommendation": string
  }
  ```

#### Find All Duplicates
- **Endpoint**: `GET /api/duplicates/find-all?min_similarity=0.85`
- **Headers**: Standard
- **Auth**: ❌ None
- **Query Params**: `min_similarity` (default: 0.85)
- **Response**: List of duplicate groups

#### Merge Duplicates
- **Endpoint**: `POST /api/duplicates/merge`
- **Headers**: 
  - `Content-Type: application/json`
- **Auth**: ❌ None
- **Request Body**:
  ```json
  {
    "keep_id": string,
    "duplicate_ids": [string]
  }
  ```
- **Response**:
  ```json
  {
    "success": boolean,
    "message": string,
    "merged_tags": [string] | null,
    "deleted_ids": [string] | null
  }
  ```

### 12. Questions API (`/api`)

#### Suggest Questions (v0)
- **Endpoint**: `GET /api/suggest-questions?context=&limit=5`
- **Headers**: Standard
- **Auth**: ❌ None
- **Query Params**:
  - `context` (optional)
  - `limit` (default: 5)
- **Response**:
  ```json
  {
    "questions": [string],
    "context": string,
    "source": string
  }
  ```

#### Suggest Questions (v1)
- **Endpoint**: `GET /api/v1/suggest-questions?context=&item_id=&limit=5`
- **Headers**: Standard
- **Auth**: ❌ None
- **Query Params**:
  - `context` (optional)
  - `item_id` (optional)
  - `limit` (default: 5)
- **Response**: Same as v0

### 13. Summarization API (`/api`)

#### Summarize Item
- **Endpoint**: `POST /api/summarization/item`
- **Headers**: 
  - `Content-Type: application/json`
  - `X-User-Context` (optional)
- **Auth**: ⚠️ Optional user context
- **Request Body**:
  ```json
  {
    "item_id": string,
    "summary_type": "brief|detailed|bullet|executive"
  }
  ```
- **Response**:
  ```json
  {
    "success": boolean,
    "data": object,
    "message": string | null
  }
  ```

#### Generate Digest
- **Endpoint**: `POST /api/summarization/digest`
- **Headers**: 
  - `Content-Type: application/json`
  - `X-User-Context` (optional)
- **Auth**: ⚠️ Optional user context
- **Request Body**:
  ```json
  {
    "period": "daily|weekly|monthly",
    "user_id": string | null
  }
  ```
- **Response**: Same structure as summarize item

#### Topic Summary
- **Endpoint**: `POST /api/summarization/topic`
- **Headers**: 
  - `Content-Type: application/json`
  - `X-User-Context` (optional)
- **Auth**: ⚠️ Optional user context
- **Request Body**:
  ```json
  {
    "topic": string,
    "limit": integer
  }
  ```
- **Response**: Same structure as summarize item

#### Custom Summary
- **Endpoint**: `POST /api/summarization/custom`
- **Headers**: 
  - `Content-Type: application/json`
  - `X-User-Context` (optional)
- **Auth**: ⚠️ Optional user context
- **Request Body**:
  ```json
  {
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "categories": [string] | null,
    "tags": [string] | null
  }
  ```
- **Response**: Same structure as summarize item

#### Batch Summary
- **Endpoint**: `POST /api/summarization/batch`
- **Headers**: 
  - `Content-Type: application/json`
  - `X-User-Context` (optional)
- **Auth**: ⚠️ Optional user context
- **Request Body**:
  ```json
  {
    "item_ids": [string],
    "summary_type": "brief|detailed|bullet|executive"
  }
  ```
- **Response**: Same structure as summarize item
- **Limit**: Maximum 50 items

#### Digest Preview
- **Endpoint**: `GET /api/summarization/digest/preview?period=daily`
- **Headers**: 
  - `X-User-Context` (optional)
- **Auth**: ⚠️ Optional user context
- **Query Params**: `period` (daily|weekly|monthly)
- **Response**: Preview data

### 14. Knowledge Graph API (`/api/knowledge-graph`)

#### Create Relationship
- **Endpoint**: `POST /api/knowledge-graph/relationships`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {token}`
- **Auth**: ✅ Required
- **Request Body**: `CreateRelationshipRequest`
- **Response**: `GraphResponse`

#### Discover Relationships
- **Endpoint**: `POST /api/knowledge-graph/discover`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {token}`
- **Auth**: ✅ Required
- **Request Body**: `DiscoverRelationshipsRequest`
- **Response**: `GraphResponse`

#### Find Learning Path
- **Endpoint**: `POST /api/knowledge-graph/path`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {token}`
- **Auth**: ✅ Required
- **Request Body**: `KnowledgePathRequest`
- **Response**: `GraphResponse`

#### Get Item Graph
- **Endpoint**: `POST /api/knowledge-graph/graph`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {token}`
- **Auth**: ✅ Required
- **Request Body**: `ItemGraphRequest`
- **Response**: `GraphResponse`

#### Get Learning Sequence
- **Endpoint**: `POST /api/knowledge-graph/learning-sequence`
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {token}`
- **Auth**: ✅ Required
- **Request Body**: `LearningSuggestionRequest`
- **Response**: `GraphResponse`

#### Find Knowledge Gaps
- **Endpoint**: `GET /api/knowledge-graph/gaps?category=`
- **Headers**: 
  - `Authorization: Bearer {token}`
- **Auth**: ✅ Required
- **Query Params**: `category` (optional)
- **Response**: Gap analysis

#### Get Item Relationships
- **Endpoint**: `GET /api/knowledge-graph/relationships/{item_id}`
- **Headers**: 
  - `Authorization: Bearer {token}`
- **Auth**: ✅ Required
- **Path Params**: `item_id` (string)
- **Response**: Relationship details

#### Delete Relationship
- **Endpoint**: `DELETE /api/knowledge-graph/relationships?source_id=&target_id=&relationship_type=`
- **Headers**: 
  - `Authorization: Bearer {token}`
- **Auth**: ✅ Required
- **Query Params**:
  - `source_id` (required)
  - `target_id` (required)
  - `relationship_type` (optional)
- **Response**: Deletion confirmation

## 🚨 Critical Gaps Identified

### 1. Authentication & Security
- **95% of endpoints have NO authentication**
- No API key management
- No rate limiting (except capture)
- No request signing or HMAC
- No CORS configuration documented
- No security headers (X-Frame-Options, CSP, etc.)

### 2. API Standards
- **No consistent versioning** (only Questions API has v1)
- **No standard error format** across endpoints
- **No request ID tracking** (X-Request-ID)
- **Inconsistent pagination** (offset/limit vs cursor)
- **No OpenAPI/Swagger documentation**

### 3. Missing Core APIs
- **User Management**: No registration, login, profile
- **Export/Import**: Referenced but not documented
- **Health/Status**: No standard health checks
- **Metrics**: Referenced but not documented
- **Jobs**: No job status tracking
- **Webhooks**: No webhook management

### 4. Header Inconsistencies
- Most endpoints don't specify required headers
- No standard headers for:
  - API versioning (X-API-Version)
  - Client identification (User-Agent, X-Client-ID)
  - Request tracking (X-Request-ID)
  - Rate limit info (X-RateLimit-*)

### 5. Response Inconsistencies
- Some return `results`, others return `items`
- Inconsistent error response structures
- No standard envelope format
- Missing HTTP status code documentation

## 🎯 Recommendations

### Immediate Actions:
1. **Implement authentication** on all non-public endpoints
2. **Standardize error responses** with consistent format
3. **Add rate limiting** to all endpoints
4. **Create health check endpoint** at `/health`
5. **Document all required headers**

### Short-term Improvements:
1. **API versioning**: Add `/v1` prefix to all endpoints
2. **Consistent pagination**: Choose cursor or offset/limit
3. **Request ID tracking**: Add X-Request-ID support
4. **OpenAPI spec**: Generate Swagger documentation
5. **CORS configuration**: Document allowed origins

### Long-term Enhancements:
1. **User management API**: Full CRUD for users
2. **API key management**: For programmatic access
3. **Webhook system**: For external integrations
4. **GraphQL endpoint**: For flexible queries
5. **Batch operations**: For bulk updates

## 📐 Proposed Standard Headers

### Request Headers:
```
Content-Type: application/json
Authorization: Bearer {token}
X-API-Version: 1.0
X-Request-ID: {uuid}
X-Client-ID: {client_identifier}
User-Agent: {client_info}
```

### Response Headers:
```
Content-Type: application/json
X-Request-ID: {uuid}
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1234567890
X-Response-Time: 123ms
```

## 🔄 Proposed Standard Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "uuid",
    "timestamp": "ISO8601"
  }
}
```

This comprehensive API contract documentation reveals significant gaps in authentication, standardization, and core functionality that should be addressed to create a robust, secure API.