# PRSNL Implementation Plan

## Phase 1: Foundation (Week 1)

### 1.1 Project Setup (Day 1)
**Owner: Claude Code + Windsurf**

```bash
# I'll create the core structure, Windsurf scaffolds the boilerplate
PRSNL/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app (Claude)
│   │   ├── config.py         # Configuration (Claude)
│   │   ├── database.py       # DB connection (Claude)
│   │   └── dependencies.py   # Shared deps (Claude)
│   ├── api/
│   │   ├── capture.py        # Capture endpoint (Claude)
│   │   ├── search.py         # Search endpoint (Claude)
│   │   └── items.py          # CRUD endpoints (Windsurf)
│   ├── core/
│   │   ├── capture_engine.py # Core logic (Claude)
│   │   ├── search_engine.py  # Search orchestrator (Claude)
│   │   └── llm_processor.py  # LLM pipeline (Claude)
│   ├── models/
│   │   └── schemas.py        # Pydantic models (Claude)
│   └── services/
│       ├── scraper.py        # Web scraping (Claude)
│       ├── embeddings.py     # Vector generation (Claude)
│       └── storage.py        # Blob storage (Claude)
├── docker-compose.yml        # Local stack (Claude)
└── requirements.txt          # Dependencies (Windsurf)
```

### 1.2 Database Schema Implementation (Day 1)
**Owner: Claude Code**

```python
# backend/app/models/database.py
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Item(Base):
    __tablename__ = "items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    src_type = Column(String(20), nullable=False, index=True)
    src_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(String)
    
    # Core content
    raw_content = Column(String)  # Original HTML/text
    processed_content = Column(String)  # Clean text
    content_hash = Column(String, unique=True)  # Deduplication
    
    # Search vectors
    embedding = Column(Vector(1536))  # OpenAI ada-002 dimensions
    search_vector = Column(TSVector)  # Full-text search
    
    # Metadata
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, server_default=func.now())
    accessed_at = Column(DateTime, server_default=func.now())
    access_count = Column(Integer, default=0)
    
    __table_args__ = (
        UniqueConstraint('src_type', 'src_id'),
        Index('idx_search', 'search_vector', postgresql_using='gin'),
        Index('idx_embedding', 'embedding', postgresql_using='ivfflat'),
        Index('idx_created', 'created_at'),
    )
```

### 1.3 Core Capture API (Day 2)
**Owner: Claude Code**

```python
# backend/app/api/capture.py
from fastapi import APIRouter, BackgroundTasks, Depends
from app.core.capture_engine import CaptureEngine
from app.schemas import CaptureRequest, CaptureResponse

router = APIRouter(prefix="/api/capture", tags=["capture"])

@router.post("/", response_model=CaptureResponse)
async def capture_item(
    request: CaptureRequest,
    background_tasks: BackgroundTasks,
    capture_engine: CaptureEngine = Depends()
):
    """
    One-click capture endpoint - the heart of PRSNL
    """
    # Immediate response (< 100ms)
    item_id = await capture_engine.quick_save(
        url=request.url,
        highlight=request.highlight,
        tags=request.tags
    )
    
    # Process in background
    background_tasks.add_task(
        capture_engine.deep_process,
        item_id=item_id
    )
    
    return CaptureResponse(
        id=item_id,
        status="queued",
        message="Capturing in background"
    )
```

### 1.4 Capture Engine Implementation (Day 2-3)
**Owner: Claude Code**

