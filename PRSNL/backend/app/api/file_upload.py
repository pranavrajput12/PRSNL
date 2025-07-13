"""File upload API endpoints"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import asyncpg
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    status,
    UploadFile,
)
from pydantic import BaseModel

from app.core.exceptions import InternalServerError, InvalidInput
from app.db.database import get_db_connection, get_db_pool, update_item_embedding
from app.middleware.rate_limit import (
    bulk_operation_limiter,
    capture_limiter,
    file_upload_limiter,
)
from app.models.schemas import ItemStatus
from app.services.cache import CacheKeys, invalidate_cache
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import embedding_service
from app.services.file_ai_processor import FileAIProcessor

logger = logging.getLogger(__name__)

router = APIRouter()

class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    file_id: UUID
    item_id: UUID
    original_filename: str
    file_size: int
    file_category: str
    processing_status: str
    message: str

class FileProcessingStatus(BaseModel):
    """File processing status response"""
    file_id: UUID
    status: str
    progress: float
    message: str
    extracted_text_length: Optional[int] = None
    word_count: Optional[int] = None
    ai_analysis_complete: bool = False

@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=FileUploadResponse, dependencies=[Depends(file_upload_limiter)])
@capture_limiter
@invalidate_cache(patterns=[f"{CacheKeys.STATS}:*"])
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    url: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    highlight: Optional[str] = Form(None),
    content_type: str = Form("auto"),
    enable_summarization: bool = Form(False),
    tags: Optional[str] = Form(None),  # JSON string of tags
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Upload and process files
    
    Args:
        files: The uploaded files
        url: Optional URL 
        title: Optional title for the item
        highlight: Optional highlight text
        content_type: Content type classification
        enable_summarization: Whether to enable AI summarization
        tags: JSON string of tags
        db_connection: Database connection
    """
    
    # Validate files
    if not files or len(files) == 0:
        raise InvalidInput("No files provided")
    
    # For now, process only the first file
    file = files[0]
    
    if not file.filename:
        raise InvalidInput("No file provided")
    
    if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
        raise InvalidInput("File size exceeds 50MB limit")
    
    # Parse tags
    parsed_tags = []
    if tags:
        try:
            parsed_tags = json.loads(tags)
        except json.JSONDecodeError:
            logger.warning(f"Invalid tags JSON: {tags}")
    
    # Create item and file IDs
    item_id = uuid4()
    file_id = uuid4()
    
    try:
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise InvalidInput("Empty file provided")
        
        # Initialize processors
        document_processor = DocumentProcessor()
        
        # Process file
        processing_result = await document_processor.process_file(
            file_content, file.filename, item_id
        )
        
        # Generate title from filename if not provided
        if not title:
            title = _generate_title_from_filename(file.filename)
        
        # Store in database
        await _store_file_and_item(
            db_connection, item_id, file_id, file.filename, 
            processing_result, title, content_type, enable_summarization, parsed_tags
        )
        
        # Process with AI in background if enabled
        if enable_summarization:
            background_tasks.add_task(
                _process_file_with_ai,
                file_id, item_id, processing_result, 
                file.filename, content_type
            )
        
        logger.info(f"File uploaded successfully: {file.filename} -> {file_id}")
        
        return FileUploadResponse(
            file_id=file_id,
            item_id=item_id,
            original_filename=file.filename,
            file_size=len(file_content),
            file_category=processing_result['file_info']['category'],
            processing_status="completed" if not enable_summarization else "processing",
            message="File uploaded and processed successfully"
        )
        
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}", exc_info=True)
        # Clean up any partial data
        await _cleanup_failed_upload(db_connection, item_id, file_id)
        raise InternalServerError(f"File upload failed: {str(e)}")

