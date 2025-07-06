# EXTERNAL_INTERFACES.md

## PRSNL External Interfaces Documentation

### Overview
PRSNL integrates with multiple external systems while maintaining its local-first architecture. This document covers all external APIs, services, and integrations.

## Browser APIs (Chrome Extension)

### Chrome Extension APIs Used

#### 1. Action API (Popup)
```javascript
// manifest.json
"action": {
    "default_popup": "popup.html",
    "default_icon": {
        "16": "icons/icon16.png",
        "48": "icons/icon48.png", 
        "128": "icons/icon128.png"
    }
}

// Usage in background.js
chrome.action.onClicked.addListener((tab) => {
    // Handle extension icon click
});
```

#### 2. Commands API (Keyboard Shortcuts)
```javascript
// manifest.json
"commands": {
    "capture-page": {
        "suggested_key": {
            "default": "Ctrl+Shift+S",
            "mac": "Command+Shift+S"
        },
        "description": "Capture current page to PRSNL"
    },
    "capture-selection": {
        "suggested_key": {
            "default": "Ctrl+Shift+E", 
            "mac": "Command+Shift+E"
        },
        "description": "Capture selected text to PRSNL"
    }
}

// Usage in background.js
chrome.commands.onCommand.addListener(async (command) => {
    if (command === 'capture-page') {
        await captureCurrentPage();
    } else if (command === 'capture-selection') {
        await captureSelection();
    }
});
```

#### 3. Context Menus API
```javascript
// Background script setup
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: 'capture-page',
        title: 'Capture page to PRSNL',
        contexts: ['page']
    });
    
    chrome.contextMenus.create({
        id: 'capture-selection', 
        title: 'Capture selection to PRSNL',
        contexts: ['selection']
    });
});

// Handle clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'capture-page') {
        captureCurrentPage();
    } else if (info.menuItemId === 'capture-selection') {
        captureSelection();
    }
});
```

#### 4. Storage API
```javascript
// Sync storage (synced across devices)
chrome.storage.sync.set({
    apiUrl: 'http://localhost:8000',
    autoTags: true,
    showNotifications: true,
    contextMenu: true
});

chrome.storage.sync.get(['apiUrl', 'autoTags'], (result) => {
    console.log('Settings:', result);
});

// Local storage (large data, local only)
chrome.storage.local.set({
    recentCaptures: captures,
    failedQueue: failedItems
});
```

#### 5. Tabs API
```javascript
// Get active tab information
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    const { url, title, id } = tab;
    
    // Send message to content script
    chrome.tabs.sendMessage(id, { action: 'getSelection' });
});

// Execute scripts in tabs
chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content.js']
});
```

#### 6. Runtime API (Messaging)
```javascript
// Background script listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'capture') {
        captureCurrentPage(message.tags);
        sendResponse({ success: true });
    }
    return true; // Required for async response
});

// Content script messaging
chrome.runtime.sendMessage({
    action: 'capture',
    data: { url, title, content, tags }
});
```

#### 7. Notifications API
```javascript
// Show notification
chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: 'PRSNL Capture',
    message: 'Page captured successfully'
});
```

#### 8. Scripting API (Content Scripts)
```javascript
// Inject content script
chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['content.js']
});

// Execute code directly
chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => window.getSelection().toString()
});
```

### Permissions Required
```json
{
    "permissions": [
        "activeTab",        // Access current tab
        "scripting",        // Inject scripts
        "storage",          // Store settings
        "tabs",             // Tab information
        "notifications",    // Show notifications
        "contextMenus"      // Right-click menus
    ],
    "host_permissions": [
        "http://localhost:8000/*"  // API access
    ]
}
```

## AI Integration APIs

### 1. Ollama Local API
```python
# Ollama HTTP API integration
import httpx

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def generate_summary(self, content: str) -> str:
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": "llama2",
                "prompt": f"Summarize this content: {content}",
                "stream": False
            }
        )
        return response.json()["response"]
    
    async def extract_tags(self, content: str) -> List[str]:
        response = await self.client.post(
            f"{self.base_url}/api/generate", 
            json={
                "model": "llama2",
                "prompt": f"Extract 3-5 relevant tags from: {content}",
                "stream": False
            }
        )
        return self._parse_tags(response.json()["response"])
```

### 2. Azure OpenAI (Backup)
```python
# Azure OpenAI integration (when Ollama unavailable)
from openai import AzureOpenAI

class AzureOpenAIClient:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    
    async def generate_summary(self, content: str) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful summarizer."},
                {"role": "user", "content": f"Summarize: {content}"}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
```

## Database Integration

