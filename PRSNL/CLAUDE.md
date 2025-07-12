# PRSNL Project Configuration for Claude

## CRITICAL: Database Configuration
**WE USE LOCAL POSTGRESQL, NOT DOCKER DATABASE**
- Database: Local PostgreSQL on port 5433 (ARM64 version)
- User: pronav
- Database name: prsnl
- Do NOT use Docker database (it's commented out in docker-compose.yml)

## 🚨 CRITICAL: Architecture Configuration (Apple Silicon M1/M2)
**THIS SYSTEM RUNS ON ARM64 ARCHITECTURE - DO NOT MIX WITH x86_64**

### PostgreSQL Architecture Setup
- **ALWAYS USE**: `/opt/homebrew/` (ARM64 Homebrew) for PostgreSQL
- **NEVER USE**: `/usr/local/` (Intel x86_64 Homebrew) for PostgreSQL
- **Current PostgreSQL**: ARM64 PostgreSQL 16 on port 5433
- **pgvector**: Must be built for ARM64 architecture

### Common Architecture Issues (AVOID THESE):
1. **DO NOT** install or use PostgreSQL from `/usr/local/` (Intel Homebrew)
2. **DO NOT** mix pgvector builds between architectures
3. **DO NOT** change PostgreSQL port from 5433 to 5432
4. **DO NOT** use `brew` from `/usr/local/bin/brew` - use `/opt/homebrew/bin/brew`

### Verify Correct Setup:
```bash
# Check PostgreSQL is ARM64
file /opt/homebrew/opt/postgresql@16/bin/postgres  # Should show: arm64

# Check pgvector extension
/opt/homebrew/opt/postgresql@16/bin/psql -U pronav -p 5433 -d prsnl -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Check which PostgreSQL is running
lsof -p $(pgrep -f postgres | head -1) | grep bin/postgres
```

### If pgvector Breaks Again:
1. Stop any x86_64 PostgreSQL: `/usr/local/bin/brew services stop postgresql@16`
2. Start ARM64 PostgreSQL: `/opt/homebrew/bin/brew services start postgresql@16`
3. Verify database is on port 5433 in `.env` and `config.py`
4. pgvector should already be installed in ARM64 PostgreSQL

## Container Runtime
- We use Rancher Desktop for containers
- Only Redis runs in Docker now
- Backend runs locally for better development experience

## Ports (Exclusive Port Ownership)
- Frontend Development: **3004** (Updated from 3003 after Svelte 5 upgrade - container conflict resolved)
- Frontend Container: **3003** (production deployments only)
- Backend API: **8000**
- PostgreSQL: **5433** (ARM64 PostgreSQL 16 - NOT 5432!)
- Redis: **6379**

**Port Conflict Resolution:**
```bash
# Kill processes on specific ports
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3004 | xargs kill -9  # Frontend Dev
lsof -ti:3003 | xargs kill -9  # Frontend Container
lsof -ti:5433 | xargs kill -9  # PostgreSQL (ARM64)
```

## Running Services - CRITICAL DISTINCTION
**DEVELOPMENT MODE (WHAT WE USE):**
- Frontend: Run locally with `cd frontend && npm run dev -- --port 3004` (port 3004)
- Backend/DB/Redis: Run in Rancher containers

**PRODUCTION/CONTAINER MODE:**
- Frontend: Container runs on port 3003
- Backend/DB/Redis: All in containers

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

## Development Tools (Expert Engineer Improvements)
- Health checks: `make test-health` - Run comprehensive smoke tests
- Port management: `make kill-ports`, `make check-ports`
- Clean environment: `make clean-dev`
- Route debugging: `curl http://localhost:8000/api/debug/routes`

## 🏗️ CRITICAL: System Architecture Repository
**BEFORE BUILDING ANY NEW FEATURE, CONSULT:**
- **File**: `/docs/SYSTEM_ARCHITECTURE_REPOSITORY.md`
- **Purpose**: Prevents breaking existing functionality when adding features
- **Contains**: API patterns, database schemas, frontend integration, testing templates
- **Rule**: ALL new development must follow the patterns in this repository

## 📊 CRITICAL: Database Schema Documentation
**COMPLETE DATABASE REFERENCE:**
- **File**: `/backend/docs/DATABASE_SCHEMA.md`
- **Purpose**: Complete and current database structure reference (Updated: 2025-07-12)
- **Contains**: 
  - All 11 tables with complete column definitions
  - Development-specific fields for Code Cortex functionality
  - Embeddings table structure for semantic search
  - Indexes, triggers, and performance optimizations
  - JSON schema examples and API response formats
  - Common query patterns and maintenance commands
- **Migration Notes**: ARM64 PostgreSQL with pgvector, normalized embeddings table
- **Usage**: Reference before any database changes, migrations, or new features

## Recent Features (DO NOT ROLLBACK BEFORE THESE)
- **NEW: GitHub Actions CI/CD Pipeline (2025-07-11)** - Comprehensive automated testing, security scanning, and deployment workflows
- **NEW: Svelte 5 Full Migration v2.3 (2025-07-11)** - Complete upgrade to Svelte 5.35.6, SvelteKit 2.22.5, Vite 7.0.4, Node.js >=24, resolved all security vulnerabilities, AI service fixes
- **NEW: Advanced Integrations v2.2 (2025-07-11)** - Vosk offline transcription, OpenTelemetry monitoring, pre-commit hooks  
- System Architecture Repository (2025-07-10) - Foundation for consistent development
- Expert Engineer Development Tools (2025-07-10) - Port management, health checks, debugging
- Fan3D component (commit b383191)
- Mac3D improvements (commit 468175f)
- Neural Motherboard Interface v4.2 (commit 0c97c5b)

## 🔒 Security & Future Planning

### Security Roadmap
- **File**: `SECURITY_FIXES.md` - Comprehensive security vulnerabilities roadmap
- **Status**: 15+ security issues identified by CI/CD pipeline (Bandit scanning)
- **Priority**: Address after authentication implementation (signup/login pages)
- **Critical Issues**: SQL injection, pickle deserialization, weak cryptography (MD5), hardcoded temp directories

### Development Environment Standards
- **Python**: 3.11+ with pip 25.1.1 (latest, auto-upgraded in CI/CD)
- **Node.js**: 20+ with npm latest (cached in CI/CD)
- **Package Management**: All dependencies pinned in requirements.txt and package-lock.json
- **CI/CD**: Version consistency enforced across all environments

### Future Development Tracking
- **Next Priority**: User authentication system (signup/login pages)
- **Security Fixes**: Scheduled after authentication completion
- **CI/CD Pipeline**: Automatically scans for security issues on every commit
- **Monitoring**: Weekly scheduled security scans and dependency vulnerability alerts