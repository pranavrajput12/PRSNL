import asyncpg
from typing import List, Dict, Any
from datetime import datetime, timedelta

async def get_knowledge_graph_tags(db_connection: asyncpg.Connection) -> List[Dict[str, Any]]:
    """
    Retrieves all tags and their counts for knowledge graph nodes.
    """
    query = """
        SELECT tag, COUNT(*) as count
        FROM item_tags
        GROUP BY tag;
    """
    return await db_connection.fetch(query)

async def get_knowledge_graph_item_tags(db_connection: asyncpg.Connection) -> List[Dict[str, Any]]:
    """
    Retrieves item IDs and their associated tags for knowledge graph edges.
    """
    query = """
        SELECT item_id, array_agg(tag) as tags
        FROM item_tags
        GROUP BY item_id;
    """
    return await db_connection.fetch(query)

async def get_daily_additions(db_connection: asyncpg.Connection) -> List[Dict[str, Any]]:
    """
    Retrieves daily content additions for the last 30 days.
    """
    query = """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM items
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY date;
    """
    return await db_connection.fetch(query)

async def get_peak_activity_hours(db_connection: asyncpg.Connection) -> List[Dict[str, Any]]:
    """
    Retrieves peak activity hours based on content creation in the last 7 days.
    """
    query = """
        SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as count
        FROM items
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY EXTRACT(HOUR FROM created_at)
        ORDER BY count DESC;
    """
    return await db_connection.fetch(query)

async def get_total_items_last_30_days(db_connection: asyncpg.Connection) -> int:
    """
    Retrieves the total number of items created in the last 30 days.
    """
    query = "SELECT COUNT(*) FROM items WHERE created_at >= NOW() - INTERVAL '30 days';"
    return await db_connection.fetchval(query)

async def get_total_items_prev_30_days(db_connection: asyncpg.Connection) -> int:
    """
    Retrieves the total number of items created in the previous 30 days.
    """
    query = "SELECT COUNT(*) FROM items WHERE created_at >= NOW() - INTERVAL '60 days' AND created_at < NOW() - INTERVAL '30 days';"
    return await db_connection.fetchval(query)

async def get_semantic_cluster_tags(db_connection: asyncpg.Connection) -> List[Dict[str, Any]]:
    """
    Retrieves tags and their associated item counts for semantic clustering simulation.
    """
    query = """
        SELECT t.tag, COUNT(it.item_id) as item_count, array_agg(it.item_id) as item_ids
        FROM tags t
        JOIN item_tags it ON t.tag = it.tag
        GROUP BY t.tag
        ORDER BY item_count DESC
        LIMIT 10;
    """
    return await db_connection.fetch(query)