```python
# backend/app/core/capture_engine.py
import hashlib
from typing import Optional, List
from app.services.scraper import SmartScraper
from app.services.llm_processor import LLMProcessor
from app.services.embeddings import EmbeddingService

class CaptureEngine:
    def __init__(self):
        self.scraper = SmartScraper()
        self.llm = LLMProcessor()
        self.embeddings = EmbeddingService()
    
    async def quick_save(self, url: str, highlight: Optional[str], tags: List[str]) -> str:
        """Stage 1: Immediate save with minimal processing"""
        # Generate content hash for deduplication
        content_hash = hashlib.sha256(f"{url}{highlight}".encode()).hexdigest()
        
        # Check if already exists
        existing = await self.db.get_by_hash(content_hash)
        if existing:
            return existing.id
        
        # Create item with basic info
        item = await self.db.create_item({
            "url": url,
            "title": url,  # Temporary, will update
            "highlight": highlight,
            "tags": tags,
            "content_hash": content_hash,
            "status": "pending"
        })
        
        return item.id
    
    async def deep_process(self, item_id: str):
        """Stage 2: Full processing pipeline"""
        item = await self.db.get_item(item_id)
        
        # 1. Scrape content
        scraped = await self.scraper.extract(item.url)
        
        # 2. Generate summary and tags (local first)
        llm_result = await self.llm.process(
            content=scraped.text,
            existing_tags=item.tags
        )
        
        # 3. Generate embeddings
        embedding = await self.embeddings.generate(llm_result.processed_text)
        
        # 4. Update item
        await self.db.update_item(item_id, {
            "title": scraped.title or llm_result.title,
            "summary": llm_result.summary,
            "raw_content": scraped.html,
            "processed_content": llm_result.processed_text,
            "tags": llm_result.tags,
            "embedding": embedding,
            "metadata": {
                "author": scraped.author,
                "published": scraped.published,
                "word_count": len(llm_result.processed_text.split())
            },
            "status": "completed"
        })
```

## Phase 2: Search Implementation (Week 1-2)

### 2.1 Hybrid Search Engine (Day 4-5)
**Owner: Claude Code**

```python
# backend/app/core/search_engine.py
from typing import List, Dict, Any
import asyncio
from app.services.embeddings import EmbeddingService

class SearchEngine:
    def __init__(self):
        self.embeddings = EmbeddingService()
        
    async def search(
        self, 
        query: str, 
        filters: Dict[str, Any] = {}, 
        limit: int = 20
    ) -> List[SearchResult]:
        """
        Hybrid search combining:
        1. BM25 keyword search
        2. Vector similarity search
        3. Recency boost
        4. LLM re-ranking (optional)
        """
        # Run searches in parallel
        keyword_task = asyncio.create_task(self._keyword_search(query, filters))
        vector_task = asyncio.create_task(self._vector_search(query, filters))
        
        keyword_results, vector_results = await asyncio.gather(
            keyword_task, vector_task
        )
        
        # Merge and rank
        merged = self._merge_results(keyword_results, vector_results)
        
        # Apply recency boost
        boosted = self._apply_recency_boost(merged)
        
        # Optional: LLM re-rank for top results
        if len(query.split()) > 3:  # Complex query
            boosted[:5] = await self._llm_rerank(query, boosted[:5])
        
        return boosted[:limit]
    
    async def _keyword_search(self, query: str, filters: Dict) -> List[Dict]:
        """PostgreSQL full-text search with typo tolerance"""
        # Build tsquery with fuzzy matching
        tsquery = self._build_fuzzy_tsquery(query)
        
        sql = """
        SELECT id, title, summary, url, 
               ts_rank(search_vector, query) as rank
        FROM items, 
             plainto_tsquery('english', %s) query
        WHERE search_vector @@ query
        AND (%s)
        ORDER BY rank DESC
        LIMIT 50
        """
        
        filter_clause = self._build_filter_clause(filters)
        results = await self.db.fetch(sql, tsquery, filter_clause)
        
        return results
    
    async def _vector_search(self, query: str, filters: Dict) -> List[Dict]:
        """pgvector similarity search"""
        # Generate query embedding
        query_embedding = await self.embeddings.generate(query)
        
        sql = """
        SELECT id, title, summary, url,
               1 - (embedding <=> %s::vector) as similarity
        FROM items
        WHERE (%s)
        ORDER BY embedding <=> %s::vector
        LIMIT 50
        """
        
        filter_clause = self._build_filter_clause(filters)
        results = await self.db.fetch(
            sql, query_embedding, filter_clause, query_embedding
        )
        
        return results
```

