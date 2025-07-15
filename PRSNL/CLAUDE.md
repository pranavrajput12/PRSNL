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

## Container Runtime - Phase 3 Configuration
- We use Rancher Desktop for containers
- **DragonflyDB** runs in Docker (replaced Redis - 25x faster)
- Backend runs locally for better development experience
- AI agents run as part of backend process (not containerized)

## Ports (Exclusive Port Ownership) - Phase 3 Updated
- Frontend Development: **3004** (Updated from 3003 after Svelte 5 upgrade - container conflict resolved)
- Frontend Container: **3003** (production deployments only)
- Backend API: **8000** (includes AI API endpoints)
- PostgreSQL: **5433** (ARM64 PostgreSQL 16 - NOT 5432!)
- DragonflyDB: **6379** (replaced Redis - 25x performance improvement)
- **NEW**: LibreChat API: `/api/ai/*` endpoints

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
- Backend: Run locally with AI integration
- Database: Local ARM64 PostgreSQL 16 on port 5433
- Cache: DragonflyDB in Rancher container

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

## Phase 4 AI Development Patterns - LangGraph & Enhanced Routing

### AI Development
**Key Principles:**
1. **LangGraph Workflows**: State-based content processing with quality improvement loops
2. **Enhanced AI Router**: ReAct agent for intelligent provider selection and cost optimization
3. **LangChain Templates**: Centralized prompt management with versioning
4. **AI Integration**: Leverage Azure OpenAI for intelligent features
5. **Azure OpenAI Integration**: Use prsnl-gpt-4 for complex reasoning
6. **Model Selection**: Choose appropriate models for different tasks
7. **Context Enhancement**: Integrate knowledge base for better responses

### LibreChat Development
**Key Principles:**
1. **OpenAI Compatibility**: Maintain full OpenAI API compatibility
2. **Knowledge Base Integration**: Automatically enhance responses with PRSNL context
3. **Model Optimization**: Use gpt-4.1-mini for fast, cost-effective responses
4. **Streaming Support**: Real-time response delivery

**LibreChat Pattern:**
```python
# Use LibreChat-specific model
model_to_use = settings.AZURE_OPENAI_LIBRECHAT_DEPLOYMENT  # gpt-4.1-mini
response = await ai_service.complete(
    prompt=user_message,
    system_prompt=system_prompt,
    model=model_to_use  # Pass model explicitly
)
```

**Testing LibreChat:**
```bash
# Test chat completion
curl -X POST http://localhost:8000/api/ai/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-PRSNL-Integration: test" \
  -d '{"model": "prsnl-gpt-4", "messages": [{"role": "user", "content": "Test"}]}'

# Test streaming
curl -X POST http://localhost:8000/api/ai/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "prsnl-gpt-4", "messages": [{"role": "user", "content": "Test"}], "stream": true}'
```

### Azure OpenAI Configuration
**Critical Environment Variables:**
```bash
# Set these for Azure OpenAI integration
AZURE_OPENAI_API_VERSION = "2023-12-01-preview"  # Standard API version
AZURE_OPENAI_DEPLOYMENT = settings.AZURE_OPENAI_DEPLOYMENT
```

**Model Selection Strategy:**
- **prsnl-gpt-4**: Complex reasoning, multi-agent workflows, function calling
- **gpt-4.1-mini**: Fast chat responses, simple queries, cost optimization

## Common Issues & Solutions - Phase 3 Updated
1. **Old design showing**: Clear Vite cache with `rm -rf node_modules/.vite .svelte-kit`
2. **API errors**: Backend is at http://localhost:8000/api/
3. **Container issues**: Check Rancher Desktop app, NOT Docker
4. **AI Integration Issues**:
   - **Function calling errors**: Check Azure OpenAI API version is 2023-12-01-preview
   - **Model not found**: Ensure prsnl-gpt-4 deployment exists in Azure OpenAI
   - **Python cache issues**: Clear with `find . -name "*.pyc" -delete && find . -name "__pycache__" -exec rm -rf {} +`
   - **AI not responding**: Check AI service status with endpoints
5. **LibreChat Issues**:
   - **No response**: Verify model deployment gpt-4.1-mini exists
   - **Slow responses**: Check if using correct model (should be fast)
   - **Context missing**: Ensure knowledge base integration is working
