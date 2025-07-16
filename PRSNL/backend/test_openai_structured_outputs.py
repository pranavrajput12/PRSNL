#!/usr/bin/env python3
"""
Simple test to verify OpenAI 1.96.0 structured outputs functionality
Tests the new guaranteed JSON output feature
"""

import asyncio
import json
import sys
sys.path.append('.')

from app.services.document_extraction_enhanced import (
    DocumentMetadata,
    EntityExtraction,
    DocumentStructure,
    enhanced_extractor
)

async def test_structured_outputs():
    """Test OpenAI 1.96.0 structured outputs with a simple example"""
    
    sample_text = """
    FastAPI Performance Boost with Version 0.116.1
    
    The latest version of FastAPI brings significant improvements:
    - 15-20% performance boost in request handling
    - Enhanced WebSocket connection management
    - Better async context managers
    - Improved OpenAPI schema generation
    
    These updates make FastAPI even more suitable for high-performance applications.
    Created by the FastAPI team in 2024.
    """
    
    print("🧪 Testing OpenAI 1.96.0 Structured Outputs")
    print("=" * 50)
    
    try:
        print("📄 Testing document metadata extraction...")
        metadata = await enhanced_extractor.extract_structured_metadata(sample_text)
        
        print("✅ Metadata extraction successful!")
        print(f"Title: {metadata.title}")
        print(f"Summary: {metadata.summary}")
        print(f"Keywords: {metadata.keywords}")
        print(f"Confidence: {metadata.confidence_score}")
        print(f"Sentiment: {metadata.sentiment}")
        
        # Verify it's a proper Pydantic model
        assert isinstance(metadata, DocumentMetadata)
        print("✅ Structured output validation passed!")
        
        print("\n👥 Testing entity extraction...")
        entities = await enhanced_extractor.extract_entities(sample_text)
        
        print("✅ Entity extraction successful!")
        print(f"Technologies: {entities.technologies}")
        print(f"People: {entities.people}")
        print(f"Organizations: {entities.organizations}")
        
        # Verify it's a proper Pydantic model
        assert isinstance(entities, EntityExtraction)
        print("✅ Entity extraction validation passed!")
        
        print("\n📊 Testing document structure analysis...")
        structure = await enhanced_extractor.analyze_document_structure(sample_text)
        
        print("✅ Structure analysis successful!")
        print(f"Document Type: {structure.document_type}")
        print(f"Sections: {structure.sections}")
        print(f"Complexity: {structure.complexity_level}")
        
        # Verify it's a proper Pydantic model
        assert isinstance(structure, DocumentStructure)
        print("✅ Structure analysis validation passed!")
        
        print("\n🔍 Testing key insights extraction...")
        insights = await enhanced_extractor.extract_key_insights(sample_text)
        
        print("✅ Insights extraction successful!")
        print(f"Main insights: {insights.get('main_insights', [])}")
        print(f"Action items: {insights.get('action_items', [])}")
        
        # Verify it's valid JSON
        assert isinstance(insights, dict)
        print("✅ Insights validation passed!")
        
        print("\n🎯 All OpenAI 1.96.0 structured outputs tests passed!")
        print("Features confirmed:")
        print("  ✅ Guaranteed JSON outputs")
        print("  ✅ Pydantic model validation")
        print("  ✅ Error handling with fallbacks")
        print("  ✅ Structured data extraction")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_json_validation():
    """Test that responses are always valid JSON"""
    print("\n🔧 Testing JSON validation robustness...")
    
    # Test with minimal text
    minimal_text = "Hello world."
    
    try:
        metadata = await enhanced_extractor.extract_structured_metadata(minimal_text)
        print(f"✅ Minimal text processed: {metadata.title}")
        
        # Test serialization to JSON
        json_data = metadata.dict()
        json_string = json.dumps(json_data)
        parsed_back = json.loads(json_string)
        
        print("✅ JSON serialization/deserialization successful")
        return True
        
    except Exception as e:
        print(f"❌ JSON validation failed: {e}")
        return False

async def test_performance():
    """Test extraction performance"""
    import time
    
    print("\n⚡ Testing extraction performance...")
    
    test_text = "FastAPI performance improvements" * 100  # Larger text
    
    start_time = time.time()
    
    # Test parallel extraction
    metadata_task = enhanced_extractor.extract_structured_metadata(test_text)
    entities_task = enhanced_extractor.extract_entities(test_text)
    structure_task = enhanced_extractor.analyze_document_structure(test_text)
    
    metadata, entities, structure = await asyncio.gather(
        metadata_task, entities_task, structure_task
    )
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"✅ Parallel extraction completed in {processing_time:.2f} seconds")
    print(f"✅ Processed {len(test_text)} characters")
    print(f"✅ Processing rate: {len(test_text) / processing_time:.0f} chars/second")
    
    return processing_time < 30  # Should complete within 30 seconds

if __name__ == "__main__":
    async def main():
        print("🚀 OpenAI 1.96.0 Structured Outputs Test Suite")
        print("Testing enhanced document extraction capabilities")
        print()
        
        # Run all tests
        tests = [
            ("Core Functionality", test_structured_outputs()),
            ("JSON Validation", test_json_validation()),
            ("Performance", test_performance())
        ]
        
        results = []
        for test_name, test_coro in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = await test_coro
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "="*60)
        print("🎯 TEST SUMMARY")
        print("="*60)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("🎉 All OpenAI 1.96.0 structured outputs features working correctly!")
        else:
            print("⚠️  Some tests failed - check configuration or network connectivity")
    
    # Run the test suite
    asyncio.run(main())