### PostgreSQL Database Interface
```python
# Database connection and operations
import asyncpg
from typing import List, Dict, Optional

class DatabaseClient:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(self.connection_string)
    
    async def store_item(self, item: Dict) -> str:
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO items (id, url, title, content, summary, tags, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """
            return await conn.fetchval(
                query, 
                item['id'], item['url'], item['title'], 
                item['content'], item['summary'], item['tags'],
                item['created_at']
            )
    
    async def search_items(self, query: str, limit: int = 50) -> List[Dict]:
        async with self.pool.acquire() as conn:
            sql = """
                SELECT *, ts_rank(search_vector, plainto_tsquery($1)) as rank
                FROM items 
                WHERE search_vector @@ plainto_tsquery($1)
                ORDER BY rank DESC, created_at DESC
                LIMIT $2
            """
            rows = await conn.fetch(sql, query, limit)
            return [dict(row) for row in rows]
    
    async def get_timeline(self, page: int = 1, per_page: int = 20) -> List[Dict]:
        async with self.pool.acquire() as conn:
            offset = (page - 1) * per_page
            query = """
                SELECT * FROM items 
                ORDER BY created_at DESC 
                LIMIT $1 OFFSET $2
            """
            rows = await conn.fetch(query, per_page, offset)
            return [dict(row) for row in rows]
```

### Database Schema (PostgreSQL)
```sql
-- Full-text search enabled tables
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    content_type VARCHAR(50) DEFAULT 'article',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    search_vector TSVECTOR
);

-- Auto-update search vector on insert/update
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.title, '') || ' ' || 
        COALESCE(NEW.content, '') || ' ' ||
        COALESCE(NEW.summary, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER items_search_vector_update
    BEFORE INSERT OR UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Full-text search index
CREATE INDEX idx_items_search ON items USING GIN(search_vector);

-- Tags system
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE item_tags (
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, tag_id)
);
```

## Web Scraping and Content Extraction

### BeautifulSoup Integration
```python
# Web content extraction
from bs4 import BeautifulSoup
import httpx
from readability import Document

class ContentExtractor:
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={'User-Agent': 'PRSNL/1.0 (+https://github.com/user/prsnl)'}
        )
    
    async def extract_content(self, url: str) -> Dict:
        response = await self.client.get(url)
        html = response.text
        
        # Use readability for main content
        doc = Document(html)
        main_content = doc.summary()
        
        # Use BeautifulSoup for metadata
        soup = BeautifulSoup(html, 'html.parser')
        
        return {
            'title': self._extract_title(soup, doc.title()),
            'content': main_content,
            'description': self._extract_description(soup),
            'author': self._extract_author(soup),
            'published_date': self._extract_date(soup),
            'images': self._extract_images(soup),
            'favicon': self._extract_favicon(soup, url)
        }
    
    def _extract_title(self, soup: BeautifulSoup, fallback: str) -> str:
        # Try various title sources
        selectors = [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]',
            'h1',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get('content') or element.text.strip()
        
        return fallback
```

### Favicon Extraction
```python
def extract_favicon(self, soup: BeautifulSoup, url: str) -> str:
    """Extract favicon URL from page"""
    favicon_selectors = [
        'link[rel="icon"]',
        'link[rel="shortcut icon"]', 
        'link[rel="apple-touch-icon"]'
    ]
    
    for selector in favicon_selectors:
        element = soup.select_one(selector)
        if element and element.get('href'):
            return urljoin(url, element.get('href'))
    
    # Fallback to Google's favicon service
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return f"https://www.google.com/s2/favicons?domain={domain}"
```

## File Format Support

### Input File Formats
```python
# Supported file types for upload
SUPPORTED_FORMATS = {
    'text': ['.txt', '.md', '.rtf'],
    'documents': ['.pdf', '.docx', '.odt'],
    'web': ['.html', '.htm', '.mhtml'],
    'code': ['.py', '.js', '.css', '.json'],
    'images': ['.png', '.jpg', '.jpeg', '.gif', '.webp']
}

class FileProcessor:
    async def process_file(self, file_path: str, content_type: str) -> Dict:
        if content_type.startswith('text/'):
            return await self._process_text_file(file_path)
        elif content_type == 'application/pdf':
            return await self._process_pdf(file_path)
        elif content_type.startswith('image/'):
            return await self._process_image(file_path)
        else:
            raise UnsupportedFormatError(f"Unsupported format: {content_type}")
    
    async def _process_pdf(self, file_path: str) -> Dict:
        # PyPDF2 or pdfplumber integration
        import PyPDF2
        
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        
        return {
            'title': os.path.basename(file_path),
            'content': text,
            'content_type': 'document',
            'page_count': len(reader.pages)
        }
```