### 2.2 Search API (Day 5)
**Owner: Claude Code**

```python
# backend/app/api/search.py
from fastapi import APIRouter, Query, Depends
from typing import Optional, List
from app.core.search_engine import SearchEngine
from app.schemas import SearchRequest, SearchResult

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("/", response_model=List[SearchResult])
async def search(
    q: str = Query(..., description="Search query"),
    src_type: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    limit: int = Query(20, le=100),
    search_engine: SearchEngine = Depends()
):
    """
    Ultra-fast hybrid search endpoint
    Target: < 1s for 100k items
    """
    filters = {}
    if src_type:
        filters["src_type"] = src_type
    if tags:
        filters["tags"] = tags
    
    results = await search_engine.search(
        query=q,
        filters=filters,
        limit=limit
    )
    
    # Log access for learning
    await search_engine.log_query(q, results)
    
    return results
```

## Phase 3: LLM Integration (Week 2)

### 3.1 Smart LLM Processor (Day 6-7)
**Owner: Claude Code**

```python
# backend/app/services/llm_processor.py
import ollama
from openai import AsyncAzureOpenAI
from typing import Dict, List, Optional

class LLMProcessor:
    def __init__(self):
        self.ollama_client = ollama.Client()
        self.azure_client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version="2024-02-01",
            azure_endpoint=settings.AZURE_ENDPOINT
        )
        self.credit_usage = 0
        self.credit_limit = settings.AZURE_CREDIT_LIMIT
    
    async def process(self, content: str, existing_tags: List[str] = []) -> ProcessedContent:
        """
        Smart routing: Local first, Azure fallback
        """
        # Try local Llama 3 first
        try:
            if len(content) < 8000:  # Llama 3 context limit
                return await self._process_local(content, existing_tags)
        except Exception as e:
            logger.warning(f"Local LLM failed: {e}")
        
        # Fallback to Azure if:
        # 1. Content too long for local
        # 2. Local failed
        # 3. Still have credits
        if self.credit_usage < self.credit_limit * 0.8:
            return await self._process_azure(content, existing_tags)
        
        # Emergency fallback: Basic processing
        return self._basic_process(content, existing_tags)
    
    async def _process_local(self, content: str, tags: List[str]) -> ProcessedContent:
        """Ollama + Llama 3 processing"""
        prompt = f"""
        Analyze this content and provide:
        1. A concise title (max 100 chars)
        2. A summary (max 200 chars) 
        3. Key topics as tags (5-10 tags)
        4. Clean, processed text
        
        Existing tags: {tags}
        Content: {content[:4000]}
        
        Response format:
        TITLE: ...
        SUMMARY: ...
        TAGS: tag1, tag2, tag3
        PROCESSED: ...
        """
        
        response = self.ollama_client.generate(
            model="llama3",
            prompt=prompt,
            stream=False
        )
        
        return self._parse_llm_response(response['response'])
    
    async def _process_azure(self, content: str, tags: List[str]) -> ProcessedContent:
        """Azure OpenAI processing for complex content"""
        messages = [
            {"role": "system", "content": "You are a personal knowledge assistant. Extract and structure information concisely."},
            {"role": "user", "content": self._build_azure_prompt(content, tags)}
        ]
        
        response = await self.azure_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Track credit usage
        self.credit_usage += response.usage.total_tokens * 0.00006  # Rough estimate
        
        return self._parse_llm_response(response.choices[0].message.content)
```

### 3.2 Embedding Service (Day 7)
**Owner: Claude Code**

```python
# backend/app/services/embeddings.py
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib
from typing import List, Optional

class EmbeddingService:
    def __init__(self):
        # Local model for embeddings (no API costs!)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cache = {}  # Simple in-memory cache
        
    async def generate(self, text: str) -> List[float]:
        """Generate embeddings with caching"""
        # Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        # Normalize for better similarity search
        embedding = embedding / np.linalg.norm(embedding)
        
        # Cache it
        self.cache[text_hash] = embedding.tolist()
        
        return embedding.tolist()
    
    async def batch_generate(self, texts: List[str]) -> List[List[float]]:
        """Efficient batch processing"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        # Normalize all
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        return embeddings.tolist()
```

