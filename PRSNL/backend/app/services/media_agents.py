"""
Media Processing Agents for PRSNL Second Brain

This module implements specialized agents for processing different media types:
- OCR Image Analysis Agent: Extracts text, analyzes context, generates tags
- Video Transcription Agent: Transcribes videos, creates summaries  
- Audio Journal Agent: Processes audio journals with advanced analysis

Integrates with the existing Crawl.ai multi-agent system and media processing infrastructure.
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from app.config import settings
from app.db.database import get_db_pool
try:
    from app.services.vision_processor import vision_processor
    VISION_PROCESSOR_AVAILABLE = True
except ImportError:
    VISION_PROCESSOR_AVAILABLE = False
    vision_processor = None

try:
    from app.services.whisper_cpp_transcription import whisper_cpp_service
    WHISPER_CPP_AVAILABLE = True
except ImportError:
    WHISPER_CPP_AVAILABLE = False
    whisper_cpp_service = None
from app.services.unified_ai_service import unified_ai_service
from app.services.cache import cache_service, CacheKeys
from app.services.embedding_manager import embedding_manager
from app.services.ner_service import ner_service

logger = logging.getLogger(__name__)


class MediaAgentResult(BaseModel):
    """Result from a media processing agent"""
    agent_name: str
    media_type: str
    status: str = "completed"
    results: Dict[str, Any]
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    

class OCRImageAnalysisAgent:
    """
    OCR Image Analysis Agent
    
    Processes uploaded images through OCR, contextualizes content, and generates tags.
    Uses existing vision_processor with Azure OpenAI GPT-4V and Tesseract fallback.
    """
    
    def __init__(self):
        self.name = "OCR Image Analysis Agent"
        self.description = "Extracts text from images, analyzes context, and generates searchable tags"
        self.vision_processor = vision_processor
        self.ai_service = unified_ai_service
        self.vision_available = VISION_PROCESSOR_AVAILABLE
        
    async def execute(self, task_data: Dict[str, Any]) -> MediaAgentResult:
        """
        Execute OCR image analysis workflow
        
        Args:
            task_data: Dictionary containing:
                - file_path: Path to image file
                - item_id: Optional item ID for database linking
                - enhance_analysis: Whether to run enhanced AI analysis
                
        Returns:
            MediaAgentResult with OCR text, description, objects, and tags
        """
        start_time = time.time()
        
        try:
            file_path = task_data.get("file_path")
            item_id = task_data.get("item_id")
            enhance_analysis = task_data.get("enhance_analysis", True)
            
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"Image file not found: {file_path}")
            
            logger.info(f"🖼️ Processing image: {file_path}")
            
            # Step 1: Run OCR and vision analysis
            if not self.vision_available:
                raise ValueError("Vision processor not available. Check OCR dependencies.")
            
            vision_result = await self.vision_processor.process_image(file_path)
            
            # Step 2: Enhanced AI contextualization if requested
            enhanced_context = {}
            if enhance_analysis and vision_result.get("text"):
                enhanced_context = await self._enhance_context_analysis(
                    vision_result, file_path
                )
            
            # Step 3: Generate knowledge base connections
            connections = await self._find_knowledge_connections(
                vision_result, item_id
            )
            
            # Step 4: Create multimodal embeddings and enhanced tags
            multimodal_enhancements = {}
            if item_id:
                try:
                    # Create image embedding for visual similarity search
                    image_embedding = await embedding_manager.create_image_embedding(
                        item_id, image_path=file_path
                    )
                    
                    # Create multimodal embedding if we have text content
                    text_content = vision_result.get("text", "")
                    if text_content:
                        multimodal_embedding = await embedding_manager.create_multimodal_embedding(
                            item_id,
                            text=text_content,
                            image_path=file_path
                        )
                        
                        # Enhance tags with NER from extracted text
                        entities = await ner_service.extract_entities(text_content)
                        current_tags = vision_result.get("tags", [])
                        enhanced_tags = await ner_service.enhance_tags(
                            current_tags, entities, max_new_tags=5
                        )
                        
                        multimodal_enhancements = {
                            "image_embedding_created": bool(image_embedding),
                            "multimodal_embedding_created": bool(multimodal_embedding),
                            "enhanced_tags": enhanced_tags,
                            "entities_extracted": entities.get("summary", {}),
                            "ner_technical_content": entities.get("summary", {}).get("has_technical_content", False)
                        }
                    else:
                        multimodal_enhancements = {
                            "image_embedding_created": bool(image_embedding),
                            "multimodal_embedding_created": False,
                            "enhanced_tags": vision_result.get("tags", []),
                            "entities_extracted": {},
                            "ner_technical_content": False
                        }
                except Exception as e:
                    logger.warning(f"Multimodal enhancement failed for {item_id}: {e}")
                    multimodal_enhancements = {"error": str(e)}
            
            # Step 5: Create final analysis result
            analysis_result = {
                "ocr_text": vision_result.get("text", ""),
                "description": vision_result.get("description", ""),
                "detected_objects": vision_result.get("objects", []),
                "generated_tags": vision_result.get("tags", []),
                "vision_provider": vision_result.get("provider", "unknown"),
                "enhanced_context": enhanced_context,
                "knowledge_connections": connections,
                "multimodal_enhancements": multimodal_enhancements,
                "file_info": {
                    "path": file_path,
                    "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    "format": Path(file_path).suffix.lower()
                },
                "quality_metrics": {
                    "text_length": len(vision_result.get("text", "")),
                    "object_count": len(vision_result.get("objects", [])),
                    "tag_count": len(vision_result.get("tags", [])),
                    "has_enhanced_analysis": bool(enhanced_context),
                    "has_multimodal_embeddings": multimodal_enhancements.get("multimodal_embedding_created", False)
                }
            }
            
            execution_time = time.time() - start_time
            
            logger.info(f"✅ Image analysis completed in {execution_time:.2f}s")
            
            return MediaAgentResult(
                agent_name=self.name,
                media_type="image",
                status="completed",
                results=analysis_result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ OCR Image Analysis failed: {e}")
            
            return MediaAgentResult(
                agent_name=self.name,
                media_type="image", 
                status="failed",
                results={"error": str(e)},
                execution_time=execution_time
            )
    
    async def _enhance_context_analysis(
        self, 
        vision_result: Dict[str, Any], 
        file_path: str
    ) -> Dict[str, Any]:
        """
        Enhanced AI analysis for deeper context understanding
        """
        try:
            # Prepare enhanced analysis prompt
            analysis_prompt = f"""
            Analyze this image content for deeper context and knowledge connections:
            
            OCR Text: {vision_result.get('text', 'No text detected')}
            Description: {vision_result.get('description', 'No description')}
            Objects: {', '.join(vision_result.get('objects', []))}
            
            Provide enhanced analysis focusing on:
            1. KNOWLEDGE DOMAIN: What field/subject does this relate to?
            2. CONTENT TYPE: Is this documentation, code, diagram, notes, etc.?
            3. KEY CONCEPTS: Extract 3-5 key concepts or technical terms
            4. LEARNING VALUE: What can someone learn from this content?
            5. SEARCHABLE KEYWORDS: Generate 5-10 specific keywords for findability
            6. RELATED TOPICS: What other topics might this connect to?
            
            Format as JSON with these exact keys: knowledge_domain, content_type, key_concepts, learning_value, searchable_keywords, related_topics
            """
            
            # Get enhanced analysis from AI
            enhanced_result = await self.ai_service.complete(
                prompt=analysis_prompt,
                system_prompt="You are an expert knowledge analyst. Provide structured analysis in valid JSON format.",
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                temperature=0.3
            )
            
            # Parse JSON response
            try:
                enhanced_data = json.loads(enhanced_result)
                return enhanced_data
            except json.JSONDecodeError:
                # Fallback to basic analysis if JSON parsing fails
                return {
                    "knowledge_domain": "general",
                    "content_type": "unknown",
                    "key_concepts": vision_result.get("tags", [])[:5],
                    "learning_value": "Content extracted from image",
                    "searchable_keywords": vision_result.get("tags", []),
                    "related_topics": []
                }
                
        except Exception as e:
            logger.error(f"Enhanced context analysis failed: {e}")
            return {}
    
    async def _find_knowledge_connections(
        self, 
        vision_result: Dict[str, Any], 
        item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find connections to existing knowledge base items
        """
        try:
            # Use extracted text and tags to find similar items
            search_text = vision_result.get("text", "")
            tags = vision_result.get("tags", [])
            
            if not search_text and not tags:
                return {"related_items": [], "connection_count": 0}
            
            # Create search query combining text and tags
            search_query = f"{search_text} {' '.join(tags)}"[:500]  # Limit length
            
            # For now, return a placeholder structure
            # In production, this would query the vector database for similar items
            connections = {
                "related_items": [],
                "connection_count": 0,
                "search_query": search_query,
                "connection_method": "semantic_search"
            }
            
            return connections
            
        except Exception as e:
            logger.error(f"Knowledge connection search failed: {e}")
            return {"related_items": [], "connection_count": 0}


