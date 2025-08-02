# PRSNL Project Configuration for Claude

## 🚨 ALWAYS USE AGENTS FOR COMPLEX TASKS
**Before doing manual work, check if an agent can handle it better. See "Claude Code Agents" section below.**
- Use `general-purpose` agent for complex searches and research
- Use `debug-accelerator` for debugging issues
- Use `ui-ux-optimizer` for component audits
- Use specialized agents for their domains

## ✅ Cipher MCP Integration (21 AI Development Tools)
**SUCCESSFULLY CONFIGURED** - Cipher MCP provides 21 AI development tools in aggregator mode:
- **File Operations**: read_file, write_file, edit_file, create_directory, search_files, etc.
- **Memory Management**: cipher_memory_search, cipher_extract_and_operate_memory, etc.
- **Reasoning Tools**: cipher_store_reasoning_memory, cipher_evaluate_reasoning, etc.
- **Configuration**: `.env.cipher` with `MCP_SERVER_MODE=aggregator`
- **Azure OpenAI**: Integrated through OpenAI-compatible interface

## CRITICAL: Database Configuration
**WE USE LOCAL POSTGRESQL, NOT DOCKER DATABASE**
- Database: Local PostgreSQL on port 5432 (ARM64 version)
- User: pronav
- Database name: prsnl
- Do NOT use Docker database (it's commented out in docker-compose.yml)

## 🚨 CRITICAL: Architecture Configuration (Apple Silicon M1/M2)
**THIS SYSTEM RUNS ON ARM64 ARCHITECTURE - DO NOT MIX WITH x86_64**

### Colima Resource Requirements
- **CPU**: 4 cores minimum (for DragonflyDB + Auth services)
- **Memory**: 8GB minimum (4GB for containers + 4GB overhead)  
- **Disk**: 100GB recommended (container images + volumes)
- **Architecture**: ARM64 native (Apple Silicon optimized)
- **Start Command**: `colima start --cpu 4 --memory 8 --disk 100`

### PostgreSQL Architecture Setup
- **ALWAYS USE**: `/opt/homebrew/` (ARM64 Homebrew) for PostgreSQL
- **NEVER USE**: `/usr/local/` (Intel x86_64 Homebrew) for PostgreSQL
- **Current PostgreSQL**: ARM64 PostgreSQL 16 on port 5432
- **pgvector**: Must be built for ARM64 architecture

### Common Architecture Issues (AVOID THESE):
1. **DO NOT** install or use PostgreSQL from `/usr/local/` (Intel Homebrew)
2. **DO NOT** mix pgvector builds between architectures
3. **DO NOT** change PostgreSQL port from 5432 to 5432
4. **DO NOT** use `brew` from `/usr/local/bin/brew` - use `/opt/homebrew/bin/brew`

### Verify Correct Setup:
```bash
# Check PostgreSQL is ARM64
file /opt/homebrew/opt/postgresql@16/bin/postgres  # Should show: arm64

# Check pgvector extension
/opt/homebrew/opt/postgresql@16/bin/psql -U pronav -p 5432 -d prsnl -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Check which PostgreSQL is running
lsof -p $(pgrep -f postgres | head -1) | grep bin/postgres
```

### If pgvector Breaks Again:
1. Stop any x86_64 PostgreSQL: `/usr/local/bin/brew services stop postgresql@16`
2. Start ARM64 PostgreSQL: `/opt/homebrew/bin/brew services start postgresql@16`
3. Verify database is on port 5432 in `.env` and `config.py`
4. pgvector should already be installed in ARM64 PostgreSQL

## Container Runtime - Phase 3 Configuration
- We use **Colima** for containers (Apple Silicon optimized)
- **DragonflyDB** runs in Colima containers (replaced Redis - 25x faster)
- Backend runs locally for better development experience
- AI agents run as part of backend process (not containerized)

## Ports (Exclusive Port Ownership) - Phase 3 Updated
- Frontend Development: **3004** (Updated from 3003 after Svelte 5 upgrade - container conflict resolved)
- Frontend Container: **3003** (production deployments only)
- Backend API: **8000** (includes AI API endpoints)
- PostgreSQL: **5432** (ARM64 PostgreSQL 16 - NOT 5432!)
- DragonflyDB: **6379** (replaced Redis - 25x performance improvement)
- **NEW**: LibreChat API: `/api/ai/*` endpoints

**Port Conflict Resolution:**
```bash
# Kill processes on specific ports
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3004 | xargs kill -9  # Frontend Dev
lsof -ti:3003 | xargs kill -9  # Frontend Container
lsof -ti:5432 | xargs kill -9  # PostgreSQL (ARM64)

# Colima container management
colima status                   # Check Colima status
colima start --cpu 4 --memory 8 --disk 100  # Start with resources
colima stop                     # Stop Colima containers
```

## Running Services - CRITICAL DISTINCTION
**DEVELOPMENT MODE (WHAT WE USE):**
- Frontend: Run locally with `cd frontend && npm run dev -- --port 3004` (port 3004)
- Backend: Run locally with AI integration
- Database: Local ARM64 PostgreSQL 16 on port 5432
- Cache: DragonflyDB in Colima container

**PRODUCTION/CONTAINER MODE:**
- Frontend: Container runs on port 3003
- Backend/DB/Redis: All in containers

**NEVER DO THIS:**
- Do NOT run frontend container when doing development
- Do NOT start frontend container on port 3003 (conflicts with dev server)
- The frontend container is ONLY for production deployments

**Colima Development Workflow:**
```bash
# Quick start all services (recommended)
./scripts/start-colima-services.sh

# Check service health
./scripts/colima-health-check.sh

# Graceful shutdown (keeps Colima running)
./scripts/stop-colima-services.sh

# Full shutdown (stops Colima too)
./scripts/stop-colima-services.sh --stop-colima

# Always stop frontend container during development
docker-compose stop frontend
```

## 🤖 Claude Code Agents - USE THESE FOR COMPLEX TASKS

**IMPORTANT: Always use agents for tasks that match their descriptions. This improves performance and accuracy.**

### Available Agents:

#### 1. **general-purpose**
- **Purpose**: General-purpose agent for researching complex questions, searching for code, and executing multi-step tasks
- **When to use**: 
  - Searching for files/code when not confident about exact matches
  - Complex research requiring multiple searches
  - Multi-step analysis tasks
- **Pre-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh recall "PRSNL architecture overview"
  ./scripts/prsnl-cipher.sh recall "[search topic]"  # Check existing knowledge
  ./scripts/prsnl-cipher.sh recall "previous searches: [similar topic]"
  ```
- **Post-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh store "SEARCH RESULT: [topic] → found in [files]"
  ./scripts/prsnl-cipher.sh store "CODE PATTERN: [pattern found] in [location]"
  ./scripts/prsnl-cipher.sh store "ARCHITECTURE INSIGHT: [discovery about system]"
  ```
- **Example**:
  ```
  Task(description="Find all API endpoints", prompt="Search for all API endpoints in the backend and analyze their authentication requirements", subagent_type="general-purpose")
  ```

#### 2. **url-architecture-manager**
- **Purpose**: Design, analyze, and restructure URL hierarchies and routing patterns in SvelteKit projects
- **When to use**:
  - Reorganizing site URL structure
  - Optimizing template inheritance
  - Implementing SEO-friendly permalinks
  - Managing hierarchical content taxonomies
- **Pre-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh recall "URL PATTERN"  # Check existing URL patterns
  ./scripts/prsnl-cipher.sh recall "routing architecture"
  ./scripts/prsnl-cipher.sh recall "SEO patterns"
  ```
- **Post-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh store "URL PATTERN: [route type] → [pattern used]"
  ./scripts/prsnl-cipher.sh store "ROUTING DECISION: Chose [pattern] because [reason]"
  ./scripts/prsnl-cipher.sh store "SEO SUCCESS: [URL structure] improved [metric]"
  ```
- **Example**:
  ```
  Task(description="Optimize URL structure", prompt="Analyze and propose optimized URL hierarchy for the blog section", subagent_type="url-architecture-manager")
  ```

#### 3. **feature-ideator-pkm**
- **Purpose**: Generate innovative feature ideas for PRSNL PKM based on user insights, feedback, or market trends
- **When to use**:
  - Processing user feedback for feature ideas
  - Analyzing PKM market trends
  - Prioritizing features with RICE scoring
- **Pre-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh recall "FEATURE REQUEST"  # Check similar requests
  ./scripts/prsnl-cipher.sh recall "user feedback patterns"
  ./scripts/prsnl-cipher.sh recall "RICE scores"
  ```
- **Post-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh store "FEATURE IDEA: [name] → RICE score [score]"
  ./scripts/prsnl-cipher.sh store "USER INSIGHT: [feedback pattern] suggests [feature]"
  ./scripts/prsnl-cipher.sh store "MARKET TREND: [trend] → opportunity for [feature]"
  ```
- **Example**:
  ```
  Task(description="Generate features from feedback", prompt="Here's user feedback: [feedback]. Generate prioritized feature ideas with RICE scores", subagent_type="feature-ideator-pkm")
  ```

#### 4. **roadmap-planner**
- **Purpose**: Transform strategic objectives and backlog items into structured, time-boxed product roadmaps
- **When to use**:
  - Creating product roadmaps from OKRs
  - Organizing backlog into epics
  - Planning quarterly releases
- **Pre-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh recall "OKR history"
  ./scripts/prsnl-cipher.sh recall "sprint velocity"
  ./scripts/prsnl-cipher.sh recall "backlog patterns"
  ```
- **Post-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh store "ROADMAP DECISION: [epic] scheduled for [timeline]"
  ./scripts/prsnl-cipher.sh store "EPIC BREAKDOWN: [epic] → [tasks list]"
  ./scripts/prsnl-cipher.sh store "VELOCITY INSIGHT: Team can handle [X] story points/sprint"
  ```
- **Example**:
  ```
  Task(description="Create Q2 roadmap", prompt="Create roadmap from these OKRs: [okrs] and backlog: [items]", subagent_type="roadmap-planner")
  ```

#### 5. **ui-ux-optimizer**
- **Purpose**: Audit UI/UX aspects of Svelte components for accessibility (WCAG 2.2 AA), visual consistency, and usability
- **When to use**:
  - After creating/modifying Svelte components
  - Reviewing CSS changes
  - Ensuring accessibility compliance
- **Pre-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh recall "COMPONENT PATTERN"  # Check existing components
  ./scripts/prsnl-cipher.sh recall "accessibility issues"
  ./scripts/prsnl-cipher.sh recall "PRSNL theme patterns"
  ```
- **Post-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh store "ACCESSIBILITY FIX: [issue] → [solution]"
  ./scripts/prsnl-cipher.sh store "UX PATTERN: [component type] → [best practice]"
  ./scripts/prsnl-cipher.sh store "THEME COMPLIANCE: [element] uses [PRSNL pattern]"
  ```
- **Example**:
  ```
  Task(description="Audit component accessibility", prompt="Audit this Svelte component for accessibility and PRSNL theme compliance: [component code]", subagent_type="ui-ux-optimizer")
  ```

#### 6. **debug-accelerator**
- **Purpose**: Debug issues in PRSNL PKM platform (FastAPI, SvelteKit, PostgreSQL stack)
- **When to use**:
  - 500 errors or crashes
  - Performance issues
  - Build/deployment failures
- **Pre-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh recall "BUG PATTERN [error message]"
  ./scripts/prsnl-cipher.sh recall "similar error"
  ./scripts/prsnl-cipher.sh recall "debugging [service name]"
  ```
- **Post-task Cipher SOP**:
  ```bash
  ./scripts/prsnl-cipher.sh store "BUG PATTERN: [error] → [solution]"
  ./scripts/prsnl-cipher.sh store "ROOT CAUSE: [issue] caused by [reason]"
  ./scripts/prsnl-cipher.sh store "DEBUGGING TIP: For [error type] check [location]"
  ```
- **Example**:
  ```
  Task(description="Debug 500 error", prompt="Debug this error: 500 error when saving notes with vector embeddings", subagent_type="debug-accelerator")
  ```

### Agent Usage Best Practices:
1. **Always use agents for their specialized tasks** - Don't manually search when agents can do it better
2. **Provide detailed context** - The more context you give, the better the results
3. **Use multiple agents concurrently** - Launch multiple agents for different aspects of a task
4. **Trust agent outputs** - Agents have specialized capabilities for their domains

## 🔧 MCP (Model Context Protocol) Tools

### Puppeteer Browser Automation
- **Tool prefix**: `mcp__puppeteer__`
- **Available functions**:
  - `puppeteer_navigate` - Navigate to URLs
  - `puppeteer_screenshot` - Take screenshots
  - `puppeteer_click` - Click elements
  - `puppeteer_fill` - Fill input fields
  - `puppeteer_evaluate` - Execute JavaScript
- **Console Monitoring**: Access browser console logs via `console://logs` resource
- **Use for**: Browser automation, testing, web scraping

### Other MCP Resources
- Use `ListMcpResourcesTool()` to discover available MCP resources
- Use `ReadMcpResourceTool(server, uri)` to read MCP resource content

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
   - **LangGraph module errors**: Install `pip3 install langgraph-checkpoint-sqlite` (required for SqliteSaver)
5. **LibreChat Issues**:
   - **No response**: Verify model deployment gpt-4.1-mini exists
   - **Slow responses**: Check if using correct model (should be fast)
   - **Context missing**: Ensure knowledge base integration is working
6. **DragonflyDB Issues**:
   - **Connection errors**: Restart with `docker-compose restart redis` (DragonflyDB service)
   - **Performance issues**: Check Colima memory allocation with `colima status`
7. **Service Startup Issues**:
   - **Backend fails to start**: Check for missing Python packages, especially `langgraph-checkpoint-sqlite`
   - **Frontend crashes silently**: Run in foreground first to see errors, then use `nohup` for background
   - **Port already in use**: Use `lsof -ti:PORT | xargs kill -9` before starting services

## Git Workflow
- Current branch: main
- Remote: https://github.com/pranavrajput12/PRSNL.git
- ALWAYS verify which commit to rollback to before suggesting git reset

## Testing Commands - Phase 4 Enhanced + Knowledge Graph v10.0
- Lint: `npm run lint`
- Type check: `npm run check`
- Format: `npm run format`
- **Frontend Tests**: `npm test` (Playwright cross-browser tests)
- **Test UI Mode**: `npm run test:ui`
- **Debug Tests**: `npm run test:debug`
- **Test Suites**: `npm run test:suite` (comprehensive), `npm run test:chat`, `npm run test:codemirror`

### **AI Services Health Checks**
- **AI health**: `curl http://localhost:8000/api/ai/health`
- **LibreChat health**: `curl http://localhost:8000/api/ai/health`
- **Full AI test**: `curl -X POST http://localhost:8000/api/ai/health`
- **AI Router status**: `curl http://localhost:8000/api/ai-router/status`
- **Enhanced routing test**: `curl -X POST http://localhost:8000/api/ai-router/test-routing -H "Content-Type: application/json" -d '{"content": "Test", "task_type": "text_generation", "priority": 8}'`
- **Dreamscape health**: `curl http://localhost:8000/api/persona/health`
- **Persona analysis test**: `curl -X POST http://localhost:8000/api/persona/analyze -H "Content-Type: application/json" -d '{"user_id": "123e4567-e89b-12d3-a456-426614174000", "analysis_depth": "light"}'`

### **🧠 Knowledge Graph System Tests (NEW v10.0)**
- **Knowledge Graph Stats**: `curl http://localhost:8000/api/unified-knowledge-graph/stats`
- **Full Graph Data**: `curl "http://localhost:8000/api/unified-knowledge-graph/visual/full?limit=50&min_confidence=0.6"`
- **Entity Types Filter**: `curl "http://localhost:8000/api/unified-knowledge-graph/visual/full?entity_type=knowledge_concept&limit=20"`
- **Item-Centered Graph**: `curl "http://localhost:8000/api/unified-knowledge-graph/visual/{item_id}?depth=2&limit=30"`

### **🎯 Semantic Clustering Tests (NEW v10.0)**
- **Semantic Clustering**: `curl -X POST http://localhost:8000/api/unified-knowledge-graph/clustering/semantic -H "Content-Type: application/json" -d '{"clustering_algorithm": "semantic", "max_clusters": 8, "min_cluster_size": 3}'`
- **Structural Clustering**: `curl -X POST http://localhost:8000/api/unified-knowledge-graph/clustering/semantic -H "Content-Type: application/json" -d '{"clustering_algorithm": "structural", "max_clusters": 6, "min_cluster_size": 4}'`
- **Hybrid Clustering**: `curl -X POST http://localhost:8000/api/unified-knowledge-graph/clustering/semantic -H "Content-Type: application/json" -d '{"clustering_algorithm": "hybrid", "max_clusters": 10, "min_cluster_size": 3, "min_confidence": 0.7}'`

### **🔍 Knowledge Gap Analysis Tests (NEW v10.0)**
- **Standard Gap Analysis**: `curl -X POST http://localhost:8000/api/unified-knowledge-graph/analysis/gaps -H "Content-Type: application/json" -d '{"analysis_depth": "standard", "min_severity": "medium", "include_suggestions": true}'`
- **Comprehensive Analysis**: `curl -X POST http://localhost:8000/api/unified-knowledge-graph/analysis/gaps -H "Content-Type: application/json" -d '{"analysis_depth": "comprehensive", "focus_domains": ["Technology", "AI"], "min_severity": "low"}'`
- **Quick Gap Check**: `curl -X POST http://localhost:8000/api/unified-knowledge-graph/analysis/gaps -H "Content-Type: application/json" -d '{"analysis_depth": "quick", "min_severity": "high"}'`

### **🛤️ Learning Path Discovery Tests (NEW v10.0)**
- **Path Discovery**: `curl -X POST http://localhost:8000/api/unified-knowledge-graph/paths/discover -H "Content-Type: application/json" -d '{"start_entity_id": "start-uuid", "end_entity_id": "end-uuid", "max_depth": 5, "min_confidence": 0.6}'`
- **Relationship-Filtered Paths**: `curl -X POST http://localhost:8000/api/unified-knowledge-graph/paths/discover -H "Content-Type: application/json" -d '{"start_entity_id": "start-uuid", "end_entity_id": "end-uuid", "relationship_types": ["explains", "builds_on", "prerequisite"], "max_depth": 4}'`

### **💡 Relationship Management Tests (NEW v10.0)**
- **Create Relationship**: `curl -X POST http://localhost:8000/api/unified-knowledge-graph/relationships -H "Content-Type: application/json" -d '{"source_entity_id": "uuid1", "target_entity_id": "uuid2", "relationship_type": "explains", "confidence_score": 0.8, "context": "Test relationship"}'`
- **Relationship Suggestions**: `curl -X POST http://localhost:8000/api/unified-knowledge-graph/relationships/suggest -H "Content-Type: application/json" -d '{"entity_id": "uuid", "limit": 10, "min_confidence": 0.6, "exclude_existing": true}'`
- **Delete Relationship**: `curl -X DELETE http://localhost:8000/api/unified-knowledge-graph/relationships/{relationship_id}`

### **⚡ Auto-Processing System Tests (NEW v10.0)**
- **Queue Status**: `curl http://localhost:8000/api/auto-processing/queue/status`
- **Process Item**: `curl -X POST http://localhost:8000/api/auto-processing/process-item/{item_id}`
- **Processing Status**: `curl http://localhost:8000/api/auto-processing/status/{processing_id}`
- **Batch Processing**: `curl -X POST http://localhost:8000/api/auto-processing/batch-process -H "Content-Type: application/json" -d '{"item_ids": ["uuid1", "uuid2"], "priority": "high"}'`

### **🔬 Entity Extraction Tests (NEW v10.0)**
- **Extract Entities**: `curl -X POST http://localhost:8000/api/entity-extraction/extract/{item_id} -H "Content-Type: application/json" -d '{"content_type": "article", "extraction_options": {"include_relationships": true, "confidence_threshold": 0.7}}'`
- **List Entities**: `curl "http://localhost:8000/api/entity-extraction/entities?entity_type=knowledge_concept&min_confidence=0.6"`
- **Entity Stats**: `curl http://localhost:8000/api/entity-extraction/stats`

### **🧪 Integration Tests**
- **Backend Integration**: `cd backend && python3 test_integrations.py`
- **Knowledge Graph Integration**: `cd backend && python3 test_entity_extraction_comprehensive.py`
- **Entity Extraction Stats**: `cd backend && python3 test_entity_extraction_stats.py`
- **API Endpoint Test**: `cd backend && python3 test_api_endpoint.py`

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
- **Colima Health Check**: `./scripts/colima-health-check.sh` - Comprehensive Colima service health check
- **Service Management**: `./scripts/start-colima-services.sh` - Start essential Colima services
- **Service Shutdown**: `./scripts/stop-colima-services.sh` - Gracefully stop services
- Port management: `make kill-ports`, `make check-ports`
- Clean environment: `make clean-dev`
- Route debugging: `curl http://localhost:8000/api/debug/routes`
- **NEW**: HTTPie API testing: `http GET localhost:8000/health`

## 🧠 CIPHER AI Memory Layer for Development

**CRITICAL: Cipher provides persistent memory for PRSNL development sessions**

### What Cipher Adds to Development:
- **Persistent Context**: Never re-explain PRSNL architecture to Claude Code
- **Cross-Session Memory**: Remembers complex port configurations, ARM64 specifics, authentication flows
- **Team Knowledge Sharing**: Share solutions and patterns across developers
- **Intelligent Problem Resolution**: Recalls previous solutions to similar issues
- **Development Consistency**: Maintains coding standards and architectural decisions
- **Automated Context Loading**: Claude Code understands PRSNL complexity instantly
- **Solution Memory**: Tracks debugging solutions and architectural reasoning

### Key Cipher Commands:
```bash
# Daily workflow
cipher "Today's progress: [what you accomplished]"
cipher recall "PRSNL architecture overview"

# Problem solving
cipher recall "similar error: 500 internal server"
cipher "Solution: [problem] fixed by [solution]"

# Architecture tracking
cipher "ADR-001: Chose pgvector over Pinecone because [reasons]"
```

### Critical PRSNL Memories (Pre-seeded):
- PostgreSQL runs on port 5432 (ARM64), pgvector via /opt/homebrew
- Frontend: dev=3004, production=3003, Azure OpenAI: gpt-4.1 + text-embedding-ada-002
- Auth: Keycloak (8080) + FusionAuth (9011), development bypasses in SECURITY_BYPASSES.md
- Testing: Playwright cross-browser, agents: general-purpose, debug-accelerator, ui-ux-optimizer
- Key files: CLAUDE.md, DATABASE_SCHEMA.md, CRASH_RECOVERY_GUIDE.md

### Setup & Usage:

**🎉 AUTOMATIC MEMORY NOW WORKING!**

#### Start Cipher Memory (One Time):
```bash
# Start the Azure OpenAI proxy for Cipher
./scripts/start-cipher.sh
```

#### Use Cipher Normally:
```bash
# Set environment variables (add to your shell profile)
export OPENAI_API_KEY="sk-cipher-azure-proxy"
export OPENAI_BASE_URL="http://localhost:8002/v1"

# Now Cipher works automatically with Claude Code!
cipher "Your development insight"
cipher recall "search term"
```

**✅ Azure OpenAI Integration**: 
- **Solution**: SDK proxy on port 8002 handles Azure auth
- **Proxy**: `/scripts/cipher-azure-proxy.py` using official OpenAI SDK
- **Config**: `~/.cipher/cipher.yml` points to localhost:8002
- **Automatic**: Works seamlessly with Claude Code MCP

**How It Works**:
1. Proxy receives OpenAI-format requests from Cipher
2. Uses `AzureOpenAI` SDK to handle auth conversion
3. Returns responses in OpenAI format
4. Cipher stores memories automatically

**Manual File-Based Backup**:
- Still available: `./scripts/cipher-prsnl` for file-based memory
- Location: `.cipher-memories/` directory

**Full Documentation**: 
- `/docs/CIPHER_IMPLEMENTATION.md` - Cipher setup guide
- Check proxy logs: `scripts/cipher-proxy.log`

### 🚀 AUTOMATIC CIPHER INDEXING (Run These Scripts)

**IMPORTANT: Agents should automatically run these scripts when appropriate:**

#### 1. Initial Setup (Run once or after major changes):
```bash
# Index all critical documentation files (50+ files)
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/scripts
./cipher-index-critical-files.sh

# Index codebase patterns (routes, services, models)
./cipher-index-codebase.sh
```

#### 2. Daily Development (Run at start of session):
```bash
# Load project context into memory
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/scripts
./prsnl-cipher.sh recall "PRSNL architecture"
./prsnl-cipher.sh recall "port"
./prsnl-cipher.sh recall "BUG PATTERN"
```

#### 3. End of Day (Run before session end):
```bash
# Capture daily patterns and insights
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/scripts
./cipher-daily-index.sh
```

#### 4. Component Development (Run when working with UI):
```bash
# Check component inventory before creating new ones
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/scripts
./component-inventory.sh
```

### Agent-Specific Cipher Integration
All agents now have pre/post task SOPs for Cipher integration. See agent descriptions above for specific commands each agent should run.

## 🤖 CIPHER PATTERN ANALYSIS AUTOMATION

**CRITICAL: Automated pattern quality improvement using CrewAI**

### What This Automation Provides:
- **Self-Improving AI Memory**: Cipher patterns automatically improve in quality over time
- **Pattern Quality Monitoring**: Weekly assessment of pattern completeness, accuracy, and usefulness
- **Relationship Discovery**: Automatic discovery of connections between patterns for better knowledge clustering
- **Gap Analysis**: Identification of missing knowledge areas for targeted improvements
- **Agent Effectiveness**: Claude Code agents become more effective with higher-quality patterns

### 🕒 Automated Schedule:
- **Weekly Analysis**: Every Sunday at 2 AM (or when triggered by development activity)
- **Trigger-Based**: Automatically runs after >10 new patterns are added
- **Agent-Triggered**: Agents automatically trigger analysis when pattern quality issues are detected
- **On-Demand**: Manual trigger available for immediate analysis

### 🚀 Quick Commands:

#### **Run Pattern Analysis** (Most Important):
```bash
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/scripts

# Full analysis (recommended weekly)
./cipher-pattern-analysis.sh

# Quick quality check
./cipher-pattern-analysis.sh quality async

# Check if analysis is overdue
./cipher-pattern-analysis.sh --check
```

#### **Check Analysis Status**:
```bash
# Quick status
./cipher-analysis-status.sh

# Detailed history
./cipher-analysis-status.sh history

# Quality trends
./cipher-analysis-status.sh trends

# Comprehensive summary
./cipher-analysis-status.sh summary
```

### 📊 Quality Metrics Tracked:
- **Pattern Completeness**: Patterns have sufficient detail and context
- **Solution Coverage**: Bug patterns include solutions (target >90%)
- **Context Validation**: Patterns include file paths and service locations
- **Format Consistency**: Standardized pattern structure
- **Overall Quality Score**: Composite score (current: 85.59%, target: >90%)

### 🔄 Agent Integration (AUTOMATIC):

**All 6 agents now automatically:**
1. **Check if analysis is overdue** before starting complex tasks
2. **Store new patterns** discovered during task execution
3. **Trigger analysis** if >5 new patterns are discovered in a session
4. **Reference improved patterns** for better task execution

**Agent-Specific Triggers:**
- **debug-accelerator**: Triggers analysis after fixing >3 bugs to improve bug patterns
- **general-purpose**: Triggers analysis after complex searches to improve search patterns
- **ui-ux-optimizer**: Triggers analysis after component audits to improve UI patterns

### 📈 Expected Improvements:
- **Pattern Quality**: 85.59% → 90%+ within 4 weeks
- **Agent Response Quality**: 20-30% improvement in accuracy and relevance
- **Development Velocity**: Faster problem resolution through better pattern matching
- **Knowledge Consistency**: Standardized patterns across all development areas

### 🔍 Monitoring & Logs:
- **Run History**: `/scripts/data/cipher-analysis-runs.log` - CSV log of all analysis runs
- **Error Logs**: `/scripts/cipher-analysis-errors.log` - Troubleshooting information
- **Cipher Memory**: Analysis results stored in Cipher memory with `PATTERN ANALYSIS:` prefix
- **Status Checks**: `./cipher-analysis-status.sh` for comprehensive monitoring

### 💡 Pro Tips:
- **Weekly Review**: Check `./cipher-analysis-status.sh trends` to monitor quality improvements
- **Manual Insights**: Add important discoveries manually: `./prsnl-cipher.sh store "INSIGHT: [discovery]"`
- **Pattern Standardization**: Use analysis recommendations to standardize pattern formats
- **Troubleshooting**: If analysis fails, check backend is running and Azure OpenAI is configured

### ⚡ Quick Setup Verification:
```bash
# Test the automation system
cd /Users/pronav/Personal\ Knowledge\ Base/PRSNL/scripts
./cipher-pattern-analysis.sh --check     # Check if analysis is overdue
./cipher-analysis-status.sh             # Show current status
```

**This automation runs automatically - no manual intervention required for weekly pattern quality improvement.**

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
- **NEW: Cipher AI Memory Layer (2025-08-01)** - Persistent development memory for Claude Code
  - **Feature**: AI memory layer that remembers PRSNL architecture, patterns, and solutions across sessions
  - **Integration**: Claude Code MCP server with Azure OpenAI embeddings (gpt-4.1 + text-embedding-ada-002)
  - **Benefits**: 50% reduction in context re-explanation, faster debugging, consistent architectural decisions
  - **Commands**: `cipher "memory"`, `cipher recall "topic"`, automatic memory via MCP integration
  - **Documentation**: `/docs/CIPHER_IMPLEMENTATION.md` - Complete setup and usage guide
- **NEW: Playwright Testing Migration (2025-08-01)** - Complete migration from Puppeteer to Playwright
  - **Removed**: All Puppeteer dependencies (146 packages removed)
  - **Added**: Playwright with cross-browser support (Chromium, Firefox, WebKit)
  - **Features**: Built-in console monitoring, auto-waiting, better debugging
  - **Test Scripts**: All test files converted to Playwright APIs
  - **MCP Integration**: `playwright-console-monitor` agent for real-time error detection
  - **Commands**: `npm test`, `npm run test:ui`, `npm run test:debug`
- **NEW: Dreamscape PersonaAnalysisCrew (2025-07-28)** - AI-powered personal intelligence system
  - **Feature**: 5-agent CrewAI system for comprehensive user persona analysis
  - **Agents**: Technical, Lifestyle, Learning, Cross-Domain, and Orchestrator agents
  - **API**: `/api/persona/*` endpoints for analysis and persona management
  - **Database**: 5 specialized tables for behavior tracking and persona storage
  - **Documentation**: Complete API docs and database schema documentation
  - **Test Command**: `curl http://localhost:8000/api/persona/health`
  - **Status**: Fully operational with Azure OpenAI integration
- **FIX: LangGraph Dependencies (2025-07-19)** - Resolved backend startup issues
  - **Issue**: Missing `langgraph-checkpoint-sqlite` package for SqliteSaver
  - **Solution**: Install with `pip3 install langgraph-checkpoint-sqlite`
  - **Impact**: Backend now starts successfully with all AI features operational
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
- **NEW: Advanced Integrations v2.2 (2025-07-11)** - whisper.cpp offline transcription, OpenTelemetry monitoring, pre-commit hooks  
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
4. **Verify Services**: Backend (8000), Frontend (3004), PostgreSQL (5432)
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