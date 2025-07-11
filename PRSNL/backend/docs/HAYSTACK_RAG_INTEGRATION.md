# Haystack v2 RAG Integration Guide

## Overview

PRSNL now includes advanced Retrieval-Augmented Generation (RAG) capabilities powered by Haystack v2. This system enables intelligent question-answering, semantic search, and knowledge retrieval across your entire knowledge base.

## Features

### 🔍 Core RAG Capabilities
- **Document Ingestion**: Automatic chunking and embedding of documents
- **Semantic Search**: Vector-based similarity search using sentence transformers
- **Question Answering**: LLM-powered answers with source citations
- **Hybrid Search**: Combines keyword and semantic search
- **Batch Processing**: Efficient bulk document ingestion

### 🏗️ Technical Architecture
- **Haystack v2**: Modern RAG framework with pipeline-based architecture
- **PGVector**: Vector database for production-scale document storage
- **Sentence Transformers**: Local embedding model (all-MiniLM-L6-v2)
- **Azure OpenAI**: LLM for answer generation
- **Guardrails-AI**: Output validation and quality assurance

## API Endpoints

### Document Management

#### POST `/api/rag/ingest`
Ingest a single document into the RAG system.

```json
{
  "content": "Your document content here...",
  "title": "Document Title",
  "source": "optional_source_identifier",
  "tags": ["tag1", "tag2"],
  "metadata": {
    "custom_field": "value"
  }
}
```

#### POST `/api/rag/ingest/batch`
Ingest multiple documents in a single request.

```json
{
  "documents": [
    {
      "content": "Document 1 content...",
      "title": "Doc 1"
    },
    {
      "content": "Document 2 content...",
      "title": "Doc 2"
    }
  ]
}
```

#### PUT `/api/rag/documents/{document_id}`
Update an existing document.

```json
{
  "content": "Updated content...",
  "metadata": {
    "updated": true
  }
}
```

#### DELETE `/api/rag/documents/{document_id}`
Remove a document from the RAG system.

### Query & Search

#### POST `/api/rag/query`
Ask questions about your knowledge base.

```json
{
  "question": "What are the key features of PRSNL?",
  "top_k": 5,
  "include_sources": true
}
```

Response:
```json
{
  "answer": "PRSNL is a comprehensive knowledge management system...",
  "confidence": 0.85,
  "sources": [
    {
      "content": "Document excerpt...",
      "metadata": {...},
      "score": 0.92
    }
  ]
}
```

#### POST `/api/rag/search/hybrid`
Perform hybrid search with adjustable weights.

```json
{
  "query": "search terms",
  "keyword_weight": 0.3,
  "semantic_weight": 0.7,
  "top_k": 10
}
```

### System Management

#### GET `/api/rag/stats`
Get RAG system statistics and configuration.

```json
{
  "enabled": true,
  "document_count": 1250,
  "document_store_type": "PgvectorDocumentStore",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "llm_model": "gpt-4"
}
```

#### GET `/api/rag/export?format=json`
Export the entire knowledge base.

## Configuration

### Environment Variables

```bash
# Required for RAG functionality
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=your-deployment-name

# Database with pgvector support
DATABASE_URL=postgresql://user:pass@localhost:5432/prsnl

# Optional: Embedding model configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

### Dependencies

Add to `requirements.txt`:
```
haystack-ai>=2.6.0
sentence-transformers>=2.2.2
qdrant-haystack>=5.0.0
pgvector-haystack>=0.4.0
```

## Database Schema

### Items Table Extensions
```sql
ALTER TABLE items 
ADD COLUMN rag_indexed BOOLEAN DEFAULT FALSE,
ADD COLUMN rag_doc_id VARCHAR(255),
ADD COLUMN rag_indexed_at TIMESTAMP;
```

### Haystack Documents Table
```sql
CREATE TABLE haystack_documents (
    id VARCHAR(255) PRIMARY KEY,
    content TEXT NOT NULL,
    content_hash VARCHAR(64),
    meta JSONB,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Query History Table
```sql
CREATE TABLE rag_query_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    query TEXT NOT NULL,
    answer TEXT,
    confidence FLOAT,
    documents_used INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage Examples

### Python Client

```python
import httpx
import asyncio

async def query_rag():
    async with httpx.AsyncClient() as client:
        # Ingest document
        doc_response = await client.post(
            "http://localhost:8000/api/rag/ingest",
            json={
                "content": "PRSNL is a powerful knowledge management system...",
                "title": "PRSNL Overview"
            }
        )
        
        # Query the system
        query_response = await client.post(
            "http://localhost:8000/api/rag/query",
            json={
                "question": "What is PRSNL?",
                "top_k": 3
            }
        )
        
        result = query_response.json()
        print(f"Answer: {result['answer']}")
        print(f"Confidence: {result['confidence']}")

asyncio.run(query_rag())
```

### JavaScript/Frontend

```javascript
// Ingest document
const ingestDocument = async (content, title) => {
  const response = await fetch('/api/rag/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, title })
  });
  return response.json();
};

