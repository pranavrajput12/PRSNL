# PRSNL Architecture Documentation

## Overview

PRSNL is a modern personal knowledge management system built with a microservices architecture, emphasizing AI-powered content processing and intelligent search capabilities.

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              User Interface Layer                          │
├────────────────┬──────────────────┬────────────────┬───────────────────┤
│  Web Browser   │  Chrome Extension │  API Clients   │   Mobile (Future) │
└────────────────┴──────────────────┴────────────────┴───────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │     SvelteKit Frontend          │
                    │   (Port 3002, TypeScript)       │
                    └────────────────┬────────────────┘
                                     │ HTTP/WebSocket
                    ┌────────────────┴────────────────┐
                    │      FastAPI Backend            │
                    │    (Port 8000, Python)          │
                    └────────────────┬────────────────┘
                                     │
        ┌────────────────────────────┴────────────────────────────┐
        │                    Service Layer                         │
        ├─────────────┬──────────────┬─────────────┬─────────────┤
        │  AI Router  │ Video Proc.  │  Scraper    │  Storage    │
        │  Service    │  Service     │  Service    │  Manager    │
        └─────────────┴──────────────┴─────────────┴─────────────┘
                                     │
        ┌────────────────────────────┴────────────────────────────┐
        │                    AI/ML Layer                           │
        ├─────────────┬──────────────┬─────────────┬─────────────┤
        │ Azure OpenAI │  Whisper    │ Embeddings  │
        │   (Cloud)    │   (ASR)     │  Service    │
        └─────────────┴──────────────┴─────────────┴─────────────┘
                                     │
        ┌────────────────────────────┴────────────────────────────┐
        │                   Data Layer                             │
        ├─────────────────────┬───────────────────────────────────┤
        │    PostgreSQL       │        File Storage               │
        │   + pgvector        │    (Videos, Thumbnails)           │
        └─────────────────────┴───────────────────────────────────┘
```

## Core Components

### Frontend (SvelteKit)
- **Technology**: SvelteKit, TypeScript, Tailwind CSS
- **Key Features**:
  - Reactive UI with real-time updates
  - Progressive Web App capabilities
  - Optimistic UI updates
  - Responsive design (mobile-first)
  - Dark theme with Manchester United red accent

### Backend (FastAPI)
- **Technology**: FastAPI, Python 3.11, AsyncIO
- **Key Features**:
  - Async request handling
  - Automatic API documentation
  - Type safety with Pydantic
  - Background task processing
  - WebSocket support (upcoming)

### Database (PostgreSQL)
- **Extensions**: pgvector for semantic search
- **Schema**:
  ```sql
  items (
    id UUID PRIMARY KEY,
    title TEXT,
    summary TEXT,
    content TEXT,
    embedding VECTOR(1536),
    status VARCHAR,
    created_at TIMESTAMP
  )
  
  tags (
    id UUID PRIMARY KEY,
    name VARCHAR UNIQUE
  )
  
  item_tags (
    item_id UUID REFERENCES items,
    tag_id UUID REFERENCES tags
  )
  ```

## Service Architecture

### AI Router Service
Intelligently routes AI tasks to the most appropriate provider:
- **Providers**: Azure OpenAI (cloud)
- **Features**:
  - Cost optimization
  - Automatic fallback
  - Load balancing
  - Performance tracking

### Video Processor Service
Handles video download and processing:
- **Supported Platforms**: YouTube, Instagram, Twitter, TikTok
- **Features**:
  - Thumbnail generation
  - Metadata extraction
  - Format conversion
  - Progress tracking

### Embedding Service
Generates and manages vector embeddings:
- **Models**: OpenAI text-embedding-ada-002, Azure OpenAI embeddings
- **Features**:
  - Batch processing
  - Caching
  - Dimension reduction
  - Index optimization

### LLM Processor
Processes content with Large Language Models:
- **Tasks**:
  - Summarization
  - Tag extraction
  - Content cleaning
  - Knowledge extraction
- **Streaming Support**:
  - Real-time response streaming
  - WebSocket integration
  - Multi-provider streaming

### Vision Processor Service
Analyzes images and screenshots:
- **Providers**: Azure OpenAI GPT-4V, Tesseract OCR
- **Features**:
  - Text extraction (OCR)
  - Object detection
  - Scene description
  - UI element recognition

### Analytics Service
Provides insights into knowledge base:
- **Endpoints**:
  - Content trends over time
  - Topic clustering
  - Usage patterns
  - AI-generated insights
- **Features**:
  - Real-time analytics
  - Historical data analysis
  - Pattern recognition

## Data Flow

### Capture Flow
```
User Input → API Endpoint → Background Task
                                ↓
                         Content Scraping
                                ↓
                         AI Processing
                                ↓
                         Embedding Generation
                                ↓
                         Database Storage
                                ↓
                         Search Index Update
