# PRSNL Deployment Guide

**Version**: 10.0  
**Last Updated**: 2025-08-01  
**Target Environment**: Production and Development

## Overview

This guide covers deploying PRSNL Personal Knowledge Management System v10.0 with the complete Knowledge Graph System, Auto-Processing pipeline, and Cipher AI memory integration.

## 🚨 **New in v10.0 - Migration Requirements**

### **Knowledge Graph Extensions**
Version 10.0 introduces major database schema changes that require migration:

1. **6 New Tables**: unified_entities, unified_relationships, conversation_turns, video_segments, code_entities, timeline_events
2. **2 Materialized Views**: entity_statistics, relationship_statistics  
3. **25+ New Indexes**: Composite indexes for graph performance
4. **3 PostgreSQL Functions**: Entity creation and relationship management

### **Migration Scripts Required**
- `backend/migrations/008_knowledge_graph_extension.sql`
- `backend/migrations/009_add_materialized_view_unique_indexes.sql`

## Prerequisites

### System Requirements

**Development Environment:**
- **Node.js**: 20+ with npm latest
- **Python**: 3.11+ with pip 25.1.1
- **PostgreSQL**: 16+ with pgvector extension (ARM64 for M1/M2 Macs)
- **Memory**: 8GB+ RAM recommended
- **Storage**: 10GB+ free space

**Production Environment:**
- **Node.js**: 20+ (LTS)
- **Python**: 3.11+
- **PostgreSQL**: 16+ with pgvector
- **Redis/DragonflyDB**: For caching and queues
- **Memory**: 16GB+ RAM recommended
- **Storage**: 50GB+ free space
- **SSL Certificate**: For HTTPS endpoints

### Required Services

1. **PostgreSQL 16+ with pgvector**
   ```bash
   # ARM64 (M1/M2 Macs) - Use Homebrew ARM64
   /opt/homebrew/bin/brew install postgresql@16
   /opt/homebrew/bin/brew install pgvector
   
   # x86_64 Linux
   sudo apt install postgresql-16 postgresql-16-pgvector
   ```

2. **Azure OpenAI Service**
   - GPT-4 deployment for complex reasoning
   - GPT-4-mini deployment for fast responses  
   - text-embedding-ada-002 for vector embeddings
   - API key and endpoint URL

3. **DragonflyDB (Recommended) or Redis**
   ```bash
   # DragonflyDB (25x faster than Redis)
   docker run -d --name dragonflydb -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly
   
   # Or Redis
   brew install redis  # macOS
   sudo apt install redis-server  # Ubuntu
   ```

## Database Setup and Migration

### 🚨 **CRITICAL: Knowledge Graph Migration (v10.0)**

**Step 1: Backup Your Database**
```bash
pg_dump -U pronav -h localhost -p 5432 prsnl > prsnl_backup_pre_v10.sql
```

**Step 2: Apply Knowledge Graph Migrations**
```bash
cd backend

# Apply core knowledge graph extension
psql -U pronav -h localhost -p 5432 -d prsnl -f migrations/008_knowledge_graph_extension.sql

# Apply materialized view indexes
psql -U pronav -h localhost -p 5432 -d prsnl -f migrations/009_add_materialized_view_unique_indexes.sql

# Verify migration success
psql -U pronav -h localhost -p 5432 -d prsnl -c "SELECT COUNT(*) FROM unified_entities;"
psql -U pronav -h localhost -p 5432 -d prsnl -c "SELECT COUNT(*) FROM unified_relationships;"
```

**Step 3: Initialize Knowledge Graph (Optional)**
```bash
# Backfill existing content into knowledge graph
python3 backend/scripts/backfill_knowledge_graph.py

# Test entity extraction
python3 backend/scripts/standalone_entity_extraction.py
```

### Database Configuration

**Environment Variables (.env):**
```bash
# Database Configuration (LOCAL POSTGRESQL - NOT DOCKER)
DATABASE_URL=postgresql://pronav@localhost:5432/prsnl
DB_HOST=localhost
DB_PORT=5432
DB_USER=pronav
DB_NAME=prsnl

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-12-01-preview
AZURE_OPENAI_DEPLOYMENT=prsnl-gpt-4
AZURE_OPENAI_LIBRECHAT_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Cache Configuration
REDIS_URL=redis://localhost:6379
DRAGONFLYDB_URL=redis://localhost:6379

# Application Configuration
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["http://localhost:3004", "http://localhost:3003"]
```

### Verify Installation

