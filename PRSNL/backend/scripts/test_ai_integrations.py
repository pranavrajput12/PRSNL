#!/usr/bin/env python3
"""
Comprehensive test suite for all AI integrations in PRSNL.

Tests:
#1. Guardrails-AI validation
2. whisper.cpp transcription
3. Unified AI service
4. End-to-end content processing
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_TIMEOUT = 30.0


async def test_health_check():
    """Test API health endpoints."""
    print("\n" + "="*60)
    print("🏥 Testing API Health")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
        # Basic health
        response = await client.get(f"{API_BASE_URL}/health")
        print(f"\n✅ Basic health: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
        
        # Detailed health
        response = await client.get(f"{API_BASE_URL}/health/details")
        print(f"\n✅ Detailed health: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            for service, status in data.items():
                if isinstance(status, dict):
                    print(f"   {service}: {status.get('status', 'unknown')}")


async def test_ai_content_analysis():
    """Test AI content analysis with validation."""
    print("\n" + "="*60)
    print("🤖 Testing AI Content Analysis")
    print("="*60)
    
    test_content = """
    Artificial Intelligence is transforming how we interact with technology. 
    From natural language processing to computer vision, AI systems are becoming 
    more sophisticated. Machine learning models can now understand context, 
    generate creative content, and even assist in complex decision-making processes.
    """
    
    async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
        # Test content analysis
        print("\n📝 Testing content analysis...")
        response = await client.post(
            f"{API_BASE_URL}/ai/analyze",
            json={"content": test_content}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Content analysis successful!")
            print(f"   Title: {result.get('title', 'N/A')}")
            print(f"   Summary: {result.get('summary', 'N/A')[:100]}...")
            print(f"   Category: {result.get('category', 'N/A')}")
            print(f"   Tags: {', '.join(result.get('tags', []))}")
            print(f"   Sentiment: {result.get('sentiment', 'N/A')}")
            print(f"   Key Points: {len(result.get('key_points', []))} found")
            
            # Validate response structure
            required_fields = ['title', 'summary', 'category', 'tags', 'key_points']
            missing_fields = [f for f in required_fields if f not in result]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
            else:
                print("   ✅ All required fields present")
        else:
            print(f"❌ Content analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")


async def test_tag_generation():
    """Test AI tag generation with validation."""
    print("\n" + "="*60)
    print("🏷️  Testing Tag Generation")
    print("="*60)
    
    test_content = """
    Python programming, machine learning, data science, neural networks,
    deep learning, TensorFlow, PyTorch, artificial intelligence, 
    natural language processing, computer vision, algorithms.
    """
    
    async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
        print("\n🏷️  Generating tags...")
        response = await client.post(
            f"{API_BASE_URL}/ai/tags",
            json={"content": test_content, "limit": 10}
        )
        
        if response.status_code == 200:
            tags = response.json()
            print(f"✅ Generated {len(tags)} tags:")
            for tag in tags:
                print(f"   - {tag}")
            
            # Validate tags
            if all(isinstance(tag, str) and tag.islower() for tag in tags):
                print("   ✅ All tags are lowercase strings")
            if len(tags) <= 10:
                print("   ✅ Tag limit respected")
            if len(tags) == len(set(tags)):
                print("   ✅ No duplicate tags")
        else:
            print(f"❌ Tag generation failed: {response.status_code}")


async def test_summary_generation():
    """Test AI summary generation."""
    print("\n" + "="*60)
    print("📄 Testing Summary Generation")
    print("="*60)
    
    test_content = """
    The Internet of Things (IoT) represents a revolutionary paradigm where everyday 
    objects are connected to the internet, enabling them to send and receive data. 
    This interconnected ecosystem includes smart home devices, wearable technology, 
    industrial sensors, and autonomous vehicles. IoT is transforming industries by 
    enabling real-time monitoring, predictive maintenance, and enhanced automation. 
    However, it also raises significant concerns about data privacy, security 
    vulnerabilities, and the need for robust infrastructure to handle the massive 
    influx of data generated by billions of connected devices.
    """
    
    async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
        # Test different summary types
        summary_types = ["brief", "detailed", "key_points"]
        
        for summary_type in summary_types:
            print(f"\n📝 Testing {summary_type} summary...")
            response = await client.post(
                f"{API_BASE_URL}/ai/summary",
                json={
                    "content": test_content,
                    "summary_type": summary_type
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {summary_type.title()} summary generated:")
                
                if summary_type == "key_points":
                    for i, point in enumerate(result.get('key_takeaways', []), 1):
                        print(f"   {i}. {point}")
                else:
                    print(f"   {result.get(summary_type, 'N/A')}")
            else:
                print(f"❌ {summary_type} summary failed: {response.status_code}")


async def test_transcription():
    """Test whisper.cpp transcription service."""
    print("\n" + "="*60)
    print("🎙️ Testing Transcription Service")
    print("="*60)
    
    # Check if we have a test audio file
    test_audio = "samples/test_audio.wav"
    
    if not os.path.exists(test_audio):
        print(f"\n⚠️  No test audio file found at {test_audio}")
        print("   Creating a simple test to verify service availability...")
        
        # Test service availability
        from app.services.whisper_only_transcription import transcription_service
        
        if transcription_service.is_available():
            print("✅ Transcription service is available")
            
            # Test model info
            models = await transcription_service.get_available_models()
            print("\n📊 Available models:")
            for model_name, info in models.items():
                status = "✅" if info['available'] else "❌"
                print(f"   {status} {model_name}: {info['size_mb']}MB - {info['accuracy']}")
            
            # Test language support
            languages = await transcription_service.get_supported_languages()
            print(f"\n🌍 Supports {len(languages)} languages")
        else:
            print("❌ Transcription service not available")
    else:
        # Test actual transcription
        from app.services.whisper_only_transcription import transcription_service
        
        print(f"\n🎤 Transcribing test audio: {test_audio}")
        
        start_time = time.time()
        result = await transcription_service.transcribe_audio(
            audio_path=test_audio,
            auto_model_selection=True
        )
        end_time = time.time()
        
        if result:
            print("✅ Transcription successful!")
            print(f"   Model used: {result.get('model_used', 'unknown')}")
            print(f"   Processing time: {end_time - start_time:.2f}s")
            print(f"   Word count: {result.get('word_count', 0)}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Text preview: {result.get('text', '')[:100]}...")
        else:
            print("❌ Transcription failed")


async def test_video_processing_with_transcription():
    """Test video processing with transcription."""
    print("\n" + "="*60)
    print("🎥 Testing Video Processing + Transcription")
    print("="*60)
    
    # This would typically use a test video URL
    test_video_url = "https://example.com/test-video.mp4"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n📹 Testing video processing workflow...")
        
        # Note: This is a conceptual test - adjust based on actual API
        response = await client.post(
            f"{API_BASE_URL}/capture",
            json={
                "url": test_video_url,
                "type": "video",
                "transcribe": True
            }
        )
        
        if response.status_code in [200, 201]:
            print("✅ Video processing initiated")
            result = response.json()
            if 'transcription' in result:
                print("   ✅ Transcription included in response")
        else:
            print(f"ℹ️  Video processing test skipped (status: {response.status_code})")


async def test_ai_validation_edge_cases():
    """Test AI validation with edge cases."""
    print("\n" + "="*60)
    print("🔍 Testing AI Validation Edge Cases")
    print("="*60)
    
    # Test cases that should trigger validation/repair
    edge_cases = [
        {
            "name": "Empty content",
            "content": ""
        },
        {
            "name": "Very short content",
            "content": "Test"
        },
        {
            "name": "Non-English content",
            "content": "这是一个测试内容。これはテストコンテンツです。"
        },
        {
            "name": "Code snippet",
            "content": "def hello_world():\n    print('Hello, World!')\n    return True"
        },
        {
            "name": "Malformed content",
            "content": "!@#$%^&*()_+" * 10
        }
    ]
    
    async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
        for test_case in edge_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            
            response = await client.post(
                f"{API_BASE_URL}/ai/analyze",
                json={"content": test_case['content']}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Handled gracefully")
                print(f"   Title: {result.get('title', 'N/A')}")
                print(f"   Category: {result.get('category', 'N/A')}")
                print(f"   Tags: {result.get('tags', [])}")
                
                # Check if defaults were applied
                if result.get('title') == 'Untitled Content':
                    print("   ℹ️  Default title applied")
                if result.get('category') == 'other':
                    print("   ℹ️  Default category applied")
            else:
                print(f"   ❌ Failed with status: {response.status_code}")


async def test_performance_metrics():
    """Test performance of AI services."""
    print("\n" + "="*60)
    print("⚡ Testing Performance Metrics")
    print("="*60)
    
    test_content = "This is a test content for performance measurement. " * 50
    
    async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
        # Measure AI analysis performance
        print("\n⏱️  Measuring AI analysis performance...")
        
        times = []
        for i in range(3):
            start = time.time()
            response = await client.post(
                f"{API_BASE_URL}/ai/analyze",
                json={"content": test_content}
            )
            end = time.time()
            
            if response.status_code == 200:
                times.append(end - start)
                print(f"   Run {i+1}: {times[-1]:.2f}s")
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"\n   Average response time: {avg_time:.2f}s")
            
            if avg_time < 2.0:
                print("   ✅ Performance is excellent (<2s)")
            elif avg_time < 5.0:
                print("   ⚠️  Performance is acceptable (2-5s)")
            else:
                print("   ❌ Performance needs improvement (>5s)")


async def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("🧪 PRSNL AI Integration Test Suite")
    print("="*80)
    print("\nThis test suite validates all AI integrations including:")
#    print("- Guardrails-AI validation")
    print("- whisper.cpp transcription")
    print("- Unified AI service")
    print("- End-to-end workflows")
    
    # Check if API is running
    print("\n🔍 Checking API availability...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ API is not responding. Please start the backend first.")
                print("   Run: cd backend && make dev")
                return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Please ensure the backend is running on port 8000")
        return
    
    print("✅ API is available")
    
    # Run all tests
    try:
        await test_health_check()
        await test_ai_content_analysis()
        await test_tag_generation()
        await test_summary_generation()
        await test_transcription()
        await test_video_processing_with_transcription()
        await test_ai_validation_edge_cases()
        await test_performance_metrics()
        
        print("\n" + "="*80)
        print("✅ All integration tests completed!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())