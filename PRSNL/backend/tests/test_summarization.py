import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db_pool
from app.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
async def db_connection():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        yield conn

@pytest.fixture(autouse=True)
async def populate_summarization_data(db_connection: asyncpg.Connection):
    # Clear existing data
    await db_connection.execute("TRUNCATE items, tags, item_tags RESTART IDENTITY CASCADE;")

    # Insert test items
    test_items = [
        {"id": "d0000000-0000-4000-8000-000000000001", "title": "Long Article on AI", "content": """Artificial intelligence (AI) is intelligence demonstrated by machines, unlike the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving".

Capabilities of AI include: reasoning, knowledge representation, planning, learning, natural language processing (NLP), perception, and the ability to move and manipulate objects. General intelligence is among the field's long-term goals. To approach this problem, researchers have developed methods for solving problems and making decisions, including search and mathematical optimization, formal logic, artificial neural networks, and methods based on statistics, probability, and economics.

AI is used in various applications including: web search engines (e.g., Google Search), recommendation systems (used by YouTube, Amazon, and Netflix), understanding human speech (such as Siri and Alexa), self-driving cars (e.g., Waymo), and competing at the highest level in strategic game systems (such as chess and Go).""", "type": "article", "created_at": datetime.now()},
        {"id": "d0000000-0000-4000-8000-000000000002", "title": "Short Note on Productivity", "content": "Use the Pomodoro Technique for better focus.", "type": "note", "created_at": datetime.now() - timedelta(minutes=1)},
    ]
    for item in test_items:
        await db_connection.execute(
            "INSERT INTO items (id, title, content, type, created_at, status) VALUES ($1, $2, $3, $4, $5, 'completed')",
            item["id"], item["title"], item["content"], item["type"], item["created_at"]
        )

@pytest.mark.asyncio
async def test_summarize_item():
    mock_ai_response = {
        "summary": "AI is a field of computer science that develops intelligent machines capable of reasoning, learning, and problem-solving. It is applied in search engines, recommendation systems, and self-driving cars."
    }
    with patch("app.services.ai_router.ai_router.execute_with_fallback") as mock_execute:
        mock_execute.return_value = json.dumps(mock_ai_response)
        response = client.post(
            "/api/summarization/item",
            json={
                "item_id": "d0000000-0000-4000-8000-000000000001",
                "summary_type": "brief"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert data["summary"] == mock_ai_response["summary"]

@pytest.mark.asyncio
async def test_summarize_digest():
    mock_ai_response = {
        "digest": "Daily digest: AI advancements and productivity tips."
    }
    with patch("app.services.ai_router.ai_router.execute_with_fallback") as mock_execute:
        mock_execute.return_value = json.dumps(mock_ai_response)
        response = client.post(
            "/api/summarization/digest",
            json={
                "timeframe": "daily"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "digest" in data
        assert data["digest"] == mock_ai_response["digest"]

@pytest.mark.asyncio
async def test_summarize_topic():
    mock_ai_response = {
        "topic_summary": "Summary of all content related to AI: ..."
    }
    with patch("app.services.ai_router.ai_router.execute_with_fallback") as mock_execute:
        mock_execute.return_value = json.dumps(mock_ai_response)
        response = client.post(
            "/api/summarization/topic",
            json={
                "topic": "AI"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "topic_summary" in data
        assert data["topic_summary"] == mock_ai_response["topic_summary"]

@pytest.mark.asyncio
async def test_summarize_custom():
    mock_ai_response = {
        "custom_summary": "Custom summary about AI and its applications."
    }
    with patch("app.services.ai_router.ai_router.execute_with_fallback") as mock_execute:
        mock_execute.return_value = json.dumps(mock_ai_response)
        response = client.post(
            "/api/summarization/custom",
            json={
                "item_ids": ["d0000000-0000-4000-8000-000000000001"],
                "prompt": "Summarize the key aspects of AI."
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "custom_summary" in data
        assert data["custom_summary"] == mock_ai_response["custom_summary"]

@pytest.mark.asyncio
async def test_summarize_batch():
    mock_ai_response = {
        "batch_summaries": [
            {"item_id": "d0000000-0000-4000-8000-000000000001", "summary": "AI is intelligence by machines."},
            {"item_id": "d0000000-0000-4000-8000-000000000002", "summary": "Pomodoro for focus."}
        ]
    }
    with patch("app.services.ai_router.ai_router.execute_with_fallback") as mock_execute:
        mock_execute.return_value = json.dumps(mock_ai_response)
        response = client.post(
            "/api/summarization/batch",
            json={
                "item_ids": [
                    "d0000000-0000-4000-8000-000000000001",
                    "d0000000-0000-4000-8000-000000000002"
                ],
                "summary_type": "brief"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "batch_summaries" in data
        assert len(data["batch_summaries"]) == 2

@pytest.mark.asyncio
async def test_get_digest_preview():
    mock_ai_response = {
        "preview": "Preview of daily digest: AI and productivity."
    }
    with patch("app.services.ai_router.ai_router.execute_with_fallback") as mock_execute:
        mock_execute.return_value = json.dumps(mock_ai_response)
        response = client.get(
            "/api/summarization/digest/preview?timeframe=daily"
        )
        assert response.status_code == 200
        data = response.json()
        assert "preview" in data
        assert data["preview"] == mock_ai_response["preview"]