### Export File Formats
```python
# Export functionality
class ExportService:
    async def export_to_json(self, items: List[Dict]) -> str:
        """Export items as JSON"""
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'items': items,
            'total_count': len(items)
        }
        return json.dumps(export_data, indent=2, default=str)
    
    async def export_to_csv(self, items: List[Dict]) -> str:
        """Export items as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'title', 'url', 'summary', 'tags', 'created_at'
        ])
        writer.writeheader()
        
        for item in items:
            writer.writerow({
                'id': item['id'],
                'title': item['title'],
                'url': item.get('url', ''),
                'summary': item.get('summary', ''),
                'tags': ', '.join(item.get('tags', [])),
                'created_at': item['created_at']
            })
        
        return output.getvalue()
    
    async def export_to_markdown(self, items: List[Dict]) -> str:
        """Export items as Markdown"""
        output = []
        output.append("# PRSNL Knowledge Export\n")
        output.append(f"Exported on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for item in items:
            output.append(f"## {item['title']}\n")
            if item.get('url'):
                output.append(f"**URL**: {item['url']}\n")
            if item.get('summary'):
                output.append(f"**Summary**: {item['summary']}\n")
            if item.get('tags'):
                output.append(f"**Tags**: {', '.join(item['tags'])}\n")
            output.append(f"**Created**: {item['created_at']}\n\n")
            if item.get('content'):
                output.append(f"{item['content']}\n\n")
            output.append("---\n\n")
        
        return ''.join(output)
```

## REST API Endpoints

### Backend API Interface
```python
# FastAPI endpoint definitions
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="PRSNL API", version="1.0.0")

class CaptureRequest(BaseModel):
    url: Optional[str] = None
    title: str
    content: Optional[str] = None
    tags: List[str] = []
    content_type: str = "article"

class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict] = {}
    limit: int = 50
    offset: int = 0

@app.post("/api/capture")
async def capture_item(request: CaptureRequest):
    """Capture a new item"""
    try:
        item_id = await capture_service.process_item(request.dict())
        return {"success": True, "item_id": item_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def search_items(
    q: str,
    limit: int = 50,
    offset: int = 0,
    date_filter: Optional[str] = None,
    type_filter: Optional[str] = None
):
    """Search items with filters"""
    try:
        results = await search_service.search(
            query=q,
            limit=limit,
            offset=offset,
            date_filter=date_filter,
            type_filter=type_filter
        )
        return {"items": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timeline")
async def get_timeline(page: int = 1, per_page: int = 20):
    """Get timeline of items"""
    try:
        items = await database.get_timeline(page, per_page)
        return {"items": items, "page": page, "per_page": per_page}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process file"""
    try:
        content = await file.read()
        result = await file_processor.process_file(content, file.content_type)
        item_id = await capture_service.process_item(result)
        return {"success": True, "item_id": item_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Third-Party Service Integrations

### Font Services (Google Fonts)
```css
/* External font loading */
@import url('https://fonts.googleapis.com/css2?family=Mulish:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');

:root {
    --font-display: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-sans: 'Mulish', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

### Favicon Services
```javascript
// Google's favicon service as fallback
function getFaviconUrl(domain) {
    return `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
}
```

## Security Considerations

### API Security
```python
# CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Input validation and sanitization
import bleach

def sanitize_html(content: str) -> str:
    """Remove dangerous HTML tags and attributes"""
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    return bleach.clean(content, tags=allowed_tags, strip=True)
```

### Extension Security
```javascript
// Content Security Policy in manifest.json
"content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
}

// Secure message validation
function validateMessage(message, sender) {
    // Verify sender origin
    if (!sender.tab || !sender.tab.url.startsWith('https://')) {
        return false;
    }
    
    // Validate message structure
    if (!message.action || typeof message.action !== 'string') {
        return false;
    }
    
    return true;
}
```

## Error Handling and Retry Logic

### Network Error Handling
```python
# Robust HTTP client with retries
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class RobustHttpClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def fetch_with_retry(self, url: str) -> httpx.Response:
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            raise
```

### Extension Error Recovery
```javascript
// Offline queue for failed captures
class OfflineQueue {
    constructor() {
        this.queue = [];
        this.processing = false;
    }
    
    async addToQueue(item) {
        this.queue.push(item);
        await chrome.storage.local.set({ failedQueue: this.queue });
        
        // Try to process queue when online
        if (navigator.onLine && !this.processing) {
            this.processQueue();
        }
    }
    
    async processQueue() {
        this.processing = true;
        
        while (this.queue.length > 0) {
            const item = this.queue.shift();
            try {
                await this.sendToAPI(item);
            } catch (error) {
                // Put back in queue if still failing
                this.queue.unshift(item);
                break;
            }
        }
        
        await chrome.storage.local.set({ failedQueue: this.queue });
        this.processing = false;
    }
}
```