# DEVELOPMENT_SETUP.md

## PRSNL Development Environment Setup Guide

### Overview
PRSNL is a multi-component local-first knowledge management system requiring setup of frontend (SvelteKit), backend (FastAPI), browser extension (Chrome), desktop overlay (Electron), and database (PostgreSQL).

## System Requirements

### Hardware Requirements
- **CPU**: 2+ cores (4+ recommended for AI processing)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 2GB free space (5GB+ for development)
- **Network**: Internet connection for initial setup only

### Software Prerequisites
- **Node.js**: v18.0.0 or higher
- **npm**: v8.0.0 or higher  
- **Python**: 3.8+ (3.11 recommended)
- **pip**: Latest version
- **Docker**: Latest stable version
- **Docker Compose**: v2.0.0 or higher
- **Git**: Latest version
- **Chrome/Chromium**: For extension development

### Operating System Support
- **Primary**: macOS 10.15+, Ubuntu 20.04+, Windows 10+
- **Testing**: All major Linux distributions
- **Browser**: Chrome 88+, Firefox 85+, Safari 14+ (extension Chrome-only)

## Quick Start (5 Minutes)

### 1. Clone and Initial Setup
```bash
# Clone the repository
git clone https://github.com/user/prsnl.git
cd prsnl

# Run automated setup script
chmod +x scripts/setup_dev.sh
./scripts/setup_dev.sh
```

### 2. Start All Services
```bash
# Start all components with one command
docker-compose up --build

# Or manually start each component
npm run dev:all
```

### 3. Verify Installation
```bash
# Check all services are running
curl http://localhost:8000/health  # Backend
curl http://localhost:3000         # Frontend
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: localhost:5432

## Detailed Component Setup

### Frontend (SvelteKit) Setup

#### 1. Install Dependencies
```bash
cd frontend
npm install
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development
VITE_VERSION=1.0.0
EOF
```

#### 3. Development Server
```bash
# Start with hot reload
npm run dev

# Start with network access
npm run dev -- --host 0.0.0.0

# Build for production
npm run build
```

#### 4. Frontend Project Structure
```
frontend/
├── src/
│   ├── lib/                    # Shared utilities
│   │   ├── components/         # Reusable components
│   │   ├── utils/             # Utility functions
│   │   ├── data/              # Sample data
│   │   └── constants.js       # App constants
│   ├── routes/                # SvelteKit pages
│   │   ├── +layout.svelte     # Root layout
│   │   ├── +page.svelte       # Homepage
│   │   ├── search/            # Search page
│   │   ├── timeline/          # Timeline page
│   │   └── settings/          # Settings page
│   └── app.html               # HTML template
├── static/                    # Static assets
├── package.json              # Dependencies
├── vite.config.ts           # Build configuration
└── svelte.config.js         # Svelte configuration
```

### Backend (FastAPI) Setup

#### 1. Python Environment
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
cat > .env << EOF
DATABASE_URL=postgresql://prsnl:prsnl@localhost:5432/prsnl
REDIS_URL=redis://localhost:6379
OLLAMA_BASE_URL=http://localhost:11434
AZURE_OPENAI_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
ENVIRONMENT=development
DEBUG=true
EOF
```

#### 3. Database Setup
```bash
# Start PostgreSQL with Docker
docker run -d --name prsnl-postgres \
  -e POSTGRES_DB=prsnl \
  -e POSTGRES_USER=prsnl \
  -e POSTGRES_PASSWORD=prsnl \
  -p 5432:5432 \
  postgres:15

# Wait for database to be ready
sleep 10

# Run database migrations
python app/db/init_db.py

# Seed with sample data
python scripts/seed_data.py
```

#### 4. Development Server
```bash
# Start with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the development script
python -m app.main

# Run worker process (separate terminal)
python app/worker.py
```

#### 5. Backend Project Structure
```
backend/
├── app/
│   ├── api/                   # API endpoints
│   │   ├── __init__.py
│   │   ├── capture.py         # Capture endpoints
│   │   ├── search.py          # Search endpoints
│   │   └── timeline.py        # Timeline endpoints
│   ├── core/                  # Business logic
│   │   ├── capture_engine.py  # Content processing
│   │   ├── search_engine.py   # Search functionality
│   │   └── ai_client.py       # AI integration
│   ├── db/                    # Database layer
│   │   ├── models.py          # SQLAlchemy models
│   │   └── init_db.py         # Database initialization
│   ├── config.py              # Application settings
│   ├── main.py                # FastAPI application
│   └── worker.py              # Background tasks
├── scripts/                   # Utility scripts
├── requirements.txt           # Production dependencies
└── requirements-dev.txt       # Development dependencies
```

### Chrome Extension Setup

