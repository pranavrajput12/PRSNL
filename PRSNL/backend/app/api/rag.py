"""
RAG (Retrieval-Augmented Generation) API endpoints for PRSNL
Powered by Haystack v2

Provides intelligent question-answering and knowledge retrieval
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
import logging
from datetime import datetime

from app.services.haystack_rag_service import haystack_rag_service, HAYSTACK_AVAILABLE
from app.core.auth import get_current_user_optional
from app.db.database import get_db_pool
from app.config import settings
import asyncpg

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG"])


# Request/Response Models
class DocumentIngestionRequest(BaseModel):
    """Request model for document ingestion"""
    content: str = Field(..., min_length=1, max_length=100000)
    title: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class BatchIngestionRequest(BaseModel):
    """Request model for batch document ingestion"""
    documents: List[DocumentIngestionRequest] = Field(..., min_items=1, max_items=100)


class RAGQueryRequest(BaseModel):
    """Request model for RAG queries"""
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    filters: Optional[Dict[str, Any]] = None
    include_sources: bool = True


class HybridSearchRequest(BaseModel):
    """Request model for hybrid search"""
    query: str = Field(..., min_length=1, max_length=500)
    keyword_weight: float = Field(0.5, ge=0, le=1)
    semantic_weight: float = Field(0.5, ge=0, le=1)
    top_k: int = Field(10, ge=1, le=50)


class DocumentUpdateRequest(BaseModel):
    """Request model for document updates"""
    content: str = Field(..., min_length=1, max_length=100000)
    metadata: Optional[Dict[str, Any]] = {}


# Endpoints
@router.post("/ingest")
async def ingest_document(
    request: DocumentIngestionRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_optional),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Ingest a document into the RAG system.
    
    Documents are processed, chunked, embedded, and stored for retrieval.
    """
    if not HAYSTACK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG service not available. Please install Haystack dependencies."
        )
    
    try:
        # Prepare metadata
        metadata = request.metadata or {}
        metadata.update({
            "title": request.title,
            "source": request.source,
            "tags": request.tags,
            "ingested_by": current_user.get("id") if current_user and isinstance(current_user, dict) else "anonymous",
            "ingested_at": datetime.now().isoformat()
        })
        
        # Generate document ID
        doc_id = f"doc_{current_user.get('id', 'anon') if current_user and isinstance(current_user, dict) else 'anon'}_{datetime.now().timestamp()}"
        
        # Ingest document
        success = await haystack_rag_service.ingest_document(
            content=request.content,
            metadata=metadata,
            doc_id=doc_id
        )
        
        if success:
            # Optionally update items table for cross-reference
            if request.source and request.source.startswith("item_"):
                item_id = int(request.source.split("_")[1])
                async with db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE items 
                        SET rag_indexed = true, rag_doc_id = $1
                        WHERE id = $2
                        """,
                        doc_id, item_id
                    )
            
            return {
                "success": True,
                "document_id": doc_id,
                "message": "Document ingested successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to ingest document"
            )
            
    except Exception as e:
        logger.error(f"Document ingestion error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.post("/ingest/batch")
async def ingest_batch(
    request: BatchIngestionRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Ingest multiple documents in batch.
    
    More efficient than individual ingestion for large datasets.
    """
    if not HAYSTACK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG service not available"
        )
    
    try:
        # Prepare documents
        documents = []
        for doc_req in request.documents:
            metadata = doc_req.metadata or {}
            metadata.update({
                "title": doc_req.title,
                "source": doc_req.source,
                "tags": doc_req.tags,
                "ingested_by": current_user.get("id") if current_user and isinstance(current_user, dict) else "anonymous",
                "ingested_at": datetime.now().isoformat()
            })
            
            documents.append({
                "content": doc_req.content,
                "metadata": metadata,
                "id": f"doc_{current_user.get('id', 'anon') if current_user and isinstance(current_user, dict) else 'anon'}_{datetime.now().timestamp()}_{len(documents)}"
            })
        
        # Ingest batch
        result = await haystack_rag_service.ingest_batch(documents)
        
        return {
            "success": result["success"],
            "failed": result["failed"],
            "total": len(documents),
            "errors": result.get("errors", [])
        }
        
    except Exception as e:
        logger.error(f"Batch ingestion error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch ingestion failed: {str(e)}"
        )


