"""
Video Streaming API endpoints
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.database import get_db
from app.services.video_streaming import VideoStreamingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video-streaming", tags=["video-streaming"])


# Request/Response Models
class ProcessVideoRequest(BaseModel):
    item_id: str = Field(..., description="Item ID to process as video")


class FindRelatedRequest(BaseModel):
    item_id: str = Field(..., description="Source video item ID")
    limit: int = Field(default=10, ge=1, le=50)


class CreateMiniCourseRequest(BaseModel):
    topic: str = Field(..., description="Course topic")
    skill_level: str = Field(
        default="beginner",
        description="Skill level: beginner, intermediate, advanced"
    )
    max_videos: int = Field(default=10, ge=3, le=20)


class VideoResponse(BaseModel):
    success: bool
    data: dict
    message: Optional[str] = None


# Initialize service
video_service = VideoStreamingService()


@router.post("/process", response_model=VideoResponse)
async def process_video(
    request: ProcessVideoRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process a saved item as a video - extract metadata, transcript, and analyze content
    """
    try:
        result = await video_service.process_video_item(
            item_id=request.item_id,
            db=db
        )
        
        return VideoResponse(
            success=True,
            data=result,
            message="Video processed successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        raise HTTPException(status_code=500, detail="Failed to process video")


@router.post("/related", response_model=VideoResponse)
async def find_related_videos(
    request: FindRelatedRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Find videos related to a specific video
    """
    try:
        related = await video_service.find_related_videos(
            item_id=request.item_id,
            limit=request.limit,
            db=db
        )
        
        return VideoResponse(
            success=True,
            data={
                "source_id": request.item_id,
                "related_videos": related,
                "count": len(related)
            }
        )
    except Exception as e:
        logger.error(f"Error finding related videos: {e}")
        raise HTTPException(status_code=500, detail="Failed to find related videos")


@router.post("/mini-course", response_model=VideoResponse)
async def create_mini_course(
    request: CreateMiniCourseRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a mini-course from saved videos on a topic
    """
    try:
        if request.skill_level not in ["beginner", "intermediate", "advanced"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid skill level. Use: beginner, intermediate, or advanced"
            )
        
        course = await video_service.create_mini_course(
            topic=request.topic,
            skill_level=request.skill_level,
            max_videos=request.max_videos,
            db=db
        )
        
        return VideoResponse(
            success=True,
            data=course
        )
    except Exception as e:
        logger.error(f"Error creating mini-course: {e}")
        raise HTTPException(status_code=500, detail="Failed to create mini-course")


@router.get("/timeline")
async def get_video_timeline(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = Query(None, description="Filter by category"),
    platform: Optional[str] = Query(None, description="Filter by platform (youtube, twitter, instagram)"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get timeline of video items with filtering options
    """
    try:
        timeline = await video_service.get_video_timeline(
            limit=limit,
            offset=offset,
            category=category,
            platform=platform,
            db=db
        )
        
        return {
            "success": True,
            "data": timeline
        }
    except Exception as e:
        logger.error(f"Error getting video timeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video timeline")


@router.get("/check-url")
async def check_video_url(
    url: str = Query(..., description="URL to check"),
    current_user = Depends(get_current_user)
):
    """
    Check if a URL is a supported video and extract basic info
    """
    try:
        video_id, platform = video_service.extract_video_id(url)
        
        if not video_id:
            return {
                "success": False,
                "is_video": False,
                "message": "Not a supported video URL"
            }
        
        # Get basic metadata without saving
        metadata = await video_service.get_video_metadata(url, video_id, platform)
        
        return {
            "success": True,
            "is_video": True,
            "data": {
                "video_id": video_id,
                "platform": platform,
                "metadata": metadata
            }
        }
    except Exception as e:
        logger.error(f"Error checking video URL: {e}")
        return {
            "success": False,
            "is_video": False,
            "message": str(e)
        }


@router.post("/batch-process")
async def batch_process_videos(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process all unprocessed video items in the database
    """
    try:
        from sqlalchemy import and_, or_, select

        from app.models.item import Item

        # Find items that look like videos but haven't been processed
        query = select(Item).where(
            and_(
                or_(
                    Item.url.like('%youtube.com%'),
                    Item.url.like('%youtu.be%'),
                    Item.url.like('%twitter.com%status%'),
                    Item.url.like('%x.com%status%'),
                    Item.url.like('%instagram.com%')
                ),
                or_(
                    Item.type == None,
                    Item.type != 'video'
                )
            )
        ).limit(20)  # Process in batches
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        processed = []
        failed = []
        
        for item in items:
            try:
                video_id, platform = video_service.extract_video_id(item.url)
                if video_id:
                    result = await video_service.process_video_item(
                        item_id=str(item.id),
                        db=db
                    )
                    processed.append({
                        "item_id": str(item.id),
                        "title": item.title,
                        "platform": platform
                    })
            except Exception as e:
                failed.append({
                    "item_id": str(item.id),
                    "error": str(e)
                })
        
        return {
            "success": True,
            "data": {
                "processed_count": len(processed),
                "failed_count": len(failed),
                "processed": processed,
                "failed": failed
            }
        }
    except Exception as e:
        logger.error(f"Error batch processing videos: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch process videos")


@router.get("/mini-courses")
async def get_saved_mini_courses(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get previously created mini-courses
    """
    try:
        # For now, we'll generate popular topic suggestions
        # In a full implementation, you'd save and retrieve created courses
        
        # Get video counts by common topics
        query = text("""
            SELECT 
                LOWER(category) as topic,
                COUNT(*) as video_count
            FROM items
            WHERE 
                type = 'video'
                AND category IS NOT NULL
            GROUP BY LOWER(category)
            HAVING COUNT(*) >= 3
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        
        result = await db.execute(query)
        topics = result.all()
        
        suggested_courses = []
        for topic_row in topics:
            suggested_courses.append({
                "topic": topic_row.topic,
                "video_count": topic_row.video_count,
                "suggested_title": f"Learn {topic_row.topic.title()}",
                "can_create": True
            })
        
        return {
            "success": True,
            "data": {
                "saved_courses": [],  # Would retrieve saved courses here
                "suggested_courses": suggested_courses
            }
        }
    except Exception as e:
        logger.error(f"Error getting mini-courses: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mini-courses")


@router.get("/stats")
async def get_video_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get statistics about video content
    """
    try:
        from sqlalchemy import func, select

        from app.models.item import Item

        # Total video count
        total_query = select(func.count(Item.id)).where(Item.type == "video")
        total_result = await db.execute(total_query)
        total_videos = total_result.scalar() or 0
        
        # Videos by platform
        platform_query = text("""
            SELECT 
                metadata->'video'->>'platform' as platform,
                COUNT(*) as count
            FROM items
            WHERE type = 'video'
            GROUP BY metadata->'video'->>'platform'
        """)
        
        platform_result = await db.execute(platform_query)
        platforms = [
            {"platform": row.platform or "unknown", "count": row.count}
            for row in platform_result.all()
        ]
        
        # Videos with transcripts
        transcript_query = text("""
            SELECT COUNT(*) as count
            FROM items
            WHERE 
                type = 'video'
                AND (metadata->'video'->>'has_transcript')::boolean = true
        """)
        
        transcript_result = await db.execute(transcript_query)
        with_transcripts = transcript_result.scalar() or 0
        
        return {
            "success": True,
            "data": {
                "total_videos": total_videos,
                "videos_by_platform": platforms,
                "videos_with_transcripts": with_transcripts,
                "transcript_percentage": (with_transcripts / total_videos * 100) if total_videos > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting video stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video statistics")