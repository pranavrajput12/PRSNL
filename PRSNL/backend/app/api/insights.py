"""
Dynamic Insights API endpoints
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_optional
from app.db.database import get_db
from app.services.dynamic_insights import DynamicInsightsService

logger = logging.getLogger(__name__)

router = APIRouter()
insights_service = DynamicInsightsService()

# Response models
class InsightData(BaseModel):
    type: str
    title: str
    description: str
    data: Dict[str, Any]
    visualization: str

class InsightsResponse(BaseModel):
    insights: List[InsightData]
    summary: str
    time_range: str
    item_count: int
    generated_at: str

class InsightTypeInfo(BaseModel):
    id: str
    name: str
    description: str
    icon: str

# Endpoints
@router.get("/insights", response_model=InsightsResponse)
async def get_insights(
    time_range: str = Query("30d", description="Time range (e.g., 7d, 30d, 3m, 1y)"),
    insight_types: Optional[str] = Query(None, description="Comma-separated insight types"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Generate dynamic insights about the knowledge base
    """
    try:
        # Parse insight types
        types_list = None
        if insight_types:
            types_list = [t.strip() for t in insight_types.split(',')]
        
        # Generate insights
        result = await insights_service.generate_insights(
            user_id=current_user.id if current_user else None,
            time_range=time_range,
            insight_types=types_list,
            db=db
        )
        
        return InsightsResponse(**result)
        
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/types", response_model=List[InsightTypeInfo])
async def get_insight_types():
    """
    Get available insight types
    """
    types = [
        {
            "id": "trending_topics",
            "name": "Trending Topics",
            "description": "Topics gaining momentum in your knowledge base",
            "icon": "trending-up"
        },
        {
            "id": "knowledge_evolution",
            "name": "Knowledge Evolution",
            "description": "How your interests have evolved over time",
            "icon": "git-branch"
        },
        {
            "id": "content_patterns",
            "name": "Content Patterns",
            "description": "Patterns in the type of content you save",
            "icon": "pie-chart"
        },
        {
            "id": "learning_velocity",
            "name": "Learning Velocity",
            "description": "Your learning pace and focus areas",
            "icon": "activity"
        },
        {
            "id": "connection_opportunities",
            "name": "Connection Opportunities",
            "description": "Potential connections between disparate topics",
            "icon": "link"
        },
        {
            "id": "knowledge_depth",
            "name": "Knowledge Depth",
            "description": "Areas where you've built deep expertise",
            "icon": "layers"
        },
        {
            "id": "exploration_suggestions",
            "name": "Exploration Suggestions",
            "description": "New areas to explore based on your interests",
            "icon": "compass"
        },
        {
            "id": "time_patterns",
            "name": "Time Patterns",
            "description": "When you're most active in learning",
            "icon": "clock"
        },
        {
            "id": "content_diversity",
            "name": "Content Diversity",
            "description": "Diversity score of your knowledge base",
            "icon": "shuffle"
        },
        {
            "id": "emerging_themes",
            "name": "Emerging Themes",
            "description": "New themes emerging from recent saves",
            "icon": "sparkles"
        }
    ]
    
    return [InsightTypeInfo(**t) for t in types]

