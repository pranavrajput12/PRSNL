# Pending Tasks & Documentation - July 11, 2025

## PROJECT CONTEXT & OVERVIEW

**PRSNL** is a personal knowledge management system with AI-powered content capture, analysis, and organization. The system uses:
- **Backend**: FastAPI + PostgreSQL + Redis + OpenAI Azure integration
- **Frontend**: SvelteKit with neural/electrical themed UI design
- **Deployment**: Rancher Desktop containers (NOT Docker Desktop)
- **Ports**: Frontend dev server: 3003, Backend API: 8000, DB: 5432

**Current Session Goal**: Implementing advanced development content management with GitHub rich previews, AI-generated connections ("synapses"), and enhanced Code Cortex functionality.

---

## CRITICAL SYSTEM INFORMATION

### Database Connection
- **Host**: localhost:5432
- **Database**: prsnl
- **User**: postgres
- **Password**: postgres
- **Connection via backend**: Use backend APIs or docker-compose exec backend python3

### File Structure Context
```
/Users/pronav/Personal Knowledge Base/PRSNL/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── capture.py (main capture logic with rich preview)
│   │   │   └── development.py (development-specific endpoints)
│   │   ├── services/
│   │   │   └── preview_service.py (GitHub API integration)
│   │   ├── utils/
│   │   │   └── url_classifier.py (auto-detection logic)
│   │   └── worker.py (background processing)
│   └── requirements.txt (includes aiohttp==3.9.3)
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── code-cortex/ (development content hub)
│   │   │   └── items/ (individual item pages - NEEDS CREATION)
│   │   └── lib/api/development.ts (API functions)
└── docs/
    └── PENDING_TASKS_2025_07_11.md (this file)
```

### API Endpoints Working
- `GET /api/timeline` - Shows all content including development
- `GET /api/development/stats` - Development analytics
- `GET /api/development/docs` - Development documents with filtering
- `GET /api/development/categories` - Development categories
- `GET /api/items/{id}` - Individual item details
- `POST /api/capture` - Capture new content (with rich preview)

---

## COMPLETED WORK (Context for Tomorrow)

### ✅ URL Classification & Auto-Detection (WORKING)
**Files**: `/backend/app/utils/url_classifier.py`
- **Function**: `URLClassifier.classify_url(url)` returns classification data
- **Supports**: GitHub, Stack Overflow, documentation sites, tutorials
- **Auto-detects**: Programming language, project category, difficulty level, career relevance
- **Example**: `https://github.com/fastapi/fastapi` → `{'is_development': True, 'platform': 'github', 'programming_language': 'python'}`

### ✅ Rich Preview Service (WORKING)
**Files**: `/backend/app/services/preview_service.py`
- **GitHub Integration**: Uses GitHub API to fetch repo data, README, commits, languages
- **Requires**: `GITHUB_TOKEN` environment variable (optional, for higher rate limits)
- **Returns**: Comprehensive repo metadata including stars, forks, description, recent commits
- **Status**: Successfully generating previews (confirmed in logs: "🟢 Rich preview generated successfully")

### ✅ Capture API Integration (WORKING)
**Files**: `/backend/app/api/capture.py` lines 247-258
- **Logic**: When `item_type == 'development'` and URL provided, calls `preview_service.generate_preview()`
- **Storage**: Saves rich preview to `metadata['rich_preview']` field
- **Bug Fixed**: Development content no longer converted to "link" type when `enable_summarization=false`
- **Test URLs**: FastAPI repo successfully processed with rich preview

### ✅ Code Cortex Frontend (FUNCTIONAL)
**Files**: `/frontend/src/routes/code-cortex/`
- **Dashboard**: Shows real development statistics and recent activity
- **Docs Page**: Lists development documents with filtering and clickable links
- **Links Page**: Shows URL-based development content with external links
- **Navigation**: All items link to `/items/{id}` for detailed view
- **APIs Connected**: Real data flowing from development endpoints (4 items currently)

### ✅ Database Schema (READY)
**Columns in `items` table**:
- `programming_language` TEXT
- `project_category` TEXT  
- `difficulty_level` INTEGER (1-5)
- `is_career_related` BOOLEAN
- `learning_path` TEXT
- `code_snippets` JSONB
- `metadata` JSONB (stores rich_preview data)

---

## 🔴 IMMEDIATE TASKS (1-2 Hours Each)

### 1. Individual Item Page for Code Cortex
**Priority**: HIGH - **Estimated**: 1.5 hours
**Context**: All Code Cortex pages link to `/items/{id}` but this route doesn't exist

**Requirements**:
- Create `/frontend/src/routes/items/[id]/+page.svelte`
- Display full document content, metadata, tags
- Show rich preview data when available (GitHub stats, README snippets)
- Add edit/delete functionality
- Include related items/suggestions
- Use existing `/api/items/{id}` endpoint

