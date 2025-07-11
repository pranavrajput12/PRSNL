"""
Duplicate Detection Service using embeddings and content analysis
"""
import logging
from typing import List, Dict, Optional, Tuple, Any
import hashlib
from urllib.parse import urlparse, unquote
import asyncio

from app.db.database import get_db_pool
from app.services.unified_ai_service import unified_ai_service
from app.config import settings
from app.utils.fingerprint import calculate_content_fingerprint
import json
import numpy as np

logger = logging.getLogger(__name__)


class DuplicateDetectionService:
    """Service for detecting and managing duplicate content"""
    
    def __init__(self):
        self.similarity_threshold = 0.85  # Threshold for considering items as duplicates
        self.url_similarity_threshold = 0.9  # Higher threshold for URL-based duplicates
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        if not url:
            return ""
        
        # Parse URL
        parsed = urlparse(url.lower().strip())
        
        # Remove common tracking parameters
        if parsed.query:
            params = []
            for param in parsed.query.split('&'):
                key = param.split('=')[0]
                if key not in ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'source']:
                    params.append(param)
            query = '&'.join(params)
        else:
            query = ''
        
        # Rebuild normalized URL
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if query:
            normalized += f"?{query}"
        
        # Remove trailing slashes
        return normalized.rstrip('/')
    
    def content_hash(self, content: str) -> str:
        """Generate hash of content for exact duplicate detection"""
        # Use the unified fingerprint calculation
        return calculate_content_fingerprint(content)
    
    async def check_duplicate(self, url: Optional[str], title: str, content: Optional[str]) -> Dict[str, Any]:
        """
        Check if an item is a duplicate of existing content
        Returns duplicate information if found
        """
        pool = await get_db_pool()
        duplicates = []
        
        async with pool.acquire() as conn:
            # 1. Check for exact URL match
            if url:
                normalized_url = self.normalize_url(url)
                url_matches = await conn.fetch("""
                    SELECT id, title, url, created_at
                    FROM items
                    WHERE LOWER(url) = $1 OR url = $2
                    ORDER BY created_at DESC
                    LIMIT 5
                """, normalized_url, url)
                
                for match in url_matches:
                    duplicates.append({
                        "id": str(match['id']),
                        "title": match['title'],
                        "url": match['url'],
                        "type": "exact_url",
                        "confidence": 1.0,
                        "created_at": match['created_at'].isoformat()
                    })
            
            # 2. Check for content hash match (exact content duplicate)
            if content and len(content) > 100:
                content_fingerprint = self.content_hash(content)
                
                # First try the dedicated content_fingerprint column
                hash_matches = await conn.fetch("""
                    SELECT id, title, url, created_at
                    FROM items
                    WHERE content_fingerprint = $1
                    ORDER BY created_at DESC
                    LIMIT 5
                """, content_fingerprint)
                
                # Fallback to metadata for backward compatibility
                if not hash_matches:
                    hash_matches = await conn.fetch("""
                        SELECT id, title, url, created_at
                        FROM items
                        WHERE metadata->>'content_hash' = $1
                        ORDER BY created_at DESC
                        LIMIT 5
                    """, content_fingerprint)
                
                for match in hash_matches:
                    if not any(d['id'] == str(match['id']) for d in duplicates):
                        duplicates.append({
                            "id": str(match['id']),
                            "title": match['title'],
                            "url": match['url'],
                            "type": "exact_content",
                            "confidence": 1.0,
                            "created_at": match['created_at'].isoformat()
                        })
            
            # 3. Check for semantic duplicates using embeddings
            if duplicates:  # If we already found exact duplicates, skip semantic search
                return {
                    "is_duplicate": True,
                    "duplicates": duplicates,
                    "recommendation": "exact_duplicate_found"
                }
            
            # Generate embedding for new content using unified AI service
            check_text = f"{title} {content[:1000] if content else ''}"
            embeddings = await unified_ai_service.generate_embeddings([check_text])
            embedding = embeddings[0] if embeddings else None
            
            if embedding:
                # Find similar items using pgvector
                similar_items = await conn.fetch("""
                    SELECT 
                        id, 
                        title, 
                        url, 
                        summary,
                        created_at,
                        embedding,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM items
                    WHERE embedding IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT 20
                """, embedding)
                
                # Get all embeddings and IDs for comparison
                embeddings_to_compare = [
                    (str(item['id']), item['embedding'])
                    for item in similar_items
                    if item['similarity'] > 0.5  # Pre-filter
                ]
                
                # Use unified AI service for semantic duplicate detection
                duplicates_found = await unified_ai_service.find_duplicates_semantic(
                    content=check_text,
                    embeddings_to_compare=embeddings_to_compare,
                    threshold=self.similarity_threshold
                )
                
                # Map duplicate results back to item data
                item_map = {str(item['id']): item for item in similar_items}
                
                for dup in duplicates_found:
                    item = item_map.get(dup['item_id'])
                    if item:
                        # Additional checks for high confidence
                        is_same_domain = False
                        if url and item['url']:
                            try:
                                new_domain = urlparse(url).netloc
                                existing_domain = urlparse(item['url']).netloc
                                is_same_domain = new_domain == existing_domain
                            except:
                                pass
                        
                        # Adjust confidence based on additional factors
                        confidence = dup['similarity']
                        if is_same_domain:
                            confidence = min(confidence * 1.1, 1.0)
                        
                        duplicates.append({
                            "id": dup['item_id'],
                            "title": item['title'],
                            "url": item['url'],
                            "type": "semantic",
                            "confidence": confidence,
                            "similarity": dup['similarity'],
                            "created_at": item['created_at'].isoformat()
                        })
        
        if duplicates:
            # Sort by confidence
            duplicates.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Determine recommendation
            if duplicates[0]['confidence'] >= 0.95:
                recommendation = "skip_duplicate"
            elif duplicates[0]['confidence'] >= 0.85:
                recommendation = "review_duplicate"
            else:
                recommendation = "possible_duplicate"
            
            return {
                "is_duplicate": True,
                "duplicates": duplicates[:5],  # Return top 5 duplicates
                "recommendation": recommendation
            }
        
        return {
            "is_duplicate": False,
            "duplicates": [],
            "recommendation": "no_duplicate"
        }
    
    async def find_all_duplicates(self, min_similarity: float = 0.85) -> List[Dict[str, Any]]:
        """
        Find all duplicate groups in the database
        Returns groups of duplicate items
        """
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Get all items with embeddings
            items = await conn.fetch("""
                SELECT id, title, url, embedding, created_at
                FROM items
                WHERE embedding IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 1000
            """)
            
            if len(items) < 2:
                return []
            
            # Find duplicate groups
            duplicate_groups = []
            processed_ids = set()
            
            for i, item in enumerate(items):
                if str(item['id']) in processed_ids:
                    continue
                
                group = [{
                    "id": str(item['id']),
                    "title": item['title'],
                    "url": item['url'],
                    "created_at": item['created_at'].isoformat()
                }]
                
                # Find all items similar to this one
                for j, other_item in enumerate(items[i+1:], i+1):
                    if str(other_item['id']) in processed_ids:
                        continue
                    
                    # Calculate similarity using numpy (faster than DB query)
                    similarity = np.dot(item['embedding'], other_item['embedding']) / (
                        np.linalg.norm(item['embedding']) * np.linalg.norm(other_item['embedding'])
                    )
                    
                    if similarity >= min_similarity:
                        group.append({
                            "id": str(other_item['id']),
                            "title": other_item['title'],
                            "url": other_item['url'],
                            "created_at": other_item['created_at'].isoformat(),
                            "similarity": similarity
                        })
                        processed_ids.add(str(other_item['id']))
                
                if len(group) > 1:
                    processed_ids.add(str(item['id']))
                    duplicate_groups.append({
                        "group_id": f"group_{len(duplicate_groups) + 1}",
                        "items": group,
                        "count": len(group)
                    })
            
            return duplicate_groups
    
    async def merge_duplicates(self, keep_id: str, duplicate_ids: List[str]) -> Dict[str, Any]:
        """
        Merge duplicate items into one, preserving the most information
        """
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                try:
                    # Get all items
                    all_ids = [keep_id] + duplicate_ids
                    items = await conn.fetch("""
                        SELECT * FROM items
                        WHERE id = ANY($1::uuid[])
                    """, all_ids)
                    
                    if len(items) != len(all_ids):
                        return {"success": False, "message": "Some items not found"}
                    
                    # Find the item to keep
                    keep_item = next(item for item in items if str(item['id']) == keep_id)
                    duplicate_items = [item for item in items if str(item['id']) != keep_id]
                    
                    # Merge tags
                    all_tags = set(keep_item['tags'] or [])
                    for item in duplicate_items:
                        all_tags.update(item['tags'] or [])
                    
                    # Merge metadata
                    merged_metadata = keep_item['metadata'] or {}
                    merged_metadata['merged_from'] = [
                        {
                            "id": str(item['id']),
                            "title": item['title'],
                            "url": item['url'],
                            "merged_at": "now"
                        }
                        for item in duplicate_items
                    ]
                    
                    # Update the kept item with merged data
                    await conn.execute("""
                        UPDATE items
                        SET 
                            tags = $2,
                            metadata = $3,
                            updated_at = NOW()
                        WHERE id = $1
                    """, keep_id, list(all_tags), merged_metadata)
                    
                    # Delete duplicates
                    await conn.execute("""
                        DELETE FROM items
                        WHERE id = ANY($1::uuid[])
                    """, duplicate_ids)
                    
                    return {
                        "success": True,
                        "message": f"Successfully merged {len(duplicate_ids)} duplicates into item {keep_id}",
                        "merged_tags": list(all_tags),
                        "deleted_ids": duplicate_ids
                    }
                    
                except Exception as e:
                    logger.error(f"Error merging duplicates: {e}")
                    raise


# Create singleton instance
duplicate_detection = DuplicateDetectionService()