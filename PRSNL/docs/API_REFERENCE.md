# PRSNL API Reference

**Version**: 10.0  
**Last Updated**: 2025-08-01  
**Base URL**: `http://localhost:8000/api`

## Overview

The PRSNL API provides comprehensive access to the Personal Knowledge Management System, including content capture, AI processing, knowledge graph analytics, and advanced search capabilities.

## Authentication

All endpoints support optional authentication via JWT tokens:

```http
Authorization: Bearer <your-jwt-token>
```

For development, many endpoints work without authentication for convenience.

## Core Content APIs

### Items Management

#### GET `/items`
List and filter items with pagination support.

**Query Parameters:**
- `limit` (int, default: 20) - Number of items per page
- `offset` (int, default: 0) - Pagination offset
- `type` (string) - Filter by item type
- `status` (string) - Filter by processing status
- `tags` (array) - Filter by tags
- `created_after` (datetime) - Filter by creation date

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Item Title",
      "url": "https://example.com",
      "type": "article",
      "status": "completed",
      "created_at": "2025-08-01T12:00:00Z",
      "tags": ["ai", "technology"]
    }
  ],
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

#### POST `/items`
Create a new item with optional AI processing.

**Request Body:**
```json
{
  "title": "Article Title",
  "url": "https://example.com",
  "content": "Article content...",
  "enable_summarization": true,
  "type": "article"
}
```

#### GET `/items/{id}`
Get a single item by ID with full details.

#### PUT `/items/{id}`
Update an existing item.

#### DELETE `/items/{id}`
Delete an item and all associated data.

### Content Capture

#### POST `/capture`
Capture content from URLs, files, or direct input.

**Request Body:**
```json
{
  "url": "https://example.com",
  "enable_summarization": true,
  "capture_type": "url",
  "content_type": "auto"
}
```

**Response:**
```json
{
  "success": true,
  "item_id": "uuid",
  "processing_status": "queued",
  "message": "Content captured and queued for processing"
}
```

## Knowledge Graph APIs

### Graph Visualization

#### GET `/unified-knowledge-graph/visual/full`
Get the complete knowledge graph for visualization.

**Query Parameters:**
- `entity_type` (string) - Filter by entity type
- `relationship_type` (string) - Filter by relationship type
- `limit` (int, default: 100, max: 500) - Maximum nodes
- `min_confidence` (float, default: 0.5) - Minimum confidence threshold

**Response:**
```json
{
  "nodes": [
    {
      "id": "uuid",
      "title": "Entity Name",
      "type": "knowledge_concept",
      "confidence": 0.85,
      "metadata": {
        "source_title": "Original Content",
        "domain": "Technology"
      }
    }
  ],
  "edges": [
    {
      "source": "uuid1",
      "target": "uuid2",
      "relationship": "explains",
      "strength": 0.8,
      "confidence": 0.9
    }
  ],
  "metadata": {
    "total_nodes": 140,
    "total_edges": 176,
    "entity_types": {
      "knowledge_concept": 85,
      "text_entity": 55
    }
  }
}
```

#### GET `/unified-knowledge-graph/visual/{item_id}`
Get knowledge graph centered around a specific item.

**Query Parameters:**
- `depth` (int, default: 2, max: 3) - Relationship traversal depth
- `limit` (int, default: 50, max: 200) - Maximum nodes

### Graph Analytics

#### GET `/unified-knowledge-graph/stats`
Get comprehensive knowledge graph statistics.

**Response:**
```json
{
  "unified_knowledge_graph": true,
  "total_entities": 140,
  "total_relationships": 176,
  "entity_types": {
    "knowledge_concept": 85,
    "text_entity": 55
  },
  "relationship_types": {
    "explains": 45,
    "references": 32,
    "builds_on": 28
  },
  "average_confidence": 0.83,
  "graph_density": 0.089,
  "connected_components": 5
}
```

#### POST `/unified-knowledge-graph/clustering/semantic`
Perform semantic clustering of entities.

**Request Body:**
```json
{
  "min_cluster_size": 3,
  "max_clusters": 10,
  "clustering_algorithm": "semantic",
  "entity_types": ["knowledge_concept", "text_entity"],
  "min_confidence": 0.5
}
```