**Design Specs**:
- Neural/electrical theme consistent with PRSNL design
- GitHub repos: Show stars, forks, language, recent commits
- Documentation: Show content with syntax highlighting
- Tags: Clickable tags that filter to related content
- Actions: Edit metadata, delete item, add to learning path

**API Endpoint**: `GET /api/items/{id}` returns full item data including metadata

### 2. GitHub Rich Preview Debugging  
**Priority**: HIGH - **Estimated**: 1 hour
**Context**: Rich preview generation works but data not visible in API responses

**Problem Analysis**:
- Logs confirm: "🟢 Rich preview generated successfully for https://github.com/fastapi/fastapi"
- Rich preview saved to `metadata['rich_preview']` during capture
- Worker processing may overwrite metadata during content processing
- API responses don't include rich_preview data

**Investigation Steps**:
1. Query database directly: `SELECT metadata FROM items WHERE id = '7cad48d3-386b-4b83-a8de-2cf8dd8d74c6'`
2. Check if `worker.py` preserves existing metadata when updating items
3. Verify API serialization includes full metadata object
4. Test metadata persistence through complete capture → worker → API flow

**Files to Check**:
- `/backend/app/worker.py` - Does it preserve metadata during processing?
- `/backend/app/core/capture_engine.py` - Metadata handling
- API response serialization in timeline, development, items endpoints

**Test Case**: FastAPI repo (ID: `7cad48d3-386b-4b83-a8de-2cf8dd8d74c6`) should have rich_preview in metadata

---

## 🔴 MEDIUM TASKS (2-3 Hours Each)

### 3. GitHub Rich Preview UI Enhancement
**Priority**: MEDIUM - **Estimated**: 2.5 hours
**Context**: Rich preview data exists but frontend doesn't display it properly

**Requirements**:
- Update timeline to show GitHub repo cards with stats
- Add GitHub-specific UI components (stars, forks, language badges)
- Display repo stats and README snippets in Code Cortex
- Design responsive preview cards for different content types

**Design Elements**:
- Repo cards: Name, description, stars/forks, language, last updated
- README snippets: First 300 characters with "Read more" link
- Language badges: Color-coded programming language indicators
- Platform icons: GitHub (🐙), Stack Overflow (📚), etc.

**Components to Create**:
- `GitHubRepoCard.svelte` - Rich repo display
- `ContentPreview.svelte` - Generic preview wrapper
- `LanguageBadge.svelte` - Programming language indicator

### 4. API Endpoints Enhancement
**Priority**: MEDIUM - **Estimated**: 2 hours
**Context**: Development APIs need to expose rich preview metadata

**Requirements**:
- Ensure development API returns rich_preview metadata
- Add dedicated endpoint for rich preview data if needed
- Update timeline API to include preview data
- Add preview data to search results

**Endpoints to Modify**:
- `GET /api/development/docs` - Include rich_preview in response
- `GET /api/timeline` - Add preview data to items
- `GET /api/search` - Include preview in search results
- New: `GET /api/items/{id}/preview` - Dedicated preview endpoint

---

## 🔴 COMPLEX TASKS (3+ Hours Each)

### 5. Phase 5.1: AI Trigger System Implementation
**Priority**: LOW - **Estimated**: 6+ hours
**Context**: Implement hybrid AI system for generating connections between development content

**Architecture Design**:
- **On-Ingest Trigger**: Analyze new content immediately for connections
- **Nightly Batch**: Process all content for deeper relationship analysis
- **OpenAI Integration**: Use GPT-4 for semantic analysis and connection detection

**Technical Requirements**:
- Background job scheduler (APScheduler or Celery)
- OpenAI prompt templates for relationship detection
- Connection scoring and ranking algorithm
- Database schema for storing relationships
- API endpoints for managing triggers

**Implementation Files**:
- `/backend/app/services/ai_trigger_service.py`
- `/backend/app/models/relationship.py`
- `/backend/app/tasks/` - Background job definitions
- Database migration for relationships table

### 6. Phase 5.2: Guide Generation Engine
**Priority**: LOW - **Estimated**: 8+ hours
**Context**: AI-powered guide generation from development content

**Three Prompt Templates**:
1. **Learning Guide**: "How to learn X technology" from collected resources
2. **Implementation Patterns**: "How to implement X feature" with code examples
3. **Troubleshooting**: "Common issues and solutions for X"

**Technical Requirements**:
- Dynamic prompt generation based on content type
- Guide versioning and update management
- Content templating and markdown formatting
- Guide quality scoring and validation
- Integration with existing development API

**Guide Structure**:
```
# Guide Title
## Prerequisites
## Step-by-Step Process
## Code Examples (from code_snippets)
## Related Resources (from captured items)
## Common Issues
## Next Steps
```