```

### Search Flow
```
Search Query → API Endpoint → Query Parser
                                  ↓
                    ┌─────────────┴─────────────┐
                    │                           │
              Full-Text Search          Semantic Search
                    │                           │
                    └─────────────┬─────────────┘
                                  ↓
                            Result Ranking
                                  ↓
                            Response Format
```

## Security Architecture

### Authentication & Authorization
- Session-based authentication
- API key authentication for extensions
- Role-based access control (future)

### Data Protection
- All data stored locally
- Encrypted storage for sensitive data
- No external data transmission without consent
- Secure WebSocket connections

### Input Validation
- Pydantic models for request validation
- SQL injection prevention
- XSS protection
- Rate limiting

## Performance Optimization

### Caching Strategy
- Redis for session management (future)
- In-memory caching for embeddings
- Browser caching for static assets
- Database query result caching

### Async Processing
- Background tasks for heavy operations
- Async database queries
- Concurrent API calls
- Stream processing for large files

### Database Optimization
- Indexed columns for fast search
- Materialized views for analytics
- Connection pooling
- Query optimization

## Monitoring & Observability

### Metrics Collection
- Prometheus metrics
- Custom business metrics
- Performance tracking
- Error rate monitoring

### Logging
- Structured logging with context
- Log aggregation (ELK stack)
- Error tracking
- Audit trails

### Health Checks
- Service health endpoints
- Database connectivity
- External service availability
- Storage capacity monitoring

## Deployment Architecture

### Development
```yaml
services:
  - PostgreSQL (Docker) - Port 5432
  - Backend (Local) - Port 8000
  - Frontend (Local) - Port 3002
```

**Note**: See `/PRSNL/PORT_ALLOCATION.md` for complete port assignments and conflict prevention.

### Production
```yaml
services:
  - PostgreSQL (Managed/Docker)
  - Backend (Docker + Gunicorn)
  - Frontend (Docker + Nginx)
  - Redis (Caching)
  - Monitoring Stack
```

## Scalability Considerations

### Horizontal Scaling
- Stateless backend services
- Load balancer ready
- Distributed task queue (Celery)
- Read replicas for database

### Vertical Scaling
- Async processing for CPU-intensive tasks
- GPU acceleration for AI models
- Memory optimization for embeddings
- Connection pooling

## Future Architecture Plans

### Planned Enhancements
1. **Real-time Collaboration**
   - WebRTC for live sharing
   - Operational Transformation for concurrent edits

2. **Mobile Architecture**
   - React Native app
   - Offline-first with sync
   - Progressive Web App

3. **Plugin System**
   - Extension API
   - Custom processors
   - Third-party integrations

4. **Advanced AI Features**
   - Custom fine-tuned models
   - Multi-modal search
   - Automatic knowledge graph generation

## Technology Decisions

### Why SvelteKit?
- Excellent performance
- Small bundle size
- Built-in SSR/SSG
- Great developer experience

### Why FastAPI?
- Native async support
- Automatic API documentation
- Type safety
- High performance

### Why PostgreSQL?
- pgvector for embeddings
- Full-text search capabilities
- ACID compliance
- Proven reliability

