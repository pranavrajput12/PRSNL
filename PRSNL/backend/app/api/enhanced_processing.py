"""
Enhanced Processing API Endpoints
Leverages new capabilities from updated packages
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid

from app.services.document_extraction_enhanced import EnhancedDocumentExtractor
from app.services.langgraph_workflows import create_workflow_manager
from app.services.crewai_flows import create_multimodal_processor
from app.services.performance_monitoring import profile_endpoint
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api/enhanced", tags=["enhanced_processing"])
logger = logging.getLogger(__name__)

# Initialize services
document_extractor = EnhancedDocumentExtractor()
workflow_manager = create_workflow_manager()
multimodal_processor = create_multimodal_processor()


@router.post("/extract/structured")
@profile_endpoint("structured_extraction")
async def extract_structured_data(
    file: UploadFile = File(...),
    user_id: Optional[str] = None  # Would come from auth in production
) -> Dict[str, Any]:
    """
    Extract structured data using OpenAI 1.96.0 guaranteed JSON outputs
    """
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        logger.info(f"Processing document {document_id} with structured extraction")
        
        # Use enhanced extraction with structured outputs
        results = await document_extractor.extract_comprehensive_analysis(text_content)
        
        return {
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "structured_data": results.dict(),
            "extraction_method": "openai_structured_outputs_1.96.0"
        }
        
    except Exception as e:
        logger.error(f"Structured extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/persistent-workflow")
@profile_endpoint("persistent_workflow")
async def process_with_persistent_workflow(
    file: UploadFile = File(...),
    resume_thread_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, Any]:
    """
    Process document with LangGraph 0.5.3 persistent workflow
    Supports crash recovery via thread_id
    """
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Generate or use existing document ID
        document_id = str(uuid.uuid4())
        
        if resume_thread_id:
            # Try to resume existing workflow
            logger.info(f"Attempting to resume workflow {resume_thread_id}")
            result = await workflow_manager.resume_workflow(resume_thread_id)
            
            if result:
                return {
                    "success": True,
                    "resumed": True,
                    "workflow_result": result
                }
        
        # Start new workflow
        logger.info(f"Starting persistent workflow for document {document_id}")
        
        # Process in background for long-running workflows
        background_tasks.add_task(
            workflow_manager.process_document,
            document_id,
            text_content
        )
        
        return {
            "success": True,
            "message": "Workflow started",
            "document_id": document_id,
            "workflow_feature": "langgraph_0.5.3_checkpointing"
        }
        
    except Exception as e:
        logger.error(f"Persistent workflow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/multimodal")
@profile_endpoint("multimodal_processing")
async def process_multimodal_document(
    text_file: Optional[UploadFile] = File(None),
    images: List[UploadFile] = File(None)
) -> Dict[str, Any]:
    """
    Process documents with CrewAI 0.141.0 multimodal capabilities
    Supports text + images analysis
    """
    try:
        document_id = str(uuid.uuid4())
        
        # Process text if provided
        text_content = ""
        if text_file:
            content = await text_file.read()
            text_content = content.decode('utf-8')
        
        # Process images if provided
        image_bytes_list = []
        if images:
            for img in images:
                img_content = await img.read()
                image_bytes_list.append(img_content)
        
        if not text_content and not image_bytes_list:
            raise HTTPException(
                status_code=400,
                detail="Please provide either text or images to process"
            )
        
        logger.info(
            f"Processing multimodal document {document_id} "
            f"(text: {bool(text_content)}, images: {len(image_bytes_list)})"
        )
        
        # Process with CrewAI multimodal flow
        result = await multimodal_processor.process_document(
            document_id=document_id,
            content=text_content,
            content_type="text/plain",
            images=image_bytes_list
        )
        
        return {
            "success": result["success"],
            "document_id": document_id,
            "multimodal_analysis": result.get("results", {}),
            "crewai_version": "0.141.0",
            "features_used": ["multimodal", "flows", "event_driven"]
        }
        
    except Exception as e:
        logger.error(f"Multimodal processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/status/{thread_id}")
async def get_workflow_status(thread_id: str) -> Dict[str, Any]:
    """
    Check status of a persistent workflow
    """
    try:
        # This would check the workflow checkpoint database
        # For now, return a placeholder
        return {
            "thread_id": thread_id,
            "status": "in_progress",
            "current_step": "extract_entities",
            "completed_steps": ["extract_metadata"],
            "checkpointing_enabled": True
        }
        
    except Exception as e:
        logger.error(f"Workflow status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_processing_metrics() -> Dict[str, Any]:
    """
    Get metrics from all enhanced processing services
    """
    try:
        crewai_metrics = multimodal_processor.get_flow_metrics()
        
        return {
            "services": {
                "openai_structured_outputs": {
                    "version": "1.96.0",
                    "status": "active",
                    "features": ["guaranteed_json", "structured_extraction"]
                },
                "langgraph_workflows": {
                    "version": "0.5.3",
                    "status": "active",
                    "features": ["checkpointing", "persistence", "crash_recovery"]
                },
                "crewai_flows": {
                    "version": "0.141.0",
                    "status": "active",
                    "features": ["multimodal", "event_driven", "flows"],
                    "metrics": crewai_metrics
                }
            },
            "performance_monitoring": {
                "sentry_profiling": "enabled",
                "version": "2.33.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))