"""
Entity Extraction Service for Knowledge Graph Integration
Extracts entities from different content types and creates knowledge graph relationships
"""
import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from app.config import settings
from app.db.database import get_db_pool
from app.services.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)


class EntityExtractionService:
    """
    Service for extracting entities from various content types and linking them to the knowledge graph.
    Supports conversations, videos, code, timeline events, and general content.
    """
    
    def __init__(self):
        self.ai_service = unified_ai_service
        
        # Entity type mappings for different content types
        self.content_type_mappings = {
            'conversation': ['conversation_turn', 'text_entity', 'knowledge_concept'],
            'video': ['video_segment', 'audio_entity', 'knowledge_concept'],
            'code': ['code_function', 'code_class', 'code_module', 'text_entity'],
            'github_repo': ['code_function', 'code_class', 'code_module'],
            'github_document': ['text_entity', 'knowledge_concept'],
            'article': ['text_entity', 'knowledge_concept'],
            'note': ['text_entity', 'knowledge_concept'],
            'timeline': ['timeline_event', 'knowledge_concept']
        }
        
        # Relationship type mappings
        self.relationship_mappings = {
            'technical_content': ['implements', 'explains', 'demonstrates', 'references'],
            'conversational': ['discusses', 'explains', 'builds_on'],
            'temporal': ['precedes', 'follows', 'enables'],
            'structural': ['contains', 'part_of', 'related_to']
        }
    
    async def extract_entities_from_content(
        self, 
        content_id: UUID,
        content_type: str,
        content_text: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Extract entities from content and create knowledge graph entries.
        
        Args:
            content_id: UUID of the source content
            content_type: Type of content (conversation, video, code, etc.)
            content_text: Raw text content to analyze
            metadata: Additional metadata about the content
            
        Returns:
            Dict with extraction results and created entities
        """
        try:
            logger.info(f"🔍 Starting entity extraction for content {content_id} (type: {content_type})")
            
            extraction_results = {
                "content_id": str(content_id),
                "content_type": content_type,
                "entities_created": [],
                "relationships_created": [],
                "extraction_method": "ai_extracted",
                "success": False
            }
            
            # Step 1: Content-specific entity extraction
            entities = await self._extract_content_specific_entities(
                content_id, content_type, content_text, metadata
            )
            
            # Step 2: Create unified entities in database
            created_entities = []
            for entity_data in entities:
                entity_id = await self._create_unified_entity(content_id, entity_data)
                if entity_id:
                    created_entities.append({
                        "entity_id": str(entity_id),
                        "name": entity_data["name"],
                        "entity_type": entity_data["entity_type"],
                        "confidence": entity_data.get("confidence", 1.0)
                    })
            
            extraction_results["entities_created"] = created_entities
            
            # Step 3: Extract and create relationships
            if len(created_entities) > 1:
                relationships = await self._extract_entity_relationships(
                    created_entities, content_text, content_type
                )
                extraction_results["relationships_created"] = relationships
            
            # Step 4: Link entities to source content
            await self._link_entities_to_content(content_id, created_entities)
            
            extraction_results["success"] = True
            logger.info(f"✅ Entity extraction completed for {content_id}. "
                       f"Created {len(created_entities)} entities, {len(extraction_results['relationships_created'])} relationships")
            
            return extraction_results
            
        except Exception as e:
            logger.error(f"❌ Entity extraction failed for {content_id}: {e}")
            extraction_results["error"] = str(e)
            return extraction_results
    
    async def _extract_content_specific_entities(
        self, 
        content_id: UUID, 
        content_type: str, 
        content_text: str, 
        metadata: Optional[Dict]
    ) -> List[Dict]:
        """Extract entities specific to the content type."""
        
        entities = []
        
        if content_type in ['conversation']:
            entities.extend(await self._extract_conversation_entities(content_text, metadata))
        
        elif content_type in ['video']:
            entities.extend(await self._extract_video_entities(content_text, metadata))
        
        elif content_type in ['code', 'github_repo', 'github_document']:
            entities.extend(await self._extract_code_entities(content_text, metadata))
        
        elif content_type in ['article', 'note', 'tutorial']:
            entities.extend(await self._extract_text_entities(content_text, metadata))
        
        # Always extract general knowledge concepts
        concepts = await self._extract_knowledge_concepts(content_text)
        entities.extend(concepts)
        
        return entities
    
    async def _extract_conversation_entities(self, content_text: str, metadata: Optional[Dict]) -> List[Dict]:
        """Extract entities from conversation content."""
        entities = []
        
        try:
            # Use AI to analyze conversation structure
            analysis_prompt = f"""
            Analyze this conversation and extract key entities:
            
            Content: {content_text[:3000]}
            
            Extract:
            1. Main topics discussed (as knowledge_concept entities)
            2. Key decisions or conclusions (as text_entity)
            3. Action items or next steps (as text_entity)
            4. Important people mentioned (as text_entity)
            5. Technical concepts or tools mentioned (as knowledge_concept)
            
            Return a JSON list of entities with: name, entity_type, description, confidence (0-1)
            """
            
            response = await self.ai_service.complete(
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse AI response
            try:
                ai_entities = json.loads(response)
                if isinstance(ai_entities, list):
                    for entity in ai_entities:
                        if all(key in entity for key in ['name', 'entity_type']):
                            entities.append({
                                "name": entity["name"],
                                "entity_type": entity["entity_type"],
                                "description": entity.get("description", ""),
                                "confidence": entity.get("confidence", 0.8),
                                "metadata": {"source": "conversation_analysis"}
                            })
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI entity extraction response")
            
        except Exception as e:
            logger.error(f"Error extracting conversation entities: {e}")
        
        return entities
    
    async def _extract_video_entities(self, content_text: str, metadata: Optional[Dict]) -> List[Dict]:
        """Extract entities from video content (transcript)."""
        entities = []
        
        try:
            # Extract video-specific entities
            analysis_prompt = f"""
            Analyze this video transcript and extract entities:
            
            Transcript: {content_text[:3000]}
            
            Extract:
            1. Key topics or themes (as knowledge_concept)
            2. Technical concepts explained (as knowledge_concept)
            3. Tools or software mentioned (as text_entity)
            4. Important timestamps or segments (as video_segment)
            5. Learning objectives (as knowledge_concept)
            
            Return JSON with entities containing: name, entity_type, description, confidence, start_time (if applicable)
            """
            
            response = await self.ai_service.complete(
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            try:
                ai_entities = json.loads(response)
                if isinstance(ai_entities, list):
                    for entity in ai_entities:
                        if all(key in entity for key in ['name', 'entity_type']):
                            entity_data = {
                                "name": entity["name"],
                                "entity_type": entity["entity_type"],
                                "description": entity.get("description", ""),
                                "confidence": entity.get("confidence", 0.8),
                                "metadata": {"source": "video_analysis"}
                            }
                            
                            # Add video-specific metadata
                            if "start_time" in entity:
                                entity_data["start_position"] = entity["start_time"]
                            
                            entities.append(entity_data)
            except json.JSONDecodeError:
                logger.warning("Failed to parse video entity extraction response")
            
        except Exception as e:
            logger.error(f"Error extracting video entities: {e}")
        
        return entities
    
    async def _extract_code_entities(self, content_text: str, metadata: Optional[Dict]) -> List[Dict]:
        """Extract entities from code content."""
        entities = []
        
        try:
            # Use regex patterns for basic code entity extraction
            # Function definitions
            function_pattern = r'(?:def|function|func)\s+(\w+)\s*\('
            functions = re.findall(function_pattern, content_text, re.IGNORECASE)
            
            for func_name in functions:
                entities.append({
                    "name": func_name,
                    "entity_type": "code_function",
                    "description": f"Function: {func_name}",
                    "confidence": 0.9,
                    "metadata": {"source": "regex_extraction", "pattern": "function"}
                })
            
            # Class definitions
            class_pattern = r'(?:class|interface)\s+(\w+)'
            classes = re.findall(class_pattern, content_text, re.IGNORECASE)
            
            for class_name in classes:
                entities.append({
                    "name": class_name,
                    "entity_type": "code_class",
                    "description": f"Class: {class_name}",
                    "confidence": 0.9,
                    "metadata": {"source": "regex_extraction", "pattern": "class"}
                })
            
            # Use AI for more sophisticated analysis
            if len(content_text) > 500:
                analysis_prompt = f"""
                Analyze this code and extract key entities:
                
                Code: {content_text[:2000]}
                
                Extract:
                1. Main classes and their purposes (as code_class)
                2. Important functions and their roles (as code_function)
                3. Key algorithms or patterns used (as knowledge_concept)
                4. External libraries or dependencies (as text_entity)
                5. Design patterns implemented (as knowledge_concept)
                
                Return JSON with entities: name, entity_type, description, confidence
                """
                
                response = await self.ai_service.complete(
                    prompt=analysis_prompt,
                    temperature=0.3,
                    max_tokens=800
                )
                
                try:
                    ai_entities = json.loads(response)
                    if isinstance(ai_entities, list):
                        for entity in ai_entities:
                            if all(key in entity for key in ['name', 'entity_type']):
                                entities.append({
                                    "name": entity["name"],
                                    "entity_type": entity["entity_type"],
                                    "description": entity.get("description", ""),
                                    "confidence": entity.get("confidence", 0.7),
                                    "metadata": {"source": "ai_code_analysis"}
                                })
                except json.JSONDecodeError:
                    logger.warning("Failed to parse code entity extraction response")
            
        except Exception as e:
            logger.error(f"Error extracting code entities: {e}")
        
        # Remove duplicates based on name and type
        unique_entities = []
        seen = set()
        for entity in entities:
            key = (entity["name"], entity["entity_type"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    async def _extract_text_entities(self, content_text: str, metadata: Optional[Dict]) -> List[Dict]:
        """Extract entities from general text content."""
        entities = []
        
        try:
            analysis_prompt = f"""
            Analyze this text content and extract key entities:
            
            Content: {content_text[:3000]}
            
            Extract:
            1. Main topics or subjects (as knowledge_concept)
            2. Important people or organizations (as text_entity)
            3. Tools, products, or technologies mentioned (as text_entity)
            4. Key concepts or ideas (as knowledge_concept)
            5. Actionable items or recommendations (as text_entity)
            
            Return JSON with entities: name, entity_type, description, confidence
            """
            
            response = await self.ai_service.complete(
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=800
            )
            
            try:
                ai_entities = json.loads(response)
                if isinstance(ai_entities, list):
                    for entity in ai_entities:
                        if all(key in entity for key in ['name', 'entity_type']):
                            entities.append({
                                "name": entity["name"],
                                "entity_type": entity["entity_type"],
                                "description": entity.get("description", ""),
                                "confidence": entity.get("confidence", 0.7),
                                "metadata": {"source": "text_analysis"}
                            })
            except json.JSONDecodeError:
                logger.warning("Failed to parse text entity extraction response")
            
        except Exception as e:
            logger.error(f"Error extracting text entities: {e}")
        
        return entities
    
    async def _extract_knowledge_concepts(self, content_text: str) -> List[Dict]:
        """Extract general knowledge concepts from any content."""
        concepts = []
        
        try:
            # Simple keyword-based concept extraction
            concept_patterns = {
                'programming': r'\b(?:programming|coding|development|software|algorithm)\b',
                'data_science': r'\b(?:data science|machine learning|ai|analytics|statistics)\b',
                'web_development': r'\b(?:web development|frontend|backend|javascript|react|vue|angular)\b',
                'design': r'\b(?:design|ui|ux|interface|user experience|visual)\b',
                'business': r'\b(?:business|marketing|strategy|management|sales|revenue)\b'
            }
            
            for concept, pattern in concept_patterns.items():
                if re.search(pattern, content_text, re.IGNORECASE):
                    concepts.append({
                        "name": concept.replace('_', ' ').title(),
                        "entity_type": "knowledge_concept",
                        "description": f"Knowledge concept: {concept.replace('_', ' ')}",
                        "confidence": 0.6,
                        "metadata": {"source": "pattern_matching", "pattern": concept}
                    })
        
        except Exception as e:
            logger.error(f"Error extracting knowledge concepts: {e}")
        
        return concepts
    
    async def _create_unified_entity(self, content_id: UUID, entity_data: Dict) -> Optional[UUID]:
        """Create a unified entity in the database."""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                entity_id = await conn.fetchval("""
                    INSERT INTO unified_entities (
                        entity_type, source_content_id, name, description, metadata,
                        start_position, end_position, confidence_score, extraction_method
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """,
                    entity_data["entity_type"],
                    content_id,
                    entity_data["name"],
                    entity_data.get("description", ""),
                    json.dumps(entity_data.get("metadata", {})),
                    entity_data.get("start_position"),
                    entity_data.get("end_position"),
                    entity_data.get("confidence", 1.0),
                    "ai_extracted"
                )
                
                return entity_id
                
        except Exception as e:
            logger.error(f"Error creating unified entity: {e}")
            return None
    
    async def _extract_entity_relationships(
        self, 
        entities: List[Dict], 
        content_text: str, 
        content_type: str
    ) -> List[Dict]:
        """Extract relationships between entities using AI."""
        relationships = []
        
        if len(entities) < 2:
            return relationships
        
        try:
            # Build entity context for AI
            entity_names = [e["name"] for e in entities]
            
            analysis_prompt = f"""
            Analyze relationships between these entities found in {content_type} content:
            
            Entities: {', '.join(entity_names)}
            
            Content context: {content_text[:2000]}
            
            Identify semantic relationships between entities. Use these relationship types:
            - implements: one entity implements another
            - explains: one entity explains another
            - references: one entity references another
            - related_to: entities are related
            - builds_on: one entity builds on another
            - contains: one entity contains another
            - demonstrates: one entity demonstrates another
            
            Return JSON array with relationships: source_entity, target_entity, relationship_type, confidence (0-1), context
            """
            
            response = await self.ai_service.complete(
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=600
            )
            
            try:
                ai_relationships = json.loads(response)
                if isinstance(ai_relationships, list):
                    # Map entity names to IDs
                    entity_name_to_id = {e["name"]: e["entity_id"] for e in entities}
                    
                    for rel in ai_relationships:
                        if all(key in rel for key in ['source_entity', 'target_entity', 'relationship_type']):
                            source_id = entity_name_to_id.get(rel["source_entity"])
                            target_id = entity_name_to_id.get(rel["target_entity"])
                            
                            if source_id and target_id and source_id != target_id:
                                # Create relationship in database
                                relationship_id = await self._create_relationship(
                                    UUID(source_id),
                                    UUID(target_id),
                                    rel["relationship_type"],
                                    rel.get("confidence", 0.7),
                                    rel.get("context", "")
                                )
                                
                                if relationship_id:
                                    relationships.append({
                                        "relationship_id": str(relationship_id),
                                        "source_entity": rel["source_entity"],
                                        "target_entity": rel["target_entity"],
                                        "relationship_type": rel["relationship_type"],
                                        "confidence": rel.get("confidence", 0.7)
                                    })
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse relationship extraction response")
            
        except Exception as e:
            logger.error(f"Error extracting entity relationships: {e}")
        
        return relationships
    
    async def _create_relationship(
        self,
        source_entity_id: UUID,
        target_entity_id: UUID,
        relationship_type: str,
        confidence: float,
        context: str
    ) -> Optional[UUID]:
        """Create a relationship in the database."""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                relationship_id = await conn.fetchval("""
                    INSERT INTO unified_relationships (
                        source_entity_id, target_entity_id, relationship_type,
                        confidence_score, context, extraction_method
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                """,
                    source_entity_id,
                    target_entity_id,
                    relationship_type,
                    confidence,
                    context,
                    "ai_inferred"
                )
                
                return relationship_id
                
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return None
    
    async def _link_entities_to_content(self, content_id: UUID, entities: List[Dict]) -> None:
        """Link extracted entities to the source content."""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                for entity in entities:
                    await conn.execute("""
                        INSERT INTO content_entity_links (
                            content_id, entity_id, link_type, confidence_score
                        )
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (content_id, entity_id, link_type) DO NOTHING
                    """,
                        content_id,
                        UUID(entity["entity_id"]),
                        "created_from",
                        entity.get("confidence", 1.0)
                    )
                    
        except Exception as e:
            logger.error(f"Error linking entities to content: {e}")
    
    async def get_entity_statistics(self) -> Dict:
        """Get statistics about extracted entities."""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Refresh materialized views
                await conn.execute("SELECT refresh_knowledge_graph_stats()")
                
                # Get entity statistics
                entity_stats = await conn.fetch("SELECT * FROM entity_statistics")
                relationship_stats = await conn.fetch("SELECT * FROM relationship_statistics")
                
                return {
                    "entity_statistics": [dict(row) for row in entity_stats],
                    "relationship_statistics": [dict(row) for row in relationship_stats],
                    "total_entities": sum(row["total_entities"] for row in entity_stats),
                    "total_relationships": sum(row["total_relationships"] for row in relationship_stats)
                }
                
        except Exception as e:
            logger.error(f"Error getting entity statistics: {e}")
            return {"error": str(e)}


# Create singleton instance
entity_extraction_service = EntityExtractionService()