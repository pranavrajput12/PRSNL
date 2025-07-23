#!/usr/bin/env python3
"""
Test script for RealtimeSTT integration
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_realtime_stt():
    """Test the RealtimeSTT WebSocket endpoint"""
    uri = "ws://localhost:8000/api/voice/ws/streaming"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to RealtimeSTT WebSocket")
            
            # Start streaming
            await websocket.send(json.dumps({
                "type": "start"
            }))
            
            # Listen for messages
            timeout = 30  # 30 seconds timeout
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        websocket.recv(), 
                        timeout=1.0
                    )
                    
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "streaming_started":
                        logger.info("Streaming started successfully")
                        logger.info("Say something into your microphone...")
                        
                    elif msg_type == "partial":
                        logger.info(f"Partial: {data.get('text')}")
                        
                    elif msg_type == "final":
                        logger.info(f"Final: {data.get('text')}")
                        
                    elif msg_type == "error":
                        logger.error(f"Error: {data.get('message')}")
                        break
                        
                except asyncio.TimeoutError:
                    # Check if we've exceeded total timeout
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        logger.info("Timeout reached, stopping stream")
                        break
                        
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
            
            # Stop streaming
            await websocket.send(json.dumps({
                "type": "stop"
            }))
            
            # Wait for stop confirmation
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "streaming_stopped":
                logger.info("Streaming stopped successfully")
                accumulated = data.get("accumulated_text", "")
                logger.info(f"Accumulated text: {accumulated}")
                
                # Test processing the text
                if accumulated:
                    logger.info("Processing accumulated text with AI...")
                    await websocket.send(json.dumps({
                        "type": "process",
                        "text": accumulated,
                        "include_audio": False  # Skip audio for testing
                    }))
                    
                    # Wait for AI response
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    while data.get("type") == "processing":
                        response = await websocket.recv()
                        data = json.loads(response)
                    
                    if data.get("type") == "ai_response":
                        logger.info(f"AI Response: {data['data']['personalized_text']}")
                        
    except websockets.exceptions.ConnectionRefused:
        logger.error("Could not connect to WebSocket. Is the backend running?")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_language_change():
    """Test changing language during streaming"""
    uri = "ws://localhost:8000/api/voice/ws/streaming"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Testing language change...")
            
            # Change language to Spanish
            await websocket.send(json.dumps({
                "type": "set_language",
                "language": "es"
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "language_changed":
                logger.info(f"Language changed to: {data.get('language')}")
                
    except Exception as e:
        logger.error(f"Language test failed: {e}")


if __name__ == "__main__":
    logger.info("Starting RealtimeSTT integration test...")
    logger.info("Make sure the backend is running with: cd backend && uvicorn app.main:app --reload --port 8000")
    
    # Run tests
    asyncio.run(test_realtime_stt())
    asyncio.run(test_language_change())