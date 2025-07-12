"""
Smart Categorization Service using Azure OpenAI
Automatically categorizes and organizes content based on AI analysis
"""
import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import asyncio

from app.services.unified_ai_service import unified_ai_service
from app.db.database import get_db_pool
from app.config import settings
import json
import numpy as np

logger = logging.getLogger(__name__)


class SmartCategorizationService:
    """Service for intelligent content categorization and organization"""
    
    def __init__(self):
        self.ai_service = unified_ai_service
        
        # Predefined category templates
        self.category_templates = {
            "development": {
                "keywords": ["code", "programming", "development", "api", "framework", "library"],
                "subcategories": ["frontend", "backend", "devops", "database", "mobile", "testing"]
            },
            "ai_ml": {
                "keywords": ["ai", "machine learning", "neural", "model", "data science", "llm"],
                "subcategories": ["nlp", "computer vision", "deep learning", "data analysis", "automation"]
            },
            "design": {
                "keywords": ["design", "ui", "ux", "interface", "visual", "graphics"],
                "subcategories": ["ui design", "ux research", "branding", "web design", "mobile design"]
            },
            "business": {
                "keywords": ["business", "strategy", "marketing", "sales", "finance", "management"],
                "subcategories": ["startup", "marketing", "finance", "operations", "leadership"]
            },
            "learning": {
                "keywords": ["tutorial", "guide", "course", "documentation", "how-to", "learn"],
                "subcategories": ["tutorials", "courses", "documentation", "reference", "guides"]
            },
            "personal": {
                "keywords": ["note", "idea", "thought", "personal", "journal", "reflection"],
                "subcategories": ["notes", "ideas", "journal", "goals", "reflections"]
            }
        }
    
    async def categorize_item(self, title: str, content: str, tags: List[str] = None) -> Dict[str, any]:
        """
        Categorize a single item using AI analysis
        Returns category, subcategory, and confidence score
        """
        try:
            # Prepare content for categorization
            full_content = f"Title: {title}\n"
            if tags:
                full_content += f"Tags: {', '.join(tags)}\n"
            full_content += f"Content: {content[:1000]}"
            
            # Use unified AI service for categorization
            result = await self.ai_service.categorize_content(
                content=full_content,
                existing_categories=list(self.category_templates.keys()),
                confidence_threshold=0.7
            )
            
            # Format response to match expected structure
            formatted_result = {
                "category": result["primary_category"]["name"],
                "subcategory": result.get("secondary_categories", [{}])[0].get("name", "general") if result.get("secondary_categories") else "general",
                "confidence": result["primary_category"]["confidence"],
                "suggested_tags": [],  # Will be populated from content analysis
                "content_type": "article",  # Default, will be enhanced
                "reasoning": result.get("reasoning", "")
            }
            
            # Get additional analysis for tags and content type
            analysis = await self.ai_service.analyze_content(content=full_content, url=None)
            
            # Merge analysis results
            formatted_result["suggested_tags"] = analysis.get("tags", [])[:5]
            formatted_result["content_type"] = analysis.get("category", "article")
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error in AI categorization: {e}")
            return self._fallback_categorization(title, content, tags)
    
    def _fallback_categorization(self, title: str, content: str, tags: List[str] = None) -> Dict[str, any]:
        """Fallback categorization based on keywords"""
        text = f"{title} {content} {' '.join(tags or [])}".lower()
        
        scores = {}
        for category, info in self.category_templates.items():
            score = sum(1 for keyword in info["keywords"] if keyword in text)
            scores[category] = score
        
        best_category = max(scores, key=scores.get) if any(scores.values()) else "other"
        
        return {
            "category": best_category,
            "subcategory": "general",
            "confidence": min(scores.get(best_category, 0) / 3, 1.0),
            "suggested_tags": [],
            "content_type": "article",
            "reasoning": "Categorized based on keyword matching"
        }
    
    async def bulk_categorize(self, limit: int = 100) -> Dict[str, any]:
        """
        Categorize uncategorized items in bulk
        Returns statistics about the categorization process
        """
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Get uncategorized items
            uncategorized_items = await conn.fetch("""
                SELECT id, title, summary, processed_content, tags
                FROM items
                WHERE category IS NULL OR category = 'general'
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)
            
            if not uncategorized_items:
                return {"processed": 0, "message": "No uncategorized items found"}
            
            # Process items in batches
            batch_size = 10
            processed = 0
            categorization_stats = defaultdict(int)
            
            for i in range(0, len(uncategorized_items), batch_size):
                batch = uncategorized_items[i:i + batch_size]
                
                # Process batch concurrently
                tasks = []
                for item in batch:
                    content = item['processed_content'] or item['summary'] or ""
                    task = self.categorize_item(
                        item['title'],
                        content,
                        item['tags']
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update items with categories
                for item, result in zip(batch, results):
                    if isinstance(result, Exception):
                        logger.error(f"Failed to categorize item {item['id']}: {result}")
                        continue
                    
                    try:
                        await conn.execute("""
                            UPDATE items 
                            SET 
                                category = $2,
                                metadata = jsonb_set(
                                    COALESCE(metadata, '{}'::jsonb),
                                    '{ai_categorization}',
                                    $3::jsonb
                                ),
                                updated_at = NOW()
                            WHERE id = $1
                        """, item['id'], result['category'], json.dumps(result))
                        
                        categorization_stats[result['category']] += 1
                        processed += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to update item {item['id']}: {e}")
            
            return {
                "processed": processed,
                "total": len(uncategorized_items),
                "stats": dict(categorization_stats),
                "message": f"Successfully categorized {processed} items"
            }
    
    async def reorganize_by_clusters(self) -> Dict[str, any]:
        """
        Reorganize content based on semantic clustering
        Groups similar items together regardless of their current categories
        """
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Get all items with embeddings
            items = await conn.fetch("""
                SELECT id, title, embedding, category
                FROM items
                WHERE embedding IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 500
            """)
            
            if len(items) < 10:
                return {"message": "Not enough items with embeddings for clustering"}
            
            # Perform clustering using embeddings
            clusters = await self._cluster_items(items)
            
            # Analyze each cluster to determine its theme
            cluster_themes = {}
            for cluster_id, cluster_items in clusters.items():
                # Get representative items from cluster
                sample_items = cluster_items[:5]
                titles = [item['title'] for item in sample_items]
                
                # Use AI to determine cluster theme
                prompt = f"""Analyze these related items and suggest a category name and description:

Items:
{chr(10).join(f'- {title}' for title in titles)}

Provide a concise category name and brief description in JSON format:
{{
    "name": "category_name",
    "description": "brief description of what connects these items"
}}"""
                
                try:
                    response = await self.ai_service.complete(
                        prompt=prompt,
                        system_prompt="You are an expert at identifying themes and patterns in content.",
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    theme = json.loads(response)
                    cluster_themes[cluster_id] = theme
                except Exception as e:
                    logger.error(f"Failed to determine theme for cluster {cluster_id}: {e}")
                    cluster_themes[cluster_id] = {
                        "name": f"Cluster {cluster_id}",
                        "description": "Related items"
                    }
            
            return {
                "clusters": len(clusters),
                "themes": cluster_themes,
                "message": f"Organized items into {len(clusters)} semantic clusters"
            }
    
    async def _cluster_items(self, items: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Cluster items based on embedding similarity
        Simple k-means style clustering
        """
        try:
            from sklearn.cluster import KMeans
        except ImportError:
            logger.warning("sklearn not available, using simple clustering")
            return self._simple_clustering(items)
        
        # Extract embeddings
        embeddings = np.array([item['embedding'] for item in items])
        
        # Determine optimal number of clusters (simple heuristic)
        n_clusters = min(max(len(items) // 20, 3), 10)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Group items by cluster
        clusters = defaultdict(list)
        for item, label in zip(items, cluster_labels):
            clusters[int(label)].append(item)
        
        return dict(clusters)
    
    def _simple_clustering(self, items: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Simple clustering fallback when sklearn is not available
        Groups items by cosine similarity
        """
        clusters = defaultdict(list)
        assigned = set()
        cluster_id = 0
        
        for i, item in enumerate(items):
            if i in assigned:
                continue
                
            # Start new cluster
            clusters[cluster_id].append(item)
            assigned.add(i)
            
            # Find similar items
            for j, other_item in enumerate(items[i+1:], i+1):
                if j in assigned:
                    continue
                    
                # Calculate cosine similarity
                similarity = np.dot(item['embedding'], other_item['embedding']) / (
                    np.linalg.norm(item['embedding']) * np.linalg.norm(other_item['embedding'])
                )
                
                if similarity > 0.8:  # High similarity threshold
                    clusters[cluster_id].append(other_item)
                    assigned.add(j)
            
            cluster_id += 1
            
            # Limit clusters
            if cluster_id >= 10:
                break
        
        return dict(clusters)
    
    async def suggest_item_connections(self, item_id: str, limit: int = 5) -> List[Dict]:
        """
        Suggest connections between items based on content analysis
        Returns items that could be linked or referenced
        """
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Get the source item
            source_item = await conn.fetchrow("""
                SELECT id, title, summary, processed_content, embedding
                FROM items
                WHERE id = $1
            """, item_id)
            
            if not source_item:
                return []
            
            # Find semantically similar items
            similar_items = await conn.fetch("""
                SELECT 
                    id, 
                    title, 
                    summary,
                    1 - (embedding <=> $1::vector) as similarity
                FROM items
                WHERE id != $2 
                    AND embedding IS NOT NULL
                ORDER BY similarity DESC
                LIMIT $3
            """, source_item['embedding'], item_id, limit * 2)
            
            # Analyze connections with AI
            connections = []
            for item in similar_items[:limit]:
                prompt = f"""Analyze the relationship between these two items:

Item 1: {source_item['title']}
Summary: {source_item['summary'] or 'No summary'}

Item 2: {item['title']}
Summary: {item['summary'] or 'No summary'}

Determine:
1. Connection type (prerequisite, related, extends, contradicts, complements)
2. Strength (strong, medium, weak)
3. Reason for connection (one sentence)

Respond in JSON format:
{{
    "connection_type": "type",
    "strength": "medium",
    "reason": "explanation"
}}"""
                
                try:
                    response = await self.ai_service.complete(
                        prompt=prompt,
                        system_prompt="You are an expert at analyzing relationships between content.",
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    connection_info = json.loads(response)
                    
                    connections.append({
                        "id": str(item['id']),
                        "title": item['title'],
                        "similarity": float(item['similarity']),
                        **connection_info
                    })
                except Exception as e:
                    logger.error(f"Failed to analyze connection: {e}")
                    connections.append({
                        "id": str(item['id']),
                        "title": item['title'],
                        "similarity": float(item['similarity']),
                        "connection_type": "related",
                        "strength": "medium",
                        "reason": "Similar content"
                    })
            
            return connections


# Create singleton instance
smart_categorization = SmartCategorizationService()