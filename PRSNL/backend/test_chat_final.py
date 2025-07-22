#!/usr/bin/env python3
"""
Test chat knowledge base retrieval
"""
import asyncio
import websockets
import json

async def test_chat():
    """Test chat with knowledge base queries"""
    # Connect to WebSocket
    uri = "ws://localhost:8000/ws/chat/test-client"
    
    print("Connecting to chat WebSocket...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Testing knowledge base retrieval...\n")
            
            # Test queries
            test_queries = [
                "What do you know about SEO tools?",
                "Tell me about ChatGPT for keyword research",
                "What AI automation tools do you have?",
                "Search for Facebook groups"
            ]
            
            for query in test_queries:
                print(f"Query: {query}")
                print("-" * 50)
                
                # Send message
                await websocket.send(json.dumps({
                    "message": query
                }))
                
                # Collect response
                full_response = ""
                message_complete = False
                
                while not message_complete:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if data.get("type") == "chunk":
                        full_response += data.get("data", "")
                        print(".", end="", flush=True)
                    elif data.get("type") == "complete":
                        message_complete = True
                        print("\n")
                        
                        # Check if citations were included
                        if data.get("citations"):
                            print(f"Citations found: {len(data['citations'])}")
                            for citation in data['citations']:
                                print(f"  - {citation.get('title', 'Unknown')}")
                        else:
                            print("No citations found")
                            
                        if data.get("suggested_items"):
                            print(f"Suggested items: {len(data['suggested_items'])}")
                    elif data.get("type") == "error":
                        print(f"Error: {data.get('data', 'Unknown error')}")
                        break
                
                print(f"\nResponse preview: {full_response[:200]}...")
                print("=" * 70 + "\n")
                
                # Small delay between queries
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"Connection error: {str(e)}")
        print("Make sure the backend is running on port 8000")

if __name__ == "__main__":
    asyncio.run(test_chat())