# PRSNL Docker Configuration Guide

## Current Setup (as of 2025-07-12)

### Database
- **Production**: Using local PostgreSQL (not Docker)
- **Connection**: `postgresql://pronav@localhost:5432/prsnl`
- **Reason**: Better performance and easier management for development

### Services Running in Docker
- **DragonflyDB**: For caching (port 6379) - 25x faster than Redis
- **Ollama**: For local LLM (port 11434) - optional

### AI Services (Phase 4)
- **LangGraph Workflows**: State-based content processing (integrated in backend)
- **Enhanced AI Router**: ReAct agent routing system (integrated in backend)
- **LangChain Templates**: Centralized prompt management (integrated in backend)
- **Azure OpenAI**: GPT-4 integration for AI services

### Backend
- **Development**: Run locally with `python3 -m uvicorn app.main:app --reload`
- **Docker**: Can be used but currently has dependency issues

## Common Commands

### Start DragonflyDB only
```bash
docker-compose up -d dragonflydb
```

### Test AI Services
```bash
# Test AI Router
curl http://localhost:8000/api/ai-router/status

# Test LangGraph Workflows
curl -X POST http://localhost:8000/api/ai-suggest \
  -H "Content-Type: application/json" \
  -d '{"content": "Test workflow processing", "context": {"use_workflow": true}}'

# Run comprehensive integration tests
cd backend && python3 test_integrations.py
```

### Start all services (excluding database)
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f redis
```

### Stop all services
```bash
docker-compose down
```

## Database Migration Commands

### Backup local database
```bash
pg_dump -U pronav prsnl > backup_$(date +%Y%m%d).sql
```

### Restore from backup
```bash
psql -U pronav prsnl < backup_file.sql
```

## Troubleshooting

### Backend can't connect to database
- Ensure local PostgreSQL is running: `brew services list | grep postgresql`
- Check connection: `psql -U pronav -d prsnl -c "SELECT 1;"`

### Docker build takes too long
- The full requirements.txt has many ML dependencies
- Consider using requirements.minimal.txt for faster builds

### Port conflicts
- Database: 5433 (local PostgreSQL ARM64)
- DragonflyDB: 6379 (Docker)
- Backend: 8000 (local or Docker)
- Frontend: 3004 (local development)

## Future Improvements
1. Create minimal requirements.txt for Docker
2. Fix OpenTelemetry dependencies
3. Consider using Docker only for services, not application code
4. Add Docker health checks for AI services
5. Implement AI service monitoring and metrics collection
6. Add automated backup system for AI model configurations