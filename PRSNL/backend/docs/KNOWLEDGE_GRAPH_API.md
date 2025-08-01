# Knowledge Graph API Documentation

**Last Updated:** 2025-08-01  
**Version:** 2.7.0  
**Base URL:** `/api/unified-knowledge-graph`

## Overview

The Knowledge Graph API provides comprehensive access to the unified entity and relationship system, enabling intelligent knowledge discovery, semantic analysis, and graph-based insights. This API supports advanced features including semantic clustering, knowledge gap analysis, relationship suggestions, and learning path discovery.

## Features

- **🧠 AI-Powered Knowledge Graph**: 140+ entities, 176+ relationships with confidence scoring
- **🔍 Semantic Clustering**: Three algorithms (semantic, structural, hybrid) for intelligent grouping
- **📊 Analytics Dashboard**: Comprehensive statistics and insights
- **🛤️ Learning Path Discovery**: Graph traversal algorithms for knowledge connections
- **💡 Relationship Suggestions**: AI-powered recommendations for new relationships
- **🔍 Knowledge Gap Analysis**: Identify missing concepts and weak domains
- **📈 Real-time Visualization**: D3.js-compatible graph data with filtering

## Base URL and Authentication

All endpoints are prefixed with `/api/unified-knowledge-graph` and use optional authentication via `get_current_user_optional`.

```
Base URL: /api/unified-knowledge-graph
Authentication: Optional (Bearer token)
Content-Type: application/json
```

## Core Data Models

### UnifiedGraphNode
```json
{
  "id": "uuid",
  "title": "Entity name",
  "type": "entity_type",
  "summary": "Entity description",
  "content_type": "text|video|code",
  "confidence": 0.85,
  "created_at": "2025-08-01T12:00:00Z",
  "metadata": {
    "source_title": "Original content title",
    "source_url": "https://example.com",
    "is_center": true
  }
}
```

### UnifiedGraphEdge
```json
{
  "source": "source_entity_id",
  "target": "target_entity_id", 
  "relationship": "explains|references|builds_on",
  "strength": 0.8,
  "confidence": 0.9,
  "context": "Why this relationship exists",
  "created_at": "2025-08-01T12:00:00Z"
}
```

## API Endpoints

### 1. Graph Visualization

#### GET `/visual/full` - Complete Knowledge Graph
Get the unified knowledge graph for D3.js visualization with filtering options.

**Parameters:**
- `entity_type` (optional): Filter by entity type (`text_entity`, `knowledge_concept`, etc.)
- `relationship_type` (optional): Filter by relationship type
- `limit` (default: 100, max: 500): Maximum nodes to return
- `min_confidence` (default: 0.5): Minimum confidence threshold (0.0-1.0)

**Response:**
```json
{
  "nodes": [UnifiedGraphNode],
  "edges": [UnifiedGraphEdge],
  "metadata": {
    "total_nodes": 140,
    "total_edges": 176,
    "filters": {
      "entity_type": "knowledge_concept",
      "min_confidence": 0.5
    },
    "entity_types": {
      "knowledge_concept": 85,
      "text_entity": 55
    },
    "relationship_types": {
      "explains": 45,
      "references": 32
    }
  }
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/unified-knowledge-graph/visual/full?entity_type=knowledge_concept&limit=50&min_confidence=0.7"
```

#### GET `/visual/{item_id}` - Item-Centered Graph
Get knowledge graph centered around a specific content item with configurable depth.

**Parameters:**
- `item_id` (required): UUID of the content item
- `depth` (default: 2, max: 3): Relationship traversal depth
- `limit` (default: 50, max: 200): Maximum nodes to return  
- `min_confidence` (default: 0.5): Minimum confidence threshold

**Response:**
```json
{
  "nodes": [UnifiedGraphNode],
  "edges": [UnifiedGraphEdge],
  "metadata": {
    "center_item_id": "uuid",
    "depth": 2,
    "total_nodes": 25,
    "total_edges": 34
  }
}
```

### 2. Graph Statistics

