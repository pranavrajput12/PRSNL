# PRSNL Project Structure & Key Files

## 🏗️ Core Project Structure

```
PRSNL/
├── backend/                 # Python/FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core functionality
│   │   ├── db/             # Database models & migrations
│   │   ├── services/       # Business logic services
│   │   └── main.py         # FastAPI app entry point
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container config
│
├── frontend/               # SvelteKit frontend
│   ├── src/
│   │   ├── lib/           # Shared components & utilities
│   │   │   ├── api.ts     # API client
│   │   │   ├── components/# Reusable UI components
│   │   │   └── utils/     # Helper functions
│   │   └── routes/        # Page components
│   ├── package.json       # Node dependencies
│   └── vite.config.ts     # Vite configuration
│
├── docker-compose.yml      # Main Docker configuration
├── nginx.conf             # NGINX proxy configuration
└── docs/                  # Documentation

## 📁 Key Configuration Files

### Docker & Infrastructure
- `docker-compose.yml` - Main services configuration (backend, db, redis, nginx)
- `docker-compose-rancher.yml` - Rancher Desktop specific config
- `nginx.conf` - Reverse proxy configuration for port 8001

### Backend Configuration
- `backend/app/config.py` - Environment variables and settings
- `backend/requirements.txt` - Python package dependencies
- `backend/.env` - Local environment variables (not in git)

### Frontend Configuration
- `frontend/vite.config.ts` - Vite dev server and proxy settings
- `frontend/package.json` - Node.js dependencies
- `frontend/src/lib/api.ts` - API client configuration

### Database
- `backend/app/db/schema.sql` - PostgreSQL schema
- `backend/app/db/migrations/` - Database migration files

## 🔑 Critical Variables & Mappings

### Database Schema → API Response → Frontend

#### Items Table Structure
```sql
items {
  id: UUID
  url: TEXT
  title: TEXT
  summary: TEXT
  status: VARCHAR(20)  -- 'pending', 'completed', 'failed', 'bookmark'
  metadata: JSONB {
    item_type: 'video|article|tweet|github|pdf'
    platform: 'youtube|twitter|github|web'
    tags: 'comma,separated,tags'
    category: 'programming|ai|productivity|etc'
    thumbnail_url: 'https://...'
    duration: 3600  -- seconds for videos
    file_path: '/media/videos/...'
  }
  created_at: TIMESTAMPTZ
}
```

#### API Response Transformation
```typescript
// Backend returns snake_case, frontend expects camelCase
{
  created_at → createdAt
  updated_at → updatedAt
  item_type → itemType
  thumbnail_url → thumbnailUrl
  file_path → filePath
}
```

#### Frontend Component Props
```typescript
// VideoCard expects
{
  id: string
  title: string
  url: string
  platform: 'youtube'  // Required for YouTube embed
  thumbnail_url?: string
}

// Timeline expects
{
  items: Array<{
    ...all fields above
    tags: string[]  // From item_tags join
  }>
}
```

## 🌐 API Endpoints

### Core Endpoints
- `GET /api/timeline` - Get items list
- `GET /api/items/{id}` - Get single item
- `POST /api/capture` - Add new item
- `GET /api/search` - Search items
- `GET /api/tags` - Get all tags

### AI Features (Backend implemented, frontend partial)
- `POST /api/suggest` - Get AI suggestions for URL
- `POST /api/categorize` - Categorize items
- `POST /api/duplicates/check` - Check for duplicates
- `POST /api/summarization/item` - Summarize content

### WebSocket
- `WS /ws/chat/{client_id}` - RAG-based chat

## 🔌 Port Allocations

- **3002** - Frontend (Vite dev server)
- **8000** - Backend (FastAPI)
- **8001** - NGINX proxy (production access)
- **5432** - PostgreSQL database
- **6379** - Redis cache

## 🚨 Common Issues & Solutions

### Frontend Can't Connect to Backend
- Check Vite proxy in `vite.config.ts`
- Ensure backend is running on port 8000
- Clear browser cache

### Videos Not Playing
- Ensure `platform: 'youtube'` is set in metadata
- Check if URL is valid YouTube URL
- Verify item status is 'completed'

### Chat Not Working
- WebSocket proxy must be configured in Vite
- Check `/ws` proxy in `vite.config.ts`
- Ensure Redis is running

### Items Not Showing in Timeline
- Items must have status 'completed' or 'bookmark'
- Check database directly: `docker exec prsnl_db psql -U postgres -d prsnl`
- Clear Redis cache: `docker exec prsnl_redis redis-cli FLUSHALL`

## 🧩 Model Responsibilities

### Claude (Integration & Documentation)
- System integration and debugging
- Documentation maintenance
- Cross-service coordination

### Windsurf (Frontend)
- All files in `frontend/src/`
- UI/UX components
- Frontend state management

### Gemini (Backend)
- All files in `backend/app/`
- API endpoints
- Database operations
- AI service implementations

## 📝 Files to Update When Adding Features

1. **Adding New API Endpoint**
   - Create in `backend/app/api/`
   - Include router in `backend/app/main.py`
   - Update `API_DOCUMENTATION.md`
   - Add TypeScript types in `frontend/src/lib/types/api.ts`

2. **Adding New Frontend Page**
   - Create in `frontend/src/routes/`
   - Add navigation in `frontend/src/routes/+layout.svelte`
   - Update API client if needed in `frontend/src/lib/api.ts`

3. **Database Schema Changes**
   - Create migration in `backend/app/db/migrations/`
   - Update `DATABASE_SCHEMA.md`
   - Update API response handlers
   - Update frontend TypeScript interfaces