class VideoTranscriptionAgent:
    """
    Video Transcription Agent
    
    Processes videos using Whisper CPP for transcription, creates AI-powered summaries,
    and generates contextual tags. Handles audio extraction from video files.
    """
    
    def __init__(self):
        self.name = "Video Transcription Agent"
        self.description = "Transcribes videos using Whisper CPP and creates intelligent summaries"
        self.whisper_service = whisper_cpp_service
        self.ai_service = unified_ai_service
        self.whisper_available = WHISPER_CPP_AVAILABLE
        
    async def execute(self, task_data: Dict[str, Any]) -> MediaAgentResult:
        """
        Execute video transcription workflow
        
        Args:
            task_data: Dictionary containing:
                - file_path: Path to video file
                - item_id: Optional item ID for database linking
                - model_name: Whisper model to use (default: "base")
                - language: Language code (default: "en")
                - create_summary: Whether to create AI summary
                
        Returns:
            MediaAgentResult with transcription, summary, and metadata
        """
        start_time = time.time()
        
        try:
            file_path = task_data.get("file_path")
            item_id = task_data.get("item_id")
            model_name = task_data.get("model_name", "base")
            language = task_data.get("language", "en")
            create_summary = task_data.get("create_summary", True)
            
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"Video file not found: {file_path}")
            
            if not self.whisper_available:
                raise ValueError("Whisper CPP not available. Check audio transcription dependencies.")
            
            logger.info(f"🎥 Processing video: {file_path}")
            
            # Step 1: Extract audio from video
            audio_path = await self._extract_audio_from_video(file_path)
            
            try:
                # Step 2: Transcribe audio using Whisper CPP
                transcription_result = await self.whisper_service.transcribe_audio(
                    audio_path=audio_path,
                    model_name=model_name,
                    language=language,
                    word_timestamps=True
                )
                
                if not transcription_result:
                    raise Exception("Whisper transcription failed")
                
                # Step 3: Create AI-powered summary and analysis
                summary_analysis = {}
                if create_summary and transcription_result.get("text"):
                    summary_analysis = await self._create_summary_and_analysis(
                        transcription_result["text"], file_path
                    )
                
                # Step 4: Generate video metadata
                video_metadata = await self._extract_video_metadata(file_path)
                
                # Step 5: Create multimodal embeddings and enhanced tags
                multimodal_enhancements = {}
                if item_id and transcription_result.get("text"):
                    try:
                        transcript_text = transcription_result["text"]
                        
                        # Create text embedding from transcript
                        text_embedding = await embedding_manager.create_embedding(
                            item_id, transcript_text
                        )
                        
                        # Enhance tags with NER from transcript
                        entities = await ner_service.extract_entities(transcript_text)
                        current_tags = summary_analysis.get("tags", [])
                        enhanced_tags = await ner_service.enhance_tags(
                            current_tags, entities, max_new_tags=8
                        )
                        
                        multimodal_enhancements = {
                            "text_embedding_created": bool(text_embedding),
                            "enhanced_tags": enhanced_tags,
                            "entities_extracted": entities.get("summary", {}),
                            "ner_technical_content": entities.get("summary", {}).get("has_technical_content", False),
                            "transcript_length": len(transcript_text),
                            "semantic_analysis": {
                                "people_mentioned": len(entities.get("people", [])),
                                "organizations_mentioned": len(entities.get("organizations", [])),
                                "technical_terms": len(entities.get("technical", {}).get("programming_languages", []) + 
                                                     entities.get("technical", {}).get("frameworks", []))
                            }
                        }
                    except Exception as e:
                        logger.warning(f"Multimodal enhancement failed for video {item_id}: {e}")
                        multimodal_enhancements = {"error": str(e)}
                
                # Step 6: Create final result
                analysis_result = {
                    "transcription": {
                        "text": transcription_result.get("text", ""),
                        "confidence": transcription_result.get("confidence", 0),
                        "word_count": transcription_result.get("word_count", 0),
                        "duration": transcription_result.get("duration", 0),
                        "processing_time": transcription_result.get("processing_time", 0),
                        "model_used": transcription_result.get("model_used", model_name),
                        "language": transcription_result.get("language", language),
                        "words": transcription_result.get("words", [])
                    },
                    "summary_analysis": summary_analysis,
                    "video_metadata": video_metadata,
                    "multimodal_enhancements": multimodal_enhancements,
                    "quality_metrics": {
                        "transcription_confidence": transcription_result.get("confidence", 0),
                        "transcription_length": len(transcription_result.get("text", "")),
                        "duration_seconds": transcription_result.get("duration", 0),
                        "real_time_factor": transcription_result.get("real_time_factor", 0),
                        "has_word_timestamps": len(transcription_result.get("words", [])) > 0,
                        "has_summary": bool(summary_analysis),
                        "has_enhanced_tags": bool(multimodal_enhancements.get("enhanced_tags"))
                    }
                }
                
                execution_time = time.time() - start_time
                
                logger.info(f"✅ Video transcription completed in {execution_time:.2f}s")
                
                return MediaAgentResult(
                    agent_name=self.name,
                    media_type="video",
                    status="completed", 
                    results=analysis_result,
                    execution_time=execution_time
                )
                
            finally:
                # Clean up temporary audio file
                if os.path.exists(audio_path):
                    os.unlink(audio_path)
                    
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Video transcription failed: {e}")
            
            return MediaAgentResult(
                agent_name=self.name,
                media_type="video",
                status="failed",
                results={"error": str(e)},
                execution_time=execution_time
            )
    
    async def _extract_audio_from_video(self, video_path: str) -> str:
        """
        Extract audio from video file using FFmpeg
        """
        try:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                audio_path = tmp_file.name
            
            # Use FFmpeg to extract audio
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',
                '-ar', '16000',  # 16kHz for Whisper
                '-ac', '1',      # Mono
                '-y',            # Overwrite output
                audio_path
            ]
            
            # Run extraction
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ Audio extracted from video: {audio_path}")
                return audio_path
            else:
                raise Exception(f"FFmpeg audio extraction failed: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise
    
    async def _create_summary_and_analysis(
        self, 
        transcript: str, 
        video_path: str
    ) -> Dict[str, Any]:
        """
        Create AI-powered summary and content analysis
        """
        try:
            # Prepare analysis prompt
            analysis_prompt = f"""
            Analyze this video transcript and provide comprehensive insights:
            
            TRANSCRIPT:
            {transcript[:3000]}  # Limit to avoid token limits
            
            Provide analysis in the following areas:
            1. EXECUTIVE SUMMARY: 2-3 sentence summary of main content
            2. KEY TOPICS: List 5-7 main topics or themes discussed
            3. IMPORTANT POINTS: Extract 3-5 most important insights or takeaways
            4. CONTENT TYPE: Categorize (educational, meeting, presentation, tutorial, etc.)
            5. TAGS: Generate 8-10 searchable tags
            6. ACTION ITEMS: Any tasks, todos, or follow-ups mentioned
            7. ENTITIES: Important people, places, technologies, or concepts mentioned
            8. DIFFICULTY LEVEL: beginner, intermediate, or advanced
            
            Format as JSON with these exact keys: executive_summary, key_topics, important_points, content_type, tags, action_items, entities, difficulty_level
            """
            
            # Get AI analysis
            analysis_result = await self.ai_service.complete(
                prompt=analysis_prompt,
                system_prompt="You are an expert content analyst. Provide structured analysis in valid JSON format.",
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                temperature=0.3
            )
            
            # Parse JSON response
            try:
                analysis_data = json.loads(analysis_result)
                return analysis_data
            except json.JSONDecodeError:
                # Fallback analysis
                return {
                    "executive_summary": "Video content transcribed and processed",
                    "key_topics": ["video", "content"],
                    "important_points": ["Transcription completed"],
                    "content_type": "unknown",
                    "tags": ["video", "transcription"],
                    "action_items": [],
                    "entities": [],
                    "difficulty_level": "unknown"
                }
                
        except Exception as e:
            logger.error(f"Summary analysis failed: {e}")
            return {}
    
    async def _extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extract video metadata using FFprobe
        """
        try:
            # Use FFprobe to get video metadata
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                metadata = json.loads(stdout.decode())
                
                # Extract useful metadata
                format_info = metadata.get("format", {})
                video_stream = None
                audio_stream = None
                
                for stream in metadata.get("streams", []):
                    if stream.get("codec_type") == "video" and not video_stream:
                        video_stream = stream
                    elif stream.get("codec_type") == "audio" and not audio_stream:
                        audio_stream = stream
                
                return {
                    "filename": format_info.get("filename", ""),
                    "duration": float(format_info.get("duration", 0)),
                    "size": int(format_info.get("size", 0)),
                    "bitrate": int(format_info.get("bit_rate", 0)),
                    "video": {
                        "codec": video_stream.get("codec_name") if video_stream else None,
                        "width": video_stream.get("width") if video_stream else None,
                        "height": video_stream.get("height") if video_stream else None,
                        "fps": video_stream.get("r_frame_rate") if video_stream else None
                    },
                    "audio": {
                        "codec": audio_stream.get("codec_name") if audio_stream else None,
                        "sample_rate": audio_stream.get("sample_rate") if audio_stream else None,
                        "channels": audio_stream.get("channels") if audio_stream else None
                    }
                }
            else:
                logger.warning(f"FFprobe failed for {video_path}: {stderr.decode()}")
                return {"error": "Could not extract metadata"}
                
        except Exception as e:
            logger.error(f"Video metadata extraction failed: {e}")
            return {"error": str(e)}


class AudioJournalAgent:
    """
    Audio Journal Agent
    
    Processes audio journals with advanced analysis including emotion detection,
    mood analysis, action item extraction, and knowledge base connections.
    Uses existing AudioJournal model and Whisper services.
    """
    
    def __init__(self):
        self.name = "Audio Journal Agent" 
        self.description = "Processes audio journals with advanced analysis and contextualization"
        self.whisper_service = whisper_cpp_service
        self.ai_service = unified_ai_service
        self.whisper_available = WHISPER_CPP_AVAILABLE
        
    async def execute(self, task_data: Dict[str, Any]) -> MediaAgentResult:
        """
        Execute audio journal processing workflow
        
        Args:
            task_data: Dictionary containing:
                - file_path: Path to audio file
                - item_id: Optional item ID for database linking
                - journal_id: Optional audio journal ID
                - model_name: Whisper model to use (default: "base")
                - language: Language code (default: "en")
                - analyze_emotions: Whether to perform emotion analysis
                
        Returns:
            MediaAgentResult with transcription, analysis, and journal metadata
        """
        start_time = time.time()
        
        try:
            file_path = task_data.get("file_path")
            item_id = task_data.get("item_id")
            journal_id = task_data.get("journal_id")
            model_name = task_data.get("model_name", "base")
            language = task_data.get("language", "en")
            analyze_emotions = task_data.get("analyze_emotions", True)
            
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"Audio file not found: {file_path}")
            
            if not self.whisper_available:
                raise ValueError("Whisper CPP not available. Check audio transcription dependencies.")
            
            logger.info(f"🎙️ Processing audio journal: {file_path}")
            
            # Step 1: Transcribe audio using Whisper CPP
            transcription_result = await self.whisper_service.transcribe_audio(
                audio_path=file_path,
                model_name=model_name,
                language=language,
                word_timestamps=True
            )
            
            if not transcription_result:
                raise Exception("Whisper transcription failed")
            
            # Step 2: Advanced journal analysis
            journal_analysis = {}
            if transcription_result.get("text"):
                journal_analysis = await self._analyze_journal_content(
                    transcription_result["text"], analyze_emotions
                )
            
            # Step 3: Find knowledge base connections
            knowledge_connections = await self._find_journal_connections(
                transcription_result.get("text", ""), 
                journal_analysis.get("key_topics", [])
            )
            
            # Step 4: Extract audio characteristics
            audio_characteristics = await self._analyze_audio_characteristics(
                file_path, transcription_result
            )
            
            # Step 5: Create final journal analysis
            analysis_result = {
                "transcription": {
                    "text": transcription_result.get("text", ""),
                    "confidence": transcription_result.get("confidence", 0),
                    "word_count": transcription_result.get("word_count", 0),
                    "duration": transcription_result.get("duration", 0),
                    "processing_time": transcription_result.get("processing_time", 0),
                    "model_used": transcription_result.get("model_used", model_name),
                    "language": transcription_result.get("language", language),
                    "words": transcription_result.get("words", [])
                },
                "journal_analysis": journal_analysis,
                "knowledge_connections": knowledge_connections,
                "audio_characteristics": audio_characteristics,
                "journal_metadata": {
                    "privacy_level": "private",  # Default for journal entries
                    "session_title": journal_analysis.get("suggested_title", "Audio Journal Entry"),
                    "emotional_tone": journal_analysis.get("dominant_emotion", "neutral"),
                    "key_topics": journal_analysis.get("key_topics", []),
                    "action_items": journal_analysis.get("action_items", []),
                    "mood_tags": journal_analysis.get("mood_indicators", [])
                },
                "quality_metrics": {
                    "transcription_confidence": transcription_result.get("confidence", 0),
                    "content_richness_score": len(journal_analysis.get("key_topics", [])) * 0.2,
                    "emotional_clarity": len(journal_analysis.get("emotions_detected", [])) * 0.1,
                    "actionability_score": len(journal_analysis.get("action_items", [])) * 0.3,
                    "connection_count": len(knowledge_connections.get("related_items", [])),
                    "has_timestamps": len(transcription_result.get("words", [])) > 0
                }
            }
            
            execution_time = time.time() - start_time
            
            logger.info(f"✅ Audio journal analysis completed in {execution_time:.2f}s")
            
            return MediaAgentResult(
                agent_name=self.name,
                media_type="audio_journal",
                status="completed",
                results=analysis_result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Audio journal processing failed: {e}")
            
            return MediaAgentResult(
                agent_name=self.name,
                media_type="audio_journal",
                status="failed",
                results={"error": str(e)},
                execution_time=execution_time
            )
    
    async def _analyze_journal_content(
        self, 
        transcript: str, 
        analyze_emotions: bool = True
    ) -> Dict[str, Any]:
        """
        Advanced analysis of journal content including emotions, topics, and insights
        """
        try:
            # Prepare comprehensive journal analysis prompt
            analysis_prompt = f"""
            Analyze this audio journal transcript for deep insights and emotional understanding:
            
            TRANSCRIPT:
            {transcript[:2500]}  # Limit to avoid token limits
            
            Provide comprehensive analysis:
            1. SUGGESTED_TITLE: A meaningful 3-6 word title for this journal entry
            2. SUMMARY: 2-3 sentence summary of the main content and themes
            3. KEY_TOPICS: List 5-8 main topics, themes, or subjects discussed
            4. EMOTIONS_DETECTED: List emotions present (happy, sad, anxious, excited, frustrated, calm, etc.)
            5. DOMINANT_EMOTION: The primary emotional tone
            6. MOOD_INDICATORS: Specific words or phrases that indicate mood
            7. ACTION_ITEMS: Any tasks, goals, or intentions mentioned
            8. INSIGHTS: Personal insights, realizations, or important thoughts shared
            9. CONCERNS: Any worries, problems, or challenges mentioned
            10. GRATITUDE: Things the person is grateful for or positive about
            11. FUTURE_PLANS: Any plans, aspirations, or future-oriented thoughts
            12. PEOPLE_MENTIONED: Names or relationships mentioned
            13. LOCATIONS_MENTIONED: Places or locations referenced
            14. PERSONAL_GROWTH: Evidence of learning, growth, or self-reflection
            15. STRESS_INDICATORS: Signs of stress, pressure, or overwhelm
            
            Format as JSON with these exact keys: suggested_title, summary, key_topics, emotions_detected, dominant_emotion, mood_indicators, action_items, insights, concerns, gratitude, future_plans, people_mentioned, locations_mentioned, personal_growth, stress_indicators
            """
            
            # Get AI analysis
            analysis_result = await self.ai_service.complete(
                prompt=analysis_prompt,
                system_prompt="You are an expert in psychology and personal development. Analyze this journal with empathy and insight. Provide structured analysis in valid JSON format.",
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                temperature=0.4  # Slightly higher for more nuanced emotional analysis
            )
            
            # Parse JSON response
            try:
                analysis_data = json.loads(analysis_result)
                return analysis_data
            except json.JSONDecodeError:
                # Fallback analysis
                return {
                    "suggested_title": "Journal Entry",
                    "summary": "Audio journal entry processed",
                    "key_topics": ["personal", "reflection"],
                    "emotions_detected": ["neutral"],
                    "dominant_emotion": "neutral",
                    "mood_indicators": [],
                    "action_items": [],
                    "insights": [],
                    "concerns": [],
                    "gratitude": [],
                    "future_plans": [],
                    "people_mentioned": [],
                    "locations_mentioned": [],
                    "personal_growth": [],
                    "stress_indicators": []
                }
                
        except Exception as e:
            logger.error(f"Journal content analysis failed: {e}")
            return {}
    
    async def _find_journal_connections(
        self, 
        transcript: str, 
        topics: List[str]
    ) -> Dict[str, Any]:
        """
        Find connections between this journal entry and existing knowledge base
        """
        try:
            # Create search terms from transcript and topics
            search_terms = topics + transcript.split()[:50]  # Limit search terms
            search_query = " ".join(search_terms)
            
            # For now, return placeholder structure
            # In production, this would use vector similarity search
            connections = {
                "related_items": [],
                "connection_count": 0,
                "search_terms": search_terms[:10],  # Top 10 terms
                "semantic_themes": topics,
                "connection_method": "semantic_analysis"
            }
            
            return connections
            
        except Exception as e:
            logger.error(f"Journal connections analysis failed: {e}")
            return {"related_items": [], "connection_count": 0}
    
    async def _analyze_audio_characteristics(
        self, 
        audio_path: str, 
        transcription_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze audio characteristics like pace, pauses, energy
        """
        try:
            duration = transcription_result.get("duration", 0)
            word_count = transcription_result.get("word_count", 0)
            words_with_timestamps = transcription_result.get("words", [])
            
            # Calculate speech pace
            speech_pace_wpm = 0
            if duration > 0:
                speech_pace_wpm = int((word_count / duration) * 60)
            
            # Analyze pauses if we have word timestamps
            pause_analysis = {"long_pauses": 0, "average_pause": 0, "total_silence": 0}
            if words_with_timestamps:
                pauses = []
                for i in range(1, len(words_with_timestamps)):
                    prev_end = words_with_timestamps[i-1].get("end", 0)
                    curr_start = words_with_timestamps[i].get("start", 0)
                    pause_duration = curr_start - prev_end
                    if pause_duration > 0.5:  # Pauses longer than 0.5 seconds
                        pauses.append(pause_duration)
                
                if pauses:
                    pause_analysis = {
                        "long_pauses": len([p for p in pauses if p > 2.0]),
                        "average_pause": sum(pauses) / len(pauses),
                        "total_silence": sum(pauses)
                    }
            
            return {
                "duration_seconds": duration,
                "word_count": word_count,
                "speech_pace_wpm": speech_pace_wpm,
                "pause_analysis": pause_analysis,
                "speaking_ratio": (duration - pause_analysis["total_silence"]) / duration if duration > 0 else 0,
                "energy_level": "moderate" if speech_pace_wpm > 120 else "calm",  # Simple heuristic
                "file_size": os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
            }
            
        except Exception as e:
            logger.error(f"Audio characteristics analysis failed: {e}")
            return {"duration_seconds": 0, "word_count": 0, "speech_pace_wpm": 0}


# Agent Registry for easy access
MEDIA_AGENTS = {
    "image_analyzer": OCRImageAnalysisAgent(),
    "video_processor": VideoTranscriptionAgent(),
    "audio_journal_processor": AudioJournalAgent()
}


def get_media_agent(agent_name: str) -> Optional[Any]:
    """Get a media agent by name"""
    return MEDIA_AGENTS.get(agent_name)


def list_media_agents() -> Dict[str, str]:
    """List all available media agents"""
    return {
        name: agent.description 
        for name, agent in MEDIA_AGENTS.items()
    }