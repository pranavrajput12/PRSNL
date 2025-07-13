#!/usr/bin/env python3
"""
Test script for whisper.cpp integration with hybrid transcription service.

Tests:
1. Service availability detection
2. Model downloading
3. Audio transcription with different strategies
4. Performance comparison vs Vosk
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.hybrid_transcription import (
    HybridTranscriptionService,
    TranscriptionStrategy,
)
from app.services.whisper_cpp_transcription import whisper_cpp_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_whisper_cpp_availability():
    """Test if whisper.cpp is available and models can be downloaded."""
    print("\n" + "="*60)
    print("🧪 Testing whisper.cpp Availability")
    print("="*60)
    
    # Check if pywhispercpp is installed
    try:
        import pywhispercpp
        print("✅ pywhispercpp is installed")
        print(f"   Version: {pywhispercpp.__version__ if hasattr(pywhispercpp, '__version__') else 'Unknown'}")
    except ImportError:
        print("❌ pywhispercpp is NOT installed")
        print("   Run: pip install pywhispercpp>=1.2.0")
        return False
    
    # Test model download
    print("\n📥 Testing model download...")
    model_names = ["tiny", "base"]
    
    for model_name in model_names:
        print(f"\n   Downloading {model_name} model...")
        success = await whisper_cpp_service.ensure_model_available(model_name)
        if success:
            print(f"   ✅ {model_name} model ready")
            model_info = await whisper_cpp_service.get_model_info(model_name)
            print(f"      Size: {model_info['size_mb']}MB")
            print(f"      Accuracy: {model_info['accuracy']}")
            print(f"      Speed: {model_info['speed']}")
        else:
            print(f"   ❌ Failed to download {model_name} model")
    
    return True


async def test_hybrid_service_status():
    """Test hybrid transcription service status."""
    print("\n" + "="*60)
    print("🔍 Testing Hybrid Service Status")
    print("="*60)
    
    service = HybridTranscriptionService()
    status = await service.get_service_status()
    
    print("\n📊 Service Status:")
    for service_name, info in status.items():
        if service_name == 'hybrid':
            print(f"\n🌐 {service_name.upper()}:")
            print(f"   Ready: {info['ready']}")
            print(f"   Recommended Strategy: {info['preferred_strategy']}")
        else:
            print(f"\n📡 {service_name.upper()}:")
            print(f"   Available: {info['available']}")
            print(f"   Status: {info['status']}")
            if 'accuracy' in info:
                print(f"   Accuracy: {info['accuracy']}")
                print(f"   Speed: {info['speed']}")
                print(f"   Privacy: {info['privacy']}")
            if 'rate_limited' in info:
                print(f"   Rate Limited: {info['rate_limited']}")
                print(f"   Recent Requests: {info['requests_in_last_minute']}")


async def test_transcription_strategies():
    """Test different transcription strategies."""
    print("\n" + "="*60)
    print("🎙️ Testing Transcription Strategies")
    print("="*60)
    
    # Create a test audio file path
    test_audio = "samples/test_audio.wav"
    
    # Check if test audio exists
    if not os.path.exists(test_audio):
        print(f"\n⚠️  Test audio file not found: {test_audio}")
        print("   Creating a simple test audio file...")
        
        # Create samples directory
        os.makedirs("samples", exist_ok=True)
        
        # Generate a simple test WAV file using text-to-speech or download
        # For now, we'll skip actual transcription if no test file
        print("   ℹ️  Skipping actual transcription tests (no test audio)")
        return
    
    service = HybridTranscriptionService()
    
    # Test different strategies
    strategies = [
        TranscriptionStrategy.AUTO,
        TranscriptionStrategy.PREFER_OFFLINE,
        TranscriptionStrategy.OFFLINE_ONLY,
        TranscriptionStrategy.PRIVACY_MODE
    ]
    
    for strategy in strategies:
        print(f"\n🔧 Testing strategy: {strategy.value}")
        
        start_time = time.time()
        result = await service.transcribe_audio(
            audio_path=test_audio,
            strategy=strategy,
            language="en"
        )
        end_time = time.time()
        
        if result:
            print(f"   ✅ Transcription successful")
            print(f"   Service used: {result.get('service_used', 'unknown')}")
            print(f"   Primary service: {result.get('primary_service', 'none')}")
            print(f"   Fallback used: {result.get('fallback_used', False)}")
            print(f"   Processing time: {end_time - start_time:.2f}s")
            print(f"   Text preview: {result['text'][:100]}...")
            print(f"   Word count: {result.get('word_count', 0)}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
        else:
            print(f"   ❌ Transcription failed")


async def compare_vosk_vs_whisper():
    """Compare Vosk and whisper.cpp performance."""
    print("\n" + "="*60)
    print("⚖️  Comparing Vosk vs whisper.cpp")
    print("="*60)
    
    test_audio = "samples/test_audio.wav"
    
    if not os.path.exists(test_audio):
        print("\n⚠️  No test audio available for comparison")
        return
    
    service = HybridTranscriptionService()
    
    # Test with Vosk only
    print("\n🎯 Testing Vosk...")
    if service.vosk_available:
        start_time = time.time()
        vosk_result = await service._transcribe_with_service("vosk", test_audio, "en")
        vosk_time = time.time() - start_time
        
        if vosk_result:
            print(f"   ✅ Vosk transcription completed")
            print(f"   Time: {vosk_time:.2f}s")
            print(f"   Confidence: {vosk_result.get('confidence', 0):.2f}")
            print(f"   Word count: {vosk_result.get('word_count', 0)}")
    else:
        print("   ❌ Vosk not available")
    
    # Test with whisper.cpp
    print("\n🚀 Testing whisper.cpp...")
    if service.whisper_cpp_available:
        start_time = time.time()
        whisper_result = await service._transcribe_with_service("whisper_cpp", test_audio, "en")
        whisper_time = time.time() - start_time
        
        if whisper_result:
            print(f"   ✅ whisper.cpp transcription completed")
            print(f"   Time: {whisper_time:.2f}s")
            print(f"   Confidence: {whisper_result.get('confidence', 0):.2f}")
            print(f"   Word count: {whisper_result.get('word_count', 0)}")
            print(f"   Model used: {whisper_result.get('model_used', 'unknown')}")
    else:
        print("   ❌ whisper.cpp not available")


async def test_model_management():
    """Test whisper.cpp model management features."""
    print("\n" + "="*60)
    print("🗄️  Testing Model Management")
    print("="*60)
    
    # List available models
    print("\n📋 Available whisper.cpp models:")
    for model_name in ["tiny", "base", "small", "medium", "large"]:
        info = await whisper_cpp_service.get_model_info(model_name)
        status = "✅" if info['available'] else "❌"
        print(f"   {status} {model_name}: {info['size_mb']}MB - {info['accuracy']}")
    
    # Test language support
    print("\n🌍 Supported languages:")
    languages = await whisper_cpp_service.get_supported_languages()
    print(f"   Total: {len(languages)} languages")
    print(f"   Sample: {', '.join(languages[:10])}...")


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 PRSNL whisper.cpp Integration Test Suite")
    print("="*80)
    
    try:
        # Test 1: Check availability
        if not await test_whisper_cpp_availability():
            print("\n❌ whisper.cpp is not available. Please install pywhispercpp.")
            return
        
        # Test 2: Service status
        await test_hybrid_service_status()
        
        # Test 3: Model management
        await test_model_management()
        
        # Test 4: Transcription strategies
        await test_transcription_strategies()
        
        # Test 5: Performance comparison
        await compare_vosk_vs_whisper()
        
        print("\n" + "="*80)
        print("✅ All tests completed!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("Test suite failed")


if __name__ == "__main__":
    asyncio.run(main())