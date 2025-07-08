# CLAUDE.md

## AI-Assisted Development Guide for PRSNL

### Overview
This document provides comprehensive guidance for AI assistants (Claude, GPT, Gemini, etc.) working on the PRSNL project. It covers architecture understanding, development workflows, coding standards, and collaboration protocols for effective AI-human partnership in local-first knowledge management system development.

## Critical Project Documents

### 📊 Centralized Task Management
- **CENTRALIZED_TASK_MANAGEMENT.md** - Complete guide to task tracking system
- **PROJECT_STATUS.md** - Current project state and priorities
- **CONSOLIDATED_TASK_TRACKER.md** - All task history and tracking
- **MODEL_ACTIVITY_LOG.md** - Real-time activity updates
- **MODEL_COORDINATION_RULES.md** - Multi-agent collaboration rules

### 📋 Model-Specific Tasks
- **CLAUDE_TASKS.md** - Complex features and integration work
- **WINDSURF_TASKS.md** - Simple frontend UI tasks
- **GEMINI_TASKS.md** - Simple backend scripts and tests

### 🔧 Technical References
- **TROUBLESHOOTING_GUIDE.md** - All known issues and solutions
- **AZURE_MODELS_CONTEXT.md** - Azure OpenAI integration status
- **PORT_ALLOCATION.md** - Service port assignments
- **DATABASE_SCHEMA.md** - Database structure and mappings
- **API_DOCUMENTATION.md** - All API endpoints

## Project Understanding for AI Assistants

### 1. Core Project Identity
- **Name**: PRSNL (Personal Knowledge Management)
- **Type**: Multi-component local-first knowledge management system
- **Philosophy**: Privacy-first, zero-cost, keyboard-centric, Manchester United red themed
- **Architecture**: SvelteKit frontend + FastAPI backend + Chrome extension + Electron overlay
- **Data**: 100% local processing, no cloud dependencies, PostgreSQL + Ollama AI

### 2. Key Design Principles
```
Local-First Architecture:
├── All data stays on user's machine
├── No external API dependencies in production
├── Ollama for local AI processing
└── PostgreSQL for local data storage

Zero-Cost Operation:
├── No recurring fees or subscriptions
├── No cloud services required
├── Self-hosted and self-contained
└── Open source and transparent

Performance First:
├── Sub-second search on 100k+ items
├── Maximum 4 keystrokes to any action
├── Instant feedback and responsiveness
└── Optimized for knowledge workers

Design Consistency:
├── Manchester United red (#dc143c) primary color
├── Mulish + Poppins typography
├── Professional, clean, modern UI
└── Consistent across all components
```

### 3. Component Architecture Map
```
PRSNL/
├── frontend/           # SvelteKit web application
│   ├── src/routes/     # Page components
│   ├── src/lib/        # Shared utilities and components
│   └── static/         # Static assets
│
├── backend/            # FastAPI Python API
│   ├── app/api/        # REST endpoints
│   ├── app/core/       # Business logic
│   └── app/db/         # Database models
│
├── extension/          # Chrome browser extension
│   ├── manifest.json   # Extension configuration
│   ├── background.js   # Service worker
│   ├── popup.html      # Extension popup
│   └── content.js      # Page injection
│
├── overlay/            # Electron desktop overlay
│   ├── main.js         # Main process
│   ├── renderer.js     # UI process
│   └── index.html      # Overlay interface
│
└── docs/               # Comprehensive documentation
    ├── PROJECT_ANALYSIS.md
    ├── DATA_FLOW.md
    ├── EXTERNAL_INTERFACES.md
    ├── DEVELOPMENT_SETUP.md
    ├── INTERFACE_DOCUMENTATION.md
    ├── BUILD_DEPLOYMENT.md
    └── CLAUDE.md (this file)
```

## AI Development Workflow

### 1. Before Starting Any Task

#### Read Current State (Updated Process)
```bash
# Follow the centralized task management system
1. Read CENTRALIZED_TASK_MANAGEMENT.md - Understand the process
2. Read PROJECT_STATUS.md - Current system state
3. Read MODEL_ACTIVITY_LOG.md - Check for active work
4. Read your task file (CLAUDE_TASKS.md, etc.) - Get your assignments
5. Check CONSOLIDATED_TASK_TRACKER.md - See task history
```

