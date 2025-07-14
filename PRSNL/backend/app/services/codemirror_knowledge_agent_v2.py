"""
CodeMirror Knowledge Integration Agent V2

Enhanced version using embeddings for semantic search and multi-agent collaboration
for finding hyper-relevant content from the PRSNL knowledge base.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
import asyncio

from app.db.database import get_db_connection
from app.services.unified_ai_service import UnifiedAIService
from app.services.embedding_manager import embedding_manager

logger = logging.getLogger(__name__)

class ContentRelevanceAgent:
    """Agent for scoring content relevance using embeddings and AI understanding"""
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
        
    async def score_relevance(
        self, 
        content: Dict[str, Any], 
        repository_context: Dict[str, Any],
        similarity_score: float
    ) -> float:
        """Score content relevance on a 0-1 scale using multiple factors"""
        
        # Base score from embedding similarity
        base_score = similarity_score
        
        # Enhance with contextual understanding
        try:
            prompt = f"""
Given this repository context and content item, rate the relevance (0-1):

Repository: {repository_context.get('name')}
Languages: {repository_context.get('languages', [])}
Frameworks: {repository_context.get('frameworks', [])}
Key Patterns: {repository_context.get('patterns', [])}

Content Type: {content.get('type')}
Content Title: {content.get('title', 'Untitled')}
Content Description: {content.get('description', '')[:200]}...

Consider:
1. Technical relevance to the repository's stack
2. Practical applicability of the content
3. Problem-solution alignment
4. Learning value for the repository's domain

Return only a number between 0 and 1.
"""
            response = await self.ai_service.complete(
                prompt=prompt,
                system_prompt="You are a technical relevance expert. Rate content relevance precisely.",
                max_tokens=10,
                temperature=0.3
            )
            
            if response:
                try:
                    ai_score = float(response.strip())
                    # Combine embedding similarity and AI understanding
                    return (base_score * 0.6 + ai_score * 0.4)
                except:
                    return base_score
                    
        except Exception as e:
            logger.warning(f"Relevance scoring failed: {e}")
            
        return base_score


class OpenSourceIntegrationAgent:
    """Agent for finding relevant open source integrations"""
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
        
    async def find_relevant_integrations(
        self,
        repository_context: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find open source integrations relevant to the repository"""
        
        try:
            async with get_db_connection() as db:
                # Build search criteria
                languages = repository_context.get('languages', [])
                frameworks = repository_context.get('frameworks', [])
                patterns = repository_context.get('patterns', [])
                
                # Search by technology stack overlap
                query = """
                    SELECT DISTINCT
                        osi.id,
                        osi.name,
                        osi.description,
                        osi.repository_url,
                        osi.category,
                        osi.tags,
                        osi.tech_stack,
                        osi.use_cases,
                        osi.integration_points,
                        osi.popularity_score,
                        -- Calculate relevance based on tech stack overlap
                        (
                            CASE WHEN osi.tech_stack ?| $1 THEN 0.5 ELSE 0 END +
                            CASE WHEN osi.tags ?| $2 THEN 0.3 ELSE 0 END +
                            CASE WHEN osi.category = ANY($3) THEN 0.2 ELSE 0 END
                        ) as relevance_score
                    FROM open_source_integrations osi
                    WHERE 
                        osi.tech_stack ?| $1 OR  -- Has any of the languages
                        osi.tags ?| $2 OR         -- Has any of the frameworks as tags
                        osi.category = ANY($3)    -- Matches pattern categories
                    ORDER BY relevance_score DESC, popularity_score DESC
                    LIMIT $4
                """
                
                # Convert to arrays for PostgreSQL
                lang_array = languages if languages else ['']
                framework_array = frameworks if frameworks else ['']
                pattern_categories = self._patterns_to_categories(patterns)
                
                results = await db.fetch(
                    query, 
                    lang_array, 
                    framework_array, 
                    pattern_categories,
                    limit
                )
                
                integrations = []
                for row in results:
                    integration = dict(row)
                    # Enhance with use case matching
                    integration['matched_use_cases'] = await self._match_use_cases(
                        integration.get('use_cases', []),
                        repository_context
                    )
                    integrations.append(integration)
                
                return integrations
                
        except Exception as e:
            logger.error(f"Error finding open source integrations: {e}", exc_info=True)
            return []
    
    def _patterns_to_categories(self, patterns: List[str]) -> List[str]:
        """Convert pattern types to integration categories"""
        category_map = {
            'authentication': ['auth', 'security'],
            'api': ['api', 'rest', 'graphql'],
            'database': ['database', 'orm', 'data'],
            'testing': ['testing', 'quality'],
            'deployment': ['deployment', 'ci/cd', 'devops'],
            'monitoring': ['monitoring', 'observability'],
            'ui': ['frontend', 'ui', 'components']
        }
        
        categories = []
        for pattern in patterns:
            pattern_lower = pattern.lower()
            for key, values in category_map.items():
                if key in pattern_lower:
                    categories.extend(values)
        
        return list(set(categories)) if categories else ['general']
    
    async def _match_use_cases(
        self, 
        use_cases: List[str], 
        repository_context: Dict[str, Any]
    ) -> List[str]:
        """Find which use cases match the repository context"""
        if not use_cases:
            return []
            
        try:
            prompt = f"""
Given this repository context, which use cases are most relevant?

Repository: {repository_context.get('name')}
Description: {repository_context.get('description', 'No description')}
Key Patterns: {repository_context.get('patterns', [])}

Available Use Cases:
{json.dumps(use_cases, indent=2)}

Return only the relevant use case indices as a comma-separated list (e.g., "0,2,3").
Return empty string if none are relevant.
"""
            response = await self.ai_service.complete(
                prompt=prompt,
                system_prompt="You are a technical matching expert.",
                max_tokens=50,
                temperature=0.3
            )
            
            if response:
                indices = [int(i.strip()) for i in response.split(',') if i.strip().isdigit()]
                return [use_cases[i] for i in indices if i < len(use_cases)]
                
        except Exception as e:
            logger.warning(f"Use case matching failed: {e}")
            
        return []


