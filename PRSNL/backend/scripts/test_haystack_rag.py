#!/usr/bin/env python3
"""
Comprehensive Haystack RAG Integration Test
Tests document ingestion, retrieval, and query functionality
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.haystack_rag_service import haystack_rag_service, HAYSTACK_AVAILABLE
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test data
SAMPLE_DOCUMENTS = [
    {
        "content": "PRSNL is a personal knowledge management system built with FastAPI and SvelteKit. It provides advanced AI-powered features for content analysis, transcription, and search capabilities.",
        "metadata": {
            "title": "PRSNL Overview",
            "source": "documentation",
            "tags": ["prsnl", "overview", "ai"]
        }
    },
    {
        "content": "Haystack v2 is a powerful framework for building Retrieval-Augmented Generation (RAG) systems. It provides document stores, embedders, retrievers, and generators for creating intelligent search applications.",
        "metadata": {
            "title": "Haystack Framework",
            "source": "documentation",
            "tags": ["haystack", "rag", "framework"]
        }
    },
    {
        "content": "The whisper.cpp integration in PRSNL provides offline transcription capabilities supporting 99 languages. It's optimized for CPU performance and doesn't require internet connectivity.",
        "metadata": {
            "title": "Whisper.cpp Integration",
            "source": "documentation",
            "tags": ["whisper", "transcription", "offline"]
        }
    }
]

SAMPLE_QUERIES = [
    "What is PRSNL?",
    "How does Haystack work?",
    "What languages does whisper.cpp support?",
    "Tell me about AI features in PRSNL",
    "How is transcription handled?"
]


async def test_service_initialization():
    """Test 1: Service initialization"""
    print("\n" + "="*50)
    print("🔧 Test 1: Service Initialization")
    print("="*50)
    
    try:
        # Check if Haystack is available
        print(f"✅ Haystack available: {HAYSTACK_AVAILABLE}")
        
        # Check service status
        print(f"✅ Service enabled: {haystack_rag_service.enabled}")
        
        # Check Azure OpenAI configuration
        print(f"✅ Azure OpenAI API Key: {'Set' if settings.AZURE_OPENAI_API_KEY else 'Not set'}")
        print(f"✅ Azure OpenAI Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
        print(f"✅ Azure OpenAI Deployment: {settings.AZURE_OPENAI_DEPLOYMENT}")
        
        # Check document store
        if haystack_rag_service.document_store:
            print(f"✅ Document store: {type(haystack_rag_service.document_store).__name__}")
        else:
            print("❌ Document store not initialized")
            
        # Check pipelines
        print(f"✅ Indexing pipeline: {'Initialized' if haystack_rag_service.indexing_pipeline else 'Not initialized'}")
        print(f"✅ Query pipeline: {'Initialized' if haystack_rag_service.query_pipeline else 'Not initialized'}")
        
        return True
        
    except Exception as e:
        logger.error(f"Service initialization test failed: {e}")
        print(f"❌ Service initialization failed: {e}")
        return False


async def test_document_ingestion():
    """Test 2: Document ingestion"""
    print("\n" + "="*50)
    print("📝 Test 2: Document Ingestion")
    print("="*50)
    
    if not haystack_rag_service.enabled:
        print("❌ Service not enabled, skipping ingestion test")
        return False
    
    try:
        # Test single document ingestion
        print("\n🔹 Testing single document ingestion...")
        doc = SAMPLE_DOCUMENTS[0]
        
        success = await haystack_rag_service.ingest_document(
            content=doc["content"],
            metadata=doc["metadata"],
            doc_id="test_doc_1"
        )
        
        if success:
            print("✅ Single document ingestion successful")
        else:
            print("❌ Single document ingestion failed")
            return False
            
        # Test batch ingestion
        print("\n🔹 Testing batch ingestion...")
        
        # Prepare batch documents
        batch_docs = []
        for i, doc in enumerate(SAMPLE_DOCUMENTS[1:], 2):
            batch_docs.append({
                "content": doc["content"],
                "metadata": doc["metadata"],
                "id": f"test_doc_{i}"
            })
        
        result = await haystack_rag_service.ingest_batch(batch_docs)
        
        print(f"✅ Batch ingestion result: {result}")
        
        if result["success"] > 0:
            print("✅ Batch ingestion successful")
        else:
            print("❌ Batch ingestion failed")
            return False
            
        # Check document count
        doc_count = await haystack_rag_service.get_document_count()
        print(f"✅ Total documents in store: {doc_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Document ingestion test failed: {e}")
        print(f"❌ Document ingestion failed: {e}")
        return False


async def test_query_functionality():
    """Test 3: Query functionality"""
    print("\n" + "="*50)
    print("🔍 Test 3: Query Functionality")
    print("="*50)
    
    if not haystack_rag_service.enabled:
        print("❌ Service not enabled, skipping query test")
        return False
    
    try:
        success_count = 0
        
        for i, query in enumerate(SAMPLE_QUERIES, 1):
            print(f"\n🔹 Query {i}: {query}")
            
            try:
                result = await haystack_rag_service.query(
                    question=query,
                    top_k=3
                )
                
                print(f"   Answer: {result['answer'][:100]}...")
                print(f"   Confidence: {result['confidence']}")
                print(f"   Documents found: {len(result['documents'])}")
                
                if result['answer'] and result['answer'] != "Query failed":
                    success_count += 1
                    print("   ✅ Query successful")
                else:
                    print("   ❌ Query failed")
                    
            except Exception as e:
                logger.error(f"Query {i} failed: {e}")
                print(f"   ❌ Query failed: {e}")
        
        print(f"\n✅ Successful queries: {success_count}/{len(SAMPLE_QUERIES)}")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Query functionality test failed: {e}")
        print(f"❌ Query functionality test failed: {e}")
        return False


async def test_hybrid_search():
    """Test 4: Hybrid search functionality"""
    print("\n" + "="*50)
    print("🔍 Test 4: Hybrid Search")
    print("="*50)
    
    if not haystack_rag_service.enabled:
        print("❌ Service not enabled, skipping hybrid search test")
        return False
    
    try:
        query = "AI features transcription"
        
        results = await haystack_rag_service.hybrid_search(
            query=query,
            keyword_weight=0.3,
            semantic_weight=0.7,
            top_k=5
        )
        
        print(f"🔹 Hybrid search query: {query}")
        print(f"✅ Results found: {len(results)}")
        
        for i, result in enumerate(results[:3], 1):
            print(f"   Result {i}:")
            print(f"     Content: {result['content'][:100]}...")
            print(f"     Score: {result.get('score', 'N/A')}")
            print(f"     Metadata: {result.get('metadata', {})}")
        
        return len(results) > 0
        
    except Exception as e:
        logger.error(f"Hybrid search test failed: {e}")
        print(f"❌ Hybrid search test failed: {e}")
        return False


async def test_document_management():
    """Test 5: Document management (update/delete)"""
    print("\n" + "="*50)
    print("📋 Test 5: Document Management")
    print("="*50)
    
    if not haystack_rag_service.enabled:
        print("❌ Service not enabled, skipping document management test")
        return False
    
    try:
        # Test document update
        print("\n🔹 Testing document update...")
        
        updated_content = "PRSNL is an advanced personal knowledge management system with AI-powered features, built using FastAPI backend and SvelteKit frontend. It now includes Haystack RAG capabilities."
        
        success = await haystack_rag_service.update_document(
            doc_id="test_doc_1",
            content=updated_content,
            metadata={"updated": True, "version": "2.0"}
        )
        
        if success:
            print("✅ Document update successful")
        else:
            print("❌ Document update failed")
            
        # Test document deletion
        print("\n🔹 Testing document deletion...")
        
        success = await haystack_rag_service.delete_document("test_doc_1")
        
        if success:
            print("✅ Document deletion successful")
        else:
            print("❌ Document deletion failed")
            
        # Check updated document count
        doc_count = await haystack_rag_service.get_document_count()
        print(f"✅ Documents remaining: {doc_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Document management test failed: {e}")
        print(f"❌ Document management test failed: {e}")
        return False


async def test_export_functionality():
    """Test 6: Export functionality"""
    print("\n" + "="*50)
    print("📤 Test 6: Export Functionality")
    print("="*50)
    
    if not haystack_rag_service.enabled:
        print("❌ Service not enabled, skipping export test")
        return False
    
    try:
        # Test JSON export
        result = await haystack_rag_service.export_knowledge_base("json")
        
        if isinstance(result, dict) and "documents" in result:
            print(f"✅ Export successful: {result['count']} documents")
            print(f"   Exported at: {result['exported_at']}")
        else:
            print(f"❌ Export failed: {result}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Export test failed: {e}")
        print(f"❌ Export test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 PRSNL Haystack RAG Integration Test Suite")
    print("=" * 60)
    
    # Test results
    test_results = []
    
    # Run all tests
    tests = [
        ("Service Initialization", test_service_initialization),
        ("Document Ingestion", test_document_ingestion),
        ("Query Functionality", test_query_functionality),
        ("Hybrid Search", test_hybrid_search),
        ("Document Management", test_document_management),
        ("Export Functionality", test_export_functionality)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Haystack RAG integration is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the output above.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite crashed: {e}")
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)