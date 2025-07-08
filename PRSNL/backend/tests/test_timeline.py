import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db_pool
import asyncpg
from datetime import datetime, timedelta
from uuid import uuid4

client = TestClient(app)

@pytest.fixture(scope="module")
async def db_connection():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        yield conn

@pytest.fixture(autouse=True)
async def populate_timeline_data(db_connection: asyncpg.Connection):
    # Clear existing data
    await db_connection.execute("TRUNCATE items, tags, item_tags RESTART IDENTITY CASCADE;")

    # Insert 30 test items with distinct created_at timestamps
    for i in range(30):
        item_id = str(uuid4())
        created_at = datetime.now() - timedelta(minutes=i)
        await db_connection.execute(
            "INSERT INTO items (id, title, url, item_type, created_at, status) VALUES ($1, $2, $3, $4, $5, 'completed')",
            item_id, f"Test Item {i}", f"http://example.com/item{i}", "article", created_at
        )

@pytest.mark.asyncio
async def test_get_timeline_first_page():
    response = client.get("/api/timeline?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 10
    assert "next_cursor" in data
    assert data["next_cursor"] is not None
    assert data["items"][0]["title"] == "Test Item 0" # Newest item
    assert data["items"][-1]["title"] == "Test Item 9"

@pytest.mark.asyncio
async def test_get_timeline_second_page():
    # Get first page to get cursor
    response = client.get("/api/timeline?limit=10")
    first_page_data = response.json()
    cursor = first_page_data["next_cursor"]

    # Get second page using cursor
    response = client.get(f"/api/timeline?limit=10&cursor={cursor}")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 10
    assert "next_cursor" in data
    assert data["next_cursor"] is not None
    assert data["items"][0]["title"] == "Test Item 10"
    assert data["items"][-1]["title"] == "Test Item 19"

@pytest.mark.asyncio
async def test_get_timeline_last_page():
    # Get first two pages to get cursor for third page
    response = client.get("/api/timeline?limit=10")
    first_page_data = response.json()
    cursor1 = first_page_data["next_cursor"]

    response = client.get(f"/api/timeline?limit=10&cursor={cursor1}")
    second_page_data = response.json()
    cursor2 = second_page_data["next_cursor"]

    # Get third page using cursor
    response = client.get(f"/api/timeline?limit=10&cursor={cursor2}")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 10
    assert "next_cursor" in data
    assert data["next_cursor"] is None # Should be last page
    assert data["items"][0]["title"] == "Test Item 20"
    assert data["items"][-1]["title"] == "Test Item 29"

@pytest.mark.asyncio
async def test_get_timeline_empty_result():
    # Clear all data
    await db_connection.execute("TRUNCATE items, tags, item_tags RESTART IDENTITY CASCADE;")
    response = client.get("/api/timeline?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 0
    assert data["next_cursor"] is None

@pytest.mark.asyncio
async def test_get_timeline_invalid_cursor():
    response = client.get("/api/timeline?limit=10&cursor=invalid-cursor")
    assert response.status_code == 400
    assert "Invalid cursor format" in response.json()["detail"]