**Response:**
```json
{
  "clusters": [
    {
      "cluster_id": "uuid",
      "cluster_name": "Technology: JavaScript & React",
      "entities": [/* UnifiedGraphNode objects */],
      "cohesion_score": 0.78,
      "description": "Cluster of 6 related technology entities",
      "keywords": ["javascript", "react", "development"],
      "domain": "Technology"
    }
  ],
  "total_entities_clustered": 92,
  "clustering_metadata": {
    "algorithm": "semantic",
    "total_entities_processed": 140
  }
}
```

#### POST `/unified-knowledge-graph/analysis/gaps`
Analyze knowledge graph for gaps and missing relationships.

**Request Body:**
```json
{
  "analysis_depth": "standard",
  "focus_domains": ["Technology", "AI"],
  "min_severity": "medium",
  "include_suggestions": true
}
```

**Response:**
```json
{
  "gaps": [
    {
      "gap_type": "isolated_entity",
      "severity": "high",
      "title": "Isolated Entity: Advanced React Patterns",
      "description": "Entity has no relationships with other entities",
      "affected_entities": ["Advanced React Patterns"],
      "suggested_actions": ["Review entity content for potential relationships"]
    }
  ],
  "domains": [
    {
      "domain_name": "Technology",
      "entity_count": 45,
      "relationship_density": 0.12,
      "completeness_score": 0.73,
      "key_entities": ["JavaScript", "React", "Node.js"]
    }
  ],
  "overall_completeness": 0.68
}
```

#### POST `/unified-knowledge-graph/paths/discover`
Find learning paths between entities.

**Request Body:**
```json
{
  "start_entity_id": "uuid",
  "end_entity_id": "uuid",
  "max_depth": 5,
  "relationship_types": ["explains", "builds_on", "prerequisite"],
  "min_confidence": 0.6
}
```

### Relationship Management

#### POST `/unified-knowledge-graph/relationships`
Create a new relationship between entities.

**Request Body:**
```json
{
  "source_entity_id": "uuid",
  "target_entity_id": "uuid",
  "relationship_type": "explains",
  "confidence_score": 0.8,
  "strength": 1.0,
  "context": "Source entity provides detailed explanation of target concept"
}
```

#### DELETE `/unified-knowledge-graph/relationships/{relationship_id}`
Remove a relationship from the knowledge graph.

#### POST `/unified-knowledge-graph/relationships/suggest`
Get AI-powered relationship suggestions.

**Request Body:**
```json
{
  "entity_id": "uuid",
  "limit": 10,
  "min_confidence": 0.6,
  "relationship_types": ["explains", "references"],
  "exclude_existing": true
}
```

## Auto-Processing APIs

### Processing Management

#### POST `/auto-processing/process-item/{item_id}`
Manually trigger auto-processing for a specific item.

**Response:**
```json
{
  "success": true,
  "processing_id": "uuid",
  "status": "queued",
  "estimated_completion": "2025-08-01T12:05:00Z"
}
```

#### GET `/auto-processing/status/{processing_id}`
Get processing status and progress.

**Response:**
```json
{
  "processing_id": "uuid",
  "status": "processing",
  "current_step": "summarization",
  "progress_percentage": 60,
  "steps_completed": ["ai_analysis", "categorization"],
  "estimated_completion": "2025-08-01T12:03:00Z"
}
```

#### GET `/auto-processing/queue/status`
Get current processing queue status.

#### POST `/auto-processing/batch-process`
Process multiple items in batch.

**Request Body:**
```json
{
  "item_ids": ["uuid1", "uuid2", "uuid3"],
  "priority": "normal",
  "enable_entity_extraction": true
}
```

## Entity Extraction APIs

### Entity Management

#### POST `/entity-extraction/extract/{item_id}`
Extract entities from a specific item's content.

**Request Body:**
```json
{
  "content_type": "article",
  "extraction_options": {
    "include_relationships": true,
    "confidence_threshold": 0.7,
    "max_entities": 50
  }
}
```

#### GET `/entity-extraction/entities`
List extracted entities with filtering.

**Query Parameters:**
- `entity_type` (string) - Filter by entity type
- `source_content_id` (uuid) - Filter by source content
- `min_confidence` (float) - Minimum confidence threshold

#### POST `/entity-extraction/relationships/batch`
Create multiple relationships in batch.

## Search APIs

### Enhanced Search

