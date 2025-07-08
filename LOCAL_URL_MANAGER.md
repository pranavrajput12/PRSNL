# Local Development URL Manager

## Active Local Services

### PRSNL Project
- **Frontend**: http://localhost:3002 (Vite)
- **Backend**: http://localhost:8000 (FastAPI in Docker)
- **Database**: postgresql://localhost:5432/prsnl
- **Redis**: redis://localhost:6379

### Common Development Ports
- **3000-3010**: Frontend applications (React, Vue, Svelte)
- **4000-4010**: Alternative frontend ports
- **5173**: Vite default port
- **8000-8010**: Backend APIs
- **5432**: PostgreSQL
- **6379**: Redis
- **27017**: MongoDB

## Ngrok Tunnels (When Active)
```bash
# Start ngrok for frontend
ngrok http 3002

# Start ngrok for backend API
ngrok http 8000
```

## Quick Commands

### Check Port Usage
```bash
# Mac/Linux
lsof -i :PORT_NUMBER

# Check all common dev ports
lsof -i :3000-3010,4000-4010,5173,8000-8010
```

### Kill Process on Port
```bash
# Find PID
lsof -ti :PORT_NUMBER

# Kill process
kill -9 $(lsof -ti :PORT_NUMBER)
```

### Start Services
```bash
# PRSNL Frontend
cd ~/Personal\ Knowledge\ Base/PRSNL/frontend && npm run dev

# PRSNL Backend (Docker)
cd ~/Personal\ Knowledge\ Base/PRSNL && docker-compose up
```

## Port Allocation Strategy
1. Always check if port is free before starting
2. Use consistent ports per project
3. Document any port changes here
4. Use ngrok for external access when needed

## Troubleshooting
- **Connection Refused**: Service not running or wrong port
- **Port Already in Use**: Kill existing process or use different port
- **CORS Issues**: Check backend CORS settings include frontend URL