#### Claim Your Task
```markdown
# In CONSOLIDATED_TASK_TRACKER.md:
### Task CLAUDE-2025-01-08-001: Implement Feature X
**Status**: IN PROGRESS
**Started**: 2025-01-08 14:30
**Assigned**: Claude
**Files**: 
  - /backend/app/api/feature.py
  - /frontend/src/routes/feature/+page.svelte
```

#### Log Your Activity
```markdown
# In MODEL_ACTIVITY_LOG.md:
### 2025-01-08 - Claude
#### Implement Feature X (CLAUDE-2025-01-08-001)
- **14:30**: Started implementation
- **14:45**: Created API endpoint
- **15:00**: Added frontend component
- **15:15**: Completed with tests
```

### Key Commands to Run
```bash
# Before starting any work
git pull --rebase
cat PROGRESS_TRACKER.md  # Check for active work

# Check for conflicts
git status
git branch -a

# Run tests (when test framework is set up)
# npm test
# pytest
# cargo test

# Run linter (when linter is configured)
# npm run lint
# ruff check
# cargo clippy
```

#### Understand the Request
- Identify which component(s) are affected
- Determine if it's a new feature, bug fix, or refactoring
- Check for dependencies between components
- Assess impact on existing functionality

### 2. During Development

#### Component-Specific Guidelines

**Frontend (SvelteKit) Tasks:**
```svelte
<!-- Always follow these patterns -->

<!-- 1. Import organization -->
<script>
  // External imports first
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  
  // Internal imports
  import Icon from '$lib/components/Icon.svelte';
  import { formatDate } from '$lib/utils/date.js';
  
  // Props and reactive variables
  export let items = [];
  let searchQuery = '';
  $: filteredItems = items.filter(item => 
    item.title.toLowerCase().includes(searchQuery.toLowerCase())
  );
</script>

<!-- 2. Always use design system -->
<div class="page">
  <h1 class="page-title">Page Title</h1>
  <!-- Use established color palette -->
  <button class="btn btn-primary">
    <Icon name="plus" />
    Action
  </button>
</div>

<style>
  /* 3. Use CSS custom properties */
  .page {
    background: var(--color-background);
    color: var(--color-text);
  }
  
  .btn-primary {
    background-color: var(--color-primary);
    color: white;
  }
</style>
```

**Backend (FastAPI) Tasks:**
```python
# Always follow these patterns

# 1. Proper imports and structure
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.core.capture_engine import CaptureEngine
from app.models.item import Item

router = APIRouter(prefix="/api", tags=["capture"])

# 2. Type hints and validation
@router.post("/capture", response_model=CaptureResponse)
async def capture_item(
    request: CaptureRequest,
    db: Session = Depends(get_db)
) -> CaptureResponse:
    """Capture a new knowledge item with AI enhancement."""
    try:
        # 3. Proper error handling
        item = await CaptureEngine.process_item(request.dict())
        return CaptureResponse(success=True, item_id=item.id)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Capture failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Capture failed")
```

**Chrome Extension Tasks:**
```javascript
// Always follow these patterns

// 1. Manifest V3 compliance
// Use service workers, not background pages
// Proper message passing between components

// 2. Error handling and user feedback
async function captureCurrentPage() {
  try {
    showStatus('Capturing...', 'loading');
    
    const response = await fetch('/api/capture', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    showStatus('Captured successfully!', 'success');
  } catch (error) {
    console.error('Capture failed:', error);
    showStatus('Capture failed', 'error');
  }
}

// 3. Consistent styling with main app
const styles = `
  .capture-btn {
    background-color: #dc143c;
    color: white;
    border: none;
    border-radius: 0.5rem;
    padding: 0.75rem 1rem;
    font-weight: 500;
  }
`;
```