// Query RAG system
const queryRAG = async (question) => {
  const response = await fetch('/api/rag/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      question, 
      top_k: 5,
      include_sources: true 
    })
  });
  return response.json();
};

// Usage
const result = await queryRAG("How does PRSNL handle AI validation?");
console.log(result.answer);
```

## Performance Considerations

### Indexing Performance
- **Batch ingestion** is more efficient than individual documents
- **Async processing** prevents blocking the main thread
- **Document chunking** optimizes retrieval accuracy

### Query Performance
- **Top-k limiting** reduces response time
- **Embedding caching** speeds up repeated queries
- **PGVector indexing** scales to millions of documents

### Resource Usage
- **Embedding model** runs on CPU by default
- **Memory usage** scales with document count
- **Disk storage** depends on document size and embedding dimension

## Quality Assurance

### Validation Pipeline
1. **Content preprocessing** removes noise and normalizes text
2. **Chunk quality** ensures meaningful semantic units
3. **Embedding validation** checks vector quality
4. **Answer validation** uses Guardrails-AI for structured outputs

### Monitoring
- **Query analytics** track usage patterns
- **Confidence scoring** measures answer quality
- **Source attribution** enables verification

## Integration with Existing Features

### Automatic Ingestion
```python
# Automatically ingest captured items
async def on_item_captured(item):
    if item.processed_content:
        await haystack_rag_service.ingest_document(
            content=item.processed_content,
            metadata={
                "item_id": item.id,
                "title": item.title,
                "url": item.url,
                "tags": item.tags
            },
            doc_id=f"item_{item.id}"
        )
```

### Enhanced Search
```python
# Combine traditional search with RAG
async def enhanced_search(query: str):
    # Traditional search
    traditional_results = await search_engine.search(query)
    
    # RAG search
    rag_results = await haystack_rag_service.hybrid_search(query)
    
    # Combine and rank results
    return merge_search_results(traditional_results, rag_results)
```

## Troubleshooting

### Common Issues

1. **Service not enabled**
   - Check Haystack dependencies installation
   - Verify Azure OpenAI credentials
   - Ensure pgvector extension is installed

2. **Low answer quality**
   - Increase `top_k` for more context
   - Improve document chunking strategy
   - Adjust embedding model for domain-specific content

3. **Slow performance**
   - Enable embedding caching
   - Use batch ingestion for bulk operations
   - Optimize database indexes

### Debug Commands

```bash
# Test RAG integration
python scripts/test_haystack_rag.py

# Check service status
curl http://localhost:8000/api/rag/stats

# View document count
curl http://localhost:8000/api/rag/export?format=json | jq '.count'
```

## Roadmap

### Phase 2 Enhancements
- **Multi-modal search** with OpenCLIP
- **RAGAS integration** for automated quality assessment
- **Firecrawl integration** for enhanced web content processing
- **Custom embedding models** for domain-specific applications

### Future Features
- **Conversational RAG** with chat history
- **Source verification** and fact-checking
- **Collaborative knowledge building**
- **Advanced analytics** and insights

## Best Practices

1. **Document Quality**: Ensure clean, well-structured content
2. **Metadata Usage**: Add rich metadata for better filtering
3. **Chunking Strategy**: Balance between context and granularity
4. **Query Optimization**: Use specific questions for better answers
5. **Regular Updates**: Keep documents current and relevant

This RAG integration transforms PRSNL from a simple capture tool into an intelligent knowledge assistant, enabling natural language interaction with your entire knowledge base.