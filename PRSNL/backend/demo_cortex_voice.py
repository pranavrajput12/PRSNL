#!/usr/bin/env python3
"""
Demo script to showcase Cortex voice personality
"""
import requests
import json

API_URL = "http://localhost:8000/api"

print("🧠 Cortex Voice Demo")
print("=" * 40)

# Test the voice processing with a personalized response
response = requests.post(f"{API_URL}/voice/test")
if response.status_code == 200:
    data = response.json()
    print(f"\n📝 Original text: {data['original_text']}")
    print(f"\n🎭 Cortex says: {data['personalized_text']}")
    print(f"\n🎵 Audio generated: {data['audio_size']:,} bytes")
    print(f"\n😊 Mood: {data['mood']}")
    print("\n✅ Voice chat is working perfectly!")
else:
    print(f"❌ Error: {response.status_code}")
    
print("\n" + "=" * 40)
print("🎯 To use voice chat:")
print("1. Open http://localhost:3004")
print("2. Look for the microphone button (bottom-left)")
print("3. Hold to record, release to send")
print("4. Cortex will respond with personality!")