**Database Health Check:**
```bash
# Test database connection
python3 -c "
import asyncpg
import asyncio

async def test_db():
    conn = await asyncpg.connect('postgresql://pronav@localhost:5432/prsnl')
    result = await conn.fetchval('SELECT COUNT(*) FROM items')
    print(f'Items count: {result}')
    
    # Test knowledge graph tables
    entities = await conn.fetchval('SELECT COUNT(*) FROM unified_entities')
    relationships = await conn.fetchval('SELECT COUNT(*) FROM unified_relationships')
    print(f'Knowledge Graph: {entities} entities, {relationships} relationships')
    
    await conn.close()

asyncio.run(test_db())
"
```

## Application Deployment

### Development Deployment

**1. Clone and Setup**
```bash
git clone https://github.com/pranavrajput12/PRSNL.git
cd PRSNL
```

**2. Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --port 8000
```

**3. Frontend Setup**
```bash
cd frontend
npm install

# Start development server (port 3004)
npm run dev -- --port 3004
```

**4. Verify Services**
```bash
# Backend health check
curl http://localhost:8000/health

# Knowledge graph health check
curl http://localhost:8000/api/unified-knowledge-graph/stats

# Auto-processing health check
curl http://localhost:8000/api/auto-processing/queue/status

# Frontend check
curl http://localhost:3004
```

### Production Deployment

**1. Environment Configuration**
```bash
# Production environment variables
NODE_ENV=production
PYTHONPATH=/app/backend
PORT=8000
FRONTEND_PORT=3003

# Security settings
SECURE_COOKIES=true
HTTPS_ONLY=true
CORS_ORIGINS=["https://your-domain.com"]

# Performance settings
WORKERS=4
MAX_CONNECTIONS=100
KEEP_ALIVE=65
```

**2. Docker Deployment (Recommended)**

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:v0.7.0
    environment:
      POSTGRES_DB: prsnl
      POSTGRES_USER: prsnl
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"

  dragonflydb:
    image: docker.dragonflydb.io/dragonflydb/dragonfly
    ports:
      - "6379:6379"
    command: dragonfly --logtostderr --maxmemory=2gb

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=postgresql://prsnl:${DB_PASSWORD}@postgres:5432/prsnl
      - REDIS_URL=redis://dragonflydb:6379
    depends_on:
      - postgres
      - dragonflydb
    ports:
      - "8000:8000"
    volumes:
      - ./backend/storage:/app/storage

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3003:3003"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
```

**3. SSL Configuration (nginx.conf)**
```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3003;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # API routes
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend routes
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**4. Deploy with Docker Compose**
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Cipher AI Memory Setup

### **Cipher Integration (v9.0+)**

**1. Install Cipher**
```bash
# Install Cipher CLI
pip install cipher-ai

# Configure Azure OpenAI integration  
./scripts/start-cipher.sh

# Test Cipher connection
cipher recall "PRSNL architecture"
```

**2. MCP Integration**
```bash
# Configure Claude Desktop MCP
# Edit ~/.claude/claude_desktop_config.json
{
    "mcpServers": {
        "cipher": {
            "command": "/path/to/PRSNL/scripts/cipher-mcp-wrapper.sh",
            "args": [],
            "env": {
                "OPENAI_API_KEY": "sk-cipher-azure-proxy",
                "OPENAI_BASE_URL": "http://localhost:8002/v1"
            }
        }
    }
}
```

**3. Automated Pattern Analysis**
```bash
# Setup weekly automated analysis
crontab -e

# Add this line for Sunday 2 AM analysis
0 2 * * 0 cd /path/to/PRSNL/scripts && ./cipher-pattern-analysis.sh

# Test pattern analysis
./scripts/cipher-pattern-analysis.sh --check
./scripts/cipher-analysis-status.sh
```

## Performance Optimization

### Database Optimization

**1. Index Optimization**
```sql
-- Monitor index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename IN ('unified_entities', 'unified_relationships', 'items');

-- Vacuum and analyze
VACUUM ANALYZE unified_entities;
VACUUM ANALYZE unified_relationships;
VACUUM ANALYZE items;

-- Refresh materialized views
REFRESH MATERIALIZED VIEW CONCURRENTLY entity_statistics;
REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_statistics;
```

**2. Connection Pool Configuration**
```python
# backend/app/core/database.py
DATABASE_POOL_CONFIG = {
    "min_size": 10,
    "max_size": 20,
    "max_queries": 50000,
    "max_inactive_connection_lifetime": 300,
    "timeout": 30,
    "command_timeout": 60
}
```

### Application Performance

**1. Redis/DragonflyDB Optimization**
```bash
# DragonflyDB configuration for production
docker run -d \
  --name dragonflydb \
  -p 6379:6379 \
  --memory="4g" \
  docker.dragonflydb.io/dragonflydb/dragonfly \
  dragonfly --logtostderr --maxmemory=3gb --proactor_threads=4
