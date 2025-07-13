# PRSNL Architecture Documentation - Phase 3 Complete

## Overview

PRSNL is a modern personal knowledge management system that has evolved into an intelligent AI second brain. With Phase 3 complete, PRSNL now features AI-powered analysis and suggestions for autonomous knowledge curation and a LibreChat integration for conversational AI interactions, all powered by Azure OpenAI.

## System Architecture - Phase 3 AI Second Brain

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           User Interface Layer                             │
├────────────────┬──────────────────┬────────────────┬───────────────────┤
│  Web Browser   │  Chrome Extension │  LibreChat UI  │   iOS App (PRSNL) │
│  (Port 3004)   │    (Integrated)   │ (OpenAI Compat)│    (External)      │
└────────────────┴──────────────────┴────────────────┴───────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │     SvelteKit Frontend          │
                    │   (Port 3004, TypeScript)       │ 
                    │     Phase 3 AI Interface        │
                    └────────────────┬────────────────┘
                                     │ HTTP/WebSocket
                    ┌────────────────┴────────────────┐
                    │      FastAPI Backend            │
                    │    (Port 8000, Python)          │
                    │   uvloop Performance Boost      │
                    └────────────────┬────────────────┘
                                     │
        ┌────────────────────────────┴────────────────────────────┐
        │                 Multi-Agent AI Layer                     │
        ├─────────────┬──────────────┬─────────────┬─────────────┤
        │ AI Services │ LibreChat    │  Unified    │  Embedding  │
        │ (Analysis)  │  Bridge      │  AI Service │  Generator  │
        │ (Suggestions)│ (OpenAI API) │ (Azure)     │ (Semantic)  │
        └─────────────┴──────────────┴─────────────┴─────────────┘
                                     │
        ┌────────────────────────────┴────────────────────────────┐
        │              AI Agents & Intelligence                    │
        ├─────────────┬──────────────┬─────────────┬─────────────┤
        │ Knowledge   │ Research     │ Content     │ Learning    │
        │ Curator     │ Synthesizer  │ Explorer    │ Pathfinder  │
        │ (Analysis)  │ (Insights)   │ (Discovery) │ (Planning)  │
        └─────────────┴──────────────┴─────────────┴─────────────┘
                                     │
        ┌────────────────────────────┴────────────────────────────┐
        │                 Cloud AI Services                        │
        ├─────────────┬──────────────┬─────────────┬─────────────┤
        │ Azure OpenAI │ Function     │ Model       │ Streaming   │
        │ (prsnl-gpt-4)│ Calling      │ Optimization│ Responses   │
        │(gpt-4.1-mini)│ (Tools API)  │ (2 Models)  │ (Real-time) │
        └─────────────┴──────────────┴─────────────┴─────────────┘
                                     │
        ┌────────────────────────────┴────────────────────────────┐
        │              High-Performance Data Layer                 │
        ├─────────────────────┬──────────────┬────────────────────┤
        │  PostgreSQL 16      │ DragonflyDB  │   File Storage     │
        │  ARM64 + pgvector   │ (25x Redis)  │ (Videos/Thumbnails)│
        │  (Port 5433)        │ (Port 6379)  │   (Local/Cloud)    │
        └─────────────────────┴──────────────┴────────────────────┘
