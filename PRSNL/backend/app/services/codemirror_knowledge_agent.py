"""
CodeMirror Knowledge Integration Agent

This agent searches the PRSNL knowledge base to find relevant content
(videos, photos, documents, notes) related to analyzed repositories.
Uses semantic search and content analysis to provide contextual knowledge.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from app.db.database import get_db_connection
from app.services.unified_ai_service import UnifiedAIService

logger = logging.getLogger(__name__)

class CodeMirrorKnowledgeAgent:
    """
    Agent for finding relevant knowledge base content for CodeMirror analysis results.
    
    Searches across:
    - Videos (technical content, tutorials, project demos)
    - Photos (architecture diagrams, whiteboard sessions, screenshots)
    - Documents (project docs, technical specs, research papers)
    - Notes (meeting notes, ideas, development logs)
    """
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
        
    async def find_relevant_content(
        self,
        repository_name: str,
        analysis_results: Dict[str, Any],
        repo_languages: List[str] = None,
        repo_frameworks: List[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Find relevant knowledge base content for a repository analysis.
        
        Args:
            repository_name: Name of the analyzed repository
            analysis_results: Results from CodeMirror analysis
            repo_languages: Programming languages detected
            repo_frameworks: Frameworks detected
            limit: Maximum number of results per content type
            
        Returns:
            Dictionary with categorized relevant content
        """
        try:
            # Extract key terms for searching
            search_terms = await self._extract_search_terms(
                repository_name, analysis_results, repo_languages, repo_frameworks
            )
            
            # Search different content types
            results = {
                'videos': await self._search_videos(search_terms, limit),
                'photos': await self._search_photos(search_terms, limit),
                'documents': await self._search_documents(search_terms, limit),
                'notes': await self._search_notes(search_terms, limit),
                'search_terms_used': search_terms,
                'total_results': 0
            }
            
            # Calculate total results
            results['total_results'] = sum(
                len(results[content_type]) 
                for content_type in ['videos', 'photos', 'documents', 'notes']
            )
            
            # If no direct matches, try broader search
            if results['total_results'] == 0:
                logger.info(f"No direct matches for {repository_name}, trying broader search")
                results = await self._fallback_search(repo_languages, repo_frameworks, limit)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding relevant content for {repository_name}: {e}", exc_info=True)
            return {
                'videos': [],
                'photos': [],
                'documents': [],
                'notes': [],
                'search_terms_used': [],
                'total_results': 0,
                'error': str(e)
            }
    
    async def _extract_search_terms(
        self,
        repository_name: str,
        analysis_results: Dict[str, Any],
        repo_languages: List[str],
        repo_frameworks: List[str]
    ) -> List[str]:
        """Extract relevant search terms from repository analysis."""
        
        search_terms = []
        
        # Add repository name and variations
        search_terms.append(repository_name.lower())
        
        # Extract from repository name (split on common separators)
        name_parts = repository_name.lower().replace('-', ' ').replace('_', ' ').split()
        search_terms.extend(name_parts)
        
        # Add languages and frameworks
        if repo_languages:
            search_terms.extend([lang.lower() for lang in repo_languages])
        if repo_frameworks:
            search_terms.extend([fw.lower() for fw in repo_frameworks])
        
        # Extract key concepts from analysis results
        if analysis_results:
            # Look for domain-specific terms
            insights = analysis_results.get('insights', [])
            for insight in insights:
                if isinstance(insight, dict):
                    title = insight.get('title', '').lower()
                    search_terms.extend(self._extract_technical_terms(title))
            
            # Look for patterns
            patterns = analysis_results.get('patterns', [])
            for pattern in patterns:
                if isinstance(pattern, dict):
                    pattern_type = pattern.get('pattern_type', '').lower()
                    if pattern_type:
                        search_terms.append(pattern_type)
        
        # Use AI to enhance search terms
        try:
            enhanced_terms = await self._ai_enhance_search_terms(
                repository_name, search_terms, analysis_results
            )
            search_terms.extend(enhanced_terms)
        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")
        
        # Remove duplicates and empty terms
        search_terms = list(set([term for term in search_terms if term and len(term) > 2]))
        
        return search_terms[:20]  # Limit to top 20 terms
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms from text using simple heuristics."""
        
        # Common technical keywords to look for
        technical_keywords = [
            'api', 'rest', 'graphql', 'database', 'sql', 'nosql', 'mongodb', 'postgresql',
            'docker', 'kubernetes', 'microservice', 'frontend', 'backend', 'fullstack',
            'authentication', 'authorization', 'security', 'testing', 'deployment',
            'ci/cd', 'devops', 'cloud', 'aws', 'azure', 'gcp', 'serverless',
            'react', 'vue', 'angular', 'svelte', 'fastapi', 'django', 'flask',
            'node', 'express', 'spring', 'laravel', 'ruby', 'rails'
        ]
        
        words = text.lower().split()
        found_terms = []
        
        for word in words:
            # Remove punctuation
            clean_word = ''.join(char for char in word if char.isalnum())
            if clean_word in technical_keywords:
                found_terms.append(clean_word)
        
        return found_terms
    
    async def _ai_enhance_search_terms(
        self,
        repository_name: str,
        current_terms: List[str],
        analysis_results: Dict[str, Any]
    ) -> List[str]:
        """Use AI to suggest additional relevant search terms."""
        
        try:
            prompt = f"""
