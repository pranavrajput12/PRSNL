"""
File Processing Celery Tasks

Distributed tasks for document processing, text extraction, and file analysis
to eliminate blocking operations during file uploads.
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pathlib import Path

from langfuse import observe

from app.workers.celery_app import celery_app
from app.db.database import get_db_connection
from app.services.document_processor import DocumentProcessor
from app.services.file_ai_processor import FileAIProcessor
from app.services.unified_ai_service import UnifiedAIService
from app.services.realtime_progress_service import send_task_progress

logger = logging.getLogger(__name__)


@celery_app.task(name="files.process_document", bind=True, max_retries=3)
def process_document_task(self, file_id: str, file_path: str, options: Dict[str, Any] = None):
    """
    Process uploaded document in background.
    
    Args:
        file_id: UUID of the file record
        file_path: Path to uploaded file
        options: Processing options (extract_text, analyze_content, generate_summary, etc.)
    
    Returns:
        Document processing results
    """
    try:
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _process_document_async(self.request.id, file_id, file_path, options or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_process_document")
async def _process_document_async(task_id: str, file_id: str, file_path: str, options: Dict[str, Any]):
    """Async implementation of document processing"""
    
    try:
        await _send_progress_update(task_id, file_id, "document_processing", 0, 5, "Starting document processing")
        
        # Verify file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_info = {
            "path": file_path,
            "size": os.path.getsize(file_path),
            "extension": Path(file_path).suffix.lower()
        }
        
        await _send_progress_update(task_id, file_id, "document_processing", 1, 5, "Extracting text content")
        
        # 1. Extract text content
        document_processor = DocumentProcessor()
        extraction_result = await document_processor.extract_text(file_path)
        
        if not extraction_result["success"]:
            raise Exception(f"Text extraction failed: {extraction_result.get('error')}")
        
        extracted_text = extraction_result["text"]
        metadata = extraction_result.get("metadata", {})
        
        await _send_progress_update(task_id, file_id, "document_processing", 2, 5, "Analyzing content with AI")
        
        # 2. AI analysis if requested
        ai_analysis = {}
        if options.get("analyze_content", True) and extracted_text:
            ai_processor = FileAIProcessor()
            
            ai_analysis = await ai_processor.analyze_document(
                content=extracted_text,
                file_type=file_info["extension"],
                metadata=metadata
            )
        
        await _send_progress_update(task_id, file_id, "document_processing", 3, 5, "Generating summary")
        
        # 3. Generate summary if requested
        summary = None
        if options.get("generate_summary", True) and extracted_text:
            ai_service = UnifiedAIService()
            summary = await ai_service.generate_summary(
                content=extracted_text,
                max_length=options.get("summary_length", 200)
            )
        
        await _send_progress_update(task_id, file_id, "document_processing", 4, 5, "Storing results")
        
        # 4. Store results in database
        processing_results = {
            "extracted_text": extracted_text,
            "metadata": metadata,
            "ai_analysis": ai_analysis,
            "summary": summary,
            "file_info": file_info,
            "processing_options": options
        }
        
        async with get_db_connection() as db:
            # Update file record
            await db.execute("""
                UPDATE attachments 
                SET 
                    extracted_text = $2,
                    ai_analysis = $3,
                    metadata = $4,
                    processing_status = 'completed',
                    processed_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, 
                UUID(file_id),
                extracted_text,
                ai_analysis,
                {**metadata, "file_info": file_info}
            )
            
            # Create content item if this is a standalone document
            if options.get("create_content_item", False):
                item_id = await db.fetchval("""
                    INSERT INTO items (
                        url, title, content, summary, content_type, type, platform,
                        raw_content, processed_content, metadata, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING id
                """,
                    f"file://{file_path}",
                    metadata.get("title", f"Document: {Path(file_path).name}"),
                    extracted_text,
                    summary,
                    "document",
                    "file",
                    "local",
                    extracted_text,
                    processing_results,
                    metadata,
                    "completed"
                )
                
                processing_results["content_item_id"] = str(item_id)
        
        await _send_progress_update(task_id, file_id, "document_processing", 5, 5, "Document processing completed")
        
        return {
            "status": "completed",
            "file_id": file_id,
            "processing_results": processing_results,
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Document processing async failed: {e}", exc_info=True)
        await _send_progress_update(task_id, file_id, "document_processing", 0, 5, f"Processing failed: {str(e)}")
        raise


@celery_app.task(name="files.extract_text_from_pdf", bind=True, max_retries=2)
def extract_text_from_pdf_task(self, file_id: str, file_path: str, options: Dict[str, Any] = None):
    """
    Extract text from PDF files with OCR fallback.
    
    Args:
        file_id: UUID of the file record
        file_path: Path to PDF file
        options: Extraction options (use_ocr, extract_images, etc.)
    
    Returns:
        Text extraction results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _extract_text_from_pdf_async(self.request.id, file_id, file_path, options or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_extract_text_from_pdf")
async def _extract_text_from_pdf_async(task_id: str, file_id: str, file_path: str, options: Dict[str, Any]):
    """Async implementation of PDF text extraction"""
    
    try:
        await _send_progress_update(task_id, file_id, "pdf_extraction", 0, 3, "Starting PDF text extraction")
        
        document_processor = DocumentProcessor()
        
        # First try direct PDF text extraction
        await _send_progress_update(task_id, file_id, "pdf_extraction", 1, 3, "Extracting text from PDF")
        
        extraction_result = await document_processor.extract_pdf_text(
            file_path=file_path,
            use_ocr_fallback=options.get("use_ocr", True),
            extract_images=options.get("extract_images", False)
        )
        
        await _send_progress_update(task_id, file_id, "pdf_extraction", 2, 3, "Processing extracted content")
        
        # Process and clean extracted text
        if extraction_result["success"]:
            cleaned_text = await document_processor.clean_extracted_text(
                text=extraction_result["text"],
                remove_headers_footers=options.get("remove_headers_footers", True)
            )
            extraction_result["cleaned_text"] = cleaned_text
        
        await _send_progress_update(task_id, file_id, "pdf_extraction", 3, 3, "PDF extraction completed")
        
        return {
            "status": "completed",
            "file_id": file_id,
            "extraction_result": extraction_result,
            "extracted_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"PDF extraction async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="files.analyze_file_with_ai", bind=True, max_retries=3)
def analyze_file_with_ai_task(self, file_id: str, content: str, file_type: str, metadata: Dict[str, Any] = None):
    """
    Analyze file content with AI for insights and categorization.
    
    Args:
        file_id: UUID of the file record
        content: Extracted text content
        file_type: File extension/type
        metadata: File metadata
    
    Returns:
        AI analysis results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _analyze_file_with_ai_async(self.request.id, file_id, content, file_type, metadata or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"File AI analysis failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_analyze_file_with_ai")
async def _analyze_file_with_ai_async(task_id: str, file_id: str, content: str, file_type: str, metadata: Dict[str, Any]):
    """Async implementation of file AI analysis"""
    
    try:
        await _send_progress_update(task_id, file_id, "ai_file_analysis", 0, 4, "Starting AI file analysis")
        
        if not content.strip():
            return {
                "status": "skipped",
                "message": "No content to analyze",
                "file_id": file_id
            }
        
        file_ai_processor = FileAIProcessor()
        
        # 1. Document type classification
        await _send_progress_update(task_id, file_id, "ai_file_analysis", 1, 4, "Classifying document type")
        
        doc_classification = await file_ai_processor.classify_document_type(
            content=content,
            file_extension=file_type,
            metadata=metadata
        )
        
        # 2. Extract key information
        await _send_progress_update(task_id, file_id, "ai_file_analysis", 2, 4, "Extracting key information")
        
        key_info = await file_ai_processor.extract_key_information(
            content=content,
            document_type=doc_classification.get("type", "general")
        )
        
        # 3. Generate insights and recommendations
        await _send_progress_update(task_id, file_id, "ai_file_analysis", 3, 4, "Generating insights")
        
        insights = await file_ai_processor.generate_document_insights(
            content=content,
            document_type=doc_classification.get("type", "general"),
            key_info=key_info
        )
        
        # 4. Store analysis results
        await _send_progress_update(task_id, file_id, "ai_file_analysis", 4, 4, "Storing analysis results")
        
        analysis_results = {
            "document_classification": doc_classification,
            "key_information": key_info,
            "insights": insights,
            "analysis_metadata": {
                "content_length": len(content),
                "file_type": file_type,
                "analyzed_at": datetime.utcnow().isoformat()
            }
        }
        
        # Update database
        async with get_db_connection() as db:
            await db.execute("""
                UPDATE attachments 
                SET 
                    ai_analysis = $2,
                    document_type = $3,
                    key_insights = $4
                WHERE id = $1
            """, 
                UUID(file_id),
                analysis_results,
                doc_classification.get("type"),
                insights
            )
        
        return {
            "status": "completed",
            "file_id": file_id,
            "analysis_results": analysis_results,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"File AI analysis async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="files.batch_process_files", bind=True)
def batch_process_files_task(self, file_batch: List[Dict[str, Any]], processing_options: Dict[str, Any] = None):
    """
    Process multiple files in batch for efficiency.
    
    Args:
        file_batch: List of file info dicts with id, path, type
        processing_options: Global processing options
    
    Returns:
        Batch processing results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _batch_process_files_async(self.request.id, file_batch, processing_options or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Batch file processing failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_batch_process_files")
async def _batch_process_files_async(task_id: str, file_batch: List[Dict[str, Any]], processing_options: Dict[str, Any]):
    """Async implementation of batch file processing"""
    
    try:
        await _send_progress_update(
            task_id, "batch", "file_processing",
            0, len(file_batch), f"Starting batch processing for {len(file_batch)} files"
        )
        
        results = []
        
        # Process files concurrently but with limited concurrency
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent file processing
        
        async def process_single_file(file_info):
            async with semaphore:
                try:
                    # Delegate to individual processing task
                    result = await _process_document_async(
                        f"{task_id}_file_{file_info['id']}",
                        file_info["id"],
                        file_info["path"],
                        {**processing_options, **file_info.get("options", {})}
                    )
                    return {
                        "file_id": file_info["id"],
                        "status": "success",
                        "result": result
                    }
                except Exception as e:
                    logger.error(f"Failed to process file {file_info['id']}: {e}")
                    return {
                        "file_id": file_info["id"],
                        "status": "failed",
                        "error": str(e)
                    }
        
        # Process all files concurrently
        tasks = [process_single_file(file_info) for file_info in file_batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count success/failure
        successful_count = len([r for r in results if isinstance(r, dict) and r.get("status") == "success"])
        failed_count = len(results) - successful_count
        
        await _send_progress_update(
            task_id, "batch", "file_processing",
            len(file_batch), len(file_batch), 
            f"Batch processing completed: {successful_count} success, {failed_count} failed"
        )
        
        return {
            "status": "completed",
            "total_files": len(file_batch),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch file processing async failed: {e}", exc_info=True)
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
            
        # Send WebSocket update for real-time progress
        await send_task_progress(
            task_id=task_id,
            progress_type=progress_type,
            current_value=current_value,
            total_value=total_value,
            message=message,
            entity_id=entity_id,
            metadata={"task_type": "file_processing"}
        )
        logger.info(f"Progress update: {task_id} - {progress_type} - {current_value}/{total_value} - {message}")
        
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")