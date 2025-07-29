"""
User Behavior Tracking Service for Dreamscape

This service captures and analyzes user interactions to build
comprehensive behavioral profiles for persona development.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db_pool

logger = logging.getLogger(__name__)


class BehaviorTrackingService:
    """Service for tracking and analyzing user behavior patterns"""
    
    def __init__(self):
        self.action_types = {
            'view': 'Content viewing',
            'save': 'Content saving',
            'tag': 'Content tagging',
            'share': 'Content sharing',
            'search': 'Search query',
            'filter': 'Apply filters',
            'navigate': 'Navigation',
            'export': 'Content export',
            'favorite': 'Mark as favorite',
            'comment': 'Add comment',
            'rate': 'Rate content',
            'download': 'Download content'
        }
    
    async def track_behavior(
        self,
        user_id: UUID,
        action_type: str,
        item_id: Optional[UUID] = None,
        item_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        duration_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Track a user behavior event.
        
        Args:
            user_id: The user performing the action
            action_type: Type of action (view, save, tag, etc.)
            item_id: ID of the content item (if applicable)
            item_type: Type of content (article, video, etc.)
            context: Additional context (search terms, filters, etc.)
            duration_seconds: How long the user engaged
            metadata: Device info, browser, etc.
        
        Returns:
            UUID of the created behavior record
        """
        try:
            pool = await get_db_pool()
            async with pool.acquire() as connection:
                    behavior_id = await connection.fetchval("""
                        INSERT INTO user_behaviors (
                            user_id, action_type, item_id, item_type,
                            context, duration_seconds, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        RETURNING id
                    """, 
                    user_id, action_type, item_id, item_type,
                    json.dumps(context or {}),
                    duration_seconds,
                    json.dumps(metadata or {})
                    )
                    
                    logger.debug(f"Tracked behavior: {action_type} for user {user_id}")
                    return behavior_id
                    
        except Exception as e:
            logger.error(f"Error tracking behavior: {str(e)}")
            raise
    
    async def track_content_view(
        self,
        user_id: UUID,
        item_id: UUID,
        item_type: str,
        duration_seconds: int,
        source: str = "direct",
        device_info: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """Track content viewing with engagement metrics"""
        
        context = {"source": source}
        metadata = device_info or {}
        
        return await self.track_behavior(
            user_id=user_id,
            action_type="view",
            item_id=item_id,
            item_type=item_type,
            context=context,
            duration_seconds=duration_seconds,
            metadata=metadata
        )
    
    async def track_search(
        self,
        user_id: UUID,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        results_count: int = 0,
        clicked_items: Optional[List[UUID]] = None
    ) -> UUID:
        """Track search behavior with query analysis"""
        
        context = {
            "query": query,
            "filters": filters or {},
            "results_count": results_count,
            "clicked_items": [str(id) for id in (clicked_items or [])]
        }
        
        return await self.track_behavior(
            user_id=user_id,
            action_type="search",
            context=context
        )
    
    async def get_user_behavior_summary(
        self, 
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive behavior summary for a user.
        
        Returns activity patterns, content preferences, and engagement metrics.
        """
        try:
            pool = await get_db_pool()
            async with pool.acquire() as connection:
                    # Get behavior data for the last N days
                    cutoff_date = datetime.now() - timedelta(days=days)
                    
                    # Activity patterns by hour and day
                    activity_patterns = await connection.fetch("""
                        SELECT 
                            EXTRACT(hour FROM created_at) as hour_of_day,
                            EXTRACT(dow FROM created_at) as day_of_week,
                            COUNT(*) as activity_count
                        FROM user_behaviors 
                        WHERE user_id = $1 AND created_at >= $2
                        GROUP BY hour_of_day, day_of_week
                        ORDER BY hour_of_day, day_of_week
                    """, user_id, cutoff_date)
                    
                    # Content type preferences
                    content_preferences = await connection.fetch("""
                        SELECT 
                            item_type,
                            COUNT(*) as views,
                            AVG(duration_seconds) as avg_engagement,
                            COUNT(DISTINCT item_id) as unique_items
                        FROM user_behaviors 
                        WHERE user_id = $1 
                            AND created_at >= $2 
                            AND action_type = 'view'
                            AND item_type IS NOT NULL
                        GROUP BY item_type
                        ORDER BY views DESC
                    """, user_id, cutoff_date)
                    
                    # Action distribution
                    action_distribution = await connection.fetch("""
                        SELECT action_type, COUNT(*) as count
                        FROM user_behaviors 
                        WHERE user_id = $1 AND created_at >= $2
                        GROUP BY action_type
                        ORDER BY count DESC
                    """, user_id, cutoff_date)
                    
                    # Engagement metrics
                    engagement_metrics = await connection.fetchrow("""
                        SELECT 
                            COUNT(DISTINCT DATE(created_at)) as active_days,
                            COUNT(*) as total_actions,
                            COUNT(DISTINCT item_id) as unique_items_interacted,
                            AVG(duration_seconds) as avg_session_duration,
                            MAX(created_at) as last_active
                        FROM user_behaviors 
                        WHERE user_id = $1 AND created_at >= $2
                    """, user_id, cutoff_date)
                    
                    # Search patterns
                    search_patterns = await connection.fetch("""
                        SELECT 
                            context->>'query' as query,
                            COUNT(*) as frequency
                        FROM user_behaviors 
                        WHERE user_id = $1 
                            AND created_at >= $2 
                            AND action_type = 'search'
                            AND context->>'query' IS NOT NULL
                        GROUP BY context->>'query'
                        ORDER BY frequency DESC
                        LIMIT 20
                    """, user_id, cutoff_date)
                    
                    return {
                        "user_id": str(user_id),
                        "analysis_period_days": days,
                        "activity_patterns": [dict(row) for row in activity_patterns],
                        "content_preferences": [dict(row) for row in content_preferences],
                        "action_distribution": [dict(row) for row in action_distribution],
                        "engagement_metrics": dict(engagement_metrics) if engagement_metrics else {},
                        "search_patterns": [dict(row) for row in search_patterns],
                        "behavioral_insights": await self._generate_behavioral_insights(
                            user_id, activity_patterns, content_preferences, engagement_metrics
                        )
                    }
                    
        except Exception as e:
            logger.error(f"Error getting behavior summary: {str(e)}")
            raise
    
    async def _generate_behavioral_insights(
        self,
        user_id: UUID,
        activity_patterns: List[Dict],
        content_preferences: List[Dict],
        engagement_metrics: Dict
    ) -> Dict[str, Any]:
        """Generate AI-powered insights from behavior patterns"""
        
        insights = {
            "activity_insights": [],
            "content_insights": [],
            "engagement_insights": [],
            "recommendations": []
        }
        
        # Activity pattern insights
        if activity_patterns:
            hour_counts = {}
            day_counts = {}
            
            for pattern in activity_patterns:
                hour = int(pattern['hour_of_day'])
                day = int(pattern['day_of_week'])
                count = pattern['activity_count']
                
                hour_counts[hour] = hour_counts.get(hour, 0) + count
                day_counts[day] = day_counts.get(day, 0) + count
            
            # Find peak hours
            peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
            if peak_hour is not None:
                if 6 <= peak_hour <= 11:
                    insights["activity_insights"].append("Most active in the morning")
                elif 12 <= peak_hour <= 17:
                    insights["activity_insights"].append("Most active in the afternoon")
                elif 18 <= peak_hour <= 22:
                    insights["activity_insights"].append("Most active in the evening")
                else:
                    insights["activity_insights"].append("Most active during late hours")
            
            # Find peak days (0=Sunday, 6=Saturday)
            peak_day = max(day_counts, key=day_counts.get) if day_counts else None
            if peak_day is not None:
                day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                if peak_day in [1, 2, 3, 4, 5]:  # Weekdays
                    insights["activity_insights"].append("More active on weekdays")
                else:
                    insights["activity_insights"].append("More active on weekends")
        
        # Content preference insights
        if content_preferences:
            top_content = content_preferences[0]
            insights["content_insights"].append(f"Prefers {top_content['item_type']} content")
            
            # Engagement analysis
            if len(content_preferences) > 1:
                high_engagement = [c for c in content_preferences if c['avg_engagement'] and c['avg_engagement'] > 120]
                if high_engagement:
                    insights["content_insights"].append("Shows high engagement with complex content")
        
        # Engagement insights
        if engagement_metrics:
            active_days = engagement_metrics.get('active_days', 0)
            total_actions = engagement_metrics.get('total_actions', 0)
            
            if active_days and total_actions:
                actions_per_day = total_actions / active_days
                if actions_per_day > 20:
                    insights["engagement_insights"].append("Power user - very high activity")
                elif actions_per_day > 10:
                    insights["engagement_insights"].append("Regular user - consistent activity")
                else:
                    insights["engagement_insights"].append("Casual user - light activity")
        
        return insights
    
    async def get_learning_velocity(self, user_id: UUID) -> float:
        """
        Calculate user's learning velocity based on behavior patterns.
        
        Returns a score from 0.0 to 1.0 indicating how quickly the user
        learns and progresses through content.
        """
        try:
            pool = await get_db_pool()
            async with pool.acquire() as connection:
                    # Get metrics for learning velocity calculation
                    metrics = await connection.fetchrow("""
                        SELECT 
                            COUNT(DISTINCT item_id) as unique_items,
                            COUNT(*) as total_interactions,
                            AVG(duration_seconds) as avg_engagement,
                            COUNT(DISTINCT item_type) as content_diversity,
                            MAX(created_at) - MIN(created_at) as time_span
                        FROM user_behaviors 
                        WHERE user_id = $1 
                            AND action_type IN ('view', 'save', 'tag')
                            AND created_at >= NOW() - INTERVAL '30 days'
                    """, user_id)
                    
                    if not metrics or not metrics['unique_items']:
                        return 0.5  # Default for new users
                    
                    # Factors for learning velocity
                    # 1. Content consumption rate
                    days_active = max(1, (metrics['time_span'].days if metrics['time_span'] else 30))
                    items_per_day = metrics['unique_items'] / days_active
                    consumption_score = min(1.0, items_per_day / 5.0)  # Max 5 items/day = 1.0
                    
                    # 2. Engagement depth
                    avg_engagement = metrics['avg_engagement'] or 0
                    engagement_score = min(1.0, avg_engagement / 300.0)  # 5 min = 1.0
                    
                    # 3. Content diversity
                    diversity_score = min(1.0, metrics['content_diversity'] / 5.0)  # 5 types = 1.0
                    
                    # 4. Interaction intensity
                    interaction_ratio = metrics['total_interactions'] / metrics['unique_items']
                    intensity_score = min(1.0, interaction_ratio / 3.0)  # 3 interactions/item = 1.0
                    
                    # Weighted average
                    velocity = (
                        consumption_score * 0.3 +
                        engagement_score * 0.3 +
                        diversity_score * 0.2 +
                        intensity_score * 0.2
                    )
                    
                    return round(velocity, 2)
                    
        except Exception as e:
            logger.error(f"Error calculating learning velocity: {str(e)}")
            return 0.5
    
    async def detect_interest_evolution(
        self, 
        user_id: UUID,
        weeks: int = 12
    ) -> Dict[str, Any]:
        """
        Detect how user's interests have evolved over time.
        
        Returns trends in content types, topics, and engagement patterns.
        """
        try:
            pool = await get_db_pool()
            async with pool.acquire() as connection:
                    # Get weekly content type preferences
                    evolution_data = await connection.fetch("""
                        SELECT 
                            DATE_TRUNC('week', created_at) as week,
                            item_type,
                            COUNT(*) as interactions,
                            AVG(duration_seconds) as avg_engagement
                        FROM user_behaviors 
                        WHERE user_id = $1 
                            AND created_at >= NOW() - INTERVAL '%s weeks'
                            AND action_type = 'view'
                            AND item_type IS NOT NULL
                        GROUP BY week, item_type
                        ORDER BY week, interactions DESC
                    """ % weeks, user_id)
                    
                    # Process evolution trends
                    weekly_data = {}
                    for row in evolution_data:
                        week_str = row['week'].strftime('%Y-%m-%d')
                        if week_str not in weekly_data:
                            weekly_data[week_str] = {}
                        
                        weekly_data[week_str][row['item_type']] = {
                            'interactions': row['interactions'],
                            'avg_engagement': float(row['avg_engagement'] or 0)
                        }
                    
                    return {
                        "user_id": str(user_id),
                        "analysis_weeks": weeks,
                        "weekly_evolution": weekly_data,
                        "trends": await self._analyze_evolution_trends(weekly_data)
                    }
                    
        except Exception as e:
            logger.error(f"Error detecting interest evolution: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_evolution_trends(
        self, 
        weekly_data: Dict[str, Dict[str, Dict]]
    ) -> Dict[str, Any]:
        """Analyze trends in the evolution data"""
        
        if not weekly_data:
            return {"trends": []}
        
        # Get content types across all weeks
        all_content_types = set()
        for week_data in weekly_data.values():
            all_content_types.update(week_data.keys())
        
        trends = []
        
        for content_type in all_content_types:
            # Get interaction counts over time
            interactions_over_time = []
            weeks = sorted(weekly_data.keys())
            
            for week in weeks:
                count = weekly_data[week].get(content_type, {}).get('interactions', 0)
                interactions_over_time.append(count)
            
            if len(interactions_over_time) >= 3:  # Need at least 3 data points
                # Simple trend detection
                recent_avg = sum(interactions_over_time[-3:]) / 3
                early_avg = sum(interactions_over_time[:3]) / 3
                
                if recent_avg > early_avg * 1.5:
                    trends.append({
                        "content_type": content_type,
                        "trend": "increasing",
                        "strength": "strong" if recent_avg > early_avg * 2 else "moderate"
                    })
                elif recent_avg < early_avg * 0.5:
                    trends.append({
                        "content_type": content_type,
                        "trend": "decreasing",
                        "strength": "strong" if recent_avg < early_avg * 0.5 else "moderate"
                    })
        
        return {"trends": trends}
    
    async def cleanup_old_behaviors(self, days_to_keep: int = 365) -> int:
        """Clean up old behavior data to manage database size"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as connection:
                    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                    
                    deleted_count = await connection.fetchval("""
                        DELETE FROM user_behaviors 
                        WHERE created_at < $1
                        RETURNING COUNT(*)
                    """, cutoff_date)
                    
                    logger.info(f"Cleaned up {deleted_count} old behavior records")
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"Error cleaning up behaviors: {str(e)}")
            return 0