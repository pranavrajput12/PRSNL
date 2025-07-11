# PRSNL v2.4 Deployment Guide

## Overview

This guide covers deploying PRSNL with the new enhanced search architecture, content fingerprinting, and normalized embeddings.

## Prerequisites

### System Requirements
- **Docker** (for containers) or **Rancher Desktop** (recommended for local development)
- **PostgreSQL 14+** with pgvector extension
- **Redis 6+** for caching
- **Node.js 24+** for frontend development
- **Python 3.11+** for backend

### Hardware Recommendations
- **RAM**: 8GB minimum, 16GB+ recommended (for embedding operations)
- **Storage**: SSD recommended for database performance
- **CPU**: 4+ cores for background processing

---

## Database Setup

### 1. PostgreSQL with pgvector
```bash
# Using Docker
docker run -d \
  --name prsnl-postgres \
  -e POSTGRES_DB=prsnl \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Or install pgvector on existing PostgreSQL
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### 2. Run Migrations
```bash
# From backend directory
cd backend

# Apply all migrations including v2.4 enhancements
psql -U postgres -d prsnl -f app/db/migrations/010_add_content_fingerprint_and_embed_vector_id.sql
psql -U postgres -d prsnl -f app/db/migrations/011_create_embeddings_table.sql

# Or use the unified schema (for fresh installs)
psql -U postgres -d prsnl -f app/db/schema_unified.sql
```

### 3. Verify Setup
```sql
-- Check extensions
SELECT * FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp');

-- Check new tables and fields
\d items
\d embeddings

-- Verify indexes
SELECT indexname FROM pg_indexes WHERE tablename IN ('items', 'embeddings');
```

---

## Backend Deployment

### 1. Environment Configuration
```bash
# .env file
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/prsnl
REDIS_URL=redis://localhost:6379

# AI Services
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01

# Monitoring (Optional)
SENTRY_DSN=your_sentry_dsn_here
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Server Configuration
PORT=8000
LOG_LEVEL=INFO
DEBUG=false
```

### 2. Docker Deployment
```bash
# Using docker-compose (recommended)
cd PRSNL
docker-compose up -d

# Or build and run manually
cd backend
docker build -t prsnl-backend .
docker run -d \
  --name prsnl-backend \
  -p 8000:8000 \
  --env-file .env \
  prsnl-backend
```

### 3. Manual Deployment
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
python -m app.db.migrate

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Frontend Deployment

### 1. Environment Configuration
```bash
# .env file (frontend)
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=production

# Sentry (Optional)
VITE_SENTRY_DSN=your_sentry_dsn_here
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 2. Build and Deploy
```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Preview build (optional)
npm run preview

# Deploy to static hosting
# Copy dist/ directory to your web server
```

### 3. Development Server
```bash
cd frontend

# Start development server
npm run dev -- --port 3004

# The app will be available at http://localhost:3004
```

---

## Post-Deployment Setup

### 1. Initial Data Migration
```bash
# Migrate existing embeddings to new architecture
curl -X POST http://localhost:8000/api/search/migrate-embeddings

# Generate content fingerprints for existing items
curl -X POST http://localhost:8000/api/search/update-embeddings

# Check system status
curl http://localhost:8000/api/search/stats
```

### 2. Health Checks
```bash
# Backend health
curl http://localhost:8000/api/health

# Database connectivity
curl http://localhost:8000/api/debug/db-test

# Search functionality
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "search_type": "hybrid", "limit": 5}'
```

### 3. Performance Optimization
```sql
-- Database optimization
ANALYZE items;
ANALYZE embeddings;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE tablename IN ('items', 'embeddings')
ORDER BY idx_scan DESC;

-- Update vector index statistics if needed
REINDEX INDEX idx_embeddings_vector;
```

---

## Configuration

### Backend Configuration
```python
# app/config.py key settings for v2.4

class Settings:
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/prsnl"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Search Configuration
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    SIMILARITY_THRESHOLD: float = 0.3
    
    # Content Fingerprinting
    ENABLE_FINGERPRINTING: bool = True
    FINGERPRINT_ALGORITHM: str = "sha256"
    
    # AI Services
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    
    # Performance
    MAX_CONCURRENT_EMBEDDINGS: int = 5
    EMBEDDING_BATCH_SIZE: int = 100
```

### Frontend Configuration
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [
    sveltekit(),
    // Sentry plugin (if enabled)
    sentrySvelteKit({
      sourceMapsUploadOptions: {
        org: process.env.SENTRY_ORG,
        project: process.env.SENTRY_PROJECT,
      },
    }),
  ],
  server: {
    port: 3004, // v2.4 standard port
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
```

---

## Monitoring and Maintenance

### 1. System Monitoring
```bash
# Check embedding coverage
curl http://localhost:8000/api/search/stats | jq '.embeddings'

# Monitor search performance
curl -w "@curl-format.txt" -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "search_type": "semantic"}'

