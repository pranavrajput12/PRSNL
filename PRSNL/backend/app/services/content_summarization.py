"""
Content Summarization Service for PRSNL

This service provides AI-powered content summarization with multiple modes:
- Single item summarization
- Daily/weekly/monthly digests
- Topic-based summaries
- Custom time range summaries
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db, get_db_pool
from app.db.models import Item
from app.services.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)


class ContentSummarizationService:
    def __init__(self):
        self.ai_service = unified_ai_service
    
    async def summarize_item(
        self, 
        item_id: str, 
        summary_type: str = "brief"
    ) -> Dict[str, Any]:
        """
        Summarize a single item with different levels of detail
        
        Args:
            item_id: The ID of the item to summarize
            summary_type: "brief" (1-2 sentences), "detailed" (paragraph), "key_points" (bullet points)
            db: Database session
        
        Returns:
            Dictionary with summary and metadata
        """
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Get the item from database
                item = await conn.fetchrow("""
                    SELECT id, title, summary, content, processed_content
                    FROM items
                    WHERE id = $1
                """, item_id)
                
                if not item:
                    raise ValueError(f"Item {item_id} not found")
                
                # Prepare content for summarization
                content_to_summarize = item['processed_content'] or item['content'] or item['summary'] or ""
                full_content = f"Title: {item['title']}\n"
                if item['summary']:
                    full_content += f"Current Summary: {item['summary']}\n"
                if content_to_summarize:
                    full_content += f"Content: {content_to_summarize[:3000]}\n"  # Limit content length
            
                # Use unified AI service for summarization
                summary = await self.ai_service.generate_summary(
                    content=full_content,
                    summary_type=summary_type
                )
                
                # Update item with new summary if brief type
                if summary_type == "brief" and summary:
                    await conn.execute("""
                        UPDATE items 
                        SET summary = $1, updated_at = NOW()
                        WHERE id = $2
                    """, summary, item_id)
            
                return {
                    "item_id": item_id,
                    "title": item['title'],
                    "summary_type": summary_type,
                    "summary": summary,
                    "original_length": len(full_content),
                    "summary_length": len(summary) if summary else 0,
                    "timestamp": datetime.utcnow()
                }
            
        except Exception as e:
            logger.error(f"Error summarizing item {item_id}: {e}")
            raise
    
    async def generate_digest(
        self,
        period: str = "daily",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a digest of content for a specific time period
        
        Args:
            period: "daily", "weekly", "monthly"
            user_id: Optional user ID to filter content
            db: Database session
        
        Returns:
            Dictionary with digest content and metadata
        """
        try:
            # Calculate time range
            now = datetime.utcnow()
            if period == "daily":
                start_date = now - timedelta(days=1)
                period_label = "Daily"
            elif period == "weekly":
                start_date = now - timedelta(days=7)
                period_label = "Weekly"
            elif period == "monthly":
                start_date = now - timedelta(days=30)
                period_label = "Monthly"
            else:
                raise ValueError(f"Invalid period: {period}")
            
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Query items from the period
                query = """
                    SELECT id, title, summary, category, created_at
                    FROM items
                    WHERE created_at >= $1
                """
                params = [start_date]
                
                if user_id:
                    query += " AND user_id = $2"
                    params.append(user_id)
                    
                query += " ORDER BY created_at DESC"
                
                items = await conn.fetch(query, *params)
            
            if not items:
                return {
                    "period": period,
                    "period_label": period_label,
                    "item_count": 0,
                    "digest": f"No new items captured in the {period} period.",
                    "start_date": start_date,
                    "end_date": now
                }
            
                # Group items by category/tags
                categories = defaultdict(list)
                for item in items:
                    category = item['category'] or "Uncategorized"
                    categories[category].append(item)
            
            # Prepare content for digest
            digest_content = f"{period_label} Digest - {len(items)} items captured\n\n"
            
            for category, category_items in categories.items():
                digest_content += f"\n{category} ({len(category_items)} items):\n"
                for item in category_items[:5]:  # Limit to top 5 per category
                    digest_content += f"- {item['title']}"
                    if item['summary']:
                        digest_content += f": {item['summary'][:100]}..."
                    digest_content += "\n"
                
                if len(category_items) > 5:
                    digest_content += f"  ...and {len(category_items) - 5} more\n"
            
                # Generate insights using unified AI service
                insights = await self.ai_service.generate_insights(
                    items_data=[dict(item) for item in items],
                    timeframe=period
                )
                
                # Get executive summary
                ai_summary = insights.get('summary', '')
            
            # Generate statistics
            stats = {
                "total_items": len(items),
                "categories": len(categories),
                "top_categories": sorted(
                    [(cat, len(items)) for cat, items in categories.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            }
            
            return {
                "period": period,
                "period_label": period_label,
                "start_date": start_date,
                "end_date": now,
                "item_count": len(items),
                "digest": digest_content,
                "executive_summary": ai_summary,
                "statistics": stats,
                "categories": {k: [dict(item) for item in v] for k, v in categories.items()},
                "timestamp": now
            }
            
        except Exception as e:
            logger.error(f"Error generating {period} digest: {e}")
            raise
    
    async def generate_topic_summary(
        self,
        topic: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Generate a summary of content related to a specific topic
        
        Args:
            topic: The topic to summarize
            limit: Maximum number of items to include
            db: Database session
        
        Returns:
            Dictionary with topic summary and related items
        """
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Search for items related to the topic using full-text search
                items = await conn.fetch("""
                    SELECT i.id, i.title, i.summary, i.created_at,
                           ts_rank(search_vector, plainto_tsquery($1)) as relevance
                    FROM items i
                    WHERE 
                        search_vector @@ plainto_tsquery($1)
                        OR EXISTS (
                            SELECT 1 FROM tags t
                            WHERE i.tags @> ARRAY[t.name]
                            AND t.name ILIKE $2
                        )
                    ORDER BY relevance DESC, created_at DESC
                    LIMIT $3
                """, topic, f"%{topic}%", limit)
            
            if not items:
                return {
                    "topic": topic,
                    "item_count": 0,
                    "summary": f"No items found related to '{topic}'",
                    "items": []
                }
            
                # Prepare content for topic summary
                topic_content = f"Topic: {topic}\nRelated items: {len(items)}\n\n"
                
                item_details = []
                for item in items[:10]:  # Use top 10 for summary
                    topic_content += f"Title: {item['title']}\n"
                    if item['summary']:
                        topic_content += f"Summary: {item['summary']}\n"
                    topic_content += "\n"
                    
                    item_details.append({
                        "id": str(item['id']),
                        "title": item['title'],
                        "summary": item['summary'],
                        "relevance": float(item['relevance']),
                        "created_at": item['created_at']
                    })
                
                # Generate AI summary using unified service
                ai_summary = await self.ai_service.generate_summary(
                    content=topic_content,
                    summary_type="detailed",
                    context={"topic": topic, "item_count": len(items)}
                )
            
            return {
                "topic": topic,
                "item_count": len(items),
                "summary": ai_summary,
                "items": item_details,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error generating topic summary for '{topic}': {e}")
            raise
    
    async def generate_custom_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Generate a custom summary for specific criteria
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            categories: Optional list of categories to filter
            tags: Optional list of tags to filter
            db: Database session
        
        Returns:
            Dictionary with custom summary
        """
        try:
            # Build query with filters
            query = select(Item).where(
                and_(
                    Item.created_at >= start_date,
                    Item.created_at <= end_date
                )
            )
            
            if categories:
                query = query.where(Item.category.in_(categories))
            
            if tags:
                # Join with tags table
                query = query.join(Item.tags).where(
                    Item.tags.any(lambda t: t.name.in_(tags))
                )
            
            result = await db.execute(query.order_by(Item.created_at.desc()))
            items = result.scalars().all()
            
            if not items:
                return {
                    "start_date": start_date,
                    "end_date": end_date,
                    "filters": {
                        "categories": categories,
                        "tags": tags
                    },
                    "item_count": 0,
                    "summary": "No items found matching the criteria"
                }
            
            # Prepare content for summary
            summary_content = f"Custom Summary\n"
            summary_content += f"Period: {start_date.date()} to {end_date.date()}\n"
            summary_content += f"Items: {len(items)}\n\n"
            
            if categories:
                summary_content += f"Categories: {', '.join(categories)}\n"
            if tags:
                summary_content += f"Tags: {', '.join(tags)}\n"
            
            summary_content += "\nItems:\n"
            for item in items[:15]:  # Limit for summary
                summary_content += f"- {item.title}"
                if item.category:
                    summary_content += f" [{item.category}]"
                summary_content += "\n"
            
            # Generate AI summary
            prompt = f"""
            Create a focused summary based on these filtered items:
            
            {summary_content}
            
            Provide:
            1. Overview of content in this period/criteria
            2. Key themes and insights
            3. Recommendations for further exploration
            
            Summary:
            """
            
            ai_summary = await self.llm_processor.process_with_llm(prompt, mode="summarize")
            
            return {
                "start_date": start_date,
                "end_date": end_date,
                "filters": {
                    "categories": categories,
                    "tags": tags
                },
                "item_count": len(items),
                "summary": ai_summary,
                "items": [
                    {
                        "id": str(item.id),
                        "title": item.title,
                        "category": item.category,
                        "created_at": item.created_at
                    }
                    for item in items[:20]
                ],
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error generating custom summary: {e}")
            raise
    
    async def batch_summarize(
        self,
        item_ids: List[str],
        summary_type: str = "brief",
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """
        Summarize multiple items in batch
        
        Args:
            item_ids: List of item IDs to summarize
            summary_type: Type of summary to generate
            db: Database session
        
        Returns:
            List of summary results
        """
        try:
            results = []
            
            # Process in batches to avoid overwhelming the API
            batch_size = 20
            for i in range(0, len(item_ids), batch_size):
                batch = item_ids[i:i + batch_size]
                
                # Process batch concurrently
                tasks = [
                    self.summarize_item(item_id, summary_type, db)
                    for item_id in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for item_id, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Error summarizing item {item_id}: {result}")
                        results.append({
                            "item_id": item_id,
                            "error": str(result)
                        })
                    else:
                        results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch summarization: {e}")
            raise