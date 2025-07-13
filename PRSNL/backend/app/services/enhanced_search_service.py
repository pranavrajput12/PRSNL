"""
Enhanced Search Service using new embedding architecture
Provides unified search across content with fingerprint-based deduplication
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.db.database import get_db_pool
from app.services.duplicate_detection import duplicate_detection
from app.services.embedding_manager import embedding_manager
from app.services.unified_ai_service import unified_ai_service
from app.utils.fingerprint import calculate_content_fingerprint

logger = logging.getLogger(__name__)


class EnhancedSearchService:
    """Enhanced search service with embedding and fingerprint integration"""
    
    def __init__(self):
        self.default_limit = 20
        self.similarity_threshold = 0.3
    
    async def semantic_search(
        self,
        query: str,
        limit: int = None,
        threshold: float = None,
        filter_by: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic search using the new embedding architecture.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            filter_by: Additional filters (type, tags, date_range, etc.)
            
        Returns:
            Dict with search results and metadata
        """
        limit = limit or self.default_limit
        threshold = threshold or self.similarity_threshold
        
        try:
            # Generate query embedding
            query_embeddings = await unified_ai_service.generate_embeddings([query])
            if not query_embeddings:
                return {"results": [], "error": "Failed to generate query embedding"}
            
            query_embedding = query_embeddings[0]
            
            # Use embedding manager for search
            similar_items = await embedding_manager.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                threshold=threshold
            )
            
            # Apply additional filters if provided
            if filter_by:
                similar_items = await self._apply_filters(similar_items, filter_by)
            
            # Enhance results with additional metadata
            enhanced_results = []
            for item in similar_items:
                enhanced_item = await self._enhance_result(item)
                enhanced_results.append(enhanced_item)
            
            return {
                "results": enhanced_results,
                "total": len(enhanced_results),
                "query": query,
                "search_type": "semantic",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {"results": [], "error": str(e)}
    
    async def hybrid_search(
        self,
        query: str,
        limit: int = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            semantic_weight: Weight for semantic similarity
            keyword_weight: Weight for keyword matching
            
        Returns:
            Dict with search results and metadata
        """
        limit = limit or self.default_limit
        
        try:
            # Get semantic results
            semantic_results = await self.semantic_search(query, limit=limit * 2)
            
            # Get keyword results
            keyword_results = await self.keyword_search(query, limit=limit * 2)
            
            # Combine and rerank results
            combined_results = self._combine_search_results(
                semantic_results.get("results", []),
                keyword_results.get("results", []),
                semantic_weight,
                keyword_weight
            )
            
            return {
                "results": combined_results[:limit],
                "total": len(combined_results),
                "query": query,
                "search_type": "hybrid",
                "weights": {"semantic": semantic_weight, "keyword": keyword_weight},
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return {"results": [], "error": str(e)}
    
    async def keyword_search(
        self,
        query: str,
        limit: int = None,
        filter_by: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform keyword-based search using PostgreSQL full-text search.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            filter_by: Additional filters
            
        Returns:
            Dict with search results and metadata
        """
        limit = limit or self.default_limit
        
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Build search query with filters
                where_clauses = ["search_vector @@ plainto_tsquery('english', $1)"]
                params = [query]
                param_count = 1
                
                if filter_by:
                    where_clauses, params, param_count = self._build_filter_clauses(
                        filter_by, where_clauses, params, param_count
                    )
                
                where_clause = " AND ".join(where_clauses)
                
                results = await conn.fetch(f"""
                    SELECT 
                        id,
                        title,
                        url,
                        summary,
                        type,
                        created_at,
                        content_fingerprint,
                        ts_rank_cd(search_vector, plainto_tsquery('english', $1)) as rank
                    FROM items
                    WHERE {where_clause}
                    ORDER BY rank DESC, created_at DESC
                    LIMIT ${param_count + 1}
                """, *params, limit)
                
                # Convert to standard format
                formatted_results = []
                for row in results:
                    formatted_results.append({
                        "id": str(row['id']),
                        "title": row['title'],
                        "url": row['url'],
                        "summary": row['summary'],
                        "type": row['type'],
                        "created_at": row['created_at'].isoformat(),
                        "content_fingerprint": row['content_fingerprint'],
                        "similarity": float(row['rank']),  # Use rank as similarity
                        "search_type": "keyword"
                    })
                
                return {
                    "results": formatted_results,
                    "total": len(formatted_results),
                    "query": query,
                    "search_type": "keyword",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return {"results": [], "error": str(e)}
    
    async def find_duplicates_by_fingerprint(
        self,
        content: str,
        exclude_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find exact duplicates using content fingerprint.
        
        Args:
            content: Content to check for duplicates
            exclude_id: Item ID to exclude from results
            
        Returns:
            List of duplicate items
        """
        fingerprint = calculate_content_fingerprint(content)
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            params = [fingerprint]
            where_clause = "content_fingerprint = $1"
            
            if exclude_id:
                where_clause += " AND id != $2"
                params.append(exclude_id)
            
            results = await conn.fetch(f"""
                SELECT id, title, url, summary, created_at, content_fingerprint
                FROM items
                WHERE {where_clause}
                ORDER BY created_at DESC
            """, *params)
            
            return [
                {
                    "id": str(row['id']),
                    "title": row['title'],
                    "url": row['url'],
                    "summary": row['summary'],
                    "created_at": row['created_at'].isoformat(),
                    "content_fingerprint": row['content_fingerprint'],
                    "match_type": "exact_fingerprint"
                }
                for row in results
            ]
    
    async def search_with_deduplication(
        self,
        query: str,
        search_type: str = "hybrid",
        limit: int = None,
        similarity_threshold: float = 0.9
    ) -> Dict[str, Any]:
        """
        Perform search with automatic deduplication based on content fingerprints.
        
        Args:
            query: Search query text
            search_type: Type of search ("semantic", "keyword", "hybrid")
            limit: Maximum number of results
            similarity_threshold: Threshold for considering items as duplicates
            
        Returns:
            Dict with deduplicated search results
        """
        # Perform initial search
        if search_type == "semantic":
            results = await self.semantic_search(query, limit=limit * 2)
        elif search_type == "keyword":
            results = await self.keyword_search(query, limit=limit * 2)
        else:  # hybrid
            results = await self.hybrid_search(query, limit=limit * 2)
        
        # Deduplicate by content fingerprint
        seen_fingerprints = set()
        deduplicated = []
        
        for item in results.get("results", []):
            fingerprint = item.get("content_fingerprint")
            if fingerprint and fingerprint in seen_fingerprints:
                continue
                
            if fingerprint:
                seen_fingerprints.add(fingerprint)
            deduplicated.append(item)
        
        return {
            **results,
            "results": deduplicated[:limit or self.default_limit],
            "deduplication": {
                "original_count": len(results.get("results", [])),
                "deduplicated_count": len(deduplicated),
                "removed_duplicates": len(results.get("results", [])) - len(deduplicated)
            }
        }
    
    async def _apply_filters(
        self,
        results: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply additional filters to search results."""
        filtered = results
        
        # Filter by type
        if "type" in filters:
            filtered = [r for r in filtered if r.get("type") == filters["type"]]
        
        # Filter by date range
        if "date_range" in filters:
            date_range = filters["date_range"]
            start_date = date_range.get("start")
            end_date = date_range.get("end")
            
            if start_date or end_date:
                filtered_by_date = []
                for r in filtered:
                    item_date = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                    
                    if start_date and item_date < datetime.fromisoformat(start_date):
                        continue
                    if end_date and item_date > datetime.fromisoformat(end_date):
                        continue
                        
                    filtered_by_date.append(r)
                filtered = filtered_by_date
        
        return filtered
    
    async def _enhance_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance search result with additional metadata."""
        # Add search metadata
        enhanced = item.copy()
        enhanced["search_metadata"] = {
            "has_embedding": True,  # Since we're using embedding manager
            "search_timestamp": datetime.utcnow().isoformat()
        }
        
        return enhanced
    
    def _combine_search_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[Dict[str, Any]]:
        """Combine and rerank semantic and keyword search results."""
        # Create lookup for semantic scores
        semantic_scores = {r["id"]: r["similarity"] for r in semantic_results}
        keyword_scores = {r["id"]: r["similarity"] for r in keyword_results}
        
        # Get all unique items
        all_item_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())
        
        combined = []
        for item_id in all_item_ids:
            # Get item data (prefer semantic result, fallback to keyword)
            item_data = None
            for r in semantic_results:
                if r["id"] == item_id:
                    item_data = r.copy()
                    break
            
            if not item_data:
                for r in keyword_results:
                    if r["id"] == item_id:
                        item_data = r.copy()
                        break
            
            if item_data:
                # Calculate combined score
                semantic_score = semantic_scores.get(item_id, 0)
                keyword_score = keyword_scores.get(item_id, 0)
                
                combined_score = (
                    semantic_score * semantic_weight +
                    keyword_score * keyword_weight
                )
                
                item_data["similarity"] = combined_score
                item_data["search_type"] = "hybrid"
                item_data["component_scores"] = {
                    "semantic": semantic_score,
                    "keyword": keyword_score
                }
                
                combined.append(item_data)
        
        # Sort by combined score
        combined.sort(key=lambda x: x["similarity"], reverse=True)
        return combined
    
    def _build_filter_clauses(
        self,
        filters: Dict[str, Any],
        where_clauses: List[str],
        params: List[Any],
        param_count: int
    ) -> Tuple[List[str], List[Any], int]:
        """Build SQL filter clauses from filter dictionary."""
        if "type" in filters:
            param_count += 1
            where_clauses.append(f"type = ${param_count}")
            params.append(filters["type"])
        
        if "date_range" in filters:
            date_range = filters["date_range"]
            
            if "start" in date_range:
                param_count += 1
                where_clauses.append(f"created_at >= ${param_count}")
                params.append(date_range["start"])
            
            if "end" in date_range:
                param_count += 1
                where_clauses.append(f"created_at <= ${param_count}")
                params.append(date_range["end"])
        
        return where_clauses, params, param_count


# Create singleton instance
enhanced_search_service = EnhancedSearchService()