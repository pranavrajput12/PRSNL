# Mac Mini M4 Setup Guide - Quick Start

## Current Status
- ✅ PostgreSQL 16 running on port 5432
- ✅ pgvector extension installed (v0.8.0)
- ✅ Database "prsnl" created
- ⚠️ Python environment needs setup
- ⚠️ Backend and frontend services need to be started
- ⚠️ Authentication services need configuration

## Quick Start Commands

### 1. Install Python (if needed)
```bash
# Add Homebrew to PATH
eval "$(/opt/homebrew/bin/brew shellenv)"

# Install Python
brew install python@3.11

# Verify installation
python3 --version
```

### 2. Set up Backend
```bash
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --port 8000
```

### 3. Set up Frontend
```bash
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/frontend

# Install dependencies
npm install

# Start frontend
npm run dev -- --port 3004
```

### 4. Start Authentication Services (Optional)
```bash
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL

# Start Colima (Docker runtime)
colima start

# Start auth services
docker-compose -f docker-compose.auth.yml up -d
```

## Test URLs
- Frontend: http://localhost:3004
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Keycloak Admin: http://localhost:8080 (admin/admin123)
- FusionAuth Admin: http://localhost:9011

## Troubleshooting

### If Python is not found:
1. Make sure Homebrew is in PATH: `eval "$(/opt/homebrew/bin/brew shellenv)"`
2. Install Python: `brew install python@3.11`
3. Add to shell profile: `echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc`

### If ports are in use:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3004
lsof -ti:3004 | xargs kill -9
```

### If PostgreSQL is not running:
```bash
brew services start postgresql@16
```

### If pgvector extension is missing:
```bash
psql -U pronav -d prsnl -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Next Steps
1. Configure test users in Keycloak/FusionAuth
2. Run database migrations
3. Test authentication flow
4. Verify all services are working together