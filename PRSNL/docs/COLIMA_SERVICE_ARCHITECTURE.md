# PRSNL Colima Service Architecture

## Service Distribution Strategy

### 🏠 LOCAL SERVICES (Run on macOS directly)
**Core Application Services - Always Local**

1. **PostgreSQL Database** (Port 5432)
   - **Why Local**: ARM64 optimized, pgvector extension
   - **Location**: `/opt/homebrew/opt/postgresql@16/`
   - **Management**: `brew services start postgresql@16`
   - **Status**: ✅ ACTIVE

2. **Backend API** (Port 8000)
   - **Why Local**: Fast development, hot reload
   - **Location**: `backend/app/main.py`
   - **Command**: `uvicorn app.main:app --reload --port 8000`
   - **Status**: ✅ ACTIVE

3. **Frontend Development** (Port 3004)
   - **Why Local**: Vite HMR, fast builds
   - **Location**: `frontend/`
   - **Command**: `npm run dev -- --port 3004`
   - **Status**: ✅ ACTIVE

### 🐳 COLIMA CONTAINER SERVICES (Run in containers)
**Supporting Infrastructure Services**

1. **DragonflyDB Cache** (Port 6379) ✅ RUNNING
   - **Service**: `redis` in docker-compose.yml
   - **Image**: `docker.dragonflydb.io/dragonflydb/dragonfly`
   - **Why Container**: Isolated cache, 25x faster than Redis
   - **Status**: ✅ HEALTHY

2. **FusionAuth** (Port 9011) ✅ RUNNING
   - **Service**: `fusionauth` 
   - **Image**: `fusionauth/fusionauth-app:1.50.1`
   - **Why Container**: Complex auth service, isolation
   - **Status**: ✅ HEALTHY

3. **Keycloak** (Port 8080) ✅ RUNNING
   - **Service**: `keycloak`
   - **Image**: `quay.io/keycloak/keycloak:23.0.7`
   - **Why Container**: Alternative auth service
   - **Status**: ✅ STARTING

### 🔄 OPTIONAL CONTAINER SERVICES (Start as needed)

4. **Neo4j Graph Database** (Ports 7474, 7687)
   - **Service**: `neo4j` in docker-compose.yml
   - **Image**: `neo4j:5.15-community`
   - **Why Container**: Graph database for knowledge relationships
   - **Status**: 🟡 AVAILABLE (not started)

5. **LibreChat** (Port 3080)
   - **Service**: `librechat` with `librechat-mongo`
   - **Image**: `ghcr.io/danny-avila/librechat-dev:latest`
   - **Why Container**: Advanced chat interface
   - **Status**: 🟡 AVAILABLE (not started)

6. **Browserless** (Port 3001)
   - **Service**: `browserless`
   - **Image**: `browserless/chrome:latest`
   - **Why Container**: Browser automation for testing
   - **Status**: 🟡 AVAILABLE (not started)

### ❌ DISABLED SERVICES (Don't use in containers)

7. **Backend Container** - DISABLED
   - **Reason**: Local development is faster
   - **Status**: ❌ COMMENTED OUT

8. **Frontend Container** - DISABLED FOR DEVELOPMENT
   - **Reason**: Conflicts with dev server on port 3004
   - **Status**: ❌ ONLY FOR PRODUCTION

9. **PostgreSQL Container** - DISABLED
   - **Reason**: Using local ARM64 PostgreSQL with pgvector
   - **Status**: ❌ COMMENTED OUT

## Resource Requirements

### Colima Configuration
```bash
# Current optimal settings
colima start --cpu 4 --memory 8 --disk 100
```

### Resource Allocation
- **CPU**: 4 cores (sufficient for container services)
- **Memory**: 8GB (DragonflyDB + Auth services + overhead)
- **Disk**: 100GB (container images + data volumes)

## Service Startup Order

### 1. Start Colima & Core Containers
```bash
# Ensure Colima is running
colima status || colima start --cpu 4 --memory 8 --disk 100

# Start essential container services
docker-compose up -d redis fusionauth keycloak
```

### 2. Start Local Services
```bash
# Start PostgreSQL (if not running)
brew services start postgresql@16

# Start backend
cd backend && uvicorn app.main:app --reload --port 8000

# Start frontend (separate terminal)
cd frontend && npm run dev -- --port 3004
```

### 3. Optional Services (as needed)
```bash
# For knowledge graph features
docker-compose up -d neo4j

# For advanced chat interface
docker-compose up -d librechat librechat-mongo

# For browser testing
docker-compose up -d browserless
```

## Health Checks

### Container Services
```bash
# Check all container status
docker-compose ps

# Individual service health
docker-compose logs redis
docker-compose logs fusionauth
docker-compose logs keycloak
```

### Local Services
```bash
# PostgreSQL
pg_isready -h localhost -p 5432

# Backend API
curl http://localhost:8000/health

# Frontend
curl http://localhost:3004
```

## Troubleshooting

### Colima Issues
```bash
# Restart Colima if containers fail
colima stop && colima start --cpu 4 --memory 8 --disk 100

# Check Colima logs
colima logs

# Reset if corrupted
colima delete && colima start --cpu 4 --memory 8 --disk 100
```

### Container Issues
```bash
# Restart specific service
docker-compose restart redis

# View logs
docker-compose logs -f redis

# Rebuild if needed
docker-compose up -d --force-recreate redis
```

## Performance Optimization

### DragonflyDB (Primary Cache)
- **Memory**: Uses about 1GB RAM
- **Performance**: 25x faster than Redis
- **Persistence**: Data survives container restarts

### Auth Services
- **FusionAuth**: ~500MB RAM, production-ready
- **Keycloak**: ~800MB RAM, enterprise features
- **Usage**: Only one needed (FusionAuth recommended)

### Optional Services Resource Usage
- **Neo4j**: ~1GB RAM (graph database)
- **LibreChat**: ~300MB RAM (chat interface)
- **Browserless**: ~200MB RAM (browser automation)

## Architecture Benefits

✅ **Fast Development**: Local backend/frontend with hot reload
✅ **Isolated Services**: Container services don't interfere with development
✅ **Resource Efficient**: Only run containers you need
✅ **Apple Silicon Optimized**: Colima + local ARM64 services
✅ **Scalable**: Easy to move services between local/container as needed