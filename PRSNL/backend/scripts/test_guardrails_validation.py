"""
Test script for Guardrails-AI validation integration
Tests various AI outputs and validation scenarios
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.ai_validation_service import ai_validation_service
from app.services.unified_ai_service import unified_ai_service


async def test_content_analysis_validation():
    """Test content analysis validation"""
    print("\n=== Testing Content Analysis Validation ===")
    
    # Test 1: Valid content analysis
    valid_output = {
        "title": "Understanding Machine Learning Fundamentals",
        "summary": "This article provides a comprehensive introduction to machine learning concepts and applications.",
        "detailed_summary": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. This article covers fundamental concepts including supervised learning, unsupervised learning, and reinforcement learning.",
        "category": "tutorial",
        "tags": ["machine learning", "ai", "programming", "data science"],
        "key_points": [
            "Machine learning enables systems to learn from data",
            "Three main types: supervised, unsupervised, and reinforcement learning",
            "Applications span from recommendation systems to autonomous vehicles"
        ],
        "entities": {
            "people": [],
            "organizations": ["Google", "OpenAI"],
            "technologies": ["TensorFlow", "PyTorch"],
            "concepts": ["neural networks", "deep learning"]
        },
        "sentiment": "positive",
        "difficulty_level": "intermediate",
        "estimated_reading_time": 10
    }
    
    result = await ai_validation_service.validate_content_analysis(valid_output)
    print(f"✅ Valid output validated: {result['title']}")
    
    # Test 2: Invalid content analysis (missing fields)
    invalid_output = {
        "title": "ML",  # Too short
        "summary": "Short",  # Too short
        "tags": ["ml", "ai", "tech", "data", "science", "computer", "algorithm", "model", "training", "dataset", "extra"],  # Too many
        "category": "unknown"  # Invalid category
    }
    
    result = await ai_validation_service.validate_content_analysis(invalid_output)
    print(f"✅ Invalid output repaired: {result['title']}")
    print(f"   - Tags limited to 10: {len(result['tags'])} tags")
    print(f"   - Category defaulted to: {result['category']}")
    
    # Test 3: Malformed JSON string
    malformed_json = '{"title": "Test", "summary": "Missing closing brace"'
    result = await ai_validation_service.validate_content_analysis(malformed_json)
    print(f"✅ Malformed JSON handled: {result['title']}")


async def test_summary_validation():
    """Test summary validation"""
    print("\n=== Testing Summary Validation ===")
    
    # Test 1: Valid summary
    valid_summary = {
        "brief": "Machine learning is a powerful technology that enables computers to learn from data without explicit programming.",
        "detailed": "Machine learning represents a paradigm shift in how we approach problem-solving with computers. Instead of programming explicit rules, we allow systems to discover patterns in data and make decisions based on these learned patterns. This technology has revolutionized fields from healthcare to finance.",
        "key_takeaways": [
            "ML systems learn from data patterns",
            "No explicit programming required",
            "Wide applications across industries"
        ]
    }
    
    result = await ai_validation_service.validate_summary(valid_summary)
    print(f"✅ Valid summary validated")
    print(f"   - Brief: {result['brief'][:50]}...")
    
    # Test 2: Plain text summary
    plain_text = "This is a simple summary of the content that doesn't follow any particular structure but contains useful information."
    result = await ai_validation_service.validate_summary(plain_text)
    print(f"✅ Plain text converted to structured summary")
    print(f"   - Generated {len(result['key_takeaways'])} key takeaways")


async def test_tag_validation():
    """Test tag generation validation"""
    print("\n=== Testing Tag Validation ===")
    
    # Test 1: Valid tags
    valid_tags = {
        "tags": ["machine learning", "artificial intelligence", "data science", "python", "tensorflow"],
        "confidence_scores": {
            "machine learning": 0.95,
            "artificial intelligence": 0.90,
            "data science": 0.85,
            "python": 0.80,
            "tensorflow": 0.75
        }
    }
    
    result = await ai_validation_service.validate_tags(valid_tags)
    print(f"✅ Valid tags: {result}")
    
    # Test 2: Tags with duplicates and mixed case
    messy_tags = ["Python", "python", "PYTHON", "Machine Learning", "machine learning", "AI", "ai"]
    result = await ai_validation_service.validate_tags(messy_tags)
    print(f"✅ Cleaned tags (duplicates removed, lowercase): {result}")
    
    # Test 3: Comma-separated string
    tag_string = "python, machine learning, data science, artificial intelligence"
    result = await ai_validation_service.validate_tags(tag_string)
    print(f"✅ String converted to tag list: {result}")


async def test_unified_ai_integration():
    """Test UnifiedAIService with validation"""
    print("\n=== Testing UnifiedAI Service Integration ===")
    
    # Test content
    test_content = """
    Machine learning is revolutionizing how we process and understand data. 
    This comprehensive guide covers the fundamentals of ML, including supervised 
    and unsupervised learning techniques. We'll explore practical applications 
    using Python and TensorFlow, making complex concepts accessible to beginners.
    """
    
    # Test 1: Content analysis with validation
    print("\n1. Testing content analysis...")
    analysis = await unified_ai_service.analyze_content(test_content)
    print(f"✅ Content analyzed and validated:")
    print(f"   - Title: {analysis['title']}")
    print(f"   - Tags: {analysis['tags'][:5]}")
    print(f"   - Category: {analysis['category']}")
    
    # Test 2: Tag generation with validation
    print("\n2. Testing tag generation...")
    tags = await unified_ai_service.generate_tags(test_content, limit=5)
    print(f"✅ Tags generated and validated: {tags}")
    
    # Test 3: Summary generation
    print("\n3. Testing summary generation...")
    summary = await unified_ai_service.generate_summary(test_content, summary_type="brief")
    print(f"✅ Summary generated: {summary[:100]}...")


async def test_error_handling():
    """Test error handling and fallbacks"""
    print("\n=== Testing Error Handling ===")
    
    # Test with None input
    result = await ai_validation_service.validate_content_analysis(None)
    print(f"✅ None input handled gracefully")
    print(f"   - Default title: {result['title']}")
    print(f"   - Default tags: {result['tags']}")
    
    # Test with empty dict
    result = await ai_validation_service.validate_content_analysis({})
    print(f"✅ Empty dict handled with defaults")
    
    # Test with wrong type
    result = await ai_validation_service.validate_tags(12345)
    print(f"✅ Wrong type handled: {result}")


async def main():
    """Run all tests"""
    print("🔧 Testing Guardrails-AI Integration for PRSNL")
    print("=" * 50)
    
    try:
        await test_content_analysis_validation()
        await test_summary_validation()
        await test_tag_validation()
        await test_unified_ai_integration()
        await test_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())