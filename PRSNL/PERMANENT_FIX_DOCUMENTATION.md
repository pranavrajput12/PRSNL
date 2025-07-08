# Permanent Fix for Frontend API Calls

## The Problem
Frontend was making API calls to its own port (3002) instead of the backend port (8000), causing 500 errors.

## The Solution

### 1. API Configuration
Updated `frontend/src/lib/api.ts` to always use relative URLs:
```javascript
const API_BASE_URL = '/api';
```

### 2. Development Setup
For development, run:
```bash
# Start backend services
docker-compose -f docker-compose.dev.yml up -d

# Run frontend separately with hot reload
cd frontend
npm install
npm run dev
```

The frontend dev server (Vite) will proxy `/api` calls to `http://localhost:8000`.

### 3. Production Setup
For production, use:
```bash
docker-compose -f docker-compose.production.yml up -d
```

This setup uses nginx to:
- Serve frontend on port 80
- Proxy `/api` calls to the backend
- Handle WebSocket connections
- Serve media files

### 4. Key Files Modified

1. **frontend/src/lib/api.ts**
   - Changed to use relative URLs (`/api`)
   
2. **frontend/src/routes/item/[id]/+page.svelte**
   - Uses `getItem()` from API library instead of direct fetch
   
3. **frontend/src/routes/videos/[id]/+page.svelte**
   - Uses `getItem()` from API library instead of direct fetch
   
4. **frontend/src/routes/videos/course/+page.svelte**
   - Uses `getItem()` from API library instead of direct fetch

5. **frontend/vite.config.ts**
   - Configured to proxy API calls in development

6. **nginx-production.conf**
   - Properly configured reverse proxy for production

### 5. Environment-Specific Configurations

#### Development
- Frontend runs on host with `npm run dev`
- Vite proxies `/api` to `http://localhost:8000`
- Hot reload enabled

#### Production
- Frontend runs in Docker container
- Nginx proxies all requests
- Optimized builds

## Testing

1. **Development Testing**:
   ```bash
   # Terminal 1
   docker-compose -f docker-compose.dev.yml up
   
   # Terminal 2
   cd frontend && npm run dev
   
   # Access at http://localhost:3002
   ```

2. **Production Testing**:
   ```bash
   docker-compose -f docker-compose.production.yml up
   
   # Access at http://localhost
   ```

## Common Issues

1. **Port conflicts**: Make sure ports 80, 3002, 5432, 6379, 8000 are free
2. **Docker caching**: Use `docker-compose build --no-cache` if changes aren't reflected
3. **Environment variables**: Check `.env` files are properly configured

## Architecture

```
User Browser
     |
     v
Port 80 (Production) / Port 3002 (Development)
     |
     v
Nginx (Production) / Vite Dev Server (Development)
     |
     ├── / → Frontend (SvelteKit)
     ├── /api → Backend (FastAPI on port 8000)
     ├── /media → Backend static files
     └── /ws → WebSocket connections
```

This is a permanent, environment-aware solution that works in both development and production.