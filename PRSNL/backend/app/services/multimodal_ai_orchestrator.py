"""
Advanced Multi-modal AI Orchestrator for PRSNL Phase 5
=======================================================

Unifies Vision + Text + Voice AI processing with intelligent routing and cross-modal analysis.

Features:
- Unified multi-modal content processing
- Cross-modal similarity search  
- Intelligent content correlation
- Advanced media understanding
- Emotional AI responses with voice adaptation
- Context-aware AI routing

This orchestrator integrates:
- VisionProcessor (image/video analysis)
- MultimodalEmbeddingService (cross-modal embeddings)
- VoiceService (speech/TTS with personality)
- UnifiedAIService (text processing)
- AI Router (intelligent provider selection)
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
import json
import base64
import io
from PIL import Image
import numpy as np
from uuid import uuid4

from app.services.vision_processor import VisionProcessor
from app.services.multimodal_embedding_service import MultimodalEmbeddingService
from app.services.voice_service import VoiceService, CortexPersonality
from app.services.unified_ai_service import unified_ai_service
from app.services.ai_router_enhanced import enhanced_ai_router
# from app.services.realtime_stt_service import RealtimeSTTService  # Temporarily disabled - missing RealtimeSTT
from app.db.database import get_db_connection
from app.config import settings

logger = logging.getLogger(__name__)

class MultimodalAIOrchestrator:
    """
    Advanced multi-modal AI orchestrator that intelligently processes 
    and correlates content across vision, text, and voice modalities.
    """
    
    def __init__(self):
        self.vision_processor = VisionProcessor()
        self.multimodal_embedding = MultimodalEmbeddingService()
        self.voice_service = VoiceService()
        # self.stt_service = RealtimeSTTService()  # Temporarily disabled - missing RealtimeSTT
        self.stt_service = None
        self.personality = CortexPersonality()
        
        # Processing capabilities
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.supported_audio_formats = {'.mp3', '.wav', '.m4a', '.ogg', '.flac'}
        self.supported_video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        
    async def process_multimodal_content(
        self,
        content_data: Dict[str, Any],
        analysis_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Process content across multiple modalities with intelligent analysis.
        
        Args:
            content_data: Dict containing content in various formats:
                - text: str
                - image_path: str or image_base64: str  
                - audio_path: str or audio_base64: str
                - video_path: str
                - url: str (for web content)
            analysis_depth: 'quick', 'standard', 'comprehensive'
            
        Returns:
            Unified analysis result with cross-modal insights
        """
        session_id = str(uuid4())
        start_time = datetime.utcnow()
        
        logger.info(f"🚀 Starting multi-modal analysis [Session: {session_id}]")
        
        try:
            # Initialize result structure
            result = {
                "session_id": session_id,
                "timestamp": start_time.isoformat(),
                "analysis_depth": analysis_depth,
                "modalities_processed": [],
                "cross_modal_insights": {},
                "unified_understanding": {},
                "processing_stats": {},
                "recommendations": []
            }
            
            # Process each modality in parallel
            processing_tasks = []
            
            # Text processing
            if content_data.get('text'):
                processing_tasks.append(
                    self._process_text_modality(content_data['text'], analysis_depth)
                )
                result["modalities_processed"].append("text")
            
            # Image processing  
            if content_data.get('image_path') or content_data.get('image_base64'):
                processing_tasks.append(
                    self._process_image_modality(content_data, analysis_depth)
                )
                result["modalities_processed"].append("vision")
            
            # Audio processing
            if content_data.get('audio_path') or content_data.get('audio_base64'):
                processing_tasks.append(
                    self._process_audio_modality(content_data, analysis_depth)
                )
                result["modalities_processed"].append("audio")
            
            # Video processing
            if content_data.get('video_path'):
                processing_tasks.append(
                    self._process_video_modality(content_data['video_path'], analysis_depth)
                )
                result["modalities_processed"].append("video")
            
            # Execute all processing tasks in parallel
            if processing_tasks:
                modality_results = await asyncio.gather(*processing_tasks, return_exceptions=True)
                
                # Combine results
                text_result = None
                vision_result = None
                audio_result = None
                video_result = None
                
                for i, task_result in enumerate(modality_results):
                    if isinstance(task_result, Exception):
                        logger.error(f"Modality processing failed: {task_result}")
                        continue
                        
                    modality = result["modalities_processed"][i]
                    if modality == "text":
                        text_result = task_result
                    elif modality == "vision":
                        vision_result = task_result
                    elif modality == "audio":
                        audio_result = task_result
                    elif modality == "video":
                        video_result = task_result
                
                # Generate cross-modal insights
                result["cross_modal_insights"] = await self._generate_cross_modal_insights(
                    text_result, vision_result, audio_result, video_result, analysis_depth
                )
                
                # Create unified understanding
                result["unified_understanding"] = await self._create_unified_understanding(
                    result["cross_modal_insights"], analysis_depth
                )
                
                # Generate recommendations
                result["recommendations"] = await self._generate_recommendations(
                    result["unified_understanding"], content_data
                )
            
            # Calculate processing stats
            end_time = datetime.utcnow()
            result["processing_stats"] = {
                "total_duration_ms": int((end_time - start_time).total_seconds() * 1000),
                "modalities_count": len(result["modalities_processed"]),
                "analysis_depth": analysis_depth,
                "insights_generated": len(result["cross_modal_insights"]),
                "recommendations_count": len(result["recommendations"])
            }
            
            logger.info(f"✅ Multi-modal analysis complete [Session: {session_id}] - {result['processing_stats']['total_duration_ms']}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Multi-modal processing failed [Session: {session_id}]: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed"
            }
    
    async def _process_text_modality(self, text: str, depth: str) -> Dict[str, Any]:
        """Process text content with AI analysis"""
        try:
            # Use enhanced AI router for intelligent processing
            analysis_prompt = self._build_text_analysis_prompt(text, depth)
            
            ai_response = await enhanced_ai_router.route_request({
                "prompt": analysis_prompt,
                "content": text,
                "task_type": "text_analysis",
                "priority": 8 if depth == "comprehensive" else 6,
                "metadata": {"modality": "text", "depth": depth}
            })
            
            # Generate embeddings
            embeddings = await unified_ai_service.generate_embeddings([text])
            
            return {
                "modality": "text",
                "content_length": len(text),
                "ai_analysis": ai_response.get("response", {}),
                "embeddings": embeddings[0] if embeddings else None,
                "key_concepts": ai_response.get("key_concepts", []),
                "sentiment": ai_response.get("sentiment", "neutral"),
                "topics": ai_response.get("topics", []),
                "complexity_score": ai_response.get("complexity_score", 0.5)
            }
            
        except Exception as e:
            logger.error(f"Text modality processing failed: {e}")
            return {"modality": "text", "error": str(e)}
    
    async def _process_image_modality(self, content_data: Dict, depth: str) -> Dict[str, Any]:
        """Process image content with vision AI"""
        try:
            # Get image path or decode base64
            image_path = content_data.get('image_path')
            if not image_path and content_data.get('image_base64'):
                # Decode base64 to temporary file
                image_data = base64.b64decode(content_data['image_base64'])
                temp_path = f"/tmp/multimodal_image_{uuid4().hex}.png"
                with open(temp_path, 'wb') as f:
                    f.write(image_data)
                image_path = temp_path
            
            if not image_path:
                raise ValueError("No image data provided")
            
            # Process with vision processor
            vision_result = await self.vision_processor.process_image(image_path)
            
            # Generate multimodal embeddings
            image_embedding = await self.multimodal_embedding.create_image_embedding(image_path)
            
            return {
                "modality": "vision",
                "image_path": image_path,
                "vision_analysis": vision_result,
                "image_embedding": image_embedding,
                "detected_objects": vision_result.get("objects", []),
                "scene_description": vision_result.get("description", ""),
                "text_content": vision_result.get("ocr_text", ""),
                "visual_complexity": vision_result.get("complexity_score", 0.5)
            }
            
        except Exception as e:
            logger.error(f"Image modality processing failed: {e}")
            return {"modality": "vision", "error": str(e)}
    
    async def _process_audio_modality(self, content_data: Dict, depth: str) -> Dict[str, Any]:
        """Process audio content with speech analysis"""
        try:
            audio_path = content_data.get('audio_path')
            if not audio_path and content_data.get('audio_base64'):
                # Decode base64 to temporary file
                audio_data = base64.b64decode(content_data['audio_base64'])
                temp_path = f"/tmp/multimodal_audio_{uuid4().hex}.wav"
                with open(temp_path, 'wb') as f:
                    f.write(audio_data)
                audio_path = temp_path
            
            if not audio_path:
                raise ValueError("No audio data provided")
            
            # Transcribe audio
            transcription = await self.stt_service.transcribe_audio_file(audio_path)
            
            # Analyze transcribed text if available
            text_analysis = None
            if transcription.get('text'):
                text_analysis = await self._process_text_modality(
                    transcription['text'], depth
                )
            
            return {
                "modality": "audio",
                "audio_path": audio_path,
                "transcription": transcription,
                "text_analysis": text_analysis,
                "audio_duration": transcription.get("duration", 0),
                "confidence_score": transcription.get("confidence", 0.0),
                "detected_language": transcription.get("language", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Audio modality processing failed: {e}")
            return {"modality": "audio", "error": str(e)}
    
    async def _process_video_modality(self, video_path: str, depth: str) -> Dict[str, Any]:
        """Process video content with frame analysis"""
        try:
            # Extract key frames for analysis
            frames = await self._extract_video_frames(video_path, max_frames=5)
            
            # Process each frame
            frame_analyses = []
            for i, frame_path in enumerate(frames):
                frame_result = await self._process_image_modality(
                    {"image_path": frame_path}, depth
                )
                frame_result["frame_number"] = i
                frame_analyses.append(frame_result)
            
            # Extract audio if present
            audio_path = await self._extract_video_audio(video_path)
            audio_analysis = None
            if audio_path:
                audio_analysis = await self._process_audio_modality(
                    {"audio_path": audio_path}, depth
                )
            
            return {
                "modality": "video",
                "video_path": video_path,
                "frame_analyses": frame_analyses,
                "audio_analysis": audio_analysis,
                "frame_count": len(frames),
                "has_audio": audio_analysis is not None
            }
            
        except Exception as e:
            logger.error(f"Video modality processing failed: {e}")
            return {"modality": "video", "error": str(e)}
    
    async def _generate_cross_modal_insights(
        self, 
        text_result: Optional[Dict], 
        vision_result: Optional[Dict],
        audio_result: Optional[Dict], 
        video_result: Optional[Dict],
        depth: str
    ) -> Dict[str, Any]:
        """Generate insights that span multiple modalities"""
        insights = {}
        
        try:
            # Text-Vision correlation
            if text_result and vision_result:
                insights["text_vision_correlation"] = await self._correlate_text_vision(
                    text_result, vision_result
                )
            
            # Audio-Text correlation
            if audio_result and text_result:
                insights["audio_text_correlation"] = await self._correlate_audio_text(
                    audio_result, text_result
                )
            
            # Multi-modal semantic similarity
            if len([r for r in [text_result, vision_result, audio_result] if r]) >= 2:
                insights["semantic_similarity"] = await self._calculate_cross_modal_similarity(
                    text_result, vision_result, audio_result
                )
            
            # Content consistency analysis
            insights["content_consistency"] = await self._analyze_content_consistency(
                text_result, vision_result, audio_result, video_result
            )
            
            return insights
            
        except Exception as e:
            logger.error(f"Cross-modal insight generation failed: {e}")
            return {"error": str(e)}
    
    async def _create_unified_understanding(
        self, 
        cross_modal_insights: Dict, 
        depth: str
    ) -> Dict[str, Any]:
        """Create a unified understanding from cross-modal insights"""
        try:
            # Use AI to synthesize insights
            synthesis_prompt = f"""
            Analyze the following cross-modal insights and create a unified understanding:
            
            {json.dumps(cross_modal_insights, indent=2)}
            
            Provide a comprehensive synthesis that:
            1. Identifies the core themes across modalities
            2. Highlights any contradictions or inconsistencies  
            3. Extracts the most important insights
            4. Suggests the overall meaning or purpose
            5. Rates the confidence in this understanding (0-1)
            
            Response format: {{
                "core_themes": [...],
                "key_insights": [...],
                "contradictions": [...],
                "overall_meaning": "...",
                "confidence_score": 0.0-1.0,
                "synthesis_summary": "..."
            }}
            """
            
            ai_response = await enhanced_ai_router.route_request({
                "prompt": synthesis_prompt,
                "task_type": "synthesis",
                "priority": 9,
                "metadata": {"stage": "unified_understanding", "depth": depth}
            })
            
            return {
                "synthesis": ai_response.get("response", {}),
                "processing_timestamp": datetime.utcnow().isoformat(),
                "modalities_analyzed": len(cross_modal_insights),
                "depth": depth
            }
            
        except Exception as e:
            logger.error(f"Unified understanding creation failed: {e}")
            return {"error": str(e)}
    
    async def _generate_recommendations(
        self, 
        unified_understanding: Dict, 
        original_content: Dict
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on unified understanding"""
        try:
            recommendations = []
            
            # Content enhancement recommendations
            if unified_understanding.get("synthesis", {}).get("confidence_score", 0) < 0.7:
                recommendations.append({
                    "type": "content_enhancement",
                    "priority": "high",
                    "title": "Improve Content Clarity",
                    "description": "The analysis shows inconsistencies across modalities. Consider aligning content better.",
                    "actions": [
                        "Review text-visual alignment",
                        "Ensure audio matches visual content",
                        "Add clarifying context"
                    ]
                })
            
            # Accessibility recommendations
            if "vision" in original_content and not original_content.get("text"):
                recommendations.append({
                    "type": "accessibility",
                    "priority": "medium", 
                    "title": "Add Alt Text",
                    "description": "Visual content detected without text description",
                    "actions": ["Add descriptive alt text", "Include image captions"]
                })
            
            # SEO and discoverability
            core_themes = unified_understanding.get("synthesis", {}).get("core_themes", [])
            if core_themes:
                recommendations.append({
                    "type": "seo_optimization",
                    "priority": "medium",
                    "title": "Optimize for Discovery",
                    "description": f"Core themes identified: {', '.join(core_themes[:3])}",
                    "actions": [
                        "Add relevant tags",
                        "Optimize title with key themes",
                        "Create topic-based categorization"
                    ]
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return [{"type": "error", "description": str(e)}]
    
    # Helper methods
    def _build_text_analysis_prompt(self, text: str, depth: str) -> str:
        """Build analysis prompt based on depth level"""
        base_prompt = f"Analyze this text content:\n\n{text}\n\n"
        
        if depth == "quick":
            return base_prompt + "Provide: main topic, sentiment, key concepts (max 3)"
        elif depth == "standard":  
            return base_prompt + "Provide: topics, sentiment, key concepts, complexity score, summary"
        else:  # comprehensive
            return base_prompt + "Provide comprehensive analysis: topics, sentiment, key concepts, complexity score, themes, writing style, target audience, emotional tone, actionable insights"
    
    async def _correlate_text_vision(self, text_result: Dict, vision_result: Dict) -> Dict[str, Any]:
        """Correlate text and vision content"""
        try:
            text_concepts = text_result.get("key_concepts", [])
            visual_objects = vision_result.get("detected_objects", [])
            visual_description = vision_result.get("scene_description", "")
            
            # Calculate semantic overlap
            overlap_score = await self._calculate_semantic_overlap(
                text_concepts, visual_objects + [visual_description]
            )
            
            return {
                "overlap_score": overlap_score,
                "text_concepts": text_concepts,
                "visual_elements": visual_objects,
                "alignment_quality": "high" if overlap_score > 0.7 else "medium" if overlap_score > 0.4 else "low"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _correlate_audio_text(self, audio_result: Dict, text_result: Dict) -> Dict[str, Any]:
        """Correlate audio and text content"""
        try:
            transcribed_text = audio_result.get("transcription", {}).get("text", "")
            original_text = text_result.get("content", "")
            
            if transcribed_text and original_text:
                # Calculate text similarity
                similarity = await self._calculate_text_similarity(transcribed_text, original_text)
                
                return {
                    "text_similarity": similarity,
                    "transcription_quality": audio_result.get("confidence_score", 0),
                    "content_match": "high" if similarity > 0.8 else "medium" if similarity > 0.5 else "low"
                }
            
            return {"status": "insufficient_data"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _calculate_cross_modal_similarity(
        self, 
        text_result: Optional[Dict],
        vision_result: Optional[Dict], 
        audio_result: Optional[Dict]
    ) -> Dict[str, float]:
        """Calculate similarity scores across modalities"""
        similarities = {}
        
        try:
            # Get embeddings for comparison
            text_embedding = text_result.get("embeddings") if text_result else None
            image_embedding = vision_result.get("image_embedding") if vision_result else None
            
            if text_embedding and image_embedding:
                # Calculate cosine similarity
                similarity = np.dot(text_embedding, image_embedding) / (
                    np.linalg.norm(text_embedding) * np.linalg.norm(image_embedding)
                )
                similarities["text_vision"] = float(similarity)
            
            return similarities
            
        except Exception as e:
            logger.error(f"Cross-modal similarity calculation failed: {e}")
            return {}
    
    async def _analyze_content_consistency(
        self,
        text_result: Optional[Dict],
        vision_result: Optional[Dict],
        audio_result: Optional[Dict],
        video_result: Optional[Dict]
    ) -> Dict[str, Any]:
        """Analyze consistency across all modalities"""
        try:
            modalities_present = []
            sentiment_scores = []
            topics_all = []
            
            # Collect data from each modality
            if text_result:
                modalities_present.append("text")
                if "sentiment" in text_result:
                    sentiment_scores.append(text_result["sentiment"])
                if "topics" in text_result:
                    topics_all.extend(text_result["topics"])
            
            if vision_result:
                modalities_present.append("vision")
            
            if audio_result:
                modalities_present.append("audio")
                if audio_result.get("text_analysis", {}).get("sentiment"):
                    sentiment_scores.append(audio_result["text_analysis"]["sentiment"])
            
            if video_result:
                modalities_present.append("video")
            
            # Calculate consistency metrics
            sentiment_consistency = self._calculate_sentiment_consistency(sentiment_scores)
            topic_coherence = len(set(topics_all)) / max(len(topics_all), 1)
            
            return {
                "modalities_present": modalities_present,
                "sentiment_consistency": sentiment_consistency,
                "topic_coherence": topic_coherence,
                "overall_consistency": (sentiment_consistency + topic_coherence) / 2
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_sentiment_consistency(self, sentiments: List[str]) -> float:
        """Calculate how consistent sentiments are across modalities"""
        if len(sentiments) < 2:
            return 1.0
        
        # Map sentiments to scores  
        sentiment_map = {"positive": 1, "neutral": 0, "negative": -1}
        scores = [sentiment_map.get(s, 0) for s in sentiments]
        
        # Calculate variance (lower = more consistent)
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            consistency = max(0, 1 - variance)  # Convert variance to consistency score
            return consistency
        
        return 1.0
    
    async def _calculate_semantic_overlap(self, concepts1: List[str], concepts2: List[str]) -> float:
        """Calculate semantic overlap between two concept lists"""
        if not concepts1 or not concepts2:
            return 0.0
        
        # Simple keyword overlap (can be enhanced with embeddings)
        set1 = set(c.lower() for c in concepts1)
        set2 = set(c.lower() for c in concepts2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        try:
            # Generate embeddings for both texts
            embeddings = await unified_ai_service.generate_embeddings([text1, text2])
            if len(embeddings) == 2:
                # Calculate cosine similarity
                similarity = np.dot(embeddings[0], embeddings[1]) / (
                    np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
                )
                return float(similarity)
            return 0.0
        except Exception as e:
            logger.error(f"Text similarity calculation failed: {e}")
            return 0.0
    
    async def _extract_video_frames(self, video_path: str, max_frames: int = 5) -> List[str]:
        """Extract key frames from video for analysis"""
        # Placeholder implementation - would use ffmpeg or opencv
        # For now, return empty list
        return []
    
    async def _extract_video_audio(self, video_path: str) -> Optional[str]:
        """Extract audio track from video"""
        # Placeholder implementation - would use ffmpeg
        return None


# Create singleton instance
multimodal_orchestrator = MultimodalAIOrchestrator()