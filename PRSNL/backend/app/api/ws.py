from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.llm_processor import LLMProcessor
from app.core.websocket_manager import manager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/ai-stream/{client_id}")
async def ai_stream(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    llm_processor = LLMProcessor()
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            if not content:
                await websocket.send_json({"error": "No content provided"})
                continue

            logger.info(f"Received content for AI stream from {client_id}: {content[:50]}...")
            
            # Stream AI responses back
            async for chunk in llm_processor.stream_process(content):
                await websocket.send_json({"chunk": chunk})

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected from AI stream")
    except Exception as e:
        logger.error(f"Error in AI stream for client {client_id}: {e}")
        await websocket.send_json({"error": str(e)})
        manager.disconnect(client_id)

@router.websocket("/ws/ai-tag-stream/{client_id}")
async def ai_tag_stream(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    llm_processor = LLMProcessor()
    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content")
            if not content:
                await websocket.send_json({"error": "No content provided"})
                continue

            logger.info(f"Received content for AI tag stream from {client_id}: {content[:50]}...")
            
            # Stream AI tag suggestions back
            async for chunk in llm_processor.stream_tag_suggestions(content):
                await websocket.send_json({"chunk": chunk})

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected from AI tag stream")
    except Exception as e:
        logger.error(f"Error in AI tag stream for client {client_id}: {e}")
        await websocket.send_json({"error": str(e)})
        manager.disconnect(client_id)