#### POST `/search/enhanced`
Perform semantic, keyword, or hybrid search.

**Request Body:**
```json
{
  "query": "machine learning algorithms",
  "search_type": "hybrid",
  "limit": 20,
  "threshold": 0.7,
  "include_duplicates": false
}
```

#### POST `/search/similar`
Find similar items using vector similarity.

**Request Body:**
```json
{
  "item_id": "uuid",
  "limit": 10,
  "threshold": 0.8,
  "exclude_self": true
}
```

## AI Integration APIs

### AI Analysis

#### POST `/ai/analyze-content`
Get AI analysis of content.

**Request Body:**
```json
{
  "content": "Content to analyze...",
  "analysis_type": "comprehensive",
  "include_entities": true,
  "include_summary": true
}
```

#### POST `/ai/suggest-tags`
Get AI-suggested tags for content.

#### POST `/ai/generate-summary`
Generate AI summary of content.

## Error Handling

All endpoints return consistent error responses:

### HTTP 400 - Bad Request
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "url",
      "reason": "Invalid URL format"
    }
  }
}
```

### HTTP 401 - Unauthorized
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Valid authentication token required"
  }
}
```

### HTTP 404 - Not Found
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "resource_id": "uuid"
  }
}
```

### HTTP 500 - Internal Server Error
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "request_id": "uuid"
  }
}
```

## Rate Limiting

API endpoints have the following rate limits:

- **Standard endpoints**: 1000 requests/hour
- **AI processing endpoints**: 100 requests/hour  
- **Knowledge graph analytics**: 60 requests/hour
- **Semantic clustering**: 20 requests/hour

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1672531200
```

## SDKs and Examples

### Python SDK Example
```python
import requests

# Initialize client
api_base = "http://localhost:8000/api"
headers = {"Authorization": "Bearer your-token"}

# Capture content
response = requests.post(f"{api_base}/capture", json={
    "url": "https://example.com",
    "enable_summarization": True
}, headers=headers)

item_id = response.json()["item_id"]

# Get knowledge graph
graph = requests.get(f"{api_base}/unified-knowledge-graph/visual/full", 
                    headers=headers).json()

# Perform semantic clustering
clusters = requests.post(f"{api_base}/unified-knowledge-graph/clustering/semantic", 
                        json={"clustering_algorithm": "hybrid"}, 
                        headers=headers).json()
```

### JavaScript SDK Example
```javascript
class PRSNLClient {
  constructor(baseUrl = 'http://localhost:8000/api', token = null) {
    this.baseUrl = baseUrl;
    this.headers = token ? {'Authorization': `Bearer ${token}`} : {};
  }

  async captureContent(url, options = {}) {
    const response = await fetch(`${this.baseUrl}/capture`, {
      method: 'POST',
      headers: { ...this.headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, ...options })
    });
    return response.json();
  }

  async getKnowledgeGraph(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${this.baseUrl}/unified-knowledge-graph/visual/full?${params}`, {
      headers: this.headers
    });
    return response.json();
  }

  async performClustering(options = {}) {
    const response = await fetch(`${this.baseUrl}/unified-knowledge-graph/clustering/semantic`, {
      method: 'POST',
      headers: { ...this.headers, 'Content-Type': 'application/json' },
      body: JSON.stringify(options)
    });
    return response.json();
  }
}
```

## Webhook Support

PRSNL supports webhooks for real-time notifications:

### Available Events
- `item.created` - New item added
- `item.processed` - Item processing completed
- `entity.extracted` - New entities discovered
- `relationship.created` - New relationship established
- `cluster.formed` - Semantic cluster created

### Webhook Configuration
```json
{
  "url": "https://your-app.com/webhooks/prsnl",
  "events": ["item.created", "item.processed"],
  "secret": "webhook-secret-key"
}
```

## API Versioning

The PRSNL API uses semantic versioning:
- **Major versions**: Breaking changes to endpoints or data models
- **Minor versions**: New endpoints and features
- **Patch versions**: Bug fixes and improvements

Current version: `10.0` (August 2025)

## Support

- **Documentation**: See individual endpoint documentation in `/backend/docs/KNOWLEDGE_GRAPH_API.md`
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Examples**: Complete examples available in `/examples` directory

---

**Last Updated**: 2025-08-01  
**API Version**: 10.0  
**Next Review**: 2025-09-01