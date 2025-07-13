# PRSNL Port Allocation & Conflict Prevention Guide - Phase 3

## Overview

This document serves as the **SINGLE SOURCE OF TRUTH** for all port allocations in the PRSNL project post-Phase 3 AI transformation. All services, development tools, and production deployments MUST reference this document for port assignments.

## 🚨 CRITICAL RULES

1. **NO PORT CHANGES** without updating this document
2. **ALWAYS CHECK** port availability before starting services
3. **NEVER OVERRIDE** assigned ports
4. **DOCUMENT** any temporary port usage

## Phase 3 Development Ports (FIXED)

| Service | Port | Status | Description | Config Location |
|---------|------|--------|-------------|-----------------|
| **Frontend Dev (SvelteKit)** | **3004** | **FIXED** | Main dev UI | `/PRSNL/frontend/vite.config.ts` |
| **Frontend Container** | **3003** | FIXED | Production UI | `/PRSNL/docker-compose.yml` |
| **Backend + AutoAgent** | **8000** | FIXED | REST API + AI agents | Local process |
| **PostgreSQL ARM64** | **5433** | **CRITICAL** | Primary database | ARM64 PostgreSQL 16 |
| **DragonflyDB** | **6379** | FIXED | Ultra-fast cache | `/PRSNL/docker-compose.yml` |

### 🤖 Phase 3 AI API Endpoints (Port 8000)

| API Path | Service | Description |
|----------|---------|-------------|
| `/api/autoagent/*` | **AutoAgent** | Multi-agent AI system |
| `/api/ai/*` | **LibreChat** | OpenAI-compatible chat |
| `/api/*` | **Core API** | Original PRSNL endpoints |

## Alternative Frontend Ports (CORS Allowed)

| Port | Purpose | When Used |
|------|---------|-----------|
| **3003** | Production container | Container deployments only |
| **3002** | Legacy fallback | If 3004 unavailable |
| **5173** | Vite default | Development testing |

## 🚨 Phase 3 Critical Port Changes

### Database Port Change: 5432 → 5433
- **Old**: PostgreSQL on port 5432 (Intel/x86_64)
- **New**: PostgreSQL 16 ARM64 on port 5433
- **Reason**: ARM64 architecture optimization for Apple Silicon
- **Impact**: All database connections must use port 5433

### Cache System Change: Redis → DragonflyDB
- **Old**: Redis on port 6379
- **New**: DragonflyDB on port 6379 (25x performance improvement)
- **Reason**: Superior performance and memory efficiency
- **Impact**: Drop-in replacement, same port

## Production Ports

| Service | Port | Description | Config Location |
|---------|------|-------------|-----------------|
| **Nginx HTTP** | **80** | HTTP traffic | `/PRSNL/DEPLOYMENT_GUIDE.md` |
| **Nginx HTTPS** | **443** | HTTPS traffic | `/PRSNL/DEPLOYMENT_GUIDE.md` |

## Monitoring & Analytics Ports (Production)

| Service | Port | Description | Config Location |
|---------|------|-------------|-----------------|
| **Grafana** | **3000** | Metrics dashboard | `/PRSNL/docker-compose.monitoring.yml` |
| **Prometheus** | **9090** | Metrics collection | `/PRSNL/docker-compose.monitoring.yml` |
| **Elasticsearch** | **9200** | Search/analytics HTTP | `/PRSNL/DEPLOYMENT_GUIDE.md` |
| **Elasticsearch** | **9300** | Search/analytics transport | `/PRSNL/DEPLOYMENT_GUIDE.md` |
| **Kibana** | **5601** | Elasticsearch UI | `/PRSNL/DEPLOYMENT_GUIDE.md` |
| **Cadvisor** | **8080** | Container monitoring | Production configs |
| **Node Exporter** | **9100** | System metrics | Production configs |

## Port Conflict Prevention

### Before Starting Any Service

