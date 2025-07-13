#!/usr/bin/env python3
"""
Example: Using PRSNL's Hybrid Transcription Service

This example shows how to use the upgraded transcription system
that intelligently routes between whisper.cpp (offline) and 
Azure OpenAI Whisper (cloud) for optimal performance.
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.hybrid_transcription import (
    hybrid_transcription_service,
    TranscriptionStrategy,
)


async def transcribe_with_different_strategies():
    """Demonstrate different transcription strategies."""
    
    # Example audio file path
    audio_file = "path/to/your/audio.mp3"
    
    print("🎙️ PRSNL Hybrid Transcription Example\n")
    
    # 1. Automatic strategy (recommended for most cases)
    print("1. AUTO Strategy - Intelligent routing:")
    result = await hybrid_transcription_service.transcribe_audio(
        audio_path=audio_file,
        strategy=TranscriptionStrategy.AUTO,
        language="en"
    )
    
    if result:
        print(f"   ✅ Success! Used: {result['service_used']}")
        print(f"   📝 Text: {result['text'][:100]}...")
        print(f"   🎯 Confidence: {result['confidence']:.2f}")
        print(f"   📊 Words: {result['word_count']}")
    
    # 2. Privacy mode - force offline only
    print("\n2. PRIVACY_MODE - Offline only for sensitive content:")
    result = await hybrid_transcription_service.transcribe_audio(
        audio_path=audio_file,
        strategy=TranscriptionStrategy.PRIVACY_MODE,
        privacy_sensitive=True
    )
    
    if result:
        print(f"   ✅ Success! Used: {result['service_used']}")
        print(f"   🔒 Privacy guaranteed - no cloud services used")
    
    # 3. Prefer offline but allow cloud fallback
    print("\n3. PREFER_OFFLINE - Use local first, cloud as backup:")
    result = await hybrid_transcription_service.transcribe_audio(
        audio_path=audio_file,
        strategy=TranscriptionStrategy.PREFER_OFFLINE
    )
    
    if result:
        print(f"   ✅ Success! Used: {result['service_used']}")
        if result.get('fallback_used'):
            print(f"   🔄 Fallback was used")


async def check_service_availability():
    """Check which transcription services are available."""
    
    print("\n📊 Service Availability Check:\n")
    
    status = await hybrid_transcription_service.get_service_status()
    
    for service, info in status.items():
        if service == 'hybrid':
            print(f"🌐 {service.upper()}:")
            print(f"   Ready: {'✅' if info['ready'] else '❌'}")
            print(f"   Strategy: {info['preferred_strategy']}")
        else:
            print(f"\n📡 {service.upper()}:")
            print(f"   Available: {'✅' if info['available'] else '❌'}")
            print(f"   Status: {info['status']}")
            
            if 'accuracy' in info:
                print(f"   Accuracy: {info['accuracy']}")
                print(f"   Speed: {info['speed']}")
                print(f"   Privacy: {info['privacy']}")


async def transcribe_with_word_timestamps():
    """Example showing word-level timestamps."""
    
    audio_file = "path/to/your/audio.mp3"
    
    print("\n⏱️ Word-level Timestamps Example:\n")
    
    # Direct whisper.cpp usage for word timestamps
    from app.services.whisper_cpp_transcription import whisper_cpp_service
    
    result = await whisper_cpp_service.transcribe_audio(
        audio_path=audio_file,
        model_name="base",
        word_timestamps=True
    )
    
    if result and result.get('words'):
        print("First 5 words with timestamps:")
        for word_info in result['words'][:5]:
            print(f"   {word_info['start']:.2f}s - {word_info['end']:.2f}s: {word_info['word']}")


async def main():
    """Run all examples."""
    
    # Check what's available
    await check_service_availability()
    
    # Example: Check if we have an audio file to test with
    test_audio = "samples/test_audio.wav"
    
    if os.path.exists(test_audio):
        print(f"\n✅ Found test audio: {test_audio}")
        
        # Update the audio path
        audio_file = test_audio
        
        # Run transcription examples
        await transcribe_with_different_strategies()
        await transcribe_with_word_timestamps()
    else:
        print(f"\n⚠️  No test audio found at {test_audio}")
        print("   To test transcription, place an audio file at that location")
        print("   or update the 'audio_file' variable in the examples")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎙️ PRSNL Hybrid Transcription Example")
    print("="*60)
    print("\nThis example demonstrates the new hybrid transcription system")
    print("that uses whisper.cpp for high-accuracy offline transcription")
    print("with automatic fallback to cloud services when needed.\n")
    
    asyncio.run(main())