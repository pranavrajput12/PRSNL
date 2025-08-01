#!/usr/bin/env python3
"""
Test auto-processing with existing database items
"""
import asyncio
import json
import uuid

import httpx
import asyncpg

# Configuration
DATABASE_URL = "postgresql://pronav@localhost:5432/prsnl"
BACKEND_URL = "http://localhost:8000/api"

async def get_test_item():
    """Get an existing item from the database for testing"""
    print("🔍 Looking for existing items to test...")
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Get an item that might not have been auto-processed yet
        item = await conn.fetchrow("""
            SELECT id, title, raw_content, url, status, 
                   metadata->>'auto_processing' as auto_processing
            FROM items 
            WHERE raw_content IS NOT NULL 
              AND LENGTH(raw_content) > 100
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        await conn.close()
        
        if item:
            print(f"✅ Found test item: {item['id']}")
            print(f"   Title: {item['title']}")
            print(f"   Status: {item['status']}")
            print(f"   Content length: {len(item['raw_content']) if item['raw_content'] else 0}")
            print(f"   Auto-processed: {'Yes' if item['auto_processing'] else 'No'}")
            return str(item['id'])
        else:
            print("❌ No suitable test items found")
            return None
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

async def test_manual_processing(item_id):
    """Test manual processing trigger on existing item"""
    print(f"\n🔧 Testing Manual Processing for item {item_id}...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Check current status first
            response = await client.get(
                f"{BACKEND_URL}/auto-processing/status/{item_id}"
            )
            
            if response.status_code == 200:
                current_status = response.json()
                print(f"✅ Current status: {current_status['data']['status']}")
                print(f"   Currently processing: {current_status['data']['currently_processing']}")
            
            # Trigger manual processing with force reprocess
            process_data = {
                "item_id": item_id,
                "enable_ai_processing": True,
                "force_reprocess": True  # Force reprocessing even if already processed
            }
            
            response = await client.post(
                f"{BACKEND_URL}/auto-processing/process",
                json=process_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Manual processing triggered!")
                print(f"   Status: {result['data']['status']}")
                print(f"   AI processing enabled: {result['data']['ai_processing_enabled']}")
                return True
            else:
                print(f"❌ Manual processing failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Manual processing error: {e}")
            return False

async def monitor_processing(item_id, duration=30):
    """Monitor processing progress for a specific duration"""
    print(f"\n👀 Monitoring processing for {duration} seconds...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(duration):
            try:
                response = await client.get(
                    f"{BACKEND_URL}/auto-processing/status/{item_id}"
                )
                
                if response.status_code == 200:
                    status_data = response.json()['data']
                    processing_data = status_data.get('processing_results', {})
                    
                    if i == 0 or i % 5 == 0:  # Print every 5 seconds
                        print(f"   [{i}s] Status: {status_data['status']}, "
                              f"Processing: {status_data['currently_processing']}")
                        
                        if processing_data:
                            steps = processing_data.get('steps_completed', [])
                            if steps:
                                print(f"        Steps completed: {steps}")
                            
                            errors = processing_data.get('errors', [])
                            if errors:
                                print(f"        Errors: {errors}")
                
                # Check queue status occasionally
                if i % 10 == 0:
                    queue_response = await client.get(f"{BACKEND_URL}/auto-processing/queue/status")
                    if queue_response.status_code == 200:
                        queue_data = queue_response.json()
                        if queue_data['queue_size'] > 0:
                            print(f"        Queue: {queue_data['queue_size']} items processing")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"   Error monitoring: {e}")
                
    print("✅ Monitoring complete!")

async def check_final_results(item_id):
    """Check the final processing results"""
    print(f"\n📋 Checking Final Results for {item_id}...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{BACKEND_URL}/auto-processing/status/{item_id}"
            )
            
            if response.status_code == 200:
                result = response.json()['data']
                print("✅ Final status retrieved!")
                print(f"   Status: {result['status']}")
                print(f"   Currently processing: {result['currently_processing']}")
                
                processing_data = result.get('processing_results', {})
                if processing_data:
                    print("\n📊 Processing Results:")
                    print(f"   Steps completed: {processing_data.get('steps_completed', [])}")
                    print(f"   Success rate: {processing_data.get('success_rate', 0):.2%}")
                    
                    errors = processing_data.get('errors', [])
                    if errors:
                        print(f"   Errors encountered: {errors}")
                    else:
                        print("   No errors encountered! ✅")
                
                return result
            else:
                print(f"❌ Failed to get final status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error checking final results: {e}")
            return None

async def test_stats_and_queue():
    """Test statistics and queue status"""
    print("\n📊 Testing Statistics and Queue...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Get processing stats
            stats_response = await client.get(f"{BACKEND_URL}/auto-processing/stats")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print("✅ Processing Statistics:")
                print(f"   Total items: {stats['total_items']}")
                print(f"   Completed: {stats['completed_items']}")
                print(f"   Failed: {stats['failed_items']}")
                print(f"   Currently processing: {stats['processing_items']}")
                print(f"   Auto-processing enabled: {stats['auto_processing_enabled']}")
            
            # Get queue status
            queue_response = await client.get(f"{BACKEND_URL}/auto-processing/queue/status")
            if queue_response.status_code == 200:
                queue = queue_response.json()
                print("\n⚡ Queue Status:")
                print(f"   Queue size: {queue['queue_size']}")
                print(f"   Status: {queue['queue_status']}")
                if queue['currently_processing']:
                    print(f"   Processing: {queue['currently_processing']}")
                
        except Exception as e:
            print(f"❌ Error getting stats/queue: {e}")

async def main():
    """Main test function"""
    print("🚀 PRSNL Auto-Processing Test (Existing Items)")
    print("=" * 55)
    
    # Get a test item from database
    item_id = await get_test_item()
    
    if not item_id:
        print("❌ Cannot proceed without test item")
        return
    
    # Test manual processing
    success = await test_manual_processing(item_id)
    
    if success:
        # Monitor processing for 30 seconds
        await monitor_processing(item_id, 30)
        
        # Check final results
        await check_final_results(item_id)
    
    # Test stats and queue
    await test_stats_and_queue()
    
    print("\n🎉 Auto-Processing Test Complete!")
    print("=" * 55)

if __name__ == "__main__":
    asyncio.run(main())