@router.get("/status/{file_id}", response_model=FileProcessingStatus)
async def get_file_processing_status(
    file_id: UUID,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Get processing status for a file"""
    
    file_record = await db_connection.fetchrow("""
        SELECT 
            f.*,
            i.title,
            i.summary,
            i.status as item_status
        FROM files f
        JOIN items i ON f.item_id = i.id
        WHERE f.id = $1
    """, file_id)
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Calculate progress
    progress = _calculate_processing_progress(file_record)
    
    return FileProcessingStatus(
        file_id=file_id,
        status=file_record['processing_status'],
        progress=progress,
        message=_get_status_message(file_record),
        extracted_text_length=len(file_record['extracted_text'] or ''),
        word_count=file_record['word_count'],
        ai_analysis_complete=file_record['item_status'] == 'completed'
    )

@router.get("/content/{file_id}")
async def get_file_content(
    file_id: UUID,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Get file content and metadata"""
    
    file_record = await db_connection.fetchrow("""
        SELECT 
            f.*,
            i.title,
            i.summary,
            i.tags,
            i.status as item_status,
            i.created_at as item_created_at
        FROM files f
        JOIN items i ON f.item_id = i.id
        WHERE f.id = $1
    """, file_id)
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Get tags
    tags = await db_connection.fetch("""
        SELECT t.name 
        FROM tags t
        JOIN item_tags it ON t.id = it.tag_id
        WHERE it.item_id = $1
    """, file_record['item_id'])
    
    return {
        'file_id': file_record['id'],
        'item_id': file_record['item_id'],
        'original_filename': file_record['original_filename'],
        'file_category': file_record['file_category'],
        'file_size': file_record['file_size'],
        'mime_type': file_record['mime_type'],
        'extracted_text': file_record['extracted_text'],
        'word_count': file_record['word_count'],
        'page_count': file_record['page_count'],
        'processing_status': file_record['processing_status'],
        'thumbnail_path': file_record['thumbnail_path'],
        'title': file_record['title'],
        'summary': file_record['summary'],
        'tags': [tag['name'] for tag in tags],
        'created_at': file_record['item_created_at'],
        'processed_at': file_record['processed_at']
    }

@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Delete a file and its associated item"""
    
    # Get file info
    file_record = await db_connection.fetchrow("""
        SELECT item_id, file_path, thumbnail_path, text_file_path
        FROM files
        WHERE id = $1
    """, file_id)
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        # Delete file from storage
        document_processor = DocumentProcessor()
        
        if file_record['file_path']:
            await document_processor.delete_file(file_record['file_path'])
        
        if file_record['thumbnail_path']:
            await document_processor.delete_file(file_record['thumbnail_path'])
        
        if file_record['text_file_path']:
            await document_processor.delete_file(file_record['text_file_path'])
        
        # Delete from database (cascades to associated item)
        await db_connection.execute("""
            DELETE FROM items WHERE id = $1
        """, file_record['item_id'])
        
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {str(e)}")
        raise InternalServerError(f"Failed to delete file: {str(e)}")

@router.get("/stats")
async def get_file_stats(
    db_connection: asyncpg.Connection = Depends(get_db_connection)
):
    """Get file storage and processing statistics"""
    
    # Get storage stats
    storage_stats = await db_connection.fetch("""
        SELECT * FROM file_storage_stats
    """)
    
    # Get processing stats
    processing_stats = await db_connection.fetch("""
        SELECT * FROM file_processing_stats
    """)
    
    # Get recent files
    recent_files = await db_connection.fetch("""
        SELECT * FROM recent_files
        LIMIT 10
    """)
    
    return {
        'storage_stats': [dict(record) for record in storage_stats],
        'processing_stats': [dict(record) for record in processing_stats],
        'recent_files': [dict(record) for record in recent_files]
    }

# Helper functions

async def _store_file_and_item(
    db_connection: asyncpg.Connection,
    item_id: UUID,
    file_id: UUID,
    filename: str,
    processing_result: Dict[str, Any],
    title: str,
    content_type: str,
    enable_summarization: bool,
    tags: List[str]
):
    """Store file and item in database"""
    
    file_info = processing_result['file_info']
    extracted_content = processing_result['extracted_content']
    
    # Create item - use content_type for type field to ensure consistency
    # If content_type is 'auto', use the detected category
    if content_type == 'auto':
        item_type = file_info['category']
    else:
        item_type = content_type if content_type else file_info['category']
    logger.info(f"🗂️ Creating file item: content_type={content_type} → type={item_type}")
    
    await db_connection.execute("""
        INSERT INTO items (
            id, title, summary, status, type, content_type, 
            has_files, file_count, enable_summarization, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
    """, 
        item_id, title, f"File: {filename}", 
        ItemStatus.COMPLETED, item_type, content_type,
        True, 1, enable_summarization
    )
    
    # Create file record
    await db_connection.execute("""
        INSERT INTO files (
            id, item_id, original_filename, file_hash, file_path,
            file_size, mime_type, file_extension, file_category,
            extracted_text, text_file_path, word_count, page_count,
            extraction_method, thumbnail_path, processing_status,
            processed_at, created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
            $14, $15, $16, $17, NOW(), NOW()
        )
    """,
        file_id, item_id, filename, processing_result['file_hash'],
        processing_result['file_path'], file_info['size'], file_info['mime_type'],
        file_info['extension'], file_info['category'],
        extracted_content.get('text'), processing_result.get('text_file_path'),
        extracted_content.get('word_count', 0), extracted_content.get('pages', 0),
        extracted_content.get('extraction_method'), processing_result.get('thumbnail_path'),
        'completed', datetime.now()
    )
    
    # Add tags
    for tag_name in tags:
        tag_id = await db_connection.fetchval("""
            INSERT INTO tags (name) VALUES ($1)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """, tag_name.lower())
        
        await db_connection.execute("""
            INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """, item_id, tag_id)

async def _process_file_with_ai(
    file_id: UUID,
    item_id: UUID,
    processing_result: Dict[str, Any],
    filename: str,
    content_type: str
):
    """Process file with AI analysis in background"""
    
    try:
        logger.info(f"Starting AI processing for file: {filename}")
        
        # Initialize AI processor
        ai_processor = FileAIProcessor()
        
        # Process with AI
        ai_analysis = await ai_processor.process_file_content(
            processing_result['extracted_content'],
            processing_result['file_info'],
            filename,
            content_type
        )
        
        # Update database with AI results
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Update item with AI analysis
            await conn.execute("""
                UPDATE items 
                SET 
                    title = $2,
                    summary = $3,
                    metadata = jsonb_set(
                        COALESCE(metadata, '{}'), 
                        '{ai_analysis}', 
                        to_jsonb($4::jsonb)
                    ),
                    updated_at = NOW()
                WHERE id = $1
            """,
                item_id, ai_analysis.title, ai_analysis.summary,
                json.dumps({
                    'summary': ai_analysis.summary,
                    'tags': ai_analysis.tags,
                    'key_points': ai_analysis.key_points,
                    'sentiment': ai_analysis.sentiment,
                    'reading_time': ai_analysis.reading_time,
                    'entities': ai_analysis.entities,
                    'questions': ai_analysis.questions,
                    'language': ai_analysis.language,
                    'content_type_detected': ai_analysis.content_type_detected,
                    'processed_at': datetime.now().isoformat()
                })
            )
            
            # Add AI-generated tags
            for tag_name in ai_analysis.tags:
                tag_id = await conn.fetchval("""
                    INSERT INTO tags (name) VALUES ($1)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                """, tag_name.lower())
                
                await conn.execute("""
                    INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                """, item_id, tag_id)
            
            # Generate and store embedding
            if ai_analysis.summary:
                try:
                    embedding = await embedding_service.generate_embedding(ai_analysis.summary)
                    if embedding:
                        await update_item_embedding(str(item_id), embedding)
                        logger.info(f"Generated embedding for file item {item_id}")
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for file {item_id}: {e}")
        
        logger.info(f"AI processing completed for file: {filename}")
        
    except Exception as e:
        logger.error(f"AI processing failed for file {filename}: {str(e)}", exc_info=True)
        
        # Update file status to indicate AI processing failed
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE files 
                SET processing_status = 'ai_failed',
                    processing_error = $2,
                    updated_at = NOW()
                WHERE id = $1
            """, file_id, str(e))

async def _cleanup_failed_upload(
    db_connection: asyncpg.Connection,
    item_id: UUID,
    file_id: UUID
):
    """Clean up database records for failed upload"""
    try:
        await db_connection.execute("DELETE FROM items WHERE id = $1", item_id)
        await db_connection.execute("DELETE FROM files WHERE id = $1", file_id)
    except Exception as e:
        logger.error(f"Failed to cleanup failed upload: {e}")

def _generate_title_from_filename(filename: str) -> str:
    """Generate title from filename"""
    name_without_ext = filename.rsplit('.', 1)[0]
    name_without_ext = name_without_ext.replace('_', ' ').replace('-', ' ')
    return ' '.join(word.capitalize() for word in name_without_ext.split())

def _calculate_processing_progress(file_record: Dict[str, Any]) -> float:
    """Calculate processing progress percentage"""
    status = file_record['processing_status']
    
    if status == 'completed':
        return 100.0
    elif status == 'processing':
        return 50.0
    elif status == 'ai_failed':
        return 75.0  # File processed but AI failed
    elif status == 'failed':
        return 0.0
    else:
        return 25.0  # Default for unknown status

def _get_status_message(file_record: Dict[str, Any]) -> str:
    """Get human-readable status message"""
    status = file_record['processing_status']
    
    if status == 'completed':
        return "File processed successfully"
    elif status == 'processing':
        return "AI analysis in progress"
    elif status == 'ai_failed':
        return "File processed, AI analysis failed"
    elif status == 'failed':
        return f"Processing failed: {file_record.get('processing_error', 'Unknown error')}"
    else:
        return "Processing status unknown"