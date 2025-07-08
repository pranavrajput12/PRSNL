# Rancher Desktop Deployment Guide

This guide covers deploying PRSNL using Rancher Desktop, including troubleshooting common issues.

## Prerequisites

1. **Rancher Desktop** installed and running
2. **Docker CLI** configured to use Rancher Desktop context
3. **Port availability**: Ensure ports 3002, 8001, 5433, and 6380 are free

## Initial Setup

### 1. Switch Docker Context

```bash
# List available contexts
docker context ls

# Switch to Rancher Desktop
docker context use rancher-desktop
```

### 2. Verify Docker is Working

```bash
docker ps
docker version
```

## Deployment Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd PRSNL
```

### 2. Environment Configuration

Create `.env` file in the backend directory:

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your configuration:
- Set `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` (optional)

### 3. Build and Deploy

```bash
# From PRSNL root directory
docker-compose -f docker-compose-rancher.yml up --build
```

## Service URLs

- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8001
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6380

## Common Issues and Solutions

### 1. Port Already in Use

**Error**: `bind: address already in use`

**Solution**:
```bash
# Find process using port (example for 8001)
lsof -i :8001

# Kill the process
kill -9 <PID>

# Or use different ports in docker-compose-rancher.yml
```

### 2. Frontend Can't Connect to Backend

**Error**: `Error: connect ECONNREFUSED ::1:8001`

**Solution**: Update frontend environment in docker-compose:
```yaml
frontend:
  environment:
    PUBLIC_API_URL: http://backend:8000  # Use container name, not localhost
```

### 3. Database Connection Issues

**Error**: `connection to server at "postgres" (172.x.x.x), port 5432 failed`

**Solution**: Ensure PostgreSQL is using the correct port:
```yaml
postgres:
  ports:
    - "5433:5432"  # Map to 5433 to avoid conflicts
```

### 4. Redis Connection Failed

**Error**: `Error connecting to Redis`

**Solution**: Verify Redis service name in backend config:
```python
REDIS_URL = "redis://redis:6379"  # Use service name, not localhost
```

### 5. Missing Dependencies

**Error**: Build failures due to missing packages

**Solution**:
```bash
# Rebuild without cache
docker-compose -f docker-compose-rancher.yml build --no-cache

# Or remove volumes and restart
docker-compose -f docker-compose-rancher.yml down -v
docker-compose -f docker-compose-rancher.yml up --build
```

### 6. Frontend Build Errors

**Error**: TypeScript or Svelte compilation errors

**Solution**:
1. Fix type mismatches between frontend and backend
2. Ensure all required fields are in API responses
3. Add missing enum values (e.g., `IMAGE` to `ItemType`)

### 7. JSONB Parsing Errors

**Error**: `Input should be a valid dictionary`

**Solution**: Handle JSONB fields properly in backend:
```python
# In API endpoints
"metadata": row["metadata"] if isinstance(row.get("metadata"), dict) else (json.loads(row["metadata"]) if row.get("metadata") else {})
```

## Nginx Proxy Configuration

The setup includes an nginx proxy to handle Rancher networking limitations:

```nginx
server {
    listen 8001;
    
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring Services

### Check Service Status

```bash
# View all running containers
docker-compose -f docker-compose-rancher.yml ps

# View logs for specific service
docker-compose -f docker-compose-rancher.yml logs backend
docker-compose -f docker-compose-rancher.yml logs frontend

# Follow logs in real-time
docker-compose -f docker-compose-rancher.yml logs -f backend
```

### Health Checks

```bash
# Check backend health
curl http://localhost:8001/api/health

# Check frontend
curl http://localhost:3002
```

## Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose-rancher.yml down

# Stop and remove volumes (full cleanup)
docker-compose -f docker-compose-rancher.yml down -v
```

## Performance Optimization

### 1. Resource Limits

Add resource limits to prevent containers from consuming too much memory:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
```

### 2. Volume Performance

Use delegated mounts for better performance on macOS:

```yaml
volumes:
  - ./backend:/app:delegated
```

### 3. Build Optimization

Use multi-stage builds and Docker build cache:

```dockerfile
# Frontend Dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/build ./build
COPY package*.json ./
EXPOSE 3000
CMD ["node", "build"]
```

## Troubleshooting Commands

```bash
# Reset everything
docker-compose -f docker-compose-rancher.yml down -v
docker system prune -a --volumes
docker-compose -f docker-compose-rancher.yml up --build

# Check container networking
docker network ls
docker network inspect prsnl_default

# Execute commands in container
docker-compose -f docker-compose-rancher.yml exec backend bash
docker-compose -f docker-compose-rancher.yml exec postgres psql -U postgres

# View detailed container info
docker inspect prsnl_backend_1
```

## Security Considerations

1. **Never commit `.env` files** with real credentials
2. **Use secrets management** for production deployments
3. **Enable HTTPS** with proper certificates for production
4. **Restrict database access** to only necessary services
5. **Regular updates** of base images and dependencies

## Next Steps

After successful deployment:

1. Test all features thoroughly
2. Set up monitoring and logging
3. Configure backups for PostgreSQL
4. Document any custom configurations
5. Create CI/CD pipeline for automated deployments