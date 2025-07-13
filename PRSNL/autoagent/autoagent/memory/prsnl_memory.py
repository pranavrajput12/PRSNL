"""
PRSNL Memory Module for AutoAgent Integration

This module extends AutoAgent's RAG memory to work with PRSNL's 
PostgreSQL + pgvector knowledge base, enabling intelligent multi-agent
knowledge processing.
"""

import os
import asyncio
import asyncpg
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import logging

from autoagent.memory.rag_memory import RagMemory
from autoagent.memory.utils import Document, SearchResult
from autoagent.types import Message

logger = logging.getLogger(__name__)

class PRSNLMemory(RagMemory):
    """
    Custom memory implementation for PRSNL that uses PostgreSQL with pgvector
    for efficient semantic search and knowledge base integration.
    """
    
    def __init__(self, 
                 db_url: str = None,
                 collection_name: str = "prsnl_knowledge_base",
                 embedding_model: str = "text-embedding-ada-002",
                 embedding_dimension: int = 1536):
        """Initialize PRSNL memory with PostgreSQL connection."""
        self.db_url = db_url or os.getenv('PRSNL_DB_URL', 'postgresql://pronav@localhost:5433/prsnl')
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension
        self.pool = None
        
        # Initialize parent class
        super().__init__(collection_name=collection_name)
        
    async def initialize(self):
        """Initialize database connection pool."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info(f"Connected to PRSNL database at {self.db_url}")
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to PRSNL knowledge base.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            List of document IDs
        """
        await self.initialize()
        
        doc_ids = []
        async with self.pool.acquire() as conn:
            for doc in documents:
                try:
                    # Insert into items table
                    item_id = await conn.fetchval("""
                        INSERT INTO items (
                            title, content, summary, type, tags, 
                            created_at, updated_at, url, metadata
                        ) VALUES (
                            $1, $2, $3, $4, $5, 
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, $6, $7
                        ) RETURNING id
                    """, 
                        doc.metadata.get('title', 'AutoAgent Document'),
                        doc.content,
                        doc.metadata.get('summary', ''),
                        doc.metadata.get('type', 'autoagent'),
                        doc.metadata.get('tags', []),
                        doc.metadata.get('url', ''),
                        json.dumps(doc.metadata)
                    )
                    
                    # Insert embedding if available
                    if hasattr(doc, 'embedding') and doc.embedding is not None:
                        await conn.execute("""
                            INSERT INTO embeddings (
                                item_id, embedding, model, created_at
                            ) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                        """, item_id, doc.embedding, self.embedding_model)
                    
                    doc_ids.append(str(item_id))
                    logger.info(f"Added document {item_id} to PRSNL knowledge base")
                    
                except Exception as e:
                    logger.error(f"Error adding document: {e}")
                    continue
        
        return doc_ids
    
    async def search(self, 
                    query: str, 
                    query_embedding: Optional[List[float]] = None,
                    top_k: int = 5,
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search PRSNL knowledge base using semantic search.
        
        Args:
            query: Search query text
            query_embedding: Pre-computed query embedding
            top_k: Number of results to return
            filters: Optional filters for search
            
        Returns:
            List of SearchResult objects
        """
        await self.initialize()
        
        results = []
        
        async with self.pool.acquire() as conn:
            # Build the query
            if query_embedding:
                # Semantic search using embeddings
                rows = await conn.fetch("""
                    SELECT 
                        i.id, i.title, i.content, i.summary, i.url, i.type, i.tags,
                        i.created_at, i.updated_at, i.metadata,
                        1 - (e.embedding <=> $1::vector) as similarity
                    FROM items i
                    JOIN embeddings e ON i.id = e.item_id
                    WHERE e.model = $2
                    ORDER BY e.embedding <=> $1::vector
                    LIMIT $3
                """, query_embedding, self.embedding_model, top_k)
            else:
                # Full-text search fallback
                rows = await conn.fetch("""
                    SELECT 
                        id, title, content, summary, url, type, tags,
                        created_at, updated_at, metadata,
                        ts_rank(search_vector, plainto_tsquery($1)) as similarity
                    FROM items
                    WHERE search_vector @@ plainto_tsquery($1)
                    ORDER BY similarity DESC
                    LIMIT $2
                """, query, top_k)
            
            # Convert to SearchResult objects
            for row in rows:
                result = SearchResult(
                    id=str(row['id']),
                    content=row['content'],
                    metadata={
                        'title': row['title'],
                        'summary': row['summary'],
                        'url': row['url'],
                        'type': row['type'],
                        'tags': row['tags'],
                        'created_at': row['created_at'].isoformat(),
                        'updated_at': row['updated_at'].isoformat(),
                        **json.loads(row['metadata'] or '{}')
                    },
                    score=float(row['similarity'])
                )
                results.append(result)
        
        return results
    
    async def get_context_for_query(self, query: str, max_tokens: int = 2000) -> str:
        """
        Get relevant context from knowledge base for a query.
        
        Args:
            query: User query
            max_tokens: Maximum tokens to include in context
            
        Returns:
            Formatted context string
        """
        # Search for relevant documents
        results = await self.search(query, top_k=5)
        
        if not results:
            return "No relevant context found in the knowledge base."
        
        # Format context
        context_parts = ["# Relevant Knowledge Base Context\n"]
        
        for i, result in enumerate(results, 1):
            title = result.metadata.get('title', 'Untitled')
            summary = result.metadata.get('summary', '')
            content = result.content[:500]  # Limit content length
            
            context_parts.append(f"\n## {i}. {title}")
            if summary:
                context_parts.append(f"Summary: {summary}")
            context_parts.append(f"Content: {content}...")
            
            if result.metadata.get('url'):
                context_parts.append(f"Source: {result.metadata['url']}")
            
            context_parts.append(f"Relevance: {result.score:.2%}\n")
        
        return "\n".join(context_parts)
    
    async def save_agent_memory(self, agent_id: str, memory_data: Dict[str, Any]):
        """
        Save agent-specific memory and state.
        
        Args:
            agent_id: Unique identifier for the agent
            memory_data: Memory data to save
        """
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO agent_memory (agent_id, memory_data, updated_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (agent_id) 
                DO UPDATE SET 
                    memory_data = $2,
                    updated_at = CURRENT_TIMESTAMP
            """, agent_id, json.dumps(memory_data))
    
    async def load_agent_memory(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Load agent-specific memory and state.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Memory data if found, None otherwise
        """
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT memory_data FROM agent_memory WHERE agent_id = $1
            """, agent_id)
            
            if row:
                return json.loads(row['memory_data'])
            return None
    
    async def get_related_items(self, item_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get items related to a specific item using embeddings.
        
        Args:
            item_id: ID of the item to find relations for
            limit: Maximum number of related items
            
        Returns:
            List of related items with similarity scores
        """
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            # Get the embedding for the source item
            embedding = await conn.fetchval("""
                SELECT embedding FROM embeddings 
                WHERE item_id = $1 AND model = $2
            """, int(item_id), self.embedding_model)
            
            if not embedding:
                return []
            
            # Find similar items
            rows = await conn.fetch("""
                SELECT 
                    i.id, i.title, i.summary, i.type,
                    1 - (e.embedding <=> $1::vector) as similarity
                FROM items i
                JOIN embeddings e ON i.id = e.item_id
                WHERE e.model = $2 AND i.id != $3
                ORDER BY e.embedding <=> $1::vector
                LIMIT $4
            """, embedding, self.embedding_model, int(item_id), limit)
            
            return [
                {
                    'id': str(row['id']),
                    'title': row['title'],
                    'summary': row['summary'],
                    'type': row['type'],
                    'similarity': float(row['similarity'])
                }
                for row in rows
            ]
    
    async def create_knowledge_graph_node(self, node_data: Dict[str, Any]) -> str:
        """
        Create a node in the knowledge graph for relationship tracking.
        
        Args:
            node_data: Node information
            
        Returns:
            Node ID
        """
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            node_id = await conn.fetchval("""
                INSERT INTO knowledge_graph_nodes (
                    item_id, node_type, properties, created_at
                ) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                RETURNING id
            """, 
                node_data.get('item_id'),
                node_data.get('node_type', 'concept'),
                json.dumps(node_data.get('properties', {}))
            )
            
        return str(node_id)
    
    async def create_knowledge_graph_edge(self, 
                                         source_id: str, 
                                         target_id: str,
                                         relationship: str,
                                         properties: Optional[Dict[str, Any]] = None) -> str:
        """
        Create an edge in the knowledge graph.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            relationship: Type of relationship
            properties: Additional properties
            
        Returns:
            Edge ID
        """
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            edge_id = await conn.fetchval("""
                INSERT INTO knowledge_graph_edges (
                    source_id, target_id, relationship, properties, created_at
                ) VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                RETURNING id
            """, 
                int(source_id), 
                int(target_id), 
                relationship,
                json.dumps(properties or {})
            )
            
        return str(edge_id)