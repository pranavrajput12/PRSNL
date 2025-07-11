#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for PRSNL v4.2.0
Tests all AI integrations: RAG, Firecrawl, OpenCLIP, Guardrails, etc.
"""

import asyncio
import sys
import os
import json
import time
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, '/app')

# Import all services to test
from app.services.haystack_rag_service import haystack_rag_service, HAYSTACK_AVAILABLE
from app.services.firecrawl_service import firecrawl_service
from app.services.openclip_service import openclip_service
from app.services.unified_ai_service import unified_ai_service
from app.config import settings

print("🚀 PRSNL v4.2.0 - Comprehensive AI Integration Test Suite")
print("=" * 70)

async def test_rag_integration():
    """Test RAG/Haystack integration"""
    print("\n" + "=" * 50)
    print("🧠 Test 1: RAG & Haystack Integration")
    print("=" * 50)
    
    try:
        # Test service availability
        print(f"✅ Haystack Available: {HAYSTACK_AVAILABLE}")
        print(f"✅ RAG Service Enabled: {haystack_rag_service.enabled}")
        print(f"✅ Document Store Type: {type(haystack_rag_service.document_store).__name__ if haystack_rag_service.document_store else 'None'}")
        
        if not haystack_rag_service.enabled:
            print("❌ RAG service not enabled, skipping tests")
            return False
        
        # Test document ingestion
        print("\n📝 Testing Document Ingestion...")
        test_doc = {
            "content": "This is a test document about Python programming. Python is a versatile programming language used for web development, data science, and artificial intelligence.",
            "metadata": {"title": "Python Programming", "source": "test", "type": "educational"}
        }
        
        result = await haystack_rag_service.ingest_document(
            content=test_doc["content"],
            metadata=test_doc["metadata"],
            doc_id="test_doc_001"
        )
        
        if result:
            print("✅ Document ingestion successful")
        else:
            print("❌ Document ingestion failed")
            return False
        
        # Test querying
        print("\n🔍 Testing RAG Query...")
        query_result = await haystack_rag_service.query(
            question="What is Python used for?",
            top_k=3
        )
        
        if query_result.get("answer"):
            print(f"✅ RAG Query successful")
            print(f"   Answer: {query_result['answer'][:100]}...")
            print(f"   Confidence: {query_result.get('confidence', 'N/A')}")
            print(f"   Documents found: {len(query_result.get('documents', []))}")
        else:
            print("❌ RAG Query failed")
            return False
        
        # Test document count
        doc_count = await haystack_rag_service.get_document_count()
        print(f"✅ Total documents in store: {doc_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG Integration Test Failed: {e}")
        return False

async def test_firecrawl_integration():
    """Test Firecrawl web scraping integration"""
    print("\n" + "=" * 50)
    print("🕷️  Test 2: Firecrawl Web Scraping Integration")
    print("=" * 50)
    
    try:
        # Test service availability
        print(f"✅ Firecrawl Service Enabled: {firecrawl_service.enabled}")
        print(f"✅ API Key Configured: {bool(firecrawl_service.api_key)}")
        
        if not firecrawl_service.enabled:
            print("❌ Firecrawl service not enabled, skipping tests")
            return False
        
        # Test URL scraping
        print("\n📄 Testing URL Scraping...")
        test_url = "https://example.com"
        
        scrape_result = await firecrawl_service.scrape_url(
            url=test_url,
            extract_content=True,
            include_markdown=True
        )
        
        if scrape_result.get("success"):
            print("✅ URL scraping successful")
            print(f"   Title: {scrape_result.get('title', 'N/A')}")
            print(f"   Content length: {len(scrape_result.get('content', ''))}")
            print(f"   Links found: {len(scrape_result.get('links', []))}")
        else:
            print(f"❌ URL scraping failed: {scrape_result.get('error', 'Unknown error')}")
            return False
        
        # Test URL validation
        valid_urls = [
            "https://example.com",
            "http://test.com",
            "invalid-url",
            "ftp://example.com"
        ]
        
        print("\n🔍 Testing URL Validation...")
        for url in valid_urls:
            is_valid = firecrawl_service.is_valid_url(url)
            status = "✅" if is_valid else "❌"
            print(f"   {status} {url}: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Firecrawl Integration Test Failed: {e}")
        return False

async def test_openclip_integration():
    """Test OpenCLIP vision integration"""
    print("\n" + "=" * 50)
    print("👁️  Test 3: OpenCLIP Vision Integration")
    print("=" * 50)
    
    try:
        # Test service availability
        model_info = openclip_service.get_model_info()
        print(f"✅ OpenCLIP Available: {model_info['available']}")
        print(f"✅ Service Enabled: {model_info['enabled']}")
        
        if model_info['enabled']:
            print(f"✅ Model: {model_info['model_name']}")
            print(f"✅ Pretrained: {model_info['pretrained']}")
            print(f"✅ Device: {model_info['device']}")
        else:
            print("❌ OpenCLIP service not enabled, skipping tests")
            return False
        
        # Test text encoding
        print("\n📝 Testing Text Encoding...")
        test_texts = [
            "a photo of a cat",
            "a beautiful landscape",
            "a person working on a computer"
        ]
        
        for text in test_texts:
            text_features = await openclip_service.encode_text(text)
            if text_features is not None:
                print(f"✅ Text encoded: '{text}' -> {text_features.shape}")
            else:
                print(f"❌ Failed to encode text: '{text}'")
        
        # Test image file validation
        print("\n🖼️  Testing Image File Validation...")
        test_files = [
            "image.jpg",
            "photo.png",
            "document.pdf",
            "video.mp4",
            "image.jpeg"
        ]
        
        for filename in test_files:
            is_image = openclip_service.is_image_file(filename)
            status = "✅" if is_image else "❌"
            print(f"   {status} {filename}: {is_image}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenCLIP Integration Test Failed: {e}")
        return False

async def test_unified_ai_service():
    """Test Unified AI Service integration"""
    print("\n" + "=" * 50)
    print("🤖 Test 4: Unified AI Service Integration")
    print("=" * 50)
    
    try:
        # Test service availability
        print(f"✅ Azure OpenAI Configured: {bool(settings.AZURE_OPENAI_API_KEY)}")
        print(f"✅ Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
        print(f"✅ Deployment: {settings.AZURE_OPENAI_DEPLOYMENT}")
        
        if not settings.AZURE_OPENAI_API_KEY:
            print("❌ Azure OpenAI not configured, skipping tests")
            return False
        
        # Test content analysis
        print("\n📊 Testing Content Analysis...")
        test_content = "This is a test article about artificial intelligence and machine learning. AI is transforming various industries."
        
        analysis_result = await unified_ai_service.analyze_content(
            content=test_content,
            content_type="text"
        )
        
        if analysis_result.get("success"):
            print("✅ Content analysis successful")
            print(f"   Summary: {analysis_result.get('summary', 'N/A')[:100]}...")
            print(f"   Tags: {analysis_result.get('tags', [])}")
            print(f"   Sentiment: {analysis_result.get('sentiment', 'N/A')}")
        else:
            print(f"❌ Content analysis failed: {analysis_result.get('error', 'Unknown error')}")
            return False
        
        # Test tag generation
        print("\n🏷️  Testing Tag Generation...")
        tag_result = await unified_ai_service.generate_tags(
            content=test_content,
            max_tags=5
        )
        
        if tag_result.get("success"):
            print("✅ Tag generation successful")
            print(f"   Tags: {tag_result.get('tags', [])}")
        else:
            print(f"❌ Tag generation failed: {tag_result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Unified AI Service Test Failed: {e}")
        return False

async def test_database_connectivity():
    """Test database connectivity and tables"""
    print("\n" + "=" * 50)
    print("🗄️  Test 5: Database Connectivity")
    print("=" * 50)
    
    try:
        from app.db.database import get_db_pool
        
        # Test connection
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Test basic query
            result = await conn.fetchval("SELECT 1")
            print(f"✅ Database connection successful: {result}")
            
            # Check for RAG tables
            rag_tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('haystack_documents', 'rag_query_history')
            """)
            
            print(f"✅ RAG tables found: {[r['table_name'] for r in rag_tables]}")
            
            # Check for pgvector extension
            vector_ext = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                )
            """)
            
            print(f"✅ PGVector extension enabled: {vector_ext}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database Connectivity Test Failed: {e}")
        return False

async def test_environment_configuration():
    """Test environment configuration"""
    print("\n" + "=" * 50)
    print("⚙️  Test 6: Environment Configuration")
    print("=" * 50)
    
    try:
        # Required environment variables
        required_vars = [
            "DATABASE_URL",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT"
        ]
        
        optional_vars = [
            "FIRECRAWL_API_KEY",
            "REDIS_URL",
            "GITHUB_TOKEN"
        ]
        
        print("Required Environment Variables:")
        all_required_present = True
        for var in required_vars:
            value = getattr(settings, var, None)
            if value:
                print(f"✅ {var}: {'*' * min(len(str(value)), 20)}")
            else:
                print(f"❌ {var}: Not set")
                all_required_present = False
        
        print("\nOptional Environment Variables:")
        for var in optional_vars:
            value = getattr(settings, var, None)
            if value:
                print(f"✅ {var}: {'*' * min(len(str(value)), 20)}")
            else:
                print(f"⚠️  {var}: Not set")
        
        return all_required_present
        
    except Exception as e:
        print(f"❌ Environment Configuration Test Failed: {e}")
        return False

async def main():
    """Run all integration tests"""
    print(f"🚀 Starting comprehensive integration tests...")
    print(f"📅 Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track test results
    test_results = {}
    
    # Run all tests
    tests = [
        ("Environment Configuration", test_environment_configuration),
        ("Database Connectivity", test_database_connectivity),
        ("RAG Integration", test_rag_integration),
        ("Firecrawl Integration", test_firecrawl_integration),
        ("OpenCLIP Integration", test_openclip_integration),
        ("Unified AI Service", test_unified_ai_service),
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            test_results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! PRSNL v4.2.0 is ready for production.")
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)