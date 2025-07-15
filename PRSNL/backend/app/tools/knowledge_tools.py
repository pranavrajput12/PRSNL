"""
Knowledge management Crew.ai tools
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Type
from crewai_tools import BaseTool
from pydantic import BaseModel, Field

from app.db.database import get_db_pool
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.unified_ai_service import unified_ai_service
from app.tools import register_tool

logger = logging.getLogger(__name__)


class KnowledgeGraphInput(BaseModel):
    """Input schema for knowledge graph tool"""
    action: str = Field(..., description="Action to perform: create, update, query, find_connections")
    entity_name: Optional[str] = Field(None, description="Entity name")
    entity_type: Optional[str] = Field(None, description="Entity type")
    properties: Optional[Dict[str, Any]] = Field(None, description="Entity properties")
    query: Optional[str] = Field(None, description="Query for searching")


@register_tool("knowledge_graph")
class KnowledgeGraphTool(BaseTool):
    name: str = "Knowledge Graph"
    description: str = (
        "Manages knowledge graph operations including creating entities, "
        "finding connections, and querying the knowledge base."
    )
    args_schema: Type[BaseModel] = KnowledgeGraphInput
    
    def _run(
        self,
        action: str,
        entity_name: Optional[str] = None,
        entity_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        query: Optional[str] = None
    ) -> str:
        """Execute knowledge graph operations"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_kg_operation(action, entity_name, entity_type, properties, query)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Knowledge graph operation failed: {e}")
            return f"Knowledge graph operation failed: {str(e)}"
    
    async def _async_kg_operation(
        self, 
        action: str,
        entity_name: Optional[str],
        entity_type: Optional[str],
        properties: Optional[Dict[str, Any]],
        query: Optional[str]
    ) -> str:
        """Async knowledge graph operations"""
        try:
            kg_service = KnowledgeGraphService()
            
            if action == "create":
                if not entity_name or not entity_type:
                    return "Error: entity_name and entity_type required for create action"
                
                # Create entity in knowledge graph
                entity_id = await kg_service.create_entity(
                    name=entity_name,
                    entity_type=entity_type,
                    properties=properties or {}
                )
                return f"Created entity '{entity_name}' of type '{entity_type}' with ID: {entity_id}"
            
            elif action == "find_connections":
                if not entity_name:
                    return "Error: entity_name required for find_connections"
                
                connections = await kg_service.find_entity_connections(entity_name)
                if not connections:
                    return f"No connections found for '{entity_name}'"
                
                output = f"Connections for '{entity_name}':\n"
                for conn in connections[:10]:
                    output += f"- {conn['related_entity']} ({conn['relationship_type']})\n"
                return output
            
            elif action == "query":
                if not query:
                    return "Error: query required for query action"
                
                results = await kg_service.query_knowledge_graph(query)
                if not results:
                    return "No results found for your query"
                
                output = f"Query results for '{query}':\n"
                for result in results[:10]:
                    output += f"- {result['name']} ({result['type']}): {result.get('description', 'N/A')}\n"
                return output
            
            else:
                return f"Unknown action: {action}. Use: create, find_connections, or query"
                
        except Exception as e:
            logger.error(f"Async KG operation failed: {e}")
            raise


class ConnectionFinderInput(BaseModel):
    """Input schema for connection finder tool"""
    content: str = Field(..., description="Content to find connections for")
    existing_tags: Optional[List[str]] = Field([], description="Existing tags to consider")
    limit: Optional[int] = Field(10, description="Maximum connections to return")