```

**2. Worker Process Configuration**
```bash
# Production backend startup
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --worker-connections 1000 \
  --max-requests 10000 \
  --max-requests-jitter 1000 \
  --timeout 120 \
  --keep-alive 65
```

## Monitoring and Logging

### Application Monitoring

**1. Health Check Endpoints**
```bash
# Comprehensive health checks
curl http://localhost:8000/health                                    # Basic health
curl http://localhost:8000/api/unified-knowledge-graph/stats         # Knowledge graph
curl http://localhost:8000/api/auto-processing/queue/status          # Processing queue
curl http://localhost:8000/api/ai/health                            # AI services
```

**2. Log Configuration**
```python
# backend/app/core/logging.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[{asctime}] {levelname} in {name}: {message}",
            "style": "{",
        },
        "json": {
            "format": '{"timestamp": "{asctime}", "level": "{levelname}", "logger": "{name}", "message": "{message}"}',
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/prsnl.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        }
    },
    "loggers": {
        "app": {
            "level": "INFO",
            "handlers": ["console", "file"],
        }
    }
}
```

### Database Monitoring

**PostgreSQL Performance Queries:**
```sql
-- Monitor slow queries
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;

-- Monitor knowledge graph table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE tablename IN ('unified_entities', 'unified_relationships', 'items')
ORDER BY size_bytes DESC;

-- Monitor index usage
SELECT 
    t.tablename,
    indexname,
    c.reltuples AS num_rows,
    pg_size_pretty(pg_relation_size(quote_ident(t.tablename)::text)) AS table_size,
    pg_size_pretty(pg_relation_size(quote_ident(indexrelname)::text)) AS index_size,
    CASE WHEN indisunique THEN 'Y' ELSE 'N' END AS UNIQUE,
    idx_scan as number_of_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_tables t
LEFT OUTER JOIN pg_class c ON c.relname=t.tablename
LEFT OUTER JOIN (
    SELECT c.relname AS ctablename, ipg.relname AS indexname, x.indnatts AS number_of_columns, idx_scan, idx_tup_read, idx_tup_fetch, indexrelname, indisunique FROM pg_index x
    JOIN pg_class c ON c.oid = x.indrelid
    JOIN pg_class ipg ON ipg.oid = x.indexrelid
    JOIN pg_stat_user_indexes psui ON x.indexrelid = psui.indexrelid )
    AS foo
    ON t.tablename = foo.ctablename
WHERE t.tablename IN ('unified_entities', 'unified_relationships', 'items')
ORDER BY 1,2;
```

## Backup and Recovery

### Database Backup Strategy

**1. Automated Backups**
```bash
#!/bin/bash
# backup-script.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="prsnl"

# Create backup directory
mkdir -p $BACKUP_DIR

# Full database backup
pg_dump -U pronav -h localhost -p 5432 $DB_NAME | gzip > $BACKUP_DIR/prsnl_full_$DATE.sql.gz

# Knowledge graph specific backup
pg_dump -U pronav -h localhost -p 5432 $DB_NAME \
  --table=unified_entities \
  --table=unified_relationships \
  --table=entity_statistics \
  --table=relationship_statistics \
  | gzip > $BACKUP_DIR/prsnl_knowledge_graph_$DATE.sql.gz

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "prsnl_*.sql.gz" -mtime +30 -delete

echo "Backup completed: prsnl_full_$DATE.sql.gz"
```

**2. Cipher Memory Backup**
```bash
# Backup Cipher memory database
cp ~/.cipher/memories.db $BACKUP_DIR/cipher_memories_$DATE.db

# Backup Cipher configuration
cp ~/.cipher/cipher.yml $BACKUP_DIR/cipher_config_$DATE.yml
```

### Recovery Procedures

**1. Database Recovery**
```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore database
gunzip -c /backups/prsnl_full_20250801_120000.sql.gz | psql -U pronav -h localhost -p 5432 prsnl

# Restart services
docker-compose -f docker-compose.prod.yml up -d

# Verify recovery
curl http://localhost:8000/api/unified-knowledge-graph/stats
```

**2. Knowledge Graph Recovery**
```bash
# Restore only knowledge graph tables
gunzip -c /backups/prsnl_knowledge_graph_20250801_120000.sql.gz | psql -U pronav -h localhost -p 5432 prsnl

# Refresh materialized views
psql -U pronav -h localhost -p 5432 prsnl -c "
REFRESH MATERIALIZED VIEW entity_statistics;
REFRESH MATERIALIZED VIEW relationship_statistics;
"

# Verify knowledge graph
python3 backend/test_entity_extraction_stats.py
```

## Security Configuration

### Production Security Checklist

**1. Environment Security**
```bash
# Secure .env file permissions
chmod 600 .env

