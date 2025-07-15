"""
Media Processing Celery Tasks

Distributed tasks for audio/video processing, transcription, and media analysis
to handle CPU-intensive media operations without blocking the main application.
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pathlib import Path

from app.workers.celery_app import celery_app
from app.db.database import get_db_connection
from app.services.video_processor import VideoProcessor
# from app.services.whisper_azure_transcription import WhisperAzureTranscription
# from app.services.whisper_local_transcription import WhisperLocalTranscription
from app.services.hybrid_transcription import HybridTranscriptionService
from app.services.unified_ai_service import UnifiedAIService

logger = logging.getLogger(__name__)


@celery_app.task(name="media.transcribe_audio", bind=True, max_retries=3, time_limit=3600)
def transcribe_audio_task(self, audio_file_path: str, options: Dict[str, Any] = None):
    """
    Transcribe audio file using hybrid transcription approach.
    
    Args:
        audio_file_path: Path to audio file
        options: Transcription options (model, language, privacy_mode, etc.)
    
    Returns:
        Transcription results with text and metadata
    """
    try:
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _transcribe_audio_async(self.request.id, audio_file_path, options or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}", exc_info=True)
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=120 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _transcribe_audio_async(task_id: str, audio_file_path: str, options: Dict[str, Any]):
    """Async implementation of audio transcription"""
    
    try:
        await _send_progress_update(task_id, "audio", "transcription", 0, 4, "Starting audio transcription")
        
        # Verify audio file exists
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        file_info = {
            "path": audio_file_path,
            "size": os.path.getsize(audio_file_path),
            "extension": Path(audio_file_path).suffix.lower()
        }
        
        await _send_progress_update(task_id, "audio", "transcription", 1, 4, "Initializing transcription service")
        
        # Choose transcription service based on options
        privacy_mode = options.get("privacy_mode", False)
        preferred_model = options.get("model", "hybrid")
        
        if privacy_mode or preferred_model == "local":
            transcription_service = WhisperLocalTranscription()
        elif preferred_model == "azure":
            transcription_service = WhisperAzureTranscription()
        else:
            transcription_service = HybridTranscription()
        
        await _send_progress_update(task_id, "audio", "transcription", 2, 4, "Processing audio transcription")
        
        # Perform transcription
        transcription_result = await transcription_service.transcribe_audio(
            audio_file_path=audio_file_path,
            language=options.get("language", "auto"),
            model_size=options.get("model_size", "base"),
            enable_diarization=options.get("enable_diarization", False)
        )
        
        if not transcription_result.get("success", False):
            raise Exception(f"Transcription failed: {transcription_result.get('error')}")
        
        await _send_progress_update(task_id, "audio", "transcription", 3, 4, "Post-processing transcription")
        
        # Post-process transcription
        transcript_text = transcription_result.get("text", "")
        
        # Clean up and enhance transcript if requested
        if options.get("enhance_transcript", True) and transcript_text:
            ai_service = UnifiedAIService()
            
            enhanced_transcript = await ai_service.enhance_transcript(
                transcript=transcript_text,
                context=options.get("context", ""),
                fix_punctuation=options.get("fix_punctuation", True),
                fix_capitalization=options.get("fix_capitalization", True)
            )
            
            transcription_result["enhanced_text"] = enhanced_transcript
        
        await _send_progress_update(task_id, "audio", "transcription", 4, 4, "Transcription completed")
        
        return {
            "status": "completed",
            "transcription_result": transcription_result,
            "file_info": file_info,
            "processing_options": options,
            "transcribed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Audio transcription async failed: {e}", exc_info=True)
        await _send_progress_update(task_id, "audio", "transcription", 0, 4, f"Transcription failed: {str(e)}")
        raise


@celery_app.task(name="media.process_video", bind=True, max_retries=2, time_limit=7200)
def process_video_task(self, video_file_path: str, options: Dict[str, Any] = None):
    """
    Process video file: extract metadata, audio, and optionally transcribe.
    
    Args:
        video_file_path: Path to video file
        options: Processing options (extract_audio, transcribe, extract_frames, etc.)
    
    Returns:
        Video processing results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _process_video_async(self.request.id, video_file_path, options or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Video processing failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _process_video_async(task_id: str, video_file_path: str, options: Dict[str, Any]):
    """Async implementation of video processing"""
    
    try:
        await _send_progress_update(task_id, "video", "processing", 0, 5, "Starting video processing")
        
        if not os.path.exists(video_file_path):
            raise FileNotFoundError(f"Video file not found: {video_file_path}")
        
        video_processor = VideoProcessor()
        processing_results = {}
        
        # 1. Extract video metadata
        await _send_progress_update(task_id, "video", "processing", 1, 5, "Extracting video metadata")
        
        metadata = await video_processor.extract_video_metadata(video_file_path)
        processing_results["metadata"] = metadata
        
        # 2. Extract audio if requested
        audio_file_path = None
        if options.get("extract_audio", True):
            await _send_progress_update(task_id, "video", "processing", 2, 5, "Extracting audio track")
            
            audio_extraction = await video_processor.extract_audio(
                video_file_path=video_file_path,
                output_format=options.get("audio_format", "wav")
            )
            
            if audio_extraction.get("success"):
                audio_file_path = audio_extraction.get("audio_file_path")
                processing_results["audio_extraction"] = audio_extraction
        
        # 3. Transcribe audio if requested and available
        if options.get("transcribe_audio", True) and audio_file_path:
            await _send_progress_update(task_id, "video", "processing", 3, 5, "Transcribing audio content")
            
            # Use hybrid transcription for best results
            transcription_service = HybridTranscription()
            transcription_result = await transcription_service.transcribe_audio(
                audio_file_path=audio_file_path,
                language=options.get("language", "auto"),
                enable_diarization=options.get("enable_diarization", False)
            )
            
            processing_results["transcription"] = transcription_result
        
        # 4. Extract key frames if requested
        if options.get("extract_frames", False):
            await _send_progress_update(task_id, "video", "processing", 4, 5, "Extracting key frames")
            
            frame_extraction = await video_processor.extract_key_frames(
                video_file_path=video_file_path,
                frame_count=options.get("frame_count", 10)
            )
            
            processing_results["frame_extraction"] = frame_extraction
        
        # 5. Generate AI insights if transcription is available
        if options.get("generate_insights", True) and processing_results.get("transcription", {}).get("text"):
            await _send_progress_update(task_id, "video", "processing", 5, 5, "Generating AI insights")
            
            ai_service = UnifiedAIService()
            
            video_insights = await ai_service.analyze_video_content(
                transcript=processing_results["transcription"]["text"],
                metadata=metadata,
                context=options.get("context", "")
            )
            
            processing_results["ai_insights"] = video_insights
        
        await _send_progress_update(task_id, "video", "processing", 5, 5, "Video processing completed")
        
        return {
            "status": "completed",
            "video_file_path": video_file_path,
            "processing_results": processing_results,
            "processing_options": options,
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Video processing async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="media.enhance_video_with_ai", bind=True, max_retries=3)
def enhance_video_with_ai_task(self, video_id: str, transcript: str, metadata: Dict[str, Any] = None):
    """
    Enhance video content with AI analysis and insights.
    
    Args:
        video_id: UUID of the video record
        transcript: Video transcript text
        metadata: Video metadata
    
    Returns:
        AI enhancement results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _enhance_video_with_ai_async(self.request.id, video_id, transcript, metadata or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Video AI enhancement failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _enhance_video_with_ai_async(task_id: str, video_id: str, transcript: str, metadata: Dict[str, Any]):
    """Async implementation of video AI enhancement"""
    
    try:
        await _send_progress_update(task_id, video_id, "video_ai_enhancement", 0, 4, "Starting AI enhancement")
        
        if not transcript.strip():
            return {
                "status": "skipped",
                "message": "No transcript available for AI enhancement",
                "video_id": video_id
            }
        
        ai_service = UnifiedAIService()
        enhancement_results = {}
        
        # 1. Generate summary
        await _send_progress_update(task_id, video_id, "video_ai_enhancement", 1, 4, "Generating video summary")
        
        summary = await ai_service.generate_video_summary(
            transcript=transcript,
            duration=metadata.get("duration", 0),
            max_length=300
        )
        enhancement_results["summary"] = summary
        
        # 2. Extract key topics and concepts
        await _send_progress_update(task_id, video_id, "video_ai_enhancement", 2, 4, "Extracting key topics")
        
        topics = await ai_service.extract_video_topics(
            transcript=transcript,
            metadata=metadata
        )
        enhancement_results["topics"] = topics
        
        # 3. Generate learning insights
        await _send_progress_update(task_id, video_id, "video_ai_enhancement", 3, 4, "Generating learning insights")
        
        learning_insights = await ai_service.generate_learning_insights(
            content=transcript,
            content_type="video",
            metadata=metadata
        )
        enhancement_results["learning_insights"] = learning_insights
        
        # 4. Store results in database
        await _send_progress_update(task_id, video_id, "video_ai_enhancement", 4, 4, "Storing enhancement results")
        
        async with get_db_connection() as db:
            await db.execute("""
                UPDATE items 
                SET 
                    summary = $2,
                    ai_analysis = $3,
                    processed_content = $4,
                    last_processed_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, 
                UUID(video_id),
                summary,
                enhancement_results,
                {"transcript": transcript, "ai_enhancement": enhancement_results}
            )
            
            # Store topics as tags
            if topics:
                for topic in topics:
                    await db.execute("""
                        INSERT INTO item_tags (item_id, tag, confidence_score, tag_type)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT DO NOTHING
                    """, 
                        UUID(video_id), 
                        topic.get("name", topic), 
                        topic.get("confidence", 0.8) if isinstance(topic, dict) else 0.8,
                        "ai_generated"
                    )
        
        return {
            "status": "completed",
            "video_id": video_id,
            "enhancement_results": enhancement_results,
            "enhanced_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Video AI enhancement async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="media.batch_transcribe_videos", bind=True)
def batch_transcribe_videos_task(self, video_batch: List[Dict[str, Any]], transcription_options: Dict[str, Any] = None):
    """
    Transcribe multiple videos in batch with resource management.
    
    Args:
        video_batch: List of video info dicts with id, path, metadata
        transcription_options: Global transcription options
    
    Returns:
        Batch transcription results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _batch_transcribe_videos_async(self.request.id, video_batch, transcription_options or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Batch video transcription failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _batch_transcribe_videos_async(task_id: str, video_batch: List[Dict[str, Any]], transcription_options: Dict[str, Any]):
    """Async implementation of batch video transcription"""
    
    try:
        await _send_progress_update(
            task_id, "batch", "video_transcription",
            0, len(video_batch), f"Starting batch transcription for {len(video_batch)} videos"
        )
        
        results = []
        
        # Process videos sequentially to manage resource usage
        # Video transcription is CPU/GPU intensive, so limit concurrency
        for i, video_info in enumerate(video_batch):
            try:
                await _send_progress_update(
                    task_id, "batch", "video_transcription",
                    i, len(video_batch), f"Processing video {i + 1}/{len(video_batch)}"
                )
                
                # Process individual video
                result = await _process_video_async(
                    f"{task_id}_video_{video_info['id']}",
                    video_info["path"],
                    {**transcription_options, **video_info.get("options", {})}
                )
                
                results.append({
                    "video_id": video_info["id"],
                    "status": "success",
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Failed to process video {video_info['id']}: {e}")
                results.append({
                    "video_id": video_info["id"],
                    "status": "failed",
                    "error": str(e)
                })
        
        # Count success/failure
        successful_count = len([r for r in results if r.get("status") == "success"])
        failed_count = len(results) - successful_count
        
        await _send_progress_update(
            task_id, "batch", "video_transcription",
            len(video_batch), len(video_batch),
            f"Batch transcription completed: {successful_count} success, {failed_count} failed"
        )
        
        return {
            "status": "completed",
            "total_videos": len(video_batch),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch video transcription async failed: {e}", exc_info=True)
        raise


async def _send_progress_update(
    task_id: str,
    entity_id: str,
    progress_type: str,
    current_value: int,
    total_value: Optional[int] = None,
    message: Optional[str] = None
):
    """Send progress update to database and WebSocket"""
    try:
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO task_progress (
                    task_id, entity_id, progress_type, current_value,
                    total_value, message, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
                ON CONFLICT (task_id) DO UPDATE SET
                    current_value = EXCLUDED.current_value,
                    total_value = EXCLUDED.total_value,
                    message = EXCLUDED.message,
                    updated_at = CURRENT_TIMESTAMP
            """,
                task_id, entity_id, progress_type, current_value,
                total_value, message
            )
            
        # TODO: Send WebSocket update for real-time progress
        logger.info(f"Progress update: {task_id} - {progress_type} - {current_value}/{total_value} - {message}")
        
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")