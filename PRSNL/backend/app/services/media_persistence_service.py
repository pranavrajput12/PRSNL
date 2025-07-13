"""
Media Persistence Service for PRSNL Second Brain

This service handles saving and retrieving media processing results to/from the database.
Integrates with the media agents to provide persistent storage for all analysis results.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
from app.config import settings
from app.db.database import get_db_pool
from app.services.media_agents import MediaAgentResult

logger = logging.getLogger(__name__)


class MediaPersistenceService:
    """
    Service for persisting media processing results to the database
    """
    
    def __init__(self):
        self.logger = logger
    
    async def save_image_analysis(self, item_id: Optional[str], file_path: str, result: MediaAgentResult) -> str:
        """
        Save OCR image analysis results to database
        
        Args:
            item_id: Optional existing item ID to update
            file_path: Path to the processed image file
            result: Media agent processing result
        
        Returns:
            str: Item ID (created or updated)
        """
        try:
            async with get_db_pool().acquire() as conn:
                # Extract key data from result
                ocr_data = result.results.get("ocr_result", {})
                vision_data = result.results.get("vision_analysis", {})
                extracted_text = ocr_data.get("text", "")
                description = vision_data.get("description", "")
                tags = result.results.get("suggested_tags", [])
                
                if item_id:
                    # Update existing item
                    await conn.execute("""
                        UPDATE items SET
                            content = $2,
                            processed_content = $3,
                            metadata = jsonb_set(
                                COALESCE(metadata, '{}'),
                                '{image_analysis}',
                                $4::jsonb
                            ),
                            status = 'completed',
                            updated_at = NOW()
                        WHERE id = $1
                    """, uuid.UUID(item_id), extracted_text, description, json.dumps(result.results))
                    
                    # Update file record
                    await conn.execute("""
                        UPDATE files SET
                            extracted_text = $2,
                            processing_status = 'completed',
                            processing_metadata = $3,
                            updated_at = NOW()
                        WHERE file_path = $1
                    """, file_path, extracted_text, json.dumps({
                        "agent": result.agent_name,
                        "execution_time": result.execution_time,
                        "timestamp": result.timestamp.isoformat()
                    }))
                    
                    return item_id
                else:
                    # Create new item
                    new_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO items (
                            id, title, content, processed_content, type, status,
                            file_path, metadata, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                    """, uuid.UUID(new_id), f"Image Analysis: {file_path}", 
                         extracted_text, description, "image", "completed",
                         file_path, json.dumps(result.results))
                    
                    # Add tags
                    if tags:
                        await self._add_tags_to_item(conn, new_id, tags)
                    
                    return new_id
                    
        except Exception as e:
            self.logger.error(f"Failed to save image analysis: {e}")
            raise
    
    async def save_video_transcription(self, item_id: Optional[str], file_path: str, result: MediaAgentResult) -> str:
        """
        Save video transcription results to database
        
        Args:
            item_id: Optional existing item ID to update  
            file_path: Path to the processed video file
            result: Media agent processing result
        
        Returns:
            str: Item ID (created or updated)
        """
        try:
            async with get_db_pool().acquire() as conn:
                # Extract key data from result
                transcription_data = result.results.get("transcription_result", {})
                ai_summary = result.results.get("ai_summary", {})
                transcript = transcription_data.get("transcript", "")
                summary = ai_summary.get("summary", "")
                tags = result.results.get("suggested_tags", [])
                
                if item_id:
                    # Update existing item
                    await conn.execute("""
                        UPDATE items SET
                            transcription = $2,
                            summary = $3,
                            duration = $4,
                            metadata = jsonb_set(
                                COALESCE(metadata, '{}'),
                                '{video_analysis}',
                                $5::jsonb
                            ),
                            status = 'completed',
                            updated_at = NOW()
                        WHERE id = $1
                    """, uuid.UUID(item_id), transcript, summary,
                         transcription_data.get("duration", 0), json.dumps(result.results))
                    
                    return item_id
                else:
                    # Create new item
                    new_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO items (
                            id, title, transcription, summary, type, status,
                            file_path, duration, video_url, metadata, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
                    """, uuid.UUID(new_id), f"Video: {file_path}", transcript,
                         summary, "video", "completed", file_path,
                         transcription_data.get("duration", 0), file_path, json.dumps(result.results))
                    
                    # Add tags
                    if tags:
                        await self._add_tags_to_item(conn, new_id, tags)
                    
                    return new_id
                    
        except Exception as e:
            self.logger.error(f"Failed to save video transcription: {e}")
            raise
    
    async def save_audio_journal(self, item_id: Optional[str], journal_id: Optional[str], 
                                file_path: str, result: MediaAgentResult) -> Tuple[str, str]:
        """
        Save audio journal analysis results to database
        
        Args:
            item_id: Optional existing item ID to update
            journal_id: Optional existing journal ID to update
            file_path: Path to the processed audio file
            result: Media agent processing result
        
        Returns:
            Tuple[str, str]: (item_id, journal_id)
        """
        try:
            async with get_db_pool().acquire() as conn:
                # Extract key data from result
                transcription_data = result.results.get("transcription_result", {})
                emotion_analysis = result.results.get("emotion_analysis", {})
                insights = result.results.get("insights_extraction", {})
                transcript = transcription_data.get("transcript", "")
                mood_score = emotion_analysis.get("overall_mood_score", 0.5)
                dominant_emotion = emotion_analysis.get("dominant_emotion", "neutral")
                action_items = insights.get("action_items", [])
                
                # Handle audio journal record
                if journal_id:
                    # Update existing journal
                    await conn.execute("""
                        UPDATE audio_journals SET
                            transcription = $2,
                            mood_score = $3,
                            dominant_emotion = $4,
                            analysis_metadata = $5,
                            updated_at = NOW()
                        WHERE id = $1
                    """, uuid.UUID(journal_id), transcript, mood_score, dominant_emotion,
                         json.dumps(result.results))
                else:
                    # Create new journal
                    journal_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO audio_journals (
                            id, user_id, title, transcription, mood_score,
                            dominant_emotion, analysis_metadata, file_path, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                    """, uuid.UUID(journal_id), None, f"Audio Journal: {file_path}",
                         transcript, mood_score, dominant_emotion, json.dumps(result.results), file_path)
                
                # Handle item record  
                if item_id:
                    # Update existing item
                    await conn.execute("""
                        UPDATE items SET
                            transcription = $2,
                            summary = $3,
                            metadata = jsonb_set(
                                COALESCE(metadata, '{}'),
                                '{audio_journal}',
                                $4::jsonb
                            ),
                            status = 'completed',
                            updated_at = NOW()
                        WHERE id = $1
                    """, uuid.UUID(item_id), transcript, 
                         insights.get("reflection_summary", ""), json.dumps(result.results))
                else:
                    # Create new item
                    item_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO items (
                            id, title, transcription, summary, type, status,
                            file_path, metadata, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                    """, uuid.UUID(item_id), f"Audio Journal: {file_path}", transcript,
                         insights.get("reflection_summary", ""), "audio", "completed",
                         file_path, json.dumps(result.results))
                
                return item_id, journal_id
                    
        except Exception as e:
            self.logger.error(f"Failed to save audio journal: {e}")
            raise
    
    async def get_media_analysis(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve saved media analysis results for an item
        
        Args:
            item_id: Item ID to retrieve
        
        Returns:
            Dict containing all saved media analysis data or None if not found
        """
        try:
            async with get_db_pool().acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        i.id, i.title, i.content, i.processed_content, i.transcription,
                        i.summary, i.type, i.file_path, i.duration, i.metadata,
                        i.created_at, i.updated_at,
                        f.extracted_text, f.processing_status, f.processing_metadata
                    FROM items i
                    LEFT JOIN files f ON f.file_path = i.file_path
                    WHERE i.id = $1
                """, uuid.UUID(item_id))
                
                if not row:
                    return None
                
                return {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "content": row["content"],
                    "processed_content": row["processed_content"],
                    "transcription": row["transcription"],
                    "summary": row["summary"],
                    "type": row["type"],
                    "file_path": row["file_path"],
                    "duration": row["duration"],
                    "metadata": row["metadata"] or {},
                    "extracted_text": row["extracted_text"],
                    "processing_status": row["processing_status"],
                    "processing_metadata": row["processing_metadata"] or {},
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get media analysis: {e}")
            return None
    
    async def update_processing_status(self, file_path: str, status: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Update processing status for a file
        
        Args:
            file_path: Path to file being processed
            status: Processing status ('pending', 'processing', 'completed', 'failed')
            metadata: Optional processing metadata
        """
        try:
            async with get_db_pool().acquire() as conn:
                await conn.execute("""
                    UPDATE files SET
                        processing_status = $2,
                        processing_metadata = $3,
                        updated_at = NOW()
                    WHERE file_path = $1
                """, file_path, status, json.dumps(metadata) if metadata else None)
                
        except Exception as e:
            self.logger.error(f"Failed to update processing status: {e}")
    
    async def _add_tags_to_item(self, conn: asyncpg.Connection, item_id: str, tags: List[str]):
        """
        Add tags to an item (helper method)
        
        Args:
            conn: Database connection
            item_id: Item ID
            tags: List of tag names
        """
        for tag_name in tags:
            # Get or create tag
            tag_row = await conn.fetchrow("""
                INSERT INTO tags (name, created_at, updated_at)
                VALUES ($1, NOW(), NOW())
                ON CONFLICT (name) DO UPDATE SET updated_at = NOW()
                RETURNING id
            """, tag_name)
            
            # Link tag to item
            await conn.execute("""
                INSERT INTO item_tags (item_id, tag_id, created_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (item_id, tag_id) DO NOTHING
            """, uuid.UUID(item_id), tag_row["id"])


# Singleton instance
media_persistence_service = MediaPersistenceService()