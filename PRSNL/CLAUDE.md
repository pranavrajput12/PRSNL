# PRSNL Project Configuration for Claude

## CRITICAL: Container Runtime
**WE USE RANCHER DESKTOP, NOT DOCKER**
- Container runtime: Rancher Desktop
- Do NOT use docker commands
- Do NOT start Docker Desktop
- Do NOT rebuild docker containers

## Ports
- Frontend: **3003** (Updated from 3002 due to container conflict)
- Backend API: **8000**
- PostgreSQL: **5432**
- Redis: **6379**

## Running Services - CRITICAL DISTINCTION
**DEVELOPMENT MODE (WHAT WE USE):**
- Frontend: Run locally with `cd frontend && npm run dev` (port 3003)
- Backend/DB/Redis: Run in Rancher containers

**NEVER DO THIS:**
- Do NOT run frontend container when doing development
- Do NOT start frontend container on port 3003 (conflicts with dev server)
- The frontend container is ONLY for production deployments

**To avoid conflicts:**
```bash
# Always stop frontend container during development
docker-compose stop frontend
```

## Common Issues & Solutions
1. **Old design showing**: Clear Vite cache with `rm -rf node_modules/.vite .svelte-kit`
2. **API errors**: Backend is at http://localhost:8000/api/
3. **Container issues**: Check Rancher Desktop app, NOT Docker

## Git Workflow
- Current branch: main
- Remote: https://github.com/pranavrajput12/PRSNL.git
- ALWAYS verify which commit to rollback to before suggesting git reset

## Testing Commands
- Lint: `npm run lint`
- Type check: `npm run check`
- Format: `npm run format`

## Recent Features (DO NOT ROLLBACK BEFORE THESE)
- Fan3D component (commit b383191)
- Mac3D improvements (commit 468175f)
- Neural Motherboard Interface v4.2 (commit 0c97c5b)