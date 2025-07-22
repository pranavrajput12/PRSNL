#!/usr/bin/env python3
"""
Test voice chat with Cortex personality
"""
import asyncio
import requests
import base64

async def test_voice_endpoints():
    """Test voice endpoints"""
    base_url = "http://localhost:8000/api"
    
    print("Testing Voice Chat with Cortex Personality")
    print("=" * 50)
    
    # Test 1: Check voice health
    print("\n1. Testing voice health endpoint...")
    try:
        response = requests.get(f"{base_url}/voice/health")
        if response.status_code == 200:
            print("✅ Voice health check passed:")
            print(f"   {response.json()}")
        else:
            print(f"❌ Voice health check failed: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Test voice processing without WebSocket
    print("\n2. Testing voice processing...")
    try:
        response = requests.post(f"{base_url}/voice/test")
        if response.status_code == 200:
            data = response.json()
            print("✅ Voice processing test passed:")
            print(f"   Original: {data['original_text']}")
            print(f"   Personalized: {data['personalized_text']}")
            print(f"   Mood: {data['mood']}")
            print(f"   Audio size: {data['audio_size']} bytes")
        else:
            print(f"❌ Voice processing test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Voice Chat Integration Summary:")
    print("- Speech-to-Text: OpenAI Whisper (base model)")
    print("- Text-to-Speech: Microsoft Edge TTS (Aria Neural voice)")
    print("- Personality: Cortex - Your Prefrontal Assistant")
    print("- Features: Real-time WebSocket streaming, mood detection, natural speech")

if __name__ == "__main__":
    asyncio.run(test_voice_endpoints())