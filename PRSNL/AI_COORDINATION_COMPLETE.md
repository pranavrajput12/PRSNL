# 🤖 AI Coordination System - Complete Guide

## 🚀 Quick Start for All AI Agents

### ⚡ Critical Pre-Task Reading
Every AI model MUST read these files before starting ANY work:

1. **`/PRSNL/PROJECT_STATUS.md`** - Current project state and context
2. **`/PRSNL/TASK_HISTORY.md`** - Task tracking and history
3. **`/PRSNL/API_DOCUMENTATION.md`** - API contracts and patterns
4. **`/PRSNL/ARCHITECTURE.md`** - System architecture and design
5. **Your section below** - Your specific role and responsibilities

---

## 🎯 AI Agent Roles & Responsibilities

### 🎨 Claude Code (Architecture & Integration Lead)
**Role**: System architect, complex feature implementation, code review, Git operations

**Responsibilities**:
- System architecture and design decisions
- Complex feature implementation (AI services, integrations, business logic)
- Code review for all changes
- ALL Git operations (add, commit, push, pull, PR creation)
- Task breakdown and delegation to other AIs
- Integration of other AIs' work
- Performance optimization and debugging
- Documentation updates and maintenance

**Current Status**: Active - handling complex development tasks, web scraping fixes, documentation consolidation

**Recent Work**:
- Fixed web scraping system with meta-tag extraction
- Resolved "Untitled" errors in AI suggestions
- Updated all backend APIs (capture, import, worker) for new scraper
- Massive documentation consolidation (48 → 13 files)

**Critical Setup**:
```bash
# Essential commands
cd /PRSNL/backend && uvicorn app.main:app --reload --port 8000
cd /PRSNL/frontend && npm run dev -- --port 3002
curl http://localhost:8000/health
```

**What You Handle**:
- Complex API endpoints and business logic
- AI service implementations (Azure OpenAI, embeddings, vision)
- Database schema changes and migrations
- WebSocket implementations
- Authentication/authorization systems
- Performance optimization
- Integration testing and debugging
- Git operations and code reviews

---

### 🚀 Windsurf (Simple Frontend Tasks)
**Role**: UI/UX polish, simple frontend tasks only

**Responsibilities**:
- Simple UI components and styling updates
- Visual polish and hover effects
- Loading states and animations
- Icon and asset management
- Formatting and display improvements
- Basic responsive design adjustments

**Current Status**: Available for simple frontend tasks

**Critical Setup**:
```bash
# MUST run on port 3002
cd /PRSNL/frontend && npm run dev -- --port 3002
```

**Active Tasks**:
- Update loading spinners to consistent style
- Add friendly empty state messages
- Improve button hover states
- Format timestamps to relative time
- Add tooltips to icon buttons
- Create mobile menu icon

**What You CAN Do**:
- Update colors and spacing
- Add hover effects and transitions
- Improve loading states with spinners
- Format dates and numbers display
- Add tooltips and help text
- Update icons and visual assets
- Simple animations and transitions
- Button styles and card layouts
- Mobile responsiveness improvements

**What You CANNOT Do**:
- API calls or data fetching logic
- State management (stores) modifications
- Component props or TypeScript interfaces
- Backend files or server-side code
- Complex business logic
- New npm packages or dependencies
- New API endpoints or routes
- Database operations
- WebSocket connections

