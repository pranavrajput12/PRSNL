#!/usr/bin/env python3
"""
Test the complete chat authentication flow
"""
import asyncio
import json
import httpx
import websockets

# The token from our previous generation
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTk2ZTNhNC01ODJhLTRhMjAtYmUyNS0wOTA3NGE0MWFkMmMiLCJleHAiOjE3NTI4NzQxMTksInR5cGUiOiJhY2Nlc3MiLCJqdGkiOiI4NjA1OGQzYi1lMzc1LTdlYzYtNGVlNC1mNzk5NjJkZDkxYjAifQ.EuD05wJSXK9PTAIHN6G0cjqAy0cVZELOMD5_6R3iYU0"

async def test_auth_endpoints():
    print("🔍 Testing Authentication Endpoints\n")
    
    async with httpx.AsyncClient() as client:
        # Test 1: /api/auth/me
        print("1. Testing /api/auth/me")
        response = await client.get(
            "http://localhost:8000/api/auth/me",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            user = response.json()
            print(f"   ✅ User: {user['email']}")
        else:
            print(f"   ❌ Error: {response.text}")
        
        # Test 2: /api/suggest-questions  
        print("\n2. Testing /api/suggest-questions")
        response = await client.get(
            "http://localhost:8000/api/suggest-questions",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Got {len(data.get('questions', []))} questions")
            for q in data.get('questions', [])[:3]:
                print(f"      - {q}")
        else:
            print(f"   ❌ Error: {response.text}")

async def test_websocket():
    print("\n3. Testing WebSocket Connection")
    
    # Test WebSocket with token
    uri = f"ws://localhost:8000/ws?token={ACCESS_TOKEN}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket connected successfully")
            
            # Send a test message
            test_message = {
                "type": "ping",
                "data": "test"
            }
            await websocket.send(json.dumps(test_message))
            
            # Wait for response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"   ✅ Received: {response}")
            except asyncio.TimeoutError:
                print("   ⏱️  No response received (timeout)")
                
    except Exception as e:
        print(f"   ❌ WebSocket error: {e}")

async def test_chat_websocket():
    print("\n4. Testing Chat WebSocket")
    
    # Test chat-specific WebSocket
    client_id = "test123"
    uri = f"ws://localhost:8000/ws/chat/{client_id}?token={ACCESS_TOKEN}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("   ✅ Chat WebSocket connected")
            
            # Send a chat message
            chat_message = {
                "message": "Hello, how are you?",
                "history": [],
                "chat_mode": "general",
                "conversation_id": None,
                "context_items": None
            }
            
            await websocket.send(json.dumps(chat_message))
            print("   📤 Sent chat message")
            
            # Read responses
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    print(f"   📥 Received: {data.get('type', 'unknown')} - {data.get('data', '')[:50]}...")
                    
                    if data.get('type') == 'complete':
                        break
                        
                except asyncio.TimeoutError:
                    print("   ⏱️  No more messages (timeout)")
                    break
                    
    except Exception as e:
        print(f"   ❌ Chat WebSocket error: {e}")

async def main():
    await test_auth_endpoints()
    await test_websocket()
    await test_chat_websocket()
    
    print("\n✅ All tests completed!")
    print("\n📝 To fix the frontend:")
    print("1. Open http://localhost:3004 in your browser")
    print("2. Open Developer Console (F12)")
    print("3. Go to Application > Local Storage > localhost:3004")
    print("4. Set these values:")
    print(f"   prsnl_auth_token = {ACCESS_TOKEN}")
    print("   prsnl_auth_source = prsnl")
    print("5. Refresh the page")

if __name__ == "__main__":
    asyncio.run(main())