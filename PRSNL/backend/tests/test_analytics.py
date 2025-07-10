import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db_pool
import asyncpg
from datetime import datetime, timedelta
import json

client = TestClient(app)

@pytest.fixture(scope="module")
async def db_connection():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        yield conn

@pytest.fixture(autouse=True)
async def clear_and_populate_db(db_connection: asyncpg.Connection):
    # Clear existing data
    await db_connection.execute("TRUNCATE items, tags, item_tags RESTART IDENTITY CASCADE;")

    # Populate with test data
    test_items = [
        {"id": "a0000000-0000-4000-8000-000000000001", "title": "Test Article 1", "url": "http://example.com/art1", "type": "article", "created_at": datetime.now() - timedelta(days=5)},
        {"id": "a0000000-0000-4000-8000-000000000002", "title": "Test Video 1", "url": "http://example.com/vid1", "type": "video", "created_at": datetime.now() - timedelta(days=5)},
        {"id": "a0000000-0000-4000-8000-000000000003", "title": "Test Note 1", "url": None, "type": "note", "created_at": datetime.now() - timedelta(days=4)},
        {"id": "a0000000-0000-4000-8000-000000000004", "title": "Test Article 2", "url": "http://example.com/art2", "type": "article", "created_at": datetime.now() - timedelta(days=3)},
        {"id": "a0000000-0000-4000-8000-000000000005", "title": "Test Video 2", "url": "http://example.com/vid2", "type": "video", "created_at": datetime.now() - timedelta(days=2)},
        {"id": "a0000000-0000-4000-8000-000000000006", "title": "Test Article 3", "url": "http://example.com/art3", "type": "article", "created_at": datetime.now() - timedelta(days=1)},
    ]
    
    for item in test_items:
        await db_connection.execute(
            "INSERT INTO items (id, title, url, type, created_at, status) VALUES ($1, $2, $3, $4, $5, 'completed')",
            item["id"], item["title"], item["url"], item["type"], item["created_at"]
        )
    
    # Add tags
    tags_to_add = [
        ("a0000000-0000-4000-8000-000000000001", "technology"),
        ("a0000000-0000-4000-8000-000000000001", "programming"),
        ("a0000000-0000-4000-8000-000000000002", "technology"),
        ("a0000000-0000-4000-8000-000000000003", "productivity"),
        ("a0000000-0000-4000-8000-000000000004", "programming"),
        ("a0000000-0000-4000-8000-000000000005", "entertainment"),
        ("a0000000-0000-4000-8000-000000000006", "productivity"),
    ]

    for item_id, tag_name in tags_to_add:
        tag_id = await db_connection.fetchval(
            "INSERT INTO tags (name) VALUES ($1) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
            tag_name
        )
        await db_connection.execute(
            "INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            item_id, tag_id
        )
    
    # Clear cache after populating data
    client.get("/clear-cache") # Assuming a cache clearing endpoint or direct cache access

@pytest.mark.asyncio
async def test_get_content_trends():
    response = client.get("/api/analytics/trends?timeframe=7d")
    assert response.status_code == 200
    data = response.json()
    assert "trends" in data
    assert len(data["trends"]) > 0
    
    # Check for expected item types and counts
    found_article_day = False
    found_video_day = False
    for trend in data["trends"]:
        if "article" in trend and trend["article"] > 0:
            found_article_day = True
        if "video" in trend and trend["video"] > 0:
            found_video_day = True
    assert found_article_day
    assert found_video_day

@pytest.mark.asyncio
async def test_get_topic_clustering():
    response = client.get("/api/analytics/topics?limit=3")
    assert response.status_code == 200
    data = response.json()
    assert "topics" in data
    assert len(data["topics"]) <= 3
    assert any(topic["tag"] == "technology" for topic in data["topics"])
    assert any(topic["tag"] == "programming" for topic in data["topics"])

@pytest.mark.asyncio
async def test_get_usage_patterns():
    response = client.get("/api/analytics/usage_patterns")
    assert response.status_code == 200
    data = response.json()
    assert "total_items" in data
    assert data["total_items"] >= 6 # Based on our fixture
    assert "content_type_distribution" in data
    assert data["content_type_distribution"]["article"] >= 3
    assert data["content_type_distribution"]["video"] >= 2
    assert "capture_source_distribution" in data # This will be empty as we don't set source in fixture

@pytest.mark.asyncio
async def test_get_ai_generated_insights():
    # Mock the AI router to avoid actual LLM calls during testing
    with patch("app.services.ai_router.ai_router.execute_with_fallback") as mock_execute:
        mock_execute.return_value = json.dumps({"insights": ["Mock insight 1", "Mock insight 2"]})
        response = client.get("/api/analytics/ai_insights")
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert len(data["insights"]) == 2
        assert data["insights"][0]["insight"] == "Mock insight 1"
        assert data["insights"][1]["insight"] == "Mock insight 2"
        mock_execute.assert_called_once()
