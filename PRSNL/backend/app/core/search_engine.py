"""Search engine using PostgreSQL full-text search"""
from typing import List, Optional
from datetime import datetime, timedelta
import asyncpg
from app.models.schemas import SearchResult


class SearchEngine:
    """Handles search queries using PostgreSQL FTS"""
    
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
    
    async def search(
        self,
        query: str,
        date_filter: str = "all",
        type_filter: str = "all",
        tags: List[str] = [],
        limit: int = 20,
        offset: int = 0
    ) -> List[SearchResult]:
        """
        Perform full-text search with filters
        """
        # Build the WHERE clause
        where_clauses = ["i.status = 'completed'"]
        params = []
        param_count = 1
        
        # Add search query
        if query:
            where_clauses.append(f"i.search_vector @@ plainto_tsquery('english', ${param_count})")
            params.append(query)
            param_count += 1
        
        # Add date filter
        if date_filter != "all":
            date_clause, date_param = self._build_date_filter(date_filter)
            if date_clause:
                where_clauses.append(date_clause.replace("$1", f"${param_count}"))
                params.append(date_param)
                param_count += 1
        
        # Add tag filter
        if tags:
            tag_placeholders = ", ".join([f"${i}" for i in range(param_count, param_count + len(tags))])
            where_clauses.append(f"""
                EXISTS (
                    SELECT 1 FROM item_tags it
                    JOIN tags t ON it.tag_id = t.id
                    WHERE it.item_id = i.id AND t.name IN ({tag_placeholders})
                )
            """)
            params.extend(tags)
            param_count += len(tags)
        
        # Build the query
        where_clause = " AND ".join(where_clauses)
        
        # Add ranking for relevance
        rank_clause = ""
        if query:
            rank_clause = f", ts_rank(i.search_vector, plainto_tsquery('english', $1)) as rank"
            order_clause = "ORDER BY rank DESC, i.created_at DESC"
        else:
            order_clause = "ORDER BY i.created_at DESC"
        
        sql = f"""
            SELECT 
                i.id,
                i.title,
                i.url,
                COALESCE(i.summary, LEFT(i.processed_content, 200)) as snippet,
                i.created_at,
                COALESCE(
                    array_agg(t.name) FILTER (WHERE t.name IS NOT NULL), 
                    '{{}}'::text[]
                ) as tags
                {rank_clause}
            FROM items i
            LEFT JOIN item_tags it ON i.id = it.item_id
            LEFT JOIN tags t ON it.tag_id = t.id
            WHERE {where_clause}
            GROUP BY i.id, i.title, i.url, i.summary, i.processed_content, i.created_at, i.search_vector
            {order_clause}
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        
        params.append(limit)
        params.append(offset)
        
        # Execute query
        rows = await self.conn.fetch(sql, *params)
        
        # Convert to SearchResult objects
        results = []
        for row in rows:
            results.append(SearchResult(
                id=row['id'],
                title=row['title'],
                url=row['url'],
                snippet=row['snippet'] or '',
                tags=row['tags'],
                created_at=row['created_at'],
                score=row.get('rank')
            ))
        
        return results
    
    async def count_results(
        self,
        query: str,
        date_filter: str = "all",
        type_filter: str = "all",
        tags: List[str] = []
    ) -> int:
        """
        Count total results for a search query
        """
        # Build the WHERE clause (same as search)
        where_clauses = ["i.status = 'completed'"]
        params = []
        param_count = 1
        
        if query:
            where_clauses.append(f"i.search_vector @@ plainto_tsquery('english', ${param_count})")
            params.append(query)
            param_count += 1
        
        if date_filter != "all":
            date_clause, date_param = self._build_date_filter(date_filter)
            if date_clause:
                where_clauses.append(date_clause.replace("$1", f"${param_count}"))
                params.append(date_param)
                param_count += 1
        
        if tags:
            tag_placeholders = ", ".join([f"${i}" for i in range(param_count, param_count + len(tags))])
            where_clauses.append(f"""
                EXISTS (
                    SELECT 1 FROM item_tags it
                    JOIN tags t ON it.tag_id = t.id
                    WHERE it.item_id = i.id AND t.name IN ({tag_placeholders})
                )
            """)
            params.extend(tags)
        
        where_clause = " AND ".join(where_clauses)
        
        sql = f"""
            SELECT COUNT(DISTINCT i.id) as count
            FROM items i
            LEFT JOIN item_tags it ON i.id = it.item_id
            LEFT JOIN tags t ON it.tag_id = t.id
            WHERE {where_clause}
        """
        
        result = await self.conn.fetchrow(sql, *params)
        return result['count']
    
    def _build_date_filter(self, date_filter: str) -> tuple[str, datetime]:
        """
        Build date filter clause
        """
        now = datetime.now()
        
        if date_filter == "today":
            date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return "i.created_at >= $1", date
        elif date_filter == "week":
            date = now - timedelta(days=7)
            return "i.created_at >= $1", date
        elif date_filter == "month":
            date = now - timedelta(days=30)
            return "i.created_at >= $1", date
        elif date_filter == "year":
            date = now - timedelta(days=365)
            return "i.created_at >= $1", date
        
        return "", None