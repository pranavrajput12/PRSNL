#!/usr/bin/env python3
"""
Integration test script for content fingerprint and embedding vector ID
"""
import asyncio
import httpx
import json
from datetime import datetime


async def test_content_fingerprint():
    """Test content fingerprint generation and duplicate detection"""
    print("\n🔐 Testing Content Fingerprint Integration...")
    
    # Test 1: Create item with content
    test_content = "This is a test article about machine learning and AI."
    
    async with httpx.AsyncClient() as client:
        # Create item
        response = await client.post("http://localhost:8000/api/capture", json={
            "type": "note",
            "content": test_content,
            "title": "Test Article"
        })
        
        if response.status_code == 201:
            item_data = response.json()
            item_id = item_data["id"]
            print(f"✅ Created item: {item_id}")
            
            # Check if content_fingerprint was generated
            db_response = await client.get(f"http://localhost:8000/api/items/{item_id}")
            if db_response.status_code == 200:
                item = db_response.json()
                if item.get("content_fingerprint"):
                    print(f"✅ Content fingerprint generated: {item['content_fingerprint'][:16]}...")
                else:
                    print("❌ Content fingerprint not found")
            
            # Test 2: Try to create duplicate content
            duplicate_response = await client.post("http://localhost:8000/api/capture", json={
                "type": "note",
                "content": test_content,  # Same content
                "title": "Duplicate Test Article"
            })
            
            if duplicate_response.status_code == 201:
                print("⚠️  Duplicate was created (duplicate detection may not be fully active)")
            else:
                print("✅ Duplicate detection working")
                
        else:
            print(f"❌ Failed to create item: {response.status_code}")
            print(response.text)


async def test_embedding_integration():
    """Test embedding creation and vector search"""
    print("\n🎯 Testing Embedding Integration...")
    
    async with httpx.AsyncClient() as client:
        # Create item with content for embedding
        response = await client.post("http://localhost:8000/api/capture", json={
            "type": "article",
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.",
            "title": "Introduction to Machine Learning"
        })
        
        if response.status_code == 201:
            item_data = response.json()
            item_id = item_data["id"]
            print(f"✅ Created item for embedding: {item_id}")
            
            # Wait a bit for background processing
            await asyncio.sleep(2)
            
            # Check if embedding was created
            db_response = await client.get(f"http://localhost:8000/api/items/{item_id}")
            if db_response.status_code == 200:
                item = db_response.json()
                if item.get("embed_vector_id"):
                    print(f"✅ Embed vector ID assigned: {item['embed_vector_id']}")
                else:
                    print("⚠️  Embed vector ID not assigned yet")
                    
                if item.get("embedding"):
                    print("✅ Legacy embedding field populated")
                else:
                    print("⚠️  Legacy embedding field not populated")
        else:
            print(f"❌ Failed to create item: {response.status_code}")


async def test_search_integration():
    """Test enhanced search with new architecture"""
    print("\n🔍 Testing Enhanced Search Integration...")
    
    async with httpx.AsyncClient() as client:
        # Test semantic search
        search_response = await client.post("http://localhost:8000/api/search/", json={
            "query": "machine learning artificial intelligence",
            "search_type": "semantic",
            "limit": 5
        })
        
        if search_response.status_code == 200:
            results = search_response.json()
            print(f"✅ Semantic search returned {len(results.get('results', []))} results")
            
            for result in results.get('results', [])[:2]:
                print(f"   - {result.get('title', 'No title')} (similarity: {result.get('similarity', 0):.3f})")
        else:
            print(f"❌ Search failed: {search_response.status_code}")


async def test_database_schema():
    """Test database schema for new fields"""
    print("\n🗄️  Testing Database Schema...")
    
    import asyncpg
    
    try:
        conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/prsnl")
        
        # Check if new columns exist
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'items' 
            AND column_name IN ('content_fingerprint', 'embed_vector_id')
            ORDER BY column_name
        """)
        
        for col in columns:
            print(f"✅ Column exists: {col['column_name']} ({col['data_type']})")
        
        # Check if embeddings table exists
        embeddings_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'embeddings'
            )
        """)
        
        if embeddings_exists:
            print("✅ Embeddings table exists")
            
            # Check embeddings table structure
            emb_columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'embeddings'
                ORDER BY column_name
            """)
            
            print("   Embeddings table columns:")
            for col in emb_columns:
                print(f"   - {col['column_name']} ({col['data_type']})")
        else:
            print("❌ Embeddings table does not exist")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")


async def test_ai_endpoints():
    """Test AI endpoints with fingerprint integration"""
    print("\n🤖 Testing AI Endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test AI analysis
        response = await client.post("http://localhost:8000/api/ai/analyze", json={
            "content": "This is a test document about renewable energy sources like solar and wind power."
        })
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI analysis endpoint working")
            print(f"   Generated title: {result.get('title', 'N/A')}")
            print(f"   Tags: {result.get('tags', [])}")
        else:
            print(f"❌ AI analysis failed: {response.status_code}")
            print(response.text)


async def main():
    """Run all integration tests"""
    print("🚀 Starting Integration Tests for Content Fingerprint & Embedding Architecture")
    print("=" * 80)
    
    # Run tests
    await test_database_schema()
    await test_content_fingerprint()
    await test_embedding_integration()
    await test_ai_endpoints()
    await test_search_integration()
    
    print("\n" + "=" * 80)
    print("✅ Integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())