@router.get("/insights/trending")
async def get_trending_insights(
    days: int = Query(7, description="Number of days to analyze"),
    limit: int = Query(10, description="Maximum number of trending topics"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Get just trending topics (lightweight endpoint)
    """
    try:
        result = await insights_service.generate_insights(
            user_id=current_user.id if current_user else None,
            time_range=f"{days}d",
            insight_types=["trending_topics"],
            db=db
        )
        
        if result['insights']:
            trending_data = result['insights'][0]['data']
            return {
                "topics": trending_data['topics'][:limit],
                "analysis": trending_data['analysis'],
                "time_range": f"{days} days",
                "generated_at": datetime.utcnow().isoformat()
            }
        else:
            return {
                "topics": [],
                "analysis": "No trending topics found",
                "time_range": f"{days} days",
                "generated_at": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error getting trending insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/learning-velocity")
async def get_learning_velocity(
    time_range: str = Query("30d", description="Time range"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Get learning velocity metrics
    """
    try:
        result = await insights_service.generate_insights(
            user_id=current_user.id if current_user else None,
            time_range=time_range,
            insight_types=["learning_velocity"],
            db=db
        )
        
        if result['insights']:
            return result['insights'][0]['data']
        else:
            return {
                "average_daily_saves": 0,
                "peak_daily_saves": 0,
                "momentum": {"value": 0, "trend": "stable"},
                "message": "Not enough data for analysis"
            }
            
    except Exception as e:
        logger.error(f"Error getting learning velocity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/exploration-suggestions")
async def get_exploration_suggestions(
    limit: int = Query(5, description="Number of suggestions"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Get personalized exploration suggestions
    """
    try:
        result = await insights_service.generate_insights(
            user_id=current_user.id if current_user else None,
            time_range="30d",
            insight_types=["exploration_suggestions"],
            db=db
        )
        
        if result['insights']:
            suggestions_data = result['insights'][0]['data']
            return {
                "suggestions": suggestions_data['suggestions'][:limit],
                "based_on_topics": suggestions_data['based_on_topics'],
                "expansion_potential": suggestions_data['expansion_potential']
            }
        else:
            return {
                "suggestions": [],
                "based_on_topics": [],
                "expansion_potential": 0
            }
            
    except Exception as e:
        logger.error(f"Error getting exploration suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/dashboard")
async def get_dashboard_insights(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Get insights optimized for dashboard display
    """
    try:
        # Generate a curated set of insights for the dashboard
        result = await insights_service.generate_insights(
            user_id=current_user.id if current_user else None,
            time_range="30d",
            insight_types=[
                "trending_topics",
                "learning_velocity", 
                "content_diversity",
                "emerging_themes"
            ],
            db=db
        )
        
        # Format for dashboard
        dashboard_data = {
            "summary": result['summary'],
            "metrics": {
                "total_items": result['item_count'],
                "time_range": result['time_range']
            },
            "widgets": []
        }
        
        # Convert insights to dashboard widgets
        for insight in result['insights']:
            widget = {
                "id": insight['type'],
                "title": insight['title'],
                "type": insight['visualization'],
                "data": insight['data'],
                "priority": _get_widget_priority(insight['type'])
            }
            dashboard_data['widgets'].append(widget)
        
        # Sort by priority
        dashboard_data['widgets'].sort(key=lambda x: x['priority'])
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting dashboard insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/timeline-trends")
async def get_timeline_trends(
    time_range: str = Query("30d", description="Time range"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Get daily content type counts for timeline trends visualization
    """
    try:
        from datetime import datetime, timedelta

        from sqlalchemy import func, text

        # Parse time range
        days = _parse_time_range(time_range)
        
        # Calculate date cutoff
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query for daily content type counts
        query = text("""
            SELECT 
                DATE(created_at) as date,
                CASE 
                    WHEN type = 'article' THEN 'articles'
                    WHEN type = 'video' THEN 'videos' 
                    WHEN type = 'note' THEN 'notes'
                    WHEN type = 'bookmark' THEN 'bookmarks'
                    ELSE 'other'
                END as content_type,
                COUNT(*) as count
            FROM items 
            WHERE created_at >= :cutoff_date
            GROUP BY DATE(created_at), CASE 
                    WHEN type = 'article' THEN 'articles'
                    WHEN type = 'video' THEN 'videos' 
                    WHEN type = 'note' THEN 'notes'
                    WHEN type = 'bookmark' THEN 'bookmarks'
                    ELSE 'other'
                END
            ORDER BY date DESC
        """)
        
        result = await db.execute(query, {"cutoff_date": cutoff_date})
        rows = result.fetchall()
        
        # Organize data by date
        daily_data = {}
        for row in rows:
            date_str = row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date)
            if date_str not in daily_data:
                daily_data[date_str] = {
                    "date": date_str,
                    "articles": 0,
                    "videos": 0, 
                    "notes": 0,
                    "bookmarks": 0,
                    "other": 0
                }
            daily_data[date_str][row.content_type] = row.count
        
        # Convert to list and sort by date
        timeline_data = list(daily_data.values())
        timeline_data.sort(key=lambda x: x["date"], reverse=True)
        
        # If no data, return empty structure
        if not timeline_data:
            timeline_data = []
        
        return {
            "timeline_data": timeline_data,
            "time_range": time_range,
            "total_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting timeline trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _parse_time_range(time_range: str) -> int:
    """Parse time range string to number of days"""
    if time_range.endswith('d'):
        return int(time_range[:-1])
    elif time_range.endswith('w'):
        return int(time_range[:-1]) * 7
    elif time_range.endswith('m'):
        return int(time_range[:-1]) * 30
    elif time_range.endswith('y'):
        return int(time_range[:-1]) * 365
    elif time_range == 'all':
        return 3650  # 10 years
    else:
        return 30  # Default 30 days

@router.get("/insights/top-tags")
async def get_top_tags(
    time_range: str = Query("30d", description="Time range"),
    limit: int = Query(10, description="Maximum number of tags to return"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Get top tags with usage counts for Memory Palace visualization
    """
    try:
        from sqlalchemy import func, text

        # Parse time range
        days = _parse_time_range(time_range)
        
        # Calculate date cutoff
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query for top tags with usage counts using proper table structure
        query = text("""
            SELECT 
                t.name,
                COUNT(it.item_id) as usage_count,
                MAX(i.created_at) as latest_use,
                CASE 
                    WHEN MAX(i.created_at) >= :cutoff_date THEN 1.0
                    ELSE 0.5
                END as recency_weight
            FROM tags t
            JOIN item_tags it ON t.id = it.tag_id
            JOIN items i ON it.item_id = i.id
            WHERE i.created_at >= :cutoff_date
            GROUP BY t.id, t.name
            ORDER BY usage_count DESC, t.name
            LIMIT :limit
        """)
        
        result = await db.execute(query, {
            "cutoff_date": cutoff_date,
            "limit": limit
        })
        rows = result.fetchall()
        
        # Format response
        tags = []
        max_count = max([row.usage_count for row in rows], default=1)
        
        for row in rows:
            tags.append({
                "name": row.name,
                "usage_count": row.usage_count,
                "latest_use": row.latest_use.isoformat(),
                "weight": min(1.0, row.usage_count / max_count),
                "recency_weight": round(float(row.recency_weight), 2)
            })
        
        return {
            "tags": tags,
            "time_range": time_range,
            "total_tags": len(tags),
            "max_usage": max_count,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting top tags: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/personality-analysis")
async def get_personality_analysis(
    time_range: str = Query("30d", description="Time range"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Analyze user's content and tags to determine personality type
    """
    try:
        from datetime import datetime, timedelta

        from sqlalchemy import func, text

        # Parse time range
        days = _parse_time_range(time_range)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get content type distribution
        content_query = text("""
            SELECT 
                type,
                COUNT(*) as count
            FROM items 
            WHERE created_at >= :cutoff_date
            GROUP BY type
            ORDER BY count DESC
        """)
        
        # Get tag diversity and patterns
        tag_query = text("""
            SELECT 
                t.name,
                COUNT(*) as usage_count,
                array_agg(DISTINCT i.type) as content_types
            FROM tags t
            JOIN item_tags it ON t.id = it.tag_id  
            JOIN items i ON it.item_id = i.id
            WHERE i.created_at >= :cutoff_date
            GROUP BY t.id, t.name
            ORDER BY usage_count DESC
            LIMIT 20
        """)
        
        # Get temporal patterns
        temporal_query = text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as daily_count
            FROM items 
            WHERE created_at >= :cutoff_date
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        
        # Execute queries
        content_result = await db.execute(content_query, {"cutoff_date": cutoff_date})
        tag_result = await db.execute(tag_query, {"cutoff_date": cutoff_date})
        temporal_result = await db.execute(temporal_query, {"cutoff_date": cutoff_date})
        
        content_data = content_result.fetchall()
        tag_data = tag_result.fetchall()
        temporal_data = temporal_result.fetchall()
        
        # Analyze personality based on patterns
        personality_analysis = _analyze_personality(content_data, tag_data, temporal_data)
        
        return {
            "personality": personality_analysis,
            "analysis_data": {
                "content_distribution": [{"type": row.type, "count": row.count} for row in content_data],
                "top_tags": [{"name": row.name, "usage": row.usage_count} for row in tag_data],
                "temporal_pattern": [{"date": row.date.isoformat(), "count": row.daily_count} for row in temporal_data]
            },
            "time_range": time_range,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing personality: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _analyze_personality(content_data, tag_data, temporal_data):
    """
    Analyze personality based on content patterns, tags, and temporal behavior
    """
    # Define personality types
    personality_types = {
        "explorer": {
            "name": "The Explorer",
            "description": "You thrive on discovering new ideas and diverse topics. Your knowledge spans wide horizons, always seeking the next frontier of understanding.",
            "traits": ["Curious", "Diverse interests", "Adventurous", "Open-minded"],
            "icon": "🧭"
        },
        "specialist": {
            "name": "The Specialist", 
            "description": "You dive deep into specific domains, building expertise through focused study. Quality over quantity defines your learning approach.",
            "traits": ["Deep focus", "Expert knowledge", "Methodical", "Thorough"],
            "icon": "🔬"
        },
        "connector": {
            "name": "The Connector",
            "description": "You excel at linking ideas across different fields. Your mind sees patterns and connections others miss.",
            "traits": ["Interdisciplinary", "Pattern recognition", "Synthesizer", "Innovative"],
            "icon": "🌐"
        },
        "practitioner": {
            "name": "The Practitioner",
            "description": "You learn by doing. Tutorials, how-tos, and hands-on content fuel your practical approach to knowledge.",
            "traits": ["Hands-on", "Implementation focused", "Practical", "Results-oriented"],
            "icon": "⚡"
        },
        "theorist": {
            "name": "The Theorist",
            "description": "You love concepts, frameworks, and abstract thinking. Research and academic content energize your analytical mind.",
            "traits": ["Analytical", "Conceptual", "Research-oriented", "Systematic"],
            "icon": "📚"
        },
        "creator": {
            "name": "The Creator",
            "description": "You consume content to fuel your creative output. Design, art, and inspiration drive your learning journey.",
            "traits": ["Creative", "Artistic", "Inspirational", "Expressive"],
            "icon": "🎨"
        },
        "analyst": {
            "name": "The Analyst",
            "description": "Data, metrics, and logical frameworks guide your learning. You seek evidence-based insights and measurable outcomes.",
            "traits": ["Data-driven", "Logical", "Quantitative", "Strategic"],
            "icon": "📊"
        },
        "communicator": {
            "name": "The Communicator",
            "description": "You learn to share and connect with others. Social content, writing, and people-focused topics dominate your interests.",
            "traits": ["Social", "Empathetic", "Storyteller", "Collaborative"],
            "icon": "💬"
        },
        "innovator": {
            "name": "The Innovator",
            "description": "You stay ahead of the curve with cutting-edge technology and emerging trends. The future excites you.",
            "traits": ["Forward-thinking", "Tech-savvy", "Disruptive", "Entrepreneurial"],
            "icon": "🚀"
        },
        "curator": {
            "name": "The Curator",
            "description": "You organize and collect knowledge systematically. Your learning is methodical and reference-oriented.",
            "traits": ["Organized", "Systematic", "Reference-focused", "Comprehensive"],
            "icon": "📂"
        }
    }
    
    # Calculate scores for each personality type
    scores = {}
    total_items = sum(row.count for row in content_data) if content_data else 1
    
    # Content type analysis
    content_types = {row.type: row.count for row in content_data}
    
    # Tag diversity analysis
    tag_count = len(tag_data)
    unique_tags = [row.name.lower() for row in tag_data]
    
    # Temporal consistency analysis
    temporal_consistency = len([row for row in temporal_data if row.daily_count > 0]) / max(len(temporal_data), 1) if temporal_data else 0
    
    # Score each personality type
    for personality_id, personality in personality_types.items():
        score = 0
        
        if personality_id == "explorer":
            # High tag diversity, varied content types
            score += min(tag_count / 20, 1.0) * 30  # Tag diversity
            score += len(content_types) * 10  # Content type variety
            
        elif personality_id == "specialist":
            # Deep focus on few topics, consistent patterns
            if tag_count > 0:
                top_tag_ratio = (tag_data[0].usage_count / total_items) if tag_data else 0
                score += top_tag_ratio * 40  # Focus on top tags
            score += temporal_consistency * 20  # Consistent learning
            
        elif personality_id == "connector":
            # Interdisciplinary tags, varied content
            interdisciplinary_keywords = ["research", "study", "analysis", "framework", "theory", "concept"]
            score += sum(1 for tag in unique_tags if any(keyword in tag for keyword in interdisciplinary_keywords)) * 5
            score += len(content_types) * 8
            
        elif personality_id == "practitioner":
            # Tutorial/how-to focused content
            practical_keywords = ["tutorial", "how-to", "guide", "implementation", "practice", "tool", "tips"]
            score += sum(1 for tag in unique_tags if any(keyword in tag for keyword in practical_keywords)) * 8
            score += content_types.get("video", 0) / total_items * 20  # Videos often practical
            
        elif personality_id == "theorist":
            # Research, academic content
            academic_keywords = ["research", "paper", "study", "theory", "academic", "science", "analysis"]
            score += sum(1 for tag in unique_tags if any(keyword in tag for keyword in academic_keywords)) * 10
            score += content_types.get("article", 0) / total_items * 15  # Articles often theoretical
            
        elif personality_id == "creator":
            # Design, art, creative content
            creative_keywords = ["design", "art", "creative", "inspiration", "ui", "ux", "visual", "aesthetic"]
            score += sum(1 for tag in unique_tags if any(keyword in tag for keyword in creative_keywords)) * 12
            
        elif personality_id == "analyst":
            # Data, metrics, business content
            analytical_keywords = ["data", "analytics", "metrics", "business", "strategy", "analysis", "performance"]
            score += sum(1 for tag in unique_tags if any(keyword in tag for keyword in analytical_keywords)) * 10
            
        elif personality_id == "communicator":
            # Social, writing, communication content
            communication_keywords = ["writing", "social", "communication", "marketing", "content", "blog", "story"]
            score += sum(1 for tag in unique_tags if any(keyword in tag for keyword in communication_keywords)) * 8
            
        elif personality_id == "innovator":
            # Tech, startup, innovation content
            innovation_keywords = ["tech", "technology", "startup", "innovation", "ai", "blockchain", "future"]
            score += sum(1 for tag in unique_tags if any(keyword in tag for keyword in innovation_keywords)) * 10
            
        elif personality_id == "curator":
            # High organization, reference content
            curation_keywords = ["reference", "documentation", "list", "resource", "collection", "bookmark"]
            score += sum(1 for tag in unique_tags if any(keyword in tag for keyword in curation_keywords)) * 8
            score += content_types.get("bookmark", 0) / total_items * 25  # Bookmarks indicate curation
            
        scores[personality_id] = max(0, score)
    
    # Find dominant personality
    if not scores or max(scores.values()) == 0:
        # Default fallback
        dominant_personality = "explorer"
        confidence = 0.3
    else:
        dominant_personality = max(scores, key=scores.get)
        max_score = scores[dominant_personality]
        total_score = sum(scores.values())
        confidence = max_score / total_score if total_score > 0 else 0.3
    
    return {
        "type": dominant_personality,
        "name": personality_types[dominant_personality]["name"],
        "description": personality_types[dominant_personality]["description"],
        "traits": personality_types[dominant_personality]["traits"],
        "icon": personality_types[dominant_personality]["icon"],
        "confidence": round(confidence, 2),
        "scores": {k: round(v, 1) for k, v in scores.items()},
        "analysis_factors": {
            "content_variety": len(content_types),
            "tag_diversity": tag_count,
            "temporal_consistency": round(temporal_consistency, 2),
            "total_items": total_items
        }
    }

@router.get("/insights/top-content")
async def get_top_content(
    time_range: str = Query("30d", description="Time range"),
    limit: int = Query(10, description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Get top-rated content for Memory Palace visualization
    """
    try:
        from datetime import datetime, timedelta

        from sqlalchemy import func, text

        # Parse time range
        days = _parse_time_range(time_range)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query for top content based on various metrics
        query = text("""
            SELECT 
                id,
                title,
                url,
                type,
                created_at,
                summary,
                -- Calculate a composite score based on multiple factors
                (
                    CASE 
                        WHEN summary IS NOT NULL AND LENGTH(summary) > 100 THEN 3
                        WHEN summary IS NOT NULL AND LENGTH(summary) > 50 THEN 2
                        WHEN summary IS NOT NULL THEN 1
                        ELSE 0
                    END +
                    CASE 
                        WHEN created_at > :recent_cutoff THEN 3
                        WHEN created_at > :medium_cutoff THEN 2
                        ELSE 1
                    END
                ) as composite_score
            FROM items 
            WHERE created_at >= :cutoff_date
            ORDER BY composite_score DESC, created_at DESC
            LIMIT :limit
        """)
        
        # Recent cutoffs for scoring
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        medium_cutoff = datetime.utcnow() - timedelta(days=30)
        
        result = await db.execute(query, {
            "cutoff_date": cutoff_date,
            "recent_cutoff": recent_cutoff,
            "medium_cutoff": medium_cutoff,
            "limit": limit
        })
        rows = result.fetchall()
        
        # Format response
        top_content = []
        for row in rows:
            # Normalize the score to 0-1 range
            normalized_score = min(1.0, row.composite_score / 6.0)
            
            top_content.append({
                "id": row.id,
                "title": row.title,
                "url": row.url,
                "type": row.type,
                "created_at": row.created_at.isoformat(),
                "summary": row.summary,
                "metadata": {
                    "ai_analysis": {
                        "score": normalized_score
                    }
                }
            })
        
        return {
            "top_content": top_content,
            "time_range": time_range,
            "total_items": len(top_content),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting top content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_widget_priority(insight_type: str) -> int:
    """
    Get display priority for dashboard widgets
    """
    priorities = {
        "trending_topics": 1,
        "learning_velocity": 2,
        "emerging_themes": 3,
        "content_diversity": 4,
        "knowledge_evolution": 5,
        "connection_opportunities": 6
    }
    return priorities.get(insight_type, 99)