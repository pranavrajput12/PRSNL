# DATA_FLOW.md

## PRSNL Data Flow Architecture

### Overview
PRSNL implements a local-first data processing pipeline that captures, processes, stores, and retrieves knowledge items without external dependencies.

## Input Sources

### 1. Browser Extension Capture
```
User selects text/page → Extension popup → Background script → Local API
├── Keyboard shortcuts: ⌘+Shift+S (page), ⌘+Shift+E (selection)
├── Right-click context menu
├── Extension popup interface
└── Auto-capture settings
```

### 2. Web Interface Capture
```
Frontend form → API client → Backend capture endpoint
├── Manual URL/text entry
├── File upload interface
├── Quick capture modal (⌘N)
└── Batch import tools
```

### 3. Desktop Overlay Capture
```
Global hotkey → Electron overlay → Background capture
├── System-wide search overlay
├── Quick capture from any application
└── Cross-application text selection
```

## Data Processing Pipeline

### Stage 1: Capture & Validation
```
Input → Validation → Standardization → Queue
│
├── URL validation and normalization
├── Text content extraction
├── File type detection
├── Duplicate detection
└── Security sanitization
```

### Stage 2: Content Enhancement
```
Raw content → Scraping → AI Enhancement → Metadata
│
├── Web scraping (BeautifulSoup + Readability)
│   ├── Title extraction
│   ├── Content cleaning
│   ├── Image extraction
│   └── Metadata parsing
│
├── AI Processing (Ollama local LLM)
│   ├── Content summarization
│   ├── Auto-tagging
│   ├── Key phrase extraction
│   └── Content categorization
│
└── Metadata Generation
    ├── Timestamps (created, modified)
    ├── Source information
    ├── Content type classification
    └── Quality scores
```

### Stage 3: Storage & Indexing
```
Enhanced content → Database → Search Index → File Storage
│
├── PostgreSQL Storage
│   ├── Items table (core data)
│   ├── Tags table (normalized tags)
│   ├── Relationships table (connections)
│   └── Search vectors (full-text)
│
├── Full-Text Search Index
│   ├── PostgreSQL FTS (primary)
│   ├── Title/content indexing
│   ├── Tag indexing
│   └── Custom ranking
│
└── File System Storage
    ├── Original content cache
    ├── Processed content
    ├── Image/media assets
    └── Backup/export files
```

## Data Flow Diagrams

### Capture Flow (ASCII Diagram)
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Chrome Extension│────▶│ Background      │────▶│ FastAPI Backend │
│ • Popup UI      │     │ • Service Worker│     │ • /api/capture  │
│ • Context Menu  │     │ • Message Queue │     │ • Validation    │
│ • Shortcuts     │     │ • Settings      │     │ • Queue Job     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
┌─────────────────┐     ┌─────────────────┐              │
│ Web Frontend    │────▶│ API Client      │──────────────┘
│ • Capture Form  │     │ • HTTP requests │
│ • File Upload   │     │ • Error handling│
│ • Quick Modal   │     │ • State mgmt    │
└─────────────────┘     └─────────────────┘
```

### Processing Pipeline (ASCII Diagram)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Capture   │───▶│   Scrape    │───▶│ AI Enhance  │───▶│   Store     │
│             │    │             │    │             │    │             │
│ • Validate  │    │ • Extract   │    │ • Summarize │    │ • Database  │
│ • Normalize │    │ • Clean     │    │ • Tag       │    │ • Index     │
│ • Queue     │    │ • Parse     │    │ • Classify  │    │ • Files     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Search Flow (ASCII Diagram)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Search Input│───▶│ Query Proc  │───▶│  Database   │───▶│   Results   │
│             │    │             │    │   Search    │    │             │
│ • Text      │    │ • Parse     │    │ • FTS Query │    │ • Rank      │
│ • Filters   │    │ • Expand    │    │ • Filter    │    │ • Format    │
│ • Context   │    │ • Optimize  │    │ • Score     │    │ • Display   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Storage Mechanisms

### PostgreSQL Database Schema
```sql
-- Core content storage
items (
    id UUID PRIMARY KEY,
    url TEXT,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    content_type VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    search_vector TSVECTOR
);

-- Normalized tag system
tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE
);

-- Many-to-many relationship
item_tags (
    item_id UUID REFERENCES items(id),
    tag_id INTEGER REFERENCES tags(id)
);

-- Full-text search index
CREATE INDEX idx_items_search ON items USING GIN(search_vector);
```

### File System Storage
```
data/
├── content/          # Original captured content
│   ├── html/         # Raw HTML content
│   ├── text/         # Processed text
│   └── media/        # Images, videos, files
├── cache/            # Temporary processing files
├── exports/          # User export files
└── backups/          # Database backups
```

### Browser Storage (Extension)
```javascript
// Chrome Extension Storage
chrome.storage.sync {
    apiUrl: "http://localhost:8000",
    autoTags: true,
    showNotifications: true,
    contextMenu: true
}