```bash
# Check if port is in use (replace PORT with actual number)
lsof -i :PORT

# Alternative check
netstat -an | grep PORT

# Kill process using port (use with caution)
kill -9 $(lsof -t -i:PORT)
```

### Docker Port Check

```bash
# List all Docker port mappings
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Check specific port in Docker
docker ps | grep ":PORT->"
```

## Port Allocation Process

1. **Check this document** for available ports
2. **Verify port availability** using commands above
3. **Update this document** if allocating new port
4. **Update dependent configs**:
   - `/PRSNL/docker-compose.yml`
   - `/PRSNL/backend/app/config.py` (for CORS)
   - `/PRSNL/frontend/.env`
   - Deployment guides

## Reserved Port Ranges

| Range | Purpose | Notes |
|-------|---------|-------|
| **3000-3999** | Frontend services | 3003 is primary |
| **8000-8999** | Backend services | 8000 is primary API |
| **5000-5999** | Databases | 5432 for PostgreSQL |
| **9000-9999** | Monitoring | Prometheus, exporters |
| **11000-11999** | AI/ML services | Reserved for future use |

## Common Port Conflicts & Solutions

### Frontend Port 3003 Conflict

```bash
# Check what's using port 3003
lsof -i :3003

# Common culprits:
# - Another PRSNL instance
# - Previous crashed process
# - Other Node.js apps
# - Frontend container running (stop with docker-compose stop frontend)

# Solution:
# 1. Kill the process or
# 2. Use alternative port 3002 (update CORS in backend)
```

### Backend Port 8000 Conflict

```bash
# Check what's using port 8000
lsof -i :8000

# Common culprits:
# - Jupyter notebooks
# - Other Python apps
# - Previous FastAPI instance

# Solution:
# Stop conflicting service or use Docker isolation
```

## Docker Compose Port Management

### Development Ports (docker-compose.yml)

```yaml
services:
  frontend:
    ports:
      - "3003:3003"  # Host:Container
  
  backend:
    ports:
      - "8000:8000"
  
  db:
    ports:
      - "5432:5432"
  
  redis:
    ports:
      - "6379:6379"
```

## Troubleshooting

### Port Already in Use Error

```bash
# Error: bind: address already in use
# Solution 1: Find and kill process
sudo lsof -i :PORT
kill -9 PID

# Solution 2: Use Docker cleanup
docker-compose down
docker system prune

# Solution 3: Restart Docker daemon
sudo systemctl restart docker
```

### CORS Issues with Ports

If changing frontend port:
1. Update `/PRSNL/backend/app/config.py`:
   ```python
   CORS_ORIGINS = ["http://localhost:3003", "http://localhost:NEW_PORT"]
   ```
2. Restart backend service

### Windows Specific Issues

```powershell
# Check port on Windows
netstat -ano | findstr :PORT

# Kill process on Windows
taskkill /F /PID <PID>
```

## Related Documentation

- **Model Coordination**: `/PRSNL/MODEL_COORDINATION_RULES.md`
- **Development Setup**: `/PRSNL/DEVELOPER_GUIDE.md`
- **Deployment Guide**: `/PRSNL/DEPLOYMENT_GUIDE.md`
- **Architecture**: `/PRSNL/ARCHITECTURE.md`

## Update History

- 2025-07-07: Initial document created with all known port allocations  
- 2025-07-10: Updated frontend port from 3002 to 3003 due to container conflict
- **2025-07-13: PHASE 3 COMPLETE - Major updates:**
  - Frontend development port changed from 3003 to 3004
  - Database port changed from 5432 to 5433 (ARM64 PostgreSQL 16)
  - Redis replaced with DragonflyDB (same port 6379)
  - Added AutoAgent API endpoints (`/api/autoagent/*`)
  - Added LibreChat API endpoints (`/api/ai/*`)
  - Updated all AI infrastructure port documentation
- Note: This document supersedes port information in MODEL_COORDINATION_RULES.md