@router.post("/query")
async def query_rag(
    request: RAGQueryRequest,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Query the RAG system with a question.
    
    Returns an AI-generated answer based on the knowledge base,
    along with source documents used to generate the answer.
    """
    if not HAYSTACK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG service not available"
        )
    
    try:
        logger.info(f"RAG query from user {current_user.get('id') if current_user and isinstance(current_user, dict) else 'anon'}: {request.question}")
        
        # Perform RAG query
        result = await haystack_rag_service.query(
            question=request.question,
            filters=request.filters,
            top_k=request.top_k
        )
        
        # Format response
        response = {
            "answer": result["answer"],
            "confidence": result["confidence"],
            "query": request.question
        }
        
        if request.include_sources:
            response["sources"] = result["documents"]
        
        return response
        
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/search/hybrid")
async def hybrid_search(
    request: HybridSearchRequest,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Perform hybrid search combining keyword and semantic search.
    
    Weights can be adjusted to favor keyword matching or semantic similarity.
    """
    if not HAYSTACK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG service not available"
        )
    
    try:
        # Normalize weights
        total_weight = request.keyword_weight + request.semantic_weight
        if total_weight > 0:
            keyword_weight = request.keyword_weight / total_weight
            semantic_weight = request.semantic_weight / total_weight
        else:
            keyword_weight = semantic_weight = 0.5
        
        # Perform hybrid search
        results = await haystack_rag_service.hybrid_search(
            query=request.query,
            keyword_weight=keyword_weight,
            semantic_weight=semantic_weight,
            top_k=request.top_k
        )
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results),
            "weights": {
                "keyword": keyword_weight,
                "semantic": semantic_weight
            }
        }
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.put("/documents/{document_id}")
async def update_document(
    document_id: str,
    request: DocumentUpdateRequest,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Update an existing document in the RAG system."""
    if not HAYSTACK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG service not available"
        )
    
    try:
        # Add update metadata
        metadata = request.metadata or {}
        metadata.update({
            "last_updated_by": current_user.get("id") if current_user else "anonymous",
            "last_updated_at": datetime.now().isoformat()
        })
        
        success = await haystack_rag_service.update_document(
            doc_id=document_id,
            content=request.content,
            metadata=metadata
        )
        
        if success:
            return {
                "success": True,
                "document_id": document_id,
                "message": "Document updated successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )
            
    except Exception as e:
        logger.error(f"Document update error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Delete a document from the RAG system."""
    if not HAYSTACK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG service not available"
        )
    
    try:
        success = await haystack_rag_service.delete_document(document_id)
        
        if success:
            return {
                "success": True,
                "document_id": document_id,
                "message": "Document deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )
            
    except Exception as e:
        logger.error(f"Document deletion error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Deletion failed: {str(e)}"
        )


@router.get("/stats")
async def get_rag_stats(
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Get RAG system statistics."""
    if not HAYSTACK_AVAILABLE:
        return {
            "enabled": False,
            "document_count": 0,
            "message": "RAG service not available"
        }
    
    try:
        doc_count = await haystack_rag_service.get_document_count()
        
        return {
            "enabled": True,
            "document_count": doc_count,
            "document_store_type": type(haystack_rag_service.document_store).__name__ if haystack_rag_service.document_store else "None",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_model": settings.AZURE_OPENAI_DEPLOYMENT if settings.AZURE_OPENAI_API_KEY else "Not configured"
        }
        
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        return {
            "enabled": True,
            "document_count": 0,
            "error": str(e)
        }


@router.get("/export")
async def export_knowledge_base(
    format: Literal["json", "csv"] = "json",
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Export the entire knowledge base."""
    if not HAYSTACK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG service not available"
        )
    
    try:
        result = await haystack_rag_service.export_knowledge_base(format=format)
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Ingest a file (PDF, DOCX, TXT) into the RAG system.
    
    The file will be processed and its content extracted before ingestion.
    """
    if not HAYSTACK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RAG service not available"
        )
    
    # File processing to be implemented with document processors
    # For now, return not implemented
    raise HTTPException(
        status_code=501,
        detail="File ingestion not yet implemented. Use text ingestion endpoint."
    )