Based on this repository analysis, suggest 5-10 additional relevant search terms for finding related content in a knowledge base:

Repository: {repository_name}
Current terms: {', '.join(current_terms)}
Analysis summary: {json.dumps(analysis_results, indent=2)[:1000]}...

Focus on:
1. Technical concepts and methodologies
2. Related technologies and tools
3. Industry terms and domains
4. Alternative names or acronyms

Return only a comma-separated list of terms, no explanations.
"""
            
            response = await self.ai_service.complete(
                prompt=prompt,
                system_prompt="You are a technical knowledge expert. Suggest relevant search terms for finding related content.",
                max_tokens=100
            )
            
            if response:
                suggested_terms = response.strip()
                # Parse comma-separated terms
                new_terms = [term.strip().lower() for term in suggested_terms.split(',')]
                return [term for term in new_terms if term and len(term) > 2]
            
        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")
        
        return []
    
    async def _search_videos(self, search_terms: List[str], limit: int) -> List[Dict[str, Any]]:
        """Search for relevant videos in the knowledge base."""
        
        try:
            async with get_db_connection() as db:
                # Search in video_details table with semantic search
                query = """
                    SELECT DISTINCT
                        vd.id,
                        vd.title,
                        vd.description,
                        vd.duration,
                        vd.thumbnail_url,
                        vd.video_url,
                        vd.tags,
                        vd.transcript_summary,
                        vd.created_at,
                        'video' as content_type,
                        -- Calculate relevance score
                        GREATEST(
                            -- Title match
                            CASE WHEN LOWER(vd.title) ~ ANY($1) THEN 10 ELSE 0 END,
                            -- Description match
                            CASE WHEN LOWER(vd.description) ~ ANY($1) THEN 8 ELSE 0 END,
                            -- Tags match
                            CASE WHEN LOWER(vd.tags::text) ~ ANY($1) THEN 6 ELSE 0 END,
                            -- Transcript summary match
                            CASE WHEN LOWER(vd.transcript_summary) ~ ANY($1) THEN 4 ELSE 0 END
                        ) as relevance_score
                    FROM video_details vd
                    WHERE (
                        LOWER(vd.title) ~ ANY($1) OR
                        LOWER(vd.description) ~ ANY($1) OR
                        LOWER(vd.tags::text) ~ ANY($1) OR
                        LOWER(vd.transcript_summary) ~ ANY($1)
                    )
                    ORDER BY relevance_score DESC, vd.created_at DESC
                    LIMIT $2
                """
                
                # Convert search terms to regex patterns
                regex_patterns = [f'\\m{term}\\M' for term in search_terms]
                
                results = await db.fetch(query, regex_patterns, limit)
                
                return [
                    {
                        'id': str(row['id']),
                        'title': row['title'],
                        'description': row['description'],
                        'duration': row['duration'],
                        'thumbnail_url': row['thumbnail_url'],
                        'video_url': row['video_url'],
                        'tags': row['tags'],
                        'transcript_summary': row['transcript_summary'],
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'content_type': row['content_type'],
                        'relevance_score': row['relevance_score']
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error searching videos: {e}", exc_info=True)
            return []
    
    async def _search_photos(self, search_terms: List[str], limit: int) -> List[Dict[str, Any]]:
        """Search for relevant photos/images in the knowledge base."""
        
        try:
            async with get_db_connection() as db:
                # Search in photos table
                query = """
                    SELECT DISTINCT
                        p.id,
                        p.filename,
                        p.description,
                        p.image_url,
                        p.thumbnail_url,
                        p.tags,
                        p.metadata,
                        p.analysis_results,
                        p.uploaded_at,
                        'photo' as content_type,
                        -- Calculate relevance score
                        GREATEST(
                            -- Filename match
                            CASE WHEN LOWER(p.filename) ~ ANY($1) THEN 10 ELSE 0 END,
                            -- Description match
                            CASE WHEN LOWER(p.description) ~ ANY($1) THEN 8 ELSE 0 END,
                            -- Tags match
                            CASE WHEN LOWER(p.tags::text) ~ ANY($1) THEN 6 ELSE 0 END,
                            -- Analysis results match
                            CASE WHEN LOWER(p.analysis_results::text) ~ ANY($1) THEN 4 ELSE 0 END
                        ) as relevance_score
                    FROM photos p
                    WHERE (
                        LOWER(p.filename) ~ ANY($1) OR
                        LOWER(p.description) ~ ANY($1) OR
                        LOWER(p.tags::text) ~ ANY($1) OR
                        LOWER(p.analysis_results::text) ~ ANY($1)
                    )
                    ORDER BY relevance_score DESC, p.uploaded_at DESC
                    LIMIT $2
                """
                
                # Convert search terms to regex patterns
                regex_patterns = [f'\\m{term}\\M' for term in search_terms]
                
                results = await db.fetch(query, regex_patterns, limit)
                
                return [
                    {
                        'id': str(row['id']),
                        'filename': row['filename'],
                        'description': row['description'],
                        'image_url': row['image_url'],
                        'thumbnail_url': row['thumbnail_url'],
                        'tags': row['tags'],
                        'metadata': row['metadata'],
                        'analysis_results': row['analysis_results'],
                        'uploaded_at': row['uploaded_at'].isoformat() if row['uploaded_at'] else None,
                        'content_type': row['content_type'],
                        'relevance_score': row['relevance_score']
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error searching photos: {e}", exc_info=True)
            return []
    
    async def _search_documents(self, search_terms: List[str], limit: int) -> List[Dict[str, Any]]:
        """Search for relevant documents in the knowledge base."""
        
        try:
            async with get_db_connection() as db:
                # Search in documents table
                query = """
                    SELECT DISTINCT
                        d.id,
                        d.filename,
                        d.title,
                        d.content_preview,
                        d.document_type,
                        d.file_path,
                        d.metadata,
                        d.uploaded_at,
                        'document' as content_type,
                        -- Calculate relevance score
                        GREATEST(
                            -- Title match
                            CASE WHEN LOWER(d.title) ~ ANY($1) THEN 10 ELSE 0 END,
                            -- Filename match
                            CASE WHEN LOWER(d.filename) ~ ANY($1) THEN 8 ELSE 0 END,
                            -- Content preview match
                            CASE WHEN LOWER(d.content_preview) ~ ANY($1) THEN 6 ELSE 0 END,
                            -- Document type match
                            CASE WHEN LOWER(d.document_type) ~ ANY($1) THEN 4 ELSE 0 END
                        ) as relevance_score
                    FROM documents d
                    WHERE (
                        LOWER(d.title) ~ ANY($1) OR
                        LOWER(d.filename) ~ ANY($1) OR
                        LOWER(d.content_preview) ~ ANY($1) OR
                        LOWER(d.document_type) ~ ANY($1)
                    )
                    ORDER BY relevance_score DESC, d.uploaded_at DESC
                    LIMIT $2
                """
                
                # Convert search terms to regex patterns
                regex_patterns = [f'\\m{term}\\M' for term in search_terms]
                
                results = await db.fetch(query, regex_patterns, limit)
                
                return [
                    {
                        'id': str(row['id']),
                        'filename': row['filename'],
                        'title': row['title'],
                        'content_preview': row['content_preview'],
                        'document_type': row['document_type'],
                        'file_path': row['file_path'],
                        'metadata': row['metadata'],
                        'uploaded_at': row['uploaded_at'].isoformat() if row['uploaded_at'] else None,
                        'content_type': row['content_type'],
                        'relevance_score': row['relevance_score']
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}", exc_info=True)
            return []
    
    async def _search_notes(self, search_terms: List[str], limit: int) -> List[Dict[str, Any]]:
        """Search for relevant notes in the knowledge base."""
        
        try:
            async with get_db_connection() as db:
                # Search in notes table
                query = """
                    SELECT DISTINCT
                        n.id,
                        n.title,
                        n.content,
                        n.category,
                        n.tags,
                        n.created_at,
                        n.updated_at,
                        'note' as content_type,
                        -- Calculate relevance score
                        GREATEST(
                            -- Title match
                            CASE WHEN LOWER(n.title) ~ ANY($1) THEN 10 ELSE 0 END,
                            -- Content match (first 500 chars)
                            CASE WHEN LOWER(LEFT(n.content, 500)) ~ ANY($1) THEN 8 ELSE 0 END,
                            -- Category match
                            CASE WHEN LOWER(n.category) ~ ANY($1) THEN 6 ELSE 0 END,
                            -- Tags match
                            CASE WHEN LOWER(n.tags::text) ~ ANY($1) THEN 4 ELSE 0 END
                        ) as relevance_score
                    FROM notes n
                    WHERE (
                        LOWER(n.title) ~ ANY($1) OR
                        LOWER(n.content) ~ ANY($1) OR
                        LOWER(n.category) ~ ANY($1) OR
                        LOWER(n.tags::text) ~ ANY($1)
                    )
                    ORDER BY relevance_score DESC, n.updated_at DESC
                    LIMIT $2
                """
                
                # Convert search terms to regex patterns
                regex_patterns = [f'\\m{term}\\M' for term in search_terms]
                
                results = await db.fetch(query, regex_patterns, limit)
                
                return [
                    {
                        'id': str(row['id']),
                        'title': row['title'],
                        'content': row['content'][:500] + '...' if len(row['content']) > 500 else row['content'],
                        'category': row['category'],
                        'tags': row['tags'],
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                        'content_type': row['content_type'],
                        'relevance_score': row['relevance_score']
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error searching notes: {e}", exc_info=True)
            return []
    
    async def _fallback_search(
        self,
        repo_languages: List[str],
        repo_frameworks: List[str],
        limit: int
    ) -> Dict[str, Any]:
        """Perform broader search when no specific matches found."""
        
        try:
            # Create broader search terms
            broad_terms = []
            
            if repo_languages:
                broad_terms.extend([lang.lower() for lang in repo_languages])
            if repo_frameworks:
                broad_terms.extend([fw.lower() for fw in repo_frameworks])
            
            # Add general programming terms
            broad_terms.extend([
                'programming', 'development', 'code', 'software', 'application',
                'project', 'tutorial', 'guide', 'documentation'
            ])
            
            if not broad_terms:
                return {
                    'videos': [],
                    'photos': [],
                    'documents': [],
                    'notes': [],
                    'search_terms_used': [],
                    'total_results': 0,
                    'fallback_used': True
                }
            
            # Search with broader terms
            results = {
                'videos': await self._search_videos(broad_terms, limit // 2),
                'photos': await self._search_photos(broad_terms, limit // 2),
                'documents': await self._search_documents(broad_terms, limit // 2),
                'notes': await self._search_notes(broad_terms, limit // 2),
                'search_terms_used': broad_terms,
                'fallback_used': True
            }
            
            results['total_results'] = sum(
                len(results[content_type]) 
                for content_type in ['videos', 'photos', 'documents', 'notes']
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in fallback search: {e}", exc_info=True)
            return {
                'videos': [],
                'photos': [],
                'documents': [],
                'notes': [],
                'search_terms_used': [],
                'total_results': 0,
                'fallback_used': True,
                'error': str(e)
            }
    
    async def store_knowledge_mapping(
        self,
        analysis_id: str,
        knowledge_results: Dict[str, Any]
    ) -> bool:
        """Store the knowledge mapping for future reference and caching."""
        
        try:
            async with get_db_connection() as db:
                # Store in codemirror_knowledge_mappings table (if exists)
                # This would be for caching and analytics
                await db.execute("""
                    INSERT INTO codemirror_knowledge_mappings 
                    (analysis_id, knowledge_results, search_terms, total_results, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (analysis_id) 
                    DO UPDATE SET 
                        knowledge_results = $2,
                        search_terms = $3,
                        total_results = $4,
                        updated_at = $5
                """, 
                    uuid.UUID(analysis_id),
                    json.dumps(knowledge_results),
                    json.dumps(knowledge_results.get('search_terms_used', [])),
                    knowledge_results.get('total_results', 0),
                    datetime.utcnow()
                )
                
                return True
                
        except Exception as e:
            # Table might not exist yet - that's okay
            logger.warning(f"Could not store knowledge mapping: {e}")
            return False