# Use environment-specific secrets
export AZURE_OPENAI_API_KEY="$(cat /etc/secrets/azure_openai_key)"
export SECRET_KEY="$(cat /etc/secrets/app_secret_key)"
export DB_PASSWORD="$(cat /etc/secrets/db_password)"
```

**2. Database Security**
```sql
-- Create application-specific user
CREATE USER prsnl_app WITH PASSWORD 'secure_password';

-- Grant minimal required permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO prsnl_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO prsnl_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO prsnl_app;

-- Secure knowledge graph access
GRANT SELECT, INSERT, UPDATE, DELETE ON unified_entities TO prsnl_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON unified_relationships TO prsnl_app;
GRANT SELECT ON entity_statistics TO prsnl_app;
GRANT SELECT ON relationship_statistics TO prsnl_app;
```

**3. API Security**
```python
# backend/app/core/security.py
SECURITY_CONFIG = {
    "cors_origins": ["https://your-domain.com"],
    "cors_credentials": True,
    "cors_methods": ["GET", "POST", "PUT", "DELETE"],
    "cors_headers": ["*"],
    "jwt_secret_key": "your-super-secret-key",
    "jwt_algorithm": "HS256",
    "jwt_expire_minutes": 30,
    "rate_limit_requests": 1000,
    "rate_limit_window": 3600,  # 1 hour
}
```

## Troubleshooting

### Common Issues

**1. Knowledge Graph Migration Failures**
```bash
# Check if tables exist
psql -U pronav -h localhost -p 5432 prsnl -c "\dt unified_*"

# Check migration status
psql -U pronav -h localhost -p 5432 prsnl -c "SELECT * FROM schema_migrations WHERE version IN ('008', '009');"

# Manual rollback if needed
psql -U pronav -h localhost -p 5432 prsnl -c "
DROP TABLE IF EXISTS unified_relationships CASCADE;
DROP TABLE IF EXISTS unified_entities CASCADE;
DROP MATERIALIZED VIEW IF EXISTS entity_statistics;
DROP MATERIALIZED VIEW IF EXISTS relationship_statistics;
"
```

**2. Auto-Processing Queue Issues**
```bash
# Check queue status
curl http://localhost:8000/api/auto-processing/queue/status

# Clear stuck items
python3 -c "
import asyncio
from app.services.auto_processing_service import auto_processing_service

async def clear_queue():
    status = await auto_processing_service.get_queue_status()
    print(f'Queue status: {status}')
    
    # Clear stuck items older than 1 hour
    cleared = await auto_processing_service.clear_stuck_items(max_age_minutes=60)
    print(f'Cleared {cleared} stuck items')

asyncio.run(clear_queue())
"
```

**3. Cipher Integration Issues**
```bash
# Check Cipher proxy status
lsof -ti:8002 && echo "Cipher proxy running" || echo "Cipher proxy not running"

# Restart Cipher proxy
./scripts/start-cipher.sh

# Test Cipher connection
cipher recall "test" || echo "Cipher connection failed"

# Check MCP configuration
cat ~/.claude/claude_desktop_config.json | jq '.mcpServers.cipher'
```

### Performance Issues

**1. Slow Knowledge Graph Queries**
```sql
-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT ue.id, ue.name, COUNT(ur.id) as relationship_count
FROM unified_entities ue
LEFT JOIN unified_relationships ur ON (ue.id = ur.source_entity_id OR ue.id = ur.target_entity_id)
GROUP BY ue.id, ue.name
ORDER BY relationship_count DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename IN ('unified_entities', 'unified_relationships')
ORDER BY idx_scan DESC;
```

**2. Memory Usage Issues**
```bash
# Check PostgreSQL memory usage
psql -U pronav -h localhost -p 5432 prsnl -c "
SELECT setting, unit FROM pg_settings WHERE name IN (
    'shared_buffers', 'effective_cache_size', 'work_mem', 'maintenance_work_mem'
);
"

# Monitor Python memory usage
python3 -c "
import psutil
import os

process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')

# Check if backend is running
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    if 'uvicorn' in str(proc.info['cmdline']):
        print(f'Backend memory: {proc.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

## Support and Maintenance

### Maintenance Schedule

**Daily:**
- Monitor application logs
- Check system resource usage
- Verify backup completion

**Weekly:**
- Refresh materialized views
- Analyze slow queries
- Update security patches

**Monthly:**
- Full system backup verification
- Performance optimization review
- Dependency updates

### Getting Help

- **Documentation**: Check `/docs` directory for detailed guides
- **Issues**: Report problems via GitHub Issues
- **Logs**: Check application logs in `/logs` directory
- **Health Checks**: Use built-in health check endpoints

---

**Deployment Guide Version**: 10.0  
**Last Updated**: 2025-08-01  
**Next Review**: 2025-09-01