#### 1. Load Extension in Development
```bash
cd extension

# Open Chrome and navigate to:
# chrome://extensions/

# Enable "Developer mode" (top right toggle)
# Click "Load unpacked"
# Select the extension/ directory
```

#### 2. Extension Project Structure
```
extension/
├── manifest.json             # Extension metadata
├── background.js             # Service worker
├── content.js               # Page injection script
├── popup.html               # Extension popup UI
├── popup.js                 # Popup functionality
├── options.html             # Settings page
├── options.js               # Settings functionality
├── styles.css               # Popup styles
├── content.css              # Page injection styles
└── icons/                   # Extension icons
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

#### 3. Testing Extension
```bash
# Test keyboard shortcuts
# ⌘+Shift+S (Mac) / Ctrl+Shift+S (Windows) - Capture page
# ⌘+Shift+E (Mac) / Ctrl+Shift+E (Windows) - Capture selection

# Test context menu
# Right-click on any page
# Look for "Capture page to PRSNL" and "Capture selection to PRSNL"

# Test popup
# Click extension icon in toolbar
```

### Desktop Overlay (Electron) Setup

#### 1. Install and Build
```bash
cd overlay

# Install dependencies
npm install

# Start development mode
npm run dev

# Build for production
npm run build

# Package for distribution
npm run package
```

#### 2. Overlay Project Structure
```
overlay/
├── main.js                  # Electron main process
├── renderer.js              # UI renderer process
├── preload.js               # Security bridge
├── index.html               # UI template
├── styles.css               # UI styles
├── package.json             # Dependencies
└── build/                   # Build output
```

### Database Setup (PostgreSQL)

#### 1. Docker Installation (Recommended)
```bash
# Start PostgreSQL container
docker run -d --name prsnl-postgres \
  -e POSTGRES_DB=prsnl \
  -e POSTGRES_USER=prsnl \
  -e POSTGRES_PASSWORD=prsnl \
  -p 5432:5432 \
  -v prsnl_data:/var/lib/postgresql/data \
  postgres:15

# Connect to database
docker exec -it prsnl-postgres psql -U prsnl -d prsnl
```

#### 2. Manual Installation
```bash
# On macOS with Homebrew
brew install postgresql@15
brew services start postgresql@15

# On Ubuntu
sudo apt update
sudo apt install postgresql postgresql-contrib

# On Windows
# Download from: https://www.postgresql.org/download/windows/
```

#### 3. Database Schema
```sql
-- Connect to PostgreSQL and run:
CREATE DATABASE prsnl;
CREATE USER prsnl WITH PASSWORD 'prsnl';
GRANT ALL PRIVILEGES ON DATABASE prsnl TO prsnl;

-- Switch to prsnl database
\c prsnl

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create tables (run from backend/app/db/init_db.py)
```

### AI Integration Setup (Ollama)

#### 1. Install Ollama
```bash
# On macOS
brew install ollama

# On Linux
curl -fsSL https://ollama.com/install.sh | sh

# On Windows
# Download from: https://ollama.com/download/windows
```

#### 2. Download Models
```bash
# Start Ollama service
ollama serve

# Download recommended models (in another terminal)
ollama pull llama2          # 7B parameter model (4GB)
ollama pull codellama       # Code-focused model (7GB)
ollama pull mistral         # Alternative model (4GB)

# Test model
ollama run llama2 "Summarize this: Hello world example."
```

#### 3. Configure API Access
```bash
# Ollama runs on http://localhost:11434 by default
curl http://localhost:11434/api/generate \
  -d '{"model": "llama2", "prompt": "Test prompt", "stream": false}'
```

## Development Scripts

### Automated Setup Script
```bash
#!/bin/bash
# scripts/setup_dev.sh

echo "🚀 Setting up PRSNL development environment..."

