import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db_pool
import asyncpg
from datetime import datetime, timedelta
from uuid import uuid4
import json

client = TestClient(app)

@pytest.fixture(scope="module")
async def db_connection():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        yield conn

@pytest.fixture(autouse=True)
async def populate_duplicate_data(db_connection: asyncpg.Connection):
    # Clear existing data
    await db_connection.execute("TRUNCATE items, tags, item_tags RESTART IDENTITY CASCADE;")

    # Insert test items, including duplicates
    test_items = [
        {"id": "c0000000-0000-4000-8000-000000000001", "title": "Unique Article", "url": "http://example.com/unique", "content": "This is unique content.", "item_type": "article", "created_at": datetime.now()},
        {"id": "c0000000-0000-4000-8000-000000000002", "title": "Duplicate Article 1", "url": "http://example.com/dup1", "content": "This is duplicate content.", "item_type": "article", "created_at": datetime.now() - timedelta(minutes=1)},
        {"id": "c0000000-0000-4000-8000-000000000003", "title": "Duplicate Article 2", "url": "http://example.com/dup2", "content": "This is duplicate content.", "item_type": "article", "created_at": datetime.now() - timedelta(minutes=2)},
        {"id": "c0000000-0000-4000-8000-000000000004", "title": "Another Unique", "url": "http://example.com/unique2", "content": "Another unique piece of content.", "item_type": "note", "created_at": datetime.now() - timedelta(minutes=3)},
    ]
    for item in test_items:
        await db_connection.execute(
            "INSERT INTO items (id, title, url, content, item_type, created_at, status) VALUES ($1, $2, $3, $4, $5, $6, 'completed')",
            item["id"], item["title"], item["url"], item["content"], item["item_type"], item["created_at"]
        )

@pytest.mark.asyncio
async def test_check_duplicates_by_content():
    response = client.post(
        "/api/duplicates/check",
        json={
            "content": "This is duplicate content."
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "duplicates" in data
    assert len(data["duplicates"]) == 2
    assert any(d["id"] == "c0000000-0000-4000-8000-000000000002" for d in data["duplicates"])
    assert any(d["id"] == "c0000000-0000-4000-8000-000000000003" for d in data["duplicates"])

@pytest.mark.asyncio
async def test_find_all_duplicates():
    response = client.get("/api/duplicates/find-all")
    assert response.status_code == 200
    data = response.json()
    assert "duplicate_groups" in data
    assert len(data["duplicate_groups"]) >= 1 # At least one group for our test data
    
    # Check for the specific duplicate group
    found_group = False
    for group in data["duplicate_groups"]:
        ids = sorted([d["id"] for d in group["items"]])
        if ids == sorted(["c0000000-0000-4000-8000-000000000002", "c0000000-0000-4000-8000-000000000003"]):
            found_group = True
            break
    assert found_group

@pytest.mark.asyncio
async def test_merge_duplicates():
    # Ensure items exist
    response = client.get("/api/duplicates/find-all")
    assert response.status_code == 200

    response = client.post(
        "/api/duplicates/merge",
        json={
            "primary_item_id": "c0000000-0000-4000-8000-000000000002",
            "duplicate_item_ids": ["c0000000-0000-4000-8000-000000000003"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["merged_count"] == 1

    # Verify that the duplicate item is gone and primary remains
    response = client.get("/api/timeline?limit=10") # Using timeline to check item existence
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(item["id"] == "c0000000-0000-4000-8000-000000000002" for item in items)
    assert not any(item["id"] == "c0000000-0000-4000-8000-000000000003" for item in items)