chrome.storage.local {
    recentCaptures: [...],
    failedQueue: [...],
    offlineBuffer: [...]
}
```

## Output Destinations

### 1. Web Interface Display
```
Database → API → Frontend → User Interface
├── Timeline view (chronological)
├── Search results (ranked)
├── Tag browser (categorized)
└── Individual item view (detailed)
```

### 2. API Responses
```json
{
    "id": "uuid",
    "title": "Item Title",
    "url": "https://example.com",
    "summary": "AI-generated summary",
    "tags": ["tag1", "tag2"],
    "created_at": "2025-01-06T22:00:00Z",
    "content_type": "article",
    "search_score": 0.95
}
```

### 3. Export Formats
```
├── JSON export (full data)
├── CSV export (tabular data)
├── Markdown export (readable format)
└── HTML export (browsable archive)
```

### 4. Chrome Extension Feedback
```
API Response → Background Script → Visual Feedback
├── Success notification
├── Page highlight animation
├── Badge count updates
└── Error state handling
```

## Inter-Module Communication

### 1. Extension ↔ Backend
```javascript
// Message passing
chrome.runtime.sendMessage({
    action: 'capture',
    data: { url, title, content, tags }
});

// HTTP API calls
fetch('/api/capture', {
    method: 'POST',
    body: JSON.stringify(data)
});
```

### 2. Frontend ↔ Backend
```javascript
// RESTful API communication
const api = {
    capture: (data) => POST('/api/capture', data),
    search: (query) => GET('/api/search', { q: query }),
    timeline: (page) => GET('/api/timeline', { page })
};
```

### 3. Backend Internal Communication
```python
# PostgreSQL LISTEN/NOTIFY for task queue
await connection.execute("NOTIFY capture_queue, %s", json.dumps(job))

# Direct function calls within modules
from app.core.capture_engine import process_item
result = await process_item(item_data)
```

## Event Systems and Message Passing

### Chrome Extension Events
```javascript
// Background script event listeners
chrome.commands.onCommand.addListener(handleKeyboardShortcut);
chrome.contextMenus.onClicked.addListener(handleContextMenu);
chrome.runtime.onMessage.addListener(handleMessage);

// Content script events
document.addEventListener('selectionchange', handleSelection);
window.addEventListener('keydown', handleGlobalHotkeys);
```

### Frontend State Management
```javascript
// Svelte stores for reactive state
export const searchResults = writable([]);
export const currentQuery = writable('');
export const isLoading = writable(false);

// Component communication
import { searchResults } from '$lib/stores/app';
$searchResults = await api.search(query);
```

### Backend Event Processing
```python
# Async task processing
async def process_capture_queue():
    async with database.listen("capture_queue") as listener:
        async for notification in listener:
            job = json.loads(notification.payload)
            await process_job(job)
```

## State Management Approach

### Frontend State (Svelte Stores)
- **Global State**: User preferences, auth state
- **Component State**: Form data, UI state
- **Derived State**: Computed values, filtered data
- **Persistent State**: localStorage for user settings

### Backend State (Stateless API)
- **Database State**: Persistent data storage
- **Cache State**: Redis for session data (future)
- **Queue State**: PostgreSQL for task management
- **File State**: Filesystem for content storage

### Extension State (Chrome Storage)
- **Sync Storage**: User settings across devices
- **Local Storage**: Large data, temporary cache
- **Session Storage**: Tab-specific data
- **Memory State**: Runtime variables

## Performance Optimizations

### Database Query Optimization
```sql
-- Optimized search query
SELECT items.*, ts_rank(search_vector, plainto_tsquery($1)) as rank
FROM items 
WHERE search_vector @@ plainto_tsquery($1)
ORDER BY rank DESC, created_at DESC
LIMIT 50;
```

### Frontend Performance
- **Lazy Loading**: Components loaded on demand
- **Virtual Scrolling**: Large lists (timeline)
- **Debounced Search**: Reduce API calls
- **Cached Results**: Avoid duplicate requests

### Extension Performance
- **Background Processing**: Non-blocking capture
- **Batched Requests**: Multiple items together
- **Offline Queue**: Handle network failures
- **Memory Management**: Clean up unused data

## Error Handling and Recovery

### Capture Pipeline Errors
```
Input Error → Validation Failed → User Feedback
Network Error → Retry Queue → Background Processing
Processing Error → Fallback Mode → Partial Save
Storage Error → Backup Location → Manual Recovery
```

### Search Pipeline Errors
```
Query Error → Fallback Search → Basic Results
Database Error → Cache Fallback → Degraded Mode
Index Error → Full Table Scan → Slower Results
Network Error → Offline Mode → Cached Results
```

## Data Security and Privacy

### Local Processing
- All AI processing uses local Ollama instance
- No data transmitted to external services
- Content never leaves user's machine
- Encryption for sensitive local storage

### Input Sanitization
```python
# XSS prevention
content = html.escape(raw_content)
content = bleach.clean(content, tags=ALLOWED_TAGS)

# SQL injection prevention
cursor.execute("INSERT INTO items VALUES (%s, %s)", (id, title))
```

### Access Control
- Extension requires explicit permissions
- API endpoints validate request sources
- File system access restricted to app directory
- Database access through connection pooling