# Check prerequisites
command -v node >/dev/null 2>&1 || { echo "Node.js required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }

# Setup frontend
echo "📦 Setting up frontend..."
cd frontend
npm install
cp .env.example .env
cd ..

# Setup backend
echo "🐍 Setting up backend..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd ..

# Start database
echo "🗄️ Starting database..."
docker run -d --name prsnl-postgres \
  -e POSTGRES_DB=prsnl \
  -e POSTGRES_USER=prsnl \
  -e POSTGRES_PASSWORD=prsnl \
  -p 5432:5432 \
  postgres:15

# Wait and initialize database
sleep 10
cd backend
source venv/bin/activate
python app/db/init_db.py
python scripts/seed_data.py
cd ..

echo "✅ Setup complete! Run 'docker-compose up' to start all services."
```

### Development Commands
```bash
# Start all services
npm run dev:all           # Start frontend, backend, worker

# Individual services
npm run dev:frontend      # Frontend only
npm run dev:backend       # Backend only
npm run dev:worker        # Worker only

# Database operations
npm run db:reset          # Reset database
npm run db:seed           # Seed sample data
npm run db:backup         # Create backup

# Testing
npm run test              # Run all tests
npm run test:frontend     # Frontend tests
npm run test:backend      # Backend tests
npm run test:e2e          # End-to-end tests

# Linting and formatting
npm run lint              # Check all code
npm run format            # Format all code
```

## Configuration Files

### Frontend Configuration (vite.config.ts)
```typescript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 3000,
    host: '0.0.0.0'
  },
  build: {
    target: 'es2020'
  }
});
```

### Backend Configuration (app/config.py)
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://prsnl:prsnl@localhost:5432/prsnl"
    redis_url: str = "redis://localhost:6379"
    ollama_base_url: str = "http://localhost:11434"
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Docker Compose Configuration
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: prsnl
      POSTGRES_USER: prsnl
      POSTGRES_PASSWORD: prsnl
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://prsnl:prsnl@postgres:5432/prsnl
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://localhost:8000
    volumes:
      - ./frontend:/app

volumes:
  postgres_data:
```

## Environment Variables

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development
VITE_VERSION=1.0.0
VITE_ENABLE_DEBUG=true
```

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://prsnl:prsnl@localhost:5432/prsnl

# Cache
REDIS_URL=redis://localhost:6379

# AI Services
OLLAMA_BASE_URL=http://localhost:11434
AZURE_OPENAI_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=info

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Development Workflow

### 1. Daily Development Routine
```bash
# Start day
git pull origin main
docker-compose up -d postgres redis

# Start development
npm run dev:all

# Code, test, commit
git add .
git commit -m "feat: description"
git push origin feature-branch

# End day
docker-compose down
```

### 2. Feature Development Process
1. **Create Feature Branch**: `git checkout -b feature/new-feature`
2. **Update Progress Tracker**: Mark task as in-progress
3. **Develop with Tests**: Write tests first, then implementation
4. **Run Full Test Suite**: Ensure all tests pass
5. **Update Documentation**: Update relevant docs
6. **Create Pull Request**: For code review
7. **Deploy to Staging**: Test in production-like environment

### 3. Testing Strategy
```bash
# Unit tests
npm run test:unit

# Integration tests
npm run test:integration

# End-to-end tests
npm run test:e2e

# Performance tests
npm run test:performance

# Security tests
npm run test:security
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using port 3000
lsof -i :3000

# Kill process using port
kill -9 $(lsof -t -i:3000)

# Use different port
npm run dev -- --port 3001
```

#### 2. Database Connection Errors
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart PostgreSQL
docker restart prsnl-postgres

# Check logs
docker logs prsnl-postgres

# Reset database
npm run db:reset
```

#### 3. Extension Not Loading
```bash
# Check Chrome extensions page
chrome://extensions/

# Reload extension
# Click reload button on extension card

# Check for manifest errors
# Look for red error messages

# Clear extension storage
# Chrome DevTools > Application > Storage > Clear
```

#### 4. AI Integration Issues
```bash
# Check Ollama status
ollama list

# Restart Ollama
pkill ollama
ollama serve

# Test API endpoint
curl http://localhost:11434/api/tags
```

#### 5. Frontend Build Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .svelte-kit
npm run dev

# Check for TypeScript errors
npm run type-check
```

### Performance Optimization Tips

#### 1. Frontend Performance
- Enable hot module replacement
- Use development source maps
- Optimize bundle size with code splitting
- Use lazy loading for heavy components

#### 2. Backend Performance
- Use connection pooling for database
- Enable database query logging in development
- Use Redis for caching frequent queries
- Profile API endpoints with timing middleware

#### 3. Database Performance
- Monitor query performance
- Add appropriate indexes
- Use EXPLAIN ANALYZE for slow queries
- Regular VACUUM and ANALYZE operations

## IDE Setup and Recommendations

### VS Code Extensions
```json
{
  "recommendations": [
    "svelte.svelte-vscode",
    "ms-python.python",
    "ms-python.black-formatter",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-eslint"
  ]
}
```

### VS Code Settings
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "svelte.enable-ts-plugin": true
}
```

## Next Steps

After completing this setup:

1. **Run the Quick Start**: Verify all components work together
2. **Read Interface Documentation**: Understand component interactions
3. **Review Build/Deployment Guide**: Learn production deployment
4. **Explore AI Integration**: Test local LLM capabilities
5. **Start Contributing**: Pick up tasks from the backlog

For questions or issues, refer to:
- **Troubleshooting Section**: Common problems and solutions
- **GitHub Issues**: Known bugs and feature requests  
- **Documentation**: Complete technical reference
- **AI Assistant**: Use /docs/CLAUDE.md for development guidance