## Phase 4: Browser Extension (Week 2)

### 4.1 Extension Core (Day 8)
**Owner: Claude Code**

```javascript
// extension/src/background.js
chrome.runtime.onInstalled.addListener(() => {
  // Register keyboard shortcut
  chrome.commands.onCommand.addListener((command) => {
    if (command === "quick-capture") {
      captureCurrentTab();
    }
  });
});

async function captureCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  // Get selected text if any
  const selection = await chrome.tabs.executeScript(tab.id, {
    code: "window.getSelection().toString();"
  });
  
  // Send to PRSNL
  const response = await fetch('http://localhost:8000/api/capture', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url: tab.url,
      title: tab.title,
      highlight: selection[0] || null
    })
  });
  
  // Quick feedback
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icon.png',
    title: 'PRSNL',
    message: 'Captured! Press Cmd+Shift+Space to search.'
  });
}
```

## Phase 5: Global Search Overlay (Week 3)

### 5.1 Native Hotkey App (Day 10-11)
**Owner: Claude Code**

```python
# overlay/prsnl_overlay.py
import webview
import keyboard
import requests
from threading import Thread

class PRSNLOverlay:
    def __init__(self):
        self.window = None
        self.api_url = "http://localhost:8000"
        
    def create_window(self):
        self.window = webview.create_window(
            'PRSNL Search',
            'overlay.html',
            width=800,
            height=100,
            y=100,
            frameless=True,
            on_top=True
        )
        
    def show_overlay(self):
        if not self.window:
            self.create_window()
        self.window.show()
        
    def hide_overlay(self):
        if self.window:
            self.window.hide()
            
    def search(self, query):
        """Called from JS in overlay"""
        response = requests.get(
            f"{self.api_url}/api/search",
            params={"q": query, "limit": 10}
        )
        return response.json()

# Register global hotkey
overlay = PRSNLOverlay()
keyboard.add_hotkey('cmd+shift+space', overlay.show_overlay)
```

## Phase 6: Testing & Optimization (Week 3-4)

### 6.1 Performance Testing Suite
**Owner: Claude Code**

```python
# tests/test_performance.py
import pytest
import asyncio
from httpx import AsyncClient
import time

@pytest.mark.asyncio
async def test_search_latency():
    """Ensure < 1s search on 100k items"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        start = time.time()
        response = await client.get("/api/search?q=python%20async")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Under 1 second
        assert len(response.json()) > 0

@pytest.mark.asyncio
async def test_capture_latency():
    """Ensure < 3s capture including scraping"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        start = time.time()
        response = await client.post("/api/capture", json={
            "url": "https://example.com",
            "tags": ["test"]
        })
        
        # Wait for background processing
        await asyncio.sleep(3)
        
        # Check item was processed
        item_id = response.json()["id"]
        item = await client.get(f"/api/items/{item_id}")
        
        assert item.json()["status"] == "completed"
        assert time.time() - start < 3.0
```

## Development Timeline

### Week 1: Foundation
- Day 1-2: Project setup, database, core APIs
- Day 3-4: Capture engine implementation
- Day 5: Search engine core

### Week 2: Intelligence
- Day 6-7: LLM integration (Ollama + Azure)
- Day 8-9: Browser extension
- Day 10: Testing framework

### Week 3: Polish
- Day 11-12: Global overlay implementation
- Day 13-14: Performance optimization
- Day 15: Documentation

### Week 4: Launch Ready
- Final testing
- Deployment scripts
- User documentation

## Key Decisions I'm Making

1. **PostgreSQL over separate vector DB** - Simpler ops, pgvector is fast enough
2. **Local embeddings model** - No API costs, good enough quality
3. **Background processing** - Instant capture feel, process later
4. **Simple overlay** - Native Python, no Electron bloat
5. **Hybrid search from day 1** - Both keyword and semantic

Ready to start implementation?