import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import asyncpg

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        pass

    async def get_knowledge_graph_data(self, db_connection: asyncpg.Connection) -> Dict[str, Any]:
        """
        Generates data for a knowledge graph, showing relationships between topics/tags.
        This is a simplified example, a real knowledge graph would involve more complex
        relationship extraction (e.g., from content analysis, linked items).
        """
        try:
            # Get all tags and their counts
            tags_query = """
                SELECT name, COUNT(*) as count
                FROM tags
                GROUP BY name;
            """
            tags_records = await db_connection.fetch(tags_query)

            nodes = []
            for r in tags_records:
                nodes.append({
                    "id": r["name"],
                    "label": r["name"],
                    "size": r["count"] # Size based on item count
                })

            # For simplicity, create edges between co-occurring tags in the same item
            # This would be very resource intensive for large datasets,
            # and a pre-calculated graph would be better.
            edges = []
            item_tags_query = """
                SELECT item_id, array_agg(tag) as tags
                FROM item_tags
                GROUP BY item_id;
            """
            item_tags_records = await db_connection.fetch(item_tags_query)

            for record in item_tags_records:
                item_tags = record["tags"]
                for i in range(len(item_tags)):
                    for j in range(i + 1, len(item_tags)):
                        tag1 = item_tags[i]
                        tag2 = item_tags[j]
                        # Add an edge, ensure no duplicates (undirected graph)
                        edge_exists = False
                        for edge in edges:
                            if (edge["source"] == tag1 and edge["target"] == tag2) or \
                               (edge["source"] == tag2 and edge["target"] == tag1):
                                edge["weight"] += 1
                                edge_exists = True
                                break
                        if not edge_exists:
                            edges.append({"source": tag1, "target": tag2, "weight": 1})
            
            return {"nodes": nodes, "edges": edges}
        except Exception as e:
            logger.error(f"Error generating knowledge graph data: {e}")
            raise

    async def get_content_velocity_data(self, db_connection: asyncpg.Connection) -> Dict[str, Any]:
        """
        Tracks content creation/consumption rates.
        """
        try:
            # Daily addition counts for the last 30 days
            daily_additions_query = """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM items
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date;
            """
            daily_additions_records = await db_connection.fetch(daily_additions_query)
            daily_additions = [{"date": str(r["date"]), "count": r["count"]}
                               for r in daily_additions_records]

            # Peak activity hours (e.g., last 7 days)
            peak_hours_query = """
                SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as count
                FROM items
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY count DESC;
            """
            peak_hours_records = await db_connection.fetch(peak_hours_query)
            peak_hours = [{"hour": int(r["hour"]), "count": r["count"]}
                          for r in peak_hours_records]

            # Growth rate (e.g., percentage increase in items over last 30 days vs previous 30 days)
            total_last_30_days = await db_connection.fetchval("SELECT COUNT(*) FROM items WHERE created_at >= NOW() - INTERVAL '30 days';")
            total_prev_30_days = await db_connection.fetchval("SELECT COUNT(*) FROM items WHERE created_at >= NOW() - INTERVAL '60 days' AND created_at < NOW() - INTERVAL '30 days';")
            
            growth_rate = 0.0
            if total_prev_30_days and total_prev_30_days > 0:
                growth_rate = ((total_last_30_days - total_prev_30_days) / total_prev_30_days) * 100

            return {
                "daily_additions": daily_additions,
                "peak_activity_hours": peak_hours,
                "growth_rate_last_30_days_percent": round(growth_rate, 2)
            }
        except Exception as e:
            logger.error(f"Error generating content velocity data: {e}")
            raise

    async def get_semantic_clusters_data(self, db_connection: asyncpg.Connection) -> Dict[str, Any]:
        """
        Groups items by semantic similarity. This would typically involve pre-calculated clusters
        based on embeddings. For this example, we'll simulate by grouping by common tags.
        """
        try:
            # This is a placeholder. Real semantic clustering requires:
            # 1. Item embeddings
            # 2. A clustering algorithm (e.g., K-Means, HDBSCAN) run offline or on demand
            # 3. Storing cluster IDs and representative keywords/summaries in the DB.

            # Simulate semantic clusters by grouping items with the same primary tag
            # and providing some keywords (which are just the tags themselves here).
            query = """
                SELECT t.tag, COUNT(it.item_id) as item_count, array_agg(it.item_id) as item_ids
                FROM tags t
                JOIN item_tags it ON t.tag = it.tag
                GROUP BY t.tag
                ORDER BY item_count DESC
                LIMIT 10;
            """
            records = await db_connection.fetch(query)

            clusters = []
            for r in records:
                clusters.append({
                    "cluster_name": r["tag"], # Using tag as cluster name
                    "item_count": r["item_count"],
                    "item_ids": r["item_ids"],
                    "keywords": [r["tag"]] # Using tag as keyword
                })
            return {"semantic_clusters": clusters}
        except Exception as e:
            logger.error(f"Error generating semantic clusters data: {e}")
            raise