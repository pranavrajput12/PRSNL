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
async def populate_categorization_data(db_connection: asyncpg.Connection):
    # Clear existing data
    await db_connection.execute("TRUNCATE items, tags, item_tags RESTART IDENTITY CASCADE;")

    # Insert test items
    test_items = [
        {"id": "b0000000-0000-4000-8000-000000000001", "title": "Python Programming Basics", "content": "Introduction to Python syntax and data structures.", "item_type": "article", "created_at": datetime.now()},
        {"id": "b0000000-0000-4000-8000-000000000002", "title": "Machine Learning with Scikit-learn", "content": "A guide to building ML models using Scikit-learn library.", "item_type": "article", "created_at": datetime.now()},
        {"id": "b0000000-0000-4000-8000-000000000003", "title": "Healthy Eating Habits", "content": "Tips for maintaining a balanced diet and healthy lifestyle.", "item_type": "note", "created_at": datetime.now()},
    ]
    for item in test_items:
        await db_connection.execute(
            "INSERT INTO items (id, title, content, item_type, created_at, status) VALUES ($1, $2, $3, $4, $5, 'completed')",
            item["id"], item["title"], item["content"], item["item_type"], item["created_at"]
        )

@pytest.mark.asyncio
async def test_categorize_item():
    response = client.post(
        "/api/categorize",
        json={
            "item_id": "b0000000-0000-4000-8000-000000000001",
            "category": "programming"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["item_id"] == "b0000000-0000-4000-8000-000000000001"
    assert data["category"] == "programming"

    # Verify category in DB (simplified check)
    response = client.get("/api/analytics/topics") # Using analytics endpoint to verify tags
    assert response.status_code == 200
    topics = response.json()["topics"]
    assert any(t["tag"] == "programming" for t in topics)

@pytest.mark.asyncio
async def test_categorize_item_invalid_id():
    response = client.post(
        "/api/categorize",
        json={
            "item_id": "b0000000-0000-4000-8000-000000000099",
            "category": "invalid"
        }
    )
    assert response.status_code == 404 # Or appropriate error for not found

@pytest.mark.asyncio
async def test_bulk_categorize():
    response = client.post(
        "/api/categorize/bulk",
        json={
            "item_ids": [
                "b0000000-0000-4000-8000-000000000002",
                "b0000000-0000-4000-8000-000000000003"
            ],
            "category": "general"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["categorized_count"] == 2

    # Verify categories in DB
    response = client.get("/api/analytics/topics")
    assert response.status_code == 200
    topics = response.json()["topics"]
    assert any(t["tag"] == "general" for t in topics)

@pytest.mark.asyncio
async def test_get_item_connections():
    # First, categorize some items to create connections (tags act as connections)
    client.post("/api/categorize", json={"item_id": "b0000000-0000-4000-8000-000000000001", "category": "programming"})
    client.post("/api/categorize", json={"item_id": "b0000000-0000-4000-8000-000000000002", "category": "programming"})

    response = client.get("/api/items/b0000000-0000-4000-8000-000000000001/connections")
    assert response.status_code == 200
    data = response.json()
    assert "connections" in data
    assert len(data["connections"]) > 0
    assert any(conn["type"] == "tag" and conn["value"] == "programming" for conn in data["connections"])

@pytest.mark.asyncio
async def test_get_categories_stats():
    # Ensure some categories exist
    client.post("/api/categorize", json={"item_id": "b0000000-0000-4000-8000-000000000001", "category": "programming"})
    client.post("/api/categorize", json={"item_id": "b0000000-0000-4000-8000-000000000003", "category": "productivity"})

    response = client.get("/api/categories/stats")
    assert response.status_code == 200
    data = response.json()
    assert "category_stats" in data
    assert len(data["category_stats"]) >= 2
    assert any(stat["category"] == "programming" and stat["count"] >= 1 for stat in data["category_stats"])
    assert any(stat["category"] == "productivity" and stat["count"] >= 1 for stat in data["category_stats"])
