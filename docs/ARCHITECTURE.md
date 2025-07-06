# PRSNL Architecture Framework - Local-First Edition

## System Overview

PRSNL is a keyboard-first, zero-friction personal knowledge management system designed for LOCAL deployment with ZERO recurring costs. Everything runs on your machine.

## Current Implementation Status (Updated 2025-01-06)

✅ **COMPLETED COMPONENTS**
- Frontend UI with Manchester United red design (#dc143c)
- Chrome Extension with options page and keyboard shortcuts
- Sample data system with 25 realistic items
- Settings management and configuration
- Development environment with Docker

🚧 **IN DEVELOPMENT**
- Backend API integration
- Real-time search functionality
- Database seeding with actual content

## Architecture Principles

1. **Local-Only**: Everything runs on your machine, no cloud dependencies
2. **Keyboard-Centric**: Maximum 4 keystrokes to any action (⌘N, ⌘K, ⌘T, ⌘H)
3. **Cost-Optimized**: Free tier friendly, no vendor lock-in
4. **Performance-First**: Sub-second search on 100k items
5. **Privacy-Focused**: All data stays on your machine, never leaves
6. **Design-First**: Manchester United red (#dc143c) with Mulish + Poppins fonts

## System Components

### 1. Data Ingestion Layer
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ Browser Extension │     │ Email Gateway│     │  RSS Poller │
└────────┬────────┘     └──────┬───────┘     └──────┬──────┘
         │                     │                      │
         └─────────────────────┴──────────────────────┘
                               │
                        ┌──────▼──────┐
                        │  Capture API │
                        │  (FastAPI)   │
                        └──────┬──────┘
                               │
                        ┌──────▼──────┐
                        │ Task Queue  │
                        │ (PostgreSQL │
                        │LISTEN/NOTIFY)│
                        └─────────────┘
```

### 2. Processing Pipeline
```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Stage 1: Scrape │────▶│ Stage 2: Enrich │────▶│ Stage 3: Index│
├─────────────────┤     ├─────────────────┤     ├──────────────┤
│ • BeautifulSoup │     │ • Ollama (local)│     │ • Full-text  │
│ • Readability   │     │ • Azure OpenAI  │     │ • Metadata   │
│ • OCR (if PDF)  │     │ • Auto-tagging  │     │ • Search idx │
└─────────────────┘     └─────────────────┘     └──────────────┘
```

### 3. Storage Architecture
```
┌─────────────────────────────────────────────┐
│              PostgreSQL                      │
├─────────────────────────────────────────────┤
│ • Metadata (items table)                    │
│ • Full-text search (tsvector)               │
│ • Tags & relationships                      │
└─────────────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────┐
│           Object Storage                     │
├─────────────────────────────────────────────┤
│ • Local: File system (/vault/blobs/)        │
│ • Cloud: NOT USED (local only)              │
│ • Structure: /YYYY/MM/DD/{uuid}/            │
└─────────────────────────────────────────────┘
```

### 4. Search Architecture
```
User Query
    │
    ▼
┌─────────────────┐
│ Search Orchestrator │
└─────┬───────────┘
      │
      ├──────────────┬──────────────┐
      ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Keyword  │  │ Recency  │  │  Filters │
│  (FTS)   │  │  Boost   │  │  (tags)  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┴─────────────┘
                         │
                   ┌─────▼─────┐
                   │ Re-ranker │
                   │ (Optional) │
                   └─────┬─────┘
                         │
                   ┌─────▼─────┐
                   │  Results   │
                   └───────────┘
```

### 5. User Interfaces
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────┐
│ Global Overlay  │     │  Web Dashboard  │     │   Browser   │
│  (Native App)   │     │   (SvelteKit)   │     │  Extension  │
├─────────────────┤     ├─────────────────┤     ├─────────────┤
│ • Hotkey capture│     │ • Hidden route  │     │ • Manifest V3│
│ • Fuzzy search │     │ • Command palette│     │ • One-click  │
│ • Quick preview│     │ • Minimal UI    │     │ • Highlight  │
└────────┬────────┘     └────────┬────────┘     └──────┬──────┘
         │                       │                      │
         └───────────────────────┴──────────────────────┘
                                 │
                          ┌──────▼──────┐
                          │   REST API  │
                          │  (FastAPI)  │
                          └─────────────┘
```

## Database Schema

### Core Tables

```sql
-- Main items table
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    src_type VARCHAR(20) NOT NULL, -- 'web', 'github', 'twitter', etc
    src_id TEXT NOT NULL, -- unique identifier within source
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    content_hash TEXT, -- for deduplication
    raw_content TEXT, -- cached for re-processing
    processed_content TEXT, -- cleaned/structured
    search_vector tsvector, -- full-text search
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    accessed_at TIMESTAMPTZ DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    UNIQUE(src_type, src_id)
);

-- Tags with hierarchy
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    parent_id UUID REFERENCES tags(id),
    aliases TEXT[] DEFAULT '{}',
    color VARCHAR(7),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Many-to-many relationship
CREATE TABLE item_tags (
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 1.0, -- for ML-suggested tags
    PRIMARY KEY (item_id, tag_id)
);

-- Performance indexes
CREATE INDEX idx_items_search ON items USING GIN(search_vector);
CREATE INDEX idx_items_created ON items(created_at DESC);
CREATE INDEX idx_items_accessed ON items(accessed_at DESC);
CREATE INDEX idx_items_src ON items(src_type, created_at DESC);
```

## API Structure

### RESTful Endpoints

```yaml
# Capture
POST   /api/capture
  body: { url, highlight?, tags? }
  response: { id, status: 'queued' }

# Search
GET    /api/search?q={query}&filters={...}&limit=20
  response: { results: [...], total, took_ms }

# Items
GET    /api/items/{id}
GET    /api/items/{id}/content  # full content
PATCH  /api/items/{id}
DELETE /api/items/{id}

# Tags
GET    /api/tags
POST   /api/tags
PATCH  /api/tags/{id}

# Export
POST   /api/export
  body: { format: 'markdown'|'csv', filters? }
  response: { job_id }

GET    /api/export/{job_id}/status
GET    /api/export/{job_id}/download

# System
GET    /api/health
GET    /api/stats  # item count, storage used, etc
```

## Deployment Architecture

### Local Docker Compose (Primary Deployment)
```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
  
  app:
    build: .
    depends_on:
      - postgres
    volumes:
      - ./data/blobs:/app/storage
    ports:
      - "8000:8000"
  
  worker:
    build: .
    command: python -m app.worker
    depends_on:
      - postgres
  
  ollama:
    image: ollama/ollama
    volumes:
      - ./data/ollama:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]  # optional
```

### Optional: VPS Deployment (if you want remote access)
```nginx
# Nginx config
server {
    listen 443 ssl http2;
    server_name vault.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/vault.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vault.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/search {
        proxy_pass http://localhost:8000;
        proxy_read_timeout 5s;
        proxy_cache search_cache;
        proxy_cache_valid 200 1m;
    }
}
```

## Security Considerations

### 1. Data Encryption
- **At Rest**: PostgreSQL TDE or filesystem encryption
- **Blob Storage**: AES-256-GCM per-file encryption
- **In Transit**: TLS 1.3 minimum
- **Backups**: Encrypted before upload to cloud

### 2. Authentication
- **OAuth 2.0**: Google as sole provider initially
- **Session Management**: Redis-backed, 24h expiry
- **API Keys**: For browser extension, rotatable

### 3. Rate Limiting
```python
# Per-endpoint limits
/api/capture: 100/minute
/api/search: 300/minute
/api/export: 5/hour
```

## Performance Optimizations

### 1. Caching Strategy
- **Search Results**: 60s cache for identical queries
- **Processed Content**: Indefinite cache, invalidate on edit
- **Embeddings**: Pre-computed for frequent queries
- **Static Assets**: CDN or nginx cache

### 2. Query Optimization
- **Parallel Search**: Keyword + vector queries run concurrently
- **Progressive Results**: Stream results as available
- **Query Planning**: Analyze and optimize based on filters
- **Connection Pooling**: PgBouncer for PostgreSQL

### 3. Resource Management
- **Worker Scaling**: Auto-scale Celery workers based on queue depth
- **Memory Limits**: 512MB per worker, spill to disk
- **Storage Quotas**: Configurable per-user limits
- **LLM Throttling**: Circuit breaker for API failures

## Monitoring & Observability

### 1. Metrics (Prometheus format)
```
vault_capture_duration_seconds{status="success|failure"}
vault_search_duration_seconds{type="keyword|vector|hybrid"}
vault_items_total
vault_storage_bytes_used
vault_llm_tokens_used{provider="ollama|azure_openai"}
```

### 2. Logging
- **Application**: Structured JSON to stdout
- **Access**: Nginx/Caddy access logs
- **Errors**: Sentry or self-hosted Glitchtip

### 3. Health Checks
```python
GET /api/health
{
  "status": "healthy",
  "checks": {
    "database": "ok",
 
    "storage": "ok",
    "llm": "ok"
  },
  "version": "1.0.0"
}
```

## Development Workflow

### 1. Local Development
```bash
# Start services
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload

# Start worker
python -m app.worker

# Start frontend
cd frontend && npm run dev
```

### 2. Testing Strategy
- **Unit Tests**: pytest for Python, Vitest for frontend
- **Integration Tests**: Test containers for external services
- **E2E Tests**: Playwright for critical user flows
- **Load Tests**: k6 or Locust for performance validation

### 3. CI/CD Pipeline
```yaml
# GitHub Actions
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    - Run linters (ruff, prettier)
    - Run unit tests
    - Run integration tests
    - Build Docker images
    
  deploy:
    if: github.ref == 'refs/heads/main'
    - Push to registry
    - Deploy to VPS via SSH
    - Run migrations
    - Health check
```

## Cost Analysis (Local-Only)

### Recurring Costs: $0/month
- **Hosting**: Your computer (already owned)
- **Database**: PostgreSQL (free, open source)
- **LLM**: Ollama + Llama 3 (free, runs locally)
- **Storage**: Your hard drive (already owned)
- **All services**: Docker containers (free)

### One-time Costs:
- **Azure OpenAI credits**: Already available (fallback only)
- **Development time**: Your time investment

### Optional Future Costs (if you want):
- **Domain**: $10-15/year (for web access)
- **VPS**: $5-10/month (for 24/7 cloud access)
- **Backup**: $6/month (for offsite backup)

## Future Considerations (Post-MVP)

1. **Multi-User**: JWT auth, row-level security
2. **Mobile Apps**: React Native with shared business logic
3. **Federation**: Sync between multiple instances
4. **Plugins**: User-defined parsers and processors
5. **Analytics**: Usage patterns and insights