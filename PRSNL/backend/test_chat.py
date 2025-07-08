#!/usr/bin/env python3
"""
Test script for the chat WebSocket endpoint
"""
import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def test_chat():
    client_id = str(uuid.uuid4())
    uri = f"ws://localhost:8000/ws/chat/{client_id}"
    
    print(f"Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for connection message...")
            
            # Wait for connection message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Connection response: {data}")
            
            # Send a test message
            test_message = {
                "message": "What articles have I saved about React?",
                "history": [],
                "chat_mode": "general"
            }
            
            print(f"\nSending message: {test_message['message']}")
            await websocket.send(json.dumps(test_message))
            
            # Receive responses
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(response)
                    
                    if data['type'] == 'status':
                        print(f"Status: {data['message']}")
                    elif data['type'] == 'chunk':
                        print(data['content'], end='', flush=True)
                    elif data['type'] == 'complete':
                        print(f"\n\nComplete! Citations: {len(data.get('citations', []))}")
                        print(f"Context items used: {data.get('context_count', 0)}")
                        if data.get('citations'):
                            print("\nCitations:")
                            for citation in data['citations']:
                                print(f"  - {citation['title']}: {citation['url']}")
                        break
                    elif data['type'] == 'error':
                        print(f"Error: {data['message']}")
                        break
                        
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
                    
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    print("Testing PRSNL Chat WebSocket...")
    print("Make sure the backend is running on port 8000")
    print("-" * 50)
    asyncio.run(test_chat())