"""
Crawl.ai Integration API for PRSNL Second Brain

This module provides FastAPI endpoints that expose Crawl.ai's
multi-agent capabilities to the PRSNL frontend, replacing AutoAgent.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field

from app.core.exceptions import InternalServerError
from app.services.crawl_ai_agents import crawl_ai_orchestrator, MultiAgentResult
from app.services.media_persistence_service import media_persistence_service

router = APIRouter(prefix="/crawl-ai", tags=["crawl-ai"])


# Request Models
class ContentProcessingRequest(BaseModel):
    """Request to process content through multi-agent workflow"""
    content: str = Field(..., description="Content to process")
    url: Optional[str] = Field(None, description="Source URL if available")
    tags: Optional[List[str]] = Field(default_factory=list, description="Existing tags")
    workflow: str = Field("full", description="Workflow type: full, curate, research, explore")


class TopicExplorationRequest(BaseModel):
    """Request to explore a topic"""
    topic: str = Field(..., description="Topic to explore (text or URL)")
    interests: Optional[List[str]] = Field(default_factory=list, description="User interests")
    depth: int = Field(2, ge=1, le=5, description="Exploration depth")


class LearningPathRequest(BaseModel):
    """Request to create a learning path"""
    goal: str = Field(..., description="Learning goal")
    current_knowledge: Optional[List[str]] = Field(default_factory=list, description="Current knowledge areas")
    preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Learning preferences (time_commitment, learning_style)"
    )


class SynthesisRequest(BaseModel):
    """Request to synthesize multiple sources"""
    sources: List[str] = Field(..., description="List of URLs or content items to synthesize")
    focus: Optional[str] = Field("general", description="Focus area for synthesis")


class InsightsReportRequest(BaseModel):
    """Request for insights report"""
    time_period: str = Field("week", description="Time period: day, week, month")
    focus_areas: Optional[List[str]] = Field(default_factory=list, description="Specific areas to focus on")


# Media Processing Request Models
class ImageProcessingRequest(BaseModel):
    """Request to process an image through OCR and AI analysis"""
    file_path: str = Field(..., description="Path to image file")
    item_id: Optional[str] = Field(None, description="Item ID for database linking")
    enhance_analysis: bool = Field(True, description="Whether to run enhanced context analysis")


class VideoProcessingRequest(BaseModel):
    """Request to process a video through transcription and analysis"""
    file_path: str = Field(..., description="Path to video file")
    item_id: Optional[str] = Field(None, description="Item ID for database linking")
    model_name: str = Field("base", description="Whisper model to use (tiny, base, small, medium, large)")
    language: str = Field("en", description="Language code for transcription")
    create_summary: bool = Field(True, description="Whether to create AI summary")


class AudioJournalProcessingRequest(BaseModel):
    """Request to process an audio journal with advanced analysis"""
    file_path: str = Field(..., description="Path to audio file")
    item_id: Optional[str] = Field(None, description="Item ID for database linking")
    journal_id: Optional[str] = Field(None, description="Audio journal ID for database linking")
    model_name: str = Field("base", description="Whisper model to use")
    language: str = Field("en", description="Language code for transcription")
    analyze_emotions: bool = Field(True, description="Whether to perform emotion analysis")


class MediaBatchProcessingRequest(BaseModel):
    """Request to process multiple media files in batch"""
    media_files: List[Dict[str, Any]] = Field(..., description="List of media files with file_path, media_type, and options")


# Response Models  
class AgentStatus(BaseModel):
    """Status of agent system"""
    status: str = "healthy"
    agents_available: List[str]
    version: str = "1.0.0"
    last_activity: Optional[datetime] = None


# API Endpoints
@router.get("/health", response_model=AgentStatus)
async def agent_health_check():
    """Check health status of Crawl.ai agent system"""
    return AgentStatus(
        status="healthy",
        agents_available=list(crawl_ai_orchestrator.agents.keys()),
        version="1.0.0",
        last_activity=datetime.utcnow()
    )


@router.post("/process-content", response_model=MultiAgentResult)
async def process_content(request: ContentProcessingRequest):
    """
    Process content through multi-agent workflow.
    
    This endpoint triggers Knowledge Curator, Research Synthesizer,
    and other agents to analyze and enhance content.
    
    Workflows:
    - **full**: All agents (default)
    - **curate**: Just knowledge curation
    - **research**: Curation + Research synthesis
    - **explore**: Curation + Content exploration
    """
    try:
        result = await crawl_ai_orchestrator.process_content(
            content=request.content,
            url=request.url,
            tags=request.tags,
            workflow=request.workflow
        )
        return result
        
    except Exception as e:
        raise InternalServerError(f"Content processing failed: {str(e)}")


@router.post("/explore-topic", response_model=MultiAgentResult)
async def explore_topic(request: TopicExplorationRequest):
    """
    Explore a topic using Content Explorer and related agents.
    
    Creates exploration paths, finds connections, and suggests learning sequences.
    Topic can be text or a URL to explore.
    """
    try:
        result = await crawl_ai_orchestrator.explore_topic(
            topic=request.topic,
            interests=request.interests,
            depth=request.depth
        )
        return result
        
    except Exception as e:
        raise InternalServerError(f"Topic exploration failed: {str(e)}")


@router.post("/create-learning-path", response_model=MultiAgentResult)
async def create_learning_path(request: LearningPathRequest):
    """
    Create a personalized learning path for a specific goal.
    
    Uses Learning Pathfinder agent to create structured learning journey
    with milestones, resources, and progress tracking.
    """
    try:
        result = await crawl_ai_orchestrator.create_learning_path(
            goal=request.goal,
            current_knowledge=request.current_knowledge,
            preferences=request.preferences
        )
        return result
        
    except Exception as e:
        raise InternalServerError(f"Learning path creation failed: {str(e)}")


@router.post("/synthesize")
async def synthesize_sources(request: SynthesisRequest):
    """
    Synthesize multiple sources into coherent insights.
    
    Uses Research Synthesizer agent to combine information from multiple
    URLs or content items into a comprehensive synthesis.
    """
    try:
        # Process sources through research synthesizer
        result = await crawl_ai_orchestrator.agents["research_synthesizer"].execute({
            "sources": request.sources,
            "focus": request.focus
        })
        
        return {
            "status": "completed",
            "synthesis": result.results,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        raise InternalServerError(f"Synthesis failed: {str(e)}")


@router.get("/insights-report")
async def generate_insights_report(
    time_period: str = "week",
    focus_areas: Optional[str] = None
):
    """
    Generate comprehensive insights report from knowledge base.
    
    Analyzes patterns, trends, and generates recommendations based on
    recent activity and content in the knowledge base.
    """
    try:
        focus_list = focus_areas.split(",") if focus_areas else None
        
        report = await crawl_ai_orchestrator.generate_insights_report(
            time_period=time_period,
            focus_areas=focus_list
        )
        
        return {
            "status": "completed",
            "report": report,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise InternalServerError(f"Insights generation failed: {str(e)}")


@router.post("/find-connections/{item_id}")
async def find_content_connections(
    item_id: str,
    limit: int = 10
):
    """
    Find connections for a specific content item.
    
    Uses Knowledge Curator agent to find related content based on
    tags, concepts, and semantic similarity.
    """
    try:
        # This would typically fetch the item from database
        # For now, use the curator's connection finding capability
        curator = crawl_ai_orchestrator.agents["knowledge_curator"]
        
        # Mock implementation - would integrate with database
        connections = await curator._find_content_connections(
            content="",  # Would fetch from DB
            tags=[]  # Would fetch from DB
        )
        
        return {
            "item_id": item_id,
            "connections": connections[:limit],
            "total_found": len(connections)
        }
        
    except Exception as e:
        raise InternalServerError(f"Connection discovery failed: {str(e)}")


@router.post("/custom-agent-query")
async def custom_agent_query(
    agent_name: str,
    query: Dict[str, Any]
):
    """
    Execute a custom query with a specific agent.
    
    Allows direct interaction with individual agents for specialized tasks.
    Available agents: knowledge_curator, research_synthesizer, 
    content_explorer, learning_pathfinder
    """
    try:
        if agent_name not in crawl_ai_orchestrator.agents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown agent: {agent_name}"
            )
        
        agent = crawl_ai_orchestrator.agents[agent_name]
        result = await agent.execute(query)
        
        return {
            "status": "completed",
            "agent": agent_name,
            "results": result.results,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise InternalServerError(f"Agent query failed: {str(e)}")


@router.get("/agent-capabilities")
async def get_agent_capabilities():
    """
    Get detailed information about available agents and their capabilities.
    """
    capabilities = {}
    
    for name, agent in crawl_ai_orchestrator.agents.items():
        capabilities[name] = {
            "name": agent.name,
            "description": agent.description,
            "available": True,
            "endpoints": []
        }
    
    # Add endpoint mappings
    capabilities["knowledge_curator"]["endpoints"] = [
        "/process-content",
        "/find-connections"
    ]
    capabilities["research_synthesizer"]["endpoints"] = [
        "/process-content",
        "/synthesize"
    ]
    capabilities["content_explorer"]["endpoints"] = [
        "/explore-topic",
        "/process-content"
    ]
    capabilities["learning_pathfinder"]["endpoints"] = [
        "/create-learning-path"
    ]
    
    return {
        "agents": capabilities,
        "workflows": {
            "full": "All agents working together",
            "curate": "Knowledge curation only",
            "research": "Curation + Research synthesis",
            "explore": "Curation + Content exploration"
        }
    }


# Media Processing Endpoints
@router.post("/process-image", response_model=MultiAgentResult)
async def process_image(request: ImageProcessingRequest):
    """
    Process an image through OCR and AI analysis.
    
    This endpoint processes images using:
    - Azure OpenAI GPT-4V for advanced vision analysis
    - Tesseract OCR as fallback
    - AI-powered context enhancement and tagging
    - Knowledge base connection discovery
    """
    try:
        result = await crawl_ai_orchestrator.process_image(
            file_path=request.file_path,
            item_id=request.item_id,
            enhance_analysis=request.enhance_analysis
        )
        return result
        
    except Exception as e:
        raise InternalServerError(f"Image processing failed: {str(e)}")


@router.post("/process-video", response_model=MultiAgentResult)
async def process_video(request: VideoProcessingRequest):
    """
    Process a video through transcription and AI analysis.
    
    This endpoint processes videos using:
    - FFmpeg for audio extraction
    - Whisper.cpp for high-accuracy transcription
    - AI-powered content summarization and analysis
    - Metadata extraction and quality metrics
    """
    try:
        result = await crawl_ai_orchestrator.process_video(
            file_path=request.file_path,
            item_id=request.item_id,
            model_name=request.model_name,
            language=request.language,
            create_summary=request.create_summary
        )
        return result
        
    except Exception as e:
        raise InternalServerError(f"Video processing failed: {str(e)}")


@router.post("/process-audio-journal", response_model=MultiAgentResult)
async def process_audio_journal(request: AudioJournalProcessingRequest):
    """
    Process an audio journal with advanced analysis.
    
    This endpoint processes audio journals using:
    - Whisper.cpp for transcription
    - AI-powered emotion and mood analysis
    - Action item and insight extraction
    - Knowledge base connection discovery
    - Personal growth and reflection analysis
    """
    try:
        result = await crawl_ai_orchestrator.process_audio_journal(
            file_path=request.file_path,
            item_id=request.item_id,
            journal_id=request.journal_id,
            model_name=request.model_name,
            language=request.language,
            analyze_emotions=request.analyze_emotions
        )
        return result
        
    except Exception as e:
        raise InternalServerError(f"Audio journal processing failed: {str(e)}")


@router.post("/process-media-batch", response_model=MultiAgentResult)
async def process_media_batch(request: MediaBatchProcessingRequest):
    """
    Process multiple media files in batch.
    
    This endpoint allows processing multiple files of different types:
    - Images: OCR and vision analysis
    - Videos: Transcription and summarization
    - Audio journals: Emotional analysis and insights
    
    Useful for bulk uploads or mixed media processing.
    """
    try:
        result = await crawl_ai_orchestrator.process_media_batch(
            media_files=request.media_files
        )
        return result
        
    except Exception as e:
        raise InternalServerError(f"Batch media processing failed: {str(e)}")


@router.post("/upload-and-process-image")
async def upload_and_process_image(
    file: UploadFile = File(...),
    item_id: Optional[str] = None,
    enhance_analysis: bool = True
):
    """
    Upload and process an image file directly.
    
    This endpoint handles file upload and processing in one step.
    Supports common image formats: PNG, JPG, JPEG, GIF, BMP, TIFF.
    """
    try:
        import tempfile
        import os
        
        # Validate file type
        allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/gif", "image/bmp", "image/tiff"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Process the image
            result = await crawl_ai_orchestrator.process_image(
                file_path=tmp_path,
                item_id=item_id,
                enhance_analysis=enhance_analysis
            )
            
            # Add upload metadata
            result.results["upload_metadata"] = {
                "original_filename": file.filename,
                "file_size": len(content),
                "content_type": file.content_type
            }
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise InternalServerError(f"Image upload and processing failed: {str(e)}")


@router.post("/upload-and-process-video")
async def upload_and_process_video(
    file: UploadFile = File(...),
    item_id: Optional[str] = None,
    model_name: str = "base",
    language: str = "en",
    create_summary: bool = True
):
    """
    Upload and process a video file directly.
    
    This endpoint handles video file upload and processing in one step.
    Supports common video formats: MP4, AVI, MOV, MKV, WMV, FLV.
    """
    try:
        import tempfile
        import os
        
        # Validate file type
        allowed_types = ["video/mp4", "video/avi", "video/mov", "video/quicktime", "video/x-msvideo", "video/x-ms-wmv"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Process the video
            result = await crawl_ai_orchestrator.process_video(
                file_path=tmp_path,
                item_id=item_id,
                model_name=model_name,
                language=language,
                create_summary=create_summary
            )
            
            # Add upload metadata
            result.results["upload_metadata"] = {
                "original_filename": file.filename,
                "file_size": len(content),
                "content_type": file.content_type
            }
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise InternalServerError(f"Video upload and processing failed: {str(e)}")


@router.post("/upload-and-process-audio-journal")
async def upload_and_process_audio_journal(
    file: UploadFile = File(...),
    item_id: Optional[str] = None,
    journal_id: Optional[str] = None,
    model_name: str = "base",
    language: str = "en",
    analyze_emotions: bool = True
):
    """
    Upload and process an audio journal file directly.
    
    This endpoint handles audio file upload and journal processing in one step.
    Supports common audio formats: MP3, WAV, M4A, FLAC, OGG.
    """
    try:
        import tempfile
        import os
        
        # Validate file type
        allowed_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/x-m4a", "audio/flac", "audio/ogg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Process the audio journal
            result = await crawl_ai_orchestrator.process_audio_journal(
                file_path=tmp_path,
                item_id=item_id,
                journal_id=journal_id,
                model_name=model_name,
                language=language,
                analyze_emotions=analyze_emotions
            )
            
            # Add upload metadata
            result.results["upload_metadata"] = {
                "original_filename": file.filename,
                "file_size": len(content),
                "content_type": file.content_type
            }
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise InternalServerError(f"Audio journal upload and processing failed: {str(e)}")


@router.get("/media-capabilities")
async def get_media_capabilities():
    """
    Get detailed information about media processing capabilities.
    
    Returns information about supported file formats, agents, and processing options.
    """
    return {
        "media_agents": {
            "image_analyzer": {
                "name": "OCR Image Analysis Agent",
                "description": "Extracts text from images, analyzes context, and generates searchable tags",
                "supported_formats": ["PNG", "JPG", "JPEG", "GIF", "BMP", "TIFF"],
                "features": [
                    "Azure OpenAI GPT-4V vision analysis",
                    "Tesseract OCR fallback",
                    "Enhanced context analysis",
                    "Knowledge base connections",
                    "Automatic tagging"
                ]
            },
            "video_processor": {
                "name": "Video Transcription Agent",
                "description": "Transcribes videos using Whisper CPP and creates intelligent summaries",
                "supported_formats": ["MP4", "AVI", "MOV", "MKV", "WMV", "FLV"],
                "features": [
                    "FFmpeg audio extraction",
                    "Whisper.cpp transcription",
                    "AI-powered summarization",
                    "Content analysis and tagging",
                    "Video metadata extraction"
                ]
            },
            "audio_journal_processor": {
                "name": "Audio Journal Agent",
                "description": "Processes audio journals with advanced analysis and contextualization",
                "supported_formats": ["MP3", "WAV", "M4A", "FLAC", "OGG"],
                "features": [
                    "Whisper.cpp transcription",
                    "Emotion and mood analysis",
                    "Action item extraction",
                    "Knowledge base connections",
                    "Personal growth insights"
                ]
            }
        },
        "processing_options": {
            "whisper_models": ["tiny", "base", "small", "medium", "large"],
            "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
            "batch_processing": True,
            "async_processing": True,
            "upload_and_process": True
        },
        "workflows": {
            "image_analysis": "OCR extraction + AI context analysis + tagging",
            "video_processing": "Audio extraction + transcription + summarization",
            "audio_journal_processing": "Transcription + emotion analysis + insights",
            "media_batch_processing": "Process multiple files of different types"
        }
    }


# Background task support
async def process_content_background(
    content: str,
    url: Optional[str],
    task_id: str
):
    """Background task for processing large content"""
    try:
        result = await crawl_ai_orchestrator.process_content(
            content=content,
            url=url,
            workflow="full"
        )
        
        # Store result in cache or database
        # Implementation depends on your storage strategy
        
    except Exception as e:
        crawl_ai_orchestrator.logger.error(f"Background processing failed: {e}")


@router.post("/process-content-async")
async def process_content_async(
    request: ContentProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Process content asynchronously in the background.
    
    Returns a task ID immediately and processes content in background.
    Useful for large content or when immediate response is needed.
    """
    task_id = f"task-{int(datetime.utcnow().timestamp())}"
    
    background_tasks.add_task(
        process_content_background,
        content=request.content,
        url=request.url,
        task_id=task_id
    )
    
    return {
        "task_id": task_id,
        "status": "processing",
        "message": "Content processing started in background"
    }


@router.get("/media-analysis/{item_id}")
async def get_media_analysis(item_id: str):
    """
    Retrieve saved media analysis results for a specific item.
    
    Returns complete media processing data including OCR text, transcriptions,
    emotion analysis, and all associated metadata.
    """
    try:
        analysis_data = await media_persistence_service.get_media_analysis(item_id)
        
        if not analysis_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No media analysis found for item: {item_id}"
            )
        
        return {
            "status": "success",
            "item_id": item_id,
            "analysis": analysis_data,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve media analysis: {str(e)}")


@router.put("/media-processing-status")
async def update_processing_status(
    file_path: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Update processing status for a media file.
    
    Used to track processing stages: pending, processing, completed, failed.
    """
    try:
        await media_persistence_service.update_processing_status(
            file_path=file_path,
            status=status,
            metadata=metadata
        )
        
        return {
            "status": "success",
            "file_path": file_path,
            "processing_status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise InternalServerError(f"Failed to update processing status: {str(e)}")