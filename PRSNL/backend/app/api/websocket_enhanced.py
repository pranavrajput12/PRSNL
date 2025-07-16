"""
Enhanced WebSocket endpoints leveraging FastAPI 0.116.1 improvements
- Better connection handling and error recovery
- Improved async context managers
- Enhanced performance monitoring
- Better disconnect handling
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from app.core.websocket_manager import manager
from app.db.database import get_db_pool
from app.services.unified_ai_service import UnifiedAIService
from app.services.performance_monitoring import profile_endpoint, track_custom_metric

router = APIRouter()
logger = logging.getLogger(__name__)

class WebSocketMetrics:
    """Track WebSocket performance metrics"""
    def __init__(self):
        self.connections = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = 0
        self.connection_times = []
        
    def track_connection(self, duration: float):
        self.connections += 1
        self.connection_times.append(duration)
        
    def track_message_sent(self):
        self.messages_sent += 1
        
    def track_message_received(self):
        self.messages_received += 1
        
    def track_error(self):
        self.errors += 1

# Global metrics instance
ws_metrics = WebSocketMetrics()

class ProgressUpdate(BaseModel):
    task_id: str
    progress: float
    status: str
    message: Optional[str] = None
    timestamp: str

@asynccontextmanager
async def websocket_connection_manager(websocket: WebSocket, client_id: str):
    """
    Enhanced async context manager for WebSocket connections
    Leverages FastAPI 0.116.1 improvements for better resource management
    """
    start_time = time.time()
    try:
        await manager.connect(websocket, client_id)
        logger.info(f"Enhanced WebSocket connection established for {client_id}")
        
        # Send connection confirmation with improved format
        await websocket.send_json({
            "type": "connection_enhanced",
            "status": "connected",
            "client_id": client_id,
            "server_version": "0.116.1",
            "features": ["async_context", "enhanced_error_handling", "performance_monitoring"],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        yield websocket
        
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for {client_id}: {e}")
        ws_metrics.track_error()
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Connection error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            pass  # Connection might already be closed
    finally:
        connection_duration = time.time() - start_time
        ws_metrics.track_connection(connection_duration)
        manager.disconnect(client_id)
        logger.info(f"WebSocket connection closed for {client_id} after {connection_duration:.2f}s")

@router.websocket("/ws/enhanced/progress/{task_id}")
async def enhanced_progress_websocket(websocket: WebSocket, task_id: str):
    """
    Enhanced progress tracking WebSocket with FastAPI 0.116.1 improvements
    Features better connection handling and error recovery
    """
    client_id = f"progress_{task_id}"
    
    async with websocket_connection_manager(websocket, client_id):
        try:
            # Monitor task progress with enhanced error handling
            while True:
                # Check if task exists and get progress
                try:
                    pool = await get_db_pool()
                    async with pool.acquire() as conn:
                        # Query task progress from database
                        task_query = """
                        SELECT 
                            id, 
                            status, 
                            progress, 
                            message,
                            created_at,
                            updated_at
                        FROM processing_jobs 
                        WHERE id = $1
                        """
                        task_row = await conn.fetchrow(task_query, task_id)
                        
                        if not task_row:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Task {task_id} not found",
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            break
                        
                        # Send progress update with enhanced format
                        progress_update = ProgressUpdate(
                            task_id=task_id,
                            progress=float(task_row['progress'] or 0),
                            status=task_row['status'],
                            message=task_row['message'],
                            timestamp=datetime.utcnow().isoformat()
                        )
                        
                        await websocket.send_json({
                            "type": "progress",
                            "data": progress_update.dict(),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        ws_metrics.track_message_sent()
                        
                        # Check if task is complete
                        if task_row['status'] in ['completed', 'failed', 'cancelled']:
                            await websocket.send_json({
                                "type": "task_complete",
                                "task_id": task_id,
                                "final_status": task_row['status'],
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            break
                            
                except Exception as e:
                    logger.error(f"Error fetching task progress: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error fetching progress: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    ws_metrics.track_error()
                
                # Wait before next check (with improved timing)
                await asyncio.sleep(1.0)  # Check every second
                
        except Exception as e:
            logger.error(f"Error in enhanced progress WebSocket: {e}")
            ws_metrics.track_error()

@router.websocket("/ws/enhanced/chat/{client_id}")
async def enhanced_knowledge_chat(websocket: WebSocket, client_id: str):
    """
    Enhanced knowledge base chat with FastAPI 0.116.1 improvements
    Features better async handling and improved error recovery
    """
    async with websocket_connection_manager(websocket, client_id):
        ai_service = UnifiedAIService()
        
        try:
            while True:
                # Receive message with enhanced error handling
                try:
                    # Set timeout for receiving messages
                    message_data = await asyncio.wait_for(
                        websocket.receive_json(), 
                        timeout=300.0  # 5 minute timeout
                    )
                    ws_metrics.track_message_received()
                    
                except asyncio.TimeoutError:
                    await websocket.send_json({
                        "type": "timeout",
                        "message": "Connection timeout due to inactivity",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    break
                
                message = message_data.get("message", "")
                conversation_history = message_data.get("history", [])
                
                if not message:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No message provided",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue
                
                logger.debug(f"Enhanced chat - Received message from {client_id}: {message}")
                
                # Enhanced status updates
                await websocket.send_json({
                    "type": "status",
                    "message": "Processing with enhanced AI pipeline...",
                    "stage": "search",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                try:
                    # Search knowledge base with enhanced error handling
                    pool = await get_db_pool()
                    async with pool.acquire() as conn:
                        # Enhanced search query with better performance
                        search_query = """
                        SELECT 
                            id, title, 
                            COALESCE(processed_content, raw_content) as content, 
                            url, 
                            metadata->>'tags' as tags,
                            created_at, 
                            summary,
                            metadata->>'category' as category,
                            ts_rank(search_vector, plainto_tsquery('english', $1)) as rank_score
                        FROM items
                        WHERE 
                            search_vector @@ plainto_tsquery('english', $1)
                            OR to_tsvector('english', title) @@ plainto_tsquery('english', $1)
                        ORDER BY rank_score DESC
                        LIMIT 5
                        """
                        
                        search_results = await conn.fetch(search_query, message)
                        
                    # Update status
                    await websocket.send_json({
                        "type": "status",
                        "message": f"Found {len(search_results)} relevant items",
                        "stage": "generation",
                        "context_count": len(search_results),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Build enhanced context
                    context_items = []
                    for item in search_results:
                        context_items.append({
                            "title": item['title'],
                            "content": item['content'][:500] + "..." if len(item['content']) > 500 else item['content'],
                            "url": item['url'],
                            "category": item['category'],
                            "tags": item['tags'].split(',') if item['tags'] else []
                        })
                    
                    # Enhanced system prompt
                    system_prompt = f"""You are PRSNL Enhanced, an AI assistant with access to the user's knowledge base.
                    Current time: {datetime.utcnow().isoformat()}
                    Knowledge base items found: {len(context_items)}
                    
                    Answer based only on the provided context. Be helpful, accurate, and cite sources."""
                    
                    context_text = "\n\n".join([
                        f"Source: {item['title']}\nContent: {item['content']}\nURL: {item['url']}"
                        for item in context_items
                    ])
                    
                    user_prompt = f"Context:\n{context_text}\n\nQuestion: {message}"
                    
                    # Stream response with enhanced chunking
                    response_chunks = []
                    chunk_count = 0
                    
                    async for chunk in ai_service.stream_chat_response(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        history=conversation_history
                    ):
                        response_chunks.append(chunk)
                        chunk_count += 1
                        
                        await websocket.send_json({
                            "type": "chunk",
                            "content": chunk,
                            "chunk_id": chunk_count,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        ws_metrics.track_message_sent()
                    
                    # Send enhanced completion
                    citations = [
                        {
                            "title": item["title"], 
                            "url": item["url"],
                            "category": item["category"]
                        } 
                        for item in context_items if item["url"]
                    ]
                    
                    await websocket.send_json({
                        "type": "complete",
                        "citations": citations,
                        "context_count": len(search_results),
                        "chunks_sent": chunk_count,
                        "processing_time": "enhanced",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Error in enhanced chat processing: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Processing error: {str(e)}",
                        "error_type": "processing",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    ws_metrics.track_error()
                    
        except Exception as e:
            logger.error(f"Error in enhanced chat WebSocket: {e}")
            ws_metrics.track_error()

@router.websocket("/ws/enhanced/metrics")
async def websocket_metrics_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metrics monitoring
    Showcases FastAPI 0.116.1 performance monitoring capabilities
    """
    client_id = "metrics_monitor"
    
    async with websocket_connection_manager(websocket, client_id):
        try:
            while True:
                # Send current metrics
                avg_connection_time = (
                    sum(ws_metrics.connection_times) / len(ws_metrics.connection_times)
                    if ws_metrics.connection_times else 0
                )
                
                metrics_data = {
                    "total_connections": ws_metrics.connections,
                    "messages_sent": ws_metrics.messages_sent,
                    "messages_received": ws_metrics.messages_received,
                    "errors": ws_metrics.errors,
                    "avg_connection_time": round(avg_connection_time, 2),
                    "active_connections": len(manager.active_connections),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await websocket.send_json({
                    "type": "metrics",
                    "data": metrics_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                ws_metrics.track_message_sent()
                
                # Update every 5 seconds
                await asyncio.sleep(5.0)
                
        except Exception as e:
            logger.error(f"Error in metrics WebSocket: {e}")
            ws_metrics.track_error()

# Health check endpoint for WebSocket service
@router.get("/ws/enhanced/health")
async def websocket_health():
    """Health check for enhanced WebSocket service"""
    return {
        "status": "healthy",
        "fastapi_version": "0.116.1",
        "websocket_features": [
            "async_context_managers",
            "enhanced_error_handling", 
            "performance_monitoring",
            "improved_connection_management"
        ],
        "metrics": {
            "total_connections": ws_metrics.connections,
            "active_connections": len(manager.active_connections),
            "total_errors": ws_metrics.errors
        },
        "timestamp": datetime.utcnow().isoformat()
    }