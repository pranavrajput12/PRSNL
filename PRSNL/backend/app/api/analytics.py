import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from openai import AzureOpenAI

from app.config import settings
from app.core.exceptions import InternalServerError
from app.db.database import get_db_connection
from app.services.ai_router import ai_router, AIProvider, AITask, TaskType

router = APIRouter()

from app.services.cache import cache_result, cache_service, CacheKeys


@router.get("/analytics/trends")
@cache_result(prefix=CacheKeys.STATS, expire=timedelta(hours=1))
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
        
        trends = []
        for r in records:
            trends.append({
                "date": str(r["date"]),
                "count": r["count"]
            })

        return {"trends": trends}
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve content trends: {e}")

@router.get("/analytics/topics")
@cache_result(prefix=CacheKeys.STATS, expire=timedelta(hours=1))
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
            SELECT tags.name, COUNT(item_tags.item_id) as count
            FROM tags
            JOIN item_tags ON tags.id = item_tags.tag_id
            GROUP BY tags.name
            ORDER BY count DESC
            LIMIT $1;
        """
        records = await db_connection.fetch(query, limit)
        
        total_items = await db_connection.fetchval("SELECT COUNT(*) FROM items")
        
        topics = [{"tag": r["name"], "count": r["count"], "percentage": (r["count"]/total_items)*100 if total_items > 0 else 0} for r in records]
        return {"topics": topics}
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve topic clustering: {e}")

@router.get("/analytics/usage_patterns")
@cache_result(prefix=CacheKeys.STATS, expire=timedelta(hours=1))
async def get_usage_patterns(
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Retrieves general usage patterns (e.g., total items, average items per day).
    """
    try:
        total_items_query = "SELECT COUNT(*) FROM items;"
        # Use metadata to determine content types if available
        content_type_query = """
            SELECT 
                CASE 
                    WHEN url LIKE '%youtube.com%' OR url LIKE '%youtu.be%' THEN 'video'
                    WHEN url LIKE '%.pdf' THEN 'pdf'
                    WHEN metadata->>'type' IS NOT NULL THEN metadata->>'type'
                    ELSE 'article'
                END as content_type,
                COUNT(*) as count 
            FROM items 
            GROUP BY content_type;
        """
        
        # Get items per day for the last 7 days
        daily_items_query = """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM items
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date;
        """

        total_items = await db_connection.fetchval(total_items_query)
        content_type_dist = await db_connection.fetch(content_type_query)
        daily_items = await db_connection.fetch(daily_items_query)
        
        # Calculate average items per day
        avg_per_day = sum(r['count'] for r in daily_items) / 7.0 if daily_items else 0

        return {
            "total_items": total_items,
            "content_type_distribution": {r['content_type']: r['count'] for r in content_type_dist},
            "average_items_per_day": round(avg_per_day, 2),
            "recent_daily_counts": [{"date": str(r['date']), "count": r['count']} for r in daily_items]
        }
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve usage patterns: {e}")

async def _execute_ai_insight_task(provider: AIProvider, task: AITask) -> str:
    if provider == AIProvider.AZURE_OPENAI:
        try:
            client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                timeout=45.0,
            )
            response = client.chat.completions.create(
                model=settings.AZURE_OPENAI_MODEL,
                messages=[{"role": "system", "content": "You are a data analyst AI."}, {"role": "user", "content": task.content}],
                max_tokens=800,
                temperature=0.5,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            raise
    elif provider == AIProvider.FALLBACK:
        return json.dumps({"insights": ["AI provider unavailable. Please try again later."]})

    raise InternalServerError(f"Provider {provider.value} not supported.")


@router.get("/analytics/ai_insights")
@cache_result(prefix=CacheKeys.STATS, expire=timedelta(hours=6))
async def get_ai_generated_insights(
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Retrieves AI-generated insights based on recent content.
    """
    try:
        recent_items_query = """
        SELECT title, processed_content FROM items
        WHERE processed_content IS NOT NULL AND created_at >= NOW() - INTERVAL '7 days'
        ORDER BY created_at DESC
        LIMIT 10;
        """
        recent_items = await db_connection.fetch(recent_items_query)

        if not recent_items:
            return {"insights": [{"id": "1", "insight": "Not enough recent data to generate insights."}]}

        # Prepare prompt for AI
        content_for_analysis = "\n".join([f"- {item['title']}: {item['content'][:200]}..." for item in recent_items])
        prompt = f"""
        Analyze the following recently captured knowledge items and generate 3-5 key insights.
        Focus on identifying emerging themes, recurring topics, or potential connections between items.
        Format the output as a JSON object with a single key 'insights' which is a list of strings.

        Recent Items:
        {content_for_analysis}
        """

        ai_task = AITask(
            type=TaskType.TEXT_GENERATION,
            content=prompt,
            priority=7
        )

        response_str = await ai_router.execute_with_fallback(ai_task, _execute_ai_insight_task)
        response_data = json.loads(response_str)

        return {"insights": [{"id": str(i+1), "insight": insight} for i, insight in enumerate(response_data.get("insights", []))]}

    except Exception as e:
        raise InternalServerError(f"Failed to generate AI insights: {e}")
