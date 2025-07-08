"""
Test script for Knowledge Graph feature
"""

import asyncio
import aiohttp
import json

API_BASE = "http://localhost:8000/api"

async def test_knowledge_graph():
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing Knowledge Graph Feature\n")
        
        # Get some items first
        item_ids = []
        async with session.get(f"{API_BASE}/timeline?limit=5") as resp:
            if resp.status == 200:
                timeline_data = await resp.json()
                item_ids = [item["id"] for item in timeline_data["items"]]
                print(f"   Found {len(item_ids)} items to work with")
        
        if len(item_ids) < 2:
            print("   ⚠️  Need at least 2 items to test relationships")
            return
        
        # 1. Test creating a relationship
        print("\n1️⃣ Testing relationship creation...")
        
        async with session.post(
            f"{API_BASE}/knowledge-graph/relationships",
            json={
                "source_id": item_ids[0],
                "target_id": item_ids[1],
                "relationship_type": "related",
                "confidence": 0.8
            }
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ Created relationship: {result['data']['source_title']} -> {result['data']['target_title']}")
            else:
                print(f"   ❌ Failed: {resp.status}")
        
        # 2. Test discovering relationships
        print("\n2️⃣ Testing relationship discovery...")
        
        async with session.post(
            f"{API_BASE}/knowledge-graph/discover",
            json={
                "item_id": item_ids[0],
                "limit": 5,
                "min_confidence": 0.6
            }
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                relationships = result['data']['relationships']
                print(f"   ✅ Discovered {len(relationships)} potential relationships:")
                for rel in relationships[:3]:
                    print(f"      - {rel['type']}: {rel['target_title']} (confidence: {rel['confidence']:.2f})")
            else:
                print(f"   ❌ Failed: {resp.status}")
        
        # 3. Test getting item graph
        print("\n3️⃣ Testing item graph retrieval...")
        
        async with session.post(
            f"{API_BASE}/knowledge-graph/graph",
            json={
                "item_id": item_ids[0],
                "depth": 2
            }
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                graph = result['data']
                print(f"   ✅ Retrieved graph:")
                print(f"      Nodes: {graph['stats']['total_nodes']}")
                print(f"      Edges: {graph['stats']['total_edges']}")
                print(f"      Max depth: {graph['stats']['max_depth_reached']}")
            else:
                print(f"   ❌ Failed: {resp.status}")
        
        # 4. Test learning sequence suggestion
        print("\n4️⃣ Testing learning sequence suggestion...")
        
        async with session.post(
            f"{API_BASE}/knowledge-graph/learning-sequence",
            json={
                "topic": "python",
                "skill_level": "beginner",
                "limit": 5
            }
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                sequence = result['data']['sequence']
                print(f"   ✅ Suggested learning sequence for 'python' (beginner):")
                for item in sequence:
                    print(f"      {item['order']}. {item['title']}")
                    print(f"         Reason: {item['reason']}")
            else:
                print(f"   ❌ Failed: {resp.status}")
        
        # 5. Test knowledge gaps
        print("\n5️⃣ Testing knowledge gap detection...")
        
        async with session.get(f"{API_BASE}/knowledge-graph/gaps") as resp:
            if resp.status == 200:
                result = await resp.json()
                gaps = result['data']['gaps']
                print(f"   ✅ Found {len(gaps)} knowledge gaps:")
                for gap in gaps[:3]:
                    print(f"      - {gap['title']} (gap score: {gap['gap_score']:.2f})")
                    print(f"        {gap['suggestion']}")
            else:
                print(f"   ❌ Failed: {resp.status}")
        
        # 6. Test knowledge path finding
        if len(item_ids) >= 2:
            print("\n6️⃣ Testing knowledge path finding...")
            
            async with session.post(
                f"{API_BASE}/knowledge-graph/path",
                json={
                    "start_id": item_ids[0],
                    "end_id": item_ids[-1],
                    "max_depth": 3
                }
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    paths = result['data']['paths']
                    print(f"   ✅ Found {result['data']['path_count']} paths")
                    if paths:
                        print(f"      Example path:")
                        for step in paths[0]:
                            print(f"      - {step['source']['title']} --{step['relationship']}--> {step['target']['title']}")
                else:
                    print(f"   ❌ Failed: {resp.status}")
        
        # 7. Test getting item relationships
        print("\n7️⃣ Testing get item relationships...")
        
        async with session.get(f"{API_BASE}/knowledge-graph/relationships/{item_ids[0]}") as resp:
            if resp.status == 200:
                result = await resp.json()
                data = result['data']
                print(f"   ✅ Relationships for '{data['item_title']}':")
                print(f"      Outgoing: {len(data['outgoing_relationships'])}")
                print(f"      Incoming: {len(data['incoming_relationships'])}")
                print(f"      Total: {data['total_relationships']}")
            else:
                print(f"   ❌ Failed: {resp.status}")
        
        print("\n✅ Knowledge Graph tests completed!")

if __name__ == "__main__":
    asyncio.run(test_knowledge_graph())