#### GET `/stats` - Knowledge Graph Statistics
Get comprehensive statistics about the unified knowledge graph.

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
  "connected_components": 5,
  "largest_component_size": 95
}
```

### 3. Relationship Management

#### POST `/relationships` - Create Relationship
Create a new relationship between two entities in the knowledge graph.

**Request Body:**
```json
{
  "source_entity_id": "uuid",
  "target_entity_id": "uuid", 
  "relationship_type": "explains",
  "confidence_score": 0.8,
  "strength": 1.0,
  "context": "Source entity provides detailed explanation of target concept",
  "metadata": {
    "created_by": "user",
    "source": "manual"
  }
}
```

**Response:**
```json
{
  "success": true,
  "relationship_id": "uuid",
  "message": "Successfully created explains relationship"
}
```

**Supported Relationship Types:**
- **Temporal**: `precedes`, `follows`, `concurrent`, `enables`, `depends_on`
- **Content**: `discusses`, `implements`, `references`, `explains`, `demonstrates`
- **Structural**: `contains`, `part_of`, `similar_to`, `related_to`, `opposite_of`
- **Cross-modal**: `visualizes`, `describes`, `transcribes`, `summarizes`, `extends`
- **Learning**: `prerequisite`, `builds_on`, `reinforces`, `applies`, `teaches`

#### DELETE `/relationships/{relationship_id}` - Delete Relationship
Remove a relationship from the knowledge graph.

**Response:**
```json
{
  "success": true,
  "message": "Relationship deleted successfully"
}
```

### 4. Learning Path Discovery

#### POST `/paths/discover` - Discover Knowledge Paths
Find learning paths between two entities using graph traversal algorithms.

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

**Response:**
```json
{
  "paths": [
    {
      "nodes": [
        {
          "entity_id": "uuid",
          "entity_name": "Basic Concepts",
          "entity_type": "knowledge_concept",
          "confidence": 0.9
        }
      ],
      "edges": [
        {
          "source_id": "uuid1",
          "target_id": "uuid2", 
          "relationship_type": "prerequisite",
          "confidence": 0.85,
          "strength": 0.9
        }
      ],
      "total_confidence": 0.756,
      "path_length": 3,
      "learning_difficulty": "medium"
    }
  ],
  "total_paths": 4,
  "search_metadata": {
    "start_entity": "Introduction to AI",
    "end_entity": "Neural Networks",
    "max_depth": 5,
    "total_relationships_considered": 120
  }
}
```

### 5. Relationship Suggestions

#### POST `/relationships/suggest` - AI Relationship Suggestions  
Get AI-powered relationship suggestions based on semantic similarity and existing patterns.

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

**Response:**
```json
{
  "suggestions": [
    {
      "source_entity_id": "uuid1",
      "target_entity_id": "uuid2",
      "suggested_relationship": "explains",
      "confidence_score": 0.82,
      "reasoning": "Text entity provides explanation of concept (semantic similarity: 0.75)",
      "source_entity_name": "JavaScript Fundamentals",
      "target_entity_name": "Variables and Data Types",
      "semantic_similarity": 0.75,
      "existing_connections": 0
    }
  ],
  "total_suggestions": 8,
  "analysis_metadata": {
    "focus_entity_id": "uuid",
    "entities_analyzed": 45,
    "existing_relationship_patterns": 12,
    "most_common_relationships": ["explains", "references", "builds_on"]
  }
}
```

### 6. Knowledge Gap Analysis

#### POST `/analysis/gaps` - Knowledge Gap Analysis
Analyze the knowledge graph to identify gaps, missing relationships, and improvement opportunities.

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
      "suggested_actions": [
        "Review entity content for potential relationships",
        "Consider connecting to related concepts"
      ],
      "confidence_score": 0.9,
      "domain": "Technology"
    }
  ],
  "domains": [
    {
      "domain_name": "Technology",
      "entity_count": 45,
      "relationship_density": 0.12,
      "completeness_score": 0.73,
      "key_entities": ["JavaScript", "React", "Node.js"],
      "missing_concepts": ["Testing", "Deployment"],
      "interconnectedness": 0.85
    }
  ],
  "overall_completeness": 0.68,
  "analysis_summary": {
    "total_entities": 140,
    "total_relationships": 176,
    "gaps_identified": 12,
    "domains_analyzed": 6,
    "avg_domain_completeness": 0.68
  },
  "recommendations": [
    "Focus on building more relationships between existing entities",
    "Strengthen Technology domain by adding foundational concepts"
  ]
}
```

