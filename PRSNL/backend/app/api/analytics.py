from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.db.database import get_db_connection
from app.core.exceptions import InternalServerError
import asyncpg

router = APIRouter()

@router.get("/analytics/trends")
async def get_content_trends(
    timeframe: str = "7d", # e.g., "7d", "30d", "90d", "1y"
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Retrieves content trends over a specified timeframe.
    """
    try:
        end_date = datetime.now()
        if timeframe == "7d":
            start_date = end_date - timedelta(days=7)
        elif timeframe == "30d":
            start_date = end_date - timedelta(days=30)
        elif timeframe == "90d":
            start_date = end_date - timedelta(days=90)
        elif timeframe == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            raise HTTPException(status_code=400, detail="Invalid timeframe specified.")

        # Example query: count items created per day
        query = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM items
            WHERE created_at BETWEEN $1 AND $2
            GROUP BY DATE(created_at)
            ORDER BY date;
        """
        records = await db_connection.fetch(query, start_date, end_date)
        
        trends = [{"date": str(r["date"]), "count": r["count"]} for r in records]
        return {"trends": trends}
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve content trends: {e}")

@router.get("/analytics/topics")
async def get_topic_clustering(
    limit: int = 10,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Retrieves top topics or tags based on frequency.
    """
    try:
        # This is a simplified example. Real topic clustering would involve
        # more complex NLP and potentially pre-calculated clusters.
        # Here, we're just counting tags.
        query = """
            SELECT tag, COUNT(*) as count
            FROM item_tags
            GROUP BY tag
            ORDER BY count DESC
            LIMIT $1;
        """
        records = await db_connection.fetch(query, limit)
        
        topics = [{"topic": r["tag"], "count": r["count"]} for r in records]
        return {"topics": topics}
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve topic clustering: {e}")

@router.get("/analytics/usage_patterns")
async def get_usage_patterns(
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Retrieves general usage patterns (e.g., total items, average items per day).
    """
    try:
        total_items = await db_connection.fetchval("SELECT COUNT(*) FROM items;")
        
        # Calculate average items per day for the last 30 days
        avg_items_per_day_query = """
            SELECT AVG(daily_count)
            FROM (
                SELECT COUNT(*) as daily_count
                FROM items
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
            ) as daily_counts;
        """
        avg_items_per_day = await db_connection.fetchval(avg_items_per_day_query)

        return {
            "total_items": total_items,
            "average_items_per_day_last_30_days": float(avg_items_per_day) if avg_items_per_day else 0.0
        }
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve usage patterns: {e}")

@router.get("/analytics/ai_insights")
async def get_ai_generated_insights(
    limit: int = 5,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Retrieves AI-generated insights (placeholder for future AI analysis results).
    """
    # This endpoint would ideally query a table storing AI-generated summaries,
    # key takeaways, or other insights derived from content.
    # For now, it's a placeholder.
    return {"insights": [
        {"id": 1, "insight": "AI suggests focusing on 'Productivity Hacks' based on recent captures."},
        {"id": 2, "insight": "Trend: Increased interest in 'Personal Knowledge Management' tools."},
    ]}
