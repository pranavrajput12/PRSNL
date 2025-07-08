import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock
import json

client = TestClient(app)

@pytest.mark.asyncio
async def test_get_ai_suggestions_success():
    mock_scraped_data = AsyncMock()
    mock_scraped_data.title = "Test Title"
    mock_scraped_data.content = "Test Content for AI suggestions."

    mock_ai_response = {
        "title": "AI Generated Title",
        "summary": "AI Generated Summary",
        "tags": ["ai-tag1", "ai-tag2"],
        "category": "article"
    }

    with patch("app.services.scraper.WebScraper") as MockWebScraper,
         patch("app.services.ai_router.ai_router.execute_with_fallback") as mock_execute_with_fallback:

        MockWebScraper.return_value.__aenter__.return_value.scrape.return_value = mock_scraped_data
        mock_execute_with_fallback.return_value = json.dumps(mock_ai_response)

        response = client.post(
            "/api/suggest",
            json={
                "url": "http://example.com/test"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "AI Generated Title"
        assert data["summary"] == "AI Generated Summary"
        assert "ai-tag1" in data["tags"]
        assert data["category"] == "article"

        MockWebScraper.return_value.__aenter__.return_value.scrape.assert_called_once()
        mock_execute_with_fallback.assert_called_once()

@pytest.mark.asyncio
async def test_get_ai_suggestions_scraping_failure():
    with patch("app.services.scraper.WebScraper") as MockWebScraper:
        MockWebScraper.return_value.__aenter__.return_value.scrape.side_effect = Exception("Scraping error")

        response = client.post(
            "/api/suggest",
            json={
                "url": "http://invalid.url"
            }
        )

        assert response.status_code == 400
        assert "Failed to scrape the URL" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_ai_suggestions_ai_failure():
    mock_scraped_data = AsyncMock()
    mock_scraped_data.title = "Test Title"
    mock_scraped_data.content = "Test Content for AI suggestions."

    with patch("app.services.scraper.WebScraper") as MockWebScraper,
         patch("app.services.ai_router.ai_router.execute_with_fallback") as mock_execute_with_fallback:

        MockWebScraper.return_value.__aenter__.return_value.scrape.return_value = mock_scraped_data
        mock_execute_with_fallback.side_effect = Exception("AI error")

        response = client.post(
            "/api/suggest",
            json={
                "url": "http://example.com/test"
            }
        )

        assert response.status_code == 200 # Fallback should return 200
        data = response.json()
        assert data["title"] == "Test Title"
        assert data["summary"] == "No description available"
        assert "uncategorized" in data["tags"]
        assert data["category"] == "article"

@pytest.mark.asyncio
async def test_get_ai_suggestions_no_content_scraped():
    mock_scraped_data = AsyncMock()
    mock_scraped_data.title = None
    mock_scraped_data.content = None

    with patch("app.services.scraper.WebScraper") as MockWebScraper:
        MockWebScraper.return_value.__aenter__.return_value.scrape.return_value = mock_scraped_data

        response = client.post(
            "/api/suggest",
            json={
                "url": "http://example.com/empty"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Untitled"
        assert data["summary"] == "Could not retrieve content from the URL."
        assert "needs-manual-review" in data["tags"]
        assert data["category"] == "article"