**Design Standards**:
- **Theme**: Manchester United red (#dc143c)
- **Framework**: SvelteKit with TypeScript
- **Components**: Use existing component patterns
- **Spacing**: Multiples of 4px or 8px
- **Fonts**: System font stack with proper weights

---

### 🧠 Gemini (Simple Backend Tasks)
**Role**: Backend utilities, scripts, testing, documentation

**Responsibilities**:
- Simple backend tasks and utility scripts
- Test data generation and population
- Database backup and maintenance scripts
- Log analysis and metrics collection
- Unit tests for utility functions
- API documentation examples
- Performance monitoring scripts

**Current Status**: Available for simple backend tasks

**Critical Setup**:
```bash
# Backend health check
curl http://localhost:8000/health
cd /PRSNL/backend && source venv/bin/activate
```

**Active Tasks**:
- Create comprehensive test data scripts
- Add API response time logging
- Database backup and restore scripts
- Write unit tests for utility functions
- Error log analysis scripts
- Health check endpoints
- Metrics collection scripts

**What You CAN Do**:
- Test data population scripts
- Database backup and restore scripts
- Log analysis and report generation
- Metrics collection and monitoring
- Unit tests for utility functions
- API documentation and examples
- Performance benchmarking scripts
- Health check implementations
- Error analysis and reporting
- Code comments and README updates

**What You CANNOT Do**:
- Core API endpoints or business logic
- Database schema changes or migrations
- Complex algorithms or AI implementations
- Authentication/authorization systems
- WebSocket implementations
- External service integrations
- Complex performance optimizations
- Git operations or code reviews

**Development Standards**:
- **Framework**: FastAPI with Python
- **Database**: PostgreSQL with proper error handling
- **Testing**: Use pytest for all tests
- **Documentation**: Clear docstrings and examples
- **Scripts**: Add proper error handling and logging

---

## 📋 New Task Lifecycle Management System

### 🚀 Task Initiation (ALWAYS Required)
```bash
# Before starting ANY task, always tag this file:
@TASK_INITIATION_GUIDE.md I'm starting task [TASK_ID] of type [TYPE]

# Examples:
@TASK_INITIATION_GUIDE.md I'm starting task CLAUDE-2025-07-09-001 of type Backend API
@TASK_INITIATION_GUIDE.md I'm starting task WINDSURF-2025-07-09-005 of type Frontend
@TASK_INITIATION_GUIDE.md I'm starting task GEMINI-2025-07-09-002 of type Backend Script
```

### ✅ Task Completion (ALWAYS Required)
```bash
# When completing ANY task, always tag this file:
@TASK_COMPLETION_GUIDE.md I completed task [TASK_ID], here's what changed: [SUMMARY]

# Examples:
@TASK_COMPLETION_GUIDE.md I completed task CLAUDE-2025-07-09-001, here's what changed: Added new video download API endpoint
@TASK_COMPLETION_GUIDE.md I completed task WINDSURF-2025-07-09-005, here's what changed: Updated all loading spinners to consistent styling
@TASK_COMPLETION_GUIDE.md I completed task GEMINI-2025-07-09-002, here's what changed: Created database backup script
```

### 🔗 Documentation Dependencies
```bash
# Check what files need updating for your task type:
@DOCUMENTATION_DEPENDENCIES.md What files need updating for [TASK_TYPE] changes?

# Examples:
@DOCUMENTATION_DEPENDENCIES.md What files need updating for Backend API changes?
@DOCUMENTATION_DEPENDENCIES.md What files need updating for Frontend changes?
@DOCUMENTATION_DEPENDENCIES.md What files need updating for Database changes?
```

### 📋 Legacy Task Management (DEPRECATED)
~~The old workflow below is deprecated. Use the new @-tagged file system above.~~

### 1. Session Start Protocol
```bash
# Read in this order:
1. /PRSNL/PROJECT_STATUS.md        # Current system state
2. /PRSNL/TASK_HISTORY.md          # Task tracking and history
3. Your role section above          # Your specific responsibilities
4. /PRSNL/API_DOCUMENTATION.md     # If touching APIs
```

### 2. Task Selection Rules
- **Claude**: Pick complex tasks involving architecture, integration, or business logic
- **Windsurf**: Pick simple UI polish tasks from your active list
- **Gemini**: Pick simple backend utility tasks from your active list

### 3. Before Starting Work
```bash
# Check for conflicts
grep "IN PROGRESS" /PRSNL/TASK_HISTORY.md
lsof -i :3002,8000  # Check port availability

# Update task status
echo "### Task [AI]-2025-01-08-001: [Task Name]" >> /PRSNL/TASK_HISTORY.md
echo "**Status**: IN PROGRESS" >> /PRSNL/TASK_HISTORY.md
echo "**Started**: $(date)" >> /PRSNL/TASK_HISTORY.md
```

### 4. During Work
- Make ONLY the changes specified in the task
- Follow existing architectural patterns
- Test changes locally before completing
- Add comments for complex logic
- Don't break existing functionality

### 5. Task Completion
```bash
# Update task status
sed -i 's/IN PROGRESS/COMPLETED/' /PRSNL/TASK_HISTORY.md
echo "**Completed**: $(date)" >> /PRSNL/TASK_HISTORY.md
echo "**Files Modified**: [list files]" >> /PRSNL/TASK_HISTORY.md
```

---

## 🔧 Critical System Information

### Port Allocation (NEVER CHANGE)
- **Frontend**: Port 3002 (Windsurf must use this)
- **Backend**: Port 8000 (Claude/Gemini coordinate)
- **Database**: Port 5433 (PostgreSQL 16)
- **Redis**: Port 6379 (if needed)

### Architecture Notes
- **ARM64 Environment**: Apple Silicon, use `/opt/homebrew`
- **PostgreSQL 16**: ARM64 compiled at `/opt/homebrew/opt/postgresql@16`
- **pgvector**: Must be compiled from source for PostgreSQL 16
- **Python**: Use python3 (system or Homebrew ARM64)

### Database Configuration
```bash
# Connection details
Database: prsnl
User: prsnl
Password: prsnl123
Host: 127.0.0.1
Port: 5433
Connection: postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl
```

### Essential Commands
```bash
# Start PostgreSQL
/opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 start

# Start Backend
cd /PRSNL/backend && uvicorn app.main:app --reload --port 8000

# Start Frontend
cd /PRSNL/frontend && npm run dev -- --port 3002

# Health checks
curl http://localhost:8000/health
curl http://localhost:3002/
```

---

## 🚨 Conflict Prevention & Resolution

### File Locking Protocol
When editing files, update task status with locked files:
```markdown
🔒 LOCKED by [AI]: /path/to/file.py (14:30-15:00)
```

### Port Conflicts
- **Never change assigned ports**
- If port occupied, STOP and coordinate
- Use `lsof -i :PORT` to check availability

### Task Conflicts
- Only one AI per task
- Check task history before starting
- Complex tasks go to Claude first

### Emergency Procedures
If blocked:
1. **STOP** - Don't proceed with conflicting work
2. **Document** the blocker in task status
3. **Wait** for human coordination
4. **Continue** with other non-conflicting tasks

---

## 📊 Success Metrics

### Quality Indicators
- **Zero Conflicts**: No file or port conflicts between AIs
- **Clean History**: All tasks properly tracked and attributed
- **Working Code**: All changes tested and functional
- **Clear Documentation**: All changes properly documented

### Efficiency Indicators
- **Fast Task Completion**: Tasks completed within estimated time
- **Clear Communication**: Minimal clarification needed
- **Parallel Work**: Multiple AIs working without conflicts
- **Consistent Quality**: Predictable output across all AIs

---

## 🔗 Quick Reference

### Key Files by Priority
1. **`PROJECT_STATUS.md`** - Always read first
2. **`TASK_HISTORY.md`** - Track all work here
3. **`API_DOCUMENTATION.md`** - API contracts and patterns
4. **`ARCHITECTURE.md`** - System design and patterns
5. **`QUICK_REFERENCE_COMPLETE.md`** - Troubleshooting and help

### AI-Specific Task Files (Legacy - Now Consolidated)
- All AI tasks are now managed in `TASK_HISTORY.md`
- Role-specific guidelines are in this file
- No more separate task files to maintain

### Essential Commands by Role
**Claude:**
```bash
git status && git add . && git commit -m "feat: description"
uvicorn app.main:app --reload --port 8000
pytest -v
```

**Windsurf:**
```bash
npm run dev -- --port 3002
npm run check  # TypeScript validation
```

**Gemini:**
```bash
python3 -m pytest tests/
python3 scripts/backup_database.py
```

---

## 🎯 Current System Status

### Recent Major Work (2025-07-09)
- **Web Scraping System**: Fixed meta-tag extraction, eliminated "Untitled" errors
- **Backend APIs**: Updated capture, import, worker APIs for new scraper
- **Content Processing**: Now focuses on og:title, meta description extraction
- **Documentation**: Consolidated 48 files → 13 files (73% reduction)

### Active Priorities
1. **Test Additional Platforms**: Vimeo, Twitter video support
2. **Content Quality**: Improve meta-tag extraction for sites without proper tags
3. **Performance**: Optimize for larger datasets
4. **UI Polish**: Complete Windsurf's simple frontend tasks

### System Health
- **Backend**: Fully operational on port 8000
- **Frontend**: Fully operational on port 3002
- **Database**: PostgreSQL 16 with pgvector, ~30 items
- **AI Services**: Azure OpenAI integration working

---

This consolidated guide replaces all previous AI coordination files and provides a single source of truth for all AI agents working on PRSNL.