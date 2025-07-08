# Simple Local Domain Setup

## Quick Solution: Use Ports Directly

Instead of complex domain setups, use these simple URLs:

### PRSNL Project
- Frontend: http://localhost:3002
- Backend: http://localhost:8000

## Browser Bookmarks Method

Create bookmarks with custom names:
1. Bookmark http://localhost:3002 as "PRSNL App"
2. Bookmark http://localhost:8000 as "PRSNL API"

## Using /etc/hosts (Simple)

Add to `/etc/hosts`:
```
127.0.0.1 prsnl
127.0.0.1 api.prsnl
```

Then access:
- http://prsnl:3002
- http://api.prsnl:8000

## Free Public URLs (No Setup)

### Using bore.pub
```bash
# Install
cargo install bore-cli

# Frontend
bore local 3002 --to bore.pub

# Backend
bore local 8000 --to bore.pub
```

### Using localhost.run
```bash
# Frontend
ssh -R 80:localhost:3002 localhost.run

# Backend  
ssh -R 80:localhost:8000 localhost.run
```

### Using ngrok (after signup)
```bash
# Frontend
ngrok http 3002

# Backend
ngrok http 8000
```

## Port Management

Use this convention for all projects:
- 3000-3099: Frontend apps
- 8000-8099: Backend APIs
- 5432: PostgreSQL
- 6379: Redis
- 27017: MongoDB

## Quick Access Script

Create `~/start-prsnl.sh`:
```bash
#!/bin/bash
echo "Starting PRSNL..."
cd ~/Personal\ Knowledge\ Base/PRSNL/frontend
open http://localhost:3002
npm run dev
```

Make it executable: `chmod +x ~/start-prsnl.sh`
Run: `~/start-prsnl.sh`