class ChatGPTConversationAgent:
    """Agent for finding relevant ChatGPT conversations"""
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
        
    async def find_relevant_conversations(
        self,
        repository_context: Dict[str, Any],
        search_embedding: List[float],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find ChatGPT conversations related to the repository topics"""
        
        try:
            async with get_db_connection() as db:
                # Search in chatgpt_conversations table using embeddings
                query = """
                    SELECT 
                        cc.id,
                        cc.title,
                        cc.summary,
                        cc.key_topics,
                        cc.code_snippets,
                        cc.conversation_date,
                        cc.url,
                        -- Calculate cosine similarity if embeddings exist
                        CASE 
                            WHEN e.vector IS NOT NULL THEN
                                1 - (e.vector <=> $1::vector)
                            ELSE 0
                        END as similarity_score
                    FROM chatgpt_conversations cc
                    LEFT JOIN embeddings e ON cc.id = e.item_id
                    WHERE 
                        -- Text search fallback
                        (
                            cc.title ILIKE ANY($2) OR
                            cc.summary ILIKE ANY($2) OR
                            cc.key_topics::text ILIKE ANY($2)
                        )
                        OR
                        -- Embedding similarity (if available)
                        (e.vector IS NOT NULL AND 1 - (e.vector <=> $1::vector) > 0.7)
                    ORDER BY similarity_score DESC, cc.conversation_date DESC
                    LIMIT $3
                """
                
                # Create search patterns
                search_patterns = self._create_search_patterns(repository_context)
                
                # Convert embedding to PostgreSQL vector format
                embedding_str = f"[{','.join(map(str, search_embedding))}]" if search_embedding else None
                
                results = await db.fetch(
                    query,
                    embedding_str,
                    search_patterns,
                    limit
                )
                
                conversations = []
                for row in results:
                    conv = dict(row)
                    # Extract relevant code snippets
                    conv['relevant_snippets'] = await self._extract_relevant_snippets(
                        conv.get('code_snippets', []),
                        repository_context
                    )
                    conversations.append(conv)
                
                return conversations
                
        except Exception as e:
            logger.error(f"Error finding ChatGPT conversations: {e}", exc_info=True)
            return []
    
    def _create_search_patterns(self, repository_context: Dict[str, Any]) -> List[str]:
        """Create search patterns from repository context"""
        patterns = []
        
        # Add language patterns
        for lang in repository_context.get('languages', []):
            patterns.append(f"%{lang}%")
        
        # Add framework patterns
        for fw in repository_context.get('frameworks', []):
            patterns.append(f"%{fw}%")
        
        # Add key terms from repository name
        repo_name = repository_context.get('name', '')
        if repo_name:
            # Split on common separators and add each part
            parts = repo_name.replace('-', ' ').replace('_', ' ').split()
            for part in parts:
                if len(part) > 2:
                    patterns.append(f"%{part}%")
        
        return patterns if patterns else ['%']
    
    async def _extract_relevant_snippets(
        self,
        code_snippets: List[Dict[str, Any]],
        repository_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract only the most relevant code snippets"""
        if not code_snippets:
            return []
        
        relevant_snippets = []
        languages = set(lang.lower() for lang in repository_context.get('languages', []))
        
        for snippet in code_snippets:
            # Check if snippet language matches
            snippet_lang = snippet.get('language', '').lower()
            if snippet_lang in languages or not languages:
                relevant_snippets.append(snippet)
        
        return relevant_snippets[:3]  # Return top 3 most relevant


class CodeMirrorKnowledgeAgentV2:
    """
    Enhanced multi-agent system for finding hyper-relevant knowledge base content.
    Uses embeddings, semantic search, and specialized agents for different content types.
    """
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
        self.relevance_agent = ContentRelevanceAgent()
        self.opensource_agent = OpenSourceIntegrationAgent()
        self.conversation_agent = ChatGPTConversationAgent()
        
    async def find_relevant_content(
        self,
        repository_name: str,
        analysis_results: Dict[str, Any],
        repo_languages: List[str] = None,
        repo_frameworks: List[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Find hyper-relevant knowledge base content using multi-agent collaboration.
        
        Returns content sorted by relevance with detailed matching information.
        """
        try:
            # Build comprehensive repository context
            repository_context = {
                'name': repository_name,
                'languages': repo_languages or [],
                'frameworks': repo_frameworks or [],
                'patterns': self._extract_patterns(analysis_results),
                'description': analysis_results.get('summary', ''),
                'insights': analysis_results.get('insights', [])
            }
            
            # Generate search embedding from repository context
            search_text = self._build_search_text(repository_context)
            search_embedding = await self._generate_embedding(search_text)
            
            # Run all agents in parallel for efficiency
            results = await asyncio.gather(
                self._search_with_embeddings('videos', search_embedding, repository_context, limit),
                self._search_with_embeddings('photos', search_embedding, repository_context, limit),
                self._search_with_embeddings('documents', search_embedding, repository_context, limit),
                self._search_with_embeddings('notes', search_embedding, repository_context, limit),
                self.opensource_agent.find_relevant_integrations(repository_context, limit),
                self.conversation_agent.find_relevant_conversations(repository_context, search_embedding, limit),
                return_exceptions=True
            )
            
            # Process results
            content_results = {
                'videos': results[0] if not isinstance(results[0], Exception) else [],
                'photos': results[1] if not isinstance(results[1], Exception) else [],
                'documents': results[2] if not isinstance(results[2], Exception) else [],
                'notes': results[3] if not isinstance(results[3], Exception) else [],
                'open_source_integrations': results[4] if not isinstance(results[4], Exception) else [],
                'chatgpt_conversations': results[5] if not isinstance(results[5], Exception) else [],
                'search_context': repository_context,
                'total_results': 0
            }
            
            # Calculate total results
            content_results['total_results'] = sum(
                len(content_results[key]) 
                for key in ['videos', 'photos', 'documents', 'notes', 'open_source_integrations', 'chatgpt_conversations']
            )
            
            # Log any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Agent {i} failed: {result}")
            
            return content_results
            
        except Exception as e:
            logger.error(f"Error in multi-agent knowledge search: {e}", exc_info=True)
            return {
                'videos': [],
                'photos': [],
                'documents': [],
                'notes': [],
                'open_source_integrations': [],
                'chatgpt_conversations': [],
                'search_context': {},
                'total_results': 0,
                'error': str(e)
            }
    
    def _extract_patterns(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Extract pattern types from analysis results"""
        patterns = []
        
        # From insights
        for insight in analysis_results.get('insights', []):
            if isinstance(insight, dict):
                insight_type = insight.get('insight_type', '')
                if insight_type:
                    patterns.append(insight_type)
        
        # From detected patterns
        for pattern in analysis_results.get('patterns', []):
            if isinstance(pattern, dict):
                pattern_type = pattern.get('pattern_type', '')
                if pattern_type:
                    patterns.append(pattern_type)
        
        return list(set(patterns))
    
    def _build_search_text(self, repository_context: Dict[str, Any]) -> str:
        """Build comprehensive search text for embedding generation"""
        parts = [
            repository_context['name'],
            repository_context.get('description', ''),
            ' '.join(repository_context.get('languages', [])),
            ' '.join(repository_context.get('frameworks', [])),
            ' '.join(repository_context.get('patterns', []))
        ]
        
        # Add key insights
        for insight in repository_context.get('insights', [])[:3]:
            if isinstance(insight, dict):
                parts.append(insight.get('title', ''))
        
        return ' '.join(filter(None, parts))
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for search text"""
        try:
            embeddings = await self.ai_service.generate_embeddings([text])
            return embeddings[0] if embeddings else []
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    async def _search_with_embeddings(
        self,
        content_type: str,
        search_embedding: List[float],
        repository_context: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search for content using embeddings and score relevance"""
        
        try:
            async with get_db_connection() as db:
                # Map content type to table
                table_map = {
                    'videos': 'video_details',
                    'photos': 'photos',
                    'documents': 'documents',
                    'notes': 'notes'
                }
                
                table = table_map.get(content_type)
                if not table:
                    return []
                
                # Build query based on content type
                query = f"""
                    WITH ranked_content AS (
                        SELECT 
                            c.*,
                            CASE 
                                WHEN e.vector IS NOT NULL THEN
                                    1 - (e.vector <=> $1::vector)
                                ELSE 0
                            END as similarity_score
                        FROM {table} c
                        LEFT JOIN embeddings e ON c.id = e.item_id
                        WHERE e.vector IS NOT NULL
                        ORDER BY similarity_score DESC
                        LIMIT $2
                    )
                    SELECT * FROM ranked_content WHERE similarity_score > 0.5
                """
                
                # Convert embedding to PostgreSQL vector format
                embedding_str = f"[{','.join(map(str, search_embedding))}]" if search_embedding else None
                
                results = await db.fetch(query, embedding_str, limit * 2)  # Get more for relevance filtering
                
                # Score each result for relevance
                scored_results = []
                for row in results:
                    content = dict(row)
                    content['content_type'] = content_type
                    
                    # Get relevance score from agent
                    relevance_score = await self.relevance_agent.score_relevance(
                        content,
                        repository_context,
                        content.get('similarity_score', 0)
                    )
                    
                    content['relevance_score'] = relevance_score
                    
                    # Only include highly relevant content
                    if relevance_score > 0.6:
                        scored_results.append(content)
                
                # Sort by relevance and return top results
                scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
                return scored_results[:limit]
                
        except Exception as e:
            logger.error(f"Error searching {content_type} with embeddings: {e}", exc_info=True)
            return []