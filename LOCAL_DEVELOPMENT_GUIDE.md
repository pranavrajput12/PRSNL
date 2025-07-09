# Local Development Guide

## Quick Access URLs

### PRSNL Project
- **Frontend**: http://localhost:3002 (Vite)
- **Backend**: http://localhost:8000 (FastAPI)
- **Database**: postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl
- **Alternative Access**: http://prsnl.local (requires setup)

## Simple Port-Based Access (Recommended)

Use these simple URLs for development:

### Browser Bookmarks Method
Create bookmarks with custom names:
1. Bookmark http://localhost:3002 as "PRSNL App"
2. Bookmark http://localhost:8000/docs as "PRSNL API Docs"

## Local Domain Setup Options

### Option 1: /etc/hosts (Simple)
Add to `/etc/hosts`:
```
127.0.0.1 prsnl.local
127.0.0.1 api.prsnl.local
```

Then access:
- http://prsnl.local:3002
- http://api.prsnl.local:8000

### Option 2: Free DNS Services (No Setup)

#### Using nip.io (Recommended)
- **Frontend**: http://prsnl.127.0.0.1.nip.io:3002
- **API**: http://api-prsnl.127.0.0.1.nip.io:8000

#### Using localtest.me
- **Frontend**: http://prsnl.localtest.me:3002
- **API**: http://api.prsnl.localtest.me:8000

### Option 3: Public Tunnels (External Access)

#### Using ngrok
```bash
# Frontend
ngrok http 3002

# Backend
ngrok http 8000
```

#### Using bore.pub (Free)
```bash
# Install
cargo install bore-cli

# Frontend
bore local 3002 --to bore.pub

# Backend
bore local 8000 --to bore.pub
```

#### Using localhost.run (Free)
```bash
# Frontend
ssh -R 80:localhost:3002 localhost.run

# Backend  
ssh -R 80:localhost:8000 localhost.run
```

## Port Management

### Standard Port Allocation
- **3000-3099**: Frontend applications
- **8000-8099**: Backend APIs
- **5432/5433**: PostgreSQL
- **6379**: Redis
- **27017**: MongoDB
- **5173**: Vite default port

### Active Services
- **Frontend**: http://localhost:3002 (Vite)
- **Backend**: http://localhost:8000 (FastAPI)
- **Database**: postgresql://localhost:5433/prsnl (PostgreSQL 16 ARM64)

## Quick Commands

### Check Port Usage
```bash
# Check specific port
lsof -i :PORT_NUMBER

# Check all common dev ports
lsof -i :3000-3010,4000-4010,5173,8000-8010,5432,5433
```

### Kill Process on Port
```bash
# Find and kill process
kill -9 $(lsof -ti :PORT_NUMBER)
```

### Start Services
```bash
# Start PostgreSQL (ARM64)
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 start

# PRSNL Frontend
cd ~/Personal\ Knowledge\ Base/PRSNL/frontend && npm run dev

# PRSNL Backend
cd ~/Personal\ Knowledge\ Base/PRSNL/backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Quick Access Script

Create `~/start-prsnl.sh`:
```bash
#!/bin/bash
echo "Starting PRSNL..."

# Start PostgreSQL if not running
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 start

# Start backend in background
cd ~/Personal\ Knowledge\ Base/PRSNL/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Start frontend and open browser
cd ~/Personal\ Knowledge\ Base/PRSNL/frontend
open http://localhost:3002
npm run dev
```

Make it executable: `chmod +x ~/start-prsnl.sh`
Run: `~/start-prsnl.sh`

## Accessing from Other Devices

Use your machine's IP with nip.io:
```
# Find your IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Access from other devices
http://prsnl.192.168.1.100.nip.io:3002
```

## Troubleshooting

### Common Issues
1. **Connection Refused**: Service not running or wrong port
2. **Port Already in Use**: Kill existing process or use different port
3. **CORS Issues**: Check backend CORS settings include frontend URL
4. **Domain not working**: Check nginx is running (if using local domains)

### DNS Cache Issues
```bash
# Clear DNS cache (macOS)
sudo dscacheutil -flushcache

# Restart mDNSResponder
sudo killall -HUP mDNSResponder
```

### ARM64 Specific Issues
- Always use ARM64 Homebrew at `/opt/homebrew`
- PostgreSQL 16 is installed at `/opt/homebrew/opt/postgresql@16`
- Verify architecture: `uname -m` should show `arm64`

## Production Deployment URLs

When deploying to production, use:
- **Railway**: prsnl-production.railway.app
- **Vercel**: prsnl.vercel.app
- **Custom Domain**: app.prsnl.com

## Port Allocation Strategy
1. Always check if port is free before starting
2. Use consistent ports per project
3. Document any port changes in this file
4. Use public tunnels for external testing only