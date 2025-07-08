"""
Video Streaming Service for PRSNL

This service handles:
- Streaming videos from external platforms (YouTube, Instagram, Twitter)
- Extracting transcripts and metadata
- AI-powered video analysis
- Automatic mini-course generation
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, parse_qs
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from youtube_transcript_api import YouTubeTranscriptApi
import httpx

from app.models.schemas import Item
from app.config import settings
from app.services.llm_processor import LLMProcessor
from app.services.embedding_service import EmbeddingService
from app.db.database import get_db

logger = logging.getLogger(__name__)
# settings already imported above


class VideoStreamingService:
    def __init__(self):
        self.llm_processor = LLMProcessor()
        self.embedding_service = EmbeddingService()
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Platform patterns
        self.PLATFORM_PATTERNS = {
            "youtube": [
                r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
                r"youtu\.be/([a-zA-Z0-9_-]+)",
                r"youtube\.com/embed/([a-zA-Z0-9_-]+)"
            ],
            "twitter": [
                r"twitter\.com/\w+/status/(\d+)",
                r"x\.com/\w+/status/(\d+)"
            ],
            "instagram": [
                r"instagram\.com/p/([a-zA-Z0-9_-]+)",
                r"instagram\.com/reel/([a-zA-Z0-9_-]+)",
                r"instagram\.com/tv/([a-zA-Z0-9_-]+)"
            ]
        }
    
    def extract_video_id(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract video ID and platform from URL
        
        Returns:
            Tuple of (video_id, platform) or (None, None)
        """
        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1), platform
        return None, None
    
    async def get_video_metadata(
        self,
        url: str,
        video_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        Get video metadata from platform
        
        Args:
            url: Original video URL
            video_id: Extracted video ID
            platform: Video platform
            
        Returns:
            Video metadata dictionary
        """
        metadata = {
            "video_id": video_id,
            "platform": platform,
            "url": url,
            "embeddable": True
        }
        
        try:
            if platform == "youtube":
                # Get YouTube metadata via oEmbed
                oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
                response = await self.client.get(oembed_url)
                
                if response.status_code == 200:
                    data = response.json()
                    metadata.update({
                        "title": data.get("title", ""),
                        "author": data.get("author_name", ""),
                        "thumbnail": data.get("thumbnail_url", ""),
                        "duration": None,  # oEmbed doesn't provide duration
                        "embed_html": data.get("html", ""),
                        "width": data.get("width", 560),
                        "height": data.get("height", 315)
                    })
                    
                    # Extract high-res thumbnail
                    if metadata["thumbnail"]:
                        metadata["thumbnail_hq"] = metadata["thumbnail"].replace("hqdefault", "maxresdefault")
                
            elif platform == "twitter":
                # Twitter/X video metadata is more complex, using basic info for now
                metadata.update({
                    "title": f"Twitter Video {video_id}",
                    "embed_url": f"https://platform.twitter.com/embed/Tweet.html?id={video_id}"
                })
                
            elif platform == "instagram":
                # Instagram requires authentication for full API, using basic info
                metadata.update({
                    "title": f"Instagram Video {video_id}",
                    "embed_url": f"https://www.instagram.com/p/{video_id}/embed/"
                })
                
        except Exception as e:
            logger.error(f"Error fetching video metadata: {e}")
        
        return metadata
    
    async def get_video_transcript(
        self,
        video_id: str,
        platform: str
    ) -> Optional[str]:
        """
        Get video transcript if available
        
        Args:
            video_id: Video ID
            platform: Video platform
            
        Returns:
            Transcript text or None
        """
        if platform != "youtube":
            # Currently only YouTube provides easy transcript access
            return None
        
        try:
            # Get available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get transcript in order of preference
            transcript = None
            
            # First try manually created transcripts
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
            except:
                # Fall back to auto-generated
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except:
                    # Try any available language
                    for t in transcript_list:
                        transcript = t
                        break
            
            if transcript:
                # Fetch the actual transcript
                transcript_data = transcript.fetch()
                
                # Combine all text with timestamps
                full_text = ""
                for entry in transcript_data:
                    timestamp = str(timedelta(seconds=int(entry['start'])))
                    text = entry['text'].strip()
                    full_text += f"[{timestamp}] {text}\n"
                
                return full_text
                
        except Exception as e:
            logger.warning(f"Could not fetch transcript for {video_id}: {e}")
            return None
    
    async def analyze_video_content(
        self,
        metadata: Dict[str, Any],
        transcript: Optional[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze video content using AI
        
        Args:
            metadata: Video metadata
            transcript: Video transcript (if available)
            db: Database session
            
        Returns:
            Analysis results
        """
        analysis = {
            "has_transcript": transcript is not None,
            "summary": "",
            "key_topics": [],
            "difficulty_level": "intermediate",
            "learning_objectives": [],
            "chapters": [],
            "key_moments": [],
            "estimated_learning_time": 0
        }
        
        if not transcript and not metadata.get("title"):
            return analysis
        
        # Prepare content for analysis
        content = f"Video Title: {metadata.get('title', 'Unknown')}\n"
        content += f"Author: {metadata.get('author', 'Unknown')}\n\n"
        
        if transcript:
            # Limit transcript length for API
            content += f"Transcript:\n{transcript[:8000]}"
        
        # Use AI to analyze the video
        prompt = f"""
        Analyze this video content and extract structured learning information.
        
        {content}
        
        Provide the following in JSON format:
        {{
            "summary": "2-3 sentence summary of the video content",
            "key_topics": ["topic1", "topic2", "topic3"],
            "difficulty_level": "beginner/intermediate/advanced",
            "learning_objectives": ["what viewer will learn 1", "what viewer will learn 2"],
            "chapters": [
                {{"timestamp": "00:00", "title": "Introduction", "description": "Brief description"}},
                {{"timestamp": "02:30", "title": "Main Concept", "description": "Brief description"}}
            ],
            "key_moments": [
                {{"timestamp": "01:15", "description": "Important insight or tip"}}
            ],
            "estimated_learning_time": 15
        }}
        
        Focus on educational value and practical takeaways.
        """
        
        response = await self.llm_processor.process_with_llm(prompt, mode="extract")
        
        try:
            ai_analysis = json.loads(response)
            analysis.update(ai_analysis)
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI video analysis")
            # Fallback to basic analysis
            if transcript:
                # Extract summary from first few lines
                lines = transcript.split('\n')[:10]
                analysis["summary"] = ' '.join(lines)[:200] + "..."
        
        return analysis
    
    async def process_video_item(
        self,
        item_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process a video item with full analysis
        
        Args:
            item_id: Item ID to process
            db: Database session
            
        Returns:
            Processing results
        """
        try:
            # Get the item
            result = await db.execute(
                select(Item).where(Item.id == item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item or not item.url:
                raise ValueError("Item not found or has no URL")
            
            # Extract video ID and platform
            video_id, platform = self.extract_video_id(item.url)
            
            if not video_id:
                raise ValueError("Not a supported video URL")
            
            # Get video metadata
            metadata = await self.get_video_metadata(item.url, video_id, platform)
            
            # Get transcript if available
            transcript = await self.get_video_transcript(video_id, platform)
            
            # Analyze video content
            analysis = await self.analyze_video_content(metadata, transcript, db)
            
            # Update item with video data
            if not item.metadata:
                item.metadata = {}
            
            item.metadata["video"] = {
                **metadata,
                **analysis,
                "processed_at": datetime.utcnow().isoformat()
            }
            
            # Update item properties
            if metadata.get("title") and not item.title:
                item.title = metadata["title"]
            
            if metadata.get("thumbnail"):
                item.thumbnail_url = metadata["thumbnail"]
            
            if analysis.get("summary"):
                item.summary = analysis["summary"]
            
            # Set item type
            item.item_type = "video"
            
            # Generate embedding for video content
            embed_text = f"{item.title} {analysis.get('summary', '')} {' '.join(analysis.get('key_topics', []))}"
            if transcript:
                embed_text += f" {transcript[:1000]}"
            
            embedding = await self.embedding_service.generate_embedding(embed_text)
            if embedding:
                item.embedding = embedding
            
            await db.commit()
            
            return {
                "item_id": item_id,
                "video_id": video_id,
                "platform": platform,
                "has_transcript": analysis["has_transcript"],
                "metadata": metadata,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error processing video item {item_id}: {e}")
            raise
    
    async def find_related_videos(
        self,
        item_id: str,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find related videos using embeddings
        
        Args:
            item_id: Source video item ID
            limit: Maximum number of related videos
            db: Database session
            
        Returns:
            List of related videos
        """
        try:
            # Get similar items that are videos
            similar_items = await self.embedding_service.find_similar(
                item_id=item_id,
                limit=limit * 2,
                db=db
            )
            
            related_videos = []
            
            for similar in similar_items:
                if similar["item_id"] == item_id:
                    continue
                
                # Get the item
                result = await db.execute(
                    select(Item).where(Item.id == similar["item_id"])
                )
                item = result.scalar_one_or_none()
                
                if item and item.item_type == "video":
                    video_data = item.metadata.get("video", {}) if item.metadata else {}
                    
                    related_videos.append({
                        "item_id": str(item.id),
                        "title": item.title,
                        "url": item.url,
                        "platform": video_data.get("platform"),
                        "thumbnail": video_data.get("thumbnail"),
                        "duration": video_data.get("duration"),
                        "similarity": similar["similarity"],
                        "summary": video_data.get("summary", item.summary)
                    })
            
            return related_videos[:limit]
            
        except Exception as e:
            logger.error(f"Error finding related videos: {e}")
            raise
    
    async def create_mini_course(
        self,
        topic: str,
        db: AsyncSession,
        skill_level: str = "beginner",
        max_videos: int = 10
    ) -> Dict[str, Any]:
        """
        Create a mini-course from saved videos on a topic
        
        Args:
            topic: Course topic
            skill_level: Target skill level
            max_videos: Maximum videos to include
            db: Database session
            
        Returns:
            Mini-course structure
        """
        try:
            # Search for videos related to the topic
            query = text("""
                SELECT i.*, ts_rank(search_vector, plainto_tsquery(:topic)) as relevance
                FROM items i
                WHERE 
                    i.item_type = 'video'
                    AND search_vector @@ plainto_tsquery(:topic)
                ORDER BY relevance DESC
                LIMIT :limit
            """)
            
            result = await db.execute(
                query,
                {"topic": topic, "limit": max_videos * 2}
            )
            
            videos = result.fetchall()
            
            if not videos:
                return {
                    "topic": topic,
                    "video_count": 0,
                    "message": "No videos found for this topic"
                }
            
            # Prepare video information for course creation
            video_info = []
            for video in videos:
                video_metadata = video.metadata.get("video", {}) if video.metadata else {}
                video_info.append({
                    "id": str(video.id),
                    "title": video.title,
                    "summary": video_metadata.get("summary", video.summary),
                    "difficulty": video_metadata.get("difficulty_level", "intermediate"),
                    "topics": video_metadata.get("key_topics", []),
                    "duration": video_metadata.get("duration"),
                    "platform": video_metadata.get("platform")
                })
            
            # Use AI to create course structure
            prompt = f"""
            Create a mini-course on "{topic}" for {skill_level} level learners using these videos:
            
            {json.dumps(video_info, indent=2)}
            
            Structure the course with:
            1. Course title and description
            2. Learning objectives
            3. Ordered video sequence with rationale
            4. Estimated total time
            5. Prerequisites
            
            Return JSON:
            {{
                "title": "Course title",
                "description": "Course description",
                "learning_objectives": ["objective1", "objective2"],
                "prerequisites": ["prereq1", "prereq2"],
                "total_duration": "X hours Y minutes",
                "modules": [
                    {{
                        "order": 1,
                        "video_id": "video_id",
                        "title": "Module title",
                        "why_this_order": "Explanation",
                        "key_takeaways": ["takeaway1", "takeaway2"]
                    }}
                ]
            }}
            
            Include only the most relevant videos (max {max_videos}).
            """
            
            response = await self.llm_processor.process_with_llm(prompt, mode="extract")
            
            try:
                course_structure = json.loads(response)
                
                # Enrich with full video details
                enriched_modules = []
                for module in course_structure.get("modules", []):
                    video = next((v for v in videos if str(v.id) == module["video_id"]), None)
                    if video:
                        video_metadata = video.metadata.get("video", {}) if video.metadata else {}
                        enriched_modules.append({
                            **module,
                            "video_details": {
                                "url": video.url,
                                "thumbnail": video_metadata.get("thumbnail"),
                                "platform": video_metadata.get("platform"),
                                "has_transcript": video_metadata.get("has_transcript", False)
                            }
                        })
                
                course_structure["modules"] = enriched_modules
                course_structure["topic"] = topic
                course_structure["skill_level"] = skill_level
                course_structure["created_at"] = datetime.utcnow().isoformat()
                
                return course_structure
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI course structure")
                # Fallback to simple ordering
                return {
                    "topic": topic,
                    "title": f"Learn {topic}",
                    "description": f"A collection of videos about {topic}",
                    "modules": [
                        {
                            "order": idx + 1,
                            "video_id": str(video.id),
                            "title": video.title,
                            "video_details": {
                                "url": video.url,
                                "platform": video.metadata.get("video", {}).get("platform") if video.metadata else None
                            }
                        }
                        for idx, video in enumerate(videos[:max_videos])
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error creating mini-course: {e}")
            raise
    
    async def get_video_timeline(
        self,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
        platform: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Get timeline of video items
        
        Args:
            limit: Maximum items to return
            offset: Pagination offset
            category: Filter by category
            platform: Filter by platform
            db: Database session
            
        Returns:
            Video timeline data
        """
        try:
            # Build query
            query = select(Item).where(Item.item_type == "video")
            
            if category:
                query = query.where(Item.category == category)
            
            if platform:
                # Filter by platform in metadata
                query = query.where(
                    Item.metadata["video"]["platform"].astext == platform
                )
            
            # Order by created date
            query = query.order_by(Item.created_at.desc())
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total_count = total_result.scalar() or 0
            
            # Get paginated results
            query = query.limit(limit).offset(offset)
            result = await db.execute(query)
            videos = result.scalars().all()
            
            # Format video data
            video_items = []
            for video in videos:
                video_metadata = video.metadata.get("video", {}) if video.metadata else {}
                
                video_items.append({
                    "id": str(video.id),
                    "title": video.title,
                    "url": video.url,
                    "platform": video_metadata.get("platform"),
                    "thumbnail": video_metadata.get("thumbnail"),
                    "duration": video_metadata.get("duration"),
                    "summary": video_metadata.get("summary", video.summary),
                    "has_transcript": video_metadata.get("has_transcript", False),
                    "key_topics": video_metadata.get("key_topics", []),
                    "created_at": video.created_at.isoformat() if video.created_at else None,
                    "category": video.category
                })
            
            return {
                "videos": video_items,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error getting video timeline: {e}")
            raise