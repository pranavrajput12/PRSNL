# 🧠 GEMINI - AI Enhancement Tasks

## Your Assigned Tasks:

### Task 1: Implement Embedding Infrastructure
**Priority**: P0 - Foundation for semantic search
**Files to create/modify**:
1. `/backend/app/services/embedding_service.py` - New service for embeddings
2. `/backend/app/db/init_db.sql` - Add embedding column to items table
3. `/backend/app/api/search.py` - Add semantic search endpoints

**Implementation Steps**:

1. **Create Embedding Service**:
```python
# /backend/app/services/embedding_service.py
import numpy as np
from typing import List, Optional
import asyncio
from app.services.llm_processor import LLMProcessor

class EmbeddingService:
    def __init__(self):
        self.llm = LLMProcessor()
        self.cache = {}  # Simple in-memory cache
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using available AI provider"""
        # Check cache first
        if text in self.cache:
            return self.cache[text]
            
        # Try Azure OpenAI first, then Ollama
        embedding = await self._azure_embedding(text)
        if not embedding:
            embedding = await self._ollama_embedding(text)
            
        if embedding:
            self.cache[text] = embedding
        return embedding
        
    async def batch_generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        tasks = [self.generate_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)
```

2. **Database Schema Update**:
```sql
-- Add to init_db.sql
ALTER TABLE items ADD COLUMN IF NOT EXISTS embedding vector(1536);
CREATE INDEX IF NOT EXISTS idx_items_embedding ON items USING ivfflat (embedding vector_cosine_ops);
```

3. **New API Endpoints**:
```python
# Add to /backend/app/api/search.py
@router.get("/search/similar/{item_id}")
async def find_similar_items(item_id: str, limit: int = 10):
    """Find items similar to the given item using embeddings"""
    
@router.post("/search/semantic")
async def semantic_search(query: str, limit: int = 20):
    """Search using semantic similarity"""
```

### Task 2: Streaming AI Response Infrastructure
**Priority**: P1 - Better UX
**Files to create/modify**:
1. `/backend/app/core/websocket_manager.py` - WebSocket connection manager
2. `/backend/app/api/ws.py` - WebSocket endpoints
3. Update `/backend/app/main.py` to include WebSocket routes

**WebSocket Implementation**:
```python
# /backend/app/api/ws.py
from fastapi import WebSocket, WebSocketDisconnect
from app.services.llm_processor import LLMProcessor

@router.websocket("/ws/ai-stream")
async def ai_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Stream AI responses back
            async for chunk in llm.stream_process(data["content"]):
                await websocket.send_json({"chunk": chunk})
    except WebSocketDisconnect:
        pass
```

## Testing Instructions:
1. Test embedding generation: `curl -X POST http://localhost:8000/api/test-embedding -d '{"text": "test"}'`
2. Test semantic search: `curl http://localhost:8000/api/search/semantic?query=machine+learning`
3. Test WebSocket: Use the provided WebSocket test client in `/backend/tests/test_websocket.py`

## Success Criteria:
- [ ] Embeddings generated for all new items
- [ ] Semantic search returns relevant results
- [ ] WebSocket streaming works smoothly
- [ ] < 500ms response time for embedding generation
- [ ] Batch processing handles 100+ items efficiently

Start with the embedding service first as it's the foundation for semantic search!