6. **DragonflyDB Issues**:
   - **Connection errors**: Restart with `docker-compose restart dragonflydb`
   - **Performance issues**: Check Rancher Desktop memory allocation

## Git Workflow
- Current branch: main
- Remote: https://github.com/pranavrajput12/PRSNL.git
- ALWAYS verify which commit to rollback to before suggesting git reset

## Testing Commands - Phase 4 Enhanced
- Lint: `npm run lint`
- Type check: `npm run check`
- Format: `npm run format`
- **NEW**: AI health: `curl http://localhost:8000/api/ai/health`
- **NEW**: LibreChat health: `curl http://localhost:8000/api/ai/health`
- **NEW**: Full AI test: `curl -X POST http://localhost:8000/api/ai/health`
- **NEW**: AI Router status: `curl http://localhost:8000/api/ai-router/status`
- **NEW**: Enhanced routing test: `curl -X POST http://localhost:8000/api/ai-router/test-routing -H "Content-Type: application/json" -d '{"content": "Test", "task_type": "text_generation", "priority": 8}'`
- **NEW**: Integration tests: `cd backend && python3 test_integrations.py`

## HTTPie Integration for API Testing
**HTTPie is now installed for improved API debugging and testing.**

### Basic HTTPie Usage
```bash
# Health checks (simpler than curl)
http GET localhost:8000/health
http GET localhost:8000/api/ai/health

# RAG queries
http POST localhost:8000/api/rag/query query="What is FastAPI?"

# AI testing
http POST localhost:8000/api/ai-suggest \
  prompt="Test content" context:='{"type": "test"}'

# LibreChat testing
http POST localhost:8000/api/ai/chat/completions \
  model="prsnl-gpt-4" \
  messages:='[{"role": "user", "content": "Test"}]'
```

### HTTPie vs curl Comparison
```bash
# curl (old way)
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# HTTPie (new way)
http POST localhost:8000/api/rag/query query="test"
```

**HTTPie Documentation**: `/docs/HTTPIE_USAGE.md` - Complete usage guide with examples

## Development Tools (Expert Engineer Improvements)
- Health checks: `make test-health` - Run comprehensive smoke tests
- Port management: `make kill-ports`, `make check-ports`
- Clean environment: `make clean-dev`
- Route debugging: `curl http://localhost:8000/api/debug/routes`
- **NEW**: HTTPie API testing: `http GET localhost:8000/health`

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

## 🚫 TEMPORARILY DISABLED FEATURES
- **AI Insights Page (2025-07-14)** - Temporarily disabled from navigation menu
  - **Reason**: Will be redesigned with Cognitive Fingerprint feature in future
  - **Location**: `/insights` route still exists but not accessible via navigation
  - **Status**: Commented out in `+layout.svelte` navigation section
  - **Re-enable**: Uncomment lines 183-189 in `+layout.svelte` when ready

## Recent Features (DO NOT ROLLBACK BEFORE THESE)
- **NEW: Codebase Cleanup (2025-07-15)** - Major build & code quality tools optimization
  - **Build Tools**: Removed tsup, jscodeshift, ts-morph (76 packages total)
  - **Code Quality**: Consolidated ESLint/Prettier configs
  - **Impact**: 10-20% faster operations, $125/year CI/CD savings
  - **Documentation**: See `/docs/CODEBASE_CLEANUP_2025.md` for full report
- **FIXED: CodeMirror (2025-07-14)** - AI-powered repository intelligence system
  - **Status**: Fully operational after 500 error fix
  - **Issue**: Missing database connection imports in codemirror_service.py
  - **Fix Applied**: Added get_db_connection import, verified auth system
  - **Test Command**: `curl -X POST "http://localhost:8000/api/codemirror/analyze/1cbb79ce-8994-490c-87ce-56911ab03807" -H "Content-Type: application/json" -d '{"repo_id": "1cbb79ce-8994-490c-87ce-56911ab03807", "analysis_depth": "standard"}'`
  - **Features**: Repository analysis, pattern detection, AI insights, job persistence
  - **Frontend**: Available at http://localhost:3004/code-cortex/codemirror