#### Code Quality Standards
```javascript
// 1. Always add comprehensive JSDoc comments
/**
 * Formats a date for display in the timeline
 * @param {Date|string} date - The date to format
 * @param {string} [format='relative'] - Format type: 'relative', 'short', 'long'
 * @returns {string} Formatted date string
 * @example
 * formatDate(new Date(), 'relative') // "2 hours ago"
 */
function formatDate(date, format = 'relative') {
  // Implementation
}

// 2. Input validation and error handling
function processUserInput(input) {
  if (!input || typeof input !== 'string') {
    throw new Error('Input must be a non-empty string');
  }
  
  const sanitized = input.trim();
  if (sanitized.length === 0) {
    throw new Error('Input cannot be empty after trimming');
  }
  
  return sanitized;
}

// 3. Consistent naming conventions
const API_ENDPOINTS = {
  CAPTURE: '/api/capture',
  SEARCH: '/api/search',
  TIMELINE: '/api/timeline'
};

class ContentProcessor {
  async processItem(item) {
    // Method implementation
  }
  
  #validateInput(input) {
    // Private method
  }
}
```

### 3. Testing and Validation

#### Always Test These Scenarios
```bash
# Frontend Testing
1. Component renders without errors
2. Props are properly typed and validated
3. User interactions work as expected
4. Responsive design works on mobile
5. Accessibility features function properly

# Backend Testing
1. API endpoints return correct responses
2. Database operations complete successfully
3. Error handling works for edge cases
4. Input validation prevents bad data
5. Performance meets requirements (<1s response)

# Extension Testing
1. Manifest validates without errors
2. Permissions are minimal and justified
3. Content scripts don't break websites
4. Background scripts handle errors gracefully
5. Storage operations work correctly

# Integration Testing
1. Frontend connects to backend APIs
2. Extension communicates with backend
3. Database schema supports all operations
4. AI processing works end-to-end
5. All components work together seamlessly
```

## Component Integration Patterns

### 1. Frontend ↔ Backend Communication
```javascript
// Standard API client pattern
class APIClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }
  
  // Specific methods
  async capture(data) {
    return this.request('/api/capture', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  async search(query) {
    return this.request(`/api/search?q=${encodeURIComponent(query)}`);
  }
}
```

### 2. Extension ↔ Backend Communication
```javascript
// Extension background script pattern
class ExtensionAPI {
  constructor() {
    this.baseURL = 'http://localhost:8000';
    this.setupMessageHandlers();
  }
  
  setupMessageHandlers() {
    chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
      try {
        switch (message.action) {
          case 'capture':
            const result = await this.captureItem(message.data);
            sendResponse({ success: true, data: result });
            break;
            
          default:
            sendResponse({ success: false, error: 'Unknown action' });
        }
      } catch (error) {
        sendResponse({ success: false, error: error.message });
      }
      
      return true; // Required for async response
    });
  }
  
  async captureItem(data) {
    const response = await fetch(`${this.baseURL}/api/capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`Capture failed: ${response.status}`);
    }
    
    return response.json();
  }
}
```

### 3. Database Integration Patterns
```python
# Always use these patterns for database operations

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ItemRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_item(self, item_data: dict) -> Item:
        """Create a new knowledge item with full-text search support."""
        try:
            item = Item(**item_data)
            self.db.add(item)
            await self.db.commit()
            await self.db.refresh(item)
            
            logger.info(f"Created item: {item.id}")
            return item
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create item: {str(e)}")
            raise
    
    async def search_items(
        self, 
        query: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Item]:
        """Search items using PostgreSQL full-text search."""
        try:
            sql = text("""
                SELECT *, ts_rank(search_vector, plainto_tsquery(:query)) as rank
                FROM items 
                WHERE search_vector @@ plainto_tsquery(:query)
                ORDER BY rank DESC, created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            result = await self.db.execute(
                sql, 
                {"query": query, "limit": limit, "offset": offset}
            )
            
            return result.fetchall()
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
```

## AI Integration Guidelines

### 1. Azure OpenAI Integration (Updated 2025-01-08)
```python
# Standard pattern for AI integration - Azure OpenAI with optional fallback
import httpx
import asyncio
from typing import Optional, List
import logging
import os

logger = logging.getLogger(__name__)

class AzureOpenAIClient:
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.client = httpx.AsyncClient(timeout=30.0) if self.api_key else None
    
    async def is_available(self) -> bool:
        """Check if Ollama is running and available."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def generate_summary(self, content: str, max_tokens: int = 150) -> Optional[str]:
        """Generate a concise summary of content."""
        if not await self.is_available():
            logger.warning("Ollama not available, skipping AI summary")
            return None
        
        try:
            prompt = f"""Summarize this content in 1-2 sentences, focusing on key insights:

{content[:2000]}  # Limit input length

Summary:"""
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": "llama2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.3
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"AI summary generation failed: {str(e)}")
            return None
    
    async def extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content."""
        if not await self.is_available():
            return []
        
        try:
            prompt = f"""Extract 3-5 relevant tags from this content. Return only tags separated by commas, no explanations:

{content[:1500]}

Tags:"""
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": "llama2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 50,
                        "temperature": 0.1
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                tags_text = result.get("response", "").strip()
                
                # Parse comma-separated tags
                tags = [
                    tag.strip().lower() 
                    for tag in tags_text.split(',') 
                    if tag.strip()
                ]
                
                return tags[:5]  # Limit to 5 tags
            else:
                return []
                
        except Exception as e:
            logger.error(f"AI tag extraction failed: {str(e)}")
            return []
```

### 2. Fallback Strategies for AI Features
```python
# Always provide fallbacks when AI is unavailable
class ContentProcessor:
    def __init__(self, ai_client: OllamaClient):
        self.ai_client = ai_client
    
    async def process_item(self, item_data: dict) -> dict:
        """Process item with AI enhancement and fallbacks."""
        
        # Generate summary (with fallback)
        summary = await self.ai_client.generate_summary(item_data.get('content', ''))
        if not summary:
            # Fallback: Use first 200 characters
            content = item_data.get('content', '')
            summary = content[:200] + '...' if len(content) > 200 else content
        
        # Extract tags (with fallback)
        ai_tags = await self.ai_client.extract_tags(item_data.get('content', ''))
        if not ai_tags:
            # Fallback: Extract from URL domain or title
            ai_tags = self._extract_fallback_tags(item_data)
        
        return {
            **item_data,
            'summary': summary,
            'tags': ai_tags,
            'ai_processed': len(ai_tags) > 0 and summary != item_data.get('content', '')[:200]
        }
    
    def _extract_fallback_tags(self, item_data: dict) -> List[str]:
        """Extract basic tags without AI."""
        tags = []
        
        # Extract from URL domain
        url = item_data.get('url', '')
        if url:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if domain:
                tags.append(domain.replace('www.', ''))
        
        # Extract from title keywords
        title = item_data.get('title', '')
        if title:
            words = title.lower().split()
            keywords = [word for word in words if len(word) > 4]
            tags.extend(keywords[:3])
        
        return tags[:5]
```

## Debugging and Troubleshooting

### 1. Common Issues and Solutions

#### Frontend Issues
```bash
# SvelteKit build errors
Problem: "Cannot resolve 'some-module'"
Solution: Check import paths, ensure module is installed

Problem: "Hydration mismatch"
Solution: Check for client/server differences, use browser check

Problem: "Component not updating"
Solution: Check reactivity, ensure proper binding, use $: for computed values

Problem: "Type 'X' is not assignable to type 'Y'"
Solution: Check frontend/backend type consistency, update TypeScript interfaces

Problem: "Property does not exist on type"
Solution: Verify API response matches frontend expectations, update types
```

#### Backend Issues
```bash
# FastAPI common issues
Problem: "Database connection failed"
Solution: Check PostgreSQL is running, verify connection string, check port (5432 vs 5433)

Problem: "Import error in Python modules"
Solution: Check PYTHONPATH, verify virtual environment is active

Problem: "CORS errors from frontend"
Solution: Update CORS settings in FastAPI middleware

Problem: "Pydantic validation error"
Solution: Ensure all required fields are in model, check JSONB field handling

Problem: "Redis connection refused"
Solution: Check Redis is running, verify connection URL uses service name in Docker

Problem: "JSONB field returns as string"
Solution: Parse with json.loads() when asyncpg returns string instead of dict
```

#### Extension Issues
```bash
# Chrome Extension common issues
Problem: "Extension not loading"
Solution: Check manifest.json syntax, verify permissions

Problem: "Content script not injecting"
Solution: Check matches patterns, verify host permissions

Problem: "Background script errors"
Solution: Check service worker syntax, use chrome.runtime properly
```

### 2. Debugging Tools and Techniques
```javascript
// Frontend debugging
console.log('Debug info:', { variable, state, props });

// Use Svelte devtools
$inspect(someStore);

// Performance monitoring
console.time('operation');
await performOperation();
console.timeEnd('operation');

// Backend debugging
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Processing item: {item_id}")
logger.info(f"Search completed: {len(results)} results")
logger.error(f"Database error: {str(e)}")

# Extension debugging
// Background script console: chrome://extensions > inspect background page
console.log('Background script loaded');

// Content script console: Regular page console
console.log('Content script injected');

// Storage debugging
chrome.storage.local.get(null, (data) => {
  console.log('All storage data:', data);
});
```

## Performance Optimization

### 1. Frontend Performance
```svelte
<!-- Use lazy loading for heavy components -->
<script>
  import { onMount } from 'svelte';
  
  let Component;
  
  onMount(async () => {
    if (shouldLoadComponent) {
      const module = await import('./HeavyComponent.svelte');
      Component = module.default;
    }
  });
</script>

{#if Component}
  <svelte:component this={Component} />
{/if}

<!-- Optimize large lists with virtual scrolling -->
<VirtualList items={largeItemList} let:item>
  <ItemCard {item} />
</VirtualList>

<!-- Debounce search input -->
<script>
  import { debounce } from '$lib/utils/performance.js';
  
  const debouncedSearch = debounce(async (query) => {
    searchResults = await api.search(query);
  }, 300);
  
  $: if (searchQuery) {
    debouncedSearch(searchQuery);
  }
</script>
```

### 2. Backend Performance
```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Optimize database queries
async def get_recent_items(db: Session, limit: int = 50):
    """Get recent items with optimized query."""
    return await db.execute(
        text("""
            SELECT id, title, summary, created_at, 
                   array_agg(t.name) as tags
            FROM items i
            LEFT JOIN item_tags it ON i.id = it.item_id
            LEFT JOIN tags t ON it.tag_id = t.id
            WHERE i.created_at > NOW() - INTERVAL '30 days'
            GROUP BY i.id, i.title, i.summary, i.created_at
            ORDER BY i.created_at DESC
            LIMIT :limit
        """),
        {"limit": limit}
    )

# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_computation(input_data: str) -> str:
    # Expensive operation here
    return result
```

### 3. Database Performance
```sql
-- Essential indexes for PRSNL
CREATE INDEX CONCURRENTLY idx_items_created_at ON items(created_at DESC);
CREATE INDEX CONCURRENTLY idx_items_search_vector ON items USING GIN(search_vector);
CREATE INDEX CONCURRENTLY idx_items_tags ON item_tags(item_id, tag_id);

-- Optimize full-text search
CREATE INDEX CONCURRENTLY idx_items_fts_rank ON items 
USING GIN(search_vector) 
WHERE search_vector IS NOT NULL;

-- Partitioning for large datasets (if needed)
CREATE TABLE items_2025 PARTITION OF items
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

## Security Considerations

### 1. Input Validation and Sanitization
```python
# Backend input validation
from pydantic import BaseModel, validator, HttpUrl
import bleach

class CaptureRequest(BaseModel):
    url: Optional[HttpUrl] = None
    title: str
    content: Optional[str] = None
    tags: List[str] = []
    
    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        if len(v) > 500:
            raise ValueError('Title too long')
        return v.strip()
    
    @validator('content')
    def sanitize_content(cls, v):
        if v:
            # Remove dangerous HTML tags
            allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3']
            return bleach.clean(v, tags=allowed_tags, strip=True)
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Too many tags')
        return [tag.strip().lower() for tag in v if tag.strip()]
```

### 2. Extension Security
```javascript
// Content Security Policy in manifest.json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}

// Validate messages in background script
function validateMessage(message, sender) {
  // Check sender origin
  if (!sender.tab || !sender.tab.url) {
    return false;
  }
  
  // Validate message structure
  if (!message.action || typeof message.action !== 'string') {
    return false;
  }
  
  // Check allowed actions
  const allowedActions = ['capture', 'search', 'status'];
  if (!allowedActions.includes(message.action)) {
    return false;
  }
  
  return true;
}

// Sanitize data before sending to API
function sanitizeCapturData(data) {
  return {
    url: data.url ? new URL(data.url).toString() : null,
    title: data.title ? data.title.slice(0, 500) : '',
    content: data.content ? data.content.slice(0, 50000) : '',
    tags: Array.isArray(data.tags) ? data.tags.slice(0, 10) : []
  };
}
```

## Collaboration Protocols

### 1. Multi-AI Development
```markdown
# Working with Multiple AI Assistants

## Task Assignment Protocol
1. Check PROGRESS_TRACKER.md for active work
2. Claim tasks by updating status to IN_PROGRESS
3. Never start work on files marked as "editing" by another AI
4. Use specific task IDs for coordination

## Communication Patterns
- Update progress every 30 minutes during active work
- Mark subtasks as complete immediately when finished
- Document any blockers or issues encountered
- Provide clear handoff notes when switching tasks

## Conflict Resolution
- If you detect a conflict, stop work immediately
- Update status to BLOCKED with clear description
- Create a GitHub issue tagged with 'ai-conflict'
- Wait for human intervention before proceeding
```

### 2. Code Review Guidelines
```markdown
# AI Code Review Checklist

## Functionality
- [ ] Code accomplishes stated requirements
- [ ] Error handling is comprehensive
- [ ] Edge cases are considered
- [ ] Performance requirements are met

## Quality
- [ ] Follows established patterns and conventions
- [ ] Has appropriate tests or validation
- [ ] Documentation is clear and complete
- [ ] No security vulnerabilities introduced

## Integration
- [ ] Compatible with existing components
- [ ] Doesn't break existing functionality
- [ ] Follows data flow patterns
- [ ] Updates documentation as needed

## PRSNL-Specific
- [ ] Maintains Manchester United red color scheme
- [ ] Follows local-first architecture
- [ ] Preserves privacy and security
- [ ] Supports keyboard-centric workflow
```

## Lessons Learned and Troubleshooting Guide

### Common Integration Issues

#### 1. Frontend/Backend Type Mismatches
**Problem**: API returns different field names or types than frontend expects
**Solutions**:
- Generate TypeScript types from Pydantic models
- Use consistent naming (camelCase vs snake_case)
- Validate API responses match documented schemas
- Add runtime type checking in development

#### 2. Container Networking with Rancher Desktop
**Problem**: Frontend can't connect to backend using localhost
**Solutions**:
- Use service names (backend:8000) instead of localhost
- Add nginx proxy for external access
- Configure proper Docker networks
- Map ports correctly in docker-compose

#### 3. Database Schema Evolution
**Problem**: Adding new fields breaks existing queries
**Solutions**:
- Always create proper migrations
- Use CASE statements for computed fields
- Handle NULL values gracefully
- Test with existing data before deploying

#### 4. JSONB Field Handling
**Problem**: PostgreSQL JSONB fields not parsing correctly
**Solutions**:
```python
# Handle both dict and string returns from asyncpg
metadata = row["metadata"] if isinstance(row.get("metadata"), dict) else (
    json.loads(row["metadata"]) if row.get("metadata") else {}
)
```

#### 5. Missing Enum Values
**Problem**: Backend defines enum values frontend doesn't recognize
**Solutions**:
- Keep enums synchronized between frontend and backend
- Add validation for unknown enum values
- Use string unions instead of enums for flexibility

### Performance Optimization Lessons

1. **Cursor-based Pagination**: More efficient than offset-based for large datasets
2. **Embedding Service**: Make optional to avoid blocking on missing Azure credentials
3. **Docker Build Cache**: Use multi-stage builds and proper layer caching
4. **Frontend Bundle Size**: Lazy load heavy components, use dynamic imports

## Testing Strategies for AI Development

### 1. Automated Testing
```javascript
// Component testing example
import { render, fireEvent } from '@testing-library/svelte';
import SearchComponent from './Search.svelte';

test('search component handles user input', async () => {
  const { getByPlaceholderText, getByText } = render(SearchComponent);
  
  const input = getByPlaceholderText('Search your knowledge...');
  await fireEvent.input(input, { target: { value: 'test query' } });
  
  // Verify search is triggered
  expect(getByText('Searching...')).toBeInTheDocument();
});

// API testing
import { test, expect } from '@playwright/test';

test('capture API endpoint works correctly', async ({ request }) => {
  const response = await request.post('/api/capture', {
    data: {
      title: 'Test Item',
      content: 'Test content',
      tags: ['test']
    }
  });
  
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data.success).toBe(true);
  expect(data.item_id).toBeDefined();
});
```

### 2. Manual Testing Protocols
```bash
# AI Testing Checklist

## Frontend Testing
1. Test all navigation paths
2. Verify responsive design on mobile
3. Check accessibility with screen reader
4. Test keyboard navigation throughout
5. Verify Manchester United red theming

## Backend Testing
1. Test all API endpoints with curl
2. Verify database operations complete
3. Test error responses and status codes
4. Check AI integration works with Ollama
5. Verify performance under load

## Extension Testing
1. Load unpacked extension in Chrome
2. Test all keyboard shortcuts
3. Verify context menu functionality
4. Test capture on various websites
5. Check settings persistence

## Integration Testing
1. End-to-end capture workflow
2. Search across all components
3. Data synchronization between parts
4. Error handling across boundaries
5. Performance of full system
```

## Documentation Standards

### 1. Code Documentation
```javascript
/**
 * Comprehensive JSDoc example for AI-generated code
 * 
 * @description Processes knowledge items with AI enhancement and validation
 * @param {Object} itemData - Raw item data from capture source
 * @param {string} itemData.title - Item title (required)
 * @param {string} [itemData.content] - Full text content
 * @param {string[]} [itemData.tags] - Initial tags
 * @param {Object} [options] - Processing options
 * @param {boolean} [options.enableAI=true] - Whether to use AI processing
 * @param {number} [options.maxSummaryLength=200] - Maximum summary length
 * @returns {Promise<ProcessedItem>} Enhanced item with AI-generated summary and tags
 * 
 * @throws {ValidationError} When item data is invalid
 * @throws {AIProcessingError} When AI processing fails
 * 
 * @example
 * const item = await processKnowledgeItem({
 *   title: "Important Article",
 *   content: "Long article content...",
 *   tags: ["research"]
 * });
 * 
 * @since 1.0.0
 * @author Claude Code
 */
async function processKnowledgeItem(itemData, options = {}) {
  // Implementation with extensive error handling
}
```

### 2. README Updates
When creating or modifying functionality, always update relevant README files:

```markdown
# Updates to include in README files

## Component README (e.g., frontend/README.md)
- New dependencies added
- New scripts or commands
- Configuration changes
- New environment variables
- Testing procedures

## Main Project README
- New features implemented
- Changed system requirements
- Updated installation steps
- New usage examples
- Performance improvements

## API Documentation
- New endpoints added
- Changed request/response formats
- New error codes
- Authentication changes
- Rate limiting updates
```

## Conclusion for AI Assistants

This document provides the foundation for effective AI-assisted development of PRSNL. Key principles to remember:

1. **Always preserve the local-first, privacy-focused architecture**
2. **Maintain Manchester United red design consistency**
3. **Follow established patterns and conventions**
4. **Provide comprehensive error handling and fallbacks**
5. **Update documentation and progress tracking consistently**
6. **Test thoroughly across all components**
7. **Coordinate effectively with other AI assistants**
8. **Keep frontend and backend types synchronized**
9. **Handle container networking properly with Rancher Desktop**
10. **Always test with real data before declaring features complete**

The PRSNL project represents a sophisticated multi-component system that requires careful attention to integration points, user experience, and performance. Common pitfalls include:
- Type mismatches between frontend and backend
- Container networking issues
- JSONB serialization problems
- Missing database migrations
- Incomplete error handling

By following these guidelines and learning from past issues, AI assistants can contribute effectively to building a world-class local-first knowledge management system.

For questions or clarifications, refer to the comprehensive documentation in the `/docs` folder or examine existing code patterns in the respective component directories.