### 7. Phase 5.3: Relationship Analysis & Graph Model
**Priority**: LOW - **Estimated**: 10+ hours
**Context**: Build dependency graphs and relationship detection

**Graph Model Design**:
- Nodes: Development items (docs, repos, tutorials)
- Edges: Relationships (depends_on, similar_to, implements, troubleshoots)
- Weights: Relationship strength scores
- Metadata: Relationship type, confidence, created_date

**Algorithm Requirements**:
- Content similarity analysis (embeddings comparison)
- Dependency detection (imports, references, mentions)
- Technology stack grouping
- Learning path recommendations

**Visualization Components**:
- Interactive graph display (D3.js or similar)
- Node filtering and search
- Path highlighting and traversal
- Relationship editing interface

### 8. Phase 6: Frontend Synapses Management UI
**Priority**: LOW - **Estimated**: 8+ hours
**Context**: Neural-themed interface for managing AI-generated connections

**UI Components**:
- **Synapses Dashboard**: Overview of all connections
- **Interactive Graph**: Visual relationship display
- **Connection Editor**: Create/edit/delete relationships
- **Neural Animation**: Electrical pulses along connections
- **Search & Filter**: Find specific synapses

**Design Inspiration**:
- Neural network visualizations
- Electrical circuit diagrams
- Brain synapse animations
- Consistent with PRSNL's neural theme

### 9. Phase 7: Analytics and Success Metrics System
**Priority**: LOW - **Estimated**: 6+ hours
**Context**: Comprehensive metrics and analytics dashboard

**Metrics to Track**:
- Content capture frequency and types
- Learning path progress
- Synapse generation success rates
- User engagement with different content types
- Knowledge base growth over time

**Dashboard Components**:
- Real-time statistics
- Trend analysis charts
- Performance monitoring
- Usage heatmaps
- Export and reporting tools

---

## 🔧 DEBUGGING CONTEXT

### Primary Issue: Rich Preview Metadata Persistence
**Status**: 80% complete - generation works, exposure doesn't
**Evidence**: 
- Logs show "🟢 Rich preview generated successfully"
- API responses missing `metadata.rich_preview`
- Test case: FastAPI repo (7cad48d3-386b-4b83-a8de-2cf8dd8d74c6)

**Investigation Priority**:
1. Database direct query to confirm data exists
2. Worker metadata preservation check
3. API serialization verification
4. End-to-end flow testing

---

## 🧠 AI SYNAPSES DESIGN SPECS (User-Provided)

### Hybrid Trigger System
- **On-Ingest**: Immediate analysis for new content
- **Nightly Batch**: Deep analysis of all content
- **Three Prompt Recipes**: Learning guide, implementation patterns, troubleshooting

### Relationship Analysis
- **Dependency Graphs**: Technology relationships and prerequisites
- **Versioning**: Track changes in relationships over time
- **Success Metrics**: Connection accuracy and user engagement

### Frontend Library Recommendations (User-Provided)
- **Markdown**: react-markdown, mdx-bundler
- **Code Diff**: diff2html
- **Editors**: @uiw/react-md-editor
- **GitHub Display**: Custom components with GitHub API integration

---

## 📚 REFERENCE DOCUMENTATION

### Key API Endpoints
```bash
# Test development content
curl "http://localhost:8000/api/development/docs?limit=5"

# Check item details  
curl "http://localhost:8000/api/items/{id}"

# Test capture with GitHub URL
curl -X POST "http://localhost:8000/api/capture" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/user/repo", "content_type": "development"}'
```

### Database Queries
```sql
-- Check rich preview data
SELECT id, title, metadata->'rich_preview' FROM items WHERE type = 'development';

-- Development content overview
SELECT type, programming_language, project_category, COUNT(*) 
FROM items WHERE type = 'development' GROUP BY type, programming_language, project_category;
```

### Container Management
```bash
# Check containers (use Rancher, not Docker)
docker-compose ps

# Rebuild backend after changes
docker-compose build backend && docker-compose up -d backend

# View logs
docker-compose logs backend --tail=50
```

---

## 🎯 SUCCESS CRITERIA

### Immediate Goals (Tomorrow)
1. ✅ Individual item pages functional with rich preview display
2. ✅ Rich preview metadata visible in all API responses
3. ✅ GitHub repo cards showing in timeline and Code Cortex

### Medium-term Goals
1. ✅ AI synapses system generating meaningful connections
2. ✅ Guide generation producing useful learning resources
3. ✅ Relationship graphs providing navigation insights

### Long-term Vision
1. ✅ Comprehensive analytics showing knowledge base growth
2. ✅ Automated learning path recommendations
3. ✅ Intelligent content organization and discovery

---

**Document Created**: July 11, 2025  
**Status**: Development content system 70% complete  
**Next Session**: Start with individual item page creation  
**Critical**: This document contains ALL context needed to continue without questions