- **NEW: Code Quality Tools (2025-07-13)** - isort + flake8 + Prettier with comprehensive CI/CD integration
- **NEW: HTTPie Integration (2025-07-13)** - Advanced API debugging and testing capabilities
- **IN DEVELOPMENT: Open Source Integrations (2025-07-13)** - Game-changing feature for Code Cortex
  - **Purpose**: Automatic discovery and intelligence for open source integrations
  - **Features**: AI-powered analysis, categorization by tech stack, integration recommendations
  - **API Endpoints**: `/api/integrations/*` - Discovery, analysis, recommendations
  - **Database**: `open_source_integrations` table with comprehensive metadata
  - **Detection**: Hybrid approach (automatic + user enhancement)
- **NEW: GitHub Actions CI/CD Pipeline (2025-07-11)** - Comprehensive automated testing, security scanning, and deployment workflows
- **NEW: Svelte 5 Full Migration v2.3 (2025-07-11)** - Complete upgrade to Svelte 5.35.6, SvelteKit 2.22.5, Vite 7.0.4, Node.js >=24, resolved all security vulnerabilities, AI service fixes
- **NEW: Advanced Integrations v2.2 (2025-07-11)** - Vosk offline transcription, OpenTelemetry monitoring, pre-commit hooks  
- System Architecture Repository (2025-07-10) - Foundation for consistent development
- Expert Engineer Development Tools (2025-07-10) - Port management, health checks, debugging
- Fan3D component (commit b383191)
- Mac3D improvements (commit 468175f)
- Neural Motherboard Interface v4.2 (commit 0c97c5b)

## 🚨 Crash Recovery & Session Management

### When Terminal Crashes
1. **Check Context**: `git log -1 --oneline` and `git status`
2. **Read Session State**: Check `CURRENT_SESSION_STATE.md` for active task
3. **Review Documentation**: `CRASH_RECOVERY_GUIDE.md` for specific scenarios
4. **Verify Services**: Backend (8000), Frontend (3004), PostgreSQL (5433)
5. **Resume Work**: Use `@CURRENT_SESSION_STATE.md Resume my last session`

### Critical Recovery Files
- **`CRASH_RECOVERY_GUIDE.md`** - Complete recovery procedures
- **`CURRENT_SESSION_STATE.md`** - Active task and progress tracking
- **`TASK_COMPLETION_GUIDE.md`** - Task completion procedures with crash recovery
- **`TASK_HISTORY.md`** - Historical context and recent completions

### Service Recovery Commands
```bash
# Backend (if hung)
lsof -ti:8000 | xargs kill -9
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Frontend (if hung)
lsof -ti:3004 | xargs kill -9
cd frontend && npm run dev -- --port 3004

# PostgreSQL (if needed)
/opt/homebrew/bin/brew services restart postgresql@16
```

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
- **Build Tools**: Vite is the sole bundler (tsup, jscodeshift, ts-morph removed on 2025-07-15)
- **Code Quality**: Single ESLint/Prettier configs (consolidated on 2025-07-15)

### Future Development Tracking
- **🚨 CRITICAL SECURITY**: Authentication bypasses added 2025-07-14 - see `SECURITY_BYPASSES.md`
  - WebSocket authentication disabled for development
  - Frontend using dummy tokens
  - **MUST FIX BEFORE ANY PUBLIC DEPLOYMENT**
- **CURRENT DEVELOPMENT**: Open Source Integrations feature (Game-changing)
  - **Phase 1**: Database schema + core services (Days 1-5)
  - **Phase 2**: AI-powered analysis + frontend integration (Days 6-10)
  - **Phase 3**: Advanced features + analytics dashboard (Days 11-15)
- **Next Priority**: User authentication system (signup/login pages)
- **Code Quality**: 22,038 flake8 issues identified (mostly whitespace)
  - **Critical**: 19 undefined names (F821) - potential bugs
  - **Medium**: 64 unnecessary f-strings (F541)
  - **Low**: 42 complex functions (C901) needing refactoring
- **Security Fixes**: Scheduled after authentication completion
- **CI/CD Pipeline**: Automatically scans for security issues on every commit
- **Monitoring**: Weekly scheduled security scans and dependency vulnerability alerts