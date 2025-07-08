# Docker Desktop to Rancher Desktop Migration Guide

## Overview
This guide documents the complete migration process from Docker Desktop to Rancher Desktop, including all issues encountered, solutions applied, and best practices learned from migrating the PRSNL project.

## Table of Contents
1. [Pre-Migration Checklist](#pre-migration-checklist)
2. [Common Issues and Solutions](#common-issues-and-solutions)
3. [Step-by-Step Migration Process](#step-by-step-migration-process)
4. [Best Practices](#best-practices)
5. [Troubleshooting Reference](#troubleshooting-reference)
6. [Post-Migration Validation](#post-migration-validation)

## Pre-Migration Checklist

Before starting the migration, ensure you have:

- [ ] Backed up all Docker volumes and important data
- [ ] Documented all running containers and their configurations
- [ ] Listed all port mappings currently in use
- [ ] Saved any custom Docker networks
- [ ] Exported environment variables and secrets
- [ ] Noted Docker Desktop-specific features in use

## Common Issues and Solutions

### 1. Container Networking Issues

**Problem**: Frontend container cannot connect to backend using `localhost` or `::1`
```
Error: connect ECONNREFUSED ::1:8001
```

**Root Cause**: Rancher Desktop handles container networking differently than Docker Desktop

**Solution**: 
- Use container service names instead of localhost
- Add an nginx reverse proxy for external access
- Update environment variables to use internal container names

```yaml
# Before (Docker Desktop)
frontend:
  environment:
    PUBLIC_API_URL: http://localhost:8001

# After (Rancher Desktop)
frontend:
  environment:
    PUBLIC_API_URL: http://backend:8000
```

### 2. Port Conflicts

**Problem**: Services fail to start due to port already in use
```
Error: bind: address already in use
```

**Solution**:
- Map to different host ports
- Use a dedicated docker-compose file for Rancher

```yaml
# docker-compose-rancher.yml
services:
  postgres:
    ports:
      - "5433:5432"  # Changed from 5432:5432
  redis:
    ports:
      - "6380:6379"  # Changed from 6379:6379
```

### 3. Volume Mount Issues

**Problem**: Volumes not persisting or permission errors

**Solution**:
- Use named volumes instead of bind mounts where possible
- For bind mounts on macOS, use delegated mode for performance

```yaml
volumes:
  # Named volume (preferred)
  postgres_data:
  
  # Bind mount with delegated mode
  - ./backend:/app:delegated
```

### 4. Database Connection Failures

**Problem**: Backend cannot connect to PostgreSQL
```
connection to server at "postgres" (172.x.x.x), port 5432 failed
```

**Solution**:
- Ensure health checks are properly configured
- Use depends_on with condition checks
- Verify connection strings use service names

```yaml
backend:
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
```

### 5. Build Context Issues

**Problem**: Docker build fails or doesn't pick up changes

**Solution**:
- Always rebuild with --no-cache when debugging
- Remove containers completely before rebuilding
- Use explicit build context paths

```bash
# Complete rebuild
docker-compose -f docker-compose-rancher.yml down -v
docker-compose -f docker-compose-rancher.yml build --no-cache
docker-compose -f docker-compose-rancher.yml up -d
```

## Step-by-Step Migration Process

### Step 1: Install and Configure Rancher Desktop

```bash
# 1. Download and install Rancher Desktop
# Visit: https://rancherdesktop.io/

# 2. Configure Rancher Desktop settings
# - Container Runtime: dockerd (moby)
# - Kubernetes: Disable if not needed
# - Resources: Allocate appropriate CPU/Memory

# 3. Switch Docker context
docker context ls
docker context use rancher-desktop
```

### Step 2: Create Rancher-Specific Docker Compose

Create `docker-compose-rancher.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-myapp}
    ports:
      - "5433:5432"  # Use different port to avoid conflicts
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"  # Use different port to avoid conflicts
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/myapp
      REDIS_URL: redis://redis:6379
      # Add other environment variables
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app:delegated
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  # Frontend Application
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      # Use backend service name, not localhost
      PUBLIC_API_URL: http://backend:8000
      NODE_ENV: development
    ports:
      - "3002:3000"  # Map to different port if needed
    depends_on:
      - backend
    volumes:
      - ./frontend:/app:delegated
      - /app/node_modules  # Prevent node_modules overlap

  # Nginx Proxy (for external access)
  nginx:
    image: nginx:alpine
    ports:
      - "8001:8001"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: myapp_network
```

### Step 3: Create Nginx Configuration

Create `nginx.conf`:

```nginx
server {
    listen 8001;
    
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Step 4: Update Application Configuration

#### Backend Updates

1. **Database connections**: Use service names
```python
# settings.py or config.py
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@postgres:5432/myapp"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
```

2. **CORS settings**: Allow frontend container
```python
BACKEND_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3002",
    "http://frontend:3000",
    # Add your domains
]
```

#### Frontend Updates

1. **API URLs**: Use environment variables
```javascript
// Use PUBLIC_API_URL from environment
const API_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8001';

// For server-side rendering, use internal URL
const SSR_API_URL = process.env.NODE_ENV === 'production' 
  ? 'http://backend:8000' 
  : 'http://localhost:8001';
```

2. **Update proxy configuration** (if using Vite/Webpack):
```javascript
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: process.env.PUBLIC_API_URL || 'http://localhost:8001',
        changeOrigin: true,
      }
    }
  }
}
```

### Step 5: Migration Execution

```bash
# 1. Stop Docker Desktop containers
docker-compose down

# 2. Switch to Rancher Desktop context
docker context use rancher-desktop

# 3. Build and start services
docker-compose -f docker-compose-rancher.yml build
docker-compose -f docker-compose-rancher.yml up -d

# 4. Check service health
docker-compose -f docker-compose-rancher.yml ps
docker-compose -f docker-compose-rancher.yml logs --tail=50

# 5. Run database migrations (if needed)
docker-compose -f docker-compose-rancher.yml exec backend python manage.py migrate
```

## Best Practices

### 1. Environment Management

```bash
# Create .env.rancher for Rancher-specific variables
cp .env .env.rancher

# Use env_file in docker-compose
services:
  backend:
    env_file:
      - .env.rancher
```

### 2. Health Checks

Always implement health checks for critical services:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 3. Resource Limits

Set appropriate resource limits:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 4. Logging Configuration

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 5. Multi-Stage Builds

Use multi-stage builds for production:

```dockerfile
# Frontend Dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/build ./build
COPY package*.json ./
EXPOSE 3000
CMD ["node", "build"]
```

## Troubleshooting Reference

### Debug Commands

```bash
# Check container networking
docker network ls
docker network inspect myapp_network

# Check container details
docker inspect <container_name>

# Test internal connectivity
docker-compose -f docker-compose-rancher.yml exec frontend ping backend
docker-compose -f docker-compose-rancher.yml exec backend curl http://frontend:3000

# Check port bindings
docker-compose -f docker-compose-rancher.yml ps
netstat -an | grep LISTEN | grep <port>

# Force rebuild
docker-compose -f docker-compose-rancher.yml down
docker-compose -f docker-compose-rancher.yml build --no-cache
docker-compose -f docker-compose-rancher.yml up -d

# Clean everything
docker system prune -a --volumes
```

### Common Error Messages and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `connect ECONNREFUSED ::1:8001` | Using localhost in container | Use service names |
| `bind: address already in use` | Port conflict | Change port mapping |
| `no such host` | DNS resolution failure | Check service names |
| `connection refused` | Service not ready | Add health checks |
| `permission denied` | Volume permissions | Check user/group IDs |
| `cannot find module` | Node modules issue | Rebuild with clean volumes |

## Post-Migration Validation

### 1. Service Connectivity Tests

```bash
# Test database connection
docker-compose -f docker-compose-rancher.yml exec backend \
  psql $DATABASE_URL -c "SELECT 1"

# Test Redis connection
docker-compose -f docker-compose-rancher.yml exec backend \
  redis-cli -u $REDIS_URL ping

# Test API endpoints
curl http://localhost:8001/health
curl http://localhost:3002/
```

### 2. Performance Validation

```bash
# Monitor resource usage
docker stats

# Check response times
time curl http://localhost:8001/api/endpoint

# Monitor logs for errors
docker-compose -f docker-compose-rancher.yml logs -f --tail=100
```

### 3. Data Integrity Checks

```bash
# Verify database data
docker-compose -f docker-compose-rancher.yml exec postgres \
  psql -U postgres -d myapp -c "SELECT COUNT(*) FROM your_table"

# Check volume persistence
docker-compose -f docker-compose-rancher.yml down
docker-compose -f docker-compose-rancher.yml up -d
# Verify data still exists
```

## Conclusion

This migration guide covers the essential steps and common pitfalls when moving from Docker Desktop to Rancher Desktop. Key takeaways:

1. **Always use service names** for inter-container communication
2. **Add nginx proxy** for external access when needed
3. **Map to different ports** to avoid conflicts
4. **Implement health checks** for service dependencies
5. **Test thoroughly** before declaring migration complete
6. **Keep both docker-compose files** for flexibility

Remember to update your CI/CD pipelines and deployment scripts to use the new configuration.