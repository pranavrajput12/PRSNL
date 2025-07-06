from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import websocket_manager
from app.services.ai_router import AIRouter, AITask, TaskType
from app.services.llm_processor import LLMProcessor
import logging
import json
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()
ai_router = AIRouter()
llm_processor = LLMProcessor()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                # Parse the incoming message
                message = json.loads(data)
                message_type = message.get('type')
                
                if message_type == 'ai_request':
                    # Handle AI request with streaming response
                    await handle_ai_request(websocket, client_id, message.get('data', {}))
                elif message_type == 'ping':
                    # Handle ping/pong for connection keep-alive
                    await websocket.send_json({"type": "pong"})
                else:
                    # Echo message back for backward compatibility
                    await websocket_manager.send_personal_message(f"You said: {data}", client_id)
                    
            except json.JSONDecodeError:
                # Handle non-JSON messages
                await websocket_manager.send_personal_message(f"You said: {data}", client_id)
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        websocket_manager.disconnect(client_id)


async def handle_ai_request(websocket: WebSocket, client_id: str, data: Dict[str, Any]):
    """Handle AI request with streaming response"""
    task_type = data.get('task', 'analyze')
    content = data.get('content', '')
    item_id = data.get('item_id')
    
    # Send initial acknowledgment
    await websocket.send_json({
        "type": "ai_response_start",
        "data": {"status": "processing"}
    })
    
    try:
        # Create AI task
        task = AITask(
            type=TaskType.CHAT if task_type == 'chat' else TaskType.SUMMARIZATION,
            content=content,
            priority=5
        )
        
        # Stream the response
        full_response = ""
        async for chunk in ai_router.stream_task(task):
            # Send each chunk as it arrives
            await websocket.send_json({
                "type": "ai_response",
                "data": {
                    "content": chunk,
                    "is_complete": False
                }
            })
            full_response += chunk
            
            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0.01)
        
        # Send completion message
        await websocket.send_json({
            "type": "ai_response_complete",
            "data": {
                "content": full_response,
                "is_complete": True,
                "item_id": item_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error in AI streaming for client {client_id}: {e}")
        await websocket.send_json({
            "type": "ai_response_error",
            "data": {
                "error": str(e),
                "message": "Failed to process AI request"
            }
        })