```

## Core Components

### Frontend (SvelteKit) - Phase 3 AI Interface
- **Technology**: SvelteKit 2.22.5, TypeScript, Tailwind CSS, TanStack Query v5
- **Port**: 3004 (development), 3003 (production container)
- **Key Features**:
  - Phase 3 AI-powered interface with intelligent features
  - Real-time AI agent status monitoring
  - LibreChat conversation interface
  - Progressive Web App capabilities with AI enhancements
  - Optimistic UI updates with background refetch
  - Responsive design (mobile-first)
  - Dark theme with Manchester United red accent
  - TanStack Query v5 for optimal state management

### iOS App (PRSNL APP)
- **Technology**: Native iOS application (Swift)
- **Status**: Separate codebase - *not yet integrated in this documentation*
- **Key Features**:
  - Native iOS experience
  - Share extension integration
  - Offline capabilities
  - Push notifications
  - Syncs with backend API

### Backend (FastAPI) - Phase 3 AI Engine
- **Technology**: FastAPI, Python 3.11, AsyncIO with uvloop (2-4x performance)
- **Port**: 8000 (local development)
- **Key Features**:
  - **AI Integration**: Intelligent analysis and suggestions
  - **LibreChat Bridge**: OpenAI-compatible API for chat interactions
  - **Azure OpenAI Integration**: Unified AI service with function calling
  - **High-Performance Async**: uvloop for enhanced async performance
  - **Multi-Model Support**: Optimized model selection (gpt-4.1-mini, prsnl-gpt-4)
  - Automatic API documentation with real-time updates
  - Type safety with Pydantic
  - Background task processing with AI workflows
  - WebSocket support for real-time AI interactions

### Database (PostgreSQL 16 ARM64) - High-Performance Knowledge Store
- **Version**: PostgreSQL 16 (ARM64 optimized)
- **Port**: 5433 (exclusive ARM64 installation)
- **Extensions**: pgvector for semantic search and AI embeddings
- **Key Features**:
  - **AI Context**: Persistent storage for AI context and learning
  - **Vector Search**: Semantic similarity search for knowledge discovery
  - **High Performance**: ARM64 optimization for Apple Silicon
  - **ACID Compliance**: Reliable data integrity for AI workflows
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

### DragonflyDB - Ultra-High Performance Cache
- **Technology**: DragonflyDB (25x faster than Redis)
- **Port**: 6379 (Docker container)
- **Key Features**:
  - **Memory Efficiency**: Superior memory utilization vs Redis
  - **Multi-threading**: Better CPU utilization
  - **Drop-in Replacement**: Redis protocol compatibility
  - **AI Caching**: Optimized for AI response caching and session storage

## Phase 3 AI Components

### AI Services - Intelligent Analysis System
- **Technology**: Custom multi-agent framework with Azure OpenAI integration
- **Purpose**: Autonomous knowledge curation and intelligent content processing
- **Architecture**:
  ```
  AI Service Integration
  ├── Knowledge Curator Agent
  │   ├── Content Analysis & Categorization
  │   ├── Tag Suggestion & Enhancement
  │   └── Quality Assessment & Improvement
  ├── Research Synthesizer Agent
  │   ├── Multi-source Information Synthesis
  │   ├── Pattern Recognition & Trend Analysis
  │   └── Insight Generation & Knowledge Gaps
  ├── Content Explorer Agent
  │   ├── Relationship Discovery & Mapping
  │   ├── Serendipitous Connection Finding
  │   └── Exploration Path Generation
  └── Learning Pathfinder Agent
      ├── Personalized Learning Sequence Creation
      ├── Progress Tracking & Adaptation
      └── Skill Development Planning
  ```

**API Endpoints**:
- `/api/ai-suggest` - AI-powered content analysis
- `/api/ai/chat/completions` - Conversational AI responses
- `/api/summarization/summarize/batch` - Content summarization
- `/api/ai/health` - AI service health monitoring

### LibreChat Integration - Conversational AI Bridge
- **Technology**: OpenAI-compatible API bridge with Azure OpenAI backend
- **Purpose**: Seamless chat interface with knowledge base integration
- **Features**:
  - **OpenAI API Compatibility**: Drop-in replacement for OpenAI API
  - **Knowledge Base Context**: Automatic integration of PRSNL knowledge
  - **Streaming Support**: Real-time response streaming
  - **Model Optimization**: Dedicated gpt-4.1-mini for fast responses

**API Endpoints**:
- `/api/ai/chat/completions` - OpenAI-compatible chat completions
- `/api/ai/models` - Available model listing
- `/api/ai/health` - LibreChat bridge health check

### Unified AI Service - Azure OpenAI Integration Layer
- **Technology**: Centralized Azure OpenAI service with dual-model optimization
- **Models**:
  - **prsnl-gpt-4**: Complex reasoning and AI workflows
  - **gpt-4.1-mini**: Fast responses and chat interactions (LibreChat)
- **Features**:
  - **Function Calling**: Full Azure OpenAI tools API support
  - **Model Routing**: Intelligent model selection based on use case
  - **Performance Optimization**: 5.5s LibreChat, 2-5s AI response times
  - **Caching & Context**: Efficient AI response management

## Performance Metrics - Phase 3

### Response Times (Verified Testing)
- **LibreChat (gpt-4.1-mini)**:
  - Regular completion: 5.5 seconds
  - Streaming completion: 4.0 seconds
- **AI Services (prsnl-gpt-4)**:
  - Learning path creation: 9.5 seconds
  - Multi-agent content processing: 10.5 seconds
  - Agent status check: <1 second

### Infrastructure Performance
- **DragonflyDB**: 25x faster than Redis for caching operations
- **PostgreSQL 16 ARM64**: Optimized for Apple Silicon M1/M2 architecture
- **uvloop**: 2-4x async performance boost for Python backend
- **TanStack Query v5**: Optimized frontend state management

### Model Optimization Strategy
- **Cost-Effective**: gpt-4.1-mini for frequent chat operations
- **High-Intelligence**: prsnl-gpt-4 for complex multi-agent reasoning
- **Function Calling**: Full Azure OpenAI tools API compatibility
- **Streaming**: Real-time response delivery for both models

## Service Architecture

### Legacy Service Architecture (Pre-Phase 3)
*Note: The following services have been superseded by the Phase 3 AI architecture above*

### AI Router Service (SUPERSEDED by Unified AI Service)
Intelligently routes AI tasks to the most appropriate provider:
- **Providers**: Azure OpenAI (cloud)
- **Status**: ⚠️ **Superseded by Unified AI Service with AI integration**

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
  - Frontend (Local) - Port 3003
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