@register_tool("connection_finder")
class ConnectionFinderTool(BaseTool):
    name: str = "Connection Finder"
    description: str = (
        "Finds connections between content and existing knowledge in the database. "
        "Uses semantic similarity and tag matching."
    )
    args_schema: Type[BaseModel] = ConnectionFinderInput
    
    def _run(
        self,
        content: str,
        existing_tags: List[str] = [],
        limit: int = 10
    ) -> str:
        """Find connections in existing knowledge"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_find_connections(content, existing_tags, limit)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Connection finding failed: {e}")
            return f"Failed to find connections: {str(e)}"
    
    async def _async_find_connections(
        self,
        content: str,
        existing_tags: List[str],
        limit: int
    ) -> str:
        """Async connection finding"""
        try:
            pool = await get_db_pool()
            
            # Generate embedding for content
            embeddings = await unified_ai_service.generate_embeddings([content[:2000]])
            if not embeddings or not embeddings[0]:
                return "Failed to generate embedding for content"
            
            embedding = embeddings[0]
            
            async with pool.acquire() as conn:
                # Find similar content by embedding
                similar_query = """
                    SELECT 
                        id, title, url, tags,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM items
                    WHERE embedding IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT $2
                """
                
                similar_items = await conn.fetch(similar_query, embedding, limit)
                
                if not similar_items:
                    return "No similar content found in knowledge base"
                
                output = "Found connections to existing knowledge:\n\n"
                
                for item in similar_items:
                    similarity = item['similarity']
                    if similarity < 0.5:
                        continue
                        
                    output += f"- {item['title']}\n"
                    output += f"  Similarity: {similarity:.2%}\n"
                    if item['tags']:
                        output += f"  Tags: {', '.join(item['tags'])}\n"
                    if item['url']:
                        output += f"  URL: {item['url']}\n"
                    output += "\n"
                
                # Also find by tag overlap
                if existing_tags:
                    tag_query = """
                        SELECT id, title, tags, url
                        FROM items
                        WHERE tags && $1::text[]
                        LIMIT $2
                    """
                    tag_matches = await conn.fetch(tag_query, existing_tags, 5)
                    
                    if tag_matches:
                        output += "\nConnections by shared tags:\n"
                        for item in tag_matches:
                            shared_tags = set(item['tags']) & set(existing_tags)
                            output += f"- {item['title']}\n"
                            output += f"  Shared tags: {', '.join(shared_tags)}\n\n"
                
                return output
                
        except Exception as e:
            logger.error(f"Async connection finding failed: {e}")
            raise


class TagSuggesterInput(BaseModel):
    """Input schema for tag suggester tool"""
    content: str = Field(..., description="Content to suggest tags for")
    existing_tags: Optional[List[str]] = Field([], description="Existing tags in the system")
    limit: Optional[int] = Field(10, description="Maximum tags to suggest")


@register_tool("tag_suggester")
class TagSuggesterTool(BaseTool):
    name: str = "Tag Suggester"
    description: str = (
        "Suggests relevant tags for content based on analysis "
        "and existing tag taxonomy."
    )
    args_schema: Type[BaseModel] = TagSuggesterInput
    
    def _run(
        self,
        content: str,
        existing_tags: List[str] = [],
        limit: int = 10
    ) -> str:
        """Suggest tags for content"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._async_suggest_tags(content, existing_tags, limit)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Tag suggestion failed: {e}")
            return f"Failed to suggest tags: {str(e)}"
    
    async def _async_suggest_tags(
        self,
        content: str,
        existing_tags: List[str],
        limit: int
    ) -> str:
        """Async tag suggestion"""
        try:
            # Use AI to generate tags
            tags = await unified_ai_service.generate_tags(
                content=content[:2000],
                limit=limit,
                existing_tags=existing_tags
            )
            
            if not tags:
                return "No tags could be suggested for this content"
            
            output = f"Suggested tags ({len(tags)}):\n"
            for tag in tags:
                output += f"- {tag}\n"
            
            # Also suggest from existing tags based on content
            if existing_tags:
                output += "\nRelevant existing tags:\n"
                # Simple keyword matching
                content_lower = content.lower()
                relevant_existing = [
                    tag for tag in existing_tags
                    if tag.lower() in content_lower
                ][:5]
                
                for tag in relevant_existing:
                    output += f"- {tag}\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Async tag suggestion failed: {e}")
            raise