### 7. Semantic Clustering

#### POST `/clustering/semantic` - Semantic Clustering
Perform semantic clustering of entities using multiple algorithms.

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

**Clustering Algorithms:**
- **`semantic`**: Content-based similarity clustering using NLP techniques
- **`structural`**: Relationship pattern-based clustering using graph topology
- **`hybrid`**: Combined semantic and structural clustering with overlap resolution

**Response:**
```json
{
  "clusters": [
    {
      "cluster_id": "uuid",
      "cluster_name": "Technology: JavaScript & React",
      "entities": [UnifiedGraphNode],
      "central_entity": UnifiedGraphNode,
      "cohesion_score": 0.78,
      "cluster_type": "semantic",
      "description": "Cluster of 6 related technology entities focusing on javascript, react, development",
      "keywords": ["javascript", "react", "development", "frontend", "technology"],
      "domain": "Technology"
    }
  ],
  "total_entities_clustered": 92,
  "clustering_metadata": {
    "algorithm": "semantic",
    "total_entities_processed": 140,
    "clustering_parameters": {
      "min_cluster_size": 3,
      "max_clusters": 10
    },
    "relationships_considered": 176
  },
  "unclustered_entities": [UnifiedGraphNode]
}
```

## Error Handling

All endpoints return consistent error responses:

**HTTP 400 - Bad Request:**
```json
{
  "detail": "Invalid parameters: min_confidence must be between 0.0 and 1.0"
}
```

**HTTP 404 - Not Found:**
```json
{
  "detail": "Entity uuid not found"
}
```

**HTTP 409 - Conflict:**
```json
{
  "detail": "Relationship already exists between these entities"
}
```

**HTTP 500 - Internal Server Error:**
```json
{
  "detail": "Failed to generate knowledge graph: Database connection error"
}
```

## Rate Limiting

Knowledge graph operations are computationally intensive. Consider implementing rate limiting:

- **Visualization endpoints**: 60 requests/minute
- **Analysis endpoints**: 20 requests/minute  
- **Clustering operations**: 10 requests/minute

## Performance Considerations

### Query Optimization
- Use `min_confidence` filtering to reduce dataset size
- Limit node counts for large graphs
- Consider pagination for extensive results

### Caching Strategy
- Cache frequently accessed full graphs
- Use Redis for clustering results (expensive computation)
- Implement cache invalidation on relationship changes

### Database Indexes
The system uses optimized indexes for performance:
```sql
-- Composite indexes for complex queries
CREATE INDEX idx_unified_entities_composite ON unified_entities(entity_type, source_content_id, created_at);
CREATE INDEX idx_unified_relationships_composite ON unified_relationships(relationship_type, confidence_score, created_at);

-- Full-text search indexes
CREATE INDEX idx_unified_entities_name_fts ON unified_entities USING gin(to_tsvector('english', name));
```

## Advanced Usage Examples

### 1. Building a Learning Dashboard
```javascript
// Get comprehensive graph data
const graphData = await fetch('/api/unified-knowledge-graph/visual/full?limit=200&min_confidence=0.6');

// Get domain statistics
const stats = await fetch('/api/unified-knowledge-graph/stats');

// Identify knowledge gaps
const gaps = await fetch('/api/unified-knowledge-graph/analysis/gaps', {
  method: 'POST',
  body: JSON.stringify({
    analysis_depth: 'comprehensive',
    min_severity: 'medium'
  })
});
```

### 2. Personalized Learning Paths
```javascript
// Find learning path from basics to advanced topic
const paths = await fetch('/api/unified-knowledge-graph/paths/discover', {
  method: 'POST',
  body: JSON.stringify({
    start_entity_id: 'javascript-basics-uuid',
    end_entity_id: 'react-advanced-uuid',
    max_depth: 5,
    min_confidence: 0.7
  })
});

// Get relationship suggestions for current learning
const suggestions = await fetch('/api/unified-knowledge-graph/relationships/suggest', {
  method: 'POST', 
  body: JSON.stringify({
    entity_id: 'current-topic-uuid',
    limit: 5,
    min_confidence: 0.6
  })
});
```

### 3. Content Organization
```javascript
// Cluster related content
const clusters = await fetch('/api/unified-knowledge-graph/clustering/semantic', {
  method: 'POST',
  body: JSON.stringify({
    clustering_algorithm: 'hybrid',
    max_clusters: 8,
    min_cluster_size: 4,
    entity_types: ['text_entity', 'knowledge_concept']
  })
});

// Organize by domains and gaps
const analysis = await fetch('/api/unified-knowledge-graph/analysis/gaps', {
  method: 'POST',
  body: JSON.stringify({
    analysis_depth: 'standard',
    focus_domains: ['Technology', 'AI'],
    include_suggestions: true
  })
});
```

## Integration with Frontend

### D3.js Visualization Integration
The API provides D3.js-compatible node and edge formats:

```javascript
// Direct integration with D3.js force simulation
const simulation = d3.forceSimulation(graphData.nodes)
  .force('link', d3.forceLink(graphData.edges).id(d => d.id))
  .force('charge', d3.forceManyBody().strength(-300))
  .force('center', d3.forceCenter(width / 2, height / 2));
```

### Real-time Updates
Consider WebSocket integration for real-time graph updates:

```javascript
// WebSocket for real-time relationship updates
const ws = new WebSocket('ws://localhost:8000/ws/knowledge-graph');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.type === 'relationship_created') {
    // Update visualization
    updateGraph(update.relationship);
  }
};
```

## Future Enhancements

### Planned Features (v2.8+)
- **Vector Similarity Search**: Semantic search using embeddings
- **Temporal Analysis**: Time-based relationship evolution
- **Multi-modal Integration**: Image and video entity support
- **Collaborative Filtering**: User behavior-based recommendations
- **Graph Embeddings**: Node2Vec and Graph2Vec support

### Performance Optimizations
- **GraphQL Integration**: Flexible query capabilities
- **Batch Operations**: Bulk relationship creation/deletion
- **Streaming APIs**: Large dataset pagination
- **Distributed Computing**: Cluster analysis for massive graphs

## API Versioning

The Knowledge Graph API follows semantic versioning:
- **Major versions**: Breaking changes to core data models
- **Minor versions**: New endpoints and features
- **Patch versions**: Bug fixes and performance improvements

Current version: `2.7.0` (August 2025)

## Support and Troubleshooting

### Common Issues

**1. Slow clustering performance:**
- Reduce `max_clusters` and increase `min_cluster_size`
- Use `semantic` algorithm for better performance than `hybrid`
- Filter by `entity_types` to reduce dataset size

**2. Low-quality relationship suggestions:**
- Increase `min_confidence` threshold
- Specify `relationship_types` filter
- Review entity descriptions for better semantic matching

**3. Sparse knowledge graphs:**
- Lower `min_confidence` to include more relationships
- Use gap analysis to identify missing connections
- Review entity extraction quality

### Debug Endpoints

**Development Mode Only:**
```bash
# Get raw entity data
GET /api/unified-knowledge-graph/debug/entities

# Get relationship statistics
GET /api/unified-knowledge-graph/debug/relationship-stats

# Validate graph consistency
POST /api/unified-knowledge-graph/debug/validate
```

---

**Documentation Version:** 2.7.0  
**Last Updated:** 2025-08-01  
**Next Review:** 2025-09-01

For additional support, see:
- [Database Schema Documentation](/backend/docs/DATABASE_SCHEMA.md)
- [System Architecture Repository](/docs/SYSTEM_ARCHITECTURE_REPOSITORY.md)
- [API Integration Examples](/docs/API_EXAMPLES.md)