# Database performance
psql -U postgres -d prsnl -c "
  SELECT 
    query, 
    calls, 
    total_time/1000 as total_time_sec,
    mean_time/1000 as mean_time_sec
  FROM pg_stat_statements 
  WHERE query LIKE '%embeddings%' 
  ORDER BY total_time DESC 
  LIMIT 10;
"
```

### 2. Regular Maintenance
```sql
-- Weekly maintenance (run via cron)

-- Update statistics
ANALYZE items;
ANALYZE embeddings;

-- Clean up orphaned embeddings
DELETE FROM embeddings 
WHERE item_id NOT IN (SELECT id FROM items);

-- Update content fingerprints for changed content
UPDATE items 
SET content_fingerprint = calculate_fingerprint(raw_content)
WHERE content_fingerprint IS NULL 
  AND raw_content IS NOT NULL;

-- Vacuum for performance
VACUUM ANALYZE items;
VACUUM ANALYZE embeddings;
```

### 3. Backup Strategy
```bash
# Database backup including vectors
pg_dump -U postgres -d prsnl \
  --format=custom \
  --compress=9 \
  --file=prsnl_backup_$(date +%Y%m%d).dump

# Restore
pg_restore -U postgres -d prsnl prsnl_backup_20240101.dump
```

---

## Troubleshooting

### Common Issues

#### 1. pgvector Extension Missing
```bash
# Error: extension "vector" is not available
# Solution: Install pgvector extension
sudo apt-get install postgresql-14-pgvector
# Or use pgvector/pgvector Docker image
```

#### 2. Slow Vector Searches
```sql
-- Check if vector index exists
SELECT indexname FROM pg_indexes WHERE indexname = 'idx_embeddings_vector';

-- Recreate index if missing
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (vector vector_cosine_ops);

-- Update statistics
ANALYZE embeddings;
```

#### 3. High Memory Usage
```python
# Reduce batch size in embedding operations
EMBEDDING_BATCH_SIZE = 50  # Down from 100

# Enable connection pooling
DATABASE_POOL_SIZE = 10
DATABASE_MAX_OVERFLOW = 20
```

#### 4. Frontend Build Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 24+

# Update dependencies
npm update
```

### Performance Tuning

#### Database Configuration
```sql
-- postgresql.conf optimizations for embeddings
shared_preload_libraries = 'pg_stat_statements'
max_connections = 100
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 64MB
maintenance_work_mem = 512MB

-- pgvector specific
ivfflat.probes = 10  # Adjust based on data size
```

#### Application Tuning
```python
# Async configuration
ASYNC_POOL_SIZE = 20
EMBEDDING_WORKERS = 4

# Caching
REDIS_CACHE_TTL = 3600  # 1 hour
QUERY_CACHE_SIZE = 1000
```

---

## Security Considerations

### 1. API Security
```python
# Enable rate limiting
RATE_LIMIT_ENABLED = True
RATE_LIMIT_REQUESTS = 100  # per minute

# API key validation (if needed)
API_KEY_REQUIRED = False  # Set to True for production
```

### 2. Database Security
```sql
-- Create read-only user for monitoring
CREATE USER prsnl_monitor WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE prsnl TO prsnl_monitor;
GRANT USAGE ON SCHEMA public TO prsnl_monitor;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO prsnl_monitor;
```

### 3. Content Security
```python
# Sanitize input content
CONTENT_MAX_LENGTH = 50000
ENABLE_CONTENT_FILTERING = True

# Embedding security
EMBEDDING_CONTENT_LIMIT = 2000  # Characters
```

---

## Production Checklist

### Pre-Deployment
- [ ] Database migrations applied
- [ ] pgvector extension installed
- [ ] Environment variables configured
- [ ] SSL certificates in place (if applicable)
- [ ] Monitoring tools configured

### Post-Deployment
- [ ] Health checks passing
- [ ] Search functionality verified
- [ ] Embedding migration completed
- [ ] Performance metrics baseline established
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured

### Ongoing Maintenance
- [ ] Weekly database maintenance
- [ ] Monthly performance review
- [ ] Quarterly dependency updates
- [ ] Semi-annual security audit

---

## Support and Updates

### Version Compatibility
- **Database**: PostgreSQL 14+ with pgvector
- **Backend**: Python 3.11+, FastAPI 0.109+
- **Frontend**: Node.js 24+, Svelte 5.35+
- **Dependencies**: See requirements.txt and package.json

### Update Procedure
1. Backup database and configurations
2. Test updates in staging environment
3. Apply database migrations
4. Deploy backend updates
5. Deploy frontend updates
6. Verify functionality
7. Update documentation

